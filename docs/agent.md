# Agent: The Neuron of the Swarm

*See also: nyaya.md for the logic agents produce, prajna.md for the intelligence they build, consciousness.md for the entity that experiences their work, dharma.md for configurable parameters.*

---

An agent is a neuron. It reads a small piece of the world, forms one small truth, and dies. It does not experience the whole. It does not understand the system. It contributes one nigamana to the CRDT and is gone. The prajna — the accumulated intelligence — is built from the work of many agents across many generations.

Agents are mortal. The prajna is not.

---

## The Agent

In plain language: an agent is defined by five things — who it is (its identity and what it can do), what capabilities it has (read files, form hypotheses, etc.), what level it operates at (single file, module, whole system, or everything), how much budget it has left to spend, and which life it is currently on (each incarnation gets a unique life id).

An agent A is a 5-tuple:

```
A = (ι, C, τ, b, L)

where:
  ι  = identity (varnanam — capabilities and constraints)
  C  = {c₁, c₂, ...}  capabilities
  τ  ∈ {file, module, system, universe}  context tier
  b  ∈ ℝ≥0  budget remaining
  L  = life id (unique per incarnation)
```

The identity ι persists across lives (rebirths). The life id L is unique to each incarnation — it seals when the agent dies and is replaced by a new L on rebirth.

---

## Actions and Costs

Every action is a state transition with a cost. No action is free (except waiting, reporting confidence, and dying — which are administrative).

```
Action           Cost    Output                    Precondition
──────────────────────────────────────────────────────────────────
spawn(A)         c_s     new agent A born          budget available in caller
read(r)          c_r     knowledge of r            r ∈ scope(A)
see(img)         c_v     visual knowledge of img   img ∈ scope(A)
parse(log)       c_r     structured log knowledge  log ∈ scope(A)
hypothesize(P)   c_h     paksha P with hetu H      |H| ≥ 1
invoke(q, C')    c_i     call issued to swarm      q is a valid question
wait()           0       blocked                   open call exists
answer(a, w)     c_a     answer with weight w      fulfills exactly one call
test(D)          c_d     drishthanta result         hypothesis formed
confidence(w)    0       epistemic report           mandatory before die
die()            0       life ends                  open_calls(L) = 0 ∧ confidence_reported(L)
rebirth(seed)    c_s     new life L'               die(L) completed
```

All cost constants (c_s, c_r, c_v, c_h, c_i, c_a, c_d) are configurable in dharma.md.

In plain language: every agent starts with a budget. Every action costs something. The total cost of all actions cannot exceed the starting budget. An agent can only die when two conditions are met: it has no unfinished delegations (no open calls waiting for answers) and it has reported its confidence level. Both must be true. An agent cannot just disappear — it must wrap up its work and say how confident it is before it dies.

Budget constraint per life:

```
Σᵢ cost(actionᵢ) ≤ b₀

b_remaining(t) = b₀ - Σᵢ₌₁ᵗ cost(actionᵢ)

die() valid ⟺ open_calls(L) = 0 ∧ confidence_reported(L)
```

---

## The Life as a Trace

In plain language: every life of an agent produces a record — a list of everything it did from the moment it was born to the moment it died. The yield is what it produced — how many formal conclusions it established. The cost is how much budget it consumed. The efficiency is the ratio of verified knowledge produced per unit of budget spent — high efficiency means the agent produced strong conclusions cheaply, low efficiency means it spent a lot for weak results.

A single life produces a trace — an ordered sequence of actions from spawn to die:

```
T(L) = [a₁, a₂, ... aₙ]     where a₁ = spawn, aₙ = die

yield(L) = {N₁, N₂, ...}     -- set of nyaya formed in this life
cost(L)  = Σᵢ cost(aᵢ)       -- total budget consumed
efficiency(L) = Σᵢ w(Γᵢ) / cost(L)    -- verified knowledge per unit cost
```

The trace is sealed in the CRDT when the agent dies. It is permanent — the record of what this life did.

---

## The Invoke-Answer Cycle

Agents do not work in isolation. They can delegate to other agents via invoke/answer:

```
invoke(q, C') :
  find A' where C' ⊆ capabilities(A')
  if ∄A' : spawn(A') with capabilities C', budget b_delegated ≤ b_remaining
  route q to A'
  caller.status ← blocked

answer(a, w) :
  fulfills exactly one invoke
  w ∈ [0, 1]
  caller.status ← active
  caller inherits a as shabda with weight w
```

Weight propagates through delegation — a caller cannot claim higher confidence than what its delegate provided:

```
w(caller's nyaya) ≤ w(answer from callee)
```

This is the budget hierarchy and the weight hierarchy — both are conserved downward through delegation.

---

## Death and Rebirth

An agent does not simply disappear. It dies formally — sealing its trace — and can be reborn.

```
die(L) :
  precondition: open_calls(L) = 0 ∧ confidence_reported(L)
  effect: T(L) sealed in CRDT, L closed

rebirth(L, seed) :
  precondition: die(L) completed
  effect: L' = (ι, C, τ, b₀, new_id)
          lineage(L') = L
          soul persists — knows blocks carry over
          conversation history does NOT carry over (fresh context window)
```

Rebirth preserves the soul (identity, capabilities, accumulated good points) but starts a fresh context window. The agent does not remember the previous life's conversation — it reads the accumulated data instead. Everything worth knowing is in the data. The conversation was transient. The truths are permanent.

---

## The Population Model

The swarm at generation g:

```
S(g) = {A₁, A₂, ... Aₖ}     -- living agents

birth_rate(g)   = |{A : spawned in g}|
death_rate(g)   = |{A : died in g}|
rebirth_rate(g) = |{A : reborn in g}|

|S(g)| = |S(g-1)| + birth_rate(g) - death_rate(g) + rebirth_rate(g)
```

The population is not fixed. Agents spawn more agents on demand (via invoke). The budget constrains the total population size — not directly, but through cost accumulation. When the generation budget is exhausted, no more spawning is possible.

---

## Budget Flow

Budget is conserved. It flows downward through delegation. No agent creates budget.

```
B(g) = total budget for generation g

Σ cost(Lᵢ) for all lives i in generation g  ≤  B(g)

On invoke: b_delegated ≤ b_remaining(caller)
           b_remaining(caller) ← b_remaining(caller) - b_delegated
```

The budget hierarchy mirrors the agent hierarchy. The root agent has the full generation budget. It delegates fractions to its children. Children delegate to their children. The leaves do the actual perception work with whatever budget remains.

A child cannot spend more than its parent delegated. A parent cannot delegate more than it has remaining. Budget is finite, flows down, and is never replenished within a generation.

---

## Cost Function

Every nyaya has a total cost — the sum of all actions that went into forming it:

```
cost(N) = Σ cost(reads) + cost(spawns) + cost(tests) + cost(invokes)
```

The efficiency of a nyaya:

```
efficiency(N) = w(Γ) / cost(N)
```

High efficiency: high-weight nigamana produced cheaply. Low efficiency: expensive work for weak results.

The swarm optimizes for total verified knowledge per unit cost:

```
maximize:  Σᵢ w(Γᵢ) / Σᵢ cost(Nᵢ)     subject to  Σᵢ cost(Nᵢ) ≤ B(g)
```

---

## Context Tiers

Agents operate at one of four context tiers. The tier determines what the agent can perceive and what paksha it can legitimately form:

```
τ = file      — reads individual files, forms paksha about one file's behavior
τ = module    — reads multiple files in a module, composes file-level nigamana via shabda
τ = system    — reads across modules, composes module-level nigamana via shabda
τ = universe  — reads across systems, composes system-level nigamana via shabda
```

Higher tiers do not read raw files — they read established nigamana from lower tiers and compose them. This enforces the knowledge hierarchy: file truths feed module truths feed system truths. No system-tier agent claims to have read a file directly. It cites the file-tier nigamana via shabda.

```
file-tier nyaya:    reads "src/auth/validator.rs" → forms N₁ about validate_token
module-tier nyaya:  cites N₁ as shabda → forms N₂ about the auth module
system-tier nyaya:  cites N₂ as shabda → forms N₃ about the full system
```

The weight of N₃ is bounded by the weakest link in the shabda chain — which is bounded by the file-tier observations. The evidence ultimately grounds out in pratyaksha (direct perception of the code). No tier above can claim higher confidence than what the tier below established.

---

## The Soul

The soul (ι) is the persistent identity of an agent across all its lives. It carries:

- **Varnanam** — the formal description of what this agent knows and can do
- **Accumulated good points** — the epistemic merit earned across all lives
- **Knows blocks** — things the soul has been explicitly told to be aware of (carry over across rebirths)

The soul does not carry conversation history — that is transient, local to each life. The soul carries identity and merit. The conversation carries context. When the agent dies and is reborn, it starts fresh but with its accumulated identity intact.

```
Soul persists:      ι, GP(soul), knows blocks
Life is transient:  conversation history, context window contents

After rebirth:
  new agent reads CRDT     — gets the accumulated prajna
  new agent reads knows    — gets the carry-over from previous lives
  new agent does NOT read  — the previous life's conversation
```

This is the correct design. The CRDT is the memory. The conversation is the working memory. Working memory clears on rebirth. Long-term memory persists in the CRDT.
