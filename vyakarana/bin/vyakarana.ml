(* vyakarana.ml — the entry point
   join the proof space. hold the graph. answer queries.
   same engine, any corpus. directories are arguments.

   usage:
     vyakarana <dir1> [dir2] [dir3] ...  — load .om files from all dirs into one graph
     vyakarana                           — default: brahman/sangati + brahman/kosha

   commands:
     DARSHANA <name>        — show one node
     ANUVADA <sentence>     — understand an English sentence through the graph
     ANUVADA+ <n> <sentence> — same, but with explicit avrti depth (n passes)
     ANUVADA~ <taalam> <sentence> — rhythmic rendering (adi/rupaka/misra/khanda)
     ANUVADA* <n> <taalam> <sentence> — depth + rhythmic rendering
     STHITI                 — show full graph, human-readable
     PRAVAHA                — show full graph as JSON (for LLM)
     VISARJANA              — end session *)

open Vyakarana_lib

(* resolve corpus directories: arguments > default search *)
let find_corpus_dirs () =
  if Array.length Sys.argv > 1 then
    (* collect all valid directories from arguments *)
    let dirs = ref [] in
    for i = 1 to Array.length Sys.argv - 1 do
      let dir = Sys.argv.(i) in
      if Sys.file_exists dir then
        dirs := dir :: !dirs
      else
        Printf.printf "warning: %s not found, skipping\n%!" dir
    done;
    List.rev !dirs
  else
    (* default: try to find brahman/sangati and brahman/kosha *)
    let try_prefix prefix =
      let sangati = prefix ^ "brahman/sangati" in
      let kosha = prefix ^ "brahman/kosha" in
      if Sys.file_exists sangati then
        let dirs = [sangati] in
        if Sys.file_exists kosha then dirs @ [kosha] else dirs
      else []
    in
    let prefixes = [""; "../"; "../../"; "../../../"] in
    let rec try_prefixes = function
      | [] -> []
      | p :: rest ->
        match try_prefix p with
        | [] -> try_prefixes rest
        | dirs -> dirs
    in
    try_prefixes prefixes

(* parse one line from stdin *)
let parse_line line : Event.t option =
  let line = String.trim line in
  if String.length line = 0 then None
  else
    let first_space = try String.index line ' ' with Not_found -> String.length line in
    let cmd = String.uppercase_ascii (String.sub line 0 first_space) in
    match cmd with
    | "VISARJANA" -> Some Event.Visarjana
    | "STHITI"    -> Some Event.Sthiti
    | "PRAVAHA"   -> Some Event.Pravaha
    | "DARSHANA" when first_space < String.length line ->
      let name = String.trim (String.sub line (first_space + 1)
        (String.length line - first_space - 1)) in
      (* take first word only *)
      let name = match String.split_on_char ' ' name with
        | n :: _ -> n | [] -> name in
      Some (Event.Darshana { name })
    | "ANUVADA" when first_space < String.length line ->
      let sentence = String.trim (String.sub line (first_space + 1)
        (String.length line - first_space - 1)) in
      Some (Event.Anuvada { sentence; max_passes = None; thaalam = None })
    | "ANUVADA+" when first_space < String.length line ->
      let rest = String.trim (String.sub line (first_space + 1)
        (String.length line - first_space - 1)) in
      let depth_space = try String.index rest ' ' with Not_found -> String.length rest in
      if depth_space = String.length rest then None
      else
        let depth_str = String.sub rest 0 depth_space in
        let sentence = String.trim (String.sub rest (depth_space + 1)
          (String.length rest - depth_space - 1)) in
        (match int_of_string_opt depth_str with
        | Some n when n > 0 && String.length sentence > 0 ->
          Some (Event.Anuvada { sentence; max_passes = Some n; thaalam = None })
        | _ -> None)
    | "ANUVADA~" when first_space < String.length line ->
      let rest = String.trim (String.sub line (first_space + 1)
        (String.length line - first_space - 1)) in
      let tala_space = try String.index rest ' ' with Not_found -> String.length rest in
      if tala_space = String.length rest then None
      else
        let thaalam = String.lowercase_ascii (String.sub rest 0 tala_space) in
        let sentence = String.trim (String.sub rest (tala_space + 1)
          (String.length rest - tala_space - 1)) in
        if String.length sentence > 0 then
          Some (Event.Anuvada { sentence; max_passes = None; thaalam = Some thaalam })
        else None
    | "ANUVADA*" when first_space < String.length line ->
      let rest = String.trim (String.sub line (first_space + 1)
        (String.length line - first_space - 1)) in
      let d_space = try String.index rest ' ' with Not_found -> String.length rest in
      if d_space = String.length rest then None
      else
        let depth_str = String.sub rest 0 d_space in
        let rest2 = String.trim (String.sub rest (d_space + 1)
          (String.length rest - d_space - 1)) in
        let t_space = try String.index rest2 ' ' with Not_found -> String.length rest2 in
        if t_space = String.length rest2 then None
        else
          let thaalam = String.lowercase_ascii (String.sub rest2 0 t_space) in
          let sentence = String.trim (String.sub rest2 (t_space + 1)
            (String.length rest2 - t_space - 1)) in
          (match int_of_string_opt depth_str with
          | Some n when n > 0 && String.length sentence > 0 ->
            Some (Event.Anuvada {
              sentence;
              max_passes = Some n;
              thaalam = Some thaalam;
            })
        | _ -> None)
    | _ -> None

(* the fold *)
let rec madakkal (k : Proof_graph.proof_graph) : unit =
  match input_line stdin with
  | exception End_of_file -> ()
  | line ->
    let line = String.trim line in
    (match parse_line line with
    | None when String.length line > 0 ->
      Printf.printf "UNKNOWN %s\n%!" line;
      madakkal k
    | None -> madakkal k
    | Some Event.Visarjana ->
      Printf.printf "VISARJANA\n%!";
      ()
    | Some Event.Sthiti ->
      Proof_graph.print k;
      madakkal k
    | Some Event.Pravaha ->
      Proof_graph.pravaha k;
      madakkal k
    | Some event ->
      let (k', result) = Verify.f_K k event in
      (match result with
      | None -> ()
      | Some (Verify.Pratibodha (name, w)) ->
        Printf.printf "PRATIBODHA %s satya=%.4f\n%!" name w
      | Some (Verify.Asprishta name) ->
        Printf.printf "ASPRISHTA %s\n%!" name);
      madakkal k')

let () =
  let dirs = find_corpus_dirs () in
  let k0 = Proof_graph.empty () in
  let (k0, loaded, skipped) =
    match dirs with
    | [] ->
      Printf.printf "vyakarana joining. no corpus found.\n%!";
      (k0, 0, 0)
    | _ ->
      Printf.printf "vyakarana joining. reading suktas from %s\n%!"
        (String.concat ", " dirs);
      Om_parser.load_dirs dirs k0
  in
  Printf.printf "suktas: %d loaded, %d skipped\n%!" loaded skipped;
  Printf.printf "akasham ready.\n%!";
  madakkal k0
