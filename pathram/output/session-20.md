# Session 20 — Pathram + Mathematical Formalization

## What was built: pathram

Living documentation system (python3 -m pathram). Renamed from patra to pathram.

**Package**: pathram/ with 8 modules:
- data.py — JSON storage + State class with in-memory indexes
- store.py — CRUD for docs, entries, sessions, baselines, refs + ops log
- query.py — search, by_tag, by_session, steps, gaps, quirks, topic, timeline
- emit.py — render to markdown, glance, index, report, timeline
- bridge.py — live data from tools/ (om, tantras, shabda, cache) + math emission
- cli.py — argparse dispatch for all commands
- __init__.py — Python API (discover, step_done, step_add, note, glance)
- __main__.py — entry point

**Storage**: pathram/data/*.json (docs, entries, sessions, baselines, refs, ops)

**Key command**: `pathram math` — generates full mathematical description from the live graph. Operations, mantra signatures, algebraic hierarchy, pipeline composition, visheshanam ring — all pulled dynamically.

## What was built: kosha nodes

Three new kosha nodes formalizing the pipeline mathematics:

1. **endomorphism** (kosha/math/algebra/operations/endomorphism.om, satya=0.89)
   - morphism-swarupa, homomorphism-abheda, function-sthita, category-sthita
   - composition-kriya, avrti-kriya — composition of endomorphisms IS avrti
   - fixed-point-phala, convergence-phala — iterated application converges
   - closure-siddha, associativity-siddha — composition is closed and associative

2. **monotone-map** (kosha/math/algebra/operations/monotone-map.om, satya=0.85)
   - endomorphism-abheda, partial-order-sthita, lattice-sthita
   - fixed-point-siddha — monotone on complete lattice guarantees fixpoint (Knaster-Tarski)
   - This is THE property that makes avrti-refine terminate: triples only added, never removed

3. **transducer** (kosha/computation/transducer.om, satya=0.83)
   - morphism-abheda, op-reduce-abheda, fold-yukta, map-yukta
   - emit-triples IS this: reads (word, info), maintains 4 subgraph state, emits triples

## Discovery: the graph describes its own math

The kosha already contains the complete mathematical specification of the system. pathram math reads it live:

- 32 operations with eval/arity/inverse declared in shabda
- 23 physics mantras as typed functions: f(janya) → phala via kriya
- Algebraic hierarchy: monoid → group → ring → graded-ring with structural permissions
- 38-element visheshanam ring (non-commutative, 10 core + 28 extended dimensions)
- Pipeline as composition of 74 tantras through the call graph

No additional tooling needed in tantra to identify math — shabda reads + walk reads + om-* primitives already expose everything.

## Discovery: om-* primitives

OCaml primitives in yantra_eval_primitives.ml that let tantras read the graph directly:

| Primitive | Arity | What |
|---|---|---|
| om-janya | 1 | node → deduplicated input concepts |
| om-phala | 1 | node → deduplicated output concepts |
| om-kriya | 1 | node → deduplicated actions |
| om-yukta | 1 | node → deduplicated properties |
| om-sthita | 1 | node → deduplicated contexts |
| om-swarupa | 1 | node → deduplicated identities |
| om-abheda | 1 | node → deduplicated equivalences |
| om-contract | 1 | node → all 7 at once (one graph touch) |

**Used**: om-janya (7 uses), om-phala (5 uses), om-swarupa (2 uses)
**Unused**: om-kriya (0), om-contract (0), om-yukta (0), om-sthita (0), om-abheda (0)

om-kriya not being used means execute-mantra reads kriya via shabda instead of walking the edge. om-contract exists as optimization but nobody calls it.

## Discovery: op-class taxonomy

99 ops in 7 algebraic classes in kosha/yantra/:

| Class | Count | Mathematical structure |
|---|---|---|
| op-class-monoid | 6 | add, mul, concat, append, and, or — associative + identity |
| op-class-binary | 7 | sub, div, power, mod, max, min, atan2 — asymmetric binary |
| op-class-relation | 9 | eq, neq, gt, lt, ge, le, member, starts-with, ends-with — predicates |
| op-class-projection | 47 | abs, sin, cos, sqrt, length, exists, ... — unary transforms |
| op-class-higher-order | 6 | reduce, map, filter, fixpoint, iterate, first-match — take functions |
| op-class-keyed | 10 | walk, walk-in, shabda, nth, split, ... — graph queries |
| op-class-constructor | 2 | pair, bind — structure builders |
| op-class-pipeline | 4 | resolve-direct, resolve-inverse, resolve-chain, resolve-reason |

op-class-monoid already has monoid-abheda ✓. All other classes are disconnected from math kosha.

## Discovery: connected vs disconnected math

**Already connected** (tantras read math from kosha):
- count-chain reads graded-ring.grade-boundary → viraam
- count-chain reads common-sense-events → kshaya/vriddhi direction
- count-chain reads addition.eval → add, subtraction.eval → sub
- viveka-ganana reads direction.eval → max/min, walks pratipaksha → opposite
- invert-math reads mantra shabda pratipaksha-N → inverse op per argument
- execute-mantra reads shabda math-op → operation name
- derive-step/derive-chain read om-janya, om-phala via om-* primitives
- mantra-select walks physics-mantra varga (not hardcoded list)
- emit-count reads addition.word → plus, subtraction.word → minus

**Not connected** (hardcoded math that should come from kosha):
- avrti-refine: 9 sub-tantras in fixed order, no connection to endomorphism
- grade-sparsha: "dvandva" hardcoded as boundary string
- count-chain: seed 0 hardcoded — should read identity-element → shunya
- count-chain: kshaya→subtraction is inline cond — should walk kshaya→kriya
- derive-chain: 3-step hardcoded — should read max-depth from convergence
- anumana-viveka: 4-level varga walk hardcoded — should read depth from partial-order
- build-question-graph: "viraam" and "dvandva" hardcoded — should read visheshanam-ring
- op-class-higher-order: no connection to endomorphism, morphism, category
- op-class-relation: no connection to partial-order
- op-class-projection: no connection to morphism
- op-class-pipeline: no connection to endomorphism, monotone-map

## Discovery: pipeline mathematical identity

Each pipeline tantra embodies a specific mathematical structure, now readable from the graph:

| Tantra | IS | Graph evidence |
|---|---|---|
| avrti-refine | monotone endomorphism under fixpoint | endomorphism→kriya→avrti, monotone-map→siddha→fixed-point |
| count-chain | fold over graded ring with monoid seed | graded-ring→kriya→addition, monoid→drishthanta→addition |
| emit-triples | finite state transducer | transducer→abheda→op-reduce |
| viveka-ganana | total order comparison on poset | partial-order→siddha→[reflexive, antisymmetric, transitive] |
| derive-chain | bounded iteration of endomorphism | convergence→phala→limit |
| sandhi-kosha | string rewriting system (compound resolution) | sandhi→kriya→kosha |
| assertion-bandha | Datalog rule (IS-A inference) | anumana→morphism |
| grade-sparsha | graded ring decomposition $R = \bigoplus R_n$ | graded-ring→swarupa→direct-sum |

The full pipeline is:

$$\text{answer} = (\text{emit} \circ \text{pramana} \circ \text{execute} \circ \text{match} \circ \text{expand} \circ \text{refine} \circ \text{build})(\text{sentence})$$

Each stage is a monotone endomorphism: $f_i : G \to G$ where $G$ is the question graph. Monotonicity (triples only added, never removed) guarantees fixpoint existence via Knaster-Tarski.

## Plan: vartamana migration

Dissolve 26 vartamana files into pathram documents. Not 1:1 — let structure emerge.

**What to keep** (current truths, philosophy of implemented things):
- nam philosophy (01-nam.md) → pathram doc "nam"
- Six insights (18-philosophy.md) → pathram doc "tantra" 
- 22 key principles (index.md) → pathram doc "principles"
- Active plan (18-implementation.md) → pathram doc "plan"
- Tantra3 philosophy (14-tantra3.md) — om graph IS the program
- Pipeline architecture (03-pipeline.md) — expansion→connection→compression
- Entity model (04-entities.md) — entity=simulation object, gaps
- Adhyayana / session (09-adhyayana.md) — three learning loops
- Tantra spec (tantra2-spec.md) — authoring reference, still active

**What to drop** (historical, superseded, implementation details):
- tantra2 notation/philosophy (11, 12) — subsumed by tantra3
- tantra rewrite (07) — tensions resolved
- Session (05) — absorbed into adhyayana
- 17-series (17, 17a, 17b, 17c) — absorbed into 18-philosophy
- tantra3 implementation (15) — steps done
- let-binding fix (16) — completed
- boot architecture (08) — reference only

**What to add** (not in vartamana, discovered this session):
- Mathematical formalization of the pipeline (from pathram math)
- Test documentation with philosophical nature
- Connected vs disconnected math inventory
- om-* primitive documentation

## Plan: pratibimba migration

Dissolve 13 pratibimba files into pathram. These are aspirational — tag as provisional.

**Core contracts to preserve**:
- avrti IS the frame (render loop = pipeline = simulation = convergence)
- Grammar not translation — pratibimba is another anuvada
- EpochOutput is the sole boundary (OCaml→Rust)
- The graph IS the scene — no separate scene data structure
- Entity-as-camera — any entity can be the eye
- Kosha IS the specification — shaders implement kosha nodes
- Thin render layer — all intelligence in graph
- Three nested avrti (session/simulation/frame)
- Loro CRDT as shared state
- wgpu not OpenGL, cpal not SDL, Slint for UI

**Implementation details to skip**: crate layout, FFI details, build order, keyboard shortcuts

## Plan: kosha math enrichment

Connect the op-class nodes and op-* nodes to the algebraic hierarchy.

**Phase 1 — op-class connections** (enrich existing .om files):

| Node | Add edges |
|---|---|
| op-class-higher-order | endomorphism-abheda, morphism-yukta, category-sthita |
| op-class-relation | partial-order-abheda |
| op-class-binary | group-sthita (inverses exist but no identity) |
| op-class-projection | morphism-abheda (projections ARE morphisms) |
| op-class-pipeline | endomorphism-abheda, monotone-map-abheda |

**Phase 2 — individual op enrichment**:

| Node | Add edges |
|---|---|
| op-reduce | monoid-sthita, fold-abheda, transducer-abheda |
| op-fixpoint | endomorphism-janya, convergence-phala, monotone-map-sthita, fixed-point-phala |
| op-map | morphism-abheda |
| op-filter | partial-order-sthita, lattice-kriya |

**Phase 3 — tantra kosha reads** (replace hardcoded values with graph reads):

| Tantra | Hardcoded | Replace with |
|---|---|---|
| count-chain | seed 0 | walk identity-element → shunya or read from monoid |
| count-chain | kshaya inline cond | walk kshaya → kriya → subtraction |
| grade-sparsha | "dvandva" string | second boundary from graded-ring shabda |
| anumana-viveka | 4-level depth | read from partial-order or lattice depth |
| execute-mantra | shabda for kriya | om-kriya (currently 0 uses) |

**Phase 4 — use om-contract**: replace multiple om-janya + om-phala calls with single om-contract call in derive-step and match-mantra.

## Plan: pathram math tool

Refine the pathram math emission to produce paper-quality output.

Current `pathram math` generates:
- Operation algebra table (32 ops with eval/arity/inverse)
- Mantra signatures as typed functions
- Algebraic hierarchy
- Pipeline composition
- Visheshanam ring dimensions

**Needs refinement**:
- Clean node name display (strip path prefixes)
- Group operations by class (monoid/binary/relation/projection/higher-order)
- Show pipeline tantras as mathematical structures (FST, fixpoint, fold) not just call counts
- Show the graded ring decomposition with proper LaTeX
- Show the four question types (physics/viveka/count/anumana) as distinct mathematical paths
- Show the proof structure (panchaavayava) as formal deduction
- Include what tests verify about each structure

## Discovery: seven abstract patterns across tantras

Every tantra is composed from seven abstract patterns. Each pattern has a distinct mathematical nature:

**1. Filter-Collect** (168 occurrences) — Relational algebra
```
graph | where [s, e, o] | and (eq e "satya") | collect s
```
Math: Selection σ + Projection π on a relation. Pure math, no state.
$$\sigma_{e=\text{satya}}(\pi_s(G))$$

**2. Scan-Accumulate** (12 tantras) — Finite state transducer
```
reduce graph [state...] (fn state triple -> ...)
```
Math: Mealy machine / FST. Procedure with state. The state IS the epistemic position — what has been seen, what is active, what is open. Each triple advances the automaton.
Examples: viveka-ganana, extract-solve-for, sandhi-kosha, emit-triples

**3. Shabda-Read** (69 occurrences) — Kosha morphism
```
shabda "addition" "eval" → "add"
```
Math: Morphism from name-space to property-space. $\phi: \text{Node} \times \text{Key} \to \text{Value}$. Pure lookup, no side effects. This is how tantras read the kosha instead of hardcoding.

**4. Walk** (38 occurrences) — Transitive closure
```
walk "kinetic-energy-mantra" "janya" → [mass, velocity]
```
Math: Transitive closure on a relation. $\text{walk}(n, r) = \{t : (n, r, t) \in E\}$. Graph traversal as type inference — janya edges ARE type declarations, the walk IS the type checker.

**5. Fixpoint** (5 call sites) — Knaster-Tarski convergence
```
fixpoint graph (fn g -> avrti-refine g)
```
Math: Least fixpoint of monotone endomorphism on complete lattice. $\text{lfp}(f) = \bigcap\{x : f(x) \leq x\}$. The constraint is monotonicity: triples only added, never removed. Used for avrti-refine and derive-step.

**6. Apply-Op** (9 occurrences) — Operation dispatch
```
apply-op "sub" [10, 3] → 7
```
Math: Evaluation morphism. $\text{eval}: \Sigma \times V^n \to V$. The shabda declares the operation, apply-op fires it. Constraint: arity must match, operands must be numeric.

**7. Om-Read** (14 occurrences via om-janya/phala/swarupa) — Graph as program
```
om-janya "kinetic-energy-mantra" → [mass, velocity]
```
Math: Reading the declaration AS the specification. janya = function domain, phala = codomain, kriya = implementation. $f: \text{janya} \to \text{phala}$ via kriya. This is tantra3 — the om graph IS the program.

**Cross-cutting: Word-Resolve** (20 occurrences via word-node + shabda-anveshana)
```
word-node "heavier" → viveka-max
shabda-anveshana "birds" → bird
```
Math: Lexicon morphism. $\lambda: \text{Word} \to \text{Node} \cup \{\bot\}$. Maps surface words to graph concepts. Includes stemming and alias resolution.

---

**Pattern composition**: a tantra is a composition of these patterns. For example, count-chain is:
1. filter-collect (extract satya concepts)
2. scan-accumulate (fold over grades with direction state)
3. shabda-read (common-sense-events → kshaya/vriddhi)
4. walk (kshaya → kriya → subtraction)
5. apply-op (sub [10, 3] → 7)

The seven patterns are the **instruction set** of the tantra language.

## Discovery: three kinds of pattern

The seven patterns fall into three mathematical kinds:

**Pure math** (stateless, algebraic):
- Filter-Collect — relational algebra (σ, π)
- Walk — transitive closure
- Shabda-Read — morphism (name → property)
- Om-Read — morphism (node → contract)
- Word-Resolve — morphism (word → concept)

These are pure functions. No side effects. Same input → same output. They compose freely. They ARE morphisms in the category of graphs.

**Math with constraints** (stateless but guarded):
- Apply-Op — evaluation morphism, constrained by arity and type
- Fixpoint — monotone endomorphism, constrained by monotonicity (only add, never remove)

These are still pure but have preconditions. Apply-op requires arity match. Fixpoint requires monotonicity. The constraints are structural permissions read from the algebraic hierarchy (monoid guarantees fold validity, distributivity validates compute-then-sum).

**Procedures** (stateful):
- Scan-Accumulate — finite state transducer with epistemic state

This is the only pattern with state. The state tracks what a reader knows at each point in the sentence: active concept, pending number, entity registry, grammar trail. The procedure IS comprehension — it models how understanding builds word by word.

Every tantra is a composition of pure morphisms, constrained operations, and at most one scan procedure. The scan is always the outermost structure — it drives the walk over the input. Inside the scan, the other patterns compose freely.
