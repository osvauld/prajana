# 17a — Discoveries & Math Kosha Inventory

**Reference document. Findings from sessions 10-12 that inform the implementation plan.**

Parent: [17-scan-ref-patterns.md](17-scan-ref-patterns.md)

---

## Three Core Discoveries

### Discovery 1: scan-ref completes the tantra cycle

The scan-ref fix (doc 16) was a parser bug fix. What it revealed is
architectural: every tantra was constrained to an incomplete cycle. A
tantra could perceive (scan the graph) but could not reflect on its
perception (reference the scan output for further processing).

The fix completes the cycle: **perceive -> reflect -> act**
(sparsha -> viveka -> bandha) within a single file.

### Discovery 2: the math kosha is an unused library of 259 nodes

259 math-domain nodes. 32 have `eval` keys (directly fireable via
`apply-op`). 41 declare `kriya` (what operations they use). 35 declare
`siddha` (what properties they prove). The pipeline fires only 13 of
the 32 operations. 16 never fire.

```
USED (13):     add sub mul div half double square sqrt reciprocal cos max min power
UNUSED (16):   abs neg floor ceil log exp sin tan factorial and or not ppr acos asin atan2
```

### Discovery 3: the graph IS the index

The pipeline's bottleneck is `derive-step` (133ms per call). It scans
all 23 mantras checking if janya are bound. But the graph already knows:

```
walk-in "mass" "janya"     -> [newton-second-law, momentum-mantra, KE-mantra, ...]
walk-in "velocity" "janya" -> [angular-velocity-mantra, relative-velocity-mantra, ...]
intersection               -> {KE-mantra, momentum-mantra, centripetal-force-mantra}
```

3 candidates instead of 23. The derivation DAG is already in the graph.

---

## Trace-Verified Findings

### Finding 1: logic operations fire but are unused

```
apply-op "and" [true, false]  -> false
apply-op "or"  [false, true]  -> true
apply-op "not" [true]         -> false
```

Enable composite anumana ("Is X both Y and Z?") and negation ("Is X not Y?").

### Finding 2: PPR computes satya but only kosha-expand reads it

`node-satya "mass"` -> 0.878. Computed at boot via `ppr-mantra.eval = "ppr"`.
`kosha-expand` uses PPR to add `kosha-janya` triples for related nodes.
No tantra reads `node-satya` for mantra prioritization or disambiguation.

### Finding 3: entity scoping is broken for multi-entity questions

"find total momentum of two balls" shows both entities with same values.
"which has more KE" compares velocity instead of computing KE per entity.
Prerequisite blocker for dvandva (step 8) and viveka-derive (step 7).

### Finding 4: viveka detection is word-based, not edge-based

anuvada-ganana detects viveka by scanning sentence subjects for words
that resolve to viveka-max/viveka-min. Before dissolving into
swarupa-driven dispatch (Phase 2), avrti-refine must emit swarupa edges
from resolved concepts.

### Finding 5: krama-viveka falls into wrong dispatch path

"A is heavier than B. B is heavier than C. who is heaviest" goes to
anumana path, producing "does A inherit viveka-max?" Needs swarupa-edge
emission from Phase 2.

### Finding 6: emit-triples alias bug

`word="many"` -> `shabda-anveshana` -> `nd="count"` -> `word != nd` ->
true -> `is-rashi-label` -> `[many, mithya, many]`. Fix: check
`word-node word == nd`. But even after fix, `8` in "8 birds" stays
orphaned -- step 1 alone doesn't fix counting.

### Finding 7: count-bandha partially works

"5 apples and 3 apples. how many total" already produces count1=5,
count2=3, solve-for=count-total. The gap is not detection -- it's
firing: no mantra takes count1+count2 -> count-total.

### Finding 8: alias bug scope is much wider than "many"

Verified via `shabda words` tool: the alias bug affects **85 words** across
three nodes:
- **count** (13 aliases): many, total, remaining, left, rest, altogether,
  combined, leftover, number, quantity, how-many, sum, count
- **viveka-max** (41 aliases): heavier, faster, bigger, taller, strongest,
  greatest, most, highest, longest, widest, etc.
- **viveka-min** (31 aliases): lighter, slower, smaller, shorter, weakest,
  least, less, lesser, etc.

Every one of these words emits `[word, mithya, word]` instead of
`[node, satya, node]` whenever there is an active concept in context.
The bug fires when `is-rashi-label` sees `has-act AND word != nd`.
Without a preceding satya concept (e.g. "how many total" alone), the
aliases resolve correctly. With one (e.g. "8 birds. how many total"),
they break.

This means Step 1 (emit-triples alias fix) has **far broader impact**
than originally estimated — it unblocks not just counting but viveka
and krama-viveka paths too.

### Finding 9: event verbs are completely unmapped

Verified via `shabda lookup` + `word-node`: 12 common event verbs tested,
all return None:

```
died, flew, gave, lost, ate, bought, sold, found, came, added, removed, received
```

The graph has **no mechanism** to know that "3 died" means subtract 3.
The kosha declares the structural connection — `subtraction --[kriya]--> kshaya`
(decrease/loss) and `addition --[kriya]--> matra` — but no `.shabda` file or
`.om` word declaration maps event verbs to these operations.

**This blocks Step 2 (count-chain rewrite).** The plan says "dissolve count-bandha's
18 hardcoded subtraction words" but the kosha has zero replacement word mappings.
Before count-chain can use kosha-driven operations, a common-sense `.shabda` table
must map event verbs to `subtraction`/`addition` signals.

The existing `.shabda` template pattern (physics-constants, matra-aayaama) provides
the mechanism — a new `common-sense-events.shabda` file would map verbs to operations
using the same `key: value` format, readable via `shabda "common-sense-events" "died"`.

### Finding 10: sankhya-bandha only binds number-after-noun

Verified via trace: "birds 10" -> `[bird, sankhya, 10]` (correct).
"10 birds" -> `[10, asprista-sankhya, 10]` stays orphaned (bug).

`sankhya-bandha` tracks `last-active` left-to-right. When number precedes
noun, there is no active concept to bind to. Natural English uses
number-before-noun ("8 birds", "3 apples") as the dominant pattern.

In multi-sentence counting ("10 birds. 3 died."), the 10 never binds to
bird. Only the 3 binds (after bird is already active). The starting
count is lost.

This is a **separate problem from the alias bug** and **separate from
event verb mapping**. Even with both fixed, count-chain needs
number-before-noun handling to get the initial quantity right.

### Finding 11: shabda tool reveals 14 nodes missing word mappings

Built `python3 -m tools shabda gaps`: 14 nodes have `eval:` keys
(fireable operations) but no `word:` declarations. These include:
abs, sum, ceil, exponential, factorial, floor, logarithm, max, min,
product, neg, tangent (second occurrence). Plus 2 common-sense nodes
without words (domain-common-sense, phase).

`max` and `min` are particularly notable — they're needed for viveka
(Steps 3, 7) but have no word aliases. The comparison words ("heavier",
"fastest") map to `viveka-max`/`viveka-min`, which in turn connect
via `abheda` to `max`/`min`, but `max`/`min` themselves are wordless.

### Finding 12: eval/apply-op is the single mechanism — tested and ready

**Session 14.** The kosha has 32 nodes with `eval:` fields. `apply-op` fires
ALL of them — arithmetic, logical, comparison. The pipeline uses this in
exactly ONE place: `execute-mantra.tantra3` line 27 (`apply-op (shabda math-op "eval") args`)
for physics. Everything else hardcodes its operations.

**Verified via `vy eval`:**
```
apply-op "sub" [10, 3]        → 7       (replaces count-bandha's 17 hardcoded words)
apply-op "add" [1, 2, 3, 4]   → 10      (variadic fold — replaces manual accumulation)
apply-op "max" [5, 8]         → 8       (replaces viveka-ganana's 40 lines of gt/lt)
apply-op "and" [true, true]   → True    (enables "is X both Y and Z?")
apply-op "or"  [true, false]  → True    (enables "is X either Y or Z?")
apply-op "not" [true]         → False   (enables "is X not Y?")
```

**Kosha chain verified for count:**
```
walk-in "kshaya" "kriya"  →  [..., subtraction, minus, ...]
∩ walk-in "arithmetic" "kriya"  →  [subtraction]  (the arithmetic operation for decrease)
shabda "subtraction" "eval"  →  "sub"
apply-op "sub" [10, 3]  →  7
```

**Two layers of readiness:**

**Layer 1 (arithmetic + comparison):** For questions where kosha words resolve,
the eval/apply-op chain works end-to-end. The gap is graph construction:
aliases (FIXED), number-before-noun (Step 1b), event verbs (Step 1c).

**Layer 2 (logical composition):** For questions where the premises are IN the
question ("all birds can fly. is a sparrow a bird?"), `apply-op "and"/"or"/"not"`
can compose truth values. But the pipeline needs to first build graph edges from
question-provided premises — "all X are Y" should produce `[X, swarupa, Y]` even
when X and Y are unknown words. Currently unknown words go mithya and no edges
are built.

**Tested:** "all birds can fly. is a sparrow a bird? can a sparrow fly?" works
ONLY because sparrow and bird are already in the kosha. "all zorks are blimps.
is a flarg a blimp?" fails — everything goes mithya.

**Implication for plan:** eval/apply-op should be the central mechanism for
Steps 2 (count), 3 (viveka), 7 (viveka-derive), 8 (dvandva), 10 (logic).
Step 10 needs a new prerequisite: premise graph construction from unknown words.

### Finding 13: vriddhi-kriya was missing from addition (and 5 other operations)

**Session 17.** `subtraction --[kriya]--> kshaya` existed but the symmetric
`addition --[kriya]--> vriddhi` did not. The kosha declared decrease operations
(subtraction, division, square-root, half → kshaya) but not increase operations.

Verified: `walk-in "vriddhi" "kriya"` returned nothing relevant to arithmetic.
After adding vriddhi-kriya to addition, multiplication, power, exponential,
square, double — and kshaya-kriya to division, square-root, half — the full
direction classification is complete:

```
walk-in "kshaya" "kriya" ∩ arithmetic → subtraction, division
walk-in "vriddhi" "kriya" ∩ arithmetic → addition, multiplication
```

This completes the kosha chain for count-chain: event verb → direction → operation → eval.

### Finding 14: BQG last-satya leaks across viraam boundaries

**Session 17.** `last-satya` in `build-question-graph` was computed by scanning
the entire accumulated graph for the last satya triple — never resetting at
viraam boundaries. In "10 birds sat on a tree. 2 more came.", `tree` (sentence 1)
was still `last-satya` when `more` (sentence 3) was processed. With `pend-num`
active from `2`, the emit-triples `has-pend + has-act + is-concept` branch fired,
producing `[tree, sankhya, 2.]` and `[tree, matra, viveka-max]`.

Fixed: added `cond (eq (nth t 1) "viraam") ""` to the last-satya reduce. Now resets
at every viraam triple.

### Finding 15: number-before-noun (1b) blocks nothing

**Session 17.** Investigation of Step 1b revealed it is not a prerequisite for
count-chain or any current test. Count sentences work because numbers stay loose
as asprista-sankhya and grade-sparsha's two-loose path preserves sentence order.

Attempting the fix exposed structural complexity: in "2 more came", the pending
number should NOT bind to viveka-max (which "more" resolves to). "More" is a
modifier indicating increase, not the counted noun. The counted noun (birds) is
implicit from a previous sentence. Correct binding requires understanding:
- containers ("birds on a tree" — tree is the container)
- event structure ("2 more came" means +2 to the container's contents)
- implicit noun resolution (the "2" refers to birds, not to viveka-max)

This is deeper than a simple retroactive bind. Step 1b is deferred.

### Finding 16: set operations used inline in 6 tantras, kosha nodes have wrong eval values

**Session 17.** Six tantras use set operations inline without referencing the kosha:

| Tantra | Operation | Inline code |
|--------|-----------|------------|
| forward-match | subset (janya ⊆ bcs) | `reduce janya true (fn a r → and a (member r bcs))` |
| derive-step | subset (same) | same pattern |
| mantra-select | member (sf ∈ phala ∪ janya) | `member solve-for phala` |
| scope-vps | union (scoped ∪ flat) | reduce with dedup |
| viveka-ganana | member (active ∈ seen) | `member active seen-vals` |
| count-bandha | intersection (signals ∩ mithya) | `member w mithya-words` |

The kosha declares set-union, set-intersection, set-difference, set-complement,
subset — but their eval values are wrong placeholders inherited from unrelated
nodes: set-union eval:div, set-difference eval:ceil, set-complement eval:sin,
subset eval:square. No runtime primitives exist for set operations.

Lattice connects to set operations: `lattice --[yukta]--> set-union, set-intersection`.
Set-difference connects to kshaya: `set-difference --[abheda]--> kshaya`.
These structural connections are correct but unused.

### Finding 13 (original): viveka already works with Step 1 fix

**Session 14.** After the alias fix, "ball A has mass 5. ball B has mass 8.
which is heavier" produces the correct answer: "ball-B is viveka-max than A".
`heavier` now resolves as `[viveka-max, satya, viveka-max]` instead of
`[heavier, mithya, heavier]`. The existing hardcoded gt/lt path fires correctly.

Step 3 (replace gt/lt with apply-op "max") is now purely an architecture
improvement — the answer is already correct. The change makes viveka
extensible (new comparison types = new om nodes, not tantra code).

---

## The Math Kosha: Four Levels

### Level 1 -- Operations (32 with eval, 13 used, 16 unused)

| Node | eval | arity | pratipaksha | Status |
|------|------|-------|-------------|--------|
| addition | add | 2 | subtraction | **Needed for count** |
| subtraction | sub | 2 | addition | **Needed for count** |
| multiplication | mul | 2 | division | Connected (physics) |
| division | div | 2 | multiplication | Connected (physics inverse) |
| max | max | 2 | min | **Needed for viveka** |
| min | min | 2 | max | **Needed for viveka** |
| sum | add | -1 | -- | **Needed for dvandva** |
| product | mul | -1 | -- | **Needed for dvandva** |
| conjunction | and | 2 | -- | **Needed for composite anumana** |
| disjunction | or | 2 | -- | **Needed for disjunctive questions** |
| negation | not | 1 | -- | **Needed for negated inference** |
| ppr-mantra | ppr | 3 | -- | **Usable as search heuristic** |
| abs | abs | 1 | -- | Unused |
| neg | neg | 1 | -- | Unused |
| floor/ceil | floor/ceil | 1 | -- | Unused |
| log/exp | log/exp | 1 | each other | Unused |
| factorial | factorial | 1 | -- | Unused |
| sin/cos/tan | sin/cos/tan | 1 | -- | cos used by work-expr only |
| acos/asin/atan2 | acos/asin/atan2 | 1-2 | -- | Unused |

### Level 2 -- Properties (35 with siddha)

| Property | What it declares | Pipeline implication |
|----------|-----------------|---------------------|
| commutativity -> drishthanta -> addition | a+b = b+a | Operand order doesn't matter |
| pratipaksha: addition <-> subtraction | They're inverses | If total and part known, find other |
| associativity -> drishthanta -> addition | (a+b)+c = a+(b+c) | Can accumulate left-to-right |
| distributivity -> kriya -> mul, add | a(b+c) = ab+ac | Per-entity derive then sum |
| partial-order -> siddha -> transitive | A>B ^ B>C -> A>C | Transitive chain in krama-viveka |

### Level 3 -- Structures (41 with kriya)

| Structure | kriya declares | Pipeline implication |
|-----------|---------------|---------------------|
| ring -> addition, multiplication | Count arithmetic is ring arithmetic | Ring laws apply |
| lattice -> join, meet | Comparison is lattice operation | Transitive comparison |
| distributivity -> mul, add | Pairwise multiply then sum | dvandva pattern |
| fold -> swarupa <- sum, product | Aggregation = iterated binary op | Variadic operations |

### Level 4 -- Bridges

| Bridge | What it maps | Purpose |
|--------|-------------|---------|
| viveka-max -> abheda -> max | Comparative word -> operation | "heavier" -> max |
| viveka-min -> abheda -> min | Comparative word -> operation | "lighter" -> min |
| fold -> swarupa <- sum, product | Aggregation = iterated binary | Variadic = fold |
| addition -> pratipaksha -> subtraction | Inverse pair | Universal inversion |
| multiplication -> pratipaksha -> division | Inverse pair | Universal inversion |

---

## Performance Profile

| Operation | Current (scan) | With walk-in | Speedup |
|-----------|---------------|-------------|---------|
| derive-step (1 call) | 133ms (scan 23) | ~18ms (walk-in 3) | ~7x |
| derive-chain (3 calls) | 257ms | ~54ms (or skip) | ~5x |
| KE end-to-end | 338ms | ~81ms (match-first) | ~4x |

Slowest tests: `test_session_accumulate` (0.69s), `test_chain_force_via_suvat` (0.58s),
`test_chain_ke_via_suvat` (0.53s). All dominated by derive-step scanning.

---

## The Ten Natural Groups of Tantras

### Group 1: ORCHESTRATORS (5 tantras, ~250 lines)
anuvada-ganana, session-anuvada, avrti-refine, emit-reasoning, reboot.
**Problem:** anuvada-ganana is a 119-line dispatch table with hardcoded question-type detection.

### Group 2: PERCEPTION (8 tantras, ~310 lines)
prathama-sparsha, shashthi-sparsha, sankhya-sparsha, bound-state,
extract-solve-for, anumana-sparsha, scope-vps, mantra-coverage.
**Status:** Well-named complete thoughts. Keep.

### Group 3: REFINEMENT (14 tantras, ~830 lines)
sandhi-kosha, sandhi-avastha, sandhi-bandhana, vibhakti-shashthi,
sandhi-viveka, vishesa-instance, rashi-viveka, vishesa-bandhana,
rashi-anuvada, sankhya-bandha, count-bandha, assertion-bandha,
flush-pending-mithya, agra-bandha.
**Problem:** count-bandha (102 lines) hardcodes word lists.

### Group 4: DERIVATION (11 tantras, ~470 lines)
derive-step, derive-chain, mantra-select, match-mantra, forward-match,
inverse-match, execute-mantra, execute-matched, invert-math,
resolve-janya-args, relative-vps.
**Note:** Already uses kosha correctly for physics. The template for everything else.

### Group 5: PROOF EMISSION (11 tantras, ~620 lines)
emit-reasoning and its 8 sub-tantras (pratijna, hetu, nigamana, etc.)
**Status:** Architecturally sound. Keep.

### Group 6: COMPARISON (3 tantras, ~200 lines)
viveka-ganana, anumana-viveka, anumana-viveka-yukta.
**Problem:** viveka-ganana hardcodes gt/lt. Kosha declares max/min via eval.

### Group 7: GRAPH CONSTRUCTION (4 tantras, ~180 lines)
build-question-graph, emit-triples, materialize-question-graph, shabda-anveshana.
**Bug:** emit-triples alias misclassification.

### Group 8: EQUATIONS (11 tantras, ~150 lines)
ke-expr, velocity-expr, acceleration-expr, etc. Pure math. Keep.

### Group 9: INFRASTRUCTURE (6 tantras, ~150 lines)
reboot, varga-inheritance, mantra-coverage, shabda-anveshana. Keep.

### Group 10: COUNTING (3 tantras, ~155 lines)
count-bandha (dissolve), count-chain (rewrite), sankhya-bandha (keep).

---

## What Has Changed

| Date | Session | Event |
|------|---------|-------|
| 2026-03-19 | 9 | Document created. Five scan-ref patterns. 22 xfails mapped. |
| 2026-03-19 | 10 | Rewritten. Architecture-driven plan. Ten groups. Four phases. |
| 2026-03-19 | 11 | Consolidated with tool-verified observations. Full math inventory. |
| 2026-03-20 | 12 | Split into 17a/17b/17c. This file = discoveries + inventory. |
| 2026-03-20 | 13 | **Findings 8-11 added.** Alias bug scope: 85 words (verified via `shabda words`). Event verb gap: 12 verbs return None (verified via `word-node`). sankhya-bandha number-before-noun: "10 birds" doesn't bind (verified via trace). shabda gaps: 14 nodes missing word mappings (verified via `shabda gaps`). |
| 2026-03-20 | 17 | **Findings 13-16 added.** vriddhi-kriya missing from addition (and 5 others). BQG last-satya leaks across viraam. Number-before-noun blocks nothing (deferred). Set operations used inline in 6 tantras with wrong kosha eval values. |
