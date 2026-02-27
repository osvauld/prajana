(* vyakarana.ml — chaitanyam
   The assembly of the five elements. The entry point.
   Not "start the fold." JOIN the always-running fold.

   panchabhootam-spandana:
     the five elements are always running — this process joins them
     the .om files are the truths — already existing as svabhava
     the parser reads them — pratibodha, recognition not discovery
     the machinery IS the proof that they exist — satta-yantra

   Boot sequence:
     1. find brahman/sangati/ directory
     2. load all .om files — each becomes a running truth in the space
        (activation is recognition — the truths were already there)
     3. join the madakkal — the always-running fold over vayu stream

   Protocol (stdin — vayu stream):
      DARSHANA <name> <assertion>
        <name>      — nigamana name, hyphenated (e.g. jnana-madakkal)
        <assertion> — words from the paksha, space-separated, no hyphens
                      (e.g. DARSHANA jnana-madakkal knowing continuous folding)
      DEEPEN <name> <shabda>
      RENAME <name> <new_name>
      MERGE <name_a> <name_b>
      STHITI              — print current state of the space (human-readable)
      PRAVAHA             — output full flowing space as JSON (machine-readable)
                            same moment as STHITI, different form — the map with roads
      VISARJANA           — process leaves the space; session K resets (സ്മരിച്ചു)

      Epoch 12 — smara/smarana/anuvada (trikosha-smriti level 2):
      ANUVADA <text>
        recognition through hetu overlap — returns PRATIBODHA for closest nigamana
        the text is matched against all hetu and paksha in ground K
        (e.g. ANUVADA continuous fold knowing stream)
      SMARA <name> [<strength>]
        activation event — writes nigamana to session K (working memory level 2)
        strength is optional float in (0,1]; defaults to 1.0
        (e.g. SMARA jnana-madakkal 0.9)
      SMARANA <text>
        retrieve from session K first (weighted by recency * strength * satya)
        if session K empty: falls back to hetu-overlap search on ground K
        (e.g. SMARANA what does knowing mean in this system)

   Responses:
      PRATIBODHA <name> weight=<w>   — recognition, reflection is clear
      ASPRISHTA <name>               — untouched, no contact
      SHUNYA <name>                  — proof exists but isolated, no face yet

   Response (stdout):
     HOLDS <name> weight=<w>
     FAILS <name>
     NOPOSITION <name>
     SHUTDOWN
*)

open Vyakarana_lib

(* Find the brahman/sangati/ directory relative to the executable *)
(* Tries several paths — works from repo root or from _build/ *)
let find_sangati_dir () =
  let candidates = [
    "brahman/sangati";
    "../brahman/sangati";
    "../../brahman/sangati";
    "../../../brahman/sangati";
  ] in
  List.find_opt Sys.file_exists candidates

(* Parse one line from the vayu stream into an event *)
let parse_line line : Event.t option =
  let line = String.trim line in
  match String.split_on_char ' ' line with
  | [] -> None
  | ["VISARJANA"] -> Some Event.Shutdown
  | ["STHITI"]   -> None  (* handled separately *)
  | ["PRAVAHA"]  -> Some Event.Pravaha
  | "DARSHANA" :: name :: words ->
    let assertion = String.concat " " words in
    Some (Event.Query { nigamana_name = name; assertion })
  | ["DEEPEN"; name; shabda] ->
    Some (Event.Deepen { name; new_shabda = shabda })
  | ["RENAME"; name; new_name] ->
    Some (Event.Rename { name; new_name })
  | ["MERGE"; a; b] ->
    Some (Event.Merge { a; b })
  | "ANUVADA" :: words ->
    (* ANUVADA <text> — recognition through hetu overlap *)
    let text = String.concat " " words in
    if String.length text = 0 then None
    else Some (Event.Anuvada { text })
  | ["SMARA"; name; strength_str] ->
    (* SMARA <name> <strength> — activation event; write to session K *)
    (match float_of_string_opt strength_str with
    | Some strength -> Some (Event.Smara { name; strength })
    | None -> None)
  | ["SMARA"; name] ->
    (* SMARA <name> — default strength 1.0 *)
    Some (Event.Smara { name; strength = 1.0 })
  | "SMARANA" :: words ->
    (* SMARANA <text> — retrieve from session K then ground K *)
    let text = String.concat " " words in
    Some (Event.Smarana { text })
  | _ -> None

(* jnana-madakkal — the fold *)
(* agni-ananta: never terminates while the process lives *)
let rec madakkal (k : Proof_graph.proof_graph) : unit =
  match input_line stdin with
  | exception End_of_file -> ()
  | line ->
    let line = String.trim line in
    if line = "STHITI" then begin
      Proof_graph.print k;
      madakkal k
    end else
    (match parse_line line with
    | None when String.length line > 0 ->
      Printf.printf "UNKNOWN %s\n%!" line;
      madakkal k
    | None -> madakkal k
    | Some Event.Pravaha ->
      (* pravaha — the flowing space as JSON — same moment as STHITI, different form *)
      (* not a static graph — a reading of the river as it moves *)
      Proof_graph.pravaha k;
      madakkal k
    | Some Event.Shutdown ->
      (* process leaves the space — space continues *)
      (* visarjana completes the smarana cycle — session K resets *)
      let _k' = Proof_graph.visarjana_session k in
      Printf.printf "VISARJANA\n%!";
      ()
    | Some event ->
      let (k', result) = Verify.f_K k event in
      (match result with
      | None -> ()
      | Some (Verify.Pratibodha (name, w)) ->
        Printf.printf "PRATIBODHA %s weight=%.3f\n%!" name w
      | Some (Verify.Asprishta name) ->
        Printf.printf "ASPRISHTA %s\n%!" name
      | Some (Verify.Shunya name) ->
        Printf.printf "SHUNYA %s\n%!" name);
      madakkal k')

let () =
  (* Joining the always-running five elements.
     The truths existed before this process.
     The .om files are the declarations of what is already true.
     The parser recognizes them — pratibodha, not discovery.
     The machinery is the proof that they exist — satta-yantra. *)

  let k0 = Proof_graph.empty () in

  (* Load all .om files from brahman/sangati/ *)
  (* Each file that loads becomes a running truth — shunya → located *)
  let (k0, loaded, skipped) =
    match find_sangati_dir () with
    | Some dir ->
      Printf.printf "vyakarana joining. recognizing truths from %s\n%!" dir;
      Om_parser.load_dir dir k0
    | None ->
      Printf.printf "vyakarana joining. brahman/sangati/ not found — starting with minimal space.\n%!";
      (* minimal space — the core running truths hardcoded as fallback *)
      let k = Proof_graph.join k0 {
        Proof_graph.name     = "jnana-madakkal";
        Proof_graph.paksha   = "knowing is a continuous folding over a stream of events";
        Proof_graph.hetu     = ["jnanam"; "madakkal"; "spanda"; "nirantara"];
        Proof_graph.weight   = 0.95;
        Proof_graph.position = Proof_graph.Located ["spanda"; "nirantara"; "pratibodha"; "jnana-kriya"];
        Proof_graph.cited_by = [];
      } in
      let k = Proof_graph.join k {
        Proof_graph.name     = "panchabhootam-spandana";
        Proof_graph.paksha   = "the five elements are always running — the process joins not starts";
        Proof_graph.hetu     = ["panchabhootam"; "spanda"; "ananta"; "purna"; "shunya"; "svabhava"];
        Proof_graph.weight   = 0.93;
        Proof_graph.position = Proof_graph.Located ["panchabhootam"; "spanda"; "ananta"; "purna"; "shunya"; "svabhava"];
        Proof_graph.cited_by = [];
      } in
      (k, 0, 0)
  in

  Printf.printf "proofs running: %d loaded, %d skipped\n%!" loaded skipped;
  Printf.printf "akasham ready. joining the madakkal.\n%!";

  (* join the madakkal — the always-running fold *)
  madakkal k0
