(* kriya_graph.ml — graph ops + dispatch + engine wiring.
   replaces yantra_eval_primitives.ml (647L) + yantra_pipeline_ops.ml (68L).
   the dispatch chains: eval_graph_op → eval_pure_op → eval_pipeline_op → tantra fallback.

   env is immutable StringMap — no env_copy.
   4 forward refs replaced by single _engine Atomic record in kriya_types.
   eval_ctx is Atomic in kriya_types.

   sections:
     1. helpers — pair_field, call_tantra_opt
     2. eval_graph_op — graph/field/context ops
     3. eval_pipeline_op — session ops + unknown fallback
     4. eval_call — chained dispatch
     5. register_primitive_arities *)

open Prakriti
open Kriya_types

(* per-thread CPU time in microseconds — excludes Domain contention *)
external thread_cpu_us : unit -> float = "caml_thread_cpu_us"

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
   1b. OM-CONTRACT CACHE — process-level cache for mantra contracts.
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
       let edges = edges_of k node_name in
       VList (List.filter_map (fun edge ->
         if edge.relation = vish && edge.target = node_name then Some (VNode edge.source)
         else None
       ) edges))

  | "om-janya" | "om-phala" | "om-kriya" | "om-yukta"
  | "om-sthita" | "om-swarupa" | "om-abheda" ->
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

  | "eval-krama" ->
    let mantra_name = eval_str 0 in
    let bindings_v = eval_lst 1 in
    Some (with_node k mantra_name (fun n ->
      let krama = n.krama in
      if krama = "" then VNone
      else
        (* Build bindings map: concept-name → float value (local Hashtbl, not env) *)
        let binds = Hashtbl.create 8 in
        List.iter (fun pair ->
          match pair with
          | VList [VString concept; VFloat v] ->
            Hashtbl.replace binds concept v
          | VList [VString concept; v] ->
            Hashtbl.replace binds concept (as_float v)
          | _ -> ()
        ) bindings_v;
        (* Also bind constants: check shabda for constants-key *)
        let janya_names = List.filter_map (fun e ->
          if e.source = mantra_name && e.relation = janya
          then Some e.target else None
        ) n.edges in
        List.iter (fun jn ->
          if not (Hashtbl.mem binds jn) then begin
            let sh = Vidya.read_shabda k jn in
            match List.assoc_opt "constants-key" sh with
            | Some ck ->
              let csh = Vidya.read_shabda k "physics-constants" in
              (match List.assoc_opt ck csh with
               | Some vs ->
                 (try Hashtbl.replace binds jn (float_of_string (String.trim vs))
                  with _ -> ())
               | None -> ())
            | None -> ()
          end
        ) janya_names;
        (* Resolve op name → eval name using eval_index *)
        let resolve_op tok =
          match Domain.DLS.get _eval_ctx with
          | Some ctx ->
            (match Hashtbl.find_opt ctx.ctx_index.eval_index tok with
             | Some _node_name -> tok
             | None ->
               let sh = Vidya.read_shabda k tok in
               (match List.assoc_opt "eval" sh with
                | Some ev -> String.trim ev
                | None -> tok))
          | None -> tok
        in
        (* Tokenize krama *)
        let toks = String.split_on_char ' ' krama
          |> List.filter (fun s -> s <> "") in
        (* Recursive evaluator for krama s-expression *)
        let rec eval_krama toks =
          match toks with
          | [] -> VNone, []
          | "(" :: rest ->
            let (v, rest2) = eval_krama rest in
            let rest3 = match rest2 with ")" :: r -> r | r -> r in
            v, rest3
          | ")" :: rest -> VNone, rest
          | tok :: rest ->
            if Hashtbl.mem binds tok then
              VFloat (Hashtbl.find binds tok), rest
            else
              match float_of_string_opt tok with
              | Some f -> VFloat f, rest
              | None ->
                let eval_name = resolve_op tok in
                let arity =
                  let sh = Vidya.read_shabda k tok in
                  match List.assoc_opt "arity" sh with
                  | Some a -> (try int_of_string (String.trim a) with _ -> 2)
                  | None ->
                    if List.mem eval_name ["half";"double";"square";"sqrt";
                       "neg";"reciprocal";"abs";"floor";"ceil";
                       "sin";"cos";"tan";"asin";"acos";"atan";
                       "log";"exp"] then 1 else 2
                in
                let args = ref [] in
                let remaining = ref rest in
                for _ = 1 to arity do
                  let (v, r) = eval_krama !remaining in
                  args := v :: !args;
                  remaining := r
                done;
                let arg_vals = List.rev !args in
                let arg_exprs = List.map (fun v -> match v with
                  | VFloat f -> Lit f | _ -> Lit 0.0) arg_vals in
                let lit_eval _k _e expr = match expr with
                  | Lit f -> VFloat f | StrLit s -> VString s
                  | BoolLit b -> VBool b | _ -> VNone in
                let result = match (Atomic.get _engine).eval_pure_op lit_eval k
                  StringMap.empty eval_name arg_exprs with
                | Some v -> v
                | None -> VNone
                in
                result, !remaining
        in
        let (result, _) = eval_krama toks in
        result
    ) VNone)

  | "krama-path" ->
    let mantra_name = eval_str 0 in
    let target = eval_str 1 in
    let bindings_v = eval_lst 2 in
    Some (with_node k mantra_name (fun n ->
      let krama = n.krama in
      if krama = "" then VList []
      else
        (* Build bindings map (local Hashtbl, not env) *)
        let binds = Hashtbl.create 8 in
        List.iter (fun pair ->
          match pair with
          | VList [VString concept; VFloat v] ->
            Hashtbl.replace binds concept v
          | VList [VString concept; v] ->
            Hashtbl.replace binds concept (as_float v)
          | _ -> ()
        ) bindings_v;
        let janya_names = List.filter_map (fun e ->
          if e.source = mantra_name && e.relation = janya
          then Some e.target else None
        ) n.edges in
        List.iter (fun jn ->
          if not (Hashtbl.mem binds jn) then begin
            let sh = Vidya.read_shabda k jn in
            match List.assoc_opt "constants-key" sh with
            | Some ck ->
              let csh = Vidya.read_shabda k "physics-constants" in
              (match List.assoc_opt ck csh with
               | Some vs ->
                 (try Hashtbl.replace binds jn (float_of_string (String.trim vs))
                  with _ -> ())
               | None -> ())
            | None -> ()
          end
        ) janya_names;
        let toks = String.split_on_char ' ' krama
          |> List.filter (fun s -> s <> "") in
        let is_op tok =
          tok <> "(" && tok <> ")" &&
          not (List.mem tok janya_names)
        in
        let resolve_op tok =
          match Domain.DLS.get _eval_ctx with
          | Some ctx ->
            (match Hashtbl.find_opt ctx.ctx_index.eval_index tok with
             | Some _ -> tok
             | None ->
               let sh = Vidya.read_shabda k tok in
               (match List.assoc_opt "eval" sh with
                | Some ev -> String.trim ev
                | None -> tok))
          | None -> tok
        in
        let rec eval_sub toks =
          match toks with
          | [] -> VNone, []
          | "(" :: rest ->
            let (v, rest2) = eval_sub rest in
            let rest3 = match rest2 with ")" :: r -> r | r -> r in
            v, rest3
          | ")" :: rest -> VNone, rest
          | tok :: rest ->
            if Hashtbl.mem binds tok then
              VFloat (Hashtbl.find binds tok), rest
            else
              match float_of_string_opt tok with
              | Some f -> VFloat f, rest
              | None ->
                let eval_name = resolve_op tok in
                let arity =
                  let sh = Vidya.read_shabda k tok in
                  match List.assoc_opt "arity" sh with
                  | Some a -> (try int_of_string (String.trim a) with _ -> 2)
                  | None ->
                    if List.mem eval_name ["half";"double";"square";"sqrt";
                       "neg";"reciprocal";"abs";"floor";"ceil";
                       "sin";"cos";"tan";"asin";"acos";"atan";
                       "log";"exp"] then 1 else 2
                in
                let args = ref [] in
                let remaining = ref rest in
                for _ = 1 to arity do
                  let (v, r) = eval_sub !remaining in
                  args := v :: !args;
                  remaining := r
                done;
                let arg_vals = List.rev !args in
                let arg_exprs = List.map (fun v -> match v with
                  | VFloat f -> Lit f | _ -> Lit 0.0) arg_vals in
                let lit_eval _k _e expr = match expr with
                  | Lit f -> VFloat f | StrLit s -> VString s
                  | BoolLit b -> VBool b | _ -> VNone in
                let result = match (Atomic.get _engine).eval_pure_op lit_eval k
                  StringMap.empty eval_name arg_exprs with
                | Some v -> v
                | None -> VNone
                in
                result, !remaining
        in
        let rec _skip_expr toks =
          match toks with
          | [] -> []
          | ")" :: _ -> toks
          | "(" :: rest ->
            let rest2 = _skip_expr rest in
            let rest3 = match rest2 with ")" :: r -> r | r -> r in
            rest3
          | tok :: rest ->
            if is_op tok then
              let sh = Vidya.read_shabda k tok in
              let arity = match List.assoc_opt "arity" sh with
                | Some a -> (try int_of_string (String.trim a) with _ -> 2)
                | None -> let en = resolve_op tok in
                  if List.mem en ["half";"double";"square";"sqrt";
                     "neg";"reciprocal";"abs";"floor";"ceil";
                     "sin";"cos";"tan";"asin";"acos";"atan";
                     "log";"exp"] then 1 else 2
              in
              let remaining = ref rest in
              for _ = 1 to arity do
                remaining := _skip_expr !remaining
              done;
              !remaining
            else rest
        in
        let eval_sibling toks =
          let (v, rest) = eval_sub toks in
          let s = match v with
            | VFloat f ->
              let i = int_of_float f in
              if Float.equal (float_of_int i) f then string_of_int i
              else Printf.sprintf "%g" f
            | VString s -> s
            | _ -> ""
          in
          s, rest
        in
        let rec parse_expr toks =
          match toks with
          | [] -> None, []
          | ")" :: _ -> None, toks
          | "(" :: rest ->
            let (result, rest2) = parse_expr rest in
            let rest3 = match rest2 with ")" :: r -> r | r -> r in
            result, rest3
          | tok :: rest ->
            if tok = target then Some [], rest
            else if is_op tok then
              let sh = Vidya.read_shabda k tok in
              let arity = match List.assoc_opt "arity" sh with
                | Some a -> (try int_of_string (String.trim a) with _ -> 2)
                | None -> let en = resolve_op tok in
                  if List.mem en ["half";"double";"square";"sqrt";
                     "neg";"reciprocal";"abs";"floor";"ceil";
                     "sin";"cos";"tan";"asin";"acos";"atan";
                     "log";"exp"] then 1 else 2
              in
              if arity = 1 then begin
                let (found, rest2) = parse_expr rest in
                match found with
                | Some ops -> Some ((tok, 0, "") :: ops), rest2
                | None -> None, rest2
              end else begin
                let (found1, rest2) = parse_expr rest in
                match found1 with
                | Some ops ->
                  let (sib_val, rest3) = eval_sibling rest2 in
                  Some ((tok, 0, sib_val) :: ops), rest3
                | None ->
                  let (found2, rest3) = parse_expr rest2 in
                  (match found2 with
                   | Some ops ->
                     let (sib_val, _) = eval_sibling rest in
                     Some ((tok, 1, sib_val) :: ops), rest3
                   | None -> None, rest3)
              end
            else
              None, rest
        in
        let (result, _) = parse_expr toks in
        match result with
        | Some ops -> VList (List.map (fun (op, idx, sib) ->
            VList [VString op; VString (string_of_int idx); VString sib]
          ) ops)
        | None -> VList []
    ) (VList []))

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

  | "dim-vector" ->
    let unit_name = eval_str 0 in
    let pairs = Vidya.read_shabda k "matra-aayaama" in
    Some (match List.find_opt (fun (name, _) -> name = unit_name) pairs with
     | Some (_, dims_str) ->
       let parts = String.split_on_char ' ' (String.trim dims_str)
         |> List.filter (fun s -> String.length s > 0) in
       VList (List.map (fun s ->
         match float_of_string_opt s with Some f -> VFloat f | None -> VFloat 0.0
       ) parts)
     | None -> VNone)

  | "word-node" ->
    let word = eval_str 0 in
    Some (match Domain.DLS.get _eval_ctx with
     | Some ctx ->
       (match Hashtbl.find_opt ctx.ctx_index.word_index word with
        | Some node_name -> VString node_name | None -> VNone)
     | None -> VNone)

  | "word-node-compound" ->
    (* reverse of expand_avastha: check if two words form a known compound.
       e.g., word-node-compound "elastic" "energy" → "elastic-energy" *)
    let w1 = eval_str 0 in
    let w2 = eval_str 1 in
    let key = w1 ^ " " ^ w2 in
    Some (match Domain.DLS.get _eval_ctx with
     | Some ctx ->
       (match Hashtbl.find_opt ctx.ctx_index.compound_word_index key with
        | Some compound_name -> VString compound_name | None -> VNone)
     | None -> VNone)

  | "eval-node" ->
    let ev = eval_str 0 in
    Some (match Domain.DLS.get _eval_ctx with
     | Some ctx ->
       (match Hashtbl.find_opt ctx.ctx_index.eval_index ev with
        | Some node_name -> VString node_name | None ->
          (match find k ev with Some _ -> VString ev | None -> VNone))
     | None -> VNone)

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
        let vs = if Float.is_integer f && Float.is_finite f
          then Printf.sprintf "%g" f else Printf.sprintf "%g" f in
        vps := VList [VString s; VString vs] :: !vps
      | _ -> ()
    ) graph_v;
    (* collect all mantras whose phala edges could fire *)
    let janya_dim = match visheshanam_of_string "janya" with
      | Some d -> d | None -> register_dimension "janya" in
    let phala_dim = match visheshanam_of_string "phala" with
      | Some d -> d | None -> register_dimension "phala" in
    let swarupa_dim = match visheshanam_of_string "swarupa" with
      | Some d -> d | None -> register_dimension "swarupa" in
    (* recursive propagation *)
    let new_triples = ref [] in
    let fired_mantras = Hashtbl.create 8 in
    let rec propagate concept =
      (* find mantras that have this concept as janya *)
      let edges = !(k.all_edges) in
      let affected = List.filter_map (fun e ->
        if e.relation = janya_dim && e.target = concept then Some e.source
        else None
      ) edges in
      List.iter (fun mantra_name ->
        if Hashtbl.mem fired_mantras mantra_name then ()
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
    let vish = match visheshanam_of_string rel_name with
      | Some v -> v
      | None -> register_dimension rel_name in
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

  | _ -> None

(* ═══════════════════════════════════════════════════════════════════════════
   3. EVAL_PIPELINE_OP — session ops + unknown fallback
   ═══════════════════════════════════════════════════════════════════════════ *)

let eval_pipeline_op (e_eval : proof_graph -> env -> expr -> value)
    (k : proof_graph) (e : env) (op : string) (args : expr list) : value option =
  match op with
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

  | _ ->
    (* try env-bound function *)
    (match StringMap.find_opt op e with
     | Some (VFn (params, body, captured)) ->
       let local = List.fold_left (fun env_acc (i, param) ->
         if i < List.length args then
           StringMap.add param (e_eval k e (List.nth args i)) env_acc
         else env_acc
       ) captured (List.mapi (fun i p -> (i, p)) params) in
       Some (e_eval k local body)
     | _ ->
       (* try tantra lookup *)
       (match Domain.DLS.get _eval_ctx with
        | Some ctx ->
          (match Hashtbl.find_opt ctx.ctx_index.by_name op with
           | Some t ->
             let input_values = List.mapi (fun i inp ->
               let v = if i < List.length args then e_eval k e (List.nth args i) else VNone in
               (inp.tp_name, v)
             ) t.t_inputs in
             Some ((Atomic.get _engine).eval_tantra k t input_values)
           | None -> None)
        | None -> None))

(* ═══════════════════════════════════════════════════════════════════════════
   4. EVAL_CALL — chained dispatch
   ═══════════════════════════════════════════════════════════════════════════ *)

let eval_call (k : proof_graph) (e : env) (op : string) (args : expr list) : value =
  let eng = Atomic.get _engine in
  let e_eval = eng.eval in
  match eval_graph_op e_eval k e op args with
  | Some v -> v
  | None ->
    match eng.eval_pure_op e_eval k e op args with
    | Some v -> v
    | None ->
      match eng.eval_pipeline_op e_eval k e op args with
      | Some v -> v
      | None ->
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
          let prim_name =
            let sh = Vidya.raw_shabda_for_node k op_name in
            (match List.assoc_opt "eval" sh with
             | Some s -> String.trim s | None -> op_name)
          in
          apply_op_vals prim_name op_args_v
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
               Printf.printf "eval: unknown operation '%s'\n%!" op; VNone))

(* ═══════════════════════════════════════════════════════════════════════════
   5. REGISTER_PRIMITIVE_ARITIES
   ═══════════════════════════════════════════════════════════════════════════ *)

let register_primitive_arities () =
  let r = Vakya.register_graph_op_arity in
  let b = Vakya.register_boundary_keyword in
  List.iter b [")" ; "]" ; "," ; "in" ; "done" ; "let" ; "otherwise"];
  List.iter b ["where" ; "collect" ; "with"];
  r "lookup"              1;
  r "walk"                2;
  r "walk-in"             2;
  r "has"                 2;
  r "edges"               1;
  r "neighbors"           1;
  r "ppr"                 3;
  r "emit-node"           4;
  r "emit-edge"           3;
  r "propagate-derive"    1;
  r "index-graph"          1;
  r "idx-subjects"         2;
  r "idx-by-edge"          2;
  r "idx-has-edge"         2;
  r "idx-value"            3;
  r "idx-append"           2;
  r "mantra-select"        1;
  r "clock-us"             0;
  r "clock-ms"             0;
  r "profile-step"         2;
  r "session-emit"         3;
  r "session-by-edge"      1;
  r "session-triples"      0;
  r "session-clear"        0;
  r "session-has-edge"     1;
  r "session-subjects"     1;
  r "session-value"        2;
  r "om-janya"            1;
  r "om-phala"            1;
  r "om-kriya"            1;
  r "om-yukta"            1;
  r "om-sthita"           1;
  r "om-swarupa"          1;
  r "om-abheda"           1;
  r "om-contract"         1;
  r "shabda"              2;
  r "node-layer"          1;
  r "node-slokas"         1;
  r "node-krama"          1;
  r "eval-krama"          2;
  r "krama-path"          3;
  r "word-node"           1;
  r "word-node-compound"  2;
  r "eval-node"           1;
  r "lookup-word"         1;
  r "apply-op"            2;
  r "call-tantra"         2;
  r "split-numeric"       1;
  r "find-context"        1;
  r "scene-extract"       1;
  r "scene-narrate"       1;
  r "dim-vector"          1;
  r "square"              1;
  r "half"                1;
  r "double"              1;
  r "reciprocal"          1;
  r "abs"                 1;
  r "sqrt"                1;
  r "floor"               1;
  r "ceil"                1;
  r "sum"                 1;
  r "not"                 1;
  r "exists"              1;
  r "eq"                  2;
  r "neq"                 2;
  r "lt"                  2;
  r "gt"                  2;
  r "and"                (-1);
  r "or"                 (-1);
  r "string-length"       1;
  r "to-string"           1;
  r "to-number"           1;
  r "concat"             (-1);
  r "substr"              3;
  r "starts-with"         2;
  r "ends-with"           2;
  r "split"               2;
  r "join"                2;
  r "char-at"             2;
  r "nth"                 2;
  r "length"              1;
  r "append"              2;
  r "flatten"             1;
  r "unique"              1;
  r "member"              2;
  r "range"               1;
  r "map"                 2;
  r "filter"              2;
  r "pmap"                2;
  r "pfilter"             2;
  r "reduce"              3;
  r "preduce"             3;
  r "fixpoint"            2;
  r "iterate"             3;
  r "add"                (-1);
  r "mul"                (-1);
  r "sub"                 2;
  r "div"                 2;
  r "max"                 2;
  r "min"                 2;
  r "power"               2
