# 17b — Algebraic Structures as Type System

**New research (session 12). The graph already declares set/group theory. No tantra reads it.**

Parent: [17-scan-ref-patterns.md](17-scan-ref-patterns.md)

---

## The Algebraic Hierarchy in the Graph

The kosha declares a complete algebraic containment chain:

```
field --[sthita]--> ring --[sthita]--> group --[swarupa]--> set
```

Each level adds guarantees:

| Level | Operations (kriya) | Properties (siddha) | Guarantees |
|-------|-------------------|---------------------|------------|
| **set** | union, intersection, complement, difference | -- | Collection membership |
| **group** | (inherits from set) | closure, associativity, identity, inverse | Operation well-definedness |
| **ring** | addition, multiplication | distributivity | Two composable operations |
| **field** | (inherits from ring) | division, commutativity | Full inverse for both ops |

And separately:

| Structure | sthita | kriya | siddha |
|-----------|--------|-------|--------|
| **partial-order** | set | -- | reflexive, antisymmetric, **transitive** |
| **lattice** | partial-order | **join, meet** | closure, associativity, commutativity |
| **monoid** | group | -- | (associativity, identity from group) |

Verified live:
```
walk "ring" "kriya"            -> addition, multiplication
walk "ring" "siddha"           -> distributivity
walk "lattice" "kriya"         -> join, meet
walk "lattice" "sthita"        -> partial-order
walk "partial-order" "siddha"  -> reflexive, antisymmetric, transitive
walk "field" "siddha"          -> division, commutativity
walk "monoid" "drishthanta"    -> addition, multiplication
```

---

## How Varga Actually Works

### The mechanism: varga-inheritance at boot

`varga-inheritance.tantra3` runs at boot:
1. For every node N, walk its `swarupa` edges to get parents
2. For each parent X, check if `X-varga` exists as a node
3. If yes, emit `N --[varga]--> X-varga`

### What populates and what doesn't

| Varga | Members | Why |
|-------|---------|-----|
| `physics-mantra` | 23 | All physics mantras have `swarupa` pointing to a physics concept; `physics-mantra` exists |
| `energy-varga` | 4 | `kinetic-energy` has `swarupa energy`; `energy-varga` exists |
| `mammal-varga` | 4 | `cat` has `swarupa mammal`; `mammal-varga` exists |
| `set-varga` | 4 | `group` has `swarupa set`; `set-varga` exists |
| `algebra-varga` | **0** | Members connect via `sthita`/`yukta`, not `swarupa` |
| `number-varga` | **0** | Same: `addition` declares `"number-varga-karma"` but `karma` is not a parsed relation |
| `logic-varga` | **0** | Same |

The algebraic hierarchy (group inside ring inside field) uses `sthita` edges,
not `swarupa`. Varga-inheritance only walks `swarupa`. So:

- `ring --[sthita]--> group` -> ring is NOT in group's varga
- `field --[sthita]--> ring` -> field is NOT in ring's varga
- `group --[swarupa]--> set` -> group IS in set-varga (the one correct case)

### The gap

The `-varga-vishesa` suffix in .om slokas is parsed by the OCaml server
differently from the Python parser. In OCaml, `"linear-force-varga-vishesa"`
becomes `target=linear-force-varga, relation=vishesa`. Since `vishesa` has
0 static members in the live graph, these edges are effectively lost.

Mass declares `"linear-force-varga-vishesa"` but has no varga edge in the
live graph. The varga-inheritance mechanism can't fire because mass's
`swarupa` is `subanta`, and `subanta-varga` doesn't exist.

---

## What Tantras Use Today

### Varga usage (51 references across 72 tantras)

- **mantra-select**: `walk-in "physics-mantra" "varga"` to get candidate mantras (O(23) vs O(2210))
- **anumana-viveka-yukta**: Walks entity's varga chain 4 levels deep to check property inheritance
- **anumana-viveka**: Walks swarupa + varga chain for IS-A checking
- **emit-anumana**: Walks varga chain for proof text generation
- **varga-inheritance**: Boot-time derivation of varga edges

### siddha usage: ZERO

**No tantra reads `siddha` edges.** Zero occurrences across all 72 tantras.
The graph declares distributivity, transitivity, commutativity, closure,
associativity -- and nobody reads any of them.

---

## Where Algebraic Structures Should Drive the Pipeline

### 1. Operation dispatch in count-bandha (Step 2)

**Currently:** 18 hardcoded subtraction words + 5 addition words decide the operation.

**With algebra:**
```
count --[yukta]--> arithmetic
walk-in "arithmetic" "kriya" -> {addition, subtraction, multiplication, division, ...}
```

The valid operation set for counting IS the set of operations on `arithmetic`.
Then: `sum --[abheda]--> addition`, `sum eval:add` maps "total" to add.

**Problem:** Both "total" and "remaining" resolve to `count` via shabda-anveshana.
They lose their distinction. Fix: "total" should resolve to `sum` (or addition)
directly; "remaining" to subtraction. Currently `word-node "plus"` -> `addition`
and `word-node "minus"` -> `subtraction` work, but "total" -> `count`.

### 2. dvandva aggregation (Step 8)

"Find total KE of two balls" = per-entity compute then aggregate.

```
distributivity --[kriya]--> [multiplication, addition]
ring --[siddha]--> distributivity
```

This IS the dvandva pattern: compute per entity (the mantra's kriya, often
involving multiplication), then aggregate via addition. The ring guarantees
this composition is valid.

Pipeline steps:
1. Detect multiple entities + "total" -> aggregation needed
2. Walk `ring --[siddha]--> distributivity --[kriya]` -> confirms [mul, add] compose
3. Fire mantra per entity, fold results via `sum --[eval]--> add`

The monoid guarantee (`monoid --[drishthanta]--> addition`) ensures the fold
is well-defined for any number of operands. `sum.arity = -1` (variadic)
exists because addition is a monoid (closed, associative, has identity 0).

### 3. Inverse math (invert-math tantra)

**Currently:** Reads `pratipaksha-0`, `pratipaksha-1` shabda keys per operation.
Already partially graph-driven.

**With algebra:**
```
group --[yukta]--> inverse-element
inverse-element --[phala]--> identity-element
field --[siddha]--> division  (multiplicative inverse exists in fields)
```

For any operation in a group, an inverse exists. The `pratipaksha` edges
on concrete operations (`addition --[pratipaksha]--> subtraction`) are the
specific instances of the group's inverse-element guarantee. The field
extension adds division as the multiplicative inverse.

### 4. Viveka transitivity (Step 9, krama-viveka)

"A is heavier than B. B is heavier than C. Who is heaviest?"

```
partial-order --[siddha]--> transitive
lattice --[sthita]--> partial-order
lattice --[kriya]--> join, meet
viveka-max --[abheda]--> max  (the JOIN operation)
```

The graph declares: comparison is a partial order, transitivity is an
established property. So A>B and B>C implies A>C without computing.

`join` = max = viveka-max. The lattice structure declares that comparison
with max IS the join operation of a lattice over a partial order with
transitivity. The pipeline could walk `partial-order -> siddha -> transitive`
to know when to apply the transitive shortcut.

### 5. Mantra-select sub-varga narrowing

`mantra-select` already notes: "future: sub-varga narrowing via solve-for
concept's own varga."

```
kinetic-energy --[varga]--> energy-varga
walk-in "energy-varga" "varga" -> {KE, PE, photon-energy}
walk-in each "phala" -> {ke-mantra, pe-mantra, photon-energy-mantra}
```

3 candidates instead of 23. The concept's varga membership intersects with
the mantra varga to narrow candidates.

### 6. Avrti validation

The algebraic structure acts as a **type checker** for composed operations:

- Ring guarantees: addition and multiplication compose via distributivity
- Monoid guarantees: fold by addition is well-defined for any N operands
- Field guarantees: every multiplicative operation has a division inverse
- Partial-order guarantees: comparison is transitive

Before firing a composite operation (dvandva, krama-viveka), the pipeline
could walk the algebraic chain to validate the composition is structurally
sound. This isn't just optimization -- it's correctness: the graph declares
which compositions are mathematically valid.

---

## The Concrete Connections (Live Graph Traces)

### Ring structure -> operations
```
ring --[kriya]--> addition, multiplication
ring --[siddha]--> distributivity
distributivity --[kriya]--> multiplication, addition
```

### Who uses addition as their operation
```
walk-in "addition" "kriya" -> 
  ring, graded-ring, distributivity,        (algebraic structures)
  vector-space, polynomial,                  (math structures)  
  velocity-step, position-step, relative-velocity  (physics processes)
```

### Identity elements
```
identity-element --[drishthanta]--> addition, multiplication
identity-element --[abheda]--> shunya  (zero = additive identity)
```

### Inverse pairs
```
addition --[pratipaksha]--> subtraction
subtraction --[pratipaksha]--> addition
multiplication --[pratipaksha]--> division
division --[pratipaksha]--> multiplication
addition shabda inverse -> subtraction
multiplication shabda inverse -> division
```

### The fold mechanism
```
fold --[swarupa]--> sum, product
sum --[abheda]--> addition        (sum IS addition)
sum eval:add, arity:-1            (variadic add)
product --[abheda]--> multiplication
product eval:mul, arity:-1        (variadic mul)
monoid --[drishthanta]--> addition, multiplication  (both are monoids)
```

### The comparison mechanism
```
viveka-max --[abheda]--> max --[eval]--> max
viveka-min --[abheda]--> min --[eval]--> min
partial-order --[siddha]--> transitive
lattice --[kriya]--> join, meet
lattice --[sthita]--> partial-order
```

---

## Summary: The Graph as Type System

The algebraic structure is a **type system for operations** that the graph
already declares:

- `siddha` edges are **axioms** (distributivity, transitivity, closure)
- `kriya` edges are **valid operations** for a structure
- `drishthanta` edges are **concrete instances** of abstract properties
- `pratipaksha` edges are **inverses**
- `sthita` edges are **containment** (ring sits inside group)
- `swarupa` edges are **identity** (group IS-A set)

No tantra reads any of this. The pipeline hardcodes what these edges declare.
The implementation plan (17c) makes the pipeline read them.

---

## vriddhi / kshaya as Universal Direction Classifier (Session 17)

Every mathematical operation has a direction: vriddhi (increase) or kshaya (decrease).
Before session 17, this was only partially declared: `subtraction --[kriya]--> kshaya`
existed, but `addition --[kriya]--> vriddhi` did not.

**Now complete (session 17):**

| Direction | Operations (kriya edges) |
|-----------|------------------------|
| **vriddhi** (increase) | addition, multiplication, power, exponential, square, double |
| **kshaya** (decrease) | subtraction, division, square-root, half |
| **both** | logarithm (vriddhi-kshaya-kriya — compresses growth) |
| **neutral** | neg (reversal), abs (direction removal) |

**Connection to event verbs:**
```
"flew away" → shabda "common-sense-events" "flew" → kshaya
kshaya → walk-in "kshaya" "kriya" → [..., subtraction, division, ...]
∩ arithmetic → subtraction → eval:sub → apply-op "sub"

"came back" → shabda "common-sense-events" "came" → vriddhi
vriddhi → walk-in "vriddhi" "kriya" → [..., addition, multiplication, ...]
∩ arithmetic → addition → eval:add → apply-op "add"
```

**The structural principle:** vriddhi and kshaya are sangati-layer concepts
(eternal qualities of change). The kriya edges connect them to kosha-layer
operations (concrete mathematics). The shabda table connects them to
bhasha-layer words (natural language). Three layers, one meaning.

## Set Operations: Declared but Disconnected (Session 17)

Six tantras use set operations inline without referencing the kosha:

| Tantra | Set operation | Current inline implementation |
|--------|--------------|------------------------------|
| forward-match / derive-step | subset (janya ⊆ bcs) | `reduce janya true (fn a r → and a (member r bcs))` |
| mantra-select | member (sf ∈ phala ∪ janya) | `member solve-for phala` |
| scope-vps | union (scoped ∪ flat) | reduce with dedup |
| viveka-ganana | member (active ∈ seen) | `member active seen-vals` |
| count-bandha | intersection (signals ∩ mithya) | `member w mithya-words` |

The kosha declares set-union, set-intersection, set-difference — with wrong
eval values (inherited placeholders: div, ceil, sin). No runtime primitives
exist. Step 2a will fix this.

**Key structural connections already in the kosha:**
- `set-difference --[abheda]--> kshaya` — set removal IS decrease
- `lattice --[yukta]--> set-union, set-intersection` — join/meet at set level
- `group --[swarupa]--> set` — algebraic structures sit on sets

---

## What Has Changed

| Date | Session | Event |
|------|---------|-------|
| 2026-03-20 | 12 | Document created. Full algebraic hierarchy traced in live graph. Varga mechanism mapped. Five concrete pipeline integration points identified. |
| 2026-03-20 | 17 | **vriddhi/kshaya classification completed.** 9 operations got kriya edges. Set operation gap documented: 6 tantras use inline, kosha nodes have wrong eval values. Two new sections added. |
