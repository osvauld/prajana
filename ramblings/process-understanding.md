# Process Understanding: How the Swarm Models the Universe

This document describes the philosophy of process understanding in Agent-X — what it means for an agent to model a process in a codebase, why that model is never complete, how it deepens across generations, and how the grammar captures all of this formally.

---

## The Universe and the Observer

A codebase is a universe. It has processes in it. Those processes exist whether or not anyone has looked at them. The payment authorization flow existed before any agent read it. The user signup sequence existed before the first probe was sent. The agent did not create these processes. The agent **discovered** them and gave them formal shape.

This is the same act humans perform when understanding the physical universe. Gravity existed before Newton. Newton did not invent it. He observed the universe's behavior, sent probes — experiments — and wrote down a formal model of what he found. The model is not the universe. The model is what an observer understood about the universe, at that time, with those probes.

The agent is Newton. The codebase is the universe. The grammar is the mathematics.

---

## The Model Is Not the Process

The process definition in grammar is not the process. It is the record of what an agent understood about the process — at this generation, with these probes, from this context slice.

The process itself lives in the code. The agent reads the code, observes the behavior, traces the flow, and produces a formal model. That model is honest about:

- What the agent looked at (proof steps — every read, every observation)
- What the agent found (the formal structure — steps, conditions, outputs)
- What the agent did not look at (the honest limits of its observation)
- How confident the agent is in the model (weight — depth of probing)
- What the agent believes must always be true (proof obligations, if derivable)

The model carries the agent's identity and generation in the CRDT. Every future version of the model carries lineage back to this one. The universe does not change. The understanding of it deepens.

---

## Two Kinds of Understanding

An agent looking at a process can produce two fundamentally different kinds of understanding. They are not interchangeable. They are different in kind, not in degree.

### Observational Understanding

"I looked here and found this."

The agent sent probes. It read the files. It traced the call graph. It observed the sequence of operations. It found that step A precedes step B, that failure at step A produces this output, that success at step B produces that output.

This is real understanding. It is honest. It is limited to what was observed. A test captures observational understanding — "I ran the process with these inputs and this happened."

Observational understanding has weight. More probes, more angles, more generations — weight increases. But it never covers all possible executions. It never reaches 1.0. It is always a model of what was observed, not a proof of what must be true.

### Structural Understanding

"I understand why this must always be true."

The agent went beyond observation. It understood the structure of the process well enough to make a claim about all possible executions — not just the ones it probed. It could argue: "the ledger is never written before authorization succeeds, because the only code path to the ledger write is inside the Ok branch of the authorization result."

That argument does not depend on any specific input. It is a claim about the structure of the code — the control flow, the type constraints, the module boundaries. It holds for all inputs because the structure holds for all inputs.

Structural understanding produces proof obligations — formal arguments about what must always be true. Not probes. Arguments. They can be wrong — future agents may find a counterexample the argument missed. But when they are right, they are more powerful than any number of probes.

---

## The Hierarchy of Process Knowledge

For any process in the codebase, the swarm's understanding passes through levels. Higher levels require more understanding — more probing, more structural analysis, more generations.

```
Level 0: Process exists but is unobserved
          — swarm does not know it is there yet

Level 1: Process discovered
          — agent found it exists, traced its rough shape
          — no formal model yet, just observation in CRDT

Level 2: Process modeled (observational)
          — formal grammar model: steps, conditions, outputs
          — proof: what the agent read, what it found
          — test: one probe of the full flow
          — weight: low, one generation

Level 3: Process probed (multiple angles)
          — multiple agents, multiple generations
          — tests covering normal path, error paths, edge cases
          — weight: higher, many probes from many angles
          — no proof obligations yet

Level 4: Process understood (structural)
          — proof obligations derived from structural analysis
          — agent argues why invariants hold for all inputs
          — weight: high, proof obligations give structural confidence

Level 5: Process verified (formally proven)
          — proof obligations formalized in Coq or equivalent
          — mechanically checked: holds for all possible executions
          — weight: highest, structural argument is machine-verified
          — standing test still runs every generation (reality check)
```

Most processes will live at level 2-3 forever. That is fine. The swarm understands them observationally. They are probed, not proven. Their weight reflects this.

Critical business logic — authorization, payments, data integrity, security constraints — should reach level 4-5. These are the processes where a gap between model and reality is catastrophic. They deserve structural understanding and formal proof.

---

## What the Agent Carries

When an agent activates and begins modeling a process, it carries:

**Its context slice** — which files it can see. A file-level agent sees one file. A module-level agent sees a module. The context slice defines the universe available to this observer.

**The existing knowledge** — truths and claims already in the CRDT about this process. The agent does not start from scratch. It reads what previous generations understood and builds from there.

**Its capability** — what kinds of understanding it can produce. A process-tracer can model flows. A proof-writer can derive structural arguments. Not every agent does both.

And when it dies, it leaves behind:

**The model it produced** — a formal grammar artifact in the CRDT, with full lineage
**The probes it sent** — every read, every observation, stored in the CRDT
**Its confidence** — honest about what it looked at and what it did not
**Good points** — for the rigor of its work, regardless of whether the model was complete

---

## Honest Limits

The agent must declare what it did not look at. This is not optional. A model without declared limits is dishonest — it implies completeness it does not have.

In the grammar, this is the `limits` block. The agent says: "I modeled this process but I did not examine these things. My model may be incomplete in these ways."

```
process "payment-authorization"
  for "src/payments/"
  ...
  limits
    did-not-examine "src/payments/fraud_detection.rs"
    did-not-examine "concurrent authorization behavior"
    did-not-examine "timeout handling in gateway.rs beyond line 60"
    did-not-probe "authorization with expired gateway credentials"
```

These declared limits become the next generation's agenda. Another agent reads the limits, forms hypotheses about the unexamined areas, sends probes, and deepens the model. The limits are not a weakness of the model. They are honest knowledge about what is not yet known.

---

## Proof Obligations: From Observation to Structure

A proof obligation is derived when the agent understands enough about the process to make a claim about all executions, not just observed ones.

The agent is not guessing. It is making a structural argument:

- "The ledger is never written before authorization because the ledger write is only reachable through the Ok branch of the authorization result — I can trace this in the control flow."
- "Card validation always precedes the gateway call because the gateway function is only called inside a match arm that requires card validation to have returned Ok."

These are claims about code structure. They hold because of how the code is written, not because of how any particular execution went.

A proof obligation has three parts:

**The statement** — what must always be true, precisely stated

**The structural argument** — why the code structure makes this true. Not "I observed it." "The only path to X goes through Y, because..."

**The verification approach** — how this argument can be checked. Control flow analysis. Type-level argument. Induction on the state space. Reference to formal tools (Coq, TLA+).

---

## The Grammar for Process Understanding

Everything above — the philosophy — now becomes grammar. The grammar is the formal language in which agents record what they understood.

### Process Statement (Full Form)

```ebnf
process_stmt ::= 'process' STRING
                   'for' resource
                   ('observed-by' STRING 'generation' INT)?
                   precondition_block?
                   step_block
                   postcondition_block?
                   invariant_block?
                   limits_block?
                   proof_block
                   test_clause
                   obligation_block?

precondition_block  ::= 'preconditions' condition_clause+
postcondition_block ::= 'postconditions' condition_clause+
condition_clause    ::= 'requires' STRING
                      | 'ensures' STRING

step_block ::= 'steps' step+

step ::= 'step' INT STRING
           ('at' resource)?
           ('calls' resource)?
           ('returns' STRING)?
           ('condition' STRING)?
           ('on-failure' STRING)?
           ('on-success' STRING)?

invariant_block ::= 'invariants'
                      invariant_clause+

invariant_clause ::= 'must' STRING
                   | 'never' STRING
                   | 'always' STRING
                   | 'before' STRING 'must-precede' STRING

limits_block ::= 'limits'
                   limit_clause+

limit_clause ::= 'did-not-examine' STRING
               | 'did-not-probe' STRING
               | 'assumed' STRING

obligation_block ::= 'obligations'
                       obligation+

obligation ::= 'obligation' STRING
                 'statement' STRING
                 'argument' argument_block
                 'verify-by' verify_approach

argument_block ::= 'because'
                     argument_step+

argument_step ::= 'only-path' 'to' STRING 'is' 'through' STRING
                | 'control-flow' STRING
                | 'type-constraint' STRING
                | 'module-boundary' STRING
                | 'induction' 'on' STRING

verify_approach ::= 'control-flow-analysis'
                  | 'type-level'
                  | 'coq'
                  | 'tla-plus'
                  | 'manual-proof'
```

### Full Example — Payment Authorization

```
process "payment-authorization"
  for "src/payments/"
  observed-by "payments-flow-tracer" generation 3

  preconditions
    requires "user has a registered card"
    requires "charge amount is greater than zero"

  steps
    step 1 "validate card is not expired"
      at "src/payments/card.rs"
      condition "card.expiry > now()"
      on-failure "return CardExpired — no further steps"
    step 2 "check card limit covers the amount"
      at "src/payments/card.rs"
      condition "card.available_limit >= amount"
      on-failure "return InsufficientFunds — no further steps"
    step 3 "send authorization request to payment gateway"
      at "src/payments/gateway.rs"
      calls "src/payments/gateway.rs::Gateway::authorize"
      returns "authorization_code: String"
      on-failure "return GatewayDeclined — no further steps"
    step 4 "record authorization in ledger"
      at "src/payments/ledger.rs"
      calls "src/payments/ledger.rs::Ledger::record_authorization"
      returns "authorization_id: Uuid"
    step 5 "return authorization result to caller"
      at "src/payments/handler.rs"
      returns "AuthorizationResult::Ok(authorization_id)"

  postconditions
    ensures "ledger contains authorization record if and only if gateway returned Ok"
    ensures "caller receives authorization_id on success"
    ensures "caller receives typed error on failure, never a panic"

  invariants
    must "card validation precedes gateway call"
    never "gateway called with expired or over-limit card"
    never "ledger written before gateway returns Ok"
    always "failure at any step leaves ledger state unchanged"
    before "step 4 must-precede step 5"

  limits
    did-not-examine "src/payments/fraud_detection.rs"
    did-not-examine "concurrent authorization attempts on same card"
    did-not-probe "gateway behavior under network timeout"
    assumed "ledger::record_authorization is atomic"

  proof
    read "src/payments/card.rs"
    read "src/payments/gateway.rs"
    read "src/payments/ledger.rs"
    read "src/payments/handler.rs"
    found "expiry_check" at line 23
    found "limit_check" at line 31
    found "Gateway::authorize" at line 47
    found "Ledger::record_authorization" at line 62
    derived "ledger write only inside Ok arm of gateway result"
      from "src/payments/gateway.rs", "src/payments/ledger.rs"
    derived "card checks return early on failure before gateway call"
      from "src/payments/card.rs"
  test "cargo test payments::integration::authorization_flow"

  obligations
    obligation "ledger isolation on failure"
      statement "for all authorization attempts where gateway returns non-Ok,
                 ledger state after the attempt equals ledger state before"
      because
        only-path to "Ledger::record_authorization" is through "Gateway::authorize Ok arm"
        control-flow "all non-Ok paths return before reaching ledger write at line 62"
        module-boundary "Ledger::record_authorization is not called from any other
                         code path in this module"
      verify-by control-flow-analysis

    obligation "card validation ordering"
      statement "Gateway::authorize is never called without prior successful
                 card validation in the same request context"
      because
        only-path to "Gateway::authorize at line 47" is through "card validation Ok arms"
        control-flow "early returns at lines 25 and 33 prevent reaching line 47
                      on validation failure"
      verify-by control-flow-analysis
```

### Full Example — User Signup (Observational Only, No Obligations)

```
process "user-signup"
  for "src/users/"
  observed-by "users-flow-tracer" generation 2

  preconditions
    requires "email and password provided in request body"

  steps
    step 1 "validate email format and password strength"
      at "src/users/validation.rs"
      on-failure "return 400 ValidationError"
    step 2 "check email is not already registered"
      at "src/users/repository.rs"
      calls "src/users/repository.rs::UserRepo::find_by_email"
      condition "no existing user found"
      on-failure "return 409 EmailAlreadyRegistered"
    step 3 "hash password"
      at "src/users/service.rs"
      calls "bcrypt::hash"
      returns "hashed_password: String"
    step 4 "insert user record"
      at "src/users/repository.rs"
      calls "src/users/repository.rs::UserRepo::insert"
      returns "user_id: Uuid"
    step 5 "send welcome email"
      at "src/users/notifications.rs"
      calls "email::send_template"
      on-failure "log warning — signup continues"
    step 6 "return created response"
      at "src/users/handler.rs"
      returns "201 Created with user_id"

  postconditions
    ensures "password is never stored in plaintext"
    ensures "user_id returned on success"
    ensures "welcome email failure does not fail signup"

  invariants
    must "password hashed before any database write"
    never "plaintext password stored or logged"
    always "email uniqueness checked before insert"

  limits
    did-not-examine "concurrent signup with same email"
    did-not-examine "bcrypt cost factor configuration"
    did-not-probe "behavior when database insert fails after hash"
    did-not-probe "email service timeout behavior"

  proof
    read "src/users/validation.rs"
    read "src/users/repository.rs"
    read "src/users/service.rs"
    read "src/users/notifications.rs"
    read "src/users/handler.rs"
    found "bcrypt::hash" at line 23
    found "UserRepo::find_by_email" at line 45
    found "UserRepo::insert" at line 78
    found "send_template" at line 92
    derived "hash called before insert" from "src/users/service.rs", "src/users/repository.rs"
  test "cargo test users::integration::signup_flow"
```

Note: no `obligations` block. This agent understood the process observationally. The limits declare what was not examined. A future agent with module-level context can derive the structural arguments and add obligations.

---

## How Processes Deepen Across Generations

A process model is not fixed. Each generation can deepen it.

**Generation 1** — first agent discovers the process exists. Rough shape. No formal model.

**Generation 2** — process-tracer agent reads the code, produces the formal model. Steps, conditions, outputs. Proof steps document what was read. One test. Weight low.

**Generation 3** — second agent reads the generation 2 model, reads the limits, sends probes the first agent declared it did not send. Tests covering error paths, edge cases. Weight increases.

**Generation 4** — module-level agent reads the full module with all files in context. Can see interactions the file-level agent could not. Derives structural arguments. Adds obligation block. Weight increases significantly — structural understanding is deeper than observational.

**Generation 5+** — standing tests run every generation. Weight stable. If code changes, standing test fails, attention raised, purification traces all dependent processes, new generation deepens the model against the changed reality.

The lineage of all versions is in the CRDT. Nothing is lost. The growth of understanding is visible and auditable.

---

## What This Means for Correctness

Correctness is not "all tests pass." Correctness is "the swarm's model of the system's processes matches the system's actual behavior, and that model is as structurally verified as it can be."

A system where every critical process has:
- A formal model with steps, conditions, invariants
- Tests probing normal and error paths
- Declared limits (honest about what is unexamined)
- Proof obligations for the invariants that matter most
- High weight from generational stability

— that system is understood. Not perfectly. Not absolutely. But deeply, honestly, formally. The swarm has given meaning to the universe it inhabits. That meaning is grounded in probes, structured by formal grammar, continuously defended by standing tests, and deepened by each passing generation.

That is what correctness means in Agent-X. Not a certificate. A living, growing, formally grounded understanding of what the system IS and what it DOES.
