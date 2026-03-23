(* kriya_graph.ml — graph ops + dispatch + forward refs.
   replaces yantra_eval_primitives.ml (647L) + yantra_pipeline_ops.ml (68L).
   the dispatch chains: eval_graph_op → eval_pure_op → eval_pipeline_op → tantra fallback.

   sections:
     1. eval context + forward refs
     2. helpers — env_copy, pair_field, call_tantra_opt
     3. eval_graph_op — graph/field/context ops (24 match arms)
     4. eval_pipeline_op — session ops + unknown fallback
     5. eval_call — chained dispatch
     6. register_primitive_arities *)

open Prakriti
open Kriya_types

(* ═══════════════════════════════════════════════════════════════════════════
   1. EVAL CONTEXT + FORWARD REFS
   ═══════════════════════════════════════════════════════════════════════════ *)

type eval_context = {
  ctx_index   : tantra_index;
  ctx_session : session;
}
let eval_ctx : eval_context option ref = ref None

let _eval_ref : (proof_graph -> env -> expr -> value) ref =
  ref (fun _ _ _ -> VNone)

let _eval_tantra_ref : (proof_graph -> tantra -> (string * value) list -> value) ref =
  ref (fun _ _ _ -> VNone)

let _eval_pure_op_raw : ((proof_graph -> env -> expr -> value) -> proof_graph -> env -> string -> expr list -> value option) ref =
  ref (fun _e_eval _k _e _op _args -> None)

let _eval_pipeline_op_raw : ((proof_graph -> env -> expr -> value) -> proof_graph -> env -> string -> expr list -> value option) ref =
  ref (fun _e_eval _k _e _op _args -> None)

let last_invoked_tantra : string ref = ref ""

(* ═══════════════════════════════════════════════════════════════════════════
   2. HELPERS
   ═══════════════════════════════════════════════════════════════════════════ *)

let env_copy (e : env) : env =
  let e2 = Hashtbl.create (Hashtbl.length e) in
  Hashtbl.iter (fun k v -> Hashtbl.replace e2 k v) e;
  e2

let pair_field (items : value list) (key : string) : value option =
  List.find_map (function
    | VPair (k, v) when k = key -> Some v
    | VList [VString k; v] when k = key -> Some v
    | _ -> None
  ) items

let call_tantra_opt (k : proof_graph) (name : string)
    (inputs : (string * value) list) ~(default : value) : value =
  match !eval_ctx with
  | Some ctx ->
    (match Hashtbl.find_opt ctx.ctx_index.by_name name with
     | Some t -> !_eval_tantra_ref k t inputs
     | None   -> default)
  | None -> default

(* ═══════════════════════════════════════════════════════════════════════════
   3. EVAL_GRAPH_OP — graph, field-accessor, and context operations
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
    Some (VList [dedup "janya"; dedup "phala"; dedup "kriya";
                 dedup "yukta"; dedup "sthita"; dedup "swarupa";
                 dedup "abheda"])

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
    (* Evaluate a mantra's krama s-expression directly.
       Args: mantra-name, bindings (list of [concept, value] pairs).
       Resolves op node-names → eval-names via eval_index, then evaluates.
       No synthetic tantra needed. *)
    let mantra_name = eval_str 0 in
    let bindings_v = eval_lst 1 in
    Some (with_node k mantra_name (fun n ->
      let krama = n.krama in
      if krama = "" then VNone
      else
        (* Build bindings map: concept-name → float value *)
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
          match !eval_ctx with
          | Some ctx ->
            (match Hashtbl.find_opt ctx.ctx_index.eval_index tok with
             | Some _node_name ->
               (* tok IS an eval name, use it directly *)
               tok
             | None ->
               (* tok might be a node name — look up its eval shabda *)
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
            (* Is it a bound variable? *)
            if Hashtbl.mem binds tok then
              VFloat (Hashtbl.find binds tok), rest
            else
              (* Try as a numeric literal *)
              match float_of_string_opt tok with
              | Some f -> VFloat f, rest
              | None ->
                (* It's an op — resolve to eval name *)
                let eval_name = resolve_op tok in
                (* Determine arity from shabda *)
                let arity =
                  let sh = Vidya.read_shabda k tok in
                  match List.assoc_opt "arity" sh with
                  | Some a -> (try int_of_string (String.trim a) with _ -> 2)
                  | None -> (* check if known unary *)
                    if List.mem eval_name ["half";"double";"square";"sqrt";
                       "neg";"reciprocal";"abs";"floor";"ceil";
                       "sin";"cos";"tan";"asin";"acos";"atan";
                       "log";"exp"] then 1 else 2
                in
                (* Evaluate arity args *)
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
                let result = match !_eval_pure_op_raw lit_eval k
                  (Hashtbl.create 0) eval_name arg_exprs with
                | Some v -> v
                | None -> VNone
                in
                result, !remaining
        in
        let (result, _) = eval_krama toks in
        result
    ) VNone)

  | "krama-path" ->
    (* Given a mantra name, solve-target, and bindings,
       parse the krama s-expr and return [op, arg-index, sibling-value]
       triples on the path from root to that variable.
       sibling-value = the evaluated result of the other branch at each binary op.
       e.g. krama "half ( mul mass ( square velocity ) )"
            target "mass", bindings [["velocity","5."]]
            → [["half","0",""], ["mul","0","25"]]
       The sibling (square velocity) is evaluated to 25 using bindings.
       For unary ops, sibling-value is "". *)
    let mantra_name = eval_str 0 in
    let target = eval_str 1 in
    let bindings_v = eval_lst 2 in
    Some (with_node k mantra_name (fun n ->
      let krama = n.krama in
      if krama = "" then VList []
      else
        (* Build bindings map *)
        let binds = Hashtbl.create 8 in
        List.iter (fun pair ->
          match pair with
          | VList [VString concept; VFloat v] ->
            Hashtbl.replace binds concept v
          | VList [VString concept; v] ->
            Hashtbl.replace binds concept (as_float v)
          | _ -> ()
        ) bindings_v;
        (* Also bind constants *)
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
        (* Resolve op name → eval name *)
        let resolve_op tok =
          match !eval_ctx with
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
        (* Evaluate a krama sub-expression with bindings *)
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
                let result = match !_eval_pure_op_raw lit_eval k
                  (Hashtbl.create 0) eval_name arg_exprs with
                | Some v -> v
                | None -> VNone
                in
                result, !remaining
        in
        (* Skip a sub-expression without evaluating, return remaining tokens *)
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
            else rest (* leaf variable — just skip *)
        in
        (* Evaluate a sub-expression from token list, return (value, remaining) *)
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
        (* parse_expr: return (path option, remaining tokens).
           Path is a list of (op_name, arg_index, sibling_value) triples. *)
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
                (* Binary op: parse first arg *)
                let (found1, rest2) = parse_expr rest in
                match found1 with
                | Some ops ->
                  (* Target in arg 0 — evaluate the sibling (arg 1) *)
                  let (sib_val, rest3) = eval_sibling rest2 in
                  Some ((tok, 0, sib_val) :: ops), rest3
                | None ->
                  (* Target not in arg 0 — parse arg 1 *)
                  let (found2, rest3) = parse_expr rest2 in
                  (match found2 with
                   | Some ops ->
                     (* Target in arg 1 — need sibling value from arg 0.
                        But we already consumed arg 0! We need to re-eval it.
                        Restart: skip arg0, but first eval it. *)
                     (* We already advanced past arg0 (rest → rest2).
                        Re-tokenize arg0 from original rest to eval it. *)
                     (* Actually, arg0 was parsed by parse_expr which consumed tokens.
                        We need to evaluate the same tokens. Let's re-eval from rest. *)
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
      name; layer; slokas; edges;
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
         name = source; layer = "kosha"; slokas = []; edges = [edge];
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
    Some (match !eval_ctx with
     | Some ctx ->
       (match Hashtbl.find_opt ctx.ctx_index.word_index word with
        | Some node_name -> VString node_name | None -> VNone)
     | None -> VNone)

  | "eval-node" ->
    (* Given an eval name (e.g. "mul"), return the node name ("multiplication").
       O(1) lookup via eval_index built at load time. *)
    let ev = eval_str 0 in
    Some (match !eval_ctx with
     | Some ctx ->
       (match Hashtbl.find_opt ctx.ctx_index.eval_index ev with
        | Some node_name -> VString node_name | None ->
          (* fallback: maybe ev IS the node name *)
          (match find k ev with Some _ -> VString ev | None -> VNone))
     | None -> VNone)

  | "call-tantra" ->
    let tname = eval_str 0 in
    let arg_list = eval_lst 1 in
    Some (match !eval_ctx with
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
          !_eval_tantra_ref k t input_values)
     | None -> VNone)

  | _ -> None

(* ═══════════════════════════════════════════════════════════════════════════
   4. EVAL_PIPELINE_OP — session ops + unknown fallback
   ═══════════════════════════════════════════════════════════════════════════ *)

let eval_pipeline_op (e_eval : proof_graph -> env -> expr -> value)
    (k : proof_graph) (e : env) (op : string) (args : expr list) : value option =
  match op with
  | "remember-bindings" ->
    let items = as_list (e_eval k e (List.nth args 0)) in
    (match !eval_ctx with
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
    (match Hashtbl.find_opt e op with
     | Some (VFn (params, body, captured)) ->
       let local = env_copy captured in
       List.iteri (fun i param ->
         if i < List.length args then
           Hashtbl.replace local param (e_eval k e (List.nth args i))
       ) params;
       Some (e_eval k local body)
     | _ ->
       (match !eval_ctx with
        | Some ctx ->
          (match Hashtbl.find_opt ctx.ctx_index.by_name op with
           | Some t ->
             let input_values = List.mapi (fun i inp ->
               let v = if i < List.length args then e_eval k e (List.nth args i) else VNone in
               (inp.tp_name, v)
             ) t.t_inputs in
             Some (!_eval_tantra_ref k t input_values)
           | None -> None)
        | None -> None))

(* ═══════════════════════════════════════════════════════════════════════════
   5. EVAL_CALL — chained dispatch
   ═══════════════════════════════════════════════════════════════════════════ *)

let eval_call (k : proof_graph) (e : env) (op : string) (args : expr list) : value =
  let e_eval = !_eval_ref in
  match eval_graph_op e_eval k e op args with
  | Some v -> v
  | None ->
    match !_eval_pure_op_raw e_eval k e op args with
    | Some v -> v
    | None ->
      match !_eval_pipeline_op_raw e_eval k e op args with
      | Some v -> v
      | None ->
        let apply_op_vals prim_name op_args =
          let lifted = List.map (fun v -> match v with
            | VFloat f -> Lit f | VString s -> StrLit s
            | VBool b -> BoolLit b | _ -> Lit (as_float v)) op_args in
          match !_eval_pure_op_raw e_eval k e prim_name lifted with
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
          (match !eval_ctx with
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
                !_eval_tantra_ref k t input_values
              | None ->
                Printf.printf "eval: unknown operation '%s'\n%!" op; VNone)
           | None ->
               Printf.printf "eval: unknown operation '%s'\n%!" op; VNone))

(* ═══════════════════════════════════════════════════════════════════════════
   6. REGISTER_PRIMITIVE_ARITIES
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
  r "reduce"              3;
  r "fixpoint"            2;
  r "iterate"             3;
  r "add"                (-1);
  r "mul"                (-1);
  r "sub"                 2;
  r "div"                 2;
  r "max"                 2;
  r "min"                 2;
  r "power"               2
