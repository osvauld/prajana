(* vyakarana.ml — the entry point
   join the proof space. hold the graph. answer queries.
   same engine, any corpus. directories are arguments.

   usage:
     vyakarana [options] [dir1] [dir2] ...

   options:
     --socket <path>          Unix domain socket server mode
     --show <sections>        comma-separated sections to print (default: reasoning only)
                              sections: strudel, music, resonance, prayoga, all
     --help                   show this message

   default corpus (when no dirs given): brahman/sangati + brahman/kosha

   inline query flags (append to any query):
     +strudel    show strudel mini-notation
     +music      show music_ir JSON
     +resonance  show resonance_ir JSON
     +prayoga    show prayoga code generation
     +all        show all sections

   stdin mode input:
     <node>              single word → inspect that node
     <sentence>          words with spaces → reason through the graph
     <a>, <b>            comma → run both, show what they share
     <sentence>?         question mark → open question mode
     <sentence>!         exclamation → assertion / force mode
     <sentence>.         full stop → closed statement mode
     <sentence>...       ellipsis → incomplete / open mode
     sanskrit <input>    prefix to see plain Sanskrit names

   utility commands:
     SHOW (sthiti)       show full graph, human-readable
     FLOW (pravaha)      show full graph as JSON
     VISARJANA           end session

   socket mode:
     request:  {"method":"query","sentence":"...","show":["resonance","music"]}
     request:  {"method":"reload","dirs":["path/to/dir"]}
     response: {"status":"ok","answer":"...","resonance_ir":{...},...} *)

open Vyakarana_lib

let print_help () =
  Printf.printf "vyakarana — proof graph engine\n\n";
  Printf.printf "usage:\n";
  Printf.printf "  vyakarana [options] [dir1] [dir2] ...\n\n";
  Printf.printf "options:\n";
  Printf.printf "  --socket <path>       Unix domain socket server mode\n";
  Printf.printf "  --show <sections>     sections to print, comma-separated\n";
  Printf.printf "                        default: reasoning only\n";
  Printf.printf "                        values:  strudel, music, resonance, prayoga, all\n";
  Printf.printf "  --help                show this message\n";
  Printf.printf "  --quiet-startup       suppress startup banners\n";
  Printf.printf "  --emit-only           emit raw generation output (implies --quiet-startup)\n\n";
  Printf.printf "inline query flags (append to any query):\n";
  Printf.printf "  +strudel              show strudel mini-notation\n";
  Printf.printf "  +music                show music_ir JSON\n";
  Printf.printf "  +resonance            show resonance_ir JSON\n";
  Printf.printf "  +prayoga              show prayoga code generation\n";
  Printf.printf "  +all                  show all sections\n\n";
  Printf.printf "socket request fields:\n";
  Printf.printf "  question   string     the query (may contain inline +flags)\n";
  Printf.printf "  show       string     comma-separated sections (same values as --show)\n";
  Printf.printf "  max_passes int        override avrti spiral depth (default 2)\n";
  Printf.printf "  thaalam    string     rhythmic mode\n";
  Printf.printf "  sahaja     bool       glossed Sanskrit output\n";
  Printf.printf "  request_id string\n";
  Printf.printf "  session_id string\n";
  Printf.printf "  turn_id    string\n\n";
  Printf.printf "stdin commands:\n";
  Printf.printf "  SHOW / STHITI         show full graph, human-readable\n";
  Printf.printf "  FLOW / PRAVAHA        show full graph as JSON\n";
  Printf.printf "  VISARJANA             end session\n%!"

(* parse argv: extract flags and remaining dir args *)
let parse_argv () : string option * Anuvada.output_flags * bool * bool * string list =
  let args = Array.to_list Sys.argv |> List.tl in
  let rec go socket_path flags quiet_startup emit_only dirs = function
    | [] -> (socket_path, flags, quiet_startup, emit_only, List.rev dirs)
    | "--help" :: _ ->
      print_help (); exit 0
    | "--quiet-startup" :: rest ->
      go socket_path flags true emit_only dirs rest
    | "--emit-only" :: rest ->
      go socket_path flags true true dirs rest
    | "--socket" :: path :: rest -> go (Some path) flags quiet_startup emit_only dirs rest
    | "--socket" :: [] ->
      Printf.eprintf "error: --socket requires a path argument\n%!";
      exit 1
    | "--show" :: csv :: rest ->
      go socket_path (Anuvada.flags_of_show_string csv) quiet_startup emit_only dirs rest
    | "--show" :: [] ->
      Printf.eprintf "error: --show requires a comma-separated list of sections\n%!";
      exit 1
    | arg :: rest ->
      if Sys.file_exists arg then go socket_path flags quiet_startup emit_only (arg :: dirs) rest
      else begin
        Printf.eprintf "warning: %s not found, skipping\n%!" arg;
        go socket_path flags quiet_startup emit_only dirs rest
      end
  in
  go None Anuvada.flags_default false false [] args

(* default corpus search when no dirs given *)
let find_default_corpus () : string list =
  let try_prefix prefix =
    let sangati = prefix ^ "brahman/sangati" in
    let kosha   = prefix ^ "brahman/kosha" in
    let engine  = prefix ^ "brahman/engine" in
    if Sys.file_exists sangati then
      let dirs = [sangati] in
      let dirs = if Sys.file_exists kosha   then dirs @ [kosha]   else dirs in
      let dirs = if Sys.file_exists engine  then dirs @ [engine]  else dirs in
      (* include all session directories *)
      let sessions_root = prefix ^ "sessions" in
      let dirs = if Sys.file_exists sessions_root then
        let entries = try Array.to_list (Sys.readdir sessions_root) with _ -> [] in
        List.fold_left (fun acc entry ->
          let path = sessions_root ^ "/" ^ entry in
          if Sys.file_exists path && Sys.is_directory path then acc @ [path] else acc
        ) dirs entries
      else dirs in
      dirs
    else []
  in
  let prefixes = [""; "../"; "../../"; "../../../"] in
  let rec try_prefixes = function
    | []        -> []
    | p :: rest ->
      match try_prefix p with
      | []  -> try_prefixes rest
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
    | "STHITI" | "SHOW" -> Some Event.Sthiti
    | "PRAVAHA" | "FLOW" -> Some Event.Pravaha
    | "PRAYOGA" when first_space < String.length line ->
      let rest = String.trim (String.sub line (first_space + 1)
        (String.length line - first_space - 1)) in
      let (instruction_raw, input) =
        match String.index_opt rest ':' with
        | Some i ->
          let instr = String.trim (String.sub rest 0 i) in
          let inp   = String.trim (String.sub rest (i + 1) (String.length rest - i - 1)) in
          (instr, inp)
        | None -> (rest, "")
      in
      (* optional domain override syntax:
         PRAYOGA domain=graph-viz build app: graph-viz-intent
         PRAYOGA domain=lua emit app: graph-viz-intent
      *)
      let (domain_hint, instruction) =
        let toks = String.split_on_char ' ' instruction_raw |> List.filter (fun s -> String.trim s <> "") in
        match toks with
        | first_tok :: tail when String.length first_tok > 7 && String.sub first_tok 0 7 = "domain=" ->
          let d = String.sub first_tok 7 (String.length first_tok - 7) in
          let instr = String.concat " " tail in
          (Some d, if String.trim instr = "" then instruction_raw else instr)
        | _ -> (None, instruction_raw)
      in
      Some (Event.Prayoga { instruction; input; domain = domain_hint })
    | "EVAL" when first_space < String.length line ->
      let rest = String.trim (String.sub line (first_space + 1)
        (String.length line - first_space - 1)) in
      Some (Event.Yantra { sentence = "EVAL:" ^ rest })
    | "SANSKRIT" when first_space < String.length line ->
      let rest = String.trim (String.sub line (first_space + 1)
        (String.length line - first_space - 1)) in
      let has_space = String.contains rest ' ' in
      let has_sentence_punct =
        String.contains rest ',' || String.contains rest '?' ||
        String.contains rest '!' ||
        (String.length rest > 0 && rest.[String.length rest - 1] = '.') in
      if has_space || has_sentence_punct then
        Some (Event.Anuvada { sentence = rest; max_passes = None; thaalam = None; sahaja = false })
      else
        Some (Event.Darshana { name = rest; sahaja = false })
    | "DARSHANA" | "INSPECT" when first_space < String.length line ->
      let rest = String.trim (String.sub line (first_space + 1)
        (String.length line - first_space - 1)) in
      Some (Event.Darshana { name = rest; sahaja = true })
    | "REASON" | "ANUVADA" when first_space < String.length line ->
      let rest = String.trim (String.sub line (first_space + 1)
        (String.length line - first_space - 1)) in
      Some (Event.Anuvada { sentence = rest; max_passes = None; thaalam = None; sahaja = true })
    | _ ->
      let has_space = String.contains line ' ' in
      let has_sentence_punct =
        String.contains line ',' ||
        String.contains line '?' ||
        String.contains line '!' ||
        (String.length line > 0 &&
         line.[String.length line - 1] = '.') in
      if has_space || has_sentence_punct then
        Some (Event.Anuvada { sentence = line; max_passes = None; thaalam = None; sahaja = true })
      else if String.length line > 0 then
        Some (Event.Darshana { name = line; sahaja = true })
      else
        None

(* stdin/stdout interactive loop *)
let rec madakkal (k : Proof_graph.proof_graph) (yantra_idx : Yantra.tantra_index)
    (yantra_session : Yantra.session) (session_flags : Anuvada.output_flags) (emit_only : bool) : unit =
  match input_line stdin with
  | exception End_of_file -> ()
  | line ->
    let line = String.trim line in
    (match parse_line line with
    | None when String.length line > 0 ->
      Printf.printf "unknown command: %s\n  try a node name, a sentence, or --help\n%!" line;
      madakkal k yantra_idx yantra_session session_flags emit_only
    | None -> madakkal k yantra_idx yantra_session session_flags emit_only
    | Some Event.Visarjana ->
      Printf.printf "released (visarjana).\n%!";
      ()
    | Some Event.Sthiti ->
      Anuvada.print k;
      madakkal k yantra_idx yantra_session session_flags emit_only
    | Some Event.Pravaha ->
      Anuvada.pravaha k;
      madakkal k yantra_idx yantra_session session_flags emit_only
    | Some (Event.Prayoga p) ->
      Prayoga.run ~emit_meta:(not emit_only) k ~instruction:p.instruction ~input:p.input ~domain_hint:p.domain;
      madakkal k yantra_idx yantra_session session_flags emit_only
    | Some (Event.Yantra y) ->
      (* explicit yantra event *)
      if String.length y.sentence > 5 && String.sub y.sentence 0 5 = "EVAL:" then begin
        (* EVAL mode: evaluate expression directly with the internal evaluator *)
        let expr_str = String.trim (String.sub y.sentence 5 (String.length y.sentence - 5)) in
        (* try as tantra-name arg1 arg2 ...
           handles quoted strings: EVAL parse-test "force when mass" *)
        let parse_eval_args (s : string) : string list =
          let len = String.length s in
          let buf = Buffer.create 16 in
          let args = ref [] in
          let i = ref 0 in
          let flush () =
            if Buffer.length buf > 0 then begin
              args := Buffer.contents buf :: !args;
              Buffer.clear buf
            end
          in
          while !i < len do
            match s.[!i] with
            | ' ' | '\t' -> flush (); incr i
            | '"' ->
              flush (); incr i;
              while !i < len && s.[!i] <> '"' do
                Buffer.add_char buf s.[!i]; incr i
              done;
              if !i < len then incr i;
              args := Buffer.contents buf :: !args;
              Buffer.clear buf
            | c -> Buffer.add_char buf c; incr i
          done;
          flush ();
          List.rev !args
        in
        let parts = parse_eval_args expr_str in
        match parts with
        | tantra_name :: args ->
          (match Hashtbl.find_opt yantra_idx.by_name tantra_name with
           | Some t ->
             let input_values = List.mapi (fun i arg ->
               let inp = if i < List.length t.t_inputs then
                 (List.nth t.t_inputs i).tp_name else Printf.sprintf "arg%d" i in
               let v = match float_of_string_opt arg with
                 | Some f -> Yantra.VFloat f
                 | None -> Yantra.VString arg
               in
               (inp, v)
             ) args in
             (* add tantra index to env *)
             let tnames = List.map (fun t -> Yantra.VString t.Yantra.t_name)
               !(yantra_idx.all_tantras) in
             let input_values = ("_tantra_index", Yantra.VList tnames) :: input_values in
             let result = Yantra.eval_tantra ~idx:yantra_idx ~session:yantra_session k t input_values in
             Printf.printf "%s\n%!" (Yantra.as_string result)
           | None ->
             (* evaluate as a raw expression *)
             let expr = Yantra.parse_expr_string expr_str in
             let env = Yantra.new_env () in
             let tnames = List.map (fun t -> Yantra.VString t.Yantra.t_name)
               !(yantra_idx.all_tantras) in
             Hashtbl.replace env "_tantra_index" (Yantra.VList tnames);
             (* set eval context so pipeline ops (extract-bindings, resolve-tantra, etc.) work *)
             Yantra.eval_ctx := Some { Yantra.ctx_index = yantra_idx; ctx_session = yantra_session };
             let result = Yantra.eval k env expr in
             Yantra.eval_ctx := None;
             Printf.printf "%s\n%!" (Yantra.as_string result))
        | [] -> Printf.printf "eval: empty expression\n%!"
      end else
        (match Yantra.run k yantra_idx yantra_session y.sentence with
         | Some r -> Yantra.print_result r
         | None -> Printf.printf "yantra: could not compute\n%!");
      madakkal k yantra_idx yantra_session session_flags emit_only
    | Some (Event.Anuvada a) ->
      (* try yantra computation first *)
      (match Yantra.run k yantra_idx yantra_session a.sentence with
       | Some r ->
         Yantra.print_result r
       | None ->
         (* try anuvada tantra for reasoning *)
         match Yantra.run_tantra_by_name k yantra_idx yantra_session
                 "anuvada" [("sentence", Yantra.VString a.sentence)] with
         | Some r -> Yantra.print_result r
         | None -> ());
      madakkal k yantra_idx yantra_session session_flags emit_only
    | Some (Event.Darshana d) ->
      (* try darshana tantra for node inspection *)
      (match Yantra.run_tantra_by_name k yantra_idx yantra_session
               "darshana" [("r-name", Yantra.VString d.name)] with
       | Some r -> Yantra.print_result r
       | None -> Printf.printf "not found: %s\n%!" d.name);
      madakkal k yantra_idx yantra_session session_flags emit_only)

let () =
  let (socket_path, session_flags, quiet_startup, emit_only, dirs) = parse_argv () in
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
  (* build yantra tantra index from loaded dirs — pass graph so tantras register as nodes *)
  let yantra_idx = Yantra.build_index ~graph:k0 dirs in
  (* derive vp_satya_weight for each relation type from the visheshanam-entropy-weights tantra.
     the tantra computes Shannon entropy of each relation's target distribution across all edges.
     this runs after build_index so the tantra is loaded and all symmetry edges are present. *)
   (let rel_names = ["swarupa";"abheda";"drishthanta";"sthita";"yukta";
                    "siddha";"kriya";"phala";"janya";"pratipaksha"] in
    match Hashtbl.find_opt yantra_idx.by_name "visheshanam-entropy-weights" with
     | None ->
       (* tantra not loaded — fall back to OCaml computation *)
       Proof_graph.compute_visheshanam_entropy_weights k0
     | Some t ->
       let session = Yantra.new_session () in
       let input = [("relations", Yantra.VList (List.map (fun s -> Yantra.VString s) rel_names))] in
       let result = try Yantra.eval_tantra ~idx:yantra_idx ~session k0 t input
         with _exn ->
           Proof_graph.compute_visheshanam_entropy_weights k0;
           Yantra.VNone in
       (* result: list of [rel-name, weight] pairs, fully rescaled by the tantra.
          just unwrap and register. *)
       let rec unwrap v =
         match v with
         | Yantra.VList [single] -> unwrap single
         | Yantra.VList items    -> items
         | other                 -> [other]
       in
       List.iter (fun item ->
         match unwrap item with
         | [Yantra.VString rel_str; weight_v] ->
           (match Proof_graph.visheshanam_of_string rel_str with
            | None -> ()
            | Some v ->
              let w = Yantra.as_float weight_v in
              let existing = Proof_graph.vish_props_of v in
              Proof_graph.register_vish_props v { existing with Proof_graph.vp_satya_weight = w })
         | _ -> ()
       ) (Yantra.as_list result));
   (* set the graph ref for legacy invert_expr calls *)
  Yantra._graph_ref := Some k0;
  let tantra_count = List.length !(yantra_idx.all_tantras) in
  let constant_count = Hashtbl.length yantra_idx.constants in
  if not quiet_startup then begin
    Printf.printf "knowledge-nodes (suktas): %d loaded, %d skipped\n%!" loaded skipped;
    if tantra_count > 0 then
      Printf.printf "tantras (yantra): %d loaded, %d constants\n%!" tantra_count constant_count;
    Printf.printf "space (akasham) ready.\n%!"
  end;
  let yantra_session = Yantra.new_session () in
  match socket_path with
  | Some path -> Socket.serve k0 path
  | None      -> madakkal k0 yantra_idx yantra_session session_flags emit_only
