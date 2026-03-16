# Graph-Native Execute-Chain Plan

**Status**: Architecture grounded in live graph. Implementation next.
**Supersedes**: graph-native-computation.md, graph-computation-tantras.md
**Part of**: engine-tantra-migration.md Step 7

---

## Ground truth from the live graph

These are facts confirmed by live queries, not assumptions.

### What the question graph actually looks like

Input: `"ball has mass 5 and velocity 10 find kinetic energy"`

After `avrti-refine` + `sankhya-bandha`:
```
[ball,            mithya,             ball]
[ball,            prathama-vibhakti,  object]
[mass,            satya,              mass]
[mass,            shashthi-vibhakti,  ball]       ← mass OF ball
[mass,            sankhya,            5.]          ← value on the concept node
[velocity,        satya,              velocity]
[velocity,        shashthi-vibhakti,  ball]
[velocity,        sankhya,            10.]
[find,            vidhi-kaala,        solve-for]  ← intent
[kinetic-energy,  satya,              kinetic-energy]
```

Key facts:
- Numbers land on **concept nodes** directly: `[mass, sankhya, 5.]`
- The entity link is only a `shashthi-vibhakti` edge: `[mass, shashthi-vibhakti, ball]`
- There are **no entity-scoped instance nodes** (`mass-of-ball`) in the current pipeline
- `solve-for` is `[find, vidhi-kaala, solve-for]` — `find` is the word, `solve-for` is the value
- The target concept (`kinetic-energy`) is present as a `satya` node, not as a `proposition`

### What the mantra node looks like in the graph

```
walk "kinetic-energy-mantra" "janya"  → ["mass", "velocity"]
walk "kinetic-energy-mantra" "phala"  → ["kinetic-energy"]
walk "kinetic-energy-mantra" "kriya"  → ["ke-expr"]
walk "kinetic-energy-mantra" "varga"  → ["physics-mantra"]
```

### What op nodes carry

```
shabda "half"           "inverse"        → "double"
shabda "half"           "eval"           → "half"
walk   "half"           "pratipaksha"    → ["double"]

shabda "square"         "inverse"        → "sqrt"
shabda "square"         "pratipaksha-0"  → "sqrt"     ← solve for arg 0
shabda "square"         "degree"         → "2"
walk   "square"         "pratipaksha"    → ["square-root"]

shabda "multiplication" "pratipaksha-0"  → "div"      ← solve for arg 0: a=c/b
shabda "multiplication" "pratipaksha-1"  → "div"      ← solve for arg 1: b=c/a

shabda "division"       "pratipaksha-0"  → "mul"      ← solve for arg 0: a=c*b
shabda "division"       "pratipaksha-1"  → "div"      ← solve for arg 1: b=a/c
shabda "division"       "pratipaksha-1-flip" → "true" ← use original dividend, not result

shabda "subtraction"    "pratipaksha-0"  → "add"      ← solve for arg 0: a=c+b
shabda "subtraction"    "pratipaksha-1"  → "sub"      ← solve for arg 1: b=a-c
shabda "subtraction"    "pratipaksha-1-flip" → "true"
```

The **`pratipaksha-N` + `pratipaksha-N-flip`** encoding is fully populated and handles
all algebraic inversion cases including the non-commutative ones (sub, div).

### Tantras are black boxes at runtime

- `shabda-pairs "ke-expr"` → `[]` — no metadata on tantra nodes
- No `get-ast`, `tantra-body`, or `tantra-inputs` primitives exist
- `call-tantra` is purely black-box: looks up by name, maps args positionally, executes

**The equation tantra body is invisible from the graph.**
Inversion cannot work by inspecting the tantra's call tree.

---

## The correct inversion architecture

Since tantras are opaque, `invert-expr` must work **without** walking the call tree.
The equation tantras already encode the expression **structurally in the graph** via
the mantra's janya/phala/kriya edges and the op nodes' pratipaksha shabda.

The solution: **encode the expression tree as a subgraph on the mantra node itself**,
not in a tantra body. Then both forward execution and inversion are graph walks.

### Expression subgraph format

Each mantra gets an `expr` subgraph rooted at the `kriya` node:

```
kinetic-energy-mantra --kriya--> ke-root
ke-root --op-->       half
ke-root --arg0-->     ke-mul
ke-mul  --op-->       multiplication
ke-mul  --arg0-->     mass            ← janya leaf
ke-mul  --arg1-->     ke-sq
ke-sq   --op-->       square
ke-sq   --arg0-->     velocity        ← janya leaf
```

Leaves are either:
- A **janya concept name** (`mass`, `velocity`) — resolved from the question graph
- A **literal constant** (`1`, `2`, `pi`) — a number node

Internal nodes are **anonymous expression nodes** (e.g. `ke-mul`, `ke-sq`, `ke-root`)
that live in `brahman/yantra/equations/` as `.om` files.

### Forward evaluation (graph walk)

```
eval-node ke-root graph:
  op   = walk ke-root "op"   → "half"
  arg0 = walk ke-root "arg0" → "ke-mul"
  v0   = eval-node ke-mul graph
  → call apply-op "half" [v0]

eval-node ke-mul graph:
  op   = walk ke-mul "op"   → "multiplication"
  arg0 = walk ke-mul "arg0" → "mass"    ← leaf: read sankhya from graph
  arg1 = walk ke-mul "arg1" → "ke-sq"
  v0   = read-sankhya "mass" graph → 5.
  v1   = eval-node ke-sq graph
  → call apply-op "multiplication" [v0, v1]

eval-node ke-sq graph:
  op   = walk ke-sq "op"   → "square"
  arg0 = walk ke-sq "arg0" → "velocity"  ← leaf: read sankhya from graph
  v0   = read-sankhya "velocity" graph → 10.
  → call apply-op "square" [v0]
  → 100.

→ multiplication(5., 100.) = 500.
→ half(500.) = 250.   ✓
```

### Inverse evaluation (graph walk — same structure, different traversal)

Solve for `mass` given `KE=250, velocity=10`:

```
invert-node ke-root "mass" 250. graph:
  op   = walk ke-root "op"   → "half"
  arg0 = walk ke-root "arg0" → "ke-mul"
  -- "mass" is under arg0. Apply pratipaksha of "half" to the result:
  inv-op = shabda "half" "inverse" → "double"
  new-target = apply-op "double" [250.] → 500.
  → invert-node ke-mul "mass" 500. graph

invert-node ke-mul "mass" 500. graph:
  op   = walk ke-mul "op"   → "multiplication"
  arg0 = walk ke-mul "arg0" → "mass"      ← THIS is the unknown
  arg1 = walk ke-mul "arg1" → "ke-sq"
  -- unknown is arg0. Use pratipaksha-0: "div". Known arg1 side:
  v1   = eval-node ke-sq graph → 100.
  inv-op = shabda "multiplication" "pratipaksha-0" → "div"
  → apply-op "div" [500., 100.] → 5.   ✓
```

Solve for `velocity` given `KE=250, mass=5`:

```
invert-node ke-root "velocity" 250. graph:
  inv-op = "double" → new-target = 500.
  → invert-node ke-mul "velocity" 500. graph

invert-node ke-mul "velocity" 500. graph:
  arg0 = "mass" (known: 5.)
  arg1 = "ke-sq" (contains velocity — the unknown)
  inv-op = shabda "multiplication" "pratipaksha-1" → "div"
  -- flip? pratipaksha-1-flip not set on multiplication → no flip
  → new-target = apply-op "div" [500., 5.] → 100.
  → invert-node ke-sq "velocity" 100. graph

invert-node ke-sq "velocity" 100. graph:
  op   = "square"  arg0 = "velocity" ← the unknown
  inv-op = shabda "square" "pratipaksha-0" → "sqrt"
  → apply-op "sqrt" [100.] → 10.   ✓
```

---

## What needs to be built

### 1. Expression subgraph nodes (`.om` files)

One set of expression nodes per mantra. Example for `kinetic-energy-mantra`:

```
-- brahman/yantra/equations/ke-root.om
kosha ke-root
  "ke-mul-arg0"
  "half-op"
  shabda expr-of:kinetic-energy-mantra
done

-- brahman/yantra/equations/ke-mul.om
kosha ke-mul
  "mass-arg0"
  "ke-sq-arg1"
  "multiplication-op"
done

-- brahman/yantra/equations/ke-sq.om
kosha ke-sq
  "velocity-arg0"
  "square-op"
done
```

The compound tokens `ke-mul-arg0`, `half-op`, `mass-arg0` etc. parse into
`arg0`/`arg1`/`op` edges pointing to the named nodes.

Mantra node updated:

```
-- kinetic-energy-mantra.om
mantra kinetic-energy-mantra
  "mechanical-energy-varga-vishesa"
  "physics-mantra-varga"
  "kinetic-energy-swarupa"
  "kinetic-energy-phala"
  "ke-root-kriya"               ← points to expr subgraph root, not tantra
  "mass-janya"
  "velocity-janya"
  shabda name:kinetic-energy unit:joule invertible:yes
done
```

### 2. `eval-node.tantra`

Recursive evaluation of an expression subgraph node against the question graph.
A leaf node is any node that appears in the mantra's `janya` list — its value is
read via `sankhya` from the question graph. Internal nodes have `op` and `arg0`/`arg1`.

```
tantra eval-node
  -- evaluate one expression subgraph node, reading leaves from the question graph.
  -- node:  the expression node name (e.g. "ke-mul", "mass")
  -- janya: list of janya concept names (leaves) from the mantra
  -- graph: the question graph (source of sankhya values for leaves)

  inputs
    node   string
    janya  list
    graph  list

  let

  -- is this a leaf? (a janya concept with a direct sankhya value in the graph)
  is-leaf = member node janya

  result = cond is-leaf
    -- leaf: read sankhya from graph
    (reduce graph 0. (fn acc [s, e, o] ->
      cond (and (s is node) (e is sankhya)) o otherwise acc))

  otherwise
    -- internal node: get op, evaluate args, apply op
    (let op   = nth (walk node "op") 0
     let args = reduce ["arg0", "arg1", "arg2"] [] (fn acc slot ->
       let targets = walk node slot
       cond (gt (length targets) 0)
         (append acc [eval-node (nth targets 0) janya graph])
       otherwise acc)
     apply-op op args)

  return
    result  any

done
```

### 3. `invert-node.tantra`

Recursive inversion: walks down the expression subgraph to isolate `unknown`,
applying `pratipaksha-N` rules at each binary/unary op.

```
tantra invert-node
  -- symbolically invert an expression subgraph node to solve for `unknown`.
  -- node:    current expression subgraph node
  -- unknown: the janya concept name we are solving for
  -- target:  the accumulated result value on the LHS so far
  -- janya:   full janya list (to identify leaves)
  -- graph:   question graph (for evaluating known sub-expressions)

  inputs
    node     string
    unknown  string
    target   any
    janya    list
    graph    list

  let

  -- base case: we've reached the unknown leaf
  at-unknown = node is unknown

  result = cond at-unknown
    target    -- isolated: target IS the answer

  otherwise
    (let op    = nth (walk node "op") 0
     let arity = to-number (shabda op "arity")

     -- unary case (arity 1): apply pratipaksha-0 to target, recurse into arg0
     cond (arity is 1)
       (let inv-op   = shabda op "pratipaksha-0"
        let new-tgt  = apply-op inv-op [target]
        let arg0     = nth (walk node "arg0") 0
        invert-node arg0 unknown new-tgt janya graph)

     -- binary case: find which arg contains the unknown, invert accordingly
     otherwise
       (let arg0 = nth (walk node "arg0") 0
        let arg1 = nth (walk node "arg1") 0

        -- does arg0 subtree contain unknown?
        let arg0-has = subtree-contains arg0 unknown janya

        cond arg0-has
          -- unknown is under arg0: use pratipaksha-0, eval arg1, recurse into arg0
          (let inv-op  = shabda op "pratipaksha-0"
           let v1      = eval-node arg1 janya graph
           let new-tgt = apply-op inv-op [target, v1]
           invert-node arg0 unknown new-tgt janya graph)

        otherwise
          -- unknown is under arg1: use pratipaksha-1, eval arg0, recurse into arg1
          (let inv-op  = shabda op "pratipaksha-1"
           let flip    = shabda op "pratipaksha-1-flip"
           let v0      = eval-node arg0 janya graph
           let new-tgt = cond (flip is "true")
             (apply-op inv-op [v0, target])   -- flip: use original order
             otherwise
             (apply-op inv-op [target, v0])
           invert-node arg1 unknown new-tgt janya graph)))

  return
    result  any

done
```

`subtree-contains` is a helper tantra: walks `arg0`/`arg1` recursively checking if
`unknown` appears as a leaf.

### 4. `eval-mantra.tantra`

Replaces `execute-chain`. Takes a mantra name and the question graph.
Detects forward vs inverse from graph structure. Calls `eval-node` or `invert-node`.

```
tantra eval-mantra
  -- evaluate a mantra against the question graph.
  -- forward: all janya have sankhya values → call eval-node on expr root
  -- inverse: exactly one janya missing, phala has sankhya → call invert-node
  --
  -- the question graph IS the bindings. no separate val-pairs needed.

  inputs
    mantra  string
    graph   list

  let

  janya     = walk mantra "janya"
  phala     = nth (walk mantra "phala") 0
  expr-root = nth (walk mantra "kriya") 0

  -- which janya concepts have sankhya values in the graph?
  bound = reduce graph [] (fn acc [s, e, o] ->
    cond (and (e is sankhya) (member s janya))
      (append acc [s])
    otherwise acc)

  -- which janya are missing?
  missing = filter janya (fn j -> not (member j bound))

  -- what is the phala value in the graph (if any)?
  phala-val = reduce graph "" (fn acc [s, e, o] ->
    cond (and (s is phala) (e is sankhya)) o otherwise acc)

  -- route: forward, inverse, or unknown
  is-forward = missing is empty
  is-inverse = and (eq (length missing) 1)
                   (gt (string-length phala-val) 0)

  result = cond is-forward
    (eval-node expr-root janya graph)

  (and (not is-forward) is-inverse)
    (let unknown = nth missing 0
     invert-node expr-root unknown phala-val janya graph)

  otherwise
    ""    -- no result (will trigger clarification path later)

  return
    result  any

done
```

### 5. Updated `match-mantra.tantra`

Extended to also match when `solve-for` is a **janya** of a mantra (inverse case),
not just the phala:

```
-- candidate filter: phala matches solve-for (forward) OR solve-for is in janya (inverse)
candidates = cond (gt (string-length solve-for) 0)
  (filter mantras (fn m ->
    let mname   = shabda m "name"
    let mphala  = nth (walk m "phala") 0
    let mjanya  = walk m "janya"
    or (mname is solve-for)
       (mphala is solve-for)
       (member solve-for mjanya)))
  otherwise mantras

-- match condition extended: all-ok (forward) OR inverse-ok (one missing, phala bound)
match = reduce candidates [] (fn acc m ->
  cond (gt (length acc) 0) acc
  otherwise
    (let janya     = walk m "janya"
     let phala     = nth (walk m "phala") 0
     let bound-set = nth bound-vals 0
     let missing   = filter janya (fn j -> not (member j bound-set))
     let phala-ok  = member phala bound-set
     let all-ok    = missing is empty
     let inv-ok    = and (eq (length missing) 1) phala-ok
     cond (or all-ok inv-ok) [m]
     otherwise []))
```

Note: `match-mantra` now returns `[mantra]` only — no `val-pairs`. The graph is
passed directly to `eval-mantra`.

### 6. Updated `anuvada-ganana.tantra`

```
tantra anuvada-ganana
  takes sentence

  raw-graph = build-question-graph sentence
  refined   = fixpoint raw-graph avrti-refine
  expanded  = kosha-expand refined

  match = match-mantra expanded

  enriched = cond (gt (length match) 0)
    expanded
  otherwise
    (fixpoint expanded derive-step)

  final-match = cond (gt (length match) 0)
    match
  otherwise
    (match-mantra enriched)

  result = cond (gt (length final-match) 0)
    (let mantra = nth final-match 0
     let value  = eval-mantra mantra expanded    ← graph, not val-pairs
     let label  = nth (walk mantra "phala") 0
     concat label " = " (to-string value))
  otherwise
    "no match"

  return result
done
```

---

## Two-entity case: the ownership problem

Current pipeline puts values on concept nodes directly:
`[mass, sankhya, 5.]` — only one value per concept.

With two entities (`ball1 mass=3, ball2 mass=5`) there is a collision:
`mass` would get two `sankhya` values. This is the **entity-scoping gap**.

This is deferred to Phase 4 (dvandva groups / rashi instances). For now:
- `eval-mantra` reads the first `sankhya` value it finds on each concept node
- Single-entity problems work correctly
- Two-entity problems require the rashi instance layer (see nyaya-plan.md Phase 4)

When entity scoping arrives, `eval-node` changes its leaf resolver from:
```
reduce graph 0. (fn acc [s,e,o] -> cond (and (s is node) (e is sankhya)) o ...)
```
to:
```
read-sankhya-for-entity node entity-name graph
```
where `entity-name` is threaded through the per-entity match.

---

## `subtree-contains` helper

```
tantra subtree-contains
  -- does the subtree rooted at `node` contain `unknown` as a leaf?
  inputs
    node     string
    unknown  string
    janya    list

  let

  is-leaf = member node janya

  result = cond is-leaf
    (node is unknown)
  otherwise
    (let arg0s = walk node "arg0"
     let arg1s = walk node "arg1"
     let a0    = cond (gt (length arg0s) 0)
       (subtree-contains (nth arg0s 0) unknown janya)
       otherwise false
     let a1    = cond (gt (length arg1s) 0)
       (subtree-contains (nth arg1s 0) unknown janya)
       otherwise false
     or a0 a1)

  return result
done
```

---

## What was done (Phase 2, P2.1–P2.7)

- ✅ P2.1 — Phase 1 regressions fixed (343 passed baseline)
- ✅ P2.2 — phala edges on all 23 physics mantras
- ✅ P2.3 — apply-op uses graph node lookup
- ✅ P2.4 — 23 equation tantras in `brahman/yantra/equations/` (forward only, inputs number)
- ✅ P2.5 — derive-step, match-mantra, mantra-coverage use walk-in "physics-mantra" "varga"
- ✅ P2.7 — krama edges, execute-chain-kriya, krama shabda keys all removed
- ✅ varga registered as live traversable dimension in proof_graph.ml
- ✅ "physics-mantra-varga" on all 23 mantra .om files

**Current baseline**: 343 passed / 11 xfailed / 0 failing

---

## Remaining: P2.6 — expression subgraph + eval-mantra + invert-node

### Implementation order (tests first)

**Step 1 — Tests** (write before any code):
```python
def test_forward_ke(vy):
    # existing — verify baseline still holds
    r = vy.eval('anuvada-ganana "ball has mass 5 and velocity 10 find kinetic energy"')
    assert "250" in r

def test_inverse_ke_solve_mass(vy):
    # KE=1000, v=20 → m = 2*KE/v² = 5
    r = vy.eval('anuvada-ganana "find mass ball has kinetic energy 1000 and velocity 20"')
    assert "5" in r

def test_inverse_ke_solve_velocity(vy):
    # KE=1000, m=5 → v = sqrt(2*KE/m) = 20
    r = vy.eval('anuvada-ganana "find velocity ball has kinetic energy 1000 and mass 5"')
    assert "20" in r

def test_inverse_newton_solve_mass(vy):
    # F=ma → find mass: F=10, a=2 → m=5
    r = vy.eval('anuvada-ganana "find mass force 10 and acceleration 2"')
    assert "5" in r

def test_inverse_acceleration_solve_time(vy):
    # a=(v-u)/t → find time: a=5, v=25, u=0 → t=5
    r = vy.eval('anuvada-ganana "find time acceleration 5 final velocity 25 initial velocity 0"')
    assert "5" in r
```

**Step 2 — Expression subgraph `.om` nodes** for all 23 mantras:
Write `ke-root.om`, `ke-mul.om`, `ke-sq.om` etc. in `brahman/yantra/equations/`.
Update each mantra `.om` to point `kriya` at the expr subgraph root instead of the tantra.

**Step 3 — `eval-node.tantra`**: forward recursive eval. Tests pass for forward cases.

**Step 4 — `subtree-contains.tantra`**: helper for inversion path-finding.

**Step 5 — `invert-node.tantra`**: inverse recursive eval. Tests pass for inverse cases.

**Step 6 — `eval-mantra.tantra`**: dispatcher (forward + inverse detection).

**Step 7 — Update `match-mantra.tantra`**: extend candidate filter for inverse case.
Returns `[mantra]` only (drop val-pairs).

**Step 8 — Update `anuvada-ganana.tantra`**: call `eval-mantra mantra graph` instead
of `execute-chain mantra val-pairs`.

**Step 9 — Update `derive-step.tantra`**: same substitution.

**Step 10 — Delete `execute-chain.tantra`** (fully replaced by eval-mantra + eval-node).

### Regression gate

P2.6 target: **360+ passed / 6 xfailed** — all forward + inverse tests passing.
Remaining xfails: two-entity dvandva (Phase 4), frequency/period constants (P8f).
