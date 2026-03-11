# Mantra Nodes — Algebraic Relation Layer

**Status**: In Progress
**Prerequisite for**: yantra_inverter.ml removal, graph-native computation (P8)
**Depends on**: math operation mantra nodes (for krama chain references)

---

## What is a mantra node

A `mantra` node is a first-class node type in the `.om` DSL (alongside `sangati`,
`kosha`, `bhasha`). It declares a formula: the krama chain of operations (forward
computation) plus the LHS/RHS structure of the equation.

```
mantra kinetic-energy-mantra

  "mechanical-energy-varga-vishesa"
  "kinetic-energy-swarupa"       -- links to the quantity concept

  -- KE = ½mv²: ordered computation steps
  "square-krama"                 -- step 1: v²   (→ math/number/operations/square)
  "multiplication-krama"         -- step 2: m·v² (→ math/number/operations/multiplication)
  "division-krama"               -- step 3: ½·m·v²

  "execute-chain-kriya"

  shabda kinetic-energy-mantra / KE-equals-half-mv-squared degree:2 krama-lhs:energy krama-rhs:mass,velocity

done
```

**Key properties:**
- `[quantity]-swarupa` links the mantra to the concept it computes
- Krama edges are positionally ordered (step sequence = sloka order)
- `krama-lhs` = the single variable on the left side (the natural output)
- `krama-rhs` = all variables on the right side (the forward chain inputs)
- `degree` = polynomial degree of lhs in rhs variables
- Inversion is handled by `invert-mantra` (P8) — no explicit pratipaksha solve nodes needed
- No `execute-inverse-kriya` on formula nodes — invert-mantra takes the mantra as input

### Design: inversion as a higher-order mantra

Inversion is itself a mantra that takes another mantra as input:

```
mantra invert-mantra
  -- input: a formula-mantra + the unknown variable name
  -- reads: krama chain + each op's inverse: metadata
  -- output: reversed krama chain that solves for the unknown
  "execute-chain-kriya"
  shabda invert-mantra / symbolic-inversion-of-any-formula-mantra
done
```

This means: `invert-mantra kinetic-energy-mantra velocity` derives
`v = sqrt(2·KE/m)` at runtime from the krama chain, using `inverse:` metadata
on each operation node (`square` → `inverse:sqrt`, `multiplication` → `inverse:division`, etc.).

### Design: mantra composition

Inputs in `krama-rhs` can themselves be computed by other mantras. The graph
naturally encodes this: `velocity` is the `krama-lhs` of `velocity-mantra`,
so if `velocity` is unknown and `velocity-mantra`'s rhs are all known, the solver
chains them automatically. This is pure graph traversal — no extra annotation needed.

---

## Node format for math operation mantras

Math operations are also `mantra` nodes. They are the building blocks that
physics/domain mantras compose via krama edges.

```
mantra square
  "number-varga-karma"
  "square-root-pratipaksha"
  shabda eval:square arity:1 degree:2 per-element:yes invertible:yes inverse:sqrt
done
```

### Krama step properties (in shabda on math operation nodes)

| Property | Values | Meaning |
|---|---|---|
| `eval` | prim-name | OCaml primitive that backs this op |
| `arity` | int / -1 | number of args (-1 = variadic) |
| `degree` | float/symbol | grade of output relative to input |
| `per-element` | yes/no | distribute over list input (map semantics) |
| `fold` | sum/product/mean | aggregate list → scalar |
| `invertible` | yes/no | whether this op can be reversed |
| `inverse` | op-name | which operation undoes this one |

---

## What is built (done)

### Parser support
- `mantra` is a registered node type in `om_parser.ml` alongside `sangati`, `kosha`, `bhasha`

### Physics mantra nodes
Located alongside their quantity nodes in `brahman/kosha/physics/`:

| Mantra | Formula | Location |
|---|---|---|
| `kinetic-energy-mantra` | KE = ½mv² | energy/mechanical/quantities/ |
| `potential-energy-mantra` | PE = mgh | energy/mechanical/quantities/ |
| `work-mantra` | W = Fd·cos(θ) | energy/mechanical/quantities/ |
| `velocity-mantra` | v = u + at | kinematics/linear/quantities/ |
| `acceleration-mantra` | a = Δv/t | kinematics/linear/quantities/ |
| `momentum-mantra` | p = mv | kinematics/linear/quantities/ |
| `friction-force-mantra` | f = μN | dynamics/linear-force/quantities/ |
| `spring-force-mantra` | F = kx | dynamics/linear-force/quantities/ |
| `centripetal-force-mantra` | F = mv²/r | dynamics/linear-force/quantities/ |
| `gravitational-force-mantra` | F = Gm₁m₂/r² | dynamics/linear-force/quantities/ |
| `torque-mantra` | τ = Iα | dynamics/rotational-force/quantities/ |
| `angular-velocity-mantra` | ω = v/r | kinematics/rotational/quantities/ |
| `angular-momentum-mantra` | L = Iω | kinematics/rotational/quantities/ |
| `period-mantra` | T = 2π/ω | oscillation/quantities/ |
| `frequency-mantra` | f = 1/T | oscillation/quantities/ |
| `electric-power-mantra` | P = VI | electromagnetism/circuit/quantities/ |
| `ohm-law` | V = IR | electromagnetism/circuit/quantities/ |
| `capacitance-mantra` | C = Q/V | electromagnetism/circuit/quantities/ |
| `photon-energy-mantra` | E = hf | electromagnetism/optics/quantities/ |
| `mass-density-mantra` | ρ = m/V | fluid/quantities/ |
| `pressure-mantra` | P = F/A | fluid/quantities/ |
| `newton-second-law-motion` | F = ma | physics/ |
| `jacobian-mantra` | J = finite-diff(FK) | ik/quantities/ |

### Math number operation mantras
All in `brahman/kosha/math/number/operations/`:
`addition`, `subtraction`, `multiplication`, `division`, `power`, `square`, `square-root`,
`abs`, `floor`, `ceil`, `logarithm`, `exponential`, `max`, `min`, `factorial`,
`sine`, `cosine`, `tangent`, `arcsine`, `arccosine`, `arctangent`, `neg`

With `eval:` bindings to OCaml primitives.

### Math calculus operation mantras
`derivative`, `antiderivative`, `fourier-transform`, `partial-derivative`
in `brahman/kosha/math/calculus/operations/`

### Math geometry/vector operation mantras
`vec-add`, `vec-scale`, `vec-dot`, `vec-norm`, `vec-cross`,
`rotation-matrix`, `homogeneous-transform`, `matrix-multiplication`, `determinant`,
`mat-transpose`, `mat-inverse`, `mat-adjugate`
plus others in `brahman/kosha/math/geometry/operations/`

Vec ops have krama chains referencing scalar operations (mul, add, square, sqrt).

---

## Operation categories and krama structure

### Trig / transcendental (math/number/operations/)
Backed by OCaml primitives. Inverse pairs:

| Node | eval | inverse |
|---|---|---|
| `sine` | sin | arcsine |
| `cosine` | cos | arccosine |
| `tangent` | tan (= sine/cosine krama) | arctangent |
| `arcsine` | asin | sine |
| `arccosine` | acos | cosine |
| `arctangent` | atan2 | tangent |
| `exponential` | exp | logarithm |
| `neg` | neg | neg (self-inverse) |

### Vector ops (math/geometry/operations/) — krama compositions

| Node | Formula | Krama chain |
|---|---|---|
| `vec-add` | [a+b per elem] | addition-krama (per-element) |
| `vec-scale` | [s·a per elem] | multiplication-krama (per-element) |
| `vec-dot` | Σ(aᵢ·bᵢ) | multiplication-krama → addition-krama (fold) |
| `vec-norm` | sqrt(Σaᵢ²) | square-krama → addition-krama → square-root-krama |
| `vec-cross` | a×b (3D) | multiplication-krama → subtraction-krama |
| `mat-mul` | row·col dot products | vec-dot-krama (per output element) |

### Statistical ops (math/number/operations/) — fold compositions

| Node | Formula | Krama chain |
|---|---|---|
| `sum` | Σxᵢ | addition-krama (fold) |
| `product` | Πxᵢ | multiplication-krama (fold) |
| `mean-mantra` | Σxᵢ/n | addition-krama (fold) → division-krama (count) |
| `variance-mantra` | mean((xᵢ-μ)²) | mean-krama → subtraction-krama → square-krama → mean-krama |
| `std-dev-mantra` | sqrt(variance) | variance-krama → square-root-krama |

### Quaternion ops (math/geometry/operations/)

| Node | Formula | Krama chain |
|---|---|---|
| `quat-mul` | Hamilton product | multiplication-krama × 16 → addition/subtraction-krama |
| `quat-norm` | sqrt(w²+x²+y²+z²) | square-krama → addition-krama → square-root-krama |
| `quat-conjugate` | [w,-x,-y,-z] | neg-krama (on x,y,z) |
| `quat-to-rotation` | 3×3 matrix from unit quat | multiplication-krama → subtraction/addition-krama |

### Interpolation (math/geometry/operations/)

| Node | Formula | Krama chain |
|---|---|---|
| `lerp-mantra` | a + t·(b-a) | subtraction-krama → multiplication-krama → addition-krama |
| `slerp-mantra` | q₁·(q₁⁻¹·q₂)ᵗ | quat-mul-krama → arctangent-krama → sine-krama |

### Complex number ops (math/number/operations/)

| Node | Formula | Krama chain |
|---|---|---|
| `complex-mul` | [ac-bd, ad+bc] | multiplication-krama → subtraction/addition-krama |
| `complex-magnitude` | sqrt(a²+b²) | square-krama → addition-krama → square-root-krama |
| `complex-phase` | atan2(b,a) | arctangent-krama |

### Number theory (math/number/operations/)

| Node | Formula | Krama chain |
|---|---|---|
| `gcd-mantra` | Euclidean algorithm | modulo-krama (iterative) |
| `lcm-mantra` | a·b/gcd(a,b) | multiplication-krama → gcd-krama → division-krama |

### Logic ops (math/logic/operations/) — already exist, converted to mantra
`conjunction` (and), `disjunction` (or), `negation` (not), `implication`

---

## Execution by tantras (P8)

`execute-chain.tantra` walks krama chain:
1. Read `krama` edges from the node (ordered by sloka position)
2. For each step node: read `per-element`, `fold`, `degree` from shabda
3. Apply the step's operation — wrapping in map/fold if flagged
4. Return the `phala` value

`invert-mantra` (P8) — higher-order, takes formula-mantra + unknown-variable:
1. Read krama chain from the given formula node
2. For each op in chain: look up `inverse:` in shabda
3. Build reversed chain that isolates the unknown
4. Execute reversed chain with known bindings

`yantra-plan-resolution.tantra` (update post-P8):
- Replace OCaml `invert_chain` calls with `invert-mantra` calls

---

## Kriya edges — context-driven executor declaration

```
"execute-chain-kriya"    -- forward: all krama-rhs known → compute krama-lhs
```

`walk formula-node "kriya"` → candidate tantras. Resolver filters by context.

| Known | Solving for | approach |
|---|---|---|
| mass, velocity | kinetic-energy | `execute-chain` on kinetic-energy-mantra |
| kinetic-energy, mass | velocity | `invert-mantra kinetic-energy-mantra velocity` |
| initial-velocity, accel, time | velocity | `execute-chain` on velocity-mantra |

---

## yantra_inverter.ml removal path (post-P8)

1. Write krama + lhs/rhs on all physics formula nodes ← DONE
2. Implement `invert-mantra` tantra
3. `resolve-inverse` in `yantra_pipeline_ops.ml`: call `invert-mantra` first, fall back to `invert_chain`
4. Once all inversions covered → remove `invert_chain` calls
5. Remove `yantra_inverter.ml` from `lib/dune`

---

## Language composition — mantra as sentence (P6+)

The krama chain is also the sentence structure:
- **Execute**: v² → m·v² → ½mv²
- **Explain**: "square the velocity, multiply by mass, take half"
- **Sentence**: "kinetic energy is half the mass times the velocity squared"
- **Question**: "what mass gives kinetic energy E at velocity v?"

After P6 (bhasha English nodes), `to-english` walks the krama chain and composes
language using bhasha surface forms on each operation node.
