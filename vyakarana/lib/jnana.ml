(* jnana.ml — tantra index builder + graph enrichment.
   replaces yantra_index.ml (452L). Uses Prakriti.dir_walk (no local copy).

   sections:
     1. index builder — empty_index, register_tantra, load_tantra_dir
     2. directory discovery — collect_tantra_dirs
     3. arity scanning — pre_scan_arities, scan_graph_op_arities
     4. visheshanam properties — scan_visheshanam_properties
     5. graph enrichment — add_edge_to_graph, apply_relation_axioms
     6. word index — build_word_index
     7. build_index — full build orchestrator *)

open Prakriti
open Kriya_types

(* ═══════════════════════════════════════════════════════════════════════════
   1. INDEX BUILDER
   ═══════════════════════════════════════════════════════════════════════════ *)

let tantra_files_recursive (root : string) : string list =
  dir_walk root ".tantra4"

let empty_index () : tantra_index = {
  by_name     = Hashtbl.create 64;
  by_output   = Hashtbl.create 64;
  by_input    = Hashtbl.create 64;
  constants   = Hashtbl.create 16;
  conversions = Hashtbl.create 16;
  all_tantras = ref [];
  word_index  = Hashtbl.create 256;
  eval_index  = Hashtbl.create 256;
}

let add_to_list_table tbl key value =
  let existing = try Hashtbl.find tbl key with Not_found -> [] in
  Hashtbl.replace tbl key (value :: existing)

let resolve_tantra_params (k : proof_graph) (t : tantra) : tantra =
  let resolve_param p =
    { p with tp_canonical = Vidya.resolve_to_canonical k p.tp_name }
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
    edges = all_edges; satya = 0.0; shabda = ""; krama = "";
  } in
  match find k t.t_name with
  | Some existing ->
    let new_edges = List.filter (fun e ->
      not (List.exists (fun ex ->
        ex.source = e.source && ex.target = e.target && ex.relation = e.relation
      ) existing.edges)
    ) all_edges in
    if new_edges <> [] then begin
      let merged = { existing with edges = existing.edges @ new_edges } in
      ignore (join k merged)
    end
  | None ->
    ignore (join k node)

let register_tantra ?(graph : proof_graph option) (idx : tantra_index) (t : tantra) : unit =
  let t = match graph with
    | Some k -> let t' = resolve_tantra_params k t in register_tantra_in_graph k t'; t'
    | None -> t
  in
  idx.all_tantras := t :: !(idx.all_tantras);
  Hashtbl.replace idx.by_name t.t_name t;
  List.iter (fun ret ->
    add_to_list_table idx.by_output ret.tp_name t;
    if ret.tp_canonical <> ret.tp_name then
      add_to_list_table idx.by_output ret.tp_canonical t
  ) t.t_returns;
  List.iter (fun inp ->
    add_to_list_table idx.by_input inp.tp_name t;
    if inp.tp_canonical <> inp.tp_name then
      add_to_list_table idx.by_input inp.tp_canonical t
  ) t.t_inputs;
  if t.t_inputs = [] then begin
    match t.t_lets with
    | [(_, Lit v)] ->
      Hashtbl.replace idx.constants t.t_name v;
      List.iter (fun ret ->
        Hashtbl.replace idx.constants ret.tp_name v
      ) t.t_returns
    | _ -> ()
  end;
  (match t.t_inputs, t.t_returns with
   | [inp], [ret] ->
     (match inp.tp_unit, ret.tp_unit with
      | Some u_in, Some u_out when u_in <> u_out ->
        Hashtbl.replace idx.conversions (u_in, u_out) t
      | _ -> ())
   | _ -> ())

let load_tantra_dir ?(graph : proof_graph option) (idx : tantra_index) (dir : string) : unit =
  let files = tantra_files_recursive dir in
  List.iter (fun path ->
    match Vakya.parse_tantra4_file path with
    | None -> () | Some t -> register_tantra ?graph idx t
  ) files

(* ═══════════════════════════════════════════════════════════════════════════
   2. DIRECTORY DISCOVERY
   ═══════════════════════════════════════════════════════════════════════════ *)

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

(* ═══════════════════════════════════════════════════════════════════════════
   3. ARITY SCANNING
   ═══════════════════════════════════════════════════════════════════════════ *)

let pre_scan_arities (tantra_dirs : string list) : unit =
  List.iter (fun dir ->
    let files = tantra_files_recursive dir in
    List.iter (fun path ->
      match Vakya.pre_scan_tantra4_file path with
      | Some (name, arity) -> Vakya.register_tantra_arity name arity
      | None -> ()
    ) files
  ) tantra_dirs

let scan_graph_op_arities (k : proof_graph) : unit =
  let get_parse_arity_from (pairs : (string * string) list) : int option =
    match List.assoc_opt "parse-arity" pairs with
    | Some s -> int_of_string_opt s | None -> None
  in
  Hashtbl.iter (fun node_name n ->
    let op_prefix = "op-" in
    let prefix_len = String.length op_prefix in
    if String.length node_name > prefix_len
       && String.sub node_name 0 prefix_len = op_prefix
       && not (String.length node_name > prefix_len + 6
               && String.sub node_name prefix_len 6 = "class-")
    then begin
      let op_name = String.sub node_name prefix_len (String.length node_name - prefix_len) in
      let own_pairs = Vidya.raw_shabda_for_node k node_name in
      let arity_opt = match get_parse_arity_from own_pairs with
        | Some a -> Some a
        | None ->
          let class_node_opt = List.fold_left (fun acc e ->
            match acc with
            | Some _ -> acc
            | None ->
              if e.source = node_name && e.relation = kriya then
                find k e.target
              else None
          ) None n.edges
          in
          (match class_node_opt with
           | Some class_node ->
             get_parse_arity_from (Vidya.raw_shabda_for_node k class_node.name)
           | None -> None)
      in
      match arity_opt with
      | Some arity -> Vakya.register_graph_op_arity op_name arity
      | None -> ()
    end
  ) k.nodes

(* ═══════════════════════════════════════════════════════════════════════════
   4. VISHESHANAM PROPERTIES
   ═══════════════════════════════════════════════════════════════════════════ *)

let scan_visheshanam_properties (k : proof_graph) : unit =
  let parse_bool pairs key =
    match List.assoc_opt key pairs with
    | Some "yes" -> true | _ -> false
  in
  let parse_ring_op pairs =
    match List.assoc_opt "ring-op" pairs with
    | Some "add" -> `Add | Some "mul" -> `Mul | _ -> `None
  in
  let parse_dual pairs =
    match List.assoc_opt "dual" pairs with
    | Some s -> visheshanam_of_string s | None -> None
  in
  let ndims = dimension_count () in
  let vish_names = List.init ndims (fun idx ->
    let name = string_of_visheshanam idx in
    ("visheshanam-" ^ name, idx)
  ) in
  List.iter (fun (node_name, vish) ->
    match find k node_name with
    | None -> ()
    | Some _n ->
      let pairs = Vidya.raw_shabda_for_node k node_name in
      let props : vish_props = {
        vp_symmetric     = parse_bool  pairs "symmetric";
        vp_antisymmetric = parse_bool  pairs "antisymmetric";
        vp_transitive    = parse_bool  pairs "transitive";
        vp_reflexive     = parse_bool  pairs "reflexive";
        vp_involutive    = parse_bool  pairs "involutive";
        vp_congruence    = parse_bool  pairs "congruence";
        vp_composable    = parse_bool  pairs "composable";
        vp_dual          = parse_dual  pairs;
        vp_ring_op       = parse_ring_op pairs;
        vp_satya_weight  = default_vish_props.vp_satya_weight;
      } in
      register_vish_props vish props
  ) vish_names

(* ═══════════════════════════════════════════════════════════════════════════
   5. GRAPH ENRICHMENT
   ═══════════════════════════════════════════════════════════════════════════ *)

let add_edge_to_graph (k : proof_graph) (e : typed_edge) : bool =
  let already = List.exists (fun ex ->
    ex.source = e.source && ex.target = e.target && ex.relation = e.relation
  ) !(k.all_edges) in
  if already then false
  else begin
    (match find k e.source with
     | Some src_node ->
       let merged = { src_node with edges = src_node.edges @ [e] } in
       ignore (join k merged)
     | None ->
       let stub : nigamana = {
         name = e.source; layer = "kosha";
         slokas = []; edges = [e]; satya = 0.0; shabda = ""; krama = "";
       } in
       ignore (join k stub));
    k.all_edges := e :: !(k.all_edges);
    true
  end

let apply_relation_axioms (k : proof_graph) : int * (string * int * int) list =
  let original_edges = !(k.all_edges) in
  let tbl : (string, int ref * int ref) Hashtbl.t = Hashtbl.create 16 in
  let get_counters name =
    match Hashtbl.find_opt tbl name with
    | Some c -> c
    | None -> let c = (ref 0, ref 0) in Hashtbl.replace tbl name c; c
  in
  List.iter (fun (e : typed_edge) ->
    let props = vish_props_of e.relation in
    let rel_name = string_of_visheshanam e.relation in
    if props.vp_symmetric then begin
      let rev : typed_edge = { source = e.target; target = e.source; relation = e.relation } in
      let (added, present) = get_counters rel_name in
      if add_edge_to_graph k rev then incr added else incr present
    end;
    (match props.vp_dual with
     | None -> ()
     | Some dual_rel ->
       let dual_name = Printf.sprintf "%s->%s"
         rel_name (string_of_visheshanam dual_rel) in
       let dual_edge : typed_edge = {
         source = e.target; target = e.source; relation = dual_rel;
       } in
       let (added, present) = get_counters dual_name in
       if add_edge_to_graph k dual_edge then incr added else incr present)
  ) original_edges;
  let summary = Hashtbl.fold (fun name (added, present) acc ->
    (name, !added, !present) :: acc
  ) tbl [] in
  let summary = List.sort (fun (a,_,_) (b,_,_) -> String.compare a b) summary in
  let total = List.fold_left (fun acc (_, a, _) -> acc + a) 0 summary in
  (total, summary)

(* ═══════════════════════════════════════════════════════════════════════════
   6. WORD + EVAL INDEX
   ═══════════════════════════════════════════════════════════════════════════ *)

let build_word_index (k : proof_graph) (idx : tantra_index) : unit =
  let naama_dim = match visheshanam_of_string "naama" with
    | Some d -> d | None -> register_dimension "naama" in
  Hashtbl.iter (fun node_name n ->
    (* word index: walk naama edges (graph-native, emitted by emit_shabda_edges) *)
    List.iter (fun e ->
      if e.source = node_name && e.relation = naama_dim then
        Hashtbl.replace idx.word_index e.target node_name
    ) n.edges;
    (* eval index: still from shabda store — eval is internal, not a word *)
    let pairs = Vidya.raw_shabda_for_node k node_name in
    (match List.assoc_opt "eval" pairs with
    | None -> ()
    | Some eval_name ->
      let ev = String.trim eval_name in
      if String.length ev > 0 then
        Hashtbl.replace idx.eval_index ev node_name)
  ) k.nodes

(* ═══════════════════════════════════════════════════════════════════════════
   7. BUILD_INDEX — full build orchestrator
   ═══════════════════════════════════════════════════════════════════════════ *)

let build_index ?(graph : proof_graph option) (dirs : string list) : tantra_index =
  let idx = empty_index () in
  let tantra_dirs = collect_tantra_dirs dirs in
  (match graph with
   | None -> ()
   | Some k ->
     scan_visheshanam_properties k;
     scan_graph_op_arities k;
     let (total_added, summary) = apply_relation_axioms k in
     Printf.printf "relation-axioms: added %d edges\n" total_added;
     List.iter (fun (name, added, present) ->
       Printf.printf "  %-20s %d added / %d already present\n" (name ^ ":") added present
     ) summary;
     init_satya k;
     build_word_index k idx);
  pre_scan_arities tantra_dirs;
  List.iter (fun dir -> load_tantra_dir ?graph idx dir) tantra_dirs;
  (* krama mantras are evaluated directly via eval-krama primitive.
     no synthetic tantras or kriya edges needed. *)
  idx
