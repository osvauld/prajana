(* setu.ml — graph walk utilities + shabda reader
   the bridge between raw graph structure and domain renderers.
   reads the graph. does not emit. does not print.

   dependency: Proof_graph only. *)

open Proof_graph

(* --- shabda reader ---
   parse_shabda: "key:value key:value ..." -> [(key, value); ...]
   read_shabda:  find node, return its parsed shabda pairs *)

let parse_shabda (s : string) : (string * string) list =
  (* Scan left-to-right. A new key starts whenever a space-separated token
     contains ':' and the part before ':' contains only key-safe chars
     (letters, digits, '-', '_'). Everything between two such boundaries
     is the value of the preceding key, allowing spaces in values. *)
  if String.length s = 0 then []
  else
    let is_key_char c =
      (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
      (c >= '0' && c <= '9') || c = '-' || c = '_' ||
      (* symbols — the graph needs to know what these characters are *)
      c = '+' || c = '*' || c = '/' || c = '=' ||
      c = '.' || c = '?' || c = '!' || c = ',' || c = ';' ||
      c = '\'' || c = '#' || c = '@' || c = '&' || c = '%'
    in
    let is_key_token tok =
      match String.split_on_char ':' tok with
      | k :: _ :: _ when String.length k > 0 ->
        String.to_seq k |> Seq.for_all is_key_char
      | _ -> false
    in
    let tokens = String.split_on_char ' ' (String.trim s) in
    (* collect (key, rest_of_first_token, subsequent_value_tokens) groups *)
    let groups : (string * string list) list ref = ref [] in
    let cur_key  = ref "" in
    let cur_vals = ref [] in
    List.iter (fun tok ->
      if is_key_token tok then begin
        if String.length !cur_key > 0 then
          groups := (!cur_key, List.rev !cur_vals) :: !groups;
        (match String.split_on_char ':' tok with
         | k :: rest ->
           cur_key  := k;
           let v = String.concat ":" rest in
           cur_vals := if String.length v > 0 then [v] else []
         | _ -> ())
      end else begin
        if String.length !cur_key > 0 then
          cur_vals := tok :: !cur_vals
      end
    ) tokens;
    if String.length !cur_key > 0 then
      groups := (!cur_key, List.rev !cur_vals) :: !groups;
    let pairs = List.filter_map (fun (k, vs) ->
      let v = String.trim (String.concat " " vs) in
      if String.length v > 0 then Some (k, v) else None
    ) (List.rev !groups) in
    (* if no key:value pairs found, treat the text before '/' as the "name" key —
       this handles inline shabda like: shabda bridge / the-crossing-that-carries-meaning-across *)
    if pairs = [] then
      let before_slash = match String.index_opt s '/' with
        | Some i -> String.trim (String.sub s 0 i)
        | None   -> String.trim s
      in
      if String.length before_slash > 0 then [("name", before_slash)] else []
    else pairs

(* parse_shabda_file: read a .shabda file — one "key: value" per line.
   blank lines and lines starting with # are ignored.
   multiline values: if value is "|", subsequent indented lines are collected
   until a non-indented non-empty line is found. *)
let parse_shabda_file (path : string) : (string * string) list =
  try
    let ic = open_in path in
    let all_lines = ref [] in
    (try
      while true do
        all_lines := input_line ic :: !all_lines
      done
    with End_of_file -> ());
    close_in ic;
    let lines = Array.of_list (List.rev !all_lines) in
    let n = Array.length lines in
    let pairs = ref [] in
    let i = ref 0 in
    while !i < n do
      let line = lines.(!i) in
      let trimmed = String.trim line in
      if String.length trimmed > 0 && trimmed.[0] <> '#' then begin
        match String.index_opt trimmed ':' with
        | Some ci ->
          let k = String.trim (String.sub trimmed 0 ci) in
          let v = String.trim (String.sub trimmed (ci + 1) (String.length trimmed - ci - 1)) in
          if String.length k > 0 then begin
            if v = "|" then begin
              (* multiline block: collect indented lines until dedent *)
              incr i;
              let buf = Buffer.create 256 in
              while !i < n && (
                let l = lines.(!i) in
                String.length l = 0 ||
                (String.length l > 0 && (l.[0] = ' ' || l.[0] = '\t'))
              ) do
                (* strip exactly 2 leading spaces if present *)
                let raw = lines.(!i) in
                let stripped =
                  if String.length raw >= 2 && raw.[0] = ' ' && raw.[1] = ' '
                  then String.sub raw 2 (String.length raw - 2)
                  else raw
                in
                Buffer.add_string buf stripped;
                Buffer.add_char buf '\n';
                incr i
              done;
              pairs := (k, Buffer.contents buf) :: !pairs
            end else begin
              pairs := (k, v) :: !pairs;
              incr i
            end
          end else incr i
        | None -> incr i
      end else incr i
    done;
    List.rev !pairs
  with _ -> []

let read_shabda (k : proof_graph) (node_name : string) : (string * string) list =
  match find k node_name with
  | None -> []
  | Some n ->
    let inline = parse_shabda n.shabda in
    (* if inline shabda contains a shabda-tmpl key, load the file instead *)
    match List.assoc_opt "shabda-tmpl" inline with
    | Some rel_path ->
      (* search kosha_root first, then all loaded dirs (covers session dirs) *)
      let search_roots =
        let kr = !(k.kosha_root) in
        let base_roots = if String.length kr > 0 then [kr] else [] in
        base_roots @ !(k.search_dirs)
      in
      (* try each root in order; use the first file that exists *)
      let rec try_roots = function
        | [] ->
          (* last resort: treat rel_path as absolute/cwd-relative *)
          parse_shabda_file rel_path
        | root :: rest ->
          let full_path = Filename.concat root rel_path in
          if Sys.file_exists full_path then parse_shabda_file full_path
          else try_roots rest
      in
      try_roots search_roots
    | None -> inline

let shabda_get (pairs : (string * string) list) (key : string) : string option =
  List.assoc_opt key pairs

(* --- tokenise --- *)

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

let bigrams tokens =
  let rec loop = function
    | [] | [_] -> []
    | a :: b :: rest -> (a ^ "-" ^ b) :: loop (b :: rest)
  in loop tokens

(* --- domain detection --- *)

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
        if e.source = n.name && e.relation = Sthita then
          domain_of_edge_target e.target
        else None
      ) n.edges
  ) seeds in
  match found with
  | Some d -> d
  | None -> "computation"

(* --- graph walk: edge readers --- *)

let kriya_of (k : proof_graph) (name : string) : string list =
  match Hashtbl.find_opt k.nodes name with
  | None -> []
  | Some n -> List.filter_map (fun e ->
      if e.source = name && e.relation = Kriya then Some e.target else None
    ) n.edges

let swarupa_of (k : proof_graph) (name : string) : string list =
  match Hashtbl.find_opt k.nodes name with
  | None -> []
  | Some n -> List.filter_map (fun e ->
      if e.source = name && e.relation = Swarupa then Some e.target else None
    ) n.edges

let yukta_of (k : proof_graph) (name : string) : string list =
  match Hashtbl.find_opt k.nodes name with
  | None -> []
  | Some n -> List.filter_map (fun e ->
      if e.source = name && e.relation = Yukta then Some e.target else None
    ) n.edges

let janya_of (k : proof_graph) (name : string) : string list =
  match Hashtbl.find_opt k.nodes name with
  | None -> []
  | Some n -> List.filter_map (fun e ->
      if e.source = name && e.relation = Janya then Some e.target else None
    ) n.edges

let has_domain_sthita (k : proof_graph) (name : string) (domain : string) : bool =
  match Hashtbl.find_opt k.nodes name with
  | None -> false
  | Some n -> List.exists (fun e ->
      e.source = name && e.relation = Sthita && e.target = domain
    ) n.edges

let is_setu (k : proof_graph) (name : string) : bool =
  match Hashtbl.find_opt k.nodes name with
  | None -> false
  | Some n -> List.exists (fun e ->
      e.source = name && e.relation = Swarupa && e.target = "setu"
    ) n.edges

let infer_inputs (k : proof_graph) (node_name : string) : string list =
  match Hashtbl.find_opt k.nodes node_name with
  | None -> []
  | Some n ->
    List.filter_map (fun e ->
      if e.source = node_name && e.relation = Sthita then
        let t = e.target in
        let is_domain = String.length t >= 7 && String.sub t 0 7 = "domain-" in
        if is_domain then None else Some t
      else None
    ) n.edges
    |> List.sort_uniq String.compare

let infer_outputs (k : proof_graph) (node_name : string) : string list =
  match Hashtbl.find_opt k.nodes node_name with
  | None -> []
  | Some n ->
    List.filter_map (fun e ->
      if e.source = node_name && e.relation = Phala then
        let t = e.target in
        let is_domain = String.length t >= 7 && String.sub t 0 7 = "domain-" in
        if is_domain then None else Some t
      else None
    ) n.edges
    |> List.sort_uniq String.compare

(* --- name resolution --- *)

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
      if e.source = name && e.relation = Abheda then Some e.target
      else None
    ) n.edges in
    let abheda_sources = List.filter_map (fun e ->
      if e.target = name && e.relation = Abheda then Some e.source
      else None
    ) !(k.all_edges) in
    name :: abheda_targets @ abheda_sources

(* collect all neighbours of a node within 1 hop — all edge targets and sources *)
let neighbours_of (k : proof_graph) (name : string) : string list =
  match Hashtbl.find_opt k.nodes name with
  | None -> []
  | Some n ->
    let out_targets = List.map (fun e -> e.target) n.edges in
    let in_sources = List.filter_map (fun e ->
      if e.target = name then Some e.source else None
    ) !(k.all_edges) in
    List.sort_uniq String.compare (out_targets @ in_sources)

(* shared-neighbour count between two nodes — context proximity score *)
let context_proximity (k : proof_graph) (candidate : string) (context : string) : int =
  let cn = neighbours_of k candidate in
  let ctx_n = neighbours_of k context in
  let ctx_set = Hashtbl.create 32 in
  List.iter (fun n -> Hashtbl.replace ctx_set n true) ctx_n;
  (* direct connection is strongest signal *)
  let direct_bonus =
    if Hashtbl.mem ctx_set candidate || List.mem context cn then 2000
    else 0
  in
  let shared = List.fold_left (fun acc n ->
    if Hashtbl.mem ctx_set n then acc + 1 else acc
  ) 0 cn in
  direct_bonus + (shared * 300)

let to_english ?(context : string option = None) (k : proof_graph) (name : string) : string =
  let english_names = Hashtbl.fold (fun source n acc ->
    let has_abheda = List.exists (fun e ->
      e.target = name && e.relation = Abheda
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
        e.relation = Abheda
      ) n.edges) in
      let non_abheda_out = List.length (List.filter (fun e ->
        e.relation <> Abheda
      ) n.edges) in
      let non_abheda_in = List.length (List.filter (fun e ->
        e.target = candidate && e.relation <> Abheda
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
      ratio + len_bonus - sloka_penalty - structure_penalty + context_bonus
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
        if e.relation = Abheda then Some e.target else None
      ) n.edges in
      let matches_bridge = List.exists (fun mid ->
        match Hashtbl.find_opt k.nodes mid with
        | None -> false
        | Some mid_n ->
          List.exists (fun e -> e.relation = Abheda && e.target = name) mid_n.edges
      ) abheda_targets in
      if matches_bridge && candidate <> name then candidate :: acc else acc
    ) k.nodes []
  in
  let bridged = List.sort_uniq String.compare bridged in
  match english_names with
  | _ ->
    (match direct with
    | Some best -> best
    | None ->
      (match pick_best bridged with
      | Some best -> best
      | None -> name))

(* --- grammar classification --- *)
(* reads from english-grammar node shabda: word:visheshanam pairs *)

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
  | Grammar of visheshanam
  | Content of string
  | Number of float
  | Operator of string
  | Unknown of string

let classify_token (k : proof_graph) word =
  let w = String.lowercase_ascii word in
  (* detect operators first *)
  let is_op = w = "+" || w = "-" || w = "*" || w = "/" || w = "=" in
  if is_op then Operator w
  else
  (* detect numbers: try float first (handles "9.8", "3.14"), then int *)
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
    | Some "sthita" -> Grammar Sthita
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
          (* search node shabda lines for this English word — checked before partial name match *)
          let shabda_match = Hashtbl.fold (fun name n acc ->
            (match acc with
            | Some _ -> acc
            | None ->
              let shabda = String.lowercase_ascii (String.trim n.shabda) in
              if shabda = "" then None
              else
                let before_slash = (match String.index_opt shabda '/' with
                  | Some i -> String.sub shabda 0 i
                  | None -> shabda)
                in
                let tokens = String.split_on_char ',' before_slash
                  |> List.map String.trim
                  |> List.concat_map (fun t -> String.split_on_char ' ' t)
                  |> List.map String.trim
                  |> List.filter (fun t -> String.length t > 0)
                in
                if List.mem w tokens then Some name else None)
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
              (* prefer domain-<word> exact match first, then word itself, then alphabetical *)
              let domain_name = "domain-" ^ w in
              if List.mem domain_name partial_matches then Content domain_name
              else if List.mem w partial_matches then Content w
              else Content (List.hd (List.sort String.compare partial_matches))
            | [] -> Unknown w)
  end

(* --- setu walk: find OCaml construct for a seed --- *)

let rec find_setu_form (k : proof_graph) (name : string) (depth : int) (visited : string list) : string option =
  if depth = 0 || List.mem name visited then None
  else begin
    let visited = name :: visited in
    let is_ocaml_node = match find k name with
      | None -> false
      | Some n -> List.exists (fun e ->
          e.source = name && e.relation = Sthita
          && (e.target = "domain-ocaml" || e.target = "domain-language")
        ) n.edges
    in
    if is_ocaml_node then Some name
    else begin
      let next = List.filter_map (fun e ->
        if e.source = name &&
           (e.relation = Abheda || e.relation = Kriya || e.relation = Swarupa || e.relation = Yukta)
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

(* --- walk: follow kriya/phala chains from seeds --- *)

(* resolve_to_canonical: given a name (as written in a tantra file),
   find the canonical graph node name.
   1. If the name is already a graph node, return it as-is.
   2. Search all nodes' shabda fields for the name → return that node's name.
   3. Otherwise return the name unchanged. *)
let resolve_to_canonical (k : proof_graph) (name : string) : string =
  (* 1. direct node lookup *)
  match Hashtbl.find_opt k.nodes name with
  | Some _ -> name
  | None ->
    (* 2. search shabda fields for this name *)
    let shabda_hit = Hashtbl.fold (fun node_name n acc ->
      match acc with
      | Some _ -> acc
      | None ->
        let raw = String.lowercase_ascii (String.trim n.shabda) in
        if raw = "" then None
        else
          (* shabda format: "key:val key:val ..." or just words before '/' *)
          let before_slash = match String.index_opt raw '/' with
            | Some i -> String.sub raw 0 i
            | None -> raw
          in
          (* tokenize: split on spaces/commas, check if any token = name *)
          let tokens = String.split_on_char ',' before_slash
            |> List.map String.trim
            |> List.concat_map (fun t -> String.split_on_char ' ' t)
            |> List.map String.trim
            |> List.filter (fun t -> String.length t > 0)
          in
          if List.mem (String.lowercase_ascii name) tokens then Some node_name
          else None
    ) k.nodes None in
    match shabda_hit with
    | Some canonical -> canonical
    | None -> name

let rec walk_chain (k : proof_graph) (name : string) (depth : int) (visited : string list) : string list =
  if depth = 0 || List.mem name visited then visited
  else
    let visited = name :: visited in
    match find k name with
    | None -> visited
    | Some n ->
      let next = List.filter_map (fun e ->
        if e.source = name &&
           (e.relation = Kriya || e.relation = Phala || e.relation = Swarupa || e.relation = Abheda)
        then Some e.target else None) n.edges in
      List.fold_left (fun acc t -> walk_chain k t (depth - 1) acc) visited next
