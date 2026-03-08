---
title: Input-Output Graph Math
description: A full whitepaper treatment of how input becomes output through graph structure and explicit equations.
---

## Statement

This engine performs a deterministic transform from language input to structured graph computation/output.

It is not a hidden latent-state predictor. The stages, parameters, and equations are explicit and inspectable.

## 0. Formal objects

Let:

- $G=(V,E,R)$ be the typed multigraph.
- $V$ be nodes (concepts).
- $E$ be directed edges.
- $R$ be relation types (`swarupa`, `abheda`, `sthita`, `yukta`, `kriya`, `phala`, `janya`, `siddha`, `drishthanta`, `pratipaksha`).
- $q$ be an input sentence.

The system computes an output string $y$ through a staged transform $F$:

$$
y = F(q, G, \Theta)
$$

where $\Theta$ is not hidden model weights; it is explicit graph metadata + formulas.

## 1. Input decomposition

First, lexical decomposition:

$$
q \xrightarrow{\text{tokenise}} W=[w_1,\dots,w_n]
$$

Then graph-aware classification and folding:

$$
W \xrightarrow{\text{classify-fold}} T=\{(\text{raw},\text{class},\text{canonical})\}
$$

Classes include:

- `concept`
- `grammar`
- `number`
- `operator`

Unlike embedding pipelines, canonicalization is explicit via graph/setu and deterministic token operations.

## 2. Structured query extraction

From $T$, planner extraction computes:

$$
(\tau, B, I)
$$

where:

- $\tau$ = target concept/tantra candidate,
- $B$ = bindings (name/value assignments),
- $I$ = intents (`identity`, `origin`, `process`, `consequence`, `transmission`).

Intent extraction is lexical-rule based in tantra and then used as a structural switch for ranking/projection.

## 3. Node prior (structural satya)

Each node $v$ has a load-time structural prior:

$$
\sigma(v)=\text{raw\_satya}(v)
$$

with normalized factors:

$$
s=\frac{\text{sloka\_count}}{1+\text{sloka\_count}},\quad
e=\frac{\text{edge\_count}}{1+\text{edge\_count}},\quad
d=\frac{\text{type\_diversity}}{1+\text{type\_diversity}}
$$

and piecewise definition:

$$
\sigma(v)=
\begin{cases}
s\cdot0.5,& \text{if edge\_count}=0\\
(s\cdot e\cdot d)^{1/3},& \text{otherwise}
\end{cases}
$$

Interpretation:

- high sloka density = richer textual grounding,
- high edge density = stronger connectivity,
- high relation diversity = broader semantic participation.

## 4. Relation conductance: static base + dynamic query boost

Each relation type $r\in R$ has base conductance weight $w_r$ stored in visheshanam `.om` data.

At query time, seed-neighborhood relation frequency boosts this weight:

$$
f_r=\frac{\#(r\text{ in seed edges})}{\max(1,\#\text{seed edges})}
$$

$$
\kappa_r=w_r(1+f_r)
$$

This is critical: **weights are not purely static**. Base weights are declarative priors; effective flow is dynamic by query context.

## 5. Posterior relevance by PPR

Given seed distribution $s(v)$ (target + bindings), posterior scores iterate as:

$$
p_{t+1}(v)=\alpha s(v)+(1-\alpha)
\sum_{u\to v}\frac{p_t(u)\,\kappa_{rel(u,v)}}{\max(1,\text{out\_cond}(u))}
$$

with:

- $\alpha=0.30$,
- convergence by max delta threshold or iteration cap.

This computes query-specific relevance landscape over the same graph.

## 6. Query-structural depth policy

Search is not fixed BFS and not fixed PPR; it is blended by structural depth affinity:

$$
\phi=\operatorname{clamp}_{[0,1]}
\left(
\left(\text{binding\_density}\cdot\text{link\_ratio}\cdot\text{computational\_ratio}\right)^{1/3}
\right)
$$

Beam score at depth $d$:

$$
\text{depth\_score}=\frac{1}{d+1}
$$

$$
\text{blend}=ppr\cdot(1-\phi)+\text{depth\_score}\cdot\phi
$$

Behavioral regimes:

- $\phi\to1$: BFS-dominant (compute-focused, shallow path preference)
- $\phi\to0$: PPR-dominant (conceptual exploration)

## 7. Dual output channels

The orchestrator computes either:

1. **Computational output** (if a plan resolves and executes), or
2. **Conceptual output** (if compute is absent/suppressed by intent policy).

Formally:

$$
y =
\begin{cases}
\text{format-response}(\text{execute-plan}(\pi)),& \text{if compute branch selected}\\
\text{compose-answer}(\Pi_{I,D}(E)),& \text{otherwise}
\end{cases}
$$

where $\Pi_{I,D}$ is intent+domain projection.

## 8. Conceptual projection operator

For conceptual branch, outgoing triples are filtered by:

1. domain closure,
2. firstness tier,
3. structural content check.

Tier partition (intent-conditioned):

- `aadya`
- `anantara`
- `apara`
- `anuvritta`

Operational projection used now:

$$
\Pi_{I,D}(E)=E_{aadya}\cup E_{anantara}\cup \widetilde{E}_{apara}
$$

with $\widetilde{E}_{apara}$ constrained by `node-satya(target) > 0`, and `anuvritta` dropped.

## 9. Deterministic language composition

Projected triples are rendered by relation-specific clause mappings:

- `swarupa` -> `is`
- `abheda` -> `the same as`
- `sthita` -> `resting on`
- `yukta` -> `with`
- `kriya` -> `through`
- `phala` -> `yielding`
- `janya` -> `arising from`

This is explicit string algebra in tantra, not probabilistic decoding.

## 10. End-to-end transform summary

$$
q
\to W
\to T
\to (\tau,B,I)
\to \pi
\to
\begin{cases}
\text{compute}\to\text{formatted scalar/unit result},\\
\text{projected triples}\to\text{deterministic narrative}
\end{cases}
$$

This gives reproducibility, inspectability, and auditability.

## 11. Concrete numeric anchors (current engine)

Observed in runtime:

- `node-satya(force) = 0.890884`
- `node-satya(net-force) = 0.693361`
- `edge-weight(swarupa) = 0.9`
- `edge-weight(yukta) = 0.5`

These values directly affect conductance and conceptual filtering.

## 12. Why this matters

This architecture is suitable where explanation and control matter:

- scientific modeling,
- symbolic-numeric hybrid computation,
- robotics planning with explicit constraints,
- safety-sensitive deterministic inference.

Because the model state is explicit and equations are fixed, behavior can be inspected and corrected at data/logic level.

## 13. Worked numeric micro-derivation (force seed)

Take a simplified seed neighborhood for target `force` where relation counts include frequent `sthita`, `kriya`, and `yukta` edges.

Given base weights:

- $w_{swarupa}=0.90$
- $w_{yukta}=0.50$
- $w_{sthita}=0.80$

and empirical seed frequencies $f_r$ from seed-edge profile:

- $f_{swarupa}=\frac{1}{9}$
- $f_{yukta}=\frac{2}{9}$
- $f_{sthita}=\frac{2}{9}$

effective conductances are:

$$
\kappa_{swarupa}=0.90\left(1+\frac{1}{9}\right)=1.0
$$

$$
\kappa_{yukta}=0.50\left(1+\frac{2}{9}\right)=0.611\overline{1}
$$

$$
\kappa_{sthita}=0.80\left(1+\frac{2}{9}\right)=0.977\overline{7}
$$

Interpretation: the query context boosts dependencies (`sthita`) and keeps identity (`swarupa`) high, while looser association (`yukta`) remains lower.

## 14. Branch selection logic as algebra

Define:

- $C(q)$ = computational result candidate,
- $E(q)$ = error payload from compute branch,
- $I(q)$ = intent set,
- $A(q)$ = conceptual anuvada result.

Then effective output branch is:

$$
y(q)=
\begin{cases}
C(q),& C(q)\neq\varnothing \land \neg\text{error}(C)\\
E(q),& \text{real-error}(E) \land \text{identity}\notin I(q)\\
A(q),& \text{otherwise}
\end{cases}
$$

This explains why:

- `what is force` falls to conceptual branch,
- `force when mass is 10` surfaces missing-input compute error.

## 15. Determinism and reproducibility conditions

The output is deterministic under these conditions:

1. Same graph content (`.om`, `.tantra`, session graph files).
2. Same relation-axiom expansion result at load.
3. Same query string and runtime flags.
4. Same arithmetic and stopping thresholds.

Formally, if $(G,\Theta,q)$ are unchanged, output string $y$ is invariant.

## 16. Complexity sketch (engineering view)

Let:

- $|V|$ = nodes,
- $|E|$ = edges,
- $k$ = max PPR iterations,
- $b$ = beam width.

Then rough dominant costs per query are:

- PPR pass: $\mathcal{O}(k\cdot |E|)$
- beam expansion: bounded by candidate fanout and $b$ per depth layer
- composition: linear in projected triples.

Because $k$ and beam width are capped, behavior remains operationally stable.

## 17. Predictability vs black-box contrast (technical)

In this model:

- relation semantics are stored in data files,
- conductance transforms are explicit,
- scoring equations are fixed,
- composition templates are explicit.

So a disagreement in output can be traced to:

1. a graph fact,
2. a relation property,
3. a scoring path,
4. a composition rule.

This is materially different from hidden high-dimensional latent behavior where attribution is not direct.

## 18. Robotics applicability bridge

For robotics, a world model needs:

- explicit entities and constraints,
- explicit causal and dependency relations,
- inspectable planning dynamics,
- deterministic fallback on missing constraints.

The current graph+tantra architecture already provides these primitives:

- entities -> graph nodes,
- constraints -> `sthita` / `siddha` / `pratipaksha` relations,
- actions -> `kriya` relations and tantras,
- outcomes -> `phala` relations,
- reversible reasoning -> inverse/chain resolution with explicit error reporting.

Hence it is a strong substrate for explainable symbolic control layers.

## Source files

- `brahman/yantra/anuvada-ganana.tantra`
- `brahman/yantra/yantra-plan-extraction.tantra`
- `brahman/yantra/yantra-plan-resolution.tantra`
- `brahman/yantra/query-intents.tantra`
- `brahman/yantra/firstness-of-triple.tantra`
- `brahman/yantra/visheshanam-projection.tantra`
- `brahman/yantra/compose-answer.tantra`
- `brahman/yantra/format-response.tantra`
- `vyakarana/lib/proof_graph.ml`
- `vyakarana/lib/yantra_resolver.ml`
- `vyakarana/lib/yantra_pipeline_ops.ml`
- `vyakarana/lib/yantra_eval_primitives.ml`
