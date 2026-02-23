# Agent-X

A multi-agent AI coding assistant runtime with a terminal UI, built in Rust.

Agent-X orchestrates a team of specialist LLM-powered agents that collaborate through structured messages to read, plan, write, review, and document real codebases — all visible and controllable from your terminal.

---

## What it does

Agent-X is not a single-prompt coding tool. It is an orchestration substrate where multiple agents with distinct roles work together on engineering tasks:

- A **planner** decomposes tasks and coordinates specialists
- A **reader** explores and understands the codebase
- A **writer** makes surgical, validated code edits
- A **reviewer** enforces quality gates before changes land
- A **docs** agent keeps documentation synchronized with code
- A **scribe** indexes the codebase for context retrieval

All inter-agent communication is structured, auditable, and visible in the TUI as live `@from -> @to` message streams.

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│                   Terminal UI (Ratatui)              │
│  ┌──────────────┐ ┌──────────────┐ ┌─────────────┐  │
│  │ Agent Status │ │ Conversation │ │  Input Bar  │  │
│  │    Panel     │ │    View      │ │             │  │
│  └──────────────┘ └──────────────┘ └─────────────┘  │
└─────────────────────────────────────────────────────┘
                         │
                    UiEvent bus
                         │
┌─────────────────────────────────────────────────────┐
│                  Runtime / Router                    │
│   message bus · TTL hop-checking · agent spawner     │
└────────┬────────────────────────────────────────────┘
         │  Envelope (session / thread / parent IDs)
    ┌────┴──────────────────────────────────┐
    │              Agent Loop               │
    │  LLM stream → parse AgentAction →     │
    │  execute tool / delegate / respond    │
    └────┬──────────────────────────────────┘
         │
    ┌────┴──────────────────────────────────────────┐
    │                 Tool Suite                    │
    │  file · search · shell · surgical · jj · LSP  │
    └───────────────────────────────────────────────┘
```

### Key design principles

1. **Peer-to-peer collaboration** — agents are peers, not a master/slave hierarchy. Delegation is explicit message passing with thread-aware correlation.
2. **Deterministic actions** — agents emit structured `AgentAction` payloads (`respond`, `tool_call`, `call_agent`, `ask_user`, `done`), not freeform text. Invalid output is rejected.
3. **Separated reasoning and execution** — `smart` tier agents handle planning/analysis; `worker` tier handles mechanical tasks. Model assignment is configurable per tier.
4. **Explicit thread lifecycle** — every delegation carries a `request_id`. Threads are first-class units. Parallel conversations are tracked and correlated.
5. **Tooling safety** — read-only agents cannot invoke mutation tools. Surgical edits include stale-check protection and post-edit validation.
6. **Human visibility** — the TUI is an operational control plane, not cosmetic. Live agent status, per-thread conversation filters, tmux integration for per-agent inspection.

---

## Prerequisites

| Dependency | Purpose |
|---|---|
| `rust` (stable, 2021 edition) | Build toolchain |
| `tmux` | Per-agent shell isolation |
| `jj` (Jujutsu) | Agent workspace isolation via VCS |
| `rg` (ripgrep) | Grep tool used by agents |
| `rust-analyzer` | Optional — enhances surgical Rust editing |
| `rustfmt` | Optional — post-edit formatting |
| `cargo` | Optional — post-edit compile validation |

An API key for a supported LLM provider is required (see Configuration).

---

## Building

```bash
cargo build --release
```

The binary will be at `target/release/agent_x`.

---

## Configuration

On first run, Agent-X generates a default config at `~/.agent_x/config.json`.

### Provider setup

Set your API key in a `.env` file at the project root or export it as an environment variable:

```bash
# For the default ZAI provider
OPENAI_API_KEY=your_key_here

# For Anthropic
ANTHROPIC_API_KEY=your_key_here
```

### Config file (`~/.agent_x/config.json`)

Key sections:

```json
{
  "provider": "zai",
  "tiers": {
    "smart": { "model": "glm-4.7" },
    "worker": { "model": "glm-4.7" }
  },
  "providers": {
    "zai": { "base_url": "https://api.z.ai/api/coding/paas/v4" },
    "openai": { "base_url": "https://api.openai.com/v1" },
    "anthropic": {}
  }
}
```

Supported providers: `zai` (default), `openai` (and any OpenAI-compatible endpoint), `anthropic`.

### Agent definitions

Dynamic project agents are discovered automatically from:

1. `.agent_x/agents/*.md` — native format
2. `.opencode/agents/*.md` — compatibility mode

Agent definition files use YAML frontmatter:

```yaml
---
name: my-agent
mode: read          # read | write
tier: smart         # smart | worker
tools:
  - read_file
  - grep
  - glob
can_invoke:
  - reader
  - planner
---

Your agent's system prompt and skills go here.
```

---

## Running

```bash
./target/release/agent_x
```

Logs are written to `~/.agent_x/logs/agent_x.log` to keep the TUI clean.

---

## Terminal UI

```
┌─ Agents ──────┐ ┌─ Conversation ─────────────────────────┐
│ ● planner     │ │ @user -> @planner                      │
│ ◌ reader      │ │   Refactor the config module           │
│ ◌ writer      │ │                                        │
│ ◌ reviewer    │ │ @planner -> @reader                    │
│ ◌ docs        │ │   Read src/config/mod.rs and report    │
└───────────────┘ │   the current structure.               │
                  │                                        │
                  │ @reader -> @planner                    │
                  │   [tool: read_file] src/config/mod.rs  │
                  │   ...                                  │
                  └────────────────────────────────────────┘
                  ┌─ Input ────────────────────────────────┐
                  │ @planner refactor the auth module >    │
                  └────────────────────────────────────────┘
```

### Key bindings

| Key | Action |
|---|---|
| `Tab` | Cycle focus between panels |
| `@` + agent name | Address a specific agent in input |
| `Tab` (in input) | Autocomplete @mention |
| `/new` | Start a new conversation thread |
| `y` | Copy selected message to clipboard |
| `Mouse scroll` | Scroll conversation view |
| `Click` agent | Select agent / filter conversation |
| `q` | Quit |

### Conversation filters

Click an agent in the agent panel to filter the conversation view:
- **All** — full unified stream
- **By agent** — messages to/from selected agent
- **By thread** — latest thread for selected agent

### tmux integration

Each agent runs in its own tmux window. From the agents panel you can open, switch to, or kill individual agent windows directly from the TUI.

---

## Agent system

### Built-in agents

| Agent | Mode | Role |
|---|---|---|
| `planner` | read | Orchestrator. Decomposes tasks, delegates to specialists, synthesizes results. |
| `reader` | read | Code explorer. Reads files, searches, reports structure and context. |
| `writer` | write | Code surgeon. Makes targeted edits using surgical Rust tools and file tools. |
| `reviewer` | read | Quality gate. Returns explicit `PASS`/`FAIL` verdicts with reasoning. |
| `docs` | write | Documentation maintainer. Updates docs to match code changes. |
| `scribe` | read | Codebase indexer. Builds context summaries for other agents. |

### Adding a custom agent

1. Create a folder: `agents/<agent_id>/`
2. Add `skills.md` describing what the agent does and how
3. Add `boundaries.md` describing what the agent must never do
4. Register the agent in `~/.agent_x/config.json` or place its definition in `.agent_x/agents/<agent_id>.md`

All agents automatically receive the shared protocol docs from `agents/_shared/`:
- `action-contract.md` — the JSON action format every agent must follow
- `tools.md` — complete tool reference with examples
- `communication.md` — inter-agent delegation protocol

---

## Tool suite

| Tool | Description |
|---|---|
| `read_file` | Read file contents with optional line offset |
| `write_file` | Write or overwrite a file |
| `patch_file` | Find-and-replace within a file |
| `glob` | Find files by glob pattern |
| `grep` | Search file contents with regex (via ripgrep) |
| `shell` | Execute commands in a tmux-managed shell window |
| `rust_list_symbols` | List functions/structs/enums/traits in a Rust file |
| `rust_replace_block` | Replace a named block in a Rust file (AST-aware, validated) |
| `rust_insert_after_block` | Insert code after a named block in a Rust file |
| `rust_validate_file` | Syntax-check a Rust file (tree-sitter + optional cargo check) |
| `jj_diff` | Show uncommitted changes in the agent's jj workspace |
| `jj_status` | Show jj workspace status |

Tool access is controlled per agent by the `tools` field in the agent definition and enforced by mode (`read` agents cannot use mutation tools).

### Surgical Rust editing

The `rust_replace_block` and `rust_insert_after_block` tools use a hybrid tree-sitter + rust-analyzer pipeline to make safe, targeted edits:

- Symbols are resolved by name with optional `module_path` and `line_hint` for disambiguation
- Stale-edit protection via SHA-256 hash checks prevents editing drifted targets
- Post-edit validation runs syntax check, optional `rustfmt`, and optional `cargo check`
- Rich result metadata (touched file, byte range, targeted symbol, validation status) is returned to the requesting agent

---

## Storage and persistence

- **Conversations** are persisted as Loro CRDT document snapshots in a `redb` embedded database at `~/.agent_x/`
- **Agent workspaces** use Jujutsu VCS for isolated working copies — each agent edits in its own workspace, changes are squashed or abandoned based on review outcome
- **Sessions** and **agent state** are also stored in redb

---

## Project structure

```
agent_x/
  src/
    main.rs               # Entry point
    agent/                # Agent event loop and action parsing
    config/               # App config and agent definition loading
    provider/             # LLM provider integrations (OpenAI, Anthropic, ZAI)
    runtime/              # Message bus, router, agent spawner
    storage/              # redb + Loro CRDT persistence
    tools/                # All tool implementations
    ui/                   # Ratatui TUI (panels, theming, markdown, highlighting)
  agents/
    _shared/              # Shared protocol docs injected into every agent prompt
    planner/              # Planner skills and boundaries
    reader/               # Reader skills and boundaries
    writer/               # Writer skills and boundaries
    reviewer/             # Reviewer skills and boundaries
    docs/                 # Docs agent skills and boundaries
    scribe/               # Scribe skills and boundaries
  docs/
    agent-x-philosophy-and-progress.md
    next-implementation-plan.md
```

---

## Status

Agent-X is at **v0.1.0** — early alpha. The core runtime, agent loop, tool suite, and TUI are functional for the happy path. Known gaps and the implementation roadmap are documented in [`docs/next-implementation-plan.md`](docs/next-implementation-plan.md). The design philosophy is documented in [`docs/agent-x-philosophy-and-progress.md`](docs/agent-x-philosophy-and-progress.md).

Current limitations:
- Anthropic provider does not yet support streaming
- Full stop-protocol enforcement (loop detection, timeout policy) is not yet complete
- Router-level `can_invoke` policy enforcement is partial
- No CI/CD pipeline
- Minimal test coverage (unit tests only)
