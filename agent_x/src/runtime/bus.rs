use chrono::{DateTime, Utc};
use serde::{Deserialize, Serialize};
use uuid::Uuid;

/// Unique identifier for an agent
pub type AgentId = String;
/// Unique identifier for a session
pub type SessionId = String;
/// Unique identifier for a thread
pub type ThreadId = String;

/// Every message on the bus is wrapped in an Envelope.
#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Envelope {
    pub id: String,
    pub session_id: SessionId,
    pub thread_id: ThreadId,
    pub parent_id: Option<String>,
    pub from: AgentId,
    pub to: AgentId,
    pub kind: MessageKind,
    pub payload: Payload,
    pub timestamp: DateTime<Utc>,
    pub ttl: u8,
    pub hop_count: u8,
}

impl Envelope {
    pub fn new(
        session_id: &str,
        thread_id: &str,
        from: &str,
        to: &str,
        kind: MessageKind,
        payload: Payload,
    ) -> Self {
        Self {
            id: Uuid::new_v4().to_string(),
            session_id: session_id.to_string(),
            thread_id: thread_id.to_string(),
            parent_id: None,
            from: from.to_string(),
            to: to.to_string(),
            kind,
            payload,
            timestamp: Utc::now(),
            ttl: 20,
            hop_count: 0,
        }
    }

    pub fn with_parent(mut self, parent_id: &str) -> Self {
        self.parent_id = Some(parent_id.to_string());
        self
    }

    /// Increment hop count and check TTL.
    pub fn hop(&mut self) -> bool {
        self.hop_count += 1;
        self.hop_count <= self.ttl
    }
}

#[derive(Clone, Debug, Serialize, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum MessageKind {
    /// User sends a direct instruction
    UserInstruction,
    /// Agent asks another agent to perform a task
    TaskRequest,
    /// Result back from an invoked agent
    TaskResult,
    /// Agent asks for clarification
    Clarification,
    /// Indicates the agent is done with its work
    Done,
    /// Tool invocation request
    ToolCall,
    /// Tool invocation result
    ToolResult,
    /// Streaming content chunk
    StreamChunk,
    /// Error
    Error,
}

#[derive(Clone, Debug, Serialize, Deserialize)]
pub struct Payload {
    /// The main text content
    pub content: String,
    /// Optional structured data (tool args, patches, etc.)
    pub data: Option<serde_json::Value>,
}

impl Payload {
    pub fn text(content: impl Into<String>) -> Self {
        Self {
            content: content.into(),
            data: None,
        }
    }

    pub fn with_data(content: impl Into<String>, data: serde_json::Value) -> Self {
        Self {
            content: content.into(),
            data: Some(data),
        }
    }
}

/// Events broadcast to the UI for rendering.
#[derive(Clone, Debug)]
pub enum UiEvent {
    /// A new message arrived on the bus
    Message(Envelope),
    /// Agent status changed
    AgentStatus {
        agent_id: AgentId,
        status: AgentStatus,
    },
    /// Streaming token for an agent
    StreamToken {
        agent_id: AgentId,
        thread_id: ThreadId,
        token: String,
    },
    /// Token usage update
    TokenUsage {
        agent_id: AgentId,
        input_tokens: u64,
        output_tokens: u64,
    },
    /// Session switched
    SessionChanged(SessionId),
}

#[derive(Clone, Debug, Serialize, Deserialize, PartialEq)]
#[serde(rename_all = "lowercase")]
pub enum AgentStatus {
    Idle,
    Thinking,
    Streaming,
    WaitingForTool,
    Error(String),
}
