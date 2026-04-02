(* kriya_krama.ml — krama (computation chain) evaluation.
   Extracted from kriya_graph.ml.

   Handles: ganana dimension, eval-name resolution, krama helpers,
   arity_of_op, and the three krama eval ops:
     eval-krama, eval-krama-dim, krama-path. *)

open Prakriti
open Kriya_types

(* ganana dimension — computation binding (concept → primitive) *)
let ganana_dim = Prakriti.register_dimension "ganana"

(* resolve eval name: walk ganana edge, fallback to shabda "eval" *)
let resolve_eval_name (k : proof_graph) (tok : string) : string =
  match Prakriti.find k tok with
  | Some n ->
    (match List.find_opt (fun e -> e.source = tok && e.relation = ganana_dim) n.edges with
     | Some e -> e.target
     | None ->
       let sh = Vidya.read_shabda k tok in
       (match List.assoc_opt "eval" sh with
        | Some ev -> String.trim ev
        | None -> tok))
  | None -> tok

(* ═══════════════════════════════════════════════════════════════════════════
   KRAMA HELPERS — used by eval-krama, eval-krama-dim, krama-path.
   ═══════════════════════════════════════════════════════════════════════════ *)

(* Load float bindings from [[concept, value], ...] pairs *)
let load_krama_bindings (bindings_v : value list) : (string, float) Hashtbl.t =
  let binds = Hashtbl.create 8 in
  List.iter (fun pair ->
    match pair with
    | VList [VString concept; VFloat v] -> Hashtbl.replace binds concept v
    | VList [VString concept; v] -> Hashtbl.replace binds concept (as_float v)
    | _ -> ()
  ) bindings_v;
  binds

(* Bind physics constants from shabda (constants-key → physics-constants lookup) *)
let bind_krama_constants (k : proof_graph) (mantra_name : string)
    (n : nigamana) (binds : (string, float) Hashtbl.t) : unit =
  let janya_names = List.filter_map (fun e ->
    if e.source = mantra_name && e.relation = janya then Some e.target else None
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
  ) janya_names

(* Swarupa fallback: if a janya concept is unbound, check swarupa parents.
   e.g. final-momentum has swarupa → momentum; if momentum is bound, use its value. *)
let bind_swarupa_fallbacks (k : proof_graph) (mantra_name : string)
    (_n : nigamana) (binds : (string, float) Hashtbl.t) : unit =
  let janya_names = List.filter_map (fun e ->
    if e.source = mantra_name && e.relation = janya then Some e.target else None
  ) _n.edges in
  List.iter (fun jn ->
    if not (Hashtbl.mem binds jn) then begin
      let parents = Vidya.swarupa_of k jn in
      List.iter (fun parent ->
        if not (Hashtbl.mem binds jn) && Hashtbl.mem binds parent then
          Hashtbl.replace binds jn (Hashtbl.find binds parent)
      ) parents
    end
  ) janya_names

(* Resolve op name via eval_index + ganana graph walk fallback *)
let resolve_krama_op (k : proof_graph) (tok : string) : string =
  (* ganana edge takes priority — resolves graph concept names to eval primitives *)
  let ganana_resolved = resolve_eval_name k tok in
  if ganana_resolved <> tok then ganana_resolved
  else match Domain.DLS.get _eval_ctx with
  | Some ctx ->
    (match Hashtbl.find_opt ctx.ctx_index.eval_index tok with
     | Some _ -> tok | None -> tok)
  | None -> tok

(* Tokenize krama s-expression *)
let tokenize_krama (krama : string) : string list =
  String.split_on_char ' ' krama |> List.filter (fun s -> s <> "")

(* ═══════════════════════════════════════════════════════════════════════════
   ARITY — derive arity from graph: op-{name} → kriya → class.
   projection = unary (1), everything else = binary (2).
   ═══════════════════════════════════════════════════════════════════════════ *)

let arity_of_op (k : proof_graph) (eval_name : string) : int =
  let op_node_name = "op-" ^ eval_name in
  let kriya_dim = match visheshanam_of_string "kriya" with
    | Some d -> d | None -> -1 in
  if kriya_dim < 0 then 2
  else match find k op_node_name with
  | None -> 2
  | Some op_node ->
    let class_name = List.fold_left (fun acc e ->
      if e.source = op_node_name && e.relation = kriya_dim then e.target
      else acc
    ) "" op_node.edges in
    if class_name = "op-class-projection" then 1 else 2

(* ═══════════════════════════════════════════════════════════════════════════
   EVAL_KRAMA_OP — handles "eval-krama", "eval-krama-dim", "krama-path".
   Returns Some value if op matched, None otherwise.
   ═══════════════════════════════════════════════════════════════════════════ *)

let eval_krama_op
    (e_eval : proof_graph -> env -> expr -> value)
    (k : proof_graph) (e : env) (op : string) (args : expr list)
    : value option =
  let (eval_arg, eval_str, _eval_flt, eval_lst, _eval_int) =
    make_eval_arg e_eval k e args in
  ignore eval_arg;
  match op with

  | "eval-krama" ->
    let mantra_name = eval_str 0 in
    let bindings_v = eval_lst 1 in
    Some (with_node k mantra_name (fun n ->
      let krama = n.krama in
      if krama = "" then VNone
      else
        let binds = load_krama_bindings bindings_v in
        bind_krama_constants k mantra_name n binds;
        bind_swarupa_fallbacks k mantra_name n binds;
        let toks = tokenize_krama krama in
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
                let eval_name = resolve_krama_op k tok in
                let arity = arity_of_op k eval_name in
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

  | "eval-krama-dim" ->
    (* Walk a mantra's krama s-expression with dimension vectors.
       Pure computation: takes bindings [[concept, [exponents]], ...],
       walks the krama tree applying matra-ghata algebra rules from shabda.
       The caller (tantra) is responsible for resolving concept→dimension.
       Returns: VList of VFloat exponents, or VNone. *)
    let mantra_name = eval_str 0 in
    let bindings_v = eval_lst 1 in
    Some (with_node k mantra_name (fun n ->
      let krama = n.krama in
      if krama = "" then VNone
      else
        (* Infer dimension length from first binding, default 7 *)
        let dim_len = match bindings_v with
          | VList [_; VList dims] :: _ -> max 1 (List.length dims)
          | _ -> 7
        in
        let zero_dim = Array.make dim_len 0.0 in
        let dim_to_vlist arr =
          VList (Array.to_list (Array.map (fun f -> VFloat f) arr))
        in
        (* Load bindings from caller *)
        let binds : (string, float array) Hashtbl.t = Hashtbl.create 16 in
        List.iter (fun pair ->
          match pair with
          | VList [VString concept; VList dims] ->
            let arr = Array.make dim_len 0.0 in
            List.iteri (fun i v ->
              if i < dim_len then arr.(i) <- as_float v
            ) dims;
            Hashtbl.replace binds concept arr
          | _ -> ()
        ) bindings_v;
        (* No implicit resolution — caller provides all bindings.
           Unbound janya evaluate to zero-dim (dimensionless). *)
        (* Dimension algebra operations *)
        let dim_add a b =
          Array.init dim_len (fun i -> a.(i) +. b.(i)) in
        let dim_sub a b =
          Array.init dim_len (fun i -> a.(i) -. b.(i)) in
        let dim_double a =
          Array.init dim_len (fun i -> a.(i) *. 2.0) in
        let dim_halve a =
          Array.init dim_len (fun i -> a.(i) /. 2.0) in
        let dim_negate a =
          Array.init dim_len (fun i -> -. a.(i)) in
        (* Resolve op's matra-ghata rule from shabda *)
        let resolve_ghata tok =
          let sh = Vidya.read_shabda k tok in
          match List.assoc_opt "matra-ghata" sh with
          | Some rule -> String.trim rule
          | None -> "identity"
        in
        let toks = tokenize_krama krama in
        let rec walk_dim toks =
          match toks with
          | [] -> Array.copy zero_dim, []
          | "(" :: rest ->
            let (v, rest2) = walk_dim rest in
            let rest3 = match rest2 with ")" :: r -> r | r -> r in
            v, rest3
          | ")" :: rest -> Array.copy zero_dim, rest
          | tok :: rest ->
            if Hashtbl.mem binds tok then
              Hashtbl.find binds tok, rest
            else
              match float_of_string_opt tok with
              | Some _ -> Array.copy zero_dim, rest
              | None ->
                let ghata = resolve_ghata tok in
                let eval_name = resolve_krama_op k tok in
                let is_op = ghata <> "identity" ||
                  (match Domain.DLS.get _eval_ctx with
                   | Some ctx -> Hashtbl.mem ctx.ctx_index.eval_index eval_name
                   | None -> false) in
                if not is_op then
                  (* unknown token = dimensionless constant (pi, e, etc.) *)
                  Array.copy zero_dim, rest
                else
                let arity = arity_of_op k eval_name in
                let args = ref [] in
                let remaining = ref rest in
                for _ = 1 to arity do
                  let (v, r) = walk_dim !remaining in
                  args := v :: !args;
                  remaining := r
                done;
                let arg_vals = List.rev !args in
                let result = match ghata, arg_vals with
                  | "add", [a; b] -> dim_add a b
                  | "sub", [a; b] -> dim_sub a b
                  | "same", a :: _ -> a
                  | "double", [a] -> dim_double a
                  | "halve", [a] -> dim_halve a
                  | "negate", [a] -> dim_negate a
                  | "identity", [a] -> a
                  | _, a :: _ -> a   (* unknown rule: pass through first arg *)
                  | _, [] -> Array.copy zero_dim
                in
                result, !remaining
        in
        let (result, _) = walk_dim toks in
        dim_to_vlist result
    ) VNone)

  | "krama-path" ->
    let mantra_name = eval_str 0 in
    let target = eval_str 1 in
    let bindings_v = eval_lst 2 in
    Some (with_node k mantra_name (fun n ->
      let krama = n.krama in
      if krama = "" then VList []
      else
        let binds = load_krama_bindings bindings_v in
        bind_krama_constants k mantra_name n binds;
        bind_swarupa_fallbacks k mantra_name n binds;
        let janya_names = List.filter_map (fun e ->
          if e.source = mantra_name && e.relation = janya
          then Some e.target else None
        ) n.edges in
        let toks = tokenize_krama krama in
        let is_op tok =
          tok <> "(" && tok <> ")" &&
          not (List.mem tok janya_names)
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
                let eval_name = resolve_krama_op k tok in
                let arity = arity_of_op k eval_name in
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
              let arity = arity_of_op k (resolve_krama_op k tok) in
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
              let arity = arity_of_op k (resolve_krama_op k tok) in
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

  | _ -> None
