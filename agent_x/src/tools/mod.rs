pub mod file;
pub mod jj;
pub mod rust_analyzer;
pub mod search;
pub mod shell;
pub mod surgical;

use anyhow::Result;
use serde::{Deserialize, Serialize};

/// Every tool call and result is typed for bus transport.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ToolCall {
    pub name: String,
    pub args: serde_json::Value,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ToolResult {
    pub name: String,
    pub success: bool,
    pub output: String,
}

/// Tool trait — each tool is a named async function.
#[async_trait::async_trait]
pub trait Tool: Send + Sync {
    fn name(&self) -> &str;
    fn description(&self) -> &str;
    async fn execute(&self, args: serde_json::Value) -> Result<ToolResult>;
}
