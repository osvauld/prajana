(* yantra_expr_parser.ml — parse_expr: tokens → expr.
   expression parser for tantra let-block lines.
   handles: literals, variables, function calls (fixed/variadic arity),
   cond chains, lambda (fn) with destructuring, let-in chains, list literals,
   from/where/collect, scan/with/when/emit. *)

open Yantra_types

(* ---- infix/postfix operators --------------------------------------------
   After parsing a primary expression we check for:
     X is Y          → eq X Y
     X is not Y      → neq X Y
     X is empty      → eq (length X) 0
     X is not empty  → gt (length X) 0
     X exists        → exists X
   These are lower precedence than function application. *)
let try_parse_infix (lhs : expr) (tokens : string list) : (expr * string list) option =
  match tokens with
  | "is" :: "not" :: "empty" :: rest ->
    Some (Call ("gt", [Call ("length", [lhs]); Lit 0.0]), rest)
  | "is" :: "empty" :: rest ->
    Some (Call ("eq", [Call ("length", [lhs]); Lit 0.0]), rest)
  | "is" :: "not" :: rest ->
    let (rhs, rest') = match rest with
      | tok :: tl when String.length tok >= 2 && tok.[0] = '"' ->
        let s = String.sub tok 1 (String.length tok - 2) in
        (StrLit s, tl)
      | tok :: tl -> (Var tok, tl)
      | [] -> failwith "is not: missing RHS"
    in
    Some (Call ("neq", [lhs; rhs]), rest')
  | "is" :: rest ->
    let (rhs, rest') = match rest with
      | tok :: tl when String.length tok >= 2 && tok.[0] = '"' ->
        let s = String.sub tok 1 (String.length tok - 2) in
        (StrLit s, tl)
      | tok :: tl -> (Var tok, tl)
      | [] -> failwith "is: missing RHS"
    in
    Some (Call ("eq", [lhs; rhs]), rest')
  | "exists" :: rest ->
    Some (Call ("exists", [lhs]), rest)
  | _ -> None

(* wrap_destructure: given a param that starts with "[", parse names until "]",
   return (synthetic_param_name, desugared_body_wrapper, remaining_tokens).
   The wrapper takes the body and wraps it in LetIn chains:
     fn _arg_N -> let name0 = nth _arg_N 0 let name1 = nth _arg_N 1 ... body *)
let parse_destructure_pattern (idx : int) (tokens : string list)
    : string * (expr -> expr) * string list =
  (* tokens starts right after "[" *)
  let arg_name = Printf.sprintf "_arg_%d" idx in
  let rec collect_names acc toks =
    match toks with
    | "]" :: rest -> (List.rev acc, rest)
    | "," :: rest -> collect_names acc rest
    | name :: rest -> collect_names (name :: acc) rest
    | [] -> (List.rev acc, [])
  in
  let (names, rest) = collect_names [] tokens in
  let wrapper body =
    List.fold_right (fun (i, name) inner ->
      LetIn (name, Call ("nth", [Var arg_name; Lit (float_of_int i)]), inner)
    ) (List.mapi (fun i n -> (i, n)) names) body
  in
  (arg_name, wrapper, rest)

let rec parse_expr (tokens : string list) : expr * string list =
  let (e, rest) = parse_expr_primary tokens in
  (* check for pipe or infix *)
  parse_pipe_or_infix e rest

and parse_pipe_or_infix (lhs : expr) (tokens : string list) : expr * string list =
  match tokens with
  | "|" :: "where" :: rest ->
    (* | where [pat] [and guard]* collect expr *)
    let (pat_names, rest) = match rest with
      | "[" :: rest' ->
        let rec cp acc = function
          | "]" :: r -> (List.rev acc, r)
          | "," :: r -> cp acc r
          | "_" :: r -> cp ("_" :: acc) r
          | name :: r -> cp (name :: acc) r
          | [] -> (List.rev acc, [])
        in
        cp [] rest'
      | _ -> failwith "| where: expected '[' pattern"
    in
    let rec collect_guards acc = function
      | "|" :: "and" :: rest | "and" :: rest ->
        let (g, rest') = parse_expr_primary rest in
        (* apply infix but NOT pipes to the guard *)
        let (g, rest') = match try_parse_infix g rest' with
          | Some (g', r) -> (g', r)
          | None -> (g, rest')
        in
        collect_guards (g :: acc) rest'
      | "|" :: "collect" :: rest | "collect" :: rest ->
        (List.rev acc, rest)
      | other -> ([], other)
    in
    let (guards, rest) = collect_guards [] rest in
    let (collect_e, rest) = parse_expr_primary rest in
    let from_e = From (lhs, pat_names, guards, collect_e) in
    parse_pipe_or_infix from_e rest
  | "|" :: "collect" :: rest ->
    (* | collect expr  — shorthand, bind "_it" to whole item *)
    let (collect_e, rest) = parse_expr_primary rest in
    let from_e = From (lhs, ["_it"], [], collect_e) in
    parse_pipe_or_infix from_e rest
  | "|" :: "filter" :: rest ->
    let (fn_e, rest) = parse_expr_primary rest in
    let e = Call ("filter", [lhs; fn_e]) in
    parse_pipe_or_infix e rest
  | "|" :: "map" :: rest ->
    let (fn_e, rest) = parse_expr_primary rest in
    let e = Call ("map", [lhs; fn_e]) in
    parse_pipe_or_infix e rest
  | "|" :: "all" :: rest ->
    let (fn_e, rest) = parse_expr_primary rest in
    let e = Call ("list-all", [lhs; fn_e]) in
    parse_pipe_or_infix e rest
  | "|" :: "any" :: rest ->
    let (fn_e, rest) = parse_expr_primary rest in
    let e = Call ("list-any", [lhs; fn_e]) in
    parse_pipe_or_infix e rest
  | "|" :: "find" :: rest ->
    let (fn_e, rest) = parse_expr_primary rest in
    let e = Call ("list-find", [lhs; fn_e]) in
    parse_pipe_or_infix e rest
  | "|" :: "reduce" :: rest ->
    let (init_e, rest) = parse_expr_primary rest in
    let (fn_e, rest) = parse_expr_primary rest in
    let e = Call ("reduce", [lhs; init_e; fn_e]) in
    parse_pipe_or_infix e rest
  | _ ->
    match try_parse_infix lhs tokens with
    | Some (e', rest') -> (e', rest')
    | None -> (lhs, tokens)

and parse_expr_primary (tokens : string list) : expr * string list =
  match tokens with
  | [] -> failwith "parse_expr: empty"
  | "(" :: rest ->
    let (e, rest') = parse_expr rest in
    (match rest' with
     | ")" :: rest'' -> (e, rest'')
     | _ -> (e, rest'))

   (* list literal: [expr, expr, ...] *)
   | "[" :: rest ->
     let rec collect_items acc toks =
       match toks with
       | "]" :: rest' -> (List.rev acc, rest')
       | "," :: rest' -> collect_items acc rest'
       | [] -> (List.rev acc, [])
       | _ ->
         let (item, rest') = parse_expr toks in
         collect_items (item :: acc) rest'
     in
     let (items, rest') = collect_items [] rest in
     (ListExpr items, rest')

   (* string literal *)
   | tok :: rest when String.length tok >= 2 && tok.[0] = '"' ->
     let s = String.sub tok 1 (String.length tok - 2) in
     (StrLit s, rest)

  (* boolean literals *)
  | "true" :: rest -> (BoolLit true, rest)
  | "false" :: rest -> (BoolLit false, rest)

  (* fn x y -> body  — with optional destructuring patterns *)
  | "fn" :: rest ->
    let rec collect_params acc param_idx = function
      | "->" :: rest' -> (List.rev acc, [], rest')
      | "[" :: rest' ->
        let (arg_name, wrapper, rest'') = parse_destructure_pattern param_idx rest' in
        collect_params (arg_name :: acc) (param_idx + 1) rest''
          |> (fun (ps, wrappers, r) -> (ps, wrapper :: wrappers, r))
      | p :: rest' -> collect_params (p :: acc) (param_idx + 1) rest'
      | [] -> (List.rev acc, [], [])
    in
    let (params, wrappers, rest') = collect_params [] 0 rest in
    let (body, rest'') = parse_expr rest' in
    (* apply all destructuring wrappers innermost-first *)
    let body' = List.fold_left (fun b w -> w b) body (List.rev wrappers) in
    (* warn if the terminal expression of the lambda body is a bare variadic op.
       this catches pitfall 1/9: concat/add/or/and at the end of a lambda body
       will greedily consume tokens from the enclosing call. wrap in (...). *)
    let rec terminal_expr = function
      | LetIn (_, _, b) -> terminal_expr b
      | e -> e
    in
    (match terminal_expr body' with
     | Call (op, args) when Yantra_arity.op_arity op = -1 && List.length args > 2 ->
       Printf.eprintf "warning: variadic op '%s' with %d args as lambda body — wrap in (...) to prevent token consumption (pitfall 1)\n%!" op (List.length args)
     | _ -> ());
    (Lambda (params, body'), rest'')

  (* let x = e1 in e2 *)
  | "let" :: name :: "=" :: rest ->
    let (rhs, rest') = parse_expr rest in
    (match rest' with
     | "in" :: rest'' ->
       let (body, rest''') = parse_expr rest'' in
       (LetIn (name, rhs, body), rest''')
     | "let" :: _ ->
       (* successive let without in: chain them *)
       let (body, rest'') = parse_expr rest' in
       (LetIn (name, rhs, body), rest'')
     | [] | ")" :: _ | "]" :: _ | "|" :: _ -> (LetIn (name, rhs, Var name), rest')
     | _ ->
       (* last let in a lambda body: parse remainder as the body *)
       let (body, rest'') = parse_expr rest' in
       (LetIn (name, rhs, body), rest''))

  (* cond (guard body) (guard body) ... otherwise default *)
  | "cond" :: rest ->
    parse_cond [] rest

  (* from <list> where [pat] [and <guard>]* collect <expr> *)
  | "from" :: rest ->
    parse_from rest

  (* scan construct removed — all tantras use reduce now *)
  | "scan" :: _ ->
    failwith "parse_expr: scan construct removed — use reduce"

  | tok :: rest ->
    (* try literal float *)
    match float_of_string_opt tok with
    | Some f -> (Lit f, rest)
    | None ->
      let arity = Yantra_arity.op_arity tok in
      if arity > 0 then begin
        (* fixed arity operation *)
        let rec collect_args n acc toks =
          if n = 0 then (List.rev acc, toks)
          else
            match toks with
            | [] -> raise Yantra_arity.Arg_overconsumed
            | t0 :: _ when Yantra_arity.is_boundary t0 -> raise Yantra_arity.Arg_overconsumed
            | t0 :: rest0 ->
              let arg_as_var = Yantra_arity.op_arity t0 > 0 && t0 <> "(" in
              if arg_as_var then
                collect_args (n - 1) (Var t0 :: acc) rest0
              else
                (try
                   let (arg, toks') = parse_expr toks in
                   collect_args (n - 1) (arg :: acc) toks'
                 with Failure _ ->
                   if t0 = "(" || t0 = ")" || Yantra_arity.is_boundary t0 then
                     raise Yantra_arity.Arg_overconsumed
                   else
                     collect_args (n - 1) (Var t0 :: acc) rest0)
        in
        (try
           let (args, rest') = collect_args arity [] rest in
           (Call (tok, args), rest')
         with Yantra_arity.Arg_overconsumed ->
           (Var tok, rest))
      end else if arity = -1 then begin
        (* variable arity: collect args until boundary or closing paren *)
        let rec collect_var_args acc toks =
          match toks with
          | [] | ")" :: _ | "|" :: _ -> (List.rev acc, toks)
          | tok :: _ when Yantra_arity.is_boundary tok -> (List.rev acc, toks)
          | _ ->
            let (arg, toks') = parse_expr toks in
            collect_var_args (arg :: acc) toks'
        in
        let (args, rest') = collect_var_args [] rest in
        (Call (tok, args), rest')
      end else
        (* variable name or constant reference *)
        (Var tok, rest)

(* ---- from/where/collect parser ------------------------------------------
   Produces: From (list_expr, pattern_names, guard_exprs, collect_expr)
   Evaluated directly by eval_from in yantra_eval.ml — no desugaring. *)
and parse_from (tokens : string list) : expr * string list =
  let rec collect_until_where acc = function
    | "where" :: rest -> (List.rev acc, rest)
    | tok :: rest -> collect_until_where (tok :: acc) rest
    | [] -> (List.rev acc, [])
  in
  let (list_toks, rest) = collect_until_where [] tokens in
  let list_expr = match list_toks with
    | [] -> failwith "from: missing list expression"
    | _ -> let (e, _) = parse_expr list_toks in e
  in
  let (pat_names, rest) = match rest with
    | "[" :: rest' ->
      let rec collect_pat acc = function
        | "]" :: r -> (List.rev acc, r)
        | "," :: r -> collect_pat acc r
        | name :: r -> collect_pat (name :: acc) r
        | [] -> (List.rev acc, [])
      in
      collect_pat [] rest'
    | _ -> failwith "from: expected '[' pattern after where"
  in
  let rec collect_guards acc = function
    | "and" :: rest ->
      let (g, rest') = parse_expr rest in
      collect_guards (g :: acc) rest'
    | "collect" :: rest -> (List.rev acc, rest)
    | other -> ([], other)
  in
  let (extra_guards, rest) = collect_guards [] rest in
  let (collect_expr, rest) = parse_expr rest in
  (From (list_expr, pat_names, extra_guards, collect_expr), rest)

and parse_cond (branches : (expr * expr) list) (tokens : string list) : expr * string list =
  match tokens with
  | [] | ")" :: _ | "]" :: _ | "|" :: _ ->
    (* end of enclosing expression — stop here, no default branch *)
    (Cond (List.rev branches, Var "_none"), tokens)
  | "otherwise" :: rest ->
    let (default, rest') = parse_expr rest in
    (Cond (List.rev branches, default), rest')
  | "(" :: rest ->
    (* parse guard *)
    let (guard, rest') = parse_expr rest in
    (* consume closing paren of guard if present, then parse body *)
    let rest' = match rest' with ")" :: r -> r | r -> r in
    let (body, rest'') = parse_expr rest' in
    parse_cond ((guard, body) :: branches) rest''
  | _ ->
    (* bare guard (variable or simple call, no parens): parse guard then body.
       stop if the next token is a boundary — it belongs to the enclosing expression. *)
    if Yantra_arity.is_boundary (List.hd tokens) then
      (Cond (List.rev branches, Var "_none"), tokens)
    else
      let (guard, rest') = parse_expr tokens in
      (match rest' with
       | [] | ")" :: _ | "]" :: _ | "|" :: _ ->
         (* ran out before body — guard is the else value *)
         (Cond (List.rev branches, guard), rest')
       | tok :: _ when Yantra_arity.is_boundary tok ->
         (Cond (List.rev branches, guard), rest')
       | _ ->
         let (body, rest'') = parse_expr rest' in
         parse_cond ((guard, body) :: branches) rest'')

let parse_expr_string (s : string) : expr =
  let tokens = Yantra_tokeniser.tokenise_expr s in
  if tokens = [] then Var "_empty"
  else
    let (e, _) = parse_expr tokens in
    e
