(* jnana.ml — tantra index builder + graph enrichment.
   replaces yantra_index.ml (452L). Uses Prakriti.dir_walk (no local copy).

   sections:
     1. index builder — empty_index, register_tantra, load_tantra_dir
     2. directory discovery — collect_tantra_dirs
     3. arity scanning — pre_scan_arities, scan_graph_op_arities
     4. visheshanam properties — scan_visheshanam_properties
     5. graph enrichment — add_edge_to_graph, apply_relation_axioms
     6. eval + compound index — build_word_index
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
    name = t.t_name; layer = "yantra"; domain = "";
    slokas = [];
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
  (* walk siddha edges on the visheshanam node to get algebraic properties *)
  let siddha_targets (n : nigamana) : string list =
    List.filter_map (fun e ->
      if e.source = n.name && e.relation = siddha then Some e.target
      else None
    ) n.edges
  in
  (* walk pratipaksha edges to derive dual *)
  let pratipaksha_targets (n : nigamana) : string list =
    List.filter_map (fun e ->
      if e.source = n.name && e.relation = pratipaksha then Some e.target
      else None
    ) n.edges
  in
  (* walk abheda edges to derive ring-op *)
  let abheda_targets (n : nigamana) : string list =
    List.filter_map (fun e ->
      if e.source = n.name && e.relation = abheda then Some e.target
      else None
    ) n.edges
  in
  let ndims = dimension_count () in
  let vish_names = List.init ndims (fun idx ->
    let name = string_of_visheshanam idx in
    ("visheshanam-" ^ name, idx)
  ) in
  List.iter (fun (node_name, vish) ->
    match find k node_name with
    | None -> ()
    | Some n ->
      let axioms = siddha_targets n in
      let has prop = List.mem prop axioms in
      (* dual: strip "visheshanam-" prefix from pratipaksha target *)
      let dual = match pratipaksha_targets n with
        | t :: _ ->
          let prefix = "visheshanam-" in
          let plen = String.length prefix in
          if String.length t > plen && String.sub t 0 plen = prefix then
            visheshanam_of_string (String.sub t plen (String.length t - plen))
          else None
        | [] -> None
      in
      (* ring-op: derived from abheda targets *)
      let ring_op =
        let abh = abheda_targets n in
        if List.mem "addition" abh then `Add
        else if List.mem "multiplication" abh then `Mul
        else `None
      in
      let props : vish_props = {
        vp_symmetric     = has "symmetric";
        vp_antisymmetric = has "antisymmetric";
        vp_transitive    = has "transitive";
        vp_reflexive     = has "reflexive";
        vp_involutive    = has "involutive";
        vp_congruence    = has "congruence";
        vp_composable    = has "composable";
        vp_reversible    = has "reversible";
        vp_inheritable   = has "inheritable";
        vp_dual          = dual;
        vp_ring_op       = ring_op;
        vp_satya_weight  = default_vish_props.vp_satya_weight;
      } in
      register_vish_props vish props
  ) vish_names

(* ═══════════════════════════════════════════════════════════════════════════
   5. GRAPH ENRICHMENT
   ═══════════════════════════════════════════════════════════════════════════ *)

(* fast edge commit — caller guarantees uniqueness (used by generators with dedup) *)
let commit_edge (k : proof_graph) (edge : typed_edge) (counter : int ref) : unit =
  match Hashtbl.find_opt k.nodes edge.source with
  | Some n ->
    Hashtbl.replace k.nodes edge.source { n with edges = edge :: n.edges };
    k.all_edges := edge :: !(k.all_edges);
    incr counter
  | None -> ()

(* slow edge insert with dedup check — for axiom application where dupes possible *)
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
         name = e.source; layer = "kosha"; domain = "";
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
   5.5 AVASTHA GENERATOR — expand (avastha q1 q2 ...) edges into child nodes
   ═══════════════════════════════════════════════════════════════════════════ *)

let expand_avastha (k : proof_graph) : int =
  let avastha_dim = ensure_dim "avastha" in
  let swarupa_dim = ensure_dim "swarupa" in
  let sthita_dim = ensure_dim "sthita" in
  let vishesa_dim = ensure_dim "vishesa" in
  let generated = ref 0 in
  (* collect base→qualifiers from avastha edges *)
  let work = ref [] in
  Hashtbl.iter (fun base_name base_node ->
    let qualifiers = List.filter_map (fun e ->
      if e.source = base_name && e.relation = avastha_dim then Some e.target
      else None
    ) base_node.edges in
    if qualifiers <> [] then
      work := (base_name, base_node, qualifiers) :: !work
  ) k.nodes;
  (* generate child nodes *)
  List.iter (fun (base_name, base_node, qualifiers) ->
    (* collect vishesa targets from base for inheritance *)
    let base_vishesa = List.filter_map (fun e ->
      if e.source = base_name && e.relation = vishesa_dim then Some e.target
      else None
    ) base_node.edges in
    List.iter (fun qualifier ->
      let child_name = qualifier ^ "-" ^ base_name in
      (* skip if node already exists (hand-written om5 takes priority) *)
      match find k child_name with
      | Some _ -> ()
      | None ->
        (* qualifier IS the context — no translation needed *)
        let context = qualifier in
        (* build edges: swarupa→base, sthita→context, inherit vishesa *)
        let edges = ref [
          { source = child_name; target = base_name; relation = swarupa_dim };
          { source = child_name; target = context; relation = sthita_dim };
        ] in
        List.iter (fun v ->
          edges := { source = child_name; target = v; relation = vishesa_dim } :: !edges
        ) base_vishesa;
        (* apply shabda overrides: keys like "override-sthita: orbit" *)
        let override_pairs = Vidya.raw_shabda_for_node k child_name in
        List.iter (fun (key, value) ->
          if String.length key > 9 && String.sub key 0 9 = "override-" then begin
            let rel_name = String.sub key 9 (String.length key - 9) in
            match visheshanam_of_string rel_name with
            | None -> ()
            | Some rel_dim ->
              let targets = String.split_on_char ',' value in
              List.iter (fun t ->
                let t = String.trim t in
                if String.length t > 0 then
                  edges := { source = child_name; target = t; relation = rel_dim } :: !edges
              ) targets
          end
        ) override_pairs;
        let edges_list = List.rev !edges in
        let child : nigamana = {
          name = child_name; layer = base_node.layer; domain = "";
          slokas = []; edges = edges_list; satya = 0.0; shabda = ""; krama = "";
        } in
        ignore (join k child);
        List.iter (fun e -> k.all_edges := e :: !(k.all_edges)) edges_list;
        (* inject shabda word: entry so word index picks up the compound name *)
        let word_forms = [child_name; String.concat " " (String.split_on_char '-' child_name)] in
        let word_str = String.concat "," word_forms in
        Vidya.inject_shabda child_name [("word", word_str)];
        incr generated
    ) qualifiers
  ) !work;
  !generated

(* ═══════════════════════════════════════════════════════════════════════════
   5a2. GENERIC REVERSE EDGE COMBINATOR
   For any relation dim: if A→B via dim, add B→A if absent.
   Optional filter: (source_node, target_node) → bool.
   Used by reciprocals, swarupa_reverse, sthita_reverse, awareness, yukta.
   ═══════════════════════════════════════════════════════════════════════════ *)

let generate_reverse_for_dim (k : proof_graph) (dim : visheshanam)
    ?(filter : nigamana -> nigamana -> bool = fun _ _ -> true) () : int =
  let generated = ref 0 in
  let work = ref [] in
  Hashtbl.iter (fun source_name node ->
    List.iter (fun e ->
      if e.source = source_name && e.relation = dim then begin
        match Hashtbl.find_opt k.nodes e.target with
        | None -> ()
        | Some target_node ->
          if filter node target_node then begin
            let has = List.exists (fun re ->
              re.source = e.target && re.target = source_name && re.relation = dim
            ) target_node.edges in
            if not has then
              work := (e.target, source_name, dim) :: !work
          end
      end
    ) node.edges
  ) k.nodes;
  List.iter (fun (src, tgt, rel) ->
    commit_edge k { source = src; target = tgt; relation = rel } generated
  ) !work;
  !generated

(* ═══════════════════════════════════════════════════════════════════════════
   5b. RECIPROCAL EDGE GENERATORS
   Graph-driven: symmetric from vp_symmetric, duals from vp_dual.
   ═══════════════════════════════════════════════════════════════════════════ *)

let generate_reciprocals (k : proof_graph) : int =
  let generated = ref 0 in
  let ndims = dimension_count () in
  (* symmetric relations (from vish_props): if A→B exists, add B→A *)
  for dim = 0 to ndims - 1 do
    let props = vish_props_of dim in
    if props.vp_symmetric then
      generated := !generated + generate_reverse_for_dim k dim ()
  done;
  (* dual pairs (from vish_props): if A-dim→B, add B-dual→A and vice versa *)
  for dim = 0 to ndims - 1 do
    let props = vish_props_of dim in
    match props.vp_dual with
    | None -> ()
    | Some dual_dim ->
      let work = ref [] in
      Hashtbl.iter (fun source_name node ->
        List.iter (fun e ->
          if e.source = source_name && e.relation = dim then begin
            match Hashtbl.find_opt k.nodes e.target with
            | None -> ()
            | Some tn ->
              let has = List.exists (fun re ->
                re.source = e.target && re.target = source_name && re.relation = dual_dim
              ) tn.edges in
              if not has then
                work := (e.target, source_name, dual_dim) :: !work
          end
        ) node.edges
      ) k.nodes;
      List.iter (fun (src, tgt, rel) ->
        commit_edge k { source = src; target = tgt; relation = rel } generated
      ) !work
  done;
  !generated

(* ═══════════════════════════════════════════════════════════════════════════
   5c. VARGA MEMBERSHIP GENERATOR
   If a node has (vishesa varga-name), auto-add reverse: varga gets
   swarupa-child edge pointing to the member. This makes vargas browsable
   from the varga node downward, not just from members upward.
   ═══════════════════════════════════════════════════════════════════════════ *)

let generate_varga_membership (k : proof_graph) : int =
  let generated = ref 0 in
  let vishesa_dim = ensure_dim "vishesa" in
  let swarupa_dim = ensure_dim "swarupa" in
  let work = ref [] in
  Hashtbl.iter (fun member_name node ->
    (* skip mantra nodes — they have their own swarupa pointing to concept *)
    if node.layer = "mantra" then ()
    else
    List.iter (fun e ->
      if e.source = member_name && e.relation = vishesa_dim then begin
        (* member has vishesa→varga, check if varga has swarupa→member *)
        let varga_name = e.target in
        match Hashtbl.find_opt k.nodes varga_name with
        | None -> ()
        | Some varga_node ->
          let has = List.exists (fun re ->
            re.source = varga_name && re.target = member_name && re.relation = swarupa_dim
          ) varga_node.edges in
          if not has then
            work := (varga_name, member_name, swarupa_dim) :: !work
      end
    ) node.edges
  ) k.nodes;
  List.iter (fun (src, tgt, rel) ->
    commit_edge k { source = src; target = tgt; relation = rel } generated
  ) !work;
  !generated

let generate_swarupa_reverse (k : proof_graph) : int =
  generate_reverse_for_dim k (ensure_dim "swarupa") ()

let generate_sthita_reverse (k : proof_graph) : int =
  generate_reverse_for_dim k (ensure_dim "sthita") ()

(* ═══════════════════════════════════════════════════════════════════════════
   5f. MATRA INHERITANCE
   If child has swarupa→parent and parent has matra edges but child doesn't,
   child inherits parent's units.
   ═══════════════════════════════════════════════════════════════════════════ *)

let generate_matra_inheritance (k : proof_graph) : int =
  let generated = ref 0 in
  let swarupa_dim = ensure_dim "swarupa" in
  let matra_dim = ensure_dim "matra" in
  let work = ref [] in
  Hashtbl.iter (fun child_name node ->
    (* skip if child already has matra edges *)
    let has_matra = List.exists (fun e ->
      e.source = child_name && e.relation = matra_dim
    ) node.edges in
    if not has_matra then begin
      (* find swarupa parent with matra *)
      List.iter (fun e ->
        if e.source = child_name && e.relation = swarupa_dim then begin
          match Hashtbl.find_opt k.nodes e.target with
          | None -> ()
          | Some parent ->
            List.iter (fun pe ->
              if pe.source = e.target && pe.relation = matra_dim then
                work := (child_name, pe.target, matra_dim) :: !work
            ) parent.edges
        end
      ) node.edges
    end
  ) k.nodes;
  (* deduplicate *)
  let unique = Hashtbl.create 16 in
  List.iter (fun (s, t, r) ->
    let key = s ^ "|" ^ t in
    if not (Hashtbl.mem unique key) then begin
      Hashtbl.replace unique key true;
      commit_edge k { source = s; target = t; relation = r } generated
    end
  ) !work;
  !generated

(* ═══════════════════════════════════════════════════════════════════════════
   5g. REVERSE AWARENESS GENERATORS
   For siddha, kriya, drishthanta: if A→B via rel, B gets reverse awareness.
   ═══════════════════════════════════════════════════════════════════════════ *)

let generate_awareness_reverse (k : proof_graph) : int =
  let acc = ref 0 in
  let ndims = dimension_count () in
  for dim = 0 to ndims - 1 do
    if (vish_props_of dim).vp_reversible then
      acc := !acc + generate_reverse_for_dim k dim ()
  done;
  !acc

(* ═══════════════════════════════════════════════════════════════════════════
   5h. YUKTA SAME-LAYER RECIPROCAL
   If A and B are in the same layer and A yukta B, add B yukta A.
   Cross-layer yukta is directional (kosha depends on sangati, not reverse).
   ═══════════════════════════════════════════════════════════════════════════ *)

let generate_yukta_same_layer (k : proof_graph) : int =
  match visheshanam_of_string "yukta" with
  | None -> 0
  | Some yukta_dim ->
    generate_reverse_for_dim k yukta_dim
      ~filter:(fun src_node tgt_node -> src_node.layer = tgt_node.layer) ()

(* ═══════════════════════════════════════════════════════════════════════════
   5i. EDGE INHERITANCE
   If child has swarupa→parent, child inherits parent's yukta, sthita,
   siddha, abheda edges (unless child already has that relation).
   Only inherits if child has NO edges of that relation type.
   ═══════════════════════════════════════════════════════════════════════════ *)

let generate_edge_inheritance (k : proof_graph) : int =
  let generated = ref 0 in
  let swarupa_dim = ensure_dim "swarupa" in
  let inherit_rels =
    let ndims = dimension_count () in
    List.init ndims Fun.id
    |> List.filter (fun d -> (vish_props_of d).vp_inheritable) in
  let work = ref [] in
  Hashtbl.iter (fun child_name node ->
    (* skip mantra nodes *)
    if node.layer = "mantra" then ()
    else begin
      (* find swarupa parents — same layer only to avoid cross-layer pollution *)
      let parents = List.filter_map (fun e ->
        if e.source = child_name && e.relation = swarupa_dim then
          match Hashtbl.find_opt k.nodes e.target with
          | Some p when p.layer = node.layer -> Some p
          | _ -> None
        else None
      ) node.edges in
      List.iter (fun rel_dim ->
        (* only inherit if child has NO edges of this relation *)
        let child_has = List.exists (fun e ->
          e.source = child_name && e.relation = rel_dim
        ) node.edges in
        if not child_has then
          List.iter (fun parent ->
            List.iter (fun pe ->
              if pe.source = parent.name && pe.relation = rel_dim
                 && pe.target <> child_name && pe.target <> parent.name then
                work := (child_name, pe.target, rel_dim) :: !work
            ) parent.edges
          ) parents
      ) inherit_rels
    end
  ) k.nodes;
  (* deduplicate *)
  let seen = Hashtbl.create 64 in
  List.iter (fun (src, tgt, rel) ->
    let key = src ^ "|" ^ tgt ^ "|" ^ (string_of_int rel) in
    if not (Hashtbl.mem seen key) then begin
      Hashtbl.replace seen key true;
      commit_edge k { source = src; target = tgt; relation = rel } generated
    end
  ) !work;
  !generated

(* ═══════════════════════════════════════════════════════════════════════════
   5j. VARGA PATTERN REPLICATION
   If >60% of a varga's members share an edge (rel, target), members
   missing it get it too. Consensus-based enrichment.
   ═══════════════════════════════════════════════════════════════════════════ *)

let generate_varga_patterns (k : proof_graph) : int =
  let generated = ref 0 in
  let vishesa_dim = ensure_dim "vishesa" in
  (* collect varga→members *)
  let varga_members : (string, string list) Hashtbl.t = Hashtbl.create 32 in
  Hashtbl.iter (fun member_name node ->
    List.iter (fun e ->
      if e.source = member_name && e.relation = vishesa_dim then begin
        let existing = try Hashtbl.find varga_members e.target with Not_found -> [] in
        Hashtbl.replace varga_members e.target (member_name :: existing)
      end
    ) node.edges
  ) k.nodes;
  (* for each varga with 5+ members, find consensus edges *)
  Hashtbl.iter (fun _varga_name members ->
    let n_members = List.length members in
    if n_members >= 5 then begin
      (* count (rel, target) occurrences across members *)
      let edge_counts : (int * string, int) Hashtbl.t = Hashtbl.create 32 in
      List.iter (fun member ->
        match Hashtbl.find_opt k.nodes member with
        | None -> ()
        | Some node ->
          if node.layer <> "mantra" then
          List.iter (fun e ->
            if e.source = member && e.relation <> vishesa_dim then begin
              let key = (e.relation, e.target) in
              let c = try Hashtbl.find edge_counts key with Not_found -> 0 in
              Hashtbl.replace edge_counts key (c + 1)
            end
          ) node.edges
      ) members;
      (* apply consensus edges (>60%) to members missing them *)
      let threshold = n_members * 6 / 10 in
      Hashtbl.iter (fun (rel, target) count ->
        if count >= threshold then
          List.iter (fun member ->
            match Hashtbl.find_opt k.nodes member with
            | None -> ()
            | Some node ->
              if node.layer = "mantra" then ()
              else
              let has = List.exists (fun e ->
                e.source = member && e.relation = rel && e.target = target
              ) node.edges in
              if not has then
                commit_edge k { source = member; target; relation = rel } generated
          ) members
      ) edge_counts
    end
  ) varga_members;
  !generated

(* ═══════════════════════════════════════════════════════════════════════════
   6. WORD + EVAL INDEX
   ═══════════════════════════════════════════════════════════════════════════ *)

let build_word_index (k : proof_graph) (idx : tantra_index) : unit =
  Hashtbl.iter (fun _key n ->
    let node_name = n.name in
    (* eval index: from ganana graph edges (first target = primitive name) *)
    let ganana_dim = ensure_dim "ganana" in
    List.iter (fun e ->
      if e.source = node_name && e.relation = ganana_dim then
        Hashtbl.replace idx.eval_index e.target node_name
    ) n.edges;
    (* fallback: shabda eval key for nodes not yet migrated *)
    if not (List.exists (fun e -> e.source = node_name && e.relation = ganana_dim) n.edges) then begin
      let pairs = Vidya.raw_shabda_for_node k node_name in
      (match List.assoc_opt "eval" pairs with
      | None -> ()
      | Some eval_name ->
        let ev = String.trim eval_name in
        if String.length ev > 0 then
          Hashtbl.replace idx.eval_index ev node_name)
    end
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
