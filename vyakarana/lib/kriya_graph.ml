(* kriya_graph.ml — graph ops + dispatch + engine wiring.
   replaces yantra_eval_primitives.ml (647L) + yantra_pipeline_ops.ml (68L).
   the dispatch chains:
     eval_graph_op → eval_krama_op → eval_shabda_op → eval_pure_op
       → eval_pipeline_op → apply-op / env / tantra fallback.

   env is immutable StringMap — no env_copy.
   4 forward refs replaced by single _engine Atomic record in kriya_types.
   eval_ctx is Atomic in kriya_types.

   sections:
     1. helpers — pair_field, call_tantra_opt
     1c. om-contract cache
     2. eval_graph_op — graph/field/context ops
     3. eval_call — chained dispatch through all modules
     4. register_primitive_arities *)

open Prakriti
open Kriya_types

(* ═══════════════════════════════════════════════════════════════════════════
   1. HELPERS
   ═══════════════════════════════════════════════════════════════════════════ *)

let pair_field (items : value list) (key : string) : value option =
  List.find_map (function
    | VPair (k, v) when k = key -> Some v
    | VList [VString k; v] when k = key -> Some v
    | _ -> None
  ) items

let call_tantra_opt (k : proof_graph) (name : string)
    (inputs : (string * value) list) ~(default : value) : value =
  match Domain.DLS.get _eval_ctx with
  | Some ctx ->
    (match Hashtbl.find_opt ctx.ctx_index.by_name name with
     | Some t -> (Atomic.get _engine).eval_tantra k t inputs
     | None   -> default)
  | None -> default

(* ═══════════════════════════════════════════════════════════════════════════
   1c. OM-CONTRACT CACHE — process-level cache for mantra contracts.
   Proof graph mantra edges are immutable after boot, so contracts
   never change. First call computes + caches, subsequent calls O(1).
   ═══════════════════════════════════════════════════════════════════════════ *)

let _om_contract_cache : (string, value) Hashtbl.t = Hashtbl.create 64

let om_contract_compute (k : proof_graph) (node_name : string) : value =
  let edges = edges_of k node_name in
  let dedup rel_name =
    match visheshanam_of_string rel_name with
    | None -> VList []
    | Some vish ->
      let seen = Hashtbl.create 8 in
      VList (List.filter_map (fun edge ->
        if edge.relation = vish && edge.source = node_name
           && not (Hashtbl.mem seen edge.target) then begin
          Hashtbl.replace seen edge.target true;
          Some (VNode edge.target)
        end else None
      ) edges)
  in
  VList [dedup "janya"; dedup "phala"; dedup "kriya";
         dedup "yukta"; dedup "sthita"; dedup "swarupa";
         dedup "abheda"]

let om_contract_cached (k : proof_graph) (node_name : string) : value =
  match Hashtbl.find_opt _om_contract_cache node_name with
  | Some v -> v
  | None ->
    let v = om_contract_compute k node_name in
    Hashtbl.replace _om_contract_cache node_name v;
    v

(* ── mantra-select index: precomputed reverse lookup ───────────────────
   Built lazily on first call. Maps:
     "" → all mantra nodes
     concept → mantras where concept appears in janya/phala/swarupa/name *)
let _mantra_select_cache : (string, value list) Hashtbl.t option Atomic.t = Atomic.make None

let walk_in_raw (k : proof_graph) (node_name : string) (rel_name : string) : string list =
  match visheshanam_of_string rel_name with
  | None -> []
  | Some vish ->
    (* prefer CSR O(degree) lookup; fall back to linear scan if CSR not ready *)
    match csr_walk_in_by_rel k node_name vish with
    | _ :: _ as results -> results
    | [] ->
      (* CSR may return [] because node not indexed OR truly no edges.
         If CSR is materialized, trust the empty result. Otherwise scan. *)
      if !(k.csr) <> None then []
      else
        List.filter_map (fun edge ->
          if edge.relation = vish && edge.target = node_name then Some edge.source
          else None
        ) !(k.all_edges)

let build_mantra_select_index (k : proof_graph) : (string, value list) Hashtbl.t =
  let all_mantras =
    let phys = walk_in_raw k "physics-mantra" "varga" in
    let math = walk_in_raw k "math-mantra" "varga" in
    List.map (fun n -> VNode n) (phys @ math)
  in
  let idx = Hashtbl.create 64 in
  Hashtbl.replace idx "" all_mantras;
  List.iter (fun m ->
    let name = as_string m in
    let contract = om_contract_cached k name in
    match contract with
    | VList items ->
      let get_strings i =
        match List.nth_opt items i with
        | Some (VList vs) -> List.map as_string vs
        | _ -> []
      in
      let janya = get_strings 0 in
      let phala = get_strings 1 in
      let swarupa = get_strings 5 in
      let sh = Vidya.read_shabda k name in
      let mname = match List.assoc_opt "name" sh with Some v -> v | None -> "" in
      let all_concepts = janya @ phala @ swarupa @
        (if mname <> "" then [mname] else []) in
      List.iter (fun c ->
        let existing = match Hashtbl.find_opt idx c with Some l -> l | None -> [] in
        if not (List.memq m existing) then
          Hashtbl.replace idx c (m :: existing)
      ) all_concepts
    | _ -> ()
  ) all_mantras;
  idx

let mantra_select_cached (k : proof_graph) (solve_for : string) : value list =
  let idx = match Atomic.get _mantra_select_cache with
    | Some i -> i
    | None ->
      let i = build_mantra_select_index k in
      Atomic.set _mantra_select_cache (Some i);
      i
  in
  if solve_for = "" then
    match Hashtbl.find_opt idx "" with Some l -> l | None -> []
  else
    match Hashtbl.find_opt idx solve_for with Some l -> l | None -> []

(* ═══════════════════════════════════════════════════════════════════════════
   2. EVAL_GRAPH_OP — graph, field-accessor, and context operations
   ═══════════════════════════════════════════════════════════════════════════ *)

let eval_graph_op (e_eval : proof_graph -> env -> expr -> value)
    (k : proof_graph) (e : env) (op : string) (args : expr list) : value option =
  let (eval_arg, eval_str, eval_flt, eval_lst, eval_int) =
    make_eval_arg e_eval k e args in
  ignore (eval_arg, eval_flt, eval_lst, eval_int);
  match op with

  | "lookup" ->
    let name = eval_str 0 in
    Some (match find k name with Some _ -> VNode name | None -> VNone)

  | "walk" ->
    let node_name = eval_str 0 in
    let rel_name = eval_str 1 in
    Some (match visheshanam_of_string rel_name with
     | None -> VList []
     | Some vish ->
       let edges = edges_of k node_name in
       VList (List.filter_map (fun edge ->
         if edge.relation = vish && edge.source = node_name then Some (VNode edge.target)
         else None
       ) edges))

  | "walk-in" ->
    let node_name = eval_str 0 in
    let rel_name = eval_str 1 in
    Some (match visheshanam_of_string rel_name with
     | None -> VList []
     | Some vish ->
       (* CSR gives true incoming from all sources; edges_of only has local edges *)
       let sources = csr_walk_in_by_rel k node_name vish in
       if sources <> [] then VList (List.map (fun s -> VNode s) sources)
       else
         (* fallback to local edges if CSR not ready *)
         let edges = edges_of k node_name in
         VList (List.filter_map (fun edge ->
           if edge.relation = vish && edge.target = node_name then Some (VNode edge.source)
           else None
         ) edges))

  | "om-contract" ->
    let node_name = eval_str 0 in
    Some (om_contract_cached k node_name)

  | "mantra-select" ->
    (* Cached mantra candidate selection. O(1) lookup replaces tantra
       that does walk-in + filter with om-contract per mantra. *)
    let solve_for = eval_str 0 in
    Some (VList (mantra_select_cached k solve_for))

  | "has" ->
    let node_name = eval_str 0 in
    let pattern = eval_str 1 in
    let edges = edges_of k node_name in
    let parts = String.split_on_char '-' pattern in
    let found = match List.rev parts with
      | rel_str :: target_parts ->
        let target = String.concat "-" (List.rev target_parts) in
        (match visheshanam_of_string rel_str with
         | Some vish ->
           List.exists (fun edge ->
             edge.relation = vish && edge.source = node_name && edge.target = target
           ) edges
         | None ->
           (match visheshanam_of_string (List.hd parts) with
            | Some vish ->
              let target2 = String.concat "-" (List.tl parts) in
              List.exists (fun edge ->
                edge.relation = vish && edge.source = node_name && edge.target = target2
              ) edges
            | None -> false))
      | [] -> false
    in
    Some (VBool found)

  | "edges" ->
    let node_name = eval_str 0 in
    Some (VList (List.map (fun edge ->
      VList [VString edge.source;
             VString (string_of_visheshanam edge.relation);
             VString edge.target]
    ) (edges_of k node_name)))

  | "neighbors" ->
    let name = eval_str 0 in
    Some (VList (List.map (fun n -> VNode n) (neighbors k name)))

  | "avrti" ->
    let seeds = eval_lst 0 in
    let max_passes = eval_int 1 in
    let seed_names = List.map as_string seeds in
    let (pass_groups, _) = Vak.avrti_anuvada k seed_names max_passes in
    let connections = List.concat_map (fun (_pass_num, triples) ->
      List.map (fun (t : Vak.anuvada_triple) ->
        VList [ VString t.a_source_raw;
                VString (string_of_visheshanam t.a_relation);
                VList (List.map (fun s -> VString s) t.a_targets_raw) ]
      ) triples
    ) pass_groups in
    Some (VList connections)

  | "name" ->
    let v = e_eval k e (List.nth args 0) in
    Some (match v with
     | VNode n -> VString n | VPair (n, _) -> VString n
     | VBinding (n, _) -> VString n | VString s -> VString s
     | _ -> VString (as_string v))

  | "node" ->
    let v = e_eval k e (List.nth args 0) in
    Some (match v with
     | VList [_; _; n] -> n | VNode _ -> v | _ -> VNone)

  | "value" ->
    let v = e_eval k e (List.nth args 0) in
    Some (match v with
     | VFloat f -> VFloat f | VBinding (_, f) -> VFloat f
     | VString s -> (match float_of_string_opt s with Some f -> VFloat f | None -> VNone)
     | _ -> VNone)

  | "role" ->
    let word = as_string (eval_arg 0) in
    let pairs = Vidya.read_shabda k "english-grammar" in
    Some (match List.find_opt (fun (w, _) -> w = word) pairs with
     | Some (_, rel) -> VString rel | None -> VNone)

  | "shabda" ->
    let node_name = eval_str 0 in
    let key = eval_str 1 in
    let pairs = Vidya.read_shabda k node_name in
    Some (match List.find_opt (fun (k, _) -> k = key) pairs with
     | Some (_, v) -> VString v | None -> VNone)

  | "node-layer" ->
    let name = eval_str 0 in
    Some (with_node k name (fun n -> VString n.layer) (VString ""))

  | "node-slokas" ->
    let name = eval_str 0 in
    Some (with_node k name (fun n ->
      VList (List.map (fun s -> VString s) n.slokas)) (VList []))

  | "node-krama" ->
    let name = eval_str 0 in
    Some (with_node k name (fun n -> VString n.krama) (VString ""))

  | "exists" ->
    Some (VBool (as_bool (eval_arg 0)))

  | "ppr" ->
    let seeds_v    = eval_lst 0 in
    let target     = eval_str 1 in
    let bindings_v = eval_lst 2 in
    let seed_nodes = List.filter_map (fun v ->
      match v with
      | VList [VString nm; w] -> Some (nm, as_float w)
      | VBinding (nm, w)       -> Some (nm, w)
      | VPair (nm, w)          -> Some (nm, as_float w)
      | _                      -> None
    ) seeds_v in
    let binding_names = List.filter_map (fun v ->
      match v with
      | VString s -> Some s | VBinding (s,_) -> Some s | _ -> None
    ) bindings_v in
    let scores = run_ppr k ~seed_nodes ~target ~binding_names in
    let pairs = Hashtbl.fold (fun name score acc -> (name, score) :: acc) scores [] in
    let sorted = List.sort (fun (_, a) (_, b) -> Float.compare b a) pairs in
    Some (VList (List.map (fun (nm, s) -> VBinding (nm, s)) sorted))

  | "emit-node" ->
    let name   = eval_str 0 in
    let layer  = eval_str 1 in
    let slokas = List.map as_string (eval_lst 2) in
    let shabda = eval_str 3 in
    let edges = List.concat_map (fun sloka ->
      let words = String.split_on_char ' ' sloka in
      List.filter_map (fun word ->
        let word = String.trim word in
        if String.length word = 0 then None
        else
          let rec try_split i =
            if i <= 0 then None
            else if word.[i] = '-' then
              let suffix = String.sub word (i + 1) (String.length word - i - 1) in
              match visheshanam_of_string suffix with
              | Some rel ->
                let target = String.sub word 0 i in
                Some { source = name; target; relation = rel }
              | None -> try_split (i - 1)
            else try_split (i - 1)
          in
          try_split (String.length word - 1)
      ) words
    ) slokas in
    let n : nigamana = {
      name; layer; domain = ""; slokas; edges;
      satya = 0.0; shabda; krama = "";
    } in
    ignore (join k n);
    let r = raw_satya n in
    Hashtbl.replace k.nodes name { n with satya = r };
    Some (VNode name)

  | "emit-edge" ->
    let source   = eval_str 0 in
    let rel_name = eval_str 1 in
    let target   = eval_str 2 in
    (match visheshanam_of_string rel_name with
     | None -> Some VNone
     | Some rel ->
       let edge : typed_edge = { source; target; relation = rel } in
       let n : nigamana = {
         name = source; layer = "kosha"; domain = "";
         slokas = []; edges = [edge];
         satya = 0.0; shabda = ""; krama = "";
       } in
       ignore (join k n);
       Some (VNode source))

  | "call-tantra" ->
    let tname = eval_str 0 in
    let arg_list = eval_lst 1 in
    Some (match Domain.DLS.get _eval_ctx with
     | Some ctx ->
       (match Hashtbl.find_opt ctx.ctx_index.by_name tname with
        | None -> VNone
        | Some t ->
          let input_values = List.mapi (fun i v ->
            let param_name = if i < List.length t.t_inputs
              then (List.nth t.t_inputs i).tp_name
              else Printf.sprintf "arg%d" i in
            (param_name, v)
          ) arg_list in
          (Atomic.get _engine).eval_tantra k t input_values)
     | None -> VNone)

  (* dynamic om-* dispatch: om-{relation} walks targets by relation name *)
  | op when String.length op > 3 && String.sub op 0 3 = "om-" ->
    let node_name = eval_str 0 in
    let rel_name = String.sub op 3 (String.length op - 3) in
    Some (match visheshanam_of_string rel_name with
     | None -> VList []
     | Some vish ->
       let edges = edges_of k node_name in
       let seen = Hashtbl.create 8 in
       VList (List.filter_map (fun edge ->
         if edge.relation = vish && edge.source = node_name
            && not (Hashtbl.mem seen edge.target) then begin
           Hashtbl.replace seen edge.target true;
           Some (VNode edge.target)
         end else None
       ) edges))

  | _ -> None

(* ═══════════════════════════════════════════════════════════════════════════
   3. EVAL_CALL — chained dispatch through all modules
   ═══════════════════════════════════════════════════════════════════════════ *)

let eval_call (k : proof_graph) (e : env) (op : string) (args : expr list) : value =
  let eng = Atomic.get _engine in
  let e_eval = eng.eval in
  match eval_graph_op e_eval k e op args with
  | Some v -> v
  | None ->
    match Kriya_krama.eval_krama_op e_eval k e op args with
    | Some v -> v
    | None ->
      match Kriya_shabda.eval_shabda_op e_eval k e op args with
      | Some v -> v
      | None ->
        match eng.eval_pure_op e_eval k e op args with
        | Some v -> v
        | None ->
          match Kriya_pipeline.eval_pipeline_op e_eval k e op args with
          | Some v -> v
          | None ->
            (* apply-op: resolve via ganana edge, apply as pure op *)
            let apply_op_vals prim_name op_args =
              let lifted = List.map (fun v -> match v with
                | VFloat f -> Lit f | VString s -> StrLit s
                | VBool b -> BoolLit b | _ -> Lit (as_float v)) op_args in
              match eng.eval_pure_op e_eval k e prim_name lifted with
              | Some v -> v
              | None ->
                (match eval_graph_op e_eval k e prim_name lifted with
                 | Some v -> v | None -> VNone)
            in
            (match op with
            | "apply-op" ->
              let op_name = as_string (e_eval k e (List.nth args 0)) in
              let op_args_v = as_list (e_eval k e (List.nth args 1)) in
              let prim_name = Kriya_krama.resolve_eval_name k op_name in
              apply_op_vals prim_name op_args_v
            | _ ->
              (* env-bound function or tantra fallback *)
              (match StringMap.find_opt op e with
               | Some (VFn (params, body, captured)) ->
                 let local = List.fold_left (fun env_acc (i, param) ->
                   if i < List.length args then
                     StringMap.add param (e_eval k e (List.nth args i)) env_acc
                   else env_acc
                 ) captured (List.mapi (fun i p -> (i, p)) params) in
                 Some (e_eval k local body) |> (function Some v -> v | None -> VNone)
               | _ ->
                 (match Domain.DLS.get _eval_ctx with
                  | Some ctx ->
                    (match Hashtbl.find_opt ctx.ctx_index.by_name op with
                     | Some t ->
                       let arg_vals = List.map (e_eval k e) args in
                       let input_values = List.mapi (fun i v ->
                         let param_name = if i < List.length t.t_inputs
                           then (List.nth t.t_inputs i).tp_name
                           else Printf.sprintf "arg%d" i in
                         (param_name, v)
                       ) arg_vals in
                       eng.eval_tantra k t input_values
                     | None ->
                       Printf.printf "eval: unknown operation '%s'\n%!" op; VNone)
                  | None ->
                      Printf.printf "eval: unknown operation '%s'\n%!" op; VNone)))

(* ═══════════════════════════════════════════════════════════════════════════
   4. REGISTER_PRIMITIVE_ARITIES
   ═══════════════════════════════════════════════════════════════════════════ *)

let register_primitive_arities () =
  let r = Vakya.register_graph_op_arity in
  let b = Vakya.register_boundary_keyword in
  List.iter b [")" ; "]" ; "," ; "in" ; "done" ; "let" ; "otherwise"];
  List.iter b ["where" ; "collect" ; "with"];
  (* engine-internal graph ops: these have no op-* om nodes, so they can't be
     picked up by scan_graph_op_arities. Must be registered explicitly.
     ops with om nodes (lookup, walk, walk-in, has, edges, neighbors, shabda)
     are handled by scan_graph_op_arities from yantra.om5. *)
  r "ppr"                 3;
  r "emit-node"           4;
  r "emit-edge"           3;
  r "propagate-derive"    1;
  r "index-graph"         1;
  r "idx-subjects"        2;
  r "idx-by-edge"         2;
  r "idx-has-edge"        2;
  r "idx-value"           3;
  r "idx-append"          2;
  r "mantra-select"       1;
  r "clock-us"            0;
  r "clock-ms"            0;
  r "profile-step"        2;
  r "session-emit"        3;
  r "session-by-edge"     1;
  r "session-triples"     0;
  r "session-clear"       0;
  r "session-has-edge"    1;
  r "session-subjects"    1;
  r "session-value"       2;
  r "om-contract"         1;
  r "node-layer"          1;
  r "node-slokas"         1;
  r "node-krama"          1;
  r "eval-krama"          2;
  r "eval-krama-dim"      2;
  r "krama-path"          3;
  r "word-node"           1;
  r "word-node-candidates" 1;
  r "decompose-unit"      1;
  r "eval-node"           1;
  r "apply-op"            2;
  r "call-tantra"         2;
  r "split-numeric"       1;
  r "str"                 2;
  r "concept-display"     1;
  r "capitalize-first"    1;
  r "dim-vector"          1;
  (* structural primitives — reduce tantra repetition *)
  r "find-first"          2;
  r "find-map"            2;
  r "flat-map"            2;
  r "split-grades"        1;
  r "append-triples"      2;
  (* migrated tantras — formerly trivial .tantra4 files *)
  r "triple-subj"         1;
  r "triple-edge"         1;
  r "triple-obj"          1;
  r "triples-by-edge"     2;
  r "non-reflexive"       1;
  r "has-text"            1;
  r "has-items"           1;
  r "is-empty"            1;
  r "is-system-concept"   1;
  r "last-of"             1;
  r "join-with"           2;
  r "words-to-str"        1;
  r "format-strand"       2;
  r "word-bigrams"        1;
  r "grade-mithya"        1;
  r "grade-numbers"       1;
  r "is-question-grade"   1;
  r "concept-in-grade"    2;
  r "last-concept"        1;
  r "user-concepts"       1;
  r "read-signal"         2;
  r "write-signals"       2;
  r "word-info"           2;
  r "question-words"      1;
  r "word-resolve"        1;
  r "resolve-or-self"     1;
  r "has-grammar-sthita"  3;
  r "is-viveka-node"      1;
  r "viveka-direction"     1;
  r "word-stem"           1;
  r "stems-match"         2;
  (* om-* relation projections: dynamic — one entry per registered dimension *)
  let ndims = Prakriti.dimension_count () in
  for i = 0 to ndims - 1 do
    r ("om-" ^ Prakriti.string_of_visheshanam i) 1
  done
  (* math/string/boolean ops omitted — registered by scan_graph_op_arities
     from op-* nodes in yantra.om5 via kriya → class → parse-arity *)
