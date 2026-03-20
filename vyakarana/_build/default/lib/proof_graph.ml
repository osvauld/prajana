(* proof_graph.ml — the proof space
   nodes are nigamana. edges are typed by visheshanam.
   satya is set from local structure at load time (raw_satya / init_satya).
   query-time PPR (run_ppr) produces a posterior score landscape per query.
   the graph holds the truths. the LLM interprets them.

   PPR uses a CSR (Compressed Sparse Row) representation of the incoming-edge
   adjacency, materialized once after build_index by materialize_csr.
   per-query cost: O(N×10) conductance derivation + O(E×iters) SpMV, zero allocation. *)

(* visheshanam — edge dimension.
   now an integer index. core 10 are constants 0-9 (backward-compatible).
   dynamic dimensions (discovered from visheshanam-swarupa edges at startup,
   or registered by tantras at runtime) get indices >= 10.
   the registry is append-only — indices never change once assigned. *)
type visheshanam = int

(* core 10 — these are the constants the rest of the codebase uses *)
let swarupa      = 0   (* identity — X IS Y *)
let abheda       = 1   (* non-different — X = Y at some level *)
let drishthanta  = 2   (* evidence — X demonstrated by Y *)
let sthita       = 3   (* foundation — X stands on Y *)
let yukta        = 4   (* connection — X joined with Y *)
let siddha       = 5   (* proof — X established by Y *)
let kriya        = 6   (* function — X acts as Y *)
let phala        = 7   (* consequence — X results from Y *)
let janya        = 8   (* origin — X born from Y *)
let pratipaksha  = 9   (* inverse — X undoes Y *)

(* ---- dynamic dimension registry (append-only) ---- *)
let _dim_name_to_idx : (string, int) Hashtbl.t = Hashtbl.create 32
let _dim_idx_to_name : (int, string) Hashtbl.t = Hashtbl.create 32
let _dim_next_idx = ref 10  (* next available index; core 0-9 are pre-assigned *)

(* initialize the core 10 in the registry *)
let () =
  (* canonical names: go into both forward and reverse tables *)
  List.iter (fun (name, idx) ->
    Hashtbl.replace _dim_name_to_idx name idx;
    Hashtbl.replace _dim_idx_to_name idx name
  ) [
    ("swarupa", 0); ("abheda", 1); ("drishthanta", 2); ("sthita", 3); ("yukta", 4);
    ("siddha", 5); ("kriya", 6); ("phala", 7); ("janya", 8); ("pratipaksha", 9);
    ("varga", 10);
  ];
  (* aliases: forward lookup only — never overwrite the canonical reverse mapping *)
  List.iter (fun (alias, idx) ->
    Hashtbl.replace _dim_name_to_idx alias idx
  ) [
    ("inverse", 9);
  ]

(* register a new dimension. returns its index. idempotent — if already registered,
   returns the existing index. called by compile phase and by tantras at runtime. *)
let register_dimension (name : string) : int =
  let name = String.lowercase_ascii name in
  match Hashtbl.find_opt _dim_name_to_idx name with
  | Some idx -> idx
  | None ->
    let idx = !_dim_next_idx in
    incr _dim_next_idx;
    Hashtbl.replace _dim_name_to_idx name idx;
    (* only set canonical reverse mapping if not already taken *)
    if not (Hashtbl.mem _dim_idx_to_name idx) then
      Hashtbl.replace _dim_idx_to_name idx name;
    idx

(* how many dimensions exist right now (core + dynamic) *)
let dimension_count () : int = !_dim_next_idx

(* typed edge between two nodes *)
type typed_edge = {
  source   : string;
  target   : string;
  relation : visheshanam;
}

(* one truth in the space *)
type nigamana = {
  name   : string;
  layer  : string;            (* "sangati" | "kosha" | "bhasha" — which layer this node lives in *)
  slokas : string list;       (* raw sloka text, preserved *)
  edges  : typed_edge list;   (* extracted from slokas *)
  satya  : float;             (* raw_satya set at load time; read-only thereafter *)
  shabda : string;            (* key:value mapping data — target-domain rendering *)
}

(* ---- visheshanam ↔ integer index ---- *)
(* identity now — visheshanam IS the index. kept for call-site compat. *)

let visheshanam_to_idx (v : visheshanam) : int = v

(* num_relations: returns current dimension count. call sites that used the
   old constant `num_relations` now call `num_relations ()`. *)
let num_relations () : int = dimension_count ()

(* ---- CSR adjacency — materialized once at startup ---- *)
(* represents the incoming-edge adjacency of the proof graph in Compressed Sparse Row form.
   this is the transpose of the usual adjacency: for PPR we walk incoming edges.
   algebraically: A^T where A[u,v] = conductance(rel(u,v)) / out_cond(u).
   equivalent to matrix-multiplication (map-janya fold-janya dot-product-kriya)
   over the sparse graph tensor. *)
type csr_adjacency = {
  csr_n             : int;                       (* node count N *)
  csr_nnz           : int;                       (* edge count E = |all_edges| *)
  csr_node_to_idx   : (string, int) Hashtbl.t;   (* name → row index 0..N-1 *)
  csr_idx_to_node   : string array;              (* row index → name, length N *)
  csr_in_row_ptr    : int array;                 (* length N+1; row i spans [ptr[i], ptr[i+1]) *)
  csr_in_col_idx    : int array;                 (* length E; source node index per incoming edge *)
  csr_in_rel_idx    : int array;                 (* length E; relation dim index per incoming edge *)
   (* out_rel_count.(u * num_dims + r) = # outgoing edges of type r from node u.
      used per-query to derive out_cond[u] = Σ_r count[u,r] × weights[r] in O(N×D). *)
   csr_out_rel_count : int array;                 (* length N × dimension_count *)
   csr_num_dims      : int;                       (* dimension_count at materialization time *)
  csr_node_satya    : float array;               (* length N; raw_satya per node for PPR init *)
}

(* ---- proof_graph ---- *)
type proof_graph = {
  nodes       : (string, nigamana) Hashtbl.t;
  all_edges   : typed_edge list ref;
  kosha_root  : string ref;   (* base path for resolving shabda-tmpl files *)
  search_dirs : string list ref; (* all loaded dirs — searched for shabda-tmpl files *)
  csr         : csr_adjacency option ref;  (* None until materialize_csr is called *)
}

(* ---- visheshanam properties (populated from .om files at startup) ---- *)

type vish_props = {
  vp_symmetric     : bool;
  vp_antisymmetric : bool;
  vp_transitive    : bool;
  vp_reflexive     : bool;
  vp_involutive    : bool;
  vp_congruence    : bool;
  vp_composable    : bool;
  vp_dual          : int option;  (* dimension index of the dual, if any *)
  vp_ring_op       : [`Add | `Mul | `None];
  vp_satya_weight  : float;   (* edge conductance in PPR — loaded from .om files *)
}

let default_vish_props : vish_props = {
  vp_symmetric     = false;
  vp_antisymmetric = false;
  vp_transitive    = false;
  vp_reflexive     = false;
  vp_involutive    = false;
  vp_congruence    = false;
  vp_composable    = false;
  vp_dual          = None;
  vp_ring_op       = `None;
  vp_satya_weight  = 0.70;   (* conservative default before .om files are loaded *)
}

(* module-level mutable table — populated once by scan_visheshanam_properties *)
let _visheshanam_props : (int, vish_props) Hashtbl.t = Hashtbl.create 16

let register_vish_props (v : visheshanam) (p : vish_props) : unit =
  Hashtbl.replace _visheshanam_props v p

let vish_props_of (v : visheshanam) : vish_props =
  match Hashtbl.find_opt _visheshanam_props v with
  | Some p -> p
  | None   -> default_vish_props

(* visheshanam string conversion — checks core 10 + dynamic registry *)
let visheshanam_of_string (s : string) : visheshanam option =
  Hashtbl.find_opt _dim_name_to_idx (String.lowercase_ascii s)

let string_of_visheshanam (v : visheshanam) : string =
  match Hashtbl.find_opt _dim_idx_to_name v with
  | Some name -> name
  | None -> Printf.sprintf "dim-%d" v


(* the space was already there *)
let empty () : proof_graph = {
  nodes       = Hashtbl.create 64;
  all_edges   = ref [];
  kosha_root  = ref "";
  search_dirs = ref [];
  csr         = ref None;
}

(* join a nigamana into the space — merge edges, never overwrite *)
let join (k : proof_graph) (n : nigamana) : proof_graph =
  (match Hashtbl.find_opt k.nodes n.name with
   | None ->
     (* new node: add directly, register all its edges *)
     Hashtbl.replace k.nodes n.name n;
     k.all_edges := n.edges @ !(k.all_edges)
   | Some existing ->
     (* existing node: merge edges (deduplicate by source+target+relation) *)
     let new_edges = List.filter (fun e ->
       not (List.exists (fun ex ->
         ex.source = e.source && ex.target = e.target && ex.relation = e.relation
       ) existing.edges)
     ) n.edges in
     let merged = { existing with edges = existing.edges @ new_edges } in
     Hashtbl.replace k.nodes n.name merged;
     (* only add genuinely new edges to all_edges *)
     k.all_edges := new_edges @ !(k.all_edges));
  k

(* find by name *)
let find (k : proof_graph) (name : string) : nigamana option =
  Hashtbl.find_opt k.nodes name

(* in-degree: how many edges point TO this node *)
let in_degree (k : proof_graph) (name : string) : int =
  List.length (List.filter (fun e -> e.target = name) !(k.all_edges))

(* out-degree: how many edges go FROM this node *)
let out_degree (k : proof_graph) (name : string) : int =
  List.length (List.filter (fun e -> e.source = name) !(k.all_edges))

(* neighbors: all nodes connected to this node (both directions) *)
let neighbors (k : proof_graph) (name : string) : string list =
  let targets = List.filter_map (fun e ->
    if e.source = name then Some e.target else None
  ) !(k.all_edges) in
  let sources = List.filter_map (fun e ->
    if e.target = name then Some e.source else None
  ) !(k.all_edges) in
  List.sort_uniq String.compare (targets @ sources)

(* edges involving a node *)
let edges_of (k : proof_graph) (name : string) : typed_edge list =
  List.filter (fun e -> e.source = name || e.target = name) !(k.all_edges)

(* ---- json_of_nigamana: serialize one om node for dump-om ---- *)

let json_escape_pg s =
  let buf = Buffer.create (String.length s) in
  String.iter (fun c ->
    match c with
    | '"'  -> Buffer.add_string buf "\\\""
    | '\\' -> Buffer.add_string buf "\\\\"
    | '\n' -> Buffer.add_string buf "\\n"
    | '\r' -> Buffer.add_string buf "\\r"
    | '\t' -> Buffer.add_string buf "\\t"
    | c    -> Buffer.add_char buf c
  ) s;
  Buffer.contents buf

let je_pg s = "\"" ^ json_escape_pg s ^ "\""

let json_of_nigamana (n : nigamana) : string =
  let slokas_json = String.concat ","
    (List.map (fun s -> je_pg s) n.slokas) in
  let edges_json = String.concat ","
    (List.map (fun e ->
      Printf.sprintf "{\"source\":%s,\"target\":%s,\"relation\":%s}"
        (je_pg e.source) (je_pg e.target) (je_pg (string_of_visheshanam e.relation))
    ) n.edges) in
  Printf.sprintf
    "{\"name\":%s,\"layer\":%s,\"satya\":%.4f,\"slokas\":[%s],\"edges\":[%s],\"shabda\":%s}"
    (je_pg n.name) (je_pg n.layer) n.satya slokas_json edges_json (je_pg n.shabda)

(* ---- satya: raw structural prior ---- *)

(* raw_satya: pure function of local topology — sloka count, edge count, type diversity.
   set once at load time into nigamana.satya. never iterated.
   PPR handles neighbour influence per query at runtime. *)
let raw_satya (n : nigamana) : float =
  let sloka_count = float_of_int (List.length n.slokas) in
  let edge_count = float_of_int (List.length n.edges) in
  let visheshanam_types = List.sort_uniq compare
    (List.map (fun e -> e.relation) n.edges) in
  let type_diversity = float_of_int (List.length visheshanam_types) in
  let s = sloka_count /. (1.0 +. sloka_count) in
  let e = edge_count /. (1.0 +. edge_count) in
  let d = type_diversity /. (1.0 +. type_diversity) in
  let base =
    if edge_count = 0.0 then
      s *. 0.5
    else
      (s *. e *. d) ** (1.0 /. 3.0)
  in
  (* bhasha nodes are surface pointers — not semantic substance.
     halve their prior so PPR strongly prefers kosha/sangati neighbours. *)
  match n.layer with
  | "bhasha" -> base *. 0.5
  | _        -> base

(* init_satya: set raw_satya on every node once at load time.
   called by build_index after apply_relation_axioms. *)
let init_satya (k : proof_graph) : unit =
  Hashtbl.iter (fun _ n ->
    let r = raw_satya n in
    Hashtbl.replace k.nodes n.name { n with satya = r }
  ) k.nodes

(* compute_visheshanam_entropy_weights: derive vp_satya_weight for each relation type
   from the Shannon entropy of its target distribution across all edges in the graph.

    For each relation r:
      p_r(v) = count(edges of type r with target v) / count(all edges of type r)
      H_r    = -Σ_v p_r(v) × ln(p_r(v))
      H_max  = ln(unique targets of r)
      w_raw  = 1 - H_r / H_max

    Then rescale all w_raw into [0.5, 0.95]:
      w_r = 0.5 + (w_raw - w_min) / (w_max - w_min) × 0.45

    Low entropy  → concentrated targets → strong inference → high w_r
    High entropy → spread targets       → weak inference  → low w_r

    Must be called after apply_relation_axioms (so symmetry edges are counted)
    and after the graph is fully loaded. Reads all_edges, writes into vish_props table. *)
let compute_visheshanam_entropy_weights (k : proof_graph) : unit =
  (* count targets per relation type across all edges *)
  let target_counts : (int, (string, int) Hashtbl.t) Hashtbl.t =
    Hashtbl.create 16 in
  let total_per_rel : (int, int) Hashtbl.t = Hashtbl.create 16 in
  List.iter (fun (e : typed_edge) ->
    let tbl = match Hashtbl.find_opt target_counts e.relation with
      | Some t -> t
      | None ->
        let t = Hashtbl.create 64 in
        Hashtbl.replace target_counts e.relation t; t
    in
    let prev = match Hashtbl.find_opt tbl e.target with Some c -> c | None -> 0 in
    Hashtbl.replace tbl e.target (prev + 1);
    let pt = match Hashtbl.find_opt total_per_rel e.relation with Some c -> c | None -> 0 in
    Hashtbl.replace total_per_rel e.relation (pt + 1)
  ) !(k.all_edges);
  (* compute raw entropy weight for each registered dimension *)
  let ndims = dimension_count () in
  let all_rels = List.init ndims (fun i -> i) in
  let raw_pairs = List.map (fun rel ->
    let w_raw = match Hashtbl.find_opt target_counts rel with
      | None -> 0.0
      | Some tbl ->
        let total = float_of_int
          (match Hashtbl.find_opt total_per_rel rel with Some c -> c | None -> 1) in
        let n_unique = float_of_int (Hashtbl.length tbl) in
        let h_rel_max = if n_unique > 1.0 then log n_unique else 1.0 in
        let h = Hashtbl.fold (fun _ count acc ->
          let p = float_of_int count /. total in
          acc -. p *. log p
        ) tbl 0.0 in
        (* normalise against this relation's own unique-target entropy ceiling,
           not against log|V| — measures concentration relative to actual reach *)
        1.0 -. (h /. h_rel_max)
    in
    (rel, w_raw)
  ) all_rels in
  (* rescale all w_raw into [0.5, 0.95] *)
  let raw_weights = List.map snd raw_pairs in
  let w_min = List.fold_left Float.min Float.max_float raw_weights in
  let w_max = List.fold_left Float.max Float.min_float raw_weights in
  let range = w_max -. w_min in
  List.iter (fun (rel, w_raw) ->
    let w = if range > 1e-9
            then 0.5 +. ((w_raw -. w_min) /. range) *. 0.45
            else 0.70 in
    let existing = vish_props_of rel in
    register_vish_props rel { existing with vp_satya_weight = w }
  ) raw_pairs

(* ---- CSR materialization ---- *)

(* materialize_csr: build CSR arrays from the frozen all_edges list.
   called once after build_index + compute_visheshanam_entropy_weights.
   after this call, !(k.csr) = Some csr and run_ppr uses the CSR path.

   pass 1: assign integer indices to all nodes in k.nodes.
   pass 2: count incoming edges per target node → in_counts[N].
   pass 3: prefix-sum in_counts → in_row_ptr[N+1].
   pass 4: fill in_col_idx and in_rel_idx; accumulate out_rel_count.
   pass 5: fill node_satya from each node's satya field.
   assert invariants: ptr[0]=0, ptr[N]=E, all indices in bounds.
   print stats. *)
let materialize_csr (k : proof_graph) : unit =
  let edges = !(k.all_edges) in
  let n = Hashtbl.length k.nodes in
  let nnz = List.length edges in

  (* pass 1: assign indices to nodes — deterministic order via sorted names *)
  let node_to_idx : (string, int) Hashtbl.t = Hashtbl.create (n * 2) in
  let idx_to_node : string array = Array.make n "" in
  let sorted_names =
    Hashtbl.fold (fun name _ acc -> name :: acc) k.nodes []
    |> List.sort String.compare
  in
  List.iteri (fun i name ->
    Hashtbl.replace node_to_idx name i;
    idx_to_node.(i) <- name
  ) sorted_names;

  (* pass 2: count incoming edges per target node *)
  let in_counts = Array.make n 0 in
  List.iter (fun (e : typed_edge) ->
    match Hashtbl.find_opt node_to_idx e.target with
    | Some ti -> in_counts.(ti) <- in_counts.(ti) + 1
    | None    -> ()   (* target not in graph — skip *)
  ) edges;

  (* pass 3: prefix-sum → in_row_ptr *)
  let in_row_ptr = Array.make (n + 1) 0 in
  for i = 0 to n - 1 do
    in_row_ptr.(i + 1) <- in_row_ptr.(i) + in_counts.(i)
  done;
  (* in_row_ptr.(n) should equal the number of edges whose target is in the graph *)
  let actual_nnz = in_row_ptr.(n) in

  (* pass 4: fill CSR arrays using insertion pointers *)
  let ndims = num_relations () in
  let in_col_idx    = Array.make actual_nnz 0 in
  let in_rel_idx    = Array.make actual_nnz 0 in
  let out_rel_count = Array.make (n * ndims) 0 in
  let insert_ptr    = Array.copy in_row_ptr in  (* insertion cursors per row *)
  List.iter (fun (e : typed_edge) ->
    let ri = visheshanam_to_idx e.relation in
    (* incoming edge: fills the target's row in the CSR *)
    (match Hashtbl.find_opt node_to_idx e.target with
     | Some ti ->
       let pos = insert_ptr.(ti) in
       in_col_idx.(pos) <- (match Hashtbl.find_opt node_to_idx e.source with
         | Some si -> si
         | None    -> 0);  (* source not in graph: use index 0 as sentinel, weight ~0 *)
       in_rel_idx.(pos) <- ri;
       insert_ptr.(ti) <- pos + 1
     | None -> ());
    (* outgoing edge: accumulate out_rel_count for the source *)
    (match Hashtbl.find_opt node_to_idx e.source with
     | Some si -> out_rel_count.(si * ndims + ri) <- out_rel_count.(si * ndims + ri) + 1
     | None    -> ())
  ) edges;

  (* pass 5: fill node_satya *)
  let node_satya = Array.make n 0.0 in
  Array.iteri (fun i name ->
    match Hashtbl.find_opt k.nodes name with
    | Some nd -> node_satya.(i) <- nd.satya
    | None    -> ()
  ) idx_to_node;

  (* assertions *)
  assert (in_row_ptr.(0) = 0);
  assert (in_row_ptr.(n) = actual_nnz);
  Array.iter (fun idx -> assert (idx >= 0 && idx < n)) in_col_idx;
  Array.iter (fun r   -> assert (r   >= 0 && r   < ndims)) in_rel_idx;

  let csr = {
    csr_n             = n;
    csr_nnz           = actual_nnz;
    csr_node_to_idx   = node_to_idx;
    csr_idx_to_node   = idx_to_node;
    csr_in_row_ptr    = in_row_ptr;
    csr_in_col_idx    = in_col_idx;
    csr_in_rel_idx    = in_rel_idx;
    csr_out_rel_count = out_rel_count;
    csr_node_satya    = node_satya;
    csr_num_dims      = ndims;
  } in
  k.csr := Some csr;
  let density = if n > 0 then
    float_of_int actual_nnz /. (float_of_int n *. float_of_int n *. float_of_int ndims) *. 100.0
  else 0.0 in
  Printf.printf "csr: materialized %d nodes, %d edges (of %d total), density %.4f%%\n%!"
    n actual_nnz nnz density

(* ---- PPR engine: structure-driven Personalized PageRank ---- *)

(* compute_depth_affinity: derive BFS-vs-PPR blend from query graph structure.
   Three signals:
     binding_density  = |binding_names| / (|target_edges| + 1)
     link_ratio       = count(bindings directly connected to target) / (|binding_names| + 1)
     computational_ratio = (Sthita+Phala+Kriya edges on target) / total_target_edges
   depth_affinity = geometric_mean of the three, clamped to [0, 1].
   depth_affinity=1.0 → pure BFS (tight computation query)
   depth_affinity=0.0 → pure PPR (open conceptual query) *)
let compute_depth_affinity (k : proof_graph) (target : string)
    (binding_names : string list) : float =
  let n_bindings = float_of_int (List.length binding_names) in
  let target_edges = match Hashtbl.find_opt k.nodes target with
    | None -> []
    | Some n -> n.edges
  in
  let n_target_edges = float_of_int (List.length target_edges) in
  (* binding_density *)
  let binding_density = n_bindings /. (n_target_edges +. 1.0) in
  let binding_density = Float.min 1.0 binding_density in
  (* link_ratio: how many binding names have a direct edge to/from target *)
  let direct_links = List.length (List.filter (fun bname ->
    List.exists (fun e ->
      (e.source = bname && e.target = target) ||
      (e.source = target && e.target = bname)
    ) !(k.all_edges)
  ) binding_names) in
  let link_ratio = float_of_int direct_links /. (n_bindings +. 1.0) in
  let link_ratio = Float.min 1.0 link_ratio in
  (* computational_ratio: fraction of target edges that are Sthita/Phala/Kriya *)
  let comp_edges = List.length (List.filter (fun e ->
    e.relation = sthita || e.relation = phala || e.relation = kriya
  ) target_edges) in
  let computational_ratio =
    if n_target_edges = 0.0 then 0.0
    else float_of_int comp_edges /. n_target_edges
  in
  (* geometric mean *)
  let product = binding_density *. link_ratio *. computational_ratio in
  if product <= 0.0 then 0.0
  else Float.min 1.0 (product ** (1.0 /. 3.0))

(* run_ppr: query-time Personalized PageRank using precomputed CSR adjacency.
   Algorithm:
     1. Derive per-relation conductances from seed neighbourhood (O(|seed_edges|)).
     2. Derive per-node out_cond from out_rel_count × weights (O(N×10)).
     3. Normalize seed to float array[N] (O(N)).
     4. Initialize score vector from seed (O(N)).
     5. Iterate SpMV: p_new[v] = α×seed[v] + (1-α)×Σ_{u→v} p[u]×w[r]/out_cond[u]
        until max_delta < 0.001 or 50 iterations.
     6. Build result Hashtbl from score array (O(N)).
   alpha = 0.30 (restart probability).
   Requires materialize_csr to have been called; raises Failure otherwise. *)
let run_ppr (k : proof_graph)
    ~(seed_nodes : (string * float) list)
    ~(target : string)
    ~(binding_names : string list)
    : (string, float) Hashtbl.t =
  let csr = match !(k.csr) with
    | Some c -> c
    | None   -> failwith "run_ppr: CSR not materialized — call Proof_graph.materialize_csr after build_index"
  in
  let n     = csr.csr_n in
  let ndims = csr.csr_num_dims in
  let alpha = 0.30 in

  (* 1. derive per-relation conductances from seed neighbourhood.
        seed_edge_freq(r) = # edges of type r touching seed nodes / total seed edges
        weights[r] = vp_satya_weight(r) × (1 + seed_edge_freq(r)) *)
  let freq  = Array.make ndims 0 in
  let total_seed_edges = ref 0 in
  List.iter (fun (name, _) ->
    match Hashtbl.find_opt k.nodes name with
    | None -> ()
    | Some nd ->
      List.iter (fun e ->
        let r = visheshanam_to_idx e.relation in
        freq.(r) <- freq.(r) + 1;
        incr total_seed_edges
      ) nd.edges
  ) seed_nodes;
  let total_f = float_of_int (max 1 !total_seed_edges) in
  let weights = Array.init ndims (fun r ->
    (* dimension index IS the visheshanam — look up props directly *)
    let base = (vish_props_of r).vp_satya_weight in
    base *. (1.0 +. float_of_int freq.(r) /. total_f)
  ) in

  (* 2. derive per-node out_cond from precomputed out_rel_count × weights.
        out_cond[u] = Σ_r out_rel_count[u,r] × weights[r]
        O(N × D) with sequential array access — cache-friendly. *)
  let out_cond = Array.make n 1.0 in
  for u = 0 to n - 1 do
    let oc = ref 0.0 in
    for r = 0 to ndims - 1 do
      oc := !oc +. float_of_int csr.csr_out_rel_count.(u * ndims + r) *. weights.(r)
    done;
    out_cond.(u) <- if !oc <= 0.0 then 1.0 else !oc
  done;

  (* 3. normalize seed to sum 1 → seed_norm Hashtbl for name lookup *)
  let seed_sum = List.fold_left (fun acc (_, w) -> acc +. w) 0.0 seed_nodes in
  let seed_sum = if seed_sum <= 0.0 then 1.0 else seed_sum in
  let seed_norm : (string, float) Hashtbl.t = Hashtbl.create 16 in
  List.iter (fun (name, w) ->
    let prev = match Hashtbl.find_opt seed_norm name with Some v -> v | None -> 0.0 in
    Hashtbl.replace seed_norm name (prev +. w /. seed_sum)
  ) seed_nodes;

  (* 4. initialize score and seed arrays over N nodes *)
  let seed_arr  = Array.make n 0.0 in
  let scores    = Array.make n 0.0 in
  for i = 0 to n - 1 do
    let name = csr.csr_idx_to_node.(i) in
    let sv = match Hashtbl.find_opt seed_norm name with
      | Some s -> s
      | None   -> csr.csr_node_satya.(i) *. 0.01
    in
    seed_arr.(i) <- sv;
    scores.(i)   <- sv
  done;

  (* 5. SpMV iteration loop — zero allocation per iteration.
        inner loop: for each incoming edge (u→v), accumulate p[u]×w[r]/out_cond[u].
        sequential reads on in_col_idx and in_rel_idx → cache-friendly.
        weights[10] stays in registers or L1. *)
  let new_scores   = Array.make n 0.0 in
  let max_iters    = 50 in
  let threshold    = 0.001 in
  let converged    = ref false in
  let iter         = ref 0 in
  while not !converged && !iter < max_iters do
    incr iter;
    let max_delta = ref 0.0 in
    for v = 0 to n - 1 do
      let incoming = ref 0.0 in
      let row_start = csr.csr_in_row_ptr.(v) in
      let row_end   = csr.csr_in_row_ptr.(v + 1) in
      let e = ref row_start in
      while !e < row_end do
        let u  = csr.csr_in_col_idx.(!e) in
        let r  = csr.csr_in_rel_idx.(!e) in
        incoming := !incoming +. scores.(u) *. weights.(r) /. out_cond.(u);
        incr e
      done;
      let nv = alpha *. seed_arr.(v) +. (1.0 -. alpha) *. !incoming in
      let delta = Float.abs (nv -. scores.(v)) in
      if delta > !max_delta then max_delta := delta;
      new_scores.(v) <- nv
    done;
    Array.blit new_scores 0 scores 0 n;
    if !max_delta < threshold then converged := true
  done;

  (* 6. build result Hashtbl from score array *)
  let result : (string, float) Hashtbl.t = Hashtbl.create n in
  for i = 0 to n - 1 do
    Hashtbl.replace result csr.csr_idx_to_node.(i) scores.(i)
  done;

  (* depth_affinity computation — unchanged, reads k.nodes and k.all_edges *)
  ignore (compute_depth_affinity k target binding_names);
  result

(* depth_affinity exposed separately for beam search in yantra_resolver *)
let query_depth_affinity (k : proof_graph) (target : string)
    (binding_names : string list) : float =
  compute_depth_affinity k target binding_names

(* walk_inheritance: collect ancestor nodes for shabda inheritance.
   follows dhatu, abheda, and swarupa edges — IS-A relationships only.
   dhatu is a dynamic dimension looked up by name; gracefully absent if not yet registered.
   returns ancestors in BFS order: immediate parents first, then grandparents.
   depth-limited to 4 hops to bound cost and avoid pathological graphs.

   which edges carry inheritance (IS-A only):
     abheda    — "is a kind of"   (static dim 1)
     swarupa   — "essentially is" (static dim 0)
     dhatu     — word-form IS-A concept root (dynamic, may not yet be registered)

   edges that do NOT carry inheritance (relations, not IS-A):
     yukta, kriya, phala, janya, pratipaksha, sandhi, matra, ... *)
let walk_inheritance (k : proof_graph) (node_name : string) : string list =
  let dhatu_idx = visheshanam_of_string "dhatu" in
  let vishesa_idx = visheshanam_of_string "vishesa" in
  let amsha_idx = visheshanam_of_string "amsha" in
  let is_inheritance_edge rel =
    rel = abheda || rel = swarupa ||
    (match dhatu_idx with Some d -> rel = d | None -> false) ||
    (match vishesa_idx with Some v -> rel = v | None -> false) ||
    (match amsha_idx with Some a -> rel = a | None -> false)
  in
  let immediate_parents name =
    match Hashtbl.find_opt k.nodes name with
    | None -> []
    | Some n ->
      List.filter_map (fun e ->
        if e.source = name && is_inheritance_edge e.relation
        then Some e.target else None
      ) n.edges
  in
  let visited = Hashtbl.create 8 in
  Hashtbl.replace visited node_name true;
  let result = ref [] in
  let frontier = ref (immediate_parents node_name) in
  for _ = 1 to 4 do
    let next_frontier = ref [] in
    List.iter (fun p ->
      if not (Hashtbl.mem visited p) then begin
        Hashtbl.replace visited p true;
        result := p :: !result;
        next_frontier := (immediate_parents p) @ !next_frontier
      end
    ) !frontier;
    frontier := !next_frontier
  done;
  List.rev !result

(* ---- surgical graph mutation ---- *)

(* replace_node: overwrite a node entirely — edges, shabda, slokas.
   removes old outgoing edges from all_edges, adds new ones.
   incoming edges from other nodes are untouched — they belong to those nodes.
   use after editing a file on disk and re-parsing it. *)
let replace_node (k : proof_graph) (n : nigamana) : unit =
  (* remove old outgoing edges for this node from all_edges *)
  k.all_edges := List.filter (fun e ->
    e.source <> n.name
  ) !(k.all_edges);
  (* add new edges *)
  k.all_edges := n.edges @ !(k.all_edges);
  (* replace node *)
  Hashtbl.replace k.nodes n.name n

(* remove_node: delete a node and all edges touching it *)
let remove_node (k : proof_graph) (name : string) : unit =
  Hashtbl.remove k.nodes name;
  k.all_edges := List.filter (fun e ->
    e.source <> name && e.target <> name
  ) !(k.all_edges)

(* add_single_edge: add one edge to the graph *)
let add_single_edge (k : proof_graph) (e : typed_edge) : unit =
  (* add to source node's edge list *)
  (match Hashtbl.find_opt k.nodes e.source with
   | Some n ->
     let already = List.exists (fun ex ->
       ex.source = e.source && ex.target = e.target && ex.relation = e.relation
     ) n.edges in
     if not already then
       Hashtbl.replace k.nodes n.name { n with edges = e :: n.edges }
   | None -> ());
  (* add to global edge list *)
  k.all_edges := e :: !(k.all_edges)

(* remove_single_edge: remove one specific edge *)
let remove_single_edge (k : proof_graph) (e : typed_edge) : unit =
  (* remove from source node's edge list *)
  (match Hashtbl.find_opt k.nodes e.source with
   | Some n ->
     let filtered = List.filter (fun ex ->
       not (ex.source = e.source && ex.target = e.target && ex.relation = e.relation)
     ) n.edges in
     Hashtbl.replace k.nodes n.name { n with edges = filtered }
   | None -> ());
  (* remove from global edge list *)
  k.all_edges := List.filter (fun ex ->
    not (ex.source = e.source && ex.target = e.target && ex.relation = e.relation)
  ) !(k.all_edges)
