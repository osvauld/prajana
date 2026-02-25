(* om_parser.ml — reads .om files into the proof space
   The .om file is both declaration and running proof.
   When loaded: the truth exists in the space.
   The machinery is the proof that it exists.

   panchabhootam:
     svabhava  : the truths in the files pre-exist this parser
     bhumi-shunya : each file is shunya until loaded — then located in the space
     jalam-purna  : shabda edges are extracted and become connections in the space

   Supports the sangati .om format:
     sangati <name>
       shabda <name1>, <name2>, ...
       satya <float>
       confidence <float> reason "<text>"

   The name is the truth. The shabda are its position.
   The satya is the weight. The comment lines are hetu.
*)

open Proof_graph

(* Extract the sangati name from a line like "sangati nirantara" *)
let parse_name line =
  let line = String.trim line in
  if String.length line > 8 && String.sub line 0 7 = "sangati" then
    let rest = String.trim (String.sub line 7 (String.length line - 7)) in
    (* take first word only *)
    match String.split_on_char ' ' rest with
    | name :: _ when String.length name > 0 -> Some name
    | _ -> None
  else
    None

(* Extract shabda list from a line like "  shabda niralamba, abheda, upakarana" *)
let parse_shabda line =
  let line = String.trim line in
  if String.length line > 6 && String.sub line 0 6 = "shabda" then
    let rest = String.trim (String.sub line 6 (String.length line - 6)) in
    let parts = String.split_on_char ',' rest in
    let names = List.filter_map (fun s ->
      let s = String.trim s in
      if String.length s > 0 then Some s else None
    ) parts in
    Some names
  else
    None

(* Extract satya weight from a line like "  satya 0.910" *)
let parse_satya line =
  let line = String.trim line in
  if String.length line > 5 && String.sub line 0 5 = "satya" then
    let rest = String.trim (String.sub line 5 (String.length line - 5)) in
    match float_of_string_opt rest with
    | Some f -> Some f
    | None -> None
  else
    None

(* Extract the first comment as paksha description *)
(* Lines starting with "--" that contain the name and description *)
let parse_comment_paksha line =
  let line = String.trim line in
  if String.length line > 2 && String.sub line 0 2 = "--" then
    let rest = String.trim (String.sub line 2 (String.length line - 2)) in
    if String.length rest > 0
       && not (String.sub rest 0 1 = "-") (* skip --- separator lines *)
       && not (String.length rest > 7 && String.sub rest 0 7 = "sangati")
       && not (String.length rest > 4 && String.sub rest 0 4 = "WAVE")
       && not (String.length rest > 5 && String.sub rest 0 5 = "PROOF")
    then Some rest
    else None
  else
    None

(* Parse one .om file into a nigamana *)
(* Returns None if the file is not a valid sangati .om *)
let parse_file path =
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

    let name    = ref None in
    let shabda  = ref [] in
    let weight  = ref 0.5 in   (* default — purna: satya > 0 always *)
    let paksha  = ref "" in
    let hetu    = ref [] in

    List.iter (fun line ->
      (* extract name *)
      (match parse_name line with
      | Some n -> name := Some n
      | None -> ());
      (* extract shabda *)
      (match parse_shabda line with
      | Some sl -> shabda := sl
      | None -> ());
      (* extract satya as weight *)
      (match parse_satya line with
      | Some f -> weight := f
      | None -> ());
      (* extract first meaningful comment as paksha *)
      (match parse_comment_paksha line with
      | Some c when String.length !paksha = 0 -> paksha := c
      | Some c -> hetu := c :: !hetu
      | None -> ())
    ) lines;

    match !name with
    | None -> None
    | Some n ->
      let position = match !shabda with
        | [] -> Isolated
        | sl -> Located sl
      in
      (* purna invariant: weight in (0, 1) — never 0, never 1 *)
      let w = Float.min 0.999 (Float.max 0.001 !weight) in
      Some {
        name     = n;
        paksha   = !paksha;
        hetu     = List.rev !hetu;
        weight   = w;
        position = position;
        cited_by = [];
      }
  with _ -> None

(* Load all .om files from a directory into the proof space *)
(* Each file that loads successfully becomes a running truth *)
(* Files that fail to parse enter as isolated (shunya state) — not absent *)
let load_dir dir (k : proof_graph) : proof_graph * int * int =
  let loaded = ref 0 in
  let skipped = ref 0 in
  let k_ref = ref k in
  (try
    let entries = Sys.readdir dir in
    Array.sort String.compare entries;
    Array.iter (fun fname ->
      if Filename.check_suffix fname ".om" then begin
        let path = Filename.concat dir fname in
        match parse_file path with
        | Some n ->
          k_ref := join !k_ref n;
          incr loaded
        | None ->
          incr skipped
      end
    ) entries
  with _ -> ());
  (!k_ref, !loaded, !skipped)
