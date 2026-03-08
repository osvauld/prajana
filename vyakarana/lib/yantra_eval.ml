(* yantra_eval.ml — core evaluator and pipeline entry points.
   contains eval: the recursive expression evaluator (Lit, Var, LetIn,
   Lambda, Cond, Call). all primitive operations live in
   yantra_eval_primitives.ml; the mutual recursion is closed here by
   wiring _eval_ref at module init.

   dependency: Proof_graph, Yantra_types, Yantra_resolver, Yantra_ops,
               Yantra_pipeline_ops, Yantra_eval_primitives. *)

open Yantra_types
open Yantra_resolver
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
            | _ -> VString v)
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

(* ---- parse output back to (name, value) pairs ---- *)
(* formats: "displacement = 39.600000" or just "8.000000" *)
let parse_output (raw : string) : (string * float) list =
  let lines = String.split_on_char '\n' raw
    |> List.map String.trim
    |> List.filter (fun s -> String.length s > 0) in
  List.filter_map (fun line ->
    match String.index_opt line '=' with
    | Some eq ->
      let name = String.trim (String.sub line 0 eq) in
      let rest = String.trim (String.sub line (eq + 1) (String.length line - eq - 1)) in
      let num_str = match String.index_opt rest ' ' with
        | Some sp -> String.sub rest 0 sp
        | None -> rest
      in
      (match float_of_string_opt num_str with
       | Some f -> Some (name, f)
       | None -> None)
    | None ->
      (match float_of_string_opt (String.trim line) with
       | Some f -> Some ("result", f)
       | None -> None)
  ) lines

(* ---- resolve a concept name to a tantra name via graph abheda walk ---- *)
let resolve_concept_to_tantra (k : proof_graph) (idx : tantra_index) (concept : string) : string option =
  if Hashtbl.mem idx.by_name concept then Some concept
  else if Hashtbl.mem idx.by_output concept then Some concept
  else if Hashtbl.mem idx.by_input concept then Some concept
  else begin
    let resolved = Setu.resolve k concept in
    List.find_map (fun name ->
      if Hashtbl.mem idx.by_name name then Some name
      else if Hashtbl.mem idx.by_output name then Some name
      else if Hashtbl.mem idx.by_input name then Some name
      else None
    ) resolved
  end

let new_session () : session =
  { bindings = []; last_result = []; history = []; context_seeds = [] }

(* ---- yantra tokeniser: preserve floats and hyphenated words ---- *)
let yantra_tokenise (s : string) : string list =
  let buf = Buffer.create 16 in
  let tokens = ref [] in
  let flush () =
    if Buffer.length buf > 0 then begin
      tokens := Buffer.contents buf :: !tokens;
      Buffer.clear buf
    end
  in
  let len = String.length s in
  let i = ref 0 in
  while !i < len do
    let c = s.[!i] in
    match c with
    | ' ' | '\t' | '\n' | ',' | '?' | '!' | ';' | '(' | ')' ->
      flush (); incr i
    | '.' ->
      let prev_digit = Buffer.length buf > 0 &&
        let contents = Buffer.contents buf in
        let last = contents.[String.length contents - 1] in
        last >= '0' && last <= '9' in
      let next_digit = !i + 1 < len && s.[!i + 1] >= '0' && s.[!i + 1] <= '9' in
      if prev_digit && next_digit then begin
        Buffer.add_char buf '.'; incr i
      end else begin
        flush (); incr i
      end
    | ':' -> flush (); incr i
    | '+' | '*' | '/' | '=' ->
      flush ();
      tokens := String.make 1 c :: !tokens;
      incr i
    | '-' ->
      let prev_alpha = Buffer.length buf > 0 &&
        let contents = Buffer.contents buf in
        let last = contents.[String.length contents - 1] in
        (last >= 'a' && last <= 'z') || (last >= 'A' && last <= 'Z') in
      let next_alpha = !i + 1 < len &&
        let nc = s.[!i + 1] in
        (nc >= 'a' && nc <= 'z') || (nc >= 'A' && nc <= 'Z') in
      if prev_alpha && next_alpha then begin
        Buffer.add_char buf '-'; incr i
      end else if Buffer.length buf = 0 && !i + 1 < len &&
                  s.[!i + 1] >= '0' && s.[!i + 1] <= '9' then begin
        Buffer.add_char buf '-'; incr i
      end else begin
        flush ();
        tokens := "-" :: !tokens;
        incr i
      end
    | c ->
      Buffer.add_char buf c;
      incr i
  done;
  flush ();
  (* lowercase multi-char tokens but preserve case on single-char tokens
     (physics convention: V = voltage, v = velocity, F = force, f = frequency) *)
  List.rev_map (fun t ->
    if String.length t > 1 then String.lowercase_ascii t
    else t
  ) !tokens

(* ---- wire up forward references ---- *)
(* connects the primitives module to the functions defined here *)
let () =
  _eval_ref := eval;
  _yantra_tokenise_ref := yantra_tokenise;
  _resolve_concept_to_tantra_ref := resolve_concept_to_tantra;
  _resolve_tantra_ref := resolve_tantra;
  _eval_tantra_ref := (fun k t inputs -> eval_tantra k t inputs);
  _eval_chain_ref := eval;
  _eval_tantra_chain_ref := (fun k t inputs -> eval_tantra k t inputs);
  _eval_pure_op_raw := eval_pure_op;
  _eval_pipeline_op_raw := eval_pipeline_op;
  (* register arities for built-in primitives not derived from graph nodes *)
  Yantra_parser.register_graph_op_arity "all-edges"    (-1);  (* variadic → Call("all-edges",[]) *)
  Yantra_parser.register_graph_op_arity "sum"           1;   (* sum [list] *)
  Yantra_parser.register_graph_op_arity "frequencies"   1;   (* frequencies [list] → [[val,count],...] *)
  Yantra_parser.register_graph_op_arity "starts-with"   2;   (* starts-with string prefix → bool *)
  Yantra_parser.register_graph_op_arity "member"        2    (* member value list → bool *)

(* ---- run anuvada-ganana: the meta-tantra pipeline ---- *)
let run_anuvada_ganana (k : proof_graph) (idx : tantra_index) (session : session)
    (sentence : string) : yantra_result option =
  match Hashtbl.find_opt idx.by_name "anuvada-ganana" with
  | None -> None
  | Some ag ->
    let result = eval_tantra ~idx ~session k ag
      [("sentence", VString sentence)] in
    let raw = as_string result in
    if String.length raw = 0 then
      None
    else begin
      let tantra_name = if String.length !last_invoked_tantra > 0 then
        !last_invoked_tantra else "anuvada-ganana" in
      Some { yr_output = []; yr_tantra = tantra_name;
             yr_code = "(via anuvada-ganana)"; yr_raw_output = raw }
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
