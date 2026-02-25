pub mod highlight;
pub mod markdown;
pub mod message;
pub mod panels;
pub mod theme;

use anyhow::Result;
use crossterm::event::{
    self, Event, KeyCode, KeyEventKind, KeyModifiers, MouseButton, MouseEvent, MouseEventKind,
};
use crossterm::terminal::{disable_raw_mode, enable_raw_mode};
use ratatui::backend::CrosstermBackend;
use ratatui::layout::{Constraint, Direction, Layout};
use ratatui::Terminal;
use std::collections::HashMap;
use std::io;
use std::sync::Arc;
use std::time::Duration;
use tokio::sync::broadcast::error::TryRecvError;
use uuid::Uuid;

use crate::config::AppConfig;
use crate::runtime::bus::{AgentStatus, UiEvent};
use crate::runtime::{self, RuntimeHandle};
use crate::storage::Store;

use self::highlight::Highlighter;
use self::message::ChatMessage;
use self::panels::agents::{AgentEntry, AgentsPanel};
use self::panels::conversation::ConversationPanel;
use self::panels::input::InputPanel;
use self::panels::status::{NotificationLevel, StatusBar};
use self::theme::Theme;

#[derive(Clone)]
struct PendingRequest {
    id: String,
    message_id: String,
    from: String,
    to: String,
    thread_id: String,
    resolved: bool,
}

// ── Focus system ────────────────────────────────────────────────

#[derive(Clone, Copy, PartialEq, Eq)]
enum FocusTarget {
    Agents,
    Conversation,
    Input,
}

const FOCUS_ORDER: &[FocusTarget] = &[
    FocusTarget::Input,
    FocusTarget::Conversation,
    FocusTarget::Agents,
];

// ── App ─────────────────────────────────────────────────────────

pub struct App {
    config: AppConfig,
    store: Arc<Store>,
    runtime: RuntimeHandle,
    ui_rx: tokio::sync::broadcast::Receiver<UiEvent>,
    should_quit: bool,

    // Panels
    agents_panel: AgentsPanel,
    conversation: ConversationPanel,
    input_panel: InputPanel,
    status_bar: StatusBar,
    clipboard: Option<arboard::Clipboard>,

    // State
    theme: Theme,
    highlighter: Highlighter,
    focus: FocusTarget,
    sessions: Vec<String>,
    active_session: usize,
    pending_requests: Vec<PendingRequest>,
    reply_thread_id: Option<String>,
    reply_request_id: Option<String>,
    active_threads_by_agent: HashMap<String, String>,
}

impl App {
    pub async fn new(config: AppConfig, store: Arc<Store>) -> Result<Self> {
        let runtime = runtime::start_runtime(&config, store.clone()).await?;
        let ui_rx = runtime.subscribe_ui();
        let mut sessions = store.list_sessions().unwrap_or_default();
        if sessions.is_empty() {
            sessions.push("default".to_string());
        }

        // Build agent entries
        let mut entries: Vec<AgentEntry> = config
            .static_agents
            .iter()
            .map(|(id, agent)| AgentEntry {
                id: id.clone(),
                role: format!("{:?}", agent.role),
                status: AgentStatus::Idle,
                tmux_active: false,
            })
            .collect();

        for (id, def) in &config.project_agents {
            entries.push(AgentEntry {
                id: id.clone(),
                role: format!("{:?}", def.mode),
                status: AgentStatus::Idle,
                tmux_active: false,
            });
        }
        entries.sort_by(|a, b| a.id.cmp(&b.id));

        for entry in &mut entries {
            entry.tmux_active = runtime.tmux_window_active(&entry.id).await.unwrap_or(false);
        }

        let theme = Theme::default().with_agent_colors(&config.ui.theme.agent_colors);

        let mut agents_panel = AgentsPanel::new(entries);
        agents_panel.focused = false;

        let mut conversation = ConversationPanel::new();
        conversation.focused = false;

        let mut input_panel = InputPanel::new();
        input_panel.focused = true;

        // Set initial target agent
        if let Some(agent_id) = agents_panel.selected_agent_id() {
            input_panel.set_target_agent(agent_id);
        }

        let status_bar = StatusBar::new();
        let clipboard = arboard::Clipboard::new().ok();

        Ok(Self {
            config,
            store,
            runtime,
            ui_rx,
            should_quit: false,
            agents_panel,
            conversation,
            input_panel,
            status_bar,
            clipboard,
            theme,
            highlighter: Highlighter::new(),
            focus: FocusTarget::Input,
            sessions,
            active_session: 0,
            pending_requests: Vec::new(),
            reply_thread_id: None,
            reply_request_id: None,
            active_threads_by_agent: HashMap::new(),
        })
    }

    pub async fn run(&mut self) -> Result<()> {
        enable_raw_mode()?;
        let mut stdout = io::stdout();
        crossterm::execute!(
            stdout,
            crossterm::terminal::EnterAlternateScreen,
            crossterm::event::EnableMouseCapture
        )?;
        let backend = CrosstermBackend::new(stdout);
        let mut terminal = Terminal::new(backend)?;

        let res = self.event_loop(&mut terminal).await;

        disable_raw_mode()?;
        crossterm::execute!(
            terminal.backend_mut(),
            crossterm::terminal::LeaveAlternateScreen,
            crossterm::event::DisableMouseCapture
        )?;
        terminal.show_cursor()?;

        res
    }

    async fn event_loop(
        &mut self,
        terminal: &mut Terminal<CrosstermBackend<io::Stdout>>,
    ) -> Result<()> {
        while !self.should_quit {
            // Drain UI events
            loop {
                match self.ui_rx.try_recv() {
                    Ok(evt) => self.apply_ui_event(evt),
                    Err(TryRecvError::Lagged(_)) => continue,
                    Err(TryRecvError::Empty) => break,
                    Err(TryRecvError::Closed) => break,
                }
            }

            self.status_bar.tick();

            terminal.draw(|f| self.draw(f))?;

            if event::poll(Duration::from_millis(30))? {
                match event::read()? {
                    Event::Key(key) if key.kind == KeyEventKind::Press => {
                        self.handle_key(key.code, key.modifiers).await?;
                    }
                    Event::Mouse(mouse) => {
                        self.handle_mouse(mouse).await?;
                    }
                    _ => {}
                }
            }
        }

        Ok(())
    }

    // ── Drawing ─────────────────────────────────────────────────

    fn draw(&mut self, frame: &mut ratatui::Frame) {
        let root = Layout::default()
            .direction(Direction::Vertical)
            .constraints([
                Constraint::Min(6),       // body
                Constraint::Length(4),     // input
                Constraint::Length(1),     // status bar
            ])
            .split(frame.area());

        let body = Layout::default()
            .direction(Direction::Horizontal)
            .constraints([
                Constraint::Length(22),    // agent list
                Constraint::Min(40),      // conversation
            ])
            .split(root[0]);

        self.agents_panel.draw(frame, body[0], &self.theme);
        self.conversation
            .draw(frame, body[1], &self.theme, &self.highlighter);
        self.input_panel.draw(frame, root[1], &self.theme);
        self.status_bar.draw(frame, root[2], &self.theme);
    }

    // ── Input handling ──────────────────────────────────────────

    async fn handle_key(&mut self, code: KeyCode, modifiers: KeyModifiers) -> Result<()> {
        // Global shortcuts
        match (code, modifiers) {
            (KeyCode::Char('c'), KeyModifiers::CONTROL) => {
                self.should_quit = true;
                return Ok(());
            }
            (KeyCode::Tab, KeyModifiers::NONE) => {
                if self.focus == FocusTarget::Input && self.input_panel.has_mention_suggestions() {
                    self.input_panel.apply_active_mention();
                    let ids: Vec<String> = self
                        .agents_panel
                        .entries
                        .iter()
                        .map(|e| e.id.clone())
                        .collect();
                    self.input_panel.refresh_mentions(&ids);
                    return Ok(());
                }
                self.cycle_focus();
                return Ok(());
            }
            (KeyCode::BackTab, KeyModifiers::SHIFT) => {
                self.cycle_focus_back();
                return Ok(());
            }
            _ => {}
        }

        // Panel-specific handling
        match self.focus {
            FocusTarget::Input => self.handle_input_key(code, modifiers).await?,
            FocusTarget::Conversation => self.handle_conversation_key(code, modifiers),
            FocusTarget::Agents => self.handle_agents_key(code, modifiers),
        }

        Ok(())
    }

    async fn handle_input_key(&mut self, code: KeyCode, modifiers: KeyModifiers) -> Result<()> {
        match (code, modifiers) {
            (KeyCode::Enter, KeyModifiers::NONE) => {
                if !self.input_panel.is_empty() {
                    self.send_message().await;
                }
            }
            (KeyCode::Tab, KeyModifiers::SHIFT) => {
                self.input_panel.cycle_mention_next();
            }
            _ => {
                // Forward to tui-textarea
                let input_event = Event::Key(crossterm::event::KeyEvent::new(code, modifiers));
                self.input_panel.textarea.input(input_event);
                let ids: Vec<String> = self
                    .agents_panel
                    .entries
                    .iter()
                    .map(|e| e.id.clone())
                    .collect();
                self.input_panel.refresh_mentions(&ids);
            }
        }
        Ok(())
    }

    fn handle_conversation_key(&mut self, code: KeyCode, _modifiers: KeyModifiers) {
        match code {
            KeyCode::Up | KeyCode::Char('k') => self.conversation.scroll_up(3),
            KeyCode::Down | KeyCode::Char('j') => self.conversation.scroll_down(3),
            KeyCode::PageUp => self.conversation.scroll_up(20),
            KeyCode::PageDown => self.conversation.scroll_down(20),
            KeyCode::Home | KeyCode::Char('g') => {
                self.conversation.scroll_offset = u16::MAX; // scroll to top
            }
            KeyCode::End | KeyCode::Char('G') => self.conversation.scroll_to_bottom(),
            KeyCode::Char('y') => {
                if let Some(last) = self.conversation.messages.last() {
                    self.copy_to_clipboard(last.content.clone());
                }
            }
            KeyCode::Char('1') => self.conversation.set_filter_all(),
            KeyCode::Char('2') => {
                if let Some(agent) = self.agents_panel.selected_agent_id() {
                    self.conversation.set_filter_agent(agent.to_string());
                }
            }
            KeyCode::Char('3') => {
                if let Some(agent) = self.agents_panel.selected_agent_id() {
                    if let Some(thread_id) = self.conversation.latest_thread_for_agent(agent) {
                        self.conversation.set_filter_thread(thread_id);
                    }
                }
            }
            KeyCode::Char('r') => {
                if let Some(req) = self
                    .pending_requests
                    .iter()
                    .rev()
                    .find(|r| !r.resolved && r.to == "user")
                    .cloned()
                {
                    if let Some(idx) = self.agents_panel.entries.iter().position(|e| e.id == req.from)
                    {
                        self.agents_panel.select_index(idx);
                        self.sync_selected_agent();
                    }
                    self.reply_thread_id = Some(req.thread_id.clone());
                    self.reply_request_id = Some(req.id.clone());
                    self.status_bar.notify(
                        NotificationLevel::Info,
                        format!("Reply mode: @{} thread {}", req.from, req.thread_id),
                    );
                } else {
                    self.status_bar
                        .notify(NotificationLevel::Warn, "No pending user questions");
                }
            }
            _ => {}
        }
    }

    fn handle_agents_key(&mut self, code: KeyCode, _modifiers: KeyModifiers) {
        match code {
            KeyCode::Up | KeyCode::Char('k') => {
                self.agents_panel.select_prev();
                self.sync_selected_agent();
            }
            KeyCode::Down | KeyCode::Char('j') => {
                self.agents_panel.select_next();
                self.sync_selected_agent();
            }
            KeyCode::Char('t') => {
                // Capture tmux for selected agent
                // (handled async in event loop — skipped for now)
            }
            _ => {}
        }
    }

    async fn handle_mouse(&mut self, mouse: MouseEvent) -> Result<()> {
        let (w, h) = crossterm::terminal::size()?;
        let root = Layout::default()
            .direction(Direction::Vertical)
            .constraints([
                Constraint::Min(6),
                Constraint::Length(4),
                Constraint::Length(1),
            ])
            .split(ratatui::layout::Rect::new(0, 0, w, h));
        let body = Layout::default()
            .direction(Direction::Horizontal)
            .constraints([Constraint::Length(22), Constraint::Min(40)])
            .split(root[0]);
        let agents_area = body[0];
        let convo_area = body[1];

        let in_conversation = mouse.column >= convo_area.x
            && mouse.column < convo_area.x + convo_area.width
            && mouse.row >= convo_area.y
            && mouse.row < convo_area.y + convo_area.height;

        match mouse.kind {
            MouseEventKind::Down(MouseButton::Left) => {
                if let Some(action) =
                    self.agents_panel
                        .click_action(agents_area, mouse.column, mouse.row)
                {
                    use self::panels::agents::AgentClickAction;
                    match action {
                        AgentClickAction::Select(idx) => {
                            self.set_focus(FocusTarget::Agents);
                            self.agents_panel.select_index(idx);
                            self.sync_selected_agent();
                        }
                        AgentClickAction::ToggleTmuxSection => {
                            self.agents_panel.tmux_expanded = !self.agents_panel.tmux_expanded;
                        }
                        AgentClickAction::OpenTmux(idx) => {
                            self.agents_panel.select_index(idx);
                            self.sync_selected_agent();
                            if let Some(agent_id) =
                                self.agents_panel.selected_agent_id().map(|s| s.to_string())
                            {
                                if std::env::var("TMUX").is_err() {
                                    self.status_bar.notify(
                                        NotificationLevel::Warn,
                                        "Open tmux from within a tmux client (TMUX not set)",
                                    );
                                } else if let Err(e) = self.runtime.open_agent_tmux_window(&agent_id).await {
                                    self.status_bar.notify(
                                        NotificationLevel::Error,
                                        format!("Failed to open tmux window: {}", e),
                                    );
                                } else {
                                    self.agents_panel.set_tmux_active(&agent_id, true);
                                    self.status_bar.notify(
                                        NotificationLevel::Info,
                                        format!("Switched to tmux window @{}", agent_id),
                                    );
                                }
                            }
                        }
                        AgentClickAction::KillTmux(idx) => {
                            self.agents_panel.select_index(idx);
                            self.sync_selected_agent();
                            if let Some(agent_id) =
                                self.agents_panel.selected_agent_id().map(|s| s.to_string())
                            {
                                match self.runtime.kill_agent_tmux_window(&agent_id).await {
                                    Ok(_) => {
                                        self.agents_panel.set_tmux_active(&agent_id, false);
                                        self.status_bar.notify(
                                            NotificationLevel::Warn,
                                            format!("Killed tmux window @{}", agent_id),
                                        );
                                    }
                                    Err(e) => {
                                        self.status_bar.notify(
                                            NotificationLevel::Error,
                                            format!("Failed to kill tmux window: {}", e),
                                        );
                                    }
                                }
                            }
                        }
                    }
                }

                if in_conversation {
                    self.set_focus(FocusTarget::Conversation);
                    if let Some(text) = self.conversation.line_text_at(convo_area, mouse.row) {
                        self.copy_to_clipboard(text);
                    }
                }
            }
            MouseEventKind::ScrollUp => {
                if in_conversation {
                    self.set_focus(FocusTarget::Conversation);
                    self.conversation.scroll_up(8);
                }
            }
            MouseEventKind::ScrollDown => {
                if in_conversation {
                    self.set_focus(FocusTarget::Conversation);
                    self.conversation.scroll_down(8);
                }
            }
            _ => {}
        }
        Ok(())
    }

    fn copy_to_clipboard(&mut self, text: String) {
        if let Some(clipboard) = self.clipboard.as_mut() {
            match clipboard.set_text(text) {
                Ok(_) => self
                    .status_bar
                    .notify(NotificationLevel::Info, "Copied to clipboard"),
                Err(e) => self.status_bar.notify(
                    NotificationLevel::Warn,
                    format!("Clipboard unavailable: {}", e),
                ),
            }
        } else {
            self.status_bar
                .notify(NotificationLevel::Warn, "Clipboard not available");
        }
    }

    // ── Focus management ────────────────────────────────────────

    fn cycle_focus(&mut self) {
        let current_idx = FOCUS_ORDER.iter().position(|f| f == &self.focus).unwrap_or(0);
        let next_idx = (current_idx + 1) % FOCUS_ORDER.len();
        self.set_focus(FOCUS_ORDER[next_idx]);
    }

    fn cycle_focus_back(&mut self) {
        let current_idx = FOCUS_ORDER.iter().position(|f| f == &self.focus).unwrap_or(0);
        let prev_idx = if current_idx == 0 {
            FOCUS_ORDER.len() - 1
        } else {
            current_idx - 1
        };
        self.set_focus(FOCUS_ORDER[prev_idx]);
    }

    fn set_focus(&mut self, target: FocusTarget) {
        self.focus = target;
        self.agents_panel.focused = target == FocusTarget::Agents;
        self.conversation.focused = target == FocusTarget::Conversation;
        self.input_panel.focused = target == FocusTarget::Input;
    }

    // ── Actions ─────────────────────────────────────────────────

    async fn send_message(&mut self) {
        let raw_content = self.input_panel.take_input();
        if raw_content.trim().is_empty() {
            return;
        }

        let known_agents: Vec<String> = self
            .agents_panel
            .entries
            .iter()
            .map(|e| e.id.clone())
            .collect();

        let routed = route_user_input(&raw_content, &known_agents);
        let content = routed.content;
        if content.trim().is_empty() {
            self.status_bar.notify(
                NotificationLevel::Warn,
                "Message is empty after @agent routing",
            );
            return;
        }

        if let Some(pref_target) = &routed.target {
            if let Some(idx) = self
                .agents_panel
                .entries
                .iter()
                .position(|e| &e.id == pref_target)
            {
                self.agents_panel.select_index(idx);
                self.sync_selected_agent();
            }
        }

        let target = self
            .agents_panel
            .selected_agent_id()
            .unwrap_or("planner")
            .to_string();

        let session_id = self
            .sessions
            .get(self.active_session)
            .cloned()
            .unwrap_or_else(|| "default".to_string());
        let thread_id = self.reply_thread_id.take().unwrap_or_else(|| {
            if routed.force_new_thread {
                format!("thread-{}", Uuid::new_v4().simple())
            } else if let Some(existing) = self.active_threads_by_agent.get(&target) {
                existing.clone()
            } else {
                format!("thread-{}", Uuid::new_v4().simple())
            }
        });
        if let Some(req_id) = self.reply_request_id.take() {
            if let Some(req) = self.pending_requests.iter_mut().find(|r| r.id == req_id) {
                req.resolved = true;
                self.conversation
                    .annotate_message(&req.message_id, "[answered by user]");
            }
        }

        self.active_threads_by_agent
            .insert(target.clone(), thread_id.clone());

        if routed.force_new_thread {
            self.status_bar.notify(
                NotificationLevel::Info,
                format!("New conversation with @{} ({})", target, thread_id),
            );
        }

        // Send to runtime
        if let Err(e) = self.runtime.try_send_user_instruction(
            &session_id,
            &thread_id,
            &target,
            content,
        ) {
            self.status_bar
                .notify(NotificationLevel::Error, format!("send failed: {}", e));
        }
    }

    fn sync_selected_agent(&mut self) {
        if let Some(agent_id) = self.agents_panel.selected_agent_id() {
            self.input_panel.set_target_agent(agent_id);
            self.status_bar.selected_agent = agent_id.to_string();

            // Update status bar with current agent's status
            if let Some(entry) = self.agents_panel.entries.iter().find(|e| e.id == agent_id) {
                self.status_bar.agent_status = entry.status.clone();
            }

            let ids: Vec<String> = self
                .agents_panel
                .entries
                .iter()
                .map(|e| e.id.clone())
                .collect();
            self.input_panel.refresh_mentions(&ids);
        }
    }

    // ── Event handling ──────────────────────────────────────────

    fn apply_ui_event(&mut self, event: UiEvent) {
        match event {
            UiEvent::Message(env) => {
                // Finish any streaming for this agent
                self.conversation.finish_streaming(&env.from);

                 if env.from == "user" {
                    self.active_threads_by_agent
                        .insert(env.to.clone(), env.thread_id.clone());
                } else if env.to == "user" {
                    self.active_threads_by_agent
                        .insert(env.from.clone(), env.thread_id.clone());
                }

                let msg = ChatMessage::from_envelope(&env);
                self.conversation.push_message(msg);

                match env.kind {
                    crate::runtime::bus::MessageKind::TaskRequest
                    | crate::runtime::bus::MessageKind::Clarification => {
                        let req_id = env
                            .payload
                            .data
                            .as_ref()
                            .and_then(|d| d.get("request_id"))
                            .and_then(|v| v.as_str())
                            .map(|s| s.to_string())
                            .unwrap_or_else(|| env.id.clone());
                        self.pending_requests.push(PendingRequest {
                            id: req_id,
                            message_id: env.id.clone(),
                            from: env.from.clone(),
                            to: env.to.clone(),
                            thread_id: env.thread_id.clone(),
                            resolved: false,
                        });
                    }
                    crate::runtime::bus::MessageKind::TaskResult
                    | crate::runtime::bus::MessageKind::Done
                    | crate::runtime::bus::MessageKind::Error => {
                        let parent = env.parent_id.clone();
                        let request_id = env
                            .payload
                            .data
                            .as_ref()
                            .and_then(|d| d.get("request_id"))
                            .and_then(|v| v.as_str())
                            .map(|s| s.to_string());
                        if let Some(req) = self
                            .pending_requests
                            .iter_mut()
                            .find(|r| {
                                !r.resolved
                                    && (parent.as_ref().map(|p| r.id == *p).unwrap_or(false)
                                        || request_id
                                            .as_ref()
                                            .map(|id| r.id == *id)
                                            .unwrap_or(false))
                            })
                        {
                            req.resolved = true;
                            self.conversation.annotate_message(
                                &req.message_id,
                                &format!(
                                    "[answered by @{} -> @{} in thread {}]",
                                    env.from, env.to, env.thread_id
                                ),
                            );
                        }
                    }
                    _ => {}
                }

                if matches!(env.kind, crate::runtime::bus::MessageKind::Error) {
                    self.status_bar.notify(
                        NotificationLevel::Error,
                        format!("{} -> {}: {}", env.from, env.to, env.payload.content),
                    );
                } else if matches!(env.kind, crate::runtime::bus::MessageKind::ToolResult)
                    && env.payload.content.contains("success=false")
                {
                    self.status_bar.notify(
                        NotificationLevel::Warn,
                        format!("tool warning from {}", env.from),
                    );
                }
            }
            UiEvent::AgentStatus { agent_id, status } => {
                self.agents_panel.update_status(&agent_id, status.clone());
                self.agents_panel.set_tmux_active(&agent_id, true);

                // Update status bar if this is the selected agent
                if self
                    .agents_panel
                    .selected_agent_id()
                    .map(|s| s == agent_id)
                    .unwrap_or(false)
                {
                    self.status_bar.agent_status = status.clone();
                }

                if let AgentStatus::Error(e) = status {
                    self.status_bar.notify(
                        NotificationLevel::Error,
                        format!("@{}: {}", agent_id, e),
                    );
                }
            }
            UiEvent::StreamToken {
                agent_id, token, ..
            } => {
                if !token.is_empty() {
                    self.conversation.update_streaming(&agent_id, &token);
                }
            }
            UiEvent::TokenUsage { .. } => {}
            UiEvent::SessionChanged(_) => {}
        }

        self.status_bar.pending_questions =
            self.pending_requests.iter().filter(|r| !r.resolved).count();
    }
}

#[derive(Default)]
struct RoutedInput {
    target: Option<String>,
    content: String,
    force_new_thread: bool,
}

fn route_user_input(raw: &str, known_agents: &[String]) -> RoutedInput {
    let mut out = RoutedInput {
        target: None,
        content: raw.trim().to_string(),
        force_new_thread: false,
    };

    let mut s = out.content.as_str();
    if let Some(rest) = s.strip_prefix("/new ") {
        out.force_new_thread = true;
        s = rest.trim_start();
    }

    if let Some(rest) = s.strip_prefix('@') {
        let mut parts = rest.splitn(2, char::is_whitespace);
        if let Some(agent) = parts.next() {
            let agent = agent.trim();
            if !agent.is_empty() && known_agents.iter().any(|id| id == agent) {
                out.target = Some(agent.to_string());
                out.content = parts.next().unwrap_or("").trim_start().to_string();
            }
        }
    }

    out
}
