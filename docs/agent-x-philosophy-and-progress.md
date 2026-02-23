# Agent-X: Philosophy and Progress

This document captures what Agent-X is, the design philosophy behind it, what has already been implemented, and where the project is heading next.

## What Agent-X Is

Agent-X is a Rust-based multi-agent coding runtime with a terminal UI.

It is designed to run on real codebases where multiple specialist agents collaborate through structured messages, delegate work to peers, use tools safely, and converge on finished outcomes without unbounded loops.

## Core Philosophy

### 1) Peer-to-peer collaboration, not master/slave

Agents are treated as peers with explicit communication permissions.

- A planner can orchestrate, but specialists can also ask other specialists for context.
- Delegation is represented as message passing (`TaskRequest`/`TaskResult`) with thread-aware correlation.
- Conversation flow is visible in the UI as `@from -> @to`.

### 2) Deterministic machine actions over freeform chat

Agent behavior is controlled via strict action payloads, not arbitrary prose.

- Canonical actions: `respond`, `tool_call`, `call_agent`, `ask_user`, `done`.
- The runtime parses and validates action payloads each turn.
- Invalid outputs are rejected (with tolerant extraction/retry safeguards).

This keeps orchestration auditable and reduces unpredictable agent behavior.

### 3) Separation of reasoning and execution

Different agent roles should use different cognitive budgets.

- Read/analyze/planning tasks can use stronger reasoning settings.
- Write/mechanical tasks can use cheaper worker settings.
- Model tiering exists (`smart`, `worker`) and is configurable.

Current temporary pin: all tiers use `glm-4.7` until heterogeneous model routing is finalized.

### 4) Explicit thread and request lifecycle

Multi-agent systems fail when requests are not tracked.

- Every delegation can carry a `request_id`.
- Requests are tracked as pending and marked resolved when replies arrive.
- Threads (`thread_id`) are first-class conversation units.

This allows parallel conversations and clear “who asked what / who answered what” visibility.

### 5) Tooling safety before autonomy

Mutation tools are controlled by policy and mode.

- Read-only agents cannot invoke write/mutation tools.
- Surgical Rust editing has validation hooks and stale-target checks.
- Shell/file/search tools are constrained by role and config.

The goal is useful autonomy with bounded blast radius.

### 6) Human visibility and intervention are non-negotiable

The TUI is not cosmetic; it is an operational control plane.

- Live per-agent status
- Unified conversation stream with filters
- Notifications for errors/warnings
- tmux integration for per-agent inspection
- Clipboard-friendly interaction and selection

## Architecture Direction

### Static + Dynamic Agents

Agent-X now follows a hybrid model:

- **Static agents**: always-on orchestrators (currently planner, reviewer)
- **Dynamic project agents**: discovered from project-local agent definitions and spawned on demand

Discovery order:

1. `.agent_x/agents/*.md` (native format)
2. `.opencode/agents/*.md` (compatibility mode)

This keeps startup lightweight while enabling large specialist rosters per repository.

## What Has Been Implemented So Far

## Runtime and agent loop

- Deterministic multi-turn action loop with strict action parsing
- Structured delegation via `call_agent` with `thread_mode` semantics
- `ask_user` path for explicit clarification requests
- Dynamic agent spawn-on-demand through the router when a target is not yet registered
- Request correlation fields (`request_id`, `parent_id`) propagated through task messages

## Config and discovery

- Tier-aware config (`smart`/`worker`)
- Static orchestrator roster + dynamic project specialist discovery
- Compatibility parsing for opencode-style frontmatter
- Peer communication defaults (`can_invoke`) with wildcard expansion behavior

## Tooling and editing

- File/search/shell tool integration
- Surgical Rust editing flow (replace/insert/validate/list symbols)
- Rust-analyzer integration path in place (hybrid RA + tree-sitter hooks)

## TUI and operability

- Agent list, conversation view, input, status bar
- Color-coded `from -> to` message headers
- Unified chat stream with filters:
  - all conversations
  - by selected agent
  - by latest thread for selected agent
- Pending request tracking and inline answer annotations
- Reply mode for unresolved user-facing questions (thread reuse)
- Mouse scrolling improvements and click-to-copy/`y` copy support
- tmux controls in agents panel (expand, open/switch, kill)
- On-screen warnings/errors as notifications
- Logs redirected to file to avoid TUI overlay (`~/.agent_x/logs/agent_x.log`)

## Reliability hardening

- More tolerant action extraction from model output (fenced block / embedded object extraction)
- Relaxed parsing fallback (`json5`) before final reject
- In-loop corrective retry when output format is invalid

## Current Known Gaps

- Full stop-protocol enforcement (open-request blocking, loop detection, timeout policy) is planned but not fully enforced end-to-end yet.
- Conversation browser is filter-based; explicit historical thread list UI is not finished.
- Permission schema is parsed but not fully enforced across all tool pathways.
- Per-role model heterogeneity is configured conceptually but currently pinned to one model in practice.

## Design Principles for Next Phase

1. **No open loops:** agents must not finalize a thread with unresolved required requests.
2. **Progress-or-stop:** detect non-progress delegation loops and fail fast with diagnostics.
3. **Evidence before mutation:** writing follows explicit context collection and verification.
4. **Review gate:** planner synthesis should pass reviewer validation before completion.
5. **Inspectable by default:** all important runtime transitions must be visible in UI and logs.

## Why This Approach

Agent-X is intentionally built as an orchestration substrate, not a single giant prompt.

The project prioritizes:

- composable agent behavior,
- explicit coordination contracts,
- robust runtime controls,
- and human-auditable operations.

That philosophy is what allows the system to scale from “single assistant chat” into “multi-agent engineering workflow” without becoming opaque or uncontrollable.
