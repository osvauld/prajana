(* kriya_eval.ml — core eval loop + pipeline + wire refs.
   replaces yantra_eval.ml (218L).

   sections:
     1. core evaluator — eval, eval_from
     2. eval_tantra — evaluate a full tantra
     3. session + context helpers
     4. pipeline entry points — run_anuvada_ganana, run_session_anuvada
     5. print_result, run_tantra_by_name
     6. wire forward references *)

open Kriya_types
open Kriya_graph

(* ═══════════════════════════════════════════════════════════════════════════
   1. CORE EVALUATOR
   ═══════════════════════════════════════════════════════════════════════════ *)

type proof_graph = Prakriti.proof_graph

let rec eval (k : proof_graph) (e : env) (expr : expr) : value =
  match expr with
  | Lit f -> VFloat f
  | StrLit s -> VString s
  | BoolLit b -> VBool b
  | ListExpr items -> VList (List.map (eval k e) items)

  | Var v ->
    (match Hashtbl.find_opt e v with
     | Some value -> value
     | None ->
       if v = "_none" then VNone
       else
         match !eval_ctx with
         | Some ctx ->
           (match Hashtbl.find_opt ctx.ctx_index.by_name v with
            | Some t when t.t_inputs = [] ->
              !_eval_tantra_ref k t []
            | Some t ->
              VFn (List.map (fun p -> p.tp_name) t.t_inputs,
                   Call (t.t_name, List.map (fun p -> Var p.tp_name) t.t_inputs),
                   new_env ())
            | None -> VString v)
         | None -> VString v)

  | LetIn (name, rhs, body) ->
    let v = eval k e rhs in
    Hashtbl.replace e name v;
    eval k e body

  | Lambda (params, body) ->
    VFn (params, body, env_copy e)

  | Cond (branches, otherwise) ->
    let rec try_branches = function
      | [] -> eval k e otherwise
      | (guard, body) :: rest ->
        if as_bool (eval k e guard) then eval k e body
        else try_branches rest
    in
    try_branches branches

  | Call (op, args) ->
    eval_call k e op args

  | From (list_expr, pat_names, guards, collect_expr) ->
    eval_from k e list_expr pat_names guards collect_expr

  | Scan _ ->
    failwith "eval: scan construct removed — all tantras use reduce now"

and eval_from (k : proof_graph) (e : env) (list_expr : expr)
    (pat_names : string list) (guards : expr list) (collect_expr : expr) : value =
  let items = as_list (eval k e list_expr) in
  let n_pat = List.length pat_names in
  let result = ref [] in
  List.iter (fun item ->
    let item_list = as_list item in
    let sub_env = env_copy e in
    List.iteri (fun i name ->
      let v = if i < List.length item_list then List.nth item_list i else VNone in
      Hashtbl.replace sub_env name v
    ) pat_names;
    Hashtbl.replace sub_env "_it" item;
    ignore n_pat;
    let pass = List.for_all (fun g -> as_bool (eval k sub_env g)) guards in
    if pass then begin
      let collected = eval k sub_env collect_expr in
      result := collected :: !result
    end
  ) items;
  VList (List.rev !result)

(* ═══════════════════════════════════════════════════════════════════════════
   2. EVAL_TANTRA
   ═══════════════════════════════════════════════════════════════════════════ *)

let eval_tantra ?(idx : tantra_index option) ?(session : session option)
    (k : proof_graph) (t : tantra) (input_values : (string * value) list) : value =
  let prev_ctx = !eval_ctx in
  (match idx, session with
   | Some i, Some s -> eval_ctx := Some { ctx_index = i; ctx_session = s }
   | _ -> ());
  let e = new_env () in
  List.iter (fun (name, v) -> Hashtbl.replace e name v) input_values;
  List.iter (fun (name, rhs) ->
    let v = eval k e rhs in
    Hashtbl.replace e name v
  ) t.t_lets;
  let result = match t.t_returns with
  | [ret] ->
    (match Hashtbl.find_opt e ret.tp_name with
     | Some v -> v | None -> VNone)
  | rets ->
    VList (List.filter_map (fun ret ->
      Hashtbl.find_opt e ret.tp_name
    ) rets)
  in
  eval_ctx := prev_ctx;
  result

(* ═══════════════════════════════════════════════════════════════════════════
   3. SESSION + CONTEXT HELPERS
   ═══════════════════════════════════════════════════════════════════════════ *)

let new_session () : session =
  { bindings = []; last_result = []; history = []; context_seeds = [] }

let with_eval_ctx (idx : tantra_index) (ses : session) (f : unit -> 'a) ~(default : 'a) : 'a =
  let prev = !eval_ctx in
  eval_ctx := Some { ctx_index = idx; ctx_session = ses };
  let r =
    try let v = f () in eval_ctx := prev; v
    with _ -> eval_ctx := prev; default
  in
  r

(* ═══════════════════════════════════════════════════════════════════════════
   4. PIPELINE ENTRY POINTS
   ═══════════════════════════════════════════════════════════════════════════ *)

let run_anuvada_ganana (k : proof_graph) (idx : tantra_index) (session : session)
    (sentence : string) : yantra_result option =
  match Hashtbl.find_opt idx.by_name "anuvada-ganana" with
  | None -> None
  | Some ag ->
    let result = eval_tantra ~idx ~session k ag
      [("sentence", VString sentence)] in
    let raw = as_string result in
    if String.length raw = 0 then None
    else begin
      let tantra_name = if String.length !last_invoked_tantra > 0 then
        !last_invoked_tantra else "anuvada-ganana" in
      Some { yr_output = []; yr_tantra = tantra_name;
             yr_code = "(via anuvada-ganana)"; yr_raw_output = raw }
    end

let run_session_anuvada (k : proof_graph) (idx : tantra_index) (session : session)
    (prior_graph : (string * string * string) list) (sentence : string)
    : yantra_result option =
  match Hashtbl.find_opt idx.by_name "session-anuvada" with
  | None -> run_anuvada_ganana k idx session sentence
  | Some sa ->
    let prior_val = VList (List.map (fun (s, p, o) ->
      VList [VString s; VString p; VString o]
    ) prior_graph) in
    let result = eval_tantra ~idx ~session k sa
      [("sentence", VString sentence); ("prior-graph", prior_val)] in
    let raw = as_string result in
    if String.length raw = 0 then None
    else begin
      let tantra_name = if String.length !last_invoked_tantra > 0 then
        !last_invoked_tantra else "session-anuvada" in
      Some { yr_output = []; yr_tantra = tantra_name;
             yr_code = "(via session-anuvada)"; yr_raw_output = raw }
    end

(* ═══════════════════════════════════════════════════════════════════════════
   5. PRINT_RESULT + RUN_TANTRA_BY_NAME
   ═══════════════════════════════════════════════════════════════════════════ *)

let print_result (r : yantra_result) : unit =
  if String.length r.yr_raw_output > 0 then
    Printf.printf "%s\n%!" r.yr_raw_output
  else begin
    List.iter (fun (name, value) ->
      if name = "result" then Printf.printf "%g\n" value
      else Printf.printf "%s = %g\n" name value
    ) r.yr_output;
    if List.length r.yr_output > 0 then
      Printf.printf "\n  tantra: %s\n%!" r.yr_tantra
  end

let run_tantra_by_name (k : proof_graph) (idx : tantra_index) (session : session)
    (name : string) (inputs : (string * value) list) : yantra_result option =
  match Hashtbl.find_opt idx.by_name name with
  | None -> None
  | Some t ->
    eval_ctx := Some { ctx_index = idx; ctx_session = session };
    let result = eval_tantra ~idx ~session k t inputs in
    eval_ctx := None;
    let raw = as_string result in
    if String.length raw = 0 then None
    else Some { yr_output = []; yr_tantra = name;
                yr_code = "(via " ^ name ^ ")"; yr_raw_output = raw }

(* ═══════════════════════════════════════════════════════════════════════════
   6. WIRE FORWARD REFERENCES
   ═══════════════════════════════════════════════════════════════════════════ *)

let () =
  _eval_ref := eval;
  _eval_tantra_ref := (fun k t inputs -> eval_tantra k t inputs);
  _eval_pure_op_raw := Kriya_ops.eval_pure_op;
  _eval_pipeline_op_raw := eval_pipeline_op;
  register_primitive_arities ()
