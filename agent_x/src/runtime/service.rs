use anyhow::Result;
use std::collections::HashMap;
use std::path::Path;
use std::sync::Arc;
use tokio::sync::{broadcast, mpsc, Mutex};

use crate::agent::Agent;
use crate::config::AppConfig;
use crate::provider;
use crate::runtime::bus::{Envelope, UiEvent};
use crate::runtime::router::Router;
use crate::storage::Store;
use crate::tools::file::{PatchFileTool, ReadFileTool, WriteFileTool};
use crate::tools::jj::JjWorkspaceManager;
use crate::tools::search::{GlobTool, GrepTool};
use crate::tools::shell::{ShellTool, TmuxManager};
use crate::tools::surgical::{
    RustInsertAfterBlockTool, RustListSymbolsTool, RustReplaceBlockTool, RustValidateFileTool,
};
use crate::tools::Tool;

// ── AgentSpawner ────────────────────────────────────────────────
// Shared state that the router uses to spawn dynamic agents on demand.

pub struct AgentSpawner {
    config: AppConfig,
    store: Arc<Store>,
    jj: JjWorkspaceManager,
    tmux: TmuxManager,
    route_tx: mpsc::Sender<Envelope>,
    ui_tx: broadcast::Sender<UiEvent>,
    shared_docs: String,
    codebase_index: String,
}

impl AgentSpawner {
    /// Spawn a dynamic project agent by id.
    /// Returns the agent's inbox sender for the router to register,
    /// or an error if the agent id is unknown.
    pub async fn spawn(&self, agent_id: &str) -> Result<mpsc::Sender<Envelope>> {
        let def = self
            .config
            .project_agents
            .get(agent_id)
            .ok_or_else(|| anyhow::anyhow!("unknown project agent: {}", agent_id))?;

        let mut agent_cfg = self.config.resolve_agent_def(def)?;

        // Build system prompt: base + shared skills + codebase index + agent-specific docs
        if !self.shared_docs.is_empty() {
            agent_cfg.system_prompt =
                format!("{}\n\n{}", agent_cfg.system_prompt, self.shared_docs);
        }
        if !self.codebase_index.is_empty() {
            agent_cfg.system_prompt =
                format!("{}\n\n{}", agent_cfg.system_prompt, self.codebase_index);
        }
        // Load agent-specific docs from agents/<id>/ directory (if any exist alongside .agent_x/agents/).
        let docs_prompt =
            load_agent_docs_prompt(&self.config.project_root, agent_id)?;
        if !docs_prompt.is_empty() {
            agent_cfg.system_prompt =
                format!("{}\n\n{}", agent_cfg.system_prompt, docs_prompt);
        }
        let rules_prompt = render_cardinal_rules(&agent_cfg.cardinal_rules);
        if !rules_prompt.is_empty() {
            agent_cfg.system_prompt =
                format!("{}\n\n{}", agent_cfg.system_prompt, rules_prompt);
        }

        // Create workspace + tmux window for this agent.
        let ws = self.jj.create_workspace(agent_id).await?;
        let _ = self
            .tmux
            .ensure_window(agent_id, ws.to_str().unwrap_or("."))
            .await?;

        let (inbox_tx, inbox_rx) = mpsc::channel::<Envelope>(256);

        let prov = provider::build_provider(&self.config, &agent_cfg)?;
        let tools = build_tool_registry(
            &agent_cfg.tools,
            agent_id,
            ws,
            self.tmux.clone(),
        );

        let agent = Agent::new(
            agent_id.to_string(),
            agent_cfg,
            inbox_rx,
            self.route_tx.clone(),
            self.ui_tx.clone(),
            prov,
            self.store.clone(),
            tools,
        );

        let agent_id_owned = agent_id.to_string();
        tokio::spawn(async move {
            if let Err(e) = agent.run().await {
                tracing::error!(agent = %agent_id_owned, error = %e, "dynamic agent exited with error");
            }
        });

        tracing::info!(agent = %agent_id, "spawned dynamic agent");
        Ok(inbox_tx)
    }
}

// ── RuntimeHandle ───────────────────────────────────────────────

pub struct RuntimeHandle {
    route_tx: mpsc::Sender<Envelope>,
    ui_tx: broadcast::Sender<UiEvent>,
    tmux: TmuxManager,
    pub agent_tmux_targets: HashMap<String, String>,
}

impl RuntimeHandle {
    pub fn try_send_user_instruction(
        &self,
        session_id: &str,
        thread_id: &str,
        target_agent: &str,
        content: String,
    ) -> Result<()> {
        use crate::runtime::bus::{MessageKind, Payload};
        let env = Envelope::new(
            session_id,
            thread_id,
            "user",
            target_agent,
            MessageKind::UserInstruction,
            Payload::text(content),
        );
        self.route_tx
            .try_send(env)
            .map_err(|e| anyhow::anyhow!("failed to enqueue user instruction: {}", e))?;
        Ok(())
    }

    pub async fn send_user_instruction(
        &self,
        session_id: &str,
        thread_id: &str,
        target_agent: &str,
        content: String,
    ) -> Result<()> {
        use crate::runtime::bus::{MessageKind, Payload};
        let env = Envelope::new(
            session_id,
            thread_id,
            "user",
            target_agent,
            MessageKind::UserInstruction,
            Payload::text(content),
        );
        self.route_tx
            .send(env)
            .await
            .map_err(|e| anyhow::anyhow!("failed to send user instruction: {}", e))?;
        Ok(())
    }

    pub fn subscribe_ui(&self) -> broadcast::Receiver<UiEvent> {
        self.ui_tx.subscribe()
    }

    pub async fn capture_agent_tmux(&self, agent_id: &str, lines: i32) -> Result<String> {
        self.tmux.capture_window(agent_id, lines).await
    }

    pub async fn tmux_window_active(&self, agent_id: &str) -> Result<bool> {
        self.tmux.window_exists(agent_id).await
    }

    pub async fn open_agent_tmux_window(&self, agent_id: &str) -> Result<()> {
        self.tmux.switch_to_window(agent_id).await
    }

    pub async fn kill_agent_tmux_window(&self, agent_id: &str) -> Result<()> {
        self.tmux.kill_window(agent_id).await
    }
}

// ── start_runtime ───────────────────────────────────────────────

pub async fn start_runtime(config: &AppConfig, store: Arc<Store>) -> Result<RuntimeHandle> {
    let (ui_tx, _) = broadcast::channel(8192);
    let (route_tx, route_rx) = mpsc::channel::<Envelope>(1024);

    // jj + tmux setup
    let project_root = config.project_root.clone();
    let jj = JjWorkspaceManager::new(project_root.clone());
    jj.ensure_jj_repo().await?;
    let tmux = TmuxManager::new("agent-x");
    tmux.ensure_session().await?;

    let mut router = Router::new(ui_tx.clone());
    let mut agent_tmux_targets = HashMap::new();

    // Load shared docs and codebase index once.
    let shared_docs = load_shared_docs(&project_root)?;
    let codebase_index = generate_codebase_index(&project_root);
    tracing::info!(
        shared_docs_len = shared_docs.len(),
        index_len = codebase_index.len(),
        project_agents = config.project_agents.len(),
        "loaded shared context"
    );

    // ── Boot static agents (planner, reviewer) ───────────────────
    for (agent_id, agent_cfg) in &config.static_agents {
        let agent_id_owned = agent_id.clone();
        let mut agent_cfg_owned = agent_cfg.clone();

        // Enrich system prompt.
        if !shared_docs.is_empty() {
            agent_cfg_owned.system_prompt =
                format!("{}\n\n{}", agent_cfg_owned.system_prompt, shared_docs);
        }
        if !codebase_index.is_empty() {
            agent_cfg_owned.system_prompt =
                format!("{}\n\n{}", agent_cfg_owned.system_prompt, codebase_index);
        }
        let docs_prompt = load_agent_docs_prompt(&project_root, &agent_id_owned)?;
        let rules_prompt = render_cardinal_rules(&agent_cfg_owned.cardinal_rules);
        if !docs_prompt.is_empty() {
            agent_cfg_owned.system_prompt =
                format!("{}\n\n{}", agent_cfg_owned.system_prompt, docs_prompt);
        }
        if !rules_prompt.is_empty() {
            agent_cfg_owned.system_prompt =
                format!("{}\n\n{}", agent_cfg_owned.system_prompt, rules_prompt);
        }

        // Inject list of available project agents into planner/reviewer prompts.
        let agent_roster = build_agent_roster_prompt(config);
        if !agent_roster.is_empty() {
            agent_cfg_owned.system_prompt =
                format!("{}\n\n{}", agent_cfg_owned.system_prompt, agent_roster);
        }

        let ws = jj.create_workspace(&agent_id_owned).await?;
        let _ = tmux
            .ensure_window(&agent_id_owned, ws.to_str().unwrap_or("."))
            .await?;
        agent_tmux_targets.insert(
            agent_id_owned.clone(),
            format!("agent-x:{}", agent_id_owned),
        );

        let (inbox_tx, inbox_rx) = mpsc::channel::<Envelope>(256);
        router.register(agent_id_owned.clone(), inbox_tx);

        let prov = provider::build_provider(config, &agent_cfg_owned)?;
        let tools = build_tool_registry(
            &agent_cfg_owned.tools,
            &agent_id_owned,
            ws,
            tmux.clone(),
        );

        let agent = Agent::new(
            agent_id_owned.clone(),
            agent_cfg_owned,
            inbox_rx,
            route_tx.clone(),
            ui_tx.clone(),
            prov,
            store.clone(),
            tools,
        );

        tokio::spawn(async move {
            if let Err(e) = agent.run().await {
                tracing::error!(agent = %agent_id_owned, error = %e, "agent task exited with error");
            }
        });
    }

    // ── Create the AgentSpawner for dynamic agents ───────────────
    let spawner = Arc::new(AgentSpawner {
        config: config.clone(),
        store: store.clone(),
        jj,
        tmux: tmux.clone(),
        route_tx: route_tx.clone(),
        ui_tx: ui_tx.clone(),
        shared_docs,
        codebase_index,
    });

    // Give the router the spawner so it can spawn on demand.
    router.set_spawner(spawner);

    // ── Start the routing loop ───────────────────────────────────
    tokio::spawn(async move {
        route_loop(route_rx, router).await;
    });

    Ok(RuntimeHandle {
        route_tx,
        ui_tx,
        tmux,
        agent_tmux_targets,
    })
}

async fn route_loop(mut route_rx: mpsc::Receiver<Envelope>, mut router: Router) {
    while let Some(env) = route_rx.recv().await {
        if let Err(e) = router.route(env).await {
            tracing::error!(error = %e, "router failed to route envelope");
        }
    }
}

// ── Build agent roster prompt ───────────────────────────────────
// Tells planner/reviewer what dynamic agents are available.

fn build_agent_roster_prompt(config: &AppConfig) -> String {
    if config.project_agents.is_empty() {
        return String::new();
    }

    let mut out = String::from("# Available Project Agents\n\n");
    out.push_str("These specialist agents are spawned on demand when you call them.\n\n");
    out.push_str("| Agent | Mode | Tier | Description |\n");
    out.push_str("|-------|------|------|-------------|\n");

    let mut sorted: Vec<_> = config.project_agents.iter().collect();
    sorted.sort_by_key(|(id, _)| id.as_str());

    for (id, def) in sorted {
        out.push_str(&format!(
            "| `{}` | {:?} | {:?} | {} |\n",
            id, def.mode, def.tier, def.description
        ));
    }

    out
}

// ── Tool registry builder ───────────────────────────────────────

fn build_tool_registry(
    allowed_names: &[String],
    agent_id: &str,
    workspace_root: std::path::PathBuf,
    tmux: TmuxManager,
) -> HashMap<String, Arc<dyn Tool>> {
    let mut map: HashMap<String, Arc<dyn Tool>> = HashMap::new();

    for name in allowed_names {
        let tool: Option<Arc<dyn Tool>> = match name.as_str() {
            "read_file" => Some(Arc::new(ReadFileTool::new(workspace_root.clone()))),
            "write_file" => Some(Arc::new(WriteFileTool::new(workspace_root.clone()))),
            "patch_file" => Some(Arc::new(PatchFileTool::new(workspace_root.clone()))),
            "glob" => Some(Arc::new(GlobTool::new(workspace_root.clone()))),
            "grep" => Some(Arc::new(GrepTool::new(workspace_root.clone()))),
            "rust_list_symbols" => {
                Some(Arc::new(RustListSymbolsTool::new(workspace_root.clone(), None)))
            }
            "rust_replace_block" => {
                Some(Arc::new(RustReplaceBlockTool::new(workspace_root.clone(), None)))
            }
            "rust_insert_after_block" => Some(Arc::new(RustInsertAfterBlockTool::new(
                workspace_root.clone(),
                None,
            ))),
            "rust_validate_file" => {
                Some(Arc::new(RustValidateFileTool::new(workspace_root.clone(), None)))
            }
            "shell" => Some(Arc::new(ShellTool::new(
                workspace_root.clone(),
                agent_id.to_string(),
                tmux.clone(),
            ))),
            _ => None,
        };

        if let Some(tool) = tool {
            map.insert(name.clone(), tool);
        }
    }

    map
}

// ── Helpers ─────────────────────────────────────────────────────

fn load_md_files_from_dir(dir: &Path, heading: &str) -> Result<String> {
    if !dir.exists() {
        return Ok(String::new());
    }

    let mut sections: Vec<(String, String)> = Vec::new();
    for entry in std::fs::read_dir(dir)? {
        let entry = entry?;
        if !entry.file_type()?.is_file() {
            continue;
        }
        let path = entry.path();
        if path.extension().and_then(|e| e.to_str()) != Some("md") {
            continue;
        }

        let name = path
            .file_name()
            .and_then(|n| n.to_str())
            .unwrap_or("doc.md")
            .to_string();
        let content = std::fs::read_to_string(&path)?;
        sections.push((name, content));
    }

    sections.sort_by(|a, b| a.0.cmp(&b.0));
    if sections.is_empty() {
        return Ok(String::new());
    }

    let mut out = format!("# {}\n", heading);
    for (name, content) in sections {
        out.push_str("\n## ");
        out.push_str(&name);
        out.push('\n');
        out.push_str(content.trim());
        out.push('\n');
    }

    Ok(out)
}

fn load_agent_docs_prompt(project_root: &Path, agent_id: &str) -> Result<String> {
    load_md_files_from_dir(
        &project_root.join("agents").join(agent_id),
        "Agent Documentation",
    )
}

fn load_shared_docs(project_root: &Path) -> Result<String> {
    load_md_files_from_dir(
        &project_root.join("agents").join("_shared"),
        "Shared Skills",
    )
}

/// Walk the project directory and build a directory-level codebase index.
fn generate_codebase_index(project_root: &Path) -> String {
    let mut out = String::from("# Codebase Index\n\n");
    out.push_str(&format!(
        "Project root: `{}`\n\n",
        project_root.display()
    ));

    let skip_dirs: &[&str] = &[
        ".git",
        ".jj",
        "target",
        "node_modules",
        ".agent_x",
        "__pycache__",
        ".vscode",
        ".idea",
    ];

    let mut tree = Vec::new();
    walk_dir_tree(project_root, project_root, 0, 3, skip_dirs, &mut tree);

    out.push_str("```\n");
    for line in &tree {
        out.push_str(line);
        out.push('\n');
    }
    out.push_str("```\n");

    // Add Cargo.toml summary if present.
    let cargo_toml = project_root.join("Cargo.toml");
    if cargo_toml.exists() {
        if let Ok(content) = std::fs::read_to_string(&cargo_toml) {
            out.push_str("\n## Cargo.toml Summary\n\n");
            let mut in_deps = false;
            let mut dep_lines = Vec::new();
            for line in content.lines() {
                if line.starts_with("name") || line.starts_with("version") {
                    out.push_str(&format!("- {}\n", line.trim()));
                }
                if line.starts_with("[dependencies]") {
                    in_deps = true;
                    continue;
                }
                if line.starts_with('[') && in_deps {
                    in_deps = false;
                }
                if in_deps && !line.trim().is_empty() && !line.starts_with('#') {
                    if let Some(name) = line.split('=').next() {
                        dep_lines.push(name.trim().to_string());
                    }
                }
            }
            if !dep_lines.is_empty() {
                out.push_str(&format!(
                    "- Key dependencies: {}\n",
                    dep_lines.join(", ")
                ));
            }
        }
    }

    out
}

fn walk_dir_tree(
    root: &Path,
    dir: &Path,
    depth: usize,
    max_depth: usize,
    skip_dirs: &[&str],
    output: &mut Vec<String>,
) {
    if depth > max_depth {
        return;
    }

    let mut entries: Vec<_> = match std::fs::read_dir(dir) {
        Ok(rd) => rd.filter_map(|e| e.ok()).collect(),
        Err(_) => return,
    };
    entries.sort_by_key(|e| e.file_name());

    let indent = "  ".repeat(depth);

    let mut file_count = 0;
    let mut file_names: Vec<String> = Vec::new();
    let mut subdirs: Vec<std::fs::DirEntry> = Vec::new();

    for entry in entries {
        let name = entry.file_name().to_string_lossy().to_string();
        if name.starts_with('.') && depth == 0 && name != ".env.example" {
            continue;
        }

        let ft = match entry.file_type() {
            Ok(ft) => ft,
            Err(_) => continue,
        };

        if ft.is_dir() {
            if skip_dirs.contains(&name.as_str()) {
                continue;
            }
            subdirs.push(entry);
        } else if ft.is_file() {
            file_count += 1;
            file_names.push(name);
        }
    }

    if file_count <= 8 {
        for name in &file_names {
            output.push(format!("{}{}", indent, name));
        }
    } else {
        let mut by_ext: HashMap<String, usize> = HashMap::new();
        for name in &file_names {
            let ext = name
                .rsplit('.')
                .next()
                .unwrap_or("other")
                .to_string();
            *by_ext.entry(ext).or_default() += 1;
        }
        let summary: Vec<String> = by_ext
            .iter()
            .map(|(ext, count)| format!("{} .{}", count, ext))
            .collect();
        output.push(format!(
            "{}({} files: {})",
            indent,
            file_count,
            summary.join(", ")
        ));
    }

    for sub in subdirs {
        let name = sub.file_name().to_string_lossy().to_string();
        output.push(format!("{}{}/", indent, name));
        walk_dir_tree(root, &sub.path(), depth + 1, max_depth, skip_dirs, output);
    }
}

fn render_cardinal_rules(rules: &[String]) -> String {
    if rules.is_empty() {
        return String::new();
    }
    let mut out = String::from("# Cardinal Rules\n");
    for rule in rules {
        out.push_str("- ");
        out.push_str(rule);
        out.push('\n');
    }
    out
}
