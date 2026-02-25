use anyhow::{Context, Result};
use serde::Deserialize;
use std::path::PathBuf;
use tokio::process::Command;
use tracing::{info, warn};
use uuid::Uuid;

use super::{Tool, ToolResult};

/// Manages a dedicated tmux session for agent command execution.
///
/// Each agent gets its own tmux window inside a shared `agent-x` session.
/// Commands run via `tmux send-keys`, output captured via `tmux capture-pane`.
/// User can attach to `tmux attach -t agent-x` to watch live.
#[derive(Clone)]
pub struct TmuxManager {
    session_name: String,
}

impl TmuxManager {
    pub fn new(session_name: impl Into<String>) -> Self {
        Self {
            session_name: session_name.into(),
        }
    }

    /// Ensure the tmux session exists.
    pub async fn ensure_session(&self) -> Result<()> {
        let check = Command::new("tmux")
            .args(["has-session", "-t", &self.session_name])
            .output()
            .await;

        match check {
            Ok(out) if out.status.success() => Ok(()),
            _ => {
                info!(session = %self.session_name, "creating tmux session");
                let output = Command::new("tmux")
                    .args(["new-session", "-d", "-s", &self.session_name, "-n", "main"])
                    .output()
                    .await
                    .context("failed to create tmux session")?;

                if !output.status.success() {
                    let stderr = String::from_utf8_lossy(&output.stderr);
                    anyhow::bail!("tmux new-session failed: {}", stderr);
                }
                Ok(())
            }
        }
    }

    /// Ensure a window exists for an agent. Idempotent.
    pub async fn ensure_window(&self, agent_id: &str, working_dir: &str) -> Result<String> {
        let target = format!("{}:{}", self.session_name, agent_id);

        // Check if window exists
        let check = Command::new("tmux")
            .args(["select-window", "-t", &target])
            .output()
            .await;

        if let Ok(out) = check {
            if out.status.success() {
                return Ok(target);
            }
        }

        // Create window
        info!(agent = agent_id, "creating tmux window");
        let output = Command::new("tmux")
            .args([
                "new-window",
                "-t",
                &self.session_name,
                "-n",
                agent_id,
                "-c",
                working_dir,
            ])
            .output()
            .await
            .context("failed to create tmux window")?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            warn!(agent = agent_id, err = %stderr, "tmux new-window warning");
        }

        Ok(target)
    }

    /// Run a command in an agent's tmux window.
    /// Returns a marker ID that we use to find where output starts.
    pub async fn send_command(&self, agent_id: &str, command: &str) -> Result<String> {
        let target = format!("{}:{}", self.session_name, agent_id);
        let marker = format!("__AX_{}__", Uuid::new_v4().simple());

        // Echo a start marker, run command, echo end marker with exit code
        let wrapped = format!(
            "echo '{}:START'; {} ; echo '{}:EXIT:'$?",
            marker, command, marker
        );

        let output = Command::new("tmux")
            .args(["send-keys", "-t", &target, &wrapped, "Enter"])
            .output()
            .await
            .context("tmux send-keys failed")?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            anyhow::bail!("tmux send-keys failed: {}", stderr);
        }

        Ok(marker)
    }

    /// Wait for a command to complete and capture its output.
    /// Polls the pane content looking for the end marker.
    pub async fn wait_and_capture(
        &self,
        agent_id: &str,
        marker: &str,
        timeout_secs: u64,
    ) -> Result<CapturedOutput> {
        let target = format!("{}:{}", self.session_name, agent_id);
        let start_marker = format!("{}:START", marker);
        let exit_prefix = format!("{}:EXIT:", marker);

        let deadline = tokio::time::Instant::now() + tokio::time::Duration::from_secs(timeout_secs);

        loop {
            if tokio::time::Instant::now() > deadline {
                return Ok(CapturedOutput {
                    stdout: "[command timed out]".into(),
                    exit_code: -1,
                    timed_out: true,
                });
            }

            // Capture pane content
            let output = Command::new("tmux")
                .args([
                    "capture-pane",
                    "-t",
                    &target,
                    "-p", // print to stdout
                    "-S",
                    "-500", // last 500 lines
                ])
                .output()
                .await?;

            let pane_content = String::from_utf8_lossy(&output.stdout).to_string();

            // Look for the exit marker
            if let Some(exit_pos) = pane_content.find(&exit_prefix) {
                // Extract exit code
                let after_prefix = &pane_content[exit_pos + exit_prefix.len()..];
                let exit_code: i32 = after_prefix
                    .lines()
                    .next()
                    .unwrap_or("1")
                    .trim()
                    .parse()
                    .unwrap_or(1);

                // Extract output between start and exit markers
                let start_pos = pane_content
                    .find(&start_marker)
                    .map(|p| p + start_marker.len())
                    .unwrap_or(0);

                let command_output = pane_content[start_pos..exit_pos].trim().to_string();

                return Ok(CapturedOutput {
                    stdout: command_output,
                    exit_code,
                    timed_out: false,
                });
            }

            tokio::time::sleep(tokio::time::Duration::from_millis(200)).await;
        }
    }

    /// Kill the entire tmux session (cleanup).
    pub async fn kill_session(&self) -> Result<()> {
        let _ = Command::new("tmux")
            .args(["kill-session", "-t", &self.session_name])
            .output()
            .await;
        Ok(())
    }

    /// Capture the latest lines from an agent's tmux window.
    pub async fn capture_window(&self, agent_id: &str, lines: i32) -> Result<String> {
        let target = format!("{}:{}", self.session_name, agent_id);
        let start = format!("-{}", lines.max(20));
        let output = Command::new("tmux")
            .args(["capture-pane", "-t", &target, "-p", "-S", &start])
            .output()
            .await
            .context("tmux capture-pane failed")?;

        if !output.status.success() {
            let stderr = String::from_utf8_lossy(&output.stderr);
            anyhow::bail!("tmux capture-pane failed: {}", stderr);
        }

        Ok(String::from_utf8_lossy(&output.stdout).to_string())
    }

    /// Check whether a window for agent exists in the session.
    pub async fn window_exists(&self, agent_id: &str) -> Result<bool> {
        let target = format!("{}:{}", self.session_name, agent_id);
        let out = Command::new("tmux")
            .args(["has-session", "-t", &target])
            .output()
            .await
            .context("tmux has-session failed")?;
        Ok(out.status.success())
    }

    /// Switch current tmux client to an agent window.
    /// Works when agent_x itself runs inside tmux.
    pub async fn switch_to_window(&self, agent_id: &str) -> Result<()> {
        let target = format!("{}:{}", self.session_name, agent_id);
        let out = Command::new("tmux")
            .args(["switch-client", "-t", &target])
            .output()
            .await
            .context("tmux switch-client failed")?;
        if !out.status.success() {
            let stderr = String::from_utf8_lossy(&out.stderr);
            anyhow::bail!("tmux switch-client failed: {}", stderr);
        }
        Ok(())
    }

    /// Kill an agent window if it exists.
    pub async fn kill_window(&self, agent_id: &str) -> Result<()> {
        let target = format!("{}:{}", self.session_name, agent_id);
        let out = Command::new("tmux")
            .args(["kill-window", "-t", &target])
            .output()
            .await
            .context("tmux kill-window failed")?;
        if !out.status.success() {
            let stderr = String::from_utf8_lossy(&out.stderr);
            anyhow::bail!("tmux kill-window failed: {}", stderr);
        }
        Ok(())
    }
}

#[derive(Clone, Debug)]
pub struct CapturedOutput {
    pub stdout: String,
    pub exit_code: i32,
    pub timed_out: bool,
}

/// Shell tool that runs commands in an agent's tmux window.
pub struct ShellTool {
    workspace_root: PathBuf,
    agent_id: String,
    tmux: TmuxManager,
    deny_list: Vec<String>,
    timeout_secs: u64,
}

/// Tool for extracting tmux logs for debugging.
pub struct TmuxLogsTool {
    tmux: TmuxManager,
    default_lines: i32,
}

impl TmuxLogsTool {
    pub fn new(tmux: TmuxManager) -> Self {
        Self {
            tmux,
            default_lines: 200,
        }
    }
}

impl ShellTool {
    pub fn new(workspace_root: PathBuf, agent_id: String, tmux: TmuxManager) -> Self {
        Self {
            workspace_root,
            agent_id,
            tmux,
            deny_list: vec![
                "rm -rf /".into(),
                "rm -rf ~".into(),
                "mkfs".into(),
                "dd if=".into(),
                "> /dev/sda".into(),
            ],
            timeout_secs: 60,
        }
    }

    pub async fn init(&self) -> Result<()> {
        self.tmux.ensure_session().await?;
        self.tmux
            .ensure_window(&self.agent_id, self.workspace_root.to_str().unwrap_or("."))
            .await?;
        Ok(())
    }
}

#[derive(Deserialize)]
struct ShellArgs {
    command: String,
    #[serde(default)]
    timeout_secs: Option<u64>,
}

#[derive(Deserialize)]
struct TmuxLogsArgs {
    agent_id: String,
    #[serde(default)]
    lines: Option<i32>,
}

#[async_trait::async_trait]
impl Tool for ShellTool {
    fn name(&self) -> &str {
        "shell"
    }

    fn description(&self) -> &str {
        "Execute a shell command in the agent's tmux window"
    }

    async fn execute(&self, args: serde_json::Value) -> Result<ToolResult> {
        let args: ShellArgs = serde_json::from_value(args)?;

        // Check deny list
        for denied in &self.deny_list {
            if args.command.contains(denied) {
                return Ok(ToolResult {
                    name: "shell".into(),
                    success: false,
                    output: format!("command blocked by safety policy: contains '{}'", denied),
                });
            }
        }

        let timeout = args.timeout_secs.unwrap_or(self.timeout_secs);

        // Send command to tmux
        let marker = self
            .tmux
            .send_command(&self.agent_id, &args.command)
            .await?;

        // Wait and capture output
        let captured = self
            .tmux
            .wait_and_capture(&self.agent_id, &marker, timeout)
            .await?;

        // Truncate if too long
        let output = if captured.stdout.len() > 50_000 {
            format!(
                "{}...\n[truncated, {} bytes total]",
                &captured.stdout[..50_000],
                captured.stdout.len()
            )
        } else {
            captured.stdout
        };

        Ok(ToolResult {
            name: "shell".into(),
            success: captured.exit_code == 0 && !captured.timed_out,
            output: if captured.timed_out {
                format!("command timed out after {}s\n{}", timeout, output)
            } else {
                output
            },
        })
    }
}

#[async_trait::async_trait]
impl Tool for TmuxLogsTool {
    fn name(&self) -> &str {
        "tmux_logs"
    }

    fn description(&self) -> &str {
        "Capture recent logs from an agent tmux pane"
    }

    async fn execute(&self, args: serde_json::Value) -> Result<ToolResult> {
        let args: TmuxLogsArgs = serde_json::from_value(args)?;
        let lines = args.lines.unwrap_or(self.default_lines).max(20);

        match self.tmux.capture_window(&args.agent_id, lines).await {
            Ok(output) => Ok(ToolResult {
                name: "tmux_logs".into(),
                success: true,
                output,
            }),
            Err(e) => Ok(ToolResult {
                name: "tmux_logs".into(),
                success: false,
                output: format!("failed to capture tmux logs: {}", e),
            }),
        }
    }
}
