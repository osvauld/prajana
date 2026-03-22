(* yantra_tantra_sexp.ml — s-expression tantra parser (.tantra4 format).
   Parses (tantra name (params...) body...) into the same tantra type
   as yantra_tantra_file2.ml.  Reuses parse2_expr for expression parsing.

   Syntax:
     (tantra name (p1 p2 ...)
       (binding-name expr...)
       ...
       final-expr)

   - Last form without a binding name becomes the return value
   - (name expr) where name is an identifier becomes a let binding
   - Comments: -- to end of line (same as tantra3)
   - Expressions inside bindings use the same syntax as tantra3
*)

open Yantra_types

(* ---- tokenizer --------------------------------------------------------- *)
(* Produces flat token list: "(", ")", strings, symbols.
   Strings preserve quotes: "\"hello\"".
   Comments (-- to EOL) are stripped. *)

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
      (* comment: skip to end of line *)
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

(* ---- sexp tree --------------------------------------------------------- *)
(* Intermediate tree before we convert to tantra AST.
   This lets us handle nested parens structurally. *)

type sexp =
  | Atom of string
  | SList of sexp list

(* collect tokens between [ and ] (with nesting) into a single string.
   this preserves [...] expressions verbatim for the expr parser. *)
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

(* parse flat tokens into sexp tree *)
let rec parse_sexp_tree (tokens : string list) : sexp * string list =
  match tokens with
  | [] -> failwith "parse_sexp_tree: unexpected end of input"
  | "(" :: rest ->
    let (children, rest') = parse_sexp_list rest in
    (SList children, rest')
  | "[" :: rest ->
    (* preserve [...] as a single atom — the expr parser handles brackets *)
    let (bracket_str, rest') = collect_bracket rest in
    (Atom bracket_str, rest')
  | ")" :: _ -> failwith "parse_sexp_tree: unexpected ')'"
  | "," :: rest ->
    (* commas inside sexp bodies — skip *)
    parse_sexp_tree rest
  | tok :: rest -> (Atom tok, rest)

and parse_sexp_list (tokens : string list) : sexp list * string list =
  match tokens with
  | [] -> failwith "parse_sexp_list: missing ')'"
  | ")" :: rest -> ([], rest)
  | "," :: rest ->
    (* skip commas between elements *)
    parse_sexp_list rest
  | _ ->
    let (item, rest) = parse_sexp_tree tokens in
    let (more, rest') = parse_sexp_list rest in
    (item :: more, rest')

(* parse all top-level sexps from tokens *)
let parse_all_sexps (tokens : string list) : sexp list =
  let result = ref [] in
  let rest = ref tokens in
  while !rest <> [] do
    let (s, r) = parse_sexp_tree !rest in
    result := s :: !result;
    rest := r
  done;
  List.rev !result

(* ---- sexp -> string (for feeding to existing expr parser) -------------- *)
(* Converts an sexp tree back to a flat string that tokenise2 + parse2_expr
   can handle.  This is the pragmatic bridge: we parse the s-expr structure
   to find bindings and params, then delegate expression parsing to the
   existing battle-tested parser. *)

let rec sexp_to_string (s : sexp) : string =
  match s with
  | Atom a -> a
  | SList children ->
    "(" ^ String.concat " " (List.map sexp_to_string children) ^ ")"

(* ---- identifier detection ---------------------------------------------- *)
let is_ident_char c =
  (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z')
  || (c >= '0' && c <= '9') || c = '-' || c = '_'

let is_identifier s =
  String.length s > 0
  && s.[0] <> '"'
  && s.[0] <> '('
  && s.[0] <> ')'
  (* must start with letter or underscore *)
  && ((s.[0] >= 'a' && s.[0] <= 'z') || (s.[0] >= 'A' && s.[0] <= 'Z') || s.[0] = '_')
  && String.to_seq s |> Seq.for_all is_ident_char

(* keywords that cannot be binding names *)
let is_keyword = function
  | "cond" | "otherwise" | "fn" | "let" | "in" | "true" | "false"
  | "scan" | "from" | "where" | "collect" | "reduce" | "map"
  | "filter" | "not" | "and" | "or" -> true
  | _ -> false

(* ---- main parser ------------------------------------------------------- *)
(* Parse a .tantra4 file into a tantra record.

   Expected structure:
     (tantra name (p1 p2 ...)
       (binding expr ...)    -- let binding
       ...
       expr)                 -- final expression = return value

   A top-level form (name body...) where name is an identifier and not a
   known op/keyword becomes a let binding.  The last form that doesn't
   match as a binding becomes the return expression. *)

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

    (* process body forms: each is either a binding or the final expression *)
    let bindings = ref [] in
    let forms = Array.of_list body in
    let n = Array.length forms in
    for i = 0 to n - 1 do
      let form = forms.(i) in
      let is_last = (i = n - 1) in
      match form with
      | SList (Atom binding_name :: expr_parts) when
          not is_last && is_identifier binding_name && not (is_keyword binding_name) ->
        (* binding: (name expr...) *)
        let expr_str = match expr_parts with
          | [single] -> sexp_to_string single
          | _ -> String.concat " " (List.map sexp_to_string expr_parts)
        in
        let expr = Yantra_expr_parser.parse_expr_string expr_str in
        bindings := (binding_name, expr) :: !bindings
      | _ ->
        (* expression — either final return or a non-binding form *)
        let expr_str = sexp_to_string form in
        let expr = Yantra_expr_parser.parse_expr_string expr_str in
        bindings := ("result", expr) :: !bindings
    done;

    let t_lets = List.rev !bindings in
    let t_returns = [{ tp_name = "result"; tp_canonical = "result";
                       tp_type = "any"; tp_unit = None; tp_avastha = None }] in
    Some { t_name = name; t_file = path; t_inputs; t_lets; t_returns }
  | _ -> None

(* ---- file entry point -------------------------------------------------- *)

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
        Printf.eprintf "yantra_tantra_sexp: expected single top-level form in %s\n" path;
        None
    end
  with exn ->
    Printf.eprintf "yantra_tantra_sexp: error parsing %s: %s\n"
      path (Printexc.to_string exn);
    None

(* ---- arity pre-scan ---------------------------------------------------- *)
(* Quick scan for (tantra name (p1 p2 ...)) — extract name and param count
   without full parse.  Used by yantra_arity.pre_scan_tantra_file. *)

let pre_scan_tantra4_file (path : string) : (string * int) option =
  try
    let ic = open_in path in
    let len = in_channel_length ic in
    let src = really_input_string ic len in
    close_in ic;
    let tokens = tokenize_sexp src in
    (* look for pattern: ( tantra NAME ( p1 p2 ... ) ... ) *)
    match tokens with
    | "(" :: "tantra" :: name :: "(" :: rest ->
      (* count tokens until closing ) *)
      let count = ref 0 in
      let r = ref rest in
      while !r <> [] && List.hd !r <> ")" do
        incr count;
        r := List.tl !r
      done;
      Some (name, !count)
    | _ -> None
  with _ -> None
