# Session Notes — 2026-03-13

## How to Run Tests

```bash
cd vyakarana

# run all suites
bash scripts/run-tests.sh

# run one suite
bash scripts/run-tests.sh avrti
bash scripts/run-tests.sh lookup
bash scripts/run-tests.sh match
bash scripts/run-tests.sh bqg
bash scripts/run-tests.sh context
bash scripts/run-tests.sh triples
bash scripts/run-tests.sh primitives

# run multiple suites
bash scripts/run-tests.sh avrti match
```

Tests live in `brahman/yantra/tests/<suite>/test-*.tantra`.
Each test returns `bool` — `true` = pass.
The runner discovers tests recursively and prints `[PASS]`/`[FAIL]` per test.

## Current Test State (2026-03-12)

| Suite | Pass | Fail | Notes |
|---|---|---|---|
| primitives | 5 | 0 | ends-with, substr, split-numeric |
| lookup | 7 | 0 | word-node, abbrev, plural inversion |
| context | 3 | 0 | find-context empty/active/pending |
| triples | 3 | 0 | emit-triples intent/concept/mithya |
| bqg | 7 | 1 | 1 known fail: compound unit (m/s) |
| avrti | 5 | 0 | compound resolution, fixpoint |
| match | 0 | 4 | blocked by lambda arity bug (see below) |

**Total: 30 pass, 5 fail** (4 in match are the same root cause)

## Critical Bug Found: Lambda Variable Name Collision

### The Problem

Any lambda parameter named after a registered op **silently breaks** ops used in the lambda body.

Example:
```
reduce vals "" (fn va pair ->
  cond (eq (nth pair 0) r) (nth pair 1) otherwise va)
```
`pair` is a registered op (from `op-pair.om`, class `op-class-constructor`, `parse-arity:-1`).
Inside the lambda body, the parser sees `nth pair 0` and tries to parse `pair` as a
**variadic call** (arity -1), consuming `0 r` etc. as its args. `nth` then gets 0 args
from the outer call and raises `Failure("nth")`.

The result looks like the op name as a string: `reduce [...] "" (fn va pair -> nth pair 0)`
returns `"nth"` — `nth` was parsed as `Var "nth"` (arity 0) because `pair` consumed
the args it needed.

### The Fix

**Rename lambda parameters to avoid op names.**

Known op names to avoid as lambda params:
- `pair` — constructor op (`op-pair.om`)
- `map`, `filter`, `reduce` — higher-order ops
- `add`, `mul`, `sub`, `div` — monoid/binary ops
- `concat`, `split`, `join` — string ops
- Any name that appears as `name:X` in a `brahman/kosha/yantra/op-*.om` file

Safe naming conventions:
```
fn acc item ->       (not: fn acc pair ->)
fn acc tri ->        (for triples)
fn acc rule ->       (for rules)
fn acc kv ->         (for key-value pairs)
fn total elem ->     (for accumulation)
```

### Why `(nth pair 0)` vs `nth pair 0` doesn't help

The `(nth pair 0)` form — parens around the call — doesn't fix it because `pair`
is parsed as the first arg BEFORE the paren is seen. The issue is the arity lookup
happening at the arg collection level, not at expression boundary.

### Systematic Fix for `match-mantra.tantra`

In `match-mantra.tantra`, rename `pair` → `kv` (or `entry`) in the value lookup reduce:
```
-- before (broken):
let v = reduce vals "" (fn va pair ->
  cond (eq (nth pair 0) r) (nth pair 1) otherwise va)

-- after (fixed):
let v = reduce vals "" (fn va kv ->
  cond (eq (nth kv 0) r) (nth kv 1) otherwise va)
```

## Arity Registrations Added (yantra_eval.ml)

The following ops were NOT registered with arities, causing them to silently
become `Var` (not `Call`) inside nested lambda bodies. Added to `init_eval`:

```
nth 2, length 1, append 2, flatten 1, unique 1
split 2, join 2, concat -1, string-length 1
to-string 1, to-number 1, abs 1, not 1, exists 1
eq 2, neq 2, lt 2, le 2, gt 2, ge 2, and 2, or 2
sub 2, map 2, filter 2, reduce 3
lookup 1, shabda 2, walk-in 2
fixpoint 2, iterate 3
```

Note: `add`, `mul` already have `parse-arity:2` in their `.om` files so they're fine.
`member`, `substr`, `word-node` etc. were already registered.

## New Things Built This Session

### OCaml
- `fixpoint` primitive in `yantra_ops.ml` — apply fn until output = input (cap 20)
- `iterate` primitive in `yantra_ops.ml` — apply fn exactly N times
- Comprehensive arity registrations in `yantra_eval.ml`

### Tantras
- `avrti-refine.tantra` — one pass of question graph refinement (compound resolution)
- `match-mantra.tantra` — find mantra whose krama-rhs are all bound (needs rename fix)

### Op Nodes (already existed as stubs)
- `op-fixpoint.om`, `op-iterate.om` — now backed by OCaml

## Architecture: Multi-Pass Avrti

The full pipeline is:
```
sentence
  → build-question-graph   (pass 1: linear word scan)
  → fixpoint avrti-refine  (passes 2+: compound resolution, mithya→satya)
  → match-mantra           (find mantra with all krama-rhs bound)
  → execute-chain          (run the mantra's krama stack machine)
  → narrate-response       (compose answer with understanding trace)
```

### Why multi-pass

Pass 1 (linear scan) processes each word independently. "kinetic" → mithya,
"energy" → active concept. But "kinetic-energy" is the actual node.

Pass 2 (avrti-refine) sees the full graph: `[kinetic, mithya]` before `[energy, active]`
→ tries `lookup "kinetic-energy"` → HIT → replaces both with `[kinetic-energy, active, concept]`.

Pass 3 would handle unit resolution against active concept's expected unit, etc.

Fixpoint terminates when graph stops changing.

### avrti-refine current rules (pass 2 only)

| Pattern | Action |
|---|---|
| `[w, mithya]` immediately before `[c, active, concept]` | try `lookup "w-c"`. hit → replace both with `[w-c, active, concept]` |

Future rules (not yet written):
- `[c, active]` + `[val, pending-number]` + `[u, mithya]` → try unit match
- Remap value bindings from component to compound after compound resolution

## What's Next

1. **Fix `match-mantra.tantra`** — rename `pair` → `kv` in the inner reduce
2. **Verify match suite** — all 4 match tests should then pass
3. **Write `narrate-response.tantra`** (P8-D2)
4. **Write `anuvada-ganana.tantra`** — wires BQG + avrti + match + execute + narrate
5. **More test suites** — graph/, mantra/, primitives/ from `tantra-testing.md`

---

# Session Notes — 2026-03-13 (late session)

## Current Test State (after graph formalization + signal-based R8)

| Suite           | Pass | Fail | Notes |
|---|---|---|---|
| primitives      |  5   |  0   | |
| lookup          |  9   |  0   | |
| context         |  3   |  0   | |
| triples         |  3   |  0   | |
| triples2        |  3   |  0   | |
| bqg             |  8   |  0   | bqg-sum-mithya moved to dvandva |
| avrti           |  5   |  0   | |
| avrti2          |  5   |  0   | |
| match           |  4   |  0   | |
| match2          |  4   |  0   | |
| formalization   |  6   |  0   | NEW: dim registration, emit-node, walk, materialize |
| dvandva         |  5   |  7   | R5/R6/R7 not implemented |
| entity          |  9   |  5   | R8 signal-based done, R9/R10/R11 not yet |

**Total: 69 pass, 12 fail** (up from 63/13 → 52/18 at start of session)

Run with:
```bash
cd vyakarana && bash scripts/run-tests.sh dvandva entity
```

## What Was Done This Session

### Pass1 rewrite: mithya accumulation
The single `pending` string was silently dropping consecutive mithya words. Changed to
a pending LIST — all mithya words accumulate, only the last is the compound candidate,
all earlier ones flush to output. Fixed: "ball" being dropped in "ball has mass".

### Grammar nodes for possession signals
Created `verb-has.om` (role:possession) and `prep-with.om` (role:possession). These are
queried by R8 via `shabda (lookup-word word) "role"` — graph-driven, not hardcoded.
Added `role:possession` to the exclusion list in `emit-triples` `is-concept` check.

### R8 implemented: entity-from-possession
Pass1c scans for `[label,mithya] + [possession-word,mithya] + [concept,active]` pattern.
Uses graph lookup for possession role. Emits `[entity]` + `[owner]` triples.
Ownership currently propagates positionally — NEEDS REWORK to signal-based.

### R4b implemented: symbol-binding
Pass1d detects mithya label after owned active concept → `[concept, symbol, label]`.
Handles "ball has velocity v1" → `[velocity, symbol, v1]`.
Currently over-fires on back-references — NEEDS GUARD.

### Punctuation stripping in BQG
Trailing `.` `?` `!` `,` stripped from words for clean lookup. Punctuation emitted as
`[punct, punct, punct]` structural triples. Numbers with commas still handled by
split-numeric. Fixed: "m/s." "ball." "velocity?" all now resolve correctly.

### Complex sentence testing
Tested 6 paragraph-length physics problems. Identified 10 issues (documented in
scene-understanding.md). Key insight: scope control = signal-based ownership, not
positional propagation.

## Key Insight: The Sentence IS the Graph

Groups are not segments or partitions. They are subgraphs connected by edges.
Entity ownership is an edge. Pronoun reference is an edge. Dvandva membership is an edge.
There is no separate "scope" or "group annotation layer" — the graph IS the structure.

Every ownership relationship must come from an EXPLICIT signal in the sentence:
- `has` / `with` / `of` / `have` → possession signal → ownership edge
- `its` / `their` / `those` → pronoun → cross-group reference edge
- `the` + known entity → back-reference, not new entity
- `and` + concept → property dvandva (same owner continues)
- `and` + mithya + possession → entity dvandva (new owner starts)

No positional propagation. No scope resets. Just signals → edges.

## Remaining Issues

| # | Issue | Category | Status |
|---|---|---|---|
| 1 | R8 positional propagation needs signal-based rework | Architecture | DONE — intent/punct clears entity scope |
| 2 | R4b false fires on back-references | Guard needed | DONE — entity-name guard blocks back-reference |
| 3 | `"is moving with"` → false entity from verb+with | Verb detection | Open |
| 4 | `"of"` dual role (possession vs "square root of") | Context-dependent | DONE — "of" checked in R8 cond branch |
| 5 | `"have"` not recognized as possession | Grammar node needed | DONE — verb-have.om created |
| 6 | `"the"` + entity back-reference not implemented | R11 | Open |
| 7 | `"total"` → `complete` wrong resolution | Kosha investigation | Open |
| 8 | `"change in"` as concept, not modifier | Classification gap | Open |
| 9 | Entity naming `ball A` → `ball-A` not implemented | R9 | Open |
| 10 | Per-entity value scoping for same concept | Architecture | Open |

## What Was Done This Session (graph formalization)

### Phase 0 — Foundation
- Created `brahman/sangati/prashna/` with 15 sangati nodes for question graph edge types
- Renamed root node to `q-prashna` (avoids collision with grammar `prashna`)
- Added 14 dimension claims to `visheshanam-ring.om` (`active-yukta`, `mithya-yukta`,
  `q-owner-yukta`, etc.)
- All 14 dimensions registered (indices 10–32), dimension-count = 36

### Phase 1 — Materialization bridge
- Created `materialize-question-graph.tantra` — converts VList triples to proof-graph
  nodes via `emit-node`, making edges walkable by `walk`/`walk-in`/`has`/`edges`
- 6 formalization tests all pass: dimension registration, emit active node, ownership
  edge (bidirectional walk), materialize simple graph, non-transitive ownership

### Phase 2 — Signal-based R8 + R4b guards
- R8 rewrite: entity scope now clears on intent triples and sentence punct (.?!)
- R8: "of" recognized as possession signal (inlined in cond branch)
- R4b guard: entity names no longer symbol-bound (back-reference protection)
- `verb-have.om` grammar node created (role:possession)
- Key discovery: adding `let X = or ...` as 7th let inside `fn` lambda breaks
  tantra parser. Workaround: inline expressions into cond branches or pre-compute
  outside the reduce.
