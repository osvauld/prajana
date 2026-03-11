# Graph-Native Computation Model

**Status**: Design complete. No implementation yet.
**Feeds into**: engine-tantra-migration.md steps 6-7, graph-computation-tantras.md

---

## Core insight

The **expression** is already a graph walk — the tantra AST is a tree and
evaluating it IS traversal. `add a b` walks `Call → [Var a, Var b] → values`.

The **execution** of input → output is also a graph walk: follow `janya` edges
(what feeds in) through `kriya` edges (what operation) to `phala` edges (what
comes out).

Both are the same thing. Right now tantras **duplicate structure the graph
already encodes**. The goal: **the proof graph IS the expression tree**. Walking
it from `janya` through `kriya` to `phala` is computation.

---

## The two layers

| Layer | What it expresses | How |
|---|---|---|
| `.om` node | What the concept IS — its structure, role, inverse | Edges: kriya/janya/phala/pratipaksha + degree: in shabda |
| `.tantra` | How to instantiate it with actual values | Reads edges, binds values, dispatches |

The `.om` is the semantic index. The `.tantra` is the value binder. Computation
is the intersection — values flowing through the graph's declared structure.

---

## Operation nodes as graded morphisms

Each operation node carries its **grade** in the visheshanam ring via `degree:`
in shabda. Composing operations = multiplying grades (ring-op:mul on kriya edges).
Inverse operations are linked via `pratipaksha` edges.

```
-- square.om
kosha square
  "number-varga-karma"
  "power-kriya"
  "sqrt-pratipaksha"
  shabda square / exponent-2; degree:2
done

-- sqrt.om
kosha sqrt
  "number-varga-karma"
  "power-kriya"
  "square-pratipaksha"
  shabda sqrt / exponent-half; degree:1/2
done
```

Walking `x → [square, degree:2] → x² → [sqrt, degree:1/2] → x` and multiplying
grades gives `2 × 1/2 = 1` — the ring identity. `sqrt(x²) = x` is derived by
graph walk, not hardcoded.

Full list of operation nodes that need `degree:` and `pratipaksha`: see
`graded-morphisms.md`.

---

## Worked example: kinematic chain

```
revolute-joint.om
  rotation-matrix-kriya   -- its operation IS rotation-matrix
  angle-janya             -- angle feeds in
  SO3-swarupa             -- lives in the rotation group
  degree:SO3-element      -- grade in the ring

kinematic-chain.om
  composition-kriya       -- operation: compose transforms
  revolute-joint-vishesa  -- made of revolute joints
  dag-swarupa             -- it IS a DAG

forward-kinematics.om
  matrix-multiplication-kriya  -- multiply all transforms
  kinematic-chain-janya        -- chain feeds in
  end-effector-phala           -- produces position
```

Walking the graph:

```
walk "forward-kinematics" "kriya"        → [matrix-multiplication]
walk "kinematic-chain" "vishesa"         → [revolute-joint] × n
walk "revolute-joint" "kriya"            → [rotation-matrix]
walk "revolute-joint" "janya"            → [angle]
```

Following those edges in order gives `T = rotation-matrix(θ₁) × rotation-matrix(θ₂) × …`.
The walk IS the computation.

Tantra that executes this (no hardcoded joint types):

```
tantra execute-kinematic-chain
  inputs
    node    string
    values  list
  let
    op       = walk node "kriya"
    joints   = walk (first (walk node "janya")) "vishesa"
    joint-op = walk (first joints) "kriya"
    matrices = map values (fn θ -> apply joint-op θ)
    result   = reduce matrices (fn a b -> mat-mul a b)
  return
    result  any
done
```

---

## Scene understanding = backward graph walk

Scene understanding (text → structure → computation) is the **same graph walk
in reverse**. The text gives you the `phala` (observed / described) and the
system walks backward through `pratipaksha` edges to find the `janya` (inputs):

```
forward-kinematics  →  pratipaksha  →  inverse-kinematics
inverse-kinematics  →  jacobian-pseudoinverse-kriya
                    →  angle-phala
```

**One graph encodes both computation and understanding.** The scene extractor
and the physics executor traverse the same structure in opposite directions.
No separate hardcoded extraction logic — `pratipaksha` edges carry the inverse
relationship. The same applies to every domain: physics, sangeetham, biology.

---

## Why tantras become thin

Currently tantras are dense because they re-declare knowledge the graph holds:
domain membership, input/output types, operation classification, node-name
dispatch tables.

With graph-native computation:
- `walk node "kriya"` replaces all `cond (eq node "add") (eq node "mul") ...` chains
- `walk node "janya"` replaces hardcoded input-type lists
- `walk node "pratipaksha"` replaces hardcoded inverse tables
- `ancestors-of node` replaces domain membership checks

Generic dispatch tantra:

```
tantra compute-from-node
  inputs
    node    string
    values  list
  let
    op     = first (walk node "kriya")
    result = apply-op op values
  return
    result  any
done
```

One tantra. No name lists. The graph routes everything.

Full tantra specs: see `graph-computation-tantras.md`.
