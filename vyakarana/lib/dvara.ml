(* dvara.ml — Unix domain socket server + session management.
   replaces socket.ml (934L). Uses Prakriti.json_escape via je helper.
   Uses Karma for edit operations. Uses Kriya for eval/tantra operations.
   Uses Jnana for tantra reload.

   sections:
     1. JSON helpers — je, field extraction, array extraction
     2. session store
     3. response builders — ok, error, graph, eval, inspect, list-tantras, triples
     4. pipeline-trace + mantra-status
     5. attach + reload
     6. edit command handler
     7. handle_client — dispatch one request
     8. serve — main server loop *)

open Prakriti
open Kriya_types

(* ═══════════════════════════════════════════════════════════════════════════
   1. JSON HELPERS
   ═══════════════════════════════════════════════════════════════════════════ *)

let je s =
  let buf = Buffer.create (String.length s + 2) in
  Buffer.add_char buf '"';
  String.iter (fun c ->
    match c with
    | '"'  -> Buffer.add_string buf "\\\""
    | '\\' -> Buffer.add_string buf "\\\\"
    | '\n' -> Buffer.add_string buf "\\n"
    | '\r' -> Buffer.add_string buf "\\r"
    | '\t' -> Buffer.add_string buf "\\t"
    | c    -> Buffer.add_char buf c
  ) s;
  Buffer.add_char buf '"';
  Buffer.contents buf

let json_string_field (json : string) (key : string) : string option =
  let pat = "\"" ^ key ^ "\"" in
  let len = String.length json in
  let pat_len = String.length pat in
  let rec scan i =
    if i + pat_len > len then None
    else if String.sub json i pat_len = pat then begin
      let j = ref (i + pat_len) in
      while !j < len && (json.[!j] = ' ' || json.[!j] = ':' || json.[!j] = '\t') do incr j done;
      if !j < len && json.[!j] = '"' then begin
        incr j;
        let buf = Buffer.create 64 in
        let escape = ref false in
        let found = ref false in
        while !j < len && not !found do
          let c = json.[!j] in
          if !escape then begin
            (match c with
            | '"' -> Buffer.add_char buf '"' | '\\' -> Buffer.add_char buf '\\'
            | 'n' -> Buffer.add_char buf '\n' | 'r' -> Buffer.add_char buf '\r'
            | 't' -> Buffer.add_char buf '\t' | _ -> Buffer.add_char buf c);
            escape := false
          end else if c = '\\' then escape := true
          else if c = '"' then found := true
          else Buffer.add_char buf c;
          incr j
        done;
        if !found then Some (Buffer.contents buf) else None
      end else None
    end else scan (i + 1)
  in
  scan 0

let json_int_field (json : string) (key : string) : int option =
  let pat = "\"" ^ key ^ "\"" in
  let len = String.length json in
  let pat_len = String.length pat in
  let rec scan i =
    if i + pat_len > len then None
    else if String.sub json i pat_len = pat then begin
      let j = ref (i + pat_len) in
      while !j < len && (json.[!j] = ' ' || json.[!j] = ':' || json.[!j] = '\t') do incr j done;
      let start = !j in
      while !j < len && json.[!j] >= '0' && json.[!j] <= '9' do incr j done;
      if !j > start then int_of_string_opt (String.sub json start (!j - start))
      else None
    end else scan (i + 1)
  in
  scan 0

let json_string_array_field (json : string) (key : string) : string list =
  let pat = "\"" ^ key ^ "\"" in
  let len = String.length json in
  let pat_len = String.length pat in
  let rec scan i =
    if i + pat_len > len then []
    else if String.sub json i pat_len = pat then begin
      let j = ref (i + pat_len) in
      while !j < len && (json.[!j] = ' ' || json.[!j] = ':' || json.[!j] = '\t') do incr j done;
      if !j < len && json.[!j] = '[' then begin
        incr j;
        let items = ref [] in
        let done_ = ref false in
        while !j < len && not !done_ do
          let c = json.[!j] in
          if c = ']' then done_ := true
          else if c = '"' then begin
            incr j;
            let buf = Buffer.create 32 in
            let escape = ref false in
            let found = ref false in
            while !j < len && not !found do
              let ch = json.[!j] in
              if !escape then begin
                (match ch with '"' -> Buffer.add_char buf '"'
                | '\\' -> Buffer.add_char buf '\\' | 'n' -> Buffer.add_char buf '\n'
                | _ -> Buffer.add_char buf ch); escape := false
              end else if ch = '\\' then escape := true
              else if ch = '"' then found := true
              else Buffer.add_char buf ch;
              incr j
            done;
            if !found then items := Buffer.contents buf :: !items
          end else incr j
        done;
        List.rev !items
      end else []
    end else scan (i + 1)
  in
  scan 0

let opt_field ?(default="") (json : string) (key : string) : string =
  Option.value ~default (json_string_field json key)

(* ═══════════════════════════════════════════════════════════════════════════
   2. SESSION STORE
   ═══════════════════════════════════════════════════════════════════════════ *)

type session_entry = {
  mutable se_graph   : (string * string * string) list;
  mutable se_turn    : int;
  mutable se_turn_id : string;
  mutable se_yantra  : session;
}

let session_store : (string, session_entry) Hashtbl.t = Hashtbl.create 16

let get_or_create_session (sid : string) : session_entry =
  match Hashtbl.find_opt session_store sid with
  | Some entry -> entry
  | None ->
    let entry = {
      se_graph = []; se_turn = 0; se_turn_id = "prashna-0";
      se_yantra = Kriya_eval.new_session ();
    } in
    Hashtbl.replace session_store sid entry; entry

(* ═══════════════════════════════════════════════════════════════════════════
   3. RESPONSE BUILDERS
   ═══════════════════════════════════════════════════════════════════════════ *)

let ok_response (req_id : string) (ses_id : string) (trn_id : string)
    (answer_text : string) : string =
  Printf.sprintf
    "{\"status\":\"ok\",\"request_id\":%s,\"session_id\":%s,\"turn_id\":%s,\"answer_text\":%s}"
    (je req_id) (je ses_id) (je trn_id) (je answer_text)

let error_response (req_id : string) (ses_id : string) (trn_id : string)
    (code : string) (msg : string) : string =
  Printf.sprintf
    "{\"status\":\"error\",\"request_id\":%s,\"session_id\":%s,\"turn_id\":%s,\
\"error\":{\"code\":%s,\"message\":%s}}"
    (je req_id) (je ses_id) (je trn_id) (je code) (je msg)

let graph_response (k : proof_graph) : string =
  let nodes = Hashtbl.fold (fun _ n acc -> n :: acc) k.nodes [] in
  let nodes = List.sort (fun a b -> String.compare a.name b.name) nodes in
  let buf = Buffer.create (1024 * 128) in
  Buffer.add_string buf "{\"status\":\"ok\",\"command\":\"graph\",\"node_count\":";
  Buffer.add_string buf (string_of_int (List.length nodes));
  Buffer.add_string buf ",\"nodes\":[";
  List.iteri (fun i n ->
    if i > 0 then Buffer.add_char buf ',';
    Buffer.add_string buf "{\"name\":"; Buffer.add_string buf (je n.name);
    Buffer.add_string buf ",\"satya\":"; Buffer.add_string buf (Printf.sprintf "%.4f" n.satya);
    Buffer.add_string buf ",\"edges\":[";
    List.iteri (fun ei e ->
      if ei > 0 then Buffer.add_char buf ',';
      Buffer.add_string buf "{\"target\":"; Buffer.add_string buf (je e.target);
      Buffer.add_string buf ",\"relation\":";
      Buffer.add_string buf (je (string_of_visheshanam e.relation));
      Buffer.add_char buf '}'
    ) n.edges;
    Buffer.add_string buf "]}"
  ) nodes;
  Buffer.add_string buf "]}";
  Buffer.contents buf

let eval_response (expr_str : string) (result_str : string) (elapsed_ms : int) : string =
  let passed = result_str = "true" || (result_str <> "" && result_str <> "false" && result_str <> "none") in
  Printf.sprintf
    "{\"status\":\"ok\",\"command\":\"eval\",\"expr\":%s,\"result\":%s,\"passed\":%s,\"elapsed_ms\":%d}"
    (je expr_str) (je result_str) (if passed then "true" else "false") elapsed_ms

let inspect_node_response (k : proof_graph) (name : string) : string =
  match Hashtbl.find_opt k.nodes name with
  | None -> error_response "" "" "" "NOT_FOUND" (Printf.sprintf "node not found: %s" name)
  | Some n ->
    let in_edges = Hashtbl.fold (fun src node acc ->
      List.fold_left (fun a e ->
        if e.target = name then
          (Printf.sprintf "{\"source\":%s,\"relation\":%s}"
            (je src) (je (string_of_visheshanam e.relation))) :: a
        else a
      ) acc node.edges
    ) k.nodes [] in
    let buf = Buffer.create 512 in
    Buffer.add_string buf "{\"status\":\"ok\",\"command\":\"inspect-node\",\"name\":";
    Buffer.add_string buf (je name);
    Buffer.add_string buf ",\"satya\":"; Buffer.add_string buf (Printf.sprintf "%.4f" n.satya);
    Buffer.add_string buf ",\"out_edges\":[";
    List.iteri (fun i e ->
      if i > 0 then Buffer.add_char buf ',';
      Buffer.add_string buf (Printf.sprintf "{\"target\":%s,\"relation\":%s}"
        (je e.target) (je (string_of_visheshanam e.relation)))
    ) n.edges;
    Buffer.add_string buf "],\"in_edges\":[";
    List.iteri (fun i s -> if i > 0 then Buffer.add_char buf ','; Buffer.add_string buf s) in_edges;
    Buffer.add_string buf "]}";
    Buffer.contents buf

let list_tantras_response (yantra_idx : tantra_index) : string =
  let names = List.map (fun t -> je t.t_name) !(yantra_idx.all_tantras) in
  let names_sorted = List.sort String.compare names in
  Printf.sprintf "{\"status\":\"ok\",\"command\":\"list-tantras\",\"count\":%d,\"tantras\":[%s]}"
    (List.length names_sorted) (String.concat "," names_sorted)

let triples_of_response (k : proof_graph) (name : string) : string =
  let buf = Buffer.create 512 in
  let triples = ref [] in
  (match Hashtbl.find_opt k.nodes name with
   | None -> ()
   | Some n ->
     List.iter (fun e ->
       triples := (Printf.sprintf "[%s,%s,%s]" (je name)
         (je (string_of_visheshanam e.relation)) (je e.target)) :: !triples
     ) n.edges);
  Hashtbl.iter (fun src node ->
    if src <> name then
      List.iter (fun e ->
        if e.target = name then
          triples := (Printf.sprintf "[%s,%s,%s]" (je src)
            (je (string_of_visheshanam e.relation)) (je name)) :: !triples
      ) node.edges
  ) k.nodes;
  Buffer.add_string buf "{\"status\":\"ok\",\"command\":\"triples-of\",\"node\":";
  Buffer.add_string buf (je name);
  Buffer.add_string buf ",\"triples\":[";
  let sorted = List.sort String.compare !triples in
  List.iteri (fun i s -> if i > 0 then Buffer.add_char buf ','; Buffer.add_string buf s) sorted;
  Buffer.add_string buf "]}";
  Buffer.contents buf

(* ═══════════════════════════════════════════════════════════════════════════
   4. PIPELINE-TRACE + MANTRA-STATUS
   ═══════════════════════════════════════════════════════════════════════════ *)

let pipeline_trace_response (k : proof_graph) (yantra_idx : tantra_index)
    (yantra_session : session) (sentence : string) : string =
  let stages = [
    "build-question-graph"; "sandhi-kosha"; "sandhi-avastha"; "sandhi-bandhana";
    "vibhakti-shashthi"; "vishesa-instance"; "rashi-viveka"; "vishesa-bandhana";
    "rashi-anuvada"; "sankhya-bandha";
  ] in
  let eval_stage stage_name arg_json =
    let expr = if stage_name = "build-question-graph" then
      Printf.sprintf "build-question-graph \"%s\"" (String.escaped sentence)
    else Printf.sprintf "%s %s" stage_name arg_json in
    let env = Kriya_eval.new_session () in
    ignore env;
    let env2 = Kriya.new_env () in
    Kriya_eval.with_eval_ctx yantra_idx yantra_session
      (fun () ->
        let parsed = Kriya.parse_expr_string expr in
        let result = Kriya.eval k env2 parsed in
        (val_to_json result, result))
      ~default:(("\"error: eval_stage failed\"", VList []))
  in
  let buf = Buffer.create 2048 in
  Buffer.add_string buf "{\"status\":\"ok\",\"command\":\"pipeline-trace\",\"sentence\":";
  Buffer.add_string buf (je sentence);
  Buffer.add_string buf ",\"stages\":[";
  let prev_json = ref "null" in
  List.iteri (fun i stage ->
    if i > 0 then Buffer.add_char buf ',';
    let (result_json, _) = eval_stage stage !prev_json in
    prev_json := result_json;
    Buffer.add_string buf "{\"stage\":"; Buffer.add_string buf (je stage);
    Buffer.add_string buf ",\"triples\":"; Buffer.add_string buf result_json;
    Buffer.add_char buf '}'
  ) stages;
  Buffer.add_string buf "]}";
  Buffer.contents buf

let mantra_status_response (k : proof_graph) (yantra_idx : tantra_index)
    (yantra_session : session) (sentence : string) : string =
  let eval_expr_json expr_str fallback =
    let env = Kriya.new_env () in
    Kriya_eval.with_eval_ctx yantra_idx yantra_session
      (fun () ->
        let parsed = Kriya.parse_expr_string expr_str in
        val_to_json (Kriya.eval k env parsed))
      ~default:fallback
  in
  let refined_json = eval_expr_json
    (Printf.sprintf "fixpoint (build-question-graph \"%s\") avrti-refine"
       (String.escaped sentence)) "[]" in
  let bound_json = eval_expr_json (Printf.sprintf "debug-bound-concepts %s" refined_json) "[]" in
  let mantras_json = eval_expr_json (Printf.sprintf "mantra-coverage %s" refined_json) "[]" in
  Printf.sprintf
    "{\"status\":\"ok\",\"command\":\"mantra-status\",\"sentence\":%s,\
\"refined_graph\":%s,\"bound_concepts\":%s,\"mantras\":%s}"
    (je sentence) refined_json bound_json mantras_json

(* ═══════════════════════════════════════════════════════════════════════════
   5. ATTACH + RELOAD
   ═══════════════════════════════════════════════════════════════════════════ *)

let attach_file (k : proof_graph) (_yantra_idx : tantra_index) (path : string) : string =
  let ext = Filename.extension path in
  match ext with
  | ".om5" ->
    (match Karma.parse_file path with
     | None -> error_response "" "" "" "ATTACH_ERROR"
         (Printf.sprintf "could not parse om5 file: %s" path)
     | Some n ->
       ignore (join k n); init_satya k; materialize_csr k;
       Printf.printf "[attach] om5: %s\n%!" n.name;
       Printf.sprintf "{\"status\":\"ok\",\"command\":\"attach\",\"kind\":\"om5\",\
\"name\":%s,\"path\":%s}" (je n.name) (je path))
  | _ ->
    error_response "" "" "" "ATTACH_ERROR"
      (Printf.sprintf "unsupported file type '%s' — expected .om5" ext)

let reload_tantras (k : proof_graph) (yantra_idx : tantra_index) (dirs : string list) : string =
  Hashtbl.clear yantra_idx.by_name;
  Hashtbl.clear yantra_idx.by_output;
  Hashtbl.clear yantra_idx.by_input;
  Hashtbl.clear yantra_idx.constants;
  Hashtbl.clear yantra_idx.conversions;
  Hashtbl.clear yantra_idx.word_index;
  Hashtbl.clear yantra_idx.eval_index;
  yantra_idx.all_tantras := [];
  let tantra_dirs = Jnana.collect_tantra_dirs dirs in
  Jnana.pre_scan_arities tantra_dirs;
  List.iter (fun dir -> Jnana.load_tantra_dir ~graph:k yantra_idx dir) tantra_dirs;
  Jnana.build_word_index k yantra_idx;
  let session = Kriya_eval.new_session () in
  (match Hashtbl.find_opt yantra_idx.by_name "reboot" with
   | Some t ->
     ignore (Kriya_eval.eval_tantra ~idx:yantra_idx ~session
                k t [("_", VString "reload")])
   | None -> ());
  materialize_csr k;
  let n = List.length !(yantra_idx.all_tantras) in
  Printf.printf "[reload-all] %d tantras loaded from %d dirs\n%!" n (List.length tantra_dirs);
  Printf.sprintf "{\"status\":\"ok\",\"command\":\"reload-all\",\"tantras_loaded\":%d}" n

(* ═══════════════════════════════════════════════════════════════════════════
   6. EDIT COMMAND HANDLER
   ═══════════════════════════════════════════════════════════════════════════ *)

let edit_response (result : Karma.edit_result) (command : string) : string =
  match result with
  | Karma.Ok name ->
    Printf.printf "[%s] ok: %s\n%!" command name;
    Printf.sprintf "{\"status\":\"ok\",\"command\":%s,\"name\":%s}" (je command) (je name)
  | Karma.Err msg ->
    error_response "" "" "" "EDIT_ERROR" msg

let handle_edit_command (k : proof_graph) (yantra_idx : tantra_index)
    (dirs : string list) (line : string) (command : string) : string =
  match command with
  | "create-node" ->
    let path = opt_field line "path" in let layer = opt_field line "layer" in
    let name = opt_field line "name" in let slokas = json_string_array_field line "slokas" in
    let shabda = opt_field line "shabda" in
    if path = "" || layer = "" || name = "" then
      error_response "" "" "" "INVALID_REQUEST" "create-node requires: path, layer, name"
    else edit_response (Karma.create_node k path layer name [] slokas shabda) command
  | "delete-node" ->
    let name = opt_field line "name" in
    if name = "" then error_response "" "" "" "INVALID_REQUEST" "delete-node requires: name"
    else edit_response (Karma.delete_node k name) command
  | "add-sloka" ->
    let name = opt_field line "name" in let sloka = opt_field line "sloka" in
    if name = "" || sloka = "" then error_response "" "" "" "INVALID_REQUEST" "add-sloka requires: name, sloka"
    else edit_response (Karma.edit_add_sloka k name sloka) command
  | "remove-sloka" ->
    let name = opt_field line "name" in let sloka = opt_field line "sloka" in
    if name = "" || sloka = "" then error_response "" "" "" "INVALID_REQUEST" "remove-sloka requires: name, sloka"
    else edit_response (Karma.edit_remove_sloka k name sloka) command
  | "set-shabda" ->
    let name = opt_field line "name" in let shabda = opt_field line "shabda" in
    if name = "" then error_response "" "" "" "INVALID_REQUEST" "set-shabda requires: name"
    else edit_response (Karma.edit_set_shabda k name shabda) command
  | "add-edge" ->
    let source = opt_field line "source" in let target = opt_field line "target" in
    let relation = opt_field line "relation" in
    if source = "" || target = "" || relation = "" then
      error_response "" "" "" "INVALID_REQUEST" "add-edge requires: source, target, relation"
    else edit_response (Karma.add_edge k source target relation) command
  | "remove-edge" ->
    let source = opt_field line "source" in let target = opt_field line "target" in
    let relation = opt_field line "relation" in
    if source = "" || target = "" || relation = "" then
      error_response "" "" "" "INVALID_REQUEST" "remove-edge requires: source, target, relation"
    else edit_response (Karma.remove_edge k source target relation) command
  | "set-comment" ->
    let name = opt_field line "name" in let prefix = opt_field line "prefix" in
    let text = opt_field line "text" in
    if name = "" || prefix = "" || text = "" then
      error_response "" "" "" "INVALID_REQUEST" "set-comment requires: name, prefix, text"
    else edit_response (Karma.edit_set_comment k name prefix text) command
  | "remove-comment" ->
    let name = opt_field line "name" in let prefix = opt_field line "prefix" in
    if name = "" || prefix = "" then
      error_response "" "" "" "INVALID_REQUEST" "remove-comment requires: name, prefix"
    else edit_response (Karma.edit_remove_comment k name prefix) command
  | "add-comment" ->
    let name = opt_field line "name" in let text = opt_field line "text" in
    if name = "" || text = "" then
      error_response "" "" "" "INVALID_REQUEST" "add-comment requires: name, text"
    else edit_response (Karma.edit_add_comment k name text) command
  | "add-shabda-entry" ->
    let path = opt_field line "path" in let word = opt_field line "word" in
    let abheda = json_string_array_field line "abheda" in
    let yukta = json_string_array_field line "yukta" in
    if path = "" || word = "" then
      error_response "" "" "" "INVALID_REQUEST" "add-shabda-entry requires: path, word"
    else edit_response (Karma.edit_add_shabda_entry k path word abheda yukta) command
  | "remove-shabda-entry" ->
    let path = opt_field line "path" in let word = opt_field line "word" in
    if path = "" || word = "" then
      error_response "" "" "" "INVALID_REQUEST" "remove-shabda-entry requires: path, word"
    else edit_response (Karma.edit_remove_shabda_entry k path word) command
  | "update-shabda-entry" ->
    let path = opt_field line "path" in let word = opt_field line "word" in
    let abheda = json_string_array_field line "abheda" in
    let yukta = json_string_array_field line "yukta" in
    if path = "" || word = "" then
      error_response "" "" "" "INVALID_REQUEST" "update-shabda-entry requires: path, word"
    else edit_response (Karma.edit_update_shabda_entry k path word abheda yukta) command
  | "write-tantra" ->
    let path = opt_field line "path" in let source = opt_field line "source" in
    if path = "" || source = "" then
      error_response "" "" "" "INVALID_REQUEST" "write-tantra requires: path, source"
    else begin
      let result = Karma.edit_write_tantra k path source in
      ignore (reload_tantras k yantra_idx dirs);
      edit_response result command
    end
  | _ ->
    error_response "" "" "" "UNKNOWN_COMMAND" (Printf.sprintf "unknown edit command: %s" command)

(* ═══════════════════════════════════════════════════════════════════════════
   7. HANDLE_CLIENT — dispatch one request
   ═══════════════════════════════════════════════════════════════════════════ *)

let handle_client (k : proof_graph) (yantra_idx : tantra_index) (yantra_session : session)
    (dirs : string list) (ic : in_channel) (oc : out_channel) : unit =
  (try
    while true do
      let line = input_line ic in
      let line = String.trim line in
      if String.length line = 0 then ()
      else begin
        let command = json_string_field line "command" in
        let resp = match command with
          | Some "graph" ->
            (try graph_response k with exn ->
               error_response "" "" "" "ENGINE_ERROR" (Printexc.to_string exn))
          | Some "eval" | Some "eval-json" ->
            let as_json = (command = Some "eval-json") in
            let expr_str = opt_field line "expr" in
            if String.trim expr_str = "" then
              error_response "" "" "" "INVALID_REQUEST" "missing required field: expr"
            else
              let t0 = Unix.gettimeofday () in
              let expr_ast =
                (try Some (Kriya.parse_expr_string expr_str)
                 with _ -> None) in
              (match expr_ast with
               | None -> error_response "" "" "" "PARSE_ERROR" ("cannot parse: " ^ expr_str)
               | Some expr_ast ->
                 let env = Kriya.new_env () in
                 let tnames = List.map (fun t -> VString t.t_name) !(yantra_idx.all_tantras) in
                 Hashtbl.replace env "_tantra_index" (VList tnames);
                 let result =
                   Kriya_eval.with_eval_ctx yantra_idx yantra_session
                     (fun () -> Kriya.eval k env expr_ast) ~default:VNone in
                 let t1 = Unix.gettimeofday () in
                 let elapsed_ms = int_of_float ((t1 -. t0) *. 1000.0) in
                 let result_str = as_string result in
                 let result_json = val_to_json result in
                 if String.length result_str <= 200 then
                   Printf.printf "[eval] %s → %s (%dms)\n%!" expr_str result_str elapsed_ms;
                 if as_json then
                   Printf.sprintf
                     "{\"status\":\"ok\",\"command\":\"eval-json\",\"expr\":%s,\"result\":%s,\"elapsed_ms\":%d}"
                     (je expr_str) result_json elapsed_ms
                 else eval_response expr_str result_str elapsed_ms)
          | Some "inspect-node" ->
            (match json_string_field line "name" with
             | None -> error_response "" "" "" "INVALID_REQUEST" "missing required field: name"
             | Some name ->
               (try inspect_node_response k name with exn ->
                  error_response "" "" "" "ENGINE_ERROR" (Printexc.to_string exn)))
          | Some "list-tantras" ->
            (try list_tantras_response yantra_idx with exn ->
               error_response "" "" "" "ENGINE_ERROR" (Printexc.to_string exn))
          | Some "triples-of" ->
            (match json_string_field line "node" with
             | None -> error_response "" "" "" "INVALID_REQUEST" "missing required field: node"
             | Some name ->
               (try triples_of_response k name with exn ->
                  error_response "" "" "" "ENGINE_ERROR" (Printexc.to_string exn)))
          | Some "pipeline-trace" ->
            (match json_string_field line "sentence" with
             | None -> error_response "" "" "" "INVALID_REQUEST" "missing required field: sentence"
             | Some sentence ->
               (try pipeline_trace_response k yantra_idx yantra_session sentence with exn ->
                  error_response "" "" "" "ENGINE_ERROR" (Printexc.to_string exn)))
          | Some "mantra-status" ->
            (match json_string_field line "sentence" with
             | None -> error_response "" "" "" "INVALID_REQUEST" "missing required field: sentence"
             | Some sentence ->
               (try mantra_status_response k yantra_idx yantra_session sentence with exn ->
                  error_response "" "" "" "ENGINE_ERROR" (Printexc.to_string exn)))
          | Some "attach" ->
            (match json_string_field line "path" with
             | None -> error_response "" "" "" "INVALID_REQUEST" "missing required field: path"
             | Some path ->
               (try attach_file k yantra_idx path with exn ->
                  error_response "" "" "" "ATTACH_ERROR" (Printexc.to_string exn)))
          | Some "reload-all" ->
            (try reload_tantras k yantra_idx dirs with exn ->
               error_response "" "" "" "RELOAD_ERROR" (Printexc.to_string exn))
          | Some "dump-ast" ->
            (match json_string_field line "path" with
             | None -> error_response "" "" "" "INVALID_REQUEST" "missing required field: path"
             | Some path ->
               (try
                 (match Vakya.parse_tantra4_file path with
                  | None -> error_response "" "" "" "PARSE_ERROR"
                      (Printf.sprintf "could not parse tantra file: %s" path)
                  | Some t ->
                    Printf.sprintf "{\"status\":\"ok\",\"command\":\"dump-ast\",\"tantra\":%s}"
                      (json_of_tantra t))
                with exn -> error_response "" "" "" "PARSE_ERROR" (Printexc.to_string exn)))
          | Some "dump-om" ->
            (match json_string_field line "path" with
             | None -> error_response "" "" "" "INVALID_REQUEST" "missing required field: path"
             | Some path ->
               (try
                 (match Karma.parse_file path with
                  | None -> error_response "" "" "" "PARSE_ERROR"
                      (Printf.sprintf "could not parse om5 file: %s" path)
                  | Some n ->
                    Printf.sprintf "{\"status\":\"ok\",\"command\":\"dump-om\",\"nigamana\":%s}"
                      (json_of_nigamana n))
                with exn -> error_response "" "" "" "PARSE_ERROR" (Printexc.to_string exn)))
          | Some "end-session" ->
            let ses_id = opt_field line "session_id" in
            if ses_id <> "" then Hashtbl.remove session_store ses_id;
            "{\"status\":\"ok\",\"command\":\"end-session\"}"
          | Some "create-node" | Some "delete-node"
          | Some "add-sloka" | Some "remove-sloka" | Some "set-shabda"
          | Some "add-edge" | Some "remove-edge"
          | Some "set-comment" | Some "remove-comment" | Some "add-comment"
          | Some "add-shabda-entry" | Some "remove-shabda-entry" | Some "update-shabda-entry"
          | Some "write-tantra" ->
            (try handle_edit_command k yantra_idx dirs line (Option.get command)
             with exn -> error_response "" "" "" "EDIT_ERROR" (Printexc.to_string exn))
          | _ ->
            let req_id = opt_field line "request_id" in
            let ses_id = opt_field line "session_id" in
            let trn_id = opt_field line "turn_id" in
            let question = json_string_field line "question" in
            let max_passes = json_int_field line "max_passes" in
            let (_active_session, _prior_graph, _has_session) =
              if ses_id <> "" then
                let entry = get_or_create_session ses_id in
                entry.se_turn <- entry.se_turn + 1;
                entry.se_turn_id <- Printf.sprintf "prashna-%d" entry.se_turn;
                (match entry.se_turn with
                | 1 -> Printf.printf "[session %s / %s]\n%!" ses_id entry.se_turn_id
                | n -> Printf.printf "[session %s / %s ← parampara: prashna-%d]\n%!"
                         ses_id entry.se_turn_id (n - 1));
                let prior = List.map (fun b ->
                  (b.b_name, "sankhya", string_of_float b.b_value)
                ) entry.se_yantra.bindings in
                (entry.se_yantra, prior, true)
              else (yantra_session, [], false)
            in
            (match question with
              | None ->
                error_response req_id ses_id trn_id
                  "INVALID_REQUEST" "missing required field: question"
              | Some q when String.trim q = "" ->
                error_response req_id ses_id trn_id
                  "INVALID_REQUEST" "question must not be empty"
              | Some q ->
                (try
                  ignore max_passes;
                  let run_result =
                    if _has_session then
                      Kriya_eval.run_session_anuvada k yantra_idx _active_session _prior_graph q
                    else
                      Kriya_eval.run_anuvada_ganana k yantra_idx _active_session q
                  in
                  (match run_result with
                   | Some r ->
                     if String.length r.yr_raw_output > 0 then
                       Printf.printf "[socket] %s\n  %s\n%!" q r.yr_raw_output;
                     ok_response req_id ses_id trn_id r.yr_raw_output
                   | None ->
                     error_response req_id ses_id trn_id
                       "ENGINE_ERROR" "session-anuvada or anuvada-ganana tantra not loaded")
                with exn ->
                  error_response req_id ses_id trn_id
                    "ENGINE_ERROR" (Printexc.to_string exn)))
        in
        output_string oc resp; output_char oc '\n'; flush oc
      end
    done
  with End_of_file | Sys_error _ -> ())

(* ═══════════════════════════════════════════════════════════════════════════
   8. SERVE — main server loop
   ═══════════════════════════════════════════════════════════════════════════ *)

let serve (k : proof_graph) (yantra_idx : tantra_index) (yantra_session : session)
    (dirs : string list) (socket_path : string) : unit =
  (try Unix.unlink socket_path with Unix.Unix_error _ -> ());
  let sock = Unix.socket Unix.PF_UNIX Unix.SOCK_STREAM 0 in
  Unix.bind sock (Unix.ADDR_UNIX socket_path);
  Unix.listen sock 16;
  Printf.printf "vyakarana socket listening: %s\n%!" socket_path;
  while true do
    let (client, _) = Unix.accept sock in
    let ic = Unix.in_channel_of_descr client in
    let oc = Unix.out_channel_of_descr client in
    (try handle_client k yantra_idx yantra_session dirs ic oc
     with exn -> Printf.eprintf "client error: %s\n%!" (Printexc.to_string exn));
    (try Unix.close client with Unix.Unix_error _ -> ())
  done
