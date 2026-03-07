(* proof_graph.ml — the proof space
   nodes are nigamana. edges are typed by visheshanam.
   satya is set from local structure at load time (raw_satya / init_satya).
   query-time PPR (run_ppr) produces a posterior score landscape per query.
   the graph holds the truths. the LLM interprets them. *)

(* visheshanam — edge types from Sanskrit grammar *)
type visheshanam =
  | Swarupa       (* identity — X IS Y *)
  | Abheda        (* non-different — X = Y at some level *)
  | Drishthanta   (* evidence — X demonstrated by Y *)
  | Sthita        (* foundation — X stands on Y *)
  | Yukta         (* connection — X joined with Y *)
  | Siddha        (* proof — X established by Y *)
  | Kriya         (* function — X acts as Y *)
  | Phala         (* consequence — X results from Y *)
  | Janya         (* origin — X born from Y *)
  | Pratipaksha   (* inverse — X undoes Y *)

(* typed edge between two nodes *)
type typed_edge = {
  source   : string;
  target   : string;
  relation : visheshanam;
}

(* one truth in the space *)
type nigamana = {
  name   : string;
  layer  : string;            (* "sangati" | "kosha" — which layer this node lives in *)
  slokas : string list;       (* raw sloka text, preserved *)
  edges  : typed_edge list;   (* extracted from slokas *)
  satya  : float;             (* raw_satya set at load time; read-only thereafter *)
  shabda : string;            (* key:value mapping data — target-domain rendering *)
}

type proof_graph = {
  nodes       : (string, nigamana) Hashtbl.t;
  all_edges   : typed_edge list ref;
  kosha_root  : string ref;   (* base path for resolving shabda-tmpl files *)
  search_dirs : string list ref; (* all loaded dirs — searched for shabda-tmpl files *)
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
  vp_dual          : visheshanam option;
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
let _visheshanam_props : (visheshanam, vish_props) Hashtbl.t = Hashtbl.create 16

let register_vish_props (v : visheshanam) (p : vish_props) : unit =
  Hashtbl.replace _visheshanam_props v p

let vish_props_of (v : visheshanam) : vish_props =
  match Hashtbl.find_opt _visheshanam_props v with
  | Some p -> p
  | None   -> default_vish_props

(* visheshanam string conversion *)
let visheshanam_of_string s =
  match String.lowercase_ascii s with
  | "swarupa"     -> Some Swarupa
  | "abheda"      -> Some Abheda
  | "drishthanta" -> Some Drishthanta
  | "sthita"      -> Some Sthita
  | "yukta"       -> Some Yukta
  | "siddha"      -> Some Siddha
  | "kriya"       -> Some Kriya
  | "phala"       -> Some Phala
  | "janya"       -> Some Janya
  | "pratipaksha" -> Some Pratipaksha
  | "inverse"     -> Some Pratipaksha
  | _             -> None

let string_of_visheshanam = function
  | Swarupa     -> "swarupa"
  | Abheda      -> "abheda"
  | Drishthanta -> "drishthanta"
  | Sthita      -> "sthita"
  | Yukta       -> "yukta"
  | Siddha      -> "siddha"
  | Kriya       -> "kriya"
  | Phala       -> "phala"
  | Janya       -> "janya"
  | Pratipaksha -> "pratipaksha"


(* the space was already there *)
let empty () : proof_graph = {
  nodes       = Hashtbl.create 64;
  all_edges   = ref [];
  kosha_root  = ref "";
  search_dirs = ref [];
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
  if edge_count = 0.0 then
    s *. 0.5
  else
    (s *. e *. d) ** (1.0 /. 3.0)

(* init_satya: set raw_satya on every node once at load time.
   called by build_index after apply_relation_axioms. *)
let init_satya (k : proof_graph) : unit =
  Hashtbl.iter (fun _ n ->
    let r = raw_satya n in
    Hashtbl.replace k.nodes n.name { n with satya = r }
  ) k.nodes

(* ---- PPR engine: structure-driven Personalized PageRank ---- *)

(* compute_seed_conductances: derive per-relation conductance from seed neighbourhood.
   seed_edge_freq(relation) = count(relation in edges of seed nodes) / total_seed_edges
   conductance(relation) = vp_satya_weight(relation) × (1 + seed_edge_freq(relation))
   Seed-heavy relations get a contextual boost — no hardcoded question-type table. *)
let compute_seed_conductances (k : proof_graph) (seed_nodes : (string * float) list)
    : visheshanam -> float =
  let freq : (visheshanam, int) Hashtbl.t = Hashtbl.create 16 in
  let total = ref 0 in
  List.iter (fun (name, _weight) ->
    match Hashtbl.find_opt k.nodes name with
    | None -> ()
    | Some n ->
      List.iter (fun e ->
        let prev = match Hashtbl.find_opt freq e.relation with Some c -> c | None -> 0 in
        Hashtbl.replace freq e.relation (prev + 1);
        incr total
      ) n.edges
  ) seed_nodes;
  let total_f = float_of_int (max 1 !total) in
  fun rel ->
    let base_weight = (vish_props_of rel).vp_satya_weight in
    let count = match Hashtbl.find_opt freq rel with Some c -> c | None -> 0 in
    let seed_freq = float_of_int count /. total_f in
    base_weight *. (1.0 +. seed_freq)

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
    e.relation = Sthita || e.relation = Phala || e.relation = Kriya
  ) target_edges) in
  let computational_ratio =
    if n_target_edges = 0.0 then 0.0
    else float_of_int comp_edges /. n_target_edges
  in
  (* geometric mean *)
  let product = binding_density *. link_ratio *. computational_ratio in
  if product <= 0.0 then 0.0
  else Float.min 1.0 (product ** (1.0 /. 3.0))

(* run_ppr: query-time Personalized PageRank.
   Produces a posterior score table focused on the query (target + binding_names).
   Algorithm:
     1. Derive per-relation conductances from seed neighbourhood.
     2. Normalise seed to sum 1.
     3. Build out-conductance index.
     4. Iterate: p_new(v) = α×seed(v) + (1-α)×Σ_{u→v} p(u)×cond(u→v)/out_cond(u)
     5. Stop at max_delta < 0.001 or 50 iterations.
   alpha = 0.30 (restart probability — the only hardcoded constant, mathematical).
   Returns (string, float) Hashtbl.t: posterior PPR score per node. *)
let run_ppr (k : proof_graph)
    ~(seed_nodes : (string * float) list)
    ~(target : string)
    ~(binding_names : string list)
    : (string, float) Hashtbl.t =
  let alpha = 0.30 in
  (* 1. structure-derived conductances *)
  let conductance = compute_seed_conductances k seed_nodes in
  (* 2. normalise seed to sum 1 *)
  let seed_sum = List.fold_left (fun acc (_, w) -> acc +. w) 0.0 seed_nodes in
  let seed_sum = if seed_sum <= 0.0 then 1.0 else seed_sum in
  let seed_norm : (string, float) Hashtbl.t = Hashtbl.create 16 in
  List.iter (fun (name, w) ->
    let prev = match Hashtbl.find_opt seed_norm name with Some v -> v | None -> 0.0 in
    Hashtbl.replace seed_norm name (prev +. w /. seed_sum)
  ) seed_nodes;
  (* 3. build out-conductance index: source → total conductance leaving it *)
  let out_cond : (string, float) Hashtbl.t = Hashtbl.create (Hashtbl.length k.nodes) in
  List.iter (fun e ->
    let c = conductance e.relation in
    let prev = match Hashtbl.find_opt out_cond e.source with Some v -> v | None -> 0.0 in
    Hashtbl.replace out_cond e.source (prev +. c)
  ) !(k.all_edges);
  (* 4. build in-edges index: target → list of (source, relation) *)
  let in_edges : (string, (string * visheshanam) list) Hashtbl.t =
    Hashtbl.create (Hashtbl.length k.nodes) in
  List.iter (fun e ->
    let prev = match Hashtbl.find_opt in_edges e.target with Some l -> l | None -> [] in
    Hashtbl.replace in_edges e.target ((e.source, e.relation) :: prev)
  ) !(k.all_edges);
  (* 5. initialise scores *)
  let scores : (string, float) Hashtbl.t = Hashtbl.create (Hashtbl.length k.nodes) in
  Hashtbl.iter (fun name n ->
    let init = match Hashtbl.find_opt seed_norm name with
      | Some s -> s
      | None   -> n.satya *. 0.01
    in
    Hashtbl.replace scores name init
  ) k.nodes;
  (* also seed any seed nodes not yet in the graph *)
  List.iter (fun (name, _) ->
    if not (Hashtbl.mem scores name) then
      Hashtbl.replace scores name
        (match Hashtbl.find_opt seed_norm name with Some s -> s | None -> 0.0)
  ) seed_nodes;
  (* 6. iterate *)
  let max_iterations = 50 in
  let threshold = 0.001 in
  let converged = ref false in
  let iter = ref 0 in
  while not !converged && !iter < max_iterations do
    incr iter;
    let max_delta = ref 0.0 in
    let new_scores : (string, float) Hashtbl.t = Hashtbl.create (Hashtbl.length scores) in
    Hashtbl.iter (fun name _ ->
      let seed_v = match Hashtbl.find_opt seed_norm name with Some s -> s | None -> 0.0 in
      (* sum incoming flow *)
      let incoming = match Hashtbl.find_opt in_edges name with
        | None -> 0.0
        | Some ins ->
          List.fold_left (fun acc (src, rel) ->
            let p_src = match Hashtbl.find_opt scores src with Some v -> v | None -> 0.0 in
            let c = conductance rel in
            let oc = match Hashtbl.find_opt out_cond src with Some v -> v | None -> 1.0 in
            acc +. p_src *. c /. (if oc <= 0.0 then 1.0 else oc)
          ) 0.0 ins
      in
      let new_v = alpha *. seed_v +. (1.0 -. alpha) *. incoming in
      let old_v = match Hashtbl.find_opt scores name with Some v -> v | None -> 0.0 in
      let delta = Float.abs (new_v -. old_v) in
      if delta > !max_delta then max_delta := delta;
      Hashtbl.replace new_scores name new_v
    ) scores;
    Hashtbl.iter (fun name v -> Hashtbl.replace scores name v) new_scores;
    if !max_delta < threshold then converged := true
  done;
  (* expose depth_affinity for callers via the target node — not stored in graph *)
  ignore (compute_depth_affinity k target binding_names);
  scores

(* depth_affinity exposed separately for beam search in yantra_resolver *)
let query_depth_affinity (k : proof_graph) (target : string)
    (binding_names : string list) : float =
  compute_depth_affinity k target binding_names
