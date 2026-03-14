# Parser Refactor Plan — Module Split + Dynamic Op Registry

**Status**: COMPLETE
**Date**: 2026-03-14
**Final test result**: 255 passed, 22 xfailed (up from 253 baseline)

---

## Problem (solved)

`yantra_parser.ml` was a 719-line monolith that owned everything: tokeniser, arity
tables, boundary keyword detection, expression parser, tantra file parser. It was
split once before into focused modules (`yantra_tokeniser`, `yantra_arity`,
`yantra_expr_parser`, `yantra_tantra_file`, `yantra_sentence_parser`) but those
modules were never wired into the dune build and were never kept in sync as
`yantra_parser.ml` kept evolving. They were dead code.

Three concrete bugs follow from this structure:

1. **`parse_cond` bug** — the `_` fallthrough branch in `parse_cond` treats `)` as
   a bare else-branch value. `reduce [1 2 3] 0 (fn acc x -> cond (gt x 1) acc x)`
   returns `")"` instead of `0`. Same bug existed in both `yantra_parser.ml` and
   `yantra_expr_parser.ml` (the dead copy).

2. **Three-place op registration** — adding a new primitive required:
   - A `.om` file in `brahman/kosha/yantra/` (arity via class membership)
   - Implementation in `yantra_eval_primitives.ml` / `yantra_ops.ml` / `yantra_pipeline_ops.ml`
   - A duplicate arity entry in `register_primitive_arities()` in `yantra_eval_primitives.ml`
   The third was redundant with the first but necessary because graph arities aren't
   loaded until `build_index` runs, after parse time.

3. **Hardcoded boundary keywords** — `is_boundary` was a hardcoded `match` expression.
   Adding new syntax constructs required manually editing `is_boundary`. The set of
   boundary keywords was not self-describing and differed between `yantra_parser.ml`
   (7 + 6 scan keywords) and `yantra_arity.ml` (7 only — missing the scan keywords).

---

## What was done

### Step 1 — Fix `parse_cond` in `yantra_parser.ml` ✅

Added `| [] | ")" :: _ | "]" :: _` as the first match arm in `parse_cond` to stop
recursion at enclosing-expression boundaries. Verified 253 tests still passed.

### Step 2 — Patch `yantra_arity.ml` ✅

- Replaced hardcoded 7-keyword `is_boundary` match with a hashtable registry:
  `_boundary_keywords`, `register_boundary_keyword`, `is_boundary` via `Hashtbl.mem`
- Updated `pre_scan_tantra_file` to handle new-style tantras:
  - bare `takes` → section `"inputs"`
  - `takes <name> [type]` inline → parse param + section `"body"`
  - `return <name>` inline → section `"return"`
- Boundary set starts empty — populated at runtime by `register_primitive_arities`

### Step 3 — Patch `yantra_expr_parser.ml` ✅

Full rewrite of the dead module to match `yantra_parser.ml` plus fixes:
- Added `try_parse_infix` — `X is Y`, `X is not Y`, `X is empty`, `X is not empty`, `X exists`
- Added `parse_destructure_pattern` — `fn [x, y] -> ...` list destructuring
- Split `parse_expr` into infix wrapper + `parse_expr_primary`
- Upgraded `fn` handler — `collect_params` with destructuring + wrappers
- Added `parse_from` — `from ... where [...] ... collect expr`
- Added `parse_scan` — `scan ... with var=init ... when/emit/set/clear/otherwise`
- Fixed `parse_cond`:
  - `| [] | ")" :: _ | "]" :: _` stop arm at top
  - Removed greedy trailing-paren consumption in `"(" :: rest` arm
  - `_ ->` arm checks `is_boundary` before consuming, and checks for boundary
    after parsing guard (handles case where guard is actually the else value)

### Step 4 — Patch `yantra_tantra_file.ml` ✅

Added new-style tantra parsing to `parse_tantra_file`:
- bare `takes` → section `"inputs"`
- `takes <name> [type]` inline → parse param + section `"body"`
- `return <name>` inline → parse return param + section `"return"`
- `"body"` section handler → feeds `let_lines`
- Second-pass fallback for new-style tantras where `let_lines` is empty after first pass

### Step 5 — Wire dune + fix call sites ✅

`vyakarana/lib/dune` — added 4 modules, kept `yantra_parser` for now:
```
yantra_tokeniser yantra_arity yantra_sentence_parser
yantra_expr_parser yantra_tantra_file
```

Call sites updated:
- `yantra_index.ml`: removed `open Yantra_parser`; updated 4 references:
  - `parse_tantra_file` → `Yantra_tantra_file.parse_tantra_file`
  - `Yantra_parser.pre_scan_tantra_file` → `Yantra_arity.pre_scan_tantra_file`
  - `Yantra_parser.register_tantra_arity` → `Yantra_arity.register_tantra_arity`
  - `Yantra_parser.register_graph_op_arity` → `Yantra_arity.register_graph_op_arity`
- `yantra_eval_primitives.ml`: `Yantra_parser.register_graph_op_arity` → `Yantra_arity.register_graph_op_arity`
- `yantra.ml`: `Yantra_parser.parse_expr_string` → `Yantra_expr_parser.parse_expr_string`

### Step 6 — Populate boundary registry ✅

Added to `register_primitive_arities()` in `yantra_eval_primitives.ml`:
```ocaml
let b = Yantra_arity.register_boundary_keyword in
List.iter b [")" ; "]" ; "," ; "in" ; "done" ; "let" ; "otherwise"];
List.iter b ["when" ; "emit" ; "set" ; "clear" ; "return"];
List.iter b ["where" ; "collect" ; "with"];
```

### Step 7 — Delete `yantra_parser.ml` ✅

Deleted. `dune build` clean. 253 tests still passing.

### Step 8 — Update `test_interpreter.py` ✅

- `test_cond_inside_reduce_ascending_list` — removed ascending-only workaround; now tests
  full max reduction over arbitrary list `[3,1,4,1,5]` → 5.0
- `test_cond_inside_map_numeric` — removed limitation comment; now tests else-branch
  fires for negative inputs: `map [-1, 2, -3] (fn x -> cond (gt x 0) x 0)` → `[0, 2, 0]`
- Added `test_cond_else_branch_in_reduce` — direct regression test for the parse_cond bug
- Added `test_cond_otherwise_branch` — tests explicit `otherwise` clause

---

## Final module structure

```
yantra_tokeniser.ml        owns: tokenise_expr
yantra_arity.ml            owns: arity tables, boundary registry, pre_scan
yantra_sentence_parser.ml  owns: try_sentence_form
yantra_expr_parser.ml      owns: all expression parsing (parse_expr, parse_cond, parse_from, parse_scan)
yantra_tantra_file.ml      owns: strip_comment, parse_let_block, parse_tantra_file
yantra_parser.ml           DELETED
```

---

## parse_cond — final correct implementation

```ocaml
and parse_cond (branches : (expr * expr) list) (tokens : string list) : expr * string list =
  match tokens with
  | [] | ")" :: _ | "]" :: _ ->
    (Cond (List.rev branches, Var "_none"), tokens)
  | "otherwise" :: rest ->
    let (default, rest') = parse_expr rest in
    (Cond (List.rev branches, default), rest')
  | "(" :: rest ->
    let (guard, rest') = parse_expr rest in
    let rest' = match rest' with ")" :: r -> r | r -> r in
    let (body, rest'') = parse_expr rest' in
    (* NOTE: do NOT consume trailing ) here — it belongs to the enclosing expr *)
    parse_cond ((guard, body) :: branches) rest''
  | _ ->
    if Yantra_arity.is_boundary (List.hd tokens) then
      (Cond (List.rev branches, Var "_none"), tokens)
    else
      let (guard, rest') = parse_expr tokens in
      (match rest' with
       | [] | ")" :: _ | "]" :: _ ->
         (Cond (List.rev branches, guard), rest')
       | tok :: _ when Yantra_arity.is_boundary tok ->
         (Cond (List.rev branches, guard), rest')
       | _ ->
         let (body, rest'') = parse_expr rest' in
         parse_cond ((guard, body) :: branches) rest'')
```

Key lesson: the `"(" :: rest` arm must NOT consume a trailing `)` after the body —
that paren belongs to the enclosing `(fn ... -> ...)` grouping, not to `cond`.

---

## Adding a new op — the new process

After this refactor, adding a primitive op requires exactly two things:

1. **`.om` file** in `brahman/kosha/yantra/op-<name>.om` — declares the op node and
   its arity class. Graph arities are loaded from this at startup.

2. **Implementation** in the appropriate `eval_*` file:
   - Graph/field ops → `yantra_eval_primitives.ml` in `eval_graph_op`
   - Pure (string/list/math) ops → `yantra_ops.ml` in `eval_pure_op`
   - Pipeline ops → `yantra_pipeline_ops.ml` in `eval_pipeline_op`

The `register_primitive_arities()` entry is **only needed** for ops that don't have
a `.om` file (i.e. primitive ops that predate the graph-arity system). New ops
should always use the `.om` file path — the duplicate OCaml entry is then redundant
and should not be added.

For new **syntax keywords** (boundaries for `from`/`scan` or new constructs): add
`register_boundary_keyword "keyword"` in `register_primitive_arities()`. One line.

---

## Regression guard

```
Before: 253 passed, 22 xfailed
After:  255 passed, 22 xfailed  (+2 new cond tests)
```
