---
title: Executive Summary
description: Whitepaper overview of the Prabandam graph + tantra model.
---

## Claim

This engine is a first-principles computational model, not a statistical next-token predictor.

- Knowledge is explicit graph data.
- Semantics are explicit typed relations.
- Inference is explicit math.
- Output is explicit composition logic.

## Core architecture

1. **Claim graph** (`sangati`, `kosha`) stores concepts and typed edges.
2. **Computation layer** (`yantra`) encodes executable symbolic programs.
3. **Runtime** (`vyakarana/lib`) resolves queries and computes scores.

## Prior + posterior model

The node prior is structural:

$$
\sigma(n)=\text{raw\_satya}(n)
$$

Posterior relevance is query-conditioned PPR:

$$
p_{t+1}(v)=\alpha s(v)+(1-\alpha)\sum_{u\to v}\frac{p_t(u)\,\kappa_{rel(u,v)}}{\max(1,\text{out\_cond}(u))}
$$

with `alpha = 0.30`.

## Why this is open and predictable

- Relation weights live in `.om` data, not hidden model tensors.
- Query-time conductance is derived from seed neighborhood statistics.
- Search strategy is explicit (`depth_affinity` + beam blend).
- Every answer can be traced from input to emitted clause.

## Learning model

This system learns by structural accretion, not hidden-parameter retraining:

$$
\mathcal{K}_{t+1}=\mathcal{K}_t\oplus\Delta_t
$$

where $\Delta_t$ contains new/updated `.om` relations and `.tantra` programs.

So new capability can be introduced by explicit knowledge/program edits, then used immediately at runtime.

## Robotics relevance

The model is suitable for robotics reasoning because:

- world-state and constraints are explicit graph relations,
- planners are deterministic and inspectable,
- symbolic and numeric computation can coexist via tantras,
- safety-critical path selection can be audited.

## Source files

- `vyakarana/lib/proof_graph.ml`
- `vyakarana/lib/yantra_resolver.ml`
- `brahman/yantra/anuvada-ganana.tantra`
- `brahman/yantra/visheshanam-projection.tantra`
- `brahman/kosha/yantra/visheshanam/visheshanam-swarupa.om`
