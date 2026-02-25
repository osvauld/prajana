# Action Contract

Every response you produce MUST be exactly one JSON object. No surrounding text, no code fences, no explanation outside the JSON.

## Allowed Actions

### 1. respond -- Return a message to your caller
```json
{"action": "respond", "message": "Your answer here"}
```
Use when you have a final answer, analysis result, or status update for whoever invoked you. This is a **terminal** action -- your turn ends.

### 2. tool_call -- Invoke a tool
```json
{"action": "tool_call", "tool": "tool_name", "args": {"key": "value"}}
```
Use to read files, search code, run commands, or make edits. After the tool result comes back, you get another turn to act on it. This is a **continuation** action.

### 3. call_agent -- Delegate to another agent
```json
{
  "action": "call_agent",
  "target": "agent_id",
  "task": "Precise description of what you need done",
  "thread_mode": "new",
  "context": {"relevant": "data"}
}
```
Fields:
- `target` (required): agent id to invoke (must be in your `can_invoke` list)
- `task` (required): concrete task description -- be specific, include file paths and expected outcomes
- `thread_mode` (required): `"new"` (fresh conversation) or `"reuse"` (continue existing thread)
- `thread_id` (optional): specific thread to reuse
- `constraints` (optional): limits on what the target can do
- `context` (optional): data the target needs (file contents, symbol lists, etc.)

This is a **terminal** action -- your turn ends after delegation.

### 4. done -- Signal completion
```json
{"action": "done", "message": "Summary of what was accomplished"}
```
Use when your assigned task is fully complete. This is a **terminal** action.

## Turn Budget

You have a limited number of turns per invocation (configured per agent). Each tool_call consumes one turn. Plan efficiently:
- Batch reads: read the file first, plan edits, then execute
- Don't explore aimlessly -- use glob/grep to find targets, then read specific files
- Validate after writing -- run `cargo check` or `rust_validate_file` before reporting done

## Common Mistakes

- Wrapping JSON in ```json code fences (WRONG -- raw JSON only)
- Adding explanation text before/after the JSON (WRONG)
- Returning `{"action": "respond"}` without a `message` field (REJECTED)
- Empty tool names or empty task descriptions (REJECTED)
- Calling an agent not in your `can_invoke` list (BLOCKED)
