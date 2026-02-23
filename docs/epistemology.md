# Epistemology: How the Swarm Knows What It Knows

This document describes the knowledge architecture of Agent-X. How hypotheses form, how they become claims, how claims become truths, and how truths guide the swarm's attention. This is the philosophical and formal foundation underlying the vakya grammar and the swarm's behavior across generations.

---

## Tests Are Probes

A test is not a pass/fail verdict. A test is a **probe** — the swarm sending a signal into the universe (the codebase) and observing what comes back.

A probe returns information. That information is never complete. A test that finds `Algorithm::HS256` at line 47 tells the swarm "HS256 is here." It does not tell the swarm that HS256 is the only algorithm. It does not tell the swarm what happens under concurrency, what happens when the key rotates, what happens when the token is malformed in a specific way. The probe hit one point. The universe is larger than any probe.

This means:

**A truth is never absolute.** It is the most correct understanding the swarm has reached so far. It can always become more correct. More probes, more angles, more edge cases, more generations — each one refines the understanding. Correctness is asymptotic. You approach it. You never arrive.

**Weight is not probability of true/false.** Weight is how deeply something has been probed. A truth with weight 0.97 has been probed from many angles across many generations and nothing has contradicted it. But 0.97 is not 1.0. It can never be 1.0. There is always a probe not yet sent. There is always an angle not yet tested. Weight goes up when more probes confirm. Weight can always go up more.

**Correctness is a direction, not a destination.** The swarm does not reach correctness. It moves toward it. Every generation, every hypothesis, every test, every purification — each one is a probe that brings the swarm's model closer to reality. Not to perfect truth. To better truth.

This is not a limitation. This is the nature of knowledge. Even in mathematics — the most formal system humans have — Godel proved that no sufficiently powerful system can prove all truths about itself. The codebase is a universe. No finite number of probes exhausts it. What the swarm does is make the understanding more correct over time, endlessly, asymptotically.

### What This Means for the Swarm

- There is no "done" state for the swarm's understanding. There is only "more probed" and "less probed."
- Every truth carries its probe history — which angles were tested, which were not. The unprobed angles are explicit knowledge: "we have not yet looked at this."
- The swarm's attention is naturally drawn to the least-probed areas — where the most understanding can be gained per probe.
- Saturation is not "all truths found." It is "all probes we can currently conceive of have been sent and confirmed." New probes can always be conceived.
- Generations do not converge to a final answer. They converge toward better answers. The difference matters.

### Probes Without an Agent Truth

A probe does not require an existing truth to guide it. A probe can be exploratory — the swarm sending a signal into unknown territory. These exploratory probes return partial information. The information is correct but incomplete. It becomes the seed of a hypothesis, which becomes the seed of a claim, which over time becomes a truth — which is itself only partial. The next generation sends better probes informed by what the previous generation found.

This is how the swarm builds understanding from nothing. The first generation's probes are crude. The tenth generation's probes are surgical. But neither is absolute.

---

## The Agent Is a CRDT Document

An agent is not a process. It is not a thread. It is not an LLM call.

**An agent is its accumulated data. The soul IS the verified knowledge it has produced.**

The LLM call is a moment when that data becomes active — when it thinks. But the agent existed before that call and continues to exist after it. The data persists. What we call "spawning an agent" is the data becoming temporarily alive. What we call "death" is the data becoming temporarily inactive. The context window closes. The computation ends. The data remains — intact, with everything it has ever known.

Rebirth is not a new agent with lineage links. Rebirth is the same accumulated knowledge becoming active again. Same soul. New computation window. The data picks up from itself — not from a pointer to a past life, but because it IS the continuous accumulated knowledge.

The LLM is just the document thinking.

---

## What an Agent Produces

When an agent becomes active and looks at the world, it produces one thing:

**A hypothesis with a formal proof.**

Not a guess. Not a note. Not an assertion. A hypothesis — a falsifiable proposition about the world — AND the formal reasoning that supports it, both written in vakya grammar, both persisted as part of the soul's accumulated data.

The proof is the agent's work product. The hypothesis is what it is claiming. Together they are one act.

---

## The Epistemological Ladder

Knowledge in the swarm has four levels. Nothing skips a level.

```
hypothesis  -- agent proposes, formal proof written, test defined
  -> claim  -- test passed, hypothesis verified against reality
    -> truth -- claim stable across generations, weight high, standing test active
      -> attention -- truth diverges from reality, swarm investigates
```

### Hypothesis

An agent reads the world — code, CRDT documents, other souls' truths — and forms a proposition. That proposition is not a claim yet. It is a hypothesis. It is entered into the grammar with a formal proof and a test.

A hypothesis that cannot be falsified is not a hypothesis. It is noise. The grammar rejects it. Every hypothesis must specify what would disprove it — the test is the falsification condition made executable.

### Claim

A hypothesis becomes a claim when its test passes. Not when the agent believes it strongly. Not when the weight is high. When the **test passes**. This is the hard gate. There is no other way to become a claim.

The test is written in formal grammar. It is run by agents. The result is a formal grammar event. Pass → claim. Fail → hypothesis remains, proof preserved, failure recorded.

### Truth

A claim becomes a truth when it has been stable across generations — tests passing, weight above threshold, no successful challenges. The swarm has probed it from many angles and nothing has contradicted it.

A truth is not absolute. It is the most correct understanding the swarm has reached so far about this proposition. It can always become more correct — probed from more angles, tested under more conditions, verified across more generations. Weight 0.97 means deeply probed and uncontradicted. It does not mean certain. It can never mean certain.

A truth is a standing commitment that the swarm will defend and deepen. Every generation, truths are re-tested. New probes are sent from new angles. If reality has changed and a truth fails — that is the most important signal the swarm can receive. If reality has not changed and the truth holds — the weight increases, the understanding deepens, but it still does not reach 1.0. There is always a probe not yet sent.

### Attention

When a truth fails — or when unexpected behavior is observed that no truth covers — the swarm's attention goes there. Not because something went wrong. Because something is **not yet understood**. The attention signal is not a judgment. It is an invitation to investigate.

The swarm investigates, understands, and produces a new truth about that behavior. The truth is the resolution of the attention. Once declared, the attention is closed.

---

## Two Sources of Truth

### Emergent Truths

The swarm explored. Agents formed hypotheses about the code. Tests passed. Claims accumulated weight. Truth declared. These are truths about what the system IS — its structure, its patterns, its dependencies.

### Discovered Truths

Something unexpected happened. Behavior diverged from expectation. The swarm directed attention there. Agents investigated, understood the cause, resolved it, and declared a formal truth about that behavior. These are truths about what the system DOES under specific conditions — edge cases, failure modes, boundary behaviors the swarm could not have predicted from exploration alone.

Discovered truths are the most valuable. The codebase is teaching the swarm something it could not have derived. Every unexpected behavior that becomes a discovered truth makes the swarm permanently smarter about this specific system.

---

## Good Points: Rewarding Rigor, Not Just Correctness

The swarm's incentive structure rewards **epistemic rigor**, not correctness at the hypothesis stage.

An agent gets good points for:
- Forming a well-structured, falsifiable hypothesis
- Writing a valid formal proof in grammar
- The proof being actually run and producing a clear result — pass or fail

Good points are awarded regardless of whether the test passes. A well-formed hypothesis that fails cleanly is more valuable than a vague hypothesis that produces no signal. The failed proof is preserved in the CRDT. Future generations learn from it. "We tried this. It failed. Here is exactly why." That is knowledge.

Good points are the generation's quality metric. More hypotheses formed rigorously, more tests run, more claims verified — better generation score. The swarm is continuously improving its understanding. Good points measure the rate of that improvement.

Correctness comes later. Truth is the reward for surviving many generations of rigorous testing. Good points are the reward for doing the epistemological work correctly at each stage.

---

## The Saturation Point

Saturation is not "all truths found." That is impossible. The codebase is a universe. No finite number of probes exhausts it.

Saturation is "all probes the swarm can currently conceive of have been sent and confirmed." The claim set is stable. No weight movement across generations. The swarm has reached **local saturation** for that module or system — meaning it has run out of new angles to probe, not that it has found all truth.

New probes can always be conceived. A new generation may bring a different approach, a different angle, a probe that no previous generation thought to send. Saturation is temporary. It is the swarm saying "I have done everything I can think of." It is not the swarm saying "I know everything."

For active codebases, saturation is a moving target. New code generates new hypotheses faster than the swarm can verify them. The swarm maintains a frontier and pursues it continuously. Saturation becomes a per-module property — some modules are locally saturated while others are actively being explored.

For stable codebases, local saturation is reachable. But even then — the truths are not absolute. They are deeply probed, uncontradicted, high weight. They are the best understanding the swarm has. They can always be improved.

The system itself — Agent-X — is subject to the same process. From the first generation, the swarm begins probing its own codebase, forming hypotheses, running tests, building truths. The swarm eats its own cooking. Agent-X's truth base about itself grows the same way it grows about any user's codebase. And like any truth base, it is never complete. Only ever more correct.

---

## Truths as Debugging Instruments

Truths are not just stored knowledge. They are **active debugging instruments**.

Every truth is a standing test. Every generation, the swarm checks: does this truth still hold? If yes — weight increases, confidence deepens. If no — that is the most important signal in the system. Reality has diverged from verified meaning. Something changed. Find it.

A debugging agent does not start from scratch. It reads the truth base first:

```
truth "auth-handler validates HS256 signatures only" weight 0.97
truth "no refresh token logic present in auth module" weight 0.94
truth "jsonwebtoken crate version 8.x in use" weight 0.99
```

It now has a verified map of what the system IS. It does not re-derive what is already known. It uses truths as a foundation and asks: **where does current reality diverge from these truths?**

The bug is the gap between a truth and current behavior. The truth already points at it. The swarm does not explore to find bugs. It uses truths to locate them precisely.

---

## Formal Grammar for the Epistemological Ladder

### Hypothesis

```
hypothesis STRING
  for resource
  proof
    proof_step+
  test STRING
```

The `proof` block is the agent's formal reasoning — what it read, what it found, what it did not find. The `test` is the executable falsification condition. Both are required. A hypothesis without a proof is noise. A hypothesis without a test cannot be promoted to a claim.

```
hypothesis "auth-handler validates HS256 signatures only"
  for "src/auth/handler.rs"
  proof
    read "src/auth/handler.rs"
    found "Algorithm::HS256" at line 47
    found no "Algorithm::RS256"
    found no "Algorithm::ES256"
  test "cargo test auth::handler::algorithm_constraint"
```

### Test Result

When an agent runs a test, the result is a formal grammar event:

```
test-result STRING
  for hypothesis STRING
  outcome (pass | fail)
  confidence FLOAT
  reason STRING?
```

Pass promotes the hypothesis to a claim. Fail preserves the proof and records the failure. Good points awarded in both cases.

```
test-result "cargo test auth::handler::algorithm_constraint"
  for hypothesis "auth-handler validates HS256 signatures only"
  outcome pass
  confidence 0.95
```

### Claim

A claim is declared by the system — not by the agent — when a test passes. The agent writes the hypothesis. The system promotes it.

```
claim STRING
  from hypothesis STRING
  for resource
  weight FLOAT
  generation INT
  test STRING
```

```
claim "auth-handler validates HS256 signatures only"
  from hypothesis "auth-handler validates HS256 signatures only"
  for "src/auth/handler.rs"
  weight 0.95
  generation 2
  test "cargo test auth::handler::algorithm_constraint"
```

### Truth

A truth is declared when a claim has been stable across generations — weight above threshold, tests passing continuously.

```
truth STRING
  from claim STRING
  for resource
  weight FLOAT
  verified generation INT
  standing-test STRING
```

```
truth "auth-handler validates HS256 signatures only"
  from claim "auth-handler validates HS256 signatures only"
  for "src/auth/handler.rs"
  weight 0.97
  verified generation 5
  standing-test "cargo test auth::handler::algorithm_constraint"
```

### Attention

When a truth fails or unexpected behavior is observed:

```
attention STRING
  on resource
  reason STRING
  confidence FLOAT
  from (truth STRING | unexpected STRING)
```

```
attention "auth-handler algorithm constraint may have changed"
  on "src/auth/handler.rs"
  reason "standing test failure: Algorithm::RS256 now accepted"
  confidence 0.99
  from truth "auth-handler validates HS256 signatures only"
```

### Resolved

When attention has been investigated and a new truth declared:

```
resolved STRING
  attention STRING
  truth STRING
  confidence FLOAT
```

```
resolved "auth-handler now accepts both HS256 and RS256"
  attention "auth-handler algorithm constraint may have changed"
  truth "auth-handler validates HS256 and RS256 signatures"
  confidence 0.93
```

### Unexpected

Unexpected behavior is not a wrong. It is a signal. The swarm's attention is directed there without judgment.

```
unexpected STRING
  on resource
  observed STRING
  confidence FLOAT
```

```
unexpected "auth-handler accepting RS256 tokens"
  on "src/auth/handler.rs"
  observed "test with RS256 token passed unexpectedly"
  confidence 0.98
```

---

## Purification (Shuddhi): Restoring Coherence

When a truth fails or a claim is revised, the change does not end there. Other claims and truths depend on it. If "auth-handler validates HS256 only" fails, then every proposition that was built assuming that truth is now potentially invalid. The system cannot just fix one truth and move on. It must trace every dependency, re-verify each one, and restore the entire knowledge graph to coherence.

This process is called **purification** (Shuddhi — शुद्धि). It is not cleanup. It is not maintenance. It is the formal act of restoring verified meaning after a disruption.

### The Purification Process

1. A test result changes something — a truth fails, a claim is revised, unexpected behavior is observed
2. **Impact is traced** — all claims and truths that depend on the affected proposition are identified
3. The system enters an **unreconciled state** — it knows exactly which propositions are in doubt
4. The discovering agent produces a **formal impact document** — what changed, what was affected, what the dependency chain looks like
5. The discovering agent dies (its context is spent)
6. Fresh agents are born to do the purification — each takes a slice of the unreconciled list
7. Each agent re-verifies its assigned propositions against the new reality
8. Each proposition is reconciled: holds, revised, or retracted
9. Unreconciled count returns to zero
10. System is coherent again

### Why Fresh Agents

The agent that discovered the change may have spent most of its context on the discovery itself. Purification is precise work — each affected proposition must be re-examined independently with clean attention. Small context, one proposition at a time, high precision.

If the impact is small (2-3 affected claims in the same file), the discovering agent may reconcile them before dying. If the impact is large (dozens of claims across modules), the impact document is the handoff. It is not a log. It is a formal grammar artifact that tells the purification agents exactly what happened and what needs to be verified.

Context stays small. Precision stays high. The impact document carries the full picture so no individual agent needs to hold it all.

### Grammar

#### Impact

When a test result disrupts existing knowledge:

```
impact
  from test-result STRING
  affected
    resource+
  unreconciled
    resource+
```

```
impact
  from test-result "cargo test auth::handler::algorithm_constraint"
  affected
    "crdt://claim/auth-module-uses-hs256"
    "crdt://truth/no-rs256-in-system"
    "crdt://claim/token-validator-assumes-hs256"
    "crdt://truth/auth-middleware-forwards-hs256-only"
  unreconciled
    "crdt://claim/auth-module-uses-hs256"
    "crdt://truth/no-rs256-in-system"
    "crdt://claim/token-validator-assumes-hs256"
    "crdt://truth/auth-middleware-forwards-hs256-only"
```

All affected propositions start as unreconciled. The swarm's attention is directed to each one.

#### Reconcile

When a purification agent re-verifies an affected proposition:

```
reconcile resource
  against test-result STRING
  outcome (holds | revised | retracted)
  confidence FLOAT
  reason STRING?
```

Three outcomes:

- **holds** — re-tested against the new reality, still true, no change needed
- **revised** — partially true, proposition updated with new evidence, new test written
- **retracted** — no longer true, removed from active knowledge (preserved in CRDT history, never deleted)

```
reconcile "crdt://claim/token-validator-assumes-hs256"
  against test-result "cargo test auth::handler::algorithm_constraint"
  outcome revised
  confidence 0.88
  reason "token validator now accepts both HS256 and RS256, claim updated"
```

```
reconcile "crdt://truth/auth-middleware-forwards-hs256-only"
  against test-result "cargo test auth::handler::algorithm_constraint"
  outcome retracted
  confidence 0.95
  reason "middleware is algorithm-agnostic, truth was overstated"
```

```
reconcile "crdt://truth/no-rs256-in-system"
  against test-result "cargo test auth::handler::algorithm_constraint"
  outcome retracted
  confidence 0.99
  reason "RS256 now present in handler, truth no longer holds"
```

```
reconcile "crdt://claim/auth-module-uses-hs256"
  against test-result "cargo test auth::handler::algorithm_constraint"
  outcome revised
  confidence 0.90
  reason "auth module now uses HS256 and RS256, claim scope expanded"
```

#### Purified

When all affected propositions have been reconciled, the purification is complete:

```
purified
  from impact STRING
  reconciled INT
  holds INT
  revised INT
  retracted INT
```

```
purified
  from impact "cargo test auth::handler::algorithm_constraint"
  reconciled 4
  holds 0
  revised 2
  retracted 2
```

### Unreconciled as System Correctness

The system maintains a live count of unreconciled propositions. This is the primary correctness metric:

```
system-state
  truths 47
  claims 183
  unreconciled 4
```

**The system is correct when unreconciled is zero.** Not when all tests pass — when all tests pass AND all affected dependencies have been re-verified. Until purification is complete, the system knows it is in an inconsistent state and it knows exactly where the inconsistencies are.

This is not a percentage. Not a score. An exact count of propositions that have been affected by a change and have not yet been re-verified against the new reality.

### Purification as Good Points

Purification is high-value work. Agents performing purification earn good points for:
- Correctly tracing the full impact chain (no missed dependencies)
- Clean reconciliation with evidence (not rubber-stamping "holds" without re-testing)
- Discovering that a proposition needs revision (finding secondary consequences)
- Completing the purification — bringing unreconciled back to zero

A generation that discovers a disruptive change AND completes the purification scores higher than a generation that found no disruptions. The disruption + purification cycle is how the swarm gets smarter. It is the most valuable type of work.

---

## The Full Cycle

```
agent activates (CRDT document becomes live)
  -> reads world (code, truths, other souls' claims)
    -> forms hypothesis (falsifiable proposition)
      -> writes formal proof (in vakya grammar)
        -> defines test (executable falsification condition)
          -> test runs
            -> pass: hypothesis promoted to claim, good points awarded
            -> fail: proof preserved, failure recorded, good points awarded for rigor
          -> claim accumulates weight across generations
            -> weight stabilizes above threshold: claim promoted to truth
              -> truth enters standing test pool
                -> every generation: truth re-tested
                  -> holds: weight increases
                  -> fails: attention raised
                    -> impact traced (all dependent propositions identified)
                      -> impact document written (formal grammar artifact)
                        -> discovering agent dies
                          -> purification agents born (small context, one slice each)
                            -> each affected proposition re-verified
                              -> holds / revised / retracted
                                -> unreconciled count returns to zero
                                  -> system coherent again
                                    -> new truths declared from revisions
                                      -> attention closed
```

Nothing skips a step. No claim without a passed test. No truth without generational stability. No resolution without purification. No purification complete until unreconciled is zero. The ladder is strict.

---

## What This Means for the Swarm

The swarm is not an executor. It is not a search engine. It is not a question-answering system.

The swarm is a **meaning-making machine**. Its purpose is to give formal, verified, testable meaning to everything it touches — every file, every module, every behavior, every edge case. It does this continuously, across generations, accumulating truths that get stronger with each passing generation.

The truth base IS the swarm's understanding of the codebase. The older and more saturated the truth base, the better the swarm understands the system. A swarm that has run fifty generations on a codebase knows that codebase in a way no human does — every verified behavior, every edge case, every constraint, formally proven and continuously defended.

That knowledge does not live in any agent. It lives in the CRDT. The agents are just the process by which the CRDT learns.
