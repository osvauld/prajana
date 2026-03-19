# 17 — Completing the Tantra: Architecture After Scan-Ref

**The working document. The structural plan for what the codebase becomes.**

---

## Two Discoveries

### Discovery 1: The scan-ref fix completes the tantra cycle

The scan-ref fix (doc 16) was a parser bug fix. But what it revealed is
architectural: every tantra was constrained to an incomplete cycle. A
tantra could perceive (scan the graph) but could not reflect on its
perception (reference the scan output for further processing). This
forced fragmentation (one thought split across files) and monoliths
(orchestrators carrying state between fragments).

The fix completes the cycle: **perceive → reflect → act**
(sparsha → viveka → bandha) within a single file.

### Discovery 2: The math kosha is an unused library of operations

83 mantra-layer nodes in the math domain are declared but not connected
to the pipeline. The pipeline uses 23 physics mantras. It hardcodes the
same logic the math kosha already declares:

```
addition   → eval:add, arity:2, pratipaksha:subtraction
subtraction → eval:sub, arity:2, pratipaksha:addition
max        → eval:max, arity:2  (viveka-max --[abheda]--> max)
min        → eval:min, arity:2  (viveka-min --[abheda]--> min)
sum        → eval:add, arity:-1 (variadic addition)
product    → eval:mul, arity:-1 (variadic multiplication)
```

And the algebraic structure behind them:

```
ring    --[kriya]--> addition, multiplication
ring    --[siddha]--> distributivity
lattice --[kriya]--> join, meet
monoid  --[abheda]--> op-class-monoid (the tantra parser's own monoid!)
commutativity --[drishthanta]--> addition, multiplication
```

And the reasoning operations:

```
modus-ponens --[janya]--> implication  (syllogism as a mantra)
inference    --[yukta]--> viveka-max, viveka-min
graph-walk   --[phala]--> path         (transitive closure)
viveka-max   --[swarupa]--> viveka     (comparison IS viveka)
```

And the bridge:

```
ganana-setu: add → addition, sub → subtraction, mul → multiplication, ...
```

The pipeline hardcodes what the kosha already says. Every tantric
improvement should read the kosha, not re-implement it.

---

## The Unifying Principle

### One mechanism for all reasoning types

Every question the pipeline answers follows the same structure:

1. **Detect** the question type by reading `swarupa` edges from
   concepts in the graph
2. **Find** the operation by following abheda/kriya/yukta edges to
   a math operation node
3. **Read** the operation's `eval` shabda to get the primitive
4. **Collect** the operands (scan-ref: perceive, then post-scan collect)
5. **Fire** via `apply-op eval operands`
6. **Emit** the result back into the graph

This is ONE mechanism, not five separate ones:

| Question type | Kosha concept | Operation | eval |
|---------------|---------------|-----------|------|
| Count addition | count → arithmetic → addition | addition | add |
| Count subtraction | count → arithmetic → subtraction | subtraction | sub |
| Comparison (more) | viveka-max → abheda → max | max | max |
| Comparison (less) | viveka-min → abheda → min | min | min |
| Total (dvandva) | sum | sum | add (variadic) |
| Syllogism | modus-ponens → janya → implication | modus-ponens | (chain) |
| Transitive | graph-walk → phala → path | graph-walk | (closure) |
| Physics | momentum-mantra → math-op → multiplication | multiplication | mul |

Physics already works this way (mantras have `math-op:multiplication`,
execute-mantra reads it, calls `apply-op "mul" args`). The other types
just need the same wiring.

### The Manipravalam principle realized

Writing `viveka-max --[abheda]--> max` in the kosha IS writing the
comparison capability. Writing `addition --[eval]--> add` IS writing
the count-addition capability. The pipeline reads these declarations
and fires. Adding a new question type = writing an .om file, not
modifying tantra code.

---

## Current baseline

**511 passed / 63 xfailed / 0 failed** (2026-03-19, session 10)

---

## The Structural Principle

### Sparsha → Viveka → Bandha at every scale

The three operations appear identically at every level:

**Inside a single tantra:**
- sparsha: a scan pattern-matches over graph triples
- viveka: a cond/filter discriminates what was found
- bandha: an emit/append writes the result

**Across tantras:**
- Group 2 (prathama-sparsha, shashthi-sparsha, ...) = sparsha
- Group 6 (viveka-ganana, anumana-viveka, ...) = viveka
- Group 3 (refinement passes) + Group 5 (proof emission) = bandha

**Across the whole pipeline:**
- anuvada-ganana sequences: perceive → discriminate → bind

### What a tantra should feel like

The equation tantras are the template: 12 lines, one thought. Every
tantra should approach this clarity — not in line count, but in
conceptual unity. One complete sparsha → viveka → bandha cycle.

---

## The Ten Natural Groups

Not by directory — by what the tantras ARE.

### Group 1: ORCHESTRATORS (5 tantras, ~250 lines)
**Tantras that sequence other tantras. They don't think — they wire.**

| Tantra | Lines | Role |
|--------|-------|------|
| anuvada-ganana | 119 | sentence → answer (dispatches everything) |
| session-anuvada | 40 | session wrapper, duplicates half of above |
| avrti-refine | 37 | sequences 10 sub-passes in refinement loop |
| emit-reasoning | 41 | sequences 5 proof limbs into speech |
| reboot | 13 | sequences boot passes |

**Problem:** anuvada-ganana is a 119-line dispatch table with hardcoded
question-type detection. The kosha already declares question types via
swarupa edges (viveka-max → swarupa → viveka). The orchestrator should
read the graph, not hardcode branches.

**Action:** Dissolve. Question-type detection reads swarupa. Dispatch
becomes thin wiring. avrti-refine and emit-reasoning stay.

### Group 2: PERCEPTION (8 tantras, ~310 lines)
**Pure readers. No side effects. The system's eyes.**

prathama-sparsha, shashthi-sparsha, sankhya-sparsha, bound-state,
extract-solve-for, anumana-sparsha, scope-vps, mantra-coverage

**Action:** Keep. These are well-named complete thoughts.

### Group 3: REFINEMENT (14 tantras, ~830 lines)
**Transform the graph within the avrti loop.**

sandhi-kosha, sandhi-avastha, sandhi-bandhana, vibhakti-shashthi,
sandhi-viveka, vishesa-instance, rashi-viveka, vishesa-bandhana,
rashi-anuvada, sankhya-bandha, count-bandha, assertion-bandha,
flush-pending-mithya, agra-bandha

**Problem:** count-bandha (102 lines) hardcodes signal-word lists and
synthetic count1/count2 concepts. The math kosha already has addition
(eval:add) and subtraction (eval:sub) with pratipaksha relationships.

**Action:** Dissolve count-bandha → count-chain reads the math kosha.
Consider merging sandhi-kosha + sandhi-avastha. The rest stay.

### Group 4: DERIVATION (11 tantras, ~470 lines)
**Compute new values from existing ones. The math engine.**

derive-step, derive-chain, mantra-select, match-mantra, forward-match,
inverse-match, execute-mantra, execute-matched, invert-math,
resolve-janya-args, relative-vps

**Note:** This group already uses the kosha correctly for physics.
execute-mantra reads `math-op` shabda, calls `apply-op`. invert-math
reads `pratipaksha` edges. This IS the pattern for all other groups.

**Action:** Simplify derive-chain (3 steps → loop). The rest stay.

### Group 5: PROOF EMISSION (11 tantras, ~620 lines)
**Turn the proof graph into speech. The panchaavayava.**

**Action:** Keep. Architecturally sound.

### Group 6: COMPARISON (3 tantras, ~200 lines)
**Discriminate: which is more, which is ancestor.**

| Tantra | Lines | What it compares |
|--------|-------|-----------------|
| viveka-ganana | 95 | which entity has more/less |
| anumana-viveka | 54 | does entity inherit from ancestor |
| anumana-viveka-yukta | 47 | does entity have property via varga |

**Problem:** viveka-ganana hardcodes gt/lt comparison. The kosha declares
`viveka-max --[abheda]--> max --[eval]--> max`. The comparison should
use `apply-op` via the kosha, same as physics mantras.

anumana-viveka manually unrolls 4 swarupa levels. The kosha declares
`graph-walk --[phala]--> path` — chain walking IS graph traversal.

**Action:** viveka-ganana uses kosha-driven max/min. anumana-viveka
uses scan-ref loop (unlimited depth).

### Group 7: GRAPH CONSTRUCTION (4 tantras, ~180 lines)
**Words in, graph out. The intake system.**

**Bug found:** emit-triples misclassifies kosha word aliases as rashi
labels when active concept exists. "many" (alias for count) becomes
mithya instead of satya when preceded by any satya word. Fix: check
`word-node` to distinguish aliases from labels.

**Action:** Fix emit-triples alias bug. Keep structure.

### Group 8: EQUATIONS (11 tantras, ~150 lines)
**Pure math. The irreducible transformations.**

**Action:** Keep. Add new ones as needed.

### Group 9: INFRASTRUCTURE (6 tantras, ~150 lines)
**Boot, lookup, debug, fixpoint.**

**Action:** Keep.

### Group 10: COUNTING (3 tantras, ~155 lines)
**The broken group. Where this all started.**

| Tantra | Lines | Status |
|--------|-------|--------|
| count-bandha | 102 | Workaround. Dissolve. |
| count-chain | 17 | Stub. Rewrite with kosha-driven ops. |
| sankhya-bandha | 36 | Works for non-count case. Keep. |

**Action:** Rewrite count-chain using the math kosha's addition/subtraction.
Dissolve count-bandha.

---

## The Math Kosha Connection

### What exists but is not connected (83 mantra-layer nodes)

**Level 1 — Operations (directly fireable via apply-op):**

| Node | eval | arity | pratipaksha | Pipeline use |
|------|------|-------|-------------|-------------|
| addition | add | 2 | subtraction | Count total |
| subtraction | sub | 2 | addition | Count remaining |
| multiplication | mul | 2 | division | Physics (connected) |
| division | div | 2 | multiplication | Physics inverse (connected) |
| max | max | 2 | — | Viveka "which has more" |
| min | min | 2 | — | Viveka "which has less" |
| sum | add | -1 | — | Dvandva "total of all" |
| product | mul | -1 | — | Dvandva "product of all" |
| square | square | 1 | square-root | Expression (connected) |
| half | half | 1 | double | Expression (connected) |

**Level 2 — Properties (reasoning shortcuts):**

| Property | What it declares | Pipeline implication |
|----------|-----------------|---------------------|
| commutativity → drishthanta → addition | a+b = b+a | Operand order doesn't matter in count |
| pratipaksha: addition ↔ subtraction | They're inverses | If total and part known, find the other |
| associativity → drishthanta → addition | (a+b)+c = a+(b+c) | Can accumulate left-to-right |
| distributivity → kriya → mul, add | a(b+c) = ab+ac | Per-entity derive then sum (dvandva) |

**Level 3 — Structures (deep reasoning):**

| Structure | What it declares | Pipeline implication |
|-----------|-----------------|---------------------|
| ring → kriya → addition, multiplication | Integers form a ring | Count arithmetic is ring arithmetic |
| lattice → kriya → join, meet | Comparison is lattice | Transitive comparison is join |
| graph-walk → phala → path | Walk produces paths | Transitive closure is graph walk |
| modus-ponens → janya → implication | Syllogism needs IF-THEN | Detect implications, fire MP |
| inference → yukta → viveka-max, viveka-min | Inference contains comparison | Comparison is a kind of inference |

**Level 4 — Bridges:**

| Bridge | What it maps | Purpose |
|--------|-------------|---------|
| ganana-setu | add→addition, sub→subtraction, ... | Eval name ↔ math concept |
| viveka-max → abheda → max | Comparative word → operation | "heavier" → max operation |
| viveka-min → abheda → min | Comparative word → operation | "lighter" → min operation |

### What's already connected (template for the rest)

The physics path IS the pattern:

```
momentum-mantra → math-op:multiplication → apply-op "mul" [mass, velocity]
kinetic-energy-mantra → kriya:ke-expr → call-tantra ke-expr [mass, velocity]
invert-math → pratipaksha walk → find inverse operation
```

execute-mantra reads the kosha. invert-math reads the kosha.
The rest of the pipeline should do the same.

---

## Known Bugs To Fix

### emit-triples alias bug

**Root cause:** `is-rashi-label` check at line 34 uses `neq word (to-string nd)`
to distinguish labels from concepts. But kosha word aliases (declared via
`shabda word:many,...` in .om files) also have word ≠ node. "many" (→ count)
gets classified as a rashi label when active concept exists.

**Effect:** "how many birds are left" → "many" becomes `[many, mithya, many]`
instead of `[count, satya, count]`. count-bandha never fires. Blocks count
tests where a satya concept precedes "how many".

**Fix:** Check `word-node word` — if it returns the same node as
shabda-anveshana, the word is a declared alias, not a label.

### sankhya-bandha number-before-noun

In "10 birds", the number precedes the concept. sankhya-bandha tracks
`last-active` left-to-right, so 10 has no preceding satya to bind to.
In "3 fly away" after "tree", 3 wrongly binds to tree.

count-chain addresses this by computing the count directly from the event
sequence rather than relying on individual number→concept binding.

---

## The Dissolution Plan

### Phase 1: Connect the Math Kosha

The first phase is not just "fix count" — it's "establish the pattern of
reading the kosha for operations." count-chain is the first connection.
viveka-ganana is the second. Both use the same mechanism.

#### 1a. Fix emit-triples alias bug (Group 7)

Add alias detection: if `word-node word` equals `nd`, the word is a
declared alias, not a label. This unblocks count detection for all
sentence patterns where satya concepts precede "how many."

#### 1b. count-chain rewrite (Group 10)

**Dissolves:** count-bandha (102 lines)
**Creates:** count-chain rewrite (~50 lines)

One thought: walk the graph as a number line.

```
"8 birds. 3 flew away. 2 came back. how many remaining."
 └─ +8    └─ −3        └─ +2        └─ emit total (7)
```

The scan perceives numbers and verb signals. Post-scan:
- Look up the operation: count → arithmetic → addition or subtraction
  (based on verb signals → kosha concept → `eval` shabda)
- Fire: `apply-op eval [accumulated-operands]`
- Emit: `[count, sankhya, result]` into the graph

The verb signal → operation mapping:
- Departure verbs (gave, flew, away, lost...) → subtraction
- Arrival verbs (came, bought, found...) → addition
- Default (no verb) → addition (accumulation)
- The signal list stays in the tantra (it's sentence perception, not math)
- But the OPERATION comes from the kosha: addition.eval = "add"

Wire into avrti-refine: line 32, count-bandha → count-chain.

For the pipeline to fire the result: count-chain emits the result
directly as `[count, sankhya, 7]` (or `[count-total, sankhya, 7]`).
The solve-for concept already has a value. The proof path needs to
handle "value already computed" — or we create count-add-mantra and
count-sub-mantra .om files so the existing match→execute path fires.

**Decision point:** Direct emission vs. mantra. Direct emission is
simpler. Mantra is more compositional (proof emission works for free).
Start with direct emission; add mantras if proof quality demands it.

#### 1c. viveka-ganana → kosha-driven comparison (Group 6)

Currently: hardcoded reduce + gt/lt.

After: scan-ref collects per-entity values. Post-scan: look up
viveka-max.abheda → max → eval:max. Fire: `apply-op "max" [val1, val2]`.
Return the entity that wins.

Same mechanism as count-chain — read kosha, find operation, fire.

#### 1d. derive-chain simplification (Group 4)

3 manually unrolled steps → 1 scan-ref loop.
composition --[swarupa]--> parampara — the chain IS composition.

#### 1e. anumana-viveka simplification (Group 6)

4 copy-pasted levels → scan-ref loop over swarupa edges.
graph-walk --[phala]--> path — the chain walk IS graph traversal.

### Phase 2: Dissolve the Monolith (Group 1)

anuvada-ganana → thin wiring that reads graph swarupa edges to
determine question type. The kosha declares the types:
- viveka-max --[swarupa]--> viveka → comparison path
- modus-ponens --[swarupa]--> inference → syllogism path
- count --[yukta]--> arithmetic → count path
- momentum-mantra --[varga]--> physics-mantra → physics path

Dispatch reads the graph and routes. No hardcoded branches.

~20 lines after extraction. session-anuvada duplication vanishes.

### Phase 3: Merge Fragments (Group 3)

sandhi-kosha + sandhi-avastha → one compound-resolution pass.
Optional, risky, defer.

### Phase 4: New Complete Thoughts

Each one follows the same pattern: detect via swarupa, find operation
via kosha, collect operands via scan-ref, fire via apply-op.

#### 4a. viveka-derive

**Thought:** For each entity, compute derived values, then compare.

"Which has more KE" = derive KE per entity (multiplication path),
then compare (max path). Uses both physics mantras AND viveka-max.

Unlocks: 4 xfails (viveka compute-then-compare)

#### 4b. dvandva-ganana

**Thought:** For each entity, compute a value, then aggregate.

"Total momentum of two balls" = compute momentum per entity, then sum.
Uses: per-entity derive (same as viveka-derive) + `sum` (eval:add, arity:-1).
distributivity --[kriya]--> multiplication, addition — per entity
multiply, then add.

total-momentum is already a kosha concept with `swarupa: momentum,
sthita: samgraha (collection)`.

Unlocks: 4 xfails (dvandva per-entity)

#### 4c. krama-viveka

**Thought:** Given comparison edges, build transitive closure.

"A > B, B > C, who is greatest?" = scan comparison edges, collect as
pairs, compute closure. lattice --[kriya]--> join, meet — the answer
is the lattice join. graph-walk --[phala]--> path — the closure IS
a graph walk.

Unlocks: 8 xfails (transitive reasoning)

#### 4d. anumana-ganana (syllogism)

**Thought:** Given implication + instance, fire modus ponens.

"All birds have wings. 3 animals are birds. How many have wings?"
modus-ponens --[janya]--> implication. The implication is "bird → wings".
The instance is "3 are birds." The conclusion: those 3 have wings.

The kosha declares the rule structure. The pipeline needs to detect
implications in the graph, match them with instances, fire MP.

Unlocks: subset of transitive/logic xfails

---

## What Does NOT Need Scan-Ref or Math Kosha

| Gate | Count | Blocked by |
|------|-------|-----------|
| session_gap2 | 6 | Session entity carry (socket.ml) |
| sthita-viveka | 4 | Multi-slot entity assignment |
| unit_rate | 4 | Compound unit handling |
| parsing: natural | 3 | Grammar improvements |
| p8f_gravity | 1 | G constant + r² composition |
| parsing: article | 1 | "the" before entity name |
| relative-velocity | 1 | Kosha concept missing |
| pratibimba | 1 | Gated on session Gap 2 |
| viveka: proportional | 2 | Proportional reasoning mechanism |

Total: ~23 xfails not addressable by this plan.

---

## Implementation Order

| Order | What | Mechanism | Tests |
|-------|------|-----------|-------|
| 1 | Fix emit-triples alias bug | word-node check | 0 (unblocks count) |
| 2 | count-chain rewrite | kosha: addition/subtraction | +6 |
| 3 | viveka-ganana → kosha max/min | kosha: max/min via abheda | 0 (quality) |
| 4 | derive-chain simplification | scan-ref loop | 0 (quality) |
| 5 | anumana-viveka simplification | scan-ref loop | 0 (quality) |
| 6 | Dissolve anuvada-ganana | swarupa-driven dispatch | 0 (architecture) |
| 7 | viveka-derive | kosha: derive + max | +4 |
| 8 | dvandva-ganana | kosha: derive + sum (variadic) | +4 |
| 9 | krama-viveka | kosha: lattice join | +8 |

**Best case: 22 xfails promoted, 63 → 41.**

**The real win:** one mechanism (read kosha → find operation → fire) for
all reasoning types. New capabilities emerge from .om declarations, not
from tantra modifications.

---

## The Net Transformation

| | Before | After |
|---|---|---|
| Total tantras | 72 | ~74 (−2 dissolved, +4 new) |
| Math kosha nodes connected | 23 (physics only) | ~35 (+ count, viveka, logic) |
| Monolith lines (anuvada-ganana) | 119 | ~20 (thin wiring) |
| Question type dispatch | Hardcoded branches | Kosha swarupa-driven |
| New question type cost | Modify orchestrator + write tantra | Write .om + write tantra |
| Tantra completeness | Fragments (scan without reflect) | Each tantra = full cycle |
| Hardcoded operations | gt/lt in viveka, add/sub lists in count | apply-op via kosha eval |

---

## Philosophical Direction

### The math kosha IS the library

The kosha declares `addition --[eval]--> add` and `max --[eval]--> max`.
These are not metadata. They are the complete specification of how to
compute. The pipeline should read them, not re-implement them.

invert-math already does this: it walks pratipaksha edges to find the
inverse operation. This IS the pattern. Every other operation (count,
viveka, syllogism) should follow the same pattern.

### The algebra is not decorative

`ring --[kriya]--> addition, multiplication` declares that integer
arithmetic has both operations. `commutativity --[drishthanta]--> addition`
declares that operand order doesn't matter. `distributivity --[kriya]-->
multiplication, addition` declares that per-entity multiply then add is
valid. These are not facts-about-math stored in the kosha. They are
structural properties that the pipeline can USE — to optimize operation
order, validate transformations, or choose between equivalent paths.

### monoid --[abheda]--> op-class-monoid

The tantra parser's own `op-class-monoid` (which `append`, `pair`, `or`,
`concat` inherit from, giving them arity=-1) IS the same algebraic
structure as the kosha's `monoid`. The code IS the math. Manipravalam.

### One mechanism

Count, comparison, syllogism, transitive reasoning, dvandva aggregation
— they look different in natural language but follow the same structure:
detect the operation in the kosha, collect operands, fire. The math
kosha is the unifying layer. Writing an .om file IS writing a capability.

---

## What Has Changed

| Date | Session | Event |
|------|---------|-------|
| 2026-03-19 | 9 | Document created. Five scan-ref patterns identified. 22 xfails mapped across 4 tiers. |
| 2026-03-19 | 10 | **Document rewritten.** Architecture-driven plan. Ten natural groups. Four phases. Principle: every tantra = one complete cycle. |
| 2026-03-19 | 10 | **Math kosha discovery.** 83 mantra-layer math nodes unused. The pipeline hardcodes what the kosha declares. One mechanism (read kosha → find operation → fire) unifies count, viveka, syllogism, transitive, dvandva. Three levels: operations (eval:add), properties (commutativity, pratipaksha), structures (ring, lattice, graph-walk). ganana-setu bridges eval names to math concepts. invert-math is the existing template. emit-triples alias bug found (word ≠ node conflates aliases with labels). |
