# Next Implementation Plan

This document captures what we should implement next, in order, based on the current state of the app.

## Current Baseline (Already Implemented)

- Multi-agent runtime with planner/reader/writer/reviewer/docs agents.
- Per-agent model/provider configuration via `~/.agent_x/agents.json` (with TOML fallback migration).
- Agent docs loading from `agents/<agent_id>/*.md` appended to each system prompt.
- Per-agent cardinal rules loaded from config and appended to prompts.
- Runtime policy checks for:
  - `can_invoke` constraints.
  - read-only mode blocking mutating tools.
- Tool registry wiring by allowed tool list.
- Rust surgical tools:
  - `rust_list_symbols`
  - `rust_replace_block`
  - `rust_insert_after_block`
  - `rust_validate_file`
- Streaming support in provider path + UI stream rendering.
- Tmux-based agent windows + log capture in UI.
- CRDT conversation persistence (Loro snapshots in redb).

## Priority 1: Deterministic Tool-Action Loop

### Why
Current orchestration still relies partly on freeform model text and compatibility parsing. We need deterministic and auditable agent behavior.

### What to build

1. Structured `AgentAction` schema.
   - Add typed actions produced by agent model output parsing:
     - `respond`
     - `tool_call`
     - `call_agent`
     - `done`
   - Include a strict parser with validation errors surfaced to UI.

2. Strong `call_agent` contract.
   - Required fields:
     - `target`
     - `task`
     - `thread_mode` (`new` or `reuse`)
   - Optional fields:
     - `thread_id`
     - `constraints` (token limits, output format)
     - `context` refs

3. Single execution path for tools.
   - Route all tool invocations through one function with:
     - policy check
     - mode check
     - execution
     - structured result envelope

### Acceptance criteria

- Agents can no longer invoke peers via ad-hoc text only.
- Invalid action format returns explicit parse error in transcript.
- Every tool/call_agent action generates a traceable `ToolResult`/`TaskResult` message.

## Priority 2: Surgical Rust Toolchain Hardening

### Why
Surgical tooling exists but needs production-grade safeguards before it is relied on for writer workflows.

### What to build

1. Stale-target protection.
   - Add optional `expected_old_hash` or `expected_old_block` check before edit.
   - Fail safely if source drifted.

2. Better target selection.
   - Support disambiguation fields when multiple blocks match:
     - `module_path`
     - `line_hint`
   - Keep strict single-target behavior by default.

3. Post-edit validation pipeline.
   - `rust_validate_file` always after mutating AST tools.
   - Optional `rustfmt` on touched file.
   - Optional `cargo check` gate for writer workflows.

4. Tool result metadata.
   - Return richer result data:
     - touched file
     - byte range
     - symbol targeted
     - validation status

### Acceptance criteria

- Writer can perform reliable block replacements without accidental drift edits.
- Failed validation blocks downstream approval.
- Tool results provide enough detail for reviewer decisions.

## Priority 3: Docs Agent Automation

### Why
We want docs to stay synchronized with implementation automatically.

### What to build

1. Change-detection trigger.
   - When writer changes non-doc files, auto-create docs task.

2. Docs task payload builder.
   - Include:
     - change summary
     - file list
     - diff snippet
     - behavior/config changes
     - validation results

3. Reviewer docs gate.
   - Reviewer verifies docs changes before final approval.

### Acceptance criteria

- Docs agent is invoked automatically for code changes.
- Docs updates are scoped and reviewable.
- Final approval path includes doc parity check.

## Priority 4: Workflow + Approval UX

### Why
Execution works, but user control over approval/retry/reject should be first-class.

### What to build

1. Explicit change states.
   - `proposed` -> `review_requested` -> `approved`/`rejected`.

2. User controls in UI.
   - Approve: squash relevant jj change.
   - Reject: abandon change.
   - Retry: ask writer to revise with reviewer feedback.

3. Per-agent task queue visibility.
   - Show pending tasks and active thread in right panel.

### Acceptance criteria

- User can approve/reject/retry without leaving TUI.
- State transitions are persisted and visible.
- jj operations are tied to explicit user actions.

## Priority 5: Conversation and Session Model Completion

### Why
CRDT persistence exists, but thread/session semantics need to be fully explicit for large workflows.

### What to build

1. Thread metadata storage.
   - Store participants, creation time, parent thread, status.

2. Thread-mode behavior.
   - Ensure `new` spawns isolated convo branches.
   - Ensure `reuse` appends to existing context deterministically.

3. Navigation and filtering.
   - UI thread list per session.
   - Filter transcript by thread/agent.

### Acceptance criteria

- Users can move between old/new threads easily.
- Agent calls preserve intended context boundaries.
- Conversation history remains recoverable and inspectable.

## Priority 6: Router-Level Policy Enforcement

### Why
Policy is currently enforced inside agents; router should also enforce to prevent bypasses.

### What to build

1. Router checks for `can_invoke` before delivery.
2. Block unauthorized `call_agent` requests centrally.
3. Emit policy-denied UI events with reason.

### Acceptance criteria

- Unauthorized routes are blocked even if an agent misbehaves.
- Violations are visible and auditable in transcript.

## Priority 7: Reliability + Observability

### Why
Need robust operations as conversations and tool volumes grow.

### What to build

1. Retry/backoff policy for provider calls.
2. Metrics events:
   - first-token latency
   - total generation latency
   - tool duration
   - routing failures
3. Better error surfacing and summaries in UI.

### Acceptance criteria

- Transient provider failures recover automatically when safe.
- Users can see where latency/errors happen quickly.

## Suggested Execution Order (Concrete)

1. Deterministic `AgentAction` + strict `call_agent` path.
2. Surgical tool hardening (`expected_old_hash`, post-edit gates).
3. Docs-agent automation trigger and payload.
4. Approval UX + jj integration states.
5. Thread/session metadata + UI navigation.
6. Router-level policy guardrails.
7. Reliability/metrics improvements.

## Scope Guard: Happy Path First

For the current implementation phase, we intentionally optimize for happy-path execution only.

- No retry/backoff logic yet.
- No complex failure recovery orchestration yet.
- Focus on deterministic actions, tool enforcement, and successful end-to-end flows.

Retry/recovery remains a later enhancement after the happy path is stable.

## Notes for Immediate Next Coding Session

- Start in `src/agent/mod.rs` by extracting model output handling into an action parser module.
- Add a dedicated `ActionParseError` type and emit structured `MessageKind::Error` on invalid action output.
- Extend surgical tool args in `src/tools/surgical.rs` with optional stale-check fields.
- Add docs-trigger hook in runtime after writer task results are received.
