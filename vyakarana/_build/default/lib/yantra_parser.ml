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
      else if trimmed = "inputs" then
        section := "inputs"
      else if trimmed = "let" || trimmed = "return" || trimmed = "done" then
        section := trimmed
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
  | ")" | "]" | "," | "in" | "otherwise" | "done" | "let" -> true
  | _ -> false

exception Arg_overconsumed

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
              (* if next token is a known op with arity > 0, treat it as Var
                 (it is an input param / variable being passed as argument,
                  not a nested call). this prevents sqrt/floor/value etc.
                  from consuming the next token when used as argument names. *)
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
        (* if the op can't collect all its arguments (e.g. a boundary keyword
           like "otherwise" appears where an arg is expected), fall back to
           treating the token as a variable reference, not a function call *)
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

(* strip_comment: remove everything after -- (two consecutive dashes) *)
let strip_comment (line : string) : string =
  let len = String.length line in
  let rec find i =
    if i >= len - 1 then line
    else if line.[i] = '-' && line.[i + 1] = '-' then
      String.sub line 0 i
    else find (i + 1)
  in
  find 0

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
   cond expressions, let-in chains, etc. *)
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
        | _ -> ()
      end
    ) lines;

    let lets = parse_let_block (List.rev !let_lines) in

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
