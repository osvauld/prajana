(* yantra_pipeline_ops.ml — pipeline and session operations.
   covers: tokenise, classify, session-bindings, remember-bindings,
   resolve-direct, resolve-inverse, resolve-chain, resolve-reason,
   execute-plan, print, and the unknown-op fallback.

   uses forward references from Yantra_eval_primitives (eval_ctx, _eval_ref,
   _eval_tantra_ref, etc.) and Yantra_resolver types.

   returns value option — Some v if op matched, None to fall through.

   dependency: Proof_graph, Yantra_types, Yantra_resolver,
               Yantra_eval_primitives, Setu. *)

open Proof_graph
open Yantra_types
open Yantra_inverter
open Yantra_resolver
open Yantra_eval_primitives

let eval_pipeline_op (e_eval : proof_graph -> env -> expr -> value)
    (k : proof_graph) (e : env) (op : string) (args : expr list) : value option =
  match op with

  (* tokenise: string → [string] *)
  | "tokenise" ->
    let s = as_string (e_eval k e (List.nth args 0)) in
    let words = !_yantra_tokenise_ref s in
    let words = List.filter (fun w -> String.length (String.trim w) > 0) words in
    Some (VList (List.map (fun w -> VString w) words))

  (* classify: string → [word, kind, resolved] *)
  | "classify" ->
    let word = as_string (e_eval k e (List.nth args 0)) in
    let classify_one w =
      match float_of_string_opt w with
      | Some f -> VList [VString w; VString "number"; VFloat f]
      | None ->
        if w = "+" || w = "-" || w = "*" || w = "/" || w = "=" then
          VList [VString w; VString "operator"; VString w]
        else
          (match !eval_ctx with
           | Some ctx ->
             (match Hashtbl.find_opt ctx.ctx_index.by_name "setu-classify-token" with
              | Some t ->
                let result = !_eval_tantra_ref k t [("word", VString w)] in
                (match as_list result with
                 | [VString kind; VString resolved] ->
                   VList [VString w; VString kind; VString resolved]
                 | _ -> VList [VString w; VString "unknown"; VString "asprista"])
              | None -> VList [VString w; VString "unknown"; VString "asprista"])
           | None -> VList [VString w; VString "unknown"; VString "asprista"])
    in
    Some (classify_one word)

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
       let bindings = List.filter_map (function
         | VBinding (n, f) -> Some { b_name = n; b_value = f; b_unit = None }
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

  (* resolve-direct: target x extraction -> [[forward-step], ...] candidates *)
  | "resolve-direct" ->
    let target = as_string (e_eval k e (List.nth args 0)) in
    let bindings_v = as_list (e_eval k e (List.nth args 1)) in
    (match !eval_ctx with
     | None -> Some (VList [])
     | Some ctx ->
       let bindings = List.filter_map (fun v ->
         match v with
         | VBinding (n, f) -> Some { b_name = n; b_value = f; b_unit = None }
         | _ -> None
       ) bindings_v in
       let target = match !_resolve_concept_to_tantra_ref k ctx.ctx_index target with
         | Some resolved -> resolved
         | None -> target in
       let target_canon = Setu.resolve_to_canonical k target in
       let bindings = List.filter (fun b ->
         let bcanon = Setu.resolve_to_canonical k b.b_name in
         not (b.b_name = target || b.b_name = target_canon || bcanon = target || bcanon = target_canon)
       ) bindings in
       let candidates =
         (match Hashtbl.find_opt ctx.ctx_index.by_name target with Some t -> [t] | None -> []) @
         (match Hashtbl.find_opt ctx.ctx_index.by_output target with Some l -> l | None -> []) @
         (let resolved = Setu.resolve k target in
          List.concat_map (fun name ->
            match Hashtbl.find_opt ctx.ctx_index.by_output name with Some l -> l | None -> []
          ) resolved)
       in
       let seen = Hashtbl.create 16 in
       let candidates = List.filter (fun t ->
         if Hashtbl.mem seen t.t_name then false
         else (Hashtbl.replace seen t.t_name true; true)
       ) candidates in
       let mk_forward_step (t : tantra) (assignments : (string * float) list) : value =
         let assign_vs = List.map (fun (n, f) -> VBinding (n, f)) assignments in
         VList [
           VPair ("kind", VString "forward");
           VPair ("tantra", VString t.t_name);
           VPair ("assignments", VList assign_vs)
         ]
       in
       let step_candidates = List.filter_map (fun t ->
         match try_match_inputs k t bindings ctx.ctx_index with
         | Some assignments -> Some (VList [mk_forward_step t assignments])
         | None -> None
       ) candidates in
       Some (VList step_candidates))

  (* resolve-inverse: target x extraction -> [[inverse-step], ...] candidates *)
  | "resolve-inverse" ->
    let target = as_string (e_eval k e (List.nth args 0)) in
    let bindings_v = as_list (e_eval k e (List.nth args 1)) in
    (match !eval_ctx with
     | None -> Some (VList [])
     | Some ctx ->
       let bindings = List.filter_map (fun v ->
         match v with
         | VBinding (n, f) -> Some { b_name = n; b_value = f; b_unit = None }
         | _ -> None
       ) bindings_v in
       let target = match !_resolve_concept_to_tantra_ref k ctx.ctx_index target with
         | Some resolved -> resolved
         | None -> target in
       let names_match (a : string) (b : string) : bool =
         a = b ||
         let ap = String.split_on_char '-' a in
         let bp = String.split_on_char '-' b in
         List.exists (fun p -> String.length p > 2 && List.mem p bp) ap ||
         List.exists (fun p -> String.length p > 2 && List.mem p ap) bp ||
         let ca = Setu.resolve_to_canonical k a in
         let cb = Setu.resolve_to_canonical k b in
         ca = cb || ca = b || a = cb
       in
       let inverse_candidates =
         match Hashtbl.find_opt ctx.ctx_index.by_input target with
         | Some l when l <> [] -> l
         | _ ->
           List.filter (fun t ->
             List.exists (fun inp ->
               names_match inp.tp_name target || names_match inp.tp_canonical target
             ) t.t_inputs
           ) !(ctx.ctx_index.all_tantras)
       in
       let mk_inverse_step (t : tantra) (tgt : string) (known_values : (string * float) list) : value =
         let kv_vs = List.map (fun (n, f) -> VBinding (n, f)) known_values in
         VList [
           VPair ("kind", VString "inverse");
           VPair ("tantra", VString t.t_name);
           VPair ("target", VString tgt);
           VPair ("known-values", VList kv_vs)
         ]
       in
       let step_candidates = List.filter_map (fun t ->
         let target_inp = List.find_opt (fun inp ->
           inp.tp_name = target || inp.tp_canonical = target ||
           names_match inp.tp_name target || names_match inp.tp_canonical target
         ) t.t_inputs in
         match target_inp with
         | None -> None
         | Some target_inp ->
           let target_inp_name = target_inp.tp_name in
           let output_bound = List.find_map (fun ret ->
             List.find_map (fun b ->
               if b.b_name = ret.tp_name || b.b_name = t.t_name
                  || names_match b.b_name ret.tp_name
                  || names_match b.b_name t.t_name
                  || (match ret.tp_unit with
                      | Some unit_name ->
                        let yuktas = Setu.yukta_of k b.b_name in
                        List.mem unit_name yuktas ||
                        (String.length b.b_name >= String.length unit_name &&
                         String.sub b.b_name 0 (String.length unit_name) = unit_name)
                      | None -> false)
               then Some (ret.tp_name, b.b_value)
               else None
             ) bindings
           ) t.t_returns in
           (match output_bound with
            | None -> None
            | Some (result_name, result_value) ->
              let other_inputs = List.filter (fun inp -> inp.tp_name <> target_inp_name) t.t_inputs in
              let other_values = List.filter_map (fun inp ->
                match List.find_opt (fun b -> names_match b.b_name inp.tp_name) bindings with
                | Some b -> Some (inp.tp_name, b.b_value)
                | None -> Hashtbl.find_opt ctx.ctx_index.constants inp.tp_name |> Option.map (fun v -> (inp.tp_name, v))
              ) other_inputs in
              if List.length other_values <> List.length other_inputs then None
              else
                let known_values = (result_name, result_value) :: other_values in
                let ret_binding_name = match List.find_opt (fun (name, _) ->
                  name = result_name || List.exists (fun ret -> ret.tp_name = name) t.t_returns
                ) t.t_lets with
                | Some (name, _) -> name
                | None -> result_name in
                let known_names = List.map fst known_values in
                let known_with_inputs = known_names @ List.map (fun inp -> inp.tp_name) other_inputs in
                match invert_chain k t.t_lets known_with_inputs target_inp_name ret_binding_name with
                | Some _plan -> Some (VList [mk_inverse_step t target known_values])
                | None -> None)
       ) inverse_candidates in
       Some (VList step_candidates))

  (* resolve-chain: target x extraction x max-depth -> [step, ...] best chain *)
  | "resolve-chain" ->
    let target = as_string (e_eval k e (List.nth args 0)) in
    let bindings_v = as_list (e_eval k e (List.nth args 1)) in
    let max_depth = int_of_float (as_float (e_eval k e (List.nth args 2))) in
    (match !eval_ctx with
     | None -> Some (VList [])
     | Some ctx ->
       let bindings = List.filter_map (fun v ->
         match v with
         | VBinding (n, f) -> Some { b_name = n; b_value = f; b_unit = None }
         | _ -> None
       ) bindings_v in
       let target = match !_resolve_concept_to_tantra_ref k ctx.ctx_index target with
         | Some resolved -> resolved
         | None -> target in
       let target_canon = Setu.resolve_to_canonical k target in
       let bindings = List.filter (fun b ->
         let bcanon = Setu.resolve_to_canonical k b.b_name in
         not (b.b_name = target || b.b_name = target_canon || bcanon = target || bcanon = target_canon)
       ) bindings in
       let mk_forward_step (t : tantra) (assignments : (string * float) list) : value =
         let assign_vs = List.map (fun (n, f) -> VBinding (n, f)) assignments in
         VList [
           VPair ("kind", VString "forward");
           VPair ("tantra", VString t.t_name);
           VPair ("assignments", VList assign_vs)
         ]
       in
       let mk_inverse_step (t : tantra) (tgt : string) (known_values : (string * float) list) : value =
         let kv_vs = List.map (fun (n, f) -> VBinding (n, f)) known_values in
         VList [
           VPair ("kind", VString "inverse");
           VPair ("tantra", VString t.t_name);
           VPair ("target", VString tgt);
           VPair ("known-values", VList kv_vs)
         ]
       in
       Some (match chain_resolve ~max_depth k ctx.ctx_index bindings target with
        | None -> VList []
        | Some steps ->
          VList (List.map (function
            | CForward (t, assignments) -> mk_forward_step t assignments
            | CInverse (t, tgt, _plan, kv) -> mk_inverse_step t tgt kv
          ) steps)))

  (* resolve-reason: target x extraction -> detailed reason string *)
  | "resolve-reason" ->
    let target = as_string (e_eval k e (List.nth args 0)) in
    let bindings_v = as_list (e_eval k e (List.nth args 1)) in
    (match !eval_ctx with
     | None -> Some (VString "missing eval context")
     | Some ctx ->
       let bindings = List.filter_map (fun v ->
         match v with
         | VBinding (n, f) -> Some { b_name = n; b_value = f; b_unit = None }
         | _ -> None
       ) bindings_v in
       let target = match !_resolve_concept_to_tantra_ref k ctx.ctx_index target with
         | Some resolved -> resolved
         | None -> target in
       Some (match !_resolve_tantra_ref k ctx.ctx_index bindings target with
        | NotFound reason -> VString reason
        | _ -> VString "plan candidates exist"))

  (* execute-plan: pair-record planner output -> result payload *)
  | "execute-plan" ->
    let plan_v = e_eval k e (List.nth args 0) in
    let items = as_list plan_v in
    let mode = match pair_field items "mode" with
      | Some v -> as_string v
      | None -> "" in
    let steps_v = match pair_field items "steps" with
      | Some v -> as_list v
      | None -> [] in
    let target = match pair_field items "target" with
      | Some v -> as_string v
      | None -> "" in
    let reason = match pair_field items "reason" with
      | Some v -> as_string v
      | None -> "plan rejected" in
    (match mode with
     | "error" ->
       Some (VList [VString "error"; VString reason; VFloat 0.0; VString ""; VString ""])
     | _ ->
       (match !eval_ctx with
        | None ->
          Some (VList [VString "error"; VString "missing eval context"; VFloat 0.0; VString ""; VString ""])
        | Some ctx ->
          let step_names = ref [] in
          let run_forward tantra_name assignments =
            match Hashtbl.find_opt ctx.ctx_index.by_name tantra_name with
            | None -> ()
            | Some t ->
              let input_values = List.map (fun (n, f) -> (n, VFloat f)) assignments in
              let result = !_eval_tantra_ref k t input_values in
              (match t.t_returns with
               | [ret] ->
                 let f = as_float result in
                 (* store under the tantra name — the canonical output key.
                    internal return variable names (e.g. "ke" for kinetic-energy)
                    are not stored to prevent stale values from polluting
                    subsequent chain resolutions. *)
                 ctx.ctx_session.bindings <-
                   { b_name = t.t_name; b_value = f; b_unit = ret.tp_unit }
                   :: List.filter (fun b -> b.b_name <> t.t_name) ctx.ctx_session.bindings
               | rets ->
                 let values = as_list result in
                 List.iteri (fun i ret ->
                   let v = if i < List.length values then List.nth values i else VNone in
                   let f = as_float v in
                   ctx.ctx_session.bindings <-
                     { b_name = ret.tp_name; b_value = f; b_unit = ret.tp_unit }
                     :: List.filter (fun b -> b.b_name <> ret.tp_name) ctx.ctx_session.bindings
                 ) rets);
              step_names := t.t_name :: !step_names
          in
          let run_inverse tantra_name tgt known_values =
            match Hashtbl.find_opt ctx.ctx_index.by_name tantra_name with
            | None -> ()
            | Some t ->
              let target_inp_name = match List.find_opt (fun inp ->
                inp.tp_name = tgt ||
                let tp = String.split_on_char '-' inp.tp_name in
                let tgtp = String.split_on_char '-' tgt in
                List.exists (fun p -> List.mem p tgtp) tp ||
                List.exists (fun p -> List.mem p tp) tgtp
              ) t.t_inputs with
              | Some inp -> inp.tp_name
              | None -> tgt
              in
              let ret_name = match t.t_returns with
                | [ret] -> ret.tp_name | _ -> "result" in
              let ret_binding_name = match List.find_opt (fun (name, _) ->
                name = ret_name || List.exists (fun ret -> ret.tp_name = name) t.t_returns
              ) t.t_lets with
              | Some (name, _) -> name
              | None -> ret_name
              in
              let known_names = List.map fst known_values in
              (match invert_chain k t.t_lets known_names target_inp_name ret_binding_name with
               | Some plan ->
                 let env = new_env () in
                 List.iter (fun (n, f) -> Hashtbl.replace env n (VFloat f)) known_values;
                 List.iter (fun (n, rhs) ->
                   let v = e_eval k env rhs in
                   Hashtbl.replace env n v
                 ) plan;
                 let f = match Hashtbl.find_opt env target_inp_name with
                   | Some v -> as_float v
                   | None -> 0.0 in
                 let unit_opt = match List.find_opt (fun inp -> inp.tp_name = target_inp_name) t.t_inputs with
                   | Some inp -> inp.tp_unit
                   | None -> None in
                 ctx.ctx_session.bindings <-
                   { b_name = tgt; b_value = f; b_unit = unit_opt }
                   :: List.filter (fun b -> b.b_name <> tgt) ctx.ctx_session.bindings
               | None -> ());
              step_names := t.t_name :: !step_names
          in
          List.iter (fun step_v ->
            let step_items = as_list step_v in
            let kind = match pair_field step_items "kind" with
              | Some v -> as_string v
              | None -> "" in
            match kind with
            | "forward" ->
              let tantra_name = match pair_field step_items "tantra" with
                | Some v -> as_string v
                | None -> "" in
              let assignments = match pair_field step_items "assignments" with
                | Some v -> List.filter_map (function VBinding (n, f) -> Some (n, f) | _ -> None) (as_list v)
                | None -> [] in
              run_forward tantra_name assignments
            | "inverse" ->
              let tantra_name = match pair_field step_items "tantra" with
                | Some v -> as_string v
                | None -> "" in
              let tgt = match pair_field step_items "target" with
                | Some v -> as_string v
                | None -> target in
              let known_values = match pair_field step_items "known-values" with
                | Some v -> List.filter_map (function VBinding (n, f) -> Some (n, f) | _ -> None) (as_list v)
                | None -> [] in
              run_inverse tantra_name tgt known_values
            | _ -> ()
          ) steps_v;
          let result_name = if String.length target > 0 then target else
            match ctx.ctx_session.last_result with
            | (n, _) :: _ -> n
            | [] -> "result"
          in
          let result_binding = List.find_opt (fun b -> b.b_name = result_name) ctx.ctx_session.bindings in
          let result_value = match result_binding with
            | Some b -> b.b_value
            | None ->
              (match ctx.ctx_session.last_result with
               | (_, v) :: _ -> v
               | [] -> 0.0) in
          let unit_str = match result_binding with
            | Some { b_unit = Some u; _ } -> u
            | _ -> "" in
          let names = List.rev !step_names in
          let attribution = match names with
            | [] -> "planner"
            | [n] -> n
            | _ ->
              let rev = List.rev names in
              let last = List.hd rev in
              let rest = List.rev (List.tl rev) in
              String.concat ", " rest ^ " and " ^ last
          in
          last_invoked_tantra := attribution;
          ctx.ctx_session.last_result <- [(result_name, result_value)];
          Some (VList [VString "result"; VString result_name; VFloat result_value; VString unit_str; VString attribution])))

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
