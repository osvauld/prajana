---
title: First Principles Model
description: How understanding is grounded in root claims, relation algebra, and equations.
---

## Root claims are the base

The model starts from explicit root nodes, not latent weights:

- `brahma` (`brahman/sangati/brahma.om`)
- `om` (`brahman/sangati/om.om`)
- `spanda` (`brahman/sangati/spanda.om`)
- `karma` (`brahman/sangati/karma.om`)
- `brahmam` (`brahman/sangati/brahmam.om`)
- `brahman` (`brahman/sangati/brahman.om`)

All higher reasoning rides on these claims and their typed relations.

## Relation adjectives (visheshanam)

These are first-class algebraic objects with properties and weights in data:

- `swarupa`, `abheda`, `sthita`, `yukta`, `kriya`, `phala`, `janya`, `siddha`, `drishthanta`, `pratipaksha`

Base conductance values come from:

- `brahman/kosha/yantra/visheshanam/visheshanam-*.om`

## Not static-only: dynamic by query

Base relation weight is static prior:

$$
w_r = \text{vp\_satya\_weight}(r)
$$

Effective conductance is dynamic:

$$
\kappa_r = w_r\left(1 + \frac{\#(r\text{ in seed edges})}{\max(1,\#\text{seed edges})}\right)
$$

So each query changes edge-flow emphasis according to its own graph neighborhood.

## Depth behavior is also structural

Search is not fixed BFS or fixed PPR. It is blended using `depth_affinity`:

$$
\text{blend}=ppr\cdot(1-\phi)+\frac{1}{d+1}\cdot\phi
$$

- `phi = 1`: BFS-dominant (compute-style query)
- `phi = 0`: PPR-dominant (concept-style query)

## Intent-conditioned projection

For conceptual response, triples are projected by firstness tiers:

- `aadya`
- `anantara`
- `apara`
- `anuvritta`

`visheshanam-projection.tantra` applies domain closure + tier filtering before language composition.

## Source files

- `brahman/sangati/brahma.om`
- `brahman/sangati/om.om`
- `brahman/sangati/spanda.om`
- `brahman/sangati/karma.om`
- `brahman/sangati/brahmam.om`
- `brahman/sangati/brahman.om`
- `brahman/kosha/yantra/visheshanam/visheshanam-swarupa.om`
- `vyakarana/lib/proof_graph.ml`
- `vyakarana/lib/yantra_resolver.ml`
- `brahman/yantra/firstness-of-triple.tantra`
- `brahman/yantra/visheshanam-projection.tantra`
