(* yantra_inverter.ml — symbolic inversion algebra for tantra let-blocks.
   given a chain of let-bindings that compute an output from inputs,
   produces an inverted evaluation plan that computes a missing input
   given the output and the other inputs.

   the inversion is graph-driven: each operation's inverse is looked up
   from the graph node's shabda (pratipaksha-0, pratipaksha-1, etc.)
   or from Pratipaksha edges.

   dependency: Proof_graph, Yantra_types, Setu. *)

open Proof_graph
open Yantra_types

(* ---- expression variable analysis ---- *)

(* collect all variable names referenced in an expression *)
let rec free_vars : expr -> string list = function
  | Var v -> [v]
  | Call (_, args) -> List.concat_map free_vars args
  | Lit _ | StrLit _ | BoolLit _ -> []
  | LetIn (_, rhs, body) -> free_vars rhs @ free_vars body
  | Lambda (params, body) ->
    List.filter (fun v -> not (List.mem v params)) (free_vars body)
  | Cond (branches, ow) ->
    List.concat_map (fun (g, b) -> free_vars g @ free_vars b) branches @ free_vars ow
  | ListExpr items -> List.concat_map free_vars items
  | From (lst, _pats, guards, collect) ->
    free_vars lst @ List.concat_map free_vars guards @ free_vars collect
  | Scan (lst, decls, branches) ->
    free_vars lst
    @ List.concat_map (fun (_, init) -> free_vars init) decls
    @ List.concat_map (fun b ->
        (match b.sb_guard with Some g -> free_vars g | None -> [])
        @ List.concat_map free_vars_stmt b.sb_body
      ) branches
and free_vars_stmt : scan_stmt -> string list = function
  | SEmit e -> free_vars e
  | SSet (_, e) -> free_vars e
  | SClear _ -> []
  | SLet (_, e) -> free_vars e
  | SWhen (g, then_body, else_body) ->
    free_vars g @ List.concat_map free_vars_stmt then_body
    @ List.concat_map free_vars_stmt else_body

let mentions_var name e = List.mem name (free_vars e)
let is_var_named name = function Var v -> v = name | _ -> false

(* ---- graph-based operation inversion ---- *)

(* cached eval→graph-node mapping, loaded once from ganana-setu *)
let eval_to_node : (string, string) Hashtbl.t = Hashtbl.create 32
let eval_mapping_loaded = ref false

let load_eval_mapping (k : proof_graph) : unit =
  if not !eval_mapping_loaded then begin
    eval_mapping_loaded := true;
    let pairs = Setu.read_shabda k "ganana-setu" in
    List.iter (fun (eval_name, node_name) ->
      Hashtbl.replace eval_to_node eval_name node_name
    ) pairs
  end

(* look up the inverse of a single operation at a given argument position.
   consults the graph node's shabda for pratipaksha-N entries, then
   falls back to walking Pratipaksha edges. *)
let graph_invert (k : proof_graph) (op : string) (arg_pos : int)
    (result_expr : expr) (other_expr : expr) (first_expr : expr option)
    : expr option =
  load_eval_mapping k;
  let node_name = match Hashtbl.find_opt eval_to_node op with
    | Some n -> n | None -> op in
  let pairs = Setu.read_shabda k node_name in
  let key = Printf.sprintf "pratipaksha-%d" arg_pos in
  match List.assoc_opt key pairs with
  | None ->
    (* fall back: walk Pratipaksha edges from the graph node *)
    (match Proof_graph.find k node_name with
     | None -> None
     | Some n ->
       let inv_node = List.find_map (fun edge ->
         if edge.source = node_name && edge.relation = pratipaksha then
           Some edge.target
         else None
       ) n.edges in
       match inv_node with
       | None -> None
       | Some inv_name ->
         let inv_pairs = Setu.read_shabda k inv_name in
         let inv_eval = match List.assoc_opt "eval" inv_pairs with
           | Some e -> e | None -> inv_name in
         Some (Call (inv_eval, [result_expr; other_expr])))
  | Some inv_eval_name ->
    let compound_key = Printf.sprintf "pratipaksha-%d-compound" arg_pos in
    let is_compound = List.assoc_opt compound_key pairs = Some "true" in
    if is_compound && op = "power" && arg_pos = 0 then
      (* a^b = r  →  a = r^(1/b) *)
      Some (Call ("power", [result_expr; Call ("div", [Lit 1.0; other_expr])]))
    else begin
      let flip_key = Printf.sprintf "pratipaksha-%d-flip" arg_pos in
      let flipped = List.assoc_opt flip_key pairs = Some "true" in
      let inv_node_name = match Hashtbl.find_opt eval_to_node inv_eval_name with
        | Some n -> n | None -> inv_eval_name in
      let inv_pairs = Setu.read_shabda k inv_node_name in
      let inv_arity = match List.assoc_opt "arity" inv_pairs with
        | Some s -> (match int_of_string_opt s with Some n -> n | None -> 2)
        | None -> 2 in
      if inv_arity = 1 then
        Some (Call (inv_eval_name, [result_expr]))
      else if flipped then
        match first_expr with
        | Some fe -> Some (Call (inv_eval_name, [fe; result_expr]))
        | None -> None
      else
        Some (Call (inv_eval_name, [result_expr; other_expr]))
    end

(* ---- single-binding inversion ---- *)

(* invert a single let-binding RHS to solve for `target`.
   result_expr is the known value of the LHS.
   recurses for nested expressions. *)
let rec invert_binding (k : proof_graph) (rhs : expr) (target : string) (result_expr : expr) : expr option =
  match rhs with
  | Call (op, [arg0; arg1]) ->
    let target_in_0 = mentions_var target arg0 in
    let target_in_1 = mentions_var target arg1 in
    if target_in_0 && is_var_named target arg0 then
      graph_invert k op 0 result_expr arg1 (Some arg0)
    else if target_in_1 && is_var_named target arg1 then
      graph_invert k op 1 result_expr arg0 (Some arg1)
    else if target_in_0 then
      (match graph_invert k op 0 result_expr arg1 (Some arg0) with
       | Some intermediate -> invert_binding k arg0 target intermediate
       | None -> None)
    else if target_in_1 then
      (match graph_invert k op 1 result_expr arg0 (Some arg1) with
       | Some intermediate -> invert_binding k arg1 target intermediate
       | None -> None)
    else None
  | Call (op, [arg0]) ->
    if is_var_named target arg0 then
      graph_invert k op 0 result_expr arg0 None
    else if mentions_var target arg0 then
      (match graph_invert k op 0 result_expr arg0 None with
       | Some intermediate -> invert_binding k arg0 target intermediate
       | None -> None)
    else None
  | Var v when v = target -> Some result_expr
  | _ -> None

(* ---- multi-step chain inversion ---- *)

(* build dependency map: binding name → variables it references *)
let build_dep_map lets =
  let tbl = Hashtbl.create 16 in
  List.iter (fun (name, rhs) ->
    Hashtbl.replace tbl name (List.sort_uniq String.compare (free_vars rhs))
  ) lets;
  tbl

(* invert through a multi-step let block.
   given:
     lets       — the forward evaluation plan (name, rhs) list
     known_names — variable names whose values are known
     target     — the input variable we want to solve for
     output_var — the variable whose value we have (the "result")
   returns an inverted plan: a new (name, rhs) list that computes target. *)
let invert_chain (k : proof_graph) (lets : (string * expr) list)
    (known_names : string list) (target : string) (output_var : string)
    : (string * expr) list option =
  let dep_map = build_dep_map lets in
  let let_map = Hashtbl.create 16 in
  List.iter (fun (n, e) -> Hashtbl.replace let_map n e) lets;

  (* find backward path: output_var → ... → binding that directly uses target *)
  let rec find_path visited node =
    if List.mem node visited then None
    else
      match Hashtbl.find_opt let_map node with
      | None -> None
      | Some rhs ->
        if mentions_var target rhs then Some [node]
        else
          let deps = try Hashtbl.find dep_map node with Not_found -> [] in
          let let_deps = List.filter (Hashtbl.mem let_map) deps in
          List.find_map (fun dep ->
            match find_path (node :: visited) dep with
            | Some path -> Some (node :: path)
            | None -> None
          ) let_deps
  in

  match find_path [] output_var with
  | None -> None
  | Some path ->
    (* forward-computable bindings not on the inversion path *)
    let fwd = List.filter_map (fun (name, rhs) ->
      if List.mem name path then None
      else
        let deps = free_vars rhs in
        if List.for_all (fun d -> List.mem d known_names || Hashtbl.mem let_map d) deps
        then Some (name, rhs) else None
    ) lets in
    let fwd_names = List.map fst fwd in
    let fwd = List.filter (fun (_name, rhs) ->
      let deps = free_vars rhs in
      List.for_all (fun d ->
        List.mem d known_names || List.mem d fwd_names
      ) deps
    ) fwd in
    (* invert along the path *)
    let rec invert_path = function
      | [] -> Some []
      | [binding_name] ->
        (match Hashtbl.find_opt let_map binding_name with
         | Some rhs ->
           (match invert_binding k rhs target (Var binding_name) with
            | Some inv -> Some [(target, inv)]
            | None -> None)
         | None -> None)
      | outer :: inner :: rest ->
        (match Hashtbl.find_opt let_map outer with
         | Some rhs ->
           (match invert_binding k rhs inner (Var outer) with
            | Some inv ->
              (match invert_path (inner :: rest) with
               | Some more -> Some ((inner, inv) :: more)
               | None -> None)
            | None -> None)
         | None -> None)
    in
    match invert_path path with
    | None -> None
    | Some inv_steps -> Some (fwd @ inv_steps)
