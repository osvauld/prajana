# Tool Reference

## Reading Tools

### read_file
Read file contents. Always read before editing.
```json
{"action": "tool_call", "tool": "read_file", "args": {"path": "src/main.rs"}}
```
Optional: `"offset": 100, "limit": 50` to read specific line ranges (0-indexed offset).

### glob
Find files by pattern. Use `**` for recursive matching.
```json
{"action": "tool_call", "tool": "glob", "args": {"pattern": "src/**/*.rs"}}
```

### grep
Search file contents with regex. Returns matching file paths and line numbers.
```json
{"action": "tool_call", "tool": "grep", "args": {"pattern": "fn main", "include": "*.rs"}}
```
`include` is optional -- filters to specific file extensions.

### rust_list_symbols
List all Rust symbols (functions, structs, enums, traits, impls) in a file with line ranges.
```json
{"action": "tool_call", "tool": "rust_list_symbols", "args": {"path": "src/agent/mod.rs"}}
```
Output format: `Kind name [start_line-end_line]` per symbol. Use this to understand file structure before editing.

## Writing Tools

### write_file
Write entire file contents. Use for new files or complete rewrites.
```json
{"action": "tool_call", "tool": "write_file", "args": {"path": "src/new.rs", "content": "// file content"}}
```

### patch_file
Replace exact text in a file. The `old_text` must match exactly (whitespace-sensitive).
```json
{"action": "tool_call", "tool": "patch_file", "args": {
  "path": "src/main.rs",
  "old_text": "fn old_name()",
  "new_text": "fn new_name()"
}}
```
Best for small, targeted changes. Fails if `old_text` is not found.

### rust_replace_block -- Surgical AST Edit
Replace an entire Rust AST block (function, struct, enum, trait, impl) by its kind and name.
```json
{"action": "tool_call", "tool": "rust_replace_block", "args": {
  "path": "src/agent/mod.rs",
  "kind": "function",
  "name": "run",
  "new_block": "pub async fn run(mut self) -> Result<()> {\n    // new implementation\n    Ok(())\n}",
  "module_path": "impl Agent",
  "line_hint": 84,
  "run_rustfmt": true,
  "run_cargo_check": false
}}
```

Fields:
- `kind`: one of `"function"`, `"struct"`, `"enum"`, `"trait"`, `"impl"`
- `name`: symbol name to find
- `new_block`: complete replacement code (the entire function/struct/etc)
- `module_path` (optional): disambiguate when multiple symbols have the same name (e.g. `"impl Agent"`)
- `line_hint` (optional): approximate line number to disambiguate
- `expected_old_hash` (optional): SHA-256 of the current block -- prevents stale edits
- `expected_old_block` (optional): full text of current block for verification
- `run_rustfmt` (optional): format the file after edit (default false)
- `run_cargo_check` (optional): run `cargo check` after edit (default false, expensive)

**When to use**: Replacing entire functions, structs, enums, or trait/impl blocks. Always prefer this over `write_file` for modifying existing Rust code -- it's AST-aware and prevents accidental corruption.

**Disambiguation**: If a file has two functions named `new`, provide `module_path: "impl Foo"` or `line_hint: 42` to pick the right one.

### rust_insert_after_block -- Insert After Symbol
Insert a new code snippet after an existing AST block.
```json
{"action": "tool_call", "tool": "rust_insert_after_block", "args": {
  "path": "src/tools/mod.rs",
  "kind": "function",
  "name": "execute",
  "snippet": "\nfn helper() -> bool {\n    true\n}\n",
  "module_path": "impl MyTool"
}}
```
Same disambiguation fields as `rust_replace_block`. Use for adding new functions/methods after existing ones.

### rust_validate_file
Check if a Rust file has valid syntax (tree-sitter parse, not full cargo check).
```json
{"action": "tool_call", "tool": "rust_validate_file", "args": {"path": "src/agent/mod.rs"}}
```

## Shell Tool

### shell
Execute a command in the agent's tmux workspace.
```json
{"action": "tool_call", "tool": "shell", "args": {"command": "cargo check 2>&1", "timeout_secs": 120}}
```
Use for: `cargo check`, `cargo build`, `cargo test`, `git status`, etc.

## Surgical Editing Workflow

The recommended flow for modifying Rust code:

1. **Discover**: `rust_list_symbols` to see what's in the file
2. **Read**: `read_file` to understand the current implementation
3. **Edit**: `rust_replace_block` or `rust_insert_after_block` for the change
4. **Validate**: `rust_validate_file` for quick syntax check, or `shell` with `cargo check` for full validation
5. **Report**: `respond` or `done` with what changed and validation results

Never skip step 2 (reading first). Never skip step 4 (validating after).
