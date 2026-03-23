(* vakya.ml — parsers: tokenizer, s-expression, expression, tantra4, arity.
   consolidates yantra_tokeniser (55L) + yantra_tantra_sexp (279L)
   + yantra_expr_parser (353L) + yantra_arity (45L).

   sections:
     1. arity — op arity tables + boundary detection
     2. tokeniser — expression string → token list
     3. expression parser — tokens → expr AST
     4. s-expression tokenizer + tree parser
     5. tantra4 parser — .tantra4 file → tantra record *)

open Kriya_types

(* ═══════════════════════════════════════════════════════════════════════════
   1. ARITY — op arity tables + boundary detection
   ═══════════════════════════════════════════════════════════════════════════ *)

let _tantra_arities : (string, int) Hashtbl.t = Hashtbl.create 64

let register_tantra_arity (name : string) (arity : int) : unit =
  Hashtbl.replace _tantra_arities name arity

let _graph_arities : (string, int) Hashtbl.t = Hashtbl.create 128

let register_graph_op_arity (name : string) (arity : int) : unit =
  Hashtbl.replace _graph_arities name arity

let op_arity name =
  match Hashtbl.find_opt _graph_arities name with
  | Some n -> n
  | None ->
    match Hashtbl.find_opt _tantra_arities name with
    | Some n -> n
    | None -> 0

let is_known_op name = op_arity name <> 0

let _boundary_keywords : (string, unit) Hashtbl.t = Hashtbl.create 32

let register_boundary_keyword (kw : string) : unit =
  Hashtbl.replace _boundary_keywords kw ()

let is_boundary (tok : string) : bool =
  Hashtbl.mem _boundary_keywords tok

exception Arg_overconsumed

(* ═══════════════════════════════════════════════════════════════════════════
   2. TOKENISER — expression string → token list
   ═══════════════════════════════════════════════════════════════════════════ *)

let tokenise_expr (s : string) : string list =
  let buf = Buffer.create 16 in
  let tokens = ref [] in
  let len = String.length s in
  let i = ref 0 in
  let flush () =
    if Buffer.length buf > 0 then begin
      tokens := Buffer.contents buf :: !tokens;
      Buffer.clear buf
    end
  in
  while !i < len do
    let c = s.[!i] in
    match c with
    | '-' when !i + 1 < len && s.[!i + 1] = '-' ->
      flush ();
      while !i < len && s.[!i] <> '\n' do incr i done
    | ' ' | '\t' | '\n' ->
      flush (); incr i
    | '(' | ')' | '[' | ']' | ',' | '|' ->
       flush ();
       tokens := String.make 1 c :: !tokens;
       incr i
    | '"' ->
      flush ();
      incr i;
      let sbuf = Buffer.create 16 in
      while !i < len && s.[!i] <> '"' do
        if s.[!i] = '\\' && !i + 1 < len then begin
          (match s.[!i + 1] with
           | 'n' -> Buffer.add_char sbuf '\n'; i := !i + 2
           | 't' -> Buffer.add_char sbuf '\t'; i := !i + 2
           | '\\' -> Buffer.add_char sbuf '\\'; i := !i + 2
           | '"' -> Buffer.add_char sbuf '"'; i := !i + 2
           | _ -> Buffer.add_char sbuf s.[!i]; incr i)
        end else begin
          Buffer.add_char sbuf s.[!i];
          incr i
        end
      done;
      if !i < len then incr i;
      tokens := ("\"" ^ Buffer.contents sbuf ^ "\"") :: !tokens
    | _ ->
      Buffer.add_char buf c;
      incr i
  done;
  flush ();
  List.rev !tokens

(* ═══════════════════════════════════════════════════════════════════════════
   3. EXPRESSION PARSER — tokens → expr AST
   ═══════════════════════════════════════════════════════════════════════════ *)

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

let parse_destructure_pattern (idx : int) (tokens : string list)
    : string * (expr -> expr) * string list =
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
  parse_pipe_or_infix e rest

and parse_pipe_or_infix (lhs : expr) (tokens : string list) : expr * string list =
  match tokens with
  | "|" :: "where" :: rest ->
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

   | tok :: rest when String.length tok >= 2 && tok.[0] = '"' ->
     let s = String.sub tok 1 (String.length tok - 2) in
     (StrLit s, rest)

  | "true" :: rest -> (BoolLit true, rest)
  | "false" :: rest -> (BoolLit false, rest)

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
    let body' = List.fold_left (fun b w -> w b) body (List.rev wrappers) in
    let rec terminal_expr = function
      | LetIn (_, _, b) -> terminal_expr b
      | e -> e
    in
    (match terminal_expr body' with
     | Call (op, args) when op_arity op = -1 && List.length args > 2 ->
       Printf.eprintf "warning: variadic op '%s' with %d args as lambda body — wrap in (...) to prevent token consumption (pitfall 1)\n%!" op (List.length args)
     | _ -> ());
    (Lambda (params, body'), rest'')

  | "let" :: name :: "=" :: rest ->
    let (rhs, rest') = parse_expr rest in
    (match rest' with
     | "in" :: rest'' ->
       let (body, rest''') = parse_expr rest'' in
       (LetIn (name, rhs, body), rest''')
     | "let" :: _ ->
       let (body, rest'') = parse_expr rest' in
       (LetIn (name, rhs, body), rest'')
     | [] | ")" :: _ | "]" :: _ | "|" :: _ -> (LetIn (name, rhs, Var name), rest')
     | _ ->
       let (body, rest'') = parse_expr rest' in
       (LetIn (name, rhs, body), rest''))

  | "cond" :: rest ->
    parse_cond [] rest

  | "from" :: rest ->
    parse_from rest

  | "scan" :: _ ->
    failwith "parse_expr: scan construct removed — use reduce"

  | tok :: rest ->
    match float_of_string_opt tok with
    | Some f -> (Lit f, rest)
    | None ->
      let arity = op_arity tok in
      if arity > 0 then begin
        let rec collect_args n acc toks =
          if n = 0 then (List.rev acc, toks)
          else
            match toks with
            | [] -> raise Arg_overconsumed
            | t0 :: _ when is_boundary t0 -> raise Arg_overconsumed
            | t0 :: rest0 ->
              let arg_as_var = op_arity t0 > 0 && t0 <> "(" in
              if arg_as_var then
                collect_args (n - 1) (Var t0 :: acc) rest0
              else
                (try
                   let (arg, toks') = parse_expr toks in
                   collect_args (n - 1) (arg :: acc) toks'
                 with Failure _ ->
                   if t0 = "(" || t0 = ")" || is_boundary t0 then
                     raise Arg_overconsumed
                   else
                     collect_args (n - 1) (Var t0 :: acc) rest0)
        in
        (try
           let (args, rest') = collect_args arity [] rest in
           (Call (tok, args), rest')
         with Arg_overconsumed ->
           (Var tok, rest))
      end else if arity = -1 then begin
        let rec collect_var_args acc toks =
          match toks with
          | [] | ")" :: _ | "|" :: _ -> (List.rev acc, toks)
          | tok :: _ when is_boundary tok -> (List.rev acc, toks)
          | _ ->
            let (arg, toks') = parse_expr toks in
            collect_var_args (arg :: acc) toks'
        in
        let (args, rest') = collect_var_args [] rest in
        (Call (tok, args), rest')
      end else
        (Var tok, rest)

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
    (Cond (List.rev branches, Var "_none"), tokens)
  | "otherwise" :: rest ->
    let (default, rest') = parse_expr rest in
    (Cond (List.rev branches, default), rest')
  | "(" :: rest ->
    let (guard, rest') = parse_expr rest in
    let rest' = match rest' with ")" :: r -> r | r -> r in
    let (body, rest'') = parse_expr rest' in
    parse_cond ((guard, body) :: branches) rest''
  | _ ->
    if is_boundary (List.hd tokens) then
      (Cond (List.rev branches, Var "_none"), tokens)
    else
      let (guard, rest') = parse_expr tokens in
      (match rest' with
       | [] | ")" :: _ | "]" :: _ | "|" :: _ ->
         (Cond (List.rev branches, guard), rest')
       | tok :: _ when is_boundary tok ->
         (Cond (List.rev branches, guard), rest')
       | _ ->
         let (body, rest'') = parse_expr rest' in
         parse_cond ((guard, body) :: branches) rest'')

let parse_expr_string (s : string) : expr =
  let tokens = tokenise_expr s in
  if tokens = [] then Var "_empty"
  else
    let (e, _) = parse_expr tokens in
    e

(* ═══════════════════════════════════════════════════════════════════════════
   4. S-EXPRESSION TOKENIZER + TREE PARSER
   ═══════════════════════════════════════════════════════════════════════════ *)

let tokenize_sexp (src : string) : string list =
  let buf = Buffer.create 16 in
  let tokens = ref [] in
  let len = String.length src in
  let i = ref 0 in
  let flush () =
    if Buffer.length buf > 0 then begin
      tokens := Buffer.contents buf :: !tokens;
      Buffer.clear buf
    end
  in
  while !i < len do
    let c = src.[!i] in
    match c with
    | '-' when !i + 1 < len && src.[!i + 1] = '-' ->
      flush ();
      while !i < len && src.[!i] <> '\n' do incr i done
    | ';' ->
      flush ();
      while !i < len && src.[!i] <> '\n' do incr i done
    | ' ' | '\t' | '\n' | '\r' ->
      flush (); incr i
    | '(' | ')' | '[' | ']' | ',' ->
      flush (); tokens := String.make 1 c :: !tokens; incr i
    | '"' ->
      flush (); incr i;
      let sbuf = Buffer.create 16 in
      while !i < len && src.[!i] <> '"' do
        if src.[!i] = '\\' && !i + 1 < len then begin
          (match src.[!i + 1] with
           | 'n'  -> Buffer.add_char sbuf '\n'
           | 't'  -> Buffer.add_char sbuf '\t'
           | '\\' -> Buffer.add_char sbuf '\\'
           | '"'  -> Buffer.add_char sbuf '"'
           | _    -> Buffer.add_char sbuf src.[!i]);
          i := !i + 2
        end else begin
          Buffer.add_char sbuf src.[!i]; incr i
        end
      done;
      if !i < len then incr i;
      tokens := ("\"" ^ Buffer.contents sbuf ^ "\"") :: !tokens
    | _ ->
      Buffer.add_char buf c; incr i
  done;
  flush ();
  List.rev !tokens

type sexp =
  | Atom of string
  | SList of sexp list

let collect_bracket (tokens : string list) : string * string list =
  let buf = Buffer.create 32 in
  Buffer.add_char buf '[';
  let depth = ref 1 in
  let rest = ref tokens in
  while !depth > 0 && !rest <> [] do
    let tok = List.hd !rest in
    rest := List.tl !rest;
    if tok = "[" then (incr depth; Buffer.add_string buf tok)
    else if tok = "]" then begin
      decr depth;
      if !depth > 0 then Buffer.add_string buf tok
      else Buffer.add_char buf ']'
    end else begin
      if Buffer.length buf > 1 && Buffer.contents buf |> fun s -> s.[String.length s - 1] <> '[' then
        Buffer.add_char buf ' ';
      Buffer.add_string buf tok
    end
  done;
  (Buffer.contents buf, !rest)

let rec parse_sexp_tree (tokens : string list) : sexp * string list =
  match tokens with
  | [] -> failwith "parse_sexp_tree: unexpected end of input"
  | "(" :: rest ->
    let (children, rest') = parse_sexp_list rest in
    (SList children, rest')
  | "[" :: rest ->
    let (bracket_str, rest') = collect_bracket rest in
    (Atom bracket_str, rest')
  | ")" :: _ -> failwith "parse_sexp_tree: unexpected ')'"
  | "," :: rest ->
    parse_sexp_tree rest
  | tok :: rest -> (Atom tok, rest)

and parse_sexp_list (tokens : string list) : sexp list * string list =
  match tokens with
  | [] -> failwith "parse_sexp_list: missing ')'"
  | ")" :: rest -> ([], rest)
  | "," :: rest ->
    parse_sexp_list rest
  | _ ->
    let (item, rest) = parse_sexp_tree tokens in
    let (more, rest') = parse_sexp_list rest in
    (item :: more, rest')

let parse_all_sexps (tokens : string list) : sexp list =
  let result = ref [] in
  let rest = ref tokens in
  while !rest <> [] do
    let (s, r) = parse_sexp_tree !rest in
    result := s :: !result;
    rest := r
  done;
  List.rev !result

let rec sexp_to_string (s : sexp) : string =
  match s with
  | Atom a -> a
  | SList children ->
    "(" ^ String.concat " " (List.map sexp_to_string children) ^ ")"

(* ═══════════════════════════════════════════════════════════════════════════
   5. TANTRA4 PARSER — .tantra4 file → tantra record
   ═══════════════════════════════════════════════════════════════════════════ *)

let is_ident_char c =
  (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z')
  || (c >= '0' && c <= '9') || c = '-' || c = '_'

let is_identifier s =
  String.length s > 0
  && s.[0] <> '"'
  && s.[0] <> '('
  && s.[0] <> ')'
  && ((s.[0] >= 'a' && s.[0] <= 'z') || (s.[0] >= 'A' && s.[0] <= 'Z') || s.[0] = '_')
  && String.to_seq s |> Seq.for_all is_ident_char

let is_keyword = function
  | "cond" | "otherwise" | "fn" | "let" | "in" | "true" | "false"
  | "scan" | "from" | "where" | "collect" | "reduce" | "map"
  | "filter" | "not" | "and" | "or" -> true
  | _ -> false

let parse_sexp_tantra (path : string) (s : sexp) : tantra option =
  match s with
  | SList (Atom "tantra" :: Atom name :: SList params :: body) ->
    let param_names = List.filter_map (fun s ->
      match s with Atom p -> Some p | _ -> None
    ) params in
    let t_inputs = List.map (fun p ->
      { tp_name = p; tp_canonical = p; tp_type = "any";
        tp_unit = None; tp_avastha = None }
    ) param_names in
    let bindings = ref [] in
    let forms = Array.of_list body in
    let n = Array.length forms in
    for i = 0 to n - 1 do
      let form = forms.(i) in
      let is_last = (i = n - 1) in
      match form with
      | SList (Atom binding_name :: expr_parts) when
          not is_last && is_identifier binding_name && not (is_keyword binding_name) ->
        let expr_str = match expr_parts with
          | [single] -> sexp_to_string single
          | _ -> String.concat " " (List.map sexp_to_string expr_parts)
        in
        let expr = parse_expr_string expr_str in
        bindings := (binding_name, expr) :: !bindings
      | _ ->
        let expr_str = sexp_to_string form in
        let expr = parse_expr_string expr_str in
        bindings := ("result", expr) :: !bindings
    done;
    let t_lets = List.rev !bindings in
    let t_returns = [{ tp_name = "result"; tp_canonical = "result";
                       tp_type = "any"; tp_unit = None; tp_avastha = None }] in
    Some { t_name = name; t_file = path; t_inputs; t_lets; t_returns }
  | _ -> None

let parse_tantra4_file (path : string) : tantra option =
  try
    let ic = open_in path in
    let len = in_channel_length ic in
    let src = really_input_string ic len in
    close_in ic;
    let tokens = tokenize_sexp src in
    if tokens = [] then None
    else begin
      let sexps = parse_all_sexps tokens in
      match sexps with
      | [s] -> parse_sexp_tantra path s
      | _ ->
        Printf.eprintf "vakya: expected single top-level form in %s\n" path;
        None
    end
  with exn ->
    Printf.eprintf "vakya: error parsing %s: %s\n"
      path (Printexc.to_string exn);
    None

let pre_scan_tantra4_file (path : string) : (string * int) option =
  try
    let ic = open_in path in
    let len = in_channel_length ic in
    let src = really_input_string ic len in
    close_in ic;
    let tokens = tokenize_sexp src in
    match tokens with
    | "(" :: "tantra" :: name :: "(" :: rest ->
      let count = ref 0 in
      let r = ref rest in
      while !r <> [] && List.hd !r <> ")" do
        incr count;
        r := List.tl !r
      done;
      Some (name, !count)
    | _ -> None
  with _ -> None
