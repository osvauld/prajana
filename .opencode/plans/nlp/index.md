# Linguistic Graph & NLP Plan — Index

**Status**: P0–P5 (structure) done. Next: **P5 degree enrichment** then **P5.5** (physics mantra).

## Key decisions (quick reference)

- `kaala.om` IS the tense parent — no separate `kala.om`. Tense values use `-kaala` suffix.
- Three IS-A edges: `swarupa` (identity), `vishesa` (particular of universal), `amsha` (member of set).
- Sangati cluster anchors use `-sthalam` suffix. Members point UP via `X-sthalam-sthita`. Thin anchors only.
- Engine nodes (`proof-graph`, `om-parser`, `nigamana`, etc.) belong in `brahman/kosha/engine/` — NOT sangati.
- Kosha cluster nodes use `-varga` suffix. Varga nodes are pure organisational anchors.
- Directory structure IS the inheritance topology.
- `domain-X-sthita` on leaves replaced by `X-varga-vishesa`. Varga carries domain identity once.
- Math uses `structures/` + `properties/` + `operations/` subdirs.
- `lakshana` is the math property edge suffix.
- `krama` IS a registered dynamic dimension — already in ring. `square-krama` parses correctly.
- Mantra nodes are NOT a separate directory. Any kosha node with `krama` + `pratipaksha` IS a mantra node.
- Mantra node = formula + sentence + question. Same structure, three directions (execute/explain/invert).
- Formula node declares execution paths via `kriya` edges — context selects which to follow.
- Sangati roots (~50 nodes) ARE the atomic vocabulary. Formula language composes from them.
- Grammar composition is a second pass: krama chain → narrative → grammar (kaala/prayoga/vachana) → sentence.
- Logic/ nodes (inference, theorem, proof) describe the structure of scene understanding.
- Graph/ nodes (breadth-first, depth-first) describe the traversal strategy for chain-resolve.
- The engine is self-describing: its own operations are nodes in the graph it walks.

## Files in this directory

| File | Contents |
|---|---|
| [architecture.md](architecture.md) | Three-layer model (sangati/kosha/bhasha), bhave-prayoga principle, domain splits |
| [inheritance.md](inheritance.md) | Varga/vishesa/amsha system, full varga hierarchy tree, subdir pattern, walk costs |
| [grammar.md](grammar.md) | Sanskrit grammar nodes: kaala, vibhakti, prayoga, vachana, purusa, pada, etc. |
| [kosha-nodes.md](kosha-nodes.md) | Bhave process nodes + subanta quantity nodes catalog with sloka patterns |
| [bhasha-english.md](bhasha-english.md) | English bhasha layer — REVISED: sangati root vocabulary (~50 nodes) + grammar composition layer |
| [shabda-extraction.md](shabda-extraction.md) | Shabda inheritance, lookup priority chain, extraction pipeline, signal weights |
| [phase-2.9-math.md](phase-2.9-math.md) | Math kosha restructure — structure DONE, degree enrichment remaining |
| [phase-cs-restructure.md](phase-cs-restructure.md) | CS kosha full restructure: types/control/state/concurrency/modules/hardware |
| [migration-status.md](migration-status.md) | What is done, what is not done, full phase sequence |
| [engine-tantra-migration.md](engine-tantra-migration.md) | OCaml → tantra migration. Steps 0–4 DONE. |
| [graph-native-computation.md](graph-native-computation.md) | Core insight — graph edges ARE the formula. Walk = execution. Scene understanding = backward walk. |
| [graded-morphisms.md](graded-morphisms.md) | degree: + pratipaksha on operation nodes. Full table. |
| [graph-computation-tantras.md](graph-computation-tantras.md) | New tantras: compute-from-node, execute-chain, scene-walk, compose-degrees, apply-op primitive |
| [mantra-nodes.md](mantra-nodes.md) | Algebraic relation layer — krama + pratipaksha + kriya edges. Language composition. yantra_inverter.ml removal path. |
| [scene-understanding.md](scene-understanding.md) | **End-to-end pipeline** — how all NLP work connects. Worked examples. Logic/ + graph/ as operational vocabulary. Grammar composition pass. |

## Other plan files (sibling directory)

```
tantra-domain-authoring.md     READ BEFORE writing any tantra — pitfalls list
visheshanam-algebra-plan.md    Ring algebra background
sphota-scene-extraction-plan.md  sphoTa extraction pattern
```

## Regression baseline

49/52 passing. 3 pre-existing failures. Do not break further.

```
vyakarana/scripts/run-regression.sh
```

## Key source files

```
vyakarana/lib/proof_graph.ml        dynamic visheshanam registry, walk_inheritance, raw_satya
vyakarana/lib/om_parser.ml          decompose_compound, expand_dir (needs bhasha fix for P6)
vyakarana/lib/setu.ml               read_shabda, raw_shabda_for_node, merge_shabda_priority
vyakarana/lib/yantra_eval.ml        Var v VFn wrapping — DONE
vyakarana/lib/yantra_eval_primitives.ml  primitives done; apply-op to add at P8
vyakarana/lib/yantra_inverter.ml    TARGET FOR REMOVAL at P8.5
brahman/kosha/yantra/visheshanam/visheshanam-ring.om  krama-yukta already present
brahman/kosha/math/                 structure DONE; degree enrichment remaining
brahman/kosha/computation/information/  DONE (P5 step 13)
brahman/kosha/engine/               engine domain
brahman/bhasha/                     surface language forms (P6)
```

---

## Full Priority Stack

### DONE: P0–P5 (structure)

| Step | What | Status |
|---|---|---|
| P0 | Tantra dead-code cleanup | ✅ |
| P1 | setu.ml forwarding aliases | ✅ |
| P2 | Higher-order tantra VFn wrapping | ✅ |
| P3 | New primitives: in-degree, out-degree, neighbors, walk-chain, resolve-node | ✅ |
| P4 | Semantic tantras: has-domain, resolve-node, infer-inputs, infer-outputs, domain-of-seeds | ✅ |
| P4.5 | krama dimension — already in ring + sangati krama.om exists | ✅ |
| P5 (structure) | Math kosha full restructure — all subdirs + nodes written | ✅ |
| | algebra/, geometry/, calculus/, number/, set/, graph/, logic/, probability/, complexity/ | ✅ |
| | CS information/ upgrade + bit.om upgraded | ✅ |

---

### P5 (remaining) — Math operation degree enrichment

Add `degree:`, `per-element:`, `invertible:`, `inverse:` to shabda on operation nodes.
Add `pratipaksha` edges where missing. These properties are needed before P5.5 can
write krama chains that reference operation node properties.

**Nodes in `number/operations/`**:

| Node | degree | per-element | invertible | inverse | notes |
|---|---|---|---|---|---|
| `square` | 2 | yes | yes | sqrt | pratipaksha already present |
| `square-root` | 0.5 | yes | yes | square | — |
| `addition` | 1 | no | yes | subtraction | pratipaksha already present |
| `subtraction` | 1 | no | yes | addition | — |
| `multiplication` | 1 | no | yes | division | pratipaksha already present |
| `division` | 1 | no | yes | multiplication | — |
| `power` | exp | no | yes | logarithm | — |
| `logarithm` | log | yes | yes | power | — |
| `abs` | 1 | yes | no | — | — |
| `floor` | 1 | yes | no | — | — |
| `ceil` | 1 | yes | no | — | — |
| `factorial` | n! | no | no | — | — |

**Nodes in `calculus/operations/`**:

| Node | degree | invertible | inverse |
|---|---|---|---|
| `derivative` | d/dx | yes | antiderivative |
| `antiderivative` | ∫dx | yes | derivative |
| `fourier-transform` | ℱ | yes | fourier-transform (self-inverse up to scale) |

**Nodes in `geometry/operations/`**:

| Node | degree | invertible | inverse |
|---|---|---|---|
| `rotation-matrix` | SO3-element | yes | rotation-matrix (transpose) |
| `homogeneous-transform` | SE3-element | yes | homogeneous-transform (inverse) |
| `inverse` | -1 | yes | inverse (self-inverse) |

**Also add `kriya` edges on operation nodes** declaring what sangati operation they ARE:
- `square` → `power-kriya`, `multiplication-kriya` (self-multiplication)
- `derivative` → `calculus-kriya`
- etc.

Regression gate: 49/52.

---

### P5.5 — Physics mantra enrichment

Enrich existing physics kosha nodes with krama chains + pratipaksha + kriya edges.
Nodes already exist — this adds the algebraic relation layer.

**Per node, add:**
1. Ordered `krama` edges → math operation nodes (from P5 degree enrichment)
2. `pratipaksha` edges → inverse-form sibling nodes (written as new .om in same dir)
3. `kriya` edges → `execute-chain-kriya`, `execute-inverse-kriya` (executor declaration)
4. `degree:` + `krama-input:` + `krama-output:` in shabda

**Inventory** (full detail in mantra-nodes.md):
- Kinematics: velocity, displacement, velocity-squared, projectile-range
- Dynamics: newton-second-law, weight, friction-force, spring-force, momentum, impulse
- Energy: kinetic-energy, potential-energy, work, power
- Circular: centripetal-force, angular-velocity, torque, rotational-kinetic-energy
- Oscillation: period-spring, period-pendulum
- EM: ohm-law, electric-power

Regression gate: 49/52. `chain-kinetic-energy` failure may fix once `kinetic-energy.om`
carries proper krama + pratipaksha.

---

### P6 — Bhasha English layer (REVISED scope)

**Original scope**: per-formula bhasha nodes for all physics/math concepts.
**Revised scope**: sangati root vocabulary only — composition handles everything else.

**P6a — Sangati root bhasha forms** (~50 nodes, `brahman/bhasha/english/sangati/`):

Write bhasha nodes for each sangati root with English surface forms. These are the
atomic vocabulary. Any formula node with sangati `yukta` edges + krama chain gets
language for free through composition.

Priority roots: `matra`, `spanda`, `avrti`, `shakha`, `sambandha`, `kshaya`, `krama`,
`seema`, `rachana`, `viveka`, `niyama`, `satya`, `purna`, `svabhava`, `niralamba`,
`taranga`, `kona`, `viparita`, `eka`, `dvandva`, `chala`, `parampara`, `ananta`,
`vikrita`, `shunya`, `sama`, `apeksha` (~27 immediate; full list in bhasha-english.md).

Also requires: loader fix for `brahman/bhasha/` in `om_parser.ml:expand_dir`.

**P6b — Grammar composition layer** (for correct OUTPUT sentences):

Grammar nodes already exist in sangati (kaala/vibhakti/prayoga/vachana/purusa — DONE).
What is missing: bhasha nodes that provide surface grammar forms for composing responses.

These are not for PARSING — they are for GENERATING correct sentences:
- `vartamana-kaala` → "is", "equals", "gives"
- `purva-kaala` → "was", "computed", "gave"
- `kartari-prayoga` → active construction ("kinetic energy IS 180 J")
- `karmani-prayoga` → passive construction ("180 J IS THE kinetic energy")
- `eka-vachana` / `bahu-vachana` → singular/plural agreement

Grammar composition is a two-pass process:
1. Walk krama chain → step narrative (from sangati root bhasha forms)
2. Apply grammar context (kaala from query intent, prayoga from sentence role) → correct sentence

**P6c — Scene understanding via logic/ + graph/ nodes**:

The logic/ and graph/ sub-vargas we just built ARE the operational vocabulary for
scene understanding — not just ontological descriptions. The engine's own inference
process is described in its own language:

- `inference` = deriving what to compute from known premises
- `theorem` = a formula node that has been established and can be used in inference
- `proof` = the krama chain execution that establishes the result
- `implication` = if these inputs are known, then this formula can be executed
- `breadth-first` = the search strategy for chain-resolve (explore all neighbors first)
- `depth-first` = the search strategy for deep inference chains

When the user asks "what is the kinetic energy?" — this IS a proposition.
Scene understanding = finding which theorem (formula node) can be proved from the
known premises (given values). The inference walk through `implication` edges IS
`chain_resolve`. The result IS a `proof` via the krama chain.

**This means scene-walk.tantra (P8) should reference `inference-kriya` and
`implication-sthita` edges** — the logic nodes declare what scene understanding IS.
The graph nodes declare HOW it traverses (BFS/DFS strategy).

The engine becomes self-describing: its own reasoning process is a walk through
the same graph it reasons about.

---

### P7 — Simplify parsing tantras (post-P6a + P6b)

After sangati root bhasha nodes + grammar composition layer exist, rewrite:
- `setu-classify-token.tantra` — pure graph walk via dhatu edges, no shabda tables
- `yantra-plan-extraction.tantra` — vibhakti-driven argument roles
- `yantra-plan-resolution.tantra` — kaala-driven intent + kriya-driven executor selection
- `classify-fold-resolve.tantra` — grammar lookup via edges
- `firstness-of-triple.tantra` — data-driven from intent node edges
- `extract-value-units.tantra` — per-sentence indexing fix (global → per-sentence)

---

### P7.5 — Grammar-composing response tantras (NEW)

After P6b grammar composition layer exists, update:
- `format-response.tantra` — compose grammatically correct sentences:
  1. Walk krama chain of formula node → step narrative
  2. Read kaala/prayoga from query context (what tense was asked? active or passive?)
  3. Apply grammar surface forms from P6b bhasha nodes
  4. Return correctly inflected sentence
- `to-english` builtin or tantra — walks sangati `yukta` edges → type description
  then composes with krama narrative

---

### P8 — Graph-native computation tantras + apply-op primitive

**Depends on**: P5 degree enrichment, P5.5 pratipaksha on physics nodes.

**OCaml change** — add `apply-op` primitive to `yantra_eval_primitives.ml`.
Full spec in `graph-computation-tantras.md`.

**New tantras**:
- `compute-from-node.tantra` — generic dispatch via kriya edge
- `execute-chain.tantra` — fold over ordered krama edges, apply each op
- `scene-walk.tantra` — backward walk through pratipaksha to janya
  (references `inference-kriya` on formula nodes — uses logic/ vocabulary)
- `compose-degrees.tantra` — multiply degree: fields
- `is-identity-composition.tantra` — composed degree ≈ 1.0?
- `infer-inputs-from-output.tantra` — wraps scene-walk

Full specs in `graph-computation-tantras.md`.

---

### P8.5 — yantra_inverter.ml removal

**Depends on**: P5.5 (pratipaksha on physics nodes), P8 (execute-chain exists).

1. `resolve-inverse` in `yantra_pipeline_ops.ml`: walk `pratipaksha` first; fall back to `invert_chain` only if no pratipaksha edge (compat shim)
2. `chain_resolve` in `yantra_resolver.ml`: same shim
3. Once all used inversions covered → remove `invert_chain` calls
4. Remove `yantra_inverter.ml` from `lib/dune`

Gate: 49/52.

---

### P9 — CS kosha restructure

Full details in `phase-cs-restructure.md`. Not started.

---

## What changes in execution with mantra nodes

| Path | Before | After |
|---|---|---|
| Inverse resolution | `invert_chain` (OCaml AST) | walk `pratipaksha` → execute-chain on inverse node |
| Operation dispatch | `cond is-add ... is-mul ...` chains | `compute-from-node node values` via kriya edge |
| Executor selection | hardcoded in resolver | `walk formula "kriya"` filtered by context |
| Scene understanding | hardcoded patterns | `scene-walk` backward through pratipaksha → janya |
| Inference | hardcoded chain_resolve | `inference` walk — theorem from premises via implication |
| Grade composition | not expressible | `compose-degrees` multiplies `degree:` fields |
| Krama chain | symbolic expression tree in OCaml | ordered krama edge walk + execute-chain fold |
| Response sentence | hardcoded templates | krama chain narrative + grammar composition pass |
| New formula language | write bhasha node per formula | write .om node; sangati roots compose sentence |

---

## Living documentation workflow

| After completing | Update file |
|---|---|
| P5 degree enrichment | `graded-morphisms.md` — mark each node done |
| P5.5 physics mantra | `mantra-nodes.md` — mark each physics node done |
| P6a sangati bhasha | `bhasha-english.md` — mark roots written |
| P6b grammar composition | `bhasha-english.md` — mark grammar layer done |
| P6c scene understanding | `graph-computation-tantras.md` — add logic/ node references |
| P7 tantra simplification | `engine-tantra-migration.md` — mark steps 6-7 done |
| P7.5 response grammar | `bhasha-english.md` — mark format-response updated |
| P8 computation tantras | `graded-morphisms.md` + `graph-computation-tantras.md` — mark done |
| P8.5 inverter removal | `engine-tantra-migration.md` — mark yantra_inverter.ml removed |
| P9 CS restructure | `phase-cs-restructure.md` — mark each batch done |
