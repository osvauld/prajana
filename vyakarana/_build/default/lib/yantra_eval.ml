(* yantra_eval.ml — core evaluator and pipeline entry points.
   contains eval: the recursive expression evaluator (Lit, Var, LetIn,
   Lambda, Cond, Call). all primitive operations live in
   yantra_eval_primitives.ml; the mutual recursion is closed here by
   wiring _eval_ref at module init.

   dependency: Proof_graph, Yantra_types, Yantra_ops,
               Yantra_pipeline_ops, Yantra_eval_primitives. *)

open Yantra_types
open Yantra_eval_primitives
open Yantra_ops
open Yantra_pipeline_ops

(* ---- core evaluator ---- *)

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
         (* try as a zero-input tantra (constant like gravity, pi, etc.) *)
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

  | Scan (list_expr, state_decls, branches) ->
    eval_scan k e list_expr state_decls branches

(* ---- eval_from: direct evaluation of from/where/collect ---- *)
and eval_from (k : proof_graph) (e : env) (list_expr : expr)
    (pat_names : string list) (guards : expr list) (collect_expr : expr) : value =
  let items = as_list (eval k e list_expr) in
  let n_pat = List.length pat_names in
  let result = ref [] in
  List.iter (fun item ->
    let item_list = as_list item in
    (* bind pattern names *)
    let sub_env = env_copy e in
    List.iteri (fun i name ->
      let v = if i < List.length item_list then List.nth item_list i else VNone in
      Hashtbl.replace sub_env name v
    ) pat_names;
    (* "_it" binds the whole current item — used by simple | collect expressions *)
    Hashtbl.replace sub_env "_it" item;
    ignore n_pat;
    (* check all guards *)
    let pass = List.for_all (fun g -> as_bool (eval k sub_env g)) guards in
    if pass then begin
      let collected = eval k sub_env collect_expr in
      result := collected :: !result
    end
  ) items;
  VList (List.rev !result)

(* ---- eval_scan: direct evaluation of scan/with/when/emit ---- *)
and eval_scan (k : proof_graph) (e : env) (list_expr : expr)
    (state_decls : (string * expr) list) (branches : scan_branch list) : value =
  let items = as_list (eval k e list_expr) in
  (* mutable state *)
  let state = Hashtbl.create 16 in
  List.iter (fun (name, init_expr) ->
    Hashtbl.replace state name (eval k e init_expr)
  ) state_decls;
  let output = ref [] in

  (* execute a list of scan_stmts *)
  let rec exec_stmts (sub_env : env) (stmts : scan_stmt list) : unit =
    List.iter (fun stmt ->
      match stmt with
      | SEmit expr ->
        let v = eval k sub_env expr in
        (* emit triple → re-emit current [word, edge, obj] *)
        let item = match v with
          | VString "triple" ->
            let w = try Hashtbl.find sub_env "word" with Not_found -> VNone in
            let e' = try Hashtbl.find sub_env "edge" with Not_found -> VNone in
            let o = try Hashtbl.find sub_env "obj" with Not_found -> VNone in
            VList [w; e'; o]
          | _ -> v
        in
        output := item :: !output
      | SSkip -> ()   (* suppress emission of current triple — no-op *)
      | SSet (var, expr) ->
        let v = eval k sub_env expr in
        Hashtbl.replace state var v;
        Hashtbl.replace sub_env var v
      | SClear var ->
        Hashtbl.replace state var (VString "");
        Hashtbl.replace sub_env var (VString "")
      | SLet (name, expr) ->
        let v = eval k sub_env expr in
        Hashtbl.replace sub_env name v
      | SWhen (guard, then_body, else_body) ->
        if as_bool (eval k sub_env guard) then
          exec_stmts sub_env then_body
        else
          exec_stmts sub_env else_body
    ) stmts
  in

  List.iter (fun item ->
    let item_list = as_list item in
    let sub_env = env_copy e in
    Hashtbl.iter (fun k v -> Hashtbl.replace sub_env k v) state;
    let word = if List.length item_list > 0 then List.nth item_list 0 else VNone in
    let edge = if List.length item_list > 1 then List.nth item_list 1 else VNone in
    let obj  = if List.length item_list > 2 then List.nth item_list 2 else VNone in
    Hashtbl.replace sub_env "word" word;
    Hashtbl.replace sub_env "edge" edge;
    Hashtbl.replace sub_env "obj" obj;
    Hashtbl.replace sub_env "triple" (VList [word; edge; obj]);

    let matched = ref false in
    List.iter (fun branch ->
      if not !matched then begin
        match branch.sb_guard with
        | None ->
          matched := true;
          exec_stmts sub_env branch.sb_body
        | Some guard ->
          if as_bool (eval k sub_env guard) then begin
            matched := true;
            exec_stmts sub_env branch.sb_body
          end
      end
    ) branches;
    List.iter (fun (name, _) ->
      match Hashtbl.find_opt sub_env name with
      | Some v -> Hashtbl.replace state name v
      | None -> ()
    ) state_decls
  ) items;
  VList (List.rev !output)

(* ---- evaluate a full tantra using the internal evaluator ---- *)
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
     | Some v -> v
     | None -> VNone)
  | rets ->
    VList (List.filter_map (fun ret ->
      Hashtbl.find_opt e ret.tp_name
    ) rets)
  in
  eval_ctx := prev_ctx;
  result

let new_session () : session =
  { bindings = []; last_result = []; history = []; context_seeds = [] }

(* ---- with_eval_ctx: exception-safe eval_ctx set/restore ----
   Before (15+ occurrences in socket.ml, always three lines):
     eval_ctx := Some { ctx_index = idx; ctx_session = ses };
     (try let r = f () in eval_ctx := None; r
      with exn -> eval_ctx := None; default)
   After:
     with_eval_ctx idx ses f ~default

   Restores the previous context (not just None) for safe re-entrance. *)
let with_eval_ctx (idx : tantra_index) (ses : session) (f : unit -> 'a) ~(default : 'a) : 'a =
  let prev = !eval_ctx in
  eval_ctx := Some { ctx_index = idx; ctx_session = ses };
  let r =
    try let v = f () in eval_ctx := prev; v
    with _ -> eval_ctx := prev; default
  in
  r

(* ---- wire up forward references ---- *)
let () =
  _eval_ref := eval;
  _eval_tantra_ref := (fun k t inputs -> eval_tantra k t inputs);
  _eval_pure_op_raw := eval_pure_op;
  _eval_pipeline_op_raw := eval_pipeline_op;
  register_primitive_arities ()

(* ---- run anuvada-ganana: the meta-tantra pipeline ---- *)
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
  | None ->
    (* fallback to anuvada-ganana if session-anuvada not loaded *)
    run_anuvada_ganana k idx session sentence
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

(* ---- print a yantra result ---- *)
let print_result (r : yantra_result) : unit =
  if String.length r.yr_raw_output > 0 then
    Printf.printf "%s\n%!" r.yr_raw_output
  else begin
    List.iter (fun (name, value) ->
      if name = "result" then
        Printf.printf "%g\n" value
      else
        Printf.printf "%s = %g\n" name value
    ) r.yr_output;
    if List.length r.yr_output > 0 then
      Printf.printf "\n  tantra: %s\n%!" r.yr_tantra
  end

(* ---- run a tantra by name with explicit inputs ---- *)
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
