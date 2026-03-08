---
title: System Overview
description: End-to-end architecture of the graph + tantra engine.
---

## Layers

- `brahman/sangati`: root and relational ontology claims.
- `brahman/kosha`: domain concept libraries and relation facts.
- `brahman/yantra`: executable tantra programs for computation and composition.
- `vyakarana/lib`: runtime engine (parser, resolver, scorer, evaluator).

## Execution path

Input sentence follows this path:

1. Tokenize + classify (`concept`, `grammar`, `number`, `operator`).
2. Extract target + bindings from classified tokens.
3. Resolve tantra plan (direct, inverse, chain, or error).
4. Execute computational plan or fall back to conceptual anuvada.
5. Compose final response from projected graph triples.

This is orchestrated by `brahman/yantra/anuvada-ganana.tantra`.

## Scoring model at a glance

The graph uses a prior+posterior structure:

$$
\sigma(n)=\text{raw\_satya}(n)
$$

$$
p_{t+1}(v)=\alpha s(v)+(1-\alpha)\sum_{u\to v}\frac{p_t(u)\,\kappa_{rel(u,v)}}{\max(1,\text{out\_cond}(u))}
$$

Where `alpha = 0.30`.

## Why this is predictable

- Relation properties and base weights are data (`.om`), not hidden constants.
- Equations are explicit in `proof_graph.ml` and resolver scoring logic.
- Intent rank tiers are explicit in `firstness-of-triple.tantra`.
- Output clauses are explicit in `compose-answer.tantra`.

## Source files

- `vyakarana/lib/proof_graph.ml`
- `vyakarana/lib/yantra_resolver.ml`
- `vyakarana/lib/yantra_pipeline_ops.ml`
- `brahman/yantra/anuvada-ganana.tantra`
- `brahman/yantra/compose-answer.tantra`
