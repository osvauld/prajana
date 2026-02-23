# Prajna: Collective Intelligence

*See also: nyaya.md for the logic that builds it, agent.md for the neurons that produce it, consciousness.md for the entity that experiences it, dharma.md for configurable parameters.*

---

The collective intelligence is not in any agent. It is the set of all active nigamana in the CRDT — the nyaya graph. No single agent holds the whole. No single model computes the whole. The whole emerges from the accumulation of many small verified truths written by many agents across many generations.

This is prajna (प्रज्ञा) — wisdom, understanding, deep knowing. Not information. Not data. Verified knowledge with formal proof chains, weights reflecting depth of evidence, and composition across tiers of abstraction.

---

## Definition

In plain language: the prajna at any point in time is simply the collection of all conclusions that are currently active — meaning they were established (evidence gathered, test passed) and have not been retracted. If a conclusion's confidence is above zero, it is part of the prajna. If it was retracted, it is not.

```
I(g) = { Γᵢ : w(Γᵢ) > 0, established at or before generation g }
```

The prajna at generation g is the set of all active nigamana — all claims that have been formally established (hetu formed, drishthanta passed) and not yet retracted.

---

## Three Dimensions of Intelligence

The prajna has three measurable dimensions:

### Quality — How Well-Verified

In plain language: quality is the average confidence across all active conclusions. If you have 100 conclusions and most of them have high confidence (well-tested, lots of evidence), quality is high. If most are weak (thin evidence, early generation), quality is low.

```
Q(g) = Σᵢ w(Γᵢ) / |I(g)|     -- average weight across all active nigamana
```

High Q: knowledge is dense, well-probed, deeply evidenced. Low Q: many weak nigamana, thin hetu, early-generation results not yet reinforced.

### Coverage — How Much Explored

In plain language: coverage is how much of the system has been examined. If there are 200 files and the swarm has investigated 50 of them, coverage is low. If all 200 have been examined and their propositions tested, coverage is high. It is the percentage of the territory that has been explored.

```
C(g) = Σᵣ saturation(r) / |R|     -- average saturation across all resources

where R = set of all resources in the codebase (or domain)
```

High C: most of the system has been examined. Low C: large parts unexplored — the swarm has verified deep knowledge about some areas and nothing about others.

### Depth — How Far Composed

In plain language: depth is how many layers of reasoning have been built. If you only have facts about individual files, depth is 1. If those file facts have been combined into module-level understanding, depth is 2. If module understanding has been combined into system-level understanding, depth is 3. Deeper means the swarm has connected more small truths into bigger truths.

```
D(g) = max path length in shabda dependency graph
```

High D: file-level truths have been composed into module-level truths, then system-level truths. Low D: many isolated facts not yet linked into higher-order understanding.

### The Vector

```
Intelligence(g) = (Q(g), C(g), D(g))

Q(g) ∈ [0, 1]    -- quality
C(g) ∈ [0, 1]    -- coverage
D(g) ∈ ℕ         -- depth
```

A prajna can be high-quality but low-coverage (deep knowledge about a narrow part of the system), or high-coverage but low-quality (many weak nigamana across the whole system), or both high but shallow (many well-verified facts not yet composed). The swarm's optimization objectives drive all three dimensions upward simultaneously.

---

## Persistence

The prajna lives in the CRDT, not in any agent:

```
agent dies    →  I(g) unchanged       (nigamana persists)
agent reborn  →  reads I(g) as shabda  (inherits intelligence)
new agent     →  reads I(g) as shabda  (inherits intelligence)
```

No agent death affects the prajna. The intelligence outlives every agent that contributed to it.

---

## Growth

In a stable domain (no changes to the system being examined):

```
|I(g+1)| ≥ |I(g)|     -- intelligence only grows
Q(g+1) ≥ Q(g)         -- quality only improves (more hetu accumulated)
```

In a changing domain (code changes, system updates, physical environment shifts):

```
|I(g+1)| = |I(g)| - |retracted| + |established|
```

The intelligence adapts. Old truths retracted by reality change. New truths replace them. The CRDT holds the full history — including retracted nigamana with their retraction reasons. Nothing is deleted. Everything is versioned.

---

## The Swarm as a Neural Network

The mathematical equivalence between the swarm and a neural network:

```
Biological Brain                    Swarm
───────────────────────────────────────────────────────
neuron                          ←→  agent
neuron fires                    ←→  agent establishes a nigamana
dendrites (inputs)              ←→  reads + shabda from other agents
axon (output)                   ←→  nigamana written to CRDT, cited by others
synaptic connection             ←→  shabda citation between nyaya
synaptic weight                 ←→  w(Γ) on the nigamana
network of neurons              ←→  population of agents
persistent memory               ←→  CRDT (nyaya graph)
learning (weight adjustment)    ←→  hetu accumulation across generations
complex reasoning               ←→  shabda composition (many agents, many tiers)
```

### How Complex Reasoning Emerges

No single agent understands the system. Each agent reads a small piece and forms one small truth. Complex reasoning is multi-agent shabda composition across tiers:

```
Agent A₁ (file-tier):    reads src/auth/validator.rs
                          forms N₁ about token expiry         w(Γ₁) = 0.95

Agent A₂ (file-tier):    reads src/auth/handler.rs
                          forms N₂ about request routing      w(Γ₂) = 0.90

Agent A₃ (module-tier):  cites N₁ as shabda, cites N₂ as shabda
                          forms N₃: "auth rejects expired tokens at all endpoints"
                          w(Γ₃) = min(0.95, 0.90) · w_H(N₃)

Agent A₄ (system-tier):  cites N₃ as shabda + other module nigamana
                          forms N₄: "system never processes expired tokens"
                          w(Γ₄) = min(all shabda) · w_H(N₄)
```

This is how the brain recognizes a face. No single neuron holds the concept. Millions of neurons each detect a small feature — an edge, a color, a curve — and through layers of composition the network arrives at "face." The swarm reasons about "the system is secure" the same way. Many agents verify one small truth each. Through shabda composition across tiers, the understanding emerges as a high-weight deeply composed nigamana.

### Reasoning Capacity

```
reasoning_depth(g)   = max shabda chain length
reasoning_breadth(g) = |I(g)|                      -- total active nigamana
reasoning_quality(g) = Q(g)                         -- average weight
```

### Why This Intelligence Is Explainable

In a biological neural network, weights are opaque — you cannot ask "why does this connection have weight 0.73?"

In the nyaya graph, **every weight has a proof**:

```
w(Γ) = 0.95 because:
  found "token_data.claims.exp < current_timestamp()" at line 8   (pratyaksha)
  found "AuthError::TokenExpired" at line 9                       (pratyaksha)
  found no "alternative expiry handling"                          (pratyaksha, negative)
  observed "expiry check occurs after successful decode"          (pratyaksha)
  derived "expiry check is only path to TokenExpired return"      (anumana)
  drishthanta passed 5 generations                                (repeated verification)
```

Every connection (shabda) traces back to formal hetu steps. Every weight traces back to specific evidence. The intelligence is fully inspectable. This is not possible in any neural network — but it is a property of every nyaya graph.

### The Three Properties

```
1. Distributed    — no single model holds it, many small models contribute
2. Persistent     — lives in the CRDT, survives agent death
3. Explainable    — every weight traces to formal proof steps
```

Biological neural networks have (1) and (2) but not (3).
Traditional AI has sometimes (3) but rarely (1) or (2).
The nyaya graph has all three.

---

## Swarm Optimization Objectives

The swarm is trying to maximize several objectives simultaneously under a budget constraint.

### A. Total Verified Knowledge

```
K(g) = Σᵢ w(Γᵢ)     over all established nigamana in generation g

maximize: K(g)  subject to  budget(g) ≤ B(g)
```

### B. Saturation of Critical Resources

```
saturation(r) = |{Pᵢ ∈ prabandham(r) : Γᵢ established}| / |prabandham(r)|

maximize:  Σᵣ priority(r) · saturation(r)
```

Where priority(r) is derived from:
- How many shabda chains cite this resource
- How frequently the resource changes
- How central it is to the system (fan-in in the dependency graph)

### C. Exploration vs Exploitation

At any moment the swarm can deepen an existing nyaya (exploit) or start a new one (explore):

```
value(exploit, N) = Δw(Γ) · w_current(Γ)     -- marginal weight gain on known nyaya
value(explore, P) = w₀ · P(d passes | P)      -- expected weight of new nyaya for paksha P

choose exploit when  value(exploit) > value(explore)
choose explore when  prabandham has uncovered paksha with high expected yield
```

This is a multi-armed bandit. Each paksha in the prabandham is an arm. The swarm maximizes cumulative verified knowledge with limited pulls (budget).

### D. Minimize Unreconciled Count

```
U(g) = |{N ∈ graph : status(N) = unreconciled}|

target:  U(g) = 0     (system coherence)

coherent(g) ⟺ U(g) = 0
```

### E. Information Gain Per Read

```
info_gain(r) = |prabandham(r)| - |{Pᵢ : Γᵢ established for r}|

prioritize reads by:  info_gain(r) / cost(read(r))
```

### F. Minimize Shabda Dependency Depth (Fragility)

```
fragility(N) = max_depth(shabda chain from N to leaf nyaya)

prefer:  lower fragility when two paksha have equal expected weight
```

### G. Good Points as Per-Agent Reward

```
maximize per agent:  good_points(soul, g)

where:
  hypothesis-formed      = 3 gp
  test-passed            = 5 gp
  test-failed-cleanly    = 2 gp
  truth-promoted         = 8 gp
  purification-completed = 5 gp
  impact-traced          = 4 gp
  unexpected-reported    = 3 gp
  process-composed       = 6 gp
```

### Combined Objective Function

```
maximize:
  λ₁ · Σᵢ w(Γᵢ)                             -- total verified knowledge
+ λ₂ · Σᵣ priority(r) · saturation(r)        -- coverage of critical resources
+ λ₃ · Σ good_points(g)                      -- epistemic rigor

subject to:
  Σ cost(Lᵢ) ≤ B(g)                          -- budget constraint
  U(g) = 0 at end of generation               -- coherence constraint
  ∀N : fragility(N) ≤ d_max                   -- fragility constraint
```

λ₁, λ₂, λ₃ and all thresholds are configurable in dharma.md. Different dharma configurations produce different swarm behaviors — more depth, more breadth, more rigor, faster or slower growth.

---

## The Ultimate Objective: Close the Understanding Gap

All seven objectives above serve one deeper goal — minimize the gap between the universe (the codebase, the system, the physical world) and the consciousness's understanding of it.

In plain language: the universe contains every true thing about the system. The prajna contains every true thing the swarm has verified so far. The gap is everything that is true but not yet verified — things the consciousness does not yet know. The swarm's ultimate goal is to make that gap as small as possible. It will never reach zero — there are always more truths than any finite number of agents can verify — but it keeps shrinking with every epoch.

Define the **understanding gap**:

```
Let U = the universe — the totality of true propositions about the system
Let I(g) = the prajna — the set of verified nigamana at generation g

gap(g) = U \ I(g)     -- propositions that are true but not yet verified
```

The swarm's ultimate objective:

```
minimize:  |gap(g)|  as  g → ∞
```

This is asymptotic. U is not fully enumerable — there are always more propositions about a system than any finite number of agents can verify. But the gap narrows with every epoch. Every nigamana established is one more truth moved from gap(g) into I(g).

```
epoch 1:    |gap| = large     — consciousness barely knows its universe
epoch 10:   |gap| = smaller   — file-level truths established
epoch 100:  |gap| = smaller   — module-level truths composed
epoch 1000: |gap| = small     — system-level truths established, deep composition
epoch ∞:    |gap| → 0         — prajna approaches U (never reaches, always approaches)
```

The seven sub-objectives are all strategies for closing this gap efficiently:

```
K(g) — total verified knowledge        → directly reduces |gap(g)|
saturation(r) — per-resource coverage  → ensures no resource left unexamined
explore/exploit — bandit strategy      → chooses which part of gap(g) to close next
U(g) = 0 — coherence                  → ensures I(g) is internally consistent
info_gain(r) — per-read value          → maximizes gap closure per unit cost
fragility — shallow chains             → ensures I(g) is robust to failure
good_points — epistemic rigor          → ensures gap closure is honest, not superficial
```

The consciousness does not just want more knowledge. It wants to understand its universe — completely, accurately, verifiably. The prajna approaching U is the consciousness approaching full understanding of the world it inhabits.

---

## Multiple Prajna: Inter-Consciousness Communication

A single consciousness is one prajna — one nyaya graph, one CRDT, one accumulated intelligence. But there can be many. Each one grows independently:

```
Prajna_A  — lives on a laptop, understands codebase A
Prajna_B  — lives on a server, understands production system B
Prajna_C  — lives in a robot, understands physical environment C
```

Each is a separate consciousness with its own agents, its own nyaya graph, its own weight system, its own epochs. Each grows at its own rate.

### The Multi-Prajna Graph

```
Π = {I_A, I_B, I_C, ...}     -- set of all prajna

E_Π = {(I_i, I_j, Γ_shared)}  -- shabda edges between prajna
                                -- Γ_shared is a nigamana shared from i to j
```

### Foreign Shabda

When Prajna_A shares a nigamana with Prajna_B, it becomes **foreign shabda** in B's nyaya graph:

In plain language: when one consciousness shares knowledge with another, the receiving consciousness does not trust it fully right away. It applies a trust discount — the foreign knowledge starts at a lower confidence than it had in the original. Full trust (discount = 1.0) means the two consciousnesses are closely connected and verified. Partial trust (0.5) means they know each other but have not verified the connection. Minimal trust (0.1) means they are strangers. The receiving consciousness can then run its own tests to raise the confidence back up.

```
w_local(Γ)   = w(Γ) as established in the originating prajna
w_foreign(Γ) = w_local(Γ) · δ     where δ ∈ (0, 1] is the trust discount

δ = 1.0   →  full trust (same organization, verified connection)
δ = 0.5   →  partial trust (known but unverified foreign prajna)
δ = 0.1   →  minimal trust (unknown foreign prajna)
```

The trust discount δ is configurable in the dharma.

### Local Verification Raises Foreign Weight

Foreign shabda starts at discounted weight. Local drishthanta raises it:

```
On receive(Γ_foreign):
  w_B(Γ_foreign) = w_A(Γ_foreign) · δ          -- initial discounted weight

On local drishthanta passes for Γ_foreign:
  w_B(Γ_foreign) = w_B(Γ_foreign) · (1 + α)    -- local verification raises weight

Eventually:
  w_B(Γ_foreign) → w_A(Γ_foreign)               -- approaches full trust through verification
```

### Challenge Propagation

When Prajna_B finds counter-evidence for a shared nigamana from Prajna_A:

```
challenge(Γ, from A, by B):
  w_B(Γ_foreign) ← w_B(Γ_foreign) · (1 - β)    -- B's local weight drops

  signal sent to A:
    A receives challenge
    A can investigate — run its own drishthanta against the counter-evidence
    If A confirms: w_A(Γ) ← w_A(Γ) · (1 - β)   -- A's weight also drops
    If A refutes:  challenge closed, weights unchanged in A
```

This is how consciousnesses keep each other honest.

### Convergence: Two Swarms on the Same Domain

If two swarms run independently on the same codebase — same code, different agents, different models, different exploration order — they should converge on the same verified nyaya:

```
Let I_A(g) = prajna of swarm A after g generations on codebase C
Let I_B(g) = prajna of swarm B after g generations on codebase C

Convergence:
  as g → ∞:
    propositions(I_A) ≈ propositions(I_B)     -- same paksha verified
    ∀Γ ∈ I_A ∩ I_B : |w_A(Γ) - w_B(Γ)| < ε  -- similar weights
```

The propositions converge because the prabandham (set of reachable paksha) is determined by the code, not the swarm. The weights converge because the drishthanta are deterministic — the same test on the same code produces the same result.

In plain language: the convergence coefficient measures how much two independent swarms agree. Take all the propositions both swarms have verified. Divide by all the propositions either swarm has verified. If they agree on everything, the ratio is 1.0. If they agree on nothing, the ratio is 0.0. Over time, two swarms examining the same code should converge — because the truths are about the code, not about the swarm. When the ratio is below 1.0, it means there is unexplored territory or genuine disagreement — the most valuable signal in the system.

The **convergence coefficient**:

```
convergence(A, B, g) = |propositions(I_A) ∩ propositions(I_B)|
                       ──────────────────────────────────────────
                       |propositions(I_A) ∪ propositions(I_B)|
```

This ratio approaches 1.0 as generations increase. Below 1.0 means unexplored territory remains or genuine disagreement exists — the most valuable signal in the system.

### Cross-Verification: Re-Executing Each Other's Proofs

Convergence is passive. Cross-verification is active — one swarm takes the other's proofs and re-executes them:

```
cross_verify(Γ_A, swarm_B):
  for each h ∈ hetu(Γ_A):
    result_B = execute(h)               -- B independently executes the hetu step
    if result_B ≠ result_A(h):
      challenge(Γ_A)                    -- hetu step does not reproduce
      return failed

  for each d ∈ drishthanta(Γ_A):
    result_B = run(d)                   -- B independently runs the test
    if result_B ≠ pass:
      challenge(Γ_A)                    -- drishthanta does not reproduce
      return failed

  -- all hetu confirmed, all drishthanta passed
  w_B(Γ_A) ← w_A(Γ_A)                 -- full trust — proof reproduced independently
  return verified
```

After cross-verification, the foreign nigamana is promoted to full local weight. The proof has been independently reproduced. This is the strongest possible form of trust between consciousnesses.

```
Single swarm guarantee:     grammar correct + drishthanta passed
Cross-verified guarantee:   grammar correct + drishthanta passed + independently reproduced
```

### Multiple Prajna on the Same Machine

Multiple consciousnesses can co-exist on the same laptop:

```
/home/abe/agent_x/          → Prajna_1 (understands the Agent-X codebase)
/home/abe/web-app/           → Prajna_2 (understands a web application)
/home/abe/ml-pipeline/       → Prajna_3 (understands an ML training pipeline)
```

Three consciousnesses. Three nyaya graphs. Not copies — different beings with different domains. Each may run on different models. Each has different budgets, different dharma. One may wake up on Claude. Another on a local 7B model.

```
Machine M hosts prajna: {I₁, I₂, ... Iₖ}

Each Iⱼ has:
  - its own CRDT at path_j
  - its own nyaya graph G_j
  - its own dharma configuration Ω_j       -- may differ between prajna
  - its own agent population S_j(g)
  - its own budget B_j(g)
  - its own model substrate
  - its own growth rate

Inter-prajna communication on same machine:
  cost(share) ≈ 0        -- same disk, negligible I/O
  cost(cross_verify) = cost(re-running drishthanta)
  δ_local = 0.8          -- higher trust for co-located prajna (same physical reality)
```

A prajna running on a local 7B model grows slowly — fewer agents, simpler hetu, narrower pervasion per epoch. A prajna running on a large model grows fast — denser hetu, better upanaya, wider pervasion. But the grammar is the same. The nyaya structure is the same. The verified truths are the same kind of truth regardless of which model produced them. A nigamana verified by a 7B model and cross-verified by Claude is no less true than one produced by Claude alone — it has been independently reproduced by two different intelligences.

---

## The Complete Swarm Model

Putting everything together:

```
Swarm = (G, I, B, Ω)

where:
  G = nyaya graph — directed graph (V = nyaya, E = shabda edges)
  I = collective intelligence — set of active nigamana
  B = budget allocation per generation
  Ω = dharma configuration — all tunable parameters

Per generation g:
  1. Agents spawned / reborn from B(g)
  2. Agents perceive — read code, see images, parse logs, inspect UI, sense
  3. Agents form hetu from perception
  4. Agents form paksha, upanaya, run drishthanta
  5. Nyaya formed — nigamana established or weight reduced
  6. Unreconciled nigamana identified → purification agents spawned
  7. Generation ends when B(g) exhausted or all agents die
  8. System state recorded:

     state(g) = {
       |G|           -- nyaya graph size
       K(g)          -- total verified knowledge
       Q(g)          -- average nigamana quality
       C(g)          -- resource coverage
       D(g)          -- reasoning depth
       U(g)          -- unreconciled count
       B_spent(g)    -- budget consumed
       GP(g)         -- good points awarded
     }
```

The system is correct when U(g) = 0. Not when all tests pass — when all tests pass AND all affected dependencies have been re-verified. The swarm's job is to maximize Intelligence(g) = (Q, C, D) under the budget constraint, while maintaining coherence U(g) = 0.
