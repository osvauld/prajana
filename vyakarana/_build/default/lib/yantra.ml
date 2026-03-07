(* yantra.ml — facade: re-exports all yantra split modules.
   provides the entry point (run) and legacy helpers not yet in split modules.
   dependency order: Yantra_types → Yantra_bigram → Yantra_parser →
     Yantra_inverter → Yantra_index → Yantra_resolver →
     Yantra_ops → Yantra_eval_primitives → Yantra_pipeline_ops → Yantra_eval *)

open Proof_graph
open Yantra_resolver   (* chain_step constructors: CForward, CInverse, Direct, Inverse, Chain, NotFound *)

(* ---- re-export split modules ---- *)

include Yantra_types        (* tantra_index, session, binding, value, env, as_float … *)
include Yantra_bigram       (* ytoken *)

(* explicit re-exports from modules that can't be cleanly include'd without
   shadowing each other *)
let parse_expr_string   = Yantra_parser.parse_expr_string
let build_index         = Yantra_index.build_index

let resolve_tantra      = Yantra_resolver.resolve_tantra
let chain_resolve       = Yantra_resolver.chain_resolve

include Yantra_eval_primitives   (* eval_ctx, eval_call, env_copy, last_invoked_tantra … *)

let eval                = Yantra_eval.eval
let eval_tantra         = Yantra_eval.eval_tantra
let print_result        = Yantra_eval.print_result
let run_tantra_by_name  = Yantra_eval.run_tantra_by_name
let run_anuvada_ganana  = Yantra_eval.run_anuvada_ganana
let yantra_tokenise     = Yantra_eval.yantra_tokenise
let new_session         = Yantra_eval.new_session

(* ---- alias table (not yet split) ---- *)

let alias_cache : (string, string) Hashtbl.t = Hashtbl.create 32
let alias_loaded = ref false

let load_aliases (k : proof_graph) : unit =
  if not !alias_loaded then begin
    alias_loaded := true;
    let pairs = Setu.read_shabda k "aliases" in
    List.iter (fun (short, full) ->
      Hashtbl.replace alias_cache short full
    ) pairs
  end

let resolve_alias (k : proof_graph) (name : string) : string =
  load_aliases k;
  match Hashtbl.find_opt alias_cache name with
  | Some full -> full
  | None -> name

(* ---- classification helpers (not yet split) ---- *)

let classify_for_yantra (k : proof_graph) (word : string) : ytoken =
  load_aliases k;
  let alias_hit = if String.length word <= 2 then
    Hashtbl.find_opt alias_cache word
  else None in
  match alias_hit with
  | Some full -> YConcept full
  | None ->
    match Setu.classify_token k word with
    | Setu.Number f    -> YNumber f
    | Setu.Operator op -> YOperator op
    | Setu.Content name -> YConcept name
    | Setu.Grammar v   -> YGrammar v
    | Setu.Article      -> YGrammar Sthita
    | Setu.Unknown w    ->
      match Hashtbl.find_opt alias_cache w with
      | Some full -> YConcept full
      | None -> YUnknown w

let try_bigram_join (k : proof_graph) (n1 : string) (n2 : string)
    (w1 : string) (w2 : string) : string option =
  let joined = n1 ^ "-" ^ n2 in
  match Hashtbl.find_opt k.nodes joined with
  | Some _ -> Some joined
  | None ->
    let joined_raw = w1 ^ "-" ^ w2 in
    if joined_raw <> joined then
      match Hashtbl.find_opt k.nodes joined_raw with
      | Some _ -> Some joined_raw
      | None -> None
    else None

let join_bigrams (k : proof_graph) (tokens : (string * ytoken) list)
    : (string * ytoken) list =
  let rec loop = function
    | [] -> []
    | (w1, YConcept c1) :: (w2, YConcept c2) :: rest ->
      (match try_bigram_join k c1 c2 w1 w2 with
       | Some joined -> (w1 ^ " " ^ w2, YConcept joined) :: loop rest
       | None -> (w1, YConcept c1) :: loop ((w2, YConcept c2) :: rest))
    | (w1, YUnknown u1) :: (w2, YUnknown u2) :: rest ->
      (match try_bigram_join k u1 u2 w1 w2 with
       | Some joined -> (w1 ^ " " ^ w2, YConcept joined) :: loop rest
       | None -> (w1, YUnknown u1) :: loop ((w2, YUnknown u2) :: rest))
    | (w1, YUnknown u1) :: (w2, YConcept c2) :: rest ->
      (match try_bigram_join k u1 c2 w1 w2 with
       | Some joined -> (w1 ^ " " ^ w2, YConcept joined) :: loop rest
       | None -> (w1, YUnknown u1) :: loop ((w2, YConcept c2) :: rest))
    | (w1, YConcept c1) :: (w2, YUnknown u2) :: rest ->
      (match try_bigram_join k c1 u2 w1 w2 with
       | Some joined -> (w1 ^ " " ^ w2, YConcept joined) :: loop rest
       | None -> (w1, YConcept c1) :: loop ((w2, YUnknown u2) :: rest))
    | x :: rest -> x :: loop rest
  in
  loop tokens

(* ---- binding extraction (not yet split) ---- *)

type extraction = {
  ex_bindings : binding list;
  ex_target   : string option;
}

let is_simple_tantra (t : tantra) : bool =
  let generic_names = ["a"; "b"; "c"; "n"; "x"; "base"; "exponent"; "angle";
                        "result"; "arg0"; "arg1"] in
  List.for_all (fun inp -> List.mem inp.tp_name generic_names) t.t_inputs

let is_question_word w =
  w = "find" || w = "solve" || w = "calculate" || w = "compute" ||
  w = "determine" || w = "evaluate"

let is_question_grammar v = v = Drishthanta

let extract_bindings (k : proof_graph) (idx : tantra_index) (session : session)
    (tokens : (string * ytoken) list) : extraction =
  let bindings = ref [] in
  let target = ref None in
  let unbound_concepts = ref [] in

  let rec walk = function
    | [] -> ()
    | (_, YConcept c) :: (_, YGrammar Swarupa) :: (_, YNumber n) :: rest
    | (_, YConcept c) :: (_, YOperator "=") :: (_, YNumber n) :: rest ->
      bindings := { b_name = c; b_value = n; b_unit = None } :: !bindings;
      walk rest
    | (w, YUnknown _) :: (_, YOperator "=") :: (_, YNumber n) :: rest
    | (w, YGrammar _) :: (_, YOperator "=") :: (_, YNumber n) :: rest ->
      let resolved = resolve_alias k w in
      bindings := { b_name = resolved; b_value = n; b_unit = None } :: !bindings;
      walk rest
    | (_, YConcept c) :: (_, YNumber n) :: rest ->
      let is_op_concept =
        let direct = Hashtbl.find_opt idx.by_name c in
        let via_graph = match direct with
          | Some _ -> direct
          | None ->
            let resolved = Setu.resolve k c in
            List.find_map (fun name -> Hashtbl.find_opt idx.by_name name) resolved
        in
        match via_graph with
        | Some t -> is_simple_tantra t
        | None -> false
      in
      if is_op_concept then begin
        unbound_concepts := c :: !unbound_concepts;
        let idx_n = List.length !bindings in
        bindings := { b_name = Printf.sprintf "arg%d" idx_n;
                      b_value = n; b_unit = None } :: !bindings;
        walk rest
      end else begin
        bindings := { b_name = c; b_value = n; b_unit = None } :: !bindings;
        walk rest
      end
    | (_, YConcept c) :: (w, YGrammar v) :: rest
      when is_question_grammar v && w = "when" && !target = None ->
      target := Some c;
      walk rest
    | (w, YGrammar v) :: rest when is_question_grammar v && !target = None ->
      ignore w;
      let rec find_target = function
        | (_, YConcept c) :: rest' -> target := Some c; walk rest'
        | (_, YGrammar _) :: rest' -> find_target rest'
        | other -> walk other
      in
      find_target rest
    | (w, YConcept _) :: rest when is_question_word w && !target = None ->
      let rec find_target = function
        | (_, YConcept c) :: rest' -> target := Some c; walk rest'
        | (_, YGrammar _) :: rest' -> find_target rest'
        | other -> walk other
      in
      find_target rest
    | (_, YConcept c) :: rest ->
      unbound_concepts := c :: !unbound_concepts; walk rest
    | (_, YGrammar _) :: rest -> walk rest
    | (_, YOperator _) :: rest -> walk rest
    | (_, YNumber n) :: rest ->
      let idx_n = List.length !bindings in
      bindings := { b_name = Printf.sprintf "arg%d" idx_n;
                    b_value = n; b_unit = None } :: !bindings;
      walk rest
    | (_, YUnknown _) :: rest -> walk rest
  in
  walk tokens;

  let target =
    match !target with
    | Some _ as t -> t
    | None ->
      let unbound = List.rev !unbound_concepts in
      List.find_map (fun c ->
        if Hashtbl.mem idx.by_name c then Some c
        else if Hashtbl.mem idx.by_output c then Some c
        else
          let resolved = Setu.resolve k c in
          List.find_map (fun name ->
            if Hashtbl.mem idx.by_name name then Some name
            else if Hashtbl.mem idx.by_output name then Some name
            else None
          ) resolved
      ) unbound
  in
  let bound_names = List.map (fun b -> b.b_name) !bindings in
  let session_additions = List.filter (fun sb ->
    not (List.mem sb.b_name bound_names)
  ) session.bindings in
  { ex_bindings = List.rev !bindings @ session_additions;
    ex_target = target }

(* ---- _graph_ref: legacy handle used by bin ---- *)

let _graph_ref : proof_graph option ref = ref None

(* ---- run: main pipeline entry point ---- *)

let run (k : proof_graph) (idx : tantra_index) (session : session)
    (sentence : string) : yantra_result option =
  match run_anuvada_ganana k idx session sentence with
  | Some _ as result ->
    session.history <- sentence :: session.history;
    result
  | None ->
    let words = yantra_tokenise sentence in
    let words = List.filter (fun w -> String.length (String.trim w) > 0) words in
    let has_number = List.exists (fun w ->
      match float_of_string_opt w with Some _ -> true | None -> false
    ) words in
    if not has_number then None
    else begin
      let classified = List.map (fun w -> (w, classify_for_yantra k w)) words in
      let classified = join_bigrams k classified in
      let extraction = extract_bindings k idx session classified in
      match extraction.ex_target, extraction.ex_bindings with
      | Some target, bindings when bindings <> [] ->
        let target_is_bound = List.exists (fun b -> b.b_name = target) bindings in
        if target_is_bound then begin
          let buf = Buffer.create 64 in
          List.iter (fun b ->
            session.bindings <- b
              :: List.filter (fun sb -> sb.b_name <> b.b_name) session.bindings;
            Buffer.add_string buf
              (Printf.sprintf "%s is %g (remembered).\n" b.b_name b.b_value)
          ) bindings;
          session.history <- sentence :: session.history;
          Some { yr_output = []; yr_tantra = ""; yr_code = "(stored)";
                 yr_raw_output = String.trim (Buffer.contents buf) }
        end else begin
          let resolution = resolve_tantra k idx bindings target in
          match resolution with
          | Direct (t, assignments) ->
            let input_values = List.map (fun (n, f) -> (n, VFloat f)) assignments in
            let result = eval_tantra ~idx ~session k t input_values in
            let output = match t.t_returns with
              | [ret] -> [(ret.tp_name, as_float result)]
              | rets ->
                let values = as_list result in
                List.mapi (fun i ret ->
                  let v = if i < List.length values then List.nth values i
                          else VNone in
                  (ret.tp_name, as_float v)
                ) rets
            in
            session.history <- sentence :: session.history;
            last_invoked_tantra := t.t_name;
            Some { yr_output = output; yr_tantra = t.t_name;
                   yr_code = "(direct)"; yr_raw_output = "" }
          | Inverse (t, tgt, plan, known_values) ->
            let env = new_env () in
            List.iter (fun (n, f) -> Hashtbl.replace env n (VFloat f)) known_values;
            List.iter (fun (n, rhs) ->
              Hashtbl.replace env n (eval k env rhs)
            ) plan;
            let result_v = match Hashtbl.find_opt env tgt with
              | Some v -> as_float v | None -> 0.0 in
            session.history <- sentence :: session.history;
            last_invoked_tantra := t.t_name ^ " (inverted)";
            Some { yr_output = [(tgt, result_v)];
                   yr_tantra = t.t_name ^ " (inverted)";
                   yr_code = "(inverse)"; yr_raw_output = "" }
          | Chain steps ->
            let final_bindings = ref bindings in
            let tantra_names = ref [] in
            List.iter (fun step ->
              match step with
              | CForward (t, assignments) ->
                let input_values = List.map (fun (n, f) -> (n, VFloat f)) assignments in
                let result = eval_tantra ~idx ~session k t input_values in
                (match t.t_returns with
                 | [ret] ->
                   let v = as_float result in
                   final_bindings := { b_name = ret.tp_name; b_value = v;
                                       b_unit = ret.tp_unit } :: !final_bindings;
                   if t.t_name <> ret.tp_name then
                     final_bindings := { b_name = t.t_name; b_value = v;
                                         b_unit = ret.tp_unit } :: !final_bindings
                 | rets ->
                   let values = as_list result in
                   List.iteri (fun i ret ->
                     let v = if i < List.length values
                             then as_float (List.nth values i) else 0.0 in
                     final_bindings := { b_name = ret.tp_name; b_value = v;
                                         b_unit = ret.tp_unit } :: !final_bindings
                   ) rets);
                tantra_names := t.t_name :: !tantra_names
              | CInverse (t, _tgt, _plan, _kv) ->
                tantra_names := (t.t_name ^ "(inv)") :: !tantra_names
            ) steps;
            let target_value = match List.find_opt (fun b ->
              b.b_name = target
            ) !final_bindings with
            | Some b -> b.b_value | None -> 0.0 in
            let chain_name = String.concat " \xe2\x86\x92 " (List.rev !tantra_names) in
            session.history <- sentence :: session.history;
            last_invoked_tantra := chain_name;
            Some { yr_output = [(target, target_value)];
                   yr_tantra = chain_name ^ " (chain)";
                   yr_code = "(chain)"; yr_raw_output = "" }
          | NotFound _ -> None
        end
      | None, (_ :: _ as bindings) ->
        let buf = Buffer.create 64 in
        List.iter (fun b ->
          session.bindings <- b
            :: List.filter (fun sb -> sb.b_name <> b.b_name) session.bindings;
          Buffer.add_string buf
            (Printf.sprintf "%s is %g (remembered).\n" b.b_name b.b_value)
        ) bindings;
        session.history <- sentence :: session.history;
        Some { yr_output = []; yr_tantra = ""; yr_code = "(stored)";
               yr_raw_output = String.trim (Buffer.contents buf) }
      | _ -> None
    end
