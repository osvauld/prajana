# Engine / Tantra Migration Plan

**Status**: Analysis complete. Implementation not yet started.
**Prerequisite for**: `graph/` sub-varga build (phase 2.9 step 10)
**Regression baseline**: 49/52 passing — do not break.

---

## Goal

Make the OCaml layer a minimal graph primitive kernel. Push all semantic
reasoning (domain detection, inheritance walking, node classification,
neighbour queries) into `.tantra` files where it can be read, tested, and
extended without recompiling. Enable higher-order tantras so one tantra can
be passed as a function to another.

---

## What the OCaml layer currently does — module map

Build order (from `lib/dune`):

```
proof_graph → event → verify → om_parser → setu_shabda → setu → setu_classify
→ anuvada → prayoga → prayoga_strudel → socket → yantra_types → yantra_bigram
→ yantra_parser → yantra_inverter → yantra_index → yantra_resolver → yantra_ops
→ yantra_eval_primitives → yantra_pipeline_ops → yantra_eval → yantra
```

### Irreducible kernel — MUST stay in OCaml

These cannot be expressed in tantra because tantra is defined in terms of them:

| Module | What it does |
|---|---|
| `proof_graph.ml` | Hashtbl graph store, CSR materialisation, `run_ppr` SpMV, `walk_inheritance` BFS, `raw_satya`, dimension registry, `join`, `find`, `edges_of` |
| `om_parser.ml` | All `.om` file I/O and parsing |
| `setu_shabda.ml` | `parse_shabda`, `read_shabda`, `raw_shabda_for_node`, shabda inheritance |
| `yantra_parser.ml` | All `.tantra` file parsing |
| `yantra_inverter.ml` | Symbolic algebra on `expr` AST (backward derivation) |
| `yantra_eval.ml` | `eval` (the recursive interpreter), `yantra_tokenise` |
| `yantra_types.ml` | All type definitions and coercions (`VFloat`, `VString`, `VNode`, `VFn`, …) |
| `yantra_ops.ml` | All pure numeric / string / list / vector primitives (atoms for tantra composition) |
| `yantra_resolver.ml` | `chain_resolve` — PPR-guided beam search; BFS bookkeeping must stay OCaml |
| `yantra_index.ml` | Index builders, `apply_relation_axioms`, `scan_visheshanam_properties` |
| `socket.ml` | Unix socket I/O |

---

## Full primitive API surface (tantra can call these today)

### Graph / node primitives

| Primitive | Arity | OCaml backing |
|---|---|---|
| `lookup` | 1 | `Proof_graph.find` |
| `walk` | 2 | `edges_of` filtered by relation (outgoing) |
| `walk-in` | 2 | `edges_of` filtered by relation (incoming) |
| `has` | 2 | `edges_of` pattern match `source-rel-target` |
| `edges` | 1 | `edges_of` → VList of [src, rel, tgt] triples |
| `outgoing-edges` | 1 | `all_edges` filtered by source |
| `all-edges` | 0 | every edge in the graph |
| `ancestors-of` | 1 | `walk_inheritance` — BFS over abheda/swarupa/dhatu/vishesa/amsha |
| `to-english` | 1 | `Setu.read_shabda` (falls back to `to-english.tantra`) |
| `describe` | 1 | `.shabda` field after `/` |
| `to-english-relation` | 1 | `Anuvada.english_of_visheshanam_from_graph` |
| `incoming-to` | 1 | delegates to `incoming-to.tantra` |
| `domain-of` | 1 | delegates to `domain-of.tantra` |
| `context-score` | 2 | delegates to `context-score-impl.tantra` |
| `node-satya` | 1 | `.satya` field |
| `edge-weight` | 1 | `vp_satya_weight` |
| `abheda-of` | 1 | delegates to `abheda-of.tantra` |
| `avrti` | 2 | `Anuvada.avrti_anuvada` — multi-pass spiral |
| `render-node` | 1 | `Anuvada.render_darshana_to_buf` |
| `name` | 1 | destructures VNode/VPair/VBinding |
| `value` | 1 | extracts VFloat/VBinding numeric value |
| `shabda` | 2 | `Setu.read_shabda k node key` |
| `shabda-pairs` | 1 | all shabda pairs for node |
| `exists` | 1 | truthy check |
| `ppr` | 3 | `Proof_graph.run_ppr` |
| `graph-node-count` | 0 | `Hashtbl.length k.nodes` |
| `graph-edge-count` | 0 | `List.length !(k.all_edges)` |
| `emit-node` | 4 | `Proof_graph.join` + `raw_satya` |
| `register-dimension` | 1 | `Proof_graph.register_dimension` |
| `ancestors-of` | 1 | `walk_inheritance` |

### Pipeline / session primitives

| Primitive | Arity | Notes |
|---|---|---|
| `tokenise` | 1 | `yantra_tokenise` |
| `classify` | 1 | → `setu-classify-token.tantra` |
| `session-bindings` | 0 | reads mutable session state |
| `remember-bindings` | 1 | mutates session state |
| `resolve-direct` | 2 | `try_match_inputs` + `Yantra_resolver` |
| `resolve-inverse` | 2 | `invert_chain` + `Yantra_inverter` |
| `resolve-chain` | 3 | `chain_resolve` BFS+PPR |
| `resolve-reason` | 2 | `resolve_tantra` → reason string |
| `execute-plan` | 1 | `run_forward` / `run_inverse` via `eval_tantra` |
| `print` | 1 | `Printf.printf` |

### Pure ops (always available in tantra)

Numeric: `add mul sub div power sqrt sin cos tan asin acos atan2 log abs neg floor ceil mod min max`
String: `split concat join char-at string-length to-number to-string upper lower starts-with`
List: `map filter first-match fold-pairs fold-triples reduce length nth flatten append range sort-desc unique member frequencies`
Vector: `vec-add vec-sub vec-scale vec-dot vec-norm vec-nth rot2d mat-mul`
Logic: `eq neq and or not lt le gt ge`
Constructors: `pair bind`

---

## Tantras that already exist (brahman/yantra/)

| Tantra | Status | Notes |
|---|---|---|
| `domain-of.tantra` | ✅ complete | uses `ancestors-of`; 4-case inheritance walk |
| `incoming-to.tantra` | ✅ complete | replaces OCaml primitive |
| `abheda-of.tantra` | ✅ complete | one-liner `walk n "abheda"` |
| `context-score-impl.tantra` | ✅ complete | edge-intersection count |
| `to-english.tantra` | ✅ functional | direct shabda lookup; OCaml has richer fallback |
| `anuvada-ganana.tantra` | ✅ meta-pipeline | orchestrates tokenise → classify → plan → execute → format |
| `classify-fold.tantra` | ✅ complete | OCaml `join_bigrams` is the fallback |
| `setu-classify-token.tantra` | ✅ partial | OCaml `classify_token` is fallback for shabda-search |
| `darshana.tantra` | ✅ complete | replaces `Anuvada.render_darshana_to_buf` for Darshana events |
| `yantra-plan-extraction.tantra` | ✅ partial | covers main binding patterns |
| `yantra-plan-resolution.tantra` | ✅ partial | covers main resolution strategies |
| `anuvada.tantra` | ✅ complete | conceptual fallback answer path |
| `spiral-domain.tantra` | ✅ complete | domain-scoped spiral walk |
| `varga-nirdhara.tantra` | ✅ complete | varga classification |
| `ppr.tantra` | ✅ exists | wraps `ppr` primitive |
| `graph-dimensions.tantra` | ✅ exists | dimension queries |
| `matra-ganana.tantra` | ✅ exists | unit arithmetic |
| `matra-nirmana.tantra` | ✅ exists | unit construction at startup |
| `visheshanam-entropy-weights.tantra` | ✅ exists | replaces OCaml fallback |
| `weighted-context-score.tantra` | ✅ exists | richer context scoring |
| `per-relation-score.tantra` | ✅ exists | per-edge-type scoring |

---

## What needs to change

### 1. Higher-order tantras as first-class values

**The gap**: `Var v` in `yantra_eval.ml:25–38` only auto-invokes zero-input tantras. A tantra with inputs returns `VString name` — it cannot be passed as a function to `map`/`filter`/`reduce`.

**Current workaround** (verbose):
```
map nodes (fn n -> domain-of n)
```

**After fix** (concise):
```
map nodes domain-of
let all-domains = flatten (map (ancestors-of node) domain-of)
```

**Engine change needed** — `yantra_eval.ml` `Var v` branch:
```ocaml
| Some t ->
  if t.t_inputs = [] then !_eval_tantra_ref k t []
  else
    (* wrap as VFn so it can be passed to map/filter/reduce *)
    VFn (List.map (fun p -> p.tp_name) t.t_inputs,
         Call (t.t_name, List.map (fun p -> Var p.tp_name) t.t_inputs),
         new_env ())
```

This makes every named tantra a first-class callable keyword. One-line change.

---

### 2. New OCaml primitives to expose

These graph operations exist in OCaml but are NOT callable from tantra. Add them
to `yantra_eval_primitives.ml` + register arity in `yantra_eval.ml`:

| New Primitive | Arity | OCaml backing | Why needed |
|---|---|---|---|
| `in-degree` | 1 | `Proof_graph.in_degree` | count incoming edges to a node |
| `out-degree` | 1 | `Proof_graph.out_degree` | count outgoing edges from a node |
| `neighbors` | 1 | `Proof_graph.neighbors` | all adjacent nodes (in + out) |
| `has-domain` | 2 | `Setu.has_domain_sthita` | `(has-domain node "domain-math")` → bool |
| `walk-chain` | 2 | `Setu.walk_chain` | `(walk-chain node 3)` — BFS N hops over kriya/phala/swarupa/abheda |
| `resolve-node` | 1 | `Setu.resolve` | `(resolve-node n)` — node + abheda aliases |

Note: `in-degree`, `out-degree`, `neighbors` can also be expressed in tantra
using existing primitives. If higher-order tantras land first (item 1 above),
these may not need OCaml primitives at all:

```
-- in-degree expressed in tantra (once all-edges + filter work efficiently):
let in-degree = (fn node -> length (filter (all-edges) (fn e -> eq (nth e 2) node)))

-- neighbors:
let neighbors = (fn node -> unique (append (walk node "swarupa") (walk-in node "swarupa")
                                           (walk node "abheda") ...))
```

---

### 3. Dead code to remove from setu.ml

`setu.ml` contains ~200 lines that are exact duplicates of `setu_shabda.ml` and
`setu_classify.ml`. These must be removed and callers updated:

| Dead symbol in setu.ml | Lines | Canonical location |
|---|---|---|
| `parse_shabda` | 13–68 | `Setu_shabda.parse_shabda` |
| `parse_shabda_file` | 70–127 | `Setu_shabda.parse_shabda_file` |
| `raw_shabda_for_node` | 129–151 | `Setu_shabda.raw_shabda_for_node` |
| `merge_shabda_priority` | 153–169 | `Setu_shabda.merge_shabda_priority` |
| `read_shabda` | 171–178 | `Setu_shabda.read_shabda` |
| `shabda_get` | 180–181 | `Setu_shabda.shabda_get` |
| `grammar_of_english_cache` + loader | 445–464 | `Setu_classify` |
| `english_token_roles_cache` + loader | 466–477 | `Setu_classify` |
| `english_number_words_cache` + loader | 479–494 | `Setu_classify` |
| `classify_token` | 504–577 | `Setu_classify.classify_token` |

Callers to update:
- `yantra.ml:63` → `Setu_classify.classify_token`
- `anuvada.ml:1195` → `Setu_classify.classify_token`

---

### 4. OCaml functions that should become tantras

These are semantic reasoning functions currently in OCaml that are good tantra
candidates. Some already have partial tantra coverage; make them complete:

#### 4a. `setu.has_domain_sthita` → `has-domain.tantra`

```
tantra has-domain
  inputs
    node    string
    domain  string
  let
    direct    = member domain (walk node "sthita")
    inherited = exists (first-match (ancestors-of node)
                  (fn a -> member domain (walk a "sthita")))
    result    = or direct inherited
  return
    result  bool
done
```

#### 4b. `setu.resolve` → `resolve-node.tantra`

```
tantra resolve-node
  inputs
    n  string
  let
    result = unique (flatten [[n] (walk n "abheda") (walk-in n "abheda")])
  return
    result  list
done
```

#### 4c. `setu.infer_inputs` → `infer-inputs.tantra`

```
tantra infer-inputs
  inputs
    node  string
  let
    sthita  = walk node "sthita"
    result  = filter sthita (fn t -> not (starts-with t "domain-"))
  return
    result  list
done
```

#### 4d. `setu.infer_outputs` → `infer-outputs.tantra`

```
tantra infer-outputs
  inputs
    node  string
  let
    phala   = walk node "phala"
    result  = filter phala (fn t -> not (starts-with t "domain-"))
  return
    result  list
done
```

#### 4e. `setu.detect_domain` → extend `domain-of.tantra`

`detect_domain` takes a list of seeds and returns the first domain found via
`sthita` edges. This is a subset of what `domain-of.tantra` already does for
a single node. Extend `domain-of.tantra` or add a `domain-of-seeds.tantra`:

```
tantra domain-of-seeds
  inputs
    seeds  list
  let
    result = first-match seeds (fn seed ->
               first-match (walk seed "sthita") (fn t ->
                 cond (starts-with t "domain-") t otherwise _none))
  return
    result  string
done
```

#### 4f. `setu.kriya_of` / `swarupa_of` / `yukta_of` / `janya_of`

These are already one-liner `walk` calls. No tantra needed — callers should
call `(walk node "kriya")` etc. directly. Remove the OCaml wrappers
from any callers once confirmed they are only used internally in `setu.ml`.

---

### 5. Verify: what needs to stay OCaml for graph/ sub-varga specifically

When writing `math/graph/operations/` nodes (bfs, dfs, shortest-path, etc.),
the engine operations they describe are concepts in the kosha — they are NOT
implementations. The `.om` files declare what BFS *is*, not run BFS.

However, once the graph sub-varga is defined, tantras can *reason about* graph
structure using the primitive layer. For example:

```
-- a tantra that checks if a node is a graph operation (using graph/ varga)
tantra is-graph-operation
  inputs
    node  string
  let
    ancestors = ancestors-of node
    result    = exists (first-match ancestors
                  (fn a -> eq a "graph-varga"))
  return
    result  bool
done
```

This is the payoff: once `graph-varga.om` exists, tantras can use
`ancestors-of` to ask semantic questions about graph topology.

---

## Graph system deepening — what we found

### Graph concepts already live in the kosha (scattered, pre-formal)

Before building `math/graph/` we discovered these graph-theoretic nodes already
exist in the kosha. The new sub-varga must connect to them, not duplicate them.

#### In `brahman/kosha/3d/` — most graph-dense area

| Node | File | Key edges | Graph meaning |
|---|---|---|---|
| `node-graph` | `3d/blender/node-graph.om` | `dag-siddha`, `proof-graph-abheda`, `sambandha-yukta` | Blender shader/geometry DAG |
| `scene-graph` | `3d/blender/scene-graph.om` | `dag-siddha`, `proof-graph-abheda`, `shakha-yukta` | 3D object parent→child transform DAG |
| `edge` | `3d/blender/edge.om` | `vertex-yukta`, `face-yukta`, `sambandha-swarupa` | Mesh edge (3D — NOT math edge) |
| `vertex` (blender) | `3d/blender/vertex.om` | `vector-swarupa`, `mesh-sthita`, `edge-yukta` | 3D mesh vertex (NOT math vertex) |
| `vertex` (render) | `3d/vertex.om` | `bindu-swarupa`, `akasham-sthita`, `normal-yukta` | Rendered-space vertex |
| `force-directed` | `3d/force-directed.om` | **`graph-phala`**, `sangati-ahara`, `avrti-kriya` | Force-directed layout — produces a **graph** as output |
| `kinematic-chain` | `3d/kinematic-chain.om` | `dag-siddha`, `scene-graph-yukta`, `shakha-yukta` | Bone chain — a DAG of transforms |

Critical: `dag-siddha` is used on three existing nodes and `graph-phala` on one,
but `dag` and `graph` have no `.om` nodes in `math/graph/` yet. These references
are dangling — they need landing targets.

#### In `brahman/kosha/yantra/` — graph infrastructure operators

| Node | What it does |
|---|---|
| `op-walk` | Graph traversal operator (keyed walk) |
| `op-walk-in` | Graph traversal inward |
| `op-edges` | Projects the `edges` field from a node |
| `op-edge-weight` | Projects `edge-weight` field |
| `op-incoming-to` | Queries incoming edges to a node |
| `op-node` | Projects the `node` field |
| `op-node-satya` | Gets the satya (truth-value) of a node |
| `op-resolve-chain` | Resolves a chain of 3 things (pipeline) |
| `op-fold-pairs` | Folds over pairs |
| `op-fold-triples` | Folds over triples |

These are the operational layer — the kosha *describes* graph traversal operations
through these yantra nodes. They correspond directly to tantra primitives.

#### In `brahman/kosha/math/`

- `lattice` (`algebra/structures/`) — `partial-order-sthita`, `join-kriya`, `meet-kriya` — Hasse diagram of a lattice IS a DAG
- `category` (`algebra/structures/`) — `object-yukta`, `morphism-yukta`, `composition-kriya` — a category IS a directed multigraph
- `topology` (`geometry/properties/`) — `connectivity-yukta`, `sambandha-yukta` — topological connectivity concept

---

### The visheshanam ring IS a typed directed multigraph schema

The entire `brahman/kosha/yantra/visheshanam/` directory is a full graph edge-type
schema. Properties declared on each visheshanam node map exactly to graph theory:

| Edge type | Ring properties | Graph-theoretic meaning |
|---|---|---|
| `sthita` | `antisymmetric, transitive, composable` | Directed partial-order edges |
| `abheda` | `symmetric, transitive, congruence, composable` | Undirected equivalence edges |
| `swarupa` | `symmetric, transitive, reflexive` | IS-A edges (reflexive closure) |
| `kriya` | `antisymmetric, composable, ring-op:mul` | Directed composable action edges |
| `phala` | `antisymmetric, dual:janya` | Output/codomain edges |
| `janya` | `antisymmetric, dual:phala` | Generator/domain edges |
| `yukta` | `symmetric, ring-op:add` | Undirected association edges |
| `vishesa` | open additive | IS-A (particular of universal) |
| `amsha` | closed partition | IS-PART-OF |
| `drishthanta` | `antisymmetric` | Concrete witness/example edges |

This means the proof-graph is already a 10-dimensional typed directed multigraph.
The `math/graph/` sub-varga is not describing something foreign — it is describing
the structure the engine itself is built on.

---

### Sangati roots that ground graph theory

The sangati layer already contains the deep conceptual vocabulary for graph
structure. Every `math/graph/` node must anchor to these:

#### Structure / relation roots

| Sangati node | Graph concept |
|---|---|
| `sambandha` | THE abstract edge — "structural relationship wire synapse bond coupling" |
| `rekha` | Undirected edge — "minimum connection between two bindus" |
| `bindu` | Vertex / graph node — "point / zero-extent position; rekha-janaka" |
| `bindu-dvaya` | Pair of vertices — "minimal pair from which rekha arises" |
| `dura` | Edge weight — "scalar measure of separation between two bindus" |
| `samsarga` | General connection — "contact that connects; aneka-aneka-swarupa" |
| `sandhi` | Junction node — "the joining that produces meaning" |
| `tantu` | Edge as thread/wire — "filament that connects as wave" |
| `sparsha` | Adjacency — "the contact that collapses" |

#### Ordering / path roots

| Sangati node | Graph concept |
|---|---|
| `krama` | Path ordering — "ordered sequence where each step grounds the next" |
| `parampara` | Chain / path — "deepening chain; shakha-yukta" |
| `shakha` | Tree branch — "branch knowing its root; mula-yukta agra-yukta" |
| `avastha` | Node state — "state at a krama point; purva-avastha-janya uttara-avastha-phala" |
| `nirantara` | Path continuity — "unbroken / no gaps = connected path" |
| `viveka` | Fork / branching decision — "discrimination at a fork; shakha-janaka, eka-aneka-kriya" |
| `dharma-anvaya` | Property inheritance along DAG edges |

#### Traversal / movement roots

| Sangati node | Graph concept |
|---|---|
| `gati` | Graph traversal movement — "direction as trajectory" |
| `abhisarana` | Convergent traversal — "approach; aneka-eka-swarupa" |
| `avrti` | Cycle traversal / revisit — "recurrence; the returning" |
| `aarambham` | Source vertex — "one-time arising that starts the krama; krama-janaka" |
| `kshaya` | Sink vertex — "decay / release; visarjana-kriya" |

#### Multiplicity / degree roots

| Sangati node | Graph concept |
|---|---|
| `eka-aneka` | Out-degree direction / tree fan-out — "one root many branches" |
| `aneka-eka` | In-degree direction / merging paths — "many-to-one convergence" |
| `eka-eka` | Bijective edge / matching — "one-to-one" |
| `aneka-aneka` | Bipartite or hyperedge — "many-to-many" |
| `dvaya` | Edge as minimal relation — "twoness / minimal multiplicity" |
| `vrnda` | Vertex set / clustering — "the gathering / many that move as one" |

#### Connectivity / topology roots

| Sangati node | Graph concept |
|---|---|
| `seema` | Cut / boundary of subgraph — "boundary threshold; line between states" |
| `purna` | Complete graph — "fullness / complete nothing missing" |
| `shunya` | Empty / null graph — "zero-void / empty; bindu-abheda" |
| `aarambham` | Source vertex |
| `kshaya` | Sink vertex |

---

### What math/graph/ needs — full inventory

**graph-varga.om** (root): `math-varga-vishesa` + `sambandha-yukta vrnda-yukta rekha-yukta bindu-yukta`

#### structures/

| Node | Key sangati anchors | Notes |
|---|---|---|
| `graph` | `sambandha-swarupa vrnda-yukta bindu-yukta rekha-yukta` | Fundamental object; `set-product-janya` (E ⊆ V×V) |
| `vertex` | `bindu-swarupa element-swarupa vrnda-sthita` | Math vertex — distinct from 3D vertex |
| `graph-edge` | `rekha-swarupa sambandha-swarupa bindu-dvaya-sthita` | Math edge — distinct from mesh edge |
| `directed-graph` | `eka-aneka-swarupa graph-vishesa` | Digraph |
| `undirected-graph` | `dvaya-swarupa sama-yukta graph-vishesa` | Simple graph |
| `weighted-graph` | `dura-yukta matra-yukta graph-vishesa` | Edge with weight |
| `dag` | `krama-sthita partial-order-abheda` | DAG — gives `dag-siddha` a landing target |
| `tree` | `shakha-swarupa parampara-sthita mula-yukta graph-vishesa` | Acyclic connected graph |
| `path` | `krama-swarupa nirantara-sthita parampara-sthita` | Vertex sequence |
| `cycle` | `avrti-swarupa krama-sthita seema-sthita path-vishesa` | Closed path |
| `walk` | `gati-swarupa krama-sthita` | Unrestricted traversal |
| `adjacency` | `sparsha-swarupa bindu-dvaya-sthita dura-abheda` | Neighbour relation |
| `subgraph` | `subset-swarupa vrnda-sthita subset-abheda` | Induced subgraph |
| `network` | `sandhi-yukta sambandha-swarupa vrnda-yukta graph-abheda` | Applied graph |

#### properties/

| Node | Key sangati anchors |
|---|---|
| `connectivity` | `nirantara-swarupa sambandha-siddha samsarga-yukta` |
| `acyclicity` | `avrti-pratipaksha krama-sthita` |
| `planarity` | `tala-sthita akasham-sthita` |
| `degree` | `aneka-swarupa matra-yukta bindu-sthita` |
| `graph-isomorphism` | `isomorphism-abheda bijection-swarupa` |
| `diameter` | `dura-yukta krama-yukta` |

#### operations/

| Node | Key sangati anchors |
|---|---|
| `bfs` | `krama-swarupa aarambham-sthita avrti-kriya` |
| `dfs` | `parampara-swarupa shakha-kriya avrti-kriya` |
| `shortest-path` | `krama-swarupa dura-yukta abhisarana-phala` |
| `spanning-tree` | `shakha-swarupa purna-phala set-sthita` |
| `topological-sort` | `krama-phala dag-sthita partial-order-siddha` |
| `graph-union` | `set-union-abheda` |
| `graph-complement` | `set-complement-abheda` |
| `adjacency-matrix` | `matrix-swarupa sparsha-yukta` |
| `graph-coloring` | `viveka-kriya seema-yukta` |

---

### What we learned about the existing tantras

#### Patterns that work well

1. **Delegation chain**: primitive → tantra → meta-tantra. `context-score` OCaml
   primitive delegates to `context-score-impl.tantra` which is a clean
   `filter`/`length` expression. `domain-of` OCaml primitive delegates to
   `domain-of.tantra` which uses `ancestors-of`. This pattern should be the
   standard for all new semantic operations.

2. **`ancestors-of` is the key unlock**: Added this session. It exposes
   `walk_inheritance` (BFS over abheda/swarupa/dhatu/vishesa/amsha edges, 4-hop)
   to the tantra layer. `domain-of.tantra` immediately used it for case 4
   (inherited domain). It is the primitive that makes the entire restructure
   work without `domain-X-sthita` on every leaf.

3. **`anuvada-ganana.tantra` is the proven meta-tantra pattern**: It calls
   `tokenise`, `classify-fold`, `query-intents`, `yantra-plan-extraction`,
   `yantra-plan-resolution`, `execute-plan`, `format-response`, `anuvada` — all
   by name, composing tantras as pipeline stages. This is the model for any new
   meta-level reasoning tantra.

4. **`first-match` + `fn` is the dominant idiom** for conditional graph walks:
   ```
   first-match (ancestors-of node) (fn a -> cond (eq a "graph-varga") a otherwise _none)
   ```
   This replaces what would be an explicit recursive loop in OCaml.

5. **`flatten (map list fn)`** is the idiom for collecting results across a list
   of nodes — e.g. collecting all sthita edges from all ancestors:
   ```
   ancestor-flat = flatten (map ancestors (fn a -> walk a "sthita"))
   ```

#### Gaps / weaknesses found

1. **No tantra-to-tantra as first-class value**: Cannot write `map nodes domain-of`.
   Must always write `map nodes (fn n -> domain-of n)`. One engine fix resolves
   this (see implementation sequence step 1).

2. **`to-english.tantra` is thin**: OCaml `Setu.to_english` (lines 365–440) does
   scored abheda traversal + PPR bonus. The tantra only does direct shabda lookup.
   For the graph sub-varga to be self-describing, `to-english.tantra` needs to
   handle the inheritance walk too.

3. **`setu-classify-token.tantra` is partial**: The OCaml fallback (`classify_token`
   lines 504–577) handles shabda-search and partial-name matching that the tantra
   doesn't. Once `has-domain` and `resolve-node` primitives exist, the tantra can
   be completed.

4. **No tantra for graph structure queries**: After building `math/graph/`, we
   should write:
   - `is-graph-node.tantra` — checks `ancestors-of` for `graph-varga`
   - `is-graph-operation.tantra` — checks for `graph-varga-karma` ancestors
   - `graph-neighbors.tantra` — wraps `walk` + `walk-in` across all relation types

5. **No recursive tantras yet**: The tantra language has `reduce` and `range` but
   no explicit recursion syntax. Deep graph walks (e.g. finding all paths between
   two nodes) would need a new `recurse` primitive or a fixed-depth `walk-chain`.
   `walk-chain` (step 2 of implementation sequence) covers the common case.

---

## Implementation sequence

```
Step 0  — remove dead duplicates from setu.ml (200 lines, no behaviour change)
Step 1  — add higher-order tantra VFn wrapping in yantra_eval.ml (1-line change)
Step 2  — add in-degree, out-degree, neighbors, has-domain, walk-chain, resolve-node
          primitives to yantra_eval_primitives.ml + register arities
Step 3  — write has-domain.tantra, resolve-node.tantra, infer-inputs.tantra,
          infer-outputs.tantra, domain-of-seeds.tantra
Step 4  — run regression (must stay 49/52)
Step 5  — proceed to math/graph/ sub-varga build (phase 2.9 step 10)
```

---

## Key files

```
vyakarana/lib/setu.ml                  dead duplicates to remove (steps 0)
vyakarana/lib/yantra_eval.ml           Var branch — higher-order tantra fix (step 1)
vyakarana/lib/yantra_eval_primitives.ml  new primitives (step 2)
brahman/yantra/has-domain.tantra        new (step 3)
brahman/yantra/resolve-node.tantra      new (step 3)
brahman/yantra/infer-inputs.tantra      new (step 3)
brahman/yantra/infer-outputs.tantra     new (step 3)
brahman/yantra/domain-of-seeds.tantra   new (step 3)
vyakarana/scripts/run-regression.sh     regression check after step 4
```
