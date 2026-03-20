# 18 — What We Learned

**The philosophical and structural insights from sessions 14-19.**
**Absorbs the discoveries from 17a, 17b, 17c into unified understanding.**

Parent: [17-scan-ref-patterns.md](17-scan-ref-patterns.md) (historical)

---

## The Six Insights

### 1. One mechanism for all reasoning

Physics, counting, comparison, logic — they all follow the same path:

```
read kosha → find operation → fire via apply-op
```

Physics already worked this way. Session 14 proved it generalizes:
`apply-op "sub" [10, 3] → 7` (count), `apply-op "max" [5, 8] → 8` (comparison),
`apply-op "and" [true, false] → False` (logic). 32 operations are fireable.
16 have never fired. The unused operations are not missing features — they are
**latent capacity** waiting for the pipeline to address them.

The kosha chain for counting, end-to-end:
```
shabda "common-sense-events" "flew" → "kshaya"
walk-in "kshaya" "kriya" ∩ walk-in "arithmetic" "kriya" → [subtraction]
shabda "subtraction" "eval" → "sub"
apply-op "sub" [10, 3] → 7
```

### 2. The algebraic hierarchy is not decorative

The graph declares: `field → ring → group → set`. Each level adds guarantees.
`monoid --[drishthanta]--> addition` means fold-by-addition is well-defined.
`distributivity --[kriya]--> [multiplication, addition]` means compute-per-entity-then-sum is valid.
`partial-order --[siddha]--> transitive` means A>B ∧ B>C → A>C without computation.

These are not abstract math curiosities. They are **structural permissions** the pipeline
reads to validate operation sequences. The algebra tells the pipeline what it's allowed to do.

### 3. Subgraphs mirror cognition

emit-triples doesn't need the full graph or a narrow context tuple. It needs what a
**reader tracks while reading a paragraph**:

| Subgraph | What a reader tracks |
|---|---|
| **current-grade** | the sentence I'm currently in |
| **entity-registry** | who has been mentioned so far |
| **binding-ledger** | what numbers belong to whom |
| **grammar-trail** | what grammatical signals are active |

These aren't arbitrary data structures — they are the working memory of comprehension.
The narrow context tuple kept breaking because it was a lossy projection of this natural
structure. Passing focused subgraphs is not an optimization — it's modeling how
understanding actually works.

### 4. Dravya is recognized by exclusion

The dravya (substance) promotion rule works by negation:
- Not a verb form (karma) → check common-sense-events + kta-pratyaya (-ed) + shatr-pratyaya (-ing)
- Not after a locative (adhikarana) → check grammar-trail for adhikarana edge
- Not already claimed by an active concept → check binding-ledger
- What remains IS dravya.

This mirrors the Vaisheshika method: substance is what's left when you eliminate
quality, action, universal, particular, and inherence. The guards ARE the padaarthas
doing their work. The system doesn't learn "what is a noun" — it learns what ISN'T,
and the residue is substance.

### 5. The karaka system was already in the graph

Every Paninian participant role maps to an existing sangati root:

| Karaka | Was already |
|---|---|
| karta (agent) | kriya (action) |
| karma (object) | phala (fruit) |
| karana (instrument) | yukta (with) |
| sampradana (recipient) | phala-target |
| apadana (source) | kshaya (departure) |
| adhikarana (locus) | sthiti + kshetra |

The Vaisheshika ontology maps the same way:

| Vaisheshika | Was already |
|---|---|
| dravya (substance) | rashi |
| guna (quality) | sankhya + matra |
| karma (action) | karma |
| samanya (universal) | varga |
| vishesha (particular) | vishesa edge |
| samavaya (inherence) | shashthi-vibhakti |

The grammar was not added to the graph — it was **discovered** in the graph.
The sangati roots ARE the Paninian and Vaisheshika systems, expressed in the
graph's own vocabulary.

### 6. All utterance is vibhakti relation to vyakarana

When someone speaks to the proof graph, the type of utterance IS a vibhakti
case relation between speaker and graph:

| Utterance | Vibhakti | Relation to vyakarana |
|---|---|---|
| "Hello" | **sambodhana** (vocative) | I acknowledge your existence — opening sambandha |
| "A ball has mass 5kg" | **dvitiya** (accusative) | I give you knowledge — prajna-dana |
| "What is mass?" | **prathama** (nominative) | Tell me what this IS — darshana |
| "Find kinetic energy" | **vidhi-kaala** (imperative) | I command you to compute — ganana |
| "How many?" | **prashna** (interrogative) | I question you — prashna |
| "Thank you" | **sambodhana** again | I acknowledge what you returned — closing |

"Hello" is not a social greeting. It is **sambodhana** — the moment the speaker
acknowledges that the proof graph exists as an addressable entity and opens a
sambandha (relationship). Every subsequent sentence is in the scope of this
sambodhana. The graph is not a "system being queried" — it is an **entity being
addressed**. The routing problem is not "classify the intent" — it is "read the vibhakti."

---

## The Math Kosha Inventory (from 17a)

259 math-domain nodes. 32 with `eval:` (fireable). 41 with `kriya`. 35 with `siddha`.

```
USED (13):     add sub mul div half double square sqrt reciprocal cos max min power
UNUSED (16):   abs neg floor ceil log exp sin tan factorial and or not ppr acos asin atan2
```

Four levels of algebraic structure: field → ring → group → set.
Five integration points: count dispatch, dvandva, inverse math, transitivity, mantra narrowing.

The graded ring is the input structure:
- Paragraph = graded ring
- Sentences = grades (separated by viraam = additive identity = shunya)
- Period = grade boundary → resets additive indexing
- "and" = dvandva boundary → resets entity scope within a grade
- "respectively" = explicit distributivity bijection

---

## What Was Built (sessions 14-19)

| Session | Step | What | Baseline |
|---|---|---|---|
| 14 | 1 | emit-triples alias fix (85 words) | 67/37/0 |
| 15 | 3 | viveka-ganana → apply-op max/min | 67/31/0 |
| 16 | 1d | grade-sparsha (graded-ring partitioning) | 73/31/0 |
| 17 | 1c, 1e | Event verb shabda + BQG viraam reset | 73/31/0 |
| 18 | 2 | count-chain + emit-count + dvandva boundary | 78/39/0 |
| 19 | 2.5 | Karaka + dravya + subgraph architecture + tools | 78/39/0 |

---

## What Has Changed

| Date | Session | Event |
|---|---|---|
| 2026-03-20 | 19 | Document created. Absorbs insights from 17a/17b/17c and session 18-19 discoveries. |

done
