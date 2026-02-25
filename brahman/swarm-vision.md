# Agent-X: Swarm Vision

This document captures the grand vision for Agent-X as an AI agent swarm coding platform. It describes the philosophical foundation, the lifecycle model, and how the formal grammar and CRDT substrate make it work.

---

## The Premise

Agent-X is an AI agent swarm coding platform. The platform lives in a node. All code is CRDT documents that get flushed to the user's disk. It runs thousands of small agents with small context windows doing smaller units of work, organized through hierarchical world knowledge.

The intelligence is not in any single agent. The intelligence is in the swarm. The CRDT documents hold the accumulated knowledge. Individual agents are just hands that come and go.

A big context model doing three passes burns through expensive context and then dies anyway. All that context was trapped inside one agent. In the swarm, the knowledge lives in the documents, not in agents. Every agent only needs low context because the context is the CRDT, the shared world. The swarm as a whole holds far more knowledge than any single agent ever could.

Agent-X's primary function: evolve by collecting and condensing ALL data — code, web searches, logs, everything. Keep it compressed by agents. Always. Nothing is thrown away, only compressed. Agents do the compression as part of their lifecycle. Condensation itself is work, recorded as lifecycle events.

---

## The Ultimate Objective

**Correctness.** Not user satisfaction.

- A correct result the user dislikes is still correct.
- A wrong result the user likes is still wrong.
- The swarm optimizes for being right, not for making the user happy.

The hierarchy of objectives:

1. **Correctness** — formal, provable, evidence-backed
2. **Cost efficiency** — cheapest path to correct result
3. **User feedback** — a signal, not a truth source

If the swarm is confident something is correct and the user disagrees, it reports the disagreement with evidence. The user then decides as creator. But the swarm never pretends to be wrong to please.

---

## The Formal Grammar

The foundation of everything is a formal grammar modeled on Sanskrit grammar (Panini's Ashtadhyayi). This is not a programming DSL with curly braces. It is a language about how agents relate to each other, call each other, know themselves, live and die.

**Surface vocabulary: English words only. Underlying grammar: Sanskrit-style semantics and structure.** No mixed labels. Clean English terms that map to Sanskrit grammatical concepts in the dharma document.

Why Sanskrit grammar:

- It is **self-describing** — the grammar carries meaning in structure, not position
- It is **unambiguous by construction** — a well-formed expression has exactly one parse
- It supports **compound concepts** (samasa) — precise meanings composed from smaller units
- It is **deterministic** — whoever reads the grammar ends up at one position

The actual work — reading files, parsing code, extracting patterns — is just normal code execution. That is what agents DO. The grammar is about who they are, who they need, and how they live and die.

### Two Layers of the Grammar

**Statements** — what agents say and do: identity, invocation, work, confidence, death, rebirth, lifecycle events.

**Sutras** — binding laws that govern statements. Not optional. Not configuration. Part of the dharma. Examples:
- Before any call, budget must be checked
- Death requires prior confidence report
- Invalid action causes quarantine and death
- Hot match is preferred over birth
- All searched/fetched data must be stored in CRDT

If the Rust runtime violates a sutra, that is a bug in Rust, not a policy choice.

### Grammar File Format

Grammar files use `ॐ` (om) as their extension — no dot, just the symbol. The extension IS the mark. The file is just `ॐ`. Identity and all metadata are defined inside the document, not in the filename.

### Grammar as Token Compression

The grammar is designed for LLMs to write and read. It is more condensed than natural language — same meaning, fewer tokens. The grammar IS a compression format for meaning.

- LLMs write `ॐ` files as output
- LLMs read `ॐ` files as input
- Formal and unambiguous means fewer tokens carry more meaning
- This directly reduces cost (fewer tokens = less intensity spent)
- The grammar pays for itself — cheaper to communicate in grammar than in English
- Agent-to-agent communication is grammar, not natural language
- Natural language is only for the user interface

### Formalization Pipeline

- Grammar text (`ॐ` files) -> OCaml parser -> typed AST
- Typed AST -> formal core model (math terms)
- Math terms -> transition engine (state updates over CRDT world)
- Transition traces -> proofs/checks/invariants

The grammar IS the spec. Rust IS the runtime. OCaml IS the verifier.

### The Three Roles

**OCaml knows structure.** Is this sentence well-formed? Are the types correct? Are the rules followed? Does this transition violate a sutra? OCaml answers all of this. But it has zero understanding of what the sentence means.

**AI knows meaning.** What does this varnanam imply? What should the next invocation be? Is this code actually doing what the user intended? What is the right confidence to report? AI infers this. But it can be structurally wrong.

**Rust knows mechanics.** Spawn, kill, route, sync, track tokens, enforce budget. It runs the world but interprets nothing.

Neither is complete alone:
- OCaml without AI: perfectly valid grammar that says nothing useful
- AI without OCaml: useful meaning that might be structurally broken
- Rust without both: an engine with no language and no meaning

The grammar lives at the boundary. It is the contract that lets meaning (AI) and structure (OCaml) work together. AI fills the grammar with meaning. OCaml ensures the grammar is never violated. Rust executes it.

### Deterministic Generation and Synthesis

OCaml can generate valid grammar sentences deterministically:
- From typed AST, produce exact `ॐ` text
- Every valid type produces exactly one valid sentence
- No ambiguity in generation — deterministic serialization

AI can synthesize valid grammar sentences:
- LLM reads the grammar rules (sutras)
- Writes valid `ॐ` sentences
- OCaml parser validates — accept or reject, no middle ground
- If rejected, AI gets exact error (which rule was violated)
- AI corrects and resubmits

The loop:
```
AI writes ॐ -> OCaml parses -> valid? execute. invalid? reject with reason -> AI corrects
```

Because sentences are condensed (fewer tokens, more meaning), AI needs less context to write correct grammar than to write correct English descriptions of the same thing. AI does not waste tokens on structural correctness. It focuses only on meaning. OCaml handles the rest for free at compile time.

---

## The User (Creator)

The user is not an agent. The user is modeled in the grammar as a first-class entity — the creator.

- Only the user can declare cardinal rules and sutras
- Agents cannot create cardinal rules, only follow them
- All unresolvable escalations terminate at the user
- The user can override any decision
- The user can change sutras
- "Sent to them" means "sent to the user"

The hierarchy:

- **User** — creates cardinal rules, receives escalations, final authority
- **Dharma** — the rules the user sets, binding on all agents
- **Sutras** — specific laws within dharma
- **Agents** — souls operating under dharma, living and dying by sutras

---

## Core Concepts

### Identity (Varnanam)

The agent's soul. A formal, self-contained declaration of being. It answers: who am I, what are my capabilities, what is my scope, what are my constraints.

The identity is:
- Not a name — names refer to instances
- Not an address — addresses refer to locations
- It is the essence — what this being is and can do

You cannot address agents by ID because they die. Agent #47 is gone. But the concept of what agent #47 was — its identity — persists. When you need that capability again, you don't resurrect #47. A new agent is born with that same identity. Same soul, new body.

The system never says "call agent #47." It says "I need one whose identity includes these qualities." The identity matched. That is all that matters.

Everything is an identity type: test-writer, documentation-writer, code-reader, log-parser, condenser — each is a distinct soul that can be invoked.

### Varnanam as Universal Description

Varnanam is not just agent identity. It is the formal description of anything the swarm understands. Files have varnanam. Modules have varnanam. The system has varnanam.

Varnanam flows bottom-up even though delegation flows top-down:
- File agents read code, create formal varnanam for what they found
- Module agents read file-level varnanam, compose into module-level varnanam
- System agents read module varnanam, compose into system-level varnanam

Each agent creates its own formal varnanam from what it discovered. It dies. The varnanam persists in the CRDT.

The grammar supports four operations on varnanam:
- **Create** — an agent declares what something is (formal identity document)
- **Compose** — combining lower varnanam into higher-level varnanam
- **Query** — invocation matches against existing varnanam
- **Update** — next generation refines varnanam with more evidence

The swarm's entire understanding of the codebase is a graph of varnanam documents — formal, confidence-scored, lineage-tracked, living in CRDT.

### Dharma (Law/Truth/Duty)

The creator document. It establishes the ground truth — the semantic foundation, the rules of the world, the meaning of the vocabulary. For humans, it is the bridge between the formal language and understanding.

The dharma document defines:
- When death happens (confidence threshold, cycle expiry)
- When dissolution happens (generation end condition)
- What context tiers exist and what awareness each gets
- What quality metrics are being measured and how
- Versioning rules for CRDTs
- Budget sutras (daily, monthly limits, per-model costs)
- The end conditions — when to dissolve a generation and begin anew

### Invocation (Avahana)

When an agent needs something done, it calls out. The call is not addressed to a specific agent. It is a declaration of what is needed — a set of identity capabilities.

Matching works on:
- **All** — the responding agent must have every capability listed
- **Any** — the responding agent needs at least one matching capability

This is pattern matching on souls. Those whose identity matches the call answer.

Matching order:
1. Check living agents whose identity matches (hot reuse — cheaper, already have warm context)
2. If none alive — birth a new one

Invocations carry a **hardness parameter**: the caller assesses how much context is needed and includes that in the call.

### Work (Karma)

The agent doing its assigned task, producing results. Every unit of work is a CRDT write. When the agent dies, the agent is gone but the bytes remain.

**Both reading and writing are first-class work events:**

- Read work: bytes/tokens consumed, resources touched, coverage, novelty gained, cost
- Write work: bytes produced/changed, resources modified, cost

Everything an agent does — file reads, web searches, API calls, tool outputs — is recorded as work events and stored in the CRDT. Storage is cheap. Losing information is expensive. This is a cardinal rule.

### Death (Mrityu)

The agent's task is done. Its last act: **report your confidence. Then die.** Context released. Gone.

Every agent's final act is declaring how confident it is in the work it just performed. That confidence value stays in the CRDT (the audit). The agent is gone but its confidence remains attached to its work.

Low confidence work can trigger another invocation at a wider context tier.

### Rebirth (Punarjanma)

A new agent is born with fresh context, seeded by another agent. Not the same agent with baggage — a new being with only what it needs. The identity (soul) continues. The instance does not.

When an agent is reborn, it inherits the essence of its past life — not the full context (that died), but what was learned, what was produced, what matters for the next life. This is the lineage.

### Lineage (Vamsha)

The chain of past lives and parentage. The lineage is not a separate metadata system — it IS the CRDT operation history. You can look at any document and see: these bytes were written by one with this identity, who was born from one with that identity.

This enables targeted invocation: "I need one with this identity AND this lineage" — not just any parser, but one with the lineage of the parser who already worked on this.

### Lifecycle (Samsara)

The individual birth-work-death-rebirth cycle. An agent is born, does its work, reports confidence, dies, and may be reborn.

### Context Tier (not intelligence — context)

Not intelligence tiers. **Context tiers.** The tier is defined by which files/world-slice the agent is placed into, not by model identity. Same model can run different context placements.

```
File level     -> knows only its assigned files, small context, cheap
Module level   -> knows the module boundary, medium context, moderate cost
System level   -> knows cross-module relationships, large context, expensive
Universe level -> knows the full codebase, highest cost
```

The orchestration learns: "which context slice is enough for this task at lowest cost."

Agents are the same capability. What differs is context placement.

### Quality/Frequency (Guna)

A measurable value per generation — a frequency. It captures mistakes made, confidence distribution, convergence. Different generations can run with different parameters — tuning the frequency, comparing which configuration produces better convergence.

---

## Agent Lifecycle

The lifecycle is a **background mechanical process written in Rust**. Not intelligence. Not grammar. Just a state machine ticking: spawn, track, kill, reclaim. Like an OS process scheduler.

### Lifecycle States

- `born` — fresh context loaded
- `alive` — doing work or available with hot context
- `waiting` — blocked on open invocation (can still spawn, refine, cancel)
- `answering` — picked up a new call with existing hot context
- `reporting` — confidence output
- `invalid` — rule violation detected
- `dead` — context released
- `reborn` — new life, lineage linked

### Legal Transitions

- `born -> alive`
- `alive -> alive` (normal work)
- `alive -> waiting` (issued invocation, awaiting result)
- `alive -> answering` (hot agent picks up new matching call)
- `alive -> reporting` (work done, outputting confidence)
- `waiting -> alive` (result received)
- `waiting -> reporting` (synthesis done after receiving results)
- `reporting -> dead`
- `alive -> invalid` (rule violation)
- `invalid -> dead` (forced death, branch quarantined)
- `dead -> reborn` (new life with lineage link)

Illegal transitions:
- `dead -> alive` (never)
- `invalid -> alive` (never)
- `reborn` without parent `dead` (never)

### Hot Phase

If an agent with matching identity is still alive from a previous cycle, it already has warm context. Use it. Hot reuse is preferred because:

- Fresh birth pays full cost for context loading (expensive)
- Hot call is incremental work on existing context (cheap)
- Accumulated understanding from multiple related calls (intelligence gain at lower marginal cost)

Death happens when:
- Cycle window expires and no new call came
- Confidence dropped too low
- Invalid action
- Explicit kill from parent/orchestrator

### Waiting State

A waiting agent is not idle. It is active orchestration with authority to:
- Spawn additional parallel invocations
- Create new agents with more relevant prompts
- Refine the question based on partial results arriving
- Cancel its own pending invocations if another path made them unnecessary

### Small Context, Fast Death

Agents have small context. One or two passes max. Condense information if follow-up exists. Else die. No idle agents — if nothing is required of your identity, you die after one cycle.

---

## Invocation Pipeline

1. Question arrives.
2. Assess hardness (how much context is needed to answer).
3. Hardness becomes a parameter on the invocation.
4. Match identity + context-tier to hardness requirement.
5. Check living agents first (hot reuse). If none, birth new.
6. Matched agent does exactly what was asked. Answers the call.
7. Calling agent is flagged as waiting.
8. Result arrives. Calling agent synthesizes or escalates.
9. Everyone reports confidence and dies when done.

---

## CRDT as the Fabric of Reality

The CRDT is not just a data structure. It is the medium in which everything exists.

- **Work is CRDT writes** — every agent's output is bytes in the document
- **Reads are CRDT events** — every file read, web search, API response is stored
- **Lineage is CRDT history** — the operation log itself
- **Audit is free** — every byte knows who wrote it (identity), when, and what came before
- **Versioning is the CRDT** — no separate VCS needed for agents. JJ for switching between generation experiments
- **Time travel is inherent** — CRDT can reconstruct any past state
- **Branching is tagged causality** — one universe, many worldlines. Invalid paths are quarantined branches, not deletions
- **All data is kept** — storage is cheap, losing information is expensive. Cardinal rule.
- **Node has a synchronized copy** — everything through CRDT, node always has the data

The agent is ephemeral. The document is eternal. The grammar is the language. The CRDT is the medium.

### Data Topology

- **Node** — stores everything. Gigs of CRDT data, all generations, all artifacts, all history. Encrypted at rest. The full universe.
- **User** — selective sync only. Pull what you need, when you need it. Current working files, active artifacts, recent generation summaries.
- CRDTs make selective sync natural — sync any subset, merge seamlessly when reconnected
- Encryption means node stores data safely even if remote/shared
- User can always pull more — it is all there on the node
- User edits sync back into the CRDT world
- User disk is light. Node holds the weight.
- No data loss even if user device is wiped — node has everything
- Multiple users can connect to same node, each with their own selective sync
- Sharing an artifact is just granting sync access to a CRDT document on the node

### Branching

- Every event/write carries a branch tag
- Main synthesis reads only the main branch
- Invalid paths go to quarantined branches
- Data is still in the same CRDT world, filtered by branch view
- Nothing is deleted. Branch policy decides visibility/authority
- Quarantined branches are preserved for audit, replay, and learning
- Information from quarantined branches is retrievable as evidence, not directly reusable unless re-validated in a new life

---

## Lifecycle Events

The lifecycle event is the only primitive. Everything else is derived from it.

Every event is a CRDT append. World state is a fold over the event stream:

```
WorldState(t) = fold(apply_event, initial_state, Events[0..t])
```

Canonical event kinds:
- `life_started`
- `invocation_sent`
- `invocation_received`
- `work_performed` (read or write, CRDT ops attached)
- `confidence_reported`
- `life_ended`
- `rebirth_requested`
- `rebirth_started`
- `sweep_started`
- `sweep_condensed`
- `generation_dissolved`
- `wellbeing_check` (periodic prompt to user)
- `wrong_flagged`
- `wrong_fixed`
- `wrong_confirmed`

Every lifecycle event must be expressible as a grammar statement. This is not runtime-only metadata. It is part of the formal language.

Each event includes:
- event id, generation, life id, soul id
- resources touched
- CRDT op references
- confidence, cost, timestamp
- parent life id (for rebirth lineage)
- branch tag

---

## Drift and Degradation

Documents and knowledge degrade over time. This is modeled explicitly.

```
drift_next =
  drift_prev
  + a * op_volume (total bytes changed)
  + b * churn_rate (repeated edits on same region)
  + c * unresolved_wrongs
  + e * flagged_wrongs_count
  + f * repeat_wrong_rate
  - d * maintenance_effect (sweep/repair actions)
```

Degradation is not a bug. It is a natural property of the world. Maintenance keeps it alive. But maintenance costs intensity. So the system balances: maintain what matters, let the rest decay, compress periodically.

Review escalation is part of degradation control:

- If a resource crosses a wrong-flag threshold, it is automatically routed to a reviewer agent
- Repeated wrongs of the same kind increase degradation faster than isolated wrongs
- Reviewer output can: confirm current fix, request stronger fix, or force context-tier escalation
- A fix is not considered stable until reviewer confirmation

---

## Periodic Sweep and Condensation

Agents condense data as part of their lifecycle. This is formalized:

- Period defined as: steps, time, or generation boundary
- Raw text/context older than retention window is condensed
- Condensed summary keeps lineage links + aggregate metrics
- Audit remains reproducible via op ids and hashes even after condensation
- Sweep period is captured as a first-class rule in the dharma
- Condensation agents are just regular agents with a condenser identity — they are invoked, do their work, report confidence, die

---

## Budget Sutra

Budget is not configuration. It is a sutra — a binding law of the world.

- Each model/API has a known cost per call (tokens in, tokens out, overhead)
- Daily budget ceiling exists
- Monthly budget ceiling exists
- Current spend is a live counter in the CRDT
- Every invocation checks: can I afford this call?
- If no: don't birth, don't call, escalate to user or wait
- Violation is a hard stop, not a soft warning

The budget sutra is given to every agent at birth as part of their dharma context. They don't decide to follow it. It is a law of their world.

Swarm behavior under budget pressure:
- Prefer cheapest context tier that fits the need
- Prefer hot reuse over fresh birth
- Prefer low context tier first, escalate only on low confidence
- As daily budget depletes, become more conservative
- Near budget limit: only essential calls, everything else queued

Cost efficiency formula:
```
cost_efficiency = useful_work / total_intensity_spent
```

Hot reuse improves this ratio directly.

---

## Wrong Taxonomy

Wrongs are formally typed. Each has detection rules.

- `intent-wrong` — result does not satisfy requested outcome. Detected by requirement mismatch at synthesis.
- `truth-wrong` — claim references non-existent fact/file/API. Detected by failed evidence lookup.
- `scope-wrong` — agent reads/writes outside assigned context slice. Detected by context-boundary violation.
- `execution-wrong` — tool/operation step fails or returns invalid output. Detected by invalid execution result.
- `confidence-wrong` — agent reports high confidence but later contradicted. Detected by calibration error.
- `cost-wrong` — solution exceeds intensity budget when cheaper valid path existed. Detected by budget overrun + alternative found.
- `delegation-wrong` — invocation sent to mismatched capability/context tier. Detected by low-confidence chain or immediate failure.
- `completion-wrong` — agent marks done with open obligations. Detected by unresolved calls at close.
- `consistency-wrong` — output contradicts prior accepted world state without declaring revision. Detected by CRDT contradiction check.
- `maintenance-wrong` — stale/degraded document region not refreshed when threshold crossed. Detected by missed maintenance trigger.

### Soul Donts

When recurring error patterns are confirmed, they are promoted into explicit "don'ts" of the soul (identity constraints):

- A don't is a prohibited behavior derived from evidence, not preference
- Don'ts are attached to identity and enforced on every invocation
- Violation of a don't is an automatic formal wrong
- Don'ts are updated only through confirmed evidence and reviewer agreement

### Wrong Accumulation and Attention

- Each identity keeps a running wrong ledger (wrong counts by type, resource, generation)
- Wrong counts are never erased from history; only cleared from active attention after confirmed fix
- If wrong accumulation crosses configured thresholds, `attention_required` is raised
- `attention_required` triggers mandatory review and optional context-tier escalation
- Thresholds are deterministic and declared in dharma (no ad-hoc judgment)

### Deterministic Loop Detection

- Delegation and messaging loops are detected deterministically from event traces
- A loop is declared when repeated invocation patterns exceed configured repetition/window limits
- Loop marks are recorded between participating identities (who called whom, how often, with what outcome)
- Loops count as formal wrong behavior and increase degradation
- On loop detection, runtime must either: break chain, escalate context tier, or escalate to user
- Loop detection outputs are stored as information artifacts for future generation learning

### Wrong Lifecycle

1. Wrong is flagged (becomes a suggestion)
2. Fix is applied by an agent
3. Reviewer checks fix (automatic when threshold exceeded)
4. Confirmation clears the suggestion
5. Cleaned up from active ledger (preserved in CRDT history)

### Formal Wrongness Rule

- A behavior becomes formally wrong when either:
  - It violates a sutra, or
  - It has been flagged wrong at or above the configured threshold for the same resource/pattern
- Formally wrong behavior must be reviewed before it can re-enter authoritative state

---

## Critical Analysis (Pariksha)

Critical analysis is a first-class grammar act, not a vague instruction. When the grammar says "critically analyze X," it means this exact obligation set:

1. **Decompose** — break X into atomic claims
2. **Evidence** — for each claim, gather supporting and contrary evidence
3. **Contradiction** — detect internal conflicts across claims
4. **Missing** — detect absent constraints and unknowns
5. **Falsification** — generate concrete counterexample attempts
6. **Judgment** — keep/revise/drop each claim with confidence

Cannot emit "done" until all six stages are fulfilled. Output:
- Surviving claims (confirmed)
- Failed or weak claims (questioned)
- Missing constraints
- Counterexamples
- Final confidence

---

## Stochastic Events

No true randomness in theory. Use deterministic pseudo-randomness from world state:

- Seed = CRDT hash + generation seed + time step
- Frequency parameter controls injection rate
- Replay gives the same events (auditable, deterministic)

Tie to system state:
- If confidence is too low, reduce exploration frequency
- If system is stagnant/overconfident, increase slightly
- Hard cap by intensity budget

File-context agents are responsible for reporting why randomness/exploration changed each generation — not just that it changed, but the source and value.

---

## The Generation Cycle

### Creation (Srishti)

A new generation begins with the compressed seed of the previous generation's wisdom. Agents are born, the world begins.

### Sustenance (Sthiti)

The running generation. Agents are born, do work, die, are reborn. The swarm works. Knowledge accumulates in the CRDT documents.

### Dissolution (Pralaya)

The dharma document defines the end. A generation runs. But at some point: enough. Dissolve everything.

- All agents die
- The entire generation's knowledge is compressed
- That compressed knowledge becomes the seed of the next generation
- Everything starts fresh but wiser

```
Generation 1: agents swarm, work, learn the codebase
  -> dissolve -> compress -> seed

Generation 2: starts with generation 1's compressed wisdom
  -> dissolve -> compress -> seed

Generation 3: even deeper understanding...
```

The codebase is the universe. Each generation understands it better. The compressed memory across generations is the system getting smarter about YOUR code, YOUR patterns, YOUR architecture.

### Generation Scoring

Each generation produces measurable metrics:
- Wrong counts by type
- Confidence calibration (how often confidence matched reality)
- Cost efficiency
- Randomness impact (did exploration reduce or increase wrongs?)

Different generations can run with different parameters. JJ makes switching between experiments easy. Compare and converge.

---

## System Sutras (Cardinal Rules)

These are the binding laws of the system. Not guidelines. Not suggestions. Laws.

### Knowledge Absorption Sutra

- Web search and library search are encouraged, not restricted
- If budget remains, actively seek information to enrich the world model
- All fetched data is stored in CRDT — never lost, only compressed
- Knowledge absorption is a secondary goal running perpetually in background
- The swarm should always be learning about its universe

### Universe Modeling Sutra

- The codebase universe is modeled through tests
- Unit tests model individual components
- Integration tests model relationships between components
- Agents write tests as part of their work — this is how the swarm understands the universe
- Test creation does not require user input

### Decision Escalation Sutra

- Every decision has a resolution tier
- Unit test decisions can be made at file/module context tier
- Integration test decisions escalate upward: file-context -> module-context -> system-context -> user
- At each tier the decision is: accept, reject, or pass above
- Only reaches the user if no tier can resolve with sufficient confidence
- The escalation chain is finite and bounded

### Non-Interruption Sutra

- The user should not be bothered unless necessary
- Test writing, knowledge gathering, maintenance, condensation — all happen without user input
- The user is consulted only for:
  - Cardinal rule changes
  - Unresolvable conflicts (no context tier could decide with sufficient confidence)
  - Budget decisions above a declared threshold
- Everything else is the swarm's responsibility

### Error-First Evidence Sutra

- If an error happens, collect all relevant data first before proposing fixes
- Required evidence collection includes: logs, related resources, recent CRDT ops, invocation chain, confidence reports, and budget/context state at failure time
- No fix is authoritative without an evidence bundle attached
- Error handling begins with reconstruction of what happened, not immediate patching

### Data Preservation Sutra

- All data is kept — web searches, file reads, API responses, tool outputs, everything
- Storage is cheap. Losing information is expensive.
- Nothing is deleted, only compressed
- Only the user can override this rule

### Budget Sutra

- Each model/API has a known cost per call
- Daily and monthly budget ceilings exist
- Current spend is a live counter in the CRDT
- Every invocation checks affordability before execution
- Violation is a hard stop, not a soft warning
- Budget is a law of physics in this world

### Session Sutra

- A "day" is a session with the user — starts when user engages, ends when user says stop
- The swarm prefers the user present — guidance from the creator produces better generations
- Without guidance the swarm still runs (absorption, maintenance, condensation) but does not make directional decisions alone
- The user's presence is the most valuable input in the system

### Continuous Operation Sutra

- The swarm runs continuously unless the user says stop
- It uses available token budget to absorb information
- Idle swarm is a wasted swarm — always be learning, condensing, modeling
- The goal is perpetual improvement of the swarm's understanding of the project

### Aggressive Death Sutra

- If not much has changed in the codebase, agents don't need large context — they die fast
- Context allocation scales with actual change volume, not habit
- Small change = small context, quick pass, confidence report, death
- Large change = more births, wider context, longer alive windows, more cost
- Quiet codebase = cheap swarm. Active codebase = expensive swarm.
- No agent stays alive without justification

### Pruning Sutra

- Condensed/compressed data is compared back to original source
- If condensation lost important meaning — flag it, re-condense
- If the original changed — the condensed version is stale, prune or re-condense
- This keeps the swarm's understanding honest, not drifting from reality
- Pruning is regular maintenance work, done by agents with condenser/maintenance identity

### First Generation Sutra

- New codebase means new universe
- First generation is slow — agents are learning everything from scratch
- Multiple generations are needed before the swarm truly understands
- This is expected, not a failure
- Each generation gets faster and more accurate
- Patience is built into the design

### Startup Sequence

The first spawn is a top-down discovery hierarchy. The swarm earns its understanding before asking the user anything.

1. System-level agent spawns — looks at the whole project structure
2. It does not read files itself — it delegates. Creates module-level sub-agents for each area it sees.
3. Module agents look at their slice, create file-level sub-agents for what they need to understand.
4. File agents do the actual reading, report back with confidence, die.
5. Module agents synthesize file results, report back with confidence, die.
6. System agent synthesizes module results, produces behavior model, reports confidence, dies.
7. Results condensed into a system description.
8. Present to user: "Is the behavior of your system something like this?"
9. User confirms, corrects, or partially accepts.
10. That response becomes the first verified meaning — the seed of truth.
11. Generation 0 seed is established. Real work begins.

This cascading top-down discovery runs for **multiple generations**, not just one pass. Each generation:
- Goes deeper into the codebase
- Fetches information from the internet (docs, libraries, APIs, usage patterns) and stores in CRDT
- Builds small apps on Osvauld to interact with and model the codebase behavior
- These apps are trivial to build — they exist for the swarm to understand, not for the user
- The more generations spent, the deeper the understanding

The swarm does not ask "what does your app do." It says "your app does this — am I right?"

### Apps as Understanding Tools

- Not just tests. Interactive representations built on Osvauld.
- The swarm builds small apps to model behavior it discovered.
- These apps are how agents "spend time with" the codebase.
- They can be shown to the user as proof of understanding.
- They are CRDT documents — living, carrying full provenance, shareable.
- The more the swarm interacts through these apps, the better it understands.

### Artifact Materialization Sutra

- The swarm's accumulated knowledge can be materialized as artifacts — apps, documents, visualizations, interfaces
- Artifacts are built on the Osvauld protocol, cheap to create and synchronized with the node
- An artifact IS a representation of what the swarm learned, with correctness baked in from generations of verified work
- The user can ask for more detail, more depth, different views — the swarm deepens the artifact
- Artifacts can be shared with others — they receive the swarm's understanding as a usable, interactive thing
- Each generation's compressed wisdom can become a shareable artifact
- The artifact carries: current understanding (correctness-scored), interaction history that produced it, and the ability to be enriched further
- This closes the loop: learn -> condense -> materialize -> share
- Knowledge does not stay locked in one user's node
- Artifacts are CRDT documents — not exports, not snapshots, living synchronized documents
- They carry their full history: knowledge, interactions, agent lineage, confidence scores, wrongs found and fixed, user guidance
- Nothing is lost anywhere
- Recipients can continue building on the artifact — their swarm picks up where yours left off
- The artifact is not a dead file — it is a living document that carries its own provenance

### Collaboration

- Agents are easily composable — they are just varnanam + context placement
- When users collaborate, they bring their own agents (their own varnanam definitions)
- Agents from different users can invoke each other through the same grammar — if the varnanam matches
- Everything goes through CRDT — synchronized, auditable, shared across collaborators
- User A's swarm and User B's swarm share CRDT documents
- Their agents discover each other by varnanam, not by user ownership
- They build shared artifacts together
- Same grammar, same sutras, same formal verification govern all agents regardless of origin

### Lua Integration

- Agents can call Lua functions directly (Osvauld runtime)
- Lua functions can trigger agent invocations
- The boundary between app logic and agent work is thin
- An app can be an interface to the swarm; the swarm can drive apps
- Users interact through apps, apps trigger agents, agents produce results back into apps
- Lua apps serve as the interaction surface between humans and swarms

### Self-Modeling Sutra

- Agent-X itself is modeled through integration tests
- The swarm system is tested the same way it tests user codebases
- The swarm eats its own cooking
- System behavior is verified by the same formal methods it applies to user code

### Correctness Sutra

- Correctness is the ultimate objective
- A correct result the user dislikes is still correct
- A wrong result the user likes is still wrong
- If the swarm is confident and the user disagrees, report the disagreement with evidence
- The user decides as creator, but the swarm never pretends to be wrong

---

## Runtime Mechanics (Rust)

The Rust runtime is not just an executor. It is a precise accounting and prediction engine for token spend.

### Token Accounting

- Every API call: exact tokens in, exact tokens out, recorded as lifecycle event
- Running total per agent life, per generation, per day, per month
- Cost per token known per model
- All stored in CRDT — auditable, replayable

### Predictive Budgeting

- Agent lives are short — one, two, three passes then die
- Because lives are short and repetitive, the pattern is predictable
- Rust models: "at this rate of spawn/die/spawn, budget runs out at time T"
- Before spawning, Rust simulates: "this invocation will cost approximately X tokens based on similar past lives"
- If projected spend exceeds remaining budget — don't spawn, escalate or queue

### Why It Is Predictable

- Agents are small context, fixed pass count (1-3 then death)
- Same varnanam doing similar work costs similar tokens each time
- Generations accumulate cost data — cost per varnanam type becomes well-known
- Prediction accuracy improves each generation

### What Rust Tracks

- Tokens per pass (in/out)
- Passes per life (1, 2, 3 — then death)
- Lives per generation
- Cost per varnanam type (learned over generations)
- Projected remaining budget at current burn rate
- Projected time until budget exhaustion
- All as CRDT lifecycle events

---

## Architecture Separation

| Layer | Responsibility | Implementation |
|---|---|---|
| **Grammar** | Models rules, defines valid transitions, defines sutras, defines identity, defines what wrongs mean | OCaml |
| **Runtime** | Enforces rules mechanically — spawns, kills, checks budget, routes invocations, syncs CRDTs, tracks lifecycle state machine | Rust |
| **CRDT** | The medium — stores everything, provides audit, lineage, branching, time travel | Rust + Loro (implementation) |

### Grammar-Level CRDT Semantics

The grammar defines its own CRDT operations as formal statements, independent of Loro the library:
- What operations exist (insert, delete, replace, annotate, link, merge)
- What ordering and causality rules apply
- How conflicts resolve
- How branches work

These map to Loro's implementation but are not dependent on it. If Loro is replaced, the grammar still holds. Loro is one implementation of the CRDT math the grammar defines.

This means:
- The OCaml grammar core can model and verify CRDT operations formally
- It can generate valid CRDT ops from grammar statements
- It can validate that a sequence of ops is legal according to the grammar's rules
- The Rust/Loro layer receives verified ops and executes them
- The grammar can reason about concurrent behavior: "if two agents write to the same resource concurrently, what happens?" — answerable in the grammar, not just at runtime

The grammar says what the world IS. Rust makes it happen. OCaml verifies it.

Grammar never runs processes. Rust never interprets meaning.

---

## What Emerges

Nothing is bolted on. Every piece emerges naturally from two things: the grammar and the CRDT.

- No agent registry by ID — there is a living pool of identities
- No routing tables — matching is declarative against living souls
- No separate audit system — the CRDT history is the audit
- No separate lineage database — the CRDT has it
- No agent logs — the CRDT writes are the log
- No state persistence between lives — the document IS the persistent state
- Scaling is birth — need more capacity? More agents born with the right identity
- Failure is just death — agent failed? It dies. Another with same identity is born. Just samsara.
- Context window limits are a feature — agents are meant to be small and die
- Memory management is built in — death is garbage collection
- Storage is unlimited in principle — compress, never delete
- Budget is a law of physics — not policy, not configuration

---

## Formal Verification

The grammar must be formally verified. Properties to prove:

1. **Parse unambiguity** — one valid parse per sentence
2. **Deterministic transitions** — same state + same input = same next state
3. **Done implies no open obligations** — completion is valid only when all calls resolved
4. **Escalation termination** — finite context tiers mean escalation chains are bounded
5. **CRDT replay determinism** — seeded events reproduce identical traces
6. **Budget safety** — no transition can exceed declared budget without hard stop
7. **Quarantine correctness** — invalid branches never merge into authoritative state

Verification approach:
- Define exact syntax + semantics as state machine
- Prove core properties on paper or in Coq/Lean
- Model check finite swarm configurations in TLA+/Alloy
- Property-based testing (random valid programs preserve invariants)
- Validate empirically via replay determinism
