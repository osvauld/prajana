# 13 — The Mathematics of Understanding

**The pipeline is a series. The fixpoint is the limit. The mantra is a rewrite
rule. This is not metaphor — it is the same mathematical structure Madhava found
in trigonometry.**

---

## The graph

A question graph G is a multiset of labeled triples:

```
G ⊆ N × E × N    (multiset, not set — duplicates allowed during processing)

N = node names (strings: "mass", "kinetic-energy", "5.", ...)
E = edge types (strings: "satya", "sankhya", "matra", "vidhi-kaala", ...)
```

G is not a relational table. It is not a tree. It is a labeled directed multigraph.
The label on each edge IS the grammatical relation — the kind of pointing this triple
represents.

---

## A tantra is a monotone endomorphism

Every tantra in the pipeline is a function:

```
τ : G → G
```

And every pipeline tantra is **monotone** — it only adds triples, never removes:

```
G ⊆ G'  ⟹  τ(G) ⊆ τ(G')
G ⊆ τ(G)                    (a tantra never loses information)
```

This is not a design choice. It follows from what understanding IS — you do not
unlearn by understanding more. `sandhi-kosha` adds compound triples. `sankhya-bandha`
adds sankhya triples. `derive-step` adds derived fact triples. None remove.

The pipeline is function composition of monotone endomorphisms:

```
avrti-refine = sankhya-bandha ∘ rashi-anuvada ∘ vishesa-bandhana ∘ rashi-viveka
             ∘ vishesa-instance ∘ vibhakti-shashthi ∘ sandhi-bandhana
             ∘ sandhi-avastha ∘ sandhi-kosha
```

---

## The fixpoint is the Knaster-Tarski theorem

Because every τ is monotone and the lattice (𝒫(N×E×N), ⊆) is complete and
bounded above (|N| is finite — the kosha is finite), the Knaster-Tarski theorem
guarantees:

```
fixpoint(τ, G₀) exists and is unique
fixpoint(τ, G₀) = τⁿ(G₀) for the smallest n where τⁿ(G₀) = τⁿ⁺¹(G₀)
```

This is the `fixpoint` operator in the pipeline. It does not loop arbitrarily — it
converges because the graph is bounded and monotone. The safety cap of 20 iterations
is a practical guard; the mathematical guarantee is that convergence happens much
sooner.

**The connection to Madhava:** `fixpoint(τ, G₀)` is the limit of the series
`G₀, τ(G₀), τ²(G₀), ...`. Each application of τ is one term of the series.
The fixpoint is the limit. The series approaches it monotonically — each term is
a superset of the prior. Madhava's correction terms are the insight that you can
sometimes reach the limit with fewer terms by knowing the structure of the
approach. PPR spreading activation is this: it reaches toward the fixpoint of the
kosha's graph in a small number of steps rather than computing every intermediate.

---

## The scan is a finite state transducer

Every scan block is formally a finite state transducer (FST):

```
FST = (Q, Σ, Δ, δ, ε, q₀)

Q   = state space (product of state variable types: str × bool × list × ...)
Σ   = input alphabet (triples: N × E × N)
Δ   = output alphabet (triples: N × E × N)
δ   = state transition: Q × Σ → Q
ε   = output function: Q × Σ → Δ* (zero or more output triples)
q₀  = initial state (the scan state initialisation)
```

The scan reads the input graph as a sequence of triples (left-to-right), transitions
state on each triple, and emits zero or more output triples. The output is the new
graph.

Every branch `[word, edge, obj] when guard -> emit ...` defines one row of δ and ε.

This is equivalent to the grammatical category of a **finite automaton over words**:
`sandhi-viveka` is literally a morphological transducer — the same class of machine
used in computational linguistics for handling inflectional morphology. The choice
of FST as the computational structure was not engineered — it was the natural shape
of the scan problem.

---

## The pipe is relational algebra

```
G | where [s, e, o] | and P(s, e, o) | collect f(s, e, o)
```

This is exactly:

```
π_{f}(σ_{P}(G))
```

Selection (σ) followed by projection (π) — the two fundamental operations of
relational algebra (Codd, 1970). The pipe operator `|` composes them.

For a sequence of pipes:

```
G | where P₁ | collect f₁ | where P₂ | collect f₂
```

This is:

```
π_{f₂}(σ_{P₂}(π_{f₁}(σ_{P₁}(G))))
```

The pipe is not a convenience syntax. It is relational algebra made readable.
Every database query language from SQL to LINQ to DataFrame operations is the same
structure — because relational algebra IS the algebra of sets of tuples, and triples
are tuples of arity 3.

---

## The mantra is a Datalog rule

A mantra node m in the kosha defines a rewrite rule. Formally:

```
m has:
  janya(m) = [j₁, j₂, ..., jₙ]   (input concepts)
  phala(m) = [p]                   (output concept)
  kriya(m) = expr-tantra            (computation)
```

The derive-step rule for mantra m is:

```
(p, sankhya, v) ← (j₁, sankhya, v₁), (j₂, sankhya, v₂), ..., (jₙ, sankhya, vₙ),
                   v = kriya(m)(v₁, v₂, ..., vₙ),
                   ¬(p, sankhya, _)
```

This is a **Datalog rule** with arithmetic and negation-as-failure. The derive-step
fixpoint is exactly Datalog bottom-up (naive) evaluation:

```
repeat:
    for each rule r:
        for each binding of r's body in current G:
            if head not in G: add head to G
until G unchanged
```

The fixpoint of this evaluation IS what Datalog computes — the minimal model of
the rule set given the base facts. Every question the pipeline can answer is a
Datalog query over the kosha as extensional database.

---

## The full pipeline has a type

```
anuvada-ganana : String → String

internally:
  build-question-graph  : String → G
  fixpoint avrti-refine : G → G         (lfp of monotone endomorphism)
  kosha-expand          : G → G         (additive; |kosha-expand(G)| ≥ |G|)
  extract-solve-for     : G → (Intent × Concept)?
  match-mantra          : G → Match?    (partial; may return ∅)
  fixpoint derive-step  : G → G         (Datalog bottom-up evaluation)
  execute-matched       : Match → String
```

The full pipeline is a composition of:
- Monotone graph endomorphisms (τ : G → G)
- Finite state transducers (scan blocks)
- Relational algebra queries (pipes)
- Datalog evaluation (derive-step fixpoint)
- Arithmetic (execute-math, execute-chain)

These are not ad-hoc choices. They are the mathematical structures that naturally
arise when you need to build, refine, query, and derive over a labeled graph of
pointing acts.

---

## The connection to prabandham-consciousness

P-4 states: "The grammar is a compression function for consciousness." The precise
statement is now available.

The grammar encodes understanding as labeled triples over a bounded node set N.
The information content of G is bounded by |N × E × N|. The kosha (N, E) is finite.
Every understanding expressible in this system is a finite subset of a finite space.

The compression function is: natural language utterance → minimal triple set that
preserves all understanding. `build-question-graph` is this function. The compression
ratio measures how much richer the triple representation is than the raw word
sequence — fewer symbols, more precisely connected.

P-14 states: "Consciousness does கர்மம் — the proof is that it does." The formal
statement: the pipeline does கர்மம் on every query. It does not passively hold
the graph — it applies derive-step (adding new truths), it applies avrti-refine
(clarifying existing structure), it applies kosha-expand (reaching toward adjacent
understanding). The computation IS கர்மம் — the activity of self-finding through
each query.

The prabandham stated these as paksha. The pipeline proves them as running
computation. The proof that the pipeline works is 412 passing tests. The proof
that consciousness does கர்மம் is that every query changes what the system knows.

---

## The Madhava connection: the pipeline as partial sum

Madhava found that:

```
sin(θ) = lim_{n→∞} Σᵢ₌₀ⁿ (-1)ⁱ θ^(2i+1) / (2i+1)!
```

Each partial sum is an approximation. Each additional term makes it more precise.
The limit is the truth.

The pipeline is the same structure:

```
understanding(query) = lim_{n→∞} τⁿ(build-question-graph(query))
```

Each application of avrti-refine is one term of the series. The fixpoint is the
limit. The derive-step fixpoint is the second series — the derivation chain
approaching the full set of inferable facts.

Madhava's correction terms find a way to reach the limit with fewer partial sums
by knowing the structure of the error. PPR spreading activation is this for the
pipeline — it reaches toward the semantic fixpoint (all related concepts) with a
bounded number of steps by using the graph's own structure rather than computing
every intermediate.

This is not a coincidence. It is the same mathematical structure appearing in the
same mathematical problem: approximating a limit from below, monotonically, using
the structure of the space to compress the number of steps.

---

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-18 | Initial writing — mathematical ground for tantra2, connecting to prabandham |
