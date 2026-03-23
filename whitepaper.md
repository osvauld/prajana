# Mathematical Foundations of a Self-Describing Proof Graph

## Abstract

A proof graph $G \in \{0,1\}^{N \times N \times R}$ where nodes are claims (nigamana) and typed edges are relations (visheshanam). The system derives answers to natural-language questions by walking its own structure — no external inference engine, no neural network at query time.

The graph declares:
- An operation algebra $(\Sigma, \circ, {}^{-1})$ with eval, arity, and pratipaksha (inverse)
- A mantra layer $\mathcal{M} = \{m_i : \text{janya}(m_i) \to \text{phala}(m_i)\}$ of typed functions expressed as krama s-expressions
- A graded ring $R = \bigoplus_n R_n$ over sentence-grades with lexical morphism $\delta: \text{Words} \to V$
- A non-commutative visheshanam ring $\mathcal{V}$ with 10 generators governing edge composition

The philosophical ontology (Advaita Vedanta, Shaiva Tantra) is structurally grounded in the algebra: $\text{shunya} = 0_\oplus$, $\text{pratipaksha} = {}^{-1}$, fixpoint iteration $= \text{pratibodha}$.

## The Proof Graph

The proof graph is a 3-tensor:

$$G \in \{0,1\}^{N \times N \times R}$$

Each node is a nigamana (truth-that-holds). The visheshanam ring $\mathcal{V}$ has 10 generators:

| Generator | Symbol | Algebraic role |
|-----------|--------|----------------|
| swarupa | $1_\otimes$ | multiplicative identity |
| abheda | $\equiv$ | equivalence |
| sthita | $\leq$ | partial order |
| yukta | $+$ | addition |
| siddha | $\vdash$ | provability |
| kriya | $\times$ | multiplication (non-commutative) |
| phala | $\to$ | consequence |
| janya | $\leftarrow$ | origin |
| drishthanta | $\exists$ | witness |
| pratipaksha | ${}^{-1}$ | group inverse |

Ring axioms: $\text{yukta} = \oplus$, $\text{kriya} = \otimes$ (non-commutative), $\text{shunya} = 0_\oplus$, $\text{swarupa} = 1_\otimes$, $\text{pratipaksha} = {}^{-1}$.

The graph is self-describing: the node `visheshanam` $\in G$ declares the ring structure using the same edge types it defines.

## The Operation Algebra

The operation algebra $\Sigma$ is the set of all graph nodes carrying an `eval` key in their shabda. Each operation $\sigma \in \Sigma$ is a triple:

$$\sigma = (\text{eval}(\sigma),\ \text{arity}(\sigma),\ \text{pratipaksha}(\sigma))$$

where $\text{eval}: \Sigma \to \text{Prim}$ maps to a primitive function, $\text{arity}: \Sigma \to \mathbb{N}$ gives argument count, and $\text{pratipaksha}: \Sigma \to \Sigma$ is the algebraic inverse.

Pratipaksha is an involution on the symmetric core:

$$\text{pratipaksha}(\text{pratipaksha}(\sigma)) = \sigma$$

Verified pairs: $\text{add} \leftrightarrow \text{sub}$, $\text{mul} \leftrightarrow \text{div}$, $\text{square} \leftrightarrow \text{sqrt}$, $\text{half} \leftrightarrow \text{double}$, $\log \leftrightarrow \text{pow}$.

The pratipaksha relation is a graph edge — the inverse declaration lives in the same structure as the concepts it inverts. No external table; the graph IS the algebra.

Resolution is $O(1)$ via an eval index $\iota: \text{EvalName} \to \text{NodeName}$ built at load time.

## Mantra Signatures

A mantra is a node $m$ with typed function signature:

$$m : \text{janya}(m) \to \text{phala}(m)$$

The computation is expressed as a krama — a compositional s-expression over $\Sigma$:

$$p = mv \quad \Longleftrightarrow \quad \texttt{(krama multiplication mass velocity)}$$

$$K = \tfrac{1}{2}mv^2 \quad \Longleftrightarrow \quad \texttt{(krama half (multiplication mass (square velocity)))}$$

$$T = \frac{2\pi}{\omega} \quad \Longleftrightarrow \quad \texttt{(krama division (multiplication 2 pi) angular-velocity)}$$

Evaluation is recursive descent: tokenize the krama, resolve each op via $\iota$, apply with bound values. The s-expression IS the computation.

Chain derivation computes the least fixpoint:

$$\text{derive-chain} = \text{lfp}(\text{derive-step})$$

At each step, every mantra whose janya are all bound fires and binds its phala. Terminates by Kleene's theorem: monotone operator on a finite lattice.

## Formula Inversion via Krama + Pratipaksha

Given mantra $m$ with $\text{krama}(m) = \sigma_1(\sigma_2(\ldots, x_i), x_j)$ and known phala $c$, solve for $x_k$:

**Step 1.** Extract the op-path from root to $x_k$:

$$\text{krama-path}(m, x_k) = [\sigma_1, \sigma_2, \ldots, \sigma_n]$$

**Step 2.** Reverse:

$$[\sigma_n, \ldots, \sigma_2, \sigma_1]$$

**Step 3.** Replace each $\sigma_i$ with $\text{pratipaksha}(\sigma_i)$ and apply:

$$x_k = \sigma_n^{-1}(\ldots \sigma_2^{-1}(\sigma_1^{-1}(c, b_1), b_2) \ldots)$$

where $b_i$ are the other arguments at each binary node, resolved from bindings.

**Example.** Solve $K = \tfrac{1}{2}mv^2$ for $v$:

$$[\text{half}, \text{mul}, \text{square}] \xrightarrow{\text{reverse}} [\text{square}, \text{mul}, \text{half}] \xrightarrow{\text{pratipaksha}} [\text{sqrt}, \text{div}, \text{double}]$$

$$v = \sqrt{\frac{2K}{m}}$$

Inversion is a **graph walk**, not symbolic algebra. The formula structure (krama) is data in $G$. The inverse operations (pratipaksha) are edges in $G$. A tantra reads both and composes them.

Logical inversion follows the same mechanism: $\land \leftrightarrow \lor$ via De Morgan, $\Rightarrow \mapsto$ contrapositive. The walk is uniform across algebraic and logical domains.

## The Graded Ring and Lexical Morphism

A paragraph is a graded ring:

$$R = \bigoplus_{n=0}^{k} R_n$$

where $R_n$ is the fact-set at sentence-grade $n$. Grade boundary $= \text{viraam}$ (period). $\oplus$ is intra-sentence accumulation. $\otimes$ is cross-sentence entity selection. Fold identity $= 0 = \text{shunya}$.

The lexical morphism $\delta: \text{Words} \to V$ maps surface words to graph concepts:

$$\delta(\text{"heavier"}) = \text{viveka-max}, \quad \delta(\text{"flew"}) = \text{kshaya}, \quad \delta(\text{"find"}) = \text{vidhi-kaala}$$

$\delta$ is structure-preserving: it maps $\text{kshaya} \leftrightarrow \text{vriddhi}$ and preserves pratipaksha. The count fold:

$$\text{acc}_0 = 0, \quad \text{acc}_{n+1} = \text{acc}_n \oplus_d v_n$$

where $\oplus_d$ is direction-determined: $\text{kshaya} \Rightarrow \text{sub}$, $\text{vriddhi} \Rightarrow \text{add}$.

## Pipeline as Stratified Evaluation

The answer function is a composition of monotone strata:

$$\text{answer} = \text{emit} \circ \text{dispatch} \circ \text{detect} \circ \text{expand} \circ \text{refine}^* \circ \text{assert} \circ \text{construct}$$

Structurally equivalent to Datalog stratified evaluation. Each stratum $S_i$ is monotone: $S_i(T) \supseteq T$ (only adds triples, never removes). The refine stratum is a krama-ordered chain of 13 sub-passes wrapped in fixpoint.

Within a grade, facts form a set (commutative, idempotent). Across grades, results compose relationally. Rules are graph walks, not logic clauses.

## The Signal Bus

Three signal layers form an encoding/decoding channel:

$$\text{detect}(\text{encode}) \xrightarrow{\text{channel}} \text{dispatch}(\text{decode})$$

1. **Lexical** — $\delta(\text{word}) \to \text{node} \to \text{edges} \to$ typed triples (satya, sankhya, mithya, copula, vidhi-kaala)
2. **Grammar** — verb morphology emits kaala (tense) $+$ vachana (number) on subjects
3. **Intent** — pattern detection writes signal triples into the question graph

The write-signal/read-signal contract: detect encodes intent, dispatch decodes it. In information-theoretic terms: encoding $=$ detect, decoding $=$ dispatch, channel $=$ question graph, noise $=$ mithya, redundancy $=$ monotonicity.

## Ontological Grounding

The philosophy IS the algebra — not metaphor layered on it. Three grounding levels:

**Load-bearing** (same node, two descriptions): $\text{shunya}$ IS the additive identity $0_\oplus$ — the fold seed reads it. $\text{pratipaksha}$ IS the algebraic inverse ${}^{-1}$ — the count-chain walks it. Delete these nodes and the pipeline breaks.

**Level-indexed** (one concept, multiple roles): $\text{purna} \equiv \text{shunya}$ at the $\oplus$ level AND $\text{purna} \equiv \text{eka}$ at the $\otimes$ level. Abheda is level-indexed — the graph enforces this by omitting the $\text{shunya} \leftrightarrow \text{eka}$ edge.

**Interpretive** (structural analogy, no direct edge): $\text{pratibodha} \sim \text{fixpoint}$, $\text{spanda} \sim \text{eval}$. Philosophically compelling but computationally dispensable.

## Panchaavayava — The Proof Structure

Every answer follows the five-limbed syllogism (panchaavayava), the Indian proof structure from Nyaya:

$$\text{pratijna} \to \text{hetu} \to \text{udaharana} \to \text{upanaya} \to \text{nigamana}$$

1. **Pratijna** (thesis) — states given values
2. **Hetu** (reason) — states what is sought
3. **Udaharana** (example) — shows the mantra formula
4. **Upanaya** (application) — substitutes values into the formula
5. **Nigamana** (conclusion) — states the result

The structure arises from the graph walk. The phala chain $\text{hetu} \xrightarrow{\text{phala}} \text{udaharana} \xrightarrow{\text{phala}} \text{upanaya} \xrightarrow{\text{phala}} \text{nigamana}$ exists as edges in $G$.

## S-Expression Syntax

Three file formats unified under s-expressions:

- **om5**: `(layer name (relation target...) ...)` — declares $G$
- **shabda**: `(shabda node (key value)...)` — metadata on nodes
- **tantra4**: `(tantra name (params) body...)` — computation

A tantra is a composition of named operations from $\Sigma$. Last expression is return value. Bindings are `(name expr)`. With sufficient named helpers, tantra bodies read as sentences — compositions of words in the operation algebra.

Four abstraction layers: $\text{primitives} \to \text{operations} \to \text{compositions} \to \text{pipeline}$. Each layer composes the one below.

## Results and Capabilities

The system answers: mantra computation (forward via krama, inverse via pratipaksha walk), chain derivation (fixpoint on $\mathcal{M}$), entity-scoped computation, count arithmetic (grade fold on $R$), comparison (viveka), categorical inference (anumana via varga chain). Every answer is a panchaavayava proof.

All computation is s-expression tantras composing $\Sigma$. The pipeline is stratified Datalog. Forward evaluation and inversion share the same graph — krama for the formula tree, pratipaksha for the inverse at each node.

## Glossary

Categorized index of terms. Sanskrit/philosophical terms with their algebraic and computational roles.

### Graph Structure

| Term | Meaning | Algebraic role |
|------|---------|----------------|
| nigamana | truth-that-holds | node in $G$ |
| visheshanam | relation type | edge label, ring generator |
| satya | truth-score | convergence measure via fixpoint |
| kosha | domain layer | typed subgraph |
| sangati | root layer | foundational concepts |

### Visheshanam (Edge Types / Ring Generators)

| Term | Meaning | Symbol |
|------|---------|--------|
| swarupa | identity / IS | $1_\otimes$ |
| abheda | non-difference | $\equiv$ |
| sthita | foundation / rests-on | $\leq$ |
| yukta | connection | $+$ |
| siddha | proof / verified | $\vdash$ |
| kriya | function / acts-as | $\times$ |
| phala | consequence / produces | $\to$ |
| janya | origin / born-from | $\leftarrow$ |
| drishthanta | evidence / witness | $\exists$ |
| pratipaksha | inverse / opposite | ${}^{-1}$ |

### Computation

| Term | Meaning | Role |
|------|---------|------|
| mantra | formula node | $m : \text{janya} \to \text{phala}$ |
| krama | ordered sequence | s-expression over $\Sigma$ |
| tantra | declarative program | composition of named ops |
| shabda | metadata | key-value pairs on nodes |
| eval | evaluation name | primitive dispatch key |
| janya | input variables | domain of $m$ |
| phala | output / result | codomain of $m$ |

### Algebra

| Term | Meaning | Role |
|------|---------|------|
| shunya | zero / void | $0_\oplus$, fold identity |
| eka | one / unit | $1_\otimes$ at mul level |
| purna | fullness | $\equiv \text{shunya}$ at $\oplus$, $\equiv \text{eka}$ at $\otimes$ |
| pratipaksha | inverse | involution: $\sigma^{-1^{-1}} = \sigma$ |
| kshaya | decrease | $\Rightarrow \text{sub}$ in count fold |
| vriddhi | increase | $\Rightarrow \text{add}$ in count fold |
| viveka | discrimination | comparison operator |
| viraam | period / stop | grade boundary in $R$ |

### Pipeline / Inference

| Term | Meaning | Role |
|------|---------|------|
| anuvada | translation | reasoning layer |
| avrti | spiral return | fixpoint iteration |
| sandhi | joining | morphological composition |
| anumana | inference | categorical reasoning via varga |
| varga | category / class | type hierarchy for inference |
| mithya | false / noise | rejected triples |
| vidhi-kaala | imperative tense | seek/find signal |

### Proof Structure (Panchaavayava)

| Term | Meaning | Step |
|------|---------|------|
| pratijna | thesis | states givens |
| hetu | reason | states sought |
| udaharana | example | shows formula |
| upanaya | application | substitutes values |
| nigamana | conclusion | states result |

### Philosophy (Grounding)

| Term | Meaning | Algebraic ground |
|------|---------|-----------------|
| shunya | emptiness | additive identity $0_\oplus$ |
| pratipaksha | opposition | algebraic inverse ${}^{-1}$ |
| pratibodha | awakening-to-awakening | fixpoint |
| spanda | self-pulsation | eval / computation |
| iccha | will / directed-reaching | directed graph walk |
| om | the primordial | root convergence |

---

## Implementation

Source: [github.com/osvauld/prajana](https://github.com/osvauld/prajana)
