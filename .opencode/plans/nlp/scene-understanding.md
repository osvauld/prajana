# Scene Understanding — End-to-End Pipeline

**Status**: Design. Unified view of how all NLP work connects.
**This file**: Maps every plan step to the scene understanding pipeline stage it enables.

---

## What scene understanding is

Scene understanding is the full pipeline from natural language input to a computed,
grammatically correct response. It is NOT a separate system — it is what the entire
NLP stack (P5–P8) enables together:

```
User text
  ↓  [P6a] token recognition — bhasha nodes, sangati root matching
  ↓  [P6b] grammar classification — pada/kaala/prayoga/vibhakti
  ↓  [P7]  proposition extraction — known values, target entity, intent
  ↓  [P6c] inference walk — logic/ + graph/ nodes find the formula
  ↓  [P5.5] formula matching — mantra node krama + pratipaksha
  ↓  [P8]  execution — execute-chain applies krama steps with values
  ↓  [P7.5] response composition — krama narrative + grammar pass
  ↓
Grammatically correct sentence
```

---

## Worked example: "what is the kinetic energy when mass is 10 and velocity is 6?"

### Stage 1 — Token recognition (P6a)

Tokens are resolved to graph nodes via bhasha lookup:
- `kinetic-energy` → bhasha node → dhatu → kosha `kinetic-energy`
- `mass` → bhasha node → dhatu → kosha `mass`
- `velocity` → bhasha node → dhatu → kosha `velocity`
- `is` (copula) → bhasha `copula` → `vartamana-kaala`, `karmani-prayoga`
- `what` → bhasha `what-question` → `prashna + prathama-vibhakti`
- `10`, `6` → numeric literals

**Sangati root matching** (from sangati bhasha forms, P6a):
- `matra-yukta` nodes → "10", "6" are quantities
- Numeric tokens next to kosha nodes → bind as values

### Stage 2 — Grammar classification (P6b)

Grammar edges on bhasha nodes determine sentence roles:
- `what` → `prathama-vibhakti` → target (what is being asked for)
- `mass is 10` → `prathama-vibhakti + vartamana-kaala` → known value / current state
- `velocity is 6` → same pattern → known value
- `what is the kinetic energy` → `vidhi/prashna-kaala` → goal/target intent

Grammar composition layer (P6b) reads:
- Query `kaala` = `prashna` (question) → response uses `vartamana-kaala` for result
- Query `prayoga` = `karmani` ("what IS it") → response uses `kartari` for answer

### Stage 3 — Proposition extraction (P7)

Vibhakti-driven argument roles (P7 tantra rewrite):
- `prathama-vibhakti` → nominative → subject/target
- Known: `{mass: 10, velocity: 6}`
- Target: `kinetic-energy`
- Intent: compute-target (all inputs known → forward execution)

This extraction IS a `proposition` in the logic/ sense:
> "There EXISTS a formula node F such that F({mass:10, velocity:6}) = kinetic-energy-value"

### Stage 4 — Inference walk (P6c + P8)

Finding which formula node to use IS mathematical inference:

```
known = [mass, velocity]
target = kinetic-energy
```

The `inference` walk (logic/ vocabulary):
1. Start from known nodes: `mass`, `velocity`
2. Walk `implication` edges — "if these inputs are known, then this formula fires"
3. Find `kinetic-energy` node whose `krama-input` matches known set
4. This IS a `theorem` — an established formula that can be instantiated

In graph terms: `scene-walk.tantra` (P8) walks from known nodes through
`janya` ← backward ← formula node to find the right mantra node.

The `breadth-first` strategy (graph/ vocabulary) IS chain_resolve:
- Explore all formula nodes reachable from known seeds
- Pick the one whose krama-input is fully satisfied
- Depth = chain length; BFS finds shortest proof chain first

### Stage 5 — Formula matching (P5.5)

`kinetic-energy.om` carries:
- `krama` edges: `square-krama`, `mul-krama`, `mul-half-krama`
- `krama-input: velocity mass` in shabda
- `execute-chain-kriya` — declares its executor tantra
- `pratipaksha` edges to inverse sibling nodes

Context check: `walk "kinetic-energy" "kriya"` → `["execute-chain"]`
Known values satisfy `krama-input` → select `execute-chain`.

### Stage 6 — Execution (P8)

`execute-chain.tantra` walks the krama chain:
1. `square` with value `velocity=6` → 36
2. `mul` with values `[36, mass=10]` → 360
3. `mul-half` with value `360` → 180

Result: `kinetic-energy = 180` with unit `joule` (from `krama-output` shabda).

### Stage 7 — Response composition (P7.5)

Two-pass sentence generation:

**Pass 1 — Krama narrative** (from sangati root bhasha forms, P6a):
Walk sangati `yukta` edges on `kinetic-energy`:
- `matra-yukta` → "measure"
- `spanda-yukta` → "of motion"
Krama steps render as: "square velocity, multiply by mass, halve"

**Pass 2 — Grammar application** (P6b grammar composition layer):
- Query was `prashna + vartamana-kaala` → answer in `vartamana-kaala`
- Query was `karmani-prayoga` ("what IS it") → answer in `kartari-prayoga` ("X IS Y")
- `prathama-purusa + eka-vachana` → "kinetic energy IS 180 joule"

Result: **"kinetic energy is 180 joule."**

---

## Worked example: "mass when force is 20 and acceleration is 2"

### Proposition
- Known: `{force: 20, acceleration: 2}`
- Target: `mass`
- Intent: solve-for (target is an INPUT to a known formula, not the output)

### Inference walk
This is NOT forward execution — it requires inverse inference:
- Walk from `mass` outward → find formula where `mass` is `krama-input`
- `newton-second-law.om` has `krama-input: mass acceleration` and `phala: force`
- Known `force` is the phala — so this is an `execute-inverse` case

`walk "newton-second-law" "pratipaksha"` → `["newton-second-law-solve-mass"]`
`walk "newton-second-law" "kriya"` filtered by context (force is known, not mass) →
select `execute-inverse-kriya`

### Execution
`newton-second-law-solve-mass.om` krama chain: `div force acceleration`
Result: `mass = 20/2 = 10` with unit `kilogram`.

### Response
"mass is 10 kilogram."

---

## What each plan step enables for scene understanding

| Plan step | What it adds to scene understanding |
|---|---|
| **P5 degree enrichment** | Operation nodes declare `degree:` + `invertible:` → `is-identity-composition` can derive inverses automatically without hardcoded tables |
| **P5.5 physics mantra** | Formula nodes carry `krama` chains + `pratipaksha` + `kriya` → execution and inverse execution become graph walks |
| **P6a sangati bhasha** | ~50 atomic vocabulary nodes → token recognition + type description in responses |
| **P6b grammar composition** | kaala/prayoga/vachana surface forms → grammatically correct response sentences |
| **P6c logic/ + graph/ nodes** | `inference`, `theorem`, `proof`, `implication` = operational vocabulary for the inference walk. `breadth-first`, `depth-first` = traversal strategies for chain-resolve |
| **P7 parsing tantras** | vibhakti-driven extraction → correct argument roles, no hardcoded word lists |
| **P7.5 response tantras** | format-response reads kaala/prayoga from context → applies grammar pass to krama narrative |
| **P8 computation tantras** | execute-chain, scene-walk, compute-from-node → the actual execution and inverse computation |
| **P8.5 inverter removal** | OCaml symbolic inversion replaced entirely by pratipaksha graph walk |

---

## The logic/ nodes as operational vocabulary

The `logic/` sub-varga (built in P5) is not just ontology — it describes what the
engine DOES during scene understanding:

| Logic node | What it IS in scene understanding |
|---|---|
| `proposition` | A user query — a statement to be evaluated as true/false (computed/not-computable) |
| `inference` | The process of finding which formula to execute given known premises |
| `implication` | "If these inputs are known, then this formula can fire" — the edge condition |
| `theorem` | A formula node that has been established and can be instantiated with values |
| `proof` | The krama chain execution — ordered steps that establish the result |
| `axiom` | A sangati truth — grounding that requires no further justification |
| `undecidable` | A query where no formula node can be matched from known seeds |

Scene understanding pipeline in logic terms:
1. User query → `proposition` to evaluate
2. Inference walk → find `theorem` (formula node) provable from `premises` (known values)
3. krama execution → `proof` of the proposition (the computed value)
4. `undecidable` → "cannot compute" response when no matching formula found

---

## The graph/ nodes as traversal vocabulary

| Graph node | What it IS in scene understanding |
|---|---|
| `graph-walk` | Walking the kosha graph from known seeds to formula nodes |
| `breadth-first` | `chain_resolve` BFS — explores all formula nodes at each hop before going deeper |
| `depth-first` | Deep inference chains — follows one path all the way down first |
| `shortest-path` | Find the formula chain with fewest steps from known to target |
| `spanning-tree` | All possible inference paths from known seeds |

`chain_resolve` in `yantra_resolver.ml` IS a breadth-first graph walk. Once P8
rewrites it as `scene-walk.tantra`, the tantra can reference `breadth-first-kriya`
on the formula node to declare which traversal strategy to use.

---

## Grammar composition — the second pass

Grammar does NOT change what is computed. It changes how the result is expressed.
This is cleanly separable — execution produces a value + formula node; grammar
produces the sentence.

**Inputs to grammar pass**:
- Computed value + unit (from execution)
- Formula node (from inference walk)
- Query kaala (from P7 extraction — what tense was used?)
- Query prayoga (from P7 extraction — active or passive construction?)
- Query purusa/vachana (from P7 — who is the subject?)

**Grammar pass logic** (P7.5 `format-response.tantra`):

```
query: "what is the kinetic energy?"
  → kaala: vartamana (is → present)
  → prayoga: kartari (asking for the subject's property)
  → response: "<formula-name> is <value> <unit>."
  → "kinetic energy is 180 joule."

query: "find the mass"
  → kaala: vidhi (imperative → goal)
  → prayoga: kartari
  → response: "<formula-name> is <value> <unit>."
  → "mass is 10 kilogram."

query: "the kinetic energy was computed as..."
  → kaala: bhuta (past)
  → prayoga: karmani (passive — "was computed")
  → response: "<formula-name> was computed as <value> <unit>."
```

The grammar IS the context. The same krama chain value gets different surface forms
depending on query intent. No hardcoded response templates — grammar nodes + bhasha
surface forms compose the right sentence for any query form.

---

## Scene understanding with chaining (multi-step inference)

For "kinetic energy when mass=10, initial-velocity=0, acceleration=2, time=3":

1. Known: `{mass:10, initial-velocity:0, acceleration:2, time:3}`
2. Target: `kinetic-energy`
3. `kinetic-energy` needs `velocity` — NOT directly known
4. Inference: find formula that produces `velocity` from known values
5. `velocity = initial-velocity + acceleration × time` → v = 0 + 2×3 = 6
6. Now `velocity=6` is known → `kinetic-energy(10, 6) = 180`

This IS a `proof` chain — two theorem applications in sequence:
- Lemma 1: `velocity` theorem from `{initial-velocity, acceleration, time}`
- Main: `kinetic-energy` theorem from `{mass, velocity}`

The `chain-kinetic-energy` regression test (currently failing) tests exactly this.
It should PASS once `kinetic-energy.om` and `velocity.om` carry proper krama +
pratipaksha edges (P5.5) and scene-walk.tantra (P8) can chain through the inference.

---

## Key files for scene understanding

```
brahman/kosha/math/logic/        inference, theorem, proof, proposition, implication
brahman/kosha/math/graph/        graph-walk, breadth-first, depth-first, shortest-path
brahman/kosha/physics/           mantra-enriched formula nodes (P5.5)
brahman/bhasha/english/sangati/  ~50 sangati root bhasha forms (P6a)
brahman/bhasha/english/grammar/  grammar composition surface forms (P6b)
brahman/yantra/execute-chain.tantra      krama chain execution (P8)
brahman/yantra/scene-walk.tantra         inference walk / backward computation (P8)
brahman/yantra/compute-from-node.tantra  generic dispatch via kriya (P8)
vyakarana/lib/yantra_pipeline_ops.ml     resolve-inverse (shim → P8.5 removal)
vyakarana/lib/yantra_resolver.ml         chain_resolve BFS (replaced by scene-walk at P8)
```
