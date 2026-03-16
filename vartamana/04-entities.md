# 04 — Entities

**An entity is not just a grammatical subject. It is a simulation object.
The rashi structure that carries an entity's owned properties IS what the
renderer reads to draw it. Getting entities right IS getting pratibimba started.**

---

## What an entity is in the graph

An entity is a node that simultaneously plays three roles:

1. **Kartaa** — the nominative subject of the scene (`prathama-vibhakti`)
2. **Kshetre** — the owner of properties (`shashthi-vibhakti`)
3. **Rashi** — a quantity-bearing instance (`vishesa rashi`)

The full structure for one entity in the graph:

```
[gola-A, prathama-vibhakti, object]     ← gola-A IS in this scene — nominative
[gola-A, vishesa,           rashi]      ← gola-A IS a quantity instance
[mass,   shashthi-vibhakti, gola-A]     ← mass BELONGS TO gola-A
[mass,   sankhya,           5.]         ← mass value
[bindu,  shashthi-vibhakti, gola-A]     ← position BELONGS TO gola-A
[bindu,  sankhya,           (0,0,0)]    ← position value
[velocity, shashthi-vibhakti, gola-A]
[velocity, sankhya,           (1e6,0,0)]
```

This structure is not a description of a scene object sitting beside the graph.
It IS the object. The renderer walks `shashthi-vibhakti` edges to find what the
object owns, `sankhya` edges to get the values, and draws accordingly.
There is no separate scene data structure. The graph IS the simulation state.

This structure is already working for a single entity from a well-formed sentence.
`test_pipeline_entity_owns_mass` passes.

---

## Why entities are the gateway to pratibimba

`pratibimba/07-simulation.md` is explicit: the simulation object IS a rashi.
The electron, the sphere, the planet — each is an entity node with owned
properties. The renderer reads `shashthi-vibhakti` to find what the object owns.
`DrawSphere` at `bindu` with `dura` comes from walking these edges.

Without entities in the graph, there is nothing to render. The scene IS entities.

The session carries the entities forward across turns — the user describes the
electron in turn 1, the field in turn 2, asks for the simulation in turn 3.
Each turn deepens the same entity structure. The renderer reads whatever the
graph holds now and draws what it finds.

---

## What is done

- `prathama-vibhakti`, `shashthi-vibhakti`, `vishesa rashi` — all in the edge vocabulary
- Single entity from a well-formed sentence — working
- `vibhakti-shashthi.tantra` — correctly promotes `has` signal to entity + ownership
- `rashi-viveka`, `vishesa-bandhana`, `rashi-anuvada` — rashi instance pipeline done
- Session carries numeric values (`sankhya` triples) across turns via `session-anuvada`
- `test_pipeline_entity_owns_mass`, `test_avrti_entity_owns_property_via_has` — passing

---

## What is not done — in priority order

### Gap 1 — Unit label collision (partially closed)

Single-letter instance labels `m`, `v`, `q`, `t` are stolen by unit lookups:
`m` → metre, `v` → volt. These are exactly the labels a user naturally writes
for an electron simulation: mass `m`, velocity `v`, charge `q`, field `B`.

**What was fixed:** `emit-triples.tantra` now has a `is-rashi-label` guard.
A word fires the guard — and emits mithya (label) instead of satya — when:
1. An active satya concept precedes it
2. No pending number exists (rules out `5 m/s` unit position)
3. `word ≠ node` — the surface word differs from the node it resolves to

The third condition is what distinguishes abbreviations (`m` → metre, word≠node)
from concept words (`mass` → mass, word=node). Concept words always emit satya
regardless of context. Abbreviations that alias to a different node emit mithya
when an active concept is present.

**Result:** `test_instance_named_m_propagates_to_mass` and `test_ke_with_m_instance_name`
now xpass — mass gets its sankhya correctly when the instance is named `m`, and KE fires.

**Still failing:** `test_instance_named_m_does_not_collide_with_metre` — this test
checks `[m, sankhya, 5.]` on the instance `m` itself. With the fix, `m` emits mithya
and sankhya propagates to `mass` via rashi-anuvada (correct), but is not stored on the
label `m` directly. The test expectation is wrong for the new behaviour — it should
check `[mass, sankhya, 5.]` instead. Stays xfail pending test update.

**Additionally fixed:**

`q`, `v`, `B` resolve to **null** in the word index — they were never unit abbreviations.
The real blocker was `vibhakti-shashthi`: it only detected entities from mithya words.
`electron` is a kosha concept → satya → `last-label` was never set → `has` was silently
discarded → no `[charge, shashthi-vibhakti, electron]` → `vishesa-instance` never fired.

Fix: `vibhakti-shashthi` now also sets `last-label` from satya words when no entity is
yet established. `electron has charge q of 1.6e-19` and `electron has velocity v of 1e6`
now produce correct vishesa instances. `q`, `v` xfail markers removed.

Scientific notation was also broken: `split-numeric` stopped at `e`, treating `e-19` as
a unit string. Fixed in `yantra_ops.ml` — `1.6e-19`, `1e6`, `9.109e-31` all parse correctly.

`vishesa-instance` extended with `can-promote` scan-state (= `has-rashi-bandha`): promotes
mithya labels in the bare `concept label of value` pattern (no `has`, no entity). Required
because outer tantra `let` bindings are NOT visible inside `scan ... when` guards —
they must be threaded through as scan state variables.

**What remains:**

- `test_field_instance_named_B` — `"magnetic field B of 0.1"`, `B` still mithya.
  `can-promote` is true but `vishesa-instance` still not promoting. Under investigation.
- `test_electron_natural_labels` — blocked on `B` resolution.
- `test_unit_in_rate_not_stolen` — `"velocity is 5 m/s"`, `m/s` has no word index entry.

**Files:**
- `brahman/yantra/sankhya/emit-triples.tantra` (is-rashi-label)
- `brahman/yantra/vibhakti/vibhakti-shashthi.tantra` (satya entity detection)
- `brahman/yantra/vishesa/vishesa-instance.tantra` (can-promote scan state)
- `vyakarana/lib/yantra_ops.ml` (split-numeric scientific notation)

---

### Gap 2 — Session does not carry entity structure

`session-anuvada` currently carries `[concept, sankhya, val]` triples across
turns — numeric values only. It does not carry:
- `[entity, prathama-vibhakti, object]` — the entity's scene identity
- `[property, shashthi-vibhakti, entity]` — ownership edges

This means turn 2 does not know that `electron-A` from turn 1 exists as an
entity, only that `mass = 9.109e-31` exists as a floating value. The entity
identity and its ownership structure are lost between turns.

**What is needed:** `session-anuvada` must carry structural triples — not just
sankhya values but the full entity context: who owns what, what is an entity.
This is the difference between the session knowing "mass is 9.109e-31" and
knowing "electron-A is an entity that has mass 9.109e-31".

The current path (as noted in `pratibimba/07-simulation.md`): describe one
entity per turn. Turn 1 establishes the entity structure, turn 2 refines it.
This works with the current session — each turn's entity is established fresh.
Cross-entity reference across turns requires Gap 2 to be closed.

**After Gap 1:** Fix `session-anuvada` to also carry `prathama-vibhakti` and
`shashthi-vibhakti` triples from `refined` (post-avrti) into the session store,
and inject them alongside sankhya triples in the next turn's `prior-graph`.

---

### Gap 3 — Multi-entity scenes

Multi-entity scenes are NOT primarily a one-sentence problem. They are a session
problem. Each turn can introduce a new entity:

```
Turn 1: "electron, mass 9.109e-31, charge 1.6e-19, velocity 1e6"
         → gola-A entity established with mass, charge, velocity
Turn 2: "magnetic field B of 0.1T along z"
         → field-B entity established with strength, direction
Turn 3: "proton, mass 1.67e-27, charge 1.6e-19"
         → proton-C entity established
Turn 4: "run lorentz simulation"
         → all three entities present in graph, simulation fires on each
```

By turn 4, the graph has three objects simultaneously. The scene grows one entity
per turn. This is the primary multi-entity path — session accumulation, not
one-sentence parsing.

**Dvandva** (two entities in one sentence) is a convenience on top of this —
"electron and proton both in field B" — that allows what session turns already
enable. It is Phase 4, not the primary path.

The session carrying entity structure (Gap 2) IS what makes the multi-entity
scene possible. Without it, each new turn replaces the prior entity instead of
accumulating alongside it. The scene cannot grow.

This requires:
1. Gap 2 closed — session carries entity structure across turns
2. `session-anuvada` merges new entities into the accumulated scene
3. Mantras fire per-entity: derive-step walks each `prathama-vibhakti` node,
   scopes its `shashthi-vibhakti` properties, computes per-entity phala

---

## The sandhi-bandhana constraint

Prior-graph (entity structure from prior turns) must be injected **after**
`avrti-refine`, before `kosha-expand`. This is non-negotiable.

`sandhi-bandhana` (inside avrti-refine) rewrites `[concept, sankhya, val]`
subjects based on rename markers for the current sentence. If a prior-turn
entity triple enters before avrti-refine, sandhi-bandhana will corrupt it —
the entity's concept may not appear in the current sentence and will be wiped.

When Gap 2 is implemented (session carries structural triples), the injection
point must remain after avrti-refine. Entity triples from prior turns travel
in `prior-graph` and are appended to `refined` in `session-anuvada.tantra`
exactly where sankhya triples are currently appended.

---

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-16 | Initial writing — entities as pipeline gaps |
| 2026-03-16 | Rewritten. Entity = simulation object. Gap ordering revised: Gap 1 (unit collision) → Gap 2 (session entity structure) → Gap 3 (dvandva). Sandhi-bandhana constraint documented. Connection to pratibimba explicit. |
| 2026-03-16 | Gap 3 reframed: multi-entity is primarily a session accumulation problem, not a one-sentence problem. Each turn adds entities. Dvandva is Phase 4 convenience on top. |
| 2026-03-16 | Gap 1 partially closed. emit-triples `is-rashi-label` guard: word≠node discriminant. `m`-as-mass-instance and KE-with-m-instance now work (2 xfails → xpass). One xfail remains (test checks wrong node for sankhya). |
| 2026-03-16 | Gap 1 further closed. Root cause for q/v: vibhakti-shashthi missed satya-named entities (electron → satya, not mithya). Fixed. Scientific notation fixed in split-numeric. can-promote scan-state pattern discovered. q, v xfails removed. B, electron_natural_labels, unit_in_rate still pending. |
