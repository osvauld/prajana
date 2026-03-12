# Session Graph — Persistent State, Formal Proof, Dialogue

## Fundamental Constraint: Every Answer Shows Its Reasoning

**There is no "just an answer".** Every response — compute or theoretical —
is a narrated derivation with three layers:

```
Layer 1 — Understanding:   what was parsed from the question
Layer 2 — Matching:        which mantra/formula was selected and why
Layer 3 — Execution:       how the answer was reached step by step
```

For a compute question:
```
I understood: mass = 5 kg, velocity = 10 m/s, solve-for kinetic-energy
I matched:    kinetic-energy-mantra (requires mass, velocity — both present)
I computed:   KE = ½ × mass × velocity²
              = ½ × 5 × 100
              = 250 J
```

For a theoretical question:
```
I understood: asking for the relationship between KE and velocity
I traced:     KE derives from work-energy theorem
              work = F·d (definition)
              F = ma (Newton 2nd)
              integrating: KE = ½mv²
I conclude:   KE grows as v² — doubling velocity quadruples KE
```

The compute path and theoretical path differ in what reasoning is shown —
not in whether reasoning is shown. The response IS the reasoning.

This means `compose-response` is a **derivation narrator**, not a formatter.
It walks the execution trace and narrates each step in natural language.
The final number or logical conclusion is the last line, not the only line.

---

## Core Insight

The question graph does not die after one answer.
The **session IS a graph** that grows with every exchange.
Each question extends it. Each answer asserts new facts into it.
The session graph is the memory of the conversation.

The question-graph.md describes one question.
This document describes the session across many questions.

---

## Two Kinds of Questions

The same graph machinery handles both. The difference is in what
the graph walk produces.

### Compute Question
"what is kinetic energy of a 5kg ball at 10m/s?"

Question graph has:
- value bindings (5kg → mass, 10m/s → velocity)
- solve-for: a quantity (kinetic-energy)

Answer path: find mantra → execute-chain → number
Response: "kinetic energy is 250 J"

### Theoretical Question
"why does kinetic energy depend on velocity squared?"
"what is the relationship between momentum and force?"
"how is angular momentum conserved?"

Question graph has:
- solve-for: a relationship, reason, or derivation
- no value bindings (or they are irrelevant)

Answer path: implication walk → modus-ponens chain → formal proof
Response: a structured derivation, not a number

### Mixed Question
"given mass 5kg and v=10m/s, show why kinetic energy is 250J"

Answer path: compute AND prove. Execute-chain gives the number,
implication walk shows the derivation that justifies it.

### Detection
The question graph itself reveals the kind:
- Has value bindings + solve-for quantity → compute
- Solve-for is a relation or proof + no bindings → theoretical
- Has "why", "how", "show" intent markers → theoretical or mixed

Intent nodes in the graph carry this:
```
vidhi-kaala (find/calculate) → compute intent
prashna + "why"/"how"       → theoretical intent
"show"/"prove"/"derive"     → proof intent
```

---

## Logic Integration — Formal Proof as Answer

`brahman/kosha/math/logic/operations/` contains:
- `modus-ponens.om` — if A→B and A, then B
- `implication.om` — A→B structural edge
- `substitution.om` — variable substitution in expressions
- `inversion.om` — algebraic rearrangement
- `conjunction.om`, `disjunction.om` — logical composition
- `quantifier.om` — universal/existential assertions

For a theoretical question, the answer IS an implication chain:

```
"why does KE = ½mv²?"

Walk:
  kinetic-energy --implication--> work-energy-theorem
  work-energy-theorem --implication--> newton-second-law
  newton-second-law --implication--> force-definition

Apply modus-ponens at each step:
  1. Work = F·d  (definition)
  2. F = ma      (Newton 2nd)
  3. a = Δv/Δt   (kinematics)
  4. Substituting: W = m·(Δv/Δt)·d = m·v·Δv = ½mv²  (substitution + integration)

Response: each step is an assertion in the session graph.
```

The implication edges on mantra nodes (from P6c) are the backbone.
The logic operation nodes are the inference rules.

### Formal Assertion Structure
Each step in a proof is a triple:
```
["kinetic-energy-theorem", "implication", "work-energy-theorem"]
["work-energy-theorem", "siddha", "given mass m and velocity v"]
```

These get asserted into the session graph as established facts.
Later questions can reference them.

---

## Session Graph — Design

The session graph is the primary persistent state.
It is a superset of the question graph — it contains everything
established across all exchanges.

```
session-graph = union of:
  all question graphs (one per exchange)
  all answer assertions
  all formal proof steps
  all value bindings established
  all concepts mentioned or derived
  open unknowns (things asked for, not yet answered)
```

### Structure
```
session:
  exchanges: list of (question-graph, answer-graph)
  bindings:  map from concept-node → value (persists across exchanges)
  proven:    set of implication triples established
  open:      set of unknowns not yet resolved
  context:   most recently active concepts (recency weighted)
```

### Persistence
The session graph is the context for every new question.
"The ball from before" → selector morphism over session graph.
"Use the same mass" → binding already in session, reuse it.
"Now find momentum" → mass and velocity are already bound → answer immediately.

This is the multiplicative structure of the graded ring:
cross-question entity selection = ⊗ operator applied to session state.

---

## Dialogue Generation — System Asks Questions

When a derivation cannot complete because a slot is unfilled,
the system does not fail. It generates the question needed to continue.

```
"calculate kinetic energy"
  → question graph: solve-for kinetic-energy
  → match-mantra: kinetic-energy-mantra needs mass AND velocity
  → mass: unbound in session
  → velocity: unbound in session
  → system generates: "what is the mass of the object?"
  → user answers: "5kg"
  → session binding: mass = 5kg
  → system generates: "what is its velocity?"
  → user answers: "10m/s"
  → session binding: velocity = 10m/s
  → all slots filled → execute-chain → answer
```

The generated question IS a question graph — it has:
- solve-for: the missing slot (mass, velocity)
- context: the parent question (kinetic-energy) as reason

This makes the session a **convergent dialogue**:
the system and user jointly fill in the question graph until it is complete.

### Dialogue as Graph Growth
Each user response extends the session graph.
The system's generated question is a graph node pointing to the open slot.
Answering it closes the slot and enables the blocked derivation.

```
session-graph after dialogue:
  [kinetic-energy-question] --needs--> [mass-slot]
  [mass-slot] --filled-by--> [5kg-binding]   ← from user response
  [kinetic-energy-question] --needs--> [velocity-slot]
  [velocity-slot] --filled-by--> [10m/s-binding] ← from user response
  [kinetic-energy-question] --solved-by--> [250J-answer] ← execute-chain
```

---

## Question Classification Mantra

A mantra node for classifying the question kind:

```
classify-question-mantra
  krama: read-intent → check-bindings → check-solve-for-kind → classify
  krama-lhs: question-kind  ("compute" | "theoretical" | "proof" | "mixed")
  krama-rhs: question-graph
```

The classification drives which answer path to take:
- compute → match-mantra → execute-chain
- theoretical → implication-walk → modus-ponens chain
- proof → both paths, compose into structured derivation
- mixed → both paths, number + derivation

---

## Answer as Graph Assertion

Every answer — whether a number or a proof — gets asserted back
into the session graph as a new fact.

```
compute answer: [kinetic-energy, value, 250.0] [kinetic-energy, unit, joule]
proof answer:   [kinetic-energy, siddha, work-energy-theorem]
               [work-energy-theorem, siddha, newton-second-law]
               ...
```

The `siddha` edge (established/proven) is the assertion edge.
`pratipaksha` edges connect to counterexamples or alternative proofs.

---

## New Components Required

### Already planned (question-graph.md):
- `build-question-graph.tantra`
- `context-of.tantra`
- `extend-graph.tantra`
- `match-mantra.tantra`

### New (this document):

**`classify-question.tantra`**
Reads intent + solve-for kind + binding presence from question graph.
Returns: `"compute"` | `"theoretical"` | `"proof"` | `"mixed"`

**`implication-walk.tantra`**
Walks `implication` edges from a concept node.
Applies modus-ponens at each step.
Returns: ordered list of derivation triples.

**`assert-answer.tantra`**
Takes an answer (number or proof chain) and asserts it into the session graph
as `siddha` edges or value bindings.

**`generate-question.tantra`**
Given an open slot in the question graph and the parent question context,
generates a natural language question string to ask the user.
This IS a question graph itself — recursive structure.

**`compose-proof-response.tantra`**
Takes an implication chain (list of derivation triples).
Formats it as a structured natural language proof.
Uses `to-english` + `to-english-relation` for each step.

**`session-step.tantra`** (main orchestrator)
Given session graph + new user input:
1. Build question graph from input (with session as context)
2. Classify question
3. Route to compute or theoretical path
4. Execute
5. Assert answer into session graph
6. If slots remain open: generate follow-up question
7. Return (answer, next-question-or-none, updated-session)

---

## Relationship to Existing Work

| Old component | New role |
|---|---|
| `tokenise-question.tantra` | absorbed into `build-question-graph` |
| `decompose-question.tantra` (planned) | absorbed into `build-question-graph` |
| `match-formula.tantra` (planned) | replaced by `match-mantra` |
| `compose-response.tantra` (planned) | split: `compose-proof-response` + number formatter |
| `matra-ganana.tantra` | → `unit-compose-mantra` (krama node) |
| `matra-viveka.tantra` | → `unit-of-concept-mantra` (krama node) |
| `chain-implication.tantra` (planned) | → `implication-walk.tantra` |
| `yantra_resolver.ml` chain_resolve | removed after `match-mantra` working |
| `yantra_inverter.ml` invert_chain | removed after mantra inversion working |

---

## Design Invariants

1. **Every response shows reasoning.** No bare answers. The response is
   always understanding + matching + execution, narrated in natural language.
2. The session graph is never reset — only extended.
3. Every answer is an assertion in the session graph.
4. The system never drops context — bindings persist until explicitly cleared.
5. A question is always a graph — even system-generated follow-ups.
6. Compute and theoretical paths share the same graph representation.
   The difference is in the walk, not the structure.
7. Implication edges are first-class. They are not metadata —
   they are the derivation chain.
8. The session graph IS the state. There is no separate session object.
9. The reasoning trace IS the answer. The final value or conclusion
   is the last step of the trace, not a separate output.
10. The narration uses `to-english` + `to-english-relation` on graph nodes —
    the vocabulary of the response comes from the graph, not hardcoded strings.

---

## Later: Multi-Turn Reasoning Session

The full vision:
```
user: "what is kinetic energy?"
system: "I need mass and velocity. What is the mass?"
user: "5kg"
system: "What is the velocity?"
user: "10m/s"
system: "kinetic energy is 250J. This follows from KE = ½mv²
         which derives from the work-energy theorem."
user: "why is there a ½?"
system: [theoretical walk] "The ½ comes from integrating F·dx
         over the path, where F = ma and a = v dv/dx..."
user: "now what if the velocity doubles?"
system: [reuses session bindings, updates v=20m/s]
        "kinetic energy becomes 1000J — four times larger,
         since KE scales as v²."
```

Each exchange is one `session-step`. The session graph accumulates.
The fourth exchange reuses bindings from the first.
The fifth shows the v² relationship — a theoretical derivation.
All from the same graph machinery.
