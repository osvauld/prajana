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

## Current state (2026-03-18, session 7)

**412 passed / 19 xfailed / 0 failing**

### Completed

**Phase 0** — OCaml bootstrap ✓
- `yantra_tantra_file2.ml` — variadic op (`arity=-1`) parsing, zero-input tantra body parse, `debug-print`
- `yantra_index.ml` — two-pass loading, `yantra_arity.ml` — tantra2 prefix

**Phase 2** — Pipeline tantras migrated ✓

| File | Status | Notes |
|---|---|---|
| `vishesa-instance.tantra2` | ✓ | typed scan state |
| `rashi-viveka.tantra2` | ✓ | gate-edge scan |
| `vishesa-bandhana.tantra2` | ✓ | reduce lambda |
| `agra-bandha.tantra2` | ✓ | generic proximity-binding |
| `sankhya-bandha.tantra2` | ✓ | simple last-active scan |
| `rashi-anuvada.tantra2` | ✓ | instance→concept bridge |
| `avrti.tantra2` | ✓ | spreading activation |
| `avrti-refine.tantra2` | ✓ | pipeline orchestrator |
| `match-mantra.tantra2` | ✓ | mantra matching with forward/inverse |
| `derive-step.tantra2` | ✓ | forward chaining |
| `execute-math.tantra2` | ✓ | math-op execution |
| `execute-chain.tantra2` | ✓ | kriya-tantra dispatch |
| `invert-math.tantra2` | ✓ | pratipaksha inversion |
| `physics-mantras.tantra2` | ✓ | all physics mantra nodes |
| `anuvada-ganana.tantra2` | ✓ | outer pipeline orchestrator |
| `session-anuvada.tantra2` | ✓ | session-aware wrapper |
| `execute-matched.tantra2` | ✓ | executor dispatch + answer formatting |
| `build-question-graph.tantra2` | ✓ | entry point for every query |
| `emit-triples.tantra2` | ✓ | word→triple dispatch |
| `find-context.tantra2` | ✓ | active-concept + pending-num |
| `sandhi-viveka.tantra2` | ✓ | grammar structure discernment |
| `kosha-expand.tantra2` | ✓ | PPR expansion |
| `sandhi-kosha.tantra2` | ✓ | compound word resolution |
| `sandhi-avastha.tantra2` | ✓ | avastha qualification |
| `sandhi-bandhana.tantra2` | ✓ | binding reattribution after compound |

**New shared tantras (session 7):**
| `flush-pending-mithya.tantra2` | ✓ | drain mithya buffer → triples |
| `satya-concepts.tantra2` | ✓ | extract satya node names from graph |
| `bound-concept-names.tantra2` | ✓ | concept names with sankhya bindings |

**New shared tantras extracted:**
| File | Replaces |
|---|---|
| `extract-solve-for.tantra2` | identical block in anuvada-ganana, session-anuvada, match-mantra |
| `bound-vals.tantra2` | identical block in derive-step, match-mantra |
| `bound-concepts.tantra2` | identical pattern in 5 tantras |
| `resolve-janya-args.tantra2` | identical block in execute-math, execute-chain, invert-math |
| `physics-mantras.tantra2` | `walk-in "physics-mantra" "varga"` in 3 tantras |

**Updated to call new shared tantras:**
- `anuvada-ganana.tantra`, `session-anuvada.tantra` → `extract-solve-for`
- `derive-step.tantra2`, `match-mantra.tantra2` → `bound-vals`, `physics-mantras`
- `execute-math.tantra`, `execute-chain.tantra` → `resolve-janya-args`
- `mantra-coverage.tantra`, `vishesa-instance.tantra2` etc. → `bound-concepts`

### Remaining to migrate (Phase 2 tail)

| File | Priority | Notes |
|---|---|---|
| `vibhakti-shashthi.tantra` | medium | 8-branch scan, 3 state vars |
| `materialize-question-graph.tantra` | low | 12-branch edge dispatch |
| `unit-of-concept.tantra` | low | 3-path kosha walk |
| `try-morpheme-rules.tantra` | low | morpheme inversion |
| `lookup-word.tantra` | low | 3-step lookup chain |
| `varga-inheritance.tantra` | low | boot pass |
| `reboot.tantra` | low | calls varga-inheritance |
| `mantra-coverage.tantra` | low | debug — uses bound-concept-names |
| `debug-bound-concepts.tantra` | low | debug only |
| equations/*.tantra (10 files) | delete | execute-math covers these |
| debug tantras (4 files) | delete | guard-test, not-member-test, etc |

### Phase 3 — New tantras (not yet built)

| Tantra | What it does | Unblocks |
|---|---|---|
| `sthita-viveka.tantra2` | Scope-aware slot resolution for tinanta interactions | All dvandva xfails, gravitational-force, N-entity |
| `varga-viveka.tantra2` | Domain routing from active concept varga membership | Self-directing pipeline, cross-domain queries |
| `sambandha-viveka.tantra2` | Discover possible interactions from co-present entities | Group formation, aneka-eka recognition |
| `dvandva-setu.tantra2` | Create interaction entity from co-present bodies | Multi-body mantras |
| `match-or-derive.tantra2` | Extract shared match→enrich→rematch from anuvada-ganana + session-anuvada | Code deduplication |

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

### 12. Local variable name must not clash with a tantra name

When `eval` looks up `Var "bound-concepts"` and the local env doesn't have it,
it falls through to `eval_ctx.ctx_index.by_name` and finds the `bound-concepts`
tantra — returning `VFn(...)` instead of the local list. `length VFn = 0`.

**Wrong:** `bound-concepts = nth bv 0` (clashes with `bound-concepts.tantra2`)  
**Right:** `bcs = nth bv 0` (safe short name)

**Rule:** Never name a local binding the same as a loaded tantra. Safe short names:
`bcs` (bound-concepts), `bv` (bound-vals), `vps` (val-pairs), `sf` (solve-for).

### 13. Zero-input tantras: body must start with `=` or `takes`

A tantra with no `takes` and no `inputs` has its first body line mistakenly parsed
as an input parameter if it doesn't contain `=`. The parser fixed: if a line in
`"header"` section contains `=`, it's treated as a body binding (not a param).

**Safe pattern:**
```
tantra2 my-tantra
result = walk-in "physics-mantra" "varga"
return result
done
```
The `result = ...` line contains `=` → parsed as body. ✓

### 14. `cond` predicate that closes to depth 0 — consequence must be on same line

The line-joiner tracks paren depth. A `cond` whose predicate is a balanced
paren expression (`(gt (length x) 0)`) closes back to depth 0. The next line
then starts a NEW binding, not the cond consequence.

**Wrong:**
```
candidates = cond (gt (string-length solve-for) 0)
  (filter mantras ...)    ← depth=0 here, treated as new binding
  otherwise mantras
```

**Right — keep consequence on same line as predicate:**
```
candidates = cond (gt (string-length solve-for) 0) (filter mantras ...) otherwise mantras
```

**Right — wrap entire cond in outer parens:**
```
result = (cond (gt (length x) 0) forward-match
  otherwise inverse-match)
```

The outer `(` keeps depth > 0 across lines until the outer `)`.

### 16. Tantra names used as function values must be wrapped in a lambda

When passing a tantra as a value to `fixpoint`, `map`, or `reduce`, the tantra name
has arity > 0 in the pre-scan table. The parser will try to consume the next token
as the tantra's argument, not leave it as a value.

**Wrong:** `refined = fixpoint raw-graph avrti-refine`
— `avrti-refine` has arity 1. Parser tries to consume next token as arg. If none
  available, throws `parse2_primary: empty` → binding silently dropped → `VNone`.

**Right:** `refined = fixpoint raw-graph (fn g -> avrti-refine g)`
— explicit lambda wraps the call. `fixpoint` receives a `VFn`, applies it each step.

Same applies to `derive-step`, `match-mantra`, and any other arity-1 tantra.

### 18. Graph op names as local bindings cause silent Failure("nth")

The arity table has two sources: tantra pre-scan AND graph op nodes (registered via
`register_graph_op_arity` from kosha nodes with `kriya` → class with `parse-arity`).

Known graph op names with arity > 0 that LOOK like ordinary words:
- `node` — arity 1
- `role` — arity 1
- `layer` — arity 1
- `value` — arity 1 (documented in Rule 2)

When these appear in the RHS of a binding as operands (not call targets), the parser
treats them as function calls and consumes the next token as their argument. This
silently corrupts the expression tree. The `Failure("nth")` at runtime is the
symptom — it means a later `nth` call received fewer args than expected because a
prior token was stolen.

**Fix**: use short safe abbreviations. For `emit-triples` and similar tantras:
- `node` → `nd`
- `role` → `rl`  
- `layer` → `ly`
- `num-val` → `nv`
- `unit-node` → `un`
- `active` → `ac`
- `pending` → `pn`

**Detection**: `c.eval('node "x"')` returns `None` (not `'node'`) → arity > 0.
`c.eval('nd "x"')` returns `'nd'` → arity 0 → safe.

### 19. Variadic ops (`append`, `concat`, `add`) consume across `let` boundaries inside lambdas

Inside a `fn` body, variadic ops collect tokens until a boundary keyword. The
boundary list (line 304 of `yantra_tantra_file2.ml`) includes `let`, `return`,
`done`, `)`, `]`, `}`, `|`, `->`, `when`, `otherwise`, `in`. But NOT bare
expressions like `(cond ...)`.

**Wrong (inside fn body):**
```
let with-word = append g triples
(cond ...)
```
`append` is variadic and greedily consumes `(cond ...)` as a third arg. The
`LetIn` body becomes empty → lambda returns `")"` (the leftover close paren).

**Right:**
```
let with-word = (append g triples)
(cond ...)
```
The outer parens bound `append`'s arg collection. `(cond ...)` is then the `LetIn` body.

**Rule**: any variadic op call that appears in a `let` binding where the NEXT
thing is NOT a boundary keyword must be wrapped in parens.

### 17. Reserved or computed names: avoid `executor`, `exec-args`, `solve-for` as local vars

Variable names that silently mismatch with primitives or arity-table entries cause
wrong parse trees. Discovered via systematic isolation:
- `executor` — caused `call-tantra executor ea` to fail even when both vars had correct values
- `exec-args` — similar issue in certain positions
- `solve-for` — is the second param of `execute-matched`; using it as a local in the
  caller causes env shadowing

**Safe names used:** `exe`, `ea`, `sf` (for solve-for), `mm` (for match result).

### 15. `debug-print` shows `VNode` as `?`

The `show` function in `debug-print` only handles `VString`, `VBool`, `VFloat`,
`VNone`, `VList`. Graph node values (`VNode`) print as `?`. This is correct —
the actual node IS there, just not human-readable via debug-print.

To see the node name: `debug-print (to-string mynode)`.

---

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-17 | Initial writing. Layer 2 decision made. agra-bandha/sthita-viveka/dvandva architecture understood. Full four-phase plan written. |
| 2026-03-17 | Phase 0 + Phase 2 Steps 1-3 completed. 407 passing (+15). 10+ parser bugs found and fixed. Layer 2 authoring rules documented from experience. |
| 2026-03-17 | Session 2: variadic arity=-1 bug fixed. 409 passing. |
| 2026-03-17 | Session 3: Phase 2 Steps 4-6 migrated. Session binding fixed. 412 passing / 0 failing. |
| 2026-03-17 | Session 4: avrti, match-mantra, derive-step, execute-* migrated. 5 shared tantras extracted. 4 new authoring rules (12-15). 412 passing. |
| 2026-03-18 | Session 5: anuvada-ganana, session-anuvada, execute-matched migrated. 2 new authoring rules (16-17). 412 passing. |
| 2026-03-18 | Session 6: build-question-graph, emit-triples, find-context, sandhi-viveka migrated. 2 new authoring rules (18-19). parse-error sentinel added to OCaml. 412 passing. |
| 2026-03-18 | Session 7: kosha-expand, sandhi-kosha, sandhi-avastha, sandhi-bandhana migrated. 3 shared tantras extracted (flush-pending-mithya, satya-concepts, bound-concept-names). 6 callers updated. 2 new authoring rules (20-21). 412 passing. |
