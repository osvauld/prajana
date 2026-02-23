# Agents Directory

Each agent has a folder with markdown docs that define behavior.

## Structure

```
agents/
  _shared/              -- Shared skills loaded for ALL agents
    action-contract.md  -- JSON action format every agent must follow
    tools.md            -- Complete tool reference with examples
    communication.md    -- Inter-agent delegation protocol
  planner/              -- Orchestrator (read-mode, delegates to others)
  reader/               -- Code explorer (read-mode, finds context)
  writer/               -- Code surgeon (write-mode, makes changes)
  reviewer/             -- Quality gate (read-mode, PASS/FAIL verdicts)
  docs/                 -- Doc maintainer (write-mode, updates docs only)
```

## How it works

At startup, agent_x loads these files for each agent and appends them to the system prompt:
1. All files from `_shared/` are loaded first (every agent gets these)
2. Then files from `agents/<agent_id>/` are loaded (agent-specific skills and boundaries)

## Adding a new agent

1. Add a folder matching the agent id in config
2. Create `skills.md` with what the agent does and how
3. Create `boundaries.md` with what the agent must never do
4. Register the agent in `config/mod.rs` or `~/.agent_x/agents.json`
