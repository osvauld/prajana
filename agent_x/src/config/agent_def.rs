//! Parse agent definition files from `.agent_x/agents/*.md`.
//!
//! # Format
//!
//! ```markdown
//! ---
//! description: "Butler storage specialist"
//! mode: write
//! tier: worker
//! temperature: 0.2
//! max_tokens: 4096
//! max_turns: 25
//! can_invoke: ["scribe", "reader"]
//! tools: ["read_file", "glob"]
//! permission:
//!   edit: deny
//!   bash:
//!     "*": deny
//!     "cargo *": allow
//! ---
//!
//! You are the Butler specialist...
//! ```
//!
//! - `mode`: `read` (no file mutations) or `write` (can edit). Default: `write`.
//! - `tier`: `smart` (strong model for reasoning) or `worker` (cheap model for mechanical edits).
//!   Default: inferred from mode — `read` → `smart`, `write` → `worker`.
//! - `model`: explicit "provider/model" override; skips tier lookup.
//! - Body after frontmatter becomes the agent's system prompt.

use anyhow::{Context, Result};
use serde::Deserialize;
use serde_yaml::Value as YamlValue;
use std::collections::HashMap;
use std::path::Path;

// ── Frontmatter schema ──────────────────────────────────────────

#[derive(Debug, Clone, Deserialize)]
pub struct AgentFrontmatter {
    pub description: String,

    #[serde(default)]
    pub mode: Option<String>,

    #[serde(default)]
    pub tier: Option<ModelTier>,

    /// Explicit "provider/model" override (e.g. "anthropic/claude-opus-4-6").
    /// When set, `tier` is ignored for model resolution.
    #[serde(default)]
    pub model: Option<String>,

    #[serde(default)]
    pub temperature: Option<f32>,

    #[serde(default)]
    pub max_tokens: Option<u32>,

    #[serde(default)]
    pub max_turns: Option<u32>,

    /// Thinking mode: on/off/true/false
    #[serde(default)]
    pub thinking: Option<YamlValue>,

    /// Peers this agent can invoke. `["*"]` means any.
    #[serde(default)]
    pub can_invoke: Vec<String>,

    /// Explicit tool list. If empty, defaults are derived from `mode`.
    #[serde(default)]
    pub tools: Vec<String>,

    #[serde(default)]
    pub permission: Option<PermissionDef>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum AgentDefMode {
    Read,
    Write,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ModelTier {
    Smart,
    Worker,
}

#[derive(Debug, Clone, Deserialize)]
pub struct PermissionDef {
    #[serde(default)]
    pub edit: Option<PermissionLevel>,
    #[serde(default)]
    pub bash: Option<YamlValue>,
}

#[derive(Debug, Clone, Copy, PartialEq, Eq, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum PermissionLevel {
    Allow,
    Deny,
    Ask,
}

// ── Parsed result ───────────────────────────────────────────────

/// A fully-resolved agent definition loaded from a `.md` file.
#[derive(Debug, Clone)]
pub struct AgentDefinition {
    /// Agent id (filename stem, e.g. "butler" from "butler.md").
    pub id: String,
    pub description: String,
    pub mode: AgentDefMode,
    pub tier: ModelTier,
    /// Explicit model override, or None to use tier default.
    pub model_override: Option<String>,
    pub temperature: f32,
    pub max_tokens: u32,
    pub max_turns: u32,
    pub thinking: bool,
    pub can_invoke: Vec<String>,
    pub tools: Vec<String>,
    pub permission: Option<PermissionDef>,
    /// The markdown body (everything after frontmatter) — becomes system prompt.
    pub system_prompt: String,
}

fn parse_mode(raw: Option<&str>, permission: Option<&PermissionDef>) -> AgentDefMode {
    match raw.unwrap_or_default().trim().to_lowercase().as_str() {
        "read" => AgentDefMode::Read,
        "write" => AgentDefMode::Write,
        // Compatibility with opencode frontmatter (`mode: subagent`).
        // Infer read vs write from permission.edit if present.
        "subagent" => match permission.and_then(|p| p.edit) {
            Some(PermissionLevel::Deny) => AgentDefMode::Read,
            _ => AgentDefMode::Write,
        },
        // Unknown or missing mode defaults to write.
        _ => AgentDefMode::Write,
    }
}

fn parse_thinking(raw: Option<&YamlValue>) -> bool {
    match raw {
        Some(YamlValue::Bool(v)) => *v,
        Some(YamlValue::String(s)) => match s.trim().to_lowercase().as_str() {
            "on" | "true" | "enabled" | "yes" => true,
            "off" | "false" | "disabled" | "no" => false,
            _ => false,
        },
        _ => false,
    }
}

// ── Default tools by mode ───────────────────────────────────────

fn default_read_tools() -> Vec<String> {
    vec![
        "read_file".into(),
        "glob".into(),
        "grep".into(),
        "rust_list_symbols".into(),
        "rust_validate_file".into(),
        "shell".into(),
    ]
}

fn default_write_tools() -> Vec<String> {
    vec![
        "read_file".into(),
        "write_file".into(),
        "patch_file".into(),
        "glob".into(),
        "grep".into(),
        "shell".into(),
        "rust_list_symbols".into(),
        "rust_replace_block".into(),
        "rust_insert_after_block".into(),
        "rust_validate_file".into(),
    ]
}

// ── Parsing ─────────────────────────────────────────────────────

/// Split a markdown file into (frontmatter_yaml, body).
/// Expects `---\n...\n---\n` at the start.
fn split_frontmatter(content: &str) -> Option<(&str, &str)> {
    let trimmed = content.trim_start();
    if !trimmed.starts_with("---") {
        return None;
    }
    // Find end of opening ---
    let after_open = &trimmed[3..];
    let after_open = after_open.strip_prefix('\n').unwrap_or(after_open);

    let close_pos = after_open.find("\n---")?;
    let yaml = &after_open[..close_pos];
    let body_start = close_pos + 4; // skip \n---
    let body = if body_start < after_open.len() {
        after_open[body_start..].trim_start_matches('\n')
    } else {
        ""
    };
    Some((yaml, body))
}

/// Parse a single `.md` agent definition file.
pub fn parse_agent_file(path: &Path) -> Result<AgentDefinition> {
    let id = path
        .file_stem()
        .and_then(|s| s.to_str())
        .ok_or_else(|| anyhow::anyhow!("invalid agent file name: {}", path.display()))?
        .to_string();

    let content = std::fs::read_to_string(path)
        .with_context(|| format!("failed to read agent file: {}", path.display()))?;

    let (yaml_str, body) = split_frontmatter(&content)
        .ok_or_else(|| anyhow::anyhow!("no YAML frontmatter in {}", path.display()))?;

    let fm: AgentFrontmatter = serde_yaml::from_str(yaml_str)
        .with_context(|| format!("invalid frontmatter in {}", path.display()))?;

    let mode = parse_mode(fm.mode.as_deref(), fm.permission.as_ref());
    let thinking = parse_thinking(fm.thinking.as_ref());
    let tier = fm.tier.unwrap_or(match mode {
        AgentDefMode::Read => ModelTier::Smart,
        AgentDefMode::Write => ModelTier::Worker,
    });

    let tools = if fm.tools.is_empty() {
        match mode {
            AgentDefMode::Read => default_read_tools(),
            AgentDefMode::Write => default_write_tools(),
        }
    } else {
        fm.tools
    };

    Ok(AgentDefinition {
        id,
        description: fm.description,
        mode,
        tier,
        model_override: fm.model,
        temperature: fm.temperature.unwrap_or(0.2),
        max_tokens: fm.max_tokens.unwrap_or(4096),
        max_turns: fm.max_turns.unwrap_or(25),
        thinking,
        can_invoke: fm.can_invoke,
        tools,
        permission: fm.permission,
        system_prompt: body.to_string(),
    })
}

/// Discover and parse all agent definitions from a directory.
/// Returns a map of agent_id → AgentDefinition.
pub fn discover_agents(dir: &Path) -> Result<HashMap<String, AgentDefinition>> {
    let mut agents = HashMap::new();

    if !dir.exists() {
        return Ok(agents);
    }

    let mut entries: Vec<_> = std::fs::read_dir(dir)?
        .filter_map(|e| e.ok())
        .filter(|e| {
            e.path()
                .extension()
                .and_then(|ext| ext.to_str())
                .map(|ext| ext == "md")
                .unwrap_or(false)
        })
        .collect();
    entries.sort_by_key(|e| e.file_name());

    for entry in entries {
        let path = entry.path();
        match parse_agent_file(&path) {
            Ok(def) => {
                tracing::info!(agent = %def.id, mode = ?def.mode, tier = ?def.tier, "loaded agent definition");
                agents.insert(def.id.clone(), def);
            }
            Err(e) => {
                tracing::warn!(path = %path.display(), error = %e, "skipping invalid agent definition");
            }
        }
    }

    Ok(agents)
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn test_split_frontmatter() {
        let input = "---\ndescription: test\nmode: read\n---\nYou are a test agent.\n";
        let (yaml, body) = split_frontmatter(input).unwrap();
        assert!(yaml.contains("description: test"));
        assert!(body.contains("You are a test agent."));
    }

    #[test]
    fn test_parse_minimal_frontmatter() {
        let yaml = "description: \"test agent\"";
        let fm: AgentFrontmatter = serde_yaml::from_str(yaml).unwrap();
        assert_eq!(fm.description, "test agent");
        assert!(fm.mode.is_none());
        assert!(fm.tier.is_none());
    }

    #[test]
    fn test_mode_defaults() {
        // read mode → smart tier
        let fm = AgentFrontmatter {
            description: "test".into(),
            mode: Some("read".into()),
            tier: None,
            model: None,
            temperature: None,
            max_tokens: None,
            max_turns: None,
            thinking: None,
            can_invoke: vec![],
            tools: vec![],
            permission: None,
        };
        let mode = parse_mode(fm.mode.as_deref(), fm.permission.as_ref());
        let tier = fm.tier.unwrap_or(match mode {
            AgentDefMode::Read => ModelTier::Smart,
            AgentDefMode::Write => ModelTier::Worker,
        });
        assert_eq!(tier, ModelTier::Smart);
    }
}
