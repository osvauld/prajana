(* yantra_expr_parser.ml — parse_expr: tokens → expr.
   expression parser for tantra let-block lines.
   handles: literals, variables, function calls (fixed/variadic arity),
   cond chains, lambda (fn), let-in chains, list literals. *)

open Yantra_types

let rec parse_expr (tokens : string list) : expr * string list =
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

  (* fn x y -> body *)
  | "fn" :: rest ->
    let rec collect_params acc = function
      | "->" :: rest' -> (List.rev acc, rest')
      | p :: rest' -> collect_params (p :: acc) rest'
      | [] -> (List.rev acc, [])
    in
    let (params, rest') = collect_params [] rest in
    let (body, rest'') = parse_expr rest' in
    (* warn if the terminal expression of the lambda body is a bare variadic op.
       this catches pitfall 1/9: concat/add/or/and at the end of a lambda body
       will greedily consume tokens from the enclosing call. wrap in (...). *)
    let rec terminal_expr = function
      | LetIn (_, _, b) -> terminal_expr b
      | e -> e
    in
    (match terminal_expr body with
     | Call (op, args) when Yantra_arity.op_arity op = -1 && List.length args > 2 ->
       Printf.eprintf "warning: variadic op '%s' with %d args as lambda body — wrap in (...) to prevent token consumption (pitfall 1)\n%!" op (List.length args)
     | _ -> ());
    (Lambda (params, body), rest'')

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
     | [] | ")" :: _ | "]" :: _ -> (LetIn (name, rhs, Var name), rest')
     | _ ->
       (* last let in a lambda body: parse remainder as the body *)
       let (body, rest'') = parse_expr rest' in
       (LetIn (name, rhs, body), rest''))

  (* cond (guard body) (guard body) ... otherwise default *)
  | "cond" :: rest ->
    parse_cond [] rest

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
              (* if next token is a known op with arity > 0, treat it as Var *)
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
          | [] | ")" :: _ -> (List.rev acc, toks)
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

and parse_cond (branches : (expr * expr) list) (tokens : string list) : expr * string list =
  match tokens with
  | "otherwise" :: rest ->
    let (default, rest') = parse_expr rest in
    (Cond (List.rev branches, default), rest')
  | "(" :: rest ->
    (* parse guard *)
    let (guard, rest') = parse_expr rest in
    (* consume closing paren of guard if present, then parse body *)
    let rest' = match rest' with ")" :: r -> r | r -> r in
    let (body, rest'') = parse_expr rest' in
    (* consume any trailing paren from an outer grouping *)
    let rest'' = match rest'' with ")" :: r -> r | r -> r in
    parse_cond ((guard, body) :: branches) rest''
  | [] ->
    (Cond (List.rev branches, Var "_none"), [])
  | _ ->
    (* bare guard (variable or simple call, no parens): parse guard then body *)
    let (guard, rest') = parse_expr tokens in
    let (body, rest'') = parse_expr rest' in
    parse_cond ((guard, body) :: branches) rest''

let parse_expr_string (s : string) : expr =
  let tokens = Yantra_tokeniser.tokenise_expr s in
  if tokens = [] then Var "_empty"
  else
    let (e, _) = parse_expr tokens in
    e
