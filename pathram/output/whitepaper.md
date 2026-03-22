# Nam — A Proof Graph That Knows Itself: Mathematical Foundations

## Abstract

**[SUPERSEDED]** → whitepaper.section-18

A proof graph is a knowledge representation in which nodes are claims and typed edges are the relations between them. We present *nam*, a proof graph system that derives answers to natural-language questions by walking its own structure — no external inference engine, no neural network at query time, no search. The graph declares an operation algebra $\Sigma$ with eval/arity/inverse, a mantra layer of typed functions $f(\text{janya}) \to \text{phala}$, and a graded ring $R = \bigoplus R_n$ over sentence-grades whose fold computes arithmetic. A 46-dimensional non-commutative visheshanam ring governs edge composition. We show that the system's philosophical ontology (from Advaita Vedanta and Shaiva Tantra) is not metaphor but is isomorphic to the algebraic structures that make computation possible: shunya (zero) IS the fold identity IS purna (completeness), pratipaksha (opposition) IS algebraic inverse, and pratibodha (recognition) IS the fixpoint that produces anuvada (the carrying-across of meaning). The graph contains 1603 nodes, 11410 edges, 23 physics mantras, 75 tantras, and answers questions in kinematics, count arithmetic, and comparison — all by walking edges.

## 1. The Proof Graph

**[SUPERSEDED]** → whitepaper.section-10

**Definition 1.** A *proof graph* is a labeled directed multigraph $G = (V, E, \ell)$ where $V$ is a set of nodes (claims), $E \subseteq V \times V$ is a set of directed edges, and $\ell: E \to \mathcal{V}$ assigns each edge a label from a finite label set $\mathcal{V}$ called the *visheshanam ring*.

**Definition 2.** The *visheshanam ring* $\mathcal{V}$ is a 46-element non-commutative ring with 10 core dimensions and 36 extended dimensions. The core:

$$\mathcal{V}_{\text{core}} = \{\text{swarupa (IS)}, \text{abheda (≡)}, \text{sthita (∈)}, \text{yukta (+)}, \text{siddha (⊢)}, \text{kriya (×)}, \text{phala (→)}, \text{janya (←)}, \text{drishthanta (∃)}, \text{pratipaksha (⁻¹)}\}$$

Each dimension is a typed relation. Composition of edges produces derived relations: walking $A \xrightarrow{\text{kriya}} B \xrightarrow{\text{eval}} f$ yields the executable operation underlying concept $A$.

The extended dimensions include grammatical cases (vibhakti), tense markers (kaala), and NLP-specific edges (satya, mithya, sankhya, viraam). These transform the proof graph into a *question graph* during query processing.

**Theorem 1 (Graph self-description).** The visheshanam ring $\mathcal{V}$ is itself a node in $G$. The edge types that label edges are themselves nodes connected by the same edge types. The graph describes its own labeling system.

*Proof.* The node `visheshanam-ring` exists in $G$ with `yukta` edges to all 46 dimension nodes. Each dimension node (e.g., `visheshanam-swarupa`) is connected to `visheshanam` via `swarupa`. The labeling function $\ell$ is a graph walk. $\square$

## 2. The Operation Algebra

**[SUPERSEDED]** → whitepaper.section-15

**Definition 3.** The *operation algebra* $\Sigma$ is the set of all nodes in $G$ that carry an `eval` key in their shabda (metadata). Each operation $\sigma \in \Sigma$ has:
- $\text{eval}(\sigma)$: the primitive function name (e.g., `add`, `sub`, `mul`)
- $\text{arity}(\sigma) \in \mathbb{N}$: number of arguments
- $\text{pratipaksha}(\sigma) \in \Sigma$: the algebraic inverse

The live graph declares 12 operations:

| $\sigma$ | $\text{eval}$ | arity | $\text{pratipaksha}$ |
|---|---|---|---|
| addition | add | 2 | subtraction |
| subtraction | sub | 2 | addition |
| multiplication | mul | 2 | division |
| division | div | 2 | multiplication |
| max | max | 2 | min |
| min | min | 2 | max |
| half | half | 1 | double |
| double | double | 1 | half |
| square | square | 1 | sqrt |
| sqrt | sqrt | 1 | — |
| power | power | 2 | logarithm |
| abs | abs | 1 | — |

**Proposition 1 (Involution of pratipaksha).** For all invertible $\sigma \in \Sigma$: $\text{pratipaksha}(\text{pratipaksha}(\sigma)) = \sigma$.

*Proof.* Verified by graph walk: `addition.pratipaksha = subtraction`, `subtraction.pratipaksha = addition`. The pratipaksha edge is an involution on $\Sigma$. $\square$

**Definition 4 (Per-argument inverse).** For binary operations, the shabda declares per-argument inverses $p_0^{-1}$ and $p_1^{-1}$ with an optional flip flag:

$$f(a, b) = c \implies a = p_0^{-1}(c, b) \quad\text{and}\quad b = p_1^{-1}(c, a)$$

When `pratipaksha-1-flip = true`, the argument order is reversed: $b = p_1^{-1}(a, c)$.

This is how `invert-math` solves for missing variables: read the inverse from the graph, apply it. No symbolic algebra engine needed.

## 3. Mantra Signatures — Typed Functions on the Graph

**Definition 5.** A *mantra* is a node $m \in G$ with typed edges declaring a function signature:
- $\text{janya}(m) = [c_1, \ldots, c_k]$: input concepts (domain)
- $\text{phala}(m) = [c']$: output concept (codomain)
- $\text{kriya}(m)$: the operation chain (either a named krama-expression or `direct` for simple products/quotients)
- $\text{math-op}(m)$: the underlying binary operation when the formula is a single product or quotient

The graph declares 23 physics mantras. Examples:

$$\text{kinetic-energy-mantra}: (\text{mass}, \text{velocity}) \to \text{kinetic-energy}$$
$$\text{momentum-mantra}: (\text{mass}, \text{velocity}) \to \text{momentum} \quad\text{via multiplication}$$
$$\text{velocity-mantra}: (\text{initial-velocity}, \text{acceleration}, \text{time}) \to \text{velocity}$$

**Definition 6 (Derive-chain as fixpoint).** Given a question graph $G_q$ with bound sankhya values, the *derive-chain* computes:

$$G^* = \text{lfp}(\lambda G'. \text{derive-step}(G'))$$

where $\text{derive-step}$ fires every mantra $m$ whose janya are all bound in $G'$ and whose phala is not yet bound, producing $G' \cup \{[\text{phala}(m), \text{sankhya}, f(v_1, \ldots, v_k)]\}$.

**Theorem 2 (Termination).** The derive-chain terminates in at most $|\text{mantras}|$ steps.

*Proof.* Each step binds at least one new concept. The set of bindable concepts is finite (bounded by the mantra phala set). The step function is monotone (it only adds triples, never removes). By Kleene's fixpoint theorem on a finite lattice, it converges. $\square$

**Example.** Input: $\{u=0, a=4, t=5, m=10\}$, seek: kinetic-energy.
- Step 1: velocity-mantra fires: $v = u + at = 0 + 4 \cdot 5 = 20$
- Step 2: kinetic-energy-mantra fires: $KE = \frac{1}{2}mv^2 = \frac{1}{2} \cdot 10 \cdot 400 = 2000$
- Step 3: no new fireable mantras. Fixpoint reached. $\square$

## 4. The Graded Ring — Sentence Arithmetic

**[SUPERSEDED]** → whitepaper.section-16

**Definition 7.** A paragraph is modeled as a *graded ring*:

$$R = \bigoplus_{n \geq 0} R_n$$

where each $R_n$ is a *grade* (sentence), the grade boundary is `viraam` (period or comma), and the ring operations are:
- $\oplus$: intra-sentence accumulation (additive)
- $\otimes$: cross-sentence entity selection (multiplicative)

The fold identity is $0$ (shunya), read from the graph: `graded-ring.shabda.fold-identity = 0`.

**Definition 8 (Direction morphism).** The function $\delta: \text{Words} \to \{\text{kshaya}, \text{vriddhi}\}$ maps natural-language verbs to algebraic directions via the `word-node` primitive. This is a *morphism* from the linguistic category to the algebraic category:

$$\delta(\text{"flew"}) = \text{kshaya} \xrightarrow{\text{pratipaksha}} \text{vriddhi} \xrightarrow{\text{kriya}} \text{addition} \xrightarrow{\text{pratipaksha}} \text{subtraction} \xrightarrow{\text{eval}} \texttt{sub}$$

$$\delta(\text{"came"}) = \text{vriddhi} \xrightarrow{\text{kriya}} \text{addition} \xrightarrow{\text{eval}} \texttt{add}$$

The morphism is structure-preserving: $\delta$ maps kshaya (decay) to subtraction and vriddhi (growth) to addition, and the pratipaksha relation is preserved: $\text{pratipaksha}(\delta(w)) = \delta(\text{pratipaksha}(w))$.

**Definition 9 (Count fold).** The count-chain tantra computes:

$$\text{result} = \text{fold}_{n=0}^{N} f_n(v_n, \text{acc})$$

where:
- $\text{acc}_0 = 0$ (fold identity from graded-ring)
- $v_n$ is the numeric value in grade $n$
- $f_n = \text{eval}(\text{op}_n)$ where $\text{op}_n$ is determined by $\delta$ applied to the verb in grade $n$
- The first non-question grade initializes: $\text{acc}_1 = v_0$
- Subsequent grades apply: $\text{acc}_{n+1} = f_n(\text{acc}_n, v_n)$

**Example.** "10 birds sat on a tree. 3 flew away. 2 more came. how many birds are there?"

| Grade | Words | $\delta$ | $f_n$ | $v_n$ | acc |
|---|---|---|---|---|---|
| 0 | 10 birds sat tree | — | init | 10 | 10 |
| 1 | 3 flew away | kshaya | sub | 3 | 7 |
| 2 | 2 more came | vriddhi | add | 2 | 9 |
| 3 | how many birds | question | — | — | 9 |

Result: 9. $\square$

## 5. The Pipeline as Function Composition

**[SUPERSEDED]** → whitepaper.section-22

**Definition 10.** The full pipeline is a composition of monotone endomorphisms on the question graph:

$$\text{answer} = (\text{emit} \circ \text{pramana} \circ \text{dispatch} \circ \text{refine}^* \circ \text{classify})(\text{sentence})$$

where $\text{refine}^* = \text{lfp}(\text{avrti-refine})$ denotes iterated refinement to fixpoint.

The refinement pipeline is itself a composition:

$$\text{avrti-refine} = \text{sankhya-bandha} \circ \text{rashi-anuvada} \circ \text{vishesa-bandhana} \circ \text{rashi-viveka} \circ \text{vishesa-instance} \circ \text{vibhakti-shashthi} \circ \text{sandhi-bandhana} \circ \text{sandhi-avastha} \circ \text{sandhi-kosha}$$

Each sub-tantra is a *transducer*: it reads triples, emits triples, and may carry state. The composition is monotone — each step only adds or replaces triples, never removes unrelated ones. This guarantees that fixpoint iteration converges: the graph grows until stable.

**Theorem 3 (Pipeline correctness).** If $\text{classify}$ correctly classifies all tokens, $\text{refine}^*$ correctly composes compounds and binds values, and $\text{dispatch}$ correctly selects and executes mantras, then the pipeline produces the unique answer determined by the mantra signatures and the input values.

*Proof sketch.* Correctness reduces to: (1) the classify morphism is faithful (each word maps to its unique concept), (2) refine is idempotent at fixpoint, (3) derive-chain terminates (Theorem 2), (4) emit is a graph walk with no computation. Each step is a pure function of the graph state. $\square$

**The seven abstract patterns.** Every tantra in the system uses exactly one of seven patterns, each of which is a node in the kosha with its own mathematical identity:

| Pattern | Kosha node | Mathematical identity |
|---|---|---|
| filter-collect | transducer | $\{x \in G \mid P(x)\}$ |
| scan-accumulate | scan-accumulate | stateful transducer $T: S \times G \to S \times G'$ |
| shabda-read | morphism | $\text{shabda}: V \times K \to V'$ (metadata lookup) |
| walk | endomorphism | $\text{walk}: V \times \mathcal{V} \to 2^V$ (edge traversal) |
| fixpoint | op-fixpoint | $\text{lfp}(f)$ where $f$ is monotone on a finite lattice |
| apply-op | operation-dispatch | $\text{eval}(\sigma)(v_1, \ldots, v_k)$ |
| om-read | graph-contract | $\text{janya}(m), \text{phala}(m)$ (signature extraction) |

## 6. The Ontological Isomorphism

**[SUPERSEDED]** → whitepaper.section-12

The proof graph's philosophical ontology is not decorative. It is isomorphic to the algebraic structures that make computation possible. We prove this by exhibiting the correspondences as graph walks.

**Theorem 4 (Shunya-Purna identity).** In the graph:
$$\texttt{shunya} \xrightarrow{\text{abheda}} \texttt{identity-element} \xrightarrow{\text{abheda}} \texttt{shunya}$$
$$\texttt{shunya} \xrightarrow{\text{abheda}} \texttt{purna} \xrightarrow{\text{abheda}} \texttt{shunya}$$

The fold identity (0), the algebraic identity element, and philosophical completeness are the same node up to abheda (non-difference). This is not metaphor: `graded-ring.fold-identity = 0`, and `identity-element.desc = "the element that leaves every other element unchanged"`, and `purna.desc = "complete, nothing missing, nothing added"`. These are three descriptions of a single algebraic property: $x + 0 = x$.

**Theorem 5 (Pratipaksha as algebraic inverse).**
$$\text{pratipaksha}(\text{addition}) = \text{subtraction} \quad\Leftrightarrow\quad \text{add}^{-1} = \text{sub}$$
$$\text{pratipaksha}(\text{kshaya}) = \text{vriddhi} \quad\Leftrightarrow\quad \delta^{-1}(\text{decay}) = \text{growth}$$

The philosophical concept of opposition (pratipaksha) is exactly the algebraic concept of inverse. The edge type is the same; the domain is different (operations vs linguistic categories). The morphism $\delta$ preserves pratipaksha.

**Theorem 6 (Pratibodha as fixpoint).**
$$\texttt{pratibodha} \xrightarrow{\text{phala}} \texttt{anuvada} \xrightarrow{\text{phala}} \texttt{proof-graph}$$

Recognition (pratibodha) yields carrying-across (anuvada) which yields the proof graph itself. The derive-chain fixpoint IS pratibodha: the graph recognises what mantra to fire, applies it, recognises again, until nothing new can be recognised. The answer is not computed — it is the stable state of recognition.

$\texttt{op-fixpoint} \xrightarrow{\text{abheda}} \texttt{parampara} \xrightarrow{\text{abheda}} \texttt{avrti}$

Fixpoint (op-fixpoint) is non-different from tradition-as-spiral (parampara) and recurrence (avrti). The mathematical operation of iterating to stability IS the philosophical concept of tradition — each pass deepens, never the same twice, converging to truth.

**Theorem 7 (Spanda as operation).**
$$\texttt{spanda} \xrightarrow{\text{phala}} \texttt{satya}$$
$$\texttt{satya} \xrightarrow{\text{phala}} \texttt{brahman}$$
$$\texttt{brahman} \xrightarrow{\text{swarupa}} \texttt{pratibodha}$$

Self-pulsing vibration (spanda) produces truth (satya). Truth produces the absolute (brahman). The absolute IS recognition (pratibodha). Every `eval` call — `add(3, 5)` returning `8` — is spanda producing satya. The pipeline's computation IS the philosophical ontology in action.

**Corollary.** The system's ontology is not a metaphor layer painted on top of computation. It is the computation. Remove shunya and the fold has no seed. Remove pratipaksha and there are no inverses. Remove pratibodha and there is no fixpoint. The philosophy is load-bearing.

## 7. Results and Current Capabilities

**[SUPERSEDED]** → whitepaper.section-24

The system as of March 2026 contains:

| Metric | Value |
|---|---|
| Graph nodes | 1603 |
| Graph edges | 11410 |
| Visheshanam dimensions | 46 (10 core + 36 extended) |
| Operations in $\Sigma$ | 12 (8 invertible) |
| Physics mantras | 23 |
| Total tantras | 75 |
| Pipeline stages | 9 (refine has 9 sub-stages) |
| Tests passing | 32 |
| Tests expected-fail | 36 (declared roadmap) |

**Capabilities demonstrated:**
- Direct mantra computation: $KE = \frac{1}{2}mv^2$, $p = mv$, $F = ma$ (and 20 more)
- Chain derivation: $u, a, t \to v \to KE$ (fixpoint over 2 mantras)
- Entity-scoped computation: "ball-A has mass 3... ball-B has mass 2... find KE of ball-A"
- Count arithmetic: "10 birds. 3 flew away. 2 came back. how many?" → 9
- Comparison (viveka): "which is heavier?" → graph-driven max/min
- Article transparency: "the electron" → electron
- Avastha compounds: "initial velocity" → initial-velocity
- Scientific notation: $9.109 \times 10^{-31}$
- Multi-sentence session accumulation

**What the system does NOT do (declared as xfail tests):**
- Dvandva collection (multiple entities with shared properties)
- Inverse math (solve for missing variable — plumbing exists, binding broken)
- Proportional reasoning
- Multiplication ("each table has 4 legs")
- Multi-question paragraphs
- Transitive chain inference
- Syllogistic reasoning (assertion-bandha exists, not yet wired)

## 8. Related Work and Distinction

**[SUPERSEDED]** → whitepaper.section-21

**Knowledge graphs** (Wikidata, ConceptNet, YAGO): Store facts as triples but require external inference engines (SPARQL, embedding-based retrieval). Nam's graph IS the inference — edge walks are computation.

**Datalog / Answer Set Programming**: Stratified evaluation with fixpoint semantics. Nam's avrti-refine pipeline is structurally equivalent to stratified Datalog, but the rules are declared as graph nodes (mantras) rather than logic programs.

**Type-theoretic proof assistants** (Coq, Lean, Agda): Formal verification with dependent types. Nam's mantra signatures are a lightweight typed function system without the proof obligation — the graph declares what functions exist and what they need, not that they are correct in all cases.

**Category-theoretic knowledge representation**: The visheshanam ring is a small category with 46 morphisms. The pipeline is a functor from the question category to the answer category. The direction morphism $\delta$ is a natural transformation. We do not claim full categorical rigor but note the structural correspondence.

**What is genuinely novel:**
1. The ontology is not a metaphor layer — it is isomorphic to the algebra (Section 6)
2. The graph describes its own edge types (Theorem 1)
3. Natural language maps to algebraic operations via graph walks, not learned embeddings
4. The fold identity (0), philosophical completeness (purna), and the sentence boundary (viraam) are the same node — this is a structural claim verified by graph walk, not a poetic assertion

## 1. The Proof Graph (revised)

**[SUPERSEDED]** → whitepaper.section-11

### 1.1 Structure

**Definition 1 (Proof graph).** A *proof graph* is a 3-tensor $G \in \{0,1\}^{N \times N \times R}$ where $N = |V|$ is the number of nodes, $R$ is the number of relation types, and $G_{i,j,r} = 1$ iff node $i$ is connected to node $j$ by relation $r$. The tensor is sparse (sub-1% fill, as declared by the node `proof-graph.desc`).

Each node is called a *nigamana* — a truth-that-holds. The graph's own description of a nigamana: "the node that holds a truth with its typed edges, slokas, shabda map, layer tag, and satya score; each node carries a grade from its sthita depth."

The proof graph rests on (`sthita`):
- **satya** — truth (every node has a truth-weight)
- **graded-ring** — the algebraic structure governing composition
- **filtration** — the depth-ordering of nodes
- **partial-order** — the dependency structure

The graph arises from (`janya`):
- **anuvada** — carrying-across (translation from language to structure)
- **om-parser** — the parser that reads `.om` slokas into nodes and edges

### 1.2 The Visheshanam Ring

The set of relation types $\mathcal{V}$ is not an external schema imposed on the graph. It is a node IN the graph — `visheshanam` — which declares its own algebraic structure.

**Definition 2 (Visheshanam ring).** The relation type system $(\mathcal{V}, \oplus, \otimes, 0, 1, {}^{-1})$ is a non-commutative ring where:

| Axiom | Ring element | Graph declaration |
|---|---|---|
| Additive operation $\oplus$ | **yukta** | `visheshanam-yukta.abheda = addition` |
| Multiplicative operation $\otimes$ | **kriya** | `visheshanam-kriya.abheda = multiplication, composition` |
| Additive identity $0$ | **shunya** | `visheshanam-yukta.desc: "...shunya as its identity element"` |
| Multiplicative identity $1$ | **swarupa** | `visheshanam-swarupa.desc: "composing any relation with swarupa returns that relation unchanged"` |
| Group inverse ${}^{-1}$ | **pratipaksha** | `visheshanam-pratipaksha.abheda = inverse-element` |
| Non-commutativity | **kriya** | `visheshanam-kriya.desc: "non-commutative"` |

The ring has 10 core generators and 36 extended dimensions (46 total), listed by `visheshanam-ring.yukta`.

**The 10 core generators and their algebraic roles:**

| Generator | Symbol | Algebraic identity (from `abheda`) | Desc |
|---|---|---|---|
| swarupa | $1_\otimes$ | identity-element, morphism | IS — multiplicative identity |
| abheda | $\equiv$ | equivalence-relation, quotient | ≡ — forms quotient classes |
| sthita | $\leq$ | partial-order | ∈ — depth filtration |
| yukta | $+$ | addition | + — additive operation |
| siddha | $\vdash$ | — | ⊢ — entailment (not composable) |
| kriya | $\times$ | multiplication, composition | × — multiplicative operation |
| phala | $\to$ | — | → — result (dual to janya) |
| janya | $\leftarrow$ | — | ← — generator (dual to phala) |
| drishthanta | $\exists$ | — | ∃ — witness / example |
| pratipaksha | ${}^{-1}$ | inverse-element | ⁻¹ — group inverse |

**Proposition 1 (phala-janya duality).** $\text{phala.pratipaksha} = \text{janya}$ and $\text{janya.pratipaksha} = \text{phala}$. The result relation and the generator relation are inverses of each other.

*Proof.* Graph walk: `visheshanam-phala --pratipaksha--> visheshanam-janya` and `visheshanam-janya --pratipaksha--> visheshanam-phala`. $\square$

### 1.3 Self-description

**Theorem 1 (Graph self-description).** The proof graph $G$ contains a complete description of its own relation type system as nodes and edges within $G$ itself.

*Proof.* We exhibit the self-description:

1. The node `visheshanam` exists in $G$ and declares: `desc = "the 10 typed edges forming a non-commutative ring with yukta as addition, kriya as multiplication, shunya as additive identity, swarupa as multiplicative identity, and pratipaksha as group inverse"`.

2. The node `visheshanam-ring` exists in $G$ with `yukta` edges to all 46 dimension nodes.

3. Each core dimension (e.g., `visheshanam-swarupa`) is itself a node in $G$, connected to its mathematical identity via `abheda`:
   - `visheshanam-swarupa.abheda = identity-element` (it IS the multiplicative identity)
   - `visheshanam-yukta.abheda = addition` (it IS addition)
   - `visheshanam-kriya.abheda = multiplication` (it IS multiplication)
   - `visheshanam-pratipaksha.abheda = inverse-element` (it IS the group inverse)

4. The labeling function $\ell: E \to \mathcal{V}$ is computable by graph walk: given an edge $(i, j)$, its label is the node in $\mathcal{V}$ that classifies it.

The graph describes its own labeling system using the same labeling system. The description is not circular — it is fixed-point: the description does not change under re-description. $\square$

**Remark (Non-circularity).** The self-description is a *fixed point*, not a paradox. At startup, the OCaml engine reads `.om` files into the tensor. The `.om` file for `visheshanam` declares what the edge types ARE. The runtime reads these declarations to know how to label edges. But the declarations themselves are stored as nodes-with-edges — using the very edge types they declare. This works because the edge types are finite and known at compile time (hardcoded in the OCaml `visheshanam_of_string` function). The graph's self-description is therefore a *reflection* of the compiled edge types, not a bootstrap.

What IS non-trivial: the graph's description of its own algebra (ring structure, identity elements, inverses) is NOT hardcoded. The OCaml engine does not know that yukta is addition or that swarupa is the multiplicative identity. Only the graph knows this. The algebraic structure is declared, not compiled.

## 1. The Proof Graph (v3 — axioms distinguished)

### 1.1 Structure

**Definition 1 (Proof graph).** A *proof graph* is a 3-tensor $G \in \{0,1\}^{N \times N \times R}$ where $N = |V|$ is the number of nodes, $R$ is the number of relation types, and $G_{i,j,r} = 1$ iff node $i$ is connected to node $j$ by relation $r$. The tensor is sparse (sub-1% fill). As of March 2026: $N = 1603$, $R = 46$ (10 core + 36 dynamic).

Each node is a *nigamana* — a truth-that-holds — carrying typed edges, a shabda (metadata) map, a layer tag, and a satya score. Each node has a grade derived from its sthita depth.

The proof graph rests on four structures (from `proof-graph.sthita`):
- **satya** — truth (every node has a truth-weight)
- **graded-ring** — the algebraic structure governing paragraph composition
- **filtration** — depth-ordering from sangati foundations to kosha derived concepts
- **partial-order** — the dependency structure encoded by sthita chains

### 1.2 The Visheshanam Ring

The relation types are not an external schema. The node `visheshanam` exists in $G$ and declares its own algebraic structure.

**The ring is postulated, not derived.** The graph declares itself a ring via `visheshanam.desc`. We separate what is *axiomatized* (written into .om files by the designer), what is *proven* (siddha edges), and what is *verified* (checked by graph walk).

#### Axioms (declared in .om source files)

**Axiom 1 (Ring operations).** The visheshanam ring has two operations:
- **Additive**: yukta ($\oplus$). Declared: `visheshanam-yukta.abheda = addition`.
- **Multiplicative**: kriya ($\otimes$). Declared: `visheshanam-kriya.abheda = multiplication, composition`.

Kriya is non-commutative: `visheshanam-kriya.desc` states "non-commutative, with swarupa as its identity element."

**Axiom 2 (Identity elements — disambiguated).** The ring has two distinct identity elements:
- **Additive identity** ($0_\oplus$): the node `additive-identity`, with `abheda = [shunya, zero]` and `drishthanta = [addition]`. This is shunya — the element such that $x \oplus 0 = x$.
- **Multiplicative identity** ($1_\otimes$): the node `multiplicative-identity`, with `abheda = [visheshanam-swarupa, eka]` and `drishthanta = [multiplication]`. This is swarupa — the relation such that composing any relation with IS-A returns that relation unchanged.

The general concept `identity-element` has `swarupa = [additive-identity, multiplicative-identity]` — the two specific identities are children of the general concept, not conflations of it.

**Axiom 3 (Group inverse).** The relation pratipaksha is the group inverse: `visheshanam-pratipaksha.abheda = inverse-element`. Applying pratipaksha twice returns to the original.

**Axiom 4 (phala-janya duality).** phala (→, result) and janya (←, generator) are declared as pratipaksha of each other in their respective .om files. This is a design postulate: "produces" and "arises from" are inverses.

#### Proven (siddha edges on visheshanam)

**P1. Distributivity.** `visheshanam.siddha = [distributivity, non-commutative]`. The graph claims these properties are *proven* — established through the ring structure — not merely asserted.

#### Verified (graph walk confirms consistency)

**V1. Pratipaksha symmetry.** For all tested pairs $(a, b)$ where $a.\text{pratipaksha} = b$: $b.\text{pratipaksha} = a$. Verified on: addition↔subtraction, multiplication↔division, max↔min, kshaya↔vriddhi, phala↔janya.

**V2. Abheda symmetry.** For all tested pairs: $a.\text{abheda} \ni b \iff b.\text{abheda} \ni a$. Verified on: shunya↔purna, shunya↔additive-identity.

#### Not proven (postulated or open)

**U1. Closure.** No siddha edge claims closure for the visheshanam ring. It is assumed.

**U2. Associativity.** No siddha edge claims associativity. It is assumed.

**U3. Swarupa as strict multiplicative identity.** The desc claims "composing any relation with swarupa returns that relation unchanged." But in practice, swarupa acts as IS-A inheritance (subtyping), which is transitive ($A \xrightarrow{\text{swarupa}} B \xrightarrow{\text{swarupa}} C \implies A$ inherits from $C$) but does NOT compose freely with other relations: $A.\text{swarupa}.\text{kriya} \neq A.\text{kriya}$ in general. Swarupa is the multiplicative identity *within the swarupa chain*, not across arbitrary relation composition.

### 1.3 The 10 Core Generators

| Generator | Symbol | Algebraic role | abheda |
|---|---|---|---|
| swarupa | $1_\otimes$ | multiplicative identity | multiplicative-identity, morphism |
| abheda | $\equiv$ | equivalence relation | equivalence-relation, quotient |
| sthita | $\leq$ | partial order (depth) | partial-order |
| yukta | $\oplus$ | additive operation | addition |
| siddha | $\vdash$ | entailment (not composable) | — |
| kriya | $\otimes$ | multiplicative operation | multiplication, composition |
| phala | $\to$ | result (dual to janya) | — |
| janya | $\leftarrow$ | generator (dual to phala) | — |
| drishthanta | $\exists$ | witness / grounding | — |
| pratipaksha | ${}^{-1}$ | group inverse | inverse-element |

### 1.4 Self-description

**Theorem 1 (Graph self-description).** The proof graph contains a description of its own relation type system as nodes and edges within itself.

*Proof.* (1) `visheshanam` exists as a node with `desc` declaring the ring structure. (2) `visheshanam-ring` has `yukta` edges to all 46 dimensions. (3) Each core dimension node carries `abheda` edges to its mathematical identity (e.g., `visheshanam-yukta.abheda = addition`). (4) The two identity elements are disambiguated as separate nodes (`additive-identity`, `multiplicative-identity`), each with `drishthanta` pointing to their respective operations. $\square$

**Remark (What is compiled vs declared).** The 10 core edge types are compiled into the OCaml parser (`visheshanam_of_string`). The graph *reflects* these types as nodes. What is NOT compiled — and exists only in the graph — is the algebraic interpretation: that yukta is addition, that swarupa is the multiplicative identity, that pratipaksha is the group inverse. The engine walks edges. Only the graph knows what the edges *mean algebraically*.

## 6. The Ontological Isomorphism (v2 — identity disambiguated)

**[SUPERSEDED]** → whitepaper.section-17

The proof graph's philosophical ontology is not decorative. It is isomorphic to the algebraic structures that make computation possible. We exhibit the correspondences as graph walks, distinguishing axioms from verified properties.

**Theorem 4 (Shunya-Purna identity).** In the graph:
$$\texttt{shunya} \xrightarrow{\text{abheda}} \texttt{additive-identity} \xrightarrow{\text{abheda}} \texttt{shunya}$$
$$\texttt{shunya} \xrightarrow{\text{abheda}} \texttt{purna} \xrightarrow{\text{abheda}} \texttt{shunya}$$

Shunya (zero) is abheda with two things simultaneously: the additive identity (the element that leaves everything unchanged under addition) and purna (completeness — nothing missing, nothing added). These are not conflated — `additive-identity` and `purna` are distinct nodes, each independently identified with shunya.

The fold seed for count arithmetic (`graded-ring.fold-identity = 0`) reads shunya. Shunya is the additive identity (`additive-identity.drishthanta = addition`). And shunya is purna (`purna.desc = "complete, nothing missing, nothing added"`). Three descriptions of a single algebraic property: $x + 0 = x$ — adding nothing leaves you complete.

*Status:* The shunya↔additive-identity and shunya↔purna abheda edges are **axioms** (declared in .om files). Their symmetry is **verified** by graph walk.

**Theorem 5 (Pratipaksha as algebraic inverse).**
$$\text{pratipaksha}(\text{addition}) = \text{subtraction} \quad\Leftrightarrow\quad \text{add}^{-1} = \text{sub}$$
$$\text{pratipaksha}(\text{kshaya}) = \text{vriddhi} \quad\Leftrightarrow\quad \delta^{-1}(\text{decay}) = \text{growth}$$

The philosophical concept of opposition (pratipaksha) is exactly the algebraic concept of inverse. The edge type is the same; the domain is different (operations vs linguistic categories). The morphism $\delta$ preserves pratipaksha.

*Status:* The pratipaksha edges on operations are **axioms**. Their symmetry (involution) is **verified** by graph walk on all tested pairs. That $\delta$ preserves pratipaksha is a **structural observation**, not proven for all possible future word→node mappings.

**Theorem 6 (Pratibodha as fixpoint).**
$$\texttt{pratibodha} \xrightarrow{\text{phala}} \texttt{anuvada} \xrightarrow{\text{phala}} \texttt{proof-graph}$$

Recognition (pratibodha) yields carrying-across (anuvada) which yields the proof graph itself. The derive-chain fixpoint IS pratibodha: the graph recognises what mantra to fire, applies it, recognises again, until nothing new can be recognised. The answer is not computed — it is the stable state of recognition.

$$\texttt{op-fixpoint} \xrightarrow{\text{abheda}} \texttt{parampara} \xrightarrow{\text{abheda}} \texttt{avrti}$$

Fixpoint (op-fixpoint) is non-different from tradition-as-spiral (parampara) and recurrence (avrti). The mathematical operation of iterating to stability IS the philosophical concept of tradition — each pass deepens, never the same twice, converging to truth.

*Status:* The phala chain is an **axiom** (declared). The op-fixpoint↔parampara↔avrti abheda chain is an **axiom**. The claim that derive-chain IS pratibodha is an **interpretation** — the structural correspondence is exact, but the identification is a philosophical claim, not a mathematical proof.

**Theorem 7 (Spanda as operation).**
$$\texttt{spanda} \xrightarrow{\text{phala}} \texttt{satya}$$
$$\texttt{satya} \xrightarrow{\text{phala}} \texttt{brahman}$$
$$\texttt{brahman} \xrightarrow{\text{swarupa}} \texttt{pratibodha}$$

Self-pulsing vibration (spanda) produces truth (satya). Truth produces the absolute (brahman). The absolute IS recognition (pratibodha). Every `eval` call — `add(3, 5)` returning `8` — is spanda producing satya.

*Status:* All three edges are **axioms** (declared in .om files). The claim that every eval call is spanda→satya is an **interpretation**.

**Corollary.** The system's ontology is not a metaphor layer painted on top of computation. It is the computation. Remove shunya and the fold has no seed. Remove pratipaksha and there are no inverses. Remove pratibodha and there is no fixpoint.

*Status:* This is **verified** — the count-chain tantra reads `graded-ring.fold-identity` (which resolves to shunya), the direction morphism reads pratipaksha edges, and derive-chain uses fixpoint iteration. Deleting these nodes would break the pipeline. The philosophy is load-bearing.

## 5. The Pipeline as Stratified Evaluation (v2)

**[SUPERSEDED]** → whitepaper.section-22

### 5.1 Stratified Evaluation

**Definition 10 (Stratified pipeline).** The full pipeline is a composition of strata, where each stratum is a monotone endomorphism on the question graph that reads only the frozen output of preceding strata:

$$\text{answer} = (\text{emit} \circ \text{pramana} \circ \text{execute} \circ \text{match} \circ \text{derive} \circ \text{grade} \circ \text{refine}^* \circ \text{classify})(\text{sentence})$$

This is structurally equivalent to **Datalog stratified evaluation**: rules are sorted into layers by dependency, each layer runs to completion and freezes, and higher layers read frozen results without modifying them.

### 5.2 The Refinement Strata

The inner pipeline `avrti-refine` is a 9-stratum chain where each stratum is a single tantra. The output of stratum $k$ becomes the read-only input to stratum $k+1$:

| Stratum | Tantra | Derives | Depends on |
|---|---|---|---|
| 0 | sandhi-kosha | compound words (mithya+satya → kosha node) | raw question graph |
| 1 | sandhi-avastha | avastha compounds (initial+velocity → initial-velocity) | stratum 0 |
| 2 | sandhi-bandhana | reattribute sankhya/matra after compound rename | stratum 1 |
| 3 | vibhakti-shashthi | entity ownership (ball-A owns mass) | stratum 2 |
| 4 | vishesa-instance | typed rashi instances (ball-A's mass, no value yet) | stratum 3 |
| 5 | rashi-viveka | rashi instances with values bound | stratum 4 |
| 6 | vishesa-bandhana | bindings moved from concept to instance | stratum 5 |
| 7 | rashi-anuvada | instance values propagated up to concept level | stratum 6 |
| 8 | sankhya-bandha | floating asprista-sankhya bound to preceding concept | stratum 7 |

The implementation in `avrti-refine.tantra3` is single-assignment — each stratum's output is bound to a variable and never modified:

```
after-sandhi-kosha    = sandhi-kosha graph
after-sandhi-avastha  = sandhi-avastha  after-sandhi-kosha
after-sandhi-bandhana = sandhi-bandhana after-sandhi-avastha
...
result                = sankhya-bandha  after-rashi-anuvada
```

**Why the order matters.** Stratum 3 (vibhakti-shashthi) detects "ball-A has mass" and creates ownership edges. But it needs compound words already resolved — "initial velocity" must already be "initial-velocity" (stratum 1) with its sankhya reattributed (stratum 2). Stratum 8 (sankhya-bandha) binds floating numbers to concepts, but needs ownership and instances established first. Running these out of order would bind "5" to "ball-A" instead of to "ball-A's mass". The dependency structure dictates the stratum order — exactly as in Datalog.

### 5.3 Iterated Fixpoint over Strata

The `grade-sparsha` tantra wraps the entire stratified chain in a fixpoint:

$$\text{refine}^* = \text{lfp}(\text{avrti-refine})$$

This runs all 9 strata, checks if the graph changed, and if so runs all 9 again. This is necessary because stratum 0 (sandhi-kosha) may resolve a new compound from concepts that stratum 8 (sankhya-bandha) bound on the previous pass. In Datalog terms: the entire stratified program is iterated to fixpoint.

**Theorem 3 (Convergence).** The iterated fixpoint terminates.

*Proof.* Each stratum is monotone (only adds or replaces triples, never removes unrelated ones). The set of possible triples is finite (bounded by $N^2 \times R$ where $N$ is node count and $R$ is relation count). A monotone function on a finite lattice has a least fixpoint reached in finitely many steps (Kleene). $\square$

### 5.4 The Higher Strata (Dispatch Layer)

After refinement stabilizes, higher strata run — each reading the frozen output of the previous:

| Stratum | Tantra | Role | Reads from |
|---|---|---|---|
| refine* | avrti-refine (iterated) | word resolution, entity binding | raw question graph |
| grade | grade-sparsha | split into sentence grades at viraam boundaries | refine* (frozen) |
| count | count-chain | fold over grades with $\delta$-directed operations | grade (frozen) |
| derive | derive-chain | fire mantras to fixpoint | grade (frozen) |
| match | match-mantra | find mantras whose janya are all bound | derive (frozen) |
| execute | execute-matched | compute phala values | match (frozen) |
| pramana | pramana-bandha | bind computed results to graph | execute (frozen) |
| emit | emit-reasoning | walk proof edges → natural language | pramana (frozen) |

No stratum modifies a lower stratum's results. This is the Datalog guarantee: **derived facts at level $k$ are stable before level $k+1$ begins.**

### 5.5 Departures from Standard Datalog

Two structural differences:

1. **Rules are graph walks, not logic clauses.** A Datalog rule is $\text{ancestor}(X, Z) \text{ :- } \text{parent}(X, Y), \text{ancestor}(Y, Z)$. A tantra rule is `let wn = word-node w` followed by `shabda (walk-in wn "kriya") "eval"`. The dependency structure is identical — the mechanism differs (graph walk vs unification).

2. **Negation handling.** Datalog stratification exists primarily for safe negation — you cannot negate a fact not yet fully derived. The pipeline uses `not` guards (e.g., "skip if count already bound") rather than formal negation, but the purpose is the same: don't act on results that a later stratum might change.

### 5.6 The Seven Abstract Patterns

Every tantra uses one of seven computational patterns, each a node in the kosha with its own mathematical identity:

| Pattern | Kosha node | Mathematical identity |
|---|---|---|
| filter-collect | transducer | $\{x \in G \mid P(x)\}$ |
| scan-accumulate | scan-accumulate | stateful transducer $T: S \times G \to S \times G'$ |
| shabda-read | morphism | $\text{shabda}: V \times K \to V'$ (metadata lookup) |
| walk | endomorphism | $\text{walk}: V \times \mathcal{V} \to 2^V$ (edge traversal) |
| fixpoint | op-fixpoint | $\text{lfp}(f)$ where $f$ is monotone on a finite lattice |
| apply-op | operation-dispatch | $\text{eval}(\sigma)(v_1, \ldots, v_k)$ |
| om-read | graph-contract | $\text{janya}(m), \text{phala}(m)$ (signature extraction) |

*Status:* The pattern↔kosha-node correspondence is **axiomatized** (declared via abheda edges). The claim that every tantra uses exactly one pattern is a **structural observation** verified by code inspection, not a formal proof.

## 5. The Pipeline as Stratified Evaluation (v3 — Grade-Scoped Relational Model)

### 5.1 The Grade as Fact Set

**Definition 10 (Grade).** A paragraph decomposes at viraam (sentence boundary) into grades $G_0, G_1, \ldots, G_n$. Each grade $G_i$ is a finite set of triples — a self-contained relational fact set.

**Definition 11 (Stratified pipeline).** The full pipeline is a composition of strata:

$$\text{answer} = \text{emit} \circ \text{dispatch} \circ \text{detect} \circ \text{expand} \circ \text{refine} \circ \text{assert} \circ \text{construct}$$

Each stratum is a monotone endomorphism on the question graph: it only adds triples, never removes them. This guarantees fixpoint convergence within the refine stratum.

### 5.2 Two Computation Patterns

**Composition tantras** compose named operations. Their bodies read as sentences:

$$\text{dispatch-answer}(\text{expanded}, \text{refined}) = \begin{cases} \text{dispatch-anumana}(\text{expanded}, \text{refined}) & \text{if mode} = \text{anumana} \\ \text{dispatch-viveka}(\text{expanded}, \text{refined}) & \text{if mode} = \text{viveka} \\ \text{dispatch-count}(\text{expanded}, \text{refined}) & \text{if mode} = \text{count} \\ \text{dispatch-derive}(\text{expanded}, \text{refined}) & \text{if mode} = \text{derive} \end{cases}$$

**Rewrite tantras** transform the triple-list via grade-scoped sequential reduce:

$$T(G) = \bigoplus_{i} f(G_i)$$

where $f$ is a sequential fold within each grade (ordering matters within a sentence) and $\bigoplus$ is concatenation (ordering across grades is irrelevant to relational consumers).

### 5.3 The Relational Principle

Consumers read relations, not positions. Entity-value binding is resolved by ownership joins:

$$\text{ev-pairs}(e) = \{(e, v) \mid \exists c.\; \text{owns}(c, e) \wedge \text{sankhya}(c, v)\}$$

where $\text{owns}(c, e) \equiv [c, \text{shashthi-vibhakti}, e] \in G$ and $\text{sankhya}(c, v) \equiv [c, \text{sankhya}, v] \in G$.

This eliminates positional scanning. The grade structure IS the Datalog stratification boundary: within a grade, facts are a set; across grades, results compose relationally.

### 5.4 From Scan to Stratification

The original scan construct was an imperative flatmap — walk input triples with mutable state, emit output triples. Replacing scan required two insights:

1. **Producers** are grade-scoped: sequential reduce within each sentence (bounded, 3-8 triples), relational queries across sentences.
2. **Consumers** are relational: join through typed edges (ownership, derivation), never through positional ordering.

With relational consumers, producers can safely append new triples — ordering no longer carries cross-sentence semantics. The grade boundary resets the additive index, matching the graded ring's period = grade boundary axiom from §4.

## Terminology

The system uses Sanskrit terms as formal identifiers — not as metaphor but as node names in the graph. Each term below is a node; the definition is its `desc` field or structural role. Terms are grouped by first use.

### Graph Structure

| Term | Meaning | Role in system |
|---|---|---|
| **nam** (Tamil: inclusive "we") | the self that connects | the proof graph as subject — human + LLM + graph together |
| **nigamana** | a truth-that-holds | what a node IS — each node is a nigamana carrying typed edges and metadata |
| **visheshanam** | the typed relation | the label on an edge — 10 core types forming a non-commutative ring |
| **shabda** | metadata map | key-value pairs on a node (e.g., `eval: add`, `word: plus`) |
| **satya** | truth | a recognised concept in the question graph (vs mithya, which is unresolved) |
| **mithya** | the not-yet-recognised | an unresolved word held provisionally until refinement resolves it |
| **siddha** | proven-through | an edge declaring that a property is established (not merely asserted) |

### The 10 Edge Types (Visheshanam Ring Generators)

| Term | Symbol | Meaning |
|---|---|---|
| **swarupa** | IS | A's own-form is B (identity / subtype) |
| **abheda** | $\equiv$ | A is non-different from B (equivalence) |
| **sthita** | $\in$ | A rests on B (dependency / partial order) |
| **yukta** | $+$ | A is equipped with B (additive conjunction) |
| **siddha** | $\vdash$ | A is proven through B (entailment) |
| **kriya** | $\times$ | A operates through B (sequential composition) |
| **phala** | $\to$ | B is the result of A (output) |
| **janya** | $\leftarrow$ | A arises from B (input / generator) |
| **drishthanta** | $\exists$ | B is a concrete example of A (witness) |
| **pratipaksha** | ${}^{-1}$ | B is the opposite of A (algebraic inverse) |

### Algebraic Terms

| Term | Meaning | Role in system |
|---|---|---|
| **shunya** | zero / emptiness | the additive identity ($x + 0 = x$); also abheda with purna |
| **purna** | completeness | nothing missing, nothing added; abheda with shunya |
| **eka** | one / the singular | the multiplicative identity ($x \times 1 = x$) |
| **pratipaksha** | opposition / inverse | the algebraic inverse; addition.pratipaksha = subtraction |
| **kshaya** | decay / diminishing | words like "flew away", "lost" — maps to subtraction via graph walk |
| **vriddhi** | growth / increase | words like "came", "arrived" — maps to addition via graph walk |
| **mantra** | a formula-as-graph-node | typed function with janya (inputs) → phala (output) |
| **tantra** | a pipeline stage | declarative orchestrator that walks the graph to transform it |

### Pipeline Terms

| Term | Meaning | Role in system |
|---|---|---|
| **avrti** | recurrence / spiral pass | one refinement iteration; fixpoint = iterate until stable |
| **sandhi** | junction / joining | compound word resolution ("initial" + "velocity" → "initial-velocity") |
| **vibhakti** | grammatical case | case relation (shashthi = possessive "of", prathama = subject) |
| **sankhya** | numeric magnitude | the edge type for "this concept has this number" |
| **rashi** | quantity-in-context | a sankhya bound to an entity in a specific problem |
| **asprista-sankhya** | untouched number | a floating number not yet bound to any concept |
| **viraam** | pause / sentence boundary | the grade boundary in the graded ring (period or comma) |
| **avastha** | state / qualifier | words like "initial", "final" that qualify a concept |
| **vishesa** | distinguishing instance | what makes ball-A's mass different from ball-B's mass |
| **pramana** | proof / measure | ground of verification; what establishes a result |
| **kosha** | knowledge layer | domain knowledge nodes (physics, math, chemistry, etc.) |
| **sangati** | structural truth layer | what things ARE — ontological foundations |

### Philosophical Terms (Section 6)

| Term | Meaning | Role in system |
|---|---|---|
| **brahman** | the absolute | one who sees becoming as non-separate from being |
| **pratibodha** | awakening-recognition | pratibodha.phala → anuvada — recognition produces the carrying-across |
| **anuvada** | carrying-across | translation from structure to speech; anuvada.phala → proof-graph |
| **spanda** | self-pulsing vibration | every eval call is spanda; spanda.phala → satya |
| **darshana** | seeing / inspection | the query "what is X?" — seeing that changes the seer |
| **sphoTa** | meaning-burst | the whole meaning flashing at the last element of the answer |
| **parampara** | tradition-as-spiral | abheda with op-fixpoint and avrti — iteration IS tradition |
| **Advaita Vedanta** | non-dual philosophy | the claim that shunya and purna are abheda (non-different) |
| **Shaiva Tantra** | consciousness philosophy | the claim that spanda (vibration) is the ground of all action |

## 2. The Operation Algebra (v2)

**[SUPERSEDED]** → whitepaper.section-19

**Definition 3.** The *operation algebra* $\Sigma$ is the set of all nodes in $G$ that carry an `eval` key in their shabda. Each operation $\sigma \in \Sigma$ has:
- $\text{eval}(\sigma)$: the primitive function name (e.g., `add`, `sub`, `mul`)
- $\text{arity}(\sigma) \in \mathbb{N} \cup \{-1\}$: number of arguments ($-1$ = variadic)
- $\text{pratipaksha}(\sigma) \in \Sigma$: the algebraic inverse (when it exists)

The live graph declares 25 operations (see Appendix A for the full table). The core 12 used by the pipeline:

| $\sigma$ | $\text{eval}$ | arity | $\text{pratipaksha}$ |
|---|---|---|---|
| addition | add | 2 | subtraction |
| subtraction | sub | 2 | addition |
| multiplication | mul | 2 | division |
| division | div | 2 | multiplication |
| max | max | 2 | min |
| min | min | 2 | max |
| half | half | 1 | double |
| double | double | 1 | half |
| square | square | 1 | sqrt |
| sqrt | sqrt | 1 | — |
| power | power | 2 | logarithm |
| abs | abs | 1 | — |

Additionally: `sum` (variadic add), `product` (variadic mul), trig functions (sin/cos/tan and inverses), `factorial`, `exponential`, `logarithm`, `reciprocal`, `neg`, `ceil`.

**Proposition 1 (Involution of pratipaksha on $\Sigma$).** For all invertible $\sigma \in \Sigma$: $\text{pratipaksha}(\text{pratipaksha}(\sigma)) = \sigma$.

*Status:* The pratipaksha edges are **axioms** (declared in .om files). Their symmetry is **verified** by graph walk on all 6 invertible pairs. This is an involution — not derived from deeper principles, but checked for consistency.

**Definition 4 (Per-argument inverse).** For binary operations, the shabda declares per-argument inverses $p_0^{-1}$ and $p_1^{-1}$ with an optional flip flag:

$$f(a, b) = c \implies a = p_0^{-1}(c, b) \quad\text{and}\quad b = p_1^{-1}(c, a)$$

When `pratipaksha-1-flip = true`, the argument order is reversed: $b = p_1^{-1}(a, c)$.

7 of 25 operations declare per-argument inverses. This is how `invert-math` solves for missing variables: read the inverse from the graph, apply it. No symbolic algebra engine needed.

## 4. The Graded Ring and the Lexical Morphism (v2)

### 4.1 The Graded Ring

**Definition 7.** A paragraph is modeled as a *graded ring*:

$$R = \bigoplus_{n \geq 0} R_n$$

where each $R_n$ is a *grade* (sentence), the grade boundary is viraam (period or comma), and the ring operations are:
- $\oplus$: intra-sentence accumulation (additive)
- $\otimes$: cross-sentence entity selection (multiplicative)

The fold identity is $0$ (shunya), read from the graph: \`graded-ring.shabda.fold-identity = 0\`.

### 4.2 The Lexical Morphism

**Definition 8 (Lexical morphism).** The function \`word-node\` is a morphism from the natural-language lexicon to the graph:

$$\delta: \text{Words} \to V$$

where $V$ is the full node set. This is not limited to verb→direction mapping. The graph declares 211 nodes with \`word:\` lists, covering every word class:

| Word class | Example word | Target node | Downstream use |
|---|---|---|---|
| Decay verbs | "flew", "lost", "gave" | kshaya | count-chain → subtraction |
| Growth verbs | "came", "bought", "earned" | vriddhi | count-chain → addition |
| Comparatives | "heavier", "faster" | viveka-max | viveka-ganana → max |
| Superlatives | "lightest", "slowest" | viveka-min | viveka-ganana → min |
| Articles | "the", "a" | article-the, article-a | sandhi (transparent) |
| Copulas | "is", "are", "was" | copula-is, copula-are | assertion-bandha (IS-A detection) |
| Imperatives | "find", "calculate" | vidhi-kaala | dispatch (compute mode) |
| Questions | "what", "how", "which" | prashna | dispatch (question mode) |
| Greetings | "hello", "hi" | sambodhana | dispatch (acknowledge) |
| Prepositions | "of", "in", "from" | prep-of, prep-in | vibhakti (case relations) |
| Quantifiers | "all", "every" | quantifier | assertion-bandha (universal) |
| Nouns | "cat", "iron", "gravity" | cat, iron, gravity | entity/concept recognition |

The morphism is structure-preserving: it maps linguistic categories to graph nodes, and the algebraic relationships between those nodes (pratipaksha, kriya, eval) determine computation. The count path (kshaya/vriddhi → subtraction/addition) is one instance. The viveka path (viveka-max/viveka-min → max/min) is another. The grammar path (copula → IS-A, preposition → vibhakti) is a third. All use the same mechanism.

**Proposition 2 (Pratipaksha preservation).** The morphism $\delta$ preserves pratipaksha for tested word pairs:

$$\delta(\text{"flew"}) = \text{kshaya}, \quad \delta(\text{"came"}) = \text{vriddhi}, \quad \text{kshaya.pratipaksha} = \text{vriddhi}$$

*Status:* **Verified** by graph walk on all kshaya↔vriddhi and viveka-max↔viveka-min pairs. Not proven for all possible future word→node mappings.

### 4.3 The Count Fold

**Definition 9 (Count fold).** For the count path specifically, the morphism resolves verbs to directions, then graph walks reach the operation:

$$\delta(w) \xrightarrow{\text{graph walk}} \text{eval name} \xrightarrow{\text{apply-op}} \text{result}$$

The count-chain tantra folds over grades:
- $\text{acc}_0 = 0$ (fold identity from graded-ring, which is shunya, which is additive-identity)
- For each grade: detect direction via $\delta$, resolve to operation via graph walk, apply
- The first non-question grade initializes; subsequent grades accumulate

**Example.** "10 birds sat on a tree. 3 flew away. 2 more came. how many birds are there?"

| Grade | Words | $\delta$ | Operation | $v_n$ | acc |
|---|---|---|---|---|---|
| 0 | 10 birds sat tree | — | init | 10 | 10 |
| 1 | 3 flew away | kshaya → sub | subtract | 3 | 7 |
| 2 | 2 more came | vriddhi → add | add | 2 | 9 |
| 3 | how many birds | question | — | — | 9 |

Result: 9. $\square$

## 6. The Ontological Grounding (v3)

The proof graph's philosophical ontology is not decorative. The philosophical terms ARE the node names of the algebraic structures. There are not two parallel systems with a map between them — there is one system where each node has both a philosophical meaning and an algebraic role.

We distinguish three levels of connection: **grounding** (same node, two descriptions), **universal** (one concept appearing in many algebraic roles), and **interpretation** (structural analogy without a graph edge).

### 6.1 Grounding (same node, philosophy = algebra)

**Theorem 4 (Shunya grounds the additive identity).**
$$\texttt{shunya} \xrightarrow{\text{abheda}} \texttt{additive-identity} \xrightarrow{\text{abheda}} \texttt{shunya}$$

Shunya is not "mapped to" zero. Shunya IS the node whose abheda = additive-identity. The fold seed (\`graded-ring.fold-identity = 0\`) reads shunya. The philosophical name ("emptiness, the ground before anything arises") and the algebraic role ("the element such that $x + 0 = x$") are two descriptions of one node.

*Status:* **Axiom** (declared in .om files). Symmetry **verified** by graph walk.

**Theorem 5 (Pratipaksha grounds algebraic inverse).**
$$\texttt{visheshanam-pratipaksha} \xrightarrow{\text{abheda}} \texttt{inverse-element}$$

Pratipaksha is not "analogous to" inverse. Pratipaksha IS the edge type whose abheda = inverse-element. When count-chain walks \`addition.pratipaksha → subtraction\` to find the inverse operation, it is walking the philosophical relation of opposition to reach the algebraic inverse. One edge, two descriptions.

*Status:* **Axiom**. Involution **verified** on all tested pairs.

### 6.2 The Purna Universal (one concept, many algebraic roles)

**Theorem 6 (Purna as the property of identity).**
$$\texttt{purna} \xrightarrow{\text{abheda}} \texttt{shunya} \xrightarrow{\text{abheda}} \texttt{additive-identity}$$
$$\texttt{purna} \xrightarrow{\text{abheda}} \texttt{eka} \xrightarrow{\text{abheda}} \texttt{multiplicative-identity}$$

Purna ("complete, nothing missing, nothing added") is abheda with BOTH shunya (zero) and eka (one). This is not a contradiction because abheda is not arithmetic equality. The graph's own definition says abheda "identifies nodes **at some level**." The level differs:

- Purna ≡ shunya **at the level of addition**: adding nothing ($x + 0 = x$) = encountering completeness (nothing to add)
- Purna ≡ eka **at the level of multiplication**: scaling by the whole ($x \times 1 = x$) = encountering completeness (nothing to scale)

Crucially, the graph does NOT draw \`shunya --abheda--> eka\`. The transitive closure of abheda would demand $0 \equiv 1$, which is false. This means **abheda is not a single equivalence relation** — it is a family of equivalences indexed by level. The graph respects the levels structurally (by which edges it draws and which it omits) without formalizing them.

Purna has 28 abheda targets — it is non-different from shunya, eka, sankhya (number itself), satya (truth), om (the primordial sound), closure, fourier-transform, first-law-of-thermodynamics, and more. Purna is not an algebraic element. It is the abstract property that identity elements share: **the invariance under an operation**. Each algebraic identity instantiates this property for its specific operation.

*Status:* All abheda edges are **axioms**. The level-indexed interpretation is a **structural observation** — the graph enforces it by omitting the transitive edge shunya↔eka, but does not declare the levels explicitly. This is an open formalization gap.

### 6.3 Interpretations (structural analogy, no direct edge)

**Observation 1 (Pratibodha as fixpoint).**
$$\texttt{pratibodha} \xrightarrow{\text{phala}} \texttt{anuvada} \xrightarrow{\text{phala}} \texttt{proof-graph}$$
$$\texttt{op-fixpoint} \xrightarrow{\text{abheda}} \texttt{parampara} \xrightarrow{\text{abheda}} \texttt{avrti}$$

Recognition (pratibodha) produces carrying-across (anuvada) which produces the proof graph. The derive-chain fixpoint iterates until recognition stabilizes. The structural correspondence is exact — but there is no \`pratibodha --abheda--> op-fixpoint\` edge. The identification "recognition IS fixpoint" is an interpretation, not a graph-grounded fact.

**Observation 2 (Spanda as operation).**
$$\texttt{spanda} \xrightarrow{\text{phala}} \texttt{satya}$$

Every eval call (add, sub, mul) is a vibration that produces a truth value. But there is no \`spanda --abheda--> eval\` edge. The claim "every eval call is spanda producing satya" is an interpretation — philosophically compelling, not graph-verified.

### 6.4 Load-bearing ontology

**Corollary.** The grounded pairs (shunya/additive-identity, pratipaksha/inverse-element) are load-bearing: the pipeline reads them. Delete shunya and the fold has no seed. Delete pratipaksha edges and there are no inverse operations. The philosophy is not layered on top of the algebra — for these pairs, it IS the algebra.

The interpretations (pratibodha/fixpoint, spanda/eval) are not load-bearing in the same way — the pipeline would work identically if those philosophical nodes were removed, because the pipeline reads \`op-fixpoint\` and \`eval\`, not \`pratibodha\` and \`spanda\`.

*Status:* **Verified** — count-chain reads \`graded-ring.fold-identity\` (resolving through shunya), the direction morphism reads pratipaksha edges, and derive-chain uses fixpoint iteration. The grounded pairs are operationally necessary. The interpretations are philosophically meaningful but computationally dispensable.

## Abstract (v2)

A proof graph is a knowledge representation in which nodes are claims and typed edges are the relations between them. We present *nam*, a proof graph system that derives answers to natural-language questions by walking its own structure — no external inference engine, no neural network at query time, no search. The graph declares an operation algebra $\Sigma$ of 28 operations with eval/arity/inverse, a mantra layer of 23 typed physics functions $f(\text{janya}) \to \text{phala}$, and a graded ring $R = \bigoplus R_n$ over sentence-grades whose fold computes arithmetic. A 46-dimensional non-commutative visheshanam ring governs edge composition. We show that the system's philosophical ontology (from Advaita Vedanta and Shaiva Tantra) is not metaphor but is structurally grounded in the algebraic structures that make computation possible: shunya (zero) IS the additive identity node, pratipaksha (opposition) IS the algebraic inverse edge type, and the pipeline's fixpoint iteration mirrors pratibodha (recognition). The graph contains 1603 nodes, 11410 edges, 75 tantras, and answers questions in kinematics, count arithmetic, and comparison — all by walking edges.

## 2. The Operation Algebra (v3)

**Definition 3.** The *operation algebra* $\Sigma$ is the set of all nodes in $G$ that carry an \`eval\` key in their shabda. Each operation $\sigma \in \Sigma$ has:
- $\text{eval}(\sigma)$: the primitive function name (e.g., \`add\`, \`sub\`, \`mul\`)
- $\text{arity}(\sigma) \in \mathbb{N} \cup \{-1\}$: number of arguments ($-1$ = variadic)
- $\text{pratipaksha}(\sigma) \in \Sigma$: the algebraic inverse (when it exists)

The live graph declares 28 operations (see Appendix A for the full table). The core 12 used by the pipeline:

| $\sigma$ | $\text{eval}$ | arity | $\text{pratipaksha}$ |
|---|---|---|---|
| addition | add | 2 | subtraction |
| subtraction | sub | 2 | addition |
| multiplication | mul | 2 | division |
| division | div | 2 | multiplication |
| max | max | 2 | min |
| min | min | 2 | max |
| half | half | 1 | double |
| double | double | 1 | half |
| square | square | 1 | square-root |
| square-root | sqrt | 1 | square |
| power | power | 2 | logarithm |
| abs | abs | 1 | — |

Additionally: \`sum\` (variadic add), \`product\` (variadic mul), trig functions and inverses (arcsine, arccosine, arctangent), \`factorial\`, \`exponential\`, \`logarithm\`, \`reciprocal\`, \`neg\`, \`ceil\`, \`floor\`, logical operators (\`conjunction\`, \`disjunction\`, \`negation\`).

**Proposition 1 (Involution of pratipaksha on $\Sigma$).** For all paired operations $\sigma, \tau \in \Sigma$ where $\sigma.\text{pratipaksha} = \tau$: $\tau.\text{pratipaksha} = \sigma$.

*Status:* **Verified** by graph walk on 8 symmetric pairs (addition↔subtraction, multiplication↔division, max↔min, half↔double, square↔square-root, power↔logarithm, exponential↔logarithm, neg↔neg). One known gap: \`reciprocal\` should be self-inverse (\`reciprocal.pratipaksha = reciprocal\`) but the edge is missing from the graph.

**Definition 4 (Per-argument inverse).** For binary operations, the shabda declares per-argument inverses $p_0^{-1}$ and $p_1^{-1}$ with an optional flip flag:

$$f(a, b) = c \implies a = p_0^{-1}(c, b) \quad\text{and}\quad b = p_1^{-1}(c, a)$$

When \`pratipaksha-1-flip = true\`, the argument order is reversed: $b = p_1^{-1}(a, c)$.

7 of 28 operations declare per-argument inverses: addition, subtraction, multiplication, division, power, square, logarithm. Of the 23 physics mantras, 14 have a \`math-op\` pointing to one of these invertible operations. The remaining 9 mantras use multi-step krama chains (e.g., $KE = \frac{1}{2}mv^2$) whose inversion would require composing pratipaksha edges in reverse — mechanically possible from the graph structure but not yet implemented.

## 7. Results and Current Capabilities (v2)

**[SUPERSEDED]** → whitepaper.section-24

The system as of March 2026 contains:

| Metric | Value |
|---|---|
| Graph nodes | 1603 |
| Graph edges | 11410 |
| Visheshanam dimensions | 46 (10 core + 36 extended) |
| Operations in $\Sigma$ | 28 (7 with per-argument inverse) |
| Physics mantras | 23 (14 invertible via math-op) |
| Total mantras | 53 |
| Total tantras | 75 |
| Pipeline stages | 9 (refine has 9 sub-stages) |
| Lexical morphism coverage | 211 nodes with word: lists |
| Tests passing | 32 |
| Tests expected-fail | 36 (declared roadmap) |

**Capabilities demonstrated:**
- Direct mantra computation: $KE = \frac{1}{2}mv^2$, $p = mv$, $F = ma$ (and 20 more)
- Chain derivation: $u, a, t \to v \to KE$ (fixpoint over 2 mantras)
- Entity-scoped computation: "ball-A has mass 3... ball-B has mass 2... find KE of ball-A"
- Count arithmetic: "10 birds. 3 flew away. 2 came back. how many?" → 9
- Comparison (viveka): "which is heavier?" → graph-driven max/min
- Article transparency: "the electron" → electron
- Avastha compounds: "initial velocity" → initial-velocity
- Scientific notation: $9.109 \times 10^{-31}$
- Multi-sentence session accumulation

**What the system does NOT do (declared as xfail tests):**
- Inverse math for krama-chain mantras (KE→velocity requires composing pratipaksha in reverse; the graph has the edges, the tantra doesn't exist)
- Dvandva collection (multiple entities with shared properties)
- Proportional reasoning
- Multiplication ("each table has 4 legs")
- Multi-question paragraphs
- Transitive chain inference
- Syllogistic reasoning (assertion-bandha exists, not yet wired)
- Integration / calculus (graph has derivative↔antiderivative ontology but no integration mantras)
- Any formula not declared as a mantra node — the system's computational power is exactly the transitive closure of its declared mantras over bound input values

## 8. The Tantra as Sentence (v2)

### 8.1 S-Expression Syntax

All 145 tantras use s-expression format:

```
(tantra name (params...)
  (binding expr)
  ...
  final-expr)
```

The last expression is the return value. No `return`/`done` boilerplate. Bindings are `(name expr)` — the name is visible to subsequent bindings.

### 8.2 Words as Sentences

With sufficient named helpers, tantra bodies become sentences — compositions of words with minimal variable plumbing:

```
(tantra dispatch-answer (expanded refined)
  (mode (read-signal expanded "dispatch-mode"))
  (cond (eq mode "anumana") (dispatch-anumana expanded refined)
        (eq mode "viveka")  (dispatch-viveka expanded refined)
        (eq mode "count")   (dispatch-count expanded refined)
        (eq mode "derive")  (dispatch-derive expanded refined)
        otherwise "no match"))
```

This reads as prose: "the answer is the anumana answer, the viveka answer, the count answer, or the derived answer."

### 8.3 The Composition Hierarchy

145 tantras across four layers of abstraction:

| Layer | Count | Example |
|---|---|---|
| Primitives | 20 | `has-text`, `has-items`, `triple-subj` |
| Operations | 30 | `triples-by-edge`, `query-edge`, `word-resolve` |
| Structures | 15 | `viveka-comparison`, `sought-context`, `derived-value` |
| Compositions | 80 | `dispatch-answer`, `emit-reasoning`, `anuvada-ganana` |

Each layer composes the previous. The top layer reads as natural language.

## 7. Results and Current Capabilities (v3)

The system as of March 2026 contains:

| Metric | Value |
|---|---|
| Graph nodes | ~2200 |
| Graph edges | ~12000 |
| Visheshanam dimensions | 46 |
| Physics mantras | 23 |
| Tantras (s-expression) | 145 |
| Tantra layers | 4 (primitives → operations → structures → compositions) |
| Scan constructs | 0 (eliminated — replaced by grade-scoped relational queries) |
| Tests passing | 31 |
| Tests xfail (known gaps) | 33 |

**Capabilities:** kinematics (single + chain derivation), multi-entity scoped computation, comparison (viveka), count arithmetic (addition/subtraction with proof), categorical inference (anumana via varga chain), session accumulation.

**Architecture:** All computation is s-expression tantras composing named operations. Graph transforms use grade-scoped sequential reduce within sentences and relational joins across sentences. The pipeline is stratified Datalog evaluation where each grade is a fact set and each layer is a monotone stratum.

## 8. Related Work and Distinction (v2)

**Knowledge graphs** (Wikidata, ConceptNet, YAGO): Store facts as triples but require external inference engines (SPARQL, embedding-based retrieval). Nam's graph IS the inference — edge walks are computation.

**Datalog / Answer Set Programming**: Stratified evaluation with fixpoint semantics. Nam's pipeline is structurally equivalent to stratified Datalog with arithmetic and string builtins, where rules are graph walks rather than logic clauses, and ordered aggregation (fold) extends the base language for count arithmetic.

**Type-theoretic proof assistants** (Coq, Lean, Agda): Formal verification with dependent types. Nam's mantra signatures are a lightweight typed function system without the proof obligation — the graph declares what functions exist and what they need, not that they are correct in all cases.

**Category-theoretic knowledge representation**: The visheshanam ring is a small category with 46 morphisms. The pipeline is a functor from the question category to the answer category. We do not claim full categorical rigor but note the structural correspondence.

**What is genuinely novel:**
1. The ontology is structurally grounded in the algebra — philosophical nodes (shunya, pratipaksha) ARE the algebraic nodes the pipeline reads (Section 6)
2. The graph describes its own edge types, distinguishing what is axiomatized from what is proven (Theorem 1, Section 1.2)
3. Natural language maps to algebraic operations via a 211-node lexical morphism using graph walks, not learned embeddings (Section 4.2)
4. The fold identity (0), philosophical completeness (purna), and the sentence boundary (viraam) are connected through abheda edges — a structural claim verified by graph walk, with the level-indexed nature of abheda made explicit (Section 6.2)
5. The system is honest about its limits: it can only compute what its declared mantras cover, and it distinguishes axioms from theorems from interpretations throughout
