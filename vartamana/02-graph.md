# 02 — The Graph

**The proof graph is a typed directed multigraph where every edge has a relation type,
and walking those edges IS understanding.**

---

## Structure IS meaning

The meaning of `mass` is not held in weights or embeddings. It IS the edges:

```
mass → matra    → kilogram
mass → abheda   → inertia
mass → siddha   → newton-second-law
mass → vishesa  → linear-force-varga
```

Walk these and you have understood `mass`. There is no hidden representation.
Structure = meaning. This is what artha-viveka does — it converts the semantic
content of a word into a structural position in the proof graph.

---

## The two layers every word enters

Every word that arrives lands in one of two layers:

**Satya** — resolved, confirmed. The triple is reflexive: subject = object = kosha node.

```
[mass,     satya,             mass]       ← reflexive: walk "mass" → kosha structure
[mass,     sankhya,           5.0]        ← numeric value
[mass,     matra,             kilogram]   ← measurement unit
[mass,     shashthi-vibhakti, ball]       ← mass OF ball — ownership
[ball,     prathama-vibhakti, object]     ← ball IS an entity — nominative
[find,     vidhi-kaala,       solve-for]  ← intent: what we are solving for
```

**Mithya** — provisional, unresolved. Held, not discarded.

```
[ball,   mithya, ball]    ← entity present, not yet fully typed
[speed,  mithya, speed]   ← synonym not yet mapped to velocity
[its,    mithya, its]     ← pronoun not yet resolved
```

Mithya is not failure. It is avidya — not-yet-known. The avrti passes apply
context pressure to collapse mithya into satya. What remains mithya after
fixpoint is genuine asprista — a word with no grounding even in full domain context.

---

## The edge vocabulary (visheshanam ring)

The proof graph is already a 10-dimensional typed directed multigraph. These are
the relation types and what they mean structurally:

| Edge type | Meaning | Direction |
|---|---|---|
| `satya` | IS (reflexive, resolved) | self → self |
| `mithya` | provisional, unresolved | self → self |
| `swarupa` | IS-A identity | open |
| `vishesa` | particular of a universal | particular → universal |
| `amsha` | member of a closed partition | member → whole |
| `abheda` | equivalence / non-difference | symmetric |
| `janya` | input / generator | concept → mantra |
| `phala` | output / result | mantra → concept |
| `krama` | operation sequence | ordered |
| `kriya` | action / callable | mantra → expression |
| `sthita` | condition / domain membership | node → domain |
| `pratipaksha` | inverse / opposite | op → inverse-op |
| `sankhya` | numeric value | concept → number |
| `matra` | unit of measurement | concept → unit |
| `shashthi-vibhakti` | genitive — X OF Y | property → owner |
| `prathama-vibhakti` | nominative — X IS the subject | entity → role |
| `vidhi-kaala` | imperative / intent | word → role |
| `kramanusara` | rate of change (general derivative) | quantity → denominator |
| `bhuta-kaala` | past tense | word → role |

Walking any node through these edges IS reasoning about that node.

---

## Sangati — the atomic vocabulary

The sangati layer (~50 nodes) are the primitive concepts from which everything else
is built. They are not defined in terms of other graph nodes — they ARE the atoms.

The living chain:
```
kaala → spanda → avrti → parampara → samskaara
jiva  = prana + life + eka-kosha + swa
swa   = runtime + function + eka-kosha + jiva + brahma + tat-kshana
```

The knowledge chain:
```
viveka  → eka-aneka → phala: eka
shuddhi → samskaara
nyaya   → shuddhi
pramana → lekhana → samskaara       [satya=0.945 — highest non-physical node]
pratijnaa → lekhana → visarjana     [assertion]
```

These are not metadata about the graph. They ARE the graph's ground.

---

## Rashi — the quantity instance

A rashi is a specific quantity in a specific scene. Not the concept `mass` — but
`mass of ball-A with value 5 kg`. The rashi layer sits between the word and the
concept.

```
[v1, vishesa,           velocity]    ← v1 IS-A velocity (particular of concept)
[v1, vishesa,           rashi]       ← v1 IS-A rashi (quantity instance)
[v1, sankhya,           20.]         ← v1 has value 20
[v1, matra,             metre-per-second]
[v1, shashthi-vibhakti, ball-A]      ← v1 BELONGS TO ball-A
```

The rashi layer was built in P8b.5. `rashi-anuvada.tantra` bridges rashi instances
to the concept level so mantras can fire: `[velocity, sankhya, 20.]` is asserted
from the instance, making `velocity-mantra` findable via match-mantra.

---

## Rashi labels and unit abbreviations — the disambiguation rule

A word is a rashi instance label when all three hold:

1. There is an active satya concept preceding it (`active` is set in `find-context`)
2. There is no pending number (`pending` is empty — the label is not in `5 m/s` position)
3. The word text differs from the node it resolves to (`word ≠ node`)

The third condition is the critical one. `m` resolves to `metre` — word ≠ node, so `m`
is a label. `mass` resolves to `mass` — word = node, so `mass` is a concept and emits
satya regardless of context.

```
"mass m of 5"        active=mass, pending='',  m→metre,    word≠node → mithya (label)
"velocity is 5 m/s"  active=velocity, pending=5., m→metre → unit binding fires instead
"mass 5 velocity 10" processing "velocity": active=mass, pending='', velocity→velocity, word=node → satya (concept)
"charge q of 1.6"    active=charge, pending='', q→null,    word≠node → mithya (already)
```

This rule lives in `emit-triples.tantra` as `is-rashi-label`. The `word ≠ node` guard
is what prevents ordinary concept words like `mass`, `velocity`, `energy` from being
misclassified as labels when they follow another concept.

Note: `q`, `v`, `B` resolve to **null** in the word index — they are not unit
abbreviations at all. They were always going through the `otherwise → mithya` branch.
The real blocker for them was `vibhakti-shashthi` not detecting satya-named entities.

---

## Satya-named entities and vibhakti-shashthi

`vibhakti-shashthi` detects entities by tracking mithya words before a `has` signal.
`ball` → mithya → `last-label = "ball"` → `has` fires → entity confirmed.

But `electron` → satya (it IS a kosha node). Satya words did not set `last-label`,
so `has` fired with no pending label and was silently discarded. The ownership chain
`[charge, shashthi-vibhakti, electron]` was never created. `vishesa-instance` never
promoted `q` or `v` because `charge` and `velocity` were not in `owned-concepts`.

**Fix:** `vibhakti-shashthi` now also sets `last-label` when a satya word is seen
before any entity is established (`cur-entity = ""`). This handles:
- `"electron has charge q of 1.6e-19"` — electron is a kosha concept, acts as entity
- `"magnetic-field B of 0.1"` — no `has`, different structure (see below)

---

## The `concept label of value` pattern without entity ownership

`"magnetic field B of 0.1"` has no `has` signal and no explicit entity. `B` follows
`magnetic-field` satya directly, then `of` rashi-bandha, then the value.

This is the bare rashi-label pattern: `concept label of value`. It cannot go through
`vibhakti-shashthi` (no `has`). `vishesa-instance` handles it via `can-promote`:
a scan state variable initialized to `has-rashi-bandha` (whether any `rashi-bandha`
triple exists in the graph). When true, any mithya word after a satya concept (not
bound, not an entity name) is promoted to a vishesa instance.

**Key discovery:** outer tantra `let` bindings (like `has-rashi-bandha`) are NOT
visible inside `scan ... when` guards. They must be passed as scan state variables
(`let can-promote be has-rashi-bandha`) to be accessible in the scan body.

---

## Scientific notation in split-numeric

`split-numeric` is an OCaml primitive in `yantra_ops.ml`. It was treating `e` as a
unit suffix: `"1.6e-19"` → `["1.6", "e-19"]`. Fixed to consume standard scientific
notation exponents (`e`/`E` + optional sign + digits) as part of the numeric prefix.
`"1.6e-19"` now → `["1.6e-19", ""]`, `"1e6"` → `["1000000.", ""]`.

---

## Mantra — the formula as graph structure

A mantra is a formula declared as graph structure. Not as code. Not as a string.
The edges ARE the formula.

```
kinetic-energy-mantra:
  janya   → mass, velocity      ← inputs
  phala   → kinetic-energy      ← output
  krama   → expression subgraph ← how to compute
  sthita  → implication         ← this IS a logical implication
```

Every physics mantra has `sthita: implication` — it IS a logical implication.
The physics/logic split is surface only. The graph unifies them.

A mantra fires when all its `janya` nodes have `sankhya` values in the current
question graph. Forward: compute phala from janya values. Inverse: given phala
and all-but-one janya, solve for the missing janya via `pratipaksha` edges on
each operation node.

---

## The kosha — the permanent knowledge store

The kosha holds the permanent structure: all physics concepts, their units, their
mantras, their inheritance chains. It does not change during a session.

The question graph is temporary — built fresh from each question, refined during
the session. The kosha is the ground the question graph is measured against.

`kosha-expand` runs PPR (personalized pagerank) over the kosha using the question
graph's satya nodes as seeds. It surfaces the mantras and related concepts that
are most relevant to this question's domain. Not a search — a guided surfacing
of what is already structurally connected.

---

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-16 | Initial writing — synthesized from nyaya-plan.md, session-graph.md, scene-understanding.md |
| 2026-03-16 | Rashi label disambiguation rule added. `word ≠ node` discriminant discovered: concept words (word=node) always emit satya; abbreviations/aliases (word≠node) emit mithya when active concept is present and no pending number. |
| 2026-03-16 | Satya-named entity detection added to vibhakti-shashthi. Scientific notation fixed in split-numeric. `can-promote` scan-state pattern documented: outer let bindings not visible in scan when guards — must pass via scan state. |
