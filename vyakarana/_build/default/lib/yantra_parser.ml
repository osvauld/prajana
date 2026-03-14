(* extracted from yantra.ml: parser *)
open Yantra_types
(* ---- tantra file parser ---- *)

(* parse an expression from a string like "mul mass acceleration"
   or "mul (mul 0.5 acceleration) (power time 2.0)"
   returns (expr, remaining_tokens) *)

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
      (* comment: skip rest of line *)
      flush ();
      while !i < len && s.[!i] <> '\n' do incr i done
    | ' ' | '\t' | '\n' ->
      flush (); incr i
    | '(' | ')' | '[' | ']' | ',' ->
       flush ();
       tokens := String.make 1 c :: !tokens;
       incr i
    | '"' ->
      (* string literal *)
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
      if !i < len then incr i;  (* skip closing quote *)
      tokens := ("\"" ^ Buffer.contents sbuf ^ "\"") :: !tokens
    | _ ->
      Buffer.add_char buf c;
      incr i
  done;
  flush ();
  List.rev !tokens

(* dynamic arity table — populated by pre-scanning .tantra files.
   tantra-to-tantra calls are discovered automatically: no need
   to hardcode every tantra name in op_arity. *)
let _tantra_arities : (string, int) Hashtbl.t = Hashtbl.create 64

let register_tantra_arity (name : string) (arity : int) : unit =
  Hashtbl.replace _tantra_arities name arity

(* graph-derived arity table — populated from the .om kosha/yantra/ nodes.
   op nodes encode their algebraic class via a kriya edge; the class node
   carries parse-arity in its shabda. this table is the graph-backed
   replacement for the hardcoded op_arity match below. *)
let _graph_arities : (string, int) Hashtbl.t = Hashtbl.create 128

let register_graph_op_arity (name : string) (arity : int) : unit =
  Hashtbl.replace _graph_arities name arity

(* pre-scan a .tantra file: extract name and input count only.
   does NOT parse the let block — just reads the header. *)
let pre_scan_tantra_file (path : string) : (string * int) option =
  try
    let ic = open_in path in
    let lines = ref [] in
    (try while true do lines := input_line ic :: !lines done
     with End_of_file -> ());
    close_in ic;
    let lines = List.rev !lines in
    let name = ref "" in
    let input_count = ref 0 in
    let section = ref "header" in
    List.iter (fun line ->
      let trimmed = String.trim line in
      (* strip comments *)
      let trimmed = match String.index_opt trimmed '-' with
        | Some i when i + 1 < String.length trimmed && trimmed.[i+1] = '-' ->
          String.trim (String.sub trimmed 0 i)
        | _ -> trimmed
      in
      if String.length trimmed >= 7 && String.sub trimmed 0 7 = "tantra " then
        name := String.trim (String.sub trimmed 7 (String.length trimmed - 7))
      else if trimmed = "inputs" || trimmed = "takes" then
        section := "inputs"
      else if trimmed = "let" || trimmed = "return" || trimmed = "done" then
        section := trimmed
      (* new-style: "return name" inline — stop body, switch to return *)
      else if String.length trimmed >= 7 && String.sub trimmed 0 7 = "return " then
        section := "return"
      (* new-style: "takes name [type]" all on one line —
         count the single param and switch to body so subsequent lines are not counted *)
      else if String.length trimmed >= 6 && String.sub trimmed 0 6 = "takes " then begin
        section := "body";
        incr input_count
      end
      (* old-style: bare param line inside inputs section *)
      else if !section = "inputs" && String.length trimmed > 0 then
        incr input_count
    ) lines;
    if String.length !name > 0 then
      Some (!name, !input_count)
    else None
  with _ -> None

(* op arity lookup — pure graph-class model.
   priority: graph-derived class arity → tantra-scanned arity → 0 (unknown).
   the hardcoded table has been deleted; all built-in op arities live in
   brahman/kosha/yantra/ .om nodes, encoded via algebraic class membership. *)
let op_arity name =
  match Hashtbl.find_opt _graph_arities name with
  | Some n -> n
  | None ->
    match Hashtbl.find_opt _tantra_arities name with
    | Some n -> n
    | None -> 0

let is_known_op name = op_arity name <> 0

(* is this token a boundary that stops argument collection? *)
let is_boundary = function
  | ")" | "]" | "," | "in" | "otherwise" | "done" | "let"
  | "when" | "emit" | "set" | "clear" | "return"
  | "where" | "collect" | "with" -> true
  | _ -> false

exception Arg_overconsumed

(* ---- infix postfix operators -------------------------------------------
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
    (* parse RHS: handle string literals and bare names *)
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
  (* try infix postfix operators *)
  match try_parse_infix e rest with
  | Some (e', rest') -> (e', rest')
  | None -> (e, rest)

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
        (* destructuring pattern *)
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
    (* warn if the terminal expression of the lambda body is a bare variadic op. *)
    let rec terminal_expr = function
      | LetIn (_, _, b) -> terminal_expr b
      | e -> e
    in
    (match terminal_expr body' with
     | Call (op, args) when op_arity op = -1 && List.length args > 2 ->
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
     | [] | ")" :: _ | "]" :: _ -> (LetIn (name, rhs, Var name), rest')
     | _ ->
       (* last let in a lambda body: parse remainder as the body *)
       let (body, rest'') = parse_expr rest' in
       (LetIn (name, rhs, body), rest''))

  (* cond (guard body) (guard body) ... otherwise default *)
  | "cond" :: rest ->
    parse_cond [] rest

  (* from <list> where [pat] [and <guard>]* collect <expr>
     desugars to: reduce <list> [] (fn _acc [pat] -> cond (guard) (append _acc [collect]) otherwise _acc) *)
  | "from" :: rest ->
    parse_from rest

  (* scan <list> with <var>=<init>,... when/otherwise ... *)
  | "scan" :: rest ->
    parse_scan rest

  | tok :: rest ->
    (* try literal float *)
    match float_of_string_opt tok with
    | Some f -> (Lit f, rest)
    | None ->
      let arity = op_arity tok in
      if arity > 0 then begin
        (* fixed arity operation *)
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
        (* variable arity: collect args until boundary or closing paren *)
        let rec collect_var_args acc toks =
          match toks with
          | [] | ")" :: _ -> (List.rev acc, toks)
          | tok :: _ when is_boundary tok -> (List.rev acc, toks)
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

(* ---- scan/with/when/emit parser -----------------------------------------
   Produces: Scan (list_expr, state_decls, branches)
   Evaluated directly by eval_scan in yantra_eval.ml — no desugaring.
   Supports nested when/otherwise inside branch bodies. *)
and parse_scan (tokens : string list) : expr * string list =
  let rec collect_until_with acc = function
    | "with" :: rest -> (List.rev acc, rest)
    | tok :: rest    -> collect_until_with (tok :: acc) rest
    | []             -> (List.rev acc, [])
  in
  let (list_toks, rest) = collect_until_with [] tokens in
  let list_expr = match list_toks with
    | [] -> failwith "scan: missing list expression"
    | _ -> let (e, _) = parse_expr list_toks in e
  in
  (* parse state variable declarations: var=init [, var=init]* until first "when"/"otherwise" *)
  let rec parse_state_decls acc toks =
    match toks with
    | "when" :: _ | "otherwise" :: _ -> (List.rev acc, toks)
    | [] -> (List.rev acc, [])
    | name :: "=" :: rest ->
      let rec collect_init iacc = function
        | ("," | "when" | "otherwise") :: _ as r -> (List.rev iacc, r)
        | tok :: rest -> collect_init (tok :: iacc) rest
        | [] -> (List.rev iacc, [])
      in
      let (init_toks, rest') = collect_init [] rest in
      let init_expr = let (e, _) = parse_expr init_toks in e in
      let rest'' = match rest' with "," :: r -> r | r -> r in
      parse_state_decls ((name, init_expr) :: acc) rest''
    | _ :: rest -> parse_state_decls acc rest
  in
  let (state_decls, rest) = parse_state_decls [] rest in
  (* parse scan body: list of scan_stmt.
     'when' is ALWAYS a top-level branch boundary → stop.
     Nested conditionals inside branch bodies use 'cond' or 'if-then'.
     'otherwise' at the start of stmts = top-level default branch → stop.
     'otherwise' after statements (inside an if-then) → handled by caller. *)
  let rec parse_scan_stmts toks : scan_stmt list * string list =
    match toks with
    | "emit" :: rest ->
      let (e, rest') = parse_expr rest in
      let (more, rest'') = parse_scan_stmts rest' in
      (SEmit e :: more, rest'')
    | "set" :: var :: "to" :: rest ->
      let (e, rest') = parse_expr rest in
      let (more, rest'') = parse_scan_stmts rest' in
      (SSet (var, e) :: more, rest'')
    | "clear" :: var :: rest ->
      let (more, rest') = parse_scan_stmts rest in
      (SClear var :: more, rest')
    | "let" :: name :: "=" :: rest ->
      let (e, rest') = parse_expr rest in
      let (more, rest'') = parse_scan_stmts rest' in
      (SLet (name, e) :: more, rest'')
    | "when" :: _ | "otherwise" :: _ | "return" :: _ | "done" :: _ | [] ->
      ([], toks)
    | _ :: rest -> parse_scan_stmts rest
  in
  (* parse branches *)
  let rec parse_branches acc toks =
    match toks with
    | "when" :: rest ->
      let (guard, rest') = parse_expr rest in
      (* check for nested "and" guard continuations before body *)
      let rec collect_and_guards g toks =
        match toks with
        | "and" :: rest ->
          let (g2, rest') = parse_expr rest in
          collect_and_guards (Call ("and", [g; g2])) rest'
        | _ -> (g, toks)
      in
      let (guard, rest') = collect_and_guards guard rest' in
      let (body, rest'') = parse_scan_stmts rest' in
      parse_branches ({ sb_guard = Some guard; sb_body = body } :: acc) rest''
    | "otherwise" :: rest ->
      let (body, rest') = parse_scan_stmts rest in
      (List.rev ({ sb_guard = None; sb_body = body } :: acc), rest')
    | [] ->
      (* implicit otherwise: emit triple *)
      (List.rev ({ sb_guard = None; sb_body = [SEmit (Var "triple")] } :: acc), [])
    | _ :: rest -> parse_branches acc rest
  in
  let (branches, rest) = parse_branches [] rest in
  (Scan (list_expr, state_decls, branches), rest)

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
  let tokens = tokenise_expr s in
  if tokens = [] then Var "_empty"
  else
    let (e, _) = parse_expr tokens in
    e

(* strip_comment: remove everything after two consecutive dashes,
   but skip dashes that appear inside string literals. *)
let strip_comment (line : string) : string =
  let len = String.length line in
  let rec find i in_string =
    if i >= len then line
    else if line.[i] = '"' then
      (* toggle string mode; handle escaped quote *)
      if i > 0 && line.[i - 1] = '\\' then find (i + 1) in_string
      else find (i + 1) (not in_string)
    else if (not in_string) && i < len - 1
            && line.[i] = '-' && line.[i + 1] = '-' then
      String.sub line 0 i
    else find (i + 1) in_string
  in
  find 0 false

(* parse the let block: multi-line expression support.
   a new binding starts when a line matches "name = ..." where name is a
   simple identifier (letters, digits, hyphens). continuation lines are
   anything else within the let section. *)
let parse_let_block (lines : string list) : (string * expr) list =
  (* first, group lines into (name, text) pairs *)
  let bindings : (string * string) list ref = ref [] in
  let cur_name = ref "" in
  let cur_text = Buffer.create 128 in
  let flush () =
    if String.length !cur_name > 0 then begin
      bindings := (!cur_name, Buffer.contents cur_text) :: !bindings;
      Buffer.clear cur_text;
      cur_name := ""
    end
  in
  let is_ident_char c =
    (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
    (c >= '0' && c <= '9') || c = '-' || c = '_'
  in
  (* detect "name = ..." pattern: identifier followed by = *)
  let try_binding_start (s : string) : (string * string) option =
    let trimmed = String.trim s in
    match String.index_opt trimmed '=' with
    | Some eq_pos when eq_pos > 0 ->
      let lhs = String.trim (String.sub trimmed 0 eq_pos) in
      (* lhs must be a single identifier *)
      if String.length lhs > 0 &&
         String.to_seq lhs |> Seq.for_all is_ident_char then
        let rhs = String.trim (String.sub trimmed (eq_pos + 1)
                    (String.length trimmed - eq_pos - 1)) in
        Some (lhs, rhs)
      else None
    | _ -> None
  in
  List.iter (fun line ->
    let stripped = strip_comment line in
    let trimmed = String.trim stripped in
    if String.length trimmed > 0 then
      match try_binding_start trimmed with
      | Some (name, rhs) ->
        flush ();
        cur_name := name;
        Buffer.add_string cur_text rhs
      | None ->
        (* continuation of current binding *)
        if String.length !cur_name > 0 then begin
          Buffer.add_char cur_text ' ';
          Buffer.add_string cur_text trimmed
        end
  ) lines;
  flush ();
  (* parse each binding's text as an expression *)
  List.filter_map (fun (name, text) ->
    if String.length (String.trim text) = 0 then None
    else begin
      ();
      try Some (name, parse_expr_string text)
      with exn ->
        Printf.printf "warning: could not parse let binding '%s': %s [%s]\n%!" name (Printexc.to_string exn) (String.trim text);
        None
    end
  ) (List.rev !bindings)

(* parse a tantra file — supports multi-line let bindings with lambdas,
   cond expressions, let-in chains, etc.
   Supports both old-style (inputs/let/return sections) and new-style
   (takes <param> on same or next line, body bindings, return <name> done). *)
let parse_tantra_file (path : string) : tantra option =
  try
    let ic = open_in path in
    let lines = ref [] in
    (try while true do lines := input_line ic :: !lines done
     with End_of_file -> ());
    close_in ic;
    let lines = List.rev !lines in

    (* first pass: split into sections *)
    let name = ref "" in
    let inputs = ref [] in
    let let_lines = ref [] in
    let returns = ref [] in
    let section = ref "header" in

    List.iter (fun line ->
      let stripped = strip_comment line in
      let trimmed = String.trim stripped in
      if String.length trimmed = 0 || trimmed = "done" then ()
      else if String.length trimmed >= 7 && String.sub trimmed 0 7 = "tantra " then
        name := String.trim (String.sub trimmed 7 (String.length trimmed - 7))
      else if trimmed = "inputs" then
        section := "inputs"
      else if trimmed = "let" then
        section := "let"
      else if trimmed = "return" then
        section := "return"
      (* new-style: "takes" keyword — same line or next line params *)
      else if trimmed = "takes" then
        section := "inputs"
      else if String.length trimmed >= 6 && String.sub trimmed 0 6 = "takes " then begin
        (* inline: takes param [type] — parse the param, then switch to body
           so subsequent lines go into let_lines, not input params *)
        section := "body";
        let rest = String.trim (String.sub trimmed 6 (String.length trimmed - 6)) in
        let parts = String.split_on_char ' ' rest
                   |> List.filter (fun s -> String.length s > 0) in
        (match parts with
         | pname :: ptype :: rest2 ->
           let punit = match rest2 with u :: _ when u <> "purva" && u <> "uttara" -> Some u | _ -> None in
           let pavastha = List.find_opt (fun s -> s = "purva" || s = "uttara") rest2 in
           inputs := { tp_name = pname; tp_canonical = pname; tp_type = ptype; tp_unit = punit; tp_avastha = pavastha } :: !inputs
         | [pname] ->
           inputs := { tp_name = pname; tp_canonical = pname; tp_type = "list"; tp_unit = None; tp_avastha = None } :: !inputs
         | _ -> ())
      end
      (* new-style: "return <name>" — single-line return *)
      else if String.length trimmed >= 7 && String.sub trimmed 0 7 = "return " then begin
        section := "return";
        let rest = String.trim (String.sub trimmed 7 (String.length trimmed - 7)) in
        let parts = String.split_on_char ' ' rest
                   |> List.filter (fun s -> String.length s > 0) in
        (match parts with
         | pname :: ptype :: rest2 ->
           let punit = match rest2 with u :: _ when u <> "purva" && u <> "uttara" -> Some u | _ -> None in
           let pavastha = List.find_opt (fun s -> s = "purva" || s = "uttara") rest2 in
           returns := { tp_name = pname; tp_canonical = pname; tp_type = ptype; tp_unit = punit; tp_avastha = pavastha } :: !returns
         | [pname] ->
           returns := { tp_name = pname; tp_canonical = pname; tp_type = "list"; tp_unit = None; tp_avastha = None } :: !returns
         | _ -> ())
      end
      else begin
        match !section with
        | "inputs" ->
           let parts = String.split_on_char ' ' trimmed
                      |> List.filter (fun s -> String.length s > 0) in
           (match parts with
            | pname :: ptype :: rest ->
              let punit = match rest with u :: _ when u <> "purva" && u <> "uttara" -> Some u | _ -> None in
              let pavastha = List.find_opt (fun s -> s = "purva" || s = "uttara") rest in
              inputs := { tp_name = pname; tp_canonical = pname; tp_type = ptype; tp_unit = punit; tp_avastha = pavastha } :: !inputs
            | _ -> ())
         | "let" ->
           let_lines := line :: !let_lines
         | "return" ->
           let parts = String.split_on_char ' ' trimmed
                      |> List.filter (fun s -> String.length s > 0) in
           (match parts with
            | pname :: ptype :: rest ->
              let punit = match rest with u :: _ when u <> "purva" && u <> "uttara" -> Some u | _ -> None in
              let pavastha = List.find_opt (fun s -> s = "purva" || s = "uttara") rest in
              returns := { tp_name = pname; tp_canonical = pname; tp_type = ptype; tp_unit = punit; tp_avastha = pavastha } :: !returns
            | _ -> ())
         (* new-style body: any line inside a tantra that isn't a keyword goes into let_lines *)
         | "body" ->
           let_lines := line :: !let_lines
         | _ -> ()
       end
    ) lines;

    (* if no explicit "let" section but we have bindings from body, use them.
       detect new-style tantras: they use "takes" instead of "inputs" and have
       no explicit "let" section — the entire body between takes and return is let_lines. *)
    (* For new-style tantras: collect all non-keyword, non-header lines as let_lines.
       We detect this by checking if let_lines is empty and section was never "let".
       Re-scan for new-style body lines. *)
    let let_lines_final =
      if !let_lines = [] then begin
        (* second pass: collect body lines for new-style tantras *)
        let body_lines = ref [] in
        let in_body = ref false in
        List.iter (fun line ->
          let stripped = strip_comment line in
          let trimmed = String.trim stripped in
          if String.length trimmed = 0 || trimmed = "done" then ()
          else if String.length trimmed >= 7 && String.sub trimmed 0 7 = "tantra " then ()
          else if trimmed = "takes" || (String.length trimmed >= 6 && String.sub trimmed 0 6 = "takes ") then
            in_body := true
          else if String.length trimmed >= 7 && String.sub trimmed 0 7 = "return " then
            in_body := false
          else if trimmed = "return" then
            in_body := false
          else if !in_body then
            body_lines := line :: !body_lines
        ) lines;
        List.rev !body_lines
      end else
        List.rev !let_lines
    in

    let lets = parse_let_block let_lines_final in

    if String.length !name > 0 then
      Some {
        t_name    = !name;
        t_file    = path;
        t_inputs  = List.rev !inputs;
        t_lets    = lets;
        t_returns = List.rev !returns;
      }
    else None
  with _ -> None
