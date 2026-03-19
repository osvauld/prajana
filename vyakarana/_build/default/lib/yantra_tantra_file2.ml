(* yantra_tantra_file2.ml — Layer 2 .tantra2 file parser.
   Header: "tantra2 name"
   Produces the same [tantra] type as yantra_tantra_file.ml.
   The eval engine (yantra_eval.ml) is unchanged.

   Layer 2 syntax eliminates the three structural tensions:
     Tension 2 — arity table drives parsing      → parse form determines meaning
     Tension 3 — outer let invisible in scan      → typed scan state with full scope
     Tension 7 — let inside fn split by parser    → block-depth tracking

   Key syntax forms:
     takes <param>                    input param declaration
     <name> = <expr>                  outer let binding
     scan <expr> [state...]:          scan with typed state header
       [word, edge, _] ->             triple pattern branch head
       [word, e1|e2, _] ->            multiple edges (or-combined guard)
       when <pred>                    one predicate per line
       ->                             separates guards from body
         emit                         emit current triple
         emit [s, e, o]               emit explicit triple
         <var> = <expr>               state assignment (SSet)
       _ -> emit                      default branch
     return <name>                    return declaration
     <expr> | where [p] | collect e   pipe expression (From)
     <expr> | filter { x -> body }    pipe filter
     fn x -> body                     lambda (file parser is block-aware)
*)

open Yantra_types

(* ---- tokeniser ------------------------------------------------------------ *)

let strip_comment (line : string) : string =
  let len = String.length line in
  let rec find i in_string =
    if i >= len then line
    else if line.[i] = '"' then
      (if i > 0 && line.[i-1] = '\\' then find (i+1) in_string
       else find (i+1) (not in_string))
    else if (not in_string) && i < len-1
            && line.[i] = '-' && line.[i+1] = '-' then
      String.sub line 0 i
    else find (i+1) in_string
  in
  find 0 false

let tokenise2 (s : string) : string list =
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
    (match c with
    | '-' when !i+1 < len && s.[!i+1] = '-' ->
      flush (); while !i < len && s.[!i] <> '\n' do incr i done
    | ' ' | '\t' | '\n' ->
      flush (); incr i
    | '(' | ')' | '[' | ']' | ',' ->
      flush (); tokens := String.make 1 c :: !tokens; incr i
    | '|' ->
      (* look ahead: || is two pipes, | alone is pipe operator *)
      flush (); tokens := "|" :: !tokens; incr i
    | '-' when !i+1 < len && s.[!i+1] = '>' ->
      flush (); tokens := "->" :: !tokens; i := !i + 2
    | '!' when !i+1 < len && s.[!i+1] = '=' ->
      flush (); tokens := "!=" :: !tokens; i := !i + 2
    | '=' when !i+1 < len && s.[!i+1] = '=' ->
      flush (); tokens := "==" :: !tokens; i := !i + 2
    | ':' when !i+1 < len && s.[!i+1] = ':' ->
      flush (); tokens := "::" :: !tokens; i := !i + 2
    | '{' ->
      flush (); tokens := "{" :: !tokens; incr i
    | '}' ->
      flush (); tokens := "}" :: !tokens; incr i
    | ':' ->
      flush (); tokens := ":" :: !tokens; incr i
    | '"' ->
      flush (); incr i;
      let sbuf = Buffer.create 16 in
      while !i < len && s.[!i] <> '"' do
        (if s.[!i] = '\\' && !i+1 < len then
          (match s.[!i+1] with
           | 'n'  -> Buffer.add_char sbuf '\n'; i := !i+2
           | 't'  -> Buffer.add_char sbuf '\t'; i := !i+2
           | '\\' -> Buffer.add_char sbuf '\\'; i := !i+2
           | '"'  -> Buffer.add_char sbuf '"';  i := !i+2
           | _    -> Buffer.add_char sbuf s.[!i]; incr i)
        else (Buffer.add_char sbuf s.[!i]; incr i))
      done;
      if !i < len then incr i;
      tokens := ("\"" ^ Buffer.contents sbuf ^ "\"") :: !tokens
    | _ ->
      Buffer.add_char buf c; incr i)
  done;
  flush ();
  List.rev !tokens

(* ---- expression parser ---------------------------------------------------- *)
(* Desugars to the same [expr] AST as the Layer 1 parser.
   The eval engine sees no difference. *)

let rec parse2_expr (tokens : string list) : expr * string list =
  let (e, rest) = parse2_primary tokens in
  (* try pipe: expr | ... *)
  parse2_pipe e rest

and parse2_pipe (lhs : expr) (tokens : string list) : expr * string list =
  match tokens with
  | "|" :: "where" :: rest ->
    (* pipe into where/collect: expr | where [pat] [and guard]* | collect expr *)
    let (pat_names, rest) = match rest with
      | "[" :: rest' ->
        let rec cp acc = function
          | "]" :: r -> (List.rev acc, r)
          | "," :: r -> cp acc r
          | "_" :: r -> cp ("_" :: acc) r
          | name :: r -> cp (name :: acc) r
          | [] -> (List.rev acc, [])
        in cp [] rest'
      | _ -> ([], rest)
    in
    (* collect_guard_expr: parse a guard expression that is always paren-wrapped
       e.g. "| and (eq e "vishesa")" — the guard is "(eq e "vishesa")".
       We parse just the paren group to avoid consuming downstream | collect. *)
    let collect_guard_expr tokens =
      match tokens with
      | "(" :: _ ->
        (* paren-wrapped: find matching close paren, parse interior *)
        let rec skip depth acc = function
          | [] -> (List.rev acc, [])
          | "(" :: r -> skip (depth+1) ("(" :: acc) r
          | ")" :: r when depth = 1 -> (List.rev acc, r)
          | ")" :: r -> skip (depth-1) (")" :: acc) r
          | t :: r -> skip depth (t :: acc) r
        in
        let (inner, rest) = skip 1 [] (List.tl tokens) in
        let (e, _) = parse2_expr inner in
        (e, rest)
      | _ ->
        (* bare token — parse as primary (e.g. bare variable name) *)
        parse2_primary tokens
    in
    let rec collect_guards acc = function
      | "and" :: rest | "|" :: "and" :: rest ->
        let (g, rest') = collect_guard_expr rest in
        collect_guards (g :: acc) rest'
      | "|" :: "collect" :: rest | "collect" :: rest ->
        (List.rev acc, rest)
      | other -> (List.rev acc, other)
    in
    let (guards, rest') = collect_guards [] rest in
    let (collect_e, rest'') = parse2_expr rest' in
    let from_e = From (lhs, pat_names, guards, collect_e) in
    parse2_pipe from_e rest''
  | "|" :: "collect" :: rest ->
    (* simple collect without where — bind "it" to the whole item *)
    let (collect_e, rest') = parse2_expr rest in
    let from_e = From (lhs, ["_it"], [], collect_e) in
    parse2_pipe from_e rest'
  | "|" :: "filter" :: rest ->
    (* expr | filter { x -> body } *)
    let (fn_e, rest') = parse2_primary rest in
    let filter_e = Call ("filter", [lhs; fn_e]) in
    parse2_pipe filter_e rest'
  | "|" :: "all" :: rest ->
    let (fn_e, rest') = parse2_primary rest in
    let all_e = Call ("list-all", [lhs; fn_e]) in
    parse2_pipe all_e rest'
  | "|" :: "any" :: rest ->
    let (fn_e, rest') = parse2_primary rest in
    let any_e = Call ("list-any", [lhs; fn_e]) in
    parse2_pipe any_e rest'
  | "|" :: "find" :: rest ->
    let (fn_e, rest') = parse2_primary rest in
    let find_e = Call ("list-find", [lhs; fn_e]) in
    parse2_pipe find_e rest'
  | "|" :: "map" :: rest ->
    let (fn_e, rest') = parse2_primary rest in
    let map_e = Call ("map", [lhs; fn_e]) in
    parse2_pipe map_e rest'
  | "|" :: "reduce" :: rest ->
    (* pipe | reduce init fn — folds the LHS list into a single value.
       init: the initial accumulator (parsed as a primary).
       fn:   the fold function (fn acc item -> body), parsed as a primary.
       This is the natural continuation of | collect | reduce without a
       named intermediate binding. *)
    let (init_e, rest') = parse2_primary rest in
    let (fn_e, rest'') = parse2_primary rest' in
    let reduce_e = Call ("reduce", [lhs; init_e; fn_e]) in
    parse2_pipe reduce_e rest''
  | "is" :: "not" :: "empty" :: rest ->
    parse2_pipe (Call ("gt", [Call ("length", [lhs]); Lit 0.0])) rest
  | "is" :: "empty" :: rest ->
    parse2_pipe (Call ("eq", [Call ("length", [lhs]); Lit 0.0])) rest
  | "is" :: "not" :: rest ->
    let (rhs, rest') = parse2_primary rest in
    parse2_pipe (Call ("neq", [lhs; rhs])) rest'
  | "is" :: rest ->
    let (rhs, rest') = parse2_primary rest in
    parse2_pipe (Call ("eq", [lhs; rhs])) rest'
  | "!=" :: rest ->
    let (rhs, rest') = parse2_primary rest in
    parse2_pipe (Call ("neq", [lhs; rhs])) rest'
  | "==" :: rest ->
    let (rhs, rest') = parse2_primary rest in
    parse2_pipe (Call ("eq", [lhs; rhs])) rest'
  | "in" :: rest ->
    let (rhs, rest') = parse2_primary rest in
    parse2_pipe (Call ("member", [lhs; rhs])) rest'
  | "not" :: "in" :: rest ->
    let (rhs, rest') = parse2_primary rest in
    parse2_pipe (Call ("not", [Call ("member", [lhs; rhs])])) rest'
  | "or" :: rest ->
    let (rhs, rest') = parse2_primary rest in
    parse2_pipe (Call ("or", [lhs; rhs])) rest'
  | _ -> (lhs, tokens)

and parse2_primary (tokens : string list) : expr * string list =
  match tokens with
  | [] -> failwith "parse2_primary: empty"
  | "(" :: rest ->
    let (e, rest') = parse2_expr rest in
    let rest'' = match rest' with ")" :: r -> r | r -> r in
    (e, rest'')
  | "[" :: rest ->
    (* list literal or triple pattern — parse as list of exprs *)
    let rec items acc toks =
      match toks with
      | "]" :: r -> (List.rev acc, r)
      | "," :: r -> items acc r
      | _ ->
        let (item, r) = parse2_expr toks in
        items (item :: acc) r
    in
    let (elems, rest') = items [] rest in
    (ListExpr elems, rest')
  | "{" :: rest ->
    (* lambda: { x y -> body } — block-aware, no arity magic *)
    let rec collect_params acc = function
      | "->" :: rest' -> (List.rev acc, rest')
      | p :: rest' -> collect_params (p :: acc) rest'
      | [] -> (List.rev acc, [])
    in
    let (params, rest') = collect_params [] rest in
    let (body, rest'') = parse2_expr rest' in
    let rest''' = match rest'' with "}" :: r -> r | r -> r in
    (Lambda (params, body), rest''')
  | "fn" :: rest ->
    (* lambda: fn x y -> body *)
    let rec collect_params acc = function
      | "->" :: rest' -> (List.rev acc, rest')
      | p :: rest' -> collect_params (p :: acc) rest'
      | [] -> (List.rev acc, [])
    in
    let (params, rest') = collect_params [] rest in
    let (body, rest'') = parse2_expr rest' in
    (Lambda (params, body), rest'')
  | "let" :: name :: "=" :: rest ->
    let (rhs, rest') = parse2_expr rest in
    (match rest' with
     | "in" :: rest'' ->
       let (body, rest''') = parse2_expr rest'' in
       (LetIn (name, rhs, body), rest''')
     | _ ->
        let (body, rest'') = parse2_expr rest' in
        (LetIn (name, rhs, body), rest''))
  | "cond" :: rest ->
    parse2_cond [] rest
  | "not" :: rest ->
    let (e, rest') = parse2_primary rest in
    (Call ("not", [e]), rest')
  | "exists" :: rest ->
    let (e, rest') = parse2_primary rest in
    (Call ("exists", [e]), rest')
  | "true" :: rest -> (BoolLit true, rest)
  | "false" :: rest -> (BoolLit false, rest)
  | tok :: rest when String.length tok >= 2 && tok.[0] = '"' ->
    let s = String.sub tok 1 (String.length tok - 2) in
    (StrLit s, rest)
  | "_" :: rest -> (Var "_none", rest)
  | tok :: rest ->
    (match float_of_string_opt tok with
     | Some f -> (Lit f, rest)
     | None ->
       (* function call: tok args... — collect args until boundary *)
       let arity = Yantra_arity.op_arity tok in
       if arity > 0 then begin
         (* fixed arity from Layer 1 table — still used during migration *)
         let rec collect n acc toks =
           if n = 0 then (List.rev acc, toks)
           else match toks with
             | [] | ")" :: _ | "]" :: _ | "}" :: _ | "|" :: _
             | "->" :: _ | "when" :: _ | "otherwise" :: _
             | "return" :: _ | "done" :: _ -> (List.rev acc, toks)
             | _ ->
               let (arg, toks') = parse2_primary toks in
               collect (n-1) (arg :: acc) toks'
         in
         let (args, rest') = collect arity [] rest in
         let e = Call (tok, args) in
         parse2_pipe e rest'
       end else if arity = -1 then begin
         (* variadic op — collect args until boundary (should be paren-wrapped at call site) *)
         let rec collect_var acc toks =
           match toks with
           | [] | ")" :: _ | "]" :: _ | "}" :: _ | "|" :: _
           | "->" :: _ | "let" :: _ | "when" :: _ | "otherwise" :: _
           | "return" :: _ | "done" :: _ | "in" :: _ -> (List.rev acc, toks)
           | _ ->
             let (arg, toks') = parse2_primary toks in
             collect_var (arg :: acc) toks'
         in
         let (args, rest') = collect_var [] rest in
         let e = Call (tok, args) in
         parse2_pipe e rest'
       end else begin
         (* variable or zero-arg call — dot access *)
         let e = Var tok in
         parse2_dot e rest
       end)

and parse2_dot (lhs : expr) (tokens : string list) : expr * string list =
  (* dot field access: expr.field → Call("shabda", [expr; StrLit "field"]) *)
  (* note: dots appear as part of identifiers in the tokeniser (not split),
     so we handle "word.field" as a single token and split here *)
  match lhs with
  | Var name ->
    (match String.index_opt name '.' with
     | Some dot_pos ->
       let obj_name = String.sub name 0 dot_pos in
       let field = String.sub name (dot_pos+1) (String.length name - dot_pos - 1) in
       let obj_e = Var obj_name in
       let field_e = StrLit field in
       let access_e = Call ("shabda", [obj_e; field_e]) in
       parse2_pipe access_e tokens
     | None -> parse2_pipe lhs tokens)
  | _ -> parse2_pipe lhs tokens

and parse2_cond (branches : (expr * expr) list) (tokens : string list)
    : expr * string list =
  match tokens with
  | "otherwise" :: rest ->
    let (def, rest') = parse2_expr rest in
    (Cond (List.rev branches, def), rest')
  | [] | ")" :: _ | "]" :: _ | "}" :: _ ->
    (Cond (List.rev branches, Var "_none"), tokens)
  | _ ->
    let (guard, rest) = parse2_expr tokens in
    let (body, rest') = parse2_expr rest in
    parse2_cond ((guard, body) :: branches) rest'

let parse2_expr_string (s : string) : expr =
  let tokens = tokenise2 s in
  if tokens = [] then Var "_empty"
  else let (e, _) = parse2_expr tokens in e

(* ---- scan parser ---------------------------------------------------------- *)
(* Parses the Layer 2 scan block:
     scan <expr> [state-decls]:
       branch*
   Each branch is one of:
     [word, edge, _] -> body      triple pattern head
     [word, e1|e2, _] -> body     multi-edge pattern
     when pred\n... -> body       explicit when lines
     _ -> body                    wildcard / default
*)

(* scan state declaration: "name: type = init-expr" *)
let parse_state_decl (s : string) : (string * expr) option =
  (* format: "name: type = init" or "name = init" *)
  match String.split_on_char '=' s with
  | lhs :: rhs_parts ->
    let rhs = String.concat "=" rhs_parts |> String.trim in
    let name = (match String.split_on_char ':' (String.trim lhs) with
      | n :: _ -> String.trim n
      | [] -> String.trim lhs)
    in
    if String.length name = 0 || String.length rhs = 0 then None
    else (try Some (name, parse2_expr_string rhs)
          with _ -> None)
  | [] -> None

(* parse the typed state header: [name: type = init, ...] *)
let parse_state_header (s : string) : (string * expr) list =
  (* s is the content between [ and ] after "scan <expr>" *)
  let parts = String.split_on_char ',' s in
  List.filter_map parse_state_decl parts

(* parse a triple pattern head: [word, edge, _] or [word, e1|e2, _] *)
(* returns (state_bindings, guard_expr) — state_bindings are (name, slot_expr) pairs *)
let parse_triple_pattern (pat_str : string) : (expr * (string * expr) list) =
  (* split on comma inside the brackets *)
  let inner = String.trim pat_str in
  let parts = String.split_on_char ',' inner
              |> List.map String.trim in
  match parts with
  | [word_s; edge_s; obj_s] ->
    let make_bind name slot = (name, Var slot) in
    (* word binding *)
    let word_bind = if word_s = "_" then [] else [make_bind word_s "word"] in
    (* edge: may be "e1|e2|e3" *)
    let edge_parts = String.split_on_char '|' edge_s |> List.map String.trim in
    let edge_guard = match edge_parts with
      | [e] when e = "_" -> BoolLit true
      | [e] ->
        let e_lit = if String.length e >= 2 && e.[0] = '"'
                    then StrLit (String.sub e 1 (String.length e - 2))
                    else StrLit e in
        Call ("eq", [Var "edge"; e_lit])
      | es ->
        let guards = List.map (fun e ->
          let e_lit = if String.length e >= 2 && e.[0] = '"'
                      then StrLit (String.sub e 1 (String.length e - 2))
                      else StrLit e in
          Call ("eq", [Var "edge"; e_lit])
        ) es in
        List.fold_left (fun acc g -> Call ("or", [acc; g]))
          (List.hd guards) (List.tl guards)
    in
    (* obj binding *)
    let obj_bind = if obj_s = "_" then [] else [make_bind obj_s "obj"] in
    let let_binds = word_bind @ obj_bind in
    (edge_guard, let_binds)
  | _ -> (BoolLit true, [])

(* ---- file parser ---------------------------------------------------------- *)

(* Block depth tracking for the file parser.
   Lines inside scan blocks or fn/lambda bodies are never treated as
   new top-level bindings regardless of "name = ..." pattern. *)

type block_kind = BKScan | BKFn | BKBrace

type parse2_state = {
  mutable name         : string;
  mutable inputs       : tantra_param list;
  mutable let_bindings : (string * string list) list;  (* name, raw_lines *)
  mutable returns      : tantra_param list;
  mutable section      : string;
  mutable block_stack  : block_kind list;
  mutable cur_name     : string;
  mutable cur_lines    : string list;
}

let is_ident_char c =
  (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
  (c >= '0' && c <= '9') || c = '-' || c = '_'

let try_binding_start (s : string) : (string * string) option =
  let trimmed = String.trim s in
  match String.index_opt trimmed '=' with
  | Some eq_pos when eq_pos > 0 ->
    let lhs = String.trim (String.sub trimmed 0 eq_pos) in
    if String.length lhs > 0 &&
       String.to_seq lhs |> Seq.for_all is_ident_char &&
       (* not "==" *)
       not (eq_pos < String.length trimmed - 1 && trimmed.[eq_pos+1] = '=') then
      let rhs = String.trim (String.sub trimmed (eq_pos+1)
                  (String.length trimmed - eq_pos - 1)) in
      Some (lhs, rhs)
    else None
  | _ -> None

(* count opening/closing delimiters in a line to track block depth *)
let count_opens_closes (line : string) : int * int =
  let s = strip_comment line in
  let opens = ref 0 and closes = ref 0 in
  let in_str = ref false in
  String.iter (fun c ->
    match c with
    | '"' -> in_str := not !in_str
    | '(' | '[' | '{' when not !in_str -> incr opens
    | ')' | ']' | '}' when not !in_str -> incr closes
    | _ -> ()
  ) s;
  (!opens, !closes)

(* does this line start a scan block?
   matches both:
     "scan <expr> [state]:"         — bare scan at top level
     "name = scan <expr> [state]:"  — scan as RHS of a let binding *)
let is_scan_start (s : string) : bool =
  let t = String.trim (strip_comment s) in
  let len = String.length t in
  if len = 0 then false
  else if t.[len-1] <> ':' then false
  else
    (* check if "scan" appears either at start or after "name =" *)
    let starts_scan = len >= 4 && String.sub t 0 4 = "scan" in
    let has_scan_rhs =
      match String.index_opt t '=' with
      | Some eq_pos ->
        let after = String.trim (String.sub t (eq_pos+1) (String.length t - eq_pos - 1)) in
        String.length after >= 4 && String.sub after 0 4 = "scan"
      | None -> false
    in
    starts_scan || has_scan_rhs

(* does this line start a fn body? contains "->" *)
let has_arrow (s : string) : bool =
  let t = strip_comment s in
  match String.split_on_char '>' t with
  | _ :: _ :: _ ->
    (match String.index_opt t '-' with
     | Some i when i+1 < String.length t && t.[i+1] = '>' -> true
     | _ -> false)
  | _ -> false

let flush_binding (st : parse2_state) : unit =
  if String.length st.cur_name > 0 && st.cur_lines <> [] then begin
    st.let_bindings <- (st.cur_name, List.rev st.cur_lines) :: st.let_bindings;
    st.cur_name <- "";
    st.cur_lines <- []
  end

(* ---- full scan block parser ----------------------------------------------- *)
(* Parses a sequence of raw lines that form the body of a "scan [...] :" block.
   Returns scan_branch list. *)

type scan_branch_raw = {
  mutable sb2_head  : string;            (* "[word, edge, _]" or "_" or "" for when-chains *)
  mutable sb2_whens : string list;       (* "when pred" lines *)
  mutable sb2_body  : string list;       (* body lines after "->" *)
  mutable sb2_default : bool;            (* true if this is the "_ ->" branch *)
}

let parse_scan_block_lines (lines : string list) : scan_branch list =
  (* First pass: group lines into branches.
     A branch starts with:
       - "[...] ->"           triple-pattern branch (possibly multi-line guard)
       - "[...]\nwhen ...\n->"  pattern + when lines
       - "when ..."           when-chain branch
       - "_ ->"               default branch
     Body lines follow until the next branch starts. *)
  let branches : scan_branch_raw list ref = ref [] in
  let cur : scan_branch_raw ref = ref {
    sb2_head = ""; sb2_whens = []; sb2_body = []; sb2_default = false
  } in
  let in_body = ref false in

  let flush_cur () =
    if !in_body || !cur.sb2_head <> "" || !cur.sb2_whens <> [] then begin
      branches := !cur :: !branches;
      cur := { sb2_head = ""; sb2_whens = []; sb2_body = []; sb2_default = false };
      in_body := false
    end
  in

  List.iter (fun line ->
    let t = String.trim (strip_comment line) in
    if String.length t = 0 then ()
    else if t = "_" then begin
      (* standalone _ — default branch head *)
      flush_cur ();
      !cur.sb2_default <- true;
      !cur.sb2_head <- "_"
    end else if String.length t >= 2 && t.[0] = '_' && t.[1] = ' ' &&
                String.sub t 0 2 = "_ " then begin
      (* "_ -> emit" on same line *)
      flush_cur ();
      let rest = String.trim (String.sub t 2 (String.length t - 2)) in
      let rest2 = if String.length rest >= 2 && String.sub rest 0 2 = "->"
                  then String.trim (String.sub rest 2 (String.length rest - 2))
                  else rest in
      !cur.sb2_default <- true;
      !cur.sb2_head <- "_";
      in_body := true;
      if String.length rest2 > 0 then
        !cur.sb2_body <- [rest2]
    end else if String.length t > 0 && t.[0] = '[' then begin
      (* triple pattern head *)
      flush_cur ();
      in_body := false;
      (* extract pattern: "[word, edge, _]" — find matching ]
         String.sub s pos len takes len chars from pos, so use close_bracket-1 *)
      let close_bracket = match String.index_opt t ']' with
        | Some i -> i | None -> String.length t - 1
      in
      let pat = String.sub t 1 (close_bracket - 1) in
      !cur.sb2_head <- pat;
      (* remainder after ] *)
      let after = String.trim (String.sub t (close_bracket+1)
                    (String.length t - close_bracket - 1)) in
      (* check for inline "->" *)
      if String.length after >= 2 && String.sub after 0 2 = "->" then begin
        let body = String.trim (String.sub after 2 (String.length after - 2)) in
        if String.length body > 0 then !cur.sb2_body <- [body];
        in_body := true
      end
    end else if String.length t >= 4 && String.sub t 0 4 = "when" then begin
      if !in_body then begin
        (* "when" inside body — treat as body line *)
        !cur.sb2_body <- t :: !cur.sb2_body
      end else begin
        (* guard line — add predicate after "when".
           if "->" appears on the same line (e.g. "when pred ->"), split there:
           treat the part before "->" as the predicate and open the body. *)
        let rest4 = String.trim (String.sub t 4 (String.length t - 4)) in
        let arrow_pos = ref (-1) in
        String.iteri (fun i c ->
          if !arrow_pos < 0 && c = '-'
             && i+1 < String.length rest4 && rest4.[i+1] = '>'
          then arrow_pos := i
        ) rest4;
        if !arrow_pos >= 0 then begin
          let pred = String.trim (String.sub rest4 0 !arrow_pos) in
          let body_rest = String.trim
            (String.sub rest4 (!arrow_pos+2)
               (String.length rest4 - !arrow_pos - 2)) in
          if String.length pred > 0 then
            !cur.sb2_whens <- pred :: !cur.sb2_whens;
          in_body := true;
          if String.length body_rest > 0 then
            !cur.sb2_body <- [body_rest]
        end else
          !cur.sb2_whens <- rest4 :: !cur.sb2_whens
      end
    end else if String.length t >= 2 && String.sub t 0 2 = "->" then begin
      (* arrow: close the guard section, open body *)
      in_body := true;
      let rest = String.trim (String.sub t 2 (String.length t - 2)) in
      if String.length rest > 0 then !cur.sb2_body <- [rest]
    end else if !in_body then begin
      !cur.sb2_body <- t :: !cur.sb2_body
    end else begin
      (* continuation of head or when section — add to whens *)
      !cur.sb2_whens <- t :: !cur.sb2_whens
    end
  ) lines;
  flush_cur ();

  (* Second pass: convert raw branches to scan_branch *)
  List.rev_map (fun raw ->
    (* build guard from head pattern + when lines *)
    let pat_guard, let_stmts =
      if raw.sb2_default then (BoolLit true, [])
      else if String.length raw.sb2_head > 0 then
        parse_triple_pattern raw.sb2_head
      else (BoolLit true, [])
    in
    let when_guards = List.rev_map (fun pred_str ->
      (* parse the when predicate — may use "in", "not in", "!=" etc. *)
      let tokens = tokenise2 pred_str in
      let (e, _) = parse2_expr tokens in e
    ) raw.sb2_whens in
    let full_guard =
      let all = pat_guard :: when_guards in
      let non_trivial = List.filter (function BoolLit true -> false | _ -> true) all in
      match non_trivial with
      | [] -> None   (* default branch — no guard *)
      | [g] -> Some g
      | gs -> Some (List.fold_left (fun acc g -> Call ("and", [acc; g])) (List.hd gs) (List.tl gs))
    in
    (* if default branch, guard is None *)
    let final_guard = if raw.sb2_default then None else full_guard in

    (* build body stmts *)
    let body_stmts =
      (* let-bindings from pattern destructuring *)
      let let_s = List.map (fun (name, e) -> SLet (name, e)) let_stmts in
      let body_s = List.rev_map (fun line ->
        let t = String.trim line in
        if t = "emit" then
          SEmit (Var "triple")
        else if String.length t >= 5 && String.sub t 0 5 = "emit " then begin
          let rest = String.trim (String.sub t 5 (String.length t - 5)) in
          SEmit (parse2_expr_string rest)
        end else if String.length t >= 6 && String.sub t 0 6 = "clear " then begin
          let var = String.trim (String.sub t 6 (String.length t - 6)) in
          SClear var
        end else if String.length t >= 4 && String.sub t 0 4 = "let " then begin
          (* "let name = expr" — local binding visible in subsequent body stmts *)
          let rest = String.trim (String.sub t 4 (String.length t - 4)) in
          (match try_binding_start rest with
           | Some (var, rhs) -> SLet (var, parse2_expr_string rhs)
           | None -> SEmit (parse2_expr_string t))
        end else begin
          (* try "var = expr" assignment first (state mutation) *)
          match try_binding_start t with
          | Some (var, rhs) -> SSet (var, parse2_expr_string rhs)
          | None ->
            (* expression statement — evaluate for side effects *)
            SEmit (parse2_expr_string t)
        end
      ) raw.sb2_body in
      let_s @ body_s
    in
    { sb_guard = final_guard; sb_body = body_stmts }
  ) !branches

(* ---- compile a let binding's raw lines to an expr ------------------------- *)

let compile_let_lines (name : string) (lines : string list) : (string * expr) option =
  (* lines includes the "name = rhs..." first line plus continuation lines.
     Extract the RHS by stripping the "name =" prefix from the first line. *)
  let first_raw = match lines with l :: _ -> strip_comment l |> String.trim | [] -> "" in
  let rhs_first = match try_binding_start first_raw with
    | Some (_, rhs) -> rhs
    | None -> first_raw
  in
  let cont_lines = match lines with _ :: rest -> rest | [] -> [] in
  let rhs_trim = String.trim rhs_first in
  (* check if this binding's RHS is a scan block *)
  let is_scan_rhs = String.length rhs_trim >= 4 && String.sub rhs_trim 0 4 = "scan" in
  if is_scan_rhs then begin
    (* scan block: rhs_first is "scan <list-expr> [state-decls]:"
       cont_lines are the branch lines *)
    let scan_head = rhs_trim in
    (* find the ":" that terminates the scan header (after optional [...]) *)
    let colon_pos = ref (-1) in
    let bracket_depth = ref 0 in
    String.iteri (fun i c ->
      if !colon_pos < 0 then
        match c with
        | '[' -> incr bracket_depth
        | ']' -> decr bracket_depth
        | ':' when !bracket_depth = 0 -> colon_pos := i
        | _ -> ()
    ) scan_head;
    let head = if !colon_pos > 0
               then String.trim (String.sub scan_head 0 !colon_pos)
               else scan_head in
    (* parse "scan <list-expr> [state-decls]" *)
    let head_tokens = tokenise2 head in
    let (list_expr, rest_tokens) = match head_tokens with
      | "scan" :: rest -> parse2_expr rest
      | _ -> (Var "_none", head_tokens)
    in
    let state_decls = match rest_tokens with
      | "[" :: rest ->
        let rec collect_state d acc toks =
          match toks with
          | "]" :: r when d = 0 -> (List.rev acc, r)
          | "]" :: r -> collect_state (d-1) ("]" :: acc) r
          | "[" :: r -> collect_state (d+1) ("[" :: acc) r
          | tok :: r -> collect_state d (tok :: acc) r
          | [] -> (List.rev acc, [])
        in
        let (state_toks, _) = collect_state 0 [] rest in
        parse_state_header (String.concat " " state_toks)
      | _ -> []
    in
    let branches = parse_scan_block_lines cont_lines in
    Some (name, Scan (list_expr, state_decls, branches))
  end else begin
    (* regular expression binding: join rhs + continuation lines *)
    let all_text = String.concat " "
      (rhs_first :: List.map (fun l -> strip_comment l |> String.trim) cont_lines)
      |> String.trim in
    if String.length all_text = 0 then None
    else
      try Some (name, parse2_expr_string all_text)
      with exn ->
        let reason = Printexc.to_string exn in
        (* truncate raw text for readability *)
        let raw_short = if String.length all_text > 80
                        then String.sub all_text 0 80 ^ "..."
                        else all_text in
        Printf.eprintf "[tantra2 PARSE_ERROR] binding '%s': %s  raw: [%s]\n%!"
          name reason raw_short;
        (* inject sentinel so the error is visible at runtime, not silent VNone *)
        let msg = Printf.sprintf "[PARSE_ERROR in '%s': %s]" name reason in
        Some (name, StrLit msg)
  end

(* ---- main file parser ----------------------------------------------------- *)

let parse_tantra2_file (path : string) : tantra option =
  try
    let ic = open_in path in
    let lines = ref [] in
    (try while true do lines := input_line ic :: !lines done
     with End_of_file -> ());
    close_in ic;
    let lines = List.rev !lines in

    let st : parse2_state = {
      name = ""; inputs = []; let_bindings = []; returns = [];
      section = "header"; block_stack = [];
      cur_name = ""; cur_lines = [];
    } in

    (* track brace/bracket/scan block depth for Tension 7 fix *)
    let depth = ref 0 in
    (* track if we are inside a scan block header *)
    let in_scan_head = ref false in
    (* track if we are inside a scan block body (branches) *)
    let in_scan_body = ref false in

    List.iter (fun line ->
      let stripped = strip_comment line in
      let trimmed = String.trim stripped in
      if String.length trimmed = 0 || trimmed = "done" then ()
      else begin
        let (opens, closes) = count_opens_closes line in

        if String.length trimmed >= 8 && String.sub trimmed 0 8 = "tantra2 " then
          st.name <- String.trim (String.sub trimmed 8 (String.length trimmed - 8))
        else if trimmed = "takes" || trimmed = "inputs" then
          st.section <- "inputs"
        else if String.length trimmed >= 6 && String.sub trimmed 0 6 = "takes " then begin
          (* "takes <name>" — inline input declaration *)
          let rest = String.trim (String.sub trimmed 6 (String.length trimmed - 6)) in
          let parts = String.split_on_char ' ' rest
                     |> List.filter (fun s -> String.length s > 0) in
          (match parts with
           | pname :: _ ->
             st.inputs <- { tp_name = pname; tp_canonical = pname;
                            tp_type = "list"; tp_unit = None; tp_avastha = None }
                          :: st.inputs;
             st.section <- "body"
           | [] -> ())
        end
        else if String.length trimmed >= 7 && String.sub trimmed 0 7 = "return " then begin
          flush_binding st;
          st.section <- "return";
          let rest = String.trim (String.sub trimmed 7 (String.length trimmed - 7)) in
          let parts = String.split_on_char ' ' rest
                     |> List.filter (fun s -> String.length s > 0) in
          (match parts with
           | pname :: _ ->
             st.returns <- { tp_name = pname; tp_canonical = pname;
                             tp_type = "list"; tp_unit = None; tp_avastha = None }
                           :: st.returns
           | [] -> ())
        end else if trimmed = "return" then begin
          flush_binding st;
          st.section <- "return"
        end else begin
          match st.section with
          | "header" | "inputs" ->
            (* if the line contains '=', it's a body binding, not a param *)
            if String.contains trimmed '=' then begin
              flush_binding st;
              st.section <- "body";
              (match try_binding_start trimmed with
               | Some (bname, _) ->
                 st.cur_name <- bname;
                 st.cur_lines <- [trimmed]
               | None -> ())
            end else begin
              let parts = String.split_on_char ' ' trimmed
                         |> List.filter (fun s -> String.length s > 0) in
              (match parts with
               | pname :: _ ->
                 st.inputs <- { tp_name = pname; tp_canonical = pname;
                                tp_type = "list"; tp_unit = None; tp_avastha = None }
                              :: st.inputs;
                 st.section <- "body"
               | [] -> ())
            end
          | "return" ->
            let parts = String.split_on_char ' ' trimmed
                       |> List.filter (fun s -> String.length s > 0) in
            (match parts with
             | pname :: _ ->
               st.returns <- { tp_name = pname; tp_canonical = pname;
                               tp_type = "list"; tp_unit = None; tp_avastha = None }
                             :: st.returns
             | [] -> ())
           | _ ->
             (* body section — track block depth *)
             (* a line is "inside a block" if: depth > 0, in scan head, or in scan body *)
             let inside_block = !depth > 0 || !in_scan_head || !in_scan_body in
             if not inside_block then begin
               (* at top level: check for new binding start or scan head *)
               if is_scan_start trimmed then begin
                 flush_binding st;
                 (match try_binding_start trimmed with
                  | Some (bname, _) ->
                    st.cur_name <- bname;
                    st.cur_lines <- [trimmed]
                  | None ->
                    st.cur_lines <- trimmed :: st.cur_lines);
                 in_scan_head := true
               end else begin
                 match try_binding_start trimmed with
                 | Some (bname, _rhs) ->
                   (* new binding — close any open scan body *)
                   in_scan_body := false;
                   flush_binding st;
                   st.cur_name <- bname;
                   st.cur_lines <- [trimmed]
                 | None ->
                   if String.length st.cur_name > 0 then
                     st.cur_lines <- trimmed :: st.cur_lines
               end
             end else begin
               (* inside a block — always continuation, never new binding *)
               if String.length st.cur_name > 0 then
                 st.cur_lines <- trimmed :: st.cur_lines
             end;
             depth := !depth + opens - closes;
             if !depth < 0 then depth := 0;
             (* scan head ends at the ":" — then scan body begins *)
             if !in_scan_head && String.length trimmed > 0
                && trimmed.[String.length trimmed - 1] = ':' then begin
               in_scan_head := false;
               in_scan_body := true
             end
        end
      end
    ) lines;
    flush_binding st;

    (* compile all let bindings.
       flush_binding stores (List.rev cur_lines) — already in correct order
       (first line = binding header, subsequent lines = continuation/body).
       Do NOT reverse again here. *)
    let lets = List.filter_map (fun (name, lines) ->
      compile_let_lines name lines
    ) (List.rev st.let_bindings) in

    if String.length st.name > 0 then
      Some {
        t_name    = st.name;
        t_file    = path;
        t_inputs  = List.rev st.inputs;
        t_lets    = lets;
        t_returns = List.rev st.returns;
      }
    else None
  with exn ->
    Printf.eprintf "[tantra2 PARSE_ERROR] file %s: %s\n%!" path (Printexc.to_string exn);
    None
