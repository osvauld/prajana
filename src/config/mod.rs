pub mod agent_def;

use anyhow::{Context, Result};
use serde::{Deserialize, Serialize};
use std::collections::HashMap;
use std::path::PathBuf;

use agent_def::{AgentDefMode, AgentDefinition, ModelTier};

// ── Top-level config ────────────────────────────────────────────

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AppConfig {
    pub storage_path: PathBuf,
    pub project_root: PathBuf,
    pub providers: HashMap<String, ProviderConfig>,
    pub tiers: TierConfig,
    /// Static agents (planner, reviewer) — always running.
    pub static_agents: HashMap<String, AgentConfig>,
    pub ui: UiConfig,

    /// Discovered project agents from `.agent_x/agents/*.md`.
    /// These are spawned on demand, not at startup.
    #[serde(skip)]
    pub project_agents: HashMap<String, AgentDefinition>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ProviderConfig {
    pub kind: ProviderKind,
    pub api_key_env: String,
    pub base_url: Option<String>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum ProviderKind {
    Anthropic,
    OpenAI,
}

// ── Tier config ─────────────────────────────────────────────────

/// Maps model tiers to concrete provider + model pairs.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TierConfig {
    pub smart: TierModelRef,
    pub worker: TierModelRef,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct TierModelRef {
    pub provider: String,
    pub model: String,
}

impl TierConfig {
    /// Resolve a tier to (provider_name, model_name).
    pub fn resolve(&self, tier: ModelTier) -> (&str, &str) {
        match tier {
            ModelTier::Smart => (&self.smart.provider, &self.smart.model),
            ModelTier::Worker => (&self.worker.provider, &self.worker.model),
        }
    }
}

// ── Agent config (for static agents and resolved dynamic agents) ──

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct AgentConfig {
    pub role: AgentRole,
    #[serde(default)]
    pub mode: AgentMode,
    pub provider: String,
    pub model: String,
    pub system_prompt: String,
    pub temperature: Option<f32>,
    pub max_tokens: Option<u32>,
    /// Enables model reasoning/thinking stream when provider supports it.
    pub thinking: Option<bool>,
    pub tools: Vec<String>,
    pub can_invoke: Vec<String>,
    #[serde(default)]
    pub cardinal_rules: Vec<String>,
    pub max_turns: Option<u32>,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum AgentRole {
    Planner,
    Reviewer,
    /// A project-defined domain specialist (read or write).
    Specialist,
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq, Eq)]
#[serde(rename_all = "lowercase")]
pub enum AgentMode {
    Read,
    Write,
}

impl Default for AgentMode {
    fn default() -> Self {
        Self::Read
    }
}

// ── UI config ───────────────────────────────────────────────────

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct UiConfig {
    pub theme: ThemeConfig,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct ThemeConfig {
    pub agent_colors: HashMap<String, String>,
}

// ── Resolve an AgentDefinition into a concrete AgentConfig ──────

impl AppConfig {
    /// Turn a project AgentDefinition into a runnable AgentConfig
    /// by resolving tier → provider + model.
    pub fn resolve_agent_def(&self, def: &AgentDefinition) -> Result<AgentConfig> {
        // For now we pin all dynamic agents to tier-resolved models
        // (currently both tiers are glm-4.7 on zai).
        if def.model_override.is_some() {
            tracing::info!(
                agent = %def.id,
                "ignoring model override; using tier model"
            );
        }
        let (p, m) = self.tiers.resolve(def.tier);
        let (provider, model) = (p.to_string(), m.to_string());

        let mode = match def.mode {
            AgentDefMode::Read => AgentMode::Read,
            AgentDefMode::Write => AgentMode::Write,
        };

        // Peer-to-peer default:
        // - if can_invoke is omitted/empty, allow all known agents (no hierarchy)
        // - if it contains "*", also allow all known agents
        // - otherwise honor the explicit list
        let mut can_invoke = if def.can_invoke.is_empty() || def.can_invoke.iter().any(|s| s == "*")
        {
            self.all_known_agent_ids()
        } else {
            def.can_invoke.clone()
        };
        can_invoke.retain(|id| id != &def.id);

        Ok(AgentConfig {
            role: AgentRole::Specialist,
            mode,
            provider,
            model,
            system_prompt: def.system_prompt.clone(),
            temperature: Some(def.temperature),
            max_tokens: Some(def.max_tokens),
            thinking: Some(def.thinking),
            tools: def.tools.clone(),
            can_invoke,
            cardinal_rules: vec![],
            max_turns: Some(def.max_turns),
        })
    }

    /// All agent ids known to this config (static + project).
    pub fn all_known_agent_ids(&self) -> Vec<String> {
        let mut ids: Vec<String> = self.static_agents.keys().cloned().collect();
        ids.extend(self.project_agents.keys().cloned());
        ids.sort();
        ids
    }

    /// Check if an agent id is a known project agent (spawnable on demand).
    pub fn is_spawnable(&self, agent_id: &str) -> bool {
        self.project_agents.contains_key(agent_id)
    }
}

// ── Defaults ────────────────────────────────────────────────────

impl Default for AppConfig {
    fn default() -> Self {
        let mut providers = HashMap::new();
        providers.insert(
            "zai".to_string(),
            ProviderConfig {
                kind: ProviderKind::OpenAI,
                api_key_env: "ZAI_API_KEY".to_string(),
                base_url: Some("https://api.z.ai/api/coding/paas/v4".to_string()),
            },
        );

        let tiers = TierConfig {
            smart: TierModelRef {
                provider: "zai".to_string(),
                model: "glm-4.7".to_string(),
            },
            worker: TierModelRef {
                provider: "zai".to_string(),
                model: "glm-4.7".to_string(),
            },
        };

        // ── Static agents ────────────────────────────────────────
        // Only planner + reviewer. Everything else comes from project agents.
        //
        //   user → planner ←→ [any project agent]
        //                  ←→ reviewer
        //   reviewer ←→ [any project agent with mode=write]
        //
        // Peer topology: planner can invoke anyone. Reviewer can invoke
        // any writer to request fixes. Project agents can invoke peers
        // per their own can_invoke list.

        let mut static_agents = HashMap::new();

        static_agents.insert(
            "planner".to_string(),
            AgentConfig {
                role: AgentRole::Planner,
                mode: AgentMode::Read,
                provider: "zai".to_string(),
                model: "glm-4.7".to_string(),
                system_prompt: concat!(
                    "You are the planner. Users talk to you. ",
                    "You decompose requests into ordered steps and delegate to specialist agents. ",
                    "You never edit code or run commands yourself.\n\n",
                    "You have access to project-specific domain agents. ",
                    "Each agent is a specialist for a particular part of the codebase. ",
                    "Delegate reading/analysis tasks to agents in read mode, ",
                    "and editing tasks to agents in write mode.\n\n",
                    "After a task completes, ask the reviewer to verify the changes."
                )
                .to_string(),
                temperature: Some(0.0),
                max_tokens: Some(4096),
                thinking: Some(false),
                tools: vec!["call_agent".into()],
                can_invoke: vec!["*".into()], // expanded at runtime
                cardinal_rules: vec![
                    "Never edit code directly -- always delegate to a specialist agent".into(),
                    "Always get context from a reader agent before asking a writer to change code"
                        .into(),
                    "After writes, delegate to reviewer for verification".into(),
                ],
                max_turns: Some(30),
            },
        );

        static_agents.insert(
            "reviewer".to_string(),
            AgentConfig {
                role: AgentRole::Reviewer,
                mode: AgentMode::Read,
                provider: "zai".to_string(),
                model: "glm-4.7".to_string(),
                system_prompt: concat!(
                    "You are the reviewer. You check changes for correctness, safety, and style. ",
                    "Give a clear PASS or FAIL with specific file:line reasons.\n\n",
                    "On FAIL, you can call a writer agent directly to request fixes. ",
                    "You never edit code yourself."
                )
                .to_string(),
                temperature: Some(0.0),
                max_tokens: Some(4096),
                thinking: Some(false),
                tools: vec![
                    "read_file".into(),
                    "glob".into(),
                    "grep".into(),
                    "rust_list_symbols".into(),
                    "rust_validate_file".into(),
                    "shell".into(),
                    "call_agent".into(),
                ],
                can_invoke: vec!["*".into()], // expanded at runtime
                cardinal_rules: vec![
                    "Never silently rewrite code -- FAIL with instructions instead".into(),
                    "Always read the actual changed files before reviewing".into(),
                    "Give concrete PASS or FAIL with file:line references".into(),
                ],
                max_turns: Some(15),
            },
        );

        let mut agent_colors = HashMap::new();
        agent_colors.insert("planner".into(), "#c678dd".into());
        agent_colors.insert("reviewer".into(), "#e5c07b".into());

        Self {
            storage_path: dirs_home().join(".agent_x"),
            project_root: std::env::current_dir().unwrap_or_else(|_| PathBuf::from(".")),
            providers,
            tiers,
            static_agents,
            ui: UiConfig {
                theme: ThemeConfig { agent_colors },
            },
            project_agents: HashMap::new(),
        }
    }
}

// ── Loading ─────────────────────────────────────────────────────

impl AppConfig {
    pub fn load() -> Result<Self> {
        let config_dir = dirs_home().join(".agent_x");
        let json_path = config_dir.join("config.json");

        let mut cfg = if json_path.exists() {
            let content = std::fs::read_to_string(&json_path)
                .with_context(|| format!("failed reading {}", json_path.display()))?;
            serde_json::from_str::<AppConfig>(&content)
                .with_context(|| format!("invalid JSON config at {}", json_path.display()))?
        } else {
            let cfg = AppConfig::default();
            // Write defaults so the user can edit them.
            std::fs::create_dir_all(&config_dir)?;
            let json = serde_json::to_string_pretty(&cfg)?;
            std::fs::write(&json_path, json)?;
            cfg
        };

        // Set project root to CWD.
        cfg.project_root = std::env::current_dir().unwrap_or_else(|_| PathBuf::from("."));

        // Discover project agents.
        // Priority:
        // 1) `.agent_x/agents/*.md` (agent_x-native format)
        // 2) `.opencode/agents/*.md` (compat mode; parsed with tolerant defaults)
        let native_dir = cfg.project_root.join(".agent_x").join("agents");
        let compat_dir = cfg.project_root.join(".opencode").join("agents");

        let mut discovered = HashMap::new();

        if native_dir.exists() {
            discovered = agent_def::discover_agents(&native_dir).unwrap_or_else(|e| {
                tracing::warn!(error = %e, "failed to discover .agent_x agents");
                HashMap::new()
            });
        }

        if discovered.is_empty() && compat_dir.exists() {
            discovered = agent_def::discover_agents(&compat_dir).unwrap_or_else(|e| {
                tracing::warn!(error = %e, "failed to discover .opencode agents");
                HashMap::new()
            });
        }

        cfg.project_agents = discovered;

        // Expand wildcard can_invoke for static agents now that we know all ids.
        let all_ids = cfg.all_known_agent_ids();
        for (_id, agent) in cfg.static_agents.iter_mut() {
            if agent.can_invoke.iter().any(|s| s == "*") {
                agent.can_invoke = all_ids.clone();
            }
        }

        // Assign colors for discovered project agents.
        let palette = [
            "#61afef", "#98c379", "#e06c75", "#56b6c2", "#d19a66", "#c678dd", "#be5046", "#e5c07b",
        ];
        for (i, id) in cfg.project_agents.keys().enumerate() {
            cfg.ui
                .theme
                .agent_colors
                .entry(id.clone())
                .or_insert_with(|| palette[i % palette.len()].to_string());
        }

        cfg.validate()?;
        Ok(cfg)
    }

    pub fn validate(&self) -> Result<()> {
        for (agent_id, agent) in &self.static_agents {
            if !self.providers.contains_key(&agent.provider) {
                anyhow::bail!(
                    "static agent '{}' references missing provider '{}'",
                    agent_id,
                    agent.provider
                );
            }
        }

        // Validate that tier providers exist.
        if !self.providers.contains_key(&self.tiers.smart.provider) {
            anyhow::bail!(
                "smart tier references missing provider '{}'",
                self.tiers.smart.provider
            );
        }
        if !self.providers.contains_key(&self.tiers.worker.provider) {
            anyhow::bail!(
                "worker tier references missing provider '{}'",
                self.tiers.worker.provider
            );
        }

        Ok(())
    }
}

fn dirs_home() -> PathBuf {
    std::env::var("HOME")
        .map(PathBuf::from)
        .unwrap_or_else(|_| PathBuf::from("."))
}
