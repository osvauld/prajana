---
title: Proof-Graph Running Examples
description: Executable examples showing input, graph behavior, and output determinism.
---

## Purpose

This chapter records real runs of the engine to demonstrate that outputs are produced from explicit graph and tantra mechanics.

All examples were run with:

```bash
./vyakarana/_build/default/bin/vyakarana.exe
```

from repository root.

## Example A — Conceptual query (`what is force`)

Command:

```bash
echo "what is force" | ./vyakarana/_build/default/bin/vyakarana.exe
```

Observed output (core lines):

```text
in physics:
force is net-force, the same as centripetal-force, the same as torque, resting on mass, resting on acceleration, with physics, with drag-force, with electric-field, E-field, with friction-force, with magnetic-field, B-field, with newton, with normal-force, with nuclear-force, with potential-energy, with spring-force, with strong-nuclear-force, with tension-force, with weak-nuclear-force, with acceleration, resting on physics.
  net-force is force, with physics, resting on motion, resting on physics.
  centripetal-force the same as force, with physics, resting on orbit, with motion, resting on physics.
  torque the same as force, resting on force, with angular-acceleration, with Nm, N-m, newton-metre, newton-meter, with moment-of-inertia, with angular-momentum, resting on physics.
```

Interpretation:

- This is conceptual branch output.
- Triple projection and composition are visible in relation-language phrases (`is`, `the same as`, `resting on`, `with`).
- Domain closure keeps response in physics neighborhood.

Solver note:

- A tantra named `force` exists but requires missing inputs.
- Because intent includes `identity`, compute error is suppressed and conceptual anuvada is selected.

## Example B — Missing-input computational query

Command:

```bash
echo "force when mass is 10" | ./vyakarana/_build/default/bin/vyakarana.exe
```

Observed output:

```text
cannot compute tantra 'force' exists but missing inputs: acceleration.
```

Interpretation:

- Plan resolution found `force` tantra.
- Required input set is incomplete.
- Since this is not an identity query, error is surfaced (not suppressed).

Solver note:

- This follows branch rule: real missing-input compute errors are shown for non-identity intents.

## Example C — Fully-bound computation (`kinetic energy`)

Command:

```bash
echo "kinetic energy when mass is 5 and velocity is 6" | ./vyakarana/_build/default/bin/vyakarana.exe
```

Observed output:

```text
kinetic-energy is 90 joule. computed by kinetic-energy.
```

Interpretation:

- Direct computational path selected.
- Numeric result and unit are formatted deterministically.

Math check:

$$
E_k = \frac{1}{2}mv^2 = \frac{1}{2}\cdot5\cdot6^2 = 90
$$

## Example D — Cross-domain conceptual query (`what is life`)

Command:

```bash
echo "what is life" | ./vyakarana/_build/default/bin/vyakarana.exe
```

Observed output (core lines):

```text
in biology:
life with nitrogen, with oxygen, with cell, resting on dna, resting on gene, with protein, with enzyme, resting on biology.
directed-will (iccha) present in the-single-cell, gene, dna; absent in inert.
```

Interpretation:

- Domain routing reaches biology conceptual neighborhood.
- Output includes explicit relation clauses and iccha bridge statement.

## Example E — Runtime score probes

Commands:

```bash
echo "EVAL node-satya force" | ./vyakarana/_build/default/bin/vyakarana.exe
echo "EVAL node-satya net-force" | ./vyakarana/_build/default/bin/vyakarana.exe
echo "EVAL edge-weight swarupa" | ./vyakarana/_build/default/bin/vyakarana.exe
echo "EVAL edge-weight yukta" | ./vyakarana/_build/default/bin/vyakarana.exe
```

Observed values:

```text
node-satya(force) = 0.890884
node-satya(net-force) = 0.693361
edge-weight(swarupa) = 0.9
edge-weight(yukta) = 0.5
```

Interpretation:

- Node prior and relation weights are query-visible.
- These values influence traversal and conceptual projection.

## Determinism note

For the same graph state and same input, the pipeline returns the same output because:

1. tokenization/classification are deterministic,
2. score equations are fixed,
3. search ordering is explicit,
4. composition is rule-based.

## Reproducibility protocol

To validate deterministic behavior experimentally:

1. Run the same command twice and diff output.
2. Restart process and rerun to ensure no hidden session drift.
3. Change one input binding and observe only local output change.
4. Probe `node-satya` and `edge-weight` values to confirm scoring anchors.

Expected result: identical outputs for identical inputs under unchanged graph state.

## Source files

- `brahman/yantra/anuvada-ganana.tantra`
- `brahman/yantra/format-response.tantra`
- `brahman/yantra/visheshanam-projection.tantra`
- `brahman/yantra/compose-answer.tantra`
- `vyakarana/lib/proof_graph.ml`
- `vyakarana/lib/yantra_resolver.ml`
- `vyakarana/lib/yantra_pipeline_ops.ml`
- `vyakarana/lib/yantra_eval_primitives.ml`
