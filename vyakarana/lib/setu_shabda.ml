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

(* raw_shabda_for_node: read a single node's own shabda without inheritance.
   handles shabda-tmpl file indirection exactly as before. *)
let raw_shabda_for_node (k : proof_graph) (node_name : string) : (string * string) list =
  match find k node_name with
  | None -> []
  | Some n ->
    let inline = parse_shabda n.shabda in
    match List.assoc_opt "shabda-tmpl" inline with
    | Some rel_path ->
      let search_roots =
        let kr = !(k.kosha_root) in
        let base_roots = if String.length kr > 0 then [kr] else [] in
        base_roots @ !(k.search_dirs)
      in
      let rec try_roots = function
        | [] -> parse_shabda_file rel_path
        | root :: rest ->
          let full_path = Filename.concat root rel_path in
          if Sys.file_exists full_path then parse_shabda_file full_path
          else try_roots rest
      in
      try_roots search_roots
    | None -> inline

(* merge_shabda_priority: merge shabda pairs where earlier lists have higher priority.
   pairs_by_priority: [own_pairs; immediate_parent_pairs; grandparent_pairs; ...]
   For each key, the first (highest-priority) value wins.
   shabda-tmpl is never inherited — it would resolve the wrong file. *)
let merge_shabda_priority (pairs_by_priority : (string * string) list list)
    : (string * string) list =
  let seen = Hashtbl.create 16 in
  let result = ref [] in
  List.iter (fun pairs ->
    List.iter (fun (key, v) ->
      if key <> "shabda-tmpl" && not (Hashtbl.mem seen key) then begin
        Hashtbl.replace seen key true;
        result := (key, v) :: !result
      end
    ) pairs
  ) pairs_by_priority;
  List.rev !result

(* read_shabda: return effective shabda pairs for a node, including inherited pairs.
   inheritance chain: walk dhatu, abheda, swarupa edges (IS-A only) via Proof_graph.
   own pairs win over inherited pairs on key conflict. *)
let read_shabda (k : proof_graph) (node_name : string) : (string * string) list =
  let own = raw_shabda_for_node k node_name in
  let ancestors = Proof_graph.walk_inheritance k node_name in
  let ancestor_shabda = List.map (raw_shabda_for_node k) ancestors in
  merge_shabda_priority (own :: ancestor_shabda)

let shabda_get (pairs : (string * string) list) (key : string) : string option =
  List.assoc_opt key pairs
