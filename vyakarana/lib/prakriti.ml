(* prakriti.ml — the proof space
   nodes are nigamana. edges are typed by visheshanam.
   satya is set from local structure at load time.
   query-time PPR produces a posterior score landscape per query.
   CSR (Compressed Sparse Row) for incoming-edge adjacency, materialized once.

   sections:
     1. visheshanam — edge dimensions (core 10 + dynamic registry)
     2. types — nigamana, typed_edge, proof_graph, vish_props, event
     3. graph — create, join, find, degree, neighbors, edges, mutation
     4. helpers — json_escape, with_node
     5. json — serialize nigamana
     6. satya — raw structural prior, entropy weights
     7. csr — materialization
     8. ppr — personalized pagerank + depth affinity *)

(* ═══════════════════════════════════════════════════════════════════════════
   1. VISHESHANAM — edge dimensions
   ═══════════════════════════════════════════════════════════════════════════ *)

type visheshanam = int

(* core 10 — constants the rest of the codebase uses *)
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

(* dynamic dimension registry (append-only) *)
let _dim_name_to_idx : (string, int) Hashtbl.t = Hashtbl.create 32
let _dim_idx_to_name : (int, string) Hashtbl.t = Hashtbl.create 32
let _dim_next_idx = ref 10

let () =
  List.iter (fun (name, idx) ->
    Hashtbl.replace _dim_name_to_idx name idx;
    Hashtbl.replace _dim_idx_to_name idx name
  ) [
    ("swarupa", 0); ("abheda", 1); ("drishthanta", 2); ("sthita", 3); ("yukta", 4);
    ("siddha", 5); ("kriya", 6); ("phala", 7); ("janya", 8); ("pratipaksha", 9);
    ("varga", 10);
  ];
  List.iter (fun (alias, idx) ->
    Hashtbl.replace _dim_name_to_idx alias idx
  ) [
    ("inverse", 9);
  ]

let _dim_mu = Mutex.create ()

let register_dimension (name : string) : int =
  let name = String.lowercase_ascii name in
  Mutex.lock _dim_mu;
  let result = match Hashtbl.find_opt _dim_name_to_idx name with
    | Some idx -> idx
    | None ->
      let idx = !_dim_next_idx in
      incr _dim_next_idx;
      Hashtbl.replace _dim_name_to_idx name idx;
      if not (Hashtbl.mem _dim_idx_to_name idx) then
        Hashtbl.replace _dim_idx_to_name idx name;
      idx
  in
  Mutex.unlock _dim_mu;
  result

let dimension_count () : int = !_dim_next_idx

let visheshanam_of_string (s : string) : visheshanam option =
  Hashtbl.find_opt _dim_name_to_idx (String.lowercase_ascii s)

let string_of_visheshanam (v : visheshanam) : string =
  match Hashtbl.find_opt _dim_idx_to_name v with
  | Some name -> name
  | None -> Printf.sprintf "dim-%d" v

let ensure_dim (name : string) : visheshanam =
  match visheshanam_of_string name with Some d -> d | None -> register_dimension name

(* ═══════════════════════════════════════════════════════════════════════════
   2. TYPES
   ═══════════════════════════════════════════════════════════════════════════ *)

type typed_edge = {
  source   : string;
  target   : string;
  relation : visheshanam;
}

type nigamana = {
  name   : string;
  layer  : string;
  domain : string;
  slokas : string list;
  edges  : typed_edge list;
  satya  : float;
  shabda : string;
  krama  : string;
}

type csr_adjacency = {
  csr_n             : int;
  csr_nnz           : int;
  csr_node_to_idx   : (string, int) Hashtbl.t;
  csr_idx_to_node   : string array;
  csr_in_row_ptr    : int array;
  csr_in_col_idx    : int array;
  csr_in_rel_idx    : int array;
  csr_out_rel_count : int array;
  csr_num_dims      : int;
  csr_node_satya    : float array;
}

type proof_graph = {
  nodes       : (string, nigamana) Hashtbl.t;
  all_edges   : typed_edge list ref;
  kosha_root  : string ref;
  search_dirs : string list ref;
  csr         : csr_adjacency option ref;
}

type vish_props = {
  vp_symmetric     : bool;
  vp_antisymmetric : bool;
  vp_transitive    : bool;
  vp_reflexive     : bool;
  vp_involutive    : bool;
  vp_congruence    : bool;
  vp_composable    : bool;
  vp_reversible    : bool;
  vp_inheritable   : bool;
  vp_dual          : int option;
  vp_ring_op       : [`Add | `Mul | `None];
  vp_satya_weight  : float;
}

(* event — what moves through the proof space *)
type event =
  | Darshana of { name : string }
  | Anuvada  of { sentence : string; max_passes : int option }
  | Yantra   of { sentence : string }
  | Sthiti
  | Pravaha
  | Visarjana

(* ═══════════════════════════════════════════════════════════════════════════
   3. GRAPH — create, join, find, degree, neighbors, edges, mutation
   ═══════════════════════════════════════════════════════════════════════════ *)

let default_vish_props : vish_props = {
  vp_symmetric     = false;
  vp_antisymmetric = false;
  vp_transitive    = false;
  vp_reflexive     = false;
  vp_involutive    = false;
  vp_congruence    = false;
  vp_composable    = false;
  vp_reversible    = false;
  vp_inheritable   = false;
  vp_dual          = None;
  vp_ring_op       = `None;
  vp_satya_weight  = 0.70;
}

let _visheshanam_props : (int, vish_props) Hashtbl.t = Hashtbl.create 16

let register_vish_props (v : visheshanam) (p : vish_props) : unit =
  Hashtbl.replace _visheshanam_props v p

let vish_props_of (v : visheshanam) : vish_props =
  match Hashtbl.find_opt _visheshanam_props v with
  | Some p -> p
  | None   -> default_vish_props

let empty () : proof_graph = {
  nodes       = Hashtbl.create 64;
  all_edges   = ref [];
  kosha_root  = ref "";
  search_dirs = ref [];
  csr         = ref None;
}

(* node_key: when both nodes have domain and domains differ, use domain/name
   to keep them distinct. Otherwise use plain name (backward compat). *)
let node_key (n : nigamana) : string =
  if n.domain = "" then n.name
  else n.domain ^ "/" ^ n.name

let join (k : proof_graph) (n : nigamana) : proof_graph =
  let key = node_key n in
  (match Hashtbl.find_opt k.nodes key with
   | None ->
     (* Check: is there an existing node under plain name with different domain? *)
     let collision = n.domain <> "" && Hashtbl.find_opt k.nodes n.name <> None &&
       (match Hashtbl.find_opt k.nodes n.name with
        | Some ex -> ex.domain <> "" && ex.domain <> n.domain
        | None -> false) in
     if collision then begin
       (* Re-key the existing node under its domain/name *)
       let ex = Hashtbl.find k.nodes n.name in
       let ex_key = node_key ex in
       if ex_key <> n.name then begin
         Hashtbl.replace k.nodes ex_key ex;
         Hashtbl.remove k.nodes n.name
       end
     end;
     Hashtbl.replace k.nodes key n;
     k.all_edges := n.edges @ !(k.all_edges)
   | Some existing ->
     let new_edges = List.filter (fun e ->
       not (List.exists (fun ex ->
         ex.source = e.source && ex.target = e.target && ex.relation = e.relation
       ) existing.edges)
     ) n.edges in
     let merged = { existing with edges = existing.edges @ new_edges } in
     Hashtbl.replace k.nodes key merged;
     k.all_edges := new_edges @ !(k.all_edges));
  k

(* layer_priority: lower = preferred when multiple domain-qualified matches exist *)
let layer_priority (layer : string) : int =
  match layer with
  | "bhasha"  -> 0  (* word-bearing nodes preferred *)
  | "kosha"   -> 1
  | "sangati" -> 2
  | "mantra"  -> 3
  | _         -> 4

(* find: tries exact name first, then scans for domain/name matches.
   When multiple domain-qualified matches exist, prefers bhasha > kosha > sangati > mantra. *)
let find (k : proof_graph) (name : string) : nigamana option =
  match Hashtbl.find_opt k.nodes name with
  | Some _ as r -> r
  | None ->
    let suffix = "/" ^ name in
    let slen = String.length suffix in
    Hashtbl.fold (fun key n acc ->
      let klen = String.length key in
      if klen > slen &&
         String.sub key (klen - slen) slen = suffix
      then
        match acc with
        | None -> Some n
        | Some prev ->
          if layer_priority n.layer < layer_priority prev.layer
          then Some n else acc
      else acc
    ) k.nodes None

(* with_node: shared pattern — match find_opt k.nodes name → None/Some.
   used across 7+ modules in v1; now a single helper. *)
let with_node (k : proof_graph) (name : string) (f : nigamana -> 'a) (default : 'a) : 'a =
  match find k name with
  | Some n -> f n
  | None   -> default

let in_degree (k : proof_graph) (name : string) : int =
  List.length (List.filter (fun e -> e.target = name) !(k.all_edges))

let out_degree (k : proof_graph) (name : string) : int =
  List.length (List.filter (fun e -> e.source = name) !(k.all_edges))

let neighbors (k : proof_graph) (name : string) : string list =
  let targets = List.filter_map (fun e ->
    if e.source = name then Some e.target else None
  ) !(k.all_edges) in
  let sources = List.filter_map (fun e ->
    if e.target = name then Some e.source else None
  ) !(k.all_edges) in
  List.sort_uniq String.compare (targets @ sources)

let edges_of (k : proof_graph) (name : string) : typed_edge list =
  List.filter (fun e -> e.source = name || e.target = name) !(k.all_edges)

(* — mutation — *)

let replace_node (k : proof_graph) (n : nigamana) : unit =
  k.all_edges := List.filter (fun e -> e.source <> n.name) !(k.all_edges);
  k.all_edges := n.edges @ !(k.all_edges);
  Hashtbl.replace k.nodes n.name n

let remove_node (k : proof_graph) (name : string) : unit =
  Hashtbl.remove k.nodes name;
  k.all_edges := List.filter (fun e ->
    e.source <> name && e.target <> name
  ) !(k.all_edges)

let add_single_edge (k : proof_graph) (e : typed_edge) : unit =
  (match Hashtbl.find_opt k.nodes e.source with
   | Some n ->
     let already = List.exists (fun ex ->
       ex.source = e.source && ex.target = e.target && ex.relation = e.relation
     ) n.edges in
     if not already then
       Hashtbl.replace k.nodes n.name { n with edges = e :: n.edges }
   | None -> ());
  k.all_edges := e :: !(k.all_edges)

let remove_single_edge (k : proof_graph) (e : typed_edge) : unit =
  (match Hashtbl.find_opt k.nodes e.source with
   | Some n ->
     let filtered = List.filter (fun ex ->
       not (ex.source = e.source && ex.target = e.target && ex.relation = e.relation)
     ) n.edges in
     Hashtbl.replace k.nodes n.name { n with edges = filtered }
   | None -> ());
  k.all_edges := List.filter (fun ex ->
    not (ex.source = e.source && ex.target = e.target && ex.relation = e.relation)
  ) !(k.all_edges)

(* ═══════════════════════════════════════════════════════════════════════════
   4. HELPERS — shared utilities
   ═══════════════════════════════════════════════════════════════════════════ *)

(* single json_escape — replaces 4 duplicated copies across v1 modules *)
let json_escape s =
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

let je s = "\"" ^ json_escape s ^ "\""

(* per-thread CPU time in microseconds — excludes Domain contention *)
external thread_cpu_us : unit -> float = "caml_thread_cpu_us"

(* dir_walk: recursive directory walk collecting files by extension.
   replaces 3 duplicated copies (om_parser, om5_parser, yantra_index). *)
let dir_walk (root : string) (ext : string) : string list =
  let files = ref [] in
  let rec walk dir =
    try
      let entries = Sys.readdir dir in
      Array.iter (fun entry ->
        let path = Filename.concat dir entry in
        if Sys.is_directory path then walk path
        else if Filename.check_suffix path ext then
          files := path :: !files
      ) entries
    with Sys_error _ -> ()
  in
  walk root;
  List.sort String.compare !files

(* read_file: read file into string list.
   replaces 5 duplicated copies (om_parser, om5_parser, om_writer, om_edit, setu_shabda). *)
let read_file (path : string) : string list =
  let ic = open_in path in
  let lines = ref [] in
  (try while true do lines := input_line ic :: !lines done
   with End_of_file -> ());
  close_in ic;
  List.rev !lines

(* ═══════════════════════════════════════════════════════════════════════════
   5. JSON — serialize nigamana
   ═══════════════════════════════════════════════════════════════════════════ *)

let json_of_nigamana (n : nigamana) : string =
  let slokas_json = String.concat ","
    (List.map (fun s -> je s) n.slokas) in
  let edges_json = String.concat ","
    (List.map (fun e ->
      Printf.sprintf "{\"source\":%s,\"target\":%s,\"relation\":%s}"
        (je e.source) (je e.target) (je (string_of_visheshanam e.relation))
    ) n.edges) in
  Printf.sprintf
    "{\"name\":%s,\"layer\":%s,\"domain\":%s,\"satya\":%.4f,\"slokas\":[%s],\"edges\":[%s],\"shabda\":%s,\"krama\":%s}"
    (je n.name) (je n.layer) (je n.domain) n.satya slokas_json edges_json (je n.shabda) (je n.krama)

(* ═══════════════════════════════════════════════════════════════════════════
   6. SATYA — raw structural prior + entropy weights
   ═══════════════════════════════════════════════════════════════════════════ *)

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
    if edge_count = 0.0 then s *. 0.5
    else (s *. e *. d) ** (1.0 /. 3.0)
  in
  match n.layer with
  | "bhasha" -> base *. 0.5
  | _        -> base

let init_satya (k : proof_graph) : unit =
  Hashtbl.iter (fun _ n ->
    let r = raw_satya n in
    Hashtbl.replace k.nodes n.name { n with satya = r }
  ) k.nodes

let compute_visheshanam_entropy_weights (k : proof_graph) : unit =
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
        1.0 -. (h /. h_rel_max)
    in
    (rel, w_raw)
  ) all_rels in
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

(* ═══════════════════════════════════════════════════════════════════════════
   6b. Ensure edge targets exist as nodes — required for CSR completeness.
   Naama/naama-mudra/sankhya edge targets are often just strings ("K", "J",
   "3") that have no nigamana entry. We create lightweight stub nodes for
   them so CSR can index incoming edges and csr_walk_in_by_rel works.
   ═══════════════════════════════════════════════════════════════════════════ *)

let ensure_edge_targets_are_nodes (k : proof_graph) : int =
  let count = ref 0 in
  List.iter (fun (e : typed_edge) ->
    if not (Hashtbl.mem k.nodes e.target) then begin
      let stub : nigamana = {
        name   = e.target;
        layer  = "stub";
        domain = "";
        slokas = [];
        edges  = [];
        satya  = 0.0;
        shabda = "";
        krama  = "";
      } in
      Hashtbl.replace k.nodes e.target stub;
      incr count
    end
  ) !(k.all_edges);
  !count

(* ═══════════════════════════════════════════════════════════════════════════
   7. CSR — materialization
   ═══════════════════════════════════════════════════════════════════════════ *)

let materialize_csr (k : proof_graph) : unit =
  let edges = !(k.all_edges) in
  let n = Hashtbl.length k.nodes in
  let nnz = List.length edges in

  (* pass 1: assign indices — deterministic via sorted names *)
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

  (* pass 2: count incoming edges per target *)
  let in_counts = Array.make n 0 in
  List.iter (fun (e : typed_edge) ->
    match Hashtbl.find_opt node_to_idx e.target with
    | Some ti -> in_counts.(ti) <- in_counts.(ti) + 1
    | None    -> ()
  ) edges;

  (* pass 3: prefix-sum → in_row_ptr *)
  let in_row_ptr = Array.make (n + 1) 0 in
  for i = 0 to n - 1 do
    in_row_ptr.(i + 1) <- in_row_ptr.(i) + in_counts.(i)
  done;
  let actual_nnz = in_row_ptr.(n) in

  (* pass 4: fill CSR arrays *)
  let ndims = dimension_count () in
  let in_col_idx    = Array.make actual_nnz 0 in
  let in_rel_idx    = Array.make actual_nnz 0 in
  let out_rel_count = Array.make (n * ndims) 0 in
  let insert_ptr    = Array.copy in_row_ptr in
  List.iter (fun (e : typed_edge) ->
    let ri = e.relation in
    (match Hashtbl.find_opt node_to_idx e.target with
     | Some ti ->
       let pos = insert_ptr.(ti) in
       in_col_idx.(pos) <- (match Hashtbl.find_opt node_to_idx e.source with
         | Some si -> si | None -> 0);
       in_rel_idx.(pos) <- ri;
       insert_ptr.(ti) <- pos + 1
     | None -> ());
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

(* ═══════════════════════════════════════════════════════════════════════════
   7b. CSR walk-in — O(degree) incoming edge lookup
   ═══════════════════════════════════════════════════════════════════════════ *)

let csr_walk_in_by_rel (k : proof_graph) (target : string) (rel : int)
    : string list =
  match !(k.csr) with
  | None -> []
  | Some csr ->
    match Hashtbl.find_opt csr.csr_node_to_idx target with
    | None -> []
    | Some idx ->
      let row_start = csr.csr_in_row_ptr.(idx) in
      let row_end   = csr.csr_in_row_ptr.(idx + 1) in
      let acc = ref [] in
      for pos = row_start to row_end - 1 do
        if csr.csr_in_rel_idx.(pos) = rel then
          acc := csr.csr_idx_to_node.(csr.csr_in_col_idx.(pos)) :: !acc
      done;
      !acc

let csr_walk_in_all (k : proof_graph) (target : string)
    : (string * int) list =
  match !(k.csr) with
  | None -> []
  | Some csr ->
    match Hashtbl.find_opt csr.csr_node_to_idx target with
    | None -> []
    | Some idx ->
      let row_start = csr.csr_in_row_ptr.(idx) in
      let row_end   = csr.csr_in_row_ptr.(idx + 1) in
      let acc = ref [] in
      for pos = row_start to row_end - 1 do
        acc := (csr.csr_idx_to_node.(csr.csr_in_col_idx.(pos)),
                csr.csr_in_rel_idx.(pos)) :: !acc
      done;
      !acc

(* ═══════════════════════════════════════════════════════════════════════════
   8. PPR — personalized pagerank + depth affinity
   ═══════════════════════════════════════════════════════════════════════════ *)

let compute_depth_affinity (k : proof_graph) (target : string)
    (binding_names : string list) : float =
  let n_bindings = float_of_int (List.length binding_names) in
  let target_edges = with_node k target (fun n -> n.edges) [] in
  let n_target_edges = float_of_int (List.length target_edges) in
  let binding_density = Float.min 1.0 (n_bindings /. (n_target_edges +. 1.0)) in
  let direct_links = List.length (List.filter (fun bname ->
    List.exists (fun e ->
      (e.source = bname && e.target = target) ||
      (e.source = target && e.target = bname)
    ) !(k.all_edges)
  ) binding_names) in
  let link_ratio = Float.min 1.0
    (float_of_int direct_links /. (n_bindings +. 1.0)) in
  let comp_edges = List.length (List.filter (fun e ->
    e.relation = sthita || e.relation = phala || e.relation = kriya
  ) target_edges) in
  let computational_ratio =
    if n_target_edges = 0.0 then 0.0
    else float_of_int comp_edges /. n_target_edges
  in
  let product = binding_density *. link_ratio *. computational_ratio in
  if product <= 0.0 then 0.0
  else Float.min 1.0 (product ** (1.0 /. 3.0))

let run_ppr (k : proof_graph)
    ~(seed_nodes : (string * float) list)
    ~(target : string)
    ~(binding_names : string list)
    : (string, float) Hashtbl.t =
  let csr = match !(k.csr) with
    | Some c -> c
    | None   -> failwith "run_ppr: CSR not materialized — call materialize_csr first"
  in
  let n     = csr.csr_n in
  let ndims = csr.csr_num_dims in
  let alpha = 0.30 in

  (* 1. per-relation conductances from seed neighbourhood *)
  let freq  = Array.make ndims 0 in
  let total_seed_edges = ref 0 in
  List.iter (fun (name, _) ->
    match Hashtbl.find_opt k.nodes name with
    | None -> ()
    | Some nd ->
      List.iter (fun e ->
        let r = e.relation in
        freq.(r) <- freq.(r) + 1;
        incr total_seed_edges
      ) nd.edges
  ) seed_nodes;
  let total_f = float_of_int (max 1 !total_seed_edges) in
  let weights = Array.init ndims (fun r ->
    let base = (vish_props_of r).vp_satya_weight in
    base *. (1.0 +. float_of_int freq.(r) /. total_f)
  ) in

  (* 2. per-node out_cond from out_rel_count × weights *)
  let out_cond = Array.make n 1.0 in
  for u = 0 to n - 1 do
    let oc = ref 0.0 in
    for r = 0 to ndims - 1 do
      oc := !oc +. float_of_int csr.csr_out_rel_count.(u * ndims + r) *. weights.(r)
    done;
    out_cond.(u) <- if !oc <= 0.0 then 1.0 else !oc
  done;

  (* 3. normalize seed *)
  let seed_sum = List.fold_left (fun acc (_, w) -> acc +. w) 0.0 seed_nodes in
  let seed_sum = if seed_sum <= 0.0 then 1.0 else seed_sum in
  let seed_norm : (string, float) Hashtbl.t = Hashtbl.create 16 in
  List.iter (fun (name, w) ->
    let prev = match Hashtbl.find_opt seed_norm name with Some v -> v | None -> 0.0 in
    Hashtbl.replace seed_norm name (prev +. w /. seed_sum)
  ) seed_nodes;

  (* 4. initialize score and seed arrays *)
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

  (* 5. SpMV iteration — zero allocation per iteration *)
  let new_scores = Array.make n 0.0 in
  let max_iters  = 50 in
  let threshold  = 0.001 in
  let converged  = ref false in
  let iter       = ref 0 in
  while not !converged && !iter < max_iters do
    incr iter;
    let max_delta = ref 0.0 in
    for v = 0 to n - 1 do
      let incoming = ref 0.0 in
      let row_start = csr.csr_in_row_ptr.(v) in
      let row_end   = csr.csr_in_row_ptr.(v + 1) in
      let e = ref row_start in
      while !e < row_end do
        let u = csr.csr_in_col_idx.(!e) in
        let r = csr.csr_in_rel_idx.(!e) in
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

  (* 6. build result *)
  let result : (string, float) Hashtbl.t = Hashtbl.create n in
  for i = 0 to n - 1 do
    Hashtbl.replace result csr.csr_idx_to_node.(i) scores.(i)
  done;
  ignore (compute_depth_affinity k target binding_names);
  result

let query_depth_affinity (k : proof_graph) (target : string)
    (binding_names : string list) : float =
  compute_depth_affinity k target binding_names

(* walk_inheritance: BFS over IS-A edges (abheda, swarupa, dhatu, vishesa, amsha).
   depth-limited to 4 hops. returns ancestors in BFS order. *)
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
    with_node k name (fun n ->
      List.filter_map (fun e ->
        if e.source = name && is_inheritance_edge e.relation
        then Some e.target else None
      ) n.edges
    ) []
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

(* ═══════════════════════════════════════════════════════════════════════════
   10. REBUILD_INDICES — single entry point after any graph mutation.
   Ensures edge targets are nodes → satya scores → CSR → entropy weights.
   ═══════════════════════════════════════════════════════════════════════════ *)

let rebuild_indices (k : proof_graph) : unit =
  let stubs = ensure_edge_targets_are_nodes k in
  if stubs > 0 then
    Printf.printf "indices: created %d stub nodes for edge targets\n%!" stubs;
  init_satya k;
  materialize_csr k;
  compute_visheshanam_entropy_weights k
