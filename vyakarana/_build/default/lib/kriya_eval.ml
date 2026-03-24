(* kriya_eval.ml — core eval loop + pipeline + engine wiring.

   env is immutable StringMap — LetIn passes new env to body, Lambda captures without copy.
   eval_ctx uses Atomic + Fun.protect for exception-safe save/restore.
   4 forward refs replaced by single _engine Atomic record.

   sections:
     1. core evaluator — eval, eval_from
     2. eval_tantra — evaluate a full tantra
     3. session + context helpers (Fun.protect)
     4. pipeline entry points — run_anuvada_ganana, run_session_anuvada
     5. print_result, run_tantra_by_name
     6. wire engine (single Atomic.set) *)

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
    (match StringMap.find_opt v e with
     | Some value -> value
     | None ->
       if v = "_none" then VNone
       else
         match Domain.DLS.get _eval_ctx with
         | Some ctx ->
           (match Hashtbl.find_opt ctx.ctx_index.by_name v with
            | Some t when t.t_inputs = [] ->
              (Atomic.get _engine).eval_tantra k t []
            | Some t ->
              VFn (List.map (fun p -> p.tp_name) t.t_inputs,
                   Call (t.t_name, List.map (fun p -> Var p.tp_name) t.t_inputs),
                   new_env ())
            | None -> VString v)
         | None -> VString v)

  | LetIn (name, rhs, body) ->
    let v = eval k e rhs in
    eval k (StringMap.add name v e) body

  | Lambda (params, body) ->
    (* immutable env — no copy needed, just capture *)
    VFn (params, body, e)

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
  let result = ref [] in
  List.iter (fun item ->
    let item_list = as_list item in
    (* build sub_env by adding pattern bindings to immutable env *)
    let sub_env = List.fold_left (fun env_acc (i, name) ->
      let v = if i < List.length item_list then List.nth item_list i else VNone in
      StringMap.add name v env_acc
    ) e (List.mapi (fun i n -> (i, n)) pat_names) in
    let sub_env = StringMap.add "_it" item sub_env in
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
  let prev_ctx = Domain.DLS.get _eval_ctx in
  (match idx, session with
   | Some i, Some s -> Domain.DLS.set _eval_ctx (Some { ctx_index = i; ctx_session = s })
   | _ -> ());
  Fun.protect ~finally:(fun () -> Domain.DLS.set _eval_ctx prev_ctx) (fun () ->
    (* build env from inputs using fold *)
    let e = List.fold_left (fun env_acc (name, v) ->
      StringMap.add name v env_acc
    ) StringMap.empty input_values in
    (* evaluate let bindings sequentially — each sees previous bindings *)
    let e = List.fold_left (fun env_acc (name, rhs) ->
      let v = eval k env_acc rhs in
      StringMap.add name v env_acc
    ) e t.t_lets in
    match t.t_returns with
    | [ret] ->
      (match StringMap.find_opt ret.tp_name e with
       | Some v -> v | None -> VNone)
    | rets ->
      VList (List.filter_map (fun ret ->
        StringMap.find_opt ret.tp_name e
      ) rets))

(* ═══════════════════════════════════════════════════════════════════════════
   3. SESSION + CONTEXT HELPERS
   ═══════════════════════════════════════════════════════════════════════════ *)

let new_session () : session =
  { bindings = []; last_result = []; history = []; context_seeds = [] }

let with_eval_ctx (idx : tantra_index) (ses : session) (f : unit -> 'a) ~(default : 'a) : 'a =
  let prev = Domain.DLS.get _eval_ctx in
  Domain.DLS.set _eval_ctx (Some { ctx_index = idx; ctx_session = ses });
  Fun.protect ~finally:(fun () -> Domain.DLS.set _eval_ctx prev)
    (fun () -> try f () with _ -> default)

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
      let tantra_name =
        let lit = Atomic.get last_invoked_tantra in
        if String.length lit > 0 then lit else "anuvada-ganana" in
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
      let tantra_name =
        let lit = Atomic.get last_invoked_tantra in
        if String.length lit > 0 then lit else "session-anuvada" in
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
    Domain.DLS.set _eval_ctx (Some { ctx_index = idx; ctx_session = session });
    Fun.protect ~finally:(fun () -> Domain.DLS.set _eval_ctx None) (fun () ->
      let result = eval_tantra ~idx ~session k t inputs in
      let raw = as_string result in
      if String.length raw = 0 then None
      else Some { yr_output = []; yr_tantra = name;
                  yr_code = "(via " ^ name ^ ")"; yr_raw_output = raw })

(* ═══════════════════════════════════════════════════════════════════════════
   6. WIRE ENGINE — single Atomic.set replaces 4 forward ref assignments
   ═══════════════════════════════════════════════════════════════════════════ *)

let () =
  Atomic.set _engine {
    eval;
    eval_tantra = (fun k t inputs -> eval_tantra k t inputs);
    eval_pure_op = Kriya_ops.eval_pure_op;
    eval_pipeline_op = eval_pipeline_op;
  };
  register_primitive_arities ()
