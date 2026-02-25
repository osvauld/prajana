pub mod anthropic;
pub mod openai;

use anyhow::Result;
use async_trait::async_trait;
use std::sync::Arc;
use tokio::sync::mpsc;

use crate::agent::ConversationMessage;
use crate::config::{AgentConfig, AppConfig, ProviderKind};

/// Trait for LLM providers. Each provider converts our internal
/// conversation format to the provider's API format.
#[async_trait]
pub trait ModelProvider: Send + Sync {
    /// Send the conversation and get a full response.
    /// If token_tx is provided, providers should stream partial tokens to it.
    async fn chat(
        &self,
        conversation: &[ConversationMessage],
        config: &AgentConfig,
        token_tx: Option<mpsc::UnboundedSender<String>>,
    ) -> Result<String>;

    /// Provider name for display/logging.
    fn name(&self) -> &str;
}

pub fn build_provider(
    app_cfg: &AppConfig,
    agent_cfg: &AgentConfig,
) -> Result<Arc<dyn ModelProvider>> {
    let provider_cfg = app_cfg
        .providers
        .get(&agent_cfg.provider)
        .ok_or_else(|| anyhow::anyhow!("missing provider config: {}", agent_cfg.provider))?;

    let api_key = std::env::var(&provider_cfg.api_key_env).map_err(|_| {
        anyhow::anyhow!(
            "missing env var for provider key: {}",
            provider_cfg.api_key_env
        )
    })?;
    if api_key.trim().is_empty() {
        anyhow::bail!("empty API key in env var: {}", provider_cfg.api_key_env);
    }
    let provider: Arc<dyn ModelProvider> = match provider_cfg.kind {
        ProviderKind::Anthropic => Arc::new(anthropic::AnthropicProvider::new(
            api_key,
            provider_cfg.base_url.clone(),
        )),
        ProviderKind::OpenAI => Arc::new(openai::OpenAIProvider::new(
            api_key,
            provider_cfg.base_url.clone(),
        )),
    };

    Ok(provider)
}
