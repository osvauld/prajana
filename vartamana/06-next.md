# 06 — What Is Next

**Baseline: 360 passed / 16 xfailed / 0 failing.** (q, v xfail markers removed)
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

---

## The 16 xfails — where they come from

| Group | test | Notes |
|---|---|---|
| Gap 1 — B label | `test_field_instance_named_B` | B still mithya — `can-promote` fires but vishesa-instance not promoting |
| Gap 1 — full electron | `test_electron_natural_labels` | blocked on B |
| Gap 1 — unit rate | `test_unit_in_rate_not_stolen` | `m/s` not in word index |
| Gap 2 — entity identity | `test_session_entity_identity_persists` |
| Gap 2 — multi-entity | `test_two_entities_across_turns_both_present` |
| Gap 2 — multi-entity | `test_two_entities_across_turns_scoped` |
| Gap 2 — multi-entity | `test_electron_and_field_across_turns` |
| Gap 2 — multi-entity | `test_three_entities_accumulate` |
| Pratibimba — sphere | `test_sphere_shape_swarupa` |
| Pratibimba — position | `test_position_ownership` |
| Pratibimba — simulation | `test_electron_simulation_scene_full` |
| Dvandva | `test_avrti_dvandva_collection_of_two_values` |
| Dvandva | `test_tier2_two_entities_ke_each` |
| Dvandva | `test_two_entity_rashi_feeds_mantra` |
| P8f — constants | `test_frequency` |
| P8f — constants | `test_gravitational_force` |

---

## Priority order

### 1. Gap 1 — Unit label collision (partially closed — 6 xfails remain)

**What:** Single-letter instance labels `m`, `v`, `q`, `B` are stolen by unit lookups.
`m` → metre, `v` → volt. These are exactly the labels a user writes for physics —
mass `m`, velocity `v`, charge `q`, field `B`. Without this, the natural language
path to the electron simulation is broken.

**What is fixed so far:**

- `emit-triples.tantra` `is-rashi-label`: `word ≠ node` — `m → metre` treated as label
- `vibhakti-shashthi.tantra`: satya-named entities (`electron has ...`) now detected
- `vishesa-instance.tantra`: bare `concept label of value` (no `has`) promoted via `can-promote` scan state
- `yantra_ops.ml` `split-numeric`: scientific notation (`1.6e-19`, `1e6`) now parsed correctly
- Test cleanup: m-instance, q, v xfail markers all removed

**Key insight discovered:** outer tantra `let` bindings are not visible inside `scan ... when`
guards. Must pass computed values as scan state: `let flag be computed-value`.

**What remains (3 xfails):**

- `test_field_instance_named_B`: `"magnetic field B of 0.1"` — `B` still mithya.
  `can-promote = true` confirmed, but `vishesa-instance` not promoting. Root cause unknown.
- `test_electron_natural_labels`: blocked on B.
- `test_unit_in_rate_not_stolen`: `"velocity is 5 m/s"` — `m/s` is a compound unit string
  with no word index entry. Needs either a composite unit parser or `m/s → metre-per-second` mapping.

**Files:** emit-triples, vibhakti-shashthi, vishesa-instance, yantra_ops.ml

---

### 2. Gap 2 — Session entity structure (unblocks multi-entity scenes)

**What:** `session-anuvada` currently carries `[concept, sankhya, val]` triples
across turns. It must also carry:
- `[entity, prathama-vibhakti, object]` — entity identity
- `[property, shashthi-vibhakti, entity]` — ownership edges
- `[entity, vishesa, rashi]` — rashi type

Each turn can introduce a NEW entity. By turn 3, the scene has three objects.
The session must accumulate them — not replace them.

**Why second:** This is the primary multi-entity path. Dvandva (one sentence) is
a convenience on top of this. Without session entity structure, the scene cannot
grow across turns — pratibimba cannot accumulate a scene.

**The change:** `session-anuvada.tantra` currently calls `remember-bindings` for
sankhya only. It must also store structural triples from `refined` into
`se_graph` in the session entry. The socket reads `se_graph` on next turn
and injects alongside `prior-graph` sankhya triples — after avrti-refine.

**Sandhi-bandhana constraint applies:** Entity triples must be injected after
`avrti-refine` exactly as sankhya triples are — not before.

---

### 3. Dvandva — two entities in one sentence (Phase 4, after Gap 2)

**What:** `"electron and proton both in field B"` — two entities in one sentence
rather than across two turns. Convenience on top of session accumulation.

**Why after Gap 2:** Session accumulation IS the multi-entity architecture.
Dvandva is the optimisation. One entity per turn already works once Gap 2 is done.

**Architecture:** A tantra that walks `prathama-vibhakti` nodes, scopes
`shashthi-vibhakti` per entity, fires match-mantra within each scope.

**Tests:** `test_tier2_two_entities_ke_each`, `test_two_entity_rashi_feeds_mantra`,
`test_avrti_dvandva_collection_of_two_values`

---

## What is permanently deferred (P8f)

`frequency-mantra`, `gravitational-force-mantra` — constants (`1`, `pi`, `G`)
not representable in the current flat krama step list.
Fixed by the expression subgraph architecture (P8f).

---

## What comes after the gaps

**Pratibimba blockers** (unblocked by Gap 1 + Gap 2):
- `sphere` → `gola` word index entry — 1 kosha change
- Spatial position binding (`bindu` as owned vector value)
- Orbital radius mantra (`lorentz-force.om`, `r = mv/qB`)
- EpochOutput generation from graph entity enumeration

**P8c — Satya phala layer:** `[concept, known, satya]` after each derivation.
Enables logical questions. Gated on Gap 1 + Gap 2 being stable.

**P8d — Nyaya mantras:** `nyaya-step.tantra`, logical inference, fixpoint after derive-step.

**P8e — Inversion:** `invert-expr.tantra`. Generic inverter via `pratipaksha` walk.
"Find mass given KE and velocity." Currently only forward computation supported.

**P8f — Expression subgraph:** Replace flat krama with `kriya` edge → expression
subgraph root. Fixes constants. No more arg-order issues.

**P7 — Tokenise-question.tantra:** Replace OCaml char loop with graph-native tantra.
Prerequisite for P8 composition pipeline.

**Session graph (formal):** `build-session-graph.tantra`, `formalize-question.tantra`,
`assert-samskaara.tantra` — full logical session as proof document. Gated on P7+P8.

---

## What the session plan got wrong

The plan said Gap 5 was "one OCaml change — pass `se_graph` into `anuvada_query`."

What was actually needed was an architectural understanding:
the session IS the outer avrti of anuvada-ganana. This led to `session-anuvada.tantra`
as the correct structure — not a wiring fix, but a new scale of the same spiral.

The other thing the plan missed: `sandhi-bandhana` corrupts prior-turn triples
when they are injected before `avrti-refine`. Prior-graph must be injected **after**
`avrti-refine`, before `kosha-expand`. This is a constraint that the architecture
must preserve going forward — any session graph expansion must respect it.

---

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-16 | Initial writing — synthesized from nyaya-plan.md xfail table, test analysis |
| 2026-03-16 | Updated: Gaps 3/4/5 done. Baseline 346/8. sandhi-bandhana constraint documented. Priority reordered. |
| 2026-03-16 | Baseline 355/21. test_entity_scene.py written — Gap 1 (8 xfails), Gap 2 (5 xfails), pratibimba render params (3 xfails). Structural disambiguation rule defined: word between satya-concept and rashi-bandha is always a rashi label. |
| 2026-03-16 | Gap 1 partially closed. emit-triples `word≠node` discriminant. 2 xfails → xpass. Baseline 355/19xfail/2xpass. Immediate cleanup: remove xfail markers from 2 xpassed tests; update `test_instance_named_m_does_not_collide_with_metre` assertion. |
| 2026-03-16 | Gap 1 further closed. vibhakti-shashthi: satya-named entities. vishesa-instance: can-promote scan state. split-numeric: scientific notation. q, v now passing. Baseline 360/16xfail. B and unit-rate still open. |
