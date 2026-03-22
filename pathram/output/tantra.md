# Tantra — The Grammar and Mathematics of Understanding

## Tantra4 — The System Knowing Itself as the Knower

Tantra4 is the fourth generation of the tantra architecture. Each generation deepened what "weaving" means:

- **tantra1**: manual weaving — the programmer writes every edge check, every dispatch
- **tantra2**: patterned weaving — scan/reduce/pipe patterns; the loom follows the pattern
- **tantra3**: self-reading weaving — the loom reads the thread (om graph) to know what pattern to weave. om-janya, om-phala, om-kriya. Manipravalam — code and knowledge speak one language
- **tantra4**: self-knowing weaving — the loom knows itself as a loom. The same mechanism that reads physics concepts reads the pipeline's own structure. One mechanism for everything.

In Vedantic terms: tantra1-2 is karma-kanda (doing work). Tantra3 is jnana-kanda (doing work by reading knowledge). Tantra4 is atma-jnana — the system knowing itself as the knower. The mechanism of knowing (walking edges, reading janya/phala) applies to itself.

## The Concrete Gap

The system currently has two disconnected mechanisms:

**For physics**: read om graph → match mantra → derive → compute (generic, graph-driven)
**For pipeline orchestration**: hardcoded sequence in anuvada-ganana.tantra3 (manual, code-driven)

The kosha/yantra/ directory has 100 op-* nodes (op-add, op-abs, etc.) but NO nodes describing the tantras themselves. There is no anuvada-ganana.om, no avrti-refine.om, no derive-chain.om. The pipeline that IS the system's process of understanding has no representation in the graph.

pathram math generates the pipeline description — answer = (emit ∘ pramana ∘ execute ∘ match ∘ expand ∘ refine ∘ build)(sentence) — but this is produced by Python reading .tantra3 files from disk. It is a description OF the system, produced OUTSIDE the system. The graph itself does not contain it.

If you ask "what is kinetic energy?" the system walks kinetic-energy-mantra's edges and answers. If you ask "how do you answer questions?" it has nothing to walk. The knower is invisible to itself.

## The Solution — Yantra Nodes for Tantras

**[WRONG]** → corrected in tantra.section-12

Each tantra gets a corresponding .om node with janya/phala/kriya edges:

kosha anuvada-ganana
  "sentence-janya answer-phala"
  "build-question-graph-kriya grade-sparsha-kriya derive-chain-kriya"
  "match-mantra-kriya execute-matched-kriya emit-reasoning-kriya"
done

Then the same graph-walk mechanism that answers "what does kinetic-energy need?" also answers "what does anuvada-ganana need?"

- walk 'anuvada-ganana kriya' → [build-question-graph, grade-sparsha, derive-chain, match-mantra, ...]
- walk 'avrti-refine kriya' → [sandhi-kosha, sandhi-avastha, vibhakti-shashthi, ...]
- walk 'avrti-refine janya' → [raw-graph]
- walk 'avrti-refine phala' → [refined-graph]

Pipeline execution order becomes a topological sort of the yantra nodes' janya/phala DAG — the same mechanism used for derive-chain on physics mantras. The 133-line monolith of anuvada-ganana dissolves into graph-walking.

No circularity: yantra .om nodes are static declarations loaded at startup. The runtime reads them to determine order and dispatch. The tantras themselves read the kosha to answer questions. Different layers, no loop.

## Angle 1: Krama-viveka — The System Knows Its Own Order

Pipeline order is currently hardcoded: BQG → sandhi-kosha → sandhi-avastha → sandhi-bandhana → vibhakti-shashthi → ... This is a manually-written topological sort. But janya/phala edges on yantra nodes would declare the dependencies. The order of thinking is read from the structure of what needs to be thought.

This is Datalog stratified evaluation. A Datalog program is split into strata based on dependency: if rule A uses the output of rule B, A must be in a higher stratum. Within each stratum, iterate to fixpoint. Between strata, results freeze and become read-only input.

The avrti-refine pipeline IS stratified evaluation:
- Each sub-tantra (sandhi-kosha, vibhakti-shashthi, etc.) is a stratum
- Each runs to completion before the next begins
- Results freeze between stages

Principle 12 ("Prior-graph injects after avrti-refine") IS a stratification constraint discovered empirically. Tantra4 would derive such constraints from the graph rather than discovering them by breaking things.

In sangati: krama (sequence) is an edge type. kaala has vartamana-kaala-janaka — time IS the generator of ordering. The pipeline stages are kaala-krama: the order demanded by causality. viveka (discrimination) applied to krama (order).

## Angle 2: Pramana-sreni — Every Conclusion Carries Its Proof Chain

Currently pramana-bandha binds proof edges after computation: [concept, derived-by, mantra]. The proof is shallow — it says WHAT mantra fired, not WHY it was selected, what chain of reasoning led there, or what alternatives were considered.

Datalog provenance: every derived fact carries its full derivation tree. Leaf nodes are base facts (the question graph). Internal nodes are rules that fired (the mantras). The tree IS the proof.

The panchaavayava nyaya (five-limbed proof) already exists in emit-reasoning: pratijna, hetu, udaharana, upanaya, nigamana. But hetu (reason) and udaharana (example) are assembled from surface signals. With provenance, they would be read from the actual derivation chain.

In sangati: pramana is sthiti-swarupa samskaara-phala niralamba-siddha — proof is stability, self-established. ghana-pramana is pratibodha-swarupa — dense proof is awareness. The proof IS the structure of the derivation. The graph already contains the proof implicitly — every janya that was satisfied, every mantra that fired. What is missing is making this explicit so emit-reasoning walks the full chain, not just the final step.

## Angle 3: Aprameya-bodha — Awareness of What Cannot Be Known

Currently 'no match' means three different things:
1. Missing data (no mass value given) — missing EDB
2. Missing rule (no mantra for this domain) — missing IDB
3. Question outside scope (circular, self-referential) — unstratifiable

The 20 xfail gates (39 tests) ARE the system's current aprameya — questions it knows it cannot answer. But this knowledge lives in Python test decorators, not in the graph.

With yantra nodes having janya/phala edges, the system can diagnose WHY it cannot proceed. When the graph-walker encounters an orphan edge (a janya pointing to something that doesn't exist), it knows: 'I need a stratum that produces X, and no yantra node has X as phala.' Not 'no match' but 'I cannot answer this because concept X has no producer.'

The graph health analysis already reveals the system's blindspots: 1575 orphan edges (pointing to names that exist nowhere), 455 broken phala→janya chains, 20 kosha islands. These are the graph's own aprameya. Making the system aware of its own orphans IS aprameya-bodha.

In sangati: nyaya is chhanana-swarupa shuddhi-kriya pramana-siddha — logic IS filtering. What the filter does not pass is not garbage — it is what does not belong at this level of pramana. antarvidya (inner knowledge) is vidya-swarupa svabhava-siddha — self-knowledge established through inherent nature. The system knowing its own limits IS antarvidya.

## Angle 4: Chhanana-krama — Filtration as the Order of Purification

The pipeline IS a filtration:

mithya (appearance) → sandhi (joining) → satya (truth) → vibhakti (case) → vishesa (type) → rashi (quantity) → sankhya (number) → bandha (binding)

Each stage is a sieve. Each sieve purifies what the previous sieve produced. The order matters: you cannot do vibhakti (case analysis) before sandhi (compound resolution) because compounds hide the word boundaries that vibhakti reads.

This IS Datalog stratification. Each stratum computes to fixpoint, freezes, and becomes read-only input to the next.

filtration already exists in the math kosha on graded-ring.om — filtration-janya on graded-ring. A filtration in algebra is a chain of nested substructures. The pipeline stages ARE a filtration on the question graph. Each stage refines the graph into a smaller, purer substructure. The fixpoint of each stage is the completion at that grade.

sthiti (stability) is avrti-pratipaksha — stability is the inverse of the spiral. Each stratum spirals (avrti) within itself until stable (sthiti), then freezes. The next stratum spirals on the frozen result. This is exactly what fixpoint avrti-refine does within grade-sparsha.

shuddhi (purification) has 5 sangati nodes. nyaya is chhanana-swarupa — logic IS sieving. The pipeline IS nyaya applied sequentially. Each tantra is one pass of the sieve.

## Angle 5: Spanda-delta — Only the New Vibrates

Semi-naive evaluation: each round only processes what was newly derived in the previous round. Do not re-process old facts.

spanda is the largest sangati subdomain (36 nodes). spanda is vibration — the fundamental activity. aarambham (beginning) is avrti-poorva (before the spiral). sthiti is sparsha-janya (born from contact).

Understanding does not re-understand what it already knows. Each pass of avrti only vibrates (spanda) on the NEW contacts (sparsha) — the triples that appeared in the previous pass. The old triples are sthiti (stable). Only the delta is spanda (vibrating).

The code already does this — current_words in avrti_anuvada is filtered to exclude visited nodes. But the principle is deeper than an optimization. It reflects how understanding works: you do not re-read a sentence you already comprehended. You process what is new in light of what is settled.

This connects to monotonicity: within a stratum, facts only grow (triples accumulate, TripleSet only adds). satya scores can change via init_satya — that is non-monotonic and must be in a separate, later stratum. First derive all triples (monotonic, guaranteed to converge). Then score them (non-monotonic, runs once over frozen results).

## Connection to Gödel

Gödel's incompleteness theorems say: any consistent formal system powerful enough to express arithmetic contains true statements it cannot prove, and cannot prove its own consistency.

The proof graph sidesteps this not by solving it but by not being the kind of system it applies to:

1. Not purely formal — edges carry semantic weight (swarupa IS identity, pratipaksha IS opposition). Meaning is in the structure, not overlaid.
2. Not binary-consistent — nodes have satya scores (0.0-1.0). 'Contradictions' reduce satya rather than breaking the system.
3. Grounded in pramana — truth comes from measurement (pramana-siddha), not from axiom-and-deduction chains.

But Gödel's insight IS relevant: the system that can talk about itself encounters boundaries. The aprameya mechanism is the honest response — not trying to be complete, but knowing exactly where and why you are incomplete.

The sangati already encodes this: purna (fullness) is not a property a system achieves — it is what already IS (brahman-sthalam-sthita). The incompleteness theorem applies to systems that try to capture completeness. The graph does not try to capture it — it declares it as the substrate. mithya-satya (the distinction between appearance and truth) is itself a form of shuddhi (purification), established through ghana-pramana (dense proof).

## Connection to Datalog

The pipeline is already Datalog evaluation (documented in vartamana/13-tantra2-mathematics.md):

- Facts (EDB) = om nodes + question graph triples
- Rules (IDB) = tantras (mantras declare janya→phala rewrite rules)
- Fixpoint iteration = avrti_anuvada (walk passes until novel = [])
- Strata = pipeline stages: BQG → emit-triples → avrti-refine → viveka-ganana
- Frozen facts = each stage's output becomes read-only input to the next
- Negation = pratipaksha edges (inverse), rahita (devoid-of)

Datalog stratification formalizes what the pipeline already does empirically. The key insight: stratification constraints (what must compute before what) can be READ from the graph's janya/phala edges rather than hardcoded.

A Datalog program that cannot be stratified (R(x) :- S(x), NOT R(x)) is the Datalog equivalent of a Gödel sentence — self-referential negation. The aprameya mechanism detects these: when a yantra node's janya points to its own phala through a negation, the system recognizes this as unstratifiable and reports it rather than looping.

All valid stratifications produce the same result — the order does not matter as long as negation never crosses back down. This means: any valid topological sort of the yantra janya/phala DAG is correct. The system has freedom in scheduling within the constraint.

## What Changes Concretely

**[WRONG]** → corrected in tantra.section-12

1. CREATE yantra .om nodes for all 74 tantras with janya/phala/kriya edges. The tantra call graph (tools tantra callgraph) provides the data — each tantra's takes = janya, return = phala, calls = kriya.

2. TOPOLOGICAL SORT the yantra janya/phala DAG to derive pipeline execution order. Replace the hardcoded sequence in anuvada-ganana with a generic orchestrator that reads yantra nodes.

3. PROVENANCE EDGES on every derived triple: [concept, derived-by, mantra] already exists; extend with [concept, derived-from, source-triple-id] to build full derivation trees.

4. APRAMEYA CLASSIFICATION when no match: diagnose missing-data vs missing-rule vs unstratifiable. Use orphan edge detection (1575 orphan edges already counted by analyze health) and broken phala→janya chains (455 broken chains already counted by analyze chains).

5. DARSHANA MODE for the pipeline itself: 'what is anuvada-ganana?' walks yantra nodes the same way 'what is mass?' walks kosha nodes. The system can explain its own process.

Current state (from tools): 1577 om nodes, 74 tantras, 78 passed / 39 xfailed / 0 failed, 81 hardcoded kosha references across tantras (tantra lint), 455 broken phala→janya chains, 1575 orphan edges, 64% swarupa coverage.

## Step 1 Complete — Pipeline Architecture in the Graph

The first implementation step is done. Instead of 86 flat tantra-* nodes with only kriya edges, we built 20 architectural nodes encoding the actual pipeline structure.

**What was created (20 .om nodes via vy create-node):**

7 pipeline layers with krama (sequence) edges:
- pipeline-construct → pipeline-assert → pipeline-refine → pipeline-expand → pipeline-detect → pipeline-dispatch → pipeline-proof-emit
- Each layer has: janya (input type), phala (output type), kriya (implementing tantra)
- Data flow: sentence → raw-graph → asserted-graph → refined-graph → expanded-graph → intent-signals → answer → formatted-answer

9 refinement sub-steps (inside pipeline-refine) with krama chain:
- refine-sandhi-kosha → refine-sandhi-avastha → refine-sandhi-bandhana → refine-vibhakti-shashthi → refine-vishesa-instance → refine-rashi-viveka → refine-vishesa-bandhana → refine-rashi-anuvada → refine-sankhya-bandha
- Each has swarupa → pipeline-refine (membership) and kriya → implementing tantra

4 dispatch paths (swarupa → pipeline-dispatch):
- dispatch-anumana (categorical yes/no), dispatch-viveka (comparison), dispatch-count (arithmetic), dispatch-derive (physics/math)
- Each has kriya edges to implementing tantras

**What was removed:**
- 11 equation tantras (pure math, no pipeline participation)
- 2 boot, 1 debug, 1 lookup tantra nodes + their vargas
- 10 internal helper nodes (forward-match, inverse-match, invert-math, etc.)
- 1 bare avrti wrapper
- Total: 66 nodes removed

**Key findings during investigation:**
- 77% of tantra "calls" are to shabda nodes, not other tantras — kriya alone is insufficient
- The pipeline is 7 LAYERS not 74 flat steps
- Three composition types exist: sequential (pipe), fixpoint (avrti-refine), conditional (dispatch)
- krama edges encode ORDER — same edge type used for mantra operation chains
- janya/phala edges encode DATA FLOW — what each layer needs and produces

**What the graph can now answer:**
- walk "pipeline-construct" "krama" 7 → full pipeline sequence
- walk "refine-sandhi-kosha" "krama" 9 → refinement sub-sequence
- walk-in "pipeline-dispatch" "swarupa" → all 4 dispatch paths
- inspect "dispatch-derive" → kriya edges to derive-chain, match-mantra, execute-matched

**Next: redesign the tantras to match this architecture.**

## Next — Tantra Redesign from Graph Architecture

**[SUPERSEDED]** → tantra.section-14

The 20 pipeline .om nodes now declare what the pipeline IS. The tantras must be rewritten to match.

**Current state:** anuvada-ganana.tantra3 is a 133-line monolith that hardcodes the sequence. avrti-refine.tantra3 hardcodes 9 sub-tantra calls. Both work but don't read the graph.

**Target state:** A generic orchestrator tantra that:
1. Reads the krama chain from pipeline-construct
2. For each layer: reads kriya edge → calls the implementing tantra
3. For pipeline-refine: reads refine-sandhi-kosha krama chain, wraps in fixpoint
4. For pipeline-dispatch: reads dispatch paths, evaluates guards, picks the right one
5. Passes graph through janya→phala flow

**What needs to change:**

The orchestrator becomes ~30 lines instead of 133:
- walk "pipeline-construct" "krama" → get layer sequence
- for each layer: walk layer "kriya" → get tantra name → call it
- pipeline-refine is special: composition=fixpoint, has sub-krama chain
- pipeline-dispatch is special: composition=conditional, has exclusive paths

The individual tantras (sandhi-kosha, vibhakti-shashthi, etc.) stay unchanged — they already take graph and return graph. Only the orchestration changes.

**Risk:** The current anuvada-ganana has viveka detection, count detection, intent guards, and proof-graph selection interleaved with the pipeline. These need to move into the DETECT and DISPATCH layers cleanly.

**Approach:** Keep anuvada-ganana working throughout. Build the new orchestrator as a parallel path, test against all 24+39 tests, then swap.

## Tantra4 Design Spec — The New Tantras

The pipeline architecture is now in the graph as 20 .om nodes. Each layer knows its order (krama), its data flow (janya/phala), its implementing tantra (kriya), and its mathematical identity (abheda). The tantras must now be rewritten to match.

**What exists in the graph (walk pipeline-construct krama 7):**

pipeline-construct → pipeline-assert → pipeline-refine → pipeline-expand → pipeline-detect → pipeline-dispatch → pipeline-proof-emit

Each layer has:
- janya: what it reads (sentence, raw-graph, asserted-graph, refined-graph, expanded-graph, intent-signals, answer)
- phala: what it produces (raw-graph, asserted-graph, refined-graph, expanded-graph, intent-signals, answer, formatted-answer)
- kriya: which tantra implements it
- abheda: what mathematical pattern it IS
- krama: next layer in sequence

**Mathematical identities (walk layer abheda):**

| Layer | IS (abheda) | Method (kriya) |
|---|---|---|
| construct | transducer | build-question-graph |
| assert | (morphism) | assertion-bandha |
| refine | endomorphism | op-fixpoint + grade-sparsha |
| expand | morphism | kosha-expand |
| detect | morphism | extract-solve-for + prathama-sparsha + anumana-sparsha |
| dispatch | conditional | viveka-ganana / derive-chain / anumana-viveka |
| proof-emit | morphism | pramana-bandha + emit-reasoning |

**Refine sub-chain (walk refine-sandhi-kosha krama 9):**

All 9 sub-steps are endomorphisms (graph → graph, monotone — triples only added). Connected via krama:
sandhi-kosha → sandhi-avastha → sandhi-bandhana → vibhakti-shashthi → vishesa-instance → rashi-viveka → vishesa-bandhana → rashi-anuvada → sankhya-bandha

**Dispatch paths (walk-in pipeline-dispatch swarupa):**

4 exclusive paths, each with kriya to implementing tantras:
- dispatch-anumana (categorical yes/no) → anumana-viveka, anumana-viveka-yukta
- dispatch-viveka (comparison) → viveka-ganana — IS fold over partial-order
- dispatch-count (arithmetic) → result pre-computed in refine — IS fold over graded-ring
- dispatch-derive (physics/math) → derive-chain, match-mantra, execute-matched

## Design Spec — The New Orchestrator

The 133-line anuvada-ganana.tantra3 dissolves into a generic orchestrator that reads the graph.

**Current (hardcoded):**
```
raw-graph = build-question-graph sentence
asserted = assertion-bandha raw-graph
refined = grade-sparsha asserted
expanded = kosha-expand refined
sf-result = extract-solve-for expanded
... (90 more lines of inline viveka/count/anumana detection) ...
answer = cond is-anumana ... otherwise (cond is-viveka ... otherwise ...)
```

**New (graph-driven):**
```
tantra3 anuvada-ganana
takes sentence

-- walk the krama chain from pipeline-construct
layers = walk "pipeline-construct" "krama"

-- sequential composition: each layer's kriya tantra takes previous output
graph = sentence
graph = (walk "pipeline-construct" "kriya") graph    -- build-question-graph
graph = (walk "pipeline-assert" "kriya") graph       -- assertion-bandha
graph = (walk "pipeline-refine" "kriya") graph       -- grade-sparsha (fixpoint inside)
graph = (walk "pipeline-expand" "kriya") graph       -- kosha-expand

-- detect: parallel reads (all read expanded, produce signals)
signals = detect-all graph

-- dispatch: conditional on signals
answer = dispatch-by-signal graph signals

-- proof + emit
proof-graph = pramana-bandha graph ...
answer = emit-reasoning proof-graph

return answer
done
```

**The key change**: the tantra reads the graph to know what to call and in what order. Adding a new layer = adding an .om node with krama edges. The orchestrator doesn't change.

**What stays the same**: individual tantras (sandhi-kosha, vibhakti-shashthi, etc.) are unchanged. They already take graph and return graph. Only the orchestration changes.

**Risk mitigation**: The detect + dispatch section of anuvada-ganana has interleaved viveka detection, count detection, intent guards, and proof-graph selection. These need careful separation into the DETECT and DISPATCH layers. The approach: build the new orchestrator alongside the old one, test against all 24+39 tests, swap when identical.

**The 7 patterns matter here**: the orchestrator IS a scan-accumulate (walk the krama chain, accumulate graph state) composed with a conditional (dispatch). The individual layers are endomorphisms (graph→graph). This composition is declared in the graph via abheda edges.

## Design Spec — What Each Layer's Tantra Becomes

**[WRONG]** → corrected in tantra.section-20

**CONSTRUCT (build-question-graph)** — unchanged. It IS the transducer. Takes sentence, emits triples via the scan-accumulate pattern. sandhi-viveka and emit-triples are called internally. Subgraph passing (current-grade, entity-registry, binding-ledger, grammar-trail) stays.

**ASSERT (assertion-bandha)** — unchanged. Reads copula signals, emits swarupa/varga edges.

**REFINE (grade-sparsha)** — structurally unchanged but now the graph declares its composition:
- pipeline-refine abheda → endomorphism (what it IS)
- pipeline-refine kriya → op-fixpoint (HOW it iterates)
- refine-sandhi-kosha krama 9 → the sub-step sequence
- Each sub-step IS an endomorphism (monotone: triples only grow)
- grade-sparsha wraps avrti-refine in fixpoint, then runs count-chain per grade
- The sandhi-bandhana constraint remains: session prior-graph injects AFTER refine, before expand

**EXPAND (kosha-expand)** — unchanged. Morphism from kosha → question graph.

**DETECT** — this is WHERE the current monolith needs real surgery. Currently interleaved in anuvada-ganana lines 20-80. Must become a clean tantra:
```
tantra3 detect-signals
takes graph
-- parallel reads, no graph mutation
sf-result = extract-solve-for graph
entities = prathama-sparsha graph
anumana-ctx = anumana-sparsha graph  -- NB: reads refined, not expanded
-- viveka: scan subjects for viveka-max/viveka-min words
-- count: read pre-computed count-total/count-remaining from graph
-- intent: has-intent from sf-result
return [sf, entities, is-viveka, is-count, is-anumana, has-intent, ...]
done
```

**DISPATCH** — the 4-way conditional. Currently 40 lines of nested cond in anuvada-ganana. Becomes:
```
tantra3 dispatch-answer
takes graph signals
mode = cond (nth signals is-anumana-idx) "anumana"
       otherwise (cond (nth signals is-viveka-idx) "viveka"
       otherwise (cond (nth signals is-count-idx) "count"
       otherwise (cond (nth signals has-intent-idx) "derive"
       otherwise "no-match")))
-- each path calls its dispatch tantra
answer = cond (eq mode "anumana") (anumana-path graph signals)
         otherwise (cond (eq mode "viveka") (viveka-path graph signals)
         otherwise (cond (eq mode "count") (count-path graph signals)
         otherwise (cond (eq mode "derive") (derive-path graph signals)
         otherwise "no match")))
return answer
done
```

**PROOF (pramana-bandha)** — unchanged. Takes graph + result + mantra, binds proof edges.

**EMIT (emit-reasoning)** — unchanged. Walks proof-graph, produces natural language via panchaavayava (5-limbed proof: pratijna, hetu, udaharana, upanaya, nigamana).

**What this means**: only 2 new tantras needed (detect-signals, dispatch-answer). The existing tantras move to new directories but keep their code. anuvada-ganana shrinks from 133 lines to ~20 lines of orchestration.

## Design Spec — Vibhakti Mode Dispatch (Future)

The current pipeline only handles ganana (computation). The plan (pathram show plan) defines 4 modes of address via vibhakti:

| Mode | Vibhakti | Signal | Status |
|---|---|---|---|
| sambodhana | vocative | hello/hi/hey → shabda signal | Signal done, response pending |
| darshana | nominative | "what is X?" — vidhi-kaala + satya + NO sankhya | Not built |
| prajna-dana | accusative | "ball has mass 5" — NO vidhi-kaala, NO prashna | Not built |
| ganana | imperative | "find KE" — vidhi-kaala + sankhya | Current pipeline |

The new orchestrator should support this. Before the 7-layer pipeline runs, a mode-detect step checks the vibhakti. Only ganana uses the full pipeline. The others route to simpler tantras.

This does NOT need an .om node yet — it's not built. When it is built, add:
```
pipeline-mode-detect → krama → pipeline-construct (for ganana)
pipeline-mode-detect → kriya → detect-vibhakti-mode
```

The .om architecture is ready to absorb this: just prepend to the krama chain.

## Design Spec — Constraints and Invariants

Constraints from the documentation that the redesign MUST preserve:

**1. Pipeline is accumulation, not transformation** (03-pipeline.md)
Each stage reads the graph state the previous stage left. Nothing is discarded. The graph only GROWS within a stratum. This is why all refine sub-steps are monotone endomorphisms.

**2. Sandhi-bandhana constraint** (04-entities.md)
Prior-graph (session state) injects AFTER avrti-refine, BEFORE kosha-expand. Session entities from prior turns must not enter sandhi-bandhana (it would corrupt their subjects). This constraint is non-negotiable and must survive the redesign.

**3. Subgraph passing** (18-philosophy.md, insight #3)
emit-triples receives 4 focused subgraphs [current-grade, entity-registry, binding-ledger, grammar-trail]. These model working memory of comprehension. The redesign must not flatten these into a single graph pass.

**4. anumana-sparsha reads REFINED, not expanded** (from anuvada-ganana source)
The detect layer is not purely parallel — anumana-sparsha reads the refined graph while extract-solve-for reads the expanded graph. The new detect-signals tantra must respect this.

**5. Count is pre-computed** (from trace analysis)
Count arithmetic happens during REFINE (grade-sparsha → count-chain). By dispatch time, the result is already in the graph as [count-total, sankhya, N]. dispatch-count just reads it.

**6. 24 tests MUST pass, 39 xfails MUST stay xfail** (baseline: 78/39/0 in v2)
The redesign is a refactor. Zero behavior change. Any test flip means a bug in the migration.

**7. The individual tantras don't change**
sandhi-kosha, vibhakti-shashthi, derive-chain, emit-reasoning, etc. — all keep their code. Only the orchestration (anuvada-ganana) and the directory structure change.

## Design Spec — Implementation Steps

**[WRONG]** → corrected in tantra.section-21

**Step A: Extract detect-signals tantra**
Pull lines 20-80 of anuvada-ganana into a new tantra: detect/detect-signals.tantra3. Takes expanded graph (and refined for anumana-sparsha). Returns a signal list: [has-intent, sf, scope-entity, is-viveka, viveka-dir, comp-word, comp-concept, is-anumana, anumana-query, anumana-assert, anumana-mode, is-count, count-result]. Test: all 24 pass.

**Step B: Extract dispatch-answer tantra**
Pull lines 80-120 of anuvada-ganana into: dispatch/dispatch-answer.tantra3. Takes graph + signals. Returns answer. The 4-way cond moves here. Test: all 24 pass.

**Step C: Slim anuvada-ganana to orchestrator**
anuvada-ganana becomes ~20 lines:
1. build-question-graph → assertion-bandha → grade-sparsha → kosha-expand (4 sequential calls)
2. detect-signals (reads expanded + refined)
3. dispatch-answer (conditional on signals)
4. pramana-bandha + emit-reasoning (proof + output)
Test: all 24 pass, all 39 xfail unchanged.

**Step D: Add shabda metadata**
Create tantra-pipeline.shabda with composition types per layer:
- pipeline-construct composition:sequential
- pipeline-refine composition:fixpoint
- pipeline-dispatch composition:conditional
- refine-* composition:sequential

**Step E: Update pathram math**
Make pathram math read the pipeline function from krama chain + janya/phala instead of static tantra file parsing. The pipeline description becomes self-derived from the graph.

**Verification at each step:**
```
python3 -m pytest tools/v2/test_answers.py -x -q  # 24 pass
python3 -m pytest tools/v2/test_xfail.py -x -q    # 39 xfail
python3 -m tools vy trace 'mass is 5 and velocity is 10. find kinetic energy'  # KE=250
python3 -m tools vy trace 'ball-A has mass 5. ball-B has mass 3. which is heavier'  # ball-A
python3 -m tools vy trace '10 birds sat on a tree. 3 flew away. how many birds are left'  # 7
```

## Tantra5 — S-Expressions and the Relational Model

Tantra5 is the fifth generation. Each generation deepened what "weaving" means:

- **tantra1** (2025): OCaml functions calling OCaml functions
- **tantra2** (2025): declarative let-blocks parsed into AST
- **tantra3** (2026-01): scan blocks, pipe syntax, graph-native resolution
- **tantra4** (2026-03): named helpers, signal bus, 4-layer composition
- **tantra5** (2026-03): s-expression syntax, relational graph model, sentence tantras

**What changed in tantra5:**

1. **S-expression format.** `(tantra name (params) body)` — last expression is return. 145 files, zero .tantra3.

2. **Scan eliminated.** The imperative scan construct (mutable state + pattern matching) replaced by grade-scoped sequential reduce within sentences + relational joins across sentences. No mutable state anywhere.

3. **Sentence tantras.** With sufficient named helpers, pipeline orchestrators read as prose: "the answer is the viveka answer or the physics answer." dispatch-answer: 57 lines → 7 lines.

4. **Relational consumers.** viveka-ganana joins entities→ownership→values through typed edges. extract-solve-for queries the question grade. No positional scanning across the full graph.

5. **Grade = fact set.** The graded ring's sentence boundary IS the Datalog stratification boundary. Within a grade: sequential (ordering matters). Across grades: relational (ordering irrelevant).

**The key insight:** scan was a flatmap (rewrite), not an append. Replacing it with append broke ordering that downstream consumers depended on. The fix: make consumers relational → ordering doesn't matter → producers can append safely. The graph IS a relational database stratified by sentence boundaries.

## Design Spec — Full Tantra Rewrite Scope

The redesign is NOT just the orchestrator. 42 tantras (2762 lines out of 3532) contain significant hardcoded logic that the graph already declares. The rewrite dissolves hardcoded strings, word lists, unrolled loops, and inline operation dispatch into graph reads.

**What changes per tantra category:**

HIGH DENSITY (rewrite substantially — 12 tantras, ~1100 lines):
- anuvada-ganana (133L) → slim to ~20L orchestrator reading krama chain
- count-chain (136L) → replace inline direction/op dispatch with graph walks
- derive-chain (80L) → replace 3 unrolled steps with fixpoint
- count-bandha (105L) → replace 18+5 hardcoded word lists with shabda reads
- emit-count (120L) → replace inline word selection with shabda reads
- viveka-ganana (95L) → replace inline gt/lt with walk viveka-max/min abheda → op
- scope-vps (68L) → reduce inline set operations
- emit-anumana (100L) → use graph for proof structure
- emit-pratijna (68L) → shabda reads for speech templates
- emit-udaharana-upanaya (76L) → shabda reads
- invert-math (56L) → already partially graph-driven, finish it
- materialize-question-graph (50L) → reduce conds with graph reads

MEDIUM DENSITY (simplify — 15 tantras, ~700 lines):
- match-mantra, sandhi-viveka, emit-reasoning, execute-mantra, sandhi-avastha,
  relative-vps, kosha-expand, build-question-graph, emit-hetu, emit-nigamana,
  entity-props-str, mantra-seen-str, anumana-sparsha, anumana-viveka-yukta,
  list-join

LOW / UNCHANGED (keep — 31 tantras, ~750 lines):
- assertion-bandha (scan-based, correct)
- The 9 refine sub-steps (already clean graph→graph endomorphisms)
- The 11 equation tantras (pure math, 12-15 lines each)
- boot tantras, debug, lookup

**The template pattern (from derive-step, the cleanest tantra3):**
```
-- derive-step already reads the graph:
ct = om-contract mantra-name      -- [janya, phala, kriya] in one call
janya = nth ct 0                  -- what it needs
phala = nth ct 1                  -- what it produces
-- no hardcoded concept names. the om node IS the spec.
```

**What replaces the hardcoded logic:**

| Hardcoded pattern | Count | Graph replacement |
|---|---|---|
| String literal edge names ("sankhya", "satya") | 81 refs | om-yukta, om-sthita reads |
| Word lists (18 subtraction words, 8 avastha words) | 5 lists | shabda reads from kosha |
| Unrolled loops (step1/step2/step3) | 3 tantras | fixpoint or bounded iteration |
| Inline op dispatch (kshaya→sub, vriddhi→add) | ~20 refs | walk kriya + shabda eval |
| Inline speech templates ("plus", "minus") | ~15 refs | shabda word reads |

**Estimated result:**
- 12 HIGH tantras: ~1100 lines → ~500 lines (50% reduction)
- 15 MED tantras: ~700 lines → ~550 lines (20% reduction)
- Total: 3532 lines → ~2800 lines, with dramatically more graph connectivity
- Every graph read is a new edge the system walks — density increases

## Design Spec — Revised Implementation Plan

**Phase 1: The Orchestrator (anuvada-ganana)**
Extract detect-signals + dispatch-answer. Slim anuvada-ganana to ~20 lines reading krama chain. Test: 24 pass, 39 xfail. This unblocks everything else.

**Phase 2: The Dense Core (6 tantras, biggest impact)**
1. derive-chain → fixpoint replaces 3 unrolled steps (~50 lines saved)
2. count-chain → graph walks replace inline direction/op dispatch (~40 lines saved)
3. count-bandha → shabda reads replace 23 hardcoded words (~30 lines saved)
4. viveka-ganana → walk abheda for op dispatch instead of inline gt/lt
5. invert-math → finish graph-driven inverse (already partial)
6. emit-count → shabda word reads replace inline strings

**Phase 3: Medium Tantras (graph reads replace string literals)**
Replace the 81 hardcoded kosha references with om-* / shabda / walk reads. Each replacement:
- Removes a string literal
- Adds a graph edge traversal
- Makes the tantra work for ANY concept, not just the hardcoded one

**Phase 4: Emit Tantras (speech from shabda)**
emit-pratijna, emit-hetu, emit-nigamana, emit-udaharana-upanaya, emit-anumana — all read speech templates from anuvada-setu.shabda. Replace inline speech strings.

**Phase 5: Shabda Metadata**
Create tantra-pipeline.shabda with composition types:
- pipeline-construct composition:sequential
- pipeline-refine composition:fixpoint
- pipeline-dispatch composition:conditional
- refine-* composition:sequential

**Phase 6: pathram math self-derivation**
Make pathram math read pipeline function from krama chain + janya/phala instead of static file parsing.

**At each phase: run full test suite. Zero behavior change.**
```
python3 -m pytest tools/v2/test_answers.py -x -q  # 24 pass
python3 -m pytest tools/v2/test_xfail.py -x -q    # 39 xfail
python3 -m tools vy trace 'mass is 5 and velocity is 10. find kinetic energy'
```

Phase 1 complete: anuvada-ganana 133→27 lines. Extracted detect-signals (53 lines) and dispatch-answer (83 lines). All 24 tests pass, 39 xfail unchanged. Key fix: tantra3 parser requires return <variable>, not return [...]. Added 15 missing kriya edges + 2 new tantra kriya edges to .om architecture nodes.
