# Plan: Tantra-Native Avrti — Spiral Walk Logic in Tantra, Not OCaml

## Principle

OCaml provides **thin graph primitives only**. All walk logic, domain grouping,
spiral depth control, output ordering, and iccha-bridging lives in **tantra files**.

Current problem: `render-walk` builtin is a fat OCaml function (~250 lines) that does
walk + domain detection + incoming edges + scoring + spiral expansion + formatting.
This is OCaml hardcoding what should be tantra logic.

---

## The Three-Node Insight Driving This

The deepest answer to "what is life?" is already in the graph:

- **jada** — matter without iccha: no will, no directed-reaching
- **visha-anu** — has replication structure but `iccha-rahita`: cannot self-direct
- **eka-kosha** — has `iccha-sthita`: self-governing, self-sustaining, reaches for ahara

`iccha → siddha → jiva` — iccha **proves** jiva. Where there is directed-will, there is life.

The spiral walk output should surface this **from concrete → root**:
eka-kosha/visha-anu/jada (biology) → iccha (bridge principle) → prana/jiva (root)

---

## The Question IS an Iccha

**Iccha** is the formal term for what we send into the walk. "What is life?" is not just a
string — it is an **iccha**: directed reaching toward understanding. The seeds extracted from
it (jiva, prana) are the **iccha-targets** — what the questioner's will is reaching toward.

The entire pipeline is therefore:

```
iccha (question)
  → extract iccha-targets (seeds: jiva, prana)
  → walk graph outward from those targets
  → collect what points back INTO those targets (incoming)
  → surface iccha-bridge: which nearby nodes have iccha, which lack it
  → root: the abstract principle the iccha was reaching for
```

The iccha-bridge section **completes the circle**: the questioner's iccha reached toward
prana/jiva, and the graph reveals that iccha is the very thing that distinguishes eka-kosha
(living) from jada (inert). The same principle that generated the question IS the answer.

In `anuvada.tantra`, the input `sentence` parameter represents the iccha. Seeds are
`iccha-targets`. The walk is the graph's response to that iccha.

---

## Step 1: New Thin Builtins in `vyakarana/lib/yantra.ml`

Remove `render-walk` and `thread-questions` from `op_arity` and `eval_call`.

Add these 7 thin primitives:

| Builtin | Arity | Returns | Description |
|---------|-------|---------|-------------|
| `incoming-to` | 1 | `VList [[src-raw, rel-str, tgt-raw], ...]` | Incoming edges to a node |
| `domain-of` | 1 | `VList [VString domain, ...]` | Domain names of a node |
| `context-score` | 2 | `VFloat n` | Edge count between node and seeds list |
| `iccha-status` | 1 | `VString "sthita"\|"rahita"\|"none"` | Whether node has iccha-sthita or iccha-rahita |
| `abheda-of` | 1 | `VList [VString name, ...]` | Abheda (same-as) targets of a node |
| `flatten` | 1 | `VList [...]` | Flatten one level of list-of-lists |
| `sort-desc` | 1 | `VList [...]` | Sort list of `[item, score]` pairs by score desc |

### `avrti` return format (simplify)

Change from nested pass-group structure to flat list of triples:

```
VList [
  VList [VString source-raw, VString relation-name, VList [VString target-raw, ...]],
  ...
]
```

Pass 1 triples come first, pass 2 after. Tantra doesn't need to know pass numbers — it
controls depth via `spiral-domain` recursion, not pass numbers.

### `incoming-to` implementation

```ocaml
| "incoming-to" ->
  let name = as_string (eval k e (List.nth args 0)) in
  let edges = Proof_graph.edges_of k name in
  let incoming = List.filter_map (fun e ->
    if e.Proof_graph.target = name && e.Proof_graph.source <> name then
      Some (VList [VString e.Proof_graph.source;
                   VString (Proof_graph.string_of_visheshanam e.Proof_graph.relation);
                   VString e.Proof_graph.target])
    else None
  ) edges in
  VList incoming
```

### `context-score` implementation

```ocaml
| "context-score" ->
  let name = as_string (eval k e (List.nth args 0)) in
  let seeds = List.map as_string (as_list (eval k e (List.nth args 1))) in
  let seed_set = Hashtbl.create 8 in
  List.iter (fun s -> Hashtbl.replace seed_set s true) seeds;
  let edges = Proof_graph.edges_of k name in
  let score = List.fold_left (fun acc e ->
    if (Hashtbl.mem seed_set e.Proof_graph.source || Hashtbl.mem seed_set e.Proof_graph.target)
    then acc + 1 else acc
  ) 0 edges in
  VFloat (float_of_int score)
```

### `iccha-status` implementation

```ocaml
| "iccha-status" ->
  let name = as_string (eval k e (List.nth args 0)) in
  let edges = Proof_graph.edges_of k name in
  (* check outgoing edges for iccha-sthita / iccha-rahita targets *)
  let has_sthita = List.exists (fun e ->
    e.Proof_graph.source = name
    && e.Proof_graph.relation = Proof_graph.Sthita
    && e.Proof_graph.target = "iccha"
  ) edges in
  let has_rahita = List.exists (fun e ->
    (* rahita edges are parsed as Pratipaksha to iccha, or we check slokas *)
    e.Proof_graph.source = name
    && e.Proof_graph.target = "iccha"
    && e.Proof_graph.relation = Proof_graph.Pratipaksha
  ) edges in
  VString (if has_sthita then "sthita" else if has_rahita then "rahita" else "none")
```

---

## Step 2: New Tantra Files in `brahman/yantra/`

### `format-triple.tantra`

Renders one [source-raw, rel-string, targets-raw-list] triple as a natural language sentence.

```
tantra format-triple

  inputs
    t  list

  let
    src    = to-english (nth t 0)
    rel    = to-english-relation (nth t 1)
    tgts   = map (nth t 2) (fn tgt -> to-english tgt)
    tgt-s  = join tgts ", "
    result = concat src " " rel " " tgt-s "."

  return
    result  string

done
```

### `format-triples.tantra`

Renders a list of triples grouped by source.

```
tantra format-triples

  inputs
    triples  list
    indent   string

  let
    lines  = map triples (fn t -> concat indent (format-triple t) "\n")
    result = join lines ""

  return
    result  string

done
```

### `spiral-domain.tantra`

Targeted recursive avrti within a domain. Depth 0 = full; depth 1 = primary only; stops at 2.

```
tantra spiral-domain

  inputs
    domain-seeds   list
    context-seeds  list
    depth          int

  let
    triples      = avrti domain-seeds 1
    formatted    = cond (eq depth 0) (format-triples triples "    ") (format-triples-primary triples "      ")
    all-targets  = flatten (map triples (fn t -> nth t 2))
    scored       = map all-targets (fn n -> pair n (context-score n context-seeds))
    high-scored  = filter scored (fn sp -> gt (nth sp 1) 1)
    next-seeds   = map high-scored (fn sp -> nth sp 0)
    deeper       = cond (and (eq depth 0) (gt (length next-seeds) 0))
                     (spiral-domain next-seeds context-seeds 1)
                     otherwise ""

  return
    concat formatted deeper  string

done
```

### `iccha-bridge.tantra`

Surfaces iccha as the bridge between matter and life. Shows which nodes have iccha
and which lack it — the differential that defines life.

```
tantra iccha-bridge

  inputs
    nodes  list

  let
    with-iccha    = filter nodes (fn n -> eq (iccha-status n) "sthita")
    without-iccha = filter nodes (fn n -> eq (iccha-status n) "rahita")
    has-both      = and (gt (length with-iccha) 0) (gt (length without-iccha) 0)
    with-str      = join (map with-iccha (fn n -> to-english n)) ", "
    without-str   = join (map without-iccha (fn n -> to-english n)) ", "
    result        = cond has-both
                      (concat "  iccha (directed-will) present in: " with-str
                              "; absent in: " without-str ".\n")
                      otherwise ""

  return
    result  string

done
```

### Updated `brahman/yantra/anuvada.tantra`

Replaces the single `render-walk` call with explicit tantra-native pipeline.
Output goes concrete → iccha-bridge → root (not root first).
The `sentence` input IS the iccha. Seeds are iccha-targets.

```
tantra anuvada

  -- sentence is the iccha: directed reaching toward understanding
  -- seeds are the iccha-targets: what the question is reaching toward
  -- the walk finds what points back into those targets
  -- iccha-bridge surfaces the life-principle in the found nodes
  -- root states the abstract principle the iccha was reaching for

  inputs
    sentence  string  -- the iccha

  let
    words        = tokenise sentence
    tokens       = classify-all words
    joined       = join-bigrams tokens
    content      = filter joined (fn t -> eq (nth t 1) "concept")
    seeds        = map content (fn t -> nth t 2)  -- iccha-targets
    -- expand seeds through abheda for richer incoming search
    abheda-exp   = flatten (map seeds (fn s -> abheda-of s))
    all-seeds    = concat seeds abheda-exp

    -- find all nodes with incoming edges to any seed
    all-incoming = flatten (map all-seeds (fn s -> incoming-to s))
    -- score each incoming node by how many context edges it has
    scored-in    = map all-incoming (fn e -> pair (nth e 0) (context-score (nth e 0) all-seeds))
    -- find top domain (most incoming connections)
    top-scored   = sort-desc scored-in
    top-node     = cond (gt (length top-scored) 0) (nth (nth top-scored 0) 0) otherwise ""
    top-domain   = cond (gt (length (domain-of top-node)) 0) (nth (domain-of top-node) 0) otherwise ""

    -- per-domain sections: top domain gets spiral, others get mentions
    top-seeds    = map (filter top-scored (fn sp -> eq (nth (domain-of (nth sp 0)) 0) top-domain))
                       (fn sp -> nth sp 0)
    top-section  = cond (gt (length top-seeds) 0)
                     (concat "  in " top-domain ":\n" (spiral-domain top-seeds all-seeds 0))
                     otherwise ""

    -- iccha bridge: surfaces jada/visha-anu/eka-kosha differential
    nearby-nodes = map top-scored (fn sp -> nth sp 0)
    iccha-sec    = iccha-bridge nearby-nodes

    -- root: the direct avrti from seeds (abstract principle, shown last)
    root-triples = avrti seeds 1
    root-sec     = concat "  root:\n" (format-triples root-triples "    ")

    result = concat top-section iccha-sec root-sec

  return
    result  string

done
```

---

## Step 3: Remove Fat OCaml Logic from `anuvada.ml`

`render_avrti_for_tantra` shrinks to a thin wrapper (used only by socket fallback):

```ocaml
(* thin version — full logic now lives in anuvada.tantra *)
let render_avrti_for_tantra ?(sahaja = true) ?(context : string option = None)
    (k : proof_graph) (content_words : string list)
    (max_passes : int) (buf : Buffer.t) : unit =
  ignore (sahaja, context, max_passes);
  (* socket fallback: use avrti_anuvada directly, simple format *)
  let (pass_groups, total_passes) = avrti_anuvada k content_words 2 in
  let total_triples = List.fold_left (fun acc (_, ts) -> acc + List.length ts) 0 pass_groups in
  Buffer.add_string buf (Printf.sprintf "  response: (%d passes, %d connections)\n" total_passes total_triples);
  List.iter (fun (_, triples) ->
    List.iter (fun t ->
      Buffer.add_string buf (Printf.sprintf "  %s %s %s.\n"
        t.a_source
        (english_of_visheshanam_from_graph k t.a_relation)
        (String.concat ", " t.a_targets))
    ) triples
  ) pass_groups
```

Keep `avrti_anuvada` intact — it's a clean primitive. The spiral logic moves to tantra.

---

## What Gets Deleted (Breaking Changes Welcome)

### From `vyakarana/lib/yantra.ml` — remove from `op_arity` and `eval_call`:
- `render-walk` — the fat builtin being replaced
- `thread-questions` — removed from output, no longer needed
- `node-info` — unused, `render-node` covers it

### From `vyakarana/lib/anuvada.ml` — delete entirely:
- `render_avrti_for_tantra` (~250 lines) — replace with 10-line socket fallback below
- `render_spiral` — dead code once socket uses the fallback
- `next_thread_question` — only fed `thread-questions` builtin
- All helpers inside render_avrti_for_tantra: `context_score`, `spiral_expand`, `avg_score`,
  `render_primary_buf`, `render_incoming_edges`, `domains_of_node`, `domain_label`, `is_domain_name`

### From `brahman/yantra/`:
- `format-avrti.tantra` — obsolete, was already superseded by `render-walk`

### `avrti` builtin return format — breaking change:
Old: `VList [VFloat pass_num, VList [triples]]` per pass group
New: flat list, pass numbers dropped
Only `anuvada.tantra` uses `avrti` and we're rewriting it.

---

## What Stays in OCaml

- `avrti_anuvada` — the walk itself (mutable visited sets, deduplication — not expressible in tantra)
- `walk_one_pass` — low-level graph traversal
- All the thin builtins listed in Step 1
- `render_darshana_to_buf` — used by `render-node` builtin (keep as-is)
- Socket mode `anuvada_query` — simplify: call `avrti_anuvada` directly, return raw triples in JSON

---

## Implementation Order

1. Add 7 new builtins to `yantra.ml` (`op_arity` + `eval_call`)
2. Change `avrti` return format to flat list of triples
3. Delete `format-avrti.tantra`
4. Create `format-triple.tantra` + `format-triples.tantra`
5. Create `spiral-domain.tantra` + `iccha-bridge.tantra`
6. Update `anuvada.tantra` (replaces `render-walk` with direct primitive calls)
7. Delete `render-walk`, `thread-questions`, `node-info` from `yantra.ml`
8. Delete `render_avrti_for_tantra`, `render_spiral`, `next_thread_question` and all helpers
   from `anuvada.ml` — replace with 10-line socket fallback
9. Build + verify all three paths work

---

## Verification

```bash
cd /home/abe/agent_x/vyakarana && dune build 2>&1

# Core test — shows: biology (concrete) → iccha-bridge → root
printf "what is life?\nVISARJANA\n" | dune exec bin/vyakarana.exe -- ../brahman

# Expected output shape:
#   in biology:
#     eka-kosha is prana; rests-on nucleotide, replication; self-governing.
#       replication: rests-on prana; produces heredity.
#     visha-anu: rests-on prana; no self-governing (iccha-rahita).
#   iccha (directed-will) present in: eka-kosha; absent in: jada, visha-anu.
#   root:
#     prana is jiva; rests-on the-limitless; born-from black-hole.

# Node inspection — still works via darshana.tantra
printf "prana\nVISARJANA\n" | dune exec bin/vyakarana.exe -- ../brahman

# Computation — unchanged
printf "find force when mass is 10 acceleration is 9.8\nVISARJANA\n" | dune exec bin/vyakarana.exe -- ../brahman
```

---

## Notes

- `format-triples-primary.tantra` (renders only the primary relation per source) is needed
  for spiral depth 1 — add after core tantras work
- Other domains beyond top-domain: simple incoming mentions (no spiral) — add in anuvada.tantra
  after top-domain section works
- `sort-desc` acts on `[[item, score], ...]` — second element must be numeric
- `join` builtin (list, separator) already exists in `op_arity` but may not be implemented
  in `eval_call` — check and add if missing
