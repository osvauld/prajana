(* yantra.ml — the computation layer
   reads tantra files, extracts bindings from natural language,
   resolves the right tantra, evaluates internally, returns results.

   dependency: Proof_graph, Setu *)

open Proof_graph

(* ---- types ---- *)

type tantra_param = {
  tp_name      : string;        (* as written in .tantra: "mass", "time" *)
  tp_canonical : string;        (* graph-resolved: "mass", "kaala" *)
  tp_type      : string;        (* "float", "int" *)
  tp_unit      : string option; (* Some "kilogram", None *)
}

(* expression tree for the let-block RHS *)
type expr =
  | Lit      of float
  | Var      of string
  | Call     of string * expr list    (* op name, arguments *)
  | StrLit   of string                (* "hello" *)
  | BoolLit  of bool                  (* true, false *)
  | ListExpr of expr list             (* [a, b, c] *)
  | Lambda   of string list * expr    (* fn x y -> body *)
  | Cond     of (expr * expr) list * expr  (* cond [(guard, body); ...] otherwise *)
  | LetIn    of string * expr * expr  (* let x = e1 in e2 *)

(* runtime value — what expressions evaluate to *)
type value =
  | VFloat   of float
  | VString  of string
  | VBool    of bool
  | VNode    of string              (* graph node name — exists in graph *)
  | VList    of value list
  | VPair    of string * value      (* named pair: (name, classified-value) *)
  | VBinding of string * float      (* concept = number *)
  | VNone                           (* nothing found / lookup miss *)
  | VFn      of string list * expr * env  (* closure: params, body, captured env *)

and env = (string, value) Hashtbl.t

type tantra = {
  t_name    : string;                         (* "force", "addition" *)
  t_file    : string;                         (* file path *)
  t_inputs  : tantra_param list;
  t_lets    : (string * expr) list;           (* [(name, rhs); ...] *)
  t_returns : tantra_param list;
}

type tantra_index = {
  by_name      : (string, tantra) Hashtbl.t;
  by_output    : (string, tantra list) Hashtbl.t;
  by_input     : (string, tantra list) Hashtbl.t;
  constants    : (string, float) Hashtbl.t;
  conversions  : (string * string, tantra) Hashtbl.t;
  all_tantras  : tantra list ref;
}

type binding = {
  b_name  : string;   (* concept name: "mass", "force", "kaala" *)
  b_value : float;
  b_unit  : string option;
}

type session = {
  mutable bindings      : binding list;
  mutable last_result   : (string * float) list;
  mutable history       : string list;
  mutable context_seeds : string list;
}

type yantra_result = {
  yr_output     : (string * float) list;   (* [(name, value); ...] *)
  yr_tantra     : string;                  (* tantra name used *)
  yr_code       : string;                  (* emitted OCaml source *)
  yr_raw_output : string;                  (* raw stdout from OCaml *)
}

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
    | '(' | ')' ->
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

(* known operations and their arities
   -1 means variable arity (determined by context) *)
let op_arity = function
  (* numeric: 2-arg *)
  | "add" | "sub" | "mul" | "div" | "power" | "min" | "max" | "mod" -> 2
  (* numeric: 1-arg *)
  | "sqrt" | "sin" | "cos" | "tan" | "log"
  | "abs" | "neg" | "floor" | "ceil"
  | "factorial" -> 1
  (* graph: fixed arity *)
  | "lookup" | "name" | "kind" | "node" | "value" | "role"
  | "exists" | "is-tantra" | "not" | "print" | "length"
  | "tokenise" | "classify" | "classify-all" | "join-bigrams"
  | "extract-bindings" | "match-sentence-patterns" | "invoke-tantra" | "format-response"
  | "op-to-tantra" | "string-length" | "to-number" | "to-string"
  | "upper" | "lower"
  | "format-triple" | "iccha-bridge"
  | "query-intents" -> 1
  | "walk" | "walk-in" | "has" | "shabda" | "split" | "eq" | "neq"
  | "map" | "filter" | "first-match" | "fold-pairs" | "fold-triples"
  | "bind" | "nth" | "resolve-tantra" | "char-at" | "join"
  | "format-triples" | "format-triples-primary"
  | "lt" | "le" | "gt" | "ge" -> 2
  | "pair" -> -1  (* 2 or 3 args *)
  | "edges" -> 1
  | "to-english" | "render-node"
  | "incoming-to" | "domain-of" | "iccha-status" | "abheda-of"
  | "flatten" | "sort-desc" | "unique" | "try-bigram" -> 1
  | "to-english-relation" -> 1
  | "avrti" | "context-score" | "append" -> 2
  | "spiral-domain" -> 3
  | "firstness-of-triple" | "rank-triples-by-intent" -> 2
  | "compose-answer" -> 3
  (* variable arity *)
  | "concat" | "and" | "or" -> -1
  | _ -> 0

let is_known_op name = op_arity name <> 0

(* is this token a boundary that stops argument collection? *)
let is_boundary = function
  | ")" | "in" | "otherwise" | "done" -> true
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
     | _ -> (LetIn (name, rhs, Var name), rest'))

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
            | [] -> failwith "parse_expr: empty"
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
                     failwith "parse_expr: empty"
                   else
                     collect_args (n - 1) (Var t0 :: acc) rest0)
        in
        let (args, rest') = collect_args arity [] rest in
        (Call (tok, args), rest')
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
  | _ ->
    (* no more branches, no otherwise — use VNone as default *)
    (Cond (List.rev branches, Var "_none"), tokens)

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
    else
      try Some (name, parse_expr_string text)
      with exn ->
        Printf.printf "warning: could not parse let binding '%s': %s [%s]\n%!" name (Printexc.to_string exn) (String.trim text);
        None
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
             let punit = match rest with u :: _ -> Some u | [] -> None in
             inputs := { tp_name = pname; tp_canonical = pname; tp_type = ptype; tp_unit = punit } :: !inputs
           | _ -> ())
        | "let" ->
          let_lines := line :: !let_lines
        | "return" ->
          let parts = String.split_on_char ' ' trimmed
                      |> List.filter (fun s -> String.length s > 0) in
          (match parts with
           | pname :: ptype :: rest ->
             let punit = match rest with u :: _ -> Some u | [] -> None in
             returns := { tp_name = pname; tp_canonical = pname; tp_type = ptype; tp_unit = punit } :: !returns
           | _ -> ())
        | _ -> ()
      end
    ) lines;

    (* parse the let block with multi-line support *)
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

(* ---- index builder ---- *)

(* recursively find all .tantra files *)
let tantra_files_recursive (root : string) : string list =
  let files = ref [] in
  let rec walk dir =
    try
      let entries = Sys.readdir dir in
      Array.iter (fun entry ->
        let path = Filename.concat dir entry in
        try
          if Sys.is_directory path then walk path
          else if Filename.check_suffix path ".tantra" then
            files := path :: !files
        with _ -> ()
      ) entries
    with _ -> ()
  in
  walk root;
  List.rev !files

let empty_index () : tantra_index = {
  by_name     = Hashtbl.create 64;
  by_output   = Hashtbl.create 64;
  by_input    = Hashtbl.create 64;
  constants   = Hashtbl.create 16;
  conversions = Hashtbl.create 16;
  all_tantras = ref [];
}

let add_to_list_table tbl key value =
  let existing = try Hashtbl.find tbl key with Not_found -> [] in
  Hashtbl.replace tbl key (value :: existing)

(* resolve canonical names for tantra params using the graph *)
let resolve_tantra_params (k : proof_graph) (t : tantra) : tantra =
  let resolve_param p =
    let canonical = Setu.resolve_to_canonical k p.tp_name in
    { p with tp_canonical = canonical }
  in
  { t with
    t_inputs = List.map resolve_param t.t_inputs;
    t_returns = List.map resolve_param t.t_returns }

let register_tantra_in_graph (k : proof_graph) (t : tantra) : unit =
  let input_edges = List.map (fun inp ->
    { source = t.t_name; target = inp.tp_name; relation = Sthita }
  ) t.t_inputs in
  let output_edges = List.map (fun ret ->
    { source = t.t_name; target = ret.tp_name; relation = Phala }
  ) t.t_returns in
  let all_edges = input_edges @ output_edges in
  let node : nigamana = {
    name = t.t_name; layer = "yantra"; slokas = [];
    edges = all_edges; satya = 0.0; shabda = "";
  } in
  (* only add if no existing node (don't overwrite sangati/kosha nodes) *)
  match Proof_graph.find k t.t_name with
  | Some existing ->
    (* merge edges: add Sthita/Phala edges from tantra to existing node *)
    let new_edges = List.filter (fun e ->
      not (List.exists (fun ex ->
        ex.source = e.source && ex.target = e.target && ex.relation = e.relation
      ) existing.edges)
    ) all_edges in
    if new_edges <> [] then begin
      let merged = { existing with edges = existing.edges @ new_edges } in
      ignore (Proof_graph.join k merged)
    end
  | None ->
    ignore (Proof_graph.join k node)

let register_tantra ?(graph : proof_graph option) (idx : tantra_index) (t : tantra) : unit =
  (* resolve canonical names if graph available *)
  let t = match graph with
    | Some k -> let t' = resolve_tantra_params k t in register_tantra_in_graph k t'; t'
    | None -> t
  in
  idx.all_tantras := t :: !(idx.all_tantras);
  Hashtbl.replace idx.by_name t.t_name t;
  (* index by return names — both tp_name and tp_canonical *)
  List.iter (fun ret ->
    add_to_list_table idx.by_output ret.tp_name t;
    if ret.tp_canonical <> ret.tp_name then
      add_to_list_table idx.by_output ret.tp_canonical t
  ) t.t_returns;
  (* index by input names — both tp_name and tp_canonical *)
  List.iter (fun inp ->
    add_to_list_table idx.by_input inp.tp_name t;
    if inp.tp_canonical <> inp.tp_name then
      add_to_list_table idx.by_input inp.tp_canonical t
  ) t.t_inputs;
  (* zero-input tantras with a single literal let = constants *)
  if t.t_inputs = [] then begin
    match t.t_lets with
    | [(_, Lit v)] ->
      Hashtbl.replace idx.constants t.t_name v;
      (* also register by return name *)
      List.iter (fun ret ->
        Hashtbl.replace idx.constants ret.tp_name v
      ) t.t_returns
    | _ -> ()
  end;
  (* conversion tantras: single input, single output, different units *)
  (match t.t_inputs, t.t_returns with
   | [inp], [ret] ->
     (match inp.tp_unit, ret.tp_unit with
      | Some u_in, Some u_out when u_in <> u_out ->
        Hashtbl.replace idx.conversions (u_in, u_out) t
      | _ -> ())
   | _ -> ())

let load_tantra_dir ?(graph : proof_graph option) (idx : tantra_index) (dir : string) : unit =
  let files = tantra_files_recursive dir in
  List.iter (fun path ->
    match parse_tantra_file path with
    | None -> ()
    | Some t -> register_tantra ?graph idx t
  ) files

let build_index ?(graph : proof_graph option) (dirs : string list) : tantra_index =
  let idx = empty_index () in
  (* collect all directories to search for tantras *)
  let searched = Hashtbl.create 16 in
  List.iter (fun dir ->
    let found_yantra = ref false in
    (* 1. look for yantra/ inside this dir *)
    let yantra_inside = Filename.concat dir "yantra" in
    if Sys.file_exists yantra_inside && Sys.is_directory yantra_inside
       && not (Hashtbl.mem searched yantra_inside) then begin
      Hashtbl.replace searched yantra_inside true;
      load_tantra_dir ?graph idx yantra_inside;
      found_yantra := true
    end;
    (* 2. look for yantra/ as sibling: ../yantra *)
    let parent = Filename.dirname dir in
    let yantra_sibling = Filename.concat parent "yantra" in
    if Sys.file_exists yantra_sibling && Sys.is_directory yantra_sibling
       && not (Hashtbl.mem searched yantra_sibling) then begin
      Hashtbl.replace searched yantra_sibling true;
      load_tantra_dir ?graph idx yantra_sibling;
      found_yantra := true
    end;
    (* 3. search the dir itself only if no yantra/ subdir was found
       (avoids double-loading when dir contains yantra/) *)
    if not !found_yantra && not (Hashtbl.mem searched dir) then begin
      Hashtbl.replace searched dir true;
      load_tantra_dir ?graph idx dir
    end
  ) dirs;
  idx

(* ---- alias loader ---- *)

(* loads the alias table from the "aliases" node in the graph *)
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

(* ---- classify + bigram for yantra ---- *)

(* yantra-specific token type *)
type ytoken =
  | YConcept  of string
  | YNumber   of float
  | YOperator of string
  | YGrammar  of visheshanam
  | YUnknown  of string

let classify_for_yantra (k : proof_graph) (word : string) : ytoken =
  (* for short words (1-2 chars), prioritize alias lookup over graph classification.
     e.g. "V" is volts in graph but "voltage" via alias, "F" is fahrenheit but "force" via alias.
     the alias captures the physics convention; the graph captures the unit symbol. *)
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
    | Setu.Article      -> YGrammar Sthita  (* articles are grammar noise for yantra *)
    | Setu.Unknown w    ->
      (* try alias resolution for longer words too *)
      match Hashtbl.find_opt alias_cache w with
      | Some full -> YConcept full
      | None -> YUnknown w

(* bigram joining: try joining adjacent concepts *)
(* try joining two names as a bigram: first try the resolved names, then original words *)
let try_bigram_join (k : proof_graph) (n1 : string) (n2 : string) (w1 : string) (w2 : string) : string option =
  let joined = n1 ^ "-" ^ n2 in
  match Hashtbl.find_opt k.nodes joined with
  | Some _ -> Some joined
  | None ->
    (* also try with the original words — "kinetic" + "energy" even if "energy" resolved to "work" *)
    let joined_raw = w1 ^ "-" ^ w2 in
    if joined_raw <> joined then
      match Hashtbl.find_opt k.nodes joined_raw with
      | Some _ -> Some joined_raw
      | None -> None
    else None

let join_bigrams (k : proof_graph) (tokens : (string * ytoken) list) : (string * ytoken) list =
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

(* ---- binding extractor ---- *)

(* extract (concept, value) bindings and identify the target concept *)
type extraction = {
  ex_bindings : binding list;
  ex_target   : string option;   (* what to solve for *)
}

(* simple-op tantras: basic arithmetic/scientific with generic parameter names.
   if a tantra's inputs are all generic names (a, b, base, exponent, angle, n, x)
   it's a simple op. if inputs have physics-specific names (mass, velocity, etc.)
   it's not simple. *)
let is_simple_tantra (t : tantra) : bool =
  let generic_names = ["a"; "b"; "c"; "n"; "x"; "base"; "exponent"; "angle";
                        "result"; "arg0"; "arg1"] in
  List.for_all (fun inp ->
    List.mem inp.tp_name generic_names
  ) t.t_inputs

(* question-target words: "find X", "what is the X", "calculate X" *)
let is_question_word w =
  w = "find" || w = "solve" || w = "calculate" || w = "compute" ||
  w = "determine" || w = "evaluate"

let is_question_grammar v =
  v = Drishthanta  (* "what" *)

let extract_bindings (k : proof_graph) (idx : tantra_index) (session : session)
    (tokens : (string * ytoken) list) : extraction =
  let bindings = ref [] in
  let target = ref None in
  let unbound_concepts = ref [] in

  let rec walk = function
    | [] -> ()
    (* Pattern: "concept is/= number" *)
    | (_, YConcept c) :: (_, YGrammar Swarupa) :: (_, YNumber n) :: rest
    | (_, YConcept c) :: (_, YOperator "=") :: (_, YNumber n) :: rest ->
      bindings := { b_name = c; b_value = n; b_unit = None } :: !bindings;
      walk rest
    (* Pattern: "alias = number" e.g. "f = 10" or "a = 9.8"
       handles YUnknown and YGrammar (e.g. "a" classified as article) *)
    | (w, YUnknown _) :: (_, YOperator "=") :: (_, YNumber n) :: rest
    | (w, YGrammar _) :: (_, YOperator "=") :: (_, YNumber n) :: rest ->
      let resolved = resolve_alias k w in
      bindings := { b_name = resolved; b_value = n; b_unit = None } :: !bindings;
      walk rest
    (* Pattern: "concept number" (no grammar between)
       BUT: if the concept resolves to a simple tantra (e.g. "plus" → "addition"),
       it's an operator, not a binding. Store the number as positional arg instead. *)
    | (_, YConcept c) :: (_, YNumber n) :: rest ->
      (* check if this concept is an operator by looking up its tantra and
         checking if the tantra has generic inputs (a, b, x, etc.) *)
      let is_op_concept =
        let direct = Hashtbl.find_opt idx.by_name c in
        let via_graph = match direct with
          | Some _ -> direct
          | None ->
            (* walk abheda to find tantra *)
            let resolved = Setu.resolve k c in
            List.find_map (fun name ->
              Hashtbl.find_opt idx.by_name name
            ) resolved
        in
        match via_graph with
        | Some t -> is_simple_tantra t
        | None -> false
      in
      if is_op_concept then begin
        (* this concept is an operator — store the number positionally *)
        unbound_concepts := c :: !unbound_concepts;
        let idx_n = List.length !bindings in
        let name = Printf.sprintf "arg%d" idx_n in
        bindings := { b_name = name; b_value = n; b_unit = None } :: !bindings;
        walk rest
      end else begin
        bindings := { b_name = c; b_value = n; b_unit = None } :: !bindings;
        walk rest
      end
    (* Pattern: "concept when ..." — "when" after a concept means "given that",
       not a question. Set the concept as target, skip the "when". *)
    | (_, YConcept c) :: (w, YGrammar v) :: rest
      when is_question_grammar v && w = "when" && !target = None ->
      target := Some c;
      walk rest
    (* Pattern: question words → next concept is target (only if no target set yet) *)
    | (w, YGrammar v) :: rest when is_question_grammar v && !target = None ->
      (* "what is the X" — skip grammar, find next concept *)
      let rec find_target = function
        | (_, YConcept c) :: rest' ->
          target := Some c;
          walk rest'
        | (_, YGrammar _) :: rest' -> find_target rest'
        | other -> walk other
      in
      ignore w;
      find_target rest
    | (w, YConcept _) :: rest when is_question_word w && !target = None ->
      (* "find X" — next concept is target *)
      let rec find_target = function
        | (_, YConcept c) :: rest' ->
          target := Some c;
          walk rest'
        | (_, YGrammar _) :: rest' -> find_target rest'
        | other -> walk other
      in
      find_target rest
    (* Unbound concept — candidate for target or operation *)
    | (_, YConcept c) :: rest ->
      unbound_concepts := c :: !unbound_concepts;
      walk rest
    (* Skip grammar, operators, articles *)
    | (_, YGrammar _) :: rest -> walk rest
    | (_, YOperator _) :: rest -> walk rest
    (* Positional numbers without preceding concept *)
    | (_, YNumber n) :: rest ->
      (* store as positional arg *)
      let idx_n = List.length !bindings in
      let name = Printf.sprintf "arg%d" idx_n in
      bindings := { b_name = name; b_value = n; b_unit = None } :: !bindings;
      walk rest
    | (_, YUnknown _) :: rest -> walk rest
  in
  walk tokens;

  (* if no target identified, use the first unbound concept that matches
     a tantra name or output (with graph resolution) *)
  let target =
    match !target with
    | Some _ as t -> t
    | None ->
      let unbound = List.rev !unbound_concepts in
      List.find_map (fun c ->
        if Hashtbl.mem idx.by_name c then Some c
        else if Hashtbl.mem idx.by_output c then Some c
        else begin
          (* try graph walk *)
          let resolved = Setu.resolve k c in
          List.find_map (fun name ->
            if Hashtbl.mem idx.by_name name then Some name
            else if Hashtbl.mem idx.by_output name then Some name
            else None
          ) resolved
        end
      ) unbound
  in

  (* merge session bindings — session values are used if not overridden *)
  let bound_names = List.map (fun b -> b.b_name) !bindings in
  let session_additions = List.filter (fun sb ->
    not (List.mem sb.b_name bound_names)
  ) session.bindings in

  { ex_bindings = List.rev !bindings @ session_additions;
    ex_target = target }

(* ---- tantra resolver ---- *)

type chain_step =
  | CForward of tantra * (string * float) list
  | CInverse of tantra * string * (string * expr) list * (string * float) list

type resolution =
  | Direct  of tantra * (string * float) list   (* tantra, input assignments *)
  | Inverse of tantra * string * (string * expr) list * (string * float) list
    (* tantra, target var, inverted eval plan, all known name-value pairs *)
  | Chain   of chain_step list                   (* cross-tantra chain *)
  | NotFound of string                           (* reason *)

(* check if all tantra inputs can be satisfied by the bindings.
   matching uses canonical names (resolved at parse time) so no graph walks needed. *)
let try_match_inputs (_k : proof_graph) (tantra : tantra) (bindings : binding list)
    (idx : tantra_index) : (string * float) list option =
  let find_binding (inp : tantra_param) : float option =
    (* exact match on tp_name or tp_canonical *)
    match List.find_opt (fun b ->
      b.b_name = inp.tp_name || b.b_name = inp.tp_canonical
    ) bindings with
    | Some b -> Some b.b_value
    | None ->
      (* partial compound match: binding "velocity" matches input "initial-velocity"
         only when the binding name is a simple word that's a component of
         the compound input name — never the reverse *)
      let parts = String.split_on_char '-' inp.tp_name in
      let canon_parts = String.split_on_char '-' inp.tp_canonical in
      match List.find_opt (fun b ->
        not (String.contains b.b_name '-') &&
        (List.mem b.b_name parts || List.mem b.b_name canon_parts)
      ) bindings with
      | Some b -> Some b.b_value
      | None ->
        (* try constant from index *)
        match Hashtbl.find_opt idx.constants inp.tp_name with
        | Some _ as hit -> hit
        | None -> Hashtbl.find_opt idx.constants inp.tp_canonical
  in
  (* try positional fallback: map arg0→first input, arg1→second, etc. *)
  let find_binding_positional (i : int) (inp : tantra_param) : float option =
    match find_binding inp with
    | Some _ as hit -> hit
    | None ->
      let argname = Printf.sprintf "arg%d" i in
      match List.find_opt (fun b -> b.b_name = argname) bindings with
      | Some b -> Some b.b_value
      | None -> None
  in
  let assignments = List.mapi (fun i inp ->
    match find_binding_positional i inp with
    | Some v -> Some (inp.tp_name, v)
    | None -> None
  ) tantra.t_inputs in
  let assignments = List.filter_map Fun.id assignments in
  if List.length assignments = List.length tantra.t_inputs then
    Some assignments
  else None

(* ---- graph-based inversion ---- *)

(* cached eval→graph-node mapping, loaded once from ganana-setu *)
let eval_to_node : (string, string) Hashtbl.t = Hashtbl.create 32
let eval_mapping_loaded = ref false

let load_eval_mapping (k : proof_graph) : unit =
  if not !eval_mapping_loaded then begin
    eval_mapping_loaded := true;
    let pairs = Setu.read_shabda k "ganana-setu" in
    List.iter (fun (eval_name, node_name) ->
      Hashtbl.replace eval_to_node eval_name node_name
    ) pairs
  end

(* collect all variable names referenced in an expression *)
let rec free_vars : expr -> string list = function
  | Var v -> [v]
  | Call (_, args) -> List.concat_map free_vars args
  | Lit _ | StrLit _ | BoolLit _ -> []
  | LetIn (_, rhs, body) -> free_vars rhs @ free_vars body
  | Lambda (params, body) ->
    List.filter (fun v -> not (List.mem v params)) (free_vars body)
  | Cond (branches, ow) ->
    List.concat_map (fun (g,b) -> free_vars g @ free_vars b) branches @ free_vars ow
  | ListExpr items -> List.concat_map free_vars items

let mentions_var name e = List.mem name (free_vars e)
let is_var_named name = function Var v -> v = name | _ -> false

(* look up inverse operation from graph shabda *)
let graph_invert (k : proof_graph) (op : string) (arg_pos : int)
    (result_expr : expr) (other_expr : expr) (first_expr : expr option)
    : expr option =
  load_eval_mapping k;
  let node_name = match Hashtbl.find_opt eval_to_node op with
    | Some n -> n | None -> op in
  let pairs = Setu.read_shabda k node_name in
  let key = Printf.sprintf "pratipaksha-%d" arg_pos in
  match List.assoc_opt key pairs with
  | None ->
    (* try walking Pratipaksha edges from the graph node *)
    (match Proof_graph.find k node_name with
     | None -> None
     | Some n ->
       let inv_node = List.find_map (fun edge ->
         if edge.source = node_name && edge.relation = Pratipaksha then
           Some edge.target
         else None
       ) n.edges in
       match inv_node with
       | None -> None
       | Some inv_name ->
         (* read the inverse node's eval name *)
         let inv_pairs = Setu.read_shabda k inv_name in
         let inv_eval = match List.assoc_opt "eval" inv_pairs with
           | Some e -> e | None -> inv_name in
         (* for Pratipaksha edge, default: same args as original but swapped result *)
         Some (Call (inv_eval, [result_expr; other_expr])))
  | Some inv_eval_name ->
    (* check for compound inverse (like power→power with reciprocal exponent) *)
    let compound_key = Printf.sprintf "pratipaksha-%d-compound" arg_pos in
    let is_compound = List.assoc_opt compound_key pairs = Some "true" in
    if is_compound && op = "power" && arg_pos = 0 then
      (* a^b = r → a = r^(1/b) *)
      Some (Call ("power", [result_expr; Call ("div", [Lit 1.0; other_expr])]))
    else begin
      (* check if the inverse op for this position uses flipped args *)
      let flip_key = Printf.sprintf "pratipaksha-%d-flip" arg_pos in
      let flipped = List.assoc_opt flip_key pairs = Some "true" in
      (* read arity of the inverse operation *)
      let inv_node_name = match Hashtbl.find_opt eval_to_node inv_eval_name with
        | Some n -> n | None -> inv_eval_name in
      let inv_pairs = Setu.read_shabda k inv_node_name in
      let inv_arity = match List.assoc_opt "arity" inv_pairs with
        | Some s -> (match int_of_string_opt s with Some n -> n | None -> 2)
        | None -> 2 in
      if inv_arity = 1 then
        Some (Call (inv_eval_name, [result_expr]))
      else if flipped then
        match first_expr with
        | Some fe -> Some (Call (inv_eval_name, [fe; result_expr]))
        | None -> None
      else
        Some (Call (inv_eval_name, [result_expr; other_expr]))
    end

(* invert a single let binding for a target variable — recursive descent for nested exprs *)
let rec invert_binding (k : proof_graph) (rhs : expr) (target : string) (result_expr : expr) : expr option =
  match rhs with
  | Call (op, [arg0; arg1]) ->
    let target_in_0 = mentions_var target arg0 in
    let target_in_1 = mentions_var target arg1 in
    if target_in_0 && is_var_named target arg0 then
      graph_invert k op 0 result_expr arg1 (Some arg0)
    else if target_in_1 && is_var_named target arg1 then
      graph_invert k op 1 result_expr arg0 (Some arg1)
    else if target_in_0 then begin
      (* target is nested in arg0 — invert top level, then recurse *)
      match graph_invert k op 0 result_expr arg1 (Some arg0) with
      | Some intermediate -> invert_binding k arg0 target intermediate
      | None -> None
    end else if target_in_1 then begin
      match graph_invert k op 1 result_expr arg0 (Some arg1) with
      | Some intermediate -> invert_binding k arg1 target intermediate
      | None -> None
    end else None
  | Call (op, [arg0]) ->
    if is_var_named target arg0 then
      graph_invert k op 0 result_expr arg0 None
    else if mentions_var target arg0 then begin
      match graph_invert k op 0 result_expr arg0 None with
      | Some intermediate -> invert_binding k arg0 target intermediate
      | None -> None
    end else None
  | Var v when v = target -> Some result_expr
  | _ -> None

(* build dependency map: for each let-binding, which variables does it reference? *)
let build_dep_map lets =
  let tbl = Hashtbl.create 16 in
  List.iter (fun (name, rhs) ->
    Hashtbl.replace tbl name (List.sort_uniq String.compare (free_vars rhs))
  ) lets; tbl

(* invert through a multi-step let block.
   given a chain of let bindings, known input names, a target variable,
   and the output variable, produce an inverted evaluation plan. *)
let invert_chain (k : proof_graph) (lets : (string * expr) list)
    (known_names : string list) (target : string) (output_var : string)
    : (string * expr) list option =
  let dep_map = build_dep_map lets in
  let let_map = Hashtbl.create 16 in
  List.iter (fun (n, e) -> Hashtbl.replace let_map n e) lets;

  (* find backward path: output_var → ... → binding that uses target *)
  let rec find_path visited node =
    if List.mem node visited then None
    else
      match Hashtbl.find_opt let_map node with
      | None -> None
      | Some rhs ->
        if mentions_var target rhs then Some [node]
        else
          let deps = try Hashtbl.find dep_map node with Not_found -> [] in
          let let_deps = List.filter (Hashtbl.mem let_map) deps in
          List.find_map (fun dep ->
            match find_path (node :: visited) dep with
            | Some path -> Some (node :: path)
            | None -> None
          ) let_deps
  in

  match find_path [] output_var with
  | None -> None
  | Some path ->
    (* 1. collect forward-computable bindings NOT on the path *)
    let fwd = List.filter_map (fun (name, rhs) ->
      if List.mem name path then None
      else
        let deps = free_vars rhs in
        if List.for_all (fun d -> List.mem d known_names || Hashtbl.mem let_map d) deps
        then Some (name, rhs) else None
    ) lets in
    (* filter fwd to only include bindings whose deps are all known or other fwd bindings *)
    let fwd_names = List.map fst fwd in
    let fwd = List.filter (fun (_name, rhs) ->
      let deps = free_vars rhs in
      List.for_all (fun d ->
        List.mem d known_names || List.mem d fwd_names
      ) deps
    ) fwd in
    (* 2. invert along the path *)
    let rec invert_path = function
      | [] -> Some []
      | [binding_name] ->
        (match Hashtbl.find_opt let_map binding_name with
         | Some rhs -> (match invert_binding k rhs target (Var binding_name) with
           | Some inv -> Some [(target, inv)]
           | None -> None)
         | None -> None)
      | outer :: inner :: rest ->
        (match Hashtbl.find_opt let_map outer with
         | Some rhs -> (match invert_binding k rhs inner (Var outer) with
           | Some inv ->
             (match invert_path (inner :: rest) with
              | Some more -> Some ((inner, inv) :: more)
              | None -> None)
           | None -> None)
         | None -> None)
    in
    match invert_path path with
    | None -> None
    | Some inv_steps -> Some (fwd @ inv_steps)

(* global graph ref for graph-based inversion from legacy call sites *)
let _graph_ref : proof_graph option ref = ref None

(* value coercions — needed by chain_resolve before eval is defined *)
let new_env () : env = Hashtbl.create 16

let as_float = function
  | VFloat f -> f
  | VString s -> (match float_of_string_opt s with Some f -> f | None -> 0.0)
  | VBool b -> if b then 1.0 else 0.0
  | _ -> 0.0

let rec as_string = function
  | VString s -> s
  | VFloat f ->
    if Float.is_integer f && Float.is_finite f then
      Printf.sprintf "%g" f
    else Printf.sprintf "%g" f
  | VBool b -> if b then "true" else "false"
  | VNode n -> n
  | VPair (n, v) -> Printf.sprintf "(%s . %s)" n (as_string v)
  | VBinding (n, v) -> Printf.sprintf "%s=%g" n v
  | VNone -> ""
  | VList items ->
    "[" ^ String.concat ", " (List.map as_string items) ^ "]"
  | VFn _ -> "<fn>"

let as_bool = function
  | VBool b -> b
  | VNone -> false
  | VFloat f -> f <> 0.0
  | VString s -> String.length s > 0
  | VList l -> l <> []
  | VNode _ -> true
  | VPair _ -> true
  | VBinding _ -> true
  | VFn _ -> true

let as_list = function
  | VList l -> l
  | VNone -> []
  | v -> [v]

(* forward ref for eval — needed by chain_resolve before eval is defined *)
let _eval_chain_ref : (proof_graph -> env -> expr -> value) ref =
  ref (fun _ _ _ -> VNone)
let _eval_tantra_chain_ref : (proof_graph -> tantra -> (string * value) list -> value) ref =
  ref (fun _ _ _ -> VNone)

let rec resolve_tantra (k : proof_graph) (idx : tantra_index) (bindings : binding list)
    (target : string) : resolution =
  (* helper: flexible name matching for inversion *)
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

  (* 1. DIRECT — tantra name or output name matches target, inputs satisfied *)
  let try_direct () =
    let candidates =
      (match Hashtbl.find_opt idx.by_name target with Some t -> [t] | None -> []) @
      (match Hashtbl.find_opt idx.by_output target with Some l -> l | None -> [])
    in
    List.find_map (fun t ->
      match try_match_inputs k t bindings idx with
      | Some assignments -> Some (Direct (t, assignments))
      | None -> None
    ) candidates
  in

  (* 2. INVERSE — target is an INPUT of a tantra whose OUTPUT we have *)
  let try_inverse () =
    let inverse_candidates =
      match Hashtbl.find_opt idx.by_input target with
      | Some l when l <> [] -> l
      | _ ->
        List.filter (fun t ->
          List.exists (fun inp ->
            names_match inp.tp_name target || names_match inp.tp_canonical target
          ) t.t_inputs
        ) !(idx.all_tantras)
    in
    List.find_map (fun t ->
      let target_inp = List.find_opt (fun inp ->
        inp.tp_name = target || inp.tp_canonical = target ||
        names_match inp.tp_name target || names_match inp.tp_canonical target
      ) t.t_inputs in
      match target_inp with
      | None -> None
      | Some target_inp ->
        let target_inp_name = target_inp.tp_name in
        (* do we have the OUTPUT? *)
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
        match output_bound with
        | None -> None
        | Some (result_name, result_value) ->
          let other_inputs = List.filter (fun inp ->
            inp.tp_name <> target_inp_name) t.t_inputs in
          let other_values = List.filter_map (fun inp ->
            match List.find_opt (fun b -> names_match b.b_name inp.tp_name) bindings with
            | Some b -> Some (inp.tp_name, b.b_value)
            | None -> Hashtbl.find_opt idx.constants inp.tp_name
                      |> Option.map (fun v -> (inp.tp_name, v))
          ) other_inputs in
          if List.length other_values <> List.length other_inputs then None
          else begin
            let known_values = (result_name, result_value) :: other_values in
            let ret_binding_name = match List.find_opt (fun (name, _) ->
              name = result_name ||
              List.exists (fun ret -> ret.tp_name = name) t.t_returns
            ) t.t_lets with
            | Some (name, _) -> name | None -> result_name in
            let known_names = List.map fst known_values in
            let known_with_inputs = known_names @
              List.map (fun inp -> inp.tp_name) other_inputs in
            match invert_chain k t.t_lets known_with_inputs
                    target_inp_name ret_binding_name with
            | Some plan -> Some (Inverse (t, target, plan, known_values))
            | None -> None
          end
    ) inverse_candidates
  in

  (* 3. GRAPH — target resolves to a known output via abheda *)
  let try_graph () =
    let resolved = Setu.resolve k target in
    let candidates = List.concat_map (fun name ->
      match Hashtbl.find_opt idx.by_output name with Some l -> l | None -> []
    ) resolved in
    List.find_map (fun t ->
      match try_match_inputs k t bindings idx with
      | Some assignments -> Some (Direct (t, assignments))
      | None -> None
    ) candidates
  in

  (* 4. CHAIN — BFS through multiple tantras *)
  let try_chain () =
    match chain_resolve k idx bindings target with
    | Some steps -> Some (Chain steps)
    | None -> None
  in

  (* try strategies in order *)
  match try_direct () with
  | Some r -> r
  | None ->
    match try_inverse () with
    | Some r -> r
    | None ->
      match try_graph () with
      | Some r -> r
      | None ->
        match try_chain () with
        | Some r -> r
        | None -> NotFound (Printf.sprintf "no tantra found for target '%s'" target)

(* ---- cross-tantra BFS chain ---- *)

(* cheap name matching for chain resolution — exact or suffix match only *)
and names_match_fast (a : string) (b : string) : bool =
  a = b

(* resolved name match — uses canonical resolution via graph *)
and names_match_resolved (k : proof_graph) (a : string) (b : string) : bool =
  names_match_fast a b ||
  let ca = Setu.resolve_to_canonical k a in
  let cb = Setu.resolve_to_canonical k b in
  ca = cb || ca = b || a = cb

(* chain input matching — exact on canonical names, no graph walks.
   canonical names are resolved at tantra parse time. *)
and try_match_chain (_k : proof_graph) (t : tantra) (known : binding list) (idx : tantra_index)
    : (string * float) list option =
  let find_binding (inp : tantra_param) : float option =
    (* exact match on tp_name or tp_canonical *)
    match List.find_opt (fun b ->
      b.b_name = inp.tp_name || b.b_name = inp.tp_canonical
    ) known with
    | Some b -> Some b.b_value
    | None ->
      match Hashtbl.find_opt idx.constants inp.tp_name with
      | Some _ as hit -> hit
      | None -> Hashtbl.find_opt idx.constants inp.tp_canonical
  in
  let assignments = List.map (fun inp ->
    match find_binding inp with
    | Some v -> Some (inp.tp_name, v)
    | None -> None
  ) t.t_inputs in
  let assignments = List.filter_map Fun.id assignments in
  if List.length assignments = List.length t.t_inputs then Some assignments
  else None

(* find tantras that COULD produce a given concept name *)
and tantras_producing (idx : tantra_index) (name : string) : tantra list =
  let by_out = match Hashtbl.find_opt idx.by_output name with Some l -> l | None -> [] in
  let by_name = match Hashtbl.find_opt idx.by_name name with Some t -> [t] | None -> [] in
  let combined = by_out @ by_name in
  if combined <> [] then combined
  else
    List.filter (fun t ->
      t.t_name = name ||
      List.exists (fun ret ->
        names_match_fast ret.tp_name name || names_match_fast ret.tp_canonical name
      ) t.t_returns
    ) !(idx.all_tantras)

(* find tantras that USE a given concept as input or produce it as output *)
and tantras_consuming (idx : tantra_index) (name : string) : tantra list =
  let by_inp = match Hashtbl.find_opt idx.by_input name with Some l -> l | None -> [] in
  let by_out = match Hashtbl.find_opt idx.by_output name with Some l -> l | None -> [] in
  let by_name = match Hashtbl.find_opt idx.by_name name with Some t -> [t] | None -> [] in
  let combined = by_inp @ by_out @ by_name in
  if combined <> [] then combined
  else
    List.filter (fun t ->
      t.t_name = name ||
      List.exists (fun inp ->
        names_match_fast inp.tp_name name || names_match_fast inp.tp_canonical name
      ) t.t_inputs ||
      List.exists (fun ret ->
        names_match_fast ret.tp_name name || names_match_fast ret.tp_canonical name
      ) t.t_returns
    ) !(idx.all_tantras)

and chain_resolve (k : proof_graph) (idx : tantra_index) (bindings : binding list)
    (target : string) : chain_step list option =
  let max_depth = 4 in

  (* build a set of candidate tantras: those reachable from knowns or target *)
  let known_names = List.map (fun b -> b.b_name) bindings in
  (* also compute canonical equivalents of known names for index lookup *)
  let known_names_expanded = List.concat_map (fun name ->
    let canon = Setu.resolve_to_canonical k name in
    if canon <> name then [name; canon] else [name]
  ) known_names in
  let candidate_tantras =
    let from_target = tantras_producing idx target in
    let from_knowns = List.concat_map (fun name ->
      tantras_consuming idx name
    ) known_names_expanded in
    (* also add tantras whose outputs feed into target-producing tantras *)
    let target_inputs = List.concat_map (fun t ->
      List.concat_map (fun inp ->
        if inp.tp_canonical <> inp.tp_name
        then [inp.tp_name; inp.tp_canonical]
        else [inp.tp_name]
      ) t.t_inputs
    ) from_target in
    let bridge = List.concat_map (fun name ->
      tantras_producing idx name
    ) target_inputs in
    (* deduplicate by name *)
    let seen = Hashtbl.create 16 in
    List.filter (fun t ->
      if Hashtbl.mem seen t.t_name then false
      else (Hashtbl.replace seen t.t_name true; true)
    ) (from_target @ from_knowns @ bridge)
  in

  (* BFS with queue — explore level by level, not depth-first *)
  let queue = Queue.create () in
  Queue.push (bindings, [], 0) queue;
  let found = ref None in
  while not (Queue.is_empty queue) && !found = None do
    let (known, steps, depth) = Queue.pop queue in
    if depth > max_depth then ()
    else begin
      let knames = List.map (fun b -> b.b_name) known in
      (* check: is target now known? *)
      if List.exists (fun n -> names_match_fast n target) knames then
        found := Some (List.rev steps)
      else begin
        (* 1. try direct: tantra that produces target with current knowns *)
        let direct_done = ref false in
        List.iter (fun t ->
          if !found <> None || !direct_done then ()
          else
            let produces_target = List.exists (fun ret ->
              names_match_fast ret.tp_name target ||
              names_match_fast ret.tp_canonical target ||
              names_match_fast t.t_name target
            ) t.t_returns in
            if produces_target then
              match try_match_chain k t known idx with
              | Some assignments ->
                found := Some (List.rev (CForward (t, assignments) :: steps));
                direct_done := true
              | None -> ()
        ) candidate_tantras;

        if !found = None then begin
          (* 2. forward: tantras whose inputs are all satisfied *)
          List.iter (fun t ->
            if !found <> None then ()
            else
              match try_match_chain k t known idx with
              | Some assignments ->
                let produces_new = List.exists (fun ret ->
                  not (List.exists (fun n -> names_match_fast n ret.tp_name) knames)
                ) t.t_returns in
                if produces_new then begin
                  let input_values = List.map (fun (n, f) -> (n, VFloat f)) assignments in
                  (try
                    let result = !_eval_tantra_chain_ref k t input_values in
                    let new_bindings = match t.t_returns with
                      | [ret] ->
                        let v = as_float result in
                        let base = [{ b_name = ret.tp_name; b_value = v;
                                      b_unit = ret.tp_unit }] in
                        (* also store under tantra name + last component as aliases *)
                        let aliases = ref base in
                        if t.t_name <> ret.tp_name then
                          aliases := { b_name = t.t_name; b_value = v; b_unit = ret.tp_unit } :: !aliases;
                        (* canonical name of return param *)
                        if ret.tp_canonical <> ret.tp_name && ret.tp_canonical <> t.t_name then
                          aliases := { b_name = ret.tp_canonical; b_value = v; b_unit = ret.tp_unit } :: !aliases;
                        (* last component: "final-velocity" → "velocity" *)
                        (match String.rindex_opt t.t_name '-' with
                         | Some i ->
                           let last = String.sub t.t_name (i+1) (String.length t.t_name - i - 1) in
                           if last <> ret.tp_name && last <> t.t_name then
                             aliases := { b_name = last; b_value = v; b_unit = ret.tp_unit } :: !aliases
                         | None -> ());
                        !aliases
                      | rets ->
                        let values = as_list result in
                        List.mapi (fun i ret ->
                          let v = if i < List.length values then List.nth values i
                                  else VNone in
                          { b_name = ret.tp_name; b_value = as_float v;
                            b_unit = ret.tp_unit }
                        ) rets
                    in
                    Queue.push (known @ new_bindings,
                                CForward (t, assignments) :: steps,
                                depth + 1) queue
                  with _ -> ())
                end
              | None -> ()
          ) candidate_tantras;

          (* 3. inverse: tantra whose output we have, missing one input *)
          List.iter (fun t ->
            if !found <> None then ()
            else
              List.iter (fun (ret : tantra_param) ->
                if !found <> None then ()
                else
                  let output_binding = List.find_opt (fun b ->
                    names_match_resolved k b.b_name ret.tp_name ||
                    names_match_resolved k b.b_name ret.tp_canonical ||
                    names_match_resolved k b.b_name t.t_name
                  ) known in
                  match output_binding with
                  | None -> ()
                  | Some ob ->
                    let missing = List.filter (fun inp ->
                      not (List.exists (fun b ->
                        names_match_resolved k b.b_name inp.tp_name ||
                        names_match_resolved k b.b_name inp.tp_canonical
                      ) known) &&
                      Hashtbl.find_opt idx.constants inp.tp_name = None &&
                      Hashtbl.find_opt idx.constants inp.tp_canonical = None
                    ) t.t_inputs in
                    match missing with
                    | [missing_inp] ->
                      let other_inputs = List.filter (fun inp ->
                        inp.tp_name <> missing_inp.tp_name
                      ) t.t_inputs in
                      let other_values = List.filter_map (fun (inp : tantra_param) ->
                        match List.find_opt (fun b ->
                          names_match_resolved k b.b_name inp.tp_name
                        ) known with
                        | Some b -> Some (inp.tp_name, b.b_value)
                        | None ->
                          match Hashtbl.find_opt idx.constants inp.tp_name with
                          | Some v -> Some (inp.tp_name, v)
                          | None -> None
                      ) other_inputs in
                      if List.length other_values = List.length other_inputs then begin
                        let ret_name = ret.tp_name in
                        let known_values = (ret_name, ob.b_value) :: other_values in
                        let known_names_for_inv = List.map fst known_values @
                          List.map (fun inp -> inp.tp_name) other_inputs in
                        match invert_chain k t.t_lets known_names_for_inv
                                missing_inp.tp_name ret_name with
                        | Some plan ->
                          let env = new_env () in
                          List.iter (fun (n, f) ->
                            Hashtbl.replace env n (VFloat f)) known_values;
                          (try
                            List.iter (fun (n, rhs) ->
                              let v = !_eval_chain_ref k env rhs in
                              Hashtbl.replace env n v
                            ) plan;
                            let result_v = match Hashtbl.find_opt env missing_inp.tp_name with
                              | Some v -> as_float v | None -> 0.0 in
                            let new_b = { b_name = missing_inp.tp_name;
                                          b_value = result_v;
                                          b_unit = missing_inp.tp_unit } in
                            Queue.push (new_b :: known,
                                        CInverse (t, missing_inp.tp_name, plan, known_values) :: steps,
                                        depth + 1) queue
                          with _ -> ())
                        | None -> ()
                      end
                    | _ -> ()
              ) t.t_returns
          ) candidate_tantras
        end
      end
    end
  done;
  !found

(* ---- internal evaluator ---- *)
(* evaluates tantra expressions directly, with access to the proof graph. *)

(* runtime context — gives evaluator access to the tantra index and session
   without changing the eval signature everywhere. set before calling eval_tantra. *)
type eval_context = {
  ctx_index   : tantra_index;
  ctx_session : session;
}
let eval_ctx : eval_context option ref = ref None

(* forward references for functions defined later in the file.
   the evaluator needs to call yantra pipeline functions (tokenise, classify, etc.)
   which depend on types only available after the evaluator. resolved at module init. *)
let _yantra_tokenise_ref : (string -> string list) ref = ref (fun _ -> [])
let _classify_for_yantra_ref : (proof_graph -> string -> ytoken) ref = ref (fun _ _ -> YUnknown "")
let _join_bigrams_ref : (proof_graph -> (string * ytoken) list -> (string * ytoken) list) ref =
  ref (fun _ tokens -> tokens)
let _extract_bindings_ref : (proof_graph -> tantra_index -> session ->
  (string * ytoken) list -> extraction) ref =
  ref (fun _ _ _ _ -> { ex_bindings = []; ex_target = None })
let _resolve_concept_to_tantra_ref : (proof_graph -> tantra_index -> string -> string option) ref =
  ref (fun _ _ _ -> None)
let _resolve_tantra_ref : (proof_graph -> tantra_index -> binding list -> string -> resolution) ref =
  ref (fun _ _ _ target -> NotFound (Printf.sprintf "not initialized: %s" target))
let _eval_tantra_ref : (proof_graph -> tantra -> (string * value) list -> value) ref =
  ref (fun _ _ _ -> VNone)
(* tracks the last tantra name used by invoke-tantra for result attribution *)
let last_invoked_tantra : string ref = ref ""

let env_copy (e : env) : env =
  let e2 = Hashtbl.create (Hashtbl.length e) in
  Hashtbl.iter (fun k v -> Hashtbl.replace e2 k v) e;
  e2

(* the evaluator *)
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

and eval_call (k : proof_graph) (e : env) (op : string) (args : expr list) : value =
  match op with

  (* ---- graph operations ---- *)

  (* lookup: string → VNode if found, VNone if not — raw table hit only *)
  | "lookup" ->
    let name = as_string (eval k e (List.nth args 0)) in
    (match Proof_graph.find k name with
     | Some _ -> VNode name
     | None   -> VNone)

  (* walk: node × relation → [node] — follow edges of a given type *)
  | "walk" ->
    let node_name = as_string (eval k e (List.nth args 0)) in
    let rel_name = as_string (eval k e (List.nth args 1)) in
    let rel = Proof_graph.visheshanam_of_string rel_name in
    (match rel with
     | None -> VList []
     | Some vish ->
       let edges = Proof_graph.edges_of k node_name in
       let targets = List.filter_map (fun edge ->
         if edge.relation = vish && edge.source = node_name then
           Some (VNode edge.target)
         else None
       ) edges in
       VList targets)

  (* walk-in: node × relation → [node] — follow INCOMING edges *)
  | "walk-in" ->
    let node_name = as_string (eval k e (List.nth args 0)) in
    let rel_name = as_string (eval k e (List.nth args 1)) in
    let rel = Proof_graph.visheshanam_of_string rel_name in
    (match rel with
     | None -> VList []
     | Some vish ->
       let edges = Proof_graph.edges_of k node_name in
       let sources = List.filter_map (fun edge ->
         if edge.relation = vish && edge.target = node_name then
           Some (VNode edge.source)
         else None
       ) edges in
       VList sources)

  (* has: node × edge-pattern → bool
     edge-pattern is "relation-target" e.g. "matra-sthita" *)
  | "has" ->
    let node_name = as_string (eval k e (List.nth args 0)) in
    let pattern = as_string (eval k e (List.nth args 1)) in
    (* parse "relation-target" from the compound: e.g. "matra-sthita" means
       does this node have a sthita edge to matra?
       or: does the node's slokas contain this compound? *)
    let edges = Proof_graph.edges_of k node_name in
    (* try parsing as target-relation compound *)
    let parts = String.split_on_char '-' pattern in
    let found = match List.rev parts with
      | rel_str :: target_parts ->
        let target = String.concat "-" (List.rev target_parts) in
        let rel = Proof_graph.visheshanam_of_string rel_str in
        (match rel with
         | Some vish ->
           List.exists (fun edge ->
             edge.relation = vish && edge.source = node_name && edge.target = target
           ) edges
         | None ->
           (* try the other way: first part is target, rest is relation *)
           let rel2 = Proof_graph.visheshanam_of_string (List.hd parts) in
           match rel2 with
           | Some vish ->
             let target2 = String.concat "-" (List.tl parts) in
             List.exists (fun edge ->
               edge.relation = vish && edge.source = node_name && edge.target = target2
             ) edges
           | None -> false)
      | [] -> false
    in
    VBool found

  (* edges: node → [(source, relation, target)] as list of strings *)
  | "edges" ->
    let node_name = as_string (eval k e (List.nth args 0)) in
    let edges = Proof_graph.edges_of k node_name in
    VList (List.map (fun edge ->
      VList [VString edge.source;
             VString (Proof_graph.string_of_visheshanam edge.relation);
             VString edge.target]
    ) edges)

  (* to-english: node-name → English name
     dispatches to to-english.tantra if loaded; falls back to shabda "name" field,
     then node name if node exists, otherwise returns "asprista".
     no reverse-abheda hunting. *)
  | "to-english" ->
     let name = as_string (eval k e (List.nth args 0)) in
     (match !eval_ctx with
      | Some ctx ->
        (match Hashtbl.find_opt ctx.ctx_index.by_name "to-english" with
         | Some t ->
            let result = !_eval_tantra_ref k t [("node", VString name)] in
            (match result with
            | VString s when String.length s > 0 -> VString s
            | _ -> VString "asprista")
         | None ->
           (* tantra not loaded yet — use shabda "name", then node if known *)
           let pairs = Setu.read_shabda k name in
            (match List.assoc_opt "name" pairs with
            | Some v -> VString v
            | None   ->
              (match Hashtbl.find_opt k.nodes name with
               | Some _ -> VString name
               | None -> VString "asprista")))
      | None -> VString "asprista")

  (* describe: node-name → shabda description string (the part after /) *)
  | "describe" ->
    let name = as_string (eval k e (List.nth args 0)) in
    (match Hashtbl.find_opt k.nodes name with
     | None -> VString ""
     | Some n ->
       let s = n.shabda in
       (* shabda format: "english-name / description-text" — extract after / *)
       match String.split_on_char '/' s with
       | _ :: rest when rest <> [] ->
         VString (String.trim (String.concat "/" rest))
       | _ -> VString "")

  (* to-english-relation: visheshanam-string → English phrase *)
  | "to-english-relation" ->
    let rel_str = as_string (eval k e (List.nth args 0)) in
    let vish = Proof_graph.visheshanam_of_string rel_str in
    (match vish with
     | Some v -> VString (Anuvada.english_of_visheshanam_from_graph k v)
     | None -> VString rel_str)

  (* incoming-to: node-name -> incoming typed edges [source, relation, target] *)
  | "incoming-to" ->
    let name = as_string (eval k e (List.nth args 0)) in
    let edges = Proof_graph.edges_of k name in
    let incoming = List.filter_map (fun edge ->
      if edge.Proof_graph.target = name && edge.Proof_graph.source <> name then
        Some (VList [ VString edge.Proof_graph.source;
                      VString (Proof_graph.string_of_visheshanam edge.Proof_graph.relation);
                      VString edge.Proof_graph.target ])
      else
        None
    ) edges in
    VList incoming

  (* domain-of: node-name -> list of domain-* names linked to this node *)
  | "domain-of" ->
    let name = as_string (eval k e (List.nth args 0)) in
    let is_domain_name n =
      String.length n >= 7 && String.sub n 0 7 = "domain-"
    in
    let own = if is_domain_name name then [name] else [] in
    let domains =
      match Hashtbl.find_opt k.nodes name with
      | None -> own
      | Some n ->
        let from_outgoing = List.filter_map (fun edge ->
          if edge.Proof_graph.source = name
             && edge.Proof_graph.relation = Proof_graph.Sthita
             && is_domain_name edge.Proof_graph.target
          then Some edge.Proof_graph.target
          else None
        ) n.edges in
        let from_incoming = List.filter_map (fun edge ->
          if edge.Proof_graph.target = name && is_domain_name edge.Proof_graph.source
          then Some edge.Proof_graph.source
          else None
        ) (Proof_graph.edges_of k name) in
        List.sort_uniq String.compare (own @ from_outgoing @ from_incoming)
    in
    VList (List.map (fun d -> VString d) domains)

  (* context-score: node-name x [seed-names] -> edge connectivity score *)
  | "context-score" ->
    let name = as_string (eval k e (List.nth args 0)) in
    let seeds = List.map as_string (as_list (eval k e (List.nth args 1))) in
    let seed_set = Hashtbl.create 16 in
    List.iter (fun s -> Hashtbl.replace seed_set s true) seeds;
    let edges = Proof_graph.edges_of k name in
    let score = List.fold_left (fun acc edge ->
      if Hashtbl.mem seed_set edge.Proof_graph.source
         || Hashtbl.mem seed_set edge.Proof_graph.target
      then acc + 1
      else acc
    ) 0 edges in
    VFloat (Float.of_int score)

  (* iccha-status: node-name -> "sthita" | "rahita" | "none" *)
  | "iccha-status" ->
    let name = as_string (eval k e (List.nth args 0)) in
    let has_sthita =
      match Hashtbl.find_opt k.nodes name with
      | None -> false
      | Some n ->
        List.exists (fun edge ->
          edge.Proof_graph.source = name
          && edge.Proof_graph.target = "iccha"
          && edge.Proof_graph.relation = Proof_graph.Sthita
        ) n.edges
    in
    let has_rahita =
      match Hashtbl.find_opt k.nodes name with
      | None -> false
      | Some n ->
        List.exists (fun sloka ->
          let marker = "iccha-rahita" in
          let s = String.lowercase_ascii sloka in
          let m = String.lowercase_ascii marker in
          try
            ignore (Str.search_forward (Str.regexp_string m) s 0);
            true
          with Not_found -> false
        ) n.slokas
    in
    VString (if has_sthita then "sthita" else if has_rahita then "rahita" else "none")

  (* abheda-of: node-name -> outgoing abheda targets *)
  | "abheda-of" ->
    let name = as_string (eval k e (List.nth args 0)) in
    let targets =
      match Hashtbl.find_opt k.nodes name with
      | None -> []
      | Some n ->
        List.filter_map (fun edge ->
          if edge.Proof_graph.source = name
             && edge.Proof_graph.relation = Proof_graph.Abheda
          then Some edge.Proof_graph.target
          else None
        ) n.edges
    in
    VList (List.map (fun t -> VString t) (List.sort_uniq String.compare targets))

  (* avrti: seed-names × max-passes -> flat triples [source-raw, relation-name, [target-raws]] *)
  | "avrti" ->
    let seeds = as_list (eval k e (List.nth args 0)) in
    let max_passes = int_of_float (as_float (eval k e (List.nth args 1))) in
    let seed_names = List.map as_string seeds in
    let (pass_groups, _) = Anuvada.avrti_anuvada k seed_names max_passes in
    let connections = List.concat_map (fun (_pass_num, triples) ->
      List.map (fun (t : Anuvada.anuvada_triple) ->
        VList [ VString t.a_source_raw;
                VString (Proof_graph.string_of_visheshanam t.a_relation);
                VList (List.map (fun s -> VString s) t.a_targets_raw) ]
      ) triples
    ) pass_groups in
    VList connections

  (* render-node: name → formatted node inspection text *)
  | "render-node" ->
    let name = as_string (eval k e (List.nth args 0)) in
    let rname =
      match Proof_graph.find k name with
      | Some _ -> name
      | None ->
        (match Setu.classify_token k name with
         | Setu.Content c when c <> name -> c
         | _ -> name)
    in
    (match Proof_graph.find k rname with
     | None -> VString (Printf.sprintf "not found: %s." name)
     | Some n ->
       let buf = Buffer.create 256 in
       Anuvada.render_darshana_to_buf k n buf;
       VString (Buffer.contents buf))


  (* name: extract name from VNode, VPair, VBinding *)
  | "name" ->
    let v = eval k e (List.nth args 0) in
    (match v with
     | VNode n -> VString n
     | VPair (n, _) -> VString n
     | VBinding (n, _) -> VString n
     | VString s -> VString s
     | _ -> VString (as_string v))

  (* kind: extract the kind/type tag from a VPair *)
  | "kind" ->
    let v = eval k e (List.nth args 0) in
    (match v with
     | VPair (_, inner) -> inner
     | _ -> VNone)

  (* node: extract the node from a classified token triple *)
  | "node" ->
    let v = eval k e (List.nth args 0) in
    (match v with
     | VList [_; _; n] -> n  (* (word, kind, node) triple *)
     | VNode _ -> v
     | _ -> VNone)

  (* value: extract numeric value from VFloat, VBinding *)
  | "value" ->
    let v = eval k e (List.nth args 0) in
    (match v with
     | VFloat f -> VFloat f
     | VBinding (_, f) -> VFloat f
     | VString s ->
       (match float_of_string_opt s with Some f -> VFloat f | None -> VNone)
     | _ -> VNone)

  (* role: look up what grammar role a word has via english-grammar shabda *)
  | "role" ->
    let v = eval k e (List.nth args 0) in
    let word = as_string v in
    let pairs = Setu.read_shabda k "english-grammar" in
    (match List.find_opt (fun (w, _) -> w = word) pairs with
     | Some (_, rel) -> VString rel
     | None -> VNone)

  (* shabda: node × key → string — read shabda data *)
  | "shabda" ->
    let node_name = as_string (eval k e (List.nth args 0)) in
    let key = as_string (eval k e (List.nth args 1)) in
    let pairs = Setu.read_shabda k node_name in
    (match List.find_opt (fun (k, _) -> k = key) pairs with
     | Some (_, v) -> VString v
     | None -> VNone)

  (* exists: value → bool — true unless VNone or empty *)
  | "exists" ->
    let v = eval k e (List.nth args 0) in
    VBool (as_bool v)

  (* op-to-tantra: operator symbol → tantra name or VNone *)
  | "op-to-tantra" ->
    let op = as_string (eval k e (List.nth args 0)) in
    let tname = match op with
      | "+" -> Some "addition"
      | "-" -> Some "subtraction"
      | "*" -> Some "multiplication"
      | "/" -> Some "division"
      | _ -> None
    in
    (match tname with Some n -> VString n | None -> VNone)

  (* is-tantra: name → bool — does a tantra with this name exist?
     also resolves through graph: "plus" → abheda → "addition" → true *)
  | "is-tantra" ->
    let tname = as_string (eval k e (List.nth args 0)) in
    (match !eval_ctx with
     | Some ctx ->
       let direct = Hashtbl.mem ctx.ctx_index.by_name tname in
       if direct then VBool true
       else
         (* try graph resolution: walk abheda to find tantra name *)
         let resolved = !_resolve_concept_to_tantra_ref k ctx.ctx_index tname in
         VBool (resolved <> None)
     | None ->
       (* fallback to env-based check *)
       match Hashtbl.find_opt e "_tantra_index" with
       | Some (VList names) ->
         VBool (List.exists (fun v -> as_string v = tname) names)
       | _ -> VBool false)

  (* ---- string operations ---- *)

  (* split: string × delimiter → [string] *)
  | "split" ->
    let s = as_string (eval k e (List.nth args 0)) in
    let delim = as_string (eval k e (List.nth args 1)) in
    let parts = if String.length delim = 1 then
      String.split_on_char delim.[0] s
      |> List.filter (fun p -> String.length (String.trim p) > 0)
      |> List.map String.trim
    else
      (* multi-char delimiter: use Str *)
      Str.split (Str.regexp_string delim) s
      |> List.filter (fun p -> String.length (String.trim p) > 0)
      |> List.map String.trim
    in
    VList (List.map (fun s -> VString s) parts)

  (* concat: string... → string *)
  | "concat" ->
    let vals = List.map (eval k e) args in
    VString (String.concat "" (List.map as_string vals))

  (* join: list x separator -> string *)
  | "join" ->
    let lst = as_list (eval k e (List.nth args 0)) in
    let sep = as_string (eval k e (List.nth args 1)) in
    VString (String.concat sep (List.map as_string lst))

  (* ---- string primitives ---- *)
  (* these are irreducible — can't be expressed as graph walks.
     they give tantras the ability to inspect string structure,
     which combined with graph knowledge (akshara-varga) enables
     classification, parsing, and pattern recognition. *)

  (* char-at: string × index → string (single character) *)
  | "char-at" ->
    let s = as_string (eval k e (List.nth args 0)) in
    let i = int_of_float (as_float (eval k e (List.nth args 1))) in
    if i >= 0 && i < String.length s then
      VString (String.make 1 s.[i])
    else VNone

  (* string-length: string → float *)
  | "string-length" ->
    let s = as_string (eval k e (List.nth args 0)) in
    VFloat (Float.of_int (String.length s))

  (* to-number: string → float or VNone *)
  | "to-number" ->
    let s = as_string (eval k e (List.nth args 0)) in
    (match float_of_string_opt s with
     | Some f -> VFloat f
     | None -> VNone)

  (* to-string: value → string *)
  | "to-string" ->
    let v = eval k e (List.nth args 0) in
    VString (as_string v)

  (* upper: string → uppercase string *)
  | "upper" ->
    VString (String.uppercase_ascii (as_string (eval k e (List.nth args 0))))

  (* lower: string → lowercase string *)
  | "lower" ->
    VString (String.lowercase_ascii (as_string (eval k e (List.nth args 0))))

  (* ---- list operations ---- *)

  (* map: list × fn → list *)
  | "map" ->
    let lst = as_list (eval k e (List.nth args 0)) in
    let fn_val = eval k e (List.nth args 1) in
    (match fn_val with
     | VFn (params, body, captured) ->
       let results = List.map (fun item ->
         let local = env_copy captured in
         (match params with
          | [p] -> Hashtbl.replace local p item
          | _ -> ());
         eval k local body
       ) lst in
       VList results
     | _ -> VList [])

  (* filter: list × fn → list *)
  | "filter" ->
    let lst = as_list (eval k e (List.nth args 0)) in
    let fn_val = eval k e (List.nth args 1) in
    (match fn_val with
     | VFn (params, body, captured) ->
       let results = List.filter (fun item ->
         let local = env_copy captured in
         (match params with
          | [p] -> Hashtbl.replace local p item
          | _ -> ());
         as_bool (eval k local body)
       ) lst in
       VList results
     | _ -> VList [])

  (* first-match: list × fn → value — first item where fn returns non-VNone *)
  | "first-match" ->
    let lst = as_list (eval k e (List.nth args 0)) in
    let fn_val = eval k e (List.nth args 1) in
    (match fn_val with
     | VFn (params, body, captured) ->
       let result = List.find_map (fun item ->
         let local = env_copy captured in
         (match params with
          | [p] -> Hashtbl.replace local p item
          | _ -> ());
         let r = eval k local body in
         match r with VNone -> None | _ -> Some r
       ) lst in
       (match result with Some v -> v | None -> VNone)
     | _ -> VNone)

  (* fold-pairs: list × fn → list — slide a window of 2 over the list *)
  | "fold-pairs" ->
    let lst = as_list (eval k e (List.nth args 0)) in
    let fn_val = eval k e (List.nth args 1) in
    (match fn_val with
     | VFn (params, body, captured) ->
       let rec process = function
         | [] -> []
         | [x] -> [x]
         | a :: b :: rest ->
           let local = env_copy captured in
           (match params with
            | [pa; pb] ->
              Hashtbl.replace local pa a;
              Hashtbl.replace local pb b
            | _ -> ());
           let result = eval k local body in
           (match result with
            | VList items -> items @ process rest  (* replaced both *)
            | VNone -> a :: process (b :: rest)    (* skip *)
            | v -> v :: process rest)              (* merged into one *)
       in
       VList (process lst)
     | _ -> VList lst)

  (* fold-triples: list × fn → accumulator
     slides a window of 3, collecting results *)
  | "fold-triples" ->
    let lst = as_list (eval k e (List.nth args 0)) in
    let fn_val = eval k e (List.nth args 1) in
    (match fn_val with
     | VFn (params, body, captured) ->
       let results = ref [] in
       let rec process = function
         | [] | [_] | [_; _] -> ()
         | a :: b :: c :: rest ->
           let local = env_copy captured in
           (match params with
            | [pa; pb; pc] ->
              Hashtbl.replace local pa a;
              Hashtbl.replace local pb b;
              Hashtbl.replace local pc c
            | _ -> ());
           let result = eval k local body in
           (match result with
            | VNone -> process (b :: c :: rest)  (* no match, slide by 1 *)
            | v ->
              results := v :: !results;
              process rest)  (* matched, skip past the triple *)
       in
       process lst;
       VList (List.rev !results)
     | _ -> VList [])

  (* length: list → int *)
  | "length" ->
    let lst = as_list (eval k e (List.nth args 0)) in
    VFloat (Float.of_int (List.length lst))

  (* nth: list × index → value *)
  | "nth" ->
    let container = eval k e (List.nth args 0) in
    let idx = int_of_float (as_float (eval k e (List.nth args 1))) in
    (match container with
     | VPair (n, v) ->
       if idx = 0 then VString n else if idx = 1 then v else VNone
     | VBinding (n, f) ->
       if idx = 0 then VString n else if idx = 1 then VFloat f else VNone
     | _ ->
       let lst = as_list container in
       if idx >= 0 && idx < List.length lst then List.nth lst idx else VNone)

  (* flatten: [[a], [b], ...] -> [a, b, ...] one level *)
  | "flatten" ->
    let lst = as_list (eval k e (List.nth args 0)) in
    let flat = List.concat_map as_list lst in
    VList flat

  (* append: list x list -> list *)
  | "append" ->
    let a = as_list (eval k e (List.nth args 0)) in
    let b = as_list (eval k e (List.nth args 1)) in
    VList (a @ b)

  (* sort-desc: [[item, score], ...] sorted by score descending *)
  | "sort-desc" ->
    let lst = as_list (eval k e (List.nth args 0)) in
    let score_of_pair = function
      | VList [_item; score] -> as_float score
      | VPair (_item, score) -> as_float score
      | _ -> 0.0
    in
    let sorted = List.sort (fun a b -> compare (score_of_pair b) (score_of_pair a)) lst in
    VList sorted

  (* try-bigram: [word, word, ...] -> [word, ...] with adjacent pairs pre-joined
     where the joined form exists as a node. context shifts as each word is read. *)
  | "try-bigram" ->
    let words = List.map as_string (as_list (eval k e (List.nth args 0))) in
    let rec loop = function
      | [] -> []
      | [w] -> [w]
      | w1 :: w2 :: rest ->
        let joined = w1 ^ "-" ^ w2 in
        if Hashtbl.mem k.nodes joined then
          joined :: loop rest
        else
          w1 :: loop (w2 :: rest)
    in
    VList (List.map (fun s -> VString s) (loop words))

  (* unique: list -> list with duplicates removed (by string representation) *)
  | "unique" ->
    let lst = as_list (eval k e (List.nth args 0)) in
    let seen = Hashtbl.create 16 in
    let unique = List.filter (fun v ->
      let key = as_string v in
      if Hashtbl.mem seen key then false
      else (Hashtbl.replace seen key true; true)
    ) lst in
    VList unique

  (* ---- boolean / comparison operations ---- *)

  | "eq" ->
    let a = eval k e (List.nth args 0) in
    let b = eval k e (List.nth args 1) in
    VBool (as_string a = as_string b)

  | "neq" ->
    let a = eval k e (List.nth args 0) in
    let b = eval k e (List.nth args 1) in
    VBool (as_string a <> as_string b)

  | "and" ->
    let results = List.map (fun arg -> as_bool (eval k e arg)) args in
    VBool (List.for_all Fun.id results)

  | "or" ->
    let results = List.map (fun arg -> as_bool (eval k e arg)) args in
    VBool (List.exists Fun.id results)

  | "not" ->
    VBool (not (as_bool (eval k e (List.nth args 0))))

  (* numeric comparisons *)
  | "lt" ->
    VBool (as_float (eval k e (List.nth args 0)) < as_float (eval k e (List.nth args 1)))
  | "le" ->
    VBool (as_float (eval k e (List.nth args 0)) <= as_float (eval k e (List.nth args 1)))
  | "gt" ->
    VBool (as_float (eval k e (List.nth args 0)) > as_float (eval k e (List.nth args 1)))
  | "ge" ->
    VBool (as_float (eval k e (List.nth args 0)) >= as_float (eval k e (List.nth args 1)))

  (* pair: name × value → VPair *)
  | "pair" ->
    let name = as_string (eval k e (List.nth args 0)) in
    let v = eval k e (List.nth args 1) in
    (match args with
     | [_; _] -> VPair (name, v)
     | [_; _; _] ->
       let v2 = eval k e (List.nth args 2) in
       VList [VString name; v; v2]  (* triple *)
     | _ -> VPair (name, v))

  (* bind: name × value → VBinding *)
  | "bind" ->
    let name = as_string (eval k e (List.nth args 0)) in
    let v = as_float (eval k e (List.nth args 1)) in
    VBinding (name, v)

  (* ---- numeric operations (same as OCaml emitter but evaluated internally) ---- *)
  | "add" -> VFloat (as_float (eval k e (List.nth args 0)) +. as_float (eval k e (List.nth args 1)))
  | "sub" -> VFloat (as_float (eval k e (List.nth args 0)) -. as_float (eval k e (List.nth args 1)))
  | "mul" -> VFloat (as_float (eval k e (List.nth args 0)) *. as_float (eval k e (List.nth args 1)))
  | "div" ->
    let b = as_float (eval k e (List.nth args 1)) in
    if b = 0.0 then VFloat 0.0
    else VFloat (as_float (eval k e (List.nth args 0)) /. b)
  | "power" -> VFloat (as_float (eval k e (List.nth args 0)) ** as_float (eval k e (List.nth args 1)))
  | "sqrt" -> VFloat (sqrt (as_float (eval k e (List.nth args 0))))
  | "sin" -> VFloat (sin (as_float (eval k e (List.nth args 0))))
  | "cos" -> VFloat (cos (as_float (eval k e (List.nth args 0))))
  | "tan" -> VFloat (tan (as_float (eval k e (List.nth args 0))))
  | "log" -> VFloat (log (as_float (eval k e (List.nth args 0))))
  | "abs" -> VFloat (abs_float (as_float (eval k e (List.nth args 0))))
  | "neg" -> VFloat (-. (as_float (eval k e (List.nth args 0))))
  | "floor" -> VFloat (floor (as_float (eval k e (List.nth args 0))))
  | "ceil" -> VFloat (ceil (as_float (eval k e (List.nth args 0))))
  | "mod" -> VFloat (mod_float (as_float (eval k e (List.nth args 0))) (as_float (eval k e (List.nth args 1))))
  | "min" -> VFloat (Float.min (as_float (eval k e (List.nth args 0))) (as_float (eval k e (List.nth args 1))))
  | "max" -> VFloat (Float.max (as_float (eval k e (List.nth args 0))) (as_float (eval k e (List.nth args 1))))

  (* ---- yantra pipeline operations ---- *)
  (* these bridge the tantra-level pipeline to the existing OCaml implementation.
     the tantra declares WHAT to do; these ops do HOW. *)

  (* tokenise: string → [string] — split sentence into words using yantra tokeniser *)
  | "tokenise" ->
    let s = as_string (eval k e (List.nth args 0)) in
    let words = !_yantra_tokenise_ref s in
    let words = List.filter (fun w -> String.length (String.trim w) > 0) words in
    VList (List.map (fun w -> VString w) words)

  (* classify: string → [word, kind, resolved]
     number/operator handled as thin primitives; everything else via setu-classify-token tantra *)
  | "classify" ->
    let word = as_string (eval k e (List.nth args 0)) in
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
    classify_one word

  (* classify-all: [string] → [(word, kind, resolved)] *)
  | "classify-all" ->
    let words = as_list (eval k e (List.nth args 0)) in
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
    VList (List.map (fun wv -> classify_one (as_string wv)) words)

  (* join-bigrams: [(word, kind, resolved)] → [(word, kind, resolved)] *)
  | "join-bigrams" ->
    let tokens = as_list (eval k e (List.nth args 0)) in
    let to_ytoken (triple : value) : (string * ytoken) option =
      match triple with
      | VList [VString w; VString kind; resolved] ->
        let yt = match kind with
          | "number" -> YNumber (as_float resolved)
          | "concept" -> YConcept (as_string resolved)
          | "operator" -> YOperator (as_string resolved)
          | "grammar" -> YGrammar Sthita
          | _ -> YUnknown (as_string resolved)
        in
        Some (w, yt)
      | _ -> None
    in
    let from_ytoken ((w, yt) : string * ytoken) : value =
      match yt with
      | YNumber f -> VList [VString w; VString "number"; VFloat f]
      | YConcept c -> VList [VString w; VString "concept"; VString c]
      | YOperator o -> VList [VString w; VString "operator"; VString o]
      | YGrammar _ -> VList [VString w; VString "grammar"; VString w]
      | YUnknown u -> VList [VString w; VString "unknown"; VString u]
    in
    let ytokens = List.filter_map to_ytoken tokens in
    let joined = !_join_bigrams_ref k ytokens in
    VList (List.map from_ytoken joined)

  (* match-sentence-patterns: [(word, kind, resolved)] → VList [target_or_stored, ...]
     graph-driven replacement for extract-bindings.
     reads sentence-pattern nodes from graph to find solve concepts.
     for assignment patterns: stores bindings to session, returns [stored; name; val; unit; ""]
     for query patterns: returns [target; VBinding ...] (same as extract-bindings) *)
  | "match-sentence-patterns" ->
    let tokens = as_list (eval k e (List.nth args 0)) in
    (* check if a concept node has yantra-kriya Kriya edge = solve-type concept *)
    let is_solve_concept name =
      match Hashtbl.find_opt k.nodes name with
      | None -> false
      | Some n -> List.exists (fun e ->
          e.relation = Kriya && e.target = "yantra-kriya"
        ) n.edges
    in
    let to_ytoken (triple : value) : (string * ytoken) option =
      match triple with
      | VList [VString w; VString kind; resolved] ->
        let yt = match kind with
          | "number" -> YNumber (as_float resolved)
          | "concept" ->
            let c = as_string resolved in
            (* if this concept is a solve-type, reclassify it so extract_bindings
               treats it as a question word (checks the original word too) *)
            if is_solve_concept c then YConcept c
            else YConcept c
          | "operator" -> YOperator (as_string resolved)
          | "grammar" -> YGrammar (match as_string resolved with
            | g when g = "what" || g = "when" -> Drishthanta
            | g when g = "is" || g = "are" || g = "am" || g = "was" || g = "were" -> Swarupa
            | g when g = "of" -> Sthita
            | g when g = "and" -> Yukta
            | _ -> Sthita)
          | _ -> YUnknown (as_string resolved)
        in
        Some (w, yt)
      | _ -> None
    in
    let ytokens = List.filter_map to_ytoken tokens in
    (* override is_question_word to use graph: check if the ytoken's resolved concept
       has kriya yantra-kriya edge (i.e. solve.om type node) *)
    let is_graph_question_word (_w : string) (yt : ytoken) =
      match yt with
      | YConcept c -> is_solve_concept c
      | _ -> false
    in
    (* walk tokens: same logic as extract_bindings but with graph-driven solve detection *)
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
          let direct = match !eval_ctx with
            | Some ctx -> Hashtbl.find_opt ctx.ctx_index.by_name c
            | None -> None in
          let via_graph = match direct with
            | Some _ -> direct
            | None ->
              let resolved = Setu.resolve k c in
              List.find_map (fun name ->
                match !eval_ctx with
                | Some ctx -> Hashtbl.find_opt ctx.ctx_index.by_name name
                | None -> None
              ) resolved
          in
          match via_graph with
          | Some t -> is_simple_tantra t
          | None -> false
        in
        if is_op_concept then begin
          unbound_concepts := c :: !unbound_concepts;
          let idx_n = List.length !bindings in
          let name = Printf.sprintf "arg%d" idx_n in
          bindings := { b_name = name; b_value = n; b_unit = None } :: !bindings;
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
        let rec find_target = function
          | (_, YConcept c) :: rest' ->
            target := Some c;
            walk rest'
          | (_, YGrammar _) :: rest' -> find_target rest'
          | other -> walk other
        in
        ignore w;
        find_target rest
      | (w, YConcept yt_c) :: rest when is_graph_question_word w (YConcept yt_c) && !target = None ->
        let rec find_target = function
          | (_, YConcept c) :: rest' ->
            target := Some c;
            walk rest'
          | (_, YGrammar _) :: rest' -> find_target rest'
          | other -> walk other
        in
        find_target rest
      | (_, YConcept c) :: rest ->
        unbound_concepts := c :: !unbound_concepts;
        walk rest
      | (_, YGrammar _) :: rest -> walk rest
      | (_, YOperator _) :: rest -> walk rest
      | (_, YNumber n) :: rest ->
        let idx_n = List.length !bindings in
        let name = Printf.sprintf "arg%d" idx_n in
        bindings := { b_name = name; b_value = n; b_unit = None } :: !bindings;
        walk rest
      | (_, YUnknown _) :: rest -> walk rest
    in
    walk ytokens;
    (* resolve target from unbound concepts if needed *)
    let resolved_target =
      match !target with
      | Some _ as t -> t
      | None ->
        let unbound = List.rev !unbound_concepts in
        List.find_map (fun c ->
          match !eval_ctx with
          | None -> None
          | Some ctx ->
            if Hashtbl.mem ctx.ctx_index.by_name c then Some c
            else if Hashtbl.mem ctx.ctx_index.by_output c then Some c
            else begin
              let resolved = Setu.resolve k c in
              List.find_map (fun name ->
                if Hashtbl.mem ctx.ctx_index.by_name name then Some name
                else if Hashtbl.mem ctx.ctx_index.by_output name then Some name
                else None
              ) resolved
            end
        ) unbound
    in
    (match !eval_ctx with
     | None -> VNone
     | Some ctx ->
       (* merge session bindings *)
       let bound_names = List.map (fun b -> b.b_name) !bindings in
       let session_additions = List.filter (fun sb ->
         not (List.mem sb.b_name bound_names)
       ) ctx.ctx_session.bindings in
       let all_bindings = List.rev !bindings @ session_additions in
       (* determine if this is a pure assignment (no target, has new bindings) *)
       let is_pure_assignment = resolved_target = None && !bindings <> [] in
       if is_pure_assignment then begin
         (* store all new bindings to session *)
         List.iter (fun b ->
           ctx.ctx_session.bindings <-
             b :: List.filter (fun sb -> sb.b_name <> b.b_name) ctx.ctx_session.bindings
         ) (List.rev !bindings);
         (* return "stored" format for the first binding *)
         let b = List.hd (List.rev !bindings) in
         let unit_str = match b.b_unit with Some u -> u | None -> "" in
         VList [VString "stored"; VString b.b_name; VFloat b.b_value;
                VString unit_str; VString ""]
       end else begin
         (* query format: [target_or_"", VBinding ...] *)
         let target_v = match resolved_target with
           | Some t -> VString t
           | None -> VString ""
         in
         let binding_vs = List.map (fun b -> VBinding (b.b_name, b.b_value)) all_bindings in
         VList (target_v :: binding_vs)
       end)

  (* extract-bindings: [(word, kind, resolved)] → VList [target, bindings...]
     returns [VString target_or_"", VBinding(name, val), ...] *)
  | "extract-bindings" ->
    let tokens = as_list (eval k e (List.nth args 0)) in
    let to_ytoken (triple : value) : (string * ytoken) option =
      match triple with
      | VList [VString w; VString kind; resolved] ->
        let yt = match kind with
          | "number" -> YNumber (as_float resolved)
          | "concept" -> YConcept (as_string resolved)
          | "operator" -> YOperator (as_string resolved)
          | "grammar" -> YGrammar (match as_string resolved with
            | g when g = "what" || g = "when" -> Drishthanta
            | g when g = "is" -> Swarupa
            | g when g = "of" -> Sthita
            | g when g = "and" -> Yukta
            | _ -> Sthita)
          | _ -> YUnknown (as_string resolved)
        in
        Some (w, yt)
      | _ -> None
    in
    (match !eval_ctx with
     | None -> VNone
     | Some ctx ->
       let ytokens = List.filter_map to_ytoken tokens in
       let extraction = !_extract_bindings_ref k ctx.ctx_index ctx.ctx_session ytokens in
       let target_v = match extraction.ex_target with
         | Some t -> VString t
         | None -> VString ""
       in
       let binding_vs = List.map (fun b ->
         VBinding (b.b_name, b.b_value)
       ) extraction.ex_bindings in
       VList (target_v :: binding_vs))

  (* resolve-tantra: string × [values] → resolution info
     takes target name and extraction list, returns [mode, tantra-name, ...] *)
  | "resolve-tantra" ->
    let target = as_string (eval k e (List.nth args 0)) in
    let bindings_v = as_list (eval k e (List.nth args 1)) in
    (match !eval_ctx with
     | None -> VNone
     | Some ctx ->
       let bindings = List.filter_map (fun v ->
         match v with
         | VBinding (n, f) -> Some { b_name = n; b_value = f; b_unit = None }
         | _ -> None
       ) bindings_v in
       (* if target is already bound, this is a store not a compute *)
       let target_is_bound = List.exists (fun b -> b.b_name = target) bindings in
       if target_is_bound then
         VList [VString "not-found"; VString "binding-store"]
       else
       let target = match !_resolve_concept_to_tantra_ref k ctx.ctx_index target with
         | Some resolved -> resolved
         | None -> target in
       let resolution = !_resolve_tantra_ref k ctx.ctx_index bindings target in
       match resolution with
       | Direct (t, assignments) ->
         let assign_vs = List.map (fun (n, v) ->
           VBinding (n, v)
         ) assignments in
         VList [VString "direct"; VString t.t_name; VList assign_vs]
       | Inverse (t, tgt, _plan, known_values) ->
         let kv_vs = List.map (fun (n, v) ->
           VBinding (n, v)
         ) known_values in
         VList [VString "inverse"; VString t.t_name; VString tgt; VList kv_vs]
       | Chain steps ->
         (* execute chain steps and return final result *)
         let step_names = ref [] in
         List.iter (fun step ->
           match step with
           | CForward (t, assignments) ->
             let input_values = List.map (fun (n, f) -> (n, VFloat f)) assignments in
             let result = !_eval_tantra_chain_ref k t input_values in
             (match t.t_returns with
              | [ret] ->
                let f = as_float result in
                ctx.ctx_session.bindings <-
                  { b_name = ret.tp_name; b_value = f; b_unit = ret.tp_unit }
                  :: List.filter (fun b -> b.b_name <> ret.tp_name) ctx.ctx_session.bindings;
                if t.t_name <> ret.tp_name then
                  ctx.ctx_session.bindings <-
                    { b_name = t.t_name; b_value = f; b_unit = ret.tp_unit }
                    :: List.filter (fun b -> b.b_name <> t.t_name) ctx.ctx_session.bindings
              | _ -> ());
             step_names := t.t_name :: !step_names
           | CInverse (t, tgt, plan, kv) ->
             let env = new_env () in
             List.iter (fun (n, f) -> Hashtbl.replace env n (VFloat f)) kv;
             List.iter (fun (n, rhs) ->
               let v = eval k env rhs in
               Hashtbl.replace env n v
             ) plan;
             let f = match Hashtbl.find_opt env tgt with
               | Some v -> as_float v | None -> 0.0 in
             let unit_opt = match List.find_opt (fun inp ->
               inp.tp_name = tgt) t.t_inputs with
               | Some inp -> inp.tp_unit | None -> None in
             ctx.ctx_session.bindings <-
               { b_name = tgt; b_value = f; b_unit = unit_opt }
               :: List.filter (fun b -> b.b_name <> tgt) ctx.ctx_session.bindings;
             step_names := t.t_name :: !step_names
         ) steps;
         let all_names = List.rev !step_names in
         (* format attribution: "force, final-velocity and kinetic-energy" *)
         let attribution = match all_names with
           | [] -> "chain"
           | [n] -> n
           | _ ->
             let rev = List.rev all_names in
             let last = List.hd rev in
             let rest = List.rev (List.tl rev) in
             String.concat ", " rest ^ " and " ^ last
         in
         let last_name = match List.rev all_names with n :: _ -> n | [] -> "chain" in
         last_invoked_tantra := last_name ^ " (chain)";
         let target_val = match List.find_opt (fun b ->
           b.b_name = target) ctx.ctx_session.bindings with
           | Some b -> b.b_value | None -> 0.0 in
         ctx.ctx_session.last_result <- [(target, target_val)];
         let unit_opt = match List.rev steps with
           | CForward (t, _) :: _ ->
             (match t.t_returns with [ret] -> ret.tp_unit | _ -> None)
           | _ -> None in
         VList [VString "chain-result"; VString attribution;
                VBinding (target, target_val); VString (match unit_opt with Some u -> u | None -> "")]
       | NotFound reason -> VList [VString "not-found"; VString reason])

  (* invoke-tantra: resolution-info → VList [kind; name; value; unit; attribution] *)
  | "invoke-tantra" ->
    let resolution_v = eval k e (List.nth args 0) in
    (match !eval_ctx with
     | None -> VNone
     | Some ctx ->
        (* build a result VList and update session.
           for physics/math tantras with short return-param abbreviations (f, v, ke, etc.),
           use the tantra name as the output name for natural language formatting. *)
        let canonical_out_name ret_name tantra_name =
          if ret_name = "result" then "result"
          else if String.length ret_name <= 2 then tantra_name
          else ret_name
        in
        let make_result kind name value unit_opt attribution =
          let f = as_float value in
          let unit_str = match unit_opt with Some u -> u | None -> "" in
          ctx.ctx_session.last_result <- [(name, f)];
          ctx.ctx_session.bindings <-
            { b_name = name; b_value = f; b_unit = unit_opt }
            :: List.filter (fun b -> b.b_name <> name) ctx.ctx_session.bindings;
          VList [VString kind; VString name; VFloat f; VString unit_str; VString attribution]
        in
        match as_list resolution_v with
        | [VString "chain-result"; VString attribution; VBinding (name, value); VString unit_str] ->
          last_invoked_tantra := attribution ^ " (chain)";
          let unit_opt = if String.length unit_str > 0 then Some unit_str else None in
          make_result "result" name (VFloat value) unit_opt attribution
        | [VString "direct"; VString tantra_name; VList assign_vs] ->
          (match Hashtbl.find_opt ctx.ctx_index.by_name tantra_name with
           | Some t ->
             last_invoked_tantra := tantra_name;
             let assignments = List.filter_map (fun v ->
               match v with VBinding (n, f) -> Some (n, f) | _ -> None
             ) assign_vs in
             let input_values = List.map (fun (n, f) -> (n, VFloat f)) assignments in
             let result = !_eval_tantra_ref k t input_values in
             (match t.t_returns with
              | [ret] ->
                let out_name = canonical_out_name ret.tp_name tantra_name in
                make_result "result" out_name result ret.tp_unit tantra_name
              | rets ->
                (* multi-return: store all, return first as primary result *)
                let values = as_list result in
                List.iteri (fun i ret ->
                  let v = if i < List.length values then List.nth values i else VNone in
                  let f = as_float v in
                  ctx.ctx_session.bindings <-
                    { b_name = ret.tp_name; b_value = f; b_unit = ret.tp_unit }
                    :: List.filter (fun b -> b.b_name <> ret.tp_name) ctx.ctx_session.bindings
                ) rets;
                let (first_ret, first_val) = match rets, values with
                  | r :: _, v :: _ -> (r, v) | r :: _, [] -> (r, VNone) | [], _ -> failwith "no rets" in
                let out_name = canonical_out_name first_ret.tp_name tantra_name in
                make_result "result" out_name first_val first_ret.tp_unit tantra_name)
           | None ->
             VList [VString "error"; VString tantra_name; VFloat 0.0; VString ""; VString ""])
        | [VString "inverse"; VString tantra_name; VString target; VList kv_vs] ->
          (match Hashtbl.find_opt ctx.ctx_index.by_name tantra_name with
           | Some t ->
             last_invoked_tantra := tantra_name ^ " (inverted)";
             let known_values = List.filter_map (fun v ->
               match v with VBinding (n, f) -> Some (n, f) | _ -> None
             ) kv_vs in
             let target_inp_name = match List.find_opt (fun inp ->
               inp.tp_name = target ||
               let tp = String.split_on_char '-' inp.tp_name in
               let tgt = String.split_on_char '-' target in
               List.exists (fun p -> List.mem p tgt) tp ||
               List.exists (fun p -> List.mem p tp) tgt
             ) t.t_inputs with
             | Some inp -> inp.tp_name
             | None -> target
             in
             let ret_name = match t.t_returns with
               | [ret] -> ret.tp_name | _ -> "result" in
             let ret_binding_name = match List.find_opt (fun (name, _) ->
               name = ret_name ||
               List.exists (fun ret -> ret.tp_name = name) t.t_returns
             ) t.t_lets with
             | Some (name, _) -> name
             | None -> ret_name
             in
             let known_names = List.map fst known_values in
             (match invert_chain k t.t_lets known_names
                      target_inp_name ret_binding_name with
              | Some plan ->
                let env = new_env () in
                List.iter (fun (n, f) -> Hashtbl.replace env n (VFloat f)) known_values;
                List.iter (fun (n, rhs) ->
                  let v = eval k env rhs in
                  Hashtbl.replace env n v
                ) plan;
                let result = match Hashtbl.find_opt env target_inp_name with
                  | Some v -> v | None -> VNone in
                let unit_opt = match List.find_opt (fun inp ->
                  inp.tp_name = target_inp_name) t.t_inputs with
                  | Some inp -> inp.tp_unit | None -> None in
                make_result "result" target result unit_opt tantra_name
              | None ->
                VList [VString "error"; VString "cannot invert expression";
                       VFloat 0.0; VString ""; VString ""])
           | None ->
             VList [VString "error"; VString tantra_name; VFloat 0.0; VString ""; VString ""])
       | [VString "not-found"; VString reason] ->
         VList [VString "error"; VString reason; VFloat 0.0; VString ""; VString ""]
       | _ ->
         VList [VString "error"; VString "invalid resolution"; VFloat 0.0; VString ""; VString ""])

  (* ---- print / debug ---- *)
  | "print" ->
    let v = eval k e (List.nth args 0) in
    Printf.printf "%s\n%!" (as_string v);
    v

  (* unknown operation — try looking up as a variable holding a function *)
  | _ ->
    (match Hashtbl.find_opt e op with
     | Some (VFn (params, body, captured)) ->
       let local = env_copy captured in
       List.iteri (fun i param ->
         if i < List.length args then
           Hashtbl.replace local param (eval k e (List.nth args i))
       ) params;
       eval k local body
     | _ ->
       (* try calling as a loaded tantra by name *)
       (match !eval_ctx with
        | Some ctx ->
          (match Hashtbl.find_opt ctx.ctx_index.by_name op with
           | Some t ->
             let input_values = List.mapi (fun i inp ->
               let v = if i < List.length args then eval k e (List.nth args i) else VNone in
               (inp.tp_name, v)
             ) t.t_inputs in
             !_eval_tantra_ref k t input_values
           | None ->
             Printf.printf "eval: unknown operation '%s'\n%!" op;
             VNone)
        | None ->
          Printf.printf "eval: unknown operation '%s'\n%!" op;
          VNone))

(* evaluate a full tantra using the internal evaluator *)
let eval_tantra ?(idx : tantra_index option) ?(session : session option)
    (k : proof_graph) (t : tantra) (input_values : (string * value) list) : value =
  (* set context if index and session provided *)
  let prev_ctx = !eval_ctx in
  (match idx, session with
   | Some i, Some s -> eval_ctx := Some { ctx_index = i; ctx_session = s }
   | _ -> ());
  let e = new_env () in
  (* bind inputs *)
  List.iter (fun (name, v) -> Hashtbl.replace e name v) input_values;
  (* evaluate let bindings in order *)
  List.iter (fun (name, rhs) ->
    let v = eval k e rhs in
    Hashtbl.replace e name v
  ) t.t_lets;
  (* return *)
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

(* parse output back to (name, value) pairs
   formats: "displacement = 39.600000" or just "8.000000" *)
let parse_output (raw : string) : (string * float) list =
  let lines = String.split_on_char '\n' raw
    |> List.map String.trim
    |> List.filter (fun s -> String.length s > 0) in
  List.filter_map (fun line ->
    match String.index_opt line '=' with
    | Some eq ->
      let name = String.trim (String.sub line 0 eq) in
      let rest = String.trim (String.sub line (eq + 1) (String.length line - eq - 1)) in
      (* strip unit suffix if present: "39.600000 metre" -> "39.600000" *)
      let num_str = match String.index_opt rest ' ' with
        | Some sp -> String.sub rest 0 sp
        | None -> rest
      in
      (match float_of_string_opt num_str with
       | Some f -> Some (name, f)
       | None -> None)
    | None ->
      (* bare number *)
      (match float_of_string_opt (String.trim line) with
       | Some f -> Some ("result", f)
       | None -> None)
  ) lines

(* ---- top-level entry point ---- *)

(* resolve a concept name to a tantra name via graph abheda walk *)
let resolve_concept_to_tantra (k : proof_graph) (idx : tantra_index) (concept : string) : string option =
  (* direct match *)
  if Hashtbl.mem idx.by_name concept then Some concept
  else if Hashtbl.mem idx.by_output concept then Some concept
  else if Hashtbl.mem idx.by_input concept then Some concept
  else begin
    (* walk abheda edges from this concept *)
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

(* tokenise for yantra: preserve floats by splitting carefully *)
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
      (* preserve '.' between digits for floats *)
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
      (* '-' could be: hyphen in "initial-velocity", negative sign, or minus operator *)
      let prev_alpha = Buffer.length buf > 0 &&
        let contents = Buffer.contents buf in
        let last = contents.[String.length contents - 1] in
        (last >= 'a' && last <= 'z') || (last >= 'A' && last <= 'Z') in
      let next_alpha = !i + 1 < len &&
        let nc = s.[!i + 1] in
        (nc >= 'a' && nc <= 'z') || (nc >= 'A' && nc <= 'Z') in
      if prev_alpha && next_alpha then begin
        (* hyphenated word: keep in buffer *)
        Buffer.add_char buf '-'; incr i
      end else if Buffer.length buf = 0 && !i + 1 < len &&
                  s.[!i + 1] >= '0' && s.[!i + 1] <= '9' then begin
        (* negative number *)
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

(* wire up forward references — connects the evaluator to the pipeline functions *)
let () =
  _yantra_tokenise_ref := yantra_tokenise;
  _classify_for_yantra_ref := classify_for_yantra;
  _join_bigrams_ref := join_bigrams;
  _extract_bindings_ref := extract_bindings;
  _resolve_concept_to_tantra_ref := resolve_concept_to_tantra;
  _resolve_tantra_ref := resolve_tantra;
  _eval_tantra_ref := (fun k t inputs -> eval_tantra k t inputs);
  _eval_chain_ref := eval;
  _eval_tantra_chain_ref := (fun k t inputs -> eval_tantra k t inputs)

(* run anuvada-ganana: the meta-tantra pipeline *)
let run_anuvada_ganana (k : proof_graph) (idx : tantra_index) (session : session)
    (sentence : string) : yantra_result option =
  match Hashtbl.find_opt idx.by_name "anuvada-ganana" with
  | None -> None
  | Some ag ->
    let result = eval_tantra ~idx ~session k ag
      [("sentence", VString sentence)] in
    let raw = as_string result in
    (* empty string means no result (error/unhandled — fall through to fallback path) *)
    if String.length raw = 0 then
      None
    else begin
      let tantra_name = if String.length !last_invoked_tantra > 0 then
        !last_invoked_tantra else "anuvada-ganana" in
      Some { yr_output = []; yr_tantra = tantra_name;
             yr_code = "(via anuvada-ganana)"; yr_raw_output = raw }
    end

let run (k : proof_graph) (idx : tantra_index) (session : session)
    (sentence : string) : yantra_result option =
  (* PRIMARY PATH: run through anuvada-ganana meta-tantra.
     the tantra orchestrates: tokenise → classify → bigrams → extract → resolve → execute. *)
  match run_anuvada_ganana k idx session sentence with
  | Some _ as result ->
    session.history <- sentence :: session.history;
    result
  | None ->
    (* anuvada-ganana returned nothing — check if this is a binding-store query
       like "mass is 10" or "v = 20" (no computation target, just remembering values). *)
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
        (* if target is already one of the bindings, just store *)
        let target_is_bound = List.exists (fun b -> b.b_name = target) bindings in
        if target_is_bound then begin
          let buf = Buffer.create 64 in
          List.iter (fun b ->
            session.bindings <- b
              :: List.filter (fun sb -> sb.b_name <> b.b_name) session.bindings;
            Buffer.add_string buf (Printf.sprintf "%s is %g (remembered).\n" b.b_name b.b_value)
          ) bindings;
          session.history <- sentence :: session.history;
          Some { yr_output = []; yr_tantra = ""; yr_code = "(stored)";
                 yr_raw_output = String.trim (Buffer.contents buf) }
        end else begin
        let resolution = !_resolve_tantra_ref k idx bindings target in
        (match resolution with
         | Direct (t, assignments) ->
           let input_values = List.map (fun (n, f) -> (n, VFloat f)) assignments in
           let result = eval_tantra ~idx ~session k t input_values in
           let output = match t.t_returns with
             | [ret] -> [(ret.tp_name, as_float result)]
             | rets ->
               let values = as_list result in
               List.mapi (fun i ret ->
                 let v = if i < List.length values then List.nth values i else VNone in
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
             let v = eval k env rhs in
             Hashtbl.replace env n v
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
                  (* also store under tantra name for target lookup *)
                  if t.t_name <> ret.tp_name then
                    final_bindings := { b_name = t.t_name; b_value = v;
                                        b_unit = ret.tp_unit } :: !final_bindings
                | rets ->
                  let values = as_list result in
                  List.iteri (fun i ret ->
                    let v = if i < List.length values then as_float (List.nth values i) else 0.0 in
                    final_bindings := { b_name = ret.tp_name; b_value = v;
                                        b_unit = ret.tp_unit } :: !final_bindings
                  ) rets);
               tantra_names := t.t_name :: !tantra_names
             | CInverse (t, _tgt, _plan, _kv) ->
               tantra_names := (t.t_name ^ "(inv)") :: !tantra_names
           ) steps;
           let target_value = match List.find_opt (fun b ->
             names_match_fast b.b_name target
           ) !final_bindings with
           | Some b -> b.b_value | None -> 0.0 in
           let chain_name = String.concat " → " (List.rev !tantra_names) in
           session.history <- sentence :: session.history;
           last_invoked_tantra := chain_name;
           Some { yr_output = [(target, target_value)];
                  yr_tantra = chain_name ^ " (chain)";
                  yr_code = "(chain)"; yr_raw_output = "" }
         | NotFound _ -> None)
        end
      | None, (_ :: _ as bindings) ->
        let buf = Buffer.create 64 in
        List.iter (fun b ->
          session.bindings <- b
            :: List.filter (fun sb -> sb.b_name <> b.b_name) session.bindings;
          Buffer.add_string buf (Printf.sprintf "%s is %g (remembered).\n" b.b_name b.b_value)
        ) bindings;
        session.history <- sentence :: session.history;
        Some { yr_output = []; yr_tantra = ""; yr_code = "(stored)";
               yr_raw_output = String.trim (Buffer.contents buf) }
      | _ -> None
    end

(* print a yantra result — uses pre-formatted output from format-response tantra *)
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

(* run a tantra by name with explicit inputs — for routing non-computation paths *)
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
