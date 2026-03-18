# 06 — What Is Next

**Baseline: see [changelog.md](changelog.md).**
**Do not break passing tests. Every step here should move at least one xfail to passing.**

---

## What was completed (since initial writing)

| Was | Now |
|---|---|
| Gap 3 (tier-3 rashi chain) — 4 xfails | All passing. Was already working, xfail markers were stale. |
| Gap 4 (entity ownership via `has`) — 2 strict xfails | Fixed. Tests were testing wrong input state. Real pipeline already correct. |
| Gap 5 (session wiring) — 1 strict xfail | Done. `session-anuvada.tantra` built. Cross-turn sankhya binding working. |
| Session understanding deepened | Multi-entity is session accumulation. Each turn adds one entity. |
| `test_entity_scene.py` written | 22 tests covering Gap 1, Gap 2, multi-entity accumulation, pratibimba render params. |
| Gap 1 fully closed (B, electron_natural_labels) | Parser: `or` infix in scan guards. Outer-let visibility. Baseline 362/14. |
| Paragraph / viraam foundation | `build-question-graph.tantra` fixed. Viraam emitted. `test_paragraph.py` 15/4. Baseline 376/19. |
| Boot/reboot architecture | `emit-edge` + `graph-all-nodes` OCaml primitives. `reboot.tantra` + `varga-inheritance.tantra`. Runs at startup and on `reload-all`. See `08-boot.md`. |
| Varga inheritance working | `walk-in "energy-varga" "varga"` → `["kinetic-energy", "potential-energy", ...]`. `swara-varga`, `oscillation-varga` etc. all populated. |
| Sandhi Way 2 (satya+satya) | `sandhi-kosha` now tries `word1-word2` lookup when both words are `satya`. `mass density` → `mass-density`, `photon energy` → `photon-energy`. |
| `photon-energy.om` authored | `photon-energy` concept node with `energy-swarupa`, `photon-yukta`, `frequency-yukta`. |
| `planck-constant.om` fixed | Added `shabda constants-key:planck-constant` — now auto-supplied in `photon-energy-mantra`. |
| `frequency.om` fixed | Added `shabda frequency / ...` line — `frequency` now resolves as `satya`, not `mithya`. |
| `wave.om` fixed | Removed `frequency` from word alias list — was shadowing `frequency` kosha node. |
| `test_frequency` xfail removed | Frequency now works — `f = 1/T` computes correctly. Down to 18 xfails. |
| Tests added | `test_bqg.py`: varga inheritance, photon-energy satya, frequency satya. `test_sandhi.py`: Way 1 + Way 2 sandhi. `test_physics_mantras.py`: photon energy (3 cases), planck constant auto-supply, mass density satya+satya compound. |
| Dvandva — entity-scoped computation | Done. `extract-solve-for` returns scope entity. `match-mantra` reads through the named entity's owned properties only. `sandhi-kosha` no longer compounds entity-subjects with what they own (`electron has mass` stays as electron owning mass — not `electron-mass`). 7 xfails → passing. Baseline 419/12. |
| Baseline | see [changelog.md](changelog.md) |
| Tantra authoring rules documented | Tensions 7–9 in `07-tantra-rewrite.md`. Boot pitfalls in `08-boot.md`. |

---

## The 12 xfails — where they come from

| Group | test | Notes |
|---|---|---|
| Gap 1 — unit rate | `test_unit_in_rate_not_stolen` | `m/s` compound unit not in word index |
| Gap 2 — entity identity | `test_session_entity_identity_persists` | session doesn't carry prathama/shashthi triples |
| Gap 2 — multi-entity | `test_two_entities_across_turns_both_present` | gated on session entity structure |
| Gap 2 — multi-entity | `test_two_entities_across_turns_scoped` | |
| Gap 2 — multi-entity | `test_electron_and_field_across_turns` | |
| Pratibimba — sphere | `test_sphere_shape_swarupa` | `sphere` not in word index → gola |
| Pratibimba — position | `test_position_ownership` | spatial position binding not implemented |
| Pratibimba — simulation | `test_electron_simulation_scene_full` | gated on Gap 2 |
| Dvandva — session | `test_avrti_dvandva_collection_of_two_values` | dvandva grouping not implemented |
| Dvandva — session | `test_tier2_two_entities_ke_each` | two-entity session, gated on Gap 2 |
| Dvandva — session | `test_two_entity_rashi_feeds_mantra` | relative velocity not yet in kosha |
| P8f — constants | `test_gravitational_force` | G constant + r² composition — deferred to P8f Phase B |

---

## Priority order

### 1. P8f — Expression subgraph + math-domain unification (NEW TOP PRIORITY)

**What changed:** Investigating inversion (P8e) revealed that the math kosha already
has the complete algebra — `multiplication`, `division`, `power`, `logarithm`,
`exponential`, `sine`, `cosine` — all with `pratipaksha` edges encoding their inverses.

The physics expr tantras (`ohm-expr.tantra`, `ke-expr.tantra`, etc.) are redundant.
They encode computation that the math kosha already knows how to do and invert.

**The insight:** Physics mantras should say WHAT the relationship is.
The math domain says HOW to compute and invert it. This unification:
- Eliminates 13+ expr tantras immediately (all simple `mul a b` / `div a b`)
- Gives free inversion for all those mantras via `pratipaksha` walk
- Unlocks Kirchhoff, Ohm's law inverse, SAS/DSP questions automatically
- The remaining 9 complex expr tantras (KE, velocity, acceleration, etc.)
  follow once the expression subgraph is in place

**What P8f means:**

Each expr tantra gets replaced by a graph structure in the kosha:

```
-- current (ohm-expr.tantra):
value = mul current resistance

-- P8f (ohm-law.om):
shabda math-op:multiplication
-- janya order encodes arg0=current, arg1=resistance
-- phala=voltage
-- no kriya edge, no expr tantra
```

For compositions (`ke = half(mul(mass, square(velocity)))`):

```
-- P8f expression subgraph:
ke-expr-root → [op: half, arg: ke-mul-node]
ke-mul-node  → [op: multiplication, arg0: mass, arg1: ke-sq-node]
ke-sq-node   → [op: square, arg0: velocity]
```

`execute-math.tantra` walks this subgraph forward.
`invert-math.tantra` walks it backward using `pratipaksha` edges at each node.

**Two phases:**

**Phase A — Simple mantras (13 mantras, no composition):**
Wire `math-op` shabda directly on mantra. Write `execute-math.tantra` +
`invert-math.tantra`. Delete 13 expr tantras. Update `match-mantra` to use
`invert-math` when solve-for is a janya.

Mantras: `ohm-law`, `momentum`, `newton`, `angular-momentum`, `electric-power`,
`friction-force`, `spring-force`, `torque`, `photon-energy` (multiplication),
`angular-velocity`, `capacitance`, `mass-density`, `pressure` (division).

**Phase B — Composed mantras (9 mantras, expression subgraph):**
Build kosha expression subgraph nodes. Write `execute-math-composed.tantra` +
`invert-math-composed.tantra`. Delete remaining expr tantras.

Mantras: `ke`, `velocity`, `acceleration`, `potential-energy`, `centripetal-force`,
`gravitational-force`, `work`, `period`, `frequency`.

**Also applies to:**
- Vector/matrix math: `vec-scale`, `vec-dot`, `mat-mul` — same path via math kosha
- SAS/DSP: `dB = 20×log(gain)`, `τ = RC`, `ω = 2πf` — new kosha nodes + math path
- Kirchhoff: `V_total = V1 + V2 + ...` — addition chain, math kosha handles it

**Files to delete (Phase A):**
```
brahman/yantra/equations/ohm-expr.tantra
brahman/yantra/equations/momentum-expr.tantra
brahman/yantra/equations/newton-expr.tantra
brahman/yantra/equations/angular-momentum-expr.tantra
brahman/yantra/equations/electric-power-expr.tantra
brahman/yantra/equations/friction-force-expr.tantra
brahman/yantra/equations/spring-force-expr.tantra
brahman/yantra/equations/torque-expr.tantra
brahman/yantra/equations/photon-energy-expr.tantra
brahman/yantra/equations/angular-velocity-expr.tantra
brahman/yantra/equations/capacitance-expr.tantra
brahman/yantra/equations/mass-density-expr.tantra
brahman/yantra/equations/pressure-expr.tantra
brahman/yantra/equations/inv-mul-arg0.tantra  (stub, not needed)
brahman/yantra/equations/inv-mul-arg1.tantra  (stub, not needed)
brahman/yantra/equations/inv-div-arg0.tantra  (stub, not needed)
brahman/yantra/equations/inv-div-arg1.tantra  (stub, not needed)
```

**Changes to physics `.om` files (Phase A):**
- Remove `"X-expr-kriya"` sloka
- Add `shabda math-op:multiplication` or `shabda math-op:division`

**New tantras:**
- `brahman/yantra/pipeline/execute-math.tantra`
- `brahman/yantra/pipeline/invert-math.tantra`

**Change to `match-mantra.tantra`:**
- When solve-for is a janya and all other janya + phala are bound → call `invert-math`

**xfails this directly closes:**
- `test_frequency` — once `frequency-mantra` wired to `reciprocal` math node
- `test_gravitational_force` — once G constant handled (Phase B)
- All future inversion tests (Ohm's law, photon energy, etc.)

---

### 2. Dvandva / vishesa-bandhana instance-map

**What:** `vishesa-bandhana` collapses multiple instances of same concept to first one.
Two entities both owning `mass` → only first entity's mass survives.

**Why second:** Paragraphs with two entities must work before sessions can accumulate
two entities. Same mechanism — just timing differs.

**The fix:** Per-entity instance-map instead of per-concept. Each
`[concept, shashthi-vibhakti, entity]` pair gets its own instance label.

**Tests unblocked:** 4 paragraph xfails + 5 dvandva session xfails

---

### 3. Gap 2 — Session entity structure

**What:** `session-anuvada` carries sankhya values only. Must carry:
- `[entity, prathama-vibhakti, object]` — entity identity
- `[property, shashthi-vibhakti, entity]` — ownership
- `[entity, vishesa, rashi]` — rashi type

**Gate:** Dvandva fix must come first — same structural issue in accumulated graph.

**Tests unblocked:** 5 Gap 2 xfails + 3 pratibimba xfails

---

### 4. Pratibimba blockers (after Gap 2)

- `sphere` → `gola` word index entry
- Spatial position binding (`bindu` as owned vector value)
- Orbital radius mantra (`r = mv/qB`) — needs P8f Phase A (division)
- EpochOutput generation from graph entity enumeration

---

## What is permanently deferred

**P8c — Satya phala layer:** `[concept, known, satya]` after each derivation.
Enables logical questions. Gated on P8f stable.

**P8d — Nyaya mantras:** logical inference, `nyaya-step.tantra`.

**P7 — Tokenise-question.tantra:** Replace OCaml char loop.

**Session graph (formal):** `build-session-graph`, `formalize-question`, `assert-samskaara`.

---

## What has changed

For baseline and session progress see [changelog.md](changelog.md).

| Date | What shifted in this doc |
|------|-------------|
| 2026-03-16 | Initial writing — xfail table, priority order, deferred items. |
| 2026-03-17 | P8f reprioritized to top. Dvandva before Gap 2. 08-boot.md added. |
| 2026-03-17 | `test_frequency` xfail removed (now passing). `test_gravitational_force` remains. Boot/reboot, sandhi Way 2, photon-energy, planck-constant, frequency fixes added to completed table. |
| 2026-03-18 | Dvandva entity-scoped computation done. xfail table updated 19→12. Stale priority note removed. |
