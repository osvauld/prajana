use anyhow::Result;
use serde::Deserialize;
use std::path::PathBuf;
use tokio::process::Command;

use super::{Tool, ToolResult};

/// Glob search tool — find files by pattern.
pub struct GlobTool {
    workspace_root: PathBuf,
}

impl GlobTool {
    pub fn new(workspace_root: PathBuf) -> Self {
        Self { workspace_root }
    }
}

#[derive(Deserialize)]
struct GlobArgs {
    pattern: String,
}

#[async_trait::async_trait]
impl Tool for GlobTool {
    fn name(&self) -> &str {
        "glob"
    }

    fn description(&self) -> &str {
        "Find files matching a glob pattern"
    }

    async fn execute(&self, args: serde_json::Value) -> Result<ToolResult> {
        let args: GlobArgs = serde_json::from_value(args)?;

        // Use fd or find as fallback
        let output = Command::new("find")
            .args([
                self.workspace_root.to_str().unwrap(),
                "-name",
                &args.pattern,
                "-not",
                "-path",
                "*/.jj/*",
                "-not",
                "-path",
                "*/target/*",
                "-not",
                "-path",
                "*/.agent-workspaces/*",
            ])
            .output()
            .await;

        match output {
            Ok(out) => {
                let files = String::from_utf8_lossy(&out.stdout);
                Ok(ToolResult {
                    name: "glob".into(),
                    success: true,
                    output: files.to_string(),
                })
            }
            Err(e) => Ok(ToolResult {
                name: "glob".into(),
                success: false,
                output: format!("glob search failed: {}", e),
            }),
        }
    }
}

/// Grep search tool — search file contents.
pub struct GrepTool {
    workspace_root: PathBuf,
}

impl GrepTool {
    pub fn new(workspace_root: PathBuf) -> Self {
        Self { workspace_root }
    }
}

#[derive(Deserialize)]
struct GrepArgs {
    pattern: String,
    #[serde(default)]
    include: Option<String>,
}

#[async_trait::async_trait]
impl Tool for GrepTool {
    fn name(&self) -> &str {
        "grep"
    }

    fn description(&self) -> &str {
        "Search file contents using regex patterns"
    }

    async fn execute(&self, args: serde_json::Value) -> Result<ToolResult> {
        let args: GrepArgs = serde_json::from_value(args)?;

        let mut cmd = Command::new("rg");
        cmd.args([
            "--no-heading",
            "--line-number",
            "--color=never",
            "--max-count=50",
            &args.pattern,
            self.workspace_root.to_str().unwrap(),
        ]);

        if let Some(ref include) = args.include {
            cmd.args(["--glob", include]);
        }

        // Exclude agent workspace and build dirs
        cmd.args([
            "--glob",
            "!.jj/**",
            "--glob",
            "!target/**",
            "--glob",
            "!.agent-workspaces/**",
        ]);

        match cmd.output().await {
            Ok(out) => {
                let results = String::from_utf8_lossy(&out.stdout);
                Ok(ToolResult {
                    name: "grep".into(),
                    success: true,
                    output: results.to_string(),
                })
            }
            Err(e) => Ok(ToolResult {
                name: "grep".into(),
                success: false,
                output: format!("grep failed: {}", e),
            }),
        }
    }
}
