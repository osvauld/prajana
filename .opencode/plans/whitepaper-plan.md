# Whitepaper Rethink — Plan

## Context

Exploratory session: read all source files, live-probed the engine, measured actual numbers.
This plan reflects what was found and what is currently missing or underdocumented.

---

## Live Engine Facts (measured, not assumed)

| Metric | Value |
|---|---|
| Binary size | 4.6 MB |
| Knowledge corpus (`.om` + `.tantra` + `.shabda`) | 1.74 MB |
| Total footprint | ~6.3 MB |
| Nodes loaded at runtime | 1,240 |
| Axiom-expanded edges at startup | 4,743 |
| Tantras (executable programs) | 94 |
| Physical constants baked in | 14 |
| Engine OCaml source | 7,459 lines |
| Full query latency (cold process) | ~0.71s |

## Live Edge Weights (measured)

| Relation | Weight |
|---|---|
| sthita | 0.95 |
| kriya | 0.70 |
| yukta | 0.60 |
| janya | 0.58 |
| abheda | 0.53 |
| swarupa | 0.55 |

## Graph Dimensionality (measured, not assumed)

**Raw declared edges by relation type:**

| Relation | Count | Ring role | Properties |
|---|---|---|---|
| yukta | 2,374 | **add (+)** | symmetric |
| sthita | 1,951 | order/filter | antisymmetric, transitive, composable |
| abheda | 1,111 | equivalence | symmetric, transitive, congruence, composable |
| swarupa | 927 | identity (×-id) | symmetric, transitive, reflexive, congruence |
| kriya | 530 | **mul (×)** | antisymmetric, composable |
| phala | 520 | codomain | antisymmetric, dual: janya |
| siddha | 491 | proof/proof | — |
| drishthanta | 284 | evidence | — |
| janya | 180 | domain/origin | antisymmetric, dual: phala |
| pratipaksha | 12 | additive-inv | symmetric, involutive |
| rahita | 41 | absence/negation | — |
| **Total raw** | **8,421** | | |
| **After axiom expansion** | **~13,164** | | |

**Three dimensional readings of the graph:**

| Dimension axis | Count | What it means |
|---|---|---|
| Relation types (edge dimension) | 10 | 10 orthogonal edge kinds — 10 independent axes of connection |
| Nodes (node basis dimension) | 1,240 | every query produces a score vector of this size |
| PPR score space | ℝ¹²⁴⁰ | one float per node — the query's posterior landscape |
| Relation tensor | 1,240 × 1,240 × 10 | 15,376,000 possible directed relation slots |
| Density | 0.085% | ~13,164 of 15,376,000 slots filled — extremely sparse |

**Dimensional vocabulary already in the graph (`brahman/sangati/`):**

| Node | Meaning | Maps to |
|---|---|---|
| shunya | zero / 0D | additive identity, the empty node |
| bindu | point / 0D | zero-dimensional object |
| rekha | line / 1D | one-dimensional extension |
| tala | plane / 2D | two-dimensional field |
| aayaama | dimension | count of independent directions |
| aayaama-vistara | expansion of dimension | growing/infinite-dimensional reach |
| antaraayaama | inner dimension | the space within |
| akasham | space | the container of all dimensions |

The graph describes its own dimensionality using these nodes. This closes the loop:
the graph is n-dimensional, and it already has the vocabulary to say so formally.

## Domain Coverage (nodes)

| Domain | Nodes |
|---|---|
| sangati (root ontology) | 240 |
| physics (incl. fluid, quantum) | 140 |
| math | 121 |
| computation | ~50 |
| philosophy | 34 |
| chemistry | 33 |
| finance | 30 |
| biology | 46 |
| sangeetham (music) | 26 |
| ayurveda | 8 |
| cross-domain | 10 |

## Tantra Families

- `bhautika/` — force, kinetic energy, Coulomb, gravitation, Ohm's law, Snell, Doppler, ideal gas, electrostatics
- `vidnyana/` — factorial, quadratic, sqrt, polynomial eval (Horner), log, trig
- `parivartana/` — unit conversions: Celsius↔Kelvin, km/h↔m/s, metre↔km, degrees↔radians
- `niyata/` — physical constants: G, ℏ, k_B, π, e, c
- `ganaka/` — arithmetic primitives
- meta — classify-fold-resolve, anuvada-ganana, compose-answer, visheshanam-projection, darshana, etc.

## What Currently Exists (whitepaper/)

| File | Status |
|---|---|
| `executive-summary.md` | Thin. Needs expansion. |
| `input-output-graph-math.md` | Good base. Recently expanded with token-classification math. |
| `learning-without-retraining.md` | Good. Keep, minor polish. |
| `proof-graph-running-examples.md` | Good. Add multi-turn + inverse examples. |
| `reference/equations.md` | Good reference. Keep. |
| `tattva/first-principles-model.md` | Thin. |
| `tattva/system-overview.md` | Thin. |
| `prayoga/music-and-code-generation.md` | Thin but correct. |

## What Is Missing (gaps)

1. **No doc on session memory** — bindings, multi-turn, how prior turns feed next
2. **No doc on engine footprint** — actual numbers, comparison to LLM alternatives
3. **Domain coverage never charted** — users don't know what the graph contains
4. **Tantra as a language never explained** — format, structure, what makes a valid tantra
5. **Theoretical capacity not addressed** — node/edge scaling, PPR bound, beam bound
6. **Three solve modes not unified** — direct / inverse / chain split across docs without a clean treatment
7. **Applications section thin** — only robotics mentioned; music gen, code gen, embedded AI absent
8. **`invert_chain` mechanism undocumented** — how symbolic inverse solve works

---

## Proposed New Structure

```
prabandam/src/content/docs/whitepaper/
  overview.md                    ← REWRITE: what this is, why, what it can do (replace executive-summary)
  ontology.md                    ← NEW: how everything connects — layers, relations, axioms, graph topology
  knowledge-layers.md            ← NEW: .om / .tantra / .shabda — format, role, worked examples of each
  reasoning-pipeline.md          ← NEW: full unified pipeline (classify→intent→extract→solve→compose)
  three-solve-modes.md           ← NEW: direct / inverse / chain — math, examples, worked traces
  session-and-memory.md          ← NEW: within-session bindings + structural learning model
  capacity-and-footprint.md      ← NEW: actual numbers, scaling analysis, comparison to alternatives
  domain-coverage.md             ← NEW: what's in the graph now, how to extend, table of coverage
  applications.md                ← NEW: embedded AI, robotics, multi-language, music, code gen
  worked-examples.md             ← EXPAND: add multi-turn, inverse, chain, conceptual traces
  input-output-graph-math.md     ← KEEP + POLISH: already good, recently expanded
  learning-without-retraining.md ← KEEP: solid
  proof-graph-running-examples.md ← KEEP + EXPAND: add session + inverse examples
```

---

## Document-by-Document Spec

### overview.md (rewrite of executive-summary)

- What this is: a graph + tantra engine, not a token predictor
- The three-layer claim: explicit knowledge, explicit semantics, explicit inference
- Prior + posterior model at a glance (one-page math summary)
- What it can do: compute, explain, remember, extend, generate
- Footprint: 6.3 MB total
- Link to deeper chapters

### ontology.md (NEW)

The most important new document. Explains how every node, relation, layer, and axiom connects
into a coherent whole. Nothing else in the whitepaper is fully understandable without this.

#### What to cover

**1. The four graph layers and their roles**

```
sangati/       — root ontology: pure abstract first principles
kosha/         — domain knowledge: physics, math, biology, music, finance, etc.
engine/        — self-description: the engine knows itself as nodes
personal/      — experiential/personal layer: lived relational facts
```

- `sangati` nodes are the ground — `brahman`, `spanda`, `iccha`, `karma`, `satya`, `avrti`, etc.
  They carry no domain tag. They are the primitive vocabulary from which all meaning descends.
- `kosha` nodes rest on domain anchors (`domain-physics-sthita`, `domain-math-sthita`, etc.).
  They inherit domain membership via the `sthita` chain.
- `engine` nodes describe the system itself (`proof-graph`, `vyakarana`, `session`, `bridge`, etc.).
  The engine is inside its own graph.
- `personal` nodes encode lived, relational, experiential facts — a distinct epistemic layer.

**2. The visheshanam relation algebra — all 10 relations with algebraic properties**

Each relation is a first-class algebraic object with declared properties (from `.om` files):

| Relation | Meaning | Algebraic properties | Ring-op |
|---|---|---|---|
| `swarupa` | identity / own-form | symmetric, transitive, reflexive, congruence, composable | — |
| `abheda` | non-difference / equivalence | symmetric, transitive, congruence, composable | — |
| `sthita` | dependency / foundation | antisymmetric, transitive, composable | — |
| `yukta` | association / joined-with | — | add |
| `kriya` | action / function application | antisymmetric, composable | mul |
| `phala` | consequence / output | antisymmetric, dual: janya | — |
| `janya` | origin / generator | antisymmetric, dual: phala | — |
| `siddha` | proof / establishment | — | — |
| `drishthanta` | evidence / example | — | — |
| `pratipaksha` | inverse / counter | symmetric, involutive | — |

Key duals: `phala ↔ janya` (output ↔ origin). If A causes B (`janya`), then B results from A (`phala`).
`pratipaksha` is its own inverse: if A undoes B, B undoes A.

**3. Axiom expansion at startup — what gets added and why**

At load time, `apply_relation_axioms` runs before any query. Measured expansion (live):

| Axiom | Edges added | Rule |
|---|---|---|
| `yukta` symmetry | 2,147 | if A yukta B → B yukta A |
| `abheda` symmetry + transitivity | 1,034 | if A abheda B → B abheda A; chain close |
| `swarupa` transitivity + reflexivity | 880 | if A swarupa B and B swarupa C → A swarupa C |
| `phala → janya` inverse | 512 | if A phala B → B janya A |
| `janya → phala` inverse | 162 | if A janya B → B phala A |
| `pratipaksha` symmetry | 8 | if A pratipaksha B → B pratipaksha A |
| **Total** | **4,743** | |

This means the graph at query time has far more edges than the `.om` files alone declare.
The reasoning space is richer than the raw data.

**4. Domain closure — how `sthita` chains create membership**

Every domain concept has a `domain-X-sthita` edge:
```
force → domain-physics-sthita
raga  → domain-sangeetham-sthita
dna   → domain-biology-sthita
```

`domain-kosha.om` connects all domain anchors:
```
domain-kosha → domain-biology-yukta, domain-physics-yukta, domain-math-yukta, ...
```

The `domain-of` tantra walks up the `sthita` chain from any node to its domain anchor.
The projection operator uses this to enforce domain closure in answers.

**5. The cross-domain bridge — how concepts span domains**

Some nodes exist in `cross-domain/` or in `sangati/` and connect multiple domains via `abheda`:

```
spanda  (sangati) → abheda → vibration (physics/music/biology)
karma   (sangati) → abheda → force-apply (physics)
change  (cross)   → abheda → vivartana, transformation, vibration
epoch-in-physics  → abheda → compression-expansion (math/physics)
```

This is how `what is spanda` reaches physics, music, ayurveda, biology all at once —
the abheda axiom expansion propagates these links into the query neighborhood.

**6. The iccha distinction — how life is encoded in the ontology**

`iccha` (will/directed purpose) is a root sangati node with explicit absence markers:
```
iccha → visha-anu-rahita  (not present in atoms/inert matter)
iccha → jada-rahita       (not present in the inert/mechanical)
iccha → jiva-siddha       (established in living beings)
iccha → swatantra-siddha  (self-grounded, not derived)
```

Living nodes: `gene-sthita`, `dna-sthita`, `the-single-cell-sthita` → `iccha-sthita`
Inert nodes: `virus-rahita`, `inert-rahita` → `iccha-rahita`

This is not commentary — it is graph structure that drives the iccha bridge line in answers
(`directed-will (iccha) present in dna, double-helix; absent in virus`).

**7. Node satya — how structural weight flows from topology**

`raw_satya` is computed purely from local structure at load time:
```
s = sloka_count / (1 + sloka_count)   — textual grounding
e = edge_count  / (1 + edge_count)    — connectivity
d = type_diversity / (1 + type_diversity)  — relation breadth

σ(v) = (s · e · d)^(1/3)   if edge_count > 0
σ(v) = s · 0.5              if edge_count = 0
```

Highly-connected nodes in the root sangati layer (e.g. `spanda`, `brahman`) naturally score
higher than sparse leaf nodes. This propagates into PPR scoring at query time.

**8. How new knowledge connects into the existing graph**

Adding a new concept:
1. Create `brahman/kosha/<domain>/<concept>.om` with slokas + edges
2. At minimum include `domain-<X>-sthita` for domain membership
3. Add `swarupa`, `abheda`, `yukta`, `sthita` edges to existing nodes as appropriate
4. Axiom expansion at next startup will fill in symmetric/transitive consequences
5. `node-satya` will be set from local topology
6. The node is immediately queryable — no other change needed

**9. The engine inside the graph — self-referential layer**

The engine describes itself in `brahman/engine/*.om`:
- `proof-graph.om` — the graph knows what a proof-graph is
- `vyakarana.om` — the engine knows what vyakarana is
- `session.om` — session is a node with edges describing what it accumulates
- `kosha.om` — the knowledge sheath knows it feeds the proof space
- `bridge.om` — the Rust bridge is a node in the graph it serves

This means `what is proof-graph` and `what is vyakarana` return real answers from the graph.
The system is partially self-describing.

**10. Worked ontology trace: `what is karma` routing**

Show the full ontology path for `karma`:
- sangati root node: `karma`
- edges: `om-yukta spanda-yukta brahma-yukta brahmam-phala avrti-kriya ananta-sthita svayambhu-siddha jiva-yukta lekhana-phala`
- abheda expansion: `karma ↔ force-apply` (via axiom)
- query routes to physics neighborhood through this abheda bridge
- output: `action-that-writes the same as force-apply, the same as force, the same as gravitational-force`
- This is cross-ontology reasoning made visible

#### Source files for this document
- `brahman/sangati/*.om` — all root nodes
- `brahman/kosha/yantra/visheshanam/*.om` — relation algebraic properties
- `brahman/kosha/domain-kosha.om` — domain anchor connections
- `brahman/kosha/cross-domain/*.om` — explicit cross-domain bridges
- `brahman/engine/*.om` — self-description layer
- `vyakarana/lib/proof_graph.ml` — raw_satya, apply_relation_axioms, run_ppr
- `vyakarana/lib/yantra_index.ml` — axiom expansion implementation

---

### knowledge-layers.md (NEW)

- Layer 1 `.om`: nodes and typed relational edges (sangati vs kosha distinction)
- Layer 2 `.tantra`: executable symbolic programs — format walkthrough
- Layer 3 `.shabda`: surface/language config — presentation vocabulary
- How layers compose at runtime
- Worked example: adding a new concept end-to-end
- The `visheshanam` relation algebra (10 types, their algebraic properties from `.om` data)

### reasoning-pipeline.md (NEW)

- Full pipeline from sentence to output string, unified in one document
- Stage 1: tokenize
- Stage 2: classify (piecewise map with math)
- Stage 3: compound fold-resolve (iterative fixpoint with math)
- Stage 4: intent extraction (indicator functions)
- Stage 5: binding/target extraction (triple predicate rules)
- Stage 6: plan resolution (policy: direct vs inverse vs chain)
- Stage 7: execution or anuvada fallback (branch gate algebra)
- Stage 8: conceptual projection (PPR → tier partition → domain closure)
- Stage 9: language composition (shabda-driven clause assembly)
- One diagram (text/ASCII) showing the full flow

### three-solve-modes.md (NEW)

- Mode 1: Direct forward — all inputs satisfied, evaluate tantra expression tree
- Mode 2: Inverse solve — output known, one input missing, `invert_chain` symbolic inversion
- Mode 3: Chain solve — beam search over tantra composition space, PPR-guided, depth_affinity-blended
- For each mode: math, worked numeric example, failure case
- Worked example direct: `force when mass=10, acceleration=9.8` → 98 N
- Worked example inverse: from voltage+resistance → current
- Worked example chain: multi-tantra derivation
- Error branch: missing-input vs identity-intent suppression

### session-and-memory.md (NEW)

- What session is in code: `mutable bindings list`, `last_result`, `history`, `context_seeds`
- How bindings persist: `remember-bindings` op, session accumulation
- Multi-turn worked example: `mass is 5` → `velocity is 3` → `kinetic energy` → 22.5 J
- How session bindings extend the binding set for plan resolution
- Structural learning: `K_{t+1} = K_t ⊕ Δ_t` — adding `.om`/`.tantra` = learning
- No retraining: inference runs directly from current graph state
- Comparison: parameter learning (gradient descent, opaque) vs structural accretion (explicit, auditable)
- How to extend the graph: file format, rebuild index, immediate effect

### capacity-and-footprint.md (NEW)

- Actual numbers: 4.6 MB binary, 1.74 MB corpus, ~6.3 MB total
- 1,240 nodes, 4,743 axiom edges, 94 tantras, 14 constants
- PPR complexity: O(k·|E|), k ≤ 50, |E| ≈ 5,000–10,000 → operationally bounded
- Beam search: O(beam_width × depth × |candidate_tantras|), all bounded
- Node scaling: hashtable — O(1) lookup, linear memory growth
- No GPU, no network, single OCaml process
- Comparison row: LLM 7B = ~14 GB weights; this engine = 6.3 MB total
- Deployment target: embedded device, edge server, single container, CLI pipe
- Startup: ~0.7s cold (includes graph load + axiom expansion + tantra index)
- Determinism: same inputs → same output, zero stochastic component

### domain-coverage.md (NEW)

- Table: all domains with node counts and sample concepts
- What each domain covers (one paragraph per domain)
- Tantra coverage table: which equations are executable, which domains they serve
- How to read what's in the graph: `DARSHANA <concept>`, `INSPECT <domain>`
- How to extend: adding a new domain (`.om` nodes + optional `.tantra`)
- Cross-domain nodes and how the graph bridges domains (cross-domain/ directory)
- Current gaps: what's not yet covered (finite element methods, statistics, linguistics)

### applications.md (NEW)

- Embedded AI assistant: 6.3 MB, runs offline, deterministic, auditable
- Scientific Q&A: compute + explain in one query; inverse solve for unknowns
- Robotics world model: explicit entities (graph nodes), constraints (sthita/siddha/pratipaksha), actions (kriya tantras), outcomes (phala)
- Multi-language output: swap shabda setu file for different language rendering (Malayalam example)
- Music generation: prayoga + strudel emission from graph walk over sangeetham nodes
- Code generation: relation-role mapping (swarupa→declaration, kriya→action body, phala→return)
- Safety-critical systems: every output traceable to graph fact + relation + equation

### worked-examples.md (expand existing)

- Example A: `what is force` — conceptual, PPR neighborhood, projection, composition
- Example B: `force when mass is 10` — missing-input error, not identity so surfaced
- Example C: `kinetic energy when mass=5, velocity=6` — direct forward solve, 90 J
- Example D: `what is life` — cross-domain biology conceptual walk, iccha bridge
- Example E: multi-turn session — `mass is 5`, `velocity is 3`, `kinetic energy` — session recall
- Example F: inverse solve — give output + partial inputs → solve for missing
- Example G: chain solve — multi-tantra derivation (temperature conversion → gas law)
- Example H: `universal gravitation when m1=5.97e24, m2=7.35e22, distance=3.84e8` → Earth-Moon force
- Example I: `what is raga` — music domain conceptual walk
- Example J: `what is consciousness` — philosophy + sangati intersection

---

## Key Mathematical Content to Include

All equations should appear in the correct chapter with:
1. The formula
2. Variable definitions
3. Concrete numbers from live probe
4. Worked numeric derivation

Key equations:
- Node satya: `σ(v) = (s·e·d)^(1/3)` 
- Entropy weight: `w_r = 0.5 + (w_raw - w_min)/(w_max - w_min) × 0.45`
- Seed conductance: `κ_r = w_r(1 + f_r)`
- PPR recurrence: `p_{t+1}(v) = α·s(v) + (1-α)·Σ p_t(u)·κ_{rel}/out_cond(u)`, α=0.30
- Depth affinity: `φ = clamp((binding_density · link_ratio · computational_ratio)^(1/3))`
- Blend: `score = ppr·(1-φ) + (1/(d+1))·φ`
- Branch gate: missingInput ∧ ¬hasIdentity → show error, else → anuvada
- Context score: `ctx(n, S) = |{e ∈ edges(n) | e.source ∈ S ∨ e.target ∈ S}|`
- Projection: `Π_{I,D}(E) = E_aadya ∪ E_anantara ∪ Ẽ_apara`
- Sentence: `eng(u) + join(unique({λ(r_i) eng(v_i)}), ", ") + "."`
- Learning: `K_{t+1} = K_t ⊕ Δ_t`

---

## Token Classification Math (already in input-output-graph-math.md — keep there)

The piecewise classifier and fold-resolve fixpoint are well-covered.
Do not duplicate — just cross-reference from reasoning-pipeline.md.

---

## Tone and Style Notes

- Technical but readable — every equation followed by plain-English interpretation
- Use actual measured numbers, not vague claims
- Show real CLI output where possible (copy from live runs)
- Keep each doc self-contained but link to others
- Avoid: "powerful", "intelligent", "understands" (unmeasurable)
- Prefer: "resolves", "projects", "computes", "scores", "composes" (observable)

---

## Priority Order for Writing

1. `knowledge-layers.md` — foundational, everything else builds on it
2. `three-solve-modes.md` — most technically novel, most questions come here
3. `session-and-memory.md` — commonly asked, not documented anywhere
4. `capacity-and-footprint.md` — practical deployment questions
5. `domain-coverage.md` — orientation for new users
6. `reasoning-pipeline.md` — good unified reference once others exist
7. `applications.md` — can reference all other docs
8. `overview.md` — rewrite last once all chapters exist
9. Expand `worked-examples.md` — add new traces as chapters complete

---

## Source Files Referenced

**Runtime / engine:**
- `vyakarana/lib/proof_graph.ml` — node satya, PPR, depth affinity, entropy weights
- `vyakarana/lib/yantra_resolver.ml` — beam search, chain solve, inverse solve
- `vyakarana/lib/yantra_types.ml` — session struct, binding, value types
- `vyakarana/lib/yantra_pipeline_ops.ml` — tokenise, classify, session ops, execute-plan
- `vyakarana/lib/setu_classify.ml` — token classification pipeline
- `vyakarana/lib/yantra_inverter.ml` — invert_chain symbolic inversion

**Tantras (pipeline):**
- `brahman/yantra/anuvada-ganana.tantra` — orchestrator
- `brahman/yantra/classify-fold.tantra` — token classification + fold
- `brahman/yantra/classify-fold-resolve.tantra` — compound resolution
- `brahman/yantra/query-intents.tantra` — intent extraction
- `brahman/yantra/yantra-plan-extraction.tantra` — binding/target extraction
- `brahman/yantra/yantra-plan-resolution.tantra` — planner policy
- `brahman/yantra/visheshanam-projection.tantra` — conceptual projection
- `brahman/yantra/compose-answer.tantra` — language composition
- `brahman/yantra/firstness-of-triple.tantra` — tier assignment

**Knowledge:**
- `brahman/kosha/yantra/visheshanam/*.om` — relation algebraic properties + weights
- `brahman/engine/*.om` — engine self-description nodes
- `brahman/personal/*.om` — personal/experiential layer
- `brahman/sangati/*.om` — root ontology nodes (240)

---

_Last updated: exploratory session, Sun Mar 08 2026_
