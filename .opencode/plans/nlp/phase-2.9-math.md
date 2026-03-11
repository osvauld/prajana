# Phase 2.9 — Math Kosha Full Restructure

**Status**: NOT YET STARTED. Next active phase.

**Regression baseline**: 49/52 passing. Do not break further.

---

## Overview

Migrate `brahman/kosha/math/` from flat files into a subdir hierarchy. Add four new
sub-vargas. Add ~15 missing nodes. Upgrade CS with `information/` subdir.
Fold in Phase 2.7 (engine move) and Phase 2.8 (Collatz migration).

---

## Edge vocabulary (math — distinct from physics)

Math uses three subdir types with corresponding edge suffixes:

| subdir | edge suffix | meaning |
|---|---|---|
| `structures/` | `X-varga-vishesa` | leaf IS a particular of that structural class |
| `properties/` | `X-varga-lakshana` | leaf IS a characterising property/axiom of that class |
| `operations/` | `X-varga-karma` | leaf IS an operation/map within that class |

The `lakshana` suffix is new and math-specific. Properties/axioms are not quantities
(subanta) nor processes (tinanta). They are characterising marks that hold over structures.

---

## Preparatory changes

### `math-varga.om` — thin it

Remove:
- `subanta-swarupa` — math has structures/properties/operations, not subanta/tinanta
- Any `domain-math-sthita` on individual leaves (use varga-vishesa instead)

### `domain-math.om` — thin it

Remove the 40+ flat `yukta` edges listing every math concept. Once varga inheritance is
in place these are redundant. Keep only domain anchor identity.

### No `domain-math-sthita` on individual leaves

Leaves inherit domain membership through the varga chain. Varga node carries it once.

---

## Directory skeleton

```
brahman/kosha/math/
  math-varga.om              ← thin: remove subanta-swarupa
  domain-math.om             ← thin: just domain anchor identity
  ganana-setu.om             ← stays as-is (bridge node)
  quantity.om                ← stays (root samanya, cross-subvarga)
  expression.om              ← stays (root samanya, cross-subvarga)
  equation.om                ← stays (root samanya, cross-subvarga)
  arithmetic.om              ← stays (root samanya, cross-subvarga)

  algebra/
    algebra-varga.om
    structures/
    properties/              (cross-domain props: commutativity, associativity, distributivity)
    operations/              (homomorphism, isomorphism, morphism, function, composition)

  geometry/
    geometry-varga.om
    structures/              (vector, matrix, coordinate, subspace, basis, manifold,
                              trikona, vrtta-stambha, dirgha-vrtta, ativakra, sama-dura-vakra)
    properties/              (orthogonal, norm, rank, singular, differential-geometry, topology)
    operations/              (rotation-matrix, homogeneous-transform, vec-add, vec-dot,
                              vec-cross, vec-norm, vec-scale, projection, transform, normal,
                              gradient, curl, divergence, laplacian, inverse, determinant,
                              matrix-multiplication, dot-product, eigenvector, eigenvalue,
                              identity-matrix)

  calculus/
    calculus-varga.om
    structures/              (limit, series, asymptote, infinitesimal, polynomial, fixed-point)
    operations/              (derivative, partial-derivative, antiderivative, fourier-transform)

  number/
    number-varga.om
    structures/              (int, float, real, rational, irrational, complex, imaginary,
                              scalar, pi, e, radian, amplitude, phase, one, two,
                              zero [NEW], sine [NEW], cosine [NEW], tangent [NEW],
                              sequence [NEW], convergence [NEW], variable [NEW])
    properties/              (prime, coefficient, permutation, combination,
                              cardinality [NEW], bijection [NEW])
    operations/              (addition, subtraction, multiplication, division, plus, minus,
                              times, equals, square-root, logarithm, power, factorial,
                              abs, floor, ceil, mod)

  set/
    set-varga.om
    structures/              (set, empty-set, subset, element, equivalence-relation,
                              partial-order)
    properties/              (closure, identity-element, inverse-element)
    operations/              (set-union, set-intersection, set-complement, set-difference,
                              set-product)

  graph/                     NEW sub-varga
    graph-varga.om           "math-varga-vishesa" + shakha-yukta sambandha-yukta krama-yukta
    structures/              (graph, vertex, edge-graph [NOT edge — clash], path, cycle, tree,
                              directed-graph, weighted-graph, adjacency-matrix)
    properties/              (connectivity, acyclicity, planarity)
    operations/              (graph-walk, breadth-first, depth-first, shortest-path, spanning-tree)

  logic/                     NEW sub-varga
    logic-varga.om           "math-varga-vishesa" + viveka-yukta niyama-yukta satya-yukta
    structures/              (axiom, theorem, proposition, proof, contradiction,
                              inference, undecidable)
    properties/              (completeness, soundness, consistency)
    operations/              (implication, negation, conjunction, disjunction, quantifier)

  probability/               NEW sub-varga
    probability-varga.om     "math-varga-vishesa" + matra-yukta viveka-yukta seema-yukta
    structures/              (probability, distribution, random-variable, sample-space,
                              event, expected-value, variance)
    properties/              (independence, conditional)
    operations/              (marginalisation, normalisation, bayes)

  complexity/                NEW sub-varga
    complexity-varga.om      "math-varga-vishesa" "cs-varga-vishesa" + krama-yukta seema-yukta
    structures/              (O-notation, complexity-class, decision-problem,
                              time-complexity, space-complexity)
    properties/              (tractable, intractable, undecidable)
    operations/              (reduction, induction [NEW], invariant [NEW], recursion [cross-ref cs])
```

---

## CS information theory upgrade

```
brahman/kosha/computation/
  information/               NEW sub-dir
    information-varga.om     "cs-varga-vishesa" "probability-varga-vishesa"
                             + viveka-yukta matra-yukta kshaya-yukta
    structures/              (entropy, information, channel, code, message, compression, noise)
    properties/              (redundancy, capacity)
    operations/              (encoding, decoding, mutual-information)
```

`bit` (already exists at `brahman/kosha/computation/bit.om`) gets upgraded:
add `information-varga-vishesa` edge.

---

## Collatz migration (Phase 2.8 folded in)

`brahman/kosha/collatz.om` and `brahman/kosha/collatz-parity.om` → rewrite into
`brahman/kosha/math/number/structures/` with:
- `number-varga-vishesa`
- `avrti-yukta`
- `sama-vishama-yukta`

Delete old files at `brahman/kosha/` root after writing new ones.

---

## Cross-domain properties (single node, multiple varga-lakshana edges)

These properties DO NOT get duplicated per-subdir. One node, multiple edges + sangati roots:

```
commutativity      → "algebra-varga-lakshana" "set-varga-lakshana" "number-varga-lakshana"
                     "sama-yukta"
closure            → "algebra-varga-lakshana" "set-varga-lakshana"
                     "purna-yukta"
identity-element   → "algebra-varga-lakshana" "set-varga-lakshana"
                     "shunya-yukta" "sama-yukta"
inverse-element    → "algebra-varga-lakshana" "set-varga-lakshana"
                     "viparita-yukta"
associativity      → "algebra-varga-lakshana" "number-varga-lakshana"
                     "sama-yukta"
equivalence-rel.   → "algebra-varga-lakshana" "set-varga-lakshana"
                     "sama-yukta" "sambandha-yukta"
partial-order      → "set-varga-lakshana" "algebra-varga-lakshana"
                     "sambandha-yukta" "krama-yukta"
morphism           → "algebra-varga-karma" "set-varga-karma"
                     "sambandha-yukta" "rachana-yukta"
```

---

## Sangati root connections to add to existing nodes

```
commutativity      → sama-yukta
associativity      → sama-yukta
closure            → purna-yukta
identity-element   → shunya-yukta + sama-yukta
inverse-element    → viparita-yukta
equivalence-rel.   → sama-yukta + sambandha-yukta
partial-order      → sambandha-yukta + krama-yukta
topology           → sambandha-yukta
series             → parampara-yukta + avrti-yukta
factorial          → avrti-yukta
power              → avrti-yukta
e                  → avrti-yukta + spanda-yukta
fixed-point        → svayambhu-yukta
pi                 → avrti-yukta + ananta-yukta
manifold           → rachana-yukta
one                → eka-yukta
two                → dvandva-yukta
list               → vrnda-yukta
scalar             → matra-yukta
truth-math         → satya-yukta
corruption-in-math → vikrita-yukta
recursion (cs)     → avrti-yukta  (already has avrti-swarupa — add yukta too)
```

All required sangati nodes already exist. No new sangati nodes needed for this phase.

---

## Missing nodes to add (during migration)

| node | subdir | sangati roots |
|---|---|---|
| `zero` | `number/structures/` | `shunya-yukta` |
| `sine` | `number/structures/` | `avrti-yukta taranga-yukta` |
| `cosine` | `number/structures/` | `avrti-yukta taranga-yukta` |
| `tangent` | `number/structures/` | `viveka-yukta kona-yukta` |
| `sequence` | `number/structures/` | `krama-yukta parampara-yukta` |
| `convergence` | `number/structures/` | `seema-yukta abhisarana-yukta` |
| `variable` | `number/structures/` | `chala-apeksha-yukta` |
| `cardinality` | `number/properties/` | `matra-yukta vrnda-yukta` |
| `bijection` | `number/properties/` | `sama-yukta eka-eka-yukta` |
| `proof` | `logic/structures/` | `satya-yukta niyama-yukta` |
| `axiom` | `logic/structures/` | `niralamba-yukta svayambhu-yukta` |
| `theorem` | `logic/structures/` | `satya-yukta niyama-siddha` |
| `inference` | `logic/operations/` | `viveka-yukta kramanusara-yukta` |
| `invariant` | `complexity/operations/` | `svabhava-yukta purna-yukta` |
| `induction` | `complexity/operations/` | `parampara-yukta krama-yukta` |
| `collatz` | `number/structures/` | `avrti-yukta sama-vishama-yukta` |
| `collatz-parity` | `number/structures/` | `avrti-yukta sama-vishama-yukta` |

---

## Build sequence

1. **Create all directory skeletons** (mkdir only, no files yet)
2. **Thin `math-varga.om`** — remove `subanta-swarupa`; **thin `domain-math.om`** — remove flat yukta list
3. **Migrate `algebra/` batch**: read flat file → write to new subdir → delete old flat file
   - structures: group, ring, field, monoid, graded-ring, ideal, kernel, quotient, subgroup, vector-space, tensor, category, lattice
   - properties: commutativity, associativity, distributivity, filtration (with cross-domain varga-lakshana edges)
   - operations: homomorphism, isomorphism, morphism, function, composition
4. **Migrate `geometry/` batch**: structures → properties → operations
5. **Migrate `calculus/` batch**: structures → operations
6. **Migrate `number/` batch** + add missing number nodes + Collatz migration
7. **Migrate `set/` batch**
8. **Add sangati root connections** to all migrated nodes (see table above)
9. **Build `graph/` sub-varga** + all nodes
10. **Build `logic/` sub-varga** + all nodes
11. **Build `probability/` sub-varga** + all nodes
12. **Build `complexity/` sub-varga** + nodes
13. **Build CS `information/` upgrade** + upgrade `bit.om`
14. **Run regression after each batch** — target 49/52 throughout

---

## Rewrite pattern for leaf nodes

**ALWAYS**: read old flat file → write fresh to new subdir path → delete old flat file.
Never move-then-edit. Never leave broken intermediate state.

When rewriting a leaf node:
- Add `X-varga-vishesa` (structures), `X-varga-lakshana` (properties), or `X-varga-karma` (operations)
- Remove `domain-math-sthita` — inherited through varga chain
- Remove `subanta-swarupa` — math leaves don't declare pada (math has no bhave/subanta split)
- Add sangati root connections from the table above
- Keep node-specific content

---

## Key rules

- Sangati nodes must NOT reference kosha domain nodes. Direction always kosha → sangati.
- No hardcoded word lists in tantra.
- No `domain-math-sthita` on individual leaves.
- `sine`, `cosine`, `tangent` as kosha number nodes — distinct from physics oscillation quantities.
- `edge-graph` not `edge` — to avoid clash with the `.om` edge concept.
