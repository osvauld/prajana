# Graded Morphisms — Operation Node Enrichment

**Status**: Design complete. No implementation yet.
**Depends on**: math/graph/ sub-varga (phase 2.9 step 10)
**Part of**: engine-tantra-migration.md step 6

---

## What this is

Operation nodes in the kosha currently declare WHAT they are (`number-varga-karma`,
`power-kriya`) but not their **grade** in the visheshanam ring and not their
**inverse**. Without grade and inverse:
- Tantras cannot derive identities like `sqrt(x²) = x` from the graph
- Tantras cannot route inverse computation from a single edge traversal
- Scene understanding cannot follow `pratipaksha` edges to reverse a computation

This plan adds `degree:` to shabda and `pratipaksha` edges to operation nodes.

---

## The ring structure (recap)

The visheshanam ring already has `ring-op:mul` on `kriya` edges — meaning kriya
edges compose multiplicatively. Composing two operations multiplies their grades.
When the product of grades = 1, the composition is the identity (the operations
are inverses).

```
degree(square) × degree(sqrt) = 2 × 1/2 = 1  →  identity
degree(log) × degree(exp)    = -1 × 1   = wait, log∘exp = id means grades cancel
```

For group-theoretic operations (SO(3), etc.) the grade is the group element type.
Composing n SO(3) elements gives another SO(3) element. Inverse = transpose.

---

## Encoding

Two additions per operation node:

1. **`degree:VALUE`** in shabda — the grade this operation contributes when traversed
2. **`X-pratipaksha`** edge — points to the inverse operation node

The tantra reads:
```
degree-a = to-number (shabda node-a "degree")
degree-b = to-number (shabda node-b "degree")
composed = mul degree-a degree-b    -- 1.0 = identity
```

---

## Number/algebra operations

| Node | degree: | pratipaksha |
|---|---|---|
| `square` | 2 | `sqrt` |
| `sqrt` | 1/2 | `square` |
| `addition` | +1 (additive) | `subtraction` |
| `subtraction` | -1 (additive) | `addition` |
| `multiplication` | ×N | `division` |
| `division` | ×(1/N) | `multiplication` |
| `logarithm` | log | `power` (exp base) |
| `power` | exp | `logarithm` |
| `negation` | -1 | `negation` (self-inverse) |
| `inverse` (matrix) | -1 | `inverse` (self-inverse) |

---

## Geometry / linear algebra operations

| Node | degree: | pratipaksha |
|---|---|---|
| `rotation-matrix` | SO3-element | `rotation-matrix` (transpose) |
| `homogeneous-transform` | SE3-element | `homogeneous-transform` (inverse) |
| `projection` | rank-reduce | none (not invertible in general) |
| `fourier-transform` | freq-domain | `fourier-transform` (inverse FT) |
| `derivative` | d/dx | `antiderivative` |
| `antiderivative` | ∫dx | `derivative` |

---

## Kinematic chain operations

| Node | degree: | pratipaksha |
|---|---|---|
| `forward-kinematics` | SO3×ℝ³-element | `inverse-kinematics` |
| `inverse-kinematics` | joint-space | `forward-kinematics` |
| `rotation-matrix` | SO3-element | `rotation-matrix` (transpose) |

---

## Calculus operations

| Node | degree: | pratipaksha |
|---|---|---|
| `derivative` | d/dx | `antiderivative` |
| `antiderivative` | ∫dx | `derivative` |
| `fourier-transform` | ℱ | `fourier-transform` (inverse) |

---

## What pratipaksha enables for scene understanding

Once pratipaksha edges exist:

```
-- a tantra that walks backward from a known output to find what inputs produced it:
tantra infer-inputs-from-output
  inputs
    output-node  string
    output-val   any
  let
    inverse-op = first (walk output-node "pratipaksha")
    inputs     = walk output-node "janya"
    result     = apply-op inverse-op [output-val]
  return
    result  any
done
```

This is scene understanding: given the end-effector position (phala), walk
`pratipaksha` to `inverse-kinematics`, apply it, get joint angles (janya).
Same tantra works for any domain where pratipaksha edges are declared.

---

## Implementation steps

1. Add `degree:` shabda field to each operation node listed above
2. Add `X-pratipaksha` compound edge token to each operation node
3. Verify `pratipaksha` is a registered visheshanam dimension
   (check `brahman/kosha/yantra/visheshanam/visheshanam-ring.om`)
4. Write `compose-degrees.tantra` — given two nodes, multiplies their degrees
5. Write `is-identity-composition.tantra` — checks if composed degree = 1
6. Run regression (49/52)

---

## Key files

```
brahman/kosha/math/number/operations/    square, sqrt, addition, subtraction, etc.
brahman/kosha/math/calculus/operations/  derivative, antiderivative, fourier-transform
brahman/kosha/math/geometry/operations/  rotation-matrix, homogeneous-transform
brahman/kosha/3d/kinematic-chain.om     forward-kinematics, inverse-kinematics refs
brahman/kosha/yantra/visheshanam/visheshanam-ring.om  check pratipaksha registered
brahman/yantra/compose-degrees.tantra    new
brahman/yantra/is-identity-composition.tantra  new
```
