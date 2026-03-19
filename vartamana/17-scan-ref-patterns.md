# 17 — Completing the Tantra: Architecture After Scan-Ref

**The working document. The structural plan for what the codebase becomes.**

---

## Three Discoveries

### Discovery 1: The scan-ref fix completes the tantra cycle

The scan-ref fix (doc 16) was a parser bug fix. But what it revealed is
architectural: every tantra was constrained to an incomplete cycle. A
tantra could perceive (scan the graph) but could not reflect on its
perception (reference the scan output for further processing). This
forced fragmentation (one thought split across files) and monoliths
(orchestrators carrying state between fragments).

The fix completes the cycle: **perceive → reflect → act**
(sparsha → viveka → bandha) within a single file.

### Discovery 2: The math kosha is an unused library of 259 nodes

259 math-domain nodes. 32 have `eval` keys (directly fireable via
`apply-op`). 41 declare `kriya` (what operations they use). 35 declare
`siddha` (what properties they prove). 11 declare `pratipaksha`
(their inverse). 140 are structural (pure graph, no computation). The
pipeline fires only 13 of the 32 operations. 16 never fire.

The operations declared:

```
USED (13):     add sub mul div half double square sqrt reciprocal cos max min power
UNUSED (16):   abs neg floor ceil log exp sin tan factorial and or not ppr acos asin atan2
```

The algebraic structures:

```
ring    --[kriya]--> addition, multiplication     (count arithmetic IS ring arithmetic)
ring    --[siddha]--> distributivity              (per-entity then aggregate)
lattice --[kriya]--> join, meet                   (comparison IS lattice operation)
lattice --[sthita]--> partial-order               (lattice sits on ordering)
partial-order --[siddha]--> transitive            (A>B ∧ B>C → A>C)
fold --[swarupa] <-- sum, product                 (aggregation = iterated binary op)
graph-walk --[phala]--> path                      (traversal produces paths)
graph-walk --[swarupa] <-- BFS, DFS, PPR, shortest-path
monoid  --[abheda]--> op-class-monoid             (parser's own monoid = kosha's monoid)
```

The logic operations (fireable but never used):

```
conjunction  --[eval]--> and  (apply-op "and" [true, true] → true)
disjunction  --[eval]--> or   (apply-op "or" [false, true] → true)
negation     --[eval]--> neg  (apply-op "not" [true] → false)
```

The bridges:

```
ganana-setu:  add → addition, sub → subtraction, mul → multiplication
viveka-max  → abheda → max  → eval:max    ("heavier" → max operation)
viveka-min  → abheda → min  → eval:min    ("lighter" → min operation)
```

### Discovery 3: The graph IS the index — walk-in replaces scanning

The pipeline's bottleneck is `derive-step` (133ms per call, 257ms for
3 calls in derive-chain). It scans all 23 mantras checking if each
one's janya are bound. But the graph already knows:

```
walk-in "mass" "janya"     → [newton-second-law, momentum-mantra, KE-mantra, ...]
walk-in "velocity" "janya" → [angular-velocity-mantra, relative-velocity-mantra, ...]
intersection               → {KE-mantra, momentum-mantra, centripetal-force-mantra}
```

3 candidates instead of 23. Instant lookup instead of linear scan.

Similarly for dependency chains:

```
walk-in "force" "phala" → [newton-second-law-motion]
  newton-second-law → janya → [mass, acceleration]
    walk-in "acceleration" "phala" → [acceleration-mantra]
      acceleration-mantra → janya → [final-velocity, initial-velocity, time]
```

The derivation DAG is already in the graph. derive-chain's 3 hardcoded
steps should be a DAG walk from solve-for backward through phala → janya
edges. The depth comes from the graph, not from a constant.

And satya scores (PPR-computed at boot, declared as `ppr-mantra` with
`eval:ppr`) weight every node but no tantra reads `node-satya`. When
multiple mantras match, higher-satya mantras should fire first.

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
| Total (dvandva) | sum (swarupa → fold, abheda → addition) | sum | add (variadic) |
| Syllogism | modus-ponens → janya → implication | modus-ponens | (chain) |
| Transitive | partial-order → siddha → transitive | graph-walk | (closure) |
| Physics | momentum-mantra → math-op → multiplication | multiplication | mul |

Physics already works this way (mantras have `math-op:multiplication`,
execute-mantra reads it, calls `apply-op "mul" args`). The other types
just need the same wiring.

### The graph operations the pipeline should use

**For speed:**
- `walk-in concept "janya"` — which mantras need this concept? (replaces scanning)
- `walk-in concept "phala"` — which mantras produce this concept? (replaces DAG unroll)
- `node-satya concept` — priority when multiple mantras match

**For composition:**
- `sum.eval = "add", sum.arity = -1` — variadic aggregation via apply-op
- `product.eval = "mul", product.arity = -1` — variadic product
- `apply-op "add" [3, 4, 5]` → 12 (variadic already works)
- `distributivity → kriya → [multiplication, addition]` — per-entity op then aggregate

**For logic:**
- `apply-op "and" [check1, check2]` — composite anumana predicates
- `apply-op "or" [check1, check2]` — disjunctive questions
- `apply-op "not" [check]` — negation in inference

**For structure:**
- `partial-order → siddha → transitive` — transitive closure property
- `lattice → kriya → [join, meet]` — comparison as lattice operation
- `pratipaksha` on every operation — universal inversion

**For self-reference:**
- `ppr-mantra.eval = "ppr"` — the graph computes its own node weights
- `fixed-point → siddha → [svabhava, niralamba, avrti]` — convergence as self-evidence
- `visheshanam-ring → yukta → [satya, mithya, sankhya, ...]` — the predicate types of
  the question graph are declared as nodes in the kosha

### The Manipravalam principle realized

Writing `viveka-max --[abheda]--> max` in the kosha IS writing the
comparison capability. Writing `addition --[eval]--> add` IS writing
the count-addition capability. The pipeline reads these declarations
and fires. Adding a new question type = writing an .om file, not
modifying tantra code.

---

## Current Baseline

**67 passed / 31 xfailed / 0 failed** (v2 test suite, 98 tests total)

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

**Caveat found:** viveka detection currently reads WORDS in the sentence
("heavier" → shabda-anveshana → viveka-max), not swarupa edges in the
graph. Before dissolving the dispatch, avrti-refine (or a new pass)
must emit typed edges like `[heavier, swarupa, viveka]` into the graph
so the dispatcher has something to read. Currently `vishesa-instance`
emits `[heavier, vishesa, mass]` but not a swarupa edge to viveka.

**Action:** Dissolve. Question-type detection reads swarupa edges added
during avrti. Dispatch becomes thin wiring. avrti-refine and
emit-reasoning stay.

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

**Performance finding:** derive-step takes 133ms per call, scanning all
23 mantras. With `walk-in bound-concept "janya"` → intersection, it
would check 3 instead of 23. derive-chain runs derive-step 3 times
(257ms total) even when match-mantra already found the answer (27ms).
For KE: match-mantra succeeds directly, derive-chain is wasted work.

**Action:** Simplify derive-chain (3 steps → DAG walk via
`walk-in solve-for "phala"`). Check match-mantra FIRST, only derive
when needed. Use walk-in for candidate narrowing.

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
`partial-order --[siddha]--> transitive` — the property is declared.

**Action:** viveka-ganana uses kosha-driven max/min. anumana-viveka
uses scan-ref loop (unlimited depth).

### Group 7: GRAPH CONSTRUCTION (4 tantras, ~180 lines)
**Words in, graph out. The intake system.**

**Bug found:** emit-triples misclassifies kosha word aliases as rashi
labels when active concept exists. "many" (alias for count) becomes
mithya instead of satya when preceded by any satya word. Fix: check
`word-node` to distinguish aliases from labels.

**Trace confirmed:** `word="many"` → `shabda-anveshana` → `nd="count"`
→ emit-triples checks `word ≠ nd` → `"many" ≠ "count"` is true →
triggers `is-rashi-label` → emits `[many, mithya, many]` instead of
`[count, satya, count]`. And `word-node "many"` returns `"count"` —
the fix is verified.

**Deeper problem:** Even after fix, `8` in "8 birds" stays as
`asprista-sankhya` with no preceding satya to bind to. Step 1 alone
doesn't fix counting — it unblocks step 2.

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

**Trace finding:** "5 apples and 3 apples. how many total" already
produces `count1=5, count2=3, solve-for=count-total` via count-bandha.
The gap is not detection — it's firing. No mantra takes count1+count2
→ count-total. Count-chain must either emit directly or wire through
math-mantra varga mantras.

**Kosha path to operations:** `count → yukta → arithmetic → yukta →
equation → yukta → addition`. 3 hops. But `addition.eval = "add"` and
`subtraction.eval = "sub"` are already there.

**Action:** Rewrite count-chain using the math kosha's addition/subtraction.
Dissolve count-bandha.

---

## The Math Kosha Connection

### Four levels of unused math (259 nodes)

**Level 1 — Operations (32 with eval, 13 used, 16 unused):**

| Node | eval | arity | pratipaksha | Status |
|------|------|-------|-------------|--------|
| addition | add | 2 | subtraction | **Needed for count** |
| subtraction | sub | 2 | addition | **Needed for count** |
| multiplication | mul | 2 | division | Connected (physics) |
| division | div | 2 | multiplication | Connected (physics inverse) |
| max | max | 2 | min | **Needed for viveka** |
| min | min | 2 | max | **Needed for viveka** |
| sum | add | -1 | — | **Needed for dvandva** |
| product | mul | -1 | — | **Needed for dvandva** |
| abs | abs | 1 | — | Unused |
| neg | neg | 1 | — | Unused |
| floor | floor | 1 | — | Unused |
| ceil | ceil | 1 | — | Unused |
| log | log | 1 | exp | Unused |
| exp | exp | 1 | log | Unused |
| factorial | factorial | 1 | — | Unused |
| sine/cosine/tangent | sin/cos/tan | 1 | — | cosine used by work-expr only |
| conjunction | and | 2 | — | **Useful for composite anumana** |
| disjunction | or | 2 | — | **Useful for disjunctive questions** |
| negation | not | 1 | — | **Useful for negated inference** |
| ppr-mantra | ppr | — | — | **Computes satya; usable as heuristic** |

**Level 2 — Properties (35 with siddha, reasoning shortcuts):**

| Property | What it declares | Pipeline implication |
|----------|-----------------|---------------------|
| commutativity → drishthanta → addition | a+b = b+a | Operand order doesn't matter in count |
| pratipaksha: addition ↔ subtraction | They're inverses | If total and part known, find the other |
| associativity → drishthanta → addition | (a+b)+c = a+(b+c) | Can accumulate left-to-right |
| distributivity → kriya → mul, add | a(b+c) = ab+ac | Per-entity derive then sum (dvandva) |
| partial-order → siddha → transitive | A>B ∧ B>C → A>C | Transitive chain in krama-viveka |
| fixed-point → siddha → svabhava, avrti | Convergence = self-evidence | Fixpoint IS the kosha concept |

**Level 3 — Structures (41 with kriya, declare composition):**

| Structure | kriya declares | Pipeline implication |
|-----------|---------------|---------------------|
| ring → addition, multiplication | Count arithmetic is ring arithmetic | Ring laws apply |
| lattice → join, meet | Comparison is lattice operation | Transitive comparison = lattice join |
| dot-product → multiplication, addition | Pairwise multiply then sum | Same as distributivity |
| vector → addition, scalar-multiplication | Vector space operations | Future: displacement vectors |
| polynomial → addition, multiplication | Polynomial operations | Future: symbolic math |
| graph-walk → phala → path | Walk produces paths | Transitive closure IS graph-walk |

**Level 4 — Bridges:**

| Bridge | What it maps | Purpose |
|--------|-------------|---------|
| ganana-setu | add→addition, sub→subtraction, ... | Eval name ↔ math concept |
| viveka-max → abheda → max | Comparative word → operation | "heavier" → max operation |
| viveka-min → abheda → min | Comparative word → operation | "lighter" → min operation |
| kshaya → kriya → visarjana | Decay/loss → departure | Verb semantics → operation |
| fold → swarupa ← sum, product | Aggregation = iterated binary op | Variadic = fold of binary |

### What's already connected (template for the rest)

The physics path IS the pattern:

```
momentum-mantra → math-op:multiplication → apply-op "mul" [mass, velocity]
kinetic-energy-mantra → kriya:ke-expr → call-tantra ke-expr [mass, velocity]
invert-math → pratipaksha walk → find inverse operation
```

execute-mantra reads the kosha. invert-math reads the kosha.
The rest of the pipeline should do the same.

### Performance: what the graph index gives us

| Operation | Current (scan) | With walk-in | Speedup |
|-----------|---------------|-------------|---------|
| derive-step (1 call) | 133ms (scan 23 mantras) | ~18ms (walk-in 3 candidates) | ~7× |
| derive-chain (3 calls) | 257ms | ~54ms (or skip entirely) | ~5× |
| KE end-to-end | 338ms | ~81ms (skip derive-chain when match-mantra succeeds) | ~4× |
| mantra-select (filtered) | 23ms | 0ms (walk-in from solve-for phala) | instant |

The pipeline's slowest tests:
- `test_session_accumulate`: 0.69s (3 ask calls × derive-chain)
- `test_chain_force_via_suvat`: 0.58s (deep chain derivation)
- `test_chain_ke_via_suvat`: 0.53s (deep chain derivation)

All dominated by derive-step scanning. walk-in eliminates it.

### Fixpoint convergence

avrti-refine converges in 2-3 passes:
- Simple (1 entity, direct): 2 passes
- Multi-entity (viveka, dvandva): 3 passes
- The kosha declares: `fixed-point → siddha → [svabhava, niralamba, avrti]`
  (convergence IS self-evidence IS recurrence)

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

**Trace (live server, verified):**
```
word="many" → shabda-anveshana → nd="count"
word-node "many" → "count"
emit-triples: word ≠ nd → true → is-rashi-label → [many, mithya, many]
```

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

**Trace finding:** count-bandha already extracts count1/count2 for
"5 apples and 3 apples" pattern. The real gap is firing: no mantra
takes count1+count2 → count-total.

**Decision point:** Direct emission vs. mantra. Direct emission is
simpler. Mantra is more compositional (proof emission works for free).
Start with direct emission; add mantras if proof quality demands it.

Wire into avrti-refine: line 32, count-bandha → count-chain.

#### 1c. viveka-ganana → kosha-driven comparison (Group 6)

Currently: hardcoded reduce + gt/lt.

After: scan-ref collects per-entity values. Post-scan: look up
viveka-max.abheda → max → eval:max. Fire: `apply-op "max" [val1, val2]`.
Return the entity that wins.

Same mechanism as count-chain — read kosha, find operation, fire.

**Verified chain:** `viveka-max → abheda → max → eval:"max"` is a 1-hop
chain. `apply-op "max" [5, 8]` returns 8. The kosha path is clean.

#### 1d. derive-chain → DAG walk (Group 4)

3 manually unrolled steps → DAG walk via `walk-in solve-for "phala"`.

The dependency graph is already in the kosha:
```
force ← newton-second-law ← [mass, acceleration]
  acceleration ← acceleration-mantra ← [final-velocity, initial-velocity, time]
```

Walk backward from solve-for. At each node: check if janya are bound.
If not, recurse. The depth comes from the graph.

**Performance:** Also check match-mantra FIRST. If it succeeds (KE case),
skip derive-chain entirely. This alone saves 257ms on KE questions.

**Also:** Use `walk-in bound-concept "janya"` to narrow candidates
instead of scanning all 23 mantras. 3 candidates instead of 23.
133ms → ~18ms per step.

composition --[swarupa]--> parampara — the chain IS composition.

#### 1e. anumana-viveka simplification (Group 6)

4 copy-pasted levels → scan-ref loop over swarupa+varga edges.
graph-walk --[phala]--> path — the chain walk IS graph traversal.

### Phase 2: Dissolve the Monolith (Group 1)

anuvada-ganana → thin wiring that reads graph swarupa edges to
determine question type. The kosha declares the types:
- viveka-max --[swarupa]--> viveka → comparison path
- modus-ponens --[swarupa]--> inference → syllogism path
- count --[swarupa]--> sankhya → count path
- momentum-mantra --[varga]--> physics-mantra → physics path

**Caveat:** Currently viveka detection is word-based (scans subjects
for words resolving to viveka-max/viveka-min), not edge-based. Before
dissolving, a new avrti pass must emit swarupa edges from resolved
concepts. After: `[heavier, swarupa, viveka]` appears in the graph,
and the dispatcher reads it.

Dispatch reads the graph and routes. No hardcoded branches.

~20 lines after extraction. session-anuvada duplication vanishes.

### Phase 3: New Complete Thoughts

Each one follows the same pattern: detect via swarupa, find operation
via kosha, collect operands via scan-ref, fire via apply-op.

#### 3a. viveka-derive

**Thought:** For each entity, compute derived values, then compare.

"Which has more KE" = derive KE per entity (multiplication path),
then compare (max path). Uses both physics mantras AND viveka-max.

**Trace finding:** Currently "which has more KE" compares velocity
(picks wrong concept). Entity scoping is broken — both entities show
same values. This must be fixed first (entity-scoped derivation).

Unlocks: 2 xfails (viveka compute-then-compare) + 1 (proportional)

#### 3b. dvandva-ganana

**Thought:** For each entity, compute a value, then aggregate.

"Total momentum of two balls" = compute momentum per entity, then sum.
Uses: per-entity derive (same as viveka-derive) + `sum` (eval:add, arity:-1).

The kosha declares the composition:
- `distributivity → kriya → [multiplication, addition]` — per entity
  multiply, then add
- `sum → swarupa → fold` and `sum → abheda → addition` — aggregation IS
  fold of addition
- `apply-op "add" [p1, p2, p3]` → variadic sum (already works)

total-momentum is already a kosha concept with `swarupa: momentum,
sthita: samgraha (collection)`.

**Trace finding:** Entity scoping is broken — both entities show same
values. Same prerequisite as viveka-derive.

Unlocks: 3 xfails (dvandva per-entity)

#### 3c. krama-viveka

**Thought:** Given comparison edges, build transitive closure.

"A > B, B > C, who is greatest?" = scan comparison edges, collect as
pairs, compute closure.

The kosha declares the mechanism:
- `partial-order → siddha → [reflexive, antisymmetric, transitive]`
- `lattice → kriya → [join, meet]` and `lattice → sthita → partial-order`
- `graph-walk → phala → path` — the closure IS a graph walk

**Trace finding:** Currently falls into anumana path (wrong dispatch),
producing "does A inherit viveka-max?" The dispatcher doesn't recognize
comparison-from-sentence as viveka. This needs the swarupa-edge emission
from Phase 2.

Unlocks: 2 xfails (transitive reasoning)

#### 3d. anumana-ganana (syllogism + composite inference)

**Thought:** Given implication + instance, fire modus ponens.

"All birds have wings. 3 animals are birds. How many have wings?"
modus-ponens --[janya]--> implication. The implication is "bird → wings".
The instance is "3 are birds." The conclusion: those 3 have wings.

**Composite questions:** "Is X both Y and Z?" requires two anumana checks
combined with `apply-op "and" [result1, result2]`. The logic operations
(conjunction, disjunction, negation) exist and fire:
```
apply-op "and" [true, true]  → true
apply-op "or"  [false, true] → true
apply-op "not" [true]        → false
```

Negated inference: "Is whale NOT a fish?" = `apply-op "not" [anumana-check]`.

Unlocks: 1 xfail (logic_nyaya) + future composite questions

### Phase 4: Use the Graph Index (Performance)

After Phases 1-3 establish the kosha-reading pattern, optimize:

#### 4a. derive-step uses walk-in

Replace `mantra-select "" → filter by bound-concepts` with
`walk-in bound-concept "janya" → intersection`. O(bound × fanout)
instead of O(all-mantras × janya-per-mantra).

#### 4b. satya-ordered candidate priority

When multiple mantras match, sort by `node-satya`. Higher satya =
more central = more likely correct. This is the PPR algorithm
(declared as `ppr-mantra.eval = "ppr"`) serving as search heuristic.

#### 4c. match-before-derive guard

In anuvada-ganana (or its successor): run match-mantra first.
If it succeeds, skip derive-chain entirely. Saves 257ms on
direct-match questions (KE, momentum, etc.).

---

## What Does NOT Need Scan-Ref or Math Kosha

| Gate | Count | Blocked by |
|------|-------|-----------|
| sthita-viveka | 2 | Multi-slot entity assignment |
| inverse-math | 3 | bound-vals / invert-math path |
| kosha: missing concept | 2 | Add om nodes |
| parsing: natural | 2 | Grammar improvements |
| parsing: article | 1 | "the" before entity name |
| relative-velocity | 1 | Kosha concept missing |
| other:test_xfail | 9 | Mixed: various |

Total: ~20 xfails not addressable by this plan.

---

## Xfail Gates → Kosha Mechanism Mapping

| Gate | Tests | Mechanism |
|------|-------|-----------|
| arithmetic: plain count | 4 | fold(addition/subtraction) + walk-in from bound concepts |
| dvandva: per-entity | 3 | distributivity.kriya + fold(sum) |
| inverse-math | 3 | pratipaksha chain + walk-in phala |
| viveka: compute-then-compare | 2 | derive per entity → max/min (fold → max) |
| viveka: proportional | 1 | derive + ratio (division.eval) |
| sthita-viveka | 2 | walk-in concept janya → scope per entity |
| transitive | 2 | partial-order.siddha → transitive + graph-walk |
| logic_nyaya | 1 | conjunction/disjunction + anumana chain |
| kosha: missing concept | 2 | add om nodes |
| parsing | 3 | shabda-anveshana / emit-triples / sandhi |
| relative-velocity | 1 | add om node + mantra |

---

## Implementation Order

| Order | What | Mechanism | Xfails unlocked |
|-------|------|-----------|-----------------|
| 1 | Fix emit-triples alias bug | word-node check | 0 (unblocks count) |
| 2 | count-chain rewrite | kosha: addition/subtraction + fold | +4 |
| 3 | viveka-ganana → kosha max/min | kosha: max/min via abheda | 0 (quality) |
| 4 | derive-chain → DAG walk + match-first | walk-in phala + walk-in janya | 0 (performance: ~4× KE) |
| 5 | anumana-viveka → scan-ref loop | graph-walk phala → path | 0 (quality) |
| 6 | Dissolve anuvada-ganana | swarupa-driven dispatch + avrti emit | 0 (architecture) |
| 7 | viveka-derive | per-entity derive + max | +3 |
| 8 | dvandva-ganana | distributivity + fold(sum) | +3 |
| 9 | krama-viveka | partial-order → transitive + lattice join | +2 |
| 10 | anumana-ganana | modus-ponens + logic ops (and/or/not) | +1 |

**Best case: 13 xfails promoted, 31 → 18.**

**The real win:** one mechanism (read kosha → find operation → fire) for
all reasoning types. New capabilities emerge from .om declarations, not
from tantra modifications.

**Performance win:** walk-in replaces scanning in derive-step.
match-before-derive skips unnecessary chain derivation. Together: ~4×
speedup on direct-match questions, ~7× on derive-step per call.

---

## The Net Transformation

| | Before | After |
|---|---|---|
| Total tantras | 72 | ~76 (−2 dissolved, +6 new) |
| Math kosha nodes connected | 13 (physics only) | ~25 (+ count, viveka, logic, fold) |
| Graph ops used | 0 (ppr computed, never read) | satya heuristic + walk-in index |
| Logic ops used | 0 | and/or/not for composite inference |
| Monolith lines (anuvada-ganana) | 119 | ~20 (thin wiring) |
| Question type dispatch | Hardcoded branches | Kosha swarupa-driven |
| New question type cost | Modify orchestrator + write tantra | Write .om + write tantra |
| Tantra completeness | Fragments (scan without reflect) | Each tantra = full cycle |
| Hardcoded operations | gt/lt in viveka, lists in count | apply-op via kosha eval |
| derive-step time | 133ms (scan all 23) | ~18ms (walk-in 3 candidates) |
| KE end-to-end | 338ms | ~81ms (match-first, skip derive) |

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

### The graph computes its own weights

PPR runs at boot. Every node gets a satya score. `ppr-mantra` declares
`eval: ppr` — the algorithm IS a kosha node with the same structure as
`addition` or `max`. The system is self-referential: the graph's own
centrality measure could guide its own search. Higher-satya mantras
tried first. Higher-satya derivation paths preferred. The math kosha
contains the algorithm that evaluates the math kosha.

### Logic completes the inference system

`conjunction`, `disjunction`, `negation` exist and fire via `apply-op`.
They enable composite questions: "Is X both Y and Z?" = run two
inference checks, combine with `and`. "Is X not Y?" = run check,
negate with `not`. The logic operations turn single-predicate
anumana into a complete first-order inference engine.

### walk-in IS the type system

`walk-in "mass" "janya"` returns every mantra that needs mass as input.
This is not a query optimization — it's the type system running. The
janya edges ARE the type declarations. The walk IS the type checker.
The graph doesn't need a separate index because the edges ARE the index.

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

## Tools for Verification

All plan steps can be verified using the tools package:

```bash
# Trace any question through the full pipeline
python3 -m tools vy trace 'ball has mass 5 velocity 10. find kinetic energy'

# Walk kosha chains to verify connections
python3 -m tools vy walk 'viveka-max abheda'
python3 -m tools vy walk 'count yukta 3'
python3 -m tools vy walk 'partial-order siddha'

# Inspect any node: satya, shabda, edges
python3 -m tools vy inspect momentum
python3 -m tools vy inspect addition

# Check which mantras fire for a sentence
python3 -m tools vy mantras 'ball has mass 5 velocity 10. find kinetic energy'

# See all triples touching a concept
python3 -m tools vy triples mass

# Evaluate any tantra expression directly
python3 -m tools vy eval 'apply-op "max" [5, 8]'
python3 -m tools vy eval 'walk-in "mass" "janya"'
python3 -m tools vy eval 'node-satya "addition"'
python3 -m tools vy eval 'shabda "addition" "eval"'

# Static analysis: what's hardcoded that shouldn't be
python3 -m tools tantra lint

# Run tests
python3 -m tools test run
```

---

## What Has Changed

| Date | Session | Event |
|------|---------|-------|
| 2026-03-19 | 9 | Document created. Five scan-ref patterns identified. 22 xfails mapped across 4 tiers. |
| 2026-03-19 | 10 | **Document rewritten.** Architecture-driven plan. Ten natural groups. Four phases. Principle: every tantra = one complete cycle. |
| 2026-03-19 | 10 | **Math kosha discovery.** 83 mantra-layer math nodes unused. The pipeline hardcodes what the kosha declares. One mechanism (read kosha → find operation → fire) unifies count, viveka, syllogism, transitive, dvandva. Three levels: operations (eval:add), properties (commutativity, pratipaksha), structures (ring, lattice, graph-walk). ganana-setu bridges eval names to math concepts. invert-math is the existing template. emit-triples alias bug found (word ≠ node conflates aliases with labels). |
| 2026-03-19 | 11 | **Plan consolidated with tool-verified observations.** Discovery 3: the graph IS the index (walk-in replaces scanning; 133ms→18ms per derive-step). Full math inventory: 259 nodes, 32 eval, 41 kriya, 35 siddha, 16 unused ops. Logic ops (and/or/not) fire via apply-op — enable composite inference. PPR computes satya but no tantra reads node-satya. Fixpoint converges in 2-3 passes. Distributivity.kriya declares the dvandva pattern. Fold declares variadic aggregation. Partial-order.siddha declares transitivity. derive-chain bottleneck traced: runs even when match-mantra succeeds (257ms wasted on KE). Entity scoping broken for multi-entity questions (prerequisite for steps 7-8). All traces verified via `vy trace`, `vy walk`, `vy inspect`, `vy mantras`. Phase renumbered: Phase 3 merged (sandhi merge deferred), old Phase 4 → Phase 3. Phase 4 added for performance (walk-in, satya heuristic, match-before-derive). Step 10 added: anumana-ganana with logic ops. Xfail gate mapping added. Tools verification section added. |
