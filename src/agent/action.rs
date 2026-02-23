use serde::Deserialize;

#[derive(Clone, Debug, Deserialize)]
#[serde(tag = "action", rename_all = "snake_case")]
pub enum AgentAction {
    Respond {
        message: String,
    },
    ToolCall {
        tool: String,
        #[serde(default)]
        args: serde_json::Value,
    },
    CallAgent {
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
    },
    AskUser {
        question: String,
    },
    Done {
        #[serde(default)]
        message: Option<String>,
    },
}

#[derive(Clone, Debug, Deserialize)]
#[serde(rename_all = "snake_case")]
pub enum ThreadMode {
    New,
    Reuse,
}

#[derive(Debug, thiserror::Error)]
pub enum ActionParseError {
    #[error("agent output must be a single JSON object")]
    NotJsonObject,
    #[error("invalid agent action payload: {0}")]
    InvalidPayload(String),
    #[error("invalid agent action: {0}")]
    Validation(String),
}

pub fn parse_agent_action(raw: &str) -> Result<AgentAction, ActionParseError> {
    let trimmed = raw.trim();
    let candidate = if trimmed.starts_with('{') && trimmed.ends_with('}') {
        trimmed.to_string()
    } else if let Some(extracted) = extract_json_object(trimmed) {
        extracted
    } else {
        return Err(ActionParseError::NotJsonObject);
    };

    let action: AgentAction = match serde_json::from_str(&candidate) {
        Ok(v) => v,
        Err(primary_err) => {
            let value: serde_json::Value = json5::from_str(&candidate)
                .map_err(|_| ActionParseError::InvalidPayload(primary_err.to_string()))?;
            serde_json::from_value(value)
                .map_err(|e| ActionParseError::InvalidPayload(e.to_string()))?
        }
    };

    validate_action(&action)?;
    Ok(action)
}

fn extract_json_object(raw: &str) -> Option<String> {
    // Try fenced ```json ... ``` first.
    if let Some(start) = raw.find("```") {
        let rest = &raw[start + 3..];
        let after_lang = if let Some(pos) = rest.find('\n') {
            &rest[pos + 1..]
        } else {
            rest
        };
        if let Some(end) = after_lang.find("```") {
            let block = after_lang[..end].trim();
            if block.starts_with('{') && block.ends_with('}') {
                return Some(block.to_string());
            }
        }
    }

    // Fallback: first balanced {...} object.
    let mut in_str = false;
    let mut escaped = false;
    let mut depth = 0usize;
    let mut start_idx: Option<usize> = None;

    for (i, ch) in raw.char_indices() {
        if in_str {
            if escaped {
                escaped = false;
            } else if ch == '\\' {
                escaped = true;
            } else if ch == '"' {
                in_str = false;
            }
            continue;
        }

        match ch {
            '"' => in_str = true,
            '{' => {
                if depth == 0 {
                    start_idx = Some(i);
                }
                depth += 1;
            }
            '}' => {
                if depth == 0 {
                    continue;
                }
                depth -= 1;
                if depth == 0 {
                    if let Some(start) = start_idx {
                        return Some(raw[start..=i].to_string());
                    }
                }
            }
            _ => {}
        }
    }

    None
}

fn validate_action(action: &AgentAction) -> Result<(), ActionParseError> {
    match action {
        AgentAction::Respond { message } => {
            if message.trim().is_empty() {
                return Err(ActionParseError::Validation(
                    "respond.message cannot be empty".to_string(),
                ));
            }
        }
        AgentAction::ToolCall { tool, .. } => {
            if tool.trim().is_empty() {
                return Err(ActionParseError::Validation(
                    "tool_call.tool cannot be empty".to_string(),
                ));
            }
        }
        AgentAction::CallAgent {
            target,
            task,
            thread_id,
            request_id,
            ..
        } => {
            if target.trim().is_empty() {
                return Err(ActionParseError::Validation(
                    "call_agent.target cannot be empty".to_string(),
                ));
            }
            if task.trim().is_empty() {
                return Err(ActionParseError::Validation(
                    "call_agent.task cannot be empty".to_string(),
                ));
            }
            if let Some(id) = thread_id {
                if id.trim().is_empty() {
                    return Err(ActionParseError::Validation(
                        "call_agent.thread_id cannot be empty when provided".to_string(),
                    ));
                }
            }
            if let Some(id) = request_id {
                if id.trim().is_empty() {
                    return Err(ActionParseError::Validation(
                        "call_agent.request_id cannot be empty when provided".to_string(),
                    ));
                }
            }
        }
        AgentAction::Done { message } => {
            if matches!(message, Some(m) if m.trim().is_empty()) {
                return Err(ActionParseError::Validation(
                    "done.message cannot be empty when provided".to_string(),
                ));
            }
        }
        AgentAction::AskUser { question } => {
            if question.trim().is_empty() {
                return Err(ActionParseError::Validation(
                    "ask_user.question cannot be empty".to_string(),
                ));
            }
        }
    }

    Ok(())
}
