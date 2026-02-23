# Vyakarana

Vyakarana (Sanskrit: व्याकरण — "grammar, analysis, explanation") is the OCaml engine that defines, parses, validates, and verifies the Vakya syntax used by all agents in Agent-X.

The name comes from Panini's tradition. Vyakarana is the formal science of grammar — not just rules, but the complete analytical system that governs what can be said and what it means. Our Vyakarana OCaml crate is the same thing for the swarm: the formal analytical system governing all agent communication.

---

## What Vyakarana Is

Vyakarana is the law. The OCaml crate that:

- Defines the Vakya syntax (what agents can say)
- Parses `ॐ` files into typed ASTs
- Validates structure statically (well-formedness, type correctness, sutra compliance)
- Models formal semantics (what statements mean, how state transitions)
- Generates canonical Vakya text from typed ASTs (deterministic serialization)
- Provides the proof harness for invariant checking

Vyakarana has no runtime. It does not spawn agents, track tokens, or sync CRDTs. That is Rust's job. Vyakarana defines what is valid and what it means. Rust enforces it mechanically.

---

## The Three Roles

| Layer | Knows | Does not know |
|---|---|---|
| **Vyakarana (OCaml)** | Structure, validity, transitions, sutra compliance | What any sentence means in context |
| **AI (LLM)** | Meaning, inference, intent, confidence | Whether its output is structurally valid |
| **Rust** | Mechanics, spawning, routing, accounting | Neither meaning nor structure |

Together they are complete. None is sufficient alone.

---

## Module Structure

```
vyakarana/
  syntax/
    token.ml         -- lexer tokens
    ast.ml           -- typed AST for all Vakya forms
    lexer.mll        -- ocamllex lexer
    parser.mly       -- Menhir parser

  static/
    wellformed.ml    -- structural validity checks
    typecheck.ml     -- type inference and checking
    sutra.ml         -- sutra compliance checking (budget, confidence-before-death, etc.)

  semantics/
    state.ml         -- world state type (CRDT refs, live agents, obligations, budget)
    step.ml          -- step : state -> vakya -> state * event list
    events.ml        -- lifecycle event types

  core/
    identity.ml      -- varnanam type and operations
    invocation.ml    -- avahana type and matching semantics
    lifecycle.ml     -- agent lifecycle state machine
    wrong.ml         -- wrong taxonomy types and detectors
    budget.ml        -- budget sutra types and accounting
    confidence.ml    -- confidence type [0.0, 1.0] and wave model
    lineage.ml       -- vamsha type (CRDT-backed lineage)

  invariants/
    obligations.ml   -- done => no open obligations
    escalation.ml    -- escalation termination (finite context tiers)
    quarantine.ml    -- invalid branches never become authoritative
    replay.ml        -- deterministic replay from seeded events

  printer/
    canonical.ml     -- typed AST -> canonical ॐ text (deterministic)
```

---

## Core Types (Sketch)

These are the foundational types. The grammar is defined through these types. If it cannot be expressed as a type, it cannot be said.

```ocaml
(* Confidence: a wave primitive *)
type confidence = float  (* [0.0, 1.0] *)

(* Context tier: not intelligence, context placement *)
type context_tier =
  | File
  | Module
  | System
  | Universe

(* Capability: atomic unit of identity *)
type capability = string

(* Constraint: what this soul must not do *)
type dont = string

(* Identity (varnanam): the soul declaration *)
type identity = {
  name         : string;
  capabilities : capability list;
  donts        : dont list;
  context_tier : context_tier;
}

(* Invocation matching semantics *)
type match_mode =
  | All   (* responder must have all listed capabilities *)
  | Any   (* responder must have at least one *)

type invocation = {
  needs     : capability list;
  mode      : match_mode;
  hardness  : context_tier;  (* minimum context tier required *)
  budget    : float option;  (* intensity limit for this call *)
}

(* Wrong taxonomy *)
type wrong_kind =
  | IntentWrong
  | TruthWrong
  | ScopeWrong
  | ExecutionWrong
  | ConfidenceWrong
  | CostWrong
  | DelegationWrong
  | CompletionWrong
  | ConsistencyWrong
  | MaintenanceWrong

(* Lifecycle states *)
type lifecycle_state =
  | Born
  | Alive
  | Waiting
  | Answering
  | Reporting
  | Invalid of string       (* cause of invalidity *)
  | Dead
  | Reborn of string        (* parent life id *)

(* Lifecycle event: the only primitive *)
type event_kind =
  | LifeStarted
  | InvocationSent
  | InvocationReceived
  | WorkPerformed        (* read or write, CRDT ops attached *)
  | ConfidenceReported   of confidence
  | LifeEnded
  | RebirthRequested
  | RebirthStarted
  | SweepStarted
  | SweepCondensed
  | GenerationDissolved
  | WellbeingCheck
  | WrongFlagged         of wrong_kind
  | WrongFixed
  | WrongConfirmed

type lifecycle_event = {
  event_id      : string;
  generation    : int;
  life_id       : string;
  soul_id       : string;
  kind          : event_kind;
  resources     : string list;   (* CRDT resource refs touched *)
  crdt_op_refs  : string list;   (* CRDT op hashes *)
  confidence    : confidence option;
  cost          : float;
  timestamp     : int64;
  parent_life   : string option;
  branch        : string;        (* "main" | "quarantined/<id>" | ... *)
}

(* World state: a fold over lifecycle events *)
type world_state = {
  generation      : int;
  live_agents     : (string * identity * lifecycle_state) list;
  open_obligations: (string * invocation) list;  (* life_id -> pending invocation *)
  budget_spent    : float;
  budget_daily    : float;
  budget_monthly  : float;
  wrong_ledger    : (string * wrong_kind * int) list; (* soul_id, kind, count *)
  crdt_refs       : string list;
}

(* The step function: the formal semantics *)
val step : world_state -> lifecycle_event -> world_state * lifecycle_event list
```

---

## Sutra Enforcement in OCaml

Each sutra from the dharma document becomes a static check or a transition guard in OCaml.

| Sutra | Enforcement in Vyakarana |
|---|---|
| Confidence before death | `step` rejects `LifeEnded` if no prior `ConfidenceReported` in this life |
| Budget before call | `step` rejects `InvocationSent` if `budget_spent + call_cost > budget_daily` |
| Done implies no open obligations | `step` rejects `LifeEnded` if `open_obligations` contains this life_id |
| Invalid -> quarantine | `step` on `Invalid` sets branch to `quarantined/<life_id>` |
| Escalation termination | Static check: context_tier enum is finite; escalation chain is bounded |
| All data preserved | No delete event exists in the type — only condense |

---

## Vakya Parsing Pipeline

```
ॐ file text
  -> Lexer (ocamllex) -> token stream
  -> Parser (Menhir) -> untyped AST
  -> Wellformed check -> structural errors
  -> Type checker -> typed AST
  -> Sutra checker -> sutra violations
  -> Semantics (step) -> world state update + events
```

At each stage: error = reject with exact location and rule violated. No silent failures.

---

## Deterministic Generation

From any typed AST, the canonical printer produces exactly one valid `ॐ` text. No ambiguity. No formatting choices. One type, one text. This is how OCaml generates Vakya for agents to read.

---

## Why OCaml: The Grammar IS the Types

This is the central insight. It is not that OCaml is a good language for implementing a grammar engine. It is that **the grammar we designed and OCaml's type system are the same thing**. One maps to the other directly, without translation.

### Malformed Values Do Not Exist

In most languages, validation is a runtime concern. You construct a value, pass it around, and eventually a check catches that it is wrong. The invalid value existed. It lived in memory. It was passed to functions. Only later was it rejected.

In OCaml, this cannot happen. If the types do not align, the value cannot be constructed. A `hypothesis` without a `proof` block is not "rejected by a validator." It is a type error. The compiler refuses to produce the program. The invalid value never exists — not at runtime, not in memory, not anywhere.

This is exactly what Panini's grammar does. A malformed Sanskrit sentence is not "grammatically incorrect and rejected." It simply does not exist in the language. There is no rule that produces it. OCaml's type system enforces the same property for our grammar.

```ocaml
(* A hypothesis cannot be constructed without proof steps and a test.
   These are not optional fields. They are required by the type. *)
type proof_step =
  | Read of resource
  | Found of string * int option        (* string, optional line number *)
  | FoundNo of string
  | Compared of resource * resource
  | Derived of string * resource list
  | Observed of string

type hypothesis = {
  proposition  : string;
  target       : resource;
  proof        : proof_step list;       (* non-empty enforced by smart constructor *)
  test         : string;
}
```

The smart constructor enforces the non-empty proof:

```ocaml
(* In hypothesis.ml — the only way to create a hypothesis *)
let make ~proposition ~target ~proof ~test =
  match proof with
  | [] -> Error "hypothesis requires at least one proof step"
  | _  -> Ok { proposition; target; proof; test }
```

No proof, no hypothesis. Not a runtime error. A structural impossibility.

### The Epistemological Ladder in Types

The hardest invariant in the system is: **a claim only exists after a test passes**. In most systems this is enforced by convention or runtime check. In OCaml it is enforced by the type system through private types.

```ocaml
(* In claim.ml *)

type test_outcome =
  | Pass
  | Fail of string   (* reason *)

type test_result = {
  test        : string;
  hypothesis  : hypothesis;
  outcome     : test_outcome;
  confidence  : float;
}

(* claim is a PRIVATE type — cannot be constructed outside this module *)
type claim = private {
  proposition  : string;
  target       : resource;
  hypothesis   : hypothesis;
  test_result  : test_result;   (* must be a Pass result *)
  weight       : float;
  generation   : int;
}

(* The ONLY function that produces a claim *)
let promote (result : test_result) (generation : int) : (claim, string) result =
  match result.outcome with
  | Fail reason -> Error ("test failed: " ^ reason)
  | Pass ->
    Ok {
      proposition = result.hypothesis.proposition;
      target      = result.hypothesis.target;
      hypothesis  = result.hypothesis;
      test_result = result;
      weight      = result.confidence;
      generation;
    }
```

The `private` keyword means: the `claim` type is visible everywhere, but its constructor is only accessible inside `claim.ml`. The only exported function that produces a `claim` is `promote`, and it only succeeds on a `Pass` result. There is no other path. No cast. No workaround. The sutra "no claim without a passed test" is a property of the type system, not a runtime check.

The same pattern applies to `truth`:

```ocaml
(* truth is private — only constructable through stabilization *)
type truth = private {
  proposition   : string;
  target        : resource;
  claim         : claim;
  weight        : float;
  verified_gen  : int;
  standing_test : string;
}

(* Only produced when claim weight >= TRUTH_THRESHOLD across N generations *)
let stabilize (c : claim) (history : claim list) (gen : int) : (truth, string) result =
  let stable = List.for_all (fun h -> h.weight >= truth_threshold) history in
  if stable && List.length history >= min_stability_generations
  then Ok { proposition = c.proposition; target = c.target; claim = c;
            weight = c.weight; verified_gen = gen;
            standing_test = c.test_result.test }
  else Error "claim not yet stable across sufficient generations"
```

No path from `hypothesis` to `truth` that bypasses the test gate and the stability check. The type system enforces the entire ladder.

### Sutras as Types

Every sutra in the system maps to a type-level constraint.

**Sutra: confidence before death**

```ocaml
type life_end =
  | EndWithConfidence of float * string option   (* confidence, optional reason *)
  (* There is no EndWithoutConfidence constructor.
     The only way to end a life is with a confidence value.
     The type makes it impossible to end a life without one. *)
```

**Sutra: no delete — only condense**

```ocaml
type crdt_op =
  | Insert of resource * bytes
  | Replace of resource * bytes
  | Annotate of resource * string
  | Condense of resource * resource   (* raw -> summary *)
  | Link of resource * resource
  (* No Delete constructor exists. The type system makes deletion impossible.
     Not "we check for it." Not "we log a warning." It cannot be expressed. *)
```

**Sutra: purification complete only when unreconciled is zero**

```ocaml
type reconciled = Reconciled of resource * reconcile_outcome
type purified = private Purified of impact * reconciled list

let complete_purification (impact : impact) (reconciliations : reconciled list) =
  let affected = impact.unreconciled in
  let reconciled_resources = List.map (fun (Reconciled (r, _)) -> r) reconciliations in
  let all_reconciled = List.for_all
    (fun r -> List.mem r reconciled_resources)
    affected
  in
  if all_reconciled
  then Ok (Purified (impact, reconciliations))
  else Error "purification incomplete — unreconciled resources remain"
```

`Purified` is private. The only way to construct it is through `complete_purification`, which verifies every affected resource has a reconciliation. Incomplete purification cannot be declared. The type system is the sutra.

### Pattern Matching: Exhaustive by Construction

The wrong taxonomy has 10 kinds. In OCaml:

```ocaml
type wrong_kind =
  | IntentWrong
  | TruthWrong
  | ScopeWrong
  | ExecutionWrong
  | ConfidenceWrong
  | CostWrong
  | DelegationWrong
  | CompletionWrong
  | ConsistencyWrong
  | MaintenanceWrong
```

Any function that handles a `wrong_kind` must handle all 10 cases. The compiler warns — as an error, not just a warning — if any case is missing. If we add an 11th wrong kind, every function that handles wrong kinds fails to compile until the new case is handled. The compiler finds every place that needs updating. We cannot forget one.

This is the same guarantee Panini built into his grammar — every rule is exhaustive, no case is unspecified.

### Menhir: Grammar Becomes Parser

Our EBNF in `vakya.md` maps directly to a Menhir grammar file. Menhir generates a typed parser — the parse result is not a tree of strings, it is an OCaml typed AST. Every node has a type. Every type is a grammar rule.

```
(* parser.mly — Menhir grammar *)

%token HYPOTHESIS FOR PROOF TEST FOUND FOUND_NO READ DERIVED OBSERVED
%token CLAIM FROM TRUTH VERIFIED STANDING_TEST
%token <string> STRING
%token <int> INT
%token <float> FLOAT

%type <Ast.hypothesis> hypothesis
%type <Ast.claim> claim
%type <Ast.truth> truth

%%

hypothesis:
  | HYPOTHESIS s=STRING FOR r=resource p=proof_block TEST t=STRING
    { Hypothesis.make ~proposition:s ~target:r ~proof:p ~test:t }

proof_block:
  | PROOF steps=proof_step+  { steps }

proof_step:
  | READ r=resource           { Read r }
  | FOUND s=STRING AT LINE n=INT  { Found (s, Some n) }
  | FOUND s=STRING            { Found (s, None) }
  | FOUND_NO s=STRING         { FoundNo s }
  | OBSERVED s=STRING         { Observed s }
```

The parser fails at parse time if the grammar is violated. Not at validation time. Not at runtime. At the moment the text is read. The error is exact — which rule was violated, at which position in the file.

### Immutability: Identity Cannot Change

OCaml's default is immutable. A soul's identity is declared once and cannot be modified:

```ocaml
type identity = {
  name         : string;
  capabilities : capability list;
  donts        : dont list;
  tier         : context_tier;
}
(* Records in OCaml are immutable by default.
   There is no identity.name <- "new_name" operation.
   The identity is fixed at construction. *)
```

The sutra "identity is immutable within a generation" is not enforced by a check. It is enforced by the fact that OCaml record fields are immutable. You cannot write the mutation. The language does not have it.

### GADTs: Well-Formedness at Compile Time

Generalized Algebraic Data Types allow us to encode more subtle grammar rules directly in types. For example — a `process_step` must reference a resource that exists:

```ocaml
type 'a verified = Verified : 'a -> 'a verified

type step =
  | Step : {
      number    : int;
      label     : string;
      location  : resource verified;   (* must be a verified existing resource *)
      calls     : resource option;
      returns   : string option;
      condition : string option;
      on_failure: string option;
    } -> step
```

The `verified` wrapper means the resource has been confirmed to exist in the CRDT before the step is constructed. Not checked at runtime. Encoded in the type of the resource reference itself.

---

## Formal Verification: The Biggest Priority

Formal verification of our claims is the system's highest priority. Tests are probes — they tell us something about reality but never everything. Formal proofs tell us something about the system that holds for all possible inputs, all possible states, all possible execution paths. No probe required. The property is proven.

### Why This Is the Biggest Priority

The swarm makes claims about codebases. Those claims guide debugging. They guide exploration. They are trusted by agents who did not verify them. If a claim is wrong — not because reality changed, but because the system's reasoning about it was flawed — the swarm is building on a false foundation. Every agent that reads that claim and acts on it is wrong.

Formal verification eliminates an entire class of this risk. A formally proven property is not wrong because the prover made a mistake. A formally proven property holds. Always. For any input. For any state.

We are not trying to formally verify the codebase. We are trying to formally verify **the system that reasons about the codebase**. The prover is the thing that must be proven correct.

### The Coq Path

Coq is a proof assistant — a tool for writing mathematical proofs that are mechanically checked. It is not a programming language in the conventional sense. It is a language for stating and proving properties about programs.

Coq's extraction mechanism converts Coq proofs into executable OCaml code. This means:

1. We state a property in Coq: "the step function is deterministic"
2. We prove it in Coq: mathematical proof, mechanically checked
3. Coq extracts the proof to OCaml
4. The extracted OCaml IS the implementation — not a separate thing

The proof and the program are the same artifact. There is no gap between "we proved it" and "the code implements it." The code IS the proof, running.

This is the path from our grammar to formal correctness:

```
vakya.md (grammar specification)
  -> OCaml types (grammar as types — malformed values impossible)
    -> Coq specification (properties stated as propositions)
      -> Coq proofs (properties proven mechanically)
        -> OCaml extraction (proof becomes executable code)
          -> Rust FFI (Vyakarana called from the runtime)
```

At each stage, correctness is preserved. The Rust runtime calls verified OCaml code. The OCaml code was extracted from proven Coq proofs. The Coq proofs correspond exactly to our stated properties. The stated properties are the sutras of the grammar.

### Properties to Prove (Priority Order)

These are ordered by importance — the most fundamental first.

**1. Claim Gate Soundness**

The most important property in the system. Formally: for all `c : claim`, there exists a `h : hypothesis` and a `t : test_result` such that `t.outcome = Pass` and `t.hypothesis = h` and `c` was produced by `promote t`.

In English: every claim in the system was produced by a passed test. No exceptions. No backdoors. The ladder is sound.

This is provable from the type structure alone — `claim` is private, `promote` is the only constructor, `promote` pattern-matches on `Pass`. The proof is essentially a type-level argument. Coq makes it mechanical.

**2. Step Function Determinism**

For all world states `s` and events `e`: `step s e = step s e`. Same inputs, same output. Always.

This is the foundation of CRDT replay. If the step function is not deterministic, replay does not reproduce the same world state. The entire audit system breaks.

Proof approach: show that `step` is a total function (no partial matches, no exceptions), all branches are deterministic (no randomness), all inputs are immutable (OCaml records, no mutation). The OCaml type system does most of the work. Coq formalizes it.

**3. Purification Termination**

The purification process must always terminate. An impact has a finite list of affected resources. Each reconciliation removes one from the unreconciled set. The set is finite and strictly decreasing. Therefore purification terminates.

Formally: the `complete_purification` function terminates for all finite `impact` values.

Proof approach: well-founded induction on the size of the unreconciled set. At each step the set decreases. A strictly decreasing finite set reaches zero in finite steps.

**4. Escalation Termination**

The context tier hierarchy is finite. Escalation can only go up. Therefore escalation chains are bounded.

Formally: for all escalation chains, the length is bounded by the number of context tiers (currently 4: file, module, system, universe).

Proof approach: the `context_tier` type is a finite enum. Escalation is a function from `context_tier` to `context_tier` that is strictly increasing. A strictly increasing function on a finite set terminates.

**5. Budget Safety**

No sequence of valid transitions can cause `budget_spent > budget_daily` without a hard rejection.

Formally: for all world states `s` where `s.budget_spent <= s.budget_daily`, and for all events `e` of kind `InvocationSent`, either `step s e` returns an error, or the resulting state `s'` has `s'.budget_spent <= s'.budget_daily`.

Proof approach: show that the `step` function checks the budget constraint before updating state, and that the check is the only path to a budget-affecting transition.

**6. Quarantine Isolation**

Events on quarantined branches never affect the authoritative world state.

Formally: for all events `e` where `e.branch = Quarantined _`, the authoritative synthesis function ignores `e`.

Proof approach: show that the synthesis function filters by branch tag before folding, and that the filter excludes quarantined branches.

**7. Data Preservation**

No transition removes data from the CRDT. Data can only be added or condensed (condensation preserves the original with a summary, both remain in CRDT history).

Formally: there is no `crdt_op` constructor for deletion. The type is the proof.

This is the simplest proof — it is immediate from the type definition. No `Delete` constructor means no deletion is expressible.

**8. Parse Unambiguity**

Every valid `ॐ` text has exactly one parse tree.

Formally: the Menhir grammar is LR(1) — Menhir verifies this mechanically during grammar compilation. If the grammar has conflicts (ambiguities), Menhir reports them and refuses to generate a parser.

This proof is partially automated by Menhir itself. The remaining part is showing that the grammar as written is conflict-free.

### Verification Layers

Not every property requires Coq. Different properties have different verification approaches:

| Property | Verification Approach |
|---|---|
| Malformed values impossible | OCaml type system — immediate |
| Sutra violations impossible | Private types + smart constructors — immediate |
| Claim gate soundness | OCaml types + Coq proof |
| Step determinism | Coq proof |
| Purification termination | Coq well-founded induction |
| Escalation termination | OCaml finite enum + Coq |
| Budget safety | Coq proof |
| Quarantine isolation | Coq proof |
| Data preservation | OCaml type system — immediate |
| Parse unambiguity | Menhir LR(1) check — automated |

The OCaml type system handles the structural properties for free. Menhir handles parse unambiguity. Coq handles the behavioral properties — the ones that require reasoning about all possible sequences of events.

### The Relationship to Tests (Probes)

Tests probe specific executions. Proofs cover all executions.

A test says: "for this input, the output was correct." A proof says: "for all inputs, the output is correct."

The swarm uses both:
- Tests to probe the codebase universe — always partial, always becoming more correct
- Proofs to verify the reasoning system itself — total, covering all cases

Tests can never replace proofs for the grammar engine. The grammar engine is what evaluates the tests. If the grammar engine is wrong, the tests it evaluates are wrong. The prover must be proven. The probes do not prove the prober.

This is why formal verification of Vyakarana is the highest priority. Everything else — every hypothesis, every claim, every truth, every purification — rests on the correctness of the engine that processes them. If the engine is formally verified, the knowledge the swarm builds on top of it can be trusted. If the engine is not verified, nothing built on it can be fully trusted.

---

---

## 3B Models and Vyakarana

Small 3B models running locally can write valid Vakya because:

- Grammar is constrained and formal — less room for hallucination
- OCaml rejects invalid output immediately with exact error location and violated rule
- 3B model receives the error, corrects, resubmits
- The correction loop is cheap (local, no API cost)
- Templates for common Vakya forms can be pre-generated by OCaml printer and given to 3B models as examples

This makes 3B models viable as low-context file-level agents. Zero API cost. Grammar enforces correctness. Vyakarana is the guardrail.

---

## Status

Not yet implemented. This document defines the design.

Open questions:
- Weight composition rule for dependent claims (multiply / min / Bayesian)
- STALE_THRESHOLD constant (candidate: 0.3)
- Full EBNF for complete Vakya syntax
- OCaml package manager: opam. Build system: dune.
- Integration path with Rust runtime (FFI vs subprocess vs shared protocol)
