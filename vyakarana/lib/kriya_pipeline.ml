(* kriya_pipeline.ml — pipeline-specific operations extracted from kriya_graph.ml.
   Handles: session overlay, indexed graph access, profiling, propagate-derive,
   remember-bindings, eval-node. *)

open Prakriti
open Kriya_types

(* ── helper: call tantra by name (duplicated from kriya_graph to avoid circular dep) ── *)

let call_tantra_opt (k : proof_graph) (name : string)
    (inputs : (string * value) list) ~(default : value) : value =
  match Domain.DLS.get _eval_ctx with
  | Some ctx ->
    (match Hashtbl.find_opt ctx.ctx_index.by_name name with
     | Some t -> (Atomic.get _engine).eval_tantra k t inputs
     | None   -> default)
  | None -> default

(* ═══════════════════════════════════════════════════════════════════════════
   EVAL_PIPELINE_OP — session overlay, indexed graph, profiling, pipeline ops
   ═══════════════════════════════════════════════════════════════════════════ *)

let eval_pipeline_op (e_eval : proof_graph -> env -> expr -> value)
    (k : proof_graph) (e : env) (op : string) (args : expr list) : value option =
  let (eval_arg, eval_str, _eval_flt, eval_lst, _eval_int) =
    make_eval_arg e_eval k e args in
  ignore (eval_arg, _eval_flt, _eval_int);
  match op with

  (* ── eval-node ────────────────────────────────────────────────────────── *)

  | "eval-node" ->
    let ev = eval_str 0 in
    Some (match Domain.DLS.get _eval_ctx with
     | Some ctx ->
       (match Hashtbl.find_opt ctx.ctx_index.eval_index ev with
        | Some node_name -> VString node_name | None ->
          (match find k ev with Some _ -> VString ev | None -> VNone))
     | None -> VNone)

  (* ── propagate-derive ─────────────────────────────────────────────────── *)

  | "propagate-derive" ->
    (* Reactive derivation: propagate bindings through janya edges.
       Takes a triple-graph. For each sankhya binding, walks janya edges
       backwards to find mantras that might fire. Fires them, propagates
       new derivations recursively. No fixpoint needed.
       Returns enriched graph with all derivable values. *)
    let graph_v = eval_lst 0 in
    (* extract bound concepts from sankhya triples *)
    let bound_concepts = Hashtbl.create 16 in
    let vps = ref [] in
    List.iter (fun triple ->
      match triple with
      | VList [VString s; VString "sankhya"; VString v] ->
        Hashtbl.replace bound_concepts s true;
        vps := VList [VString s; VString v] :: !vps
      | VList [VString s; VString "sankhya"; VFloat f] ->
        Hashtbl.replace bound_concepts s true;
        let vs = Printf.sprintf "%g" f in
        vps := VList [VString s; VString vs] :: !vps
      | _ -> ()
    ) graph_v;
    (* collect all mantras whose phala edges could fire *)
    let janya_dim = ensure_dim "janya" in
    let phala_dim = ensure_dim "phala" in
    let swarupa_dim = ensure_dim "swarupa" in
    (* recursive propagation *)
    let new_triples = ref [] in
    let fired_mantras = Hashtbl.create 8 in
    let rec propagate concept =
      (* find mantras that have this concept as janya *)
      let edges = !(k.all_edges) in
      let varga_dim = match visheshanam_of_string "varga" with
        | Some d -> d | None -> -1 in
      let affected = List.filter_map (fun e ->
        if e.relation = janya_dim && e.target = concept then Some e.source
        else None
      ) edges in
      List.iter (fun mantra_name ->
        if Hashtbl.mem fired_mantras mantra_name then ()
        (* skip unit-mantra varga — definition mantras are for dimensional analysis only *)
        else if varga_dim >= 0 && List.exists (fun e ->
          e.source = mantra_name && e.relation = varga_dim && e.target = "unit-mantra"
        ) (edges_of k mantra_name) then ()
        else begin
          (* get this mantra's janya and phala *)
          let m_edges = edges_of k mantra_name in
          let m_janya = List.filter_map (fun e ->
            if e.relation = janya_dim && e.source = mantra_name then Some e.target else None
          ) m_edges in
          let m_phala = List.filter_map (fun e ->
            if e.relation = phala_dim && e.source = mantra_name then Some e.target else None
          ) m_edges in
          let m_swarupa = List.filter_map (fun e ->
            if e.relation = swarupa_dim && e.source = mantra_name then Some e.target else None
          ) m_edges in
          let phala_name = match m_phala with
            | p :: _ -> p
            | [] -> match m_swarupa with s :: _ -> s | [] ->
              let sh = Vidya.read_shabda k mantra_name in
              (match List.assoc_opt "name" sh with Some n -> String.trim n | None -> "")
          in
          (* skip if phala already bound *)
          if Hashtbl.mem bound_concepts phala_name then ()
          else begin
            (* check all janya are bound (or are constants) *)
            let all_ok = List.for_all (fun jn ->
              Hashtbl.mem bound_concepts jn ||
              (let sh = Vidya.read_shabda k jn in
               match List.assoc_opt "constants-key" sh with
               | Some ck -> String.length (String.trim ck) > 0
               | None -> false)
            ) m_janya in
            if all_ok then begin
              Hashtbl.replace fired_mantras mantra_name true;
              (* fire via execute-mantra tantra *)
              let vps_val = VList !vps in
              let result = call_tantra_opt k "execute-mantra"
                [("mantra", VString mantra_name);
                 ("bindings", vps_val);
                 ("mode", VString "forward");
                 ("solve-for", VString "")]
                ~default:VNone in
              let result_str = as_string result in
              if String.length result_str > 0 && result_str <> "" then begin
                (* add derived binding *)
                Hashtbl.replace bound_concepts phala_name true;
                vps := VList [VString phala_name; VString result_str] :: !vps;
                new_triples :=
                  VList [VString phala_name; VString "sankhya"; VString result_str] ::
                  VList [VString phala_name; VString "derived-by"; VString mantra_name] ::
                  !new_triples;
                (* recursively propagate the new derivation *)
                propagate phala_name
              end
            end
          end
        end
      ) affected
    in
    (* trigger propagation from each initially bound concept *)
    let initial_concepts = Hashtbl.fold (fun c _ acc -> c :: acc) bound_concepts [] in
    List.iter propagate initial_concepts;
    (* build fired-matches list: [[mantra, vps, "forward"], ...] for dispatch *)
    let fired_list = Hashtbl.fold (fun mname _ acc ->
      VList [VString mname; VList !vps; VString "forward"] :: acc
    ) fired_mantras [] in
    (* return [enriched-graph, fired-matches, vps] *)
    Some (VList [
      VList (graph_v @ !new_triples);
      VList fired_list;
      VList !vps;
    ])

  (* ── session overlay primitives ────────────────────────────────────────── *)

  | "session-emit" ->
    (* Emit a triple into the session overlay. O(1) insert into both indices.
       Auto-registers unknown edge types as new dimensions. *)
    let source   = eval_str 0 in
    let rel_name = eval_str 1 in
    let target   = eval_str 2 in
    let vish = ensure_dim rel_name in
    (let vish = vish in
       let overlay = Domain.DLS.get _session_overlay in
       let edge : typed_edge = { source; target; relation = vish } in
       (* index by source *)
       let existing = match Hashtbl.find_opt overlay.by_source source with
         | Some es -> es | None -> [] in
       Hashtbl.replace overlay.by_source source (edge :: existing);
       (* index by edge type *)
       let by_e = match Hashtbl.find_opt overlay.by_edge vish with
         | Some ps -> ps | None -> [] in
       Hashtbl.replace overlay.by_edge vish ((source, target) :: by_e);
       (* also index by target for walk-in *)
       let existing_tgt = match Hashtbl.find_opt overlay.by_source target with
         | Some es -> es | None -> [] in
       Hashtbl.replace overlay.by_source target (edge :: existing_tgt);
       (* record for reconstruction *)
       overlay.triples := (source, vish, target) :: !(overlay.triples);
       Some (VNode source))

  | "session-by-edge" ->
    (* O(1) lookup: all (source, target) pairs with given edge type in session.
       Replaces: graph | where [s,e,o] | and (eq e "X") | collect [s, o] *)
    let rel_name = eval_str 0 in
    Some (match visheshanam_of_string rel_name with
     | None -> VList []
     | Some vish ->
       let overlay = Domain.DLS.get _session_overlay in
       match Hashtbl.find_opt overlay.by_edge vish with
       | None -> VList []
       | Some pairs -> VList (List.map (fun (s, t) ->
           VList [VString s; VString t]) pairs))

  | "session-triples" ->
    (* Return all session triples as [[s, e, o], ...] for compatibility. *)
    let overlay = Domain.DLS.get _session_overlay in
    Some (VList (List.map (fun (s, rel, t) ->
      VList [VString s; VString (string_of_visheshanam rel); VString t]
    ) !(overlay.triples)))

  | "session-clear" ->
    (* Clear session overlay — call at start of each query. *)
    let overlay = Domain.DLS.get _session_overlay in
    Hashtbl.clear overlay.by_source;
    Hashtbl.clear overlay.by_edge;
    overlay.triples := [];
    Some VNone

  | "session-has-edge" ->
    (* Does ANY triple with this edge type exist in session? O(1) check. *)
    let rel_name = eval_str 0 in
    Some (match visheshanam_of_string rel_name with
     | None -> VBool false
     | Some vish ->
       let overlay = Domain.DLS.get _session_overlay in
       VBool (Hashtbl.mem overlay.by_edge vish))

  | "session-subjects" ->
    (* All subjects (sources) with given edge type. O(1) + map.
       Replaces: graph | where [s,e,o] | and (eq e "X") | collect (to-string s) *)
    let rel_name = eval_str 0 in
    Some (match visheshanam_of_string rel_name with
     | None -> VList []
     | Some vish ->
       let overlay = Domain.DLS.get _session_overlay in
       match Hashtbl.find_opt overlay.by_edge vish with
       | None -> VList []
       | Some pairs -> VList (List.map (fun (s, _) -> VString s) pairs))

  | "session-value" ->
    (* Get the object of a specific (subject, edge) pair. O(1).
       Replaces: reduce graph "" (fn a t -> cond (and (eq s X) (eq e Y)) o a) *)
    let subject  = eval_str 0 in
    let rel_name = eval_str 1 in
    Some (match visheshanam_of_string rel_name with
     | None -> VNone
     | Some vish ->
       let overlay = Domain.DLS.get _session_overlay in
       match Hashtbl.find_opt overlay.by_edge vish with
       | None -> VNone
       | Some pairs ->
         match List.find_opt (fun (s, _) -> s = subject) pairs with
         | Some (_, t) -> VString t | None -> VNone)

  (* ── indexed graph primitives (pure value, no mutation) ──────────────── *)

  | "index-graph" ->
    (* Build indexed graph from flat triple list. O(n) build, O(1) lookups. *)
    let triples = eval_lst 0 in
    Some (VGraph (index_triples triples))

  | "idx-subjects" ->
    (* All subjects with given edge type. O(1). *)
    let g = eval_arg 0 in
    let edge_type = eval_str 1 in
    Some (match g with
     | VGraph gi ->
       (match Hashtbl.find_opt gi.gi_by_edge edge_type with
        | None -> VList []
        | Some pairs -> VList (List.map (fun (s, _) -> VString s) pairs))
     | _ -> VList [])

  | "idx-by-edge" ->
    (* All (subject, object) pairs with given edge type. O(1). *)
    let g = eval_arg 0 in
    let edge_type = eval_str 1 in
    Some (match g with
     | VGraph gi ->
       (match Hashtbl.find_opt gi.gi_by_edge edge_type with
        | None -> VList []
        | Some pairs -> VList (List.map (fun (s, o) ->
            VList [VString s; VString o]) pairs))
     | _ -> VList [])

  | "idx-has-edge" ->
    (* Does any triple with this edge type exist? O(1). *)
    let g = eval_arg 0 in
    let edge_type = eval_str 1 in
    Some (match g with
     | VGraph gi -> VBool (Hashtbl.mem gi.gi_by_edge edge_type)
     | _ -> VBool false)

  | "idx-value" ->
    (* Get object for specific (subject, edge) pair. O(1). *)
    let g = eval_arg 0 in
    let subject = eval_str 1 in
    let edge_type = eval_str 2 in
    Some (match g with
     | VGraph gi ->
       (match Hashtbl.find_opt gi.gi_by_edge edge_type with
        | None -> VNone
        | Some pairs ->
          match List.find_opt (fun (s, _) -> s = subject) pairs with
          | Some (_, o) -> VString o | None -> VNone)
     | _ -> VNone)

  | "idx-append" ->
    (* Append triples to indexed graph, updating index. O(k) for k new triples. *)
    let g = eval_arg 0 in
    let new_triples = eval_lst 1 in
    Some (match g with
     | VGraph gi ->
       let by_edge = Hashtbl.copy gi.gi_by_edge in
       List.iter (fun triple ->
         match triple with
         | VList (VString s :: VString e :: rest) ->
           let o = match rest with VString o :: _ -> o | _ -> as_string (VList rest) in
           let existing = match Hashtbl.find_opt by_edge e with Some l -> l | None -> [] in
           Hashtbl.replace by_edge e ((s, o) :: existing)
         | _ -> ()
       ) new_triples;
       VGraph { gi_triples = gi.gi_triples @ new_triples; gi_by_edge = by_edge }
     | VList existing ->
       VGraph (index_triples (existing @ new_triples))
     | _ -> VGraph (index_triples new_triples))

  (* ── profiling primitives ──────────────────────────────────────────── *)

  | "clock-us" ->
    (* Returns per-thread CPU time in microseconds (no contention). *)
    Some (VFloat (thread_cpu_us ()))

  | "clock-ms" ->
    (* Backwards compat — returns milliseconds (wall clock). *)
    Some (VFloat (Unix.gettimeofday () *. 1000.0))

  | "profile-step" ->
    (* Evaluate an expression and return [result, elapsed-us, label].
       Uses per-thread CPU time — accurate under concurrency.
       Usage: (profile-step "label" <expr>) *)
    let label = eval_str 0 in
    let t0 = thread_cpu_us () in
    let result = e_eval k e (List.nth args 1) in
    let elapsed = thread_cpu_us () -. t0 in
    Some (VList [result; VFloat elapsed; VString label])

  (* ── remember-bindings ─────────────────────────────────────────────── *)

  | "remember-bindings" ->
    let items = as_list (e_eval k e (List.nth args 0)) in
    (match Domain.DLS.get _eval_ctx with
     | None ->
       Some (VList [VString "error"; VString "missing eval context"; VFloat 0.0; VString ""; VString ""])
     | Some ctx ->
       let now = Unix.gettimeofday () in
       let bindings = List.filter_map (function
         | VBinding (n, f) -> Some { b_name = n; b_value = f; b_unit = None;
                                     b_timestamp = now; b_source = "user";
                                     b_confidence = 1.0; b_ttl = None }
         | _ -> None
       ) items in
       List.iter (fun b ->
         ctx.ctx_session.bindings <-
           b :: List.filter (fun sb -> sb.b_name <> b.b_name) ctx.ctx_session.bindings
       ) bindings;
       Some (match bindings with
        | b :: _ ->
          let unit_s = match b.b_unit with Some u -> u | None -> "" in
          VList [VString "stored"; VString b.b_name; VFloat b.b_value; VString unit_s; VString ""]
        | [] ->
          VList [VString "error"; VString "no bindings"; VFloat 0.0; VString ""; VString ""]))

  | _ -> None
