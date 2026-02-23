# Dharma: The Configuration of the Swarm

**Dharma** (धर्म — law, order, the way things work) is the configuration layer of Agent-X. Every tunable parameter in the system — weight constants, thresholds, costs, optimization weights — is declared in the dharma.

Dharma is **versionable and branchable**. Different dharma configurations produce different swarm behaviors from the same grammar and the same codebase. You branch the dharma, run the same swarm, and compare which configuration produces better intelligence. The grammar is fixed. The logic is fixed. The dharma is the experiment.

---

## Weight Update Constants

In plain language: α (alpha) is how much confidence goes up when you find confirming evidence — set to 0.05, meaning a 5% boost each time. β (beta) is how much confidence goes down when you find a counter-example — set to 0.10, meaning a 10% drop. Counter-evidence hits harder than confirmation helps. This is intentional — it is easier to break a truth than to build one. Confidence can never go above 1.0 (certainty) or below 0.0 (nothing).

```
α  = 0.05     -- confirmation factor: how much a confirming hetu step raises weight
β  = 0.10     -- contradiction factor: how much a counter-case lowers weight
```

On confirming hetu step: `w_new = min(w_old · (1 + α), 1.0)`
On counter-case found:   `w_new = max(w_old · (1 - β), 0.0)`
On drishthanta pass:     `w_new = min(w_old · (1 + α), 1.0)`
On drishthanta fail:     `w_new = max(w_old · (1 - β), 0.0)`

---

## Pramana Weight Scaling

Different evidence types contribute differently to weight. These factors scale the base α for each pramana type:

```
α_pratyaksha  = 1.0 · α     -- direct observation: full weight (read, found, saw)
α_anumana     = 0.6 · α     -- inference: weaker (derived)
α_upamana     = 0.8 · α     -- comparison: moderate (compared)
α_shabda      = w(cited Γ)  -- testimony: inherited weight of the cited nigamana
```

A hetu built entirely from anumana (inference) without pratyaksha (direct observation) contributes less weight per step. This is configurable — different domains may value inference more or less.

---

## Threshold Values

```
θ_claim    = 0.80     -- minimum weight to be promoted from nigamana to claim
θ_truth    = 0.90     -- minimum weight to be promoted from claim to truth
θ_satya    = 0.99     -- minimum weight to approach satya
θ_retract  = 0.25     -- minimum weight before nigamana is retracted
θ_stale    = 0.30     -- minimum weight before a knows block is considered stale
```

---

## Generation Thresholds

```
G_min_claim  = 2      -- minimum generations held to be promoted to claim
G_min_truth  = 5      -- minimum generations held to be promoted to truth
```

---

## Cost Constants

Every action has a cost in budget units:

```
c_s  = 0.10     -- cost to spawn an agent
c_r  = 0.01     -- cost to read a resource (code file)
c_v  = 0.02     -- cost to perceive a visual resource (image, screenshot)
c_h  = 0.02     -- cost to form a hypothesis (allocate reasoning)
c_i  = 0.05     -- cost to invoke another agent (issue a call)
c_a  = 0.01     -- cost to produce an answer
c_d  = 0.10     -- cost to run a drishthanta (execute a test)
```

Budget per generation:

```
B(g) = 20.0     -- total budget available per generation (configurable)
```

---

## Optimization Weights

In plain language: the swarm tries to optimize three things at once — total verified knowledge, how much of the system has been explored, and how rigorous the agents were. These three weights (λ₁, λ₂, λ₃) control how much the swarm cares about each one. λ₁ = 1.0 means verified knowledge is the top priority. λ₂ = 0.5 means coverage matters but half as much. λ₃ = 0.3 means rigor matters but less than the other two. Changing these weights changes how the swarm behaves — more λ₂ means it explores broadly, more λ₁ means it digs deep.

The relative importance of the three optimization objectives:

```
λ₁ = 1.0      -- weight on total verified knowledge: Σ w(Γᵢ)
λ₂ = 0.5      -- weight on resource coverage: Σ priority(r) · saturation(r)
λ₃ = 0.3      -- weight on epistemic rigor: Σ good_points
```

---

## Good Points Values

Per-action reward for epistemic rigor:

```
gp_hypothesis_formed       = 3
gp_process_traced          = 4
gp_proof_written           = 2
gp_test_passed             = 5
gp_test_failed_cleanly     = 2
gp_truth_promoted          = 8
gp_unexpected_reported     = 3
gp_impact_traced           = 4
gp_reconcile_completed     = 3
gp_purification_completed  = 5
gp_process_composed        = 6
```

---

## Fragility Constraint

```
d_max = 10     -- maximum allowed shabda dependency depth
```

Nyaya with shabda chains deeper than d_max raise a warning. This is a soft constraint — deep chains are not rejected, but the swarm prefers shallower composition when possible.

---

## Initial Weight

When a nigamana is first established (drishthanta passes for the first time):

```
w₀ = 0.70     -- initial weight for a new nigamana
```

This reflects that a single passed test is real evidence but narrow pervasion. The starting point from which hetu accumulation raises weight across generations.

---

## Versioning

A dharma configuration is identified by a version string:

```
dharma "agent-x-v1"
  α 0.05
  β 0.10
  θ_claim 0.80
  θ_truth 0.90
  θ_satya 0.99
  θ_retract 0.25
  θ_stale 0.30
  ...
```

Branching the dharma:

```
dharma "agent-x-v2-aggressive"
  α 0.08          -- faster weight gain
  β 0.05          -- slower weight loss
  θ_claim 0.75    -- easier promotion
  ...
```

Run both configurations against the same codebase. Compare Intelligence(g) = (Q, C, D) after the same number of generations. The configuration that produces higher quality, wider coverage, and deeper reasoning is the better dharma.

The math is the same. The grammar is the same. The constants are the experiment.
