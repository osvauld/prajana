# 17c — Implementation Plan

**The actionable steps. What to do, in what order, verified against what.**

Parent: [17-scan-ref-patterns.md](17-scan-ref-patterns.md)
Reference: [17a-discoveries.md](17a-discoveries.md), [17b-algebraic-types.md](17b-algebraic-types.md)

---

## Baseline

**73 passed / 31 xfailed / 0 failed** (v2 test suite, 104 tests total, session 17)

---

## The Unifying Principle

**eval/apply-op is the single mechanism.** 32 kosha nodes declare `eval:` fields.
`apply-op` fires all of them. The pipeline uses this in exactly ONE place today
(execute-mantra line 27, for physics). Everything else hardcodes its operations.

Every question type should follow the same structure:

1. **Build** the graph from the question (graph construction)
2. **Detect** the question type by reading `swarupa` edges from concepts
3. **Find** the operation by following abheda/kriya/yukta edges to an operation node
4. **Read** the operation's `eval` shabda to get the primitive
5. **Collect** the operands (scan-ref: perceive, then post-scan collect)
6. **Fire** via `apply-op eval operands`
7. **Emit** the result back into the graph

### Verified in session 14 — all operations fire today:

```
apply-op "sub" [10, 3]        → 7       (count subtraction)
apply-op "add" [10, 3]        → 13      (count addition)
apply-op "add" [1, 2, 3, 4]   → 10      (variadic fold)
apply-op "max" [5, 8]         → 8       (viveka comparison)
apply-op "min" [5, 8]         → 5       (viveka comparison)
apply-op "and" [true, true]   → True    (logical conjunction)
apply-op "and" [true, false]  → False   (logical conjunction)
apply-op "or"  [true, false]  → True    (logical disjunction)
apply-op "not" [true]         → False   (logical negation)
apply-op "mul" [0.5, 5, 100]  → 250     (physics — already working)
reduce vals 0 (fn a v -> apply-op "max" [a, v])  → variadic max
```

### Two layers of readiness:

**Layer 1 — kosha words resolve (arithmetic, comparison):**
Walk kosha edges → read `eval` → fire `apply-op`. The operations work.
The gap is graph construction: aliases must resolve (Step 1, DONE),
numbers must bind to concepts (Step 1b), event verbs must resolve (Step 1c).

**Layer 2 — question provides premises (logical composition):**
"all birds can fly. is a sparrow a bird?" — the question IS the knowledge base.
`apply-op "and"/"or"/"not"` compose truth values from graph queries.
The gap is deeper: the pipeline must build graph edges from question-provided
premises ("all X are Y" → `[X, swarupa, Y]`), even when X and Y are not in
the kosha. Currently unknown words go mithya and no edges are built.

### Operation routing table:

| Question type | Kosha path | eval | Status |
|---------------|------------|------|--------|
| Physics | mantra → math-op → eval | mul, div, ... | **Working** (execute-mantra) |
| Count addition | event verb → vriddhi → addition | add | Blocked (1b, 1c) |
| Count subtraction | event verb → kshaya → subtraction | sub | Blocked (1b, 1c) |
| Comparison (more) | viveka-max → abheda → max | max | **Unblocked** (Step 1 done) |
| Comparison (less) | viveka-min → abheda → min | min | **Unblocked** (Step 1 done) |
| Total (dvandva) | sum → abheda → addition | add (variadic) | Blocked (entity scoping) |
| Logical AND | conjunction | and | Blocked (premise graph construction) |
| Logical OR | disjunction | or | Blocked (premise graph construction) |
| Negation | negation | not | Blocked (premise graph construction) |
| Syllogism | modus-ponens → janya → implication | (chain) | Blocked (premise graph) |
| Transitive | partial-order → siddha → transitive | (closure) | Blocked (step 6) |

---

## Phase 1: Connect the Math Kosha

### Step 1: Fix emit-triples alias bug — DONE (session 14)

**File:** `brahman/yantra/sankhya/emit-triples.tantra3` line 33-35
**Bug:** `is-rashi-label` check used `neq word (to-string nd)`. Kosha word aliases
also have word != node. "many" (-> count) became mithya instead of satya.
**Fix:** Two-condition check: `(neq word (to-string nd))` catches direct matches,
`(neq (to-string (word-node word)) (to-string nd))` catches kosha aliases.
A word is a rashi-label only if BOTH conditions pass — i.e., word text differs
from node name AND word-node doesn't resolve to the same node.
**Result:** 67 passed / 31 xfailed / 0 failed (no regressions).
- "5 cats. how many total" → `[count, satya, count]` (was `[many, mithya, many]`)
- "8 birds. 3 flew away. how many remaining" → `[count, satya, count]` for both aliases
- "ball A has mass 5. ball B has mass 8. which is heavier" → `[viveka-max, satya, viveka-max]`
  AND produces correct answer: "ball-B is viveka-max than A"
- Physics path (mass, velocity, energy) unaffected — words where word==nd short-circuit.

**First fix attempt failed:** `(not (exists (word-node word)))` broke physics —
words like "mass" resolve via shabda-anveshana (nd="mass") but `word-node "mass"`
returns None (physics words aren't in the word index). 13 test failures.
The two-condition fix handles both cases correctly.

### Step 1b: sankhya-bandha number-before-noun fix — DEFERRED

**File:** `brahman/yantra/sankhya/sankhya-bandha.tantra3`
**Bug:** `last-active` state only binds numbers to preceding concepts.
"10 birds" -> 10 stays as asprista-sankhya (orphaned). "birds 10" works.
**Why deferred (session 17):** Count sentences work without this. Numbers stay
loose as asprista-sankhya and grade-sparsha's two-loose path handles them correctly.
The three-sentence chain fails because count-bandha only handles 2 operands, NOT
because of number-before-noun. Attempting the fix revealed structural complexity:
"2 more came" should NOT bind 2 to viveka-max — "more" is a modifier, not the
counted noun. The binding decision requires understanding containers ("birds on a
tree") and event structure, which is deeper than a simple retroactive bind.
**Only needed for:** unnatural physics inputs like "10 mass" (nobody writes this).
**Verify:** `python3 -m tools vy trace '10 birds'` — 10 stays loose (correct for count).

### Step 1c: common-sense event shabda table — DONE (session 17)

**New files:**
- `brahman/kosha/common-sense/processes/common-sense-events.shabda` — 32 event verbs
- `brahman/kosha/common-sense/processes/common-sense-events.om` — links shabda template

**What was done:**
32 event verbs mapped to kshaya (decrease) or vriddhi (increase):
- kshaya (18 verbs): flew, away, left, died, lost, ate, eaten, used, spent, broke,
  broken, gone, sold, dropped, gave, removed, fell, disappeared
- vriddhi (14 verbs): came, arrived, found, added, bought, received, gained, got,
  joined, returned, appeared, grew, hatched, born

**vriddhi-kriya / kshaya-kriya edges added to ALL mathematical operations:**
- addition: + vriddhi-kriya (was missing — the symmetric counterpart to subtraction's kshaya-kriya)
- multiplication: + vriddhi-kriya (amplification)
- power: + vriddhi-kriya (exponential growth)
- exponential: + vriddhi-kriya (growth)
- square: + vriddhi-kriya (amplification)
- double: + vriddhi-kriya (doubling)
- division: + kshaya-kriya (reduction)
- square-root: + kshaya-kriya (reduction)
- half: + kshaya-kriya (halving)
- (subtraction already had kshaya-kriya; logarithm already had vriddhi-kshaya-kriya)

**Kosha chain now verified end-to-end:**
```
shabda "common-sense-events" "flew" → "kshaya"
walk-in "kshaya" "kriya" → [..., subtraction, division, square-root, half, ...]
∩ walk-in "arithmetic" "kriya" → [subtraction]
shabda "subtraction" "eval" → "sub"
apply-op "sub" [10, 3] → 7

shabda "common-sense-events" "came" → "vriddhi"
walk-in "vriddhi" "kriya" → [..., addition, multiplication, power, ...]
∩ walk-in "arithmetic" "kriya" → [addition]
shabda "addition" "eval" → "add"
apply-op "add" [7, 2] → 9
```

**Result:** 73/31/0 — no regressions. Step 2 (count-chain) is now unblocked.

### Step 1e: BQG last-satya viraam reset — DONE (session 17)

**File:** `brahman/yantra/pipeline/build-question-graph.tantra3` line 22
**Bug:** `last-satya` was computed by scanning the ENTIRE accumulated graph
for the last satya subject. It never reset at viraam boundaries. `tree` from
sentence 1 leaked into sentence 3, causing `[tree, sankhya, 2.]` when "2 more"
followed a viraam after a sentence containing `tree`.
**Fix:** Added viraam reset: `cond (eq (nth t 1) "viraam") "" otherwise ...`
in the last-satya reduce. Now last-satya resets to "" at every viraam triple.
**Verify:** `python3 -m tools vy trace '10 birds sat on a tree. 2 more came.'`
— tree no longer gets sankhya 2. BQG output is clean.

### Step 1d: grade-sparsha sentence partitioning — PARTLY DONE (session 16)

**Mechanism:** The question graph IS a graded ring (`proof-graph --[sthita]--> graded-ring`).
Sentences are grades. Viraam (period and comma) is the additive identity
(`viraam --[swarupa]--> shunya`). Per-grade refinement enforces filtration closure
(`filtration --[siddha]--> closure`).

**Kosha bridge:** Added `grade-boundary: viraam` to `graded-ring.om` shabda.
Connects the abstract `grade` node to the concrete NLP signal (`viraam` edge).
Without this, grade-sparsha would need to hardcode "viraam" — the bridge makes it kosha-driven.

**New tantra:** `brahman/yantra/avrti/grade-sparsha.tantra3`
- Reads `boundary-edge = shabda "graded-ring" "grade-boundary"` → "viraam"
- Splits flat graph into grade sublists using reduce with [completed, current] state
- Maps `fixpoint avrti-refine` over each grade (sentence-local closure)
- Flattens refined grades back to flat graph
- Runs `count-bandha` on merged graph (cross-grade count arithmetic)

**Wire in anuvada-ganana:** `refined = grade-sparsha asserted` replaces
`refined = fixpoint asserted (fn g -> avrti-refine g)`.

**count-bandha n1/n2 ordering fix (session 16):**
When one-loose + one-bound (typical cross-sentence case):
- OLD: n1=loose (change), n2=bound (initial) → subtraction gave wrong sign
- NEW: n1=bound (initial, earlier sentence), n2=loose (change, later sentence)
- For "10 birds. 3 flew away" → n1=10, n2=3 → 10-3=7 ✓
- Two-loose case unchanged: order preserved by sentence order (10 before 3)

**Key insight:** For pure count sentences where numbers appear BEFORE nouns
("10 birds"), the numbers stay loose (1b not fixed yet). This is actually CORRECT
for grade-sparsha: both numbers end up loose, two-loose path fires, sentence order
preserves n1=initial, n2=change. grade-sparsha + two-loose path = working count
WITHOUT needing 1b for the basic test cases.

**Status:** DONE. Files changed:
- `brahman/kosha/math/algebra/structures/graded-ring.om` — grade-boundary: viraam
- `brahman/yantra/avrti/grade-sparsha.tantra3` — NEW
- `brahman/yantra/sankhya/count-bandha.tantra3` — n1/n2 swap for one-loose
- `brahman/yantra/pipeline/anuvada-ganana.tantra3` — grade-sparsha wired
- `brahman/yantra/sankhya/sankhya-bandha.tantra3` — viraam reset (session 15)
**Result:** 73/31/0. +6 xfails promoted (more than expected):
- test_count_addition, test_count_subtraction (arithmetic gate)
- test_count_subtraction_comma_boundary, test_count_number_before_noun,
  test_count_named_entity_total, test_count_gave_away (sentence_scope gate)
Remaining sentence_scope xfails: test_count_three_sentence_chain, test_viveka_after_count.

### Step 2: count-chain rewrite — DONE (session 18)

**Dissolved:** `count-bandha` (105 lines, 18 hardcoded word lists).
**New:** `count-chain` (~90 lines) + `emit-count` (~80 lines).
**Parser fixes:** variadic `concat` must wrap in parens inside lambda `let` bindings.
Flat cond chains — nested `(cond ...)` as branch body triggers parse_expr:empty.

**What was done:**
- count-chain fold over grades with per-grade operation detection via kosha
- Bigram event verb detection: "got-off", "picked-up" etc. in common-sense-events.shabda
- emit-count tantra: walks grades + count-steps + shabda bridge to produce natural output
- emit-reasoning routes to emit-count when `derived-by count-chain` detected
- anuvada-ganana reads count-total/count-remaining sankhya from grade-sparsha output
- dvandva boundary: BQG emits `[and, dvandva, dvandva]` triple on conj-and
- sankhya-bandha and grade-sparsha reset on dvandva boundary

**Result:** 78 passed / 39 xfailed / 0 failed. +5 promoted from xfail.
New xfail gates added: dvandva_count, entity_scope, multi_question, multiplication,
count_compare, long_chain.

**Emit output (before → after):**
```
before: we seek: count-total. we know: count-chain ( → result). we find: count-total = 7
after:  we have: 10 bird sat on tree. we know: 3 minus (10 → 7). we find: 7 birds
```

### Step 2.5: Karaka + dravya recognition — NEXT (IMMEDIATE)

**Why this is next:** The count pipeline works for known kosha words (bird, cat, dog)
and accidentally for unknown words (apples, cookies) because loose asprista-sankhya
gets picked up per grade. But the graph doesn't actually know that "apples" is a
substance (dravya) that bears a count (sankhya-guna). The process is not aligned
with the bridge — emit-reasoning cannot produce correct sentences without knowing
what words are nouns, verbs, or locations.

**The ontological mapping (all concepts already exist in sangati):**

| Vaisheshika | Sangati equivalent | Status |
|---|---|---|
| **dravya** (substance) | `rashi` — quantity-bearing instance | EXISTS: `rashi --[yukta]--> sankhya, matra` |
| **guna** (quality) | `guna` → `matra-guna` + `sankhya` | EXISTS (thin but present) |
| **karma** (action) | `karma` | EXISTS (rich) |
| **samanya** (universal) | `varga` mechanism | EXISTS (boot-time varga-inheritance) |
| **vishesha** (particular) | `vishesa` edge type | EXISTS (IS the edge system) |
| **samavaya** (inherence) | `shashthi-vibhakti` (genitive) | EXISTS (ownership = inherence) |

**The karaka mapping (all map to existing sangati roots):**

| Karaka | Vibhakti | Sangati root | Connection |
|---|---|---|---|
| **karta** (agent) | prathama | kriya | `kriya --[siddha]--> karma` (agent proven through action) |
| **karma** (object) | dvitiya | phala | `phala --[janya]--> kriya` (object arises from action) |
| **karana** (instrument) | tritiya | yukta | action-with-instrument |
| **sampradana** (recipient) | chaturthi | phala-target | where the fruit arrives |
| **apadana** (source) | panchami | kshaya | `kshaya` = point of departure |
| **adhikarana** (locus) | saptami | sthiti + kshetra | `sthiti` = state, `kshetra` = field |

**What needs to be built (5 pieces):**

**2.5a — Locative prepositions (prep-on, prep-in):**
Add `prep-on` and `prep-in` to `bhasha/english/grammar/`, connecting to
`saptami-vibhakti`. "on a table", "in a pond" → adhikarana (locus).
This tells BQG that the word after "on"/"in" is a location, not a counted entity.

**2.5b — Auxiliary verb nodes (was, were, is, are as tense carriers):**
Add `aux-was`, `aux-were` to `bhasha/english/grammar/`, connecting to
`bhuta-kaala` (past tense). "were eaten" = bhuta-kaala + karmani-prayoga.
Tells BQG the next word is a verb form, not a noun.

**2.5c — Verb morphology (kta-pratyaya = -ed, shatr-pratyaya = -ing):**
Extend the morphology layer: strip -ed suffix, check if stem or word is in
common-sense-events. "eaten" → kta-pratyaya → karma (action, not dravya).
"running" → shatr-pratyaya → karma. This is the guard that prevents
"3 eaten" from promoting "eaten" to satya.

**2.5d — Dravya promotion rule:**
In `emit-triples`: when an unknown word follows a number AND:
- word is NOT in common-sense-events (not a known verb)
- word does NOT resolve as kta/shatr-pratyaya (not a verb form)
- previous triple is NOT a locative preposition (on/in/at)
→ promote from mithya to satya. The word is a dravya (rashi bearing sankhya-guna).

**2.5e — Karaka nodes in sangati:**
Add `sangati/grammar/karaka/` directory with 6 karaka nodes.
Connect each karaka to its vibhakti and its sangati root:
`karta --[yukta]--> prathama-vibhakti`, `karta --[swarupa]--> kriya`.
`adhikarana --[yukta]--> saptami-vibhakti`, `adhikarana --[swarupa]--> sthiti`.
This completes the Paninian grammar layer in the graph.

**Dependency order:** 2.5a → 2.5b → 2.5c → 2.5d (each adds a guard for dravya).
2.5e can be done in parallel (ontological wiring, no pipeline change).

**Xfails unlocked:** 0 directly (infrastructure). But makes entity_scope, multi_question,
and future sentence understanding structurally correct.

**Verify:** After 2.5d:
```
python3 -m tools vy eval 'build-question-graph "there are 10 apples on a table"'
  → [10, asprista-sankhya, 10.] [apples, satya, apples] [on, saptami-vibhakti, ...] [table, ...]
python3 -m tools vy eval 'build-question-graph "3 were eaten"'
  → [3, asprista-sankhya, 3.] [were, bhuta-kaala, ...] [eaten, mithya, eaten] (NOT satya)
python3 -m tools test run  → 78 passed (no regressions)
```

### Step 2 (original): count-chain rewrite — DONE (session 18)

**Dissolves:** `count-bandha` (105 lines, 18 hardcoded subtraction words)
**Rewrites:** `count-chain` (~50 lines)
**Prerequisites:** 1c (event verbs) **DONE**. 1e (BQG viraam reset) **DONE**.
**Mechanism:** Fold over grades (sentences) with per-grade operation detection.
Each grade's mithya words are checked against `shabda "common-sense-events" word`
to get kshaya/vriddhi direction. Direction walks to arithmetic operation via
`walk-in direction "kriya" ∩ walk-in "arithmetic" "kriya"`. Operation's eval
fires via apply-op.

**Kosha chain (verified live):**
```
per sentence: scan mithya words against shabda "common-sense-events"
  "flew" → kshaya, "came" → vriddhi, no match → default (add for total, sub for remaining)
kshaya → walk-in "kshaya" "kriya" ∩ arithmetic → subtraction → eval:sub
vriddhi → walk-in "vriddhi" "kriya" ∩ arithmetic → addition → eval:add
fold: reduce numbers initial-value (fn acc n → apply-op op [acc, n])
```

**Algebraic backing (17b):** addition is a monoid (closure, associativity, identity=0).
fold by addition is guaranteed well-defined. `monoid --[drishthanta]--> addition`.

**Wire:** grade-sparsha line 55, count-bandha → count-chain.
**Xfails unlocked:** +2 (test_count_three_sentence_chain, test_viveka_after_count)
**Verify:** `python3 -m tools test run` — 75 passed / 29 xfailed expected.
Also: `python3 -m tools vy trace '10 birds sat on a tree. 3 flew away. 2 more came. how many birds are on the tree now'`
should show 10 - 3 + 2 = 9.

### Step 3: viveka-ganana -> kosha max/min — DONE (session 15)

**Was:** Hardcoded reduce + gt/lt comparison.
**Fix:** Read `eval:` from the `direction` node (`shabda direction "eval"` → "max"/"min").
Read opposite via `walk direction "pratipaksha"` → `shabda opp "eval"` → "min"/"max".
Replace gt/lt with `apply-op op-eval [kv-val, best-val]` (winner) and
`apply-op opp-eval [kv-val, worst-val]` (loser).
**Algebraic backing (17b):** max is the JOIN of a lattice over partial-order.
`lattice --[kriya]--> join, meet`. `viveka-max --[abheda]--> max`.
**Result:** 67/31/0 — no regressions. Viveka trace confirmed correct.
**Xfails unlocked:** 0 (architecture improvement, same results).

### Step 2a: Set operation runtime primitives

**Gap (session 17):** The kosha declares set-union, set-intersection, set-difference,
set-complement, subset — but their eval values are wrong placeholders (div, ceil, sin,
square) and no runtime primitives exist. Six tantras use set operations inline
(member, filter, reduce-with-member) without referencing the kosha.

**What's needed:**
1. Add runtime primitives: set-member, set-subset, set-intersect, set-union, set-diff
2. Fix eval shabda on kosha nodes:
   - set-union: eval → set-union (was: div)
   - set-intersection: eval → set-intersect (was: None)
   - set-difference: eval → set-diff (was: ceil)
   - set-complement: eval → set-complement (was: sin)
   - subset: eval → set-subset (was: square)

**What it unlocks in existing tantras:**
| Tantra | Current inline | Becomes |
|--------|---------------|---------|
| forward-match | `reduce janya true (fn a r → and a (member r bcs))` | `apply-op "set-subset" [janya, bcs]` |
| derive-step | same subset check | `apply-op "set-subset" [janya, bcs]` |
| mantra-select | `member solve-for phala` | `apply-op "set-member" [sf, phala]` |
| scope-vps | reduce with dedup | `apply-op "set-union" [scoped, flat]` |
| count-bandha | `member w mithya-words` × hardcoded lists | replaced by shabda lookup (1c) |

**Connection to algebraic hierarchy:**
- lattice --[yukta]--> set-union, set-intersection (join/meet at set level)
- set-difference --[abheda]--> kshaya (set removal IS decrease)
- group --[swarupa]--> set (group IS a set with structure)

**Xfails unlocked:** 0 (infrastructure improvement, same results)
**Verify:** `python3 -m tools vy eval 'apply-op "set-subset" [["mass", "velocity"], ["mass", "velocity", "energy"]]'` → true

### Step 4: derive-chain -> DAG walk + match-first

**Currently:** 3 manually unrolled copy-paste steps (80 refs, 79 lines).
**After:** DAG walk via `walk-in solve-for "phala"`. Depth from graph, not constant.
**Also:** match-mantra FIRST. If it succeeds (KE case), skip derive-chain entirely.
**Also:** `walk-in bound-concept "janya"` to narrow candidates (3 instead of 23).
**Performance:** KE end-to-end 338ms -> ~81ms. derive-step 133ms -> ~18ms.
**Xfails unlocked:** 0 (performance + architecture).
**Verify:** `python3 -m tools test run` -- no regressions; slow tests should be faster.

### Step 5: anumana-viveka -> scan-ref loop

**Currently:** 4 copy-pasted level walks (6 refs with step numbers).
**After:** scan-ref loop over swarupa + varga edges. Unlimited depth.
**Kosha path:** `graph-walk --[phala]--> path` -- chain walking IS graph traversal.
**Xfails unlocked:** 0 (quality: handles deeper inheritance chains).
**Verify:** `python3 -m tools vy eval 'anumana-viveka-yukta [] "cat" "breathing"'` -> "yes"

---

## Phase 2: Dissolve the Monolith

### Step 6: Dissolve anuvada-ganana

**Currently:** 119-line dispatch table with hardcoded question-type detection.
**After:** Thin wiring (~20 lines) that reads swarupa edges from the graph.
**Prerequisite:** avrti-refine (or a new pass) must emit typed edges:
`[heavier, swarupa, viveka]` into the graph so the dispatcher has something to read.
Currently `vishesa-instance` emits `[heavier, vishesa, mass]` but not a swarupa
edge to viveka.

**Kosha declares the types:**
- `viveka-max --[swarupa]--> viveka` -> comparison path
- `modus-ponens --[swarupa]--> inference` -> syllogism path
- `count --[swarupa]--> sankhya` -> count path
- `momentum-mantra --[varga]--> physics-mantra` -> physics path

**session-anuvada duplication vanishes.**
**Xfails unlocked:** 0 (architecture).
**Verify:** Full test suite -- no regressions.

---

## Phase 3: New Complete Thoughts

Each follows: detect via swarupa, find operation via kosha, collect operands
via scan-ref, fire via apply-op.

### Step 7: viveka-derive (per-entity derive + compare)

"Which has more KE" = derive KE per entity, then compare via max.
**Prerequisite:** Entity scoping fix (both entities currently show same values).
**Algebraic backing (17b):** The composition is: ring kriya (multiplication in KE formula)
per entity, then lattice join (max) to compare. `ring --[siddha]--> distributivity`
validates the per-entity-then-aggregate pattern.
**Xfails unlocked:** +3 (viveka: compute-then-compare + proportional)

### Step 8: dvandva-ganana (per-entity derive + aggregate)

"Total momentum of two balls" = compute per entity, then sum.
**Kosha path:** `distributivity -> kriya -> [multiplication, addition]` = dvandva.
`sum -> swarupa -> fold`, `sum -> abheda -> addition`, `sum eval:add arity:-1`.
**Algebraic backing (17b):** Monoid closure guarantees fold is well-defined.
Ring distributivity guarantees compute-then-add is valid.
**Prerequisite:** Same entity scoping fix as step 7.
**Xfails unlocked:** +3 (dvandva: per-entity)

### Step 9: krama-viveka (transitive comparison)

"A > B, B > C, who is greatest?" = scan comparison edges, compute closure.
**Kosha path:** `partial-order -> siddha -> transitive`. `lattice -> kriya -> join`.
**Algebraic backing (17b):** Transitivity is an established property (siddha) of
partial-order. The pipeline reads this property to know A>C without computing.
**Prerequisite:** swarupa-edge emission from Phase 2 (step 6).
**Xfails unlocked:** +2 (transitive reasoning)

### Step 10: anumana-ganana (syllogism + composite inference)

"All birds have wings. 3 animals are birds. How many have wings?"
`modus-ponens --[janya]--> implication`. Fire the implication.
**Composite:** "Is X both Y and Z?" = two checks + `apply-op "and" [r1, r2]`.
**Negation:** "Is X not Y?" = check + `apply-op "not" [result]`.
**Xfails unlocked:** +1 (logic_nyaya)

---

## Phase 4: Use the Graph Index (Performance)

### Step 4a: derive-step uses walk-in

Replace `mantra-select "" -> filter by bound-concepts` with
`walk-in bound-concept "janya" -> intersection`.
O(bound x fanout) instead of O(all-mantras x janya-per-mantra).

### Step 4b: satya-ordered candidate priority

When multiple mantras match, sort by `node-satya`. Higher satya =
more central = more likely correct. PPR as search heuristic.

### Step 4c: match-before-derive guard

In anuvada-ganana: run match-mantra first. If it succeeds, skip
derive-chain entirely. Saves 257ms on direct-match questions.

---

## Xfail Gates -> Kosha Mechanism Mapping

**Total: 37 xfails** (31 original + 6 sentence_scope added session 16)

| Gate | Tests | Mechanism | Step |
|------|-------|-----------|------|
| sentence_scope | 6 | grade-sparsha (graded-ring partitioning) | 1d |
| arithmetic: plain count | 4 | grade-sparsha (two-loose path) + count dispatch | 1d + 2 |
| dvandva: per-entity | 3 | distributivity.kriya + fold(sum) | 8 |
| inverse-math | 3 | pratipaksha chain + walk-in phala | 4 |
| viveka: compute-then-compare | 2 | derive per entity -> max/min | 7 |
| sthita-viveka | 2 | walk-in concept janya -> scope per entity | 7-8 |
| transitive | 2 | partial-order.siddha -> transitive | 9 |
| viveka: proportional | 1 | derive + ratio (division.eval) | 7 |
| logic_nyaya | 1 | conjunction/disjunction + anumana chain | 10 |
| kosha: missing concept | 2 | add om nodes | -- |
| parsing | 3 | shabda-anveshana / emit-triples / sandhi | 1 |
| relative-velocity | 1 | add om node + mantra | -- |

**Not addressable by this plan:** ~20 xfails (sthita-viveka partial,
inverse-math, kosha missing, parsing natural, article handling, etc.)

---

## Known Bugs (Fix Before Steps)

### emit-triples alias bug (Step 1) — FIXED (session 14)

**Was:** `is-rashi-label` at line 34 used `neq word (to-string nd)`. 85 words affected.
**Fixed:** Two-condition check: word text AND word-node resolution. See Step 1 above.
**Verified:** 67/31/0, all three trace cases pass. Steps 3, 7, 9 unblocked.

### sankhya-bandha number-before-noun (Step 1b)

In "10 birds", number precedes concept. sankhya-bandha tracks last-active
left-to-right, so 10 has no preceding satya and stays as asprista-sankhya.
Verified: "birds 10" binds correctly, "10 birds" does not.
This is the dominant English number pattern. Must be fixed for count-chain.
**Note:** The original plan assumed count-chain would handle this, but
count-chain needs the numbers already bound to concepts.

### Event verb gap (Step 1c)

12 common event verbs tested via `word-node`: all return None.
The kosha has `subtraction --[kriya]--> kshaya` and `growth --[abheda]--> vriddhi`
but no word declarations map verbs to these nodes.
A `.shabda` template file for common-sense events is needed.

---

## Implementation Order Summary

**Baseline (session 16):** 73 passed / 31 xfailed / 0 failed (104 tests)
**After session 17:** 73 passed / 31 xfailed / 0 failed (kosha enrichment, no xfail change)

| Step | What | Xfails promoted | Cumulative (pass/xfail) | Status |
|------|------|-----------------|-------------------------|--------|
| 1 | Fix emit-triples alias bug | 0 | 67/37 | **DONE** (session 14) |
| 3 | viveka-ganana → apply-op max/min | 0 | 67/37 | **DONE** (session 15) |
| 1d | grade-sparsha (graded-ring sentence partitioning) | +6 | 73/31 | **DONE** (session 16) |
| 1c | Common-sense event shabda table + vriddhi/kshaya | 0 | 73/31 | **DONE** (session 17) |
| 1e | BQG last-satya viraam reset | 0 | 73/31 | **DONE** (session 17) |
| **2** | **count-chain rewrite via kosha fold** | **+2** | **75/29** | **NEXT** |
| 2a | Set operation runtime primitives | 0 | 75/29 | Pending (infrastructure) |
| 4 | derive-chain → DAG walk + match-first | 0 | 75/29 | Pending |
| 5 | anumana-viveka → scan-ref loop | 0 | 75/29 | Pending |
| 6 | Dissolve anuvada-ganana | 0 | 75/29 | Pending |
| 7 | viveka-derive (per-entity + max) | +3 | 78/26 | Pending |
| 8 | dvandva-ganana (distributivity + fold) | +3 | 81/23 | Pending |
| 9 | krama-viveka (transitive) | +2 | 83/21 | Pending |
| 10 | anumana-ganana (logical ops + premise graph) | +1 | 84/20 | Pending |
| 1b | sankhya-bandha number-before-noun | 0 | -- | **DEFERRED** |

**Best case: 17 xfails promoted, 31 → 14.**

**Reordering rationale (session 17):**

Step 1b deferred — session 17 investigation revealed it blocks nothing. Count
sentences work with loose numbers via grade-sparsha's two-loose path. The
three-sentence chain fails because count-bandha handles only 2 operands, not
because of number-before-noun. Attempting the fix exposed structural complexity:
"2 more came" must NOT bind 2 to viveka-max (alias for "more"). The binding
decision requires container semantics ("birds on a tree"), which is deeper work.

Step 1c moved before Step 2 and completed — the event verb shabda table is the
real prerequisite for count-chain. vriddhi/kshaya kriya edges added to all
mathematical operations, completing the direction classification that was
partially declared (subtraction→kshaya existed, addition→vriddhi did not).

Step 2a (set operations) added as new infrastructure step. Session 17 analysis
found 6 tantras using set operations inline (member, filter, reduce-with-member)
without referencing the kosha's set operation nodes. The kosha has wrong eval
values on set-union/set-intersection/set-difference. Runtime primitives needed.

Step 10 still has two prerequisites: (1) eval/apply-op for and/or/not (already
working), and (2) premise graph construction — the pipeline must build edges
from question-provided facts ("all X are Y" → `[X, swarupa, Y]`) even when
X and Y are unknown words. Currently unknown words go mithya.

---

## The Net Transformation

| | Before | After |
|---|---|---|
| Total tantras | 72 | ~76 (-2 dissolved, +6 new) |
| Math kosha nodes connected | 13 (physics only) | ~25 (+ count, viveka, logic, fold) |
| Graph ops used | PPR in kosha-expand only | + satya heuristic + walk-in index |
| Logic ops used | 0 | and/or/not for composite inference |
| Monolith lines (anuvada-ganana) | 119 | ~20 (thin wiring) |
| Question type dispatch | Hardcoded branches | Kosha swarupa-driven |
| Algebraic properties read (siddha) | 0 | distributivity, transitivity (steps 8-9) |
| Hardcoded operations | gt/lt in viveka, lists in count | apply-op via kosha eval |
| derive-step time | 133ms (scan all 23) | ~18ms (walk-in 3 candidates) |
| KE end-to-end | 338ms | ~81ms (match-first, skip derive) |

---

## Verification Commands

```bash
# ── shabda analysis (static, no server needed) ────────────────────────
python3 -m tools shabda summary              # full landscape: 1498 words, 17 files
python3 -m tools shabda lookup heavier       # trace word -> node + keys
python3 -m tools shabda lookup died          # find gaps (returns "not found")
python3 -m tools shabda eval                 # 32 fireable operations
python3 -m tools shabda gaps                 # nodes missing word mappings
python3 -m tools shabda words count          # all 13 aliases for count
python3 -m tools shabda node subtraction     # full shabda metadata

# ── live graph queries (auto-starts server) ───────────────────────────
# Trace any question through the full pipeline
python3 -m tools vy trace 'ball has mass 5 velocity 10. find kinetic energy'
python3 -m tools vy trace '10 birds. 3 died. 2 came back. how many remaining'

# Walk kosha chains to verify connections
python3 -m tools vy walk 'viveka-max abheda'
python3 -m tools vy walk 'partial-order siddha'
python3 -m tools vy walk 'ring kriya'

# Inspect any node
python3 -m tools vy inspect addition
python3 -m tools vy inspect distributivity

# Check word resolution
python3 -m tools vy eval 'word-node "many"'       # -> count (alias)
python3 -m tools vy eval 'word-node "died"'        # -> None (gap)
python3 -m tools vy eval 'word-node "heavier"'     # -> viveka-max (alias)

# Check mantra coverage
python3 -m tools vy mantras 'ball has mass 5 velocity 10. find kinetic energy'

# Evaluate expressions directly
python3 -m tools vy eval 'apply-op "max" [5, 8]'
python3 -m tools vy eval 'walk-in "mass" "janya"'
python3 -m tools vy eval 'walk-in "arithmetic" "kriya"'

# Static analysis
python3 -m tools tantra lint

# Run tests
python3 -m tools test run
```

---

## What Has Changed

| Date | Session | Event |
|------|---------|-------|
| 2026-03-19 | 10-11 | Plan created and consolidated in 17-scan-ref-patterns.md |
| 2026-03-20 | 12 | Split into 17c. Algebraic backing added per step (references 17b). Verification commands per step. |
| 2026-03-20 | 13 | **Steps 1b, 1c added.** Live graph tracing revealed alias bug affects 85 words (not just "many"), sankhya-bandha doesn't bind number-before-noun, and 12+ event verbs are completely unmapped. shabda analysis tool built (`python3 -m tools shabda`). Step 2 prerequisites expanded. |
| 2026-03-20 | 14 | **Step 1 DONE.** emit-triples alias fix (two-condition check). eval/apply-op tested as central mechanism: all 32 operations fire, arithmetic + logical + comparison all verified via `vy eval`. Plan reordered: Step 3 (viveka → apply-op) moved up as simplest proof of generalization. Two-layer readiness model added (kosha-words vs question-premises). Premise graph construction identified as new prerequisite for Step 10 (Finding 12). |
| 2026-03-20 | 15 | **Step 3 DONE.** viveka-ganana: gt/lt replaced by `apply-op op-eval`/`apply-op opp-eval`. Op names read from kosha: `shabda direction "eval"` and `shabda (walk direction "pratipaksha") "eval"`. 67/31/0 — no regressions. Next: Steps 1b + 1c + 2 (count-chain). |
| 2026-03-20 | 16 | **Step 1d CODE DONE (untested).** grade-sparsha tantra created; graded-ring.om gets `grade-boundary: viraam`; count-bandha n1/n2 ordering fixed for cross-sentence case; anuvada-ganana routes through grade-sparsha. Key insight: number-before-noun numbers stay loose in pure count sentences — grade-sparsha two-loose path handles them correctly without 1b. 6 new sentence_scope xfail tests added (test suite now 104 tests, 37 xfailed). count-dispatch in anuvada-ganana already wired (partial Step 2). |
| 2026-03-20 | 17 | **Step 1c DONE. Step 1e DONE. Step 1b DEFERRED. Plan reordered.** (1) BQG last-satya viraam reset — `last-satya` in build-question-graph never reset at viraam boundaries, causing `tree` from sentence 1 to leak into sentence 3 as `[tree, sankhya, 2.]`. Fixed with viraam check in reduce. (2) Event verb shabda table — 32 verbs mapped to kshaya/vriddhi in `common-sense-events.shabda`. New om node `common-sense-events.om` links the template. (3) vriddhi-kriya / kshaya-kriya edges added to 9 mathematical operations (addition, multiplication, power, exponential, square, double → vriddhi; division, square-root, half → kshaya). The addition→vriddhi edge was missing — the symmetric counterpart to subtraction→kshaya. (4) Step 1b deferred after investigation showed it blocks nothing: count sentences work with loose numbers, and "2 more came" should NOT bind 2 to viveka-max. (5) Set operation analysis: 6 tantras use set operations inline without referencing kosha. Set operation nodes have wrong eval values. Step 2a added for runtime primitives. (6) Step 1d verified — 73/31/0. |
