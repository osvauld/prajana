# 08 — Boot / Reboot Architecture

**Boot passes run structural graph enrichment after the kosha is loaded.
They add derived edges that cannot be encoded in `.om` files.**

---

## Why boot passes exist

The `.om` file parser builds the graph from static declarations. Some graph
structure cannot be declared statically — it must be computed from the loaded
graph. Examples:

- **Varga membership** — `kinetic-energy` IS-A `energy` is encoded as
  `swarupa energy` in the `.om` file. But `energy-varga` is a separate node.
  The edge `[kinetic-energy, varga, energy-varga]` must be derived at runtime
  by scanning all nodes for `swarupa X` where `X-varga` exists.

- **Future passes** — dimension normalization, cross-varga inheritance,
  derived unit edges, concept clustering — all require a fully loaded graph
  before they can run.

---

## The two call sites

### 1. Startup — `vyakarana.ml`

```
graph loaded from .om files
  ↓
build_index (tantras loaded)
  ↓
reboot "boot"          ← structural enrichment
  ↓
materialize_csr        ← PPR adjacency rebuilt
```

Called once when the server starts. Arg is `"boot"`.

### 2. reload-all — `socket.ml` `reload_tantras`

```
tantras reloaded from disk
  ↓
build_word_index       ← word→node mapping rebuilt
  ↓
reboot "reload"        ← structural enrichment re-runs
  ↓
materialize_csr        ← PPR adjacency rebuilt
```

Called every time `{"command":"reload-all"}` is sent to the socket. Arg is
`"reload"`. This is important — tantra edits picked up by `reload-all` must
not lose the derived edges. Reboot re-derives them every time.

---

## The tantra files

### `brahman/yantra/boot/reboot.tantra`

Orchestrator. Calls all passes in dependency order.

```
tantra reboot
  inputs
    _  string     -- "boot" or "reload"
  let
  _ = varga-inheritance ""
  return "ok" any
done
```

To add a new pass: add `_ = new-pass-name ""` here, in the right order.
Order matters — pass 2 may depend on edges emitted by pass 1.

### `brahman/yantra/boot/varga-inheritance.tantra`

Pass 1. Derives `varga` membership edges from `swarupa` IS-A edges.

**Rule:** if node `N` has `swarupa X` and node `X-varga` exists in the graph
→ emit `[N, varga, X-varga]`

**Before this pass:**
```
walk-in "energy-varga" "varga"  →  []
```

**After this pass:**
```
walk-in "energy-varga" "varga"  →  ["kinetic-energy", "potential-energy", ...]
walk-in "swara-varga" "varga"   →  ["shadja", "rishabha", "gandhara", ...]
```

**Why `swarupa` not `vishesa`:**
Physics `.om` files contain slokas like `"mechanical-energy-varga-vishesa"`.
These produce NO graph edge — `vishesa` is not a registered dimension.
The actual IS-A relationship is `swarupa energy` (pointing to the concept name,
not the varga node). `varga-inheritance` bridges `swarupa X` → `X-varga`.

---

## OCaml primitives added for boot passes

### `emit-edge source relation target → VNode`

Adds a single typed edge to the live graph. Idempotent via `Proof_graph.join`.
Adds to `k.all_edges` — edges persist through `reload-all` (which only clears
the tantra index, not the graph). `walk-in` and `edges_of` both read `all_edges`.

```
emit-edge "kinetic-energy" "varga" "energy-varga"
→ VNode "kinetic-energy"
```

### `graph-all-nodes → [VNode ...]`

Returns all node names in the live graph as a `VNode` list. Used by boot passes
to iterate over the full graph.

**Important:** returns `VNode` items, not `VString`. Must use `to-string` before
any string operation (`concat`, comparison, `emit-edge`):

```
-- WRONG: concat (VNode "energy") "-varga" → ""
-- RIGHT: concat (to-string parent) "-varga" → "energy-varga"
```

---

## Known pitfalls in boot tantra authorship

### Pitfall 1 — `let` inside `fn` body gets split (Tension 7)

The tantra file parser (`parse_let_block`) scans for `name = ...` line patterns.
Any line matching this inside a `fn` body is extracted as a new top-level binding.

```
-- BROKEN
_ = map nodes (fn node ->
  let snode = to-string node      ← parser splits this out as: snode = to-string node
  emit-edge snode "varga" ...)    ← snode resolves to VString "snode", not the value
```

```
-- CORRECT: inline everything, no bare let inside fn
_ = map nodes (fn node ->
  map (walk node "swarupa") (fn parent ->
    cond (exists (lookup (concat (to-string parent) "-varga")))
      (emit-edge (to-string node) "varga" (concat (to-string parent) "-varga"))
    otherwise _none))
```

This is the exact bug that made `varga-inheritance` run for 351ms and emit
nothing — it was silently iterating 1855 nodes but calling
`emit-edge "snode" "varga" "energy-varga"` (the literal string "snode")
instead of the actual node name.

### Pitfall 2 — `graph-all-nodes` returns `VNode` (Tension 8)

All graph traversal primitives (`walk`, `walk-in`, `graph-all-nodes`) return
`VNode` items. String ops (`concat`, `emit-edge`, equality) expect `VString`.
Passing `VNode` to `concat` returns `""` silently. Always `to-string` first.

### Pitfall 3 — emit-edge with non-existent relation returns VNone silently

If `relation` is not a registered dimension, `emit-edge` returns `VNone` without
error. The `"varga"` dimension is registered as a core dimension (index 10) so
it always works. For custom dimensions, call `register-dimension "name"` first.

---

## Adding a new boot pass

1. Write `brahman/yantra/boot/my-pass.tantra`
2. Add `_ = my-pass ""` to `reboot.tantra` (after any dependencies)
3. Add a test that calls `reload-all` then verifies the derived edges
4. The pass will run at startup AND on every `reload-all` automatically

---

## What has changed

For baseline and session progress see [changelog.md](changelog.md).

| Date | What shifted in this doc |
|------|-------------|
| 2026-03-17 | Initial writing. Boot/reboot architecture implemented and documented. |
