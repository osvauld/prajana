# Arity-to-Math Semantics Plan

Status: Draft v0.4
Owner: OpenCode + user
Scope: Replace raw arity hardcoding with math-structured operation classes, then encode those classes in graph data (`.om`/`shabda`) for denser and more meaningful parser behavior.

## End Goal

Arity is not treated as a flat number table. Instead:
- Operations are grouped by algebraic meaning (monoid, relation, projection, keyed lookup, higher-order, constructor, pipeline).
- Parser arity is derived from class semantics.
- `shabda` points to these classes, so metadata is compact and carries intent, not just counts.
- The graph becomes the source of truth for operation structure.

## Algebraic Class Table

This is the ground truth. Per-op assignment lives in the graph (`.om`), not in a maintained matrix.

| Class | Parse arity | Invariants | Current members |
|---|---|---|---|
| **monoid** | `-1` (variadic) | associative, folds over all args | `add`, `mul`, `and`, `or`, `concat`, `append` |
| **projection** | `1` | pure, no side effects | `name`, `kind`, `node`, `value`, `length`, `exists`, `not`, `to-string`, `to-number`, `upper`, `lower`, `string-length`, `edges`, `abheda-of`, `to-english`, `to-english-relation`, `render-node`, `describe`, `iccha-status`, `domain-of`, `incoming-to`, `role`, `op-to-tantra`, `is-tantra`, `flatten`, `sort-desc`, `unique`, `tokenise`, `classify`, `remember-bindings`, `session-bindings`, `execute-plan`, `print`, `sqrt`, `sin`, `cos`, `tan`, `log`, `abs`, `neg`, `floor`, `ceil`, `factorial` |
| **binary** | `2` | pure, asymmetric, fixed 2 args | `sub`, `div`, `power`, `mod`, `min`, `max` |
| **keyed** | `2` | arg0 = container/source, arg1 = key/index | `shabda`, `nth`, `char-at`, `split`, `join`, `walk`, `walk-in`, `has`, `context-score`, `avrti`, `lookup` |
| **relation** | `2` | symmetric or asymmetric binary predicate | `eq`, `neq`, `lt`, `le`, `gt`, `ge` |
| **higher-order** | `2` | arg0 = data, arg1 = function | `map`, `filter`, `first-match`, `fold-pairs`, `fold-triples` |
| **constructor** | `-1` | builds a typed value from parts | `bind`, `pair` |
| **pipeline** | `2`–`3` | effectful, ordered, may chain | `resolve-direct`, `resolve-inverse`, `resolve-chain`, `resolve-reason` |

**Key inconsistency to fix in Phase 5**: `add`/`mul` are currently hardcoded arity `2` but belong to monoid (variadic). This is the primary structural correction.

**Class count**: 8 (`monoid`, `projection`, `binary`, `keyed`, `relation`, `higher-order`, `constructor`, `pipeline`).

The per-op class assignment will be written into the graph as `.om` nodes. The matrix above is a snapshot — the graph is the authority once Phase 5 lands.

## Plan for the Plan

### Phase 0 - Baseline Audit
- [x] Inventory current built-in ops and arities in `yantra_parser.ml`.
- [x] Identify parser behaviors that depend on `op_arity` beyond argument count.
- [x] Classify all ops into the 7 algebraic classes above.
- [x] Note key inconsistency: `add`/`mul` should be monoid (variadic), not fixed arity 2.

Deliverable: Class table above (replaces per-op matrix — the graph will hold per-op assignment).

### Phase 1 - Algebraic Taxonomy
- [x] Define class-level parse contracts (fixed, variadic, specialized).
- [x] Define class-level invariants (associativity, symmetry, argument roles).
- [x] Add `binary` class for pure asymmetric 2-arg ops (`sub`, `div`, `power`, `mod`, `min`, `max`).
- [x] Keep `constructor` separate from `keyed` — different intent (build vs. read).

Deliverable: 8-class taxonomy locked (table above).

### Phase 2 - Graph Encoding Model
- [x] Class nodes: `brahman/kosha/yantra/op-class-*.om` — 8 files, each with `shabda parse-arity:N`.
- [x] Op nodes: `brahman/kosha/yantra/op-<name>.om` — one per op, sloka `op-class-<class>-kriya`.
- [x] Per-op arity override: `op-resolve-chain.om` carries `shabda parse-arity:3` directly.
- [x] `lookup` corrected from keyed → projection (1-arg).

Deliverable: 90 `.om` files in `brahman/kosha/yantra/` encoding all class and op metadata.

### Phase 3 - Runtime/Parser Integration
- [x] `_graph_arities` table added to `yantra_parser.ml`.
- [x] `scan_graph_op_arities` added to `yantra_index.ml` — walks `op-*` nodes, follows `kriya` edges to class, reads `parse-arity`.
- [x] Called in `build_index` before tantra pre-scan (graph is already loaded at that point).
- [x] Lookup priority: graph-class → tantra-scanned → 0.

Deliverable: Parser derives arity from graph with no hardcoded table.

### Phase 4 - Shabda Role Redefinition
- [ ] Deferred — current `shabda` contract works for Phase 5. Revisit when schema evolves.

### Phase 5 - Direct Cutover
- [x] Hardcoded `op_arity` match table deleted from `yantra_parser.ml`.
- [x] `add`/`mul` evaluator updated to variadic fold (monoid identity elements: 0.0 and 1.0).
- [x] All 49 regression tests pass post-cutover.

Deliverable: Complete — hardcoded table gone, graph is sole source of truth.

### Phase 6 - Freeze
- [x] Graph-class model is the only arity lookup path.
- [x] No dead code remains (hardcoded table deleted in Phase 5).
- [ ] Freeze: adding a new built-in op requires only a new `.om` file in `brahman/kosha/yantra/`.

Deliverable: Model frozen. New ops are added via graph only.

## Load Order (relevant for Phase 3)

Graph is **fully loaded before** tantra parsing begins (`bin/vyakarana.ml`):
1. `Om_parser.load_dirs` loads all `.om` files into `k0`.
2. `Yantra.build_index ~graph:k0` — graph complete at this point.
3. Inside `build_index`: `pre_scan_arities` runs (reads tantra headers), then full parse.

Class metadata nodes will already be in the graph during tantra parse. Bootstrap only needs `read_shabda` which is pure OCaml with no graph dependency.

## Status

**Implementation complete.** All 6 phases done. 49 regression tests pass.

To add a new built-in op:
1. Create `brahman/kosha/yantra/op-<name>.om` with the correct class sloka (`op-class-<class>-kriya`).
2. Implement the evaluator case in the appropriate `yantra_*.ml` file.
3. Run regression.
