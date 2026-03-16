# Nyaya Plan — Canonical Reference

**Created**: 2026-03-14
**Updated**: 2026-03-15
**Status**: Active — supersedes full-pipeline-plan.md for architecture decisions
**Baseline**: 314 passed / 13 xfailed / 0 failing (pytest). Do not break passing tests.

---

## What We Found

Starting from a single bug (`acceleration = 0.2` instead of `5`), we traced through
successive layers to arrive at a complete reasoning architecture.

### Layer 1 — The surface bug
`List.rev` in `execute-chain` reverses args before pushing onto the stack. Every
non-commutative operation (subtraction, division) in every physics mantra is computing
the wrong result. 9 mantras affected.

### Layer 2 — Why the bug exists
`krama-rhs` is a flat string serving two conflated purposes:
- **Matching** — `match-mantra` checks if all concepts are bound (order irrelevant)
- **Execution** — `execute-chain` uses it as the arg list for the stack machine (order critical)

These two needs pull in opposite directions. You cannot satisfy both with one string
in one convention.

### Layer 3 — The stack machine is the wrong abstraction
The krama step sequence (`subtraction-krama, division-krama`) and the `krama-rhs` string
are two representations of the same formula that can silently diverge. The comment
`-- a = (v-u)/t` is a third. All three can disagree. The formula has no single
authoritative representation.

### Layer 4 — The graph already has the structure
`janya` edges = inputs. `phala` edge = output. `krama` edges = operation sequence.
`sthita` = logical condition. These are already on mantra nodes. The stack machine
is redundant — the graph IS the formula. Walk it.

### Layer 5 — Physics and logic are the same structure
Every physics mantra has `sthita: implication` — it IS a logical implication.
`modus-ponens` has the same `janya`/`phala` shape — just over truth values
instead of numbers. The physics/logic split is surface only.

### Layer 6 — A mantra has two phalas simultaneously
When `acceleration-mantra` fires:
1. **Sankhya phala** — `acceleration = 5` (the numeric value)
2. **Satya phala** — `acceleration-known` (the fact that acceleration is established)

The satya phala becomes janya for logical mantras. Every numeric computation
automatically populates a truth layer. The two layers feed each other.

### Layer 7 — Nyaya is the logical reasoning layer
`nyaya` reasons over the satya layer that sankhya computations populate.
It answers logical questions ("can X be negative?", "is this physically valid?",
"what follows from knowing X?") by chaining satya phalas through logical mantras.

### Layer 8 — Varga is the imagination frame
Each domain has a varga root that IS the imagination frame for that domain.
`fluid-varga` = the lens for density, pressure, viscosity problems.
`geometry-varga` = the lens for shape, distance, area problems.
`3d-varga` (missing) = the spatial visualisation frame — sits above geometry AND physics.

The varga inheritance chain:
```
mass-density-mantra
  vishesa→ fluid-varga
    vishesa→ physics-varga
      vishesa→ math-varga
```

Currently `varga-vishesa` strings in `.om` files create dead `sthita` edges to
non-existent nodes (e.g. `fluid-varga-vishesa` has `satya=0`). The naming convention
implies the inheritance but the parser treats the whole string as a node name.

`derive-step` and `match-mantra` currently try ALL 24 mantras with no varga filtering.
Varga filtering would narrow candidates to the active imagination frame.

### Layer 9 — 3D is the visualisation varga
`domain-3d` is `sthita domain-math` AND `domain-physics` — it IS a subdomain of both.
But there is no `3d-varga` in the varga inheritance chain.

The graph already contains the right structure for scene construction:
- `scene-graph abheda proof-graph` — a physics scene IS a proof graph
- `force-directed` and `particle` show the pattern: `sthita domain-3d + domain-physics`,
  carrying `velocity`, `position`, `spring-force` — physics quantities on 3D objects
- `kinematic-chain` bridges `domain-3d`, `domain-physics`, `domain-robotics` — the model
- `velocity kramanusara displacement` — rate of change IS the 3D animation primitive
- `position-step` and `velocity-step` exist as tinanta (actions) in the graph

A physics problem scene = `scene-graph` where each entity is simultaneously:
- A geometric shape (`gola`, `vrtta-stambha`) with spatial properties
- A physics body with quantities (mass, velocity, position in `world-space`)
- Connected via forces/constraints to other entities

Rate of change (kramanusara) connects physics to 3D motion: velocity IS dura/kaala,
which IS the animation step. The physics problem can be understood as a 3D scene
because the graph already represents motion as kramanusara.

### Layer 10 — Geometry quantities are the missing bridge
All geometry shape nodes (`gola`, `vrtta-stambha`, `vrtta`, `trikona`) have good satya
and correct structural edges — but **zero measurement quantities**:

| Quantity | satya | word: | Missing for |
|---|---|---|---|
| `volume`        | 0 | None | mass-density, gola, vrtta-stambha |
| `area`          | 0 | None | pressure (force/area), trikona, vrtta |
| `circumference` | 0 | None | vrtta |
| `surface-area`  | 0 | None | gola, vrtta-stambha |
| `diameter`      | 0 | None | vrtta, gola |
| `width`         | 0 | None | cuboid shapes |
| `depth`         | 0 | None | cuboid shapes |

`dura` (distance/scalar separation) already exists with `satya=0.839`, `swarupa matra`.
`dura` IS the radius concept — `gola sthita sama-dura` (all points equidistant from bindu).
`pi` already has `yukta circumference` and `yukta diameter` — those nodes are referenced
but not built.

Units: `metre` exists (`word: m,metre,meter`). `square-metre` and `cubic-metre` have
`satya=0` — they don't exist as real nodes.

The `mass-density-mantra` test fails because `volume` has no `word:` key — BQG emits
`['volume', 'mithya', 'volume']` instead of `['volume', 'satya', 'volume']`.

---

## The Complete Architecture

### Two parallel layers, bridged by mantras

```
SANKHYA LAYER                    SATYA (NYAYA) LAYER
─────────────────                ──────────────────────────────
mass = 1200       ──fires──→     mass-known
velocity = 40     ──fires──→     velocity-known
energy = 960000   ←──fires──     energy-known
                                  energy > 0
                                  conservation-holds
                                  "can energy be negative?" → NO
```

Every mantra bridges both layers:
- Consumes sankhya janya (numeric inputs)
- Produces sankhya phala (numeric output)
- Simultaneously produces satya phala (fact of knowing the output)

Logical (nyaya) mantras live in the satya layer:
- Consume satya janya (known facts as inputs)
- Produce satya phala (new conclusions)
- Can query into sankhya layer for comparisons

### Three phala types

| Type | What | Example |
|---|---|---|
| `sankhya` | numeric value | `acceleration = 5` |
| `satya` | truth value | `acceleration-known`, `energy-positive` |
| `pada` | symbolic term | `v = sqrt(2·KE/m)` (uninverted) |

The phala type is implicit in the swarupa of the phala node:
- `acceleration` node has `sankhya-swarupa` → numeric
- `acceleration-known` node has `satya-swarupa` → truth
- Warm-blooded IS a satya concept directly (no number involved)

### The five mantra edges (complete formula description)

```
janya       → what it needs (input concepts)
krama       → how it transforms (operation sequence, as graph nodes)
phala       → what it produces (output concept)
sthita      → when it is valid (logical condition)
pratipaksha → its inverse (rearranged form for solving unknowns)
```

Everything else (`krama-rhs` string, `krama-lhs` string, stack machine arg order)
is **derived** from these five edges. No divergence possible.

### Varga as imagination frame

```
GEOMETRY VARGA          3D VARGA (missing)       PHYSICS VARGA
──────────────          ──────────────────       ─────────────
bindu, rekha,           gola + mass              fluid-varga
kona, kshetra,          vrtta-stambha + volume   kinematics-varga
gola, vrtta             scene-graph              dynamics-varga
    ↑ shape                  ↑ scene                  ↑ formula
    
geometry quantities ──→ 3d scene objects ──→ physics mantras fire
(volume, area, dura)    (position, shape)   (density, force, energy)
```

---

## What Changes in the Mantra Nodes

### Current (broken)
```
acceleration-mantra
  "subtraction-krama"          ← execution sequence (stack order)
  "division-krama"
  "execute-chain-kriya"        ← callable tag
  "implication-sthita"
  "final-velocity-janya"
  "initial-velocity-janya"
  "time-janya"
  shabda krama-lhs:acceleration krama-rhs:final-velocity,initial-velocity,time
```

Problems:
- `krama-rhs` arg order conflicts with stack machine `List.rev`
- `phala` is buried in `shabda` as a string (`krama-lhs:acceleration`), not a graph edge
- No satya phala edge
- Inversion requires reading the krama step sequence and inverting manually

### Target (correct)
```
acceleration-mantra
  "implication-sthita"
  "final-velocity-janya"
  "initial-velocity-janya"
  "time-janya"
  "acceleration-phala"         ← graph edge, not shabda string
  "acceleration-known-phala"   ← satya phala — the fact of knowing
  "execute-chain-kriya"
  shabda name:acceleration krama-lhs:acceleration krama-rhs:time,initial-velocity,final-velocity
```

Where:
- `krama-rhs` order is now **execution order** (stack-correct: last arg at top after List.rev)
- `phala` is a real graph edge pointing to `acceleration` concept node
- `acceleration-known` is a satya node that nyaya mantras can consume
- `krama` steps remain for backward compatibility with current execute-chain

### Longer term (krama as expression graph)
Replace the flat krama step sequence with a `kriya` edge pointing to the root
of an expression subgraph:

```
acceleration-mantra --kriya--> divide
                                 --dividend--> subtract
                                                 --minuend-->    final-velocity
                                                 --subtrahend--> initial-velocity
                                 --divisor-->  time
```

Forward evaluation: walk bottom-up, substitute leaves, compute.
Inversion: rearrange the subgraph to isolate any unknown leaf.
No stack machine needed. No arg order problem. No List.rev.

---

## What Changes in the Tantras

### derive-step.tantra (exists, working)
Currently uses `krama-rhs` shabda string for input lookup.
Should use `janya` edges directly — cleaner, no string parsing.
Also: after firing, assert satya phala for each derived concept.

### nyaya-step.tantra (new)
Mirror of `derive-step` but for the satya layer:
- Finds logical mantras whose satya janya inputs are all established
- Fires them, produces satya phala
- Adds new satya bindings to the graph

```
tantra nyaya-step
  takes graph

  -- build set of established satya facts
  -- find logical mantras with all janya covered
  -- fire each, add satya phala to graph
  -- return enriched graph
done
```

### anuvada-ganana.tantra (upgrade)
```
raw-graph = build-question-graph sentence
refined   = fixpoint raw-graph avrti-refine
enriched  = fixpoint refined derive-step      ← sankhya layer
reasoned  = fixpoint enriched nyaya-step      ← satya/nyaya layer
match     = match-mantra reasoned
```

The nyaya pass runs after derive-step, over the enriched graph.
It can answer both numeric questions (via match-mantra on sankhya)
and logical questions (via match-mantra on satya).

---

## What Changes in the Kosha

### Geometry quantities layer (new — unblocks P8a mass-density)
```
brahman/kosha/math/geometry/quantities/
  volume.om          word:volume,volumes,cubic   matra:cubic-metre   geometry-varga-vishesa
  area.om            word:area                   matra:square-metre  geometry-varga-vishesa
  circumference.om   word:circumference          matra:metre         geometry-varga-vishesa
  surface-area.om    word:surface-area           matra:square-metre  geometry-varga-vishesa
  diameter.om        word:diameter               matra:metre         geometry-varga-vishesa
  depth.om           word:depth                  matra:metre         geometry-varga-vishesa
  width.om           word:width                  matra:metre         geometry-varga-vishesa
```

Note: `dura` already exists as the radius/distance primitive (satya=0.839).
No new radius node needed — mantras use `dura-janya`.

### Unit nodes (new)
```
brahman/kosha/physics/units/
  square-metre.om    word:m2,square-metre,square-meter
  cubic-metre.om     word:m3,cubic-metre,cubic-meter
```

### Geometry mantras (new — connects shapes to quantities)
```
brahman/kosha/math/geometry/mantras/
  vrtta-area-mantra.om              π·r²      janya:dura  phala:area
  vrtta-circumference-mantra.om     2·π·r     janya:dura  phala:circumference
  trikona-area-mantra.om            ½·b·h     janya:rekha,dura  phala:area
  gola-volume-mantra.om             (4/3)·π·r³  janya:dura  phala:volume
  gola-surface-area-mantra.om       4·π·r²    janya:dura  phala:surface-area
  vrtta-stambha-volume-mantra.om    π·r²·h    janya:dura,dura  phala:volume
```

These enable the chain: "find density of sphere radius 3 mass 60"
→ gola-volume-mantra fires (dura=3) → volume=113.1
→ mass-density-mantra fires (mass=60, volume=113.1) → density=0.53

### 3d-varga (new — the visualisation imagination frame)
```
brahman/kosha/3d/3d-varga.om
  "geometry-varga-vishesa"     ← 3d inherits geometry
  "physics-varga-vishesa"      ← 3d IS also physics
  scene-graph-yukta
  akasham-yukta
  gati-yukta                   ← 3d involves motion
```

Update `gola.om` and `vrtta-stambha.om` to add `3d-varga-vishesa`.
This connects geometry shapes into the varga inheritance chain.

### Nyaya mantras (new nodes)
Logical inference mantras with janya/krama/phala edges over satya:

```
brahman/kosha/math/logic/mantras/modus-ponens-mantra.om
  "inference-swarupa"
  "implication-sthita"
  "premise-janya"
  "implication-janya"
  "conclusion-phala"
  "nyaya-chain-kriya"           ← callable by nyaya-step
  shabda name:modus-ponens krama-lhs:conclusion krama-rhs:premise,implication

brahman/kosha/math/logic/mantras/transitivity-mantra.om
  P→Q, Q→R ⊢ P→R

brahman/kosha/math/logic/mantras/physical-validity-mantra.om
  mass-known + energy-known ⊢ physically-valid (if both > 0)

brahman/kosha/math/logic/mantras/conservation-mantra.om
  initial-energy-known + final-energy-known ⊢ conservation-holds (if equal)
```

### Satya phala nodes (new)
For each physics concept that can be computed, a corresponding satya node:

```
brahman/sangati/known.om       ← base satya marker
acceleration-known             ← "acceleration has been established"
energy-known                   ← "energy has been established"
velocity-known
...
```

Or more elegantly: a single `known` relation edge rather than per-concept nodes.
`[acceleration, known, satya]` — acceleration IS known. Walk `known` to get all
established facts.

### phala edges on all physics mantras
Add `X-phala` edges to all 24 physics mantra nodes.
Remove `krama-lhs` from shabda (redundant once phala edge exists).
Fix `krama-rhs` order to match stack machine convention (short term fix).

---

## Implementation Order

### P8a — Fix the stack machine bug + missing volume word ✅ COMPLETE

**Done:**
1. `volume.om` built at `brahman/kosha/math/geometry/quantities/volume.om` ✓
2. `test_chain_force_from_suvat` xfail marker removed ✓

Mantras fixed: acceleration ✓, pressure ✓, angular-velocity ✓,
centripetal-force ✓, capacitance ✓

Mantras still broken (structural — deferred to P8f):
- `frequency-mantra` — missing constant 1 in krama
- `period-mantra` — missing pi,2 constants
- `gravitational-force-mantra` — complex krama order

### P8b — Migrate derive-step and match-mantra to janya/phala edges ✅ COMPLETE

**Done:**
- `newton-second-law-motion.om` and `ohm-law.om` now have `janya` edges ✓
- `derive-step` uses `walk mantra "janya"` instead of `split krama-rhs ","` ✓
- `match-mantra` uses `walk mantra "janya"` and `walk mantra "phala"` ✓

### P8b.5 — Rashi instance layer ✅ COMPLETE

This layer was discovered as necessary between P8b and P8c.

**Done:**
- `sankhya.om` moved from `kosha/` to `sangati/` (structural primitive, not domain concept) ✓
- `rashi.om` rewritten — quantity instance with `vishesa`, `sankhya`, `matra` ✓
- `rashi-bandha.om` created — `of` as value-assignment edge, not shashthi-vibhakti ✓
- `prep-of.om` changed to `rashi-bandha-sthita` — distinct from possession ✓
- `emit-triples.tantra` excludes `rashi-bandha` from `is-concept` check ✓
- `vishesa-instance.tantra` bug fix — `let concept = last-active` before clear ✓
- `vibhakti-shashthi.tantra` bug fix — `clear cur-entity` after ownership ✓
- `kosha-expand` moved from `build-question-graph` to `anuvada-ganana` post-refine ✓
- `rashi-viveka.tantra` created — avrti pass for `label of value` constituent ✓
- `asprista-sankhya.om` updated ✓
- `test_rashi.py` — 14 tests all passing ✓

**What rashi instances provide:**
`v1` and `v2` in "ball1 has velocity v1 of 20" are now correctly identified as
rashi instances: `[v1, vishesa, velocity]`, `[v1, sankhya, 20.]`.
The pipeline emits clean structural triples and the avrti fixpoint resolves ownership.

### P8b.6 — Rashi→mantra bridge ✅ COMPLETE (2026-03-15)

**Done:**
- `rashi-anuvada.tantra` created — for each `[inst, vishesa, concept]` + `[inst, sankhya, val]`
  emits `[concept, sankhya, val]` after `vishesa-bandhana` ✓
- Wired into `avrti-refine.tantra` as last stage (after `vishesa-bandhana`, before `sankhya-bandha`) ✓
- `socket.ml` `pipeline_trace_response` stages list updated to include `rashi-anuvada` ✓
- `total-momentum-mantra.om` reclassified — was wrongly a formula mantra (`p=mv`);
  total momentum is a conservation principle over a system of particles, not a
  single-step derivation. Rewritten as kosha concept node only. Will become a
  nyaya/dvandva step in Phase 4. ✓
- `anuvada-ganana.tantra` pipeline order corrected: match-mantra fires FIRST on
  the understood graph; derive-step only runs if match returns empty (chained
  derivation fallback). Previously derive-step was firing ALL mantras eagerly before
  match-mantra, which produced ambiguous results when multiple mantras shared janya. ✓
- Tier 1 test sentences updated to include `find` (solve-for) — without a stated
  intent a sentence with mass+velocity is genuinely ambiguous (KE vs momentum). ✓
- `test_mantra_rashi.py` xfail markers removed from 9 promoted tests ✓

**Key design decision (pipeline order):**
```
WRONG (old): avrti-refine → kosha-expand → derive-step (fires ALL) → match-mantra
RIGHT (new): avrti-refine → kosha-expand → match-mantra (ONE, solve-for driven)
                → if no match: derive-step → match-mantra again (chained derivation)
```
The system understands first, then matches one target, then executes. Not compute
everything and pick from the pile.

**Test results after P8b.6:**
- 314 passed / 13 xfailed / 0 failing (up from 295/7 before this session)
- 10 new tests promoted from xfail → passing (all tier 1 + tier 2 from test_mantra_rashi.py,
  plus test_rashi_instance_feeds_ke_mantra)
- Socket debug commands: inspect-node, list-tantras, triples-of, pipeline-trace, mantra-status ✓
- vy.py debug helpers added ✓

### P8c — Satya phala layer
Add `known` relation to the graph (new sangati node `brahman/sangati/known.om`).
Update `derive-step` to assert `[concept, known, satya]` for each derived concept.
`match-mantra` to also match satya-phala mantras for logical questions.

### P8d — Nyaya mantras
Write nyaya mantra nodes in `brahman/kosha/math/logic/mantras/`.
Write `nyaya-step.tantra`.
Upgrade `anuvada-ganana` to run `fixpoint nyaya-step` after `fixpoint derive-step`.
Write xfail tests for logical questions.

### P8e — Inversion + eval-mantra (active — see graph-native-execute-chain.md)
`execute-chain` replaced by `eval-mantra` — takes (mantra, question-graph), not
(mantra, flat-list). Three paths: forward, inverse, clarification.
**No explicit inverse tantras.** Inversion is handled by a single generic
`invert-expr` that walks the equation tantra's call tree top-down, applying
`pratipaksha` edges at each op node to isolate the unknown. One inverter works
for all 23 equation tantras — no per-equation authored inverse.
`match-mantra` returns [mantra] only.
Per-entity firing: match and eval fire once per entity with full janya coverage.
Clarification: when context incomplete, generate-question produces a new sphoTa.

### P8f — Polymorphic ops (inputs any, not inputs number)
Equation tantras updated: `inputs any` not `inputs number` — node indices passed.
Ops are polymorphic: resolve sankhya, walk kramanusara, reason from properties.
This also fixes frequency/period/gravitational-force — constants (`1`, `pi`, `2`)
become literal nodes in the equation tantra body rather than missing krama steps.

### P8g — Geometry quantities + 3d-varga (unblocks scene understanding)
Build the geometry quantities layer and 3d-varga.
This enables:
- Shape → volume → density chains (sphere, cylinder problems)
- Varga-based filtering in derive-step (only fire mantras in active imagination frame)
- Scene construction: physics problem as 3d scene-graph

---

## Key Principles

1. **The graph IS the formula** — janya/krama/phala edges ARE the computation description
2. **No flat strings for structure** — krama-lhs/rhs strings are transitional; phala/janya edges are canonical
3. **Two layers, one structure** — sankhya and satya use identical edge vocabulary
4. **Mantras bridge layers** — firing produces both numeric and truth phalas
5. **Nyaya reasons over satya** — logical questions answered by chaining truth phalas
6. **Inversion is free** — pratipaksha on the expression graph gives inverse without new mantras
7. **No hardcoding** — every formula, every inference rule, every logical relationship lives in the graph
8. **Varga is the imagination frame** — each domain's varga root IS the lens through which concepts are understood; derive-step should activate the right frame first
9. **3D is the visualisation varga** — not just a rendering pipeline; it IS the spatial imagination frame above geometry and physics; rate of change (kramanusara) connects physics quantities to 3D motion natively

---

## Current Baseline

- **314 pytest passing / 13 xfailed / 0 failing**
- `derive-step.tantra` working — fixpoint fires intermediate mantras correctly, uses janya/phala edges
- `anuvada-ganana.tantra` working — match-first pipeline, derive-step only as chained fallback
- `rashi-anuvada.tantra` live — rashi instances feed derive-step and match-mantra via concept-level sankhya
- KE chain test passing (`u,a,t,m → v → KE`)
- Force chain test passing (xfail removed)
- `mass-density` test passing (`volume.om` created)
- All mantras have janya edges and phala edges
- `total-momentum-mantra` reclassified as conservation principle (not formula mantra)
- Rashi instances correctly identified and bridged to concept level ✓
- No satya phala layer (P8c)
- No nyaya-step (P8d)
- No varga filtering in derive-step/match-mantra (P8g)
- No geometry quantities beyond volume (P8g)
- No 3d-varga (P8g)

### Remaining xfails (13)

| Test | Blocked by |
|---|---|
| `test_tier2_two_entities_ke_each` | two-entity rashi (dvandva groups) |
| `test_tier3_velocity_then_ke_chain` | tier 3 chained derivation via derive-step |
| `test_tier3_velocity_then_momentum_chain` | tier 3 chained derivation |
| `test_tier3_intermediate_velocity_in_graph` | tier 3 chained derivation |
| `test_tier3_force_then_work_chain` | tier 3 chained derivation |
| `test_two_entity_rashi_feeds_mantra` | two-entity rashi |
| `test_frequency` | structural — P8f (frequency=1/T, constant 1 in krama) |
| `test_period` | structural — P8f (pi,2 constants in krama) |
| `test_gravitational_force` | structural — P8f (complex krama order) |
| `test_avrti_entity_owns_property_via_has` | entity ownership Gap 4 |
| `test_avrti_dvandva_collection_of_two_values` | dvandva groups Phase 4 |
| `test_avrti_entity_ownership` | entity ownership Gap 4 |
| `test_cross_turn_binding_completes_match` | session wiring Gap 5 |

---

## Files

### Active tantras
```
brahman/yantra/pipeline/anuvada-ganana.tantra   orchestrator
brahman/yantra/pipeline/derive-step.tantra      sankhya fixpoint step
brahman/yantra/pipeline/build-question-graph.tantra
brahman/yantra/pipeline/materialize-question-graph.tantra
brahman/yantra/pipeline/kosha-expand.tantra
brahman/yantra/avrti/avrti-refine.tantra
brahman/yantra/avrti/avrti.tantra
brahman/yantra/match/match-mantra.tantra
```

### Created / modified (P8b / P8b.5 — prior session)
```
brahman/sangati/sankhya.om                          moved from kosha/ — structural primitive
brahman/sangati/rashi.om                            rewritten — quantity instance ontology
brahman/sangati/prashna/rashi-bandha.om             NEW — value-assignment edge type
brahman/sangati/prashna/asprista-sankhya.om         updated
brahman/kosha/math/geometry/quantities/volume.om    NEW — word:volume (P8a)
brahman/kosha/yantra/visheshanam/visheshanam-ring.om added rashi-bandha-yukta
brahman/bhasha/english/grammar/prep-of.om           rashi-bandha-sthita (not shashthi-vibhakti)
brahman/yantra/vishesa/vishesa-instance.tantra      bug fix: let concept = last-active before clear
brahman/yantra/vishesa/rashi-viveka.tantra          NEW — avrti pass for label/of/value constituent
brahman/yantra/vibhakti/vibhakti-shashthi.tantra    bug fix: clear cur-entity after ownership
brahman/yantra/sankhya/emit-triples.tantra          excludes rashi-bandha from is-concept
brahman/yantra/pipeline/build-question-graph.tantra removed kosha-expand
brahman/yantra/pipeline/derive-step.tantra          uses janya/phala edges
brahman/yantra/match/match-mantra.tantra            uses janya/phala edges
brahman/yantra/avrti/avrti-refine.tantra            added rashi-viveka pass
vyakarana/tests/test_rashi.py                       NEW — 14 tests
```

### Created / modified (P8b.6 — this session 2026-03-15)
```
brahman/yantra/vishesa/rashi-anuvada.tantra         NEW — P8b.6 bridge
brahman/yantra/avrti/avrti-refine.tantra            added rashi-anuvada pass (after vishesa-bandhana)
brahman/yantra/pipeline/anuvada-ganana.tantra       match-first pipeline order
brahman/kosha/physics/kinematics/linear/quantities/total-momentum-mantra.om
                                                    reclassified: mantra → kosha concept (conservation principle)
vyakarana/lib/socket.ml                             pipeline_trace stages: added rashi-anuvada
vyakarana/tests/test_mantra_rashi.py                9 xfail markers removed; tier 1 sentences updated with find
vyakarana/lib/socket.ml                             (requires dune build after change)
```

### To be written (next up — ordered by priority)

**Tier 3 chained derivation (unblocks 4 xfails):**
```
-- test_tier3_* tests: derive intermediate concept first, then feed target mantra
-- e.g. "find kinetic energy given u=0, a=10, t=3, m=2"
--      → velocity-mantra: v = u+at = 30 → kinetic-energy-mantra: KE = ½mv² = 900
-- Currently derive-step runs as fallback but match-mantra on enriched graph
-- should then find kinetic-energy-mantra. Need to verify the chain works end-to-end.
```

**Entity ownership gaps (unblocks 3 xfails — Gap 2+4):**
```
brahman/bhasha/english/grammar/verb-has.om          verify role:possession exists
brahman/bhasha/english/grammar/copula-was.om        role:bhuta-kaala
brahman/bhasha/english/grammar/verb-with.om         role:possession
```

**Two-entity dvandva (unblocks 2 xfails):**
```
-- test_tier2_two_entities_ke_each and test_two_entity_rashi_feeds_mantra
-- "ball1 has mass m1 of 3 and velocity v1 of 4, ball2 has mass m2 of 2 and velocity v2 of 5"
-- requires dvandva group handling — Phase 4
```

**P8c — Satya phala layer:**
```
brahman/sangati/known.om                            satya marker relation
-- derive-step: assert [concept, known, satya] for each derived concept
-- match-mantra: also match satya-phala mantras for logical questions
```

**P8d — Nyaya mantras:**
```
brahman/yantra/pipeline/nyaya-step.tantra           satya fixpoint step
brahman/kosha/math/logic/mantras/                   nyaya mantra nodes
-- anuvada-ganana: fixpoint nyaya-step after fixpoint derive-step
```

**P8e — Inversion (pratipaksha):**
```
brahman/yantra/pipeline/invert-expr.tantra    (or OCaml primitive)
-- single generic inverter: walks equation tantra call tree top-down
-- applies pratipaksha edges at each op to isolate unknown janya
-- works for all 23 equation tantras — no per-equation inverse authored
-- "find mass given KE=1000 and velocity=20" → invert-expr ke-expr mass KE known graph
```

**P8f — Expression graph (fixes frequency/period/gravitational-force):**
```
-- replace flat krama step list with kriya edge → expression subgraph
-- no more List.rev, no arg order issues, constants in graph
```

**P8g — Geometry quantities + 3d-varga:**
```
brahman/kosha/math/geometry/quantities/area.om      word:area
brahman/kosha/math/geometry/quantities/             full quantities layer
brahman/kosha/math/geometry/mantras/                shape volume/area mantras
brahman/kosha/3d/3d-varga.om                        visualisation varga
brahman/kosha/physics/units/square-metre.om
brahman/kosha/physics/units/cubic-metre.om
```

### Physics mantras still broken (deferred to P8f — structural)
```
brahman/kosha/physics/oscillation/quantities/frequency-mantra.om
brahman/kosha/physics/oscillation/quantities/period-mantra.om
brahman/kosha/physics/dynamics/linear-force/quantities/gravitational-force-mantra.om
```
