use anyhow::{Context, Result};
use async_trait::async_trait;
use eventsource_stream::Eventsource;
use futures::StreamExt;
use reqwest::Client;
use serde::{Deserialize, Serialize};
use serde_json::Value;
use tokio::sync::mpsc;

use crate::agent::{ConversationMessage, Role};
use crate::config::AgentConfig;

use super::ModelProvider;

pub struct OpenAIProvider {
    client: Client,
    api_key: String,
    base_url: String,
}

impl OpenAIProvider {
    pub fn new(api_key: String, base_url: Option<String>) -> Self {
        Self {
            client: Client::new(),
            api_key,
            base_url: base_url.unwrap_or_else(|| "https://api.openai.com".to_string()),
        }
    }

    fn chat_url(&self) -> String {
        let base = self.base_url.trim_end_matches('/');

        if base.ends_with("/chat/completions") {
            base.to_string()
        } else if base.ends_with("/v1")
            || base.ends_with("/api/paas/v4")
            || base.ends_with("/api/coding/paas/v4")
        {
            format!("{}/chat/completions", base)
        } else {
            format!("{}/v1/chat/completions", base)
        }
    }
}

#[derive(Serialize)]
struct OpenAIRequest {
    model: String,
    #[serde(skip_serializing_if = "Option::is_none")]
    temperature: Option<f32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    max_tokens: Option<u32>,
    #[serde(skip_serializing_if = "Option::is_none")]
    stream: Option<bool>,
    messages: Vec<OpenAIMessage>,
}

#[derive(Serialize)]
struct OpenAIMessage {
    role: String,
    content: String,
}

#[derive(Deserialize)]
struct OpenAIResponse {
    choices: Vec<Choice>,
}

#[derive(Deserialize)]
struct Choice {
    message: ChoiceMessage,
}

#[derive(Deserialize)]
struct ChoiceMessage {
    content: Option<String>,
}

#[async_trait]
impl ModelProvider for OpenAIProvider {
    async fn chat(
        &self,
        conversation: &[ConversationMessage],
        config: &AgentConfig,
        token_tx: Option<mpsc::UnboundedSender<String>>,
    ) -> Result<String> {
        let messages: Vec<OpenAIMessage> = conversation
            .iter()
            .map(|m| OpenAIMessage {
                role: match m.role {
                    Role::System => "system".to_string(),
                    Role::User | Role::ToolResult => "user".to_string(),
                    Role::Assistant => "assistant".to_string(),
                },
                content: m.content.clone(),
            })
            .collect();

        let body = OpenAIRequest {
            model: config.model.clone(),
            temperature: config.temperature,
            max_tokens: config.max_tokens,
            stream: Some(token_tx.is_some()),
            messages,
        };

        let resp = self
            .client
            .post(self.chat_url())
            .header("Authorization", format!("Bearer {}", self.api_key))
            .header("Content-Type", "application/json")
            .json(&body)
            .send()
            .await
            .context("OpenAI API request failed")?;

        let status = resp.status();
        if !status.is_success() {
            let err_body = resp.text().await.unwrap_or_default();
            anyhow::bail!("OpenAI API error ({}): {}", status, err_body);
        }

        if let Some(token_tx) = token_tx {
            let mut stream = resp.bytes_stream().eventsource();
            let mut full_text = String::new();
            let mut reasoning_text = String::new();

            while let Some(event) = stream.next().await {
                let event = event.context("failed to read streaming event")?;
                if event.data == "[DONE]" {
                    break;
                }

                let chunk: Value = serde_json::from_str(&event.data)
                    .context("failed to parse stream JSON chunk")?;

                if let Some(choice) = chunk
                    .get("choices")
                    .and_then(|v| v.as_array())
                    .and_then(|arr| arr.first())
                {
                    if let Some(delta) = choice.get("delta") {
                        // Common OpenAI-compatible shape: delta.content = "..."
                        if let Some(content) = delta.get("content").and_then(|v| v.as_str()) {
                            if !content.is_empty() {
                                full_text.push_str(content);
                                let _ = token_tx.send(content.to_string());
                            }
                        }

                        // Some providers emit reasoning stream separately
                        if config.thinking.unwrap_or(false) {
                            if let Some(reasoning) =
                                delta.get("reasoning_content").and_then(|v| v.as_str())
                            {
                                if !reasoning.is_empty() {
                                    reasoning_text.push_str(reasoning);
                                    let _ = token_tx.send(reasoning.to_string());
                                }
                            }
                        }

                        // Alternate shape: delta.content = [{"type":"text","text":"..."}]
                        if let Some(parts) = delta.get("content").and_then(|v| v.as_array()) {
                            for part in parts {
                                if let Some(text) = part.get("text").and_then(|v| v.as_str()) {
                                    if !text.is_empty() {
                                        full_text.push_str(text);
                                        let _ = token_tx.send(text.to_string());
                                    }
                                }
                            }
                        }
                    }

                    // Non-stream fallback chunk shape inside stream
                    if let Some(content) = choice
                        .get("message")
                        .and_then(|m| m.get("content"))
                        .and_then(|v| v.as_str())
                    {
                        if !content.is_empty() {
                            full_text.push_str(content);
                            let _ = token_tx.send(content.to_string());
                        }
                    }
                }
            }

            if full_text.is_empty() {
                Ok(reasoning_text)
            } else {
                Ok(full_text)
            }
        } else {
            let result: OpenAIResponse = resp.json().await?;
            let text = result
                .choices
                .into_iter()
                .next()
                .and_then(|c| c.message.content)
                .unwrap_or_default();

            Ok(text)
        }
    }

    fn name(&self) -> &str {
        "openai"
    }
}
