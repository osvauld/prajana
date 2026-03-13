# Scene Understanding — End-to-End Pipeline

**Status**: Active design. Canonical reference for the full pipeline.
**Incorporates**: graph-inference.md (merged here, that file deleted)
**Last updated**: 2026-03-13 (S1.5 done — reflexive satya, baseline 124/11)

---

## What Scene Understanding Is

Scene understanding is the full pipeline from natural language input to a computed,
reasoned response. It is NOT a separate system — it is what the full NLP stack enables:

```
English dhvani
  ↓  artha-viveka
build-question-graph    — word-by-word stateful reduce → flat triple graph
                          words land as [node, satya, node] or [word, mithya, word]
  ↓
fixpoint:
  avrti-refine          — structural passes: mithya → satya (compound, avastha, ownership...)
  kosha-expand          — for each satya node: PPR over kosha → pull in relevant structure
                          domain boundary: upward freely, downward only into owned domains
                          lateral cross-domain connections: blocked
  avrti-refine          — contextual mithya resolution using expanded domain context
  → repeat until fixpoint (sphoTa: no resolvable mithya remains)
  ↓
match-mantra            — READ the mantra already surfaced by PPR expansion (not a search)
  ↓
execute-chain           — krama stack machine → computed result
  ↓
compose-trace           — reads every graph phase → reasoning trace
  ↓
anuvada                 — result artha → fresh English dhvani
```

The pipeline is not a transformation sequence. Each step reads the **graph state** from
the previous step. The graph accumulates — nothing is discarded. The mithya layer is
always present alongside the satya layer. The compose-trace step reads all of it.

**Semantic → Structural.** Artha-viveka does not merely label words — it converts their
semantic content into structural position in the proof graph. The meaning of `mass` IS
its edges: `kilogram-matra`, `inertia-abheda`, `newton-second-law-siddha`. There is no
hidden representation. Walking the structure IS understanding.

---

## The Two Layers: Mithya and Satya

Every word in the input lands in one of two layers:

**Satya** — resolved, confirmed. The node IS the kosha node — the triple is reflexive.
```
[mass,     satya,              mass]      ← reflexive: subject = object = kosha node
[mass,     sankhya,            5.0]       ← numeric value
[mass,     matra,              kilogram]  ← measurement unit
[find,     vidhi-kaala,        solve-for] ← imperative intent
[mass,     shashthi-vibhakti,  ball]      ← mass of ball (genitive ownership)
[ball,     prathama-vibhakti,  object]    ← ball is the nominative subject/entity
```

The satya triple `[mass, satya, mass]` is reflexive — the subject and object are the same
kosha node. This makes the full kosha structure of `mass` walkable from the question graph:
`walk "mass" "satya"` → `mass` → `walk "mass" "newton-second-law-siddha"` → the mantra.

**Mithya** — provisional, unresolved. Held, not discarded. Available for reasoning.
```
[ball,     mithya,  ball]       ← physical entity, not yet typed
[moving,   mithya,  moving]     ← verb, no role yet
[its,      mithya,  its]        ← pronoun, not yet resolved
[speed,    mithya,  speed]      ← synonym not yet mapped to velocity
```

Mithya is not failure. It is **avidya** — not-yet-known. The avrti passes apply
context pressure to collapse mithya into satya. With kosha expansion, this context
pressure includes domain-scoped PPR: resolved concepts surface their domain, and
mithya words are looked up within that domain. `"speed"` in a mechanics context →
`velocity`. What remains mithya after fixpoint is genuine `asprista` — not a lookup
failure, but a word with no grounding even in full domain context.

Context accumulates across the entire input. A ball's mass from sentence one is valid
when computing kinetic energy in sentence two. Context does NOT reset at commas or
full stops. Punctuation carries structural meaning, not context boundaries.

---

## The Sentence IS the Graph

### Core principle

The sentence does not get "parsed into" a graph. The sentence **is** a graph. Every
word produces triples. Those triples ARE nodes and edges. Relationships between words
— ownership, reference, grouping — are just more edges in the same graph.

There is no separate "group annotation layer" or "scope control mechanism". Group
membership is an edge. Entity ownership is an edge. Cross-sentence references are edges.
The graph IS the structure.

### What this means for implementation

- **No positional scope propagation.** Entity ownership does not "propagate by position"
  — it is established by explicit signals in the sentence (has, with, of, its, their).
- **No group partitioning pass.** Groups are not segments of the triple list. They are
  subgraphs connected by ownership/reference edges.
- **No scope reset rules.** We don't need "reset entity scope at intent" or "reset at
  period" — we just need to correctly identify each relationship signal.

### Punctuation as structural triples

BQG strips trailing sentence punctuation from words for lookup, but emits the
punctuation as a structural triple:

```
"ball."     → lookup "ball" → [ball, mithya, ball] + [., punct, .]
"velocity?" → lookup "velocity" → [velocity, active, concept] + [?, punct, ?]
"10,"       → split-numeric handles → [10, pending-number, 10.] (comma in unit field)
```

The comma is already handled by split-numeric for numbers. Period and question mark
are stripped at word level but preserved as `[punct]` triples. These are boundary
markers available for avrti to read — they are NOT discarded.

---

## Signal-Based Ownership

### The key insight

Every ownership relationship in the graph must come from an **explicit signal** in
the sentence. Positional propagation ("everything after this entity is owned by it")
is wrong — it causes over-attribution across sentence boundaries.

### Ownership signals

| Signal word | Role | Edge it produces | Example |
|---|---|---|---|
| `has` | `role:possession` | `[concept, shashthi-vibhakti, entity]` | "ball **has** mass 5 kg" |
| `with` | `role:possession` | `[concept, shashthi-vibhakti, entity]` | "block **with** mass 5 kg" |
| `of` | `role:possession` | `[concept, shashthi-vibhakti, entity]` | "momentum **of** the ball" |
| `have` | `role:possession` | `[concept, shashthi-vibhakti, entity]` | "objects **have** mass" |
| `its` | `role:pronoun` | `[pronoun, naama-pratibodha, entity]` | "find **its** energy" |
| `their` | `role:pronoun` | `[pronoun, naama-pratibodha, [entities]]` | "find **their** momentum" |
| `the` + entity | back-reference | not a new entity | "energy of **the ball**" |

### How "and" works — dvandva at two levels

`"and"` is the dvandva operator, but its meaning depends on what it joins:

**Property-level dvandva** (same owner):
```
"ball has mass 5 kg and velocity 10 m/s"
  → [ball, prathama-vibhakti, object]
  → [mass,     shashthi-vibhakti, ball]  ← from "has"
  → [velocity, shashthi-vibhakti, ball]  ← from dvandva: "and" distributes under same "has"
```
The `has` distributes over the `and`. Both mass and velocity are owned by ball.
Detection: `and` followed by concept → same entity's property.

**Entity-level dvandva** (different owners):
```
"ball A has mass 3 kg and ball B has mass 7 kg"
  → [ball-A, prathama-vibhakti, object] + [mass, shashthi-vibhakti, ball-A]  ← first "has"
  → [ball-B, prathama-vibhakti, object] + [mass, shashthi-vibhakti, ball-B]  ← second "has"
```
Each `has` establishes its own entity. `and` separates two entity groups.
Detection: `and` followed by mithya + possession-signal → new entity.

### How "of" works — reverse possession

`"of"` signals ownership in the reverse direction from `has`:
```
"find the kinetic energy of the ball"
  → kinetic-energy is the solve-for concept
  → "of the ball" → kinetic-energy belongs to ball
  → [kinetic-energy, shashthi-vibhakti, ball]  ← from "of" + back-reference
```

`"the ball"` after `"of"` is a back-reference to a previously defined entity,
not a new entity. The definite article `the` signals this.

### How pronouns work — cross-group references

Pronouns connect different parts of the sentence (or different sentences) by
referencing a previously established entity:

```
"a ball has mass 5 kg. find its kinetic energy."

  group 0: [ball, prathama-vibhakti, object]
           [mass, shashthi-vibhakti, ball]
           [mass, sankhya, 5.0]
  group 1: [find, vidhi-kaala, solve-for]
           [kinetic-energy, satya, kinetic-energy]
                  ↑
            [its, naama-pratibodha, ball]           ← cross-group reference
            [kinetic-energy, shashthi-vibhakti, ball] ← derived from "its"
```

`"its"` = singular, refers to last entity. `"their"` = plural, refers to last
entity set. The reference is an explicit edge, not scope propagation.

### What a word belongs to

A word can participate in multiple relationships:
- **Defined** in one context: `[ball, entity, object]` from "ball has mass"
- **Referenced** from another: `"of the ball"` or `"its"` from a later clause
- **Grouped** with peers: `[ball-A, ball-B]` in a dvandva set

The entity is not "in scope" — it is **reachable** through edges. Anything that
can reach the entity through ownership, reference, or group edges can use it.

---

## The Output: Reasoning Trace

The output is not just an answer. It is a full account of how the system reasoned.
Each section maps to a phase of the pipeline graph.

```
Proposition:
  "Find kinetic energy given mass=5kg, velocity=10m/s"
  [The question restated as a logical claim to evaluate]

Understanding:
  "kinetic energy" ← compound resolved from "kinetic"(mithya) + "energy"(active)
  mass = 5 kg      ← directly bound
  velocity = 10 m  ← directly bound
  solve-for = kinetic-energy ← from intent triple [find, intent, solve-for]
  [What each word became in the graph — the avrti rename map made visible]

Reasoning:
  mass ∧ velocity are known (satya layer)
  kinetic-energy-mantra requires: mass, velocity — fully covered ✓
  momentum-mantra also requires mass, velocity — excluded: solve-for=kinetic-energy,
    momentum-mantra name=momentum ✗
  Implication: (mass ∧ velocity ∧ solve-for=kinetic-energy) → kinetic-energy-mantra
  [The inference walk made visible — why this theorem and not another]

Theorem:
  kinetic-energy-mantra: KE = ½ × mass × velocity²
  (established formula — niyama-siddha)
  [The mantra node's krama chain read as a formula]

Proof:
  step 1: velocity² = 10² = 100    [square-krama]
  step 2: mass × 100 = 5 × 100 = 500  [multiplication-krama]
  step 3: ½ × 500 = 250            [half-krama]
  [The execute-chain intermediate values — krama-yukta ordered steps]

Conclusion:
  kinetic energy = 250 joules
  [krama-lhs name + result + krama-lhs-unit]

Assumptions (remaining mithya):
  "ball" — treated as unnamed physical object, did not affect computation
  "a"    — article, ignored
  [What stayed mithya and whether it mattered — the refinement signal]
```

### Mithya as Refinement Signal

The assumptions section is the most important part of the output for refinement.
It tells the user:

- What the system silently assumed
- Whether those assumptions affected the result
- What to clarify to change the answer

Examples:
- `[height, mithya]` when potential energy asked → "I couldn't resolve 'height' —
  do you mean elevation above a reference point? I need this to compute potential energy."
- `[ball, mithya]` when ball is the only entity → "I treated 'ball' as an unnamed object.
  Its material/type doesn't affect this kinetic energy computation."
- `[moving, mithya]` → "I ignored 'moving' — it didn't change any binding."
- `[its, mithya]` after entity resolution fails → "I couldn't resolve 'its' — did you
  mean the ball's kinetic energy?"

### The compose-trace Tantra

`compose-trace.tantra` reads the graph at each phase:

| Input | What it reads | Output section |
|---|---|---|
| question graph | intent triples + active concept triples | Proposition |
| avrti rename map | `[[base, compound], ...]` | Understanding |
| avrti graph | value/unit triples | Understanding |
| match-mantra reasoning | candidates considered, why rejected | Reasoning |
| mantra node shabda | name:, krama-rhs:, krama chain | Theorem |
| execute-chain trace | intermediate values at each krama step | Proof |
| mantra shabda | krama-lhs:, krama-lhs-unit:, result | Conclusion |
| remaining mithya triples | what stayed mithya after all passes | Assumptions |

No templates. The graph structure drives the narrative order. The same tantra works
for any question because the graph always has the same layer structure.

---

## The Comma and Structural Signals

### What the comma actually is

The comma is not punctuation noise to be stripped. It is a **dvandva operator** —
a copulative joiner that marks co-equal membership in a structural role.

`split-numeric "10,"` → `[10., ","]` — the comma is already surfaced by the numeric
parser as the unit-suffix field. It is never lost. It just needs to be interpreted.

The interpretation depends on what is on both sides — determined during avrti, not BQG:

| Context | Comma role |
|---|---|
| `mass 5 kg, velocity 10 m/s` | joins two binding clauses as parallel givens |
| `find KE, given mass 5` | separates intent clause from premise clause |
| `m1, m2 and m3` | joins three instance labels as set members |
| `10, 14, 15 and 29` | joins four anonymous numbers as set members |
| `find force, given mass 10, acceleration 2` | clause separator + list joiner |

Context does NOT reset at commas. The graph accumulates.

---

## Dvandva Groups

A dvandva group is a set of co-equal items joined by `,` and/or `and`. In the graph:

```
[concept, dvandva, [elem0, elem1, elem2, ...]]
```

Grade = list index. Maps directly onto `graded-ring`: `grade-yukta direct-sum-swarupa`.

### Anonymous numeric group

Elements are bare values; type comes from the operation:
```
"find the sum of 10, 14, 15 and 29"
→ [sum, dvandva, [10., 14., 15., 29.]]
```
`of` is the argument attachment signal — binds the group to the preceding concept.

### Typed instance group

Elements are named labels; type comes from the adjacent bahu-vachana noun:
```
"v1, v2 and v3 velocities"
→ [velocity, dvandva, [v1, v2, v3]]
```
Tatpurusha typing: v1 is-a velocity, v2 is-a velocity, v3 is-a velocity.

### Graded ring structure

The `graded-ring` kosha node is the formal structure:
- **Grade** = position in the dvandva list
- **Addition** (⊕) = dvandva join (comma/and)
- **Multiplication** (⊗) = set-product (pairing across two groups)
- **Direct sum** = assembled results across all grades
- **Grade preservation** = what "respectively" enforces

The graded ring is already in the kosha. Avrti applies its properties as inference steps.
As the kosha grows, the inference engine grows with it — no new avrti rules needed.

---

## Entity Recognition

An entity is a **named physical object** that has properties. Distinct from a concept:
`mass` is a concept. `ball` is an entity. `ball A` is a named entity instance.

Entities start as mithya — `lookup-word "ball"` → `_none`. This is correct.
Avrti pressure types them from context.

### Entity signals — signal-based, not positional

Entity ownership is established ONLY through explicit signals, never through
positional scope propagation:

**Primary signals** (role:possession in the graph):
```
"ball has mass 5 kg"     → has: [ball, entity, object] + [mass, owner, ball]
"block with mass 5 kg"   → with: [block, entity, object] + [mass, owner, block]
"body of mass 10 kg"     → of: [body, entity, object] + [mass, owner, body]
```

**Continuation signal** (dvandva within same possession clause):
```
"ball has mass 5 kg and velocity 10 m/s"
  → "and" + concept following = property dvandva under same "has"
  → [velocity, owner, ball]  (derived from "has" distributing over "and")
```

**Cross-reference signals** (pronouns connecting groups):
```
"a ball has mass 5 kg. find its kinetic energy."
  → "its" → refers to "ball" → [kinetic-energy, owner, ball]
```

**Back-reference signal** (definite article + known entity):
```
"find the kinetic energy of the ball"
  → "the ball" refers to previously established ball entity
  → [kinetic-energy, owner, ball]  (from "of" + back-reference)
```

### Entity naming (R9 — tatpurusha compound)

```
"ball A has mass 5 kg"
  → [ball, mithya] + [A, mithya] → compound entity label: ball-A
  → [ball-A, entity, object]
```

Two consecutive mithya tokens before a possession signal → tatpurusha compound.
The qualifier (A) refines the label (ball).

### Multiple entities

```
"ball A has mass 5 kg and ball B has mass 10 kg"
→ [ball-A, entity, object] + [mass, owner, ball-A] + [mass, value, 5.]
→ [ball-B, entity, object] + [mass, owner, ball-B] + [mass, value, 10.]
```

Each `has` establishes its own entity. The `and` between them is entity-level
dvandva — different entities, not additional properties of the same entity.

### Pronoun resolution

```
[ball, entity] ... [its, mithya] ... [kinetic-energy, active]
→ [its, refers-to, ball]
→ [kinetic-energy, owner, ball]
```

`its` = singular, refers to last entity.
`their` = plural, refers to all entities in the current entity dvandva group.
`those` = demonstrative plural, refers to a previously named set.

---

## Logic-Driven Inference

### The key insight

Avrti passes do not need hardcoded rules for every sentence pattern. The **kosha
defines the inference rules**. Avrti reads those structures and applies them.

| Kosha node | What it defines | Inference application |
|---|---|---|
| `set` / `element` | membership in a collection | mithya sequence → dvandva group |
| `equivalence-relation` | reflexive, symmetric, transitive | "respectively" = grade bijection |
| `morphism` | structure-preserving map | grade-preserving zip of two groups |
| `set-product` | pairing across two sets | (m_n, v_n) → one mantra instance |
| `graded-ring` | grade-indexed direct sum | grade = position in dvandva list |
| `dvandva` (samasa) | copulative compound, co-equal | comma/and = dvandva operator |
| `quantifier` | for-all / there-exists | "all", "every", "some" → iteration |
| `conjunction` | logical AND | "and" = both items are givens |
| `inference` | kramanusara-yukta | each mithya→satya collapse is an inference step |
| `implication` | if A then B, directional | mass∧velocity → kinetic-energy-mantra fires |
| `theorem` | niyama-siddha | each mantra node is a theorem |
| `proof` | krama-yukta ordered chain | execute-chain IS the proof |
| `axiom` | niralamba, svayambhu | sangati truths — require no further justification |
| `undecidable` | no formula can match | surfaced in assumptions as "cannot compute" |

---

## Complex Sentence Analysis

### What works now (after R8 + punctuation fix)

Tested against real physics paragraph inputs. Current pipeline output:

**"a ball has mass 5 kg and velocity 10 m/s. find the kinetic energy of the ball."**
```
✓ [ball, entity, object]         — R8 fires on "has"
✓ [mass, owner, ball]            — ownership from "has"
✓ [mass, value, 5.] [mass, unit, kilogram]
✓ [velocity, owner, ball]        — ownership propagation across "and"
✓ [velocity, value, 10.] [velocity, unit, metre-per-second]  — punctuation stripped
✓ [kinetic-energy, active]       — compound "kinetic"+"energy" resolved
✗ [kinetic-energy, owner, ball]  — WRONG: positional propagation, not signal-based
✗ [kinetic-energy, symbol, ball] — WRONG: R4b false fire on reference-back "ball"
```

**"a train has initial velocity 20 m/s and final velocity 40 m/s."**
```
✓ [train, entity, object]
✓ [initial-velocity, active]    — compound "initial"+"velocity" (avastha)
✓ [initial-velocity, owner, train]
✓ [initial-velocity, value, 20.]
✓ [final-velocity, active]      — compound "final"+"velocity" (avastha)
✓ [final-velocity, owner, train]
✓ [final-velocity, value, 40.] [final-velocity, unit, metre-per-second]
✗ [mass, symbol, train]         — WRONG: R4b false fire on "the train" back-reference
```

**"why does a heavier object have more momentum than a lighter object at the same velocity?"**
```
✓ [object, active, concept]     — recognized
✓ [momentum, active, concept]   — recognized
✓ [velocity, active, concept]   — punctuation stripped from "velocity?"
✗ [have, mithya]                — not recognized as possession (needs grammar node)
✗ [heavier, mithya]             — comparative adjective, no role yet
✗ [lighter, mithya]             — comparative adjective, no role yet
```

### Remaining issues (require signal-based ownership rework)

| # | Issue | Root cause | Fix |
|---|---|---|---|
| 1 | Entity scope over-propagates past intent | Positional `cur-entity` | Signal-based: only `has/with/of/its` set ownership |
| 2 | R4b false symbols on back-reference words | R4b fires on ANY mithya after owned concept | Only fire when no possession/grammar signal present |
| 3 | `"is moving with"` → `moving` becomes entity | `with` triggers R8 after verb | Need verb detection: `is` + gerund → not entity |
| 4 | `"and"` doesn't break scope for new entity | Ownership propagates through `and` | `and` + mithya + possession → new entity; `and` + concept → same entity |
| 5 | `"of"` not a possession signal | No grammar node | Add `prep-of.om` with `role:possession` (careful: `of` already exists as `role:grammar`) |
| 6 | `"have"` not recognized | No grammar node | Add `verb-have.om` with `role:possession` |
| 7 | `"the" + entity` = back-reference | Not implemented | `the` + known entity name → reference edge, not new entity |
| 8 | `"total"` → `complete` wrong | Kosha word: key match | Investigate complete.om word: key |
| 9 | `"change in"` treated as concept | `change` has a kosha node | Needs modifier/operator classification |
| 10 | Self-reference: `[mass, symbol, train]` | R4b fires on entity name after its own concept | Guard: don't symbol-bind the entity's own name |

---

## Worked Examples

### Example 1: Simple forward computation

**Input**: `"what is kinetic energy given mass 5 kg and velocity 10 m"`

**BQG graph**:
```
[find,     intent,         solve-for]
[kinetic,  mithya,         kinetic]
[energy,   active,         concept]
[given,    grammar,        _]
[mass,     active,         concept]
[mass,     value,          5.]
[mass,     unit,           kilogram]
[velocity, active,         concept]
[velocity, value,          10.]
[velocity, unit,           metre]
```

**After avrti**:
```
[kinetic-energy, active,  concept]   ← compound: kinetic+energy
[mass,           value,   5.]
[mass,           unit,    kilogram]
[velocity,       value,   10.]
[velocity,       unit,    metre]
```

**Match**: kinetic-energy-mantra (solve-for=kinetic-energy, mass∧velocity covered)

**Execute**: ½ × 5 × 10² = 250

**Reasoning trace**:
```
Proposition:  Find kinetic energy given mass=5kg, velocity=10m
Understanding: "kinetic energy" resolved from "kinetic"+"energy" compound
               mass=5, unit=kilogram; velocity=10, unit=metre
Reasoning:    kinetic-energy-mantra selected: solve-for matches, krama-rhs covered
              momentum-mantra excluded: solve-for=kinetic-energy ≠ momentum
Theorem:      KE = ½ × mass × velocity²
Proof:        10²=100 → 5×100=500 → ½×500=250
Conclusion:   kinetic energy = 250 joules
Assumptions:  none (no unresolved mithya affected the computation)
```

---

### Example 2: Inverse computation

**Input**: `"mass when force is 20 and acceleration is 2"`

**Inference walk**: mass is in krama-rhs, not krama-lhs → pratipaksha direction
- `newton-second-law-motion` krama-rhs: mass, acceleration; krama-lhs: force
- force=20 is known (the krama-lhs output) → invert: mass = force / acceleration

**Execute**: 20 / 2 = 10

**Reasoning trace**:
```
Proposition:  Find mass given force=20, acceleration=2
Reasoning:    mass is an input to newton-second-law, not its output
              pratipaksha path: force=20 known as output → invert formula
              mass = force / acceleration
Theorem:      F = ma → (pratipaksha) → m = F/a
Proof:        20 / 2 = 10
Conclusion:   mass = 10 kilogram
```

---

### Example 3: Multi-step chaining

**Input**: `"kinetic energy when mass=10, initial-velocity=0, acceleration=2, time=3"`

**Inference walk**: kinetic-energy needs velocity — not directly known.
Chain: velocity-mantra(initial-velocity=0, acceleration=2, time=3) → velocity=6
Then: kinetic-energy-mantra(mass=10, velocity=6) → 180

**Reasoning trace**:
```
Proposition:  Find kinetic energy given mass=10, u=0, a=2, t=3
Reasoning:    kinetic-energy needs velocity — not given
              implication chain: (u ∧ a ∧ t) → velocity [velocity-mantra]
              then: (mass ∧ velocity) → kinetic-energy [kinetic-energy-mantra]
Lemma:        velocity = u + at = 0 + 2×3 = 6  [velocity-mantra, proof]
Theorem:      KE = ½mv²  [kinetic-energy-mantra]
Proof:        6²=36 → 10×36=360 → ½×360=180
Conclusion:   kinetic energy = 180 joules
```

---

### Example 4: Anonymous numeric group

**Input**: `"find the sum of 10, 14, 15 and 29"`

**BQG graph**:
```
[find, intent,         solve-for]
[sum,  mithya,         sum]      ← sum is mantra layer (known gap — needs kosha node)
[10,   pending-number, 10.]
[14,   pending-number, 14.]
[15,   pending-number, 15.]
[29,   pending-number, 29.]
```

**After avrti (R5 — anonymous numeric group)**:
```
[sum, active,  concept]
[sum, dvandva, [10., 14., 15., 29.]]
```

**Match**: sum-mantra, krama-rhs: dvandva-group → fold-add

**Reasoning trace**:
```
Proposition:  Find sum of 10, 14, 15, 29
Understanding: four numbers form a dvandva group under "sum"
               "of" signals argument attachment
Theorem:      sum = fold addition over group
Proof:        10+14=24 → 24+15=39 → 39+29=68
Conclusion:   sum = 68
```

---

### Example 5: Typed instance group with respectively

**Input**: `"find momentum of m1, m2 and m3 with v1, v2 and v3 velocities respectively"`

**After avrti**:
```
pass 1 (R6 — typed instance group):
  [mass,     dvandva, [m1, m2, m3]]   ← typed by momentum krama-rhs position
  [velocity, dvandva, [v1, v2, v3]]   ← typed by bahu-vachana "velocities"

pass 2 (R7 — respectively as morphism):
  [mass, morphism, velocity]
  [m1, paired-with, v1]
  [m2, paired-with, v2]
  [m3, paired-with, v3]

pass 3 (set-product instantiation):
  three momentum-mantra instantiations, one per grade
```

---

### Example 6: Multiple entities with signal-based ownership

**Input**: `"ball A has mass 5 kg and ball B has mass 10 kg. find their total momentum if both move with velocity 3 m/s."`

**After avrti (target — not yet implemented)**:
```
[ball-A, entity, object]           ← R9: "ball"+"A" compound
[mass, owner, ball-A]              ← R8: from first "has"
[mass, value, 5.]                  ← scoped to ball-A
[ball-B, entity, object]           ← R9: "ball"+"B" compound
[mass, owner, ball-B]              ← R8: from second "has"
[mass, value, 10.]                 ← scoped to ball-B
[their, refers-to, [ball-A, ball-B]]  ← R10: "their" = plural pronoun
[velocity, value, 3.]              ← shared (applies to both via "both")
[momentum, active, concept]        ← solve-for
[total, avastha, complete]         ← qualifier on solve-for
```

**Key**: ball-A's mass=5 and ball-B's mass=10 are SEPARATE bindings because each
`has` signal establishes ownership independently. "their" connects the query group
back to both entities. "both" confirms the plural reference.

---

## Grammar Nodes for Signals

### Implemented

| File | word: | role | Purpose |
|---|---|---|---|
| `verb-has.om` | `has` | `possession` | primary entity signal |
| `prep-with.om` | `with` | `possession` | alternative entity signal |

### Needed

| File | word: | role | Purpose |
|---|---|---|---|
| `verb-have.om` | `have` | `possession` | conjugated form of has |
| `prep-of.om` | needs `role:possession` added | `possession` | reverse ownership ("of the ball") |
| `pronoun-its.om` | `its` | `pronoun` | singular back-reference |
| `pronoun-their.om` | `their` | `pronoun` | plural back-reference |
| `pronoun-those.om` | `those` | `pronoun` | demonstrative back-reference |
| `adv-respectively.om` | `respectively` | `morphism` | grade-preserving zip |

**Note on `of`**: `prep-of.om` already exists with `role:grammar`. Need to change to
`role:possession` — but `of` has dual use ("square root of X" vs "mass of the ball").
May need context-dependent role resolution.

### Kosha nodes needed

| File | Purpose | Unblocks |
|---|---|---|
| `kosha/math/number/sum.om` | sum as concept, not just mantra | anonymous numeric group |

---

## Avrti Rules — Current + Planned

### Implemented

| Rule | Pass | Pattern | Action |
|---|---|---|---|
| R1 | pass1 | `[w, mithya]` before `[c, active]` | compound lookup: "w-c" |
| R2 | pass1 | same, w is avastha qualifier | synthesize compound key |
| R3 | pass1b | `[base, value/unit, X]` after rename | reattribute to compound |
| R4 | pass2 | `[concept, active]` + `[w, pending-number, v]` | unitless bind `[concept, value, v]` |
| R8 | pass1c | `[label, mithya]` + `[possession-signal, mithya]` + `[concept, active]` | entity + ownership |
| R4b | pass1d | `[concept, active, owned]` + `[label, mithya]` | symbol binding |

Pass1 accumulates consecutive mithya into a pending list (not single word).
Only the last pending word is the compound candidate; all earlier ones flush to output.

### Needs rework

| Rule | Issue | Fix |
|---|---|---|
| R8 | Positional `cur-entity` propagation | Signal-based: only possession signals set ownership |
| R4b | Fires on back-reference words | Guard: only fire when no possession/grammar signal; don't bind entity's own name |

### Not yet implemented

| Rule | Pattern | Action | Kosha basis |
|---|---|---|---|
| R5 | N pending-numbers under active concept | `[concept, dvandva, [v0,...]]` | `set`, `element` |
| R6 | N mithya items before active concept | `[concept, dvandva, [x0,...]]` | `bahu-vachana`, `set` |
| R7 | `[respectively, mithya]` + two equal-length dvandva groups | morphism + paired-with | `morphism`, `equivalence-relation` |
| R9 | `[label, mithya]` + `[qualifier, mithya]` before possession | compound entity label | `tatpurusha` |
| R10 | `[its/their, mithya]` | `[pronoun, refers-to, entity]` | `parampara`, `samsarga` |
| R11 | `[the, grammar]` + `[entity-name, mithya]` | back-reference, not new entity | definite article |
| R12 | `"and"` interpretation | property-dvandva vs entity-dvandva | conjunction context |

---

## Implementation Order (Revised — Graph Formalization)

**Full plan**: `graph-formalization-plan.md` (canonical for implementation order)

The old Phase A–F is replaced by a formalization-first approach. Instead of fixing
R8 with better reduce logic, we register the question graph's edge labels as
visheshanam dimensions and materialize the question graph into the proof graph.
Then R8 becomes a typed graph walk, not a stateful reduce, and ownership correctness
is enforced structurally by the dimension properties (antisymmetric, non-transitive).

### Phase 0 — Foundation (no behavior change)
- Create `brahman/sangati/prashna/` nodes for each edge label (active, mithya, q-owner, etc.)
- Register as dimensions in `visheshanam-ring.om`
- No regressions possible — purely additive

### Phase 1 — Materialization bridge
- `materialize-question-graph.tantra` — VList triples → proof-graph nodes via emit-node
- Formalization test suite — verify dimensions registered, nodes walkable

### Phase 2 — Signal-based R8 rewrite
- Remove `cur-entity` propagation, use bounded ownership with explicit stop boundaries
- R4b guards (no entity self-reference, no grammar word binding)
- Grammar nodes: `verb-have.om`, `prep-of.om` role2:possession

### Phase 3 — Pronouns and back-references (R10, R11)
### Phase 4 — Dvandva groups (R5, R6, R7, R12)
### Phase 5 — Full pipeline integration (materialize → match → execute → trace)

---

## Key Files

```
brahman/kosha/math/logic/          inference, theorem, proof, proposition, implication, axiom
brahman/kosha/math/graph/          graph-walk, breadth-first, depth-first, shortest-path
brahman/kosha/math/algebra/        graded-ring, morphism, equivalence-relation, set-product
brahman/kosha/math/set/            set, element, subset
brahman/kosha/physics/             21 mantra nodes — krama + pratipaksha + implication
brahman/bhasha/english/grammar/    grammar nodes — copula, articles, prepositions, conjunctions
brahman/yantra/build-question-graph.tantra   BQG — word-by-word, punctuation-aware
brahman/yantra/avrti-refine.tantra           avrti — R1-R4, R8, R4b (signal-based ownership)
brahman/yantra/emit-triples.tantra           triple emission with role:possession exclusion
brahman/yantra/match-mantra.tantra           match — implication walk + coverage check
brahman/yantra/execute-chain.tantra          execute — krama stack machine
brahman/yantra/compose-trace.tantra          compose — full reasoning trace (TODO Phase F)
brahman/yantra/tests/dvandva/               dvandva group tests (5/12 passing)
brahman/yantra/tests/entity/                entity recognition tests (8/14 passing)
```
