(* om_writer.ml — surgical file I/O for .om, .shabda, and .tantra3 files.
   reads file, makes targeted edit, writes back.
   disk is the source of truth — graph is updated after.

   .om file format:
     <layer> <name>
       -- desc: what this node IS
       -- not: what it is NOT
       -- example: concrete instance
       -- usage: pipeline consumers
       -- see: cross-reference
       -- math: $E = mc^2$
       -- free-form comment
       "<sloka>"
       ...
     shabda <key:val ...>
     done

   comment prefixes: desc, not, example, usage, see, math
   any other -- line is free-form. *)

(* ---- helpers ---- *)

let read_file (path : string) : string list =
  let ic = open_in path in
  let lines = ref [] in
  (try while true do lines := input_line ic :: !lines done
   with End_of_file -> ());
  close_in ic;
  List.rev !lines

let write_lines (path : string) (lines : string list) : unit =
  let dir = Filename.dirname path in
  (* ensure parent directory exists *)
  if not (Sys.file_exists dir) then begin
    let rec mkdir_p d =
      if Sys.file_exists d then ()
      else begin mkdir_p (Filename.dirname d); Unix.mkdir d 0o755 end
    in
    mkdir_p dir
  end;
  let oc = open_out path in
  List.iter (fun line ->
    output_string oc line;
    output_char oc '\n'
  ) lines;
  close_out oc

(* comment prefix types *)
let comment_prefixes = ["desc"; "not"; "example"; "usage"; "see"; "math"]

(* parse a comment line into (prefix option, text) *)
let parse_comment_line (line : string) : (string option * string) option =
  let trimmed = String.trim line in
  if String.length trimmed >= 2
     && trimmed.[0] = '-' && trimmed.[1] = '-' then
    let rest = String.trim (String.sub trimmed 2 (String.length trimmed - 2)) in
    (* check for typed prefix *)
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
        else
          None
    ) None comment_prefixes in
    (match found with
     | Some r -> Some r
     | None -> Some (None, rest))
  else
    None

(* is this a continuation comment line (-- followed by whitespace-indented text, no prefix)? *)
let is_continuation_comment (line : string) : bool =
  let trimmed = String.trim line in
  String.length trimmed >= 4
  && trimmed.[0] = '-' && trimmed.[1] = '-'
  && trimmed.[2] = ' ' && trimmed.[3] = ' '
  && (match parse_comment_line line with
      | Some (None, _) -> true
      | _ -> false)

(* ---- .om file operations ---- *)

(* create a new .om file *)
let create_om (path : string) (layer : string) (name : string)
    (comments : (string option * string) list)
    (slokas : string list) (shabda : string) : unit =
  let lines = ref [] in
  lines := [Printf.sprintf "%s %s" layer name; ""];
  (* comments *)
  List.iter (fun (prefix, text) ->
    let line = match prefix with
      | Some p -> Printf.sprintf "  -- %s: %s" p text
      | None   -> Printf.sprintf "  -- %s" text
    in
    lines := line :: !lines
  ) comments;
  if comments <> [] then lines := "" :: !lines;
  (* slokas *)
  List.iter (fun s ->
    lines := (Printf.sprintf "  \"%s\"" s) :: !lines
  ) slokas;
  (* shabda *)
  if shabda <> "" then
    lines := (Printf.sprintf "shabda %s" shabda) :: !lines;
  (* done *)
  lines := "done" :: !lines;
  write_lines path (List.rev !lines)

(* add a sloka to an existing .om file — inserts before shabda/done *)
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
    end else
      line :: acc
  ) lines [] in
  write_lines path result

(* remove a sloka from an existing .om file *)
let remove_sloka (path : string) (sloka : string) : unit =
  let lines = read_file path in
  let target = Printf.sprintf "\"%s\"" sloka in
  let result = List.filter (fun line ->
    let trimmed = String.trim line in
    trimmed <> target
  ) lines in
  write_lines path result

(* set the shabda line in an .om file — replace existing or insert before done *)
let set_shabda (path : string) (shabda : string) : unit =
  let lines = read_file path in
  let had_shabda = ref false in
  let result = List.fold_right (fun line acc ->
    let trimmed = String.trim line in
    if String.length trimmed > 6 && String.sub trimmed 0 6 = "shabda" then begin
      had_shabda := true;
      if shabda = "" then acc  (* remove shabda line *)
      else (Printf.sprintf "shabda %s" shabda) :: acc
    end else if trimmed = "done" && not !had_shabda && shabda <> "" then begin
      had_shabda := true;
      (Printf.sprintf "shabda %s" shabda) :: line :: acc
    end else
      line :: acc
  ) lines [] in
  write_lines path result

(* set a typed comment (desc, not, example, usage, see, math).
   replaces existing comment block with that prefix, or adds after header. *)
let set_comment (path : string) (prefix : string) (text : string) : unit =
  let lines = read_file path in
  (* remove existing lines with this prefix *)
  let filtered = List.filter (fun line ->
    match parse_comment_line line with
    | Some (Some p, _) when p = prefix -> false
    | _ -> true
  ) lines in
  (* find insertion point: after header line and existing comments *)
  let new_line = Printf.sprintf "  -- %s: %s" prefix text in
  let inserted = ref false in
  let result = List.fold_left (fun acc line ->
    if !inserted then acc @ [line]
    else begin
      let trimmed = String.trim line in
      (* insert before first sloka or shabda or done *)
      if (String.length trimmed >= 1 && trimmed.[0] = '"')
         || trimmed = "done"
         || (String.length trimmed >= 6 && String.sub trimmed 0 6 = "shabda") then begin
        inserted := true;
        acc @ [new_line] @ [line]
      end else
        acc @ [line]
    end
  ) [] filtered in
  let result = if not !inserted then result @ [new_line] else result in
  write_lines path result

(* remove a typed comment by prefix *)
let remove_comment (path : string) (prefix : string) : unit =
  let lines = read_file path in
  let result = List.filter (fun line ->
    match parse_comment_line line with
    | Some (Some p, _) when p = prefix -> false
    | _ -> true
  ) lines in
  write_lines path result

(* add a free-form comment *)
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
        inserted := true;
        acc @ [new_line] @ [line]
      end else
        acc @ [line]
    end
  ) [] lines in
  let result = if not !inserted then result @ [new_line] else result in
  write_lines path result

(* delete a file from disk *)
let delete_file (path : string) : unit =
  if Sys.file_exists path then Sys.remove path

(* ---- .shabda file operations ---- *)

(* format: one entry per line
   # comment line
   word: abheda1 abheda2 | yukta1 yukta2 *)

(* add an entry to a .shabda file (creates file if needed) *)
let add_shabda_entry (path : string) (word : string)
    (abheda : string list) (yukta : string list) : unit =
  let entry =
    let base = word ^ ": " ^ String.concat " " abheda in
    if yukta = [] then base
    else base ^ " | " ^ String.concat " " yukta
  in
  let lines =
    if Sys.file_exists path then read_file path
    else []
  in
  write_lines path (lines @ [entry])

(* remove an entry from a .shabda file by word *)
let remove_shabda_entry (path : string) (word : string) : unit =
  let lines = read_file path in
  let prefix = word ^ ":" in
  let result = List.filter (fun line ->
    let trimmed = String.trim line in
    not (String.length trimmed >= String.length prefix
         && String.sub trimmed 0 (String.length prefix) = prefix)
  ) lines in
  write_lines path result

(* update an entry in a .shabda file — remove old, add new *)
let update_shabda_entry (path : string) (word : string)
    (abheda : string list) (yukta : string list) : unit =
  remove_shabda_entry path word;
  add_shabda_entry path word abheda yukta

(* ---- .tantra3 file operations ---- *)

(* write a tantra file — full source replacement *)
let write_tantra (path : string) (source : string) : unit =
  let oc = open_out path in
  output_string oc source;
  close_out oc
