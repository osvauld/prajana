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

(* --- pass 1.5: compile dynamic dimensions ---
   reads the visheshanam-ring node to discover which concepts are dimensions.
   the ring reaches down to structural truths (sangati nodes) — those nodes
   stay pure, the ring declares membership.
   must run after collect_names and before sloka decomposition. *)

let collect_dynamic_dims_from_ring (files : string list) (known_names : string list)
    : string list =
  (* find and parse the visheshanam-ring node *)
  let ring_slokas = ref [] in
  List.iter (fun path ->
    try
      let ic = open_in path in
      let is_ring = ref false in
      (try
        while true do
          let line = input_line ic in
          (match parse_node_header line with
           | Some (_layer, name) when name = "visheshanam-ring" -> is_ring := true
           | Some _ -> is_ring := false
           | None ->
             if !is_ring then
               match parse_sloka line with
               | Some s -> ring_slokas := s :: !ring_slokas
               | None -> ())
        done
      with End_of_file -> ());
      close_in ic
    with _ -> ()
  ) files;
  (* extract dimension members: any "X-yukta" compound in the ring's slokas
     where X is a known node name and X is NOT already a core dimension (0-9).
     the ring claims members via yukta edges.
     skip visheshanam-* prefixed targets — those are graph edges to the
     existing ring member NODES, not new dimension declarations. *)
  let dims = ref [] in
  let is_visheshanam_prefixed s =
    String.length s > 12 && String.sub s 0 12 = "visheshanam-" in
  List.iter (fun sloka ->
    let words = String.split_on_char ' ' sloka in
    List.iter (fun word ->
      let word = String.trim word in
      if String.length word > 0 then
        (* decompose: try splitting at last '-' to find a yukta suffix *)
        let rec try_split i =
          if i <= 0 then ()
          else if word.[i] = '-' then begin
            let suffix = String.sub word (i + 1) (String.length word - i - 1) in
            if suffix = "yukta" then begin
              let target = String.sub word 0 i in
              (* register if: known node, not already a core dim, not a visheshanam-* node ref *)
              if List.mem target known_names
                 && Proof_graph.visheshanam_of_string target = None
                 && not (is_visheshanam_prefixed target) then
                dims := target :: !dims
            end else
              try_split (i - 1)
          end else
            try_split (i - 1)
        in
        try_split (String.length word - 1)
    ) words
  ) !ring_slokas;
  List.sort_uniq String.compare !dims

(* register discovered dimensions into the proof_graph registry *)
let register_dynamic_dims (dim_names : string list) : unit =
  List.iter (fun name ->
    ignore (Proof_graph.register_dimension name)
  ) dim_names

(* --- pass 2: sloka decomposition --- *)

(* try to match a compound word against known names + visheshanam suffix
   e.g. "dharana-jivamsha-swarupa" -> Some ("dharana-jivamsha", Swarupa)
   tries longest name match first.
   fallback: if no known name matches, try splitting at last '-' before
   a known visheshanam suffix — allows cross-layer references to names
   not in this graph *)
(* pre-sorted names cache — sort once, reuse across all decompositions *)
let _sorted_names_cache : (string list * string list) ref = ref ([], [])

let get_sorted_names (known_names : string list) : string list =
  let (cached_input, cached_sorted) = !_sorted_names_cache in
  if cached_input == known_names then cached_sorted  (* physical equality = same list *)
  else begin
    let sorted = List.sort (fun a b ->
      compare (String.length b) (String.length a)
    ) known_names in
    _sorted_names_cache := (known_names, sorted);
    sorted
  end

let decompose_compound (_known_names : string list) (word : string) : (string * visheshanam) option =
  let word_lower = String.lowercase_ascii word in
  (* fast path: split at each '-' from the right and check suffix as visheshanam *)
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

(* load all .om files from a directory — three-pass *)
let load_dir ?(emit_meta = true) dir (k : proof_graph) : proof_graph * int * int =
  (* pass 1: collect all names *)
  let known_names = collect_names dir in
  (* pass 1.5: discover dynamic dimensions from the visheshanam-ring node *)
  let all_files = om_files_recursive dir in
  let dyn_dims = collect_dynamic_dims_from_ring all_files known_names in
  register_dynamic_dims dyn_dims;
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
  (* set raw_satya as structural prior on every node *)
  Proof_graph.init_satya !k_ref;
  ignore emit_meta;
  (!k_ref, !loaded, !skipped)

(* load multiple directories into one graph — unified namespace
   pass 1:   collect names from ALL directories
   pass 1.5: discover dynamic dimensions (visheshanam-swarupa) and register them
   pass 2:   parse all files with the combined vocabulary + dynamic dims
   satya-ganana runs once on the unified graph *)
let load_dirs ?(emit_meta = true) (dirs : string list) (k : proof_graph) : proof_graph * int * int =
  (* pass 1: collect names from all directories *)
  let known_names = List.concat_map collect_names dirs in
  (* pass 1.5: discover dynamic dimensions from the visheshanam-ring node *)
  let all_files = List.concat_map om_files_recursive dirs in
  let dyn_dims = collect_dynamic_dims_from_ring all_files known_names in
  register_dynamic_dims dyn_dims;
  (* pass 2: parse all files from all directories *)
  let loaded = ref 0 in
  let skipped = ref 0 in
  let k_ref = ref k in
  let all_files = List.concat_map om_files_recursive dirs in
  List.iter (fun path ->
    match parse_file known_names path with
    | Some n ->
      k_ref := join !k_ref n;
      incr loaded
    | None ->
      incr skipped
  ) all_files;
  (* record kosha root — prefer a dir containing "kosha", else use last dir *)
  let kosha_dir = List.fold_left (fun acc d ->
    let base = Filename.basename d in
    if base = "kosha" || (try let _ = Str.search_forward (Str.regexp_string "kosha") d 0 in true with Not_found -> false)
    then d else acc
  ) "" dirs in
  let kosha_dir = if kosha_dir = "" then (match List.rev dirs with d :: _ -> d | [] -> "") else kosha_dir in
  !k_ref.kosha_root := kosha_dir;
  !k_ref.search_dirs := dirs;
  (* set raw_satya as structural prior on every node *)
  Proof_graph.init_satya !k_ref;
  ignore emit_meta;
  (!k_ref, !loaded, !skipped)
