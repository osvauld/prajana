(* vyakarana.ml — grammar engine entry point.
   join the proof space. hold the graph. answer queries.
   same engine, any corpus. directories are arguments. *)

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

let parse_argv () : string option * bool * bool * string list =
  let args = Array.to_list Sys.argv |> List.tl in
  let rec go socket_path quiet_startup emit_only dirs = function
    | [] -> (socket_path, quiet_startup, emit_only, List.rev dirs)
    | "--help" :: _ -> print_help (); exit 0
    | "--quiet-startup" :: rest ->
      go socket_path true emit_only dirs rest
    | "--emit-only" :: rest ->
      go socket_path true true dirs rest
    | "--socket" :: path :: rest -> go (Some path) quiet_startup emit_only dirs rest
    | "--socket" :: [] ->
      Printf.eprintf "error: --socket requires a path argument\n%!"; exit 1
    | arg :: rest ->
      if Sys.file_exists arg then go socket_path quiet_startup emit_only (arg :: dirs) rest
      else begin
        Printf.eprintf "warning: %s not found, skipping\n%!" arg;
        go socket_path quiet_startup emit_only dirs rest
      end
  in
  go (Some "/tmp/vy.sock") false false [] args

let find_default_corpus () : string list =
  let try_prefix prefix =
    let sangati = prefix ^ "brahman/sangati" in
    let kosha   = prefix ^ "brahman/kosha" in
    let bhasha  = prefix ^ "brahman/bhasha" in
    let engine  = prefix ^ "brahman/engine.om5" in
    let personal = prefix ^ "brahman/personal.om5" in
    if Sys.file_exists sangati then
      let dirs = [sangati] in
      let dirs = if Sys.file_exists kosha    then dirs @ [kosha]    else dirs in
      let dirs = if Sys.file_exists bhasha   then dirs @ [bhasha]   else dirs in
      let dirs = if Sys.file_exists engine   then dirs @ [engine]   else dirs in
      let dirs = if Sys.file_exists personal then dirs @ [personal] else dirs in
      dirs
    else []
  in
  let prefixes = [""; "../"; "../../"; "../../../"] in
  let rec try_prefixes = function
    | [] -> [] | p :: rest ->
      match try_prefix p with [] -> try_prefixes rest | dirs -> dirs
  in
  try_prefixes prefixes

let parse_line (line : string) : Prakriti.event option =
  let line = String.trim line in
  if String.length line = 0 then None
  else
    let first_space = try String.index line ' ' with Not_found -> String.length line in
    let cmd = String.uppercase_ascii (String.sub line 0 first_space) in
    let rest () = String.trim (String.sub line (first_space + 1)
      (String.length line - first_space - 1)) in
    let has_rest = first_space < String.length line in
    match cmd with
    | "VISARJANA" -> Some Prakriti.Visarjana
    | "STHITI" | "SHOW" -> Some Prakriti.Sthiti
    | "PRAVAHA" | "FLOW" -> Some Prakriti.Pravaha
    | "EVAL" when has_rest ->
      Some (Prakriti.Yantra { sentence = "EVAL:" ^ rest () })
    | "DARSHANA" | "INSPECT" | "SANSKRIT" when has_rest ->
      Some (Prakriti.Darshana { name = rest () })
    | "REASON" | "ANUVADA" when has_rest ->
      Some (Prakriti.Anuvada { sentence = rest (); max_passes = None })
    | _ ->
      let has_space = String.contains line ' ' in
      let has_punct =
        String.contains line ',' || String.contains line '?' ||
        String.contains line '!' ||
        (String.length line > 0 && line.[String.length line - 1] = '.') in
      if has_space || has_punct then
        Some (Prakriti.Anuvada { sentence = line; max_passes = None })
      else if String.length line > 0 then
        Some (Prakriti.Darshana { name = line })
      else None

let rec madakkal (k : Prakriti.proof_graph) (idx : Kriya.tantra_index)
    (session : Kriya.session) (emit_only : bool) : unit =
  ignore emit_only;
  match input_line stdin with
  | exception End_of_file -> ()
  | line ->
    let line = String.trim line in
    (match parse_line line with
    | None when String.length line > 0 ->
      Printf.printf "unknown command: %s\n  try a node name, a sentence, or --help\n%!" line;
      madakkal k idx session emit_only
    | None ->
      madakkal k idx session emit_only
    | Some Prakriti.Visarjana ->
      Printf.printf "released (visarjana).\n%!"
    | Some Prakriti.Sthiti ->
      Vak.print k;
      madakkal k idx session emit_only
    | Some Prakriti.Pravaha ->
      Vak.pravaha k;
      madakkal k idx session emit_only
    | Some (Prakriti.Yantra y) ->
      if String.length y.sentence > 5 && String.sub y.sentence 0 5 = "EVAL:" then begin
        let expr_str = String.trim (String.sub y.sentence 5 (String.length y.sentence - 5)) in
        let expr = Kriya.parse_expr_string expr_str in
        let tnames = List.map (fun t -> Kriya.VString t.Kriya.t_name)
          !(idx.all_tantras) in
        let env = Kriya.StringMap.add "_tantra_index" (Kriya.VList tnames) Kriya.StringMap.empty in
        Domain.DLS.set Kriya._eval_ctx (Some { Kriya.ctx_index = idx; ctx_session = session });
        let result = Fun.protect
          ~finally:(fun () -> Domain.DLS.set Kriya._eval_ctx None)
          (fun () -> Kriya.eval k env expr) in
        Printf.printf "%s\n%!" (Kriya.as_string result)
      end else
        (match Kriya.run_anuvada_ganana k idx session y.sentence with
         | Some r -> Kriya.print_result r
         | None   -> Printf.printf "kriya: anuvada-ganana not loaded\n%!");
      madakkal k idx session emit_only
    | Some (Prakriti.Anuvada a) ->
      (match Kriya.run_anuvada_ganana k idx session a.sentence with
       | Some r -> Kriya.print_result r
       | None ->
         match Kriya.run_tantra_by_name k idx session
                 "anuvada" [("sentence", Kriya.VString a.sentence)] with
         | Some r -> Kriya.print_result r
         | None   -> ());
      madakkal k idx session emit_only
    | Some (Prakriti.Darshana d) ->
      (match Kriya.run_tantra_by_name k idx session
               "darshana" [("r-name", Kriya.VString d.name)] with
       | Some r -> Kriya.print_result r
       | None   -> Printf.printf "not found: %s\n%!" d.name);
      madakkal k idx session emit_only)

(* ---- om5 loading: three-pass loader ---- *)
let load_dirs ?(emit_meta=true) (dirs : string list) (k : Prakriti.proof_graph)
    : Prakriti.proof_graph * int * int =
  (* pass 1: discover dynamic dimensions from visheshanam-ring *)
  let all_names = List.concat_map Karma.collect_names dirs in
  let dynamic_dims = Karma.collect_dynamic_dims_from_ring dirs all_names in
  List.iter (fun d -> ignore (Prakriti.register_dimension d)) dynamic_dims;
  if emit_meta && dynamic_dims <> [] then
    Printf.printf "dimensions: registered %d dynamic (%s)\n%!"
      (List.length dynamic_dims) (String.concat ", " dynamic_dims);
  (* pass 2: set search_dirs and kosha_root *)
  k.search_dirs := dirs;
  (match dirs with d :: _ -> k.kosha_root := d | [] -> ());
  (* pass 3: load all .om5 files (multi-node aware) *)
  let loaded = ref 0 in
  let skipped = ref 0 in
  List.iter (fun dir ->
    let files = Karma.om5_files_recursive dir in
    List.iter (fun path ->
      let nodes = Karma.parse_file_multi path in
      if nodes = [] then incr skipped
      else List.iter (fun n ->
        ignore (Prakriti.join k n); incr loaded
      ) nodes
    ) files
  ) dirs;
  (k, !loaded, !skipped)

let () =
  let (socket_path, quiet_startup, emit_only, dirs) = parse_argv () in
  let dirs = if dirs = [] then find_default_corpus () else dirs in
  let k0 = Prakriti.empty () in
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
      load_dirs ~emit_meta:(not quiet_startup) dirs k0
  in
  let shabda_loaded =
    let seen = Hashtbl.create 4 in
    let try_dir d acc =
      if Hashtbl.mem seen d then acc
      else begin Hashtbl.replace seen d true; acc + Vidya.load_shabda_dir d end
    in
    List.fold_left (fun acc d ->
      let acc = try_dir (Filename.concat d "shabda") acc in
      let parent = Filename.dirname d in
      try_dir (Filename.concat parent "shabda") acc
    ) 0 dirs in
  if shabda_loaded > 0 && not quiet_startup then
    Printf.printf "shabda: %d entries loaded from external .shabda files\n%!" shabda_loaded;
  let avastha_generated = Jnana.expand_avastha k0 in
  if avastha_generated > 0 && not quiet_startup then
    Printf.printf "avastha: generated %d child nodes\n%!" avastha_generated;
  let reciprocals = Jnana.generate_reciprocals k0 in
  if reciprocals > 0 && not quiet_startup then
    Printf.printf "reciprocals: generated %d mirror edges (abheda, pratipaksha, janya↔phala)\n%!" reciprocals;
  let varga_edges = Jnana.generate_varga_membership k0 in
  if varga_edges > 0 && not quiet_startup then
    Printf.printf "varga: generated %d membership edges\n%!" varga_edges;
  let swarupa_rev = Jnana.generate_swarupa_reverse k0 in
  if swarupa_rev > 0 && not quiet_startup then
    Printf.printf "swarupa-reverse: generated %d parent→child edges\n%!" swarupa_rev;
  let sthita_rev = Jnana.generate_sthita_reverse k0 in
  if sthita_rev > 0 && not quiet_startup then
    Printf.printf "sthita-reverse: generated %d context→member edges\n%!" sthita_rev;
  let matra_inh = Jnana.generate_matra_inheritance k0 in
  if matra_inh > 0 && not quiet_startup then
    Printf.printf "matra-inherit: generated %d unit inheritance edges\n%!" matra_inh;
  let awareness = Jnana.generate_awareness_reverse k0 in
  if awareness > 0 && not quiet_startup then
    Printf.printf "awareness: generated %d reverse edges (siddha, kriya, drishthanta)\n%!" awareness;
  let yukta_sl = Jnana.generate_yukta_same_layer k0 in
  if yukta_sl > 0 && not quiet_startup then
    Printf.printf "yukta-same-layer: generated %d reciprocal edges\n%!" yukta_sl;
  let edge_inh = Jnana.generate_edge_inheritance k0 in
  if edge_inh > 0 && not quiet_startup then
    Printf.printf "edge-inherit: generated %d inherited edges from parents\n%!" edge_inh;
  let varga_pat = Jnana.generate_varga_patterns k0 in
  if varga_pat > 0 && not quiet_startup then
    Printf.printf "varga-patterns: generated %d consensus-replicated edges\n%!" varga_pat;
  let naama_edges = Vidya.emit_shabda_edges k0 in
  if naama_edges > 0 && not quiet_startup then
    Printf.printf "naama: %d word edges emitted into graph\n%!" naama_edges;
  let yantra_idx = Kriya.build_index ~graph:k0 dirs in
  Vidya.set_word_index yantra_idx.word_index;
  Prakriti.materialize_csr k0;
  Prakriti.compute_visheshanam_entropy_weights k0;
  let yantra_session = Kriya.new_session () in
  (match Hashtbl.find_opt yantra_idx.Kriya.by_name "reboot" with
   | Some t ->
     ignore (Kriya_eval.eval_tantra ~idx:yantra_idx ~session:yantra_session
                k0 t [("_", Kriya.VString "boot")])
   | None -> ());
  Prakriti.materialize_csr k0;
  if not quiet_startup then begin
    let n_nodes = Hashtbl.length k0.Prakriti.nodes in
    let n_edges = List.length !(k0.Prakriti.all_edges) in
    Printf.printf "loaded %d suktas (%d skipped). %d nodes, %d edges.\n%!"
      loaded skipped n_nodes n_edges;
    let ndims = Prakriti.dimension_count () in
    if ndims > 10 then
      Printf.printf "dimensions (visheshanam): %d (10 core + %d dynamic)\n%!" ndims (ndims - 10);
    Printf.printf "space (akasham) ready.\n%!"
  end;
  match socket_path with
  | Some path -> Dvara.serve k0 yantra_idx yantra_session dirs path
  | None      -> madakkal k0 yantra_idx yantra_session emit_only
