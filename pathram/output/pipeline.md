# Pipeline — How Sentences Become Understanding

## The Architecture

The pipeline is Datalog stratified evaluation. Seven layers, each a stratum. Within each stratum, triples accumulate monotonically. Between strata, results freeze and become read-only input to the next.

```
sentence
  → construct    (sentence → raw question graph)
  → assert       (raw → asserted: IS-A edges from copula patterns)
  → refine*      (asserted → refined: fixpoint enrichment spiral)
  → expand       (refined → expanded: kosha janya injection)
  → detect       (expanded → signals: intent/mode detection)
  → dispatch     (signals → answer: 4-way conditional)
  → emit         (answer → formatted output: proof + reasoning)
```

`refine*` denotes fixpoint — it runs until no new triples appear.

## Signal Flow

Every word in the sentence resolves to a graph node. That node's edges declare what the word IS. Those edges are the signals.

The pipeline is a signal chain: construct emits signals, downstream layers consume them. No layer drops signals — they flow through the graph and are available to any tantra that reads the edge type it cares about.

```
word → word-node → graph edges → typed triples (signals)
     → downstream tantra filters for edges it needs
```

### Signal types

| Signal | Edge type | Emitted by | Consumed by |
|---|---|---|---|
| concept | satya | emit-triples | everywhere |
| number | asprista-sankhya | emit-triples | sankhya-bandha, count-chain |
| event verb | mithya (kshaya/vriddhi via word-node) | emit-triples | count-chain |
| copula | copula | emit-triples | assertion-bandha |
| possession | shashthi-vibhakti | emit-triples | vibhakti-shashthi |
| conjunction | dvandva | emit-triples | grade-sparsha |
| question | vidhi-kaala | emit-triples | detect-signals |
| location | adhikarana | emit-triples | sandhi-avastha |
| period | viraam | emit-triples | grade-sparsha, count-chain |
| IS-A | swarupa | assertion-bandha | swarupa-anuvada |
| entity ownership | shashthi-vibhakti | vibhakti-shashthi | sankhya-bandha, derive |
| bound number | sankhya | sankhya-bandha | swarupa-anuvada, derive, viveka |
| propagated number | sankhya (on category) | swarupa-anuvada | count-chain aggregation |

### Signals not yet emitted (planned)

| Signal | Edge type | Source word | Would unlock |
|---|---|---|---|
| plural | bahu-vachana | -s/-es/-ies suffix | stem resolution, class signals |
| past tense | bhuta-kaala | -ed suffix, was/were | temporal reasoning |
| ablative case | panchami-vibhakti | "from" | "from rest" → initial-velocity=0 |
| locative case | saptami-vibhakti | "at"/"in"/"on" | "at 60 km/h" binding |
| dative case | chaturthi-vibhakti | "to" | "gave 3 to Mary" recipient |
| instrumental | tritiya-vibhakti | "by"/"with" | agent/means |
| distribution | distribution | "each"/"every"/"per" | multiplication |
| active voice | kartari-prayoga | "moves"/"moving" | velocity binding |
| universal | quantifier | "all"/"every" | class-level assertions |

## Monotonicity — The Convergence Guarantee

Every tantra in the refine layer is a monotone endomorphism: it only adds triples, never removes. The graph grows within a stratum until stable.

This guarantees fixpoint convergence (Kleene's theorem on a finite lattice): the set of triples can only grow, and is bounded by the finite set of possible triples. Therefore iteration terminates.

**Consequence for signal flow**: a signal emitted late in pass N is visible to all steps in pass N+1. No signal is ever lost. Within-layer async is handled by the fixpoint. Cross-layer async is handled by the layer ordering.

**The monotonicity contract**:
- emit alongside, never consume
- sankhya-bandha emits `[concept, sankhya, value]` alongside the original `[word, asprista-sankhya, value]` — both coexist
- swarupa-anuvada emits `[category, sankhya, value]` alongside `[entity, sankhya, value]` — both coexist
- count-chain reads whichever edge type it needs for its mode

## The Refine Spiral (avrti-refine)

The refine layer is a fixpoint over a krama chain of 10 monotone sub-steps:

```
sandhi-kosha       → compound word resolution
sandhi-avastha     → avastha qualification
sandhi-bandhana    → reattribute after rename
vibhakti-shashthi  → entity + ownership
vishesa-instance   → typed instances
rashi-viveka       → instance quantity binding
vishesa-bandhana   → move bindings to instances
rashi-anuvada      → propagate sankhya through vishesa (instance → concept)
sankhya-bandha     → bind floating numbers to concepts
swarupa-anuvada    → propagate sankhya through swarupa (entity → category)
```

The ordering is a dependency chain: each step reads what the previous step produced. The fixpoint wraps the whole chain — if swarupa-anuvada produces edges that sandhi-kosha can use, the next pass picks them up.

### Two propagation patterns

Both rashi-anuvada and swarupa-anuvada are the same abstract operation: **propagate PROPERTY through RELATION**.

```
rashi-anuvada:    [X, vishesa, Y] + [X, sankhya, V] → [Y, sankhya, V]
swarupa-anuvada:  [X, swarupa, Y] + [X, sankhya, V] → [Y, sankhya, V]
```

This is the transitive property of identity: if X IS Y, then X's attributes ARE Y's attributes. The graph's swarupa edge IS mathematical identity — the visheshanam ring's multiplicative identity preserves everything it touches.

## Count-Chain — Two Modes

Count-chain detects its mode from the graph:

**Aggregation mode**: query concept has sankhya edges propagated by swarupa-anuvada. Sum them.
- "cat is animal. 5 cats and 2 dogs" → `[animal, sankhya, 5]` + `[animal, sankhya, 2]` → 7
- Graph determines: swarupa edges exist + query concept has propagated sankhya

**Arithmetic mode**: grades have asprista-sankhya with event verbs. Fold with direction.
- "10 birds. 3 flew. 2 came" → 10 - 3 + 2 = 9
- Grade fold: per-grade direction from word-node (kshaya=subtract, vriddhi=add)

No hardcoded logic. The graph structure determines which mode fires.

## Assertion-Bandha — IS-A from Copula

When emit-triples sees a copula word ("is", "are"), it emits `[word, copula, word]`. Assertion-bandha reads this signal:

```
[cat, satya, cat]       -- subject (subj-ok = true)
[is, copula, is]        -- copula fires (saw-cop = true)
[animal, satya, animal] -- IS-A target → emit [cat, swarupa, animal]
```

The swarupa edge is the IS-A relation — same edge the kosha uses for taxonomy. assertion-bandha makes sentence-level IS-A explicit so swarupa-anuvada can propagate through it.

Guard: copula only fires when the subject was satya (subj-ok). "there are 5" doesn't trigger — "there" is mithya.
