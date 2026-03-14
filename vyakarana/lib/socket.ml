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

(* ---- handle one client connection ---- *)

let handle_client (k : proof_graph) (yantra_idx : tantra_index) (yantra_session : session)
    (ic : in_channel) (oc : out_channel) : unit =
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
             let expr_str = Option.value ~default:"" (json_string_field line "expr") in
             if String.trim expr_str = "" then
               error_response "" "" "" "INVALID_REQUEST" "missing required field: expr"
             else
               (try
                 let t0 = Unix.gettimeofday () in
                 let expr = Yantra.parse_expr_string expr_str in
                 let env  = Yantra.new_env () in
                 let tnames = List.map (fun t -> Yantra.VString t.t_name)
                   !(yantra_idx.all_tantras) in
                 Hashtbl.replace env "_tantra_index" (Yantra.VList tnames);
                 Yantra.eval_ctx := Some { Yantra.ctx_index = yantra_idx; ctx_session = yantra_session };
                 let result = Yantra.eval k env expr in
                 Yantra.eval_ctx := None;
                 let t1 = Unix.gettimeofday () in
                 let elapsed_ms = int_of_float ((t1 -. t0) *. 1000.0) in
                 let result_str = Yantra.as_string result in
                 let result_json = Yantra.val_to_json result in
                 Printf.printf "[eval] %s → %s (%dms)\n%!" expr_str result_str elapsed_ms;
                 if as_json then
                   Printf.sprintf
                     "{\"status\":\"ok\",\"command\":\"eval-json\",\"expr\":%s,\"result\":%s,\"elapsed_ms\":%d}"
                     (je expr_str) result_json elapsed_ms
                 else
                   eval_response expr_str result_str elapsed_ms
               with exn ->
                 Yantra.eval_ctx := None;
                 error_response "" "" "" "ENGINE_ERROR" (Printexc.to_string exn))
          | Some "end-session" ->
            (* explicit session teardown — clears session state from store *)
            let ses_id = Option.value ~default:"" (json_string_field line "session_id") in
            if ses_id <> "" then Hashtbl.remove session_store ses_id;
            "{\"status\":\"ok\",\"command\":\"end-session\"}"
          | _ ->
            let req_id     = Option.value ~default:"" (json_string_field line "request_id") in
            let ses_id     = Option.value ~default:"" (json_string_field line "session_id") in
            let trn_id     = Option.value ~default:"" (json_string_field line "turn_id") in
            let question   = json_string_field line "question" in
            let max_passes = json_int_field line "max_passes" in
            (* resolve per-session yantra context when session_id is present *)
            let _active_session =
              if ses_id <> "" then
                let entry = get_or_create_session ses_id in
                entry.se_turn    <- entry.se_turn + 1;
                entry.se_turn_id <- Printf.sprintf "prashna-%d" entry.se_turn;
                (match entry.se_turn with
                | 1 -> Printf.printf "[session %s / %s]\n%!" ses_id entry.se_turn_id
                | n -> Printf.printf "[session %s / %s ← parampara: prashna-%d]\n%!"
                         ses_id entry.se_turn_id (n - 1));
                entry.se_yantra
              else yantra_session
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
                  let r = Anuvada.anuvada_query
                    ~max_passes:(Option.value ~default:2 max_passes)
                    ~request_id:req_id ~session_id:ses_id ~turn_id:trn_id
                    k q in
                  if String.length r.Anuvada.qr_answer_text > 0 then
                    Printf.printf "[socket] %s\n  %s\n%!" q r.Anuvada.qr_answer_text;
                  ok_response req_id ses_id trn_id r.Anuvada.qr_answer_text
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
    (socket_path : string) : unit =
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
    (try handle_client k yantra_idx yantra_session ic oc
     with exn ->
       Printf.eprintf "client error: %s\n%!" (Printexc.to_string exn));
    (try Unix.close client with Unix.Unix_error _ -> ())
  done
