# 07 — The Tantra Rewrite

**The tantra language must evolve. Not to fix bugs — to match its own purpose.
Tantras describe understanding. They should read like understanding.**

---

## Why now — what the parser bugs revealed

Two days of parser work (2026-03-17) exposed structural tensions that cannot
be patched incrementally. Every fix created a new subtle failure.

**Tension 1 — One grammar, two semantics.**
`scan` branches and `let` expressions share `parse_expr` but mean different things.
`and` in `when edge is satya and word is "."` is a guard combinator.
`and` in `(and a b c)` is a boolean function. Same token. Different context.
Every attempt to make `or` infix at the expression level corrupted `let-in`.
Current fix: `parse_guard_atom` with `absorb_or` in `collect_and_guards` —
`or` is infix only within scan guard lines, not in general expressions.
This holds but signals the grammar needs splitting at a deeper level.

**Tension 2 — Arity table drives parsing.**
Whether `or a b` means "call or with 2 args" or "call or until boundary" depends
on a runtime arity table populated dynamically. Silent truncation when arity is
wrong — no error, wrong result. This caused the original `B` promotion failure
and the `match-mantra` regression.
Current fix: `and`/`or` are variadic (`-1`). Works because they always appear
inside explicit parens `(and a b c)` where `)` stops collection.

**Tension 3 — Outer `let` bindings are invisible in scan guards.**
Variables defined in the tantra `let` block are NOT accessible inside
`scan ... when` guard conditions. They must be passed explicitly as scan
state variables (`let can-promote be can-promote-val`). The scan state
initialisation evaluates outer `let` values at scan entry — but the guard
evaluator only sees scan state, not the outer environment.

This caused a hard regression: `vishesa-instance.tantra` was rewritten to use
bare form guards (`and member last-active owned-concepts or can-promote`).
The bare form failed silently — `owned-concepts` evaluated to `""` in the guard.
Fix: always wrap guard expressions in parens when they reference outer `let`
bindings. The existing form `((member last-active owned-concepts) or can-promote)`
works because parens force evaluation in the expression context before entering
the guard evaluator.

In Layer 2 this is solved properly: the scan header has full access to the
outer scope — no invisible boundary between `let` and `scan`.

**Tension 4 — `collect_init` ate subsequent state declarations.**
The scan state parser stopped collecting init tokens at `,`, `when`, `otherwise`
— but not at `let`. So multi-line state:
```
scan graph with let last be ""
  let owned be owned-concepts
  let bound be bound-concepts
```
Collapsed all three into `last`'s init expression. Fixed: stop at `let`.

**Tension 5 — `parse_scan_stmts` silently dropped unknown tokens.**
The catch-all `| _ :: rest -> parse_scan_stmts rest` swallowed any token that
wasn't a known stmt keyword — including `or can-promote` left over from a
mis-parsed guard. Fixed: loud failure on unexpected tokens (except `)` `]`
which are legitimate scan-body terminators when scan is inside a `cond`).

**Tension 6 — The language describes understanding but reads like OCaml.**
`from graph where [s, e, o] and e is shashthi-vibhakti collect s` is correct but
not how anyone would naturally express "find everything owned by an entity."
The gap between what a tantra means and how it reads slows both writing and review.

**Tension 7 — `let` inside `fn` bodies is split by the file parser.**
The tantra file parser (`parse_let_block`) scans lines looking for `name = ...`
patterns. Any line matching that pattern — even inside a `fn` body — is treated
as a new top-level binding. So:

```
-- BROKEN: 'let snode = ...' matches parse_let_block's name=rhs detector
_ = map nodes (fn node ->
  let snode = to-string node       ← parsed as NEW binding: snode = to-string node
  map parents (fn parent ->        ← fn body is just: map parents (fn parent ->
    emit-edge snode ...))          ← snode resolves to VString "snode", not the value
```

becomes:
```
_ = map nodes (fn node -> snode)   ← broken: fn body = just "snode"
snode = to-string node             ← "node" not in scope → VString "node"
```

**Rule:** Do NOT use bare `let x = ...` lines inside `fn` bodies in tantra files.
Instead inline the expression or use nested calls:

```
-- CORRECT: no let inside fn body
_ = map nodes (fn node ->
  map (walk node "swarupa") (fn parent ->
    cond (exists (lookup (concat (to-string parent) "-varga")))
      (emit-edge (to-string node) "varga" (concat (to-string parent) "-varga"))
    otherwise _none))
```

This is solved in Layer 2 by `{ }` lambda syntax — explicit boundaries that
the file parser cannot mistake for top-level bindings.

**Tension 8 — `graph-all-nodes` returns `VNode`, not `VString`.**
`walk`, `walk-in` and other graph traversal primitives return `VNode` items.
String operations (`concat`, `emit-edge`, string comparison) expect `VString`.
Passing `VNode` to `concat` returns `""` silently (no error).
**Rule:** Always apply `to-string` when using graph node results in string ops.
In Layer 2 this is solved by typed values — `VNode` and `VString` are
distinct types and `concat` on a `VNode` is a compile-time error.

**Tension 9 — word alias shadowing.**
`word-node` looks up the `word_index` first, before `lookup` tries the direct
node name. A `word:` shabda entry in any `.om` file that claims a word already
used by a concept node silently shadows the concept.
Example: `wave.om` had `word:wave wave, oscillation, frequency, ripple` —
`frequency` as a word returned `wave`, not the `frequency` kosha node.
**Rule:** When a word and a concept node share a name, do NOT add the word to
a different concept's `word:` shabda. The direct node name takes priority in
`lookup-word` step 2 only if step 1 (word-node) returns nothing.

**The core insight:**
The pipeline already understands natural language → graph.
The rule compiler for Layer 3 can be the pipeline itself.
Tantras should be writable in the language the system understands.

---

## The three-layer architecture

```
┌─────────────────────────────────────────────────────────┐
│  Layer 3 — Natural language rules (.rule files)          │
│  Written by domain experts. Readable without knowing     │
│  the implementation. For linguistic rules (tantras)      │
│  — the system already understands this language.         │
│  Compiled by the pipeline itself via rule-compile.tantra │
└───────────────────────┬─────────────────────────────────┘
                        │  pipeline parses → graph → compile
┌───────────────────────▼─────────────────────────────────┐
│  Layer 2 — Clean DSL (tantra IR)                         │
│  Written by us. No arity magic. No shared grammar.       │
│  Scan and expression are syntactically distinct.         │
│  `tantra2` header — new parser runs alongside current.   │
└───────────────────────┬─────────────────────────────────┘
                        │  new parser → AST → eval
┌───────────────────────▼─────────────────────────────────┐
│  Layer 1 — OCaml execution engine                        │
│  Graph storage. Pattern match. Pipeline runner.          │
│  No domain knowledge. Pure mechanics.                    │
│  Split into clean modules (see below).                   │
└─────────────────────────────────────────────────────────┘
```

---

## Layer 2 — The clean DSL

### What changes in scan branches

**Now:**
```
-- outer let bindings: NOT visible in scan guards
owned-concepts = from graph where [s, e, o] and e is shashthi-vibhakti collect s
bound-concepts = from graph where [s, e, o] and e is sankhya collect s
ent-names      = from graph where [s, e, o] and e is prathama-vibhakti collect s
can-promote-val = exists (from graph where [s, e, o] and e is rashi-bandha collect s)

-- must wrap in parens so outer lets evaluate before entering guard context
result = scan graph with let last-active be "", let can-promote be can-promote-val

  when edge is mithya
    and last-active is not ""
    and ((member last-active owned-concepts) or can-promote)
    and (not (member last-active bound-concepts))
    and (not (member word ent-names))
    let concept = last-active
    clear last-active
    emit [word, vishesa, concept]
    emit [word, vishesa, rashi]

  otherwise
    emit triple
```

Note: `owned-concepts`, `bound-concepts`, `ent-names` are outer `let` bindings.
They are visible inside guard parens because the paren expression is evaluated
in the outer env before the scan guard evaluator sees it.
`can-promote` works because it is passed as scan state (`let can-promote be ...`).

**Layer 2:**
```
scan graph [last: str = "", can-promote: bool = false,
            owned: list = owned-concepts, bound: list = bound-concepts,
            entities: list = ent-names]:

  [word, satya, _] ->
    last = word
    emit

  [_, sankhya | matra | vishesa, _] ->
    last = ""
    emit

  [word, mithya, _]
    when last != ""
    when last in owned or can-promote
    when last not in bound
    when word not in entities ->
      emit [word, vishesa, last]
      emit [word, vishesa, rashi]
      last = ""

  _ -> emit
```

Key differences:
- **Typed scan state with full outer scope access** — `owned: list = owned-concepts`
  makes `owned` a scan state variable initialised from the outer `let` binding.
  No invisible boundary. No paren workarounds needed.
- Branch head is a **triple pattern** `[word, edge, obj]` — destructure directly
- `|` in branch heads for multiple edge types: `sankhya | matra | vishesa`
- `when` lines are **separate predicate lines** — one condition per line.
  `in`, `not in`, `or` are unambiguous here. No `let-in` possible in a `when` line.
- State assignment: `last = word` not `set last to word`
- **Typed state** catches `SClear` assigning `""` to a bool at parse time
- `->` separates conditions from body
- `_ -> emit` for the default branch

### What changes in expressions

**Now:**
```
owned-concepts = from graph
  where [s, e, o]
  and e is shashthi-vibhakti
  collect s

candidates = filter mantras (fn m ->
  let mname  = shabda m "name"
  let mphala = nth (walk m "phala") 0
  or (mname is solve-for) (mphala is solve-for))

all-ok = reduce janya true (fn a r ->
  and a (or (member r (nth bound-vals 0))
            (gt (string-length (shabda r "constants-key")) 0)))
```

**Layer 2:**
```
owned = graph | where [s, shashthi-vibhakti, _] | collect s

candidates = mantras | filter { m ->
  m.name == solve-for or m.phala == solve-for }

all-ok = janya | all { r ->
  r in bound or r.constants-key != "" }
```

Key differences:
- **Pipe `|`** for chaining — left to right, no nesting, reads as a sentence
- **`{ }` lambdas** — explicit boundary. No greedy argument consumption.
  `in` inside `{ }` is unambiguous — no `let x = e in body` inside braces.
- **`.` field access** — `m.name` replaces `shabda m "name"`,
  `m.phala` replaces `nth (walk m "phala") 0`
- **`|` is pipe in expressions, `or` is disjunction in `when` lines** — no collision
- `all`, `any`, `find` as named pipe terminators

### No arity table

Parse form determines meaning — not a runtime lookup:

| Form | Meaning |
|---|---|
| `f a b` | prefix call, fixed args until boundary |
| `{ x -> body }` | lambda, explicit boundary |
| `a \| f` | pipe — `f` receives `a` as first arg |
| `a.key` | field/edge access |
| `when a op b ->` | guard line — `in`, `not in`, `or` infix |
| `+` `-` `*` `/` `==` `!=` | standard infix in expressions |

The arity table (`yantra_arity.ml`) is deprecated in Layer 2.
A tantra named `or` or `not` cannot corrupt the parser.

---

## Layer 3 — Natural language rules

A new file type: `.rule`. For **linguistic rules only** — the transformation
rules that are tantras. Not for physics formulas (see note below).

The system already understands natural language. A `.rule` file is written
in that same natural language. The pipeline parses it, produces a graph,
and `rule-compile.tantra` (written in Layer 2) compiles that graph to
a Layer 2 tantra.

**Example — `vishesa-instance.rule`:**
```
rule: vishesa-instance
purpose: promote an unlabelled word to a quantity instance

context:
  owned    = concepts owned by an entity in this graph
  bound    = concepts that already have a value
  entities = entity names in this graph

pattern:
  a known concept was just seen
  an unlabelled word follows it

condition:
  the concept belongs to an entity, or a value assignment follows
  the concept does not already have a value
  the word is not an entity name

then:
  the word is a particular instance of the concept
  the word is a measurable quantity
```

The `.rule` file is the source of truth. The `.tantra2` file is the
compiled artifact. Both live in the repository. Humans read and write `.rule`.
The machine executes `.tantra2`.

### What Layer 3 does NOT cover

**Physics formulas and kosha expansion** — adding a new formula like `r = mv/qB`
requires authoring the concept nodes (`lorentz-radius`, `magnetic-field-strength`)
with their full root connections: dimension vectors, unit edges, varga membership,
semantic relations (`abheda`, `yukta`, `sthita`). These encode what the concept
IS in the world — not just how to compute it. They cannot be derived from a formula.
They require human authorship.

The kosha must be expanded by a person who understands the domain.
Layer 3 does not change this.

---

## What Layer 3 genuinely unlocks

**Self-description.** The system can explain its own rules in natural language
because the rules ARE natural language. A user asks "how do you identify a
quantity label?" — the system reads `vishesa-instance.rule` and answers directly.

**Readable rules for review.** A linguist or physicist can read a `.rule` file
and verify it is correct without knowing the tantra DSL or OCaml. The rules
are auditable by domain experts.

**Rule authorship by domain experts.** A linguist can write a new linguistic
rule — "when a word ending in -ity follows a concept, treat it as an
abstract property" — without knowing how `scan` works. The rule compiler
handles the translation to Layer 2.

---

## OCaml restructuring — Layer 1

Current: `yantra_eval.ml`, `yantra_ops.ml`, `yantra_eval_primitives.ml` — one blob.
The scan evaluator, expression evaluator, graph query, and primitives are entangled.
This is why fixing the parser kept breaking the evaluator.

Target — five clean modules:

```
Graph_query      pure graph traversal
                 from/where/collect, walk, has, exists
                 no scan, no expression eval

Graph_scan       scan evaluator only
                 typed state, triple pattern heads, when-line guards
                 calls Expr_eval only for emit/set values

Expr_eval        functional expression evaluator
                 pipes, lambdas, field access
                 no scan knowledge

Tantra_runtime   dispatch, reload, pipeline orchestration
                 calls Graph_query, Graph_scan, Expr_eval

Primitives       string / math / list / vector utilities
                 no graph dependency
```

Each module has a clean interface. The Layer 2 parser knows which module
handles which syntactic form. No cross-module entanglement.

---

## Migration path — no flag day

The new and old parsers run side by side. A tantra file header signals which:

```
tantra  vishesa-instance    -- current syntax, current parser
tantra2 vishesa-instance    -- Layer 2 DSL, new parser
```

The `.rule` files are compiled to `.tantra2` by `rule-compile.tantra`.

Migration order:
1. **Layer 2 parser** — new `yantra_expr_parser2.ml` alongside current.
   Start with one tantra (`vishesa-instance`). Tests prove equivalence.
2. **OCaml restructuring** — split the eval blob into five modules.
   No behaviour change — tests still pass.
3. **Migrate tantras one by one** — most complex first:
   `match-mantra` → `vishesa-instance` → `rashi-viveka` → `vishesa-bandhana`
   → `execute-chain` → remaining.
   Each: write `.tantra2`, tests pass, retire old file.
4. **Layer 3 rule compiler** — `rule-compile.tantra` written in Layer 2.
   Input: a rule graph (produced by pipeline on a `.rule` file).
   Output: Layer 2 DSL text.
5. **Write `.rule` files** for existing linguistic tantras.
   `vishesa-instance.rule`, `vibhakti-shashthi.rule`, `sandhi-bandhana.rule` etc.
   The `.tantra2` files become generated artifacts — not hand-written.

---

## Boot / reboot architecture

A structural graph enrichment system runs at startup and on every `reload-all`.
This is needed because derived edges (varga membership, etc.) cannot be encoded
in `.om` files — they are computed from the loaded graph.

### The mechanism

Two OCaml primitives added:
- `emit-edge source relation target` — adds a single typed edge to the live graph
- `graph-all-nodes` — returns all node names as a `VNode` list

Two tantra files in `brahman/yantra/boot/`:
- `reboot.tantra` — orchestrator, calls all enrichment passes in order
- `varga-inheritance.tantra` — pass 1: derives varga membership edges

Two call sites in OCaml:
- `vyakarana.ml` — calls `reboot "boot"` after initial graph load + `build_index`
- `socket.ml` `reload_tantras` — calls `reboot "reload"` after re-scanning tantras

### reboot.tantra

```
tantra reboot
  inputs
    _  string       -- "boot" at startup, "reload" on reload-all

  let
  _ = varga-inheritance ""

  return "ok" any
done
```

Simple orchestrator. Add new passes here. Order matters — each pass may depend
on edges added by prior passes.

### varga-inheritance.tantra

Derives traversable `varga` membership edges from `swarupa` IS-A edges.

**Pattern:** if node `N` has `swarupa X` and node `X-varga` exists → emit `[N, varga, X-varga]`

**Example:** `kinetic-energy` → `swarupa` → `energy` + `energy-varga` exists
→ emits `[kinetic-energy, varga, energy-varga]`

**Result:** `walk-in "energy-varga" "varga"` returns `["kinetic-energy", "potential-energy", ...]`

**Why not in `.om` files:** The `"mechanical-energy-varga-vishesa"` slokas in physics
`.om` files produce NO graph edges — `vishesa` is not a registered dimension.
The IS-A relationship is encoded as `swarupa` edges to concept names (`energy`,
`force`, etc.), not to varga nodes. The `varga-inheritance` pass bridges these.

**Key implementation notes (from bugs found):**
- `graph-all-nodes` returns `VNode` items — must `to-string` before string ops
- fn bodies in tantra files must NOT contain bare `let x = ...` lines (Tension 7)
- The working form inline-evaluates everything:
  ```
  _ = map nodes (fn node ->
    map (walk node "swarupa") (fn parent ->
      cond (exists (lookup (concat (to-string parent) "-varga")))
        (emit-edge (to-string node) "varga" (concat (to-string parent) "-varga"))
      otherwise _none))
  ```

### Notes on `emit-edge` persistence

`emit-edge` calls `Proof_graph.join` which adds to `k.all_edges` (the persistent
edge list). `edges_of` and `walk-in` both read `all_edges`. Edges survive across
`reload-all` because `reload-all` only clears the tantra index, not the graph.
After `reboot` runs during `reload-all`, `materialize_csr` is called to rebuild
the CSR adjacency for PPR.

### Rules for tantra authors

| Rule | Reason |
|---|---|
| Never use bare `let x = ...` inside `fn` bodies in `.tantra` files | T7: file parser splits it as new top-level binding |
| Always `to-string` graph node results before string ops | T8: `VNode` → `concat` returns `""` silently |
| Never claim a word alias matching another concept's node name | T9: `word-node` shadows `lookup` — concept unreachable |
| Wrap `or` / `and` multi-arg calls in `(...)` | T2: arity table drives parsing, greedy consumption |
| Reference outer `let` bindings in scan guards only inside `(...)` | T3: outer env invisible in scan guard evaluator |
| Test every new tantra with a direct `eval` call before wiring to pipeline | Silent failures look like "no match", not errors |

---

## Immediate steps in vartamana context

These happen **before** the Layer 2 migration begins:

**Step 1 — Fix parser regression (today)**
Get back to 362/14. The `parse_guard_atom` + `absorb_or` approach is correct
but something in the existing tantras is still being mis-parsed.
Use `vishesa-instance-debug.tantra` + graph queries to isolate.

**Step 2 — Gap 2: session entity structure**
`session-anuvada` carries `prathama-vibhakti` and `shashthi-vibhakti` triples.
Multi-entity scenes accumulate across turns. Unblocks pratibimba.
(See `04-entities.md` Gap 2, `05-session.md`.)

**Step 3 — P8e: invert-expr.tantra**
Generic inverter via `pratipaksha` walk. "Find mass given KE and velocity."
Gated on Gap 1 + Gap 2 stable. The `pratipaksha` edges are already in the kosha.
This is a tantra, not an OCaml change. Layer 2 migration makes this cleaner
but it can be written in current syntax first.

**Step 4 — Document Layer 2 grammar formally**
`vartamana/08-layer2-grammar.md` — complete BNF.
No implementation yet. The spec to build toward.

**Step 5 — Begin Layer 2 parser**
After Gap 2 and P8e are stable. One tantra at a time.

---

---

## Layer 2 — current state (2026-03-17)

Layer 2 is no longer a future plan. It is partially implemented and in use.

**Parser:** `vyakarana/lib/yantra_tantra_file2.ml` (~900 lines). Produces the same
`tantra` AST type as Layer 1. The eval engine (`yantra_eval.ml`) is unchanged.

**Migrated tantras (3 of 12):**
- `vishesa-instance.tantra2` — typed scan state, Tension 3 resolved
- `rashi-viveka.tantra2` — gate-edge scan
- `vishesa-bandhana.tantra2` — reduce lambda, pipe filters

**Tensions resolved by Layer 2:**

| Tension | Status |
|---------|--------|
| 1 (one grammar two semantics) | `parse2_pipe` is separate from `parse2_primary` — pipe ops and expression ops don't collide |
| 2 (arity table drives parsing) | Still partially present — Layer 2 still consults `op_arity` for backward compat during migration |
| 3 (outer let invisible in scan) | **Resolved.** Typed scan state `[name: type = init-expr]` initializes from outer scope |
| 7 (let inside fn body) | **Resolved.** File parser tracks `in_scan_body` depth — assignments inside body are `SSet`, not new bindings |

**Tensions NOT YET resolved:**
- Tension 2 (arity table) — still active for calling Layer 1 tantras from Layer 2 context
- Tension 4 (emit/emit-triple) — scan emit works but no formal fix
- Tension 5 (string equality) — still uses `as_string` comparison
- Tension 6 (flat name-based lookup) — still flat; `sthita-viveka` needed

**Key authoring rules for Layer 2 (full list in `10-layer2-rewrite.md`):**

1. `| where` patterns are ALL variables — use `| and (eq e "sankhya")` for filtering
2. Never use `value`, `pair`, or any kosha op name as a variable — causes silent mis-parse
3. Use `_it` not `_` in `| collect` expressions for the current item
4. Avoid nested parens in `fn` body inside `(fn ...)` — use `{fn ...}` braces for complex lambdas
5. Put `->` on its own line after multi-line `when` guards
6. `or` is infix — `(member x list) or flag` works. `and` is NOT infix — use separate `when` lines

---

## What has changed

For baseline and session progress see [changelog.md](changelog.md).

| Date | What shifted in this doc |
|------|-------------|
| 2026-03-17 | Initial writing — three-layer architecture, Tensions 1–2. |
| 2026-03-17 | Tensions 3–6 added from regression investigation. |
| 2026-03-17 | Tensions 7–9 added from boot pass investigation. Boot/reboot architecture section added. Tantra author rules table added. |
| 2026-03-17 | Layer 2 current state section added. Tensions 1/3/7 marked resolved. Authoring rules from migration experience. |
