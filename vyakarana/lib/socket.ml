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

(* ---- response builders ---- *)

let steps_json (pass_groups : (int * Anuvada.anuvada_triple list) list) : string =
  let buf = Buffer.create 256 in
  Buffer.add_char buf '[';
  let all_steps = List.concat_map (fun (pass_num, triples) ->
    (* group triples by domain presence for kind field *)
    List.map (fun t ->
      let kind = if pass_num = 1 then "pure_domain" else "nature_equiv" in
      let text = Printf.sprintf "%s %s %s"
        t.Anuvada.a_source
        (string_of_visheshanam t.Anuvada.a_relation)
        (String.concat ", " t.Anuvada.a_targets) in
      (pass_num, kind, text)
    ) triples
  ) pass_groups in
  List.iteri (fun i (pass_num, kind, text) ->
    Buffer.add_string buf
      (Printf.sprintf "{\"pass\":%d,\"kind\":%s,\"text\":%s}"
        pass_num (je kind) (je text));
    if i < List.length all_steps - 1 then Buffer.add_char buf ','
  ) all_steps;
  Buffer.add_char buf ']';
  Buffer.contents buf

let graph_delta_json (r : Anuvada.query_result) : string =
  let nodes = List.map je r.Anuvada.qr_content_words in
  let edges = List.concat_map (fun (_, triples) ->
    List.concat_map (fun t ->
      List.map (fun tgt ->
        Printf.sprintf "{\"source\":%s,\"relation\":%s,\"target\":%s}"
          (je t.Anuvada.a_source_raw)
          (je (string_of_visheshanam t.Anuvada.a_relation))
          (je tgt)
      ) t.Anuvada.a_targets_raw
    ) triples
  ) r.Anuvada.qr_steps in
  Printf.sprintf "{\"nodes_activated\":[%s],\"edges_activated\":[%s]}"
    (String.concat "," nodes)
    (String.concat "," edges)

let ok_response (req_id : string) (ses_id : string) (trn_id : string)
    (r : Anuvada.query_result) (flags : Anuvada.output_flags) : string =
  let buf = Buffer.create 512 in
  Buffer.add_string buf
    (Printf.sprintf
      "{\"schema_version\":\"1.0\",\"request_id\":%s,\"session_id\":%s,\"turn_id\":%s,\
\"status\":\"ok\",\"answer_text\":%s,\"steps\":%s,\"next_questions\":[%s],\
\"graph_delta\":%s"
      (je req_id) (je ses_id) (je trn_id)
      (je r.Anuvada.qr_answer_text)
      (steps_json r.Anuvada.qr_steps)
      (String.concat "," (List.map je r.Anuvada.qr_next_qs))
      (graph_delta_json r));
  if flags.Anuvada.show_music then
    Buffer.add_string buf (Printf.sprintf ",\"music_ir\":%s" r.Anuvada.qr_music_ir);
  if flags.Anuvada.show_resonance then
    Buffer.add_string buf (Printf.sprintf ",\"resonance_ir\":%s" r.Anuvada.qr_resonance_ir);
  if flags.Anuvada.show_strudel then
    Buffer.add_string buf (Printf.sprintf ",\"assets\":{\"strudel\":%s}" (je r.Anuvada.qr_strudel));
  Buffer.add_string buf
    (Printf.sprintf ",\"diagnostics\":{\"passes\":%d,\"connections\":%d,\"confidence_top\":%.4f}}"
      r.Anuvada.qr_passes
      r.Anuvada.qr_connections
      r.Anuvada.qr_confidence);
  Buffer.contents buf

let error_response (req_id : string) (ses_id : string) (trn_id : string)
    (code : string) (msg : string) (retryable : bool) : string =
  Printf.sprintf
    "{\"schema_version\":\"1.0\",\"request_id\":%s,\"session_id\":%s,\"turn_id\":%s,\
\"status\":\"error\",\"error\":{\"code\":%s,\"message\":%s,\"retryable\":%s},\
\"diagnostics\":{}}"
    (je req_id) (je ses_id) (je trn_id)
    (je code) (je msg) (if retryable then "true" else "false")

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

(* ---- handle one client connection ---- *)

let handle_client (k : proof_graph) (ic : in_channel) (oc : out_channel) : unit =
  (try
    while true do
      let line = input_line ic in
      let line = String.trim line in
      if String.length line = 0 then ()
      else begin
        let command = json_string_field line "command" in
        let resp = match command with
          | Some "graph" ->
            (* return full proof graph as pravaha JSON — used by engine:graph() Lua binding *)
            (try graph_response k
             with exn ->
               error_response "" "" "" "ENGINE_ERROR" (Printexc.to_string exn) true)
          | _ ->
            let req_id  = Option.value ~default:"" (json_string_field line "request_id") in
            let ses_id  = Option.value ~default:"" (json_string_field line "session_id") in
            let trn_id  = Option.value ~default:"" (json_string_field line "turn_id") in
            let question = json_string_field line "question" in
            let show_str = json_string_field line "show" in
            let max_passes = json_int_field line "max_passes" in
            let thaalam = json_string_field line "thaalam" in
            let sahaja  = Option.value ~default:true (json_bool_field line "sahaja") in
            (match question with
              | None ->
                error_response req_id ses_id trn_id
                  "INVALID_REQUEST" "missing required field: question" false
              | Some q when String.trim q = "" ->
                error_response req_id ses_id trn_id
                  "INVALID_REQUEST" "question must not be empty" false
              | Some q ->
                (try
                  let base_flags = match show_str with
                    | Some s -> Anuvada.flags_of_show_string s
                    | None   -> Anuvada.flags_default
                  in
                  let (clean_q, flags) = Anuvada.parse_inline_flags ~base:base_flags q in
                  let r = Anuvada.anuvada_query
                    ~max_passes:(Option.value ~default:2 max_passes)
                    ?thaalam
                    ~sahaja
                    ~request_id:req_id
                    ~session_id:ses_id
                    ~turn_id:trn_id
                    k clean_q in
                  (* echo answer to terminal so human sees it alongside LLM *)
                  if String.length r.Anuvada.qr_answer_text > 0 then
                    Printf.printf "[socket] %s\n  %s\n%!"
                      q r.Anuvada.qr_answer_text;
                  ok_response req_id ses_id trn_id r flags
                with exn ->
                  error_response req_id ses_id trn_id
                    "ENGINE_ERROR" (Printexc.to_string exn) true))
        in
        output_string oc resp;
        output_char oc '\n';
        flush oc
      end
    done
  with End_of_file | Sys_error _ -> ())

(* ---- main server loop ---- *)

let serve (k : proof_graph) (socket_path : string) : unit =
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
    (try handle_client k ic oc
     with exn ->
       Printf.eprintf "client error: %s\n%!" (Printexc.to_string exn));
    (try Unix.close client with Unix.Unix_error _ -> ())
  done
