(* socket.ml — Unix domain socket server mode for vyakarana
   listens on a UDS path, reads newline-delimited JSON requests,
   calls anuvada_query (the same engine as stdin mode),
   writes newline-delimited JSON responses.

   wire protocol: each message is one JSON object per line (no length prefix).

   request fields (all optional except question):
     schema_version  string   "1.0"
     request_id      string
     session_id      string
     turn_id         string
     question        string   the query — may contain inline +flags
     show            string   comma-separated sections: reasoning,strudel,music,resonance,prayoga,all
                              default: reasoning only (answer_text + steps + next_questions + graph_delta)
     question_chain  array    [{turn_id, role, text}]  max 8
     context         object   {running_prayoga: {...}}
     max_passes      int      override avrti depth
     thaalam         string   rhythmic mode
     sahaja          bool     glossed output

   response fields (always present):
     schema_version  "1.0"
     request_id
     session_id
     turn_id
     status          "ok" | "needs_clarification" | "error"
     answer_text
     steps           [{pass, kind, text}]
     next_questions  [string]
     graph_delta     {nodes_activated, edges_activated}
     diagnostics     {passes, connections, confidence_top}

   response fields (only when requested via show):
     music_ir        object   show includes "music"
     resonance_ir    object   show includes "resonance"
     assets          {strudel: string}   show includes "strudel"

   error response adds:
     error           {code, message, retryable} *)

open Proof_graph
open Yantra_types

(* ---- minimal JSON helpers ---- *)

let je s = (* json-escape a string value including quotes *)
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

(* ---- JSON field extraction (no external dep, minimal parser) ----
   only handles the flat fields we need from the request. *)

let json_string_field (json : string) (key : string) : string option =
  (* find "key": "value" *)
  let pat = "\"" ^ key ^ "\"" in
  match String.split_on_char '"' json with
  | _ ->
    (* walk token by token *)
    let len = String.length json in
    let pat_len = String.length pat in
    let rec scan i =
      if i + pat_len > len then None
      else if String.sub json i pat_len = pat then begin
        (* skip past key, find colon, then opening quote *)
        let j = ref (i + pat_len) in
        while !j < len && (json.[!j] = ' ' || json.[!j] = ':' || json.[!j] = '\t') do
          incr j
        done;
        if !j < len && json.[!j] = '"' then begin
          incr j;
          let buf = Buffer.create 64 in
          let escape = ref false in
          let found = ref false in
          while !j < len && not !found do
            let c = json.[!j] in
            if !escape then begin
              (match c with
              | '"'  -> Buffer.add_char buf '"'
              | '\\' -> Buffer.add_char buf '\\'
              | 'n'  -> Buffer.add_char buf '\n'
              | 'r'  -> Buffer.add_char buf '\r'
              | 't'  -> Buffer.add_char buf '\t'
              | _    -> Buffer.add_char buf c);
              escape := false
            end else if c = '\\' then
              escape := true
            else if c = '"' then
              found := true
            else
              Buffer.add_char buf c;
            incr j
          done;
          if !found then Some (Buffer.contents buf) else None
        end else None
      end else
        scan (i + 1)
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
      while !j < len && (json.[!j] = ' ' || json.[!j] = ':' || json.[!j] = '\t') do
        incr j
      done;
      let start = !j in
      while !j < len && json.[!j] >= '0' && json.[!j] <= '9' do
        incr j
      done;
      if !j > start then
        int_of_string_opt (String.sub json start (!j - start))
      else None
    end else
      scan (i + 1)
  in
  scan 0

let json_bool_field (json : string) (key : string) : bool option =
  let pat = "\"" ^ key ^ "\"" in
  let len = String.length json in
  let pat_len = String.length pat in
  let rec scan i =
    if i + pat_len > len then None
    else if String.sub json i pat_len = pat then begin
      let j = ref (i + pat_len) in
      while !j < len && (json.[!j] = ' ' || json.[!j] = ':' || json.[!j] = '\t') do
        incr j
      done;
      if !j + 4 <= len && String.sub json !j 4 = "true" then Some true
      else if !j + 5 <= len && String.sub json !j 5 = "false" then Some false
      else None
    end else
      scan (i + 1)
  in
  scan 0

(* ---- JSON field helpers — collapse Option.value ~default patterns ----
   Before (21+ occurrences):
     Option.value ~default:"" (json_string_field line "key")
   After:
     opt_field line "key"             -- defaults to ""
     opt_field ~default:"x" line "key" -- custom default
     req_field line "key"             -- "" when missing (same as opt_field) *)

let opt_field ?(default="") (json : string) (key : string) : string =
  Option.value ~default (json_string_field json key)

let req_field (json : string) (key : string) : string =
  opt_field json key

(* ---- JSON array extraction (string arrays only) ---- *)

(* extract ["a","b","c"] from a JSON field — minimal parser for flat string arrays *)
let json_string_array_field (json : string) (key : string) : string list =
  let pat = "\"" ^ key ^ "\"" in
  let len = String.length json in
  let pat_len = String.length pat in
  let rec scan i =
    if i + pat_len > len then []
    else if String.sub json i pat_len = pat then begin
      (* skip past key, find colon, then opening bracket *)
      let j = ref (i + pat_len) in
      while !j < len && (json.[!j] = ' ' || json.[!j] = ':' || json.[!j] = '\t') do
        incr j
      done;
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
                (match ch with
                | '"'  -> Buffer.add_char buf '"'
                | '\\' -> Buffer.add_char buf '\\'
                | 'n'  -> Buffer.add_char buf '\n'
                | _    -> Buffer.add_char buf ch);
                escape := false
              end else if ch = '\\' then escape := true
              else if ch = '"' then found := true
              else Buffer.add_char buf ch;
              incr j
            done;
            if !found then items := Buffer.contents buf :: !items
          end else
            incr j
        done;
        List.rev !items
      end else []
    end else
      scan (i + 1)
  in
  scan 0

(* ---- session store ---- *)
(* in-memory per-session state, keyed by session_id string.
   each session has its own yantra evaluation context so bindings are isolated.
   sessions are created on first question request and persist until end-session
   or server restart. *)

type session_entry = {
  mutable se_graph   : (string * string * string) list;  (* accumulated triple layers *)
  mutable se_turn    : int;                              (* turn count, 1-based *)
  mutable se_turn_id : string;                           (* "prashna-N" *)
  mutable se_yantra  : session;                          (* per-session yantra context *)
}

let session_store : (string, session_entry) Hashtbl.t = Hashtbl.create 16

let get_or_create_session (sid : string) : session_entry =
  match Hashtbl.find_opt session_store sid with
  | Some entry -> entry
  | None ->
    let entry = {
      se_graph   = [];
      se_turn    = 0;
      se_turn_id = "prashna-0";
      se_yantra  = Yantra.new_session ();
    } in
    Hashtbl.replace session_store sid entry;
    entry

(* ---- response builders ---- *)

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

(* ---- graph response — full pravaha as a single JSON line ---- *)

let graph_response (k : proof_graph) : string =
  let nodes = Hashtbl.fold (fun _ n acc -> n :: acc) k.nodes [] in
  let nodes = List.sort (fun a b -> String.compare a.name b.name) nodes in
  let buf = Buffer.create (1024 * 128) in
  Buffer.add_string buf "{\"status\":\"ok\",\"command\":\"graph\",\"node_count\":";
  Buffer.add_string buf (string_of_int (List.length nodes));
  Buffer.add_string buf ",\"nodes\":[";
  List.iteri (fun i n ->
    if i > 0 then Buffer.add_char buf ',';
    Buffer.add_string buf "{\"name\":";
    Buffer.add_string buf (je n.name);
    Buffer.add_string buf ",\"satya\":";
    Buffer.add_string buf (Printf.sprintf "%.4f" n.satya);
    Buffer.add_string buf ",\"edges\":[";
    List.iteri (fun ei e ->
      if ei > 0 then Buffer.add_char buf ',';
      Buffer.add_string buf "{\"target\":";
      Buffer.add_string buf (je e.target);
      Buffer.add_string buf ",\"relation\":";
      Buffer.add_string buf (je (string_of_visheshanam e.relation));
      Buffer.add_char buf '}'
    ) n.edges;
    Buffer.add_string buf "]}"
  ) nodes;
  Buffer.add_string buf "]}";
  Buffer.contents buf

(* ---- eval response ---- *)

let eval_response (expr_str : string) (result_str : string) (elapsed_ms : int) : string =
  (* passed = result is "true" (test convention) or non-empty non-"false" *)
  let passed = result_str = "true" || (result_str <> "" && result_str <> "false" && result_str <> "none") in
  Printf.sprintf
    "{\"status\":\"ok\",\"command\":\"eval\",\"expr\":%s,\"result\":%s,\"passed\":%s,\"elapsed_ms\":%d}"
    (je expr_str) (je result_str) (if passed then "true" else "false") elapsed_ms

(* ---- inspect-node: return one node with both outgoing and incoming edges ---- *)

let inspect_node_response (k : proof_graph) (name : string) : string =
  match Hashtbl.find_opt k.nodes name with
  | None ->
    error_response "" "" "" "NOT_FOUND"
      (Printf.sprintf "node not found: %s" name)
  | Some n ->
    (* incoming edges: scan all nodes for edges pointing at `name` *)
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
    Buffer.add_string buf ",\"satya\":";
    Buffer.add_string buf (Printf.sprintf "%.4f" n.satya);
    Buffer.add_string buf ",\"out_edges\":[";
    List.iteri (fun i e ->
      if i > 0 then Buffer.add_char buf ',';
      Buffer.add_string buf
        (Printf.sprintf "{\"target\":%s,\"relation\":%s}"
          (je e.target) (je (string_of_visheshanam e.relation)))
    ) n.edges;
    Buffer.add_string buf "],\"in_edges\":[";
    List.iteri (fun i s ->
      if i > 0 then Buffer.add_char buf ',';
      Buffer.add_string buf s
    ) in_edges;
    Buffer.add_string buf "]}";
    Buffer.contents buf

(* ---- list-tantras: enumerate all loaded tantras by name ---- *)

let list_tantras_response (yantra_idx : tantra_index) : string =
  let names = List.map (fun t -> je t.t_name) !(yantra_idx.all_tantras) in
  let names_sorted = List.sort String.compare names in
  Printf.sprintf "{\"status\":\"ok\",\"command\":\"list-tantras\",\"count\":%d,\"tantras\":[%s]}"
    (List.length names_sorted)
    (String.concat "," names_sorted)

(* ---- triples-of: all triples involving a node (as subj or obj) ---- *)

let triples_of_response (k : proof_graph) (name : string) : string =
  (* outgoing: [name, rel, target] for each edge from name *)
  (* incoming: [source, rel, name] for each edge to name *)
  let buf = Buffer.create 512 in
  let triples = ref [] in
  (match Hashtbl.find_opt k.nodes name with
   | None -> ()
   | Some n ->
     List.iter (fun e ->
       triples := (Printf.sprintf "[%s,%s,%s]"
         (je name)
         (je (string_of_visheshanam e.relation))
         (je e.target)) :: !triples
     ) n.edges);
  Hashtbl.iter (fun src node ->
    if src <> name then
      List.iter (fun e ->
        if e.target = name then
          triples := (Printf.sprintf "[%s,%s,%s]"
            (je src)
            (je (string_of_visheshanam e.relation))
            (je name)) :: !triples
      ) node.edges
  ) k.nodes;
  Buffer.add_string buf "{\"status\":\"ok\",\"command\":\"triples-of\",\"node\":";
  Buffer.add_string buf (je name);
  Buffer.add_string buf ",\"triples\":[";
  let sorted = List.sort String.compare !triples in
  List.iteri (fun i s ->
    if i > 0 then Buffer.add_char buf ',';
    Buffer.add_string buf s
  ) sorted;
  Buffer.add_string buf "]}";
  Buffer.contents buf

(* ---- pipeline-trace: run avrti-refine stage-by-stage, return graph delta per stage ---- *)

let pipeline_trace_response (k : proof_graph) (yantra_idx : tantra_index)
    (yantra_session : session) (sentence : string) : string =
  let stages = [
    "build-question-graph";
    "sandhi-kosha";
    "sandhi-avastha";
    "sandhi-bandhana";
    "vibhakti-shashthi";
    "vishesa-instance";
    "rashi-viveka";
    "vishesa-bandhana";
    "rashi-anuvada";
    "sankhya-bandha";
  ] in
  (* helper: eval one tantra call, passing previous result as input *)
  let eval_stage stage_name arg_json =
    let expr = if stage_name = "build-question-graph" then
      Printf.sprintf "build-question-graph \"%s\"" (String.escaped sentence)
    else
      Printf.sprintf "%s %s" stage_name arg_json
    in
    let env = Yantra.new_env () in
    Yantra_eval.with_eval_ctx yantra_idx yantra_session
      (fun () ->
        let parsed = Yantra.parse_expr_string expr in
        let result = Yantra.eval k env parsed in
        (Yantra.val_to_json result, result))
      ~default:(
        let msg = Printf.sprintf "\"error: eval_stage failed\"" in
        (msg, Yantra.VList []))
  in
  let buf = Buffer.create 2048 in
  Buffer.add_string buf "{\"status\":\"ok\",\"command\":\"pipeline-trace\",\"sentence\":";
  Buffer.add_string buf (je sentence);
  Buffer.add_string buf ",\"stages\":[";
  let prev_json = ref "null" in
  List.iteri (fun i stage ->
    if i > 0 then Buffer.add_char buf ',';
    let (result_json, _result_val) = eval_stage stage !prev_json in
    prev_json := result_json;
    Buffer.add_string buf "{\"stage\":";
    Buffer.add_string buf (je stage);
    Buffer.add_string buf ",\"triples\":";
    Buffer.add_string buf result_json;
    Buffer.add_char buf '}'
  ) stages;
  Buffer.add_string buf "]}";
  Buffer.contents buf

(* ---- mantra-status: show all mantras + coverage for a sentence ---- *)

let mantra_status_response (k : proof_graph) (yantra_idx : tantra_index)
    (yantra_session : session) (sentence : string) : string =
  (* eval a tantra expr string, returning JSON string result *)
  let eval_expr_json expr_str fallback =
    let env = Yantra.new_env () in
    Yantra_eval.with_eval_ctx yantra_idx yantra_session
      (fun () ->
        let parsed = Yantra.parse_expr_string expr_str in
        Yantra.val_to_json (Yantra.eval k env parsed))
      ~default:fallback
  in
  (* step 1: build refined graph *)
  let refined_json =
    eval_expr_json
      (Printf.sprintf "fixpoint (build-question-graph \"%s\") avrti-refine"
         (String.escaped sentence))
      "[]"
  in
  (* step 2: extract bound-concepts from refined graph via debug-bound-concepts tantra *)
  let bound_json   = eval_expr_json (Printf.sprintf "debug-bound-concepts %s" refined_json) "[]" in
  (* step 3: for each mantra, check coverage via mantra-coverage tantra *)
  let mantras_json = eval_expr_json (Printf.sprintf "mantra-coverage %s" refined_json) "[]" in
  Printf.sprintf
    "{\"status\":\"ok\",\"command\":\"mantra-status\",\"sentence\":%s,\
\"refined_graph\":%s,\"bound_concepts\":%s,\"mantras\":%s}"
    (je sentence) refined_json bound_json mantras_json

(* ---- attach: incrementally add one .om or .tantra file to the live graph ---- *)

let attach_file (k : proof_graph) (_yantra_idx : tantra_index) (path : string) : string =
  let ext = Filename.extension path in
  match ext with
  | ".om" ->
    (* derive known names from the live graph — no disk re-scan needed *)
    let known_names = Hashtbl.fold (fun name _ acc -> name :: acc) k.nodes [] in
    (match Om_parser.parse_file known_names path with
     | None ->
       error_response "" "" "" "ATTACH_ERROR"
         (Printf.sprintf "could not parse om file: %s" path)
     | Some n ->
       ignore (Proof_graph.join k n);
       Proof_graph.init_satya k;
       Proof_graph.materialize_csr k;
       Printf.printf "[attach] om: %s\n%!" n.name;
       Printf.sprintf "{\"status\":\"ok\",\"command\":\"attach\",\"kind\":\"om\",\
\"name\":%s,\"path\":%s}" (je n.name) (je path))
  | _ ->
    error_response "" "" "" "ATTACH_ERROR"
      (Printf.sprintf "unsupported file type '%s' — expected .om" ext)

(* ---- reload-all: re-read all tantra files from disk into the live index ---- *)

let reload_tantras (k : proof_graph) (yantra_idx : tantra_index) (dirs : string list) : string =
  (* clear all tantra index tables *)
  Hashtbl.clear yantra_idx.by_name;
  Hashtbl.clear yantra_idx.by_output;
  Hashtbl.clear yantra_idx.by_input;
  Hashtbl.clear yantra_idx.by_output;
  Hashtbl.clear yantra_idx.constants;
  Hashtbl.clear yantra_idx.conversions;
  Hashtbl.clear yantra_idx.word_index;
  yantra_idx.all_tantras := [];
  (* re-scan arities and re-register all tantras *)
  let tantra_dirs = Yantra_index.collect_tantra_dirs dirs in
  Yantra_index.pre_scan_arities tantra_dirs;
  List.iter (fun dir ->
    Yantra_index.load_tantra_dir ~graph:k yantra_idx dir
  ) tantra_dirs;
  (* rebuild word index from the live graph — needed for lookup-word *)
  Yantra_index.build_word_index k yantra_idx;
  (* run reboot tantra: re-derive structural edges (varga inheritance etc.) *)
  let session = Yantra.new_session () in
  (match Hashtbl.find_opt yantra_idx.by_name "reboot" with
   | Some t ->
     ignore (Yantra_eval.eval_tantra ~idx:yantra_idx ~session
                k t [("_", VString "reload")])
   | None -> ());
  Proof_graph.materialize_csr k;
  let n = List.length !(yantra_idx.all_tantras) in
  Printf.printf "[reload-all] %d tantras loaded from %d dirs\n%!" n (List.length tantra_dirs);
  Printf.sprintf "{\"status\":\"ok\",\"command\":\"reload-all\",\"tantras_loaded\":%d}" n

(* ---- edit command handler ---- *)

let edit_response (result : Om_edit.edit_result) (command : string) : string =
  match result with
  | Om_edit.Ok name ->
    Printf.printf "[%s] ok: %s\n%!" command name;
    Printf.sprintf "{\"status\":\"ok\",\"command\":%s,\"name\":%s}" (je command) (je name)
  | Om_edit.Err msg ->
    error_response "" "" "" "EDIT_ERROR" msg

(* parse comments from JSON: [{"prefix":"desc","text":"..."},{"text":"free form"}] *)
let parse_comments_json (json : string) : (string option * string) list =
  (* minimal: extract from "comments" array field.
     each element has optional "prefix" and required "text". *)
  let _ = json in  (* TODO: full parse — for now, empty *)
  []

let handle_edit_command (k : proof_graph) (yantra_idx : Yantra_types.tantra_index)
    (dirs : string list) (line : string) (command : string) : string =
  match command with
  | "create-node" ->
    let path   = opt_field line "path" in
    let layer  = opt_field line "layer" in
    let name   = opt_field line "name" in
    let slokas = json_string_array_field line "slokas" in
    let shabda = opt_field line "shabda" in
    if path = "" || layer = "" || name = "" then
      error_response "" "" "" "INVALID_REQUEST" "create-node requires: path, layer, name"
    else
      edit_response (Om_edit.create_node k path layer name [] slokas shabda) command

  | "delete-node" ->
    let name = opt_field line "name" in
    if name = "" then
      error_response "" "" "" "INVALID_REQUEST" "delete-node requires: name"
    else
      edit_response (Om_edit.delete_node k name) command

  | "add-sloka" ->
    let name  = opt_field line "name" in
    let sloka = opt_field line "sloka" in
    if name = "" || sloka = "" then
      error_response "" "" "" "INVALID_REQUEST" "add-sloka requires: name, sloka"
    else
      edit_response (Om_edit.add_sloka k name sloka) command

  | "remove-sloka" ->
    let name  = opt_field line "name" in
    let sloka = opt_field line "sloka" in
    if name = "" || sloka = "" then
      error_response "" "" "" "INVALID_REQUEST" "remove-sloka requires: name, sloka"
    else
      edit_response (Om_edit.remove_sloka k name sloka) command

  | "set-shabda" ->
    let name   = opt_field line "name" in
    let shabda = opt_field line "shabda" in
    if name = "" then
      error_response "" "" "" "INVALID_REQUEST" "set-shabda requires: name"
    else
      edit_response (Om_edit.set_shabda k name shabda) command

  | "add-edge" ->
    let source   = opt_field line "source" in
    let target   = opt_field line "target" in
    let relation = opt_field line "relation" in
    if source = "" || target = "" || relation = "" then
      error_response "" "" "" "INVALID_REQUEST" "add-edge requires: source, target, relation"
    else
      edit_response (Om_edit.add_edge k source target relation) command

  | "remove-edge" ->
    let source   = opt_field line "source" in
    let target   = opt_field line "target" in
    let relation = opt_field line "relation" in
    if source = "" || target = "" || relation = "" then
      error_response "" "" "" "INVALID_REQUEST" "remove-edge requires: source, target, relation"
    else
      edit_response (Om_edit.remove_edge k source target relation) command

  | "set-comment" ->
    let name   = opt_field line "name" in
    let prefix = opt_field line "prefix" in
    let text   = opt_field line "text" in
    if name = "" || prefix = "" || text = "" then
      error_response "" "" "" "INVALID_REQUEST" "set-comment requires: name, prefix, text"
    else
      edit_response (Om_edit.set_comment k name prefix text) command

  | "remove-comment" ->
    let name   = opt_field line "name" in
    let prefix = opt_field line "prefix" in
    if name = "" || prefix = "" then
      error_response "" "" "" "INVALID_REQUEST" "remove-comment requires: name, prefix"
    else
      edit_response (Om_edit.remove_comment k name prefix) command

  | "add-comment" ->
    let name = opt_field line "name" in
    let text = opt_field line "text" in
    if name = "" || text = "" then
      error_response "" "" "" "INVALID_REQUEST" "add-comment requires: name, text"
    else
      edit_response (Om_edit.add_comment k name text) command

  | "add-shabda-entry" ->
    let path   = opt_field line "path" in
    let word   = opt_field line "word" in
    let abheda = json_string_array_field line "abheda" in
    let yukta  = json_string_array_field line "yukta" in
    if path = "" || word = "" then
      error_response "" "" "" "INVALID_REQUEST" "add-shabda-entry requires: path, word"
    else
      edit_response (Om_edit.add_shabda_entry k path word abheda yukta) command

  | "remove-shabda-entry" ->
    let path = opt_field line "path" in
    let word = opt_field line "word" in
    if path = "" || word = "" then
      error_response "" "" "" "INVALID_REQUEST" "remove-shabda-entry requires: path, word"
    else
      edit_response (Om_edit.remove_shabda_entry k path word) command

  | "update-shabda-entry" ->
    let path   = opt_field line "path" in
    let word   = opt_field line "word" in
    let abheda = json_string_array_field line "abheda" in
    let yukta  = json_string_array_field line "yukta" in
    if path = "" || word = "" then
      error_response "" "" "" "INVALID_REQUEST" "update-shabda-entry requires: path, word"
    else
      edit_response (Om_edit.update_shabda_entry k path word abheda yukta) command

  | "write-tantra" ->
    let path   = opt_field line "path" in
    let source = opt_field line "source" in
    if path = "" || source = "" then
      error_response "" "" "" "INVALID_REQUEST" "write-tantra requires: path, source"
    else begin
      let result = Om_edit.write_tantra k path source in
      (* reload tantras so the new/edited tantra is available *)
      ignore (reload_tantras k yantra_idx dirs);
      edit_response result command
    end

  | _ ->
    error_response "" "" "" "UNKNOWN_COMMAND" (Printf.sprintf "unknown edit command: %s" command)

(* ---- handle one client connection ---- *)

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
            (* return full proof graph as JSON *)
            (try graph_response k
             with exn ->
               error_response "" "" "" "ENGINE_ERROR" (Printexc.to_string exn))
          | Some "eval" | Some "eval-json" ->
             (* evaluate a tantra expression directly — used by the Python test runner.
                "eval"      → result field is a string (as_string repr, legacy).
                "eval-json" → result field is a JSON value (val_to_json repr). *)
             let as_json = (command = Some "eval-json") in
              let expr_str = opt_field line "expr" in
             if String.trim expr_str = "" then
               error_response "" "" "" "INVALID_REQUEST" "missing required field: expr"
             else
                let t0 = Unix.gettimeofday () in
                let expr_ast =
                  (try Some (Yantra.parse_expr_string expr_str)
                   with exn ->
                     error_response "" "" "" "ENGINE_ERROR" (Printexc.to_string exn)
                     |> fun _ -> None)
                in
                (match expr_ast with
                 | None -> error_response "" "" "" "PARSE_ERROR" ("cannot parse: " ^ expr_str)
                 | Some expr_ast ->
                   let env = Yantra.new_env () in
                   let tnames = List.map (fun t -> Yantra.VString t.t_name) !(yantra_idx.all_tantras) in
                   Hashtbl.replace env "_tantra_index" (Yantra.VList tnames);
                   let result =
                     Yantra_eval.with_eval_ctx yantra_idx yantra_session
                       (fun () -> Yantra.eval k env expr_ast)
                       ~default:Yantra.VNone
                   in
                   let t1 = Unix.gettimeofday () in
                   let elapsed_ms = int_of_float ((t1 -. t0) *. 1000.0) in
                   let result_str = Yantra.as_string result in
                   let result_json = Yantra.val_to_json result in
                   if String.length result_str <= 200 then
                     Printf.printf "[eval] %s → %s (%dms)\n%!" expr_str result_str elapsed_ms;
                   if as_json then
                     Printf.sprintf
                       "{\"status\":\"ok\",\"command\":\"eval-json\",\"expr\":%s,\"result\":%s,\"elapsed_ms\":%d}"
                       (je expr_str) result_json elapsed_ms
                   else
                     eval_response expr_str result_str elapsed_ms)
          | Some "inspect-node" ->
            (* return one node with outgoing + incoming edges.
               request: {"command": "inspect-node", "name": "velocity"}
               response: {"status":"ok","name":"velocity","satya":...,"out_edges":[...],"in_edges":[...]} *)
            (match json_string_field line "name" with
             | None ->
               error_response "" "" "" "INVALID_REQUEST" "missing required field: name"
             | Some name ->
               (try inspect_node_response k name
                with exn ->
                  error_response "" "" "" "ENGINE_ERROR" (Printexc.to_string exn)))
          | Some "list-tantras" ->
            (* return names of all loaded tantras.
               request: {"command": "list-tantras"}
               response: {"status":"ok","count":N,"tantras":["avrti-refine",...]} *)
            (try list_tantras_response yantra_idx
             with exn ->
               error_response "" "" "" "ENGINE_ERROR" (Printexc.to_string exn))
          | Some "triples-of" ->
            (* return all triples where node appears as subject or object.
               request: {"command": "triples-of", "node": "velocity"}
               response: {"status":"ok","node":"velocity","triples":[[s,p,o],...]} *)
            (match json_string_field line "node" with
             | None ->
               error_response "" "" "" "INVALID_REQUEST" "missing required field: node"
             | Some name ->
               (try triples_of_response k name
                with exn ->
                  error_response "" "" "" "ENGINE_ERROR" (Printexc.to_string exn)))
          | Some "pipeline-trace" ->
            (* run avrti-refine stage-by-stage; return graph after each stage.
               request: {"command": "pipeline-trace", "sentence": "ball has mass m1 of 5"}
               response: {"status":"ok","stages":[{"stage":"sandhi-kosha","triples":[...]}, ...]} *)
            (match json_string_field line "sentence" with
             | None ->
               error_response "" "" "" "INVALID_REQUEST" "missing required field: sentence"
             | Some sentence ->
               (try pipeline_trace_response k yantra_idx yantra_session sentence
                with exn ->
                  error_response "" "" "" "ENGINE_ERROR" (Printexc.to_string exn)))
          | Some "mantra-status" ->
            (* show all mantras with janya coverage for a sentence.
               request: {"command": "mantra-status", "sentence": "ball has mass m1 of 5 and velocity v1 of 20"}
               response: {"status":"ok","refined_graph":[...],"bound_concepts":[...],"mantras":[...]} *)
            (match json_string_field line "sentence" with
             | None ->
               error_response "" "" "" "INVALID_REQUEST" "missing required field: sentence"
             | Some sentence ->
               (try mantra_status_response k yantra_idx yantra_session sentence
                with exn ->
                  error_response "" "" "" "ENGINE_ERROR" (Printexc.to_string exn)))
          | Some "attach" ->
            (* incrementally load one .om or .tantra file into the live graph.
               request: {"command": "attach", "path": "/abs/path/to/file.tantra"}
               response: {"status":"ok","command":"attach","kind":"tantra"|"om","name":...} *)
            (match json_string_field line "path" with
             | None ->
               error_response "" "" "" "INVALID_REQUEST" "missing required field: path"
             | Some path ->
               (try attach_file k yantra_idx path
                with exn ->
                  error_response "" "" "" "ATTACH_ERROR" (Printexc.to_string exn)))
          | Some "reload-all" ->
            (* re-read all tantra files from disk — picks up edits to existing tantras.
               request: {"command": "reload-all"}
               response: {"status":"ok","command":"reload-all","tantras_loaded":N} *)
            (try reload_tantras k yantra_idx dirs
             with exn ->
               error_response "" "" "" "RELOAD_ERROR" (Printexc.to_string exn))
          | Some "dump-ast" ->
            (* parse a tantra file and return its AST as JSON for external analysis.
               request:  {"command": "dump-ast", "path": "/abs/path/to/file.tantra2"}
               response: {"status":"ok","command":"dump-ast","tantra":{...ast...}}
               the "tantra" field is the full json_of_tantra serialization:
                 name, file, inputs, returns, bindings (list of {name, expr})
               each expr node has a "kind" discriminant for consumer pattern-matching.
               supports both .tantra (layer 1) and .tantra2 (layer 2) files. *)
            (match json_string_field line "path" with
             | None ->
               error_response "" "" "" "INVALID_REQUEST" "missing required field: path"
             | Some path ->
               (try
                 let t_opt = Yantra_tantra_file2.parse_tantra2_file path in
                 (match t_opt with
                  | None ->
                    error_response "" "" "" "PARSE_ERROR"
                      (Printf.sprintf "could not parse tantra file: %s" path)
                  | Some t ->
                    Printf.sprintf
                      "{\"status\":\"ok\",\"command\":\"dump-ast\",\"tantra\":%s}"
                      (Yantra_types.json_of_tantra t))
                with exn ->
                  error_response "" "" "" "PARSE_ERROR" (Printexc.to_string exn)))
           | Some "dump-om" ->
            (* parse an .om file and return its nigamana as JSON.
               request:  {"command": "dump-om", "path": "/abs/path/to/file.om"}
               response: {"status":"ok","command":"dump-om","nigamana":{name,layer,satya,slokas,edges,shabda}}
               uses the live graph's known_names for sloka decomposition. *)
            (match json_string_field line "path" with
             | None ->
               error_response "" "" "" "INVALID_REQUEST" "missing required field: path"
             | Some path ->
               (try
                 let known_names = Hashtbl.fold (fun name _ acc -> name :: acc) k.nodes [] in
                 let n_opt = Om_parser.parse_file known_names path in
                 (match n_opt with
                  | None ->
                    error_response "" "" "" "PARSE_ERROR"
                      (Printf.sprintf "could not parse om file: %s" path)
                  | Some n ->
                    Printf.sprintf
                      "{\"status\":\"ok\",\"command\":\"dump-om\",\"nigamana\":%s}"
                      (Proof_graph.json_of_nigamana n))
                with exn ->
                  error_response "" "" "" "PARSE_ERROR" (Printexc.to_string exn)))
           | Some "end-session" ->
             (* explicit session teardown — clears session state from store *)
             let ses_id = opt_field line "session_id" in
             if ses_id <> "" then Hashtbl.remove session_store ses_id;
             "{\"status\":\"ok\",\"command\":\"end-session\"}"

          (* ---- surgical edit commands ---- *)
          | Some "create-node" | Some "delete-node"
          | Some "add-sloka" | Some "remove-sloka"
          | Some "set-shabda"
          | Some "add-edge" | Some "remove-edge"
          | Some "set-comment" | Some "remove-comment" | Some "add-comment"
          | Some "add-shabda-entry" | Some "remove-shabda-entry" | Some "update-shabda-entry"
          | Some "write-tantra" ->
            (try handle_edit_command k yantra_idx dirs line (Option.get command)
             with exn ->
               error_response "" "" "" "EDIT_ERROR" (Printexc.to_string exn))
           | _ ->
             let req_id     = opt_field line "request_id" in
             let ses_id     = opt_field line "session_id" in
             let trn_id     = opt_field line "turn_id" in
            let question   = json_string_field line "question" in
            let max_passes = json_int_field line "max_passes" in
            (* resolve per-session yantra context when session_id is present *)
            let (_active_session, _prior_graph, _has_session) =
              if ses_id <> "" then
                let entry = get_or_create_session ses_id in
                entry.se_turn    <- entry.se_turn + 1;
                entry.se_turn_id <- Printf.sprintf "prashna-%d" entry.se_turn;
                (match entry.se_turn with
                | 1 -> Printf.printf "[session %s / %s]\n%!" ses_id entry.se_turn_id
                | n -> Printf.printf "[session %s / %s ← parampara: prashna-%d]\n%!"
                         ses_id entry.se_turn_id (n - 1));
                (* build prior_graph from session bindings accumulated by session-anuvada *)
                let prior = List.map (fun b ->
                  (b.Yantra_types.b_name, "sankhya",
                   string_of_float b.Yantra_types.b_value)
                ) entry.se_yantra.Yantra_types.bindings in
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
                      Yantra.run_session_anuvada k yantra_idx _active_session _prior_graph q
                    else
                      Yantra.run_anuvada_ganana k yantra_idx _active_session q
                  in
                  (match run_result with
                   | Some r ->
                     if String.length r.Yantra.yr_raw_output > 0 then
                       Printf.printf "[socket] %s\n  %s\n%!" q r.Yantra.yr_raw_output;
                     ok_response req_id ses_id trn_id r.Yantra.yr_raw_output
                   | None ->
                     error_response req_id ses_id trn_id
                       "ENGINE_ERROR" "session-anuvada or anuvada-ganana tantra not loaded")
                with exn ->
                  error_response req_id ses_id trn_id
                    "ENGINE_ERROR" (Printexc.to_string exn)))
        in
        output_string oc resp;
        output_char oc '\n';
        flush oc
      end
    done
  with End_of_file | Sys_error _ -> ())

(* ---- main server loop ---- *)

let serve (k : proof_graph) (yantra_idx : tantra_index) (yantra_session : session)
    (dirs : string list) (socket_path : string) : unit =
  (* remove stale socket *)
  (try Unix.unlink socket_path with Unix.Unix_error _ -> ());
  let sock = Unix.socket Unix.PF_UNIX Unix.SOCK_STREAM 0 in
  Unix.bind sock (Unix.ADDR_UNIX socket_path);
  Unix.listen sock 16;
  Printf.printf "vyakarana socket listening: %s\n%!" socket_path;
  (* accept loop — sequential: one client at a time per session *)
  while true do
    let (client, _) = Unix.accept sock in
    let ic = Unix.in_channel_of_descr client in
    let oc = Unix.out_channel_of_descr client in
    (try handle_client k yantra_idx yantra_session dirs ic oc
     with exn ->
       Printf.eprintf "client error: %s\n%!" (Printexc.to_string exn));
    (try Unix.close client with Unix.Unix_error _ -> ())
  done
