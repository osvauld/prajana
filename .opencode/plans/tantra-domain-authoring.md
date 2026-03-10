# Tantra Domain Authoring Guide

**Philosophy**: `.opencode/plans/sphota-scene-extraction-plan.md`
**Scene comprehension master**: `.opencode/plans/scene-comprehension-plan.md`
**Robotics IK detail**: `.opencode/plans/robotics-ik-2dof-plan.md`

---

## 1. Architecture Overview

```
NL sentence
  → tokenise → lower → classify-fold → [[word, kind, resolved], ...]
  → anuvada-ganana.tantra (router)
      ├─ scene-understand.tantra  (highest priority: multi-entity physical descriptions)
      │    └─ scene-understand-<domain>.tantra
      │         ├─ scene-extract-<domain>.tantra   (emit graph nodes)
      │         ├─ scene-narrate-<domain>.tantra   (human narration)
      │         └─ computation tantras              (physics / kinematics)
      ├─ computation pipeline  (numeric queries)
      │    ├─ yantra-plan-extraction.tantra
      │    ├─ yantra-plan-resolution.tantra
      │    └─ execute-plan → format-response.tantra
      └─ anuvada.tantra  (conceptual fallback: graph walk)
```

**Three physical layers in `brahman/`:**

| Layer    | Path                    | Content                          |
|----------|-------------------------|----------------------------------|
| kosha    | `brahman/kosha/`        | Concept nodes, metadata, units   |
| sangati  | `brahman/sangati/`      | Typed relational structure       |
| yantra   | `brahman/yantra/`       | Computation (tantras)            |

**Engine**: `vyakarana/` (OCaml). Build: `cd vyakarana && dune build`.

---

## 2. The Proof Graph

### Node (nigamana)

| Field   | Type   | Description                              |
|---------|--------|------------------------------------------|
| name    | string | Unique identifier                        |
| layer   | string | `"kosha"` or `"sangati"`                 |
| slokas  | list   | Edge declarations (see below)            |
| edges   | list   | Compiled typed edges                     |
| satya   | float  | Truth weight (0..1)                      |
| shabda  | map    | Key:value metadata pairs                 |

### 10 Core Edge Types (visheshanam)

| #  | Name         | Semantics                              |
|----|--------------|----------------------------------------|
| 0  | swarupa      | Is-a / identity / class membership    |
| 1  | abheda       | Non-different-from / synonym           |
| 2  | drishthanta  | Example-of                             |
| 3  | sthita       | Located-in / context / state           |
| 4  | yukta        | Connected-to / composed-of             |
| 5  | siddha       | Proven-from / derives-from             |
| 6  | kriya        | Action / produces                      |
| 7  | phala        | Result-of / outcome                    |
| 8  | janya        | Generated-by                           |
| 9  | pratipaksha  | Opposite-of / negation                 |

### `.om` Sloka Syntax

In `.om` files, compound tokens are auto-parsed into typed edges:

```
-- Compound token format: <node>-<relation>
-- Example slokas field:
slokas: energy-yukta work-yukta kilogram-metre-squared-per-second-squared-swarupa

-- Parsed as:
--   yukta edge  → node "energy"
--   yukta edge  → node "work"
--   swarupa edge → node "kilogram-metre-squared-per-second-squared"
```

Relation suffixes recognized: `-swarupa`, `-abheda`, `-drishthanta`, `-sthita`, `-yukta`, `-siddha`, `-kriya`, `-phala`, `-janya`, `-pratipaksha`.

---

## 3. Tantra Syntax

### Full Structure

```tantra
tantra <name>

  -- comments use double-dash

  inputs
    <param-name>  <type>  [<unit>]   -- type: float | string | list | bool
    ...

  let
    <var> = <expr>
    ...

  return
    <var>  <type>  [<unit>]
    ...                              -- multi-value return: returns VList

done
```

**Types**: `float`, `string`, `list`, `bool`
**Units** (on inputs/return): `metre`, `second`, `radian`, `radian-per-second`, etc.
**Avastha**: annotate state transitions with comments; no special syntax.

### Expression Forms

```tantra
-- Literals
42            -- float
"hello"       -- string (ASCII only — see pitfall 6)
_none         -- VNone (absence)

-- Variable reference
my-var

-- Function call (prefix)
add x y
mul a b c     -- variadic — see pitfall 1

-- Conditional (FLAT — see pitfall 2)
cond <test1> <value1> <test2> <value2> otherwise <default>

-- Anonymous function
fn acc x -> <body>

-- Let binding (in let block)
let <var> = <expr>
```

### Critical Patterns

#### Pattern 1: Flat cond — never nest

```tantra
-- WRONG: nested cond as branch body
cond a b (cond c d otherwise e)

-- RIGHT: flat chain
cond a b c d otherwise e

-- ALSO WRONG: pre-compute to variable then use in cond body
-- If branch body is complex (concat, etc.), pre-compute:
let branch-val = concat "prefix-" (to-string x)
let result = cond condition branch-val otherwise "default"
```

#### Pattern 2: Variadic ops in lambda bodies — explicit arity

`add`, `mul`, `or`, `and`, `concat` are variadic and will greedily consume remaining tokens inside a lambda body.

```tantra
-- WRONG: add eats x, y, AND rest-of-body
let bad = map lst (fn x -> add x y rest-of-body)

-- RIGHT: pre-compute the addition
let good = map lst (fn x ->
  let s = add x y
  s)
```

**Rule**: `add` and `mul` must have `parse-arity:2` in their shabda. `concat` can have many args but avoid using it as the last expr of a lambda.

#### Pattern 3: reduce accumulator as flat list

```tantra
-- RIGHT: flat list [result, state1, state2]
pass1 = reduce classified [[], _none]
  (fn acc triple ->
    let results  = nth acc 0
    let last-num = nth acc 1
    ...
    [new-results, new-num])    -- return new flat list

-- WRONG: nested pairs as accumulator
```

#### Pattern 4: No local function calls via `let f = fn...`

```tantra
-- WRONG: let f = fn... has arity 0 when called later
let lookup = fn kv -> nth kv 1
let result = lookup my-pair       -- silently returns VNone

-- RIGHT: inline with first-match or filter
let result = first-match my-list (fn kv -> cond (eq (nth kv 0) key) (nth kv 1) otherwise _none)
```

---

## 4. The Unit System

### SI Exponent Vector

Every unit carries an 8-dimensional exponent vector: `[M, L, T, I, θ, N, J, scale]`

| Index | Dimension         | Base unit |
|-------|-------------------|-----------|
| 0     | Mass (M)          | kilogram  |
| 1     | Length (L)        | metre     |
| 2     | Time (T)          | second    |
| 3     | Current (I)       | ampere    |
| 4     | Temperature (θ)   | kelvin    |
| 5     | Amount (N)        | mole      |
| 6     | Luminosity (J)    | candela   |
| 7     | Scale (log10)     | 1         |

**Examples:**
```
metre                → [0, 1, 0, 0, 0, 0, 0, 1]
metre-per-second     → [0, 1, -1, 0, 0, 0, 0, 1]
radian-per-second    → [0, 0, -1, 0, 0, 0, 0, 1]
newton               → [1, 1, -2, 0, 0, 0, 0, 1]
joule                → [1, 2, -2, 0, 0, 0, 0, 1]
watt                 → [1, 2, -3, 0, 0, 0, 0, 1]
kilometre            → [0, 1, 0, 0, 0, 0, 0, 0.001]  (scale=10^-3 for kilo → base)
centimetre           → [0, 1, 0, 0, 0, 0, 0, 0.01]
```

**Kramanusara depth** = `|T exponent|`. Position in derivative chain:
- depth 0: position/angle
- depth 1: velocity
- depth 2: acceleration
- depth 3: jerk

### Adding a New Unit: 3 Files to Touch

#### 1. `brahman/kosha/physics/matra-beeja.shabda`

```shabda
my-unit: <concept>-yukta | <base1>-yukta <base2>-yukta | alias1, alias2 / description concepts-for-unit:concept1,concept2
```

**Critical**: put `concepts-for-unit` here, not in a separate `.om` file (see pitfall 4).

Example:
```shabda
radian-per-second: angular-velocity-yukta | radian-yukta second-yukta | rad/s, radians-per-second / unit-of-angular-velocity concepts-for-unit:joint-speed-max,angular-velocity
```

#### 2. `brahman/kosha/physics/matra-aayaama.shabda`

```shabda
my-unit: <M> <L> <T> <I> <theta> <N> <J> <scale>
```

Example:
```shabda
radian-per-second: 0 0 -1 0 0 0 0 1
```

#### 3. `brahman/kosha/language/english/unit-aliases.shabda`

```shabda
rad/s:radian-per-second
rad/sec:radian-per-second
radian/s:radian-per-second
```

---

## 5. Sphoṭa Extraction Pattern

### Three Convergent Signals (disambiguate unambiguously)

1. **Dim-vector** of the unit → physical class (L, T⁻¹, etc.)
2. **Kramanusara depth** (`|T|`) → position in derivative chain
3. **`concepts-for-unit`** shabda on unit node → candidate concepts in this domain

Example: `"2 rad/s"` → `radian-per-second` → dim `[0,0,-1,...]` + depth 1 + `concepts-for-unit:joint-speed-max,angular-velocity` → assigns to `joint-speed-max` in robotics domain.

### Two-Pass `extract-value-units` Pattern

**Full tantra**: `brahman/yantra/scene/extract-value-units.tantra`

```tantra
-- Pass 1: collect raw [value, concept, unit] triples in sentence order
--   Accumulator: [results, last-num]
--   For each number token → store as last-num
--   For each unit token with pending last-num → emit [value, concept, unit-name]
--   Concept resolved from: concepts-for-unit shabda on unit node

-- Pass 2: assign joint-idx = position within concept group
--   For each triple: idx = length(filter acc (fn r -> eq (nth r 1) concept))
--   Each concept class forms independent 0-based index sequence

result: [[value, concept, unit-name, joint-idx], ...]
```

### Group Theory of Input Semantics

Each concept class (`link-length`, `joint-speed-max`, etc.) forms an independent group indexed `{0, 1, ..., n-1}`.

```
"Links are 0.3 m and 0.5 m. Joint speeds are 2 rad/s and 3 rad/s."

Pass 1 triples: [0.3, link-length, metre], [0.5, link-length, metre],
                [2.0, joint-speed-max, radian-per-second], [3.0, joint-speed-max, radian-per-second]

Pass 2 idx:     [0.3, link-length, metre, 0], [0.5, link-length, metre, 1],
                [2.0, joint-speed-max, ..., 0], [3.0, joint-speed-max, ..., 1]
```

"Respectively" falls out naturally — shared index set across concept groups = joint-0 gets (0.3m, 2 rad/s), joint-1 gets (0.5m, 3 rad/s).

### The Provided-Flag Discipline

Every extracted property emits a companion flag:

```tantra
let spd-prov = cond (exists spd-m) "yes" otherwise "no"
-- written into node shabda:
" spd-provided:" spd-prov
```

At understanding time, **the flag determines whether clarification is needed** — not the value. A default value of `5.0` with `rtorq-provided:no` triggers a clarification request; the same `5.0` with `rtorq-provided:yes` does not.

---

## 6. Scene Extraction Pattern

### 3-Tantra Structure

```
scene-extract-<domain>.tantra
  → scene-narrate-<domain>.tantra
  → scene-understand-<domain>.tantra
```

### Template: `scene-extract-<domain>.tantra`

```tantra
tantra scene-extract-<domain>

  inputs
    sentence    string
    scene-hash  string

  let
    -- 1. tokenise and classify
    words = map (tokenise sentence) (fn w -> lower w)
    classified = classify-fold words

    -- 2. detect entity counts (scan for "joint N", "link N" markers)
    -- 3. detect goals from goal-words shabda
    -- 4. detect target/destination values
    -- 5. emit target node
    target-name = emit-node (concat "target-" scene-hash) "kosha"
                    (split "relevant-slokas" " ")
                    "x:0 y:0 z:0"

    -- 6. sphoṭa extraction
    value-tuples = extract-value-units classified

    -- 7. defaults from <domain>-defaults.shabda
    -- 8. emit per-entity nodes with provided-flags
    -- 9. emit root node

  return
    root-name  string
done
```

### Template: `scene-narrate-<domain>.tantra`

```tantra
tantra scene-narrate-<domain>

  inputs
    root-node  string

  let
    root-pairs = shabda-pairs root-node
    -- extract metadata from root node
    -- construct per-entity narration lines using concat
    -- assemble with join

  return
    narration  string
done
```

### Template: `scene-understand-<domain>.tantra`

```tantra
tantra scene-understand-<domain>

  inputs
    sentence  string

  let
    hash      = "sc1"
    root-name = scene-extract-<domain> sentence hash
    narration = scene-narrate-<domain> root-name

    -- read root and entity nodes via shabda-pairs
    -- run computation tantras
    -- detect optimization goal from sentence keywords (exact-match)
    -- check motor/resource feasibility
    -- compute path energy and optimal plan
    -- detect missing (defaulted) values via provided-flags
    -- assemble clarification block

    result = concat narration compute-block clarify-block

  return
    result  string
done
```

### Missing-Value Clarification Block Pattern

```tantra
-- 1. Read provided-flags
mp0-s = first-match l0p (fn p -> cond (eq (nth p 0) "mass-provided") (nth p 1) otherwise _none)

-- 2. Determine which groups have missing values
mass-miss = cond (eq mp0-s "no") "yes" otherwise "no"

-- 3. Pre-compute note strings
mass-note-str = concat "\n    link masses (default: " (to-string lm-def) " kg/link)"
mass-note     = cond (eq mass-miss "yes") mass-note-str otherwise ""

-- 4. Pre-compute suggestion strings
mass-q = cond (eq mass-miss "yes") "\n    \"Link masses are [m0] kg and [m1] kg.\"" otherwise ""

-- 5. Assemble with pre-computed variables (not nested concat inside cond)
any-missing = cond (eq mass-miss "yes") "yes" otherwise "no"
clarify-body = concat "\n\nNot specified (defaults used):" mass-note "\n\nFor accurate results:" mass-q
clarify-block = cond (eq any-missing "yes") clarify-body otherwise ""
```

---

## 7. Adding a New Domain (Step by Step)

### Step 1: Concept nodes

Create `brahman/kosha/<domain>/<domain>.om`:
```
nigamana <domain>-concept-name
  layer: kosha
  slokas: relevant-domain-swarupa
  shabda: description:what-this-is
```

### Step 2: Units

Add to the 3 files (see §4): `matra-beeja.shabda`, `matra-aayaama.shabda`, `unit-aliases.shabda`.

### Step 3: Language layer

Create `brahman/kosha/language/english/<domain>-defaults.shabda`:
```shabda
default-entity-count:2
default-property-a:1.0
default-property-b:0.5
```

Create `brahman/kosha/language/english/<domain>-words.shabda` for goal keywords:
```shabda
goal-trigger:minimize
goal-trigger:optimize
minimize:property-a
minimize:time
```

### Step 4: Extraction tantra

Create `brahman/yantra/scene/scene-extract-<domain>.tantra`.
- Tokenise, classify, detect entity count and goals
- Call `extract-value-units classified`
- Load defaults from `<domain>-defaults.shabda`
- Emit nodes with `emit-node` and provided-flags
- Return root node name

### Step 5: Computation tantras

Create `brahman/yantra/<domain>/<computation>.tantra` for each computation.
- Pure: inputs → let → return → done
- No side effects; no emitting nodes
- Returns a list for multi-value results

### Step 6: Narration tantra

Create `brahman/yantra/scene/scene-narrate-<domain>.tantra`.
- Reads graph nodes via `shabda-pairs`
- Constructs human-readable text
- Uses `"?"` fallbacks for missing optional values

### Step 7: Scene-understand tantra

Create `brahman/yantra/scene/scene-understand-<domain>.tantra`.
- Calls extract → narrate → compute → clarify
- Detects optimization goals with exact-match keyword scan
- Assembles final result string

### Step 8: Wire entry point

In `brahman/yantra/scene/scene-understand.tantra`, add a branch:
```tantra
let <domain>-result = cond (eq scene-type "<domain>") (scene-understand-<domain> sentence) otherwise ""
```

### File Naming Conventions

| Purpose                    | Canonical path                                              |
|----------------------------|-------------------------------------------------------------|
| Concept node               | `brahman/kosha/<domain>/<concept>.om`                      |
| Domain root node           | `brahman/kosha/<domain>/<domain>.om`                       |
| Unit seeds                 | `brahman/kosha/physics/matra-beeja.shabda`                 |
| Unit dim vectors           | `brahman/kosha/physics/matra-aayaama.shabda`               |
| Unit aliases               | `brahman/kosha/language/english/unit-aliases.shabda`       |
| Scene defaults             | `brahman/kosha/language/english/<domain>-defaults.shabda`  |
| Goal keywords              | `brahman/kosha/language/english/goal-words.shabda`         |
| Extraction tantra          | `brahman/yantra/scene/scene-extract-<domain>.tantra`       |
| Narration tantra           | `brahman/yantra/scene/scene-narrate-<domain>.tantra`       |
| Understanding tantra       | `brahman/yantra/scene/scene-understand-<domain>.tantra`    |
| Computation tantras        | `brahman/yantra/<domain>/<computation>.tantra`             |
| Physics (existing)         | `brahman/yantra/bhautika/<name>.tantra`                    |
| Math/vector (existing)     | `brahman/yantra/vidnyana/<name>.tantra`                    |

---

## 8. Path Energy & Optimization

### Invariant

For any process moving something (joints, charges, heat):

```
E = Σ effort_i × |change_i|
```

Where:
- `effort` = torque (N·m), force (N), voltage (V), heat flux (W/K)
- `change` = angle (rad), displacement (m), charge (C), temperature (K)

**E is invariant with respect to speed.** Only the time T changes.
Power P = E/T. As T increases, P decreases. As T decreases, P increases.

### Pareto Optimum

To minimize both T and P simultaneously, minimize L = T + E/T:

```
dL/dT = 1 - E/T² = 0  →  T* = √E
```

At T*: P* = E/T* = E/√E = √E. So T* = P* = √E.

This gives the Pareto-optimal balanced plan. Any deviation increases either T or P.

**Practical plan selection:**

```tantra
-- Time-optimal: T = T_min (speed-limited by rated max)
-- Power-optimal: T = 3*T* (practical example; P decreases as T increases)
-- Balanced: T = T* = sqrt(path-energy)
```

**Domain generalization:**

| Domain      | effort     | change      | unit      |
|-------------|------------|-------------|-----------|
| Robotics    | torque     | Δangle      | J         |
| Linear mech | force      | displacement| J         |
| Electrical  | voltage    | charge      | J         |
| Thermal     | heat flux  | ΔT          | J         |

### Goal Detection (Exact-Match Pattern)

```tantra
sent-words   = split (lower sentence) " "
-- Use eq not starts-with: "power" != "powers", "time" != "timeout"
saw-minimize = cond (exists (first-match sent-words (fn w -> cond (eq w "minimize") "yes" otherwise _none))) "yes" otherwise "no"
saw-pw-goal  = cond (exists (first-match sent-words (fn w -> cond (eq w "power") "yes" otherwise _none))) "yes" otherwise "no"
saw-t-goal   = cond (exists (first-match sent-words (fn w -> cond (eq w "time") "yes" otherwise _none))) "yes" otherwise "no"
saw-fastest  = cond (exists (first-match sent-words (fn w -> cond (eq w "fastest") "yes" (eq w "quickest") "yes" otherwise _none))) "yes" otherwise "no"

-- Combine: needs trigger AND objective
wants-min-pw = cond (eq saw-minimize "yes") saw-pw-goal otherwise "no"
wants-min-t-a = cond (eq saw-minimize "yes") saw-t-goal otherwise "no"
wants-min-t   = cond (eq saw-fastest "yes") "yes" otherwise wants-min-t-a
```

---

## 9. Classify-Fold Pipeline

```
sentence
  → tokenise          → ["A", "2", "-DOF", "arm", ...]
  → lower             → ["a", "2", "-dof", "arm", ...]
  → classify-fold     → [[word, kind, resolved], ...]
```

### Token Kinds

| Kind        | Description                                    | Example                        |
|-------------|------------------------------------------------|--------------------------------|
| `compound`  | Multi-word concept resolved via bigram join    | `"angular velocity"` → `angular-velocity` |
| `seema`     | Boundary / punctuation token                   | `"."`, `","`, `"and"`          |
| `aggregation` | Grouping marker                              | `"respectively"`               |
| `concept`   | Known graph node (concept or unit)             | `"velocity"`, `"radian"`       |
| `avastha`   | State/modifier word                            | `"max"`, `"rated"`             |
| `number`    | Numeric literal                                | `"2.5"`, `"0"`                 |
| `unknown`   | Not in graph, not a number                     | unrecognized word               |

### Bigram Joining

Adjacent words that together form a compound concept are merged before classification:
`"joint" "speed"` → classified as `joint-speed` concept node if it exists in the graph.

### Modifier Folding

`avastha` tokens (max, rated, minimum, etc.) fold with the following concept token, modifying its resolved name.

---

## 10. All Available Ops (Quick Reference)

### Arithmetic

| Op      | Signature                | Notes                              |
|---------|--------------------------|------------------------------------|
| `add`   | variadic → float         | **Variadic — explicit arity:2 in lambda** |
| `mul`   | variadic → float         | **Variadic — explicit arity:2 in lambda** |
| `sub`   | a b → float              |                                    |
| `div`   | a b → float              | Returns 0 if b=0                   |
| `power` | base exp → float         |                                    |
| `sqrt`  | x → float                |                                    |
| `abs`   | x → float                |                                    |
| `neg`   | x → float                |                                    |
| `floor` | x → float                |                                    |
| `ceil`  | x → float                |                                    |
| `mod`   | a b → float              |                                    |
| `min`   | a b → float              |                                    |
| `max`   | a b → float              |                                    |
| `sum`   | list → float             | Reduces list by addition           |

### Trigonometry

| Op      | Signature          |
|---------|--------------------|
| `sin`   | x → float          |
| `cos`   | x → float          |
| `tan`   | x → float          |
| `asin`  | x → float          |
| `acos`  | x → float          |
| `atan2` | y x → float        |
| `log`   | x → float          |

### Comparison

| Op    | Signature         | Notes                          |
|-------|-------------------|--------------------------------|
| `eq`  | a b → bool        | String comparison              |
| `neq` | a b → bool        |                                |
| `lt`  | a b → bool        | Numeric                        |
| `le`  | a b → bool        |                                |
| `gt`  | a b → bool        |                                |
| `ge`  | a b → bool        |                                |

### Boolean

| Op    | Signature         | Notes                             |
|-------|-------------------|-----------------------------------|
| `and` | variadic → bool   | **Variadic — pre-compute in lambda** |
| `or`  | variadic → bool   | **Variadic — pre-compute in lambda** |
| `not` | bool → bool       |                                   |

### String

| Op              | Signature              | Notes                                    |
|-----------------|------------------------|------------------------------------------|
| `concat`        | variadic → string      | **Variadic — avoid as last lambda expr** |
| `split`         | str delim → list       |                                          |
| `join`          | list sep → string      |                                          |
| `upper`         | str → str              |                                          |
| `lower`         | str → str              |                                          |
| `starts-with`   | str prefix → bool      |                                          |
| `string-length` | str → float            |                                          |
| `char-at`       | str i → str            |                                          |
| `to-string`     | any → string           |                                          |
| `to-number`     | str → float \| _none   |                                          |

### List

| Op            | Signature                   | Notes                                    |
|---------------|-----------------------------|------------------------------------------|
| `map`         | list fn → list              |                                          |
| `filter`      | list fn → list              |                                          |
| `reduce`      | list init fn → value        | fn takes (acc, item)                     |
| `first-match` | list fn → value \| _none    | Returns _none (not false) on no match    |
| `fold-pairs`  | list fn → list              | Slides window of 2                       |
| `fold-triples`| list fn → list              | Slides window of 3                       |
| `nth`         | container i → value         | Works on list, VPair, VBinding           |
| `length`      | list → float                |                                          |
| `append`      | list list → list            |                                          |
| `flatten`     | list-of-lists → list        |                                          |
| `range`       | n → [0..n-1]                |                                          |
| `member`      | value list → bool           |                                          |
| `unique`      | list → list                 | Dedup by string key                      |
| `sort-desc`   | list → list                 | Sorts [[v, score]] pairs descending      |
| `sum`         | list → float                |                                          |
| `frequencies` | list → [[value, count]]     |                                          |
| `exists`      | value → bool                | False for VNone, true otherwise          |

### Constructors

| Op      | Signature             | Notes                               |
|---------|-----------------------|-------------------------------------|
| `pair`  | name value → VPair    | name always stringified             |
| `bind`  | name float → VBinding |                                     |

### Graph

| Op              | Signature                    | Notes                             |
|-----------------|------------------------------|-----------------------------------|
| `shabda`        | node-name key → string       | Reads node metadata               |
| `shabda-pairs`  | node-name → [[k,v], ...]     | All metadata as list of pairs     |
| `emit-node`     | name layer slokas shabda → _ | Creates/joins graph node          |
| `outgoing-edges`| node-name → list             | All edges from node               |
| `incoming-to`   | node-name → list             | Nodes with edges pointing here    |
| `dim-vector`    | unit-name → list             | SI exponent vector or _none       |

### Dimension / Unit

| Op              | Signature                  |
|-----------------|----------------------------|
| `dim-vector`    | name → [M,L,T,I,θ,N,J,s]  |
| `matra-viveka`  | vec → string               |

### Vector / Matrix

| Op          | Signature                      |
|-------------|--------------------------------|
| `vec-add`   | [a] [b] → [a+b]                |
| `vec-sub`   | [a] [b] → [a-b]                |
| `vec-scale` | s [a] → [s·a]                  |
| `vec-dot`   | [a] [b] → float                |
| `vec-norm`  | [a] → float                    |
| `vec-nth`   | [a] i → float                  |
| `rot2d`     | theta [x,y] → [x',y']          |
| `mat-mul`   | A ncols B pcols → C (flat)     |

### Scene / NL

| Op                           | Signature                            |
|------------------------------|--------------------------------------|
| `tokenise`                   | sentence → list of words             |
| `classify-fold`              | words → [[word, kind, resolved]]     |
| `extract-value-units`        | classified → [[v,concept,unit,idx]]  |
| `shabda-pairs`               | node-name → [[k,v]]                  |
| `motor-check`                | tq pw rated-tq rated-pw → [ok,...]   |
| `arm-plan-2dof`              | l1 l2 th1 th2 tx ty w1 w2 → plan    |
| `scene-understand`           | sentence → string                    |

---

## 11. Critical Pitfalls

### Pitfall 1: Variadic ops in lambda bodies

`add`, `mul`, `or`, `and`, `concat` consume ALL remaining tokens as args when used inside a lambda body. Without a boundary, the variadic op eats past the intended end of the `let` binding into the return expression (or beyond the lambda).

**Two fixes:**

**Fix A (preferred for multi-arg concat in let):** Wrap the variadic call in parentheses. This gives the parser an explicit boundary:

```tantra
-- WRONG: concat eats past "]" into the return expression
reduce lst "" (fn acc i ->
  let ln = concat "\n  joint" (to-string i) ": " (to-string val) " units"
  concat acc ln)
-- Result: ln evaluates to string "ln", output shows "lnln" artifacts

-- RIGHT: parentheses bound the variadic call
reduce lst "" (fn acc i ->
  let ln = (concat "\n  joint" (to-string i) ": " (to-string val) " units")
  concat acc ln)
-- Result: ln holds the formatted string, accumulator builds correctly
```

**Fix B (for simple 2-arg cases):** Pre-compute into a named variable, return the variable:

```tantra
-- WRONG
map lst (fn x -> add x offset rest-of-expression)

-- RIGHT
map lst (fn x ->
  let s = add x offset
  s)
```

**Rule of thumb:** If a `let` binding uses a variadic op with more than 2 args, always wrap in `(...)`. If a variadic op is the final expression of a lambda, limit it to 2 args or pre-compute.

### Pitfall 2: Nested `(cond)` or `(concat)` as cond branch body

The `(` handler in the parser interprets `(cond...)` as `(guard) body` pair, consuming the closing `)` as the guard's paren, then calls `parse_expr` on empty tokens → `failwith "parse_expr: empty"` → bubbles up as `Arg_overconsumed` → op evaluates to `VString "op-name"`.

**Fix**: Flatten all nested conds to a single cond chain. Pre-compute complex branches into named variables.

```tantra
-- WRONG
cond a b (cond c d otherwise e)

-- RIGHT
cond a b c d otherwise e
```

### Pitfall 3: Local function calls (`let f = fn...`)

Named functions defined with `let f = fn...` have arity 0 when looked up later. Calling `f arg` evaluates to `VString "f"` (the name), silently ignoring the arg.

**Fix**: Always inline lambdas directly into `map`, `filter`, `first-match`, `reduce`.

### Pitfall 4: Node shabda overwrite (units)

`Proof_graph.join` merges edges but keeps the **existing** node's shabda (not the incoming one). `matra-nirmana` emits unit nodes from `matra-beeja.shabda` **before** `.om` files load.

If you put `concepts-for-unit` in a `.om` file for a unit already defined in `matra-beeja.shabda`, that `.om` shabda is silently ignored.

**Fix**: Put all unit metadata including `concepts-for-unit` directly in `matra-beeja.shabda` — that's the single source of truth for generated units.

### Pitfall 5: Defaults masking missing values

Never test the value to decide if clarification is needed. The value `5.0` means nothing — it could be real data or a default. Only the `provided`-flag is authoritative:

```tantra
-- WRONG: testing value
cond (gt rt0 0) "ok" otherwise "missing"

-- RIGHT: testing the flag
cond (eq rtorq-provided "no") "missing" otherwise "ok"
```

### Pitfall 6 (NEW): Tokeniser attaches brackets to numbers

`tokenise` does not strip bracket/paren characters when they are adjacent to a number token. `"[0.4, 0.3]"` tokenises to `["[0.4", "0.3]"]` — not `["0.4", "0.3"]`. `to-number "[0.4"` returns `_none`.

**Fix**: Before calling `to-number` on any token that may be a bracketed coordinate, strip `[`, `]`, `(`, `)` via `split`/`filter`/`join`:

```tantra
-- strip brackets so "[0.4" and "0.3]" parse correctly
let clean = (join (filter (split tok "") (fn c ->
  and (neq c "[") (neq c "]") (neq c "(") (neq c ")"))) "")
let as-num = to-number clean
```

**Applies to**: any target-position scan, coordinate extraction, or any numeric scan over tokenised input that may include list/tuple notation.

### Pitfall 7 (was 6): UTF-8 characters in string literals

The tantra parser operates on byte strings. Non-ASCII chars (→, ×, ≤, etc.) in string literals cause parse errors or corrupt output.

**Fix**: Use ASCII alternatives: `->`, `x`, `<=`, `N*m`, `rad/s`.

### Pitfall 8 (was 7): `starts-with` vs exact-match for keyword detection

`starts-with "power"` matches `"powers"`, `"powered"`, `"power-check"` etc. Use exact `eq` on the split word list:

```tantra
-- WRONG: matches "powers" in "rated motor powers"
saw-pw = exists (first-match words (fn w -> cond (starts-with w "power") "yes" otherwise _none))

-- RIGHT: exact match only
saw-pw = cond (exists (first-match words (fn w -> cond (eq w "power") "yes" otherwise _none))) "yes" otherwise "no"
```

### Pitfall 9 (was 8): `or`/`and` with multi-condition — pre-compute to bools

`or` is variadic. Inside a lambda or let-chain, `or (eq a "x") (eq b "y") rest...` eats `rest`.

```tantra
-- WRONG
let is-trig = or (eq tok "minimize") (eq tok "optimize") other-var

-- RIGHT
let is-min = eq tok "minimize"
let is-opt = eq tok "optimize"
let is-trig = or is-min is-opt
```

### Pitfall 10 (was 9): `first-match` returns `_none` not `false`

`first-match` returns `VNone` when no item matches — not `VBool false`. Use `exists` to test:

```tantra
-- WRONG: tests equality with false string
let found = first-match lst (fn x -> ...)
cond (eq found "false") ...   -- never triggers

-- RIGHT
let found = first-match lst (fn x -> ...)
cond (exists found) "yes" otherwise "no"
```

### Pitfall 11 (was 10): `pair` first arg always stringified

`VPair (name, value)` — the first element is always a string. `nth pair 0` returns `VString name`. Use `nth` consistently; never pattern-match on pair structure in tantra:

```tantml
let kv-pair = pair "my-key" 42
let k = nth kv-pair 0   -- "my-key" (string)
let v = nth kv-pair 1   -- 42 (float)
```

### Pitfall 12 (REFINED): Single-return vs multi-return access pattern

The access pattern depends on how many values a tantra returns — not merely whether a return is a list or scalar.

| Return declaration | Access pattern | Example |
|---|---|---|
| Single scalar (`return x float`) | `nth result 0` | `let e = nth (path-energy-ndof ...) 0` |
| Single list (`return x list`) | use result directly | `let coords = extract-vector-coords ...` |
| Multiple returns (any mix) | `nth result N` for slot N | `nth jd 5` for 6th return of read-joint-data |

**Single list return — flattened into VList:**

When a tantra declares only `return coords list`, the engine flattens the list elements into the VList — NOT a VList wrapping one inner list.

```tantra
-- WRONG: applying nth to a single-list return
let tq-res  = torque-gravity-ndof n masses lengths g
let torques = nth tq-res 0    -- gets only element 0, not the whole list

-- RIGHT: use directly
let torques = torque-gravity-ndof n masses lengths g
let tq0     = nth torques 0   -- correct
let tq1     = nth torques 1   -- correct
```

**Multiple returns — nth by slot index works for all types:**

When a tantra has multiple return lines (even if some are lists), `nth result N` gives the Nth slot as-is — list slots come back as usable lists.

```tantra
-- read-joint-data returns 12 lists — nth jd N works fine:
let link-masses = nth jd 5    -- returns the full list at slot 5

-- joint-velocity-ndof: omegas list; t-safe float
let omegas = nth vr-res 0     -- full list at slot 0
let t-move = nth vr-res 1     -- scalar at slot 1

-- velocity-plan-ndof: t-opt float; t-budget float; omegas-opt list; omegas-slow list; ...
let t-opt      = nth vp-res 0   -- scalar
let omegas-opt = nth vp-res 2   -- full list
```

**Diagnostic**: if joint 1+ values appear wrong (all equal to joint 0's value), check whether a single-list-return tantra is being accessed with `nth result 0` instead of directly.

### Pitfall 13 (was 11): `reduce` — last expression is the return value

In a reduce lambda with multiple `let` bindings, the expression **after the final `let` binding** is the return value. An accidental trailing let with no expression after returns the value of that let-binding's name:

```tantra
-- The final expression (here a list literal) is the accumulator update
reduce lst init (fn acc x ->
  let part-a = nth acc 0
  let part-b = nth acc 1
  let new-a  = add part-a x
  [new-a, part-b])   -- THIS is the return value — must be explicit
```

---

## 12. Existing Domain Coverage

### Fully Implemented

| Domain             | Location                          | Tantras                                        |
|--------------------|-----------------------------------|------------------------------------------------|
| Kinematics (2-DOF) | `brahman/yantra/robotics/`        | `ik-2dof`, `fk-2dof`, `arm-plan-2dof`, `joint-velocity-2dof` |
| 3D FK (n-DOF)      | `brahman/yantra/robotics/`        | `fk-ndof`, `fk-yz-prismatic`, `ik-yz-prismatic` |
| Physics (30+)      | `brahman/yantra/bhautika/`        | Forces, energy, oscillators, optics, circuits, thermodynamics |
| Math               | `brahman/yantra/vidnyana/`        | vec ops, rot2d, rot3d, mat-mul, trig, log, polynomial |
| Unit system        | `brahman/kosha/physics/`          | Full SI, scaled variants, aliases              |
| NL classification  | `brahman/yantra/classify-fold.tantra` | Tokenise, bigram join, modifier fold       |
| Scene              | `brahman/yantra/scene/`           | kinematic-chain fully wired                    |

### Scene Types with Defaults

| Scene type         | Defaults file                              | Status          |
|--------------------|--------------------------------------------|-----------------|
| kinematic-chain    | `scene-defaults-kinematic-chain.shabda`    | Complete        |
| circuit            | (planned)                                  | Stub            |
| oscillator         | (planned)                                  | Stub            |
| pulley-system      | (planned)                                  | Stub            |

### Known Limitations

- `scene-understand-kinematic-chain` hardcoded to read joints 0, 1, 2 (not fully n-DOF); generalization needed
- `arm-plan-2dof` computes IK only for first 2 revolute joints in XY; Jacobian IK for n-DOF pending
- Motor torque estimate is gravity-load only (no dynamic / inertial load)

---

## 13. Testing

### Build
```bash
cd vyakarana && dune build
```

### Scene query
```bash
cd vyakarana && dune exec vyakarana/bin/vyakarana.exe -- \
  "A 2-DOF robot arm. Links are 0.3 m and 0.4 m. Move to (0.5, 0.3)."
```

### Physics computation
```bash
cd vyakarana && dune exec vyakarana/bin/vyakarana.exe -- \
  "A mass of 5 kg falls from height 10 m. What is the kinetic energy at the bottom?"
```

### Graph inspection (darshana)
```bash
cd vyakarana && dune exec vyakarana/bin/vyakarana.exe -- \
  "show radian-per-second"
```

### Unit check
```bash
cd vyakarana && dune exec vyakarana/bin/vyakarana.exe -- \
  "what are the dimensions of newton-metre"
```

---

## Appendix: Reference Tantras

### `extract-value-units.tantra` (two-pass Sphoṭa extraction)

Located: `brahman/yantra/scene/extract-value-units.tantra`

```tantra
tantra extract-value-units
  inputs
    classified  list    -- output of classify-fold

  let
    unit-alias-pairs = shabda-pairs "unit-aliases"

    -- pass 1: collect raw [value, concept, unit] triples
    pass1 = reduce classified [[], _none]
      (fn acc triple ->
        let results  = nth acc 0
        let last-num = nth acc 1
        let word     = nth triple 0
        let kind     = nth triple 1
        let resolved = nth triple 2
        let as-num    = to-number word
        let is-number = exists as-num
        let direct-vec = cond (eq kind "concept") (dim-vector resolved) otherwise _none
        let alias-name = cond (not (exists direct-vec))
          (first-match unit-alias-pairs (fn kv -> cond (eq (nth kv 0) word) (nth kv 1) otherwise _none))
          otherwise _none
        let unit-vec   = cond (exists direct-vec) direct-vec (exists alias-name) (dim-vector alias-name) otherwise _none
        let unit-name  = cond (exists direct-vec) resolved (exists alias-name) alias-name otherwise ""
        let is-unit    = exists unit-vec
        let cands   = cond is-unit (split (shabda unit-name "concepts-for-unit") ",") otherwise (range 0)
        let concept = cond (gt (length cands) 0) (nth cands 0) otherwise unit-name
        let new-results = cond (and is-unit (exists last-num))
          (append results [[last-num, concept, unit-name]])
          otherwise results
        let new-num = cond is-number as-num is-unit _none otherwise last-num
        [new-results, new-num])

    raw-triples = nth pass1 0

    -- pass 2: assign joint-idx by position within concept group
    result = reduce raw-triples [] (fn acc t ->
      let concept = nth t 1
      let idx     = length (filter acc (fn r -> eq (nth r 1) concept))
      append acc [[nth t 0, concept, nth t 2, idx]])

  return
    result  list
done
```

### `arm-plan-2dof.tantra` (2-DOF IK + velocity + FK verify)

Located: `brahman/yantra/robotics/arm-plan-2dof.tantra`

```tantra
tantra arm-plan-2dof
  inputs
    link-length-1   float  metre
    link-length-2   float  metre
    theta1-current  float  radian
    theta2-current  float  radian
    target-x        float  metre
    target-y        float  metre
    omega1-max      float  radian-per-second
    omega2-max      float  radian-per-second

  let
    -- IK
    cos-theta2 = div (sub (add (mul target-x target-x) (mul target-y target-y))
                         (add (mul link-length-1 link-length-1) (mul link-length-2 link-length-2)))
                    (mul 2 (mul link-length-1 link-length-2))
    theta2     = acos cos-theta2
    alpha      = atan2 target-y target-x
    beta       = atan2 (mul link-length-2 (sin theta2))
                       (add link-length-1 (mul link-length-2 cos-theta2))
    theta1     = sub alpha beta
    -- FK verify
    j2x = mul link-length-1 (cos theta1)
    j2y = mul link-length-1 (sin theta1)
    ex  = add j2x (mul link-length-2 (cos (add theta1 theta2)))
    ey  = add j2y (mul link-length-2 (sin (add theta1 theta2)))
    -- synchronized velocity
    delta-theta1 = sub theta1 theta1-current
    delta-theta2 = sub theta2 theta2-current
    move-time    = max (div (abs delta-theta1) omega1-max)
                       (div (abs delta-theta2) omega2-max)
    omega1 = div delta-theta1 move-time
    omega2 = div delta-theta2 move-time

  return
    theta1 theta2 omega1 omega2 move-time j2x j2y ex ey
done
```
