# Graded Ring Extraction: Sentence Algebra for n-DOF Scenes

**Extends**: `sphota-scene-extraction-plan.md` (group theory, three signals)
**Extends**: `tantra-domain-authoring.md` (tantra patterns, pitfalls)
**Supersedes**: the "no sentence-splitting needed" claim in the sphoṭa plan

---

## The Problem

The sphoṭa plan established that each concept class forms a **group** indexed by
position. "Link lengths are 0.3, 0.3, 0.2 m" → `{link-length_0, link-length_1,
link-length_2}`. This is correct within a single sentence.

But the current `extract-value-units` counts concept occurrences **across the
entire paragraph**, ignoring sentence boundaries. This causes:

1. **Index pollution**: "Move to 0.4, 0.3 m." appends two more link-length values
   at indices 3 and 4 — they're metres, so the extractor calls them link-length.
   Result: 5-DOF arm instead of 3.

2. **Cross-reference blindness**: "The second joint has speed 1.5 rad/s." should
   assign index 1 by explicit reference, not by counting prior joint-speed-max
   occurrences across all sentences.

3. **Concept ambiguity**: the same unit (metre) serves different roles in different
   sentences — link-length in the structural sentence, position-coordinate in the
   target sentence. The first `concepts-for-unit` candidate always wins, but sentence
   context should disambiguate.

**The sphoṭa plan was correct that grammar IS algebra. But it used only group theory.
The full algebraic structure of a paragraph is a graded ring.**

---

## The Graded Ring Structure

### Why a ring, not just a group

A group has one operation. A paragraph has two:

| Operation | Algebraic role | NL realization |
|-----------|---------------|----------------|
| **Additive** (⊕) | Intra-sentence indexing | Comma, "and", position within sentence |
| **Multiplicative** (⊗) | Cross-sentence selection | "the second joint", "joint 1", ordinal references |

These satisfy:
- **(⊕) is a group**: sequential index assignment within a concept class in one sentence.
  Identity = empty sequence. Inverse = removal. Closure = adding another value extends the group.
- **(⊗) is a monoid**: entity selection composes ("the second joint's rated torque" = select joint ⊗ select property).
  Identity = "this sentence's own entities". No inverse (you can't un-refer).
- **Distributivity**: "Joints 0 and 1 have speeds 2 and 1.5 rad/s respectively."
  The additive structure (commas → indices {0, 1}) distributes over the multiplicative
  structure (joint references → entity selection). "Respectively" is the distributive
  law stated in natural language.

Group + monoid + distributivity = **ring**.

### Why graded

Each sentence occupies a **grade** (depth). The grades form a filtration:

| Grade | Role | Example |
|-------|------|---------|
| 0 | **Structural** | "A 3-joint robot arm." — establishes entity count |
| 1 | **Property** | "Link lengths are 0.3, 0.3, 0.2 m." — assigns values to entities |
| 2 | **Refinement** | "The second joint has speed 1.5 rad/s." — cross-references + assigns |
| 3 | **Goal/constraint** | "Move to 0.4, 0.3 m. Minimize power." — target + objective |

**Multiplication respects grading**: a sentence at grade k can only reference entities
established at grade < k. A grade-1 sentence attaches properties to grade-0 entities.
A grade-2 sentence selects into grade-0 entities using explicit references. A grade-3
sentence specifies targets and goals that operate on the fully-defined entity space.

This is exactly the graded-ring property from `graded-ring.om`:
```
ring-sthita  filtration-yukta  partial-order-yukta
grade-yukta  depth-yukta
```

### The existing kosha already defines this

```
graded-ring.om:  ring-sthita filtration-yukta partial-order-yukta
                 grade-yukta depth-yukta monoid-janya

ring.om:         group-sthita monoid-yukta distributivity-siddha

distributivity.om: multiplication-kriya addition-kriya
```

No new math concepts needed. The algebraic structure is already in the graph.
What's missing is the **implementation** in the extraction pipeline.

---

## Entity Selectors (new concept)

Cross-sentence reference requires a **selector** — a morphism from name-space to
entity-space. Selectors are how the multiplicative operation works concretely.

### Types of selectors

| Selector form | Example | Resolution |
|---------------|---------|------------|
| Ordinal | "the second joint" | index = ordinal - 1 |
| Cardinal | "joint 1", "link 2" | index = cardinal |
| Demonstrative | "that joint", "the link" | index = most recent entity in focus |
| Possessive | "its speed", "the joint's torque" | index = antecedent entity |
| Implicit | (no selector) | index = position within additive group |

### Selector as morphism

A selector is a morphism `S: Name → Entity` where:
- **Name** is the token or phrase ("the second joint", "joint 1")
- **Entity** is a node in the scene graph (joint-1-sc1)
- The morphism preserves structure: "the second joint's rated torque" =
  S("second joint") ⊗ S("rated torque") = joint-1 × rated-torque property

This maps to the existing `morphism.om`:
```
morphism.om: eka-eka-swarupa aadana-visarjana-swarupa
```

### New kosha node needed

```
kosha entity-selector

  "morphism-swarupa domain-language-sthita"
  "name-aadana entity-visarjana"
  "ordinal-yukta cardinal-yukta demonstrative-yukta"
  "anaphora-abheda"

shabda entity-selector, selector / a-morphism-that-maps-a-natural-language-reference-to-a-scene-graph-entity
```

---

## Joint DOF Model (corrected)

The current model conflates joints, links, and DOF. The correct model:

### Each joint has a type, each type has a DOF

| Joint type | DOF | Generalized coordinates |
|-----------|-----|------------------------|
| Revolute | 1 | 1 angle (θ) |
| Prismatic | 1 | 1 displacement (d) |
| Cylindrical | 2 | 1 angle + 1 displacement |
| Spherical | 3 | 3 angles (θ, φ, ψ) |
| Planar | 3 | 2 translations + 1 rotation |
| Free | 6 | 3 translations + 3 rotations |

### The kinematic chain

```
ground → [joint_0, type_0, dof=k_0] → link_0
       → [joint_1, type_1, dof=k_1] → link_1
       → ...
       → [joint_{n-1}, type_{n-1}, dof=k_{n-1}] → link_{n-1} → end-effector
```

- **n-joints** = number of physical joints (structural count from link-lengths)
- **n-links** = n-joints (one link per joint in a serial chain)
- **total-DOF** = Σ dof(type_i) — computed, not extracted
- **configuration** = vector of all generalized coordinates, dimension = total-DOF

### What this means for extraction

1. Count link-length values in the structural sentence → n-joints
2. Each joint defaults to revolute (DOF=1) unless explicitly specified
3. Total DOF is a computed property, never directly extracted
4. The IK solver must match the joint types:
   - All revolute, 2 joints → arm-plan-2dof (analytic)
   - All revolute, n joints → Jacobian IK (future: ik-ndof)
   - Mixed types → dispatched per-type (future)

---

## Upgraded Extract-Value-Units Design

### Current (broken)

```
Pass 1: collect [value, concept, unit] across entire paragraph
Pass 2: idx = count of ALL prior triples with same concept (global)
```

### Upgraded (graded ring)

```
Pass 1: collect [value, concept, unit, sentence-num] — tag with grade
  - Track sentence boundaries (period tokens in classified stream)
  - sentence-num increments at each period

Pass 2: for each triple at sentence s:
  a. Check for explicit selector in same sentence
     (ordinal/cardinal near the value → multiplicative index)
  b. If no selector: idx = count of prior triples with same concept
     IN THE SAME SENTENCE (additive index, grade-local)
  c. Tag: [value, concept, unit, idx, sentence-num, selector-type]
```

### What changes in extract-value-units.tantra

**Pass 1** — add sentence tracking to the accumulator:

```
-- accumulator: [results, last-num, sentence-num]
-- on period token: increment sentence-num, clear last-num
-- each emitted triple becomes [value, concept, unit, sentence-num]
```

**Pass 2** — grade-local indexing:

```
-- for each triple t at sentence s:
-- idx = count of prior triples with same concept AND same sentence-num
-- result: [value, concept, unit, idx, sentence-num]
```

### What changes in scene-extract-kinematic-chain.tantra

**n-joints detection**:
- Find the structural sentence (the one with link-length values)
- n-joints = count of link-length triples in that sentence alone
- No subtraction hacks. No DOF-pattern detection needed as fallback
  (though N-DOF detection remains as a bonus signal)

**Property assignment**:
- For each joint i, filter value-tuples where concept matches AND idx = i
- Cross-sentence triples (refinement sentences) use their selector-resolved idx
- Grade-3 sentences (target/goal) are handled separately — they don't contribute
  to entity properties

---

## Sentence Grade Assignment

How to determine a sentence's grade:

| Signal | Grade | Reason |
|--------|-------|--------|
| Contains "arm", "robot", "joint", "DOF" + count | 0 | Structural declaration |
| Contains property values with units, no selectors | 1 | Bulk property assignment |
| Contains explicit entity reference + values | 2 | Refinement via cross-reference |
| Contains "move", "to", "target", "minimize", "optimize" | 3 | Goal/constraint |

For the initial implementation, we don't need to classify grades explicitly.
The sentence-num tag is sufficient — the scene extractor knows:
- Link-length triples define n-joints (structural role)
- Target triggers separate target coordinates from entity properties
- Explicit selectors override additive indexing

Grade classification can be added later as the system grows more sophisticated.

---

## Implementation Phases

### Phase A: Sentence-aware extraction (the additive fix)

1. Modify `extract-value-units.tantra`:
   - Track sentence boundaries (period in token stream)
   - Tag triples with sentence-num
   - Pass 2 counts within same sentence only

2. Modify `scene-extract-kinematic-chain.tantra`:
   - n-joints = count of link-length triples in the structural sentence
   - Remove n-from-values subtraction hack
   - Remove n-joints-pre / n-use-values complexity

3. Test: "3 links + target coords" gives n-joints=3, not 5.

### Phase B: Entity selectors (the multiplicative operation)

1. Create `entity-selector.om` in kosha/language
2. Detect ordinal/cardinal selectors in classify-fold:
   - "the second joint" → selector(ordinal, 1)
   - "joint 1" → selector(cardinal, 1)
3. In pass 2 of extract-value-units:
   - If a selector is detected near a value, use selector index
   - Override additive indexing with multiplicative selection
4. Test: "The second joint has speed 1.5 rad/s." assigns to joint index 1.

### Phase C: n-DOF understanding (generalized computation)

1. `scene-understand-kinematic-chain.tantra` already generalized:
   - Per-joint data read via `map (range n-joints)`
   - Motor check, path energy, optimization via `reduce`
   - Print lines via `reduce` with paren-wrapped concat
2. Remaining: IK dispatch based on joint types
   - All revolute, n=2 → arm-plan-2dof (current)
   - All revolute, n>2 → fk-ndof for FK; IK reports "joints 2+ not solved" (current)
   - Mixed types → future: Jacobian IK (ik-ndof.tantra)
3. FK verification via fk-ndof for all n joints (future enhancement)

### Phase D: Distributive law ("respectively")

1. Detect "respectively" in classify-fold
2. When found: the two concept groups in the same sentence share a bijective
   index mapping — zip them together
3. "Joints 0 and 1 have lengths 5 and 3 m and speeds 2 and 3 rad/s respectively."
   → link-length and joint-speed-max groups share the same index set
4. This already works implicitly (both groups get 0-based indices by position).
   "Respectively" just makes the bijection explicit and validates it.

---

## Tantra Parser Pitfalls for This Work

(Carried forward from tantra-domain-authoring.md)

1. **`le` not `lte`**: comparison ops are `lt`, `le`, `gt`, `ge` — not `lte`/`gte`
2. **`le i 0.5` threshold trick**: range returns VFloat; to compare index i with
   integer boundary, use 0.5/1.5 thresholds to avoid VFloat/VInt ambiguity
   (but prefer building string lists and using nth instead)
3. **Variadic concat in lambda**: wrap in parens `let ln = (concat ...)` to prevent
   greedy consumption of the following return expression
4. **Nested cond**: never write `cond guard1 body1 cond guard2 body2` — pre-compute
   booleans into named vars, then flat cond: `cond is-a val-a is-b val-b otherwise def`
5. **No VInt**: all numbers are VFloat. `range` returns VFloat list.

---

## Cross-References

- Sphoṭa philosophy: `.opencode/plans/sphota-scene-extraction-plan.md`
- Domain authoring guide: `.opencode/plans/tantra-domain-authoring.md`
- Scene comprehension master: `.opencode/plans/scene-comprehension-plan.md`
- Robotics IK detail: `.opencode/plans/robotics-ik-2dof-plan.md`
- Graded ring definition: `brahman/kosha/math/graded-ring.om`
- Ring definition: `brahman/kosha/math/ring.om`
- Distributivity: `brahman/kosha/math/distributivity.om`
- Current extractor: `brahman/yantra/scene/extract-value-units.tantra`
- Current scene extract: `brahman/yantra/scene/scene-extract-kinematic-chain.tantra`
- Current scene understand: `brahman/yantra/scene/scene-understand-kinematic-chain.tantra`

---

## Verification

After Phase A:

```
Input:  "A 3-DOF robot arm has link lengths 0.3, 0.3, and 0.2 m. Move the end effector to 0.4, 0.3 m."
Expect: n-joints = 3 (from 3 link-length values in sentence 1, not 5)
        target = [0.4, 0.3, 0]
        joints 0,1,2 with link-lengths 0.3, 0.3, 0.2
```

After Phase B:

```
Input:  "A 3-joint arm with link lengths 0.3, 0.3, 0.2 m. The second joint has a speed of 1.5 rad/s."
Expect: joint-1 gets joint-speed-max=1.5 (from ordinal selector "second")
        joints 0,2 get default speed
```

After Phase D:

```
Input:  "Link lengths are 5 and 3 m. Max speeds are 2 and 3 rad/s respectively."
Expect: link-length and joint-speed-max groups share index set {0, 1}
        "respectively" validates the bijection
```
