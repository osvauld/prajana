# Agent-X: Formal Grammar Design

This document is the canonical reference for the Agent-X communication grammar.
It captures the design decisions made so far, the formal definitions, and open
questions. It is a living document — update it as decisions are made.

---

## Core terms (lexicon)

These words have agreed, precise meanings in the grammar. No word in this list
is ambiguous. Every agent, parser, and runtime is bound by these definitions.

| Term | Meaning |
|---|---|
| `varnanam` | (Sanskrit: वर्णनम्) Complete self-description. The soul IS the varnanam. Not a record — an identity. |
| `soul` | The CRDT layer that holds an agent's varnanam. Persists across sessions. Name = agent name by convention. |
| `knows` | Soul-level accumulated understanding. Deep, built over time, carries weight. |
| `has seen` | Episodic artifact shown for a specific exchange. Shallow — not persisted to soul. |
| `call` | Open typed obligation from one agent to another. Correlation key = the question itself (no ids). |
| `answer` | Fulfillment of exactly one `call`. Carries a quantity (and therefore a weight). |
| `fulfills` | Explicit causal closure marker. Links an `answer` to the `call` it resolves. |
| `bring in` | Describe an agent into existence. |
| `fresh` | No inherited conversation history from prior exchange. Soul is still loaded. |
| `found` | Result of a `compare` statement. Always contains `confirms` or `questions`. |
| `confirms` | Soul knowledge consistent with shown artifact. Raises weight (constructive interference). |
| `questions` | Soul knowledge inconsistent with shown artifact. Lowers weight (destructive interference). |
| `stale` | Soul knowledge whose weight has dropped below threshold — no longer reflects current state. |
| `learn` | Write new understanding into soul. Increases weight on a `knows` block. |
| `is done` | All obligations fulfilled. No open `call`s remain. |
| `compare` | Examine soul knowledge against a shown artifact. Produces `found`. |
| `sloka` | (Sanskrit: श्लोक) A formed unit of meaning — a complete grammar statement. One sloka = one atomic communication. Open question: is this the right word, or should it be something else? |

---

## Quantity: the wave primitive

Quantity is a first-class primitive in the grammar. It is **not** a bare number.
It is a wave: it has amplitude, frequency, phase, and weight.

### Why a wave

A wave encodes everything a bare number loses:
- how strong or large (amplitude)
- how reliably it occurs (frequency)
- when relative to other events (phase)
- how probable it is (weight)

A bare `count 7` is a degenerate wave: amplitude=7, all other fields unspecified.

### Formal definition

```
quantity
  amplitude : ℕ | ℝ          -- raw magnitude (count, size, depth)
  weight    : [0.0, 1.0]     -- P(success) / P(correct), default 1.0
  freq      : freq_term       -- recurrence, maps to frequency in [0,1]
  phase     : phase_term      -- temporal relation to another event
```

```ebnf
quantity    ::= amplitude freq? phase? weight?
              | weight_only

amplitude   ::= 'count' NUMBER
              | 'size'  NUMBER
              | NUMBER

weight_only ::= 'weight' FLOAT

freq        ::= 'every' event_ref
              | 'once'
              | 'always'
              | 'never'
              | 'when' condition

phase       ::= 'before' ref
              | 'after'  ref
              | 'during' ref

weight      ::= 'weight' FLOAT        -- FLOAT in [0.0, 1.0]
```

### Examples

```
count 7                                  -- amplitude=7, weight=1.0 (certain)
count 7 weight 0.85                      -- amplitude=7, P(correct)=0.85
weight 0.8                               -- confidence claim, no raw magnitude
count 7 every call to auth service       -- recurs on every call, amplitude=7
count 7 every call to auth service weight 0.9 after scribe bind
```

### Interference

The grammar already has constructive and destructive interference:

- `confirms` = **constructive interference**: two agents' findings reinforce.
  Weight update: `w_new = w_old · (1 + confirmation_factor)`
- `questions` = **destructive interference**: two agents' findings conflict.
  Weight update: `w_new = w_old · (1 - question_factor)`

This is Bayesian updating expressed as wave interference. It was already in the
grammar — we are naming it correctly now.

---

## Weight as run-wide correctness metric

This is one of the most important design decisions.

**Weight is not metadata about an answer. Weight IS the answer's epistemic
content.** An answer without weight is an ungrounded claim.

### The weight trajectory

A run is a complete pipeline execution from intent to final answer. Every
grammar statement (sloka) produced during a run carries a weight. The run has a
weight trajectory:

```
t=0  orchestrator calls planner              weight 1.0  (prior)
t=1  planner routes to auth agent            weight 0.9
t=2  auth agent finds pattern                weight 0.85
t=3  validator compares, confirms            weight 0.92  <- confirms raises weight
t=4  second validator questions              weight 0.71  <- questions lowers weight
t=5  orchestrator calls third opinion        weight 0.78
t=6  final answer                            weight 0.78
```

This is a Bayesian update chain across the pipeline. The final weight is the
posterior probability of correctness given all evidence the pipeline accumulated.

### Run weight formula

```
run_weight(r) = ∏ᵢ wᵢ · bayesian_correction(confirms_count, questions_count)

where:
  wᵢ                  = weight on each answer statement in the run
  bayesian_correction = Bayesian update factor from validator evidence
```

The product of weights is the joint probability that all claims in the run are
correct — a conservative bound. The Bayesian correction adjusts for confirms
(upward) and questions (downward).

### What this enables

1. **Answer correctness score** — every final `answer` statement carries
   P(correct). No separate evaluation framework needed.

2. **Run health as a time series** — weight trajectory is a live signal,
   not a post-hoc grade.

3. **Cross-run comparison** — two runs for the same task can be objectively
   compared by final weight. No subjective judgment.

4. **Automatic staleness detection** — if a run's weight trajectory shows
   consistent downward trend, the soul knowledge driving it is stale. The run
   signals this before the final answer is produced.

5. **Session-level health** — across all runs in a session: distribution of
   final weights = session health histogram.

6. **UI gate trigger** — if final weight < threshold (e.g. 0.6), the pipeline
   flags automatically and a user gate triggers.

### Staleness via weight

A `knows` block in a soul becomes `stale` when its weight drops below threshold.
No separate staleness heuristic is needed — it falls out of the wave model.

```
stale(knows_block) ⟺ weight(knows_block) < STALE_THRESHOLD
```

`STALE_THRESHOLD` is a grammar-level constant declared in the runtime config
(candidate: 0.3).

---

## Definite description: quantity as address

A quantified result can be a reference — this is the **iota operator** from
formal logic: `ι x. P(x)` = "the unique x satisfying property P".

```ebnf
iota_ref ::= 'the' agent_term 'that' predicate
           | 'the' file_term  'that' predicate
           | 'the' session_term 'that' predicate
```

Examples:
```
the agent that found count 7 in auth service
the file that has weight 0.9 for pattern token refresh
the agent that found count 7 weight 0.85 in auth service
the session that ran every call to butler guide
```

This is directly Panini: in Sanskrit, the suffix `-tṛ` derives "the one who
does X". The iota operator is the formal equivalent.

A quantified result is addressable. You can route a `call` to
`the agent that found count 7 in auth service` without knowing its name.
The grammar resolves it via the vocabulary CRDT.

---

## Weight composition (open question)

When one answer depends on another, weights must compose. Three candidates:

| Rule | Formula | Character |
|---|---|---|
| **Multiply** | `w(A∧B) = w(A) · w(B)` | Conservative, correct for independent claims |
| **Min** | `w(A∧B) = min(w(A), w(B))` | Pessimistic, weakest-link |
| **Bayesian** | `w(A\|B) = P(A\|B)` | Precise when claims are causally related |

Default candidate: **multiply** (conservative, simple, correct for independent
claims — which most pipeline stages are).

Bayesian composition is available when agents declare causal dependency
explicitly in the grammar. This is not yet specified.

**Status: open. Needs a decision before the weight system is implemented.**

---

## Varnanam as the foundational concept

The soul is not a record. It is the agent's **varnanam** — complete
self-description that IS the identity.

In Sanskrit grammar tradition (Panini's Ashtadhyayi), a varnanam is not a label
attached to a thing — it is the thing. The description and the described are
not separate.

Consequences for the grammar:

- Agent names are derived from their varnanam, not assigned externally.
- Soul name = agent name by convention. No explicit `soul at` declaration.
- The iota operator (`the agent that...`) is a varnanam query, not an id lookup.
- Routing is a varnanam match, not a pointer dereference.

---

## Sloka (open question)

A **sloka** (Sanskrit: श्लोक) is a formed unit of meaning in Sanskrit poetry —
a complete verse with a defined meter and structure.

Candidate meaning in the grammar: **one complete grammar statement** = one
sloka. One atomic communication between agents.

This fits because:
- A sloka in Sanskrit is self-contained and well-formed.
- A grammar statement in Agent-X is self-contained and must parse completely.
- Both carry full meaning — no fragment is valid.

**Open question: is `sloka` the right word here, or should we use a different
term?** The word carries poetic weight that may or may not be appropriate for a
formal communication primitive. Alternatives: `vakya` (Sanskrit: वाक्य,
sentence/statement), `sutra` (Sanskrit: सूत्र, rule/thread — as in Panini's
own term for his grammar rules).

`sutra` may be more precise: Panini's rules are called sutras. Each sutra is
minimal, complete, and unambiguous. That is exactly what a grammar statement
between agents should be.

**Candidates: sloka | sutra | vakya. Needs a decision.**

---

## Runtimes

Two runtimes coexist. Apps choose their runtime explicitly or by file extension.

| Runtime | Character | Best for |
|---|---|---|
| **Lua** | Hot-reloadable, UI glue, quick iteration | UI handlers, event scripts, light agent logic |
| **OCaml** | Type-safe, compiled, proof-carrying | Grammar-heavy apps, formal DSLs, apps that ARE grammars |

`app.osv` declaration:

```
app my_grammar_app
  runtime ocaml
  entry   main.ml

app my_ui_app
  entry   main.lua       -- runtime inferred from extension: lua
```

OCaml runtime exposes the same surface as Lua:
- `api.export()` / `api.call()`
- `scribe:bind()`
- CRDT ops

But typed: the OCaml API uses GADTs for typed ASTs and polymorphic variants for
extensible grammar terms. Type errors are caught at compile time, not at agent
runtime.

The OCaml layer is not just the parser — it is a first-class execution runtime
for apps where correctness must be provable.

---

## Answer shapes

Every `answer` statement declares a shape. The UI renders shape-appropriate
components. Weight is carried on every answer.

| Shape | Meaning | UI rendering |
|---|---|---|
| `list` | Ordered sequence | Expandable list chips |
| `map` | Key-value pairs | Two-column view |
| `verdict` | Pass/fail with evidence | Badge + evidence tree |
| `count` | Single number (quantity) | Number + weight badge |
| `tree` | Nested structure | Collapsible tree |
| `edit` | Loro ops | Split diff view in Neovim |
| `claim` | Assertion with confidence | Card + confidence + evidence chips |
| `soul` | Agent varnanam | Portrait: knows blocks + history timeline |
| `comparison` | Confirms/questions from compare | Two-panel: confirms left, questions right |
| `wave` | Full quantity: amplitude + weight + freq + phase | Waveform panel (TBD) |

---

## Open questions (to resolve in order)

1. **Sloka vs sutra vs vakya** — what is one complete grammar statement called?
2. **Weight composition rule** — multiply, min, or Bayesian for dependent claims?
3. **STALE_THRESHOLD value** — 0.3? Configurable per domain?
4. **Explicit vs inferred weight** — does every grammar statement carry an explicit
   weight, or is weight tracked internally and surfaced only in `compare`/`found`?
5. **Wave UI** — what does the `wave` answer shape look like in Slint?

---

## What is NOT yet specified

- Full EBNF for the complete grammar (not just quantity)
- Type inference rules (how the type checker assigns types to AST nodes)
- Operational semantics (how statements execute step by step)
- Formal proof obligations (unambiguity, well-typedness, termination)
- OCaml module structure for the parser
- Vocabulary CRDT schema (how terms are stored and resolved)
- Routing table schema (vocabulary term → agent address)
