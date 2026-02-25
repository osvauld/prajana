mod agent;
mod config;
mod provider;
mod runtime;
mod storage;
mod tools;
mod ui;

use anyhow::Result;
use std::sync::Arc;

#[tokio::main]
async fn main() -> Result<()> {
    // Load .env automatically when present, overriding stale exported vars.
    let _ = dotenvy::dotenv_override();

    // Load config
    let cfg = config::AppConfig::load()?;

    // Initialize tracing to file so logs don't overlay the TUI.
    let log_dir = cfg.storage_path.join("logs");
    std::fs::create_dir_all(&log_dir)?;
    let file_appender = tracing_appender::rolling::daily(log_dir, "agent_x.log");
    let (non_blocking, _guard) = tracing_appender::non_blocking(file_appender);

    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::from_default_env()
                .add_directive("agent_x=info".parse()?),
        )
        .with_target(false)
        .with_ansi(false)
        .with_writer(non_blocking)
        .init();

    // Initialize storage
    let store = Arc::new(storage::Store::open(&cfg.storage_path)?);

    // Build and run the app
    let mut app = ui::App::new(cfg, store).await?;
    app.run().await
}
