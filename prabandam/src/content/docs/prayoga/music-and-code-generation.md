---
title: Music + Code Generation
description: How the graph emits Strudel music and source code artifacts.
---

## Principle

Generation is graph-driven, not hardcoded by domain tables.

`prayoga.ml` states this directly: the graph holds domain knowledge and code only walks/composes.

## Music generation path

Main files:

- `vyakarana/lib/prayoga_strudel.ml`
- `vyakarana/lib/anuvada.ml`

Data sources via shabda maps:

- `swara-to-strudel`
- `ornament-to-strudel`
- `strudel`
- `music-ir`

The engine maps concept/ornament structure to emitted Strudel stacks and optional `music_ir` payload.

### Emission model

If `S` is seed concept set and `W` is walk path, the emitted layer stack is a deterministic function:

$$
\text{strudel\_program} = F(\text{shabda maps}, S, W, \text{input tokens})
$$

No stochastic sampling step is required.

## Code generation path

Main files:

- `vyakarana/lib/anuvada.ml` (OCaml emission helpers)
- `vyakarana/lib/prayoga.ml` (relation-role driven composition)

Generation uses relation semantics:

- `swarupa` -> declaration/type context
- `kriya` -> action body
- `sthita` -> dependencies
- `phala` -> output/return
- `yukta` -> associated parameters

The role map is explicit and inspectable.

## Programming with tantra

A tantra is an executable symbolic spec:

1. Declare typed inputs.
2. Define symbolic math in `let`.
3. Return typed output + unit.

Example pattern:

$$
f = m\cdot a
$$

is encoded as a tantra (e.g. force), resolved from graph concepts + bindings, then executed.

## Verify

- Run with `+strudel` / `+music` / `+prayoga` flags to inspect generated artifacts.
- Compare outputs from same input twice: deterministic generation should match.

## Source files

- `vyakarana/lib/prayoga.ml`
- `vyakarana/lib/prayoga_strudel.ml`
- `vyakarana/lib/anuvada.ml`
- `vyakarana/lib/socket.ml`
