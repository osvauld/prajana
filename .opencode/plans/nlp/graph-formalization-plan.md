# Graph Formalization Plan — Question Graph as Typed Subgraph

**Status**: Phases 0–5 complete. Phase 2 (R8 rewrite) done via sandhi-viveka + shashthi-vibhakti typed edges.
**Created**: 2026-03-13
**Current baseline**: 124 pass / 11 fail (2026-03-13, after reflexive satya)

---

## The Insight

The question graph is currently a `VList` of `VList` triples with raw string edge
labels (`"active"`, `"mithya"`, `"owner"`, etc.). These strings are never registered
as visheshanam dimensions. The graph ops (`walk`, `walk-in`, `has`, `edges`) cannot
see them. Every avrti rule is a stateful `reduce` doing string comparisons.

The fix: **register the question graph's edge labels as visheshanam dimensions and
materialize the question graph into the proof graph via `emit-node`.** Then:

- R8 entity resolution becomes a typed 2-hop walk, not a stateful reduce
- Ownership is an antisymmetric, non-transitive dimension — the engine enforces this
- `walk-in "owner"` finds all concepts owned by an entity in one call
- No positional propagation bug is possible — only edges that exist can be walked
- PPR can score the question graph nodes (pronoun resolution = relevance query)

No OCaml changes needed. The dimension registry is append-only. `emit-node` already
decomposes slokas against registered dimensions. `walk`/`walk-in` already work on
typed edges.

---

## What Exists Today

### Dimension registry
- Core 10: swarupa, abheda, drishthanta, sthita, yukta, siddha, kriya, phala, janya, pratipaksha
- Dynamic: sandhi, matra, krama, kramanusara, avastha, apeksha, ahara, dhatu, vrnda,
  kala, prayoga, vachana, purusa, vishesa, amsha
- Registration: `visheshanam-ring.om` slokas scanned by `om_parser.ml` for `X-yukta`
  patterns where X is a known node name → `register_dimension` called
- Runtime registration: `(register-dimension "name")` op available to tantras

### Question graph edge labels (currently raw strings)
| Label | Meaning | Used in |
|---|---|---|
| `active` | Resolved concept | emit-triples, avrti-refine |
| `mithya` | Unresolved word | emit-triples, avrti-refine |
| `value` | Numeric binding | emit-triples, avrti-refine, match-mantra |
| `unit` | Unit binding | emit-triples |
| `pending-number` | Unattached number | emit-triples, avrti-refine |
| `intent` | Query intent | emit-triples, match-mantra |
| `owner` | Entity ownership | avrti-refine (R8) |
| `entity` | Entity declaration | avrti-refine (R8) |
| `symbol` | Symbolic label | avrti-refine (R4b) |
| `punct` | Punctuation marker | build-question-graph |
| `dvandva` | Group membership | planned (R5/R6) |
| `refers-to` | Pronoun reference | planned (R10) |
| `paired-with` | Respectively zip | planned (R7) |
| `instance-of` | Type membership | planned (R6) |

### Graph ops that would work once dimensions are registered
- `walk node "owner"` → all concepts owned by entity
- `walk-in concept "owner"` → which entity owns this concept
- `has node "active"` → is this node an active concept?
- `walk node "refers-to"` → pronoun resolution target
- `walk-in entity "refers-to"` → what pronouns point here?
- `edges node` → all relationships of a question graph node
- `ppr [seeds] target bindings` → rank candidate referents

---

## Implementation Plan

### Step 0 — Foundation nodes (kosha)

Create sangati/kosha anchor nodes for each question graph edge label. These must exist
as named nodes in the graph before the ring can claim them as `X-yukta` dimensions.

**Files to create:**

| File | Declaration | Slokas | Shabda |
|---|---|---|---|
| `brahman/sangati/prashna/active.om` | `sangati active` | `"satya-sthita prashna-sthita"` | `active / resolved-concept-in-question-graph` |
| `brahman/sangati/prashna/mithya.om` | `sangati mithya` | `"avidya-sthita prashna-sthita"` | `mithya / unresolved-word-in-question-graph` |
| `brahman/sangati/prashna/prashna.om` | `sangati prashna` | `"vakya-sthita"` | `question / question-graph-root` |

**Why sangati, not kosha?** These are structural truths about the question graph — they
define what the edge dimensions MEAN, not domain-specific knowledge. Same level as
`krama`, `sandhi`, `matra` which are already sangati nodes claimed by the ring.

**For the remaining labels** (owner, entity, value, unit, etc.), we have two options:

Option A: All as sangati nodes in `brahman/sangati/prashna/`
Option B: Only the core 3 (active, mithya, prashna) as sangati; the rest as kosha
nodes in a new `brahman/kosha/prashna/` directory

Recommendation: **Option A** — these are structural/grammatical concepts about how
questions work, not domain knowledge. They parallel the existing grammatical dimensions
(kala, prayoga, vachana, purusa).

**Full sangati node list:**

| File | Node | Slokas |
|---|---|---|
| `prashna.om` | `sangati prashna` | `"vakya-sthita directed-graph-swarupa"` |
| `active.om` | `sangati active` | `"satya-sthita prashna-sthita"` |
| `mithya.om` | `sangati mithya` | `"avidya-sthita prashna-sthita"` |
| `q-value.om` | `sangati q-value` | `"matra-sthita prashna-sthita"` |
| `q-unit.om` | `sangati q-unit` | `"matra-sthita prashna-sthita"` |
| `q-owner.om` | `sangati q-owner` | `"sambandha-sthita prashna-sthita directed-graph-sthita"` |
| `q-entity.om` | `sangati q-entity` | `"prashna-sthita"` |
| `q-intent.om` | `sangati q-intent` | `"prashna-sthita kriya-sthita"` |
| `q-symbol.om` | `sangati q-symbol` | `"prashna-sthita"` |
| `q-pending.om` | `sangati q-pending` | `"matra-sthita prashna-sthita"` |
| `q-punct.om` | `sangati q-punct` | `"prashna-sthita"` |
| `q-dvandva.om` | `sangati q-dvandva` | `"prashna-sthita dvandva-sthita"` |
| `q-refers-to.om` | `sangati q-refers-to` | `"prashna-sthita sambandha-sthita"` |
| `q-paired-with.om` | `sangati q-paired-with` | `"prashna-sthita sambandha-sthita"` |
| `q-instance-of.om` | `sangati q-instance-of` | `"prashna-sthita vishesa-sthita"` |

**Naming**: Using `q-` prefix for labels that collide with existing concepts (`value`,
`unit`, `owner` are common English words). `active` and `mithya` are unique enough to
keep unprefixed. The `q-` prefix makes clear these are question-graph-specific dimensions.

**Decision needed**: Use `q-` prefix consistently for ALL labels, or only for collisions?
Recommendation: `q-` for all except `active` and `mithya` (which are already
philosophically grounded terms in the system — satya/mithya/avidya vocabulary).

---

### Step 1 — Register dimensions in visheshanam-ring

Add the new dimension claims to `visheshanam-ring.om`. The om_parser scans for
`X-yukta` patterns where X is a known node name.

**Add to `visheshanam-ring.om`:**
```
  -- question graph dimensions (prashna layer)
  "active-yukta mithya-yukta"
  "q-value-yukta q-unit-yukta q-pending-yukta"
  "q-owner-yukta q-entity-yukta q-intent-yukta"
  "q-symbol-yukta q-punct-yukta"
  "q-dvandva-yukta q-refers-to-yukta"
  "q-paired-with-yukta q-instance-of-yukta"
```

This gives each label a visheshanam index (≥ 25, after the existing 25 dimensions).
Once registered, `walk`, `walk-in`, `has`, `edges` all recognize them.

**Verification**: After this step, `(dimension-count)` should return the old count + 14.

---

### Step 2 — Dimension property files (optional but valuable)

Create `visheshanam-<name>.om` files for key dimensions to declare algebraic properties.
These properties affect PPR conductance weights, axiom expansion, and correctness
enforcement.

**Priority properties:**

| Dimension | Properties | Why |
|---|---|---|
| `q-owner` | antisymmetric, NOT transitive | ownership does not propagate: if A owns B, and B owns C, A does NOT own C |
| `active` | antisymmetric | concept is active; reverse doesn't hold |
| `mithya` | reflexive | mithya word refers to itself |
| `q-refers-to` | antisymmetric, NOT transitive | pronoun refers to entity, not the reverse |
| `q-value` | antisymmetric | concept has value, not value has concept |
| `q-dvandva` | symmetric? | membership goes both ways? Or directed: concept → group |

**Files to create** (in `brahman/kosha/yantra/visheshanam/`):

| File | Key shabda |
|---|---|
| `visheshanam-q-owner.om` | `antisymmetric:true transitive:false` |
| `visheshanam-active.om` | `antisymmetric:true` |
| `visheshanam-mithya.om` | `reflexive:true` |
| `visheshanam-q-refers-to.om` | `antisymmetric:true transitive:false` |

These are optional for correctness — the system works without them — but they make
the ontology self-describing and affect PPR edge weights.

---

### Step 3 — Materialization tantra: `materialize-question-graph.tantra`

This tantra takes the VList-of-triples question graph and emits each triple as a
proof-graph node with typed edges via `emit-node`.

**Design:**

```
tantra materialize-question-graph
  inputs
    graph  list    -- [[subject, edge-label, object], ...]
  let
    -- for each triple, emit the subject node with a sloka connecting it
    -- to the object via the edge label dimension
    result = map graph (fn tri ->
      let subj = nth tri 0
      let edge = nth tri 1
      let obj  = nth tri 2
      -- translate string edge labels to dimension-prefixed slokas
      -- "active"  → "concept-active"     (obj is "concept")
      -- "owner"   → "ball-q-owner"       (obj is entity name)
      -- "value"   → the numeric value     (stored as shabda, not sloka edge)
      -- "mithya"  → "word-mithya"        (obj is the word itself)
      let dim-name = cond
        (eq edge "active")        "active"
        (eq edge "mithya")        "mithya"
        (eq edge "owner")         "q-owner"
        (eq edge "entity")        "q-entity"
        (eq edge "value")         "q-value"
        (eq edge "unit")          "q-unit"
        (eq edge "intent")        "q-intent"
        (eq edge "symbol")        "q-symbol"
        (eq edge "pending-number") "q-pending"
        (eq edge "punct")         "q-punct"
        (eq edge "dvandva")       "q-dvandva"
        (eq edge "refers-to")     "q-refers-to"
        (eq edge "paired-with")   "q-paired-with"
        (eq edge "instance-of")   "q-instance-of"
        otherwise                 edge
      let sloka = concat obj "-" dim-name
      emit-node subj "prashna" [sloka] (concat "q-edge:" edge " q-obj:" obj))
  return
    result  list
done
```

**Key decisions:**
- Each question graph subject becomes a `prashna`-layer node
- The edge label becomes a typed visheshanam edge via sloka decomposition
- Numeric values go into shabda (not slokas) since they are data, not structure
- The `"prashna"` layer tag distinguishes question graph nodes from kosha/bhasha/sangati

**When to call**: After `fixpoint avrti-refine` completes, before `match-mantra`. This
is the bridge between the VList world and the proof-graph world.

**Alternative**: Materialize incrementally during avrti-refine itself, so each rule
can use `walk`/`walk-in` instead of reduce. More complex but more powerful.

---

### Step 4 — Rewrite avrti-refine to use graph traversal

Once the question graph is materialized (or materializing incrementally), replace the
stateful `reduce` passes with graph queries.

**R8 entity-from-possession (current: stateful reduce with cur-entity):**

Current broken logic:
```
reduce triples ["", "", []] (fn state tri ->
  ... if possession signal, set cur-entity
  ... if active concept, add [concept, owner, cur-entity]  ← PROPAGATES FOREVER
  ...)
```

New graph-based logic:
```
-- for each mithya word followed by a possession-signal word:
-- 1. emit [label, entity, object]
-- 2. scan forward from the possession signal for active concepts
-- 3. emit [concept, owner, label] for each, STOPPING at:
--    - next possession signal (new entity)
--    - next intent signal (solve-for boundary)
--    - "and" + mithya + possession (entity-level dvandva)

-- after materialization, to find what an entity owns:
-- walk entity "q-owner"  → all owned concepts
-- walk-in concept "q-owner" → which entity owns it
```

The key difference: ownership edges are ONLY created by explicit signals. There is
no `cur-entity` variable that leaks across boundaries. Each ownership edge is a
discrete `emit-node` call with a typed `q-owner` dimension edge.

**R4b symbol-binding (current: fires on any mithya after owned concept):**

New guards using graph queries:
```
-- before emitting [concept, symbol, label]:
-- 1. check label is not an entity name: NOT (has label "q-entity")
-- 2. check label is not a grammar word: NOT (exists (lookup-word label) "role")
-- 3. check label is not a back-reference: NOT (eq (shabda (lookup-word label) "role") "grammar")
-- 4. check concept doesn't already have a value: NOT (has concept "q-value")
```

**Compound resolution (R1/R2) — no change needed.** These work correctly today.
They operate on the VList directly and don't need graph traversal.

**Pending-number binding (R4) — no change needed.** Works correctly today.

---

### Step 5 — Signal-based ownership rules (R8 rework detail)

The core rewrite. Instead of one `reduce` pass, R8 becomes a set of discrete
pattern-match rules that fire independently:

**Rule 8a — possession signal detection:**
```
pattern: [label, mithya, _] + [signal, mithya, _] where shabda(lookup-word signal) "role" = "possession"
action:  emit [label, entity, object]
         set current-entity = label (for 8b)
```

**Rule 8b — ownership binding (bounded, not propagating):**
```
pattern: active concept AFTER a possession signal, BEFORE the next signal
action:  emit [concept, owner, current-entity]
         -- "after" and "before" are positional in the VList, but the key difference
         -- from the old code is: we STOP at clear boundaries
```

**Boundaries that terminate ownership scope:**
1. Another possession signal (has/with/of/have) → new entity starts
2. An intent signal (find/what/calculate) → solve-for zone
3. A period/question mark → sentence boundary
4. "and" followed by mithya + possession → entity-level dvandva

**Rule 8c — "and" continuation (property dvandva under same has):**
```
pattern: [and, grammar, _] + [concept, active, _] while current-entity is set
         AND no possession signal between "and" and concept
action:  emit [concept, owner, current-entity]
         -- "has" distributes over "and" for properties
```

**Rule 8d — "of" as reverse possession:**
```
pattern: [concept, active, _] + [of, grammar, _] + [entity-name, mithya, _]
         where entity-name was previously declared as entity
action:  emit [concept, owner, entity-name]
         -- "of" reverses the direction: "mass of the ball" = ball owns mass
```

---

### Step 6 — Grammar nodes needed

| File | word: | role | Status |
|---|---|---|---|
| `verb-has.om` | `has` | `possession` | EXISTS |
| `prep-with.om` | `with` | `possession` | EXISTS |
| `verb-have.om` | `have` | `possession` | CREATE |
| `prep-of.om` | `of` | needs context-dependent handling | EXISTS (role:grammar) |
| `pronoun-its.om` | `its` | `pronoun` | CREATE |
| `pronoun-their.om` | `their` | `pronoun` | CREATE |
| `pronoun-it.om` | `it` | `pronoun` | CREATE |

**The `of` problem**: `prep-of.om` currently has `role:grammar`. It needs
`role:possession` for "mass of the ball" but NOT for "square root of 16". Two options:

Option A: Add `role:possession` alongside `role:grammar`. R8d checks context
(is the following word an entity name?) to decide which role applies.

Option B: Create two nodes: `prep-of-possession.om` and `prep-of-structural.om`.
Disambiguation happens during avrti based on what follows.

Recommendation: **Option A** — single node, context-dependent interpretation in avrti.
The grammar node provides BOTH roles; the avrti rule decides which applies based on
what follows the "of" (known entity → possession; otherwise → structural).

**Implementation**: Add `role2:possession` to `prep-of.om` shabda, or use a list
in the role field. The avrti rule checks: does an entity name follow "of"? If yes,
treat as possession. If no (e.g., "square root of"), treat as structural.

---

### Step 7 — Pronoun resolution via graph (R10)

Once the question graph is materialized, pronoun resolution is a graph query:

```
-- "its" detected as role:pronoun
-- find the most recent entity in the question graph:
--   walk-in "q-entity" on all prashna-layer nodes
--   → returns list of entity nodes
--   → take the last one (most recent)
-- emit [its, refers-to, last-entity]
-- emit [solve-for-concept, owner, last-entity]
```

For "their" (plural), the same query but taking ALL entities, not just the last.

PPR could help here: if there are multiple entities, PPR over the solve-for concept
seeds could rank which entity is the most relevant referent.

---

### Step 8 — Tests

**New test suite: `brahman/yantra/tests/formalization/`**

| Test | What it verifies |
|---|---|
| `test-dimension-registered.tantra` | `active` and `q-owner` are registered visheshanam dimensions |
| `test-emit-prashna-node.tantra` | `emit-node "mass" "prashna" ["concept-active"] ""` creates a walkable node |
| `test-walk-owner.tantra` | After emitting ownership edges, `walk "ball" "q-owner"` returns owned concepts |
| `test-walk-in-owner.tantra` | `walk-in "mass" "q-owner"` returns the owning entity |
| `test-no-transitive-owner.tantra` | Ownership does not propagate transitively |
| `test-materialize-simple.tantra` | Materialize a simple question graph, verify all nodes walkable |

**Updated entity tests** (expect more to pass after signal-based rework):

| Test | Expected change |
|---|---|
| `test-entity-no-false-ownership.tantra` | PASS (was FAIL — positional propagation) |
| `test-entity-symbol-not-backref.tantra` | PASS (was FAIL — R4b false fire) |

---

## Implementation Order

### Phase 0 — Foundation (no behavior change, no regressions possible)
1. Create `brahman/sangati/prashna/` directory with anchor nodes
2. Add dimension claims to `visheshanam-ring.om`
3. Verify: `dune build` succeeds, dimension-count increased, all 63 tests still pass
4. Optional: create visheshanam property files for key dimensions

### Phase 1 — Materialization bridge
5. Write `materialize-question-graph.tantra`
6. Write formalization test suite (dimension registration, emit, walk)
7. Verify: materialized nodes are walkable via `walk`/`walk-in`

### Phase 2 — Signal-based R8 rewrite
8. Rewrite R8 in avrti-refine: remove `cur-entity`, use bounded ownership
9. Add `verb-have.om` grammar node
10. Handle "of" context-dependent possession
11. Add R4b guards (no entity self-reference, no grammar word binding)
12. Entity test suite: expect improvement

### Phase 3 — Pronouns and back-references
13. Create pronoun grammar nodes (its, their, it)
14. Implement R10 pronoun resolution
15. Implement R11 definite article back-reference
16. Pronoun + entity test suite

### Phase 4 — Dvandva groups (R5/R6/R7)
17. R5 anonymous numeric group
18. R6 typed instance group
19. R12 "and" interpretation (property vs entity dvandva)
20. R7 respectively zip
21. Dvandva test suite: expect all pass

### Phase 5 — Full pipeline integration
22. Wire: BQG → avrti → materialize → match-mantra → execute → compose-trace
23. Match-mantra reads from materialized graph via walk instead of VList scan
24. Pipeline test suite: end-to-end worked examples

---

## Key Decision Points

### Q1: Materialize incrementally or at the end?

**End-of-avrti** (recommended to start): Simpler. avrti-refine still works on VList.
After fixpoint, one call to `materialize-question-graph` converts to proof-graph.
Match-mantra and compose-trace then use `walk`/`walk-in`.

**Incremental** (future upgrade): Each avrti rule emits into the proof graph directly.
Rules can use `walk`/`walk-in` mid-pass. More powerful but requires rewriting all
reduce passes to use graph ops. Do this AFTER the end-of-avrti approach works.

### Q2: Should match-mantra read from materialized graph?

Yes, eventually. Currently it scans the VList for `"value"` and `"active"` predicates.
After materialization, it would use `walk concept "q-value"` and
`walk-in concept "active"`. But this is Phase 5 — get the fundamentals working first.

### Q3: q- prefix on all dimension names?

Use `q-` for all except `active` and `mithya`. These two are philosophically grounded
terms in the system (satya/mithya/avidya vocabulary) and don't collide with existing
dimension names.

---

## Files Modified / Created

### Created (Phase 0)
```
brahman/sangati/prashna/prashna.om
brahman/sangati/prashna/active.om
brahman/sangati/prashna/mithya.om
brahman/sangati/prashna/q-value.om
brahman/sangati/prashna/q-unit.om
brahman/sangati/prashna/q-owner.om
brahman/sangati/prashna/q-entity.om
brahman/sangati/prashna/q-intent.om
brahman/sangati/prashna/q-symbol.om
brahman/sangati/prashna/q-pending.om
brahman/sangati/prashna/q-punct.om
brahman/sangati/prashna/q-dvandva.om
brahman/sangati/prashna/q-refers-to.om
brahman/sangati/prashna/q-paired-with.om
brahman/sangati/prashna/q-instance-of.om
```

### Modified (Phase 0)
```
brahman/kosha/yantra/visheshanam/visheshanam-ring.om  — add prashna dimension claims
```

### Created (Phase 1)
```
brahman/yantra/materialize-question-graph.tantra
brahman/yantra/tests/formalization/test-*.tantra  (6+ tests)
```

### Modified (Phase 2)
```
brahman/yantra/avrti-refine.tantra  — R8 rewrite, R4b guards
brahman/bhasha/english/grammar/verb-have.om  — CREATE
brahman/bhasha/english/grammar/prep-of.om  — add role2:possession
```

### Created (Phase 3)
```
brahman/bhasha/english/grammar/pronoun-its.om
brahman/bhasha/english/grammar/pronoun-their.om
brahman/bhasha/english/grammar/pronoun-it.om
```

### Modified (Phase 5)
```
brahman/yantra/match-mantra.tantra  — read from materialized graph
```

---

## Regression Gate

Every phase must maintain the current 124/11 baseline or improve it.
Run: `cd vyakarana && bash scripts/run-tests.sh`

Phase 0 changes NO behavior — purely additive kosha/sangati nodes.
Phase 1 adds a new tantra and tests — no existing code touched.
Phase 2 modifies avrti-refine — this is where regressions are possible.
  Run entity + dvandva + avrti + avrti2 suites after every change.
