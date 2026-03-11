# Phase CS — Computation Kosha Full Restructure

**Status**: NOT YET STARTED. Follows Phase 2.9 (math).

**Regression baseline**: 49/52 passing. Do not break further.

---

## Overview

Restructure `brahman/kosha/computation/` from a flat `concepts/` bucket into a proper
sub-varga hierarchy: `types/`, `control/`, `state/`, `concurrency/`, `modules/`,
`hardware/`. Each sub-varga gets `structures/` / `properties/` / `operations/` internally
— the same three-way split as math.

The current `concepts/` directory has the right nodes but the wrong structure:
- Three varga nodes (`type-varga`, `computation-varga`, `memory-varga`) exist but
  **nothing declares `type-varga-vishesa` or `computation-varga-vishesa`** — the varga
  hierarchy is declared but not connected. Every leaf just says `domain-cs-sthita`.
- `subanta-swarupa` on varga nodes — wrong, CS has no subanta/tinanta split.
- `domain-cs-sthita` on every leaf — should be inherited through the varga chain.
- Six entire topic areas have zero nodes: type algebra, functional properties,
  concurrency, module system, error handling, and hardware.

---

## Edge vocabulary (CS — same as math)

CS uses the same three subdir types as math with the same edge suffixes:

| subdir | edge suffix | meaning |
|---|---|---|
| `structures/` | `X-varga-vishesa` | leaf IS a particular structural construct of that class |
| `properties/` | `X-varga-lakshana` | leaf IS a characterising property that holds of that class |
| `operations/` | `X-varga-karma` | leaf IS an operation or transformation within that class |

`lakshana` carries the same meaning as in math — characterising marks that hold over
structures, neither measured quantities (subanta) nor temporal processes (tinanta).

---

## Preparatory changes

### `cs-varga.om` — thin it

Remove:
- `subanta-swarupa` — CS has structures/properties/operations, not subanta/tinanta
- `domain-cs-sthita` on the varga node itself is fine — it IS the domain anchor

### `domain-cs.om` — thin it

Remove the flat `yukta` list of every CS concept. Keep only domain anchor identity and
its connection to `domain-computation` and `domain-vak`.

### Three old varga nodes — retire and replace

`type-varga`, `computation-varga`, `memory-varga` in `concepts/` are replaced by the
new sub-varga nodes. They had `cs-varga-vishesa` but no leaves used them. Delete them
once migration is complete.

### No `domain-cs-sthita` on individual leaves

Leaves inherit domain membership through the varga chain. `cs-varga` carries it once.

---

## Directory skeleton

```
brahman/kosha/computation/
  cs-varga.om              ← thin: remove subanta-swarupa
  domain-cs.om             ← thin: just domain anchor identity
  domain-computation.om    ← stays (hardware-level domain anchor)
  bit.om                   ← MOVE to hardware/structures/ + add hardware-varga-vishesa
                              + add information-varga-vishesa (from math phase 2.9)
  qubit.om                 ← MOVE to hardware/structures/
  computer.om              ← MOVE to hardware/structures/
  instruction.om           ← MOVE to hardware/structures/
  classical-computer.om    ← MOVE to hardware/structures/
  quantum-computer.om      ← MOVE to hardware/structures/
  quantum-gate.om          ← MOVE to hardware/structures/
  quantum-vyakarana.om     ← MOVE to hardware/structures/
  llm.om                   ← MOVE to hardware/structures/

  types/
    types-varga.om          "cs-varga-vishesa" + viveka-yukta niyama-yukta seema-yukta
    structures/             type, primitive-type, composite-type,
                            int, float, bool, nil, cs-string,
                            array, cs-list, cs-map, record, tuple,
                            sum-type [NEW], product-type [NEW], option-type [NEW],
                            result-type [NEW], algebraic-data-type [NEW],
                            variant [NEW], enum [NEW]
    properties/             primitive [NEW], composite [NEW], mutable [NEW],
                            immutable [NEW], nullable [NEW], opaque [NEW]
    operations/             type-check [NEW], type-infer [NEW], type-unify [NEW],
                            pattern-match [NEW], destructure [NEW]

  control/
    control-varga.om        "cs-varga-vishesa" + krama-yukta viveka-yukta avrti-yukta
    structures/             algorithm, callable, expression, statement,
                            conditional, loop, recursion, closure,
                            higher-order-function [NEW], continuation [NEW]
    properties/             terminating [NEW], deterministic [NEW],
                            tail-recursive [NEW], pure [NEW], total [NEW]
    operations/             apply [NEW], fold [NEW], map-op [NEW],
                            filter-op [NEW], compose [NEW], curry [NEW]

  state/
    state-varga.om          "cs-varga-vishesa" + avastha-yukta niyama-yukta smarana-yukta
    structures/             binding, scope, identifier, variable,
                            assignment, mutation, stack, parameter,
                            argument, return-value, naming-convention,
                            entry-point, lifecycle, event-loop, clock-cycle,
                            signal, propagation
    properties/             mutable-state [NEW], immutable-state [NEW],
                            lexical [NEW], dynamic-scope [NEW], closed-over [NEW]
    operations/             bind [NEW], rebind [NEW], capture [NEW],
                            assign-op [NEW], dereference [NEW]

  concurrency/
    concurrency-varga.om    "cs-varga-vishesa" + kaala-yukta sandhi-yukta viveka-yukta
    structures/             thread [NEW], process-cs [NEW], channel [NEW],
                            mutex [NEW], semaphore [NEW], actor [NEW],
                            async-task [NEW], future [NEW], promise [NEW]
    properties/             atomic [NEW], blocking [NEW], non-blocking [NEW],
                            race-condition [NEW], deadlock [NEW]
    operations/             spawn [NEW], send-msg [NEW], receive-msg [NEW],
                            lock [NEW], unlock [NEW], await-op [NEW], yield [NEW]

  modules/
    modules-varga.om        "cs-varga-vishesa" + rachana-yukta niyama-yukta shakha-yukta
    structures/             module [NEW], namespace [NEW], interface [NEW],
                            trait [NEW], signature [NEW], dependency [NEW],
                            package [NEW]
    properties/             abstract [NEW], opaque-module [NEW], open [NEW],
                            sealed [NEW]
    operations/             import [NEW], export [NEW], open-module [NEW],
                            functor-apply [NEW], instantiate [NEW]

  hardware/
    hardware-varga.om       "cs-varga-vishesa" + spanda-yukta niyama-yukta eka-aneka-yukta
    structures/             bit, qubit, computer, instruction,
                            classical-computer, quantum-computer,
                            quantum-gate, quantum-vyakarana, llm
    properties/             deterministic-hw [NEW], probabilistic [NEW],
                            reversible [NEW]
    operations/             gate-apply [NEW], measure [NEW],
                            execute-instruction [NEW], clock-tick [NEW]
```

---

## Cross-domain nodes (multiple varga-lakshana edges)

Some CS properties hold across multiple sub-vargas. One node, multiple edges:

```
pure            → "control-varga-lakshana" "state-varga-lakshana"
                  "satya-yukta"             (no side effect = truthful)
immutable       → "types-varga-lakshana" "state-varga-lakshana"
                  "purna-yukta"             (cannot be changed = whole/fixed)
terminating     → "control-varga-lakshana" "complexity-varga-lakshana"
                  "seema-yukta"             (reaches a bound)
deterministic   → "control-varga-lakshana" "hardware-varga-lakshana"
                  "niyama-yukta"            (same input → same output)
atomic          → "concurrency-varga-lakshana" "state-varga-lakshana"
                  "purna-yukta"             (indivisible = whole)
```

`complexity-varga` is in math — `terminating` bridges CS control and math complexity.
One node, both `control-varga-lakshana` and `complexity-varga-lakshana`.

---

## Sangati root connections to add (during migration)

### Existing nodes gaining new sangati roots

```
algorithm       → krama-yukta niyama-yukta
callable        → aadana-visarjana-yukta
recursion       → avrti-yukta              (already has avrti-swarupa — confirm)
loop            → avrti-yukta krama-yukta
closure         → dharana-yukta smarana-yukta
scope           → seema-yukta
binding         → sama-yukta               (a name IS its value)
stack           → parampara-yukta
signal          → sambandha-yukta
event-loop      → avrti-yukta spanda-yukta
clock-cycle     → spanda-yukta avrti-yukta
entry-point     → aarambham-yukta
lifecycle       → krama-yukta aarambham-yukta kshaya-yukta
```

### New nodes — sangati roots

| node | sub-varga / subdir | sangati roots |
|---|---|---|
| `sum-type` | `types/structures/` | `dvandva-yukta viveka-yukta` |
| `product-type` | `types/structures/` | `rachana-yukta vrnda-yukta` |
| `option-type` | `types/structures/` | `abhava-yukta viveka-yukta` |
| `result-type` | `types/structures/` | `satya-yukta viparita-yukta` |
| `algebraic-data-type` | `types/structures/` | `rachana-yukta viveka-yukta` |
| `variant` | `types/structures/` | `viveka-yukta dvandva-yukta` |
| `enum` | `types/structures/` | `vrnda-yukta seema-yukta` |
| `immutable` | `types/properties/` | `purna-yukta` |
| `pure` | `control/properties/` | `satya-yukta abhava-yukta` |
| `terminating` | `control/properties/` | `seema-yukta kshaya-yukta` |
| `tail-recursive` | `control/properties/` | `avrti-yukta seema-yukta` |
| `higher-order-function` | `control/structures/` | `rachana-yukta krama-yukta` |
| `continuation` | `control/structures/` | `krama-yukta parampara-yukta` |
| `thread` | `concurrency/structures/` | `tantu-yukta kaala-yukta` |
| `channel` | `concurrency/structures/` | `sambandha-yukta prasarana-yukta` |
| `actor` | `concurrency/structures/` | `jiva-yukta sambandha-yukta` |
| `async-task` | `concurrency/structures/` | `kaala-yukta seema-yukta` |
| `deadlock` | `concurrency/properties/` | `vikrita-yukta seema-yukta` |
| `module` | `modules/structures/` | `rachana-yukta seema-yukta` |
| `interface` | `modules/structures/` | `viveka-yukta niyama-yukta` |
| `trait` | `modules/structures/` | `dharma-yukta viveka-yukta` |
| `dependency` | `modules/structures/` | `sambandha-yukta parampara-yukta` |
| `llm` | `hardware/structures/` | `parampara-yukta viveka-yukta` |
| `quantum-gate` | `hardware/structures/` | `vivartana-yukta spanda-yukta` |

---

## Nodes to migrate (existing → new subdir)

Every existing flat node in `concepts/` is rewritten into its new subdir.
Read old file → write fresh to new path → delete old file.

### `types/structures/`
`type`, `primitive-type`, `composite-type`, `int`, `float`, `bool`, `nil`,
`cs-string`, `array`, `cs-list`, `cs-map`, `record`, `tuple`

When rewriting, replace:
- `domain-cs-sthita` → remove (inherited)
- `subanta-swarupa` (on varga nodes) → remove
- `primitive-type-swarupa` / `composite-type-swarupa` → replace with `types-varga-vishesa`
- Add specific sangati roots from the table above

### `control/structures/`
`algorithm`, `callable`, `expression`, `statement`, `conditional`, `loop`,
`recursion`, `closure`

When rewriting, replace:
- `domain-cs-sthita` → remove (inherited)
- `algorithm-sthita` on nodes that are subkinds → replace with `control-varga-vishesa`

### `state/structures/`
`binding`, `scope`, `identifier`, `variable`, `mutation`, `assignment`, `stack`,
`parameter`, `argument`, `return-value`, `naming-convention`,
`entry-point`, `lifecycle`, `event-loop`, `clock-cycle`, `signal`, `propagation`

### `hardware/structures/`
`bit`, `qubit`, `computer`, `instruction`, `classical-computer`,
`quantum-computer`, `quantum-gate`, `quantum-vyakarana`, `llm`

When rewriting hardware nodes, replace:
- `domain-cs-sthita` / `domain-computation-sthita` → remove (inherited)
- Add `hardware-varga-vishesa`

---

## Nodes already in bhasha that need kosha foundation

These are currently in `brahman/bhasha/ocaml/` with no kosha node under them.
Once the CS kosha restructure is done, these bhasha nodes need a `dhatu` edge added
pointing to the new kosha node:

| bhasha node | needs dhatu → | new kosha node |
|---|---|---|
| `brahman/bhasha/ocaml/functor.om` | → | `modules/operations/functor-apply` |
| `brahman/bhasha/ocaml/module-system.om` | → | `modules/structures/module` |
| `brahman/bhasha/ocaml/algebraic-data-type.om` | → | `types/structures/algebraic-data-type` |

---

## Build sequence

1. **Create all directory skeletons** (mkdir only, no files yet)
2. **Thin `cs-varga.om`** — remove `subanta-swarupa`; **thin `domain-cs.om`** — remove flat yukta list
3. **Migrate `hardware/` batch** — rewrite all 9 root-level hardware nodes into `hardware/structures/`; add `hardware-varga-vishesa`; delete old files
4. **Migrate `types/` batch** — rewrite 13 existing concept nodes into `types/structures/`; add new type algebra nodes (`sum-type`, `product-type`, `option-type`, `result-type`, `algebraic-data-type`, `variant`, `enum`); add `types/properties/` and `types/operations/` nodes
5. **Migrate `control/` batch** — rewrite 8 existing nodes; add new nodes (`higher-order-function`, `continuation`); add properties (`pure`, `terminating`, `tail-recursive`, `deterministic`) and operations (`apply`, `fold`, `map-op`, `filter-op`, `compose`, `curry`)
6. **Migrate `state/` batch** — rewrite 17 existing nodes; add properties and operations
7. **Build `concurrency/` sub-varga** — all new: `thread`, `process-cs`, `channel`, `mutex`, `semaphore`, `actor`, `async-task`, `future`, `promise`; properties and operations
8. **Build `modules/` sub-varga** — all new: `module`, `namespace`, `interface`, `trait`, `signature`, `dependency`, `package`; properties and operations
9. **Add sangati root connections** to all migrated nodes (see table above)
10. **Retire old varga nodes** — delete `type-varga.om`, `computation-varga.om`, `memory-varga.om` from `concepts/` (replaced by the new sub-vargas)
11. **Delete `concepts/` directory** once empty
12. **Update bhasha/ocaml nodes** — add `dhatu` edges to `functor.om`, `module-system.om`, `algebraic-data-type.om`
13. **Run regression after each batch** — target 49/52 throughout

---

## Rewrite pattern for leaf nodes

**ALWAYS**: read old file → write fresh to new subdir path → delete old file.
Never move-then-edit. Never leave a broken intermediate state.

When rewriting an existing node:
- Add `X-varga-vishesa` (structures), `X-varga-lakshana` (properties), or `X-varga-karma` (operations)
- Remove `domain-cs-sthita` — inherited through varga chain
- Remove `subanta-swarupa` — CS leaves don't declare pada
- Remove `primitive-type-swarupa` / `composite-type-swarupa` / `algorithm-sthita` where used as IS-A — replace with the new varga-vishesa edge
- Add sangati root connections from the tables above
- Keep all node-specific content (relationships, shabda)

---

## Key rules

- Sangati nodes must NOT reference kosha domain nodes. Direction always kosha → sangati.
- No `domain-cs-sthita` on individual leaves — inherited through varga chain.
- `process-cs` not `process` — to avoid clash with the general `kosha/process.om` node.
- `map-op` not `map` — `cs-map` is the structure; `map-op` is the higher-order operation.
- `send-msg` / `receive-msg` not `send` / `receive` — avoid clash with network concepts.
- `assign-op` not `assign` — `assignment` is the structure; `assign-op` is the operation.
- `await-op` not `await` — avoid potential keyword clash in bhasha nodes.
- `open-module` not `open` — avoid clash with file I/O.
- Cross-domain nodes (`pure`, `immutable`, `terminating`, `deterministic`, `atomic`)
  get multiple `X-varga-lakshana` edges — do NOT duplicate them per sub-varga.
