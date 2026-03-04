(* om_parser.ml — reads .om suktas into the proof space
   two-pass parser:
     pass 1: collect all node names (the vocabulary)
     pass 2: parse slokas, decompose compounds into typed edges

   .om format:
     sangati <name>   -- universal structural truth (Sanskrit body only)
       "<sloka 1>"
       "<sloka 2>"
       ...
     done

     kosha <name>     -- domain application (may reference sangati + other kosha)
       "<sloka 1>"
       ...
     done

   everything else is ignored. comments (--) are inert. *)

open Proof_graph

(* recursively collect all .om file paths under a directory *)
let om_files_recursive (root : string) : string list =
  let files = ref [] in
  let rec walk dir =
    try
      let entries = Sys.readdir dir in
      Array.iter (fun entry ->
        let path = Filename.concat dir entry in
        try
          if Sys.is_directory path then walk path
          else if Filename.check_suffix entry ".om" then
            files := path :: !files
        with _ -> ()
      ) entries
    with _ -> ()
  in
  walk root;
  List.sort String.compare !files

(* --- pass 1: collect names --- *)

(* extract layer and node name from a header line.
   recognizes both:
     sangati <name>  — universal structural truth
     kosha <name>    — domain application
   returns Some (layer_string, name) or None *)
let parse_node_header line =
  let line = String.trim line in
  let try_prefix prefix =
    let plen = String.length prefix in
    if String.length line > plen + 1
       && String.sub line 0 plen = prefix
       && (line.[plen] = ' ' || line.[plen] = '\t') then
      let rest = String.trim (String.sub line plen (String.length line - plen)) in
      match String.split_on_char ' ' rest with
      | name :: _ when String.length name > 0 -> Some (prefix, name)
      | _ -> None
    else
      None
  in
  match try_prefix "sangati" with
  | Some r -> Some r
  | None   -> try_prefix "kosha"

(* collect all node names from a directory *)
let collect_names dir : string list =
  let names = ref [] in
  List.iter (fun path ->
    try
      let ic = open_in path in
      (try
        while true do
          let line = input_line ic in
          match parse_node_header line with
          | Some (_layer, name) -> names := name :: !names; raise Exit
          | None -> ()
        done
      with Exit | End_of_file -> ());
      close_in ic
    with _ -> ()
  ) (om_files_recursive dir);
  !names

(* --- pass 2: sloka decomposition --- *)

(* extract a quoted string from a line: "content" -> Some content *)
let parse_sloka line =
  let line = String.trim line in
  if String.length line >= 2 then
    try
      let q1 = String.index line '"' in
      let q2 = String.rindex line '"' in
      if q2 > q1 then
        Some (String.sub line (q1 + 1) (q2 - q1 - 1))
      else
        None
    with Not_found -> None
  else
    None

(* try to match a compound word against known names + visheshanam suffix
   e.g. "dharana-jivamsha-swarupa" -> Some ("dharana-jivamsha", Swarupa)
   tries longest name match first.
   fallback: if no known name matches, try splitting at last '-' before
   a known visheshanam suffix — allows cross-layer references to names
   not in this graph *)
let decompose_compound (known_names : string list) (word : string) : (string * visheshanam) option =
  (* sort names by length descending — try longest first *)
  let sorted_names = List.sort (fun a b ->
    compare (String.length b) (String.length a)
  ) known_names in
  let word_lower = String.lowercase_ascii word in
  let try_name name =
    let name_lower = String.lowercase_ascii name in
    let name_len = String.length name_lower in
    let word_len = String.length word_lower in
    (* name must be followed by '-' then visheshanam *)
    if word_len > name_len + 1
       && String.sub word_lower 0 name_len = name_lower
       && word_lower.[name_len] = '-' then
      let suffix = String.sub word_lower (name_len + 1) (word_len - name_len - 1) in
      match visheshanam_of_string suffix with
      | Some v -> Some (name, v)
      | None -> None
    else
      None
  in
  (* try each name, longest first *)
  let rec try_names = function
    | [] -> None
    | name :: rest ->
      match try_name name with
      | Some result -> Some result
      | None -> try_names rest
  in
  match try_names sorted_names with
  | Some result -> Some result
  | None ->
    (* fallback: split at last '-' and check if suffix is a visheshanam *)
    let rec try_last_dash i =
      if i <= 0 then None
      else if word_lower.[i] = '-' then
        let suffix = String.sub word_lower (i + 1) (String.length word_lower - i - 1) in
        match Proof_graph.visheshanam_of_string suffix with
        | Some v ->
          let prefix = String.sub word 0 i in
          Some (prefix, v)
        | None -> try_last_dash (i - 1)
      else try_last_dash (i - 1)
    in
    try_last_dash (String.length word_lower - 1)

(* decompose all words in a sloka into typed edges *)
let decompose_sloka (known_names : string list) (source : string) (sloka : string)
    : typed_edge list =
  let words = String.split_on_char ' ' sloka in
  List.filter_map (fun word ->
    let word = String.trim word in
    if String.length word = 0 then None
    else
      match decompose_compound known_names word with
      | Some (target, relation) ->
        Some { source; target; relation }
      | None -> None
  ) words

(* parse one .om file into a nigamana (pass 2) *)
let parse_file (known_names : string list) (path : string) : nigamana option =
  try
    let ic = open_in path in
    let lines = ref [] in
    (try
      while true do
        lines := input_line ic :: !lines
      done
    with End_of_file -> ());
    close_in ic;
    let lines = List.rev !lines in

    let name = ref None in
    let layer = ref "sangati" in
    let slokas = ref [] in
    let shabda_val = ref "" in

    List.iter (fun line ->
      (* extract name and layer *)
      (match parse_node_header line with
      | Some (lyr, n) -> name := Some n; layer := lyr
      | None ->
        (* extract shabda — unquoted line starting with "shabda " *)
        let trimmed = String.trim line in
        let shabda_prefix = "shabda " in
        let shabda_len = String.length shabda_prefix in
        if String.length trimmed > shabda_len
           && String.sub trimmed 0 shabda_len = shabda_prefix then
          shabda_val := String.trim (String.sub trimmed shabda_len
                          (String.length trimmed - shabda_len))
        else
        (* extract sloka — any quoted line that isn't a comment *)
        if String.length trimmed > 0
           && trimmed.[0] <> '-'  (* not a comment *)
           && trimmed <> "done"
           && (parse_node_header trimmed = None) then
          match parse_sloka line with
          | Some s when String.length s > 0 -> slokas := s :: !slokas
          | _ -> ()
      )
    ) lines;

    match !name with
    | None -> None
    | Some n ->
      let slokas_list = List.rev !slokas in
      (* decompose all slokas into edges *)
      let edges = List.concat_map (decompose_sloka known_names n) slokas_list in
      Some {
        name   = n;
        layer  = !layer;
        slokas = slokas_list;
        edges;
        satya  = 0.0;  (* will be computed by satya-ganana *)
        shabda = !shabda_val;
      }
  with _ -> None

(* load all .om files from a directory — two-pass *)
let load_dir ?(emit_meta = true) dir (k : proof_graph) : proof_graph * int * int =
  (* pass 1: collect all names *)
  let known_names = collect_names dir in
  (* pass 2: parse all files with known names *)
  let loaded = ref 0 in
  let skipped = ref 0 in
  let k_ref = ref k in
  List.iter (fun path ->
    match parse_file known_names path with
    | Some n ->
      k_ref := join !k_ref n;
      incr loaded
    | None ->
      incr skipped
  ) (om_files_recursive dir);
  (* run satya-ganana: avrti convergence *)
  let iterations = satya_ganana !k_ref in
  if emit_meta then
    Printf.printf "truth-scoring (satya-ganana): %d spiral-passes (avrti)\n%!" iterations;
  (!k_ref, !loaded, !skipped)

(* load multiple directories into one graph — unified namespace
   pass 1: collect names from ALL directories
   pass 2: parse all files with the combined vocabulary
   satya-ganana runs once on the unified graph *)
let load_dirs ?(emit_meta = true) (dirs : string list) (k : proof_graph) : proof_graph * int * int =
  (* pass 1: collect names from all directories *)
  let known_names = List.concat_map collect_names dirs in
  (* pass 2: parse all files from all directories *)
  let loaded = ref 0 in
  let skipped = ref 0 in
  let k_ref = ref k in
  List.iter (fun dir ->
    List.iter (fun path ->
      match parse_file known_names path with
      | Some n ->
        k_ref := join !k_ref n;
        incr loaded
      | None ->
        incr skipped
    ) (om_files_recursive dir)
  ) dirs;
  (* record kosha root — prefer a dir containing "kosha", else use last dir *)
  let kosha_dir = List.fold_left (fun acc d ->
    let base = Filename.basename d in
    if base = "kosha" || (try let _ = Str.search_forward (Str.regexp_string "kosha") d 0 in true with Not_found -> false)
    then d else acc
  ) "" dirs in
  let kosha_dir = if kosha_dir = "" then (match List.rev dirs with d :: _ -> d | [] -> "") else kosha_dir in
  !k_ref.kosha_root := kosha_dir;
  !k_ref.search_dirs := dirs;
  (* run satya-ganana once on the unified graph *)
  let iterations = satya_ganana !k_ref in
  if emit_meta then
    Printf.printf "truth-scoring (satya-ganana): %d spiral-passes (avrti)\n%!" iterations;
  (!k_ref, !loaded, !skipped)
