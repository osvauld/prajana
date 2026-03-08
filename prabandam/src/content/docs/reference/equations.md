---
title: Equations
description: Full mathematical specification of scoring, approximation, and intensity used by the graph engine.
---

## Why this page exists

Yes: approximation and intensity are represented mathematically in this system.

They are not informal tuning words. They are explicit transforms over graph structure.

## 0) Notation

- $G=(V,E,R)$: typed directed multigraph
- $v\in V$: node
- $e=(u,r,v)\in E$: edge with relation type $r\in R$
- $R$: set of visheshanam relations
- $\sigma(v)$: structural prior (`raw_satya`)
- $w_r$: base relation weight (`vp_satya_weight`)
- $f_r$: seed-local relation frequency
- $\kappa_r$: effective conductance of relation $r$
- $p_t(v)$: posterior relevance at iteration $t$
- $\alpha$: restart probability (`0.30`)
- $\phi$: depth affinity
- $d$: search depth
- $I$: intent set
- $D$: seed-domain set

## 1) Structural prior (node-level intensity)

The first node intensity is structural, not query-dependent:

$$
\sigma(v)=\text{raw\_satya}(v)
$$

with:

$$
s=\frac{\text{sloka\_count}(v)}{1+\text{sloka\_count}(v)},\quad
e=\frac{\text{edge\_count}(v)}{1+\text{edge\_count}(v)},\quad
d=\frac{\text{type\_diversity}(v)}{1+\text{type\_diversity}(v)}
$$

$$
\sigma(v)=
\begin{cases}
s\cdot 0.5,& \text{if edge\_count}(v)=0\\
(s\cdot e\cdot d)^{1/3},& \text{otherwise}
\end{cases}
$$

Interpretation: this is base epistemic intensity from local structure.

## 2) Relation conductance (edge-level intensity)

Base relation intensity is data-defined:

$$
w_r = \text{vp\_satya\_weight}(r)
$$

Query-conditioned boost:

$$
f_r=\frac{\#\{e\in E_{seed}:rel(e)=r\}}{\max(1,|E_{seed}|)}
$$

$$
\kappa_r=w_r(1+f_r)
$$

So edge intensity is dynamic despite static base weights.

## 3) Posterior propagation (global relevance intensity)

PPR recurrence:

$$
p_{t+1}(v)=\alpha s(v)+(1-\alpha)\sum_{u\to v}
\frac{p_t(u)\,\kappa_{rel(u,v)}}{\max(1,\text{out\_cond}(u))}
$$

Stop criterion:

$$
\Delta_t=\max_{v\in V}|p_{t+1}(v)-p_t(v)|,
\qquad
\Delta_t<10^{-3}
$$

or iteration cap reached.

## 4) Matrix form (compact)

Define weighted transition matrix $M$ with:

$$
M_{uv}=\frac{\kappa_{rel(u,v)}}{\max(1,\text{out\_cond}(u))}
\quad\text{for edges }u\to v,
$$

and $M_{uv}=0$ otherwise.

Then:

$$
\mathbf{p}_{t+1}=\alpha\mathbf{s}+(1-\alpha)M^T\mathbf{p}_t
$$

Fixed-point equation:

$$
\mathbf{p}^*=\alpha\mathbf{s}+(1-\alpha)M^T\mathbf{p}^*
$$

$$
\Rightarrow\;
\left(I-(1-\alpha)M^T\right)\mathbf{p}^*=\alpha\mathbf{s}
$$

## 5) Approximation operators used in practice

The runtime uses explicit approximations for bounded compute:

### 5.1 Iterative approximation of fixed point

Instead of closed-form inversion, the solver uses iterative approximation:

$$
\mathbf{p}^{(k)} \to \mathbf{p}^*
$$

with finite cap $k\le 50$.

### 5.2 Beam approximation of search frontier

Let $\mathcal{S}_d$ be all states at depth $d$. Runtime keeps top-$b$ by score:

$$
\widetilde{\mathcal{S}}_d = \operatorname{TopB}_b(\mathcal{S}_d,\text{blend})
$$

This is an explicit approximation of full frontier expansion.

### 5.3 Conceptual projection approximation

Let $E_{out}(v)$ be all outgoing triples from a seed/root node. Conceptual response uses projected subset:

$$
\Pi_{I,D}(E_{out})=E_{aadya}\cup E_{anantara}\cup\widetilde{E}_{apara}
$$

with domain closure and satya filters; `anuvritta` tier is truncated.

This is approximation-by-structured-subspace, not random pruning.

## 6) Depth-policy blending

Depth affinity:

$$
\phi=\operatorname{clamp}_{[0,1]}\left(
\left(\text{binding\_density}\cdot\text{link\_ratio}\cdot\text{computational\_ratio}\right)^{1/3}
\right)
$$

Depth score:

$$
\text{depth\_score}(d)=\frac{1}{d+1}
$$

Blend objective:

$$
\text{blend}=ppr\cdot(1-\phi)+\text{depth\_score}\cdot\phi
$$

This is the explicit mathematical model for exploration-vs-exploitation intensity.

## 7) Branch-selection function

Define:

- $C(q)$: compute result payload
- $Err(q)$: compute error payload
- $Id(q)$: indicator that `identity` intent is present
- $A(q)$: conceptual anuvada payload

Then:

$$
Y(q)=
\begin{cases}
C(q),& \text{if compute succeeded}\\
Err(q),& \text{if real missing-input error and }\neg Id(q)\\
A(q),& \text{otherwise}
\end{cases}
$$

This is why `what is force` and `force when mass is 10` diverge cleanly.

## 8) How equations are solved in runtime

Given extracted target $\tau$ and bindings $B$, the runtime does not invoke a generic CAS.
It runs a graph-aware planner with three explicit solve modes.

### 8.1 Direct solve (forward evaluation)

If inputs of a tantra $T$ are satisfied by $B$ (plus constants), execute:

$$
\text{out} = T(\text{input assignments})
$$

This is standard forward numeric evaluation over tantra `let` expressions.

### 8.2 Inverse solve (single unknown)

If output and all but one input are known, runtime attempts symbolic inversion over tantra let-chain:

$$
T(x_1,\dots,x_n)=y,
\quad
x_k\text{ unknown}
$$

It builds an inverse plan using the internal equation chain (`invert_chain`) and solves for $x_k$.

### 8.3 Chain solve (multi-step derivation)

If direct/inverse cannot finish in one tantra, solver composes steps:

$$
B_0 \xrightarrow{T_1} B_1 \xrightarrow{T_2} B_2 \xrightarrow{\cdots} B_m
$$

until target binding appears or depth/beam limits are reached.

## 9) Solve-path scoring during chain search

Candidate expansions are scored with blended objective:

$$
\text{score}(state)=ppr\cdot(1-\phi)+\frac{1}{d+1}\cdot\phi
$$

with beam truncation:

$$
\widetilde{\mathcal{S}}_d=\operatorname{TopB}_b(\mathcal{S}_d,\text{score})
$$

This yields a bounded approximate search over equation-composition space.

## 10) Approximation and intensity are explicit

- **Approximation** appears as finite-iteration PPR, beam truncation, and projection subspace selection.
- **Intensity** appears as $\sigma(v)$ (node prior), $w_r$ (relation base intensity), $\kappa_r$ (query-conditioned edge intensity), and $p(v)$ (posterior relevance intensity).

So both are mathematical operators in the engine, not narrative labels.

## 11) Runtime intensity probes (observed)

Observed by direct evaluator calls:

$$
\sigma(\text{force})=0.890884,
\qquad
\sigma(\text{net-force})=0.693361
$$

$$
w_{swarupa}=0.9,
\qquad
w_{yukta}=0.5
$$

These values are not hidden; they are query-visible.

## 12) Determinism claim (engineering form)

For fixed graph state and identical runtime configuration:

$$
(G,\Theta,q)=(G',\Theta',q')\implies Y(q)=Y'(q')
$$

subject to identical numeric arithmetic environment.

## 13) Source files

- `vyakarana/lib/proof_graph.ml`
- `vyakarana/lib/yantra_resolver.ml`
- `vyakarana/lib/yantra_eval_primitives.ml`
- `brahman/yantra/visheshanam-projection.tantra`
- `brahman/yantra/anuvada-ganana.tantra`
