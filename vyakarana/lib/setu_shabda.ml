(* setu_shabda.ml — shabda I/O: parse and read node metadata strings.
   pure data layer — no graph policy, no classification, no scoring.
   dependency: Proof_graph only. *)

open Proof_graph

(* parse_shabda: "key:value key:value ..." -> [(key, value); ...]
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

(* ---- global shabda store ----
   loaded from brahman/shabda/*.shabda files at startup.
   stores parsed (key, value) pairs per node — the native query format.
   all consumers query pairs directly via shabda_get or List.assoc_opt. *)

let _shabda_store : (string, (string * string) list) Hashtbl.t = Hashtbl.create 1024

(* --- S-expression shabda parser ---
   format:
     shabda node-name
       (key value ...)
       (word a b c)
       -- comment
     done

   Parses directly into (key, value) pairs — the native query format.
   Multi-value: (word a b c) → ("word", "a,b,c")
   Single-value: (eval mul) → ("eval", "mul")
   Description: (desc "text") → ("desc", "text")
   Alias: (alias x y) → ("name", "x y")  *)

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

(* detect whether a file uses S-expression format *)
let is_sexp_format (lines : string list) : bool =
  List.exists (fun line ->
    let trimmed = String.trim line in
    String.length trimmed > 7 &&
    String.sub trimmed 0 7 = "shabda " &&
    trimmed.[6] = ' '
  ) lines

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

(* load flat file: returns (node-name, pairs) list *)
let load_flat_file (lines : string list) : (string * (string * string) list) list =
  let results = ref [] in
  List.iter (fun line ->
    let trimmed = String.trim line in
    if String.length trimmed > 0 && trimmed.[0] <> '#' then
      match String.index_opt trimmed ':' with
      | Some ci ->
        let name = String.trim (String.sub trimmed 0 ci) in
        let raw = String.trim (String.sub trimmed (ci + 1)
                    (String.length trimmed - ci - 1)) in
        if String.length name > 0 && String.length raw > 0 then
          results := (name, parse_shabda raw) :: !results
      | None -> ()
  ) lines;
  List.rev !results

(* load all *.shabda files from a directory into the store.
   auto-detects format per file: S-expression or flat. *)
let load_shabda_dir (dir : string) : int =
  if not (Sys.file_exists dir && Sys.is_directory dir) then 0
  else begin
    let count = ref 0 in
    let entries = Sys.readdir dir in
    Array.iter (fun fname ->
      if Filename.check_suffix fname ".shabda" then begin
        let path = Filename.concat dir fname in
        try
          let ic = open_in path in
          let all_lines = ref [] in
          (try while true do
            all_lines := input_line ic :: !all_lines
          done with End_of_file -> ());
          close_in ic;
          let lines = List.rev !all_lines in
          let entries_list =
            if is_sexp_format lines then load_sexp_file lines
            else load_flat_file lines
          in
          List.iter (fun (name, pairs) ->
            Hashtbl.replace _shabda_store name pairs;
            incr count
          ) entries_list
        with _ -> ()
      end
    ) entries;
    !count
  end

(* raw_shabda_for_node: read a single node's own shabda without inheritance.
   priority: 1) global shabda store (from .shabda files)  2) inline shabda on node *)
let raw_shabda_for_node (k : proof_graph) (node_name : string) : (string * string) list =
  (* shabda store has all entries from brahman/shabda/*.shabda — check first *)
  match Hashtbl.find_opt _shabda_store node_name with
  | Some pairs -> pairs
  | None ->
    (* fallback: inline shabda on the .om node *)
    match find k node_name with
    | None -> []
    | Some n ->
      let inline = parse_shabda n.shabda in
      if inline <> [] then inline else []

(* merge_shabda_priority: merge shabda pairs where earlier lists have higher priority.
   pairs_by_priority: [own_pairs; immediate_parent_pairs; grandparent_pairs; ...]
   For each key, the first (highest-priority) value wins. *)
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

(* inheritable_keys: only these keys flow upward through IS-A inheritance.
   structural/classification keys (role:, word:, name:, krama-lhs/rhs) are node-own only. *)
let inheritable_keys = [
  "eval"; "arity"; "parse-arity"; "degree"; "pratipaksha";
  "copula"; "copula-plural"; "copula-formula";
  "matra"
]

(* read_shabda: return effective shabda pairs for a node, including inherited pairs.
   inheritance chain: walk dhatu, abheda, swarupa edges (IS-A only) via Proof_graph.
   own pairs win over inherited pairs on key conflict.
   Only inheritable_keys flow from ancestors — structural keys (role:, word:, name:) stay local. *)
let read_shabda (k : proof_graph) (node_name : string) : (string * string) list =
  let own = raw_shabda_for_node k node_name in
  let ancestors = Proof_graph.walk_inheritance k node_name in
  let ancestor_shabda = List.map (fun a ->
    List.filter (fun (key, _) -> List.mem key inheritable_keys)
      (raw_shabda_for_node k a)
  ) ancestors in
  merge_shabda_priority (own :: ancestor_shabda)

let shabda_get (pairs : (string * string) list) (key : string) : string option =
  List.assoc_opt key pairs
