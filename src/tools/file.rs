use anyhow::Result;
use serde::Deserialize;
use std::path::{Path, PathBuf};

use super::{Tool, ToolResult};

/// File read tool — reads from an agent's jj workspace.
pub struct ReadFileTool {
    workspace_root: PathBuf,
}

impl ReadFileTool {
    pub fn new(workspace_root: PathBuf) -> Self {
        Self { workspace_root }
    }

    fn resolve_path(&self, rel_path: &str) -> Result<PathBuf> {
        let full = self.workspace_root.join(rel_path);
        // Prevent path traversal
        let canonical = full.canonicalize().unwrap_or(full.clone());
        if !canonical.starts_with(&self.workspace_root) {
            anyhow::bail!("path traversal blocked: {}", rel_path);
        }
        Ok(full)
    }
}

#[derive(Deserialize)]
struct ReadArgs {
    path: String,
    #[serde(default)]
    offset: Option<usize>,
    #[serde(default)]
    limit: Option<usize>,
}

#[async_trait::async_trait]
impl Tool for ReadFileTool {
    fn name(&self) -> &str {
        "read_file"
    }

    fn description(&self) -> &str {
        "Read file contents from the workspace"
    }

    async fn execute(&self, args: serde_json::Value) -> Result<ToolResult> {
        let args: ReadArgs = serde_json::from_value(args)?;
        let path = self.resolve_path(&args.path)?;

        match tokio::fs::read_to_string(&path).await {
            Ok(content) => {
                let lines: Vec<&str> = content.lines().collect();
                let offset = args.offset.unwrap_or(0);
                let limit = args.limit.unwrap_or(lines.len());
                let subset: Vec<String> = lines
                    .iter()
                    .skip(offset)
                    .take(limit)
                    .enumerate()
                    .map(|(i, line)| format!("{:>4} | {}", offset + i + 1, line))
                    .collect();

                Ok(ToolResult {
                    name: "read_file".into(),
                    success: true,
                    output: subset.join("\n"),
                })
            }
            Err(e) => Ok(ToolResult {
                name: "read_file".into(),
                success: false,
                output: format!("failed to read {}: {}", args.path, e),
            }),
        }
    }
}

/// File write tool — writes to an agent's jj workspace.
pub struct WriteFileTool {
    workspace_root: PathBuf,
}

impl WriteFileTool {
    pub fn new(workspace_root: PathBuf) -> Self {
        Self { workspace_root }
    }

    fn resolve_path(&self, rel_path: &str) -> Result<PathBuf> {
        let full = self.workspace_root.join(rel_path);
        Ok(full)
    }
}

#[derive(Deserialize)]
struct WriteArgs {
    path: String,
    content: String,
}

#[async_trait::async_trait]
impl Tool for WriteFileTool {
    fn name(&self) -> &str {
        "write_file"
    }

    fn description(&self) -> &str {
        "Write content to a file in the workspace"
    }

    async fn execute(&self, args: serde_json::Value) -> Result<ToolResult> {
        let args: WriteArgs = serde_json::from_value(args)?;
        let path = self.resolve_path(&args.path)?;

        // Ensure parent dirs exist
        if let Some(parent) = path.parent() {
            tokio::fs::create_dir_all(parent).await?;
        }

        match tokio::fs::write(&path, &args.content).await {
            Ok(()) => Ok(ToolResult {
                name: "write_file".into(),
                success: true,
                output: format!("wrote {} bytes to {}", args.content.len(), args.path),
            }),
            Err(e) => Ok(ToolResult {
                name: "write_file".into(),
                success: false,
                output: format!("failed to write {}: {}", args.path, e),
            }),
        }
    }
}

/// Patch file tool — applies surgical text edits.
pub struct PatchFileTool {
    workspace_root: PathBuf,
}

impl PatchFileTool {
    pub fn new(workspace_root: PathBuf) -> Self {
        Self { workspace_root }
    }
}

#[derive(Deserialize)]
struct PatchArgs {
    path: String,
    old_text: String,
    new_text: String,
}

#[async_trait::async_trait]
impl Tool for PatchFileTool {
    fn name(&self) -> &str {
        "patch_file"
    }

    fn description(&self) -> &str {
        "Replace exact text in a file (surgical edit)"
    }

    async fn execute(&self, args: serde_json::Value) -> Result<ToolResult> {
        let args: PatchArgs = serde_json::from_value(args)?;
        let path = self.workspace_root.join(&args.path);

        match tokio::fs::read_to_string(&path).await {
            Ok(content) => {
                if !content.contains(&args.old_text) {
                    return Ok(ToolResult {
                        name: "patch_file".into(),
                        success: false,
                        output: "old_text not found in file".into(),
                    });
                }

                let new_content = content.replacen(&args.old_text, &args.new_text, 1);
                tokio::fs::write(&path, &new_content).await?;

                Ok(ToolResult {
                    name: "patch_file".into(),
                    success: true,
                    output: format!("patched {}", args.path),
                })
            }
            Err(e) => Ok(ToolResult {
                name: "patch_file".into(),
                success: false,
                output: format!("failed to read {}: {}", args.path, e),
            }),
        }
    }
}
