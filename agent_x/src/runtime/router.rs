use std::collections::HashMap;
use std::sync::Arc;
use tokio::sync::{broadcast, mpsc};
use tracing::{info, warn};

use super::bus::{AgentId, Envelope, UiEvent};
use super::service::AgentSpawner;

/// The Router holds a sender for each registered agent and
/// a broadcast channel for UI events.
pub struct Router {
    agents: HashMap<AgentId, mpsc::Sender<Envelope>>,
    ui_tx: broadcast::Sender<UiEvent>,
    spawner: Option<Arc<AgentSpawner>>,
}

impl Router {
    pub fn new(ui_tx: broadcast::Sender<UiEvent>) -> Self {
        Self {
            agents: HashMap::new(),
            ui_tx,
            spawner: None,
        }
    }

    /// Set dynamic agent spawner used for on-demand registration.
    pub fn set_spawner(&mut self, spawner: Arc<AgentSpawner>) {
        self.spawner = Some(spawner);
    }

    /// Register an agent's inbox sender.
    pub fn register(&mut self, agent_id: AgentId, tx: mpsc::Sender<Envelope>) {
        info!(agent = %agent_id, "registered agent");
        self.agents.insert(agent_id, tx);
    }

    /// Route an envelope to the target agent.
    pub async fn route(&mut self, mut envelope: Envelope) -> anyhow::Result<()> {
        // Hop check
        if !envelope.hop() {
            warn!(
                id = %envelope.id,
                from = %envelope.from,
                to = %envelope.to,
                "message exceeded TTL, dropping"
            );
            return Ok(());
        }

        // Broadcast to UI
        let _ = self.ui_tx.send(UiEvent::Message(envelope.clone()));

        // Messages addressed to "user" are terminal UI messages.
        // They are already broadcast above, so no agent delivery is needed.
        if envelope.to == "user" {
            return Ok(());
        }

        // Deliver to target agent. If unknown and a spawner exists,
        // attempt dynamic spawn-on-first-message.
        if !self.agents.contains_key(&envelope.to) {
            if let Some(spawner) = &self.spawner {
                match spawner.spawn(&envelope.to).await {
                    Ok(inbox_tx) => {
                        info!(agent = %envelope.to, "dynamically registered agent");
                        self.agents.insert(envelope.to.clone(), inbox_tx);
                    }
                    Err(e) => {
                        warn!(to = %envelope.to, error = %e, "failed to spawn dynamic agent");
                    }
                }
            }
        }

        if let Some(tx) = self.agents.get(&envelope.to) {
            tx.send(envelope)
                .await
                .map_err(|e| anyhow::anyhow!("failed to deliver message: {}", e))?;
        } else {
            warn!(to = %envelope.to, "no agent registered for target");
        }

        Ok(())
    }

    /// Get a UI event subscriber.
    pub fn subscribe_ui(&self) -> broadcast::Receiver<UiEvent> {
        self.ui_tx.subscribe()
    }

    /// Get the UI broadcast sender (for agents to emit status, tokens, etc.)
    pub fn ui_tx(&self) -> broadcast::Sender<UiEvent> {
        self.ui_tx.clone()
    }
}
