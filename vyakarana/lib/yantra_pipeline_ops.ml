(* yantra_pipeline_ops.ml — pipeline and session operations.
   covers: session-bindings, remember-bindings, print,
   and the unknown-op fallback (env VFn / loaded tantra by name).

   returns value option — Some v if op matched, None to fall through.

   dependency: Proof_graph, Yantra_types, Yantra_eval_primitives. *)

open Proof_graph
open Yantra_types
open Yantra_eval_primitives

let eval_pipeline_op (e_eval : proof_graph -> env -> expr -> value)
    (k : proof_graph) (e : env) (op : string) (args : expr list) : value option =
  match op with

  (* session-bindings: _ -> [VBinding ...] from current yantra session *)
  | "session-bindings" ->
    (match !eval_ctx with
     | None -> Some (VList [])
     | Some ctx ->
       Some (VList (List.map (fun b -> VBinding (b.b_name, b.b_value)) ctx.ctx_session.bindings)))

  (* remember-bindings: [VBinding ...] -> ["stored"; name; value; unit; ""] *)
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

  (* print / debug *)
  | "print" ->
    let v = e_eval k e (List.nth args 0) in
    Printf.printf "%s\n%!" (as_string v);
    Some v

  (* unknown operation — try env variable holding a function, then loaded tantra *)
  | _ ->
    (match Hashtbl.find_opt e op with
     | Some (VFn (params, body, captured)) ->
       let env_copy c =
         let e2 = Hashtbl.create (Hashtbl.length c) in
         Hashtbl.iter (fun k v -> Hashtbl.replace e2 k v) c; e2
       in
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
