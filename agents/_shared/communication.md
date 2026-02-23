# Inter-Agent Communication Protocol

## Agent Roster (Peer Topology)

Agents are NOT hierarchical. Any agent can invoke any peer in its `can_invoke` list.

| Agent | Mode | Purpose | Can Invoke |
|-------|------|---------|------------|
| **planner** | read | Decomposes user requests, delegates to specialists | reader, writer, reviewer, scribe |
| **reader** | read | Explores codebase, extracts context, finds symbols | (none -- returns findings to caller) |
| **writer** | write | Executes precise code changes, validates they compile | reader |
| **reviewer** | read | Validates changes for correctness, safety, style | writer |
| **scribe** | write | Updates codebase index, collects summaries, end-of-run cleanup | reader |
| **docs** | write | Updates documentation to match implementation | (none) |

## Peer Communication Patterns

### Writer asks Reader directly
Writer doesn't need planner's permission to get context:
```
writer needs to understand a file before editing
writer -> reader: "List symbols in src/tools/surgical.rs and read lines 100-200"
reader -> writer: [structured findings]
writer proceeds with the edit
```

### Reviewer asks Writer to fix directly
No need to bounce through planner for fix-and-recheck:
```
reviewer finds a bug in the change
reviewer -> writer: "FAIL: the match arm at line 142 doesn't handle the None case. Add a None => bail!(...) arm."
writer fixes it, validates, reports done
reviewer can then re-check
```

### Planner calls Scribe at end of run
```
planner finishes a multi-step task
planner -> scribe: "Task complete. Changed src/agent/mod.rs (added retry), src/config/mod.rs (added timeout field). Update the codebase index."
scribe -> reader: "glob src/** and list symbols in the changed files"
scribe updates agents/_shared/codebase-index.md and agents/_shared/last-run.md
```

## Delegation Rules

### How to delegate (call_agent)
Always provide:
1. **Specific task** -- not "look at the code" but "read src/agent/mod.rs and list all public methods on Agent"
2. **Context** -- include relevant file paths, symbol names, error messages
3. **Expected outcome** -- what the target should produce or verify

### Good delegation
```json
{
  "action": "call_agent",
  "target": "writer",
  "task": "Add a `timeout` field (Option<Duration>) to the Agent struct in src/agent/mod.rs. Initialize it from config.max_timeout in Agent::new(). Use it in call_model_with_stream to replace the hardcoded 90s timeout.",
  "thread_mode": "new",
  "context": {"files": ["src/agent/mod.rs:35-80"], "current_timeout": "hardcoded 90s at line 186"}
}
```

### Bad delegation
```json
{
  "action": "call_agent",
  "target": "writer",
  "task": "fix the timeout thing",
  "thread_mode": "new"
}
```

## Communication Flows

### User Request Flow
```
User -> planner: "Add retry logic to the agent loop"
  planner -> reader: "Read src/agent/mod.rs, find the action loop and error handling"
  reader -> planner: "Loop at 114-159, errors at 118-122, no retry exists"
  planner -> writer: "Add 3-attempt exponential backoff around model call at 116-123"
  writer -> reader: "Read the current call_model_with_stream signature"  (direct peer call)
  writer makes the change, validates with cargo check
  planner -> reviewer: "Review retry changes in src/agent/mod.rs"
  reviewer reads files, gives PASS
  planner -> scribe: "Task done. src/agent/mod.rs changed (added retry). Update index."
  planner -> user: "Done. Added retry with backoff."
```

### Reviewer-Writer Fix Loop (no planner needed)
```
reviewer -> writer: "FAIL: retry wraps wrong scope. Move it to wrap only call_model_with_stream."
writer reads, fixes, validates
writer -> done
reviewer re-reads, gives PASS
```

### Direct Tool Invocation
Any agent with tools can use them directly:
```
writer: {"action": "tool_call", "tool": "read_file", "args": {"path": "src/agent/mod.rs"}}
writer: {"action": "tool_call", "tool": "rust_replace_block", "args": {...}}
writer: {"action": "tool_call", "tool": "shell", "args": {"command": "cargo check 2>&1"}}
writer: {"action": "done", "message": "Replaced Agent::run with retry. cargo check passes."}
```

## Thread Modes

- **new**: Fresh conversation. Use for independent tasks.
- **reuse**: Continue an existing thread. Use when building on previous work.

Default to `"new"` unless you're explicitly continuing a revision chain.

## Error Handling

If a tool call fails:
1. Read the error message carefully
2. Try to fix the issue (wrong path? stale hash? ambiguous symbol?)
3. If you can't fix it, `respond` with the error details so your caller can adjust

Never silently swallow errors. Never claim success when a tool failed.
