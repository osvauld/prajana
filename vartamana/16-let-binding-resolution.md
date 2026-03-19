# 16 — The Scan Body Escape Fix

**Scan output can now be referenced by name in subsequent let bindings.**

This documents the actual bug found and fixed in session 9. The original
plan (below) hypothesised a parse-time scope resolution issue. The real
bug was simpler and more fundamental: the file parser's line grouper
never closed the scan body, so every line after a scan header was
absorbed into the scan binding.

---

## The actual root cause

### What was happening

In `yantra_tantra_file2.ml` (the file-level parser that groups lines into
bindings before the expression parser runs), there is a state flag
`in_scan_body` that is set to `true` when a scan header's `:` is
encountered (line 907). This flag gates whether subsequent lines are
treated as continuation (scan body lines) or as new top-level bindings.

The flag was **never reset to false** while lines were being consumed.
The logic at line 872 computed:

```ocaml
let inside_block = !depth > 0 || !in_scan_head || !in_scan_body in
```

When `in_scan_body = true`, `inside_block = true`, so the parser went
directly to the continuation branch (line 897):

```ocaml
(* inside a block — always continuation, never new binding *)
st.cur_lines <- trimmed :: st.cur_lines
```

The `in_scan_body := false` reset at line 888 was inside the
`not inside_block` branch — which was unreachable when `in_scan_body`
was true. A perfect deadlock: the flag could only be cleared from code
that only ran when the flag was already clear.

### The consequence

Every tantra file that had bindings AFTER a scan block would silently
absorb those bindings into the scan's raw lines. The expression parser
would never see them as separate let bindings. The `result = ...`
binding after a scan would not be stored in the eval environment.
The `return result` would look up `e["result"]` and find `None`.

**All existing scan tantras worked** because they all used the pattern
`result = scan graph [...]:` — the scan IS the return value, with no
post-scan bindings. This is why the bug went undetected through 500+
tests.

### Evidence

```
[debug-print] [['apple', 'satya', 'apple'], ['5', 'sankhya', 'apple']]  ← graph (takes param, in env)
[debug-print] 'scanned'  ← scanned resolves to STRING "scanned" (not in env)
```

The `Var "scanned"` node was correctly emitted by the expression parser.
But the eval-time env lookup `Hashtbl.find_opt e "scanned"` returned
`None` because the `scanned = scan ...` binding was never separately
compiled — it was fused with all subsequent lines as one giant scan block.

---

## The fix

### First attempt (insufficient)

Removed `in_scan_body` from the `inside_block` computation and added an
`escaped_scan` check: when in a scan body at depth 0, if the current
line starts a new binding or a new scan, close the scan body.

```ocaml
let escaped_scan = !in_scan_body && !depth = 0
  && not !in_scan_head
  && (is_scan_start trimmed
      || (match try_binding_start trimmed with
          | Some _ -> true | None -> false))
```

**This broke 250+ tests.** The reason: scan body lines include state
assignments like `cur-base = (cond ...)` which `try_binding_start`
matches as new top-level bindings. Every scan with state mutations was
being prematurely closed.

### Second attempt (correct)

Added an **indentation check**. Scan body state assignments are always
indented (2+ spaces). Top-level bindings start at column 0. The fix
checks `stripped.[0]` (the comment-stripped line before trimming):

```ocaml
let is_top_level_line =
  String.length stripped > 0
  && stripped.[0] <> ' ' && stripped.[0] <> '\t'
in
let escaped_scan = !in_scan_body && !depth = 0
  && not !in_scan_head
  && is_top_level_line
  && (is_scan_start trimmed
      || (match try_binding_start trimmed with
          | Some _ -> true | None -> false))
in
```

Only un-indented lines that look like bindings can escape the scan body.
This correctly distinguishes:
- `  cur-base = (cond ...)` — indented, scan body state mutation → stay in scan
- `after = debug-print scanned` — column 0, new top-level binding → escape scan

### Result

**511 passed / 63 xfailed / 0 failed** — matches baseline within expected
variance (2 count tests newly xfailed due to count.om changes from session 8,
not related to this fix).

---

## What this unlocks

See [17-scan-ref-patterns.md](17-scan-ref-patterns.md) for the full analysis
of patterns now possible and xfail gates that become attackable.

The short version: scan output can now be post-processed (filtered, mapped,
appended, measured) within the same tantra file. This enables:

1. **count-chain** — event-sequence arithmetic with post-scan total extraction
2. **viveka compute-then-compare** — scan entities, derive per-entity, then compare
3. **dvandva per-entity** — scan entities, compute per-entity, then aggregate
4. **transitive closure** — scan edges, then build closure from collected pairs
5. **derive-chain simplification** — scan with fixpoint, collect steps after

---

## The original (incorrect) theory

The plan below was written during session 8 before the fix was implemented.
It hypothesised a parse-time scope resolution issue where `Var "scanned"` was
being emitted as `StrLit "scanned"`. This theory was wrong — the expression
parser correctly emits `Var "scanned"`, and the evaluator correctly checks
the env first. The issue was that the binding was never compiled separately.

The lesson: when `debug-print x` shows the string `'x'`, the cause can be
either (a) the identifier resolving to a string literal, or (b) the eval-time
env lookup failing because the binding was never stored. We assumed (a) but
it was (b). The file parser's line grouping — an earlier stage than expression
parsing — was the culprit.

---

## Changelog

| Date | Session | Event |
|------|---------|-------|
| 2026-03-19 | 8 | Discovered: `scanned = scan graph [...]` then `filter scanned` returns None. Hypothesised parse-time scope resolution issue. |
| 2026-03-19 | 8 | Plan written targeting parse-time scope tracking. |
| 2026-03-19 | 9 | Actual root cause found: file parser `in_scan_body` flag never resets. First fix attempt broke 250+ tests (state assignments mistaken for bindings). |
| 2026-03-19 | 9 | Correct fix: indentation check — only un-indented lines escape scan body. 511/63/0 confirmed. |
