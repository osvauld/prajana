(* karma.ml — om5 parser + editor + file I/O.
   consolidates om5_parser.ml (181L) + om_edit.ml (186L) + om_writer.ml (269L).
   uses Prakriti.dir_walk and Prakriti.read_file (no local copies).

   sections:
     1. om5 parser — tokenize + parse .om5 s-expression files
     2. file writer — surgical .om/.shabda/.tantra file I/O
     3. editor — combined disk + graph operations *)

open Prakriti

(* ═══════════════════════════════════════════════════════════════════════════
   1. OM5 PARSER
   ═══════════════════════════════════════════════════════════════════════════ *)

let tokenize = Vakya.tokenize_sexp

let parse_edge_group (source : string) (tokens : string list)
    : typed_edge list * string list =
  match tokens with
  | [] -> ([], [])
  | rel_name :: rest ->
    let rel = visheshanam_of_string rel_name in
    let rec collect acc toks =
      match toks with
      | ")" :: rest' -> (List.rev acc, rest')
      | [] -> (List.rev acc, [])
      | t :: rest' -> collect (t :: acc) rest'
    in
    let (targets, remaining) = collect [] rest in
    match rel with
    | None -> ([], remaining)
    | Some v ->
      let edges = List.map (fun target ->
        { source; target; relation = v }
      ) targets in
      (edges, remaining)

let is_layer_keyword s =
  s = "sangati" || s = "kosha" || s = "bhasha" || s = "mantra"

(* Parse one (layer name ...) block from tokens. Returns (node, remaining_tokens).
   Handles inline (mantra name ...) by extracting as separate nodes. *)
let parse_one_node (tokens : string list) : (nigamana list * string list) =
  match tokens with
  | "(" :: layer_str :: name :: rest when is_layer_keyword layer_str ->
    let all_edges = ref [] in
    let krama_expr = ref "" in
    let domain_str = ref "" in
    let inline_nodes = ref [] in
    let remaining_after = ref [] in
    let rec parse_body toks =
      match toks with
      | [] -> ()
      | ")" :: rest -> remaining_after := rest
      | "(" :: "domain" :: dpath :: ")" :: rest ->
        domain_str := dpath;
        parse_body rest
      | "(" :: "krama" :: rest ->
        let depth = ref 1 in
        let expr_toks = ref [] in
        let remaining = ref rest in
        while !depth > 0 && !remaining <> [] do
          match !remaining with
          | "(" :: tl -> incr depth; expr_toks := "(" :: !expr_toks; remaining := tl
          | ")" :: tl -> decr depth;
            if !depth > 0 then expr_toks := ")" :: !expr_toks;
            remaining := tl
          | t :: tl -> expr_toks := t :: !expr_toks; remaining := tl
          | [] -> ()
        done;
        krama_expr := String.concat " " (List.rev !expr_toks);
        parse_body !remaining
      | "(" :: "mantra" :: mantra_name :: mantra_rest ->
        (* Inline mantra: extract as separate mantra-layer node *)
        let mantra_edges = ref [] in
        let mantra_krama = ref "" in
        let rec parse_mantra_body mtoks =
          match mtoks with
          | [] -> ()
          | ")" :: mrest -> remaining_after := mrest;
              (* continue parsing parent body *)
              parse_body mrest
          | "(" :: "krama" :: krest ->
            let depth = ref 1 in
            let expr_toks = ref [] in
            let rem = ref krest in
            while !depth > 0 && !rem <> [] do
              match !rem with
              | "(" :: tl -> incr depth; expr_toks := "(" :: !expr_toks; rem := tl
              | ")" :: tl -> decr depth;
                if !depth > 0 then expr_toks := ")" :: !expr_toks;
                rem := tl
              | t :: tl -> expr_toks := t :: !expr_toks; rem := tl
              | [] -> ()
            done;
            mantra_krama := String.concat " " (List.rev !expr_toks);
            parse_mantra_body !rem
          | "(" :: mrest ->
            let (edges, mrem) = parse_edge_group mantra_name mrest in
            mantra_edges := edges @ !mantra_edges;
            parse_mantra_body mrem
          | _ :: mrest -> parse_mantra_body mrest
        in
        parse_mantra_body mantra_rest;
        (* Auto-add swarupa→parent and phala→parent edges if not present *)
        let swarupa_dim = match visheshanam_of_string "swarupa" with
          | Some d -> d | None -> register_dimension "swarupa" in
        let phala_dim = match visheshanam_of_string "phala" with
          | Some d -> d | None -> register_dimension "phala" in
        let has_swarupa = List.exists (fun e ->
          e.relation = swarupa_dim) !mantra_edges in
        let has_phala = List.exists (fun e ->
          e.relation = phala_dim) !mantra_edges in
        if not has_swarupa then
          mantra_edges := { source = mantra_name; target = name;
                           relation = swarupa_dim } :: !mantra_edges;
        if not has_phala then
          mantra_edges := { source = mantra_name; target = name;
                           relation = phala_dim } :: !mantra_edges;
        let mantra_node = {
          name = mantra_name; layer = "mantra"; domain = !domain_str;
          slokas = [];
          edges = List.rev !mantra_edges;
          satya = 0.0; shabda = ""; krama = !mantra_krama;
        } in
        inline_nodes := mantra_node :: !inline_nodes
      | "(" :: rest ->
        let (edges, remaining) = parse_edge_group name rest in
        all_edges := edges @ !all_edges;
        parse_body remaining
      | _ :: rest ->
        parse_body rest
    in
    parse_body rest;
    let main_node = {
      name; layer = layer_str; domain = !domain_str;
      slokas = [];
      edges = List.rev !all_edges;
      satya = 0.0; shabda = ""; krama = !krama_expr;
    } in
    (main_node :: List.rev !inline_nodes, !remaining_after)
  | _ -> ([], tokens)

(* Parse all (layer name ...) blocks from a token stream. *)
let parse_om5_tokens_multi (tokens : string list) : nigamana list =
  let results = ref [] in
  let remaining = ref tokens in
  let safety = ref 0 in
  while !remaining <> [] && !safety < 1000 do
    incr safety;
    match !remaining with
    | "(" :: layer :: _ :: _ when is_layer_keyword layer ->
      let (nodes, rest) = parse_one_node !remaining in
      results := !results @ nodes;
      remaining := rest
    | _ :: rest -> remaining := rest
    | [] -> ()
  done;
  !results

(* Backward compat: parse first node only *)
let parse_om5_tokens (tokens : string list) : nigamana option =
  match parse_om5_tokens_multi tokens with
  | n :: _ -> Some n
  | [] -> None

let parse_file_multi (path : string) : nigamana list =
  try
    let ic = open_in path in
    let buf = Buffer.create 1024 in
    (try while true do
      Buffer.add_string buf (input_line ic);
      Buffer.add_char buf '\n'
    done with End_of_file -> ());
    close_in ic;
    let tokens = tokenize (Buffer.contents buf) in
    parse_om5_tokens_multi tokens
  with _ -> []

let parse_file (path : string) : nigamana option =
  match parse_file_multi path with
  | n :: _ -> Some n
  | [] -> None

let om5_files_recursive (root : string) : string list =
  dir_walk root ".om5"

let collect_dynamic_dims_from_ring (dirs : string list) (_known_names : string list) : string list =
  let dims = ref [] in
  List.iter (fun dir ->
    List.iter (fun path ->
      List.iter (fun n ->
        if n.name = "visheshanam-ring" then begin
          let yukta_idx = visheshanam_of_string "yukta" in
          List.iter (fun e ->
            if e.source = "visheshanam-ring" then
              match yukta_idx with
              | Some yi when e.relation = yi ->
                let target = e.target in
                if not (String.length target > 13
                        && String.sub target 0 13 = "visheshanam-")
                   && visheshanam_of_string target = None then
                  dims := target :: !dims
              | _ -> ()
          ) n.edges
        end
      ) (parse_file_multi path)
    ) (om5_files_recursive dir)
  ) dirs;
  !dims

let collect_names (dir : string) : string list =
  let names = ref [] in
  List.iter (fun path ->
    try
      let ic = open_in path in
      let buf = Buffer.create 256 in
      (try for _ = 1 to 5 do
        Buffer.add_string buf (input_line ic);
        Buffer.add_char buf '\n'
      done with End_of_file -> ());
      close_in ic;
      let tokens = tokenize (Buffer.contents buf) in
      (match tokens with
       | "(" :: layer :: name :: _
         when layer = "sangati" || layer = "kosha"
           || layer = "bhasha" || layer = "mantra" ->
         names := name :: !names
       | _ -> ())
    with _ -> ()
  ) (om5_files_recursive dir);
  !names

(* ═══════════════════════════════════════════════════════════════════════════
   2. FILE WRITER — surgical .om/.shabda/.tantra file I/O
   ═══════════════════════════════════════════════════════════════════════════ *)

let write_lines (path : string) (lines : string list) : unit =
  let dir = Filename.dirname path in
  if not (Sys.file_exists dir) then begin
    let rec mkdir_p d =
      if Sys.file_exists d then ()
      else begin mkdir_p (Filename.dirname d); Unix.mkdir d 0o755 end
    in
    mkdir_p dir
  end;
  let oc = open_out path in
  List.iter (fun line -> output_string oc line; output_char oc '\n') lines;
  close_out oc

let comment_prefixes = ["desc"; "not"; "example"; "usage"; "see"; "math"]

let parse_comment_line (line : string) : (string option * string) option =
  let trimmed = String.trim line in
  if String.length trimmed >= 2 && trimmed.[0] = '-' && trimmed.[1] = '-' then
    let rest = String.trim (String.sub trimmed 2 (String.length trimmed - 2)) in
    let found = List.fold_left (fun acc prefix ->
      match acc with
      | Some _ -> acc
      | None ->
        let plen = String.length prefix in
        if String.length rest > plen + 1
           && String.sub rest 0 plen = prefix
           && rest.[plen] = ':' then
          let text = String.trim (String.sub rest (plen + 1) (String.length rest - plen - 1)) in
          Some (Some prefix, text)
        else None
    ) None comment_prefixes in
    (match found with Some r -> Some r | None -> Some (None, rest))
  else None

let create_om5 (path : string) (layer : string) (name : string)
    (comments : string list)
    (edges : (string * string list) list) : unit =
  let lines = ref [] in
  (* comments as ; lines before the node *)
  List.iter (fun c -> lines := (Printf.sprintf "; %s" c) :: !lines) comments;
  if comments <> [] then lines := "" :: !lines;
  (* opening: (layer name *)
  lines := (Printf.sprintf "(%s %s" layer name) :: !lines;
  (* edge groups: (relation target1 target2 ...) *)
  List.iter (fun (rel, targets) ->
    if targets <> [] then
      lines := (Printf.sprintf "  (%s %s)" rel (String.concat " " targets)) :: !lines
  ) edges;
  (* closing paren *)
  lines := ")" :: !lines;
  write_lines path (List.rev !lines)

let add_sloka (path : string) (sloka : string) : unit =
  let lines = read_file path in
  let inserted = ref false in
  let result = List.fold_right (fun line acc ->
    let trimmed = String.trim line in
    if not !inserted
       && (trimmed = "done"
           || (String.length trimmed > 6 && String.sub trimmed 0 6 = "shabda")) then begin
      inserted := true;
      line :: (Printf.sprintf "  \"%s\"" sloka) :: acc
    end else line :: acc
  ) lines [] in
  write_lines path result

let remove_sloka (path : string) (sloka : string) : unit =
  let lines = read_file path in
  let target = Printf.sprintf "\"%s\"" sloka in
  let result = List.filter (fun line -> String.trim line <> target) lines in
  write_lines path result

let set_shabda (path : string) (shabda : string) : unit =
  let lines = read_file path in
  let had_shabda = ref false in
  let result = List.fold_right (fun line acc ->
    let trimmed = String.trim line in
    if String.length trimmed > 6 && String.sub trimmed 0 6 = "shabda" then begin
      had_shabda := true;
      if shabda = "" then acc
      else (Printf.sprintf "shabda %s" shabda) :: acc
    end else if trimmed = "done" && not !had_shabda && shabda <> "" then begin
      had_shabda := true;
      (Printf.sprintf "shabda %s" shabda) :: line :: acc
    end else line :: acc
  ) lines [] in
  write_lines path result

let set_comment (path : string) (prefix : string) (text : string) : unit =
  let lines = read_file path in
  let filtered = List.filter (fun line ->
    match parse_comment_line line with
    | Some (Some p, _) when p = prefix -> false | _ -> true
  ) lines in
  let new_line = Printf.sprintf "  -- %s: %s" prefix text in
  let inserted = ref false in
  let result = List.fold_left (fun acc line ->
    if !inserted then acc @ [line]
    else begin
      let trimmed = String.trim line in
      if (String.length trimmed >= 1 && trimmed.[0] = '"')
         || trimmed = "done"
         || (String.length trimmed >= 6 && String.sub trimmed 0 6 = "shabda") then begin
        inserted := true; acc @ [new_line] @ [line]
      end else acc @ [line]
    end
  ) [] filtered in
  let result = if not !inserted then result @ [new_line] else result in
  write_lines path result

let remove_comment (path : string) (prefix : string) : unit =
  let lines = read_file path in
  let result = List.filter (fun line ->
    match parse_comment_line line with
    | Some (Some p, _) when p = prefix -> false | _ -> true
  ) lines in
  write_lines path result

let add_freeform_comment (path : string) (text : string) : unit =
  let lines = read_file path in
  let new_line = Printf.sprintf "  -- %s" text in
  let inserted = ref false in
  let result = List.fold_left (fun acc line ->
    if !inserted then acc @ [line]
    else begin
      let trimmed = String.trim line in
      if (String.length trimmed >= 1 && trimmed.[0] = '"')
         || trimmed = "done"
         || (String.length trimmed >= 6 && String.sub trimmed 0 6 = "shabda") then begin
        inserted := true; acc @ [new_line] @ [line]
      end else acc @ [line]
    end
  ) [] lines in
  let result = if not !inserted then result @ [new_line] else result in
  write_lines path result

let delete_file (path : string) : unit =
  if Sys.file_exists path then Sys.remove path

let add_shabda_entry (path : string) (word : string)
    (abheda : string list) (yukta : string list) : unit =
  let entry =
    let base = word ^ ": " ^ String.concat " " abheda in
    if yukta = [] then base else base ^ " | " ^ String.concat " " yukta
  in
  let lines = if Sys.file_exists path then read_file path else [] in
  write_lines path (lines @ [entry])

let remove_shabda_entry (path : string) (word : string) : unit =
  let lines = read_file path in
  let prefix = word ^ ":" in
  let result = List.filter (fun line ->
    let trimmed = String.trim line in
    not (String.length trimmed >= String.length prefix
         && String.sub trimmed 0 (String.length prefix) = prefix)
  ) lines in
  write_lines path result

let update_shabda_entry (path : string) (word : string)
    (abheda : string list) (yukta : string list) : unit =
  remove_shabda_entry path word;
  add_shabda_entry path word abheda yukta

let write_tantra (path : string) (source : string) : unit =
  let oc = open_out path in
  output_string oc source;
  close_out oc

(* ═══════════════════════════════════════════════════════════════════════════
   3. EDITOR — combined disk + graph operations
   ═══════════════════════════════════════════════════════════════════════════ *)

type edit_result =
  | Ok of string
  | Err of string

let reparse_and_replace (k : proof_graph) (path : string) : edit_result =
  match parse_file path with
  | None -> Err (Printf.sprintf "re-parse failed: %s" path)
  | Some n ->
    replace_node k n;
    init_satya k;
    materialize_csr k;
    Ok n.name

let path_of_node (k : proof_graph) (name : string) : string option =
  let dirs = !(k.search_dirs) in
  let rec find_in_dirs = function
    | [] -> None
    | dir :: rest ->
      let files = om5_files_recursive dir in
      let found = List.fold_left (fun acc path ->
        match acc with
        | Some _ -> acc
        | None ->
          (try
            match parse_file path with
            | Some n when n.name = name -> Some path
            | _ -> None
          with _ -> None)
      ) None files in
      (match found with Some p -> Some p | None -> find_in_dirs rest)
  in
  find_in_dirs dirs

let create_node (k : proof_graph) (path : string) (layer : string) (name : string)
    (comments : string list)
    (edges : (string * string list) list) : edit_result =
  if Sys.file_exists path then
    Err (Printf.sprintf "file already exists: %s" path)
  else if Hashtbl.mem k.nodes name then
    Err (Printf.sprintf "node already exists in graph: %s" name)
  else begin
    create_om5 path layer name comments edges;
    reparse_and_replace k path
  end

let edit_add_sloka (k : proof_graph) (name : string) (sloka : string) : edit_result =
  match path_of_node k name with
  | None -> Err (Printf.sprintf "node not found: %s" name)
  | Some path -> add_sloka path sloka; reparse_and_replace k path

let edit_remove_sloka (k : proof_graph) (name : string) (sloka : string) : edit_result =
  match path_of_node k name with
  | None -> Err (Printf.sprintf "node not found: %s" name)
  | Some path -> remove_sloka path sloka; reparse_and_replace k path

let edit_set_shabda (k : proof_graph) (name : string) (shabda : string) : edit_result =
  match path_of_node k name with
  | None -> Err (Printf.sprintf "node not found: %s" name)
  | Some path -> set_shabda path shabda; reparse_and_replace k path

let delete_node (k : proof_graph) (name : string) : edit_result =
  match path_of_node k name with
  | None -> Err (Printf.sprintf "node not found: %s" name)
  | Some path ->
    delete_file path;
    remove_node k name;
    init_satya k;
    materialize_csr k;
    Ok name

let add_edge (k : proof_graph) (source : string) (target : string)
    (relation : string) : edit_result =
  match path_of_node k source with
  | None -> Err (Printf.sprintf "source node not found: %s" source)
  | Some path ->
    add_sloka path (Printf.sprintf "%s-%s" target relation);
    reparse_and_replace k path

let remove_edge (k : proof_graph) (source : string) (target : string)
    (relation : string) : edit_result =
  match path_of_node k source with
  | None -> Err (Printf.sprintf "source node not found: %s" source)
  | Some path ->
    remove_sloka path (Printf.sprintf "%s-%s" target relation);
    reparse_and_replace k path

let edit_set_comment (k : proof_graph) (name : string) (prefix : string)
    (text : string) : edit_result =
  match path_of_node k name with
  | None -> Err (Printf.sprintf "node not found: %s" name)
  | Some path -> set_comment path prefix text; Ok name

let edit_remove_comment (k : proof_graph) (name : string) (prefix : string) : edit_result =
  match path_of_node k name with
  | None -> Err (Printf.sprintf "node not found: %s" name)
  | Some path -> remove_comment path prefix; Ok name

let edit_add_comment (k : proof_graph) (name : string) (text : string) : edit_result =
  match path_of_node k name with
  | None -> Err (Printf.sprintf "node not found: %s" name)
  | Some path -> add_freeform_comment path text; Ok name

let edit_add_shabda_entry (_k : proof_graph) (path : string) (word : string)
    (abheda : string list) (yukta : string list) : edit_result =
  add_shabda_entry path word abheda yukta; Ok word

let edit_remove_shabda_entry (_k : proof_graph) (path : string)
    (word : string) : edit_result =
  remove_shabda_entry path word; Ok word

let edit_update_shabda_entry (_k : proof_graph) (path : string) (word : string)
    (abheda : string list) (yukta : string list) : edit_result =
  update_shabda_entry path word abheda yukta; Ok word

let edit_write_tantra (_k : proof_graph) (path : string) (source : string) : edit_result =
  write_tantra path source; Ok path
