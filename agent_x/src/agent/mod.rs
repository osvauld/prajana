use anyhow::Result;
use loro::{ExportMode, LoroDoc};
use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{broadcast, mpsc};

mod action;

use crate::config::{AgentConfig, AgentMode};
use crate::provider::ModelProvider;
use crate::runtime::bus::*;
use crate::storage::Store;
use crate::tools::Tool;
use action::{parse_agent_action, ActionParseError, AgentAction, ThreadMode};

/// Conversation message stored per-agent in their Loro doc.
#[derive(Clone, Debug, serde::Serialize, serde::Deserialize)]
pub struct ConversationMessage {
    pub role: Role,
    pub content: String,
    pub timestamp: chrono::DateTime<chrono::Utc>,
    pub from_agent: Option<AgentId>,
}

#[derive(Clone, Debug, serde::Serialize, serde::Deserialize)]
#[serde(rename_all = "lowercase")]
pub enum Role {
    System,
    User,
    Assistant,
    ToolResult,
}

/// A live agent instance running as a tokio task.
pub struct Agent {
    pub id: AgentId,
    pub config: AgentConfig,
    pub conversation: Vec<ConversationMessage>,
    pub status: AgentStatus,
    inbox: mpsc::Receiver<Envelope>,
    router_tx: mpsc::Sender<Envelope>,
    ui_tx: broadcast::Sender<UiEvent>,
    provider: Arc<dyn ModelProvider>,
    store: Arc<Store>,
    docs: HashMap<String, LoroDoc>,
    tools: HashMap<String, Arc<dyn Tool>>,
}

impl Agent {
    pub fn new(
        id: AgentId,
        config: AgentConfig,
        inbox: mpsc::Receiver<Envelope>,
        router_tx: mpsc::Sender<Envelope>,
        ui_tx: broadcast::Sender<UiEvent>,
        provider: Arc<dyn ModelProvider>,
        store: Arc<Store>,
        tools: HashMap<String, Arc<dyn Tool>>,
    ) -> Self {
        let action_prompt = render_agent_action_contract(&config.tools, &config.can_invoke);
        let system_msg = ConversationMessage {
            role: Role::System,
            content: format!("{}\n\n{}", config.system_prompt, action_prompt),
            timestamp: chrono::Utc::now(),
            from_agent: None,
        };

        Self {
            id,
            config,
            conversation: vec![system_msg],
            status: AgentStatus::Idle,
            inbox,
            router_tx,
            ui_tx,
            provider,
            store,
            docs: HashMap::new(),
            tools,
        }
    }

    /// Main event loop for this agent.
    pub async fn run(mut self) -> Result<()> {
        tracing::info!(agent = %self.id, "agent started");

        while let Some(envelope) = self.inbox.recv().await {
            // Direct tool call interface:
            // /tool <name> <json>
            if envelope.payload.content.starts_with("/tool ") {
                self.handle_tool_invocation(envelope).await;
                continue;
            }

            self.append_crdt_line(
                &envelope.session_id,
                format!(
                    "{} -> {}: {}",
                    envelope.from, self.id, envelope.payload.content
                ),
            );

            // Add incoming message to our conversation
            self.conversation.push(ConversationMessage {
                role: Role::User,
                content: envelope.payload.content.clone(),
                timestamp: chrono::Utc::now(),
                from_agent: Some(envelope.from.clone()),
            });

            let max_turns = self.config.max_turns.unwrap_or(8).max(1);
            let mut finished = false;

            for turn in 0..max_turns {
                self.set_status(AgentStatus::Thinking);
                let response = match self.call_model_with_stream(&envelope.thread_id).await {
                    Ok(response) => response,
                    Err(e) => {
                        tracing::error!(agent = %self.id, error = %e, "model call failed");
                        self.set_status(AgentStatus::Error(e.to_string()));
                        break;
                    }
                };

                self.conversation.push(ConversationMessage {
                    role: Role::Assistant,
                    content: response.clone(),
                    timestamp: chrono::Utc::now(),
                    from_agent: None,
                });

                let action = match parse_agent_action(&response) {
                    Ok(action) => action,
                    Err(err) => {
                        if turn + 1 < max_turns {
                            self.conversation.push(ConversationMessage {
                                role: Role::User,
                                content: format!(
                                    "FORMAT ERROR: your previous output was invalid. Return exactly one strict JSON object only. Error: {}",
                                    err
                                ),
                                timestamp: chrono::Utc::now(),
                                from_agent: None,
                            });
                            continue;
                        }

                        self.emit_action_parse_error(&envelope, err, &response)
                            .await;
                        finished = true;
                        break;
                    }
                };

                let should_finish = self.execute_agent_action(&envelope, action).await;
                if should_finish {
                    finished = true;
                    break;
                }

                if turn + 1 == max_turns {
                    self.send_error_reply(
                        &envelope,
                        format!(
                            "agent '{}' reached max action turns ({}) without terminal action",
                            self.id, max_turns
                        ),
                    )
                    .await;
                    finished = true;
                }
            }

            if finished {
                self.set_status(AgentStatus::Idle);
            }
        }

        Ok(())
    }

    async fn call_model_with_stream(&mut self, thread_id: &str) -> Result<String> {
        let (token_tx, mut token_rx) = tokio::sync::mpsc::unbounded_channel::<String>();
        let ui_tx = self.ui_tx.clone();
        let stream_agent_id = self.id.clone();
        let stream_thread_id = thread_id.to_string();

        let stream_task = tokio::spawn(async move {
            while let Some(token) = token_rx.recv().await {
                let _ = ui_tx.send(UiEvent::StreamToken {
                    agent_id: stream_agent_id.clone(),
                    thread_id: stream_thread_id.clone(),
                    token,
                });
            }
        });

        self.set_status(AgentStatus::Streaming);
        let model_call = tokio::time::timeout(
            std::time::Duration::from_secs(90),
            self.provider
                .chat(&self.conversation, &self.config, Some(token_tx)),
        )
        .await;

        let _ = tokio::time::timeout(std::time::Duration::from_secs(1), stream_task).await;

        match model_call {
            Ok(Ok(response)) => Ok(response),
            Ok(Err(e)) => Err(e),
            Err(_) => Err(anyhow::anyhow!("model call timed out after 90s")),
        }
    }

    fn set_status(&mut self, status: AgentStatus) {
        self.status = status.clone();
        let _ = self.ui_tx.send(UiEvent::AgentStatus {
            agent_id: self.id.clone(),
            status,
        });
    }

    fn append_crdt_line(&mut self, session_id: &str, line: String) {
        let doc = self.docs.entry(session_id.to_string()).or_insert_with(|| {
            if let Ok(Some(bytes)) = self.store.load_conversation(session_id, &self.id) {
                if let Ok(doc) = LoroDoc::from_snapshot(&bytes) {
                    return doc;
                }
            }
            let doc = LoroDoc::new();
            let text = doc.get_text("conversation");
            let _ = text.push_str(&format!("system: {}\n", self.config.system_prompt));
            doc
        });

        let text = doc.get_text("conversation");
        let _ = text.push_str(&format!("{}\n", line));
        doc.commit();

        if let Ok(bytes) = doc.export(ExportMode::Snapshot) {
            let _ = self.store.save_conversation(session_id, &self.id, &bytes);
        }
    }

    async fn handle_tool_invocation(&mut self, envelope: Envelope) {
        self.set_status(AgentStatus::WaitingForTool);

        let rest = envelope.payload.content.trim_start_matches("/tool ").trim();
        let mut parts = rest.splitn(2, ' ');
        let tool_name = parts.next().unwrap_or_default().trim();
        let args_json = parts.next().unwrap_or("{}").trim();

        let args: serde_json::Value = match serde_json::from_str(args_json) {
            Ok(v) => v,
            Err(e) => {
                let err = Envelope::new(
                    &envelope.session_id,
                    &envelope.thread_id,
                    &self.id,
                    &envelope.from,
                    MessageKind::Error,
                    Payload::text(format!("invalid tool args JSON: {}", e)),
                )
                .with_parent(&envelope.id);
                let _ = self.router_tx.send(err).await;
                self.set_status(AgentStatus::Idle);
                return;
            }
        };

        self.execute_tool_action(&envelope, tool_name, args).await;
        self.set_status(AgentStatus::Idle);
    }

    async fn execute_agent_action(&mut self, envelope: &Envelope, action: AgentAction) -> bool {
        match action {
            AgentAction::Respond { message } => {
                let request_id = envelope
                    .payload
                    .data
                    .as_ref()
                    .and_then(|d| d.get("request_id"))
                    .and_then(|v| v.as_str())
                    .map(|s| s.to_string());
                let reply = Envelope::new(
                    &envelope.session_id,
                    &envelope.thread_id,
                    &self.id,
                    &envelope.from,
                    MessageKind::TaskResult,
                    Payload::with_data(
                        &message,
                        serde_json::json!({
                            "request_id": request_id,
                            "reply_to": envelope.id,
                        }),
                    ),
                )
                .with_parent(&envelope.id);
                let _ = self.router_tx.send(reply).await;
                self.append_crdt_line(
                    &envelope.session_id,
                    format!("{} -> {}: {}", self.id, envelope.from, message),
                );
                true
            }
            AgentAction::ToolCall { tool, args } => {
                self.execute_tool_action(envelope, &tool, args).await;
                false
            }
            AgentAction::CallAgent {
                target,
                task,
                thread_mode,
                thread_id,
                request_id,
                constraints,
                context,
            } => {
                let args = CallAgentToolArgs {
                    target,
                    task,
                    thread_mode,
                    thread_id,
                    request_id,
                    constraints,
                    context,
                };
                self.execute_call_agent_action(envelope, args).await;
                true
            }
            AgentAction::AskUser { question } => {
                let ask = Envelope::new(
                    &envelope.session_id,
                    &envelope.thread_id,
                    &self.id,
                    "user",
                    MessageKind::Clarification,
                    Payload::text(question),
                )
                .with_parent(&envelope.id);
                let _ = self.router_tx.send(ask).await;
                true
            }
            AgentAction::Done { message } => {
                let done_content = message.unwrap_or_else(|| "done".to_string());
                let request_id = envelope
                    .payload
                    .data
                    .as_ref()
                    .and_then(|d| d.get("request_id"))
                    .and_then(|v| v.as_str())
                    .map(|s| s.to_string());
                let done = Envelope::new(
                    &envelope.session_id,
                    &envelope.thread_id,
                    &self.id,
                    &envelope.from,
                    MessageKind::Done,
                    Payload::with_data(
                        done_content,
                        serde_json::json!({
                            "request_id": request_id,
                            "reply_to": envelope.id,
                        }),
                    ),
                )
                .with_parent(&envelope.id);
                let _ = self.router_tx.send(done).await;
                true
            }
        }
    }

    async fn execute_tool_action(
        &mut self,
        envelope: &Envelope,
        tool_name: &str,
        args: serde_json::Value,
    ) {
        if !self.config.tools.iter().any(|t| t == tool_name) {
            self.send_error_reply(
                envelope,
                format!(
                    "tool '{}' is not allowed for agent '{}'",
                    tool_name, self.id
                ),
            )
            .await;
            return;
        }

        if self.config.mode == AgentMode::Read
            && matches!(
                tool_name,
                "write_file" | "patch_file" | "rust_replace_block" | "rust_insert_after_block"
            )
        {
            self.send_error_reply(
                envelope,
                format!("agent '{}' is read-only; '{}' denied", self.id, tool_name),
            )
            .await;
            return;
        }

        if tool_name == "call_agent" {
            let parsed = match serde_json::from_value::<CallAgentToolArgs>(args) {
                Ok(v) => v,
                Err(e) => {
                    self.send_error_reply(envelope, format!("invalid call_agent args JSON: {}", e))
                        .await;
                    return;
                }
            };
            self.execute_call_agent_action(envelope, parsed).await;
            return;
        }

        let Some(tool) = self.tools.get(tool_name).cloned() else {
            self.send_error_reply(envelope, format!("tool '{}' not registered", tool_name))
                .await;
            return;
        };

        let result = tool.execute(args).await;
        let payload = match result {
            Ok(r) => Payload::text(format!("[{} success={}]\n{}", r.name, r.success, r.output)),
            Err(e) => Payload::text(format!("tool execution failed: {}", e)),
        };

        let reply = Envelope::new(
            &envelope.session_id,
            &envelope.thread_id,
            &self.id,
            &envelope.from,
            MessageKind::ToolResult,
            payload.clone(),
        )
        .with_parent(&envelope.id);
        let _ = self.router_tx.send(reply).await;

        self.conversation.push(ConversationMessage {
            role: Role::ToolResult,
            content: payload.content,
            timestamp: chrono::Utc::now(),
            from_agent: None,
        });
    }

    async fn execute_call_agent_action(&mut self, envelope: &Envelope, args: CallAgentToolArgs) {
        if !self.config.can_invoke.iter().any(|a| a == &args.target) {
            self.send_error_reply(
                envelope,
                format!(
                    "agent '{}' cannot invoke '{}' (blocked by can_invoke policy)",
                    self.id, args.target
                ),
            )
            .await;
            return;
        }

        let thread_mode_label = match args.thread_mode.clone() {
            ThreadMode::New => "new",
            ThreadMode::Reuse => "reuse",
        };

        let target_thread = match args.thread_mode {
            ThreadMode::New => args
                .thread_id
                .unwrap_or_else(|| format!("thread-{}", uuid::Uuid::new_v4().simple())),
            ThreadMode::Reuse => args.thread_id.unwrap_or_else(|| envelope.thread_id.clone()),
        };

        let request_id = args
            .request_id
            .clone()
            .unwrap_or_else(|| format!("req-{}", uuid::Uuid::new_v4().simple()));

        let from_id = self.id.clone();
        let target_id = args.target.clone();
        let delegated = Envelope::new(
            &envelope.session_id,
            &target_thread,
            &self.id,
            &args.target,
            MessageKind::TaskRequest,
            Payload::with_data(
                args.task.clone(),
                serde_json::json!({
                    "request_id": request_id,
                    "from": from_id,
                    "to": target_id,
                    "thread_id": target_thread,
                }),
            ),
        )
        .with_parent(&envelope.id);
        let _ = self.router_tx.send(delegated).await;

        let ack = Envelope::new(
            &envelope.session_id,
            &envelope.thread_id,
            &self.id,
            &envelope.from,
            MessageKind::TaskResult,
            Payload::text(format!(
                "[call_agent success=true]\nrequest_id={} invoked={} thread_mode={} thread_id={} constraints={} context={}",
                request_id,
                args.target,
                thread_mode_label,
                target_thread,
                args.constraints
                    .map(|v| v.to_string())
                    .unwrap_or_else(|| "null".to_string()),
                args.context
                    .map(|v| v.to_string())
                    .unwrap_or_else(|| "null".to_string())
            )),
        )
        .with_parent(&envelope.id);
        let _ = self.router_tx.send(ack).await;
    }

    async fn emit_action_parse_error(
        &mut self,
        envelope: &Envelope,
        err: ActionParseError,
        raw: &str,
    ) {
        let error_payload = serde_json::json!({
            "error": err.to_string(),
            "raw": raw,
        });

        let reply = Envelope::new(
            &envelope.session_id,
            &envelope.thread_id,
            &self.id,
            &envelope.from,
            MessageKind::Error,
            Payload::with_data(
                "invalid agent action output; expected strict JSON AgentAction payload",
                error_payload,
            ),
        )
        .with_parent(&envelope.id);
        let _ = self.router_tx.send(reply).await;
    }

    async fn send_error_reply(&mut self, envelope: &Envelope, message: String) {
        let err = Envelope::new(
            &envelope.session_id,
            &envelope.thread_id,
            &self.id,
            &envelope.from,
            MessageKind::Error,
            Payload::text(message),
        )
        .with_parent(&envelope.id);
        let _ = self.router_tx.send(err).await;
    }
}

#[derive(serde::Deserialize)]
struct CallAgentToolArgs {
    target: String,
    task: String,
    thread_mode: ThreadMode,
    #[serde(default)]
    thread_id: Option<String>,
    #[serde(default)]
    request_id: Option<String>,
    #[serde(default)]
    constraints: Option<serde_json::Value>,
    #[serde(default)]
    context: Option<serde_json::Value>,
}

fn render_agent_action_contract(allowed_tools: &[String], allowed_agents: &[String]) -> String {
    let tools = if allowed_tools.is_empty() {
        "none".to_string()
    } else {
        allowed_tools.join(", ")
    };
    let targets = if allowed_agents.is_empty() {
        "none".to_string()
    } else {
        allowed_agents.join(", ")
    };

    format!(
        "# Action Contract\nReturn exactly one JSON object with no surrounding text and no code fences.\nAllowed actions:\n1) {{\"action\":\"respond\",\"message\":\"...\"}}\n2) {{\"action\":\"tool_call\",\"tool\":\"<allowed-tool>\",\"args\":{{...}}}}\n3) {{\"action\":\"call_agent\",\"target\":\"<allowed-agent>\",\"task\":\"...\",\"thread_mode\":\"new|reuse\",\"thread_id\":\"optional\",\"request_id\":\"optional\",\"constraints\":{{...}},\"context\":{{...}}}}\n4) {{\"action\":\"ask_user\",\"question\":\"...\"}}\n5) {{\"action\":\"done\",\"message\":\"optional\"}}\nAllowed tools: {}\nAllowed call_agent targets: {}\nAny invalid format is rejected.",
        tools, targets
    )
}
