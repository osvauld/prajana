use anyhow::{Context, Result};
use async_trait::async_trait;
use reqwest::Client;
use serde::{Deserialize, Serialize};
use tokio::sync::mpsc;

use crate::agent::{ConversationMessage, Role};
use crate::config::AgentConfig;

use super::ModelProvider;

pub struct AnthropicProvider {
    client: Client,
    api_key: String,
    base_url: String,
}

impl AnthropicProvider {
    pub fn new(api_key: String, base_url: Option<String>) -> Self {
        Self {
            client: Client::new(),
            api_key,
            base_url: base_url.unwrap_or_else(|| "https://api.anthropic.com".to_string()),
        }
    }
}

#[derive(Serialize)]
struct AnthropicRequest {
    model: String,
    max_tokens: u32,
    #[serde(skip_serializing_if = "Option::is_none")]
    temperature: Option<f32>,
    system: String,
    messages: Vec<AnthropicMessage>,
}

#[derive(Serialize)]
struct AnthropicMessage {
    role: String,
    content: String,
}

#[derive(Deserialize)]
struct AnthropicResponse {
    content: Vec<ContentBlock>,
}

#[derive(Deserialize)]
struct ContentBlock {
    text: Option<String>,
}

#[async_trait]
impl ModelProvider for AnthropicProvider {
    async fn chat(
        &self,
        conversation: &[ConversationMessage],
        config: &AgentConfig,
        token_tx: Option<mpsc::UnboundedSender<String>>,
    ) -> Result<String> {
        // Extract system prompt (first message) and rest
        let system = conversation
            .iter()
            .find(|m| matches!(m.role, Role::System))
            .map(|m| m.content.clone())
            .unwrap_or_default();

        let messages: Vec<AnthropicMessage> = conversation
            .iter()
            .filter(|m| !matches!(m.role, Role::System))
            .map(|m| AnthropicMessage {
                role: match m.role {
                    Role::User | Role::ToolResult => "user".to_string(),
                    Role::Assistant => "assistant".to_string(),
                    Role::System => unreachable!(),
                },
                content: m.content.clone(),
            })
            .collect();

        let body = AnthropicRequest {
            model: config.model.clone(),
            max_tokens: config.max_tokens.unwrap_or(4096),
            temperature: config.temperature,
            system,
            messages,
        };

        let resp = self
            .client
            .post(format!("{}/v1/messages", self.base_url))
            .header("x-api-key", &self.api_key)
            .header("anthropic-version", "2023-06-01")
            .header("content-type", "application/json")
            .json(&body)
            .send()
            .await
            .context("anthropic API request failed")?;

        let status = resp.status();
        if !status.is_success() {
            let err_body = resp.text().await.unwrap_or_default();
            anyhow::bail!("Anthropic API error ({}): {}", status, err_body);
        }

        let result: AnthropicResponse = resp.json().await?;
        let text = result
            .content
            .into_iter()
            .filter_map(|b| b.text)
            .collect::<Vec<_>>()
            .join("");

        if let Some(tx) = token_tx {
            let _ = tx.send(text.clone());
        }

        Ok(text)
    }

    fn name(&self) -> &str {
        "anthropic"
    }
}
