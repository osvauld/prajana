# 17 — Completing the Tantra: Architecture After Scan-Ref

**The working document. The structural plan for what the codebase becomes.**

---

## The Discovery

The scan-ref fix (doc 16) was a parser bug fix. But what it revealed is
architectural: every tantra in the system was constrained to an incomplete
cycle. A tantra could perceive (scan the graph) but could not reflect on
its perception (reference the scan output for further processing). This
forced two structural distortions:

1. **Fragmentation** — one thought split across two or more files because
   the second half needed the first half's scan output
2. **Monoliths** — orchestrator tantras that exist solely to carry state
   between fragments that should be self-contained

The fix removes both constraints. A tantra can now complete the full cycle:
**perceive → reflect → act** (sparsha → viveka → bandha) within a single
file. This changes what a tantra IS — not a fragment of logic, but a
complete unit of thought.

---

## Current baseline

**511 passed / 63 xfailed / 0 failed** (2026-03-19, session 9)

---

## The Structural Principle

### Sparsha → Viveka → Bandha at every scale

The three operations appear identically at every level:

**Inside a single tantra:**
- sparsha: a scan pattern-matches over graph triples
- viveka: a cond/filter discriminates what was found
- bandha: an emit/append writes the result

**Across tantras:**
- Group 2 (prathama-sparsha, shashthi-sparsha, ...) = sparsha at tantra scale
- Group 6 (viveka-ganana, anumana-viveka, ...) = viveka at tantra scale
- Group 3 (refinement passes) + Group 5 (proof emission) = bandha at tantra scale

**Across the whole pipeline:**
- anuvada-ganana sequences: perceive (build+refine+expand), discriminate
  (viveka? anumana? physics?), bind (execute+prove+emit)

The scan-ref fix completes the cycle at the tantra scale. Before, a tantra
could only do sparsha (scan) without subsequent viveka (filter the output)
or bandha (emit from the filtered output). That forced the cycle to be
broken across files. Now each tantra can be one complete thought.

### What a tantra should feel like

The equation tantras are the template:

```
tantra3 ke-expr
takes mass
takes velocity
result = mul mass (mul velocity (div velocity 2))
return result
done
```

12 lines. Takes inputs, returns output. One thought. Every tantra should
approach this clarity — not in line count, but in conceptual unity. A
tantra should be one complete sparsha → viveka → bandha cycle, not a
fragment requiring an orchestrator to complete it.

---

## The Ten Natural Groups

Not by directory — by what the tantras ARE.

### Group 1: ORCHESTRATORS (5 tantras, ~250 lines)
**Tantras that sequence other tantras. They don't think — they wire.**

| Tantra | Lines | Role |
|--------|-------|------|
| anuvada-ganana | 119 | sentence → answer (dispatches everything) |
| session-anuvada | 40 | session wrapper, duplicates half of anuvada-ganana |
| avrti-refine | 37 | sequences 10 sub-passes in refinement loop |
| emit-reasoning | 41 | sequences 5 proof limbs into speech |
| reboot | 13 | sequences boot passes |

**Problem:** anuvada-ganana is a 119-line dispatch table. Every new question
type (viveka, anumana, count, transitive) requires adding a `cond` branch
to the monolith. It carries state between fragments that should be
self-contained.

**Action:** Dissolve anuvada-ganana into composable pieces. Each piece
completes its own sparsha → viveka → bandha cycle. The orchestrator
becomes thin wiring — or disappears entirely if composition is clean
enough. avrti-refine stays (already thin). emit-reasoning stays (already
a weaver, not a thinker).

### Group 2: PERCEPTION (8 tantras, ~310 lines)
**Pure readers. No side effects. The system's eyes.**

| Tantra | Lines | What it perceives |
|--------|-------|-------------------|
| prathama-sparsha | 15 | entities |
| shashthi-sparsha | 25 | ownership |
| sankhya-sparsha | 15 | numeric values |
| bound-state | 28 | what concepts have values |
| extract-solve-for | 55 | intent + solve-for + scope |
| anumana-sparsha | 83 | categorical question structure |
| scope-vps | 68 | entity-scoped value pairs |
| mantra-coverage | 23 | which mantras could fire |

**Action:** Keep. These are well-named, complete thoughts. Each one IS
a sparsha — contact with a specific aspect of the graph. The naming IS
the abstraction. extract-solve-for and anumana-sparsha could be simplified
later but work now.

### Group 3: REFINEMENT (14 tantras, ~830 lines)
**Transform the graph within the avrti loop. The understanding passes.**

| Tantra | Lines | What it refines |
|--------|-------|----------------|
| sandhi-kosha | 80 | mithya → compound lookup |
| sandhi-avastha | 45 | mithya → avastha compound |
| sandhi-bandhana | 50 | reattribute values after rename |
| vibhakti-shashthi | 74 | detect entities + ownership |
| sandhi-viveka | 50 | grammar structure from mithya words |
| vishesa-instance | 57 | create typed rashi instances |
| rashi-viveka | 60 | bind value to rashi instance |
| vishesa-bandhana | 51 | redirect bindings to instances |
| rashi-anuvada | 41 | propagate instance value to concept |
| sankhya-bandha | 36 | bind floating numbers to concepts |
| count-bandha | 102 | count operand assignment (WORKAROUND) |
| assertion-bandha | 93 | IS-A assertions → swarupa edges |
| flush-pending-mithya | 14 | helper for sandhi |
| agra-bandha | 76 | generic proximity binding |

**Problem:** count-bandha (102 lines) is a workaround for the broken cycle.
It splits the continuous act of counting into two discrete steps (bind
operands, then fire mantra) because the system couldn't hold intermediate
state within a scan. sandhi-kosha + sandhi-avastha are two passes over
the same word sequence for the same purpose (compound resolution).

**Action:** Dissolve count-bandha — replaced by count-chain. Consider
merging sandhi-kosha + sandhi-avastha (which dissolves flush-pending-mithya
too). The rest stay.

### Group 4: DERIVATION (11 tantras, ~470 lines)
**Compute new values from existing ones. The math engine.**

| Tantra | Lines | What it does |
|--------|-------|-------------|
| derive-step | 39 | one pass: fire all ready mantras |
| derive-chain | 79 | iterate derive-step, record changes |
| mantra-select | 41 | filter mantra candidates |
| match-mantra | 52 | find best matching mantra |
| forward-match | 25 | all janya bound → forward |
| inverse-match | 33 | phala bound → inverse |
| execute-mantra | 48 | fire a mantra (3 dispatch paths) |
| execute-matched | 31 | dispatch + format answer |
| invert-math | 56 | solve for missing input |
| resolve-janya-args | 27 | resolve mantra inputs |
| relative-vps | 42 | paired velocity values |

**Problem:** derive-chain (79 lines) manually unrolls 3 identical steps
because it needed to record what changed at each step and the system
couldn't do scan-then-analyze.

**Action:** Simplify derive-chain — 3 unrolled steps → one loop with
scan-ref. The rest are clean and well-decomposed.

### Group 5: PROOF EMISSION (11 tantras, ~620 lines)
**Turn the proof graph into speech. The panchaavayava.**

| Tantra | Lines | What it emits |
|--------|-------|--------------|
| emit-pratijna | 68 | "we have: ..." |
| emit-hetu | 34 | "we seek: ..." |
| emit-udaharana-upanaya | 76 | "we know: ... we see: ..." |
| emit-nigamana | 60 | "we find: ..." |
| emit-anumana | 100 | categorical proof |
| mantra-known-str | 33 | "we know: mantra (j → p)" |
| mantra-seen-str | 66 | "we see: applying j=val" |
| entity-props-str | 34 | "entity (c=val)" |
| list-join | 42 | Oxford comma join |
| pramana-bandha | 65 | bind proof edges into graph |
| sought-bandha | 46 | bind sought edges |

**Action:** Keep. The five-limbed proof structure is well-decomposed.
Each limb is its own tantra. This group is architecturally sound.

### Group 6: COMPARISON (3 tantras, ~200 lines)
**Discriminate: which is more, which is ancestor.**

| Tantra | Lines | What it compares |
|--------|-------|-----------------|
| viveka-ganana | 95 | which entity has more/less |
| anumana-viveka | 54 | does entity inherit from ancestor |
| anumana-viveka-yukta | 47 | does entity have property via varga |

**Problem:** All three contain copy-pasted structure. viveka-ganana uses
reduce as a poor scan. anumana-viveka and anumana-viveka-yukta manually
unroll 4 levels of chain walking because the system couldn't collect
then iterate.

**Action:** All three absorb their internal repetition using scan-ref.

### Group 7: GRAPH CONSTRUCTION (4 tantras, ~180 lines)
**Words in, graph out. The intake system.**

| Tantra | Lines | What it builds |
|--------|-------|---------------|
| build-question-graph | 36 | sentence → raw triples |
| emit-triples | 52 | word + context → triples |
| kosha-expand | 39 | add PPR-related concepts |
| materialize-question-graph | 50 | triples → traversable nodes |

**Action:** Keep. These use reduce/map correctly for their purpose.

### Group 8: EQUATIONS (11 tantras, ~150 lines)
**Pure math. The irreducible transformations.**

ke-expr, velocity-expr, acceleration-expr, work-expr,
potential-energy-expr, period-expr, frequency-expr,
centripetal-force-expr, gravitational-force-expr, ke-inv-mass,
relative-velocity-expr

**Action:** Keep. Add new ones as needed (area-expr, distance-expr).

### Group 9: INFRASTRUCTURE (6 tantras, ~150 lines)
**Boot, lookup, debug, fixpoint.**

reboot, varga-inheritance, shabda-anveshana, avrti, unit-of-concept,
mantra-coverage

**Action:** Keep.

### Group 10: COUNTING (3 tantras, ~155 lines)
**The broken group. Where this all started.**

| Tantra | Lines | Status |
|--------|-------|--------|
| count-bandha | 102 | Workaround. Dissolve. |
| count-chain | 17 | Stub. Rewrite. |
| sankhya-bandha | 36 | Works for non-count case. Keep. |

**Action:** Rewrite count-chain as a complete thought (scan events, track
running total, emit). Dissolve count-bandha.

---

## The Dissolution Plan

### Phase 1: Complete Thoughts (fix the broken cycles)

Make each affected tantra a complete sparsha → viveka → bandha cycle.
This is the structural work — not test-driven, architecture-driven.

#### 1a. count-chain rewrite (Group 10)

**Dissolves:** count-bandha (102 lines)
**Creates:** count-chain rewrite (~40 lines)

The sentence IS a number line. The scan walks events in order, tracking
a running total. Post-scan, extract the total and emit:

```
"8 birds. 3 flew away. 2 came back. how many remaining."
 └─ +8    └─ -3        └─ +2        └─ emit total (7)
```

One thought: perceive the events (scan), discriminate add/subtract
(verb signals), bind the total (emit). Complete cycle.

Wire into avrti-refine: line 32, count-bandha → count-chain.

#### 1b. derive-chain simplification (Group 4)

**Absorbs:** 3 manually unrolled steps → 1 loop (~40 lines from 79)

One thought: keep deriving until nothing new appears. Record what
changed at each step for reasoning emission. The loop IS the thought
— not three copies of it.

#### 1c. anumana-viveka simplification (Group 6)

**Absorbs:** 4 copy-pasted levels → scan + iterate (~25 lines from 54)
**Same for:** anumana-viveka-yukta (~25 lines from 47)

One thought: walk up the inheritance chain until you find the target
or exhaust the chain. Any depth, not just 4.

#### 1d. viveka-ganana cleanup (Group 6)

**Absorbs:** reduce-as-poor-scan → proper scan + post-comparison
(~70 lines from 95)

One thought: collect per-entity values (scan), then compare them
(post-scan viveka). Two phases, one file.

### Phase 2: Dissolve the Monolith (Group 1)

anuvada-ganana today is 119 lines of dispatch:

```
lines 21-24:  perceive (build → assert → refine → expand)
lines 26-29:  extract intent (solve-for, scope)
lines 31-44:  detect viveka (is this a comparison question?)
lines 47-54:  execute viveka path
lines 62-63:  detect intent gate
lines 65-78:  detect anumana (is this a categorical question?)
lines 74-78:  execute anumana path
lines 81-91:  execute physics/math path
lines 93-98:  select result from paths
lines 100-106: select base graph for proof
lines 109:    build proof graph
lines 112-114: emit speech
```

Each block is a distinct thought. The dissolution:

#### 2a. Extract viveka-sparsha (lines 31-44 → new tantra)

The 14 lines that detect whether this is a comparison question.
Currently embedded inside anuvada-ganana. This IS a perception —
it looks at the graph and says "this is a viveka question about
concept X in direction Y." Complete sparsha.

#### 2b. Extract ganana-dispatch (lines 81-98 → new tantra or simplify)

The result-selection cascade:
```
if anumana → anumana-result
if viveka → viveka-winner
if no-intent → "no match"
if has-match → execute
else → "no match"
```

This is pure viveka — discriminating which path produced the answer.
Could become a generic pattern: given N candidate results, return the
first non-empty one.

#### 2c. Extract pramana-siddhi (lines 100-114 → absorb into existing)

Proof graph selection + emission. This might fold into pramana-bandha
or emit-reasoning rather than becoming its own tantra.

#### 2d. The residual anuvada-ganana

After extraction, what remains is thin wiring:
```
graph = build → assert → refine → expand
intent = extract-solve-for graph
type = question-type graph  (viveka-sparsha + anumana-sparsha)
result = dispatch type graph intent
proof = pramana-bandha graph result
answer = emit-reasoning proof
```

~20 lines. Pure composition. Adding a new question type means writing
a new tantra, not modifying the orchestrator.

#### 2e. session-anuvada unification

session-anuvada currently duplicates half of anuvada-ganana. With the
dissolution, session-anuvada becomes: inject prior-graph after refine,
then call the same composable pieces. The duplication vanishes.

### Phase 3: Merge Fragments (Group 3)

#### 3a. Unify sandhi-kosha + sandhi-avastha (optional, risky)

Both do compound resolution. sandhi-kosha checks the kosha for
registered compounds. sandhi-avastha checks for avastha qualifiers
(initial, final). The thought is ONE: "these adjacent words form one
concept." With scan-ref, a single compound-resolution scan could
handle both, checking kosha first then avastha as fallback.

This dissolves flush-pending-mithya (14 lines) automatically.

**Risk:** High. Both work. The merge could introduce subtle ordering
bugs. Defer unless the architecture demands it.

### Phase 4: New Complete Thoughts (what scan-ref enables for xfails)

These aren't patches — they're new tantras, each expressing one
complete thought that was previously impossible.

#### 4a. viveka-derive (new)

**Thought:** For each entity, compute its derived values, then compare.

Currently viveka can only compare values already in the graph.
"Which has more KE" requires computing KE per entity first. This is
scan → derive-per-entity → compare. One complete cycle.

**Unlocks:** 4 xfails (viveka compute-then-compare)

#### 4b. dvandva-ganana (new)

**Thought:** For each entity, compute a value, then aggregate (sum).

"Total momentum of two balls" = compute momentum per ball, then sum.
Same per-entity derive infrastructure as viveka-derive, but aggregates
instead of comparing.

**Unlocks:** 4 xfails (dvandva per-entity)

#### 4c. krama-viveka (new)

**Thought:** Given comparison edges, build transitive closure.

"A > B, B > C, who is greatest?" Scan for comparison edges, collect
as pairs, iterate until the closure is complete.

**Unlocks:** 8 xfails (transitive reasoning)

---

## What Does NOT Need Scan-Ref

These xfail gates are blocked by other things entirely:

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

The order follows the structural principle: complete the broken cycles
first, then dissolve the monolith, then build new thoughts.

| Order | What | Group | Nature | Tests |
|-------|------|-------|--------|-------|
| 1 | count-chain rewrite + wire | 10, 3 | Complete a broken cycle | +6 |
| 2 | derive-chain simplification | 4 | Absorb repetition | 0 (quality) |
| 3 | anumana-viveka simplification | 6 | Absorb repetition | 0 (quality) |
| 4 | viveka-ganana cleanup | 6 | Absorb repetition | 0 (quality) |
| 5 | Dissolve anuvada-ganana | 1 | Dissolve monolith | 0 (architecture) |
| 6 | viveka-derive | new | New complete thought | +4 |
| 7 | dvandva-ganana | new | New complete thought | +4 |
| 8 | krama-viveka | new | New complete thought | +8 |

**Best case: 22 xfails promoted, 63 → 41.**
**But the real win is structural**: every tantra becomes a complete thought,
composition replaces orchestration, and new capabilities emerge from
writing new tantras — not from modifying existing ones.

---

## The Net Transformation

| | Before | After |
|---|---|---|
| Total tantras | 72 | ~74 (−2 dissolved, +4 new/extracted) |
| Monolith lines (anuvada-ganana) | 119 | ~20 (thin wiring) |
| Copy-pasted code | 4 swarupa levels, 3 derive steps, 102-line count workaround | Eliminated |
| New question type cost | Modify anuvada-ganana + write tantra | Write tantra only |
| Tantra completeness | Many fragments (scan without reflect) | Each tantra = full cycle |

---

## Philosophical Direction

### The equation tantras ARE the target form

ke-expr is 12 lines. It takes inputs, returns output. It IS one thought.
Not every tantra can be 12 lines. But every tantra should be one thought
— one complete sparsha → viveka → bandha cycle. The question is never
"how many lines" but "how many thoughts." If the answer is more than one,
the tantra should be dissolved.

### Dissolution IS abstraction

When we dissolve anuvada-ganana, we're not just splitting a file. We're
naming what was unnamed. The viveka detection block becomes viveka-sparsha
— a perception with a name, callable from anywhere. The dispatch block
becomes visible as a pattern (first non-empty result wins) rather than
hidden inside a monolith. Naming the fragments is the abstraction.

### Composition replaces orchestration

The goal: adding a new question type (say, proportional reasoning) should
require writing ONE new tantra that expresses one complete thought. That
tantra composes with existing pieces naturally — it doesn't require
modifying anuvada-ganana to add a new `cond` branch. The pipeline
discovers it and routes to it. This is what doc 14 (tantra3 philosophy)
describes: the om graph declares the capability, the pipeline reads it.

### The three operations at every scale — the unifying insight

sparsha, viveka, bandha are not just useful categories. They are the
structure of understanding itself. Every act of understanding follows the
same cycle: contact (what is here?), discrimination (what does it mean?),
binding (what do I do with it?). The codebase should reflect this at
every level — inside each tantra, across tantras, and across the pipeline.
When it does, the architecture becomes self-similar. A new contributor
can read any tantra and know where they are in the cycle. The structure
IS the documentation.

---

## What Has Changed

| Date | Session | Event |
|------|---------|-------|
| 2026-03-19 | 9 | Document created. Five scan-ref patterns identified. 22 xfails mapped across 4 tiers. |
| 2026-03-19 | 10 | **Document rewritten.** Shifted from test-driven to architecture-driven plan. Ten natural groups identified across all 72 tantras (not by directory — by what they ARE). Four phases: complete broken cycles → dissolve monolith → merge fragments → build new thoughts. The unifying principle: every tantra should be one complete sparsha → viveka → bandha cycle. Dissolution IS abstraction. Composition replaces orchestration. |
