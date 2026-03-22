(* setu_shabda.ml — shabda I/O: parse and read node metadata strings.
   pure data layer — no graph policy, no classification, no scoring.
   dependency: Proof_graph only.

   All .shabda files use S-expression format:
     shabda node-name
       (key value ...)
       (word a b c)
     done
*)

open Proof_graph

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

(* load all *.shabda files from a directory into the store. *)
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

(* raw_shabda_for_node: read a single node's own shabda from the store. *)
let raw_shabda_for_node (_k : proof_graph) (node_name : string) : (string * string) list =
  match Hashtbl.find_opt _shabda_store node_name with
  | Some pairs -> pairs
  | None -> []

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
