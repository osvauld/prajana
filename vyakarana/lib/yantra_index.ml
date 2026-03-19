(* extracted from yantra.ml: index builder *)
open Proof_graph
open Yantra_types

(* ---- index builder ---- *)

(* recursively find all .tantra files *)
let tantra_files_recursive (root : string) : string list =
  let files = ref [] in
  let rec walk dir =
    try
      let entries = Sys.readdir dir in
      Array.iter (fun entry ->
        let path = Filename.concat dir entry in
        try
          if Sys.is_directory path then walk path
          else if Filename.check_suffix path ".tantra"
               || Filename.check_suffix path ".tantra2"
               || Filename.check_suffix path ".tantra3" then
            files := path :: !files
        with _ -> ()
      ) entries
    with _ -> ()
  in
  walk root;
  List.rev !files

let empty_index () : tantra_index = {
  by_name     = Hashtbl.create 64;
  by_output   = Hashtbl.create 64;
  by_input    = Hashtbl.create 64;
  constants   = Hashtbl.create 16;
  conversions = Hashtbl.create 16;
  all_tantras = ref [];
  word_index  = Hashtbl.create 256;
}

let add_to_list_table tbl key value =
  let existing = try Hashtbl.find tbl key with Not_found -> [] in
  Hashtbl.replace tbl key (value :: existing)

(* resolve canonical names for tantra params using the graph *)
let resolve_tantra_params (k : proof_graph) (t : tantra) : tantra =
  let resolve_param p =
    let canonical = Setu.resolve_to_canonical k p.tp_name in
    { p with tp_canonical = canonical }
  in
  { t with
    t_inputs = List.map resolve_param t.t_inputs;
    t_returns = List.map resolve_param t.t_returns }

let register_tantra_in_graph (k : proof_graph) (t : tantra) : unit =
  let input_edges = List.map (fun inp ->
    { source = t.t_name; target = inp.tp_name; relation = sthita }
  ) t.t_inputs in
  let output_edges = List.map (fun ret ->
    { source = t.t_name; target = ret.tp_name; relation = phala }
  ) t.t_returns in
  let all_edges = input_edges @ output_edges in
  let node : nigamana = {
    name = t.t_name; layer = "yantra"; slokas = [];
    edges = all_edges; satya = 0.0; shabda = "";
  } in
  (* only add if no existing node (don't overwrite sangati/kosha nodes) *)
  match Proof_graph.find k t.t_name with
  | Some existing ->
    (* merge edges: add sthita/phala edges from tantra to existing node *)
    let new_edges = List.filter (fun e ->
      not (List.exists (fun ex ->
        ex.source = e.source && ex.target = e.target && ex.relation = e.relation
      ) existing.edges)
    ) all_edges in
    if new_edges <> [] then begin
      let merged = { existing with edges = existing.edges @ new_edges } in
      ignore (Proof_graph.join k merged)
    end
  | None ->
    ignore (Proof_graph.join k node)

let register_tantra ?(graph : proof_graph option) (idx : tantra_index) (t : tantra) : unit =
  (* resolve canonical names if graph available *)
  let t = match graph with
    | Some k -> let t' = resolve_tantra_params k t in register_tantra_in_graph k t'; t'
    | None -> t
  in
  idx.all_tantras := t :: !(idx.all_tantras);
  Hashtbl.replace idx.by_name t.t_name t;
  (* index by return names — both tp_name and tp_canonical *)
  List.iter (fun ret ->
    add_to_list_table idx.by_output ret.tp_name t;
    if ret.tp_canonical <> ret.tp_name then
      add_to_list_table idx.by_output ret.tp_canonical t
  ) t.t_returns;
  (* index by input names — both tp_name and tp_canonical *)
  List.iter (fun inp ->
    add_to_list_table idx.by_input inp.tp_name t;
    if inp.tp_canonical <> inp.tp_name then
      add_to_list_table idx.by_input inp.tp_canonical t
  ) t.t_inputs;
  (* zero-input tantras with a single literal let = constants *)
  if t.t_inputs = [] then begin
    match t.t_lets with
    | [(_, Lit v)] ->
      Hashtbl.replace idx.constants t.t_name v;
      (* also register by return name *)
      List.iter (fun ret ->
        Hashtbl.replace idx.constants ret.tp_name v
      ) t.t_returns
    | _ -> ()
  end;
  (* conversion tantras: single input, single output, different units *)
  (match t.t_inputs, t.t_returns with
   | [inp], [ret] ->
     (match inp.tp_unit, ret.tp_unit with
      | Some u_in, Some u_out when u_in <> u_out ->
        Hashtbl.replace idx.conversions (u_in, u_out) t
      | _ -> ())
   | _ -> ())

let load_tantra_dir ?(graph : proof_graph option) (idx : tantra_index) (dir : string) : unit =
  let files = tantra_files_recursive dir in
  (* tantra2 first, then tantra3 — tantra3 overwrites same-name tantra2 (supersedes) *)
  let tantra2 = List.filter (fun p -> Filename.check_suffix p ".tantra2") files in
  List.iter (fun path ->
    match Yantra_tantra_file2.parse_tantra2_file path with
    | None -> () | Some t -> register_tantra ?graph idx t
  ) tantra2;
  let tantra3 = List.filter (fun p -> Filename.check_suffix p ".tantra3") files in
  List.iter (fun path ->
    match Yantra_tantra_file2.parse_tantra2_file path with
    | None -> () | Some t -> register_tantra ?graph idx t
  ) tantra3

(* collect all tantra directories from the given dirs list *)
let collect_tantra_dirs (dirs : string list) : string list =
  let searched = Hashtbl.create 16 in
  let result = ref [] in
  List.iter (fun dir ->
    let found_yantra = ref false in
    let yantra_inside = Filename.concat dir "yantra" in
    if Sys.file_exists yantra_inside && Sys.is_directory yantra_inside
       && not (Hashtbl.mem searched yantra_inside) then begin
      Hashtbl.replace searched yantra_inside true;
      result := yantra_inside :: !result;
      found_yantra := true
    end;
    let parent = Filename.dirname dir in
    let yantra_sibling = Filename.concat parent "yantra" in
    if Sys.file_exists yantra_sibling && Sys.is_directory yantra_sibling
       && not (Hashtbl.mem searched yantra_sibling) then begin
      Hashtbl.replace searched yantra_sibling true;
      result := yantra_sibling :: !result;
      found_yantra := true
    end;
    if not !found_yantra && not (Hashtbl.mem searched dir) then begin
      Hashtbl.replace searched dir true;
      result := dir :: !result
    end
  ) dirs;
  List.rev !result

(* pre-scan all .tantra files for arities before full parse.
   this lets tantras call other tantras naturally — the parser
   knows every tantra's arity before parsing any let blocks. *)
let pre_scan_arities (tantra_dirs : string list) : unit =
  List.iter (fun dir ->
    let files = tantra_files_recursive dir in
    List.iter (fun path ->
      (* both .tantra and .tantra2 use same header format for name/arity *)
      match Yantra_arity.pre_scan_tantra_file path with
      | Some (name, arity) ->
        Yantra_arity.register_tantra_arity name arity
      | None -> ()
    ) files
  ) tantra_dirs

(* scan op nodes from the graph (kosha/yantra/ layer) and register their arities.
   lookup flow for each op-<name> node:
     1. if the node's own shabda has parse-arity — use it directly (per-op override)
     2. otherwise walk the kriya edge to the class node, read parse-arity from class shabda
   class parse-arity values: -1 = variadic, 1 = projection, 2 = binary/keyed/relation/higher-order/pipeline *)
let scan_graph_op_arities (k : proof_graph) : unit =
  let get_parse_arity (shabda_str : string) : int option =
    let pairs = Setu_shabda.parse_shabda shabda_str in
    match List.assoc_opt "parse-arity" pairs with
    | Some s -> int_of_string_opt s
    | None   -> None
  in
  (* walk every node whose name starts with "op-" *)
  Hashtbl.iter (fun node_name n ->
    let op_prefix = "op-" in
    let prefix_len = String.length op_prefix in
    if String.length node_name > prefix_len
       && String.sub node_name 0 prefix_len = op_prefix
       (* exclude the class nodes themselves: op-class-* *)
       && not (String.length node_name > prefix_len + 6
               && String.sub node_name prefix_len 6 = "class-")
    then begin
      let op_name = String.sub node_name prefix_len (String.length node_name - prefix_len) in
      (* try per-op override first *)
      let arity_opt = match get_parse_arity n.shabda with
        | Some a -> Some a
        | None ->
          (* walk kriya edges to find the class node *)
          let class_node_opt = List.fold_left (fun acc e ->
            match acc with
            | Some _ -> acc
            | None ->
              if e.source = node_name && e.relation = Proof_graph.kriya then
                Proof_graph.find k e.target
              else None
          ) None n.edges
          in
          (match class_node_opt with
           | Some class_node -> get_parse_arity class_node.shabda
           | None -> None)
      in
      match arity_opt with
      | Some arity -> Yantra_arity.register_graph_op_arity op_name arity
      | None -> ()
    end
  ) k.nodes

(* scan visheshanam-* nodes from the graph and populate the vish_props table.
   called first in build_index, before op arities and tantra scan.
   reads the shabda key:value pairs of each visheshanam-<name> node. *)
let scan_visheshanam_properties (k : proof_graph) : unit =
  let parse_bool pairs key =
    match List.assoc_opt key pairs with
    | Some "yes" -> true
    | _          -> false
  in
  let parse_ring_op pairs =
    match List.assoc_opt "ring-op" pairs with
    | Some "add" -> `Add
    | Some "mul" -> `Mul
    | _          -> `None
  in
  let parse_dual pairs =
    match List.assoc_opt "dual" pairs with
    | Some s -> Proof_graph.visheshanam_of_string s
    | None   -> None
  in
  (* build the list dynamically from the dimension registry — covers core 10 + any dynamic dims *)
  let ndims = Proof_graph.dimension_count () in
  let vish_names = List.init ndims (fun idx ->
    let name = Proof_graph.string_of_visheshanam idx in
    ("visheshanam-" ^ name, idx)
  ) in
  List.iter (fun (node_name, vish) ->
    match Proof_graph.find k node_name with
    | None -> ()
    | Some n ->
      let pairs = Setu_shabda.parse_shabda n.Proof_graph.shabda in
      let props : Proof_graph.vish_props = {
        vp_symmetric     = parse_bool  pairs "symmetric";
        vp_antisymmetric = parse_bool  pairs "antisymmetric";
        vp_transitive    = parse_bool  pairs "transitive";
        vp_reflexive     = parse_bool  pairs "reflexive";
        vp_involutive    = parse_bool  pairs "involutive";
        vp_congruence    = parse_bool  pairs "congruence";
        vp_composable    = parse_bool  pairs "composable";
        vp_dual          = parse_dual  pairs;
        vp_ring_op       = parse_ring_op pairs;
        vp_satya_weight  = Proof_graph.default_vish_props.vp_satya_weight;
        (* entropy-derived weight computed later by compute_visheshanam_entropy_weights *)
      } in
      Proof_graph.register_vish_props vish props
  ) vish_names

(* add a single directed edge to a node in the graph (merge pattern — idempotent).
   only appends to all_edges if genuinely new. *)
let add_edge_to_graph (k : proof_graph) (e : Proof_graph.typed_edge) : bool =
  (* check if edge already present in all_edges *)
  let already = List.exists (fun ex ->
    ex.Proof_graph.source   = e.Proof_graph.source &&
    ex.Proof_graph.target   = e.Proof_graph.target &&
    ex.Proof_graph.relation = e.Proof_graph.relation
  ) !(k.Proof_graph.all_edges) in
  if already then false
  else begin
    (* add to source node's edge list (or create stub node) *)
    (match Proof_graph.find k e.Proof_graph.source with
     | Some src_node ->
       let merged = { src_node with
         Proof_graph.edges = src_node.Proof_graph.edges @ [e]
       } in
       ignore (Proof_graph.join k merged)
     | None ->
       (* source node not yet in graph — create a stub *)
       let stub : Proof_graph.nigamana = {
         name = e.Proof_graph.source; layer = "kosha";
         slokas = []; edges = [e]; satya = 0.0; shabda = "";
       } in
       ignore (Proof_graph.join k stub));
    k.Proof_graph.all_edges := e :: !(k.Proof_graph.all_edges);
    true
  end

(* apply structural axioms derived from vish_props:
   - symmetric relations: add reverse edge if missing
   - dual relations:      add (target, dual, source) if missing
   returns (total_added, per-relation summary list) *)
let apply_relation_axioms (k : proof_graph) : int * (string * int * int) list =
  (* snapshot the edge list before we start adding — iterate over the
     original set only, not edges we add during this pass *)
  let original_edges = !(k.Proof_graph.all_edges) in
  (* per-relation counters: (added, already_present) *)
  let tbl : (string, int ref * int ref) Hashtbl.t = Hashtbl.create 16 in
  let get_counters name =
    match Hashtbl.find_opt tbl name with
    | Some c -> c
    | None ->
      let c = (ref 0, ref 0) in
      Hashtbl.replace tbl name c; c
  in
  List.iter (fun (e : Proof_graph.typed_edge) ->
    let props = Proof_graph.vish_props_of e.Proof_graph.relation in
    let rel_name = Proof_graph.string_of_visheshanam e.Proof_graph.relation in
    (* symmetric: add reverse *)
    if props.Proof_graph.vp_symmetric then begin
      let rev : Proof_graph.typed_edge = {
        source = e.Proof_graph.target;
        target = e.Proof_graph.source;
        relation = e.Proof_graph.relation;
      } in
      let (added, present) = get_counters rel_name in
      if add_edge_to_graph k rev then incr added
      else incr present
    end;
    (* dual: add (target, dual_rel, source) *)
    (match props.Proof_graph.vp_dual with
     | None -> ()
     | Some dual_rel ->
       let dual_name = Printf.sprintf "%s->%s"
         rel_name (Proof_graph.string_of_visheshanam dual_rel) in
       let dual_edge : Proof_graph.typed_edge = {
         source = e.Proof_graph.target;
         target = e.Proof_graph.source;
         relation = dual_rel;
       } in
       let (added, present) = get_counters dual_name in
       if add_edge_to_graph k dual_edge then incr added
       else incr present)
  ) original_edges;
  (* collect results *)
  let summary = Hashtbl.fold (fun name (added, present) acc ->
    (name, !added, !present) :: acc
  ) tbl [] in
  let summary = List.sort (fun (a,_,_) (b,_,_) -> String.compare a b) summary in
  let total = List.fold_left (fun acc (_, a, _) -> acc + a) 0 summary in
  (total, summary)

(* build_word_index: scan all graph nodes for word: key in their shabda.
   populates idx.word_index with word → node-name mappings.
   comma-separated word: values (e.g. "word:and,both") register all words.
   called after build_index and register_mantra_nodes. *)
let build_word_index (k : proof_graph) (idx : tantra_index) : unit =
  Hashtbl.iter (fun node_name n ->
    let pairs = Setu_shabda.parse_shabda n.Proof_graph.shabda in
    (* index word: keys only — abbreviations and explicit aliases (kg, N, m, rad).
       concept nodes (mass, acceleration, kinetic-energy) are found via lookup
       (Proof_graph.find) in lookup-word.tantra — no need to duplicate them here. *)
    match List.assoc_opt "word" pairs with
    | None -> ()
    | Some words_str ->
      let words = String.split_on_char ',' words_str in
      List.iter (fun w ->
        let w = String.trim w in
        if String.length w > 0 then
          Hashtbl.replace idx.word_index w node_name
      ) words
  ) k.Proof_graph.nodes

let build_index ?(graph : proof_graph option) (dirs : string list) : tantra_index =
  let idx = empty_index () in
  let tantra_dirs = collect_tantra_dirs dirs in
  (match graph with
   | None -> ()
   | Some k ->
     (* pass 0: load visheshanam property table from graph *)
     scan_visheshanam_properties k;
     (* pass 1a: derive op arities from graph class nodes (kosha/yantra/) *)
     scan_graph_op_arities k;
     (* pass 1b: structural completion — add symmetric/dual edges *)
     let (total_added, summary) = apply_relation_axioms k in
     Printf.printf "relation-axioms: added %d edges\n" total_added;
     List.iter (fun (name, added, present) ->
       Printf.printf "  %-20s %d added / %d already present\n" (name ^ ":") added present
     ) summary;
      (* pass 1c: set raw_satya as structural prior on every node.
         no iteration — PPR handles neighbour influence per query at runtime. *)
       Proof_graph.init_satya k;
       (* pass 1d: build word_index from all nodes' word: shabda keys.
          enables O(1) word-node lookups for abbreviations and aliases. *)
       build_word_index k idx);
  (* pass 2: pre-scan all tantra arities so the parser knows them *)
  pre_scan_arities tantra_dirs;
  (* pass 3: full parse and registration *)
  List.iter (fun dir ->
    load_tantra_dir ?graph idx dir
  ) tantra_dirs;
  idx
