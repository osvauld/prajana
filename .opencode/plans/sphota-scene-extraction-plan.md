# Sphoṭa-Based Scene Extraction

## Philosophy

### Sphoṭa — meaning arrives whole

In Bhartṛhari's sphoṭa theory (स्फोट), meaning **emerges as a whole** when sufficient
conditions converge. Not assembled piece by piece from words. The sangati node `sphoTa.om`
encodes this: `tantu-swarupa spanda-kriya anunada-phala` — the thread-form, the
vibration-action, the resonance-result. Meaning is the resonance that arises when
independent vibrations align.

### Vyākaraṇa — grammar as meaning

The engine is named `vyakarana` — Pāṇini's grammar. In Sanskrit grammar, grammatical
relations ARE meaning-carriers, not decoration. kāraka (case relations), vibhakti
(inflection), samāsa (compound structure) encode structure that English encodes through
word order and punctuation. Our parser treats punctuation as **structural operators with
algebraic semantics**:

- **Period (.)** — group boundary. Resets concept context. A new sentence = a new group.
- **Comma / "and"** — intra-group element separator. Next element in the current sequence.
- **"respectively"** — explicit bijection. Two parallel sequences share the same index set.
- **Modifier** — semantic role carrier. "max" = seema (constraint). "initial" = avastha (state).

Grammar is not decoration. It is algebra.

### Group theory — the scene graph IS the group structure

The natural language paragraph is a **group-theoretic encoding** of a scene graph. Parsing
does not produce an intermediate representation that then becomes a graph. **The graph is
the direct output. They are the same thing.**

Each concept class extracted from text forms a **group** with its own index set:

```
link-length group:      {5m, 3m}      indexed by joints {0, 1}
joint-speed-max group:  {2 rad/s, 3 rad/s}  indexed by joints {0, 1}
```

The joint nodes `{joint-0, joint-1}` are the **shared index set** across all groups.
"Respectively" asserts a **group isomorphism** — both groups map onto the same joint nodes.
Without the word, it is implied by position.

The same element belongs to **multiple groups simultaneously**, each expressing a different
semantic relationship:

```
2 rad/s at joint-0:
  → joint-speed-max group  (concept class)
  → seema group            (constraint — because "max" modifier)
  → kramanusara depth-1    (first time-derivative of angle)
  → angular-velocity class (unit dimension group)
```

These are not contradictions. They are multiple simultaneous truths expressed as multiple
edge types in the graph — exactly the visheshanam (edge type) model we already have.

### Three convergent signals — sphoṭa in the graph

No single signal selects a concept unambiguously. Three converge:

**1. Dimension signal (matra)** — unit decomposes into SI exponent vector `[M,L,T,I,θ,N,J]`.
`rad/s` → `[0,0,-1,0,0,0,0,1]`. Physical class independent of word used.

**2. Kramanusara depth** — `|T exponent|` = position in derivative chain:
- depth 0 → position (radian, metre)
- depth 1 → velocity (rad/s, m/s)
- depth 2 → acceleration (rad/s², m/s²)

**3. Domain context** — modifier semantic role + scene type + neighbouring concepts.
`rad/s` + `seema` modifier + domain `kinematic-chain` → `joint-speed-max`.

The graph PPR/context-score infrastructure already does this convergence. The parser reads
the grammar structure; the graph resolves the meaning.

### No defaults

If a property is not stated in the input, the system asks for it. Defaults are fabrications.
The input must be self-contained. The system reports exactly what it understood and asks for
what it did not receive.

### Input discipline

Input is a **natural language paragraph**, grammatically well-formed, one concept group per
sentence:

```
A 2-joint robot arm.
Link lengths are 5 metres and 3 metres.
Joint angles are 0 and 0 radians.
Max joint speeds are 2 rad/s and 3 rad/s.
Move the end effector to position 3, 4.
```

This is normal good writing. The group structure falls out of grammar naturally. No special
syntax required from the user.

---

## Architecture

### The scene graph is built directly from parsing

Each sentence parsed emits edges directly into the scene sub-graph. No intermediate tuple
list that is then converted. Parsing = graph construction.

```
Sentence 1: "Link lengths are 5 metres and 3 metres."
  → creates link-length edges on joint-0 and joint-1

Sentence 2: "Max joint speeds are 2 rad/s and 3 rad/s."
  → creates joint-speed-max (seema) edges on joint-0 and joint-1

Sentence 3: "Move the end effector to position 3, 4."
  → creates target node with lakshya edge from arm node
```

The joint nodes are created first (from n-joints detection). Every subsequent sentence
attaches properties to the **same joint nodes** — the shared index set made concrete.

### Edge types emitted per value

A single extracted value creates **multiple simultaneous edges** — one per group membership:

```
joint-0 --[joint-speed-max]--> 2.0   (concept assignment)
joint-0 --[seema]-----------> 2.0   (constraint — from seema modifier)
joint-0 --[matra]-----------> radian-per-second  (unit)
```

The visheshanam (edge type) system already supports this.

### Modifier semantic role in the token

`classify-fold` now reads modifier subtype from shabda:
- `max`, `rated`, `limit` → kind = `seema` (constraint modifier)
- `kinetic`, `electrical`, `angular` → kind = `compound` (compound-forming)
- `average`, `net`, `total` → kind = `aggregation`

`classify-fold-resolve` propagates the modifier's role when folding with a concept.

The token triple `[word, kind, resolved]` where `kind` now carries semantic role — not just
syntactic category.

### Index assignment — group position, not global counter

Joint index for a value = **position of this value within its concept group** in the
sentence. Computed by: count of same-concept values already seen.

Two-pass approach:
1. Collect raw `[value, concept, unit]` triples in sentence order
2. For each triple: `idx = count of prior triples with same concept` → assigns 0, 1, 2...

This naturally gives each concept group its own 0-based index sequence regardless of
how many other concept groups appear in the same paragraph.

### Completeness check before computation

After building the scene graph, check required properties are present:
- **Required**: n-joints, link-length per joint, joint-angle per joint
- **Optional but reported**: joint-speed-max, rated-torque, rated-power, link-mass

Missing required property → return clarification request, not computation.
Missing optional property → note it in narration, skip that part of computation.

---

## Implementation Plan

### Phase 1: Classifier (DONE)
- `english-modifiers.om` — modifier subtypes in shabda: `seema`, `compound`, `aggregation`
- `classify-fold.tantra` — reads modifier subtype, uses as token kind
- `classify-fold-resolve.tantra` — propagates modifier role when folding

### Phase 2: Value-unit extraction rewrite
- `extract-value-units.tantra` — two-pass: collect triples, then assign group indices
- No global counter. No sentence-splitting needed — group position is sufficient.
- Returns `[value, concept, unit, joint-idx]` with correct per-concept indices

### Phase 3: Direct graph construction
- `scene-extract-kinematic-chain.tantra` — create joint/link nodes first
- Attach properties as edges using extracted tuples
- Each value → multiple edge types (concept + seema/avastha role + unit)

### Phase 4: Completeness check and narration
- After graph construction, verify required properties present
- Missing → ask for it, not default
- Narration echoes exactly what was understood

### Phase 5: Joint dynamics in graph
- Joint node already has `rated-torque-yukta`, `angular-velocity-yukta`
- Tantra `joint-dynamics` computes required-torque = I·α from link properties
- Motor feasibility = compare required vs rated — already partially there

---

## Files

### To rewrite
| File | Change |
|------|--------|
| `brahman/yantra/scene/extract-value-units.tantra` | Two-pass group-index approach |
| `brahman/yantra/scene/scene-extract-kinematic-chain.tantra` | Direct graph construction, no defaults |

### Done
| File | Change |
|------|--------|
| `brahman/kosha/language/english/modifiers.om` | Modifier subtypes: seema/compound/aggregation |
| `brahman/yantra/classify-fold.tantra` | Reads modifier subtype from shabda |
| `brahman/yantra/classify-fold-resolve.tantra` | Propagates modifier role in fold |
| `brahman/kosha/physics/matra-beeja.shabda` | `concepts-for-unit` in unit entries |
| `brahman/kosha/physics/metre.om` | Changed to kosha node |
| `brahman/kosha/physics/radian-per-second.om` | Removed — defined in matra-beeja |

### Debug code to remove
| File | What |
|------|------|
| `vyakarana/lib/yantra_parser.ml` | DBG-tantra, DBG-parse, DBG-collect_args |
| `vyakarana/lib/yantra_index.ml` | DBG-arity prints |
| `vyakarana/lib/yantra_ops.ml` | DBG-reduce prints |
| `vyakarana/lib/yantra_eval_primitives.ml` | DBG-shabda print |
| `brahman/yantra/scene/scene-extract-kinematic-chain.tantra` | DBG value-tuples print |
| `brahman/yantra/scene/extract-value-units.tantra` | DBG-cfu, DBG-evu prints |

---

## Verification

Input (complete, self-contained, one concept per sentence):
```
A 2-joint robot arm. Link lengths are 5 metres and 3 metres. Joint angles are 0 and 0 radians. Max joint speeds are 2 rad/s and 3 rad/s. Move the end effector to position 3, 4.
```

Expected scene graph:
```
arm-sc1
  n-joints: 2
  joint-0: link-length=5m, joint-angle=0rad, joint-speed-max=2rad/s (seema)
  joint-1: link-length=3m, joint-angle=0rad, joint-speed-max=3rad/s (seema)
  target: [3, 4, 0]
```

Expected output: correct IK solution, no `?` in narration, no defaults used.
