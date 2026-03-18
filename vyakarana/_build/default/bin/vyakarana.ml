(* vyakarana.ml — grammar engine entry point.
   join the proof space. hold the graph. answer queries.
   same engine, any corpus. directories are arguments.

   usage:
     vyakarana [options] [dir1] [dir2] ...

   options:
     --socket <path>          Unix domain socket server mode
     --help                   show this message

   stdin mode input:
     <node>        single word → inspect that node
     <sentence>    words with spaces → reason through the graph
     EVAL <expr>   evaluate a tantra expression directly

   utility commands:
     SHOW (sthiti)   show full graph, human-readable
     FLOW (pravaha)  show full graph as JSON
     VISARJANA       end session

   socket mode:
     request:  {"question": "...", "session_id": "...", "request_id": "..."}
     response: {"status": "ok", "session_id": "...", "request_id": "...",
                "answer_text": "..."} *)

open Vyakarana_lib

let print_help () =
  Printf.printf "vyakarana — proof graph engine\n\n";
  Printf.printf "usage:\n";
  Printf.printf "  vyakarana [options] [dir1] [dir2] ...\n\n";
  Printf.printf "options:\n";
  Printf.printf "  --socket <path>       Unix domain socket server mode\n";
  Printf.printf "  --help                show this message\n";
  Printf.printf "  --quiet-startup       suppress startup banners\n\n";
  Printf.printf "socket request fields:\n";
  Printf.printf "  question   string     the query\n";
  Printf.printf "  session_id string     session identifier (optional)\n";
  Printf.printf "  request_id string     request identifier (optional)\n";
  Printf.printf "  turn_id    string     turn identifier (optional)\n";
  Printf.printf "  max_passes int        override avrti spiral depth (default 2)\n\n";
  Printf.printf "stdin commands:\n";
  Printf.printf "  EVAL <expr>           evaluate a tantra expression\n";
  Printf.printf "  SHOW / STHITI         show full graph, human-readable\n";
  Printf.printf "  FLOW / PRAVAHA        show full graph as JSON\n";
  Printf.printf "  VISARJANA             end session\n%!"

(* parse argv: extract flags and remaining dir args *)
let parse_argv () : string option * bool * bool * string list =
  let args = Array.to_list Sys.argv |> List.tl in
  let rec go socket_path quiet_startup emit_only dirs = function
    | [] -> (socket_path, quiet_startup, emit_only, List.rev dirs)
    | "--help" :: _ ->
      print_help (); exit 0
    | "--quiet-startup" :: rest ->
      go socket_path true emit_only dirs rest
    | "--emit-only" :: rest ->
      go socket_path true true dirs rest
    | "--socket" :: path :: rest -> go (Some path) quiet_startup emit_only dirs rest
    | "--socket" :: [] ->
      Printf.eprintf "error: --socket requires a path argument\n%!";
      exit 1
    | arg :: rest ->
      if Sys.file_exists arg then go socket_path quiet_startup emit_only (arg :: dirs) rest
      else begin
        Printf.eprintf "warning: %s not found, skipping\n%!" arg;
        go socket_path quiet_startup emit_only dirs rest
      end
  in
  go (Some "/tmp/vy.sock") false false [] args

(* default corpus: brahman/sangati + brahman/kosha + brahman/bhasha + brahman/engine *)
let find_default_corpus () : string list =
  let try_prefix prefix =
    let sangati = prefix ^ "brahman/sangati" in
    let kosha   = prefix ^ "brahman/kosha" in
    let bhasha  = prefix ^ "brahman/bhasha" in
    let engine  = prefix ^ "brahman/engine" in
    if Sys.file_exists sangati then
      let dirs = [sangati] in
      let dirs = if Sys.file_exists kosha  then dirs @ [kosha]  else dirs in
      let dirs = if Sys.file_exists bhasha then dirs @ [bhasha] else dirs in
      let dirs = if Sys.file_exists engine then dirs @ [engine] else dirs in
      dirs
    else []
  in
  let prefixes = [""; "../"; "../../"; "../../../"] in
  let rec try_prefixes = function
    | []        -> []
    | p :: rest ->
      match try_prefix p with
      | []   -> try_prefixes rest
      | dirs -> dirs
  in
  try_prefixes prefixes

(* parse one line from stdin into an event *)
let parse_line (line : string) : Event.t option =
  let line = String.trim line in
  if String.length line = 0 then None
  else
    let first_space = try String.index line ' ' with Not_found -> String.length line in
    let cmd = String.uppercase_ascii (String.sub line 0 first_space) in
    let rest () = String.trim (String.sub line (first_space + 1)
      (String.length line - first_space - 1)) in
    let has_rest = first_space < String.length line in
    match cmd with
    | "VISARJANA" -> Some Event.Visarjana
    | "STHITI" | "SHOW" -> Some Event.Sthiti
    | "PRAVAHA" | "FLOW" -> Some Event.Pravaha
    | "EVAL" when has_rest ->
      Some (Event.Yantra { sentence = "EVAL:" ^ rest () })
    | "DARSHANA" | "INSPECT" | "SANSKRIT" when has_rest ->
      Some (Event.Darshana { name = rest () })
    | "REASON" | "ANUVADA" when has_rest ->
      Some (Event.Anuvada { sentence = rest (); max_passes = None })
    | _ ->
      let has_space = String.contains line ' ' in
      let has_punct =
        String.contains line ',' || String.contains line '?' ||
        String.contains line '!' ||
        (String.length line > 0 && line.[String.length line - 1] = '.') in
      if has_space || has_punct then
        Some (Event.Anuvada { sentence = line; max_passes = None })
      else if String.length line > 0 then
        Some (Event.Darshana { name = line })
      else
        None

(* stdin/stdout interactive loop *)
let rec madakkal (k : Proof_graph.proof_graph) (yantra_idx : Yantra.tantra_index)
    (yantra_session : Yantra.session) (emit_only : bool) : unit =
  match input_line stdin with
  | exception End_of_file -> ()
  | line ->
    let line = String.trim line in
    (match parse_line line with
    | None when String.length line > 0 ->
      Printf.printf "unknown command: %s\n  try a node name, a sentence, or --help\n%!" line;
      madakkal k yantra_idx yantra_session emit_only
    | None ->
      madakkal k yantra_idx yantra_session emit_only
    | Some Event.Visarjana ->
      Printf.printf "released (visarjana).\n%!"
    | Some Event.Sthiti ->
      Anuvada.print k;
      madakkal k yantra_idx yantra_session emit_only
    | Some Event.Pravaha ->
      Anuvada.pravaha k;
      madakkal k yantra_idx yantra_session emit_only
    | Some (Event.Yantra y) ->
      if String.length y.sentence > 5 && String.sub y.sentence 0 5 = "EVAL:" then begin
        let expr_str = String.trim (String.sub y.sentence 5 (String.length y.sentence - 5)) in
        let expr = Yantra.parse_expr_string expr_str in
        let env  = Yantra.new_env () in
        let tnames = List.map (fun t -> Yantra.VString t.Yantra.t_name)
          !(yantra_idx.all_tantras) in
        Hashtbl.replace env "_tantra_index" (Yantra.VList tnames);
        Yantra.eval_ctx := Some { Yantra.ctx_index = yantra_idx; ctx_session = yantra_session };
        let result = Yantra.eval k env expr in
        Yantra.eval_ctx := None;
        Printf.printf "%s\n%!" (Yantra.as_string result)
      end else
        (match Yantra.run_anuvada_ganana k yantra_idx yantra_session y.sentence with
         | Some r -> Yantra.print_result r
         | None   -> Printf.printf "yantra: anuvada-ganana not loaded\n%!");
      madakkal k yantra_idx yantra_session emit_only
    | Some (Event.Anuvada a) ->
      (match Yantra.run_anuvada_ganana k yantra_idx yantra_session a.sentence with
       | Some r -> Yantra.print_result r
       | None ->
         match Yantra.run_tantra_by_name k yantra_idx yantra_session
                 "anuvada" [("sentence", Yantra.VString a.sentence)] with
         | Some r -> Yantra.print_result r
         | None   -> ());
      madakkal k yantra_idx yantra_session emit_only
    | Some (Event.Darshana d) ->
      (match Yantra.run_tantra_by_name k yantra_idx yantra_session
               "darshana" [("r-name", Yantra.VString d.name)] with
       | Some r -> Yantra.print_result r
       | None   -> Printf.printf "not found: %s\n%!" d.name);
      madakkal k yantra_idx yantra_session emit_only)

let () =
  let (socket_path, quiet_startup, emit_only, dirs) = parse_argv () in
  let dirs = if dirs = [] then find_default_corpus () else dirs in
  let k0 = Proof_graph.empty () in
  let (k0, loaded, skipped) =
    match dirs with
    | [] ->
      if not quiet_startup then
        Printf.printf "grammar-engine (vyakarana) joining. no corpus found.\n%!";
      (k0, 0, 0)
    | _ ->
      if not quiet_startup then
        Printf.printf "grammar-engine (vyakarana) joining. reading knowledge-nodes (suktas) from %s\n%!"
          (String.concat ", " dirs);
      Om_parser.load_dirs ~emit_meta:(not quiet_startup) dirs k0
  in
  let yantra_idx = Yantra.build_index ~graph:k0 dirs in
  Proof_graph.materialize_csr k0;
  Proof_graph.compute_visheshanam_entropy_weights k0;
  (* run boot tantra: graph enrichment passes (varga inheritance etc.) *)
  let yantra_session = Yantra.new_session () in
  (match Hashtbl.find_opt yantra_idx.Yantra.by_name "reboot" with
   | Some t ->
     ignore (Yantra_eval.eval_tantra ~idx:yantra_idx ~session:yantra_session
                k0 t [("_", Yantra_types.VString "boot")])
   | None -> ());
  (* re-materialize after boot tantra may have added edges *)
  Proof_graph.materialize_csr k0;
  if not quiet_startup then begin
    let n_nodes = Hashtbl.length k0.Proof_graph.nodes in
    let n_edges = List.length !(k0.Proof_graph.all_edges) in
    Printf.printf "loaded %d suktas (%d skipped). %d nodes, %d edges.\n%!"
      loaded skipped n_nodes n_edges;
    let ndims = Proof_graph.dimension_count () in
    if ndims > 10 then
      Printf.printf "dimensions (visheshanam): %d (10 core + %d dynamic)\n%!" ndims (ndims - 10);
    Printf.printf "space (akasham) ready.\n%!"
  end;
  match socket_path with
  | Some path -> Socket.serve k0 yantra_idx yantra_session dirs path
  | None      -> madakkal k0 yantra_idx yantra_session emit_only
