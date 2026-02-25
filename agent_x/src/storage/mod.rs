use anyhow::{Context, Result};
use redb::{Database, ReadableTable, TableDefinition};
use std::path::Path;

/// Table: sessions — SessionId -> SessionMeta (JSON bytes)
const SESSIONS: TableDefinition<&str, &[u8]> = TableDefinition::new("sessions");

/// Table: conversations — "session_id:agent_id" -> Loro doc bytes
const CONVERSATIONS: TableDefinition<&str, &[u8]> = TableDefinition::new("conversations");

/// Table: agent_state — "session_id:agent_id" -> AgentSnapshot (JSON bytes)
const AGENT_STATE: TableDefinition<&str, &[u8]> = TableDefinition::new("agent_state");

/// Thin wrapper around redb for persistent storage.
pub struct Store {
    db: Database,
}

impl Store {
    pub fn open(base_dir: &Path) -> Result<Self> {
        std::fs::create_dir_all(base_dir)?;
        let db_path = base_dir.join("agent_x.redb");
        let db = Database::create(&db_path).context("failed to open redb database")?;

        // Ensure tables exist
        let write_txn = db.begin_write()?;
        {
            let _ = write_txn.open_table(SESSIONS)?;
            let _ = write_txn.open_table(CONVERSATIONS)?;
            let _ = write_txn.open_table(AGENT_STATE)?;
        }
        write_txn.commit()?;

        Ok(Self { db })
    }

    // ---- Sessions ----

    pub fn save_session(&self, session_id: &str, data: &[u8]) -> Result<()> {
        let write_txn = self.db.begin_write()?;
        {
            let mut table = write_txn.open_table(SESSIONS)?;
            table.insert(session_id, data)?;
        }
        write_txn.commit()?;
        Ok(())
    }

    pub fn load_session(&self, session_id: &str) -> Result<Option<Vec<u8>>> {
        let read_txn = self.db.begin_read()?;
        let table = read_txn.open_table(SESSIONS)?;
        Ok(table.get(session_id)?.map(|v| v.value().to_vec()))
    }

    pub fn list_sessions(&self) -> Result<Vec<String>> {
        let read_txn = self.db.begin_read()?;
        let table = read_txn.open_table(SESSIONS)?;
        let mut sessions = Vec::new();
        let iter = table.iter()?;
        for entry in iter {
            let (key, _) = entry?;
            sessions.push(key.value().to_string());
        }
        Ok(sessions)
    }

    pub fn delete_session(&self, session_id: &str) -> Result<()> {
        let write_txn = self.db.begin_write()?;
        {
            let mut table = write_txn.open_table(SESSIONS)?;
            table.remove(session_id)?;
        }
        write_txn.commit()?;
        Ok(())
    }

    // ---- Conversations (Loro doc bytes) ----

    pub fn save_conversation(
        &self,
        session_id: &str,
        agent_id: &str,
        doc_bytes: &[u8],
    ) -> Result<()> {
        let key = format!("{}:{}", session_id, agent_id);
        let write_txn = self.db.begin_write()?;
        {
            let mut table = write_txn.open_table(CONVERSATIONS)?;
            table.insert(key.as_str(), doc_bytes)?;
        }
        write_txn.commit()?;
        Ok(())
    }

    pub fn load_conversation(&self, session_id: &str, agent_id: &str) -> Result<Option<Vec<u8>>> {
        let key = format!("{}:{}", session_id, agent_id);
        let read_txn = self.db.begin_read()?;
        let table = read_txn.open_table(CONVERSATIONS)?;
        Ok(table.get(key.as_str())?.map(|v| v.value().to_vec()))
    }

    // ---- Agent state snapshots ----

    pub fn save_agent_state(&self, session_id: &str, agent_id: &str, state: &[u8]) -> Result<()> {
        let key = format!("{}:{}", session_id, agent_id);
        let write_txn = self.db.begin_write()?;
        {
            let mut table = write_txn.open_table(AGENT_STATE)?;
            table.insert(key.as_str(), state)?;
        }
        write_txn.commit()?;
        Ok(())
    }

    pub fn load_agent_state(&self, session_id: &str, agent_id: &str) -> Result<Option<Vec<u8>>> {
        let key = format!("{}:{}", session_id, agent_id);
        let read_txn = self.db.begin_read()?;
        let table = read_txn.open_table(AGENT_STATE)?;
        Ok(table.get(key.as_str())?.map(|v| v.value().to_vec()))
    }
}
