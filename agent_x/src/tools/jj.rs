use anyhow::{Context, Result};
use std::path::{Path, PathBuf};
use tokio::process::Command;
use tracing::{info, warn};

/// Manages jj workspaces for agent isolation.
///
/// Each agent gets its own jj workspace (working copy) so they can
/// read/write files independently without conflicts.
///
/// Layout:
///   project/            <- main workspace (user)
///   .jj/
///   .agent-workspaces/
///     reader/           <- reader agent workspace
///     writer/           <- writer agent workspace
///     reviewer/         <- reviewer agent workspace
pub struct JjWorkspaceManager {
    /// Root of the project (where .jj lives)
    project_root: PathBuf,
    /// Base directory for agent workspaces
    workspaces_dir: PathBuf,
}

impl JjWorkspaceManager {
    pub fn new(project_root: PathBuf) -> Self {
        let workspaces_dir = project_root.join(".agent-workspaces");
        Self {
            project_root,
            workspaces_dir,
        }
    }

    /// Ensure the project is a jj repo. If not, initialize it.
    pub async fn ensure_jj_repo(&self) -> Result<()> {
        if !self.project_root.join(".jj").exists() {
            info!(path = %self.project_root.display(), "initializing jj repo");
            let output = Command::new("jj")
                .args(["git", "init"])
                .current_dir(&self.project_root)
                .output()
                .await
                .context("failed to run jj git init")?;

            if !output.status.success() {
                let stderr = String::from_utf8_lossy(&output.stderr);
                anyhow::bail!("jj git init failed: {}", stderr);
            }
        }
        Ok(())
    }

    /// Create a workspace for an agent. Idempotent.
    pub async fn create_workspace(&self, agent_id: &str) -> Result<PathBuf> {
        let ws_path = self.workspaces_dir.join(agent_id);

        if ws_path.exists() {
            info!(agent = agent_id, "workspace already exists");
            return Ok(ws_path);
        }

        std::fs::create_dir_all(&self.workspaces_dir)?;

        info!(agent = agent_id, path = %ws_path.display(), "creating jj workspace");
        let output = Command::new("jj")
            .args([
                "workspace",
                "add",
                "--name",
                agent_id,
                ws_path.to_str().unwrap(),
            ])
            .current_dir(&self.project_root)
            .output()
            .await
            .context("failed to create jj workspace")?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            // Workspace might already exist in jj but dir was cleaned
            if !stderr.contains("already exists") {
                anyhow::bail!("jj workspace add failed: {}", stderr);
            }
        }

        Ok(ws_path)
    }

    /// Get the workspace path for an agent.
    pub fn workspace_path(&self, agent_id: &str) -> PathBuf {
        self.workspaces_dir.join(agent_id)
    }

    /// Create a new jj change in an agent's workspace (for writing).
    pub async fn new_change(&self, agent_id: &str, description: &str) -> Result<String> {
        let ws_path = self.workspace_path(agent_id);
        let output = Command::new("jj")
            .args(["new", "-m", description])
            .current_dir(&ws_path)
            .output()
            .await
            .context("jj new failed")?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            anyhow::bail!("jj new failed: {}", stderr);
        }

        // Get the change id
        let id_output = Command::new("jj")
            .args(["log", "-r", "@", "--no-graph", "-T", "change_id"])
            .current_dir(&ws_path)
            .output()
            .await?;

        let change_id = String::from_utf8_lossy(&id_output.stdout)
            .trim()
            .to_string();
        info!(agent = agent_id, change = %change_id, "created new change");
        Ok(change_id)
    }

    /// Get the diff for an agent's current working copy change.
    pub async fn diff(&self, agent_id: &str) -> Result<String> {
        let ws_path = self.workspace_path(agent_id);
        let output = Command::new("jj")
            .args(["diff"])
            .current_dir(&ws_path)
            .output()
            .await
            .context("jj diff failed")?;

        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    }

    /// Squash an agent's change into the parent (approve / merge).
    pub async fn squash(&self, agent_id: &str) -> Result<()> {
        let ws_path = self.workspace_path(agent_id);
        let output = Command::new("jj")
            .args(["squash"])
            .current_dir(&ws_path)
            .output()
            .await
            .context("jj squash failed")?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            anyhow::bail!("jj squash failed: {}", stderr);
        }

        info!(agent = agent_id, "squashed change into parent");
        Ok(())
    }

    /// Abandon an agent's current change (reject / rollback).
    pub async fn abandon(&self, agent_id: &str) -> Result<()> {
        let ws_path = self.workspace_path(agent_id);
        let output = Command::new("jj")
            .args(["abandon", "@"])
            .current_dir(&ws_path)
            .output()
            .await
            .context("jj abandon failed")?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            warn!(agent = agent_id, err = %stderr, "jj abandon warning");
        }

        info!(agent = agent_id, "abandoned current change");
        Ok(())
    }

    /// Show log for an agent's workspace.
    pub async fn log(&self, agent_id: &str, limit: usize) -> Result<String> {
        let ws_path = self.workspace_path(agent_id);
        let output = Command::new("jj")
            .args(["log", "-n", &limit.to_string()])
            .current_dir(&ws_path)
            .output()
            .await
            .context("jj log failed")?;

        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    }

    /// Describe (set message on) the current change.
    pub async fn describe(&self, agent_id: &str, message: &str) -> Result<()> {
        let ws_path = self.workspace_path(agent_id);
        let output = Command::new("jj")
            .args(["describe", "-m", message])
            .current_dir(&ws_path)
            .output()
            .await
            .context("jj describe failed")?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            anyhow::bail!("jj describe failed: {}", stderr);
        }
        Ok(())
    }

    /// Show status of all agent workspaces.
    pub async fn status_all(&self) -> Result<Vec<WorkspaceStatus>> {
        let mut statuses = Vec::new();

        if let Ok(entries) = std::fs::read_dir(&self.workspaces_dir) {
            for entry in entries.flatten() {
                if entry.file_type().map(|t| t.is_dir()).unwrap_or(false) {
                    let agent_id = entry.file_name().to_string_lossy().to_string();
                    let diff = self.diff(&agent_id).await.unwrap_or_default();
                    let has_changes = !diff.trim().is_empty();
                    statuses.push(WorkspaceStatus {
                        agent_id,
                        has_changes,
                        diff_summary: if has_changes {
                            let lines: Vec<&str> = diff.lines().take(5).collect();
                            lines.join("\n")
                        } else {
                            "clean".to_string()
                        },
                    });
                }
            }
        }

        Ok(statuses)
    }

    /// Clean up all agent workspaces.
    pub async fn cleanup(&self) -> Result<()> {
        if let Ok(entries) = std::fs::read_dir(&self.workspaces_dir) {
            for entry in entries.flatten() {
                if entry.file_type().map(|t| t.is_dir()).unwrap_or(false) {
                    let name = entry.file_name().to_string_lossy().to_string();
                    let output = Command::new("jj")
                        .args(["workspace", "forget", &name])
                        .current_dir(&self.project_root)
                        .output()
                        .await?;

                    if output.status.success() {
                        let _ = std::fs::remove_dir_all(entry.path());
                    }
                }
            }
        }
        Ok(())
    }
}

#[derive(Clone, Debug)]
pub struct WorkspaceStatus {
    pub agent_id: String,
    pub has_changes: bool,
    pub diff_summary: String,
}
