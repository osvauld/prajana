(* vidya.ml — shabda loading, graph walks, classification, resolution.
   consolidates setu_shabda.ml (181L) + setu_classify.ml (145L) + setu.ml (373L).
   the bridge between raw graph structure and domain renderers.

   sections:
     1. shabda store — global store + S-expression parser
     2. shabda reader — inheritance-aware read_shabda
     3. classification — token_role, grammar, number words
     4. tokenisation + domain detection
     5. graph walks — edge readers, resolution, neighbours
     6. to_english — English rendering of graph nodes *)

open Prakriti

(* ═══════════════════════════════════════════════════════════════════════════
   1. SHABDA STORE — global store + S-expression parser
   ═══════════════════════════════════════════════════════════════════════════ *)

let _shabda_store : (string, (string * string) list) Hashtbl.t = Hashtbl.create 1024

(* tokenize S-expression body: split on spaces, respecting "quoted strings" *)
let _tokenize_sexp (s : string) : string list =
  let tokens = ref [] in
  let buf = Buffer.create 32 in
  let in_quote = ref false in
  String.iter (fun c ->
    if c = '"' then
      in_quote := not !in_quote
    else if (c = ' ' || c = '\t') && not !in_quote then begin
      if Buffer.length buf > 0 then begin
        tokens := Buffer.contents buf :: !tokens;
        Buffer.clear buf
      end
    end else
      Buffer.add_char buf c
  ) s;
  if Buffer.length buf > 0 then
    tokens := Buffer.contents buf :: !tokens;
  List.rev !tokens

(* parse one S-expression block body into (key, value) pairs *)
let parse_sexp_pairs (body_lines : string list) : (string * string) list =
  let pairs = ref [] in
  List.iter (fun line ->
    let trimmed = String.trim line in
    if String.length trimmed > 1 && trimmed.[0] = '(' then begin
      let inner = String.trim (String.sub trimmed 1
        (String.length trimmed - (if trimmed.[String.length trimmed - 1] = ')'
         then 2 else 1))) in
      let toks = _tokenize_sexp inner in
      (match toks with
      | [] -> ()
      | key :: values ->
        let k = if key = "description" then "desc"
                else if key = "alias" then "name"
                else key in
        let v = match values with
          | [] -> ""
          | [v] -> v
          | vs -> String.concat "," vs
        in
        if String.length v > 0 then
          pairs := (k, v) :: !pairs)
    end
  ) body_lines;
  List.rev !pairs

(* load S-expression file: returns (node-name, pairs) list *)
let load_sexp_file (lines : string list) : (string * (string * string) list) list =
  let results = ref [] in
  let i = ref 0 in
  let n = List.length lines in
  let arr = Array.of_list lines in
  while !i < n do
    let line = String.trim arr.(!i) in
    if String.length line > 7 && String.sub line 0 7 = "shabda " then begin
      let name = String.trim (String.sub line 7 (String.length line - 7)) in
      incr i;
      let body = ref [] in
      while !i < n && String.trim arr.(!i) <> "done" do
        body := arr.(!i) :: !body;
        incr i
      done;
      if !i < n then incr i;
      let pairs = parse_sexp_pairs (List.rev !body) in
      if String.length name > 0 && pairs <> [] then
        results := (name, pairs) :: !results
    end else
      incr i
  done;
  List.rev !results

(* load all *.shabda files from a directory into the store *)
let load_shabda_dir (dir : string) : int =
  if not (Sys.file_exists dir && Sys.is_directory dir) then 0
  else begin
    let count = ref 0 in
    let entries = Sys.readdir dir in
    Array.iter (fun fname ->
      if Filename.check_suffix fname ".shabda" then begin
        let path = Filename.concat dir fname in
        try
          let lines = read_file path in
          let entries_list = load_sexp_file lines in
          List.iter (fun (name, pairs) ->
            Hashtbl.replace _shabda_store name pairs;
            incr count
          ) entries_list
        with _ -> ()
      end
    ) entries;
    !count
  end

(* ═══════════════════════════════════════════════════════════════════════════
   2. SHABDA READER — inheritance-aware
   ═══════════════════════════════════════════════════════════════════════════ *)

let raw_shabda_for_node (_k : proof_graph) (node_name : string) : (string * string) list =
  match Hashtbl.find_opt _shabda_store node_name with
  | Some pairs -> pairs
  | None -> []

let merge_shabda_priority (pairs_by_priority : (string * string) list list)
    : (string * string) list =
  let seen = Hashtbl.create 16 in
  let result = ref [] in
  List.iter (fun pairs ->
    List.iter (fun (key, v) ->
      if not (Hashtbl.mem seen key) then begin
        Hashtbl.replace seen key true;
        result := (key, v) :: !result
      end
    ) pairs
  ) pairs_by_priority;
  List.rev !result

let inheritable_keys = [
  "eval"; "arity"; "parse-arity"; "degree"; "pratipaksha";
  "copula"; "copula-plural"; "copula-formula";
  "matra"
]

let read_shabda (k : proof_graph) (node_name : string) : (string * string) list =
  let own = raw_shabda_for_node k node_name in
  let ancestors = walk_inheritance k node_name in
  let ancestor_shabda = List.map (fun a ->
    List.filter (fun (key, _) -> List.mem key inheritable_keys)
      (raw_shabda_for_node k a)
  ) ancestors in
  merge_shabda_priority (own :: ancestor_shabda)

let shabda_get (pairs : (string * string) list) (key : string) : string option =
  List.assoc_opt key pairs

(* ═══════════════════════════════════════════════════════════════════════════
   3. CLASSIFICATION — token_role, grammar, number words
   ═══════════════════════════════════════════════════════════════════════════ *)

let grammar_of_english_cache : (string, visheshanam option) Hashtbl.t = Hashtbl.create 64
let grammar_of_english_loaded = ref false

let load_grammar_of_english (k : proof_graph) : unit =
  if not !grammar_of_english_loaded then begin
    grammar_of_english_loaded := true;
    let pairs = read_shabda k "english-grammar" in
    List.iter (fun (word, vish_str) ->
      let v = visheshanam_of_string vish_str in
      Hashtbl.replace grammar_of_english_cache word v
    ) pairs
  end

let grammar_of_english (k : proof_graph) word =
  load_grammar_of_english k;
  let w = String.lowercase_ascii word in
  match Hashtbl.find_opt grammar_of_english_cache w with
  | Some v -> v
  | None   -> None

let english_token_roles_cache : (string, string) Hashtbl.t = Hashtbl.create 64
let english_token_roles_loaded = ref false

let load_english_token_roles (k : proof_graph) : unit =
  if not !english_token_roles_loaded then begin
    english_token_roles_loaded := true;
    let pairs = read_shabda k "english-token-roles" in
    List.iter (fun (token, role) ->
      Hashtbl.replace english_token_roles_cache token role
    ) pairs
  end

let english_number_words_cache : (string, string) Hashtbl.t = Hashtbl.create 32
let english_number_words_loaded = ref false

let load_english_number_words (k : proof_graph) : unit =
  if not !english_number_words_loaded then begin
    english_number_words_loaded := true;
    let pairs = read_shabda k "english-number-words" in
    List.iter (fun (n, word) ->
      Hashtbl.replace english_number_words_cache n word
    ) pairs
  end

let english_number_word (k : proof_graph) (n : string) : string option =
  load_english_number_words k;
  Hashtbl.find_opt english_number_words_cache n

type token_role =
  | Article
  | Grammar of int
  | Content of string
  | Number of float
  | Operator of string
  | Unknown of string

let classify_token (k : proof_graph) word =
  let w = String.lowercase_ascii word in
  let is_op = w = "+" || w = "-" || w = "*" || w = "/" || w = "=" in
  if is_op then Operator w
  else
  match float_of_string_opt w with
  | Some f -> Number f
  | None ->
  let is_number =
    match int_of_string_opt w with
    | Some _ -> true
    | None -> false
  in
  if is_number then
    match english_number_word k w with
    | Some mapped -> Content mapped
    | None -> Content w
  else begin
    load_english_token_roles k;
    match Hashtbl.find_opt english_token_roles_cache w with
    | Some "article" -> Article
    | Some "sthita" -> Grammar sthita
    | Some role ->
      (match grammar_of_english k role with
       | Some v -> Grammar v
       | None -> Content role)
    | None ->
      match grammar_of_english k w with
      | Some v -> Grammar v
      | None ->
        match Hashtbl.find_opt k.nodes w with
        | Some _ -> Content w
        | None ->
          let shabda_match = Hashtbl.fold (fun name _n acc ->
            (match acc with
            | Some _ -> acc
            | None ->
              let pairs = match Hashtbl.find_opt _shabda_store name with
                | Some p -> p | None -> [] in
              if pairs = [] then None
              else
                let word_match = match List.assoc_opt "word" pairs with
                  | Some wv ->
                    let words = String.split_on_char ',' wv
                      |> List.map (fun s -> String.lowercase_ascii (String.trim s))
                      |> List.filter (fun s -> String.length s > 0) in
                    List.mem w words
                  | None -> false in
                let name_match = match List.assoc_opt "name" pairs with
                  | Some n -> String.lowercase_ascii (String.trim n) = w
                  | None -> false in
                if word_match || name_match then Some name else None)
          ) k.nodes None in
          (match shabda_match with
          | Some name -> Content name
          | None ->
            let partial_matches = Hashtbl.fold (fun name _ acc ->
              let parts = String.split_on_char '-' name in
              if List.exists (fun p -> String.lowercase_ascii p = w) parts then
                name :: acc
              else acc
            ) k.nodes [] in
            match partial_matches with
            | [single] -> Content single
            | _ :: _ ->
              let domain_name = "domain-" ^ w in
              if List.mem domain_name partial_matches then Content domain_name
              else if List.mem w partial_matches then Content w
              else Content (List.hd (List.sort String.compare partial_matches))
            | [] -> Unknown w)
  end

(* ═══════════════════════════════════════════════════════════════════════════
   4. TOKENISATION + DOMAIN DETECTION
   ═══════════════════════════════════════════════════════════════════════════ *)

let tokenise s =
  let buf = Buffer.create 16 in
  let tokens = ref [] in
  String.iter (fun c ->
    match c with
    | ' ' | '\t' | '\n' | ',' | '.' | '?' | '!' | ':' | ';' | '(' | ')' ->
      if Buffer.length buf > 0 then begin
        tokens := Buffer.contents buf :: !tokens;
        Buffer.clear buf
      end
    | '-' -> Buffer.add_char buf c
    | c   -> Buffer.add_char buf (Char.lowercase_ascii c)
  ) s;
  if Buffer.length buf > 0 then tokens := Buffer.contents buf :: !tokens;
  List.rev !tokens

let domain_of_edge_target t =
  if String.length t > 7 && String.sub t 0 7 = "domain-" then
    Some (String.sub t 7 (String.length t - 7))
  else None

let detect_domain (k : proof_graph) (seeds : string list) : string =
  let found = List.find_map (fun seed ->
    match find k seed with
    | None -> None
    | Some n ->
      List.find_map (fun e ->
        if e.source = n.name && e.relation = sthita then
          domain_of_edge_target e.target
        else None
      ) n.edges
  ) seeds in
  match found with
  | Some d -> d
  | None -> "computation"

(* ═══════════════════════════════════════════════════════════════════════════
   5. GRAPH WALKS — edge readers, resolution, neighbours
   ═══════════════════════════════════════════════════════════════════════════ *)

let edges_by_rel (k : proof_graph) (name : string) (rel : visheshanam) : string list =
  with_node k name (fun n ->
    List.filter_map (fun e ->
      if e.source = name && e.relation = rel then Some e.target else None
    ) n.edges
  ) []

let kriya_of k name = edges_by_rel k name kriya
let swarupa_of k name = edges_by_rel k name swarupa
let yukta_of k name = edges_by_rel k name yukta
let janya_of k name = edges_by_rel k name janya

let has_domain_sthita (k : proof_graph) (name : string) (domain : string) : bool =
  let has_direct node_name =
    with_node k node_name (fun n ->
      List.exists (fun e ->
        e.source = node_name && e.relation = sthita && e.target = domain
      ) n.edges
    ) false
  in
  has_direct name ||
  List.exists has_direct (walk_inheritance k name)

let is_setu (k : proof_graph) (name : string) : bool =
  with_node k name (fun n ->
    List.exists (fun e ->
      e.source = name && e.relation = swarupa && e.target = "setu"
    ) n.edges
  ) false

let infer_inputs (k : proof_graph) (node_name : string) : string list =
  with_node k node_name (fun n ->
    List.filter_map (fun e ->
      if e.source = node_name && e.relation = sthita then
        let t = e.target in
        if String.length t >= 7 && String.sub t 0 7 = "domain-" then None
        else Some t
      else None
    ) n.edges
    |> List.sort_uniq String.compare
  ) []

let infer_outputs (k : proof_graph) (node_name : string) : string list =
  with_node k node_name (fun n ->
    List.filter_map (fun e ->
      if e.source = node_name && e.relation = phala then
        let t = e.target in
        if String.length t >= 7 && String.sub t 0 7 = "domain-" then None
        else Some t
      else None
    ) n.edges
    |> List.sort_uniq String.compare
  ) []

let sanitize_ocaml_ident (s : string) : string =
  let buf = Buffer.create (String.length s) in
  String.iter (fun c ->
    if (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z')
       || (c >= '0' && c <= '9') || c = '_' then
      Buffer.add_char buf (Char.lowercase_ascii c)
    else if c = '-' then Buffer.add_char buf '_'
    else ()
  ) s;
  let out = Buffer.contents buf in
  if out = "" then "x" else out

let capitalize_first (s : string) : string =
  if String.length s = 0 then s
  else let b = Bytes.of_string s in
       Bytes.set b 0 (Char.uppercase_ascii (Bytes.get b 0));
       Bytes.to_string b

let resolve (k : proof_graph) (name : string) : string list =
  match Hashtbl.find_opt k.nodes name with
  | None -> [name]
  | Some n ->
    let abheda_targets = List.filter_map (fun e ->
      if e.source = name && e.relation = abheda then Some e.target
      else None
    ) n.edges in
    let abheda_sources = List.filter_map (fun e ->
      if e.target = name && e.relation = abheda then Some e.source
      else None
    ) !(k.all_edges) in
    name :: abheda_targets @ abheda_sources

let resolve_to_canonical (k : proof_graph) (name : string) : string =
  match Hashtbl.find_opt k.nodes name with
  | Some _ -> name
  | None ->
    let shabda_hit = Hashtbl.fold (fun node_name _n acc ->
      match acc with
      | Some _ -> acc
      | None ->
        let pairs = match Hashtbl.find_opt _shabda_store node_name with
          | Some p -> p | None -> [] in
        if pairs = [] then None
        else
          let lname = String.lowercase_ascii name in
          let word_match = match List.assoc_opt "word" pairs with
            | Some w ->
              let words = String.split_on_char ',' w
                |> List.map (fun s -> String.lowercase_ascii (String.trim s))
                |> List.filter (fun s -> String.length s > 0) in
              List.mem lname words
            | None -> false in
          let name_match = match List.assoc_opt "name" pairs with
            | Some n -> String.lowercase_ascii (String.trim n) = lname
            | None -> false in
          if word_match || name_match then Some node_name
          else None
    ) k.nodes None in
    match shabda_hit with
    | Some canonical -> canonical
    | None -> name

let neighbours_of (k : proof_graph) (name : string) : string list =
  with_node k name (fun n ->
    let out_targets = List.map (fun e -> e.target) n.edges in
    let in_sources = List.filter_map (fun e ->
      if e.target = name then Some e.source else None
    ) !(k.all_edges) in
    List.sort_uniq String.compare (out_targets @ in_sources)
  ) []

let context_proximity (k : proof_graph) (candidate : string) (context : string) : int =
  let cn = neighbours_of k candidate in
  let ctx_n = neighbours_of k context in
  let ctx_set = Hashtbl.create 32 in
  List.iter (fun n -> Hashtbl.replace ctx_set n true) ctx_n;
  let direct_bonus =
    if Hashtbl.mem ctx_set candidate || List.mem context cn then 2000
    else 0
  in
  let shared = List.fold_left (fun acc n ->
    if Hashtbl.mem ctx_set n then acc + 1 else acc
  ) 0 cn in
  direct_bonus + (shared * 300)

let rec find_setu_form (k : proof_graph) (name : string) (depth : int) (visited : string list) : string option =
  if depth = 0 || List.mem name visited then None
  else begin
    let visited = name :: visited in
    let is_ocaml_node =
      with_node k name (fun n ->
        List.exists (fun e ->
          e.source = name && e.relation = sthita
           && (e.target = "domain-ocaml" || e.target = "domain-language")
        ) n.edges
      ) false
    in
    if is_ocaml_node then Some name
    else begin
      let next = List.filter_map (fun e ->
        if e.source = name &&
           (e.relation = abheda || e.relation = kriya || e.relation = swarupa || e.relation = yukta)
        then Some e.target
        else None
      ) !(k.all_edges) in
      List.find_map (fun t -> find_setu_form k t (depth - 1) visited) next
    end
  end

let resolve_ocaml_forms (k : proof_graph) (seeds : string list) : (string * string) list =
  let setu_map = read_shabda k "ocaml-setu" in
  List.filter_map (fun seed ->
    match find_setu_form k seed 5 [] with
    | Some setu_node ->
      (match shabda_get setu_map setu_node with
       | Some construct -> Some (seed, construct)
       | None -> None)
    | None -> None
  ) seeds

let rec walk_chain (k : proof_graph) (name : string) (depth : int) (visited : string list) : string list =
  if depth = 0 || List.mem name visited then visited
  else
    let visited = name :: visited in
    match find k name with
    | None -> visited
    | Some n ->
      let next = List.filter_map (fun e ->
        if e.source = name &&
           (e.relation = kriya || e.relation = phala || e.relation = swarupa || e.relation = abheda)
        then Some e.target else None) n.edges in
      List.fold_left (fun acc t -> walk_chain k t (depth - 1) acc) visited next

(* ═══════════════════════════════════════════════════════════════════════════
   6. TO_ENGLISH — English rendering of graph nodes
   ═══════════════════════════════════════════════════════════════════════════ *)

let to_english ?(context : string option = None)
               ?(ppr : (string, float) Hashtbl.t option = None)
               (k : proof_graph) (name : string) : string =
  let english_names = Hashtbl.fold (fun source n acc ->
    let has_abheda = List.exists (fun e ->
      e.target = name && e.relation = abheda
    ) n.edges in
    if has_abheda && source <> name then source :: acc
    else acc
  ) k.nodes [] in
  let score candidate =
    match Hashtbl.find_opt k.nodes candidate with
    | None -> 0
    | Some n ->
      let total_edges = List.length n.edges in
      let abheda_edges = List.length (List.filter (fun e ->
        e.relation = abheda
      ) n.edges) in
      let non_abheda_out = List.length (List.filter (fun e ->
        e.relation <> abheda
      ) n.edges) in
      let non_abheda_in = List.length (List.filter (fun e ->
        e.target = candidate && e.relation <> abheda
      ) !(k.all_edges)) in
      let ratio = if total_edges > 0
        then (abheda_edges * 1000) / total_edges
        else 0 in
      let len = String.length candidate in
      let len_bonus = if len >= 3 && len <= 25 then 50 else 0 in
      let sloka_penalty = List.length n.slokas * 100 in
      let structure_penalty = (non_abheda_out * 300) + (non_abheda_in * 200) in
      let context_bonus = match context with
        | None -> 0
        | Some ctx -> context_proximity k candidate ctx
      in
      let ppr_bonus = match ppr with
        | None -> 0
        | Some tbl ->
          (match Hashtbl.find_opt tbl candidate with
           | Some s -> int_of_float (s *. 500.0)
           | None   -> 0)
      in
      ratio + len_bonus - sloka_penalty - structure_penalty + context_bonus + ppr_bonus
  in
  let pick_best names =
    match names with
    | [] -> None
    | [one] -> Some one
    | multiple ->
      Some (List.hd (List.sort (fun a b -> compare (score b) (score a)) multiple))
  in
  let direct = pick_best english_names in
  let bridged =
    if direct <> None then []
    else Hashtbl.fold (fun candidate n acc ->
      let abheda_targets = List.filter_map (fun e ->
        if e.relation = abheda then Some e.target else None
      ) n.edges in
      let matches_bridge = List.exists (fun mid ->
        match Hashtbl.find_opt k.nodes mid with
        | None -> false
        | Some mid_n ->
          List.exists (fun e -> e.relation = abheda && e.target = name) mid_n.edges
      ) abheda_targets in
      if matches_bridge && candidate <> name then candidate :: acc else acc
    ) k.nodes []
  in
  let bridged = List.sort_uniq String.compare bridged in
  match direct with
  | Some best -> best
  | None ->
    (match pick_best bridged with
    | Some best -> best
    | None -> name)
