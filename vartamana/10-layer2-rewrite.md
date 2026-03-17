# 10 — Layer 2 Tantra Rewrite

**This is the immediate active plan. Everything else waits.**

The tantra language must match its own purpose. Tantras describe understanding.
They should read like understanding. The current Layer 1 syntax fights itself at
every structural turn — nine documented tensions, each a crack in the foundation.
The understanding has now deepened enough to see what the rewrite must become.

The 350+ passing tests are the contract. They hold the rewrite honest.
Breaking changes are expected. The tests will catch regressions and confirm
when each step is correct.

---

## What we understood today

Three passes — `vishesa-instance`, `rashi-viveka`, `vishesa-bandhana` — are all
the same movement: **proximity binding via a moving anchor**. The most recently
seen instance of a concept IS the agra — the foremost. Bindings attach to agra.
Agra updates forward as new instances arrive. The sequence IS the scope.

We named this `agra-bandha` and wrote it as a shared primitive. But Layer 1
syntax prevented the abstraction from being clean — Tension 7 (let inside fn),
Tension 3 (outer let invisible in scan), Tension 2 (arity table) all constrained
what could be expressed.

Then deeper: `sthita` / `aneka-eka` / `eka-aneka` — the kosha already declares
the interaction structure. `coulomb` has `particle-a-sthita particle-b-sthita`.
`bond` has `particle-a-sthita particle-b-sthita`. `gravitational-force` has
`aneka-eka-swarupa`. The pipeline doesn't read this yet. It treats all nodes as
flat concepts.

The three kinds of nodes the kosha already declares:
- **Subanta** — a quantity node. Scalar value. Belongs to one entity.
- **Tinanta** — a process/interaction node. Has `sthita` slots. Has `phala`. Has `kriya`.
- **Varga** — a containment node. Members via `vishesa` or `varga` edges.

`match-mantra` and `derive-step` are flat. They look for `[concept, sankhya, val]`
in a flat namespace. They cannot see entity scope. They cannot see interaction
structure. `sthita-viveka` — the scope-aware lookup — cannot be written cleanly
in Layer 1 syntax.

Layer 2 is not cosmetic. It is the prerequisite for the architecture the kosha
already encodes.

---

## The three tensions Layer 2 eliminates structurally

**Tension 7 — `let` inside `fn` body split by file parser.**
The Layer 1 file parser detects `name = ...` lines and splits them as top-level
bindings even inside `fn` bodies. This caused `varga-inheritance` to silently
emit nothing for 351ms.

Layer 2 fix: the file parser tracks block depth. Inside a scan body or `fn` body
(marked by `->` and indentation / brace depth), `name = ...` is always assignment,
never binding-start.

**Tension 3 — Outer `let` bindings invisible in scan guards.**
Variables defined in the outer let block cannot be used directly in `scan ... when`
guards. They must be threaded in as scan state (`let flag be computed-value`).
This caused the `vishesa-instance` can-promote regression — `given` was promoted
to a rashi instance of `momentum`.

Layer 2 fix: typed scan state `[name: type = init-expr]` initialises from outer
let bindings at scan entry. Full outer scope access. No paren workarounds.

**Tension 2 — Arity table drives parsing.**
Whether `f a b` means "call f with 2 args" or "f with args until boundary" depends
on a runtime arity table. Silent truncation when wrong. No error.

Layer 2 fix: parse form determines meaning. `fn x ->` and `{ }` have explicit
boundaries. `|` pipe is explicit. No arity table needed for Layer 2 tantras.

---

## The four phases

---

### Phase 0 — OCaml bootstrap (one server restart)

**New file: `vyakarana/lib/yantra_tantra_file2.ml`**
The Layer 2 parser. ~400 lines. Produces the same `tantra` AST type as Layer 1.
The eval engine (`yantra_eval.ml`) does not change at all.

**`yantra_index.ml`** — two small changes:
1. `tantra_files_recursive`: also pick up `.tantra2` suffix
2. `load_tantra_dir`: route `.tantra2` files to the new parser
3. `pre_scan_arities`: also scan `.tantra2` files (registers input counts for
   backward-compat during migration period when Layer 1 calls Layer 2)

**One server restart** after these OCaml changes. After that: all `.tantra2`
iteration is `reload-all` only. No further OCaml changes needed for migration.

---

### Phase 1 — Write the Layer 2 parser

The new syntax the parser must handle:

| Feature | Desugars to |
|---|---|
| Pipe `\|` — `expr \| where [pat] \| collect expr` | `From(...)` — existing eval |
| Dot access — `m.name`, `m.phala` | `Call("shabda", ...)` / `Call("nth", [Call("walk",...)])` |
| Lambda — `fn x -> body` (with block-aware file parser) | `Lambda(...)` |
| Typed scan state — `[name: type = init]` | same `(string * expr) list` state_decls |
| Triple pattern heads — `[word, edge, _]` | branches with auto-bound word/edge/obj |
| `\|` in patterns — `sankhya \| matra \| vishesa` | multiple edges → `or`-combined guard |
| `when` lines — one predicate per line | `and`-chained guards |
| `->` closes guards, opens body | same `scan_branch` structure |
| State assignment `var = expr` | `SSet(var, expr)` |
| Pipe terminators: `all`, `any`, `find`, `filter` | `Call("reduce", ...)` / `Call("filter", ...)` |
| `in` / `not in` in `when` lines | `Call("member", ...)` / `Call("not", [Call("member", ...)])` |
| `!=` / `==` in `when` lines | `Call("neq", ...)` / `Call("eq", ...)` |

**Example — vishesa-instance in Layer 2 syntax (actual working file):**
```
tantra2 vishesa-instance

takes graph

owned    = graph | where [s, e, _] | and (eq e "shashthi-vibhakti") | collect s
bound    = graph | where [s, e, _] | and (eq e "sankhya") | collect s
entities = graph | where [s, e, _] | and (eq e "prathama-vibhakti") | collect s
can-promote = exists (graph | where [_, e, _] | and (eq e "rashi-bandha") | collect _it)

result = scan graph [last-agra: str = "", can-promote: bool = can-promote,
                     owned: list = owned, bound: list = bound,
                     entities: list = entities]:

  [word, satya, _] ->
    last-agra = (to-string word)
    emit

  [_, sankhya, _] ->
    last-agra = ""
    emit

  [_, matra, _] ->
    last-agra = ""
    emit

  [_, vishesa, _] ->
    last-agra = ""
    emit

  [word, mithya, _]
    when last-agra != ""
    when (member last-agra owned) or can-promote
    when not (member last-agra bound)
    when not (member word entities)
    ->
      emit [word, "vishesa", last-agra]
      emit [word, "vishesa", "rashi"]
      last-agra = ""

  _ -> emit

return result

done
```

**Key differences from the Layer 1 version and from the plan's original example:**
- `| where [s, e, _] | and (eq e "sankhya")` — NOT `| where [s, sankhya, _]`
  (pattern names in `| where` are ALL variables — see authoring rules)
- `| collect _it` — NOT `| collect _` (`_` maps to VNone, `_it` binds the whole item)
- `(to-string word)` — explicit string conversion for scan state
- No `sankhya | matra | vishesa` multi-edge pattern yet (not implemented in parser)
- No `in` / `not in` sugar yet — use `(member x list)` / `not (member x list)`
- No invisible boundary, no paren workarounds, no `can-promote-val` relay variable,
  no Tension 3 or Tension 7 possible.

---

### Phase 2 — Migrate tantras one by one

Write `.tantra2` → `reload-all` → full test suite → confirm → mark old `.tantra` for cleanup.

| Step | File | What it validates / fixes |
|---|---|---|
| 1 | `vishesa-bandhana.tantra2` | Parser loads, calls other tantras, passes lists |
| 2 | `vishesa-instance.tantra2` | Typed scan state + outer scope. Fixes `given` regression |
| 3 | `rashi-viveka.tantra2` | Gate-edge scan pattern |
| 4 | `agra-bandha.tantra2` | Abstract primitive in Layer 2. Map-update logic clean |
| 5 | `sankhya-bandha.tantra2` | Agra-discipline for N-entity sankhya binding |
| 6 | `rashi-anuvada.tantra2` | Entity-scoped propagation, no last-write-wins collapse |
| 7 | `match-mantra.tantra2` | Pipe + dot. Gains `sthita-viveka` for multi-entity matches |
| 8 | `derive-step.tantra2` | Same. Gains `sthita-viveka` for multi-body derivation |
| 9 | `avrti-refine.tantra2` | Pipeline orchestrator |
| 10 | `anuvada-ganana.tantra2` | Outer pipeline |
| 11 | `session-anuvada.tantra2` | Session entity structure — carries prathama/shashthi triples |
| 12 | All remaining | `sandhi-*.tantra2`, `vibhakti-*.tantra2`, `build-question-graph.tantra2`, etc. |

---

### Phase 3 — New tantras that Layer 2 enables

These cannot be written cleanly in Layer 1. They require clean scoped-binding syntax.

**`sthita-viveka.tantra2`**
Given a tinanta node and a question graph: for each `sthita` slot, find the entity
that fills it and return its owned quantities as `[[slot, entity, [[concept, val]...]]...]`.
Called from `match-mantra` and `derive-step`. Fixes all multi-entity computation.

Closes: all dvandva xfails, `test_gravitational_force`, N-entity paragraph tests.

**`varga-viveka.tantra2`**
Given active concepts from the question graph, walk their `varga` membership to
find the most specific shared domain. Returns the domain for routing. Makes the
pipeline self-directing — domain reads from the kosha, not hardcoded order.

**`sambandha-viveka.tantra2`**
Given two or more entities, find tinanta nodes whose `sthita` slots can be filled
by those entities' owned quantities. Returns candidate interactions. The
`aneka-eka` recogniser.

**`dvandva-setu.tantra2`**
Creates an interaction entity from co-present bodies. When a sentence mentions
two masses and a radius with a gravitational relation, `dvandva-setu` creates
the interaction node (the tinanta) that encompasses both bodies. The mantra fires
on the interaction, not on the individual bodies.

---

### Phase 4 — Full cleanup (after all tests pass)

The removal of everything Layer 1. The test suite is the contract.

**Remove `.tantra` files** (all replaced by `.tantra2` equivalents)

**Remove from OCaml:**
- `yantra_expr_parser.ml` — Layer 1 expression parser
- `yantra_tantra_file.ml` — Layer 1 tantra file parser
- `yantra_arity.ml` — arity table (not needed in Layer 2)
- `yantra_sentence_parser.ml` — sentence-form sugar parser
- `.tantra` suffix from `tantra_files_recursive`
- Old routing branch in `load_tantra_dir`

**Remove debug/test tantras:**
- `vishesa-instance-debug.tantra`
- `rashi-viveka-debug.tantra`
- `guard-test.tantra`
- `not-member-test.tantra`

**Update vartamana docs:**
- `07-tantra-rewrite.md` — Tensions 1–9 marked resolved. Layer 2 syntax is now
  the canonical tantra authoring guide. Layer 1 workarounds become historical.
- `08-boot.md` — pitfall section (Tensions 7–9) becomes historical.
- `index.md` — add this file, update file table.
- `changelog.md` — record new baseline after cleanup.

---

## What does NOT change

- **`yantra_eval.ml`** — eval engine. Unchanged. Layer 2 produces the same `tantra`
  AST. The scan evaluator, expression evaluator, from-evaluator — all unchanged.
- **`yantra_types.ml`** — type definitions. Unchanged.
- **`yantra_eval_primitives.ml`** — OCaml primitives. Unchanged.
- **`.om` kosha files** — unchanged. The kosha is jada. The rewrite does not touch it.
- **Test files** — unchanged. The tests are the contract. They do not know or care
  whether a tantra is Layer 1 or Layer 2.
- **Socket protocol** — unchanged. `reload-all`, `ask`, `eval` work identically.

---

## What this unlocks after completion

With Layer 2 stable and `sthita-viveka` + `varga-viveka` written:

- **N-entity computation** — any number of entities, each owning instances of the
  same concepts. No collapse. No last-write-wins.
- **Multi-body interactions** — gravitational force, coulomb, collision, bond —
  the tinanta structure IS the interaction. The mantra fires on the interaction node,
  pulls quantities from each sthita member's scope.
- **Cross-domain mantras** — a concept owned by one entity spans multiple vargas.
  `sthita-viveka` finds it regardless of which varga it belongs to.
- **Gap 2 — session entity structure** — `session-anuvada` carries entity structural
  triples (prathama/shashthi-vibhakti) in `se_graph`. Unblocks multi-entity session
  accumulation and pratibimba rendering.
- **Gravitational force** — `test_gravitational_force` closes. Two bodies, one
  interaction entity, G auto-supplied, r from the interaction's sthita.
- **Pratibimba** — `test_sphere_shape_swarupa` and electron simulation scene close.
  Entity structure in session → renderer can enumerate all scene objects.

---

## Current state (2026-03-17, session 3)

**412 passed / 19 xfailed / 0 failing** (was 407 / 20 / 4 at start of session 2)

All tests pass. Two pre-existing failures fixed. Two xfail markers removed.

### Completed

**Phase 0** — OCaml bootstrap ✓
- `yantra_tantra_file2.ml` — variadic op (`arity=-1`) parsing fixed
- `yantra_index.ml` — two-pass loading (`.tantra` first, `.tantra2` last)
- `yantra_arity.ml` — `"tantra2 "` prefix in pre-scan
- `debug-print` op added to `yantra_ops.ml`
- `_it` binding added to `eval_from` for `| collect (nth _it 0)` pattern

**Phase 2 Steps 1-6** — Six tantras migrated ✓
- `vishesa-instance.tantra2` — typed scan state, Tension 3 fixed
- `rashi-viveka.tantra2` — gate-edge scan, `qty` instead of reserved `value`
- `vishesa-bandhana.tantra2` — reduce lambda fully working, ownership redirects correct
- `agra-bandha.tantra2` — generic proximity-binding scan, `agra-map` state, variadic `(and ...)` guards
- `sankhya-bandha.tantra2` — simple scan with `last-active` state
- `rashi-anuvada.tantra2` — instance→concept sankhya bridge via `reduce`

Old `.tantra` originals removed for all six.

**Non-migration fixes:**
- `session-anuvada.tantra` — stores bindings under `shashthi-vibhakti` concept subjects, enabling cross-turn KE with kosha constants (e.g. `electron-mass → mass`)
- `test_rashi_entities.py::test_two_entities_ownership` — corrected assertion to check instance-level ownership (`m1 --shashthi-vibhakti--> ball1`) not concept-level

### Phase 2 remaining steps

| Step | File | Status |
|---|---|---|
| 1 | `vishesa-bandhana.tantra2` | ✓ |
| 2 | `vishesa-instance.tantra2` | ✓ |
| 3 | `rashi-viveka.tantra2` | ✓ |
| 4 | `agra-bandha.tantra2` | ✓ |
| 5 | `sankhya-bandha.tantra2` | ✓ |
| 6 | `rashi-anuvada.tantra2` | ✓ |
| 7 | `avrti-refine.tantra2` | not started |
| 8 | `build-question-graph.tantra2` | not started |
| 9 | `match-mantra.tantra2` | not started |
| 10 | `derive-step.tantra2` | not started |
| 11 | remaining pipeline tantras | not started |
| 12 | remaining utility tantras | not started |

---

## Layer 2 authoring rules (learned from migration)

These rules emerged from debugging the first three tantra migrations. They are
not arbitrary — each one was discovered by a failing test or silent mis-parse.

### 1. Pattern names in `| where` are ALL variables

Unlike scan branch patterns where `[_, sankhya, _]` auto-generates `eq(edge, "sankhya")`,
the pipe `| where [s, sankhya, _]` treats `sankhya` as a **variable name**.

**Wrong:** `graph | where [s, sankhya, _] | collect s`
**Right:** `graph | where [s, e, _] | and (eq e "sankhya") | collect s`

This is because scan branch patterns have their own `parse_triple_pattern` which
generates edge guards from literal names, while `| where` uses `eval_from` which
binds ALL pattern names as variables. The `| and (eq ...)` guard is the explicit filter.

### 2. Never use reserved op names as variables

The arity table is global. If a name has arity > 0 (from kosha `parse-arity`
or from a tantra input count), `parse2_primary` will try to collect arguments.

Known reserved names that cause silent mis-parse:
- `value` — `op-value` has `parse-arity:1` (projection op)
- `pair` — `op-pair` has `parse-arity:-1` (variadic constructor)
- Any kosha `op-*` node name

**Safe alternatives:** `val`, `qty`, `num`, `item`, `elem`, single letters (`v`, `q`, `n`).

### 3. `| collect expr` for simple pipes needs `_it`

`graph | collect (nth _it 0)` — `_it` is bound to the whole current item by `eval_from`.
Do NOT use `_` (maps to `Var "_none"` → `VNone`).

### 4. Avoid graph op names as lambda parameter names

Any name with a non-zero arity in the graph arity table will be parsed as a
function call, not a variable. This silently corrupts argument collection.

**Particularly dangerous:** variadic ops with `arity=-1` (monoid class ops) —
they greedily consume ALL remaining tokens until a boundary.

Known variadic op names to avoid: `append`, `concat`, `add`, `mul`, `or`, `and`, `pair`.
- `pair` — `op-pair` inherits `op-class-monoid` → `parse-arity:-1`
- `append` — `op-append` inherits `op-class-monoid` → `parse-arity:-1`

**Wrong:** `reduce list [] (fn acc pair -> nth pair 0 ...)`  
**Right:** `reduce list [] (fn acc kv -> nth kv 0 ...)`

**Safe lambda parameter names:** `acc`, `kv`, `elem`, `item`, `x`, `s`, `e`, `i`, `n`.

### 5. `cond` inside expressions must be parenthesized

`cond guard body otherwise default` is greedy — `otherwise` consumes the next
`parse2_expr` token. If `cond` is the last expression in a `LetIn` chain,
`otherwise` will consume tokens meant for the outer context.

**Safe:** `let x = (cond guard body otherwise default)` — parens contain the `cond`.
**Unsafe:** `let x = cond guard body otherwise default let y = ...` — `otherwise`
may consume `let` as the default value.

### 6. `when` guards on separate lines, `->` on its own line

For scan branches with multiple `when` guards, put each on its own line.
The `->` that opens the body should be on its own line too.

```
  [word, mithya, _]
    when last-agra != ""
    when (member last-agra owned) or can-promote
    when not (member last-agra bound)
    ->
      emit [word, "vishesa", last-agra]
```

Do NOT put `->` on the same line as the last `when` — the parser's `when ... ->`
splitting works but is fragile with complex expressions.

### 7. Edge names with `-` in scan patterns work correctly

In scan branch patterns, `[_, rashi-bandha, _]` correctly generates
`eq(edge, "rashi-bandha")` via `parse_triple_pattern`. This is DIFFERENT from
`| where [_, rashi-bandha, _]` which treats it as a variable (see rule 1).

### 8. `or` works as infix, `and` does not

`or` is an infix operator in `parse2_pipe`: `(member x list) or flag` works.
`and` was removed from `parse2_pipe` because it conflicted with `| and` guard
syntax. Use separate `when` lines for AND-chaining instead.

### 9. Variadic `(and ...)` works inside scan branch `when` guards

In `agra-bandha.tantra2`, the `allowed` computation uses:
```
let allowed = (and gated (neq agra "") (not (member concept exclude-bind)) ...)
```
This works because `and` arity=-1 (variadic monoid op) inside parens collects all
args until `)`. This is the RIGHT use of variadic ops — inside explicit parens.

### 10. `reload-all` crashes the server

The `reload-all` socket command reliably crashes the server when called during
a live session. Always restart the server fresh after any `.tantra` or `.tantra2`
file changes. OCaml source changes require `dune build` + server restart.

Do NOT use `reload-all` in scripts — it will kill the server.

### 11. `session-anuvada` stores sankhya by node name, not concept name

`session-anuvada` collects `[s, sankhya, v]` triples and stores bindings under `s`.
For sentences like "electron has mass 9.109e-31", `s = "electron-mass"` (a kosha
constant), not `"mass"` (the user-facing concept). Turn 2 sees `[electron-mass, sankhya, ...]`
but the KE mantra needs `[mass, sankhya, ...]`.

The fix: also store bindings under `shashthi-vibhakti` concept subjects from `refined`.
These are the concepts the user explicitly named. "electron has mass 9.109e-31" has
`[mass, shashthi-vibhakti, electron]` → store `mass = 9.109e-31`.

---

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-17 | Initial writing. Layer 2 decision made. agra-bandha/sthita-viveka/dvandva architecture understood. Full four-phase plan written. |
| 2026-03-17 | Phase 0 + Phase 2 Steps 1-3 completed. 407 passing (+15). 10+ parser bugs found and fixed. Layer 2 authoring rules documented from experience. |
| 2026-03-17 | Session 2: variadic arity=-1 bug fixed. 409 passing. |
| 2026-03-17 | Session 3: Phase 2 Steps 4-6 migrated. Session binding fixed. 412 passing / 0 failing. All tests green. |
