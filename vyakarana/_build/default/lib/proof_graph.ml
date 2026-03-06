(* proof_graph.ml — the proof space
   nodes are nigamana. edges are typed by visheshanam.
   satya is computed from structure by avrti (spiral convergence).
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
  satya  : float;             (* computed by avrti *)
  shabda : string;            (* key:value mapping data — target-domain rendering *)
}

type proof_graph = {
  nodes       : (string, nigamana) Hashtbl.t;
  all_edges   : typed_edge list ref;
  kosha_root  : string ref;   (* base path for resolving shabda-tmpl files *)
  search_dirs : string list ref; (* all loaded dirs — searched for shabda-tmpl files *)
}

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

(* join a nigamana into the space *)
let join (k : proof_graph) (n : nigamana) : proof_graph =
  Hashtbl.replace k.nodes n.name n;
  k.all_edges := n.edges @ !(k.all_edges);
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

(* --- satya-ganana: avrti (spiral convergence) --- *)

(* pass 1: raw satya from local structure
   - sloka count contributes (more angles = denser)
   - edge count contributes (more connections = richer)
   - edge type diversity contributes (richer relationships = deeper)
   all normalized to (0, 1) *)
let raw_satya (n : nigamana) : float =
  let sloka_count = float_of_int (List.length n.slokas) in
  let edge_count = float_of_int (List.length n.edges) in
  (* count distinct visheshanam types used *)
  let visheshanam_types = List.sort_uniq compare
    (List.map (fun e -> e.relation) n.edges) in
  let type_diversity = float_of_int (List.length visheshanam_types) in
  (* sigmoid-like: approaches 1.0 but never reaches *)
  (* each factor contributes: 1 - 1/(1+x) = x/(1+x) *)
  let s = sloka_count /. (1.0 +. sloka_count) in
  let e = edge_count /. (1.0 +. edge_count) in
  let d = type_diversity /. (1.0 +. type_diversity) in
  (* combine: geometric mean keeps values in (0, 1) *)
  (* root nodes with no edges get satya from slokas alone *)
  if edge_count = 0.0 then
    s *. 0.5  (* root node: sloka contribution only, halved *)
  else
    (s *. e *. d) ** (1.0 /. 3.0)

(* pass 2+: adjust by neighbor satya — one avrti turn
   returns the new satya for one node.
   only INCOMING edges (nodes that cite this node) contribute neighbor influence.
   pointing to brahman does not give you brahman's satya —
   brahman pointing to you does. *)
let avrti_step (k : proof_graph) (name : string) (current : float) : float =
  (* incoming neighbors: nodes that have an edge pointing TO this node *)
  let in_nbrs = List.filter_map (fun e ->
    if e.target = name then Some e.source else None
  ) !(k.all_edges) in
  let in_nbrs = List.sort_uniq String.compare in_nbrs in
  let in_deg = float_of_int (List.length in_nbrs) in
  let citation_boost = in_deg /. (1.0 +. in_deg) in
  if in_nbrs = [] then
    (* no one cites this node — raw structure only, dampened *)
    0.7 *. current +. 0.3 *. citation_boost
  else begin
    let nbr_satya_sum = List.fold_left (fun acc nb ->
      match Hashtbl.find_opt k.nodes nb with
      | Some n -> acc +. n.satya
      | None   -> acc
    ) 0.0 in_nbrs in
    let nbr_count = float_of_int (List.length in_nbrs) in
    let nbr_avg = nbr_satya_sum /. nbr_count in
    (* blend: 60% own structure, 40% incoming neighbor influence *)
    let blended = 0.6 *. current +. 0.4 *. nbr_avg in
    (* combine: blend with citation influence *)
    0.7 *. blended +. 0.3 *. citation_boost
  end

(* run satya-ganana: iterate until convergence *)
let satya_ganana (k : proof_graph) : int =
  (* build in-edges index: target → list of unique sources *)
  let in_edges : (string, string list) Hashtbl.t = Hashtbl.create (Hashtbl.length k.nodes) in
  List.iter (fun e ->
    let prev = match Hashtbl.find_opt in_edges e.target with Some l -> l | None -> [] in
    if not (List.mem e.source prev) then
      Hashtbl.replace in_edges e.target (e.source :: prev)
  ) !(k.all_edges);
  (* pass 1: set raw satya for all nodes *)
  Hashtbl.iter (fun _ n ->
    let raw = raw_satya n in
    Hashtbl.replace k.nodes n.name { n with satya = raw }
  ) k.nodes;
  (* avrti_step using pre-built index *)
  let avrti_step_indexed name current =
    let in_nbrs = match Hashtbl.find_opt in_edges name with Some l -> l | None -> [] in
    let in_deg = float_of_int (List.length in_nbrs) in
    let citation_boost = in_deg /. (1.0 +. in_deg) in
    if in_nbrs = [] then
      0.7 *. current +. 0.3 *. citation_boost
    else begin
      let nbr_satya_sum = List.fold_left (fun acc nb ->
        match Hashtbl.find_opt k.nodes nb with
        | Some n -> acc +. n.satya
        | None   -> acc
      ) 0.0 in_nbrs in
      let nbr_count = float_of_int (List.length in_nbrs) in
      let nbr_avg = nbr_satya_sum /. nbr_count in
      let blended = 0.6 *. current +. 0.4 *. nbr_avg in
      0.7 *. blended +. 0.3 *. citation_boost
    end
  in
  (* pass 2+: avrti — iterate until convergence *)
  let max_iterations = 100 in
  let threshold = 0.001 in
  let iterations = ref 0 in
  let converged = ref false in
  while not !converged && !iterations < max_iterations do
    incr iterations;
    let max_delta = ref 0.0 in
    let updates = Hashtbl.fold (fun name n acc ->
      let new_satya = avrti_step_indexed name n.satya in
      let clamped = Float.min 0.999 (Float.max 0.001 new_satya) in
      let delta = Float.abs (clamped -. n.satya) in
      if delta > !max_delta then max_delta := delta;
      (name, clamped) :: acc
    ) k.nodes [] in
    List.iter (fun (name, new_satya) ->
      match Hashtbl.find_opt k.nodes name with
      | Some n -> Hashtbl.replace k.nodes name { n with satya = new_satya }
      | None -> ()
    ) updates;
    if !max_delta < threshold then converged := true
  done;
  !iterations
