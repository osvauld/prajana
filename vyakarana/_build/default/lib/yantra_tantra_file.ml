(* yantra_tantra_file.ml — full .tantra file parser.
   parse_let_block: multi-line let bindings → (name × expr) list.
   parse_tantra_file: file path → tantra option.
   strip_comment: remove -- comments from a line. *)

open Yantra_types

(* strip_comment: remove everything after two consecutive dashes,
   but skip dashes that appear inside string literals. *)
let strip_comment (line : string) : string =
  let len = String.length line in
  let rec find i in_string =
    if i >= len then line
    else if line.[i] = '"' then
      (* toggle string mode; handle escaped quote *)
      if i > 0 && line.[i - 1] = '\\' then find (i + 1) in_string
      else find (i + 1) (not in_string)
    else if (not in_string) && i < len - 1
            && line.[i] = '-' && line.[i + 1] = '-' then
      String.sub line 0 i
    else find (i + 1) in_string
  in
  find 0 false

(* parse the let block: multi-line expression support.
   a new binding starts when a line matches "name = ..." where name is a
   simple identifier (letters, digits, hyphens). continuation lines are
   anything else within the let section. *)
let parse_let_block (lines : string list) : (string * expr) list =
  (* sentence-form bindings: pre-parsed exprs keyed by name, in order *)
  let sentence_bindings : (string * expr) list ref = ref [] in
  (* text bindings: grouped (name, accumulated_text) for normal let lines *)
  let bindings : (string * string) list ref = ref [] in
  let cur_name = ref "" in
  let cur_text = Buffer.create 128 in
  let flush () =
    if String.length !cur_name > 0 then begin
      bindings := (!cur_name, Buffer.contents cur_text) :: !bindings;
      Buffer.clear cur_text;
      cur_name := ""
    end
  in
  let is_ident_char c =
    (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z') ||
    (c >= '0' && c <= '9') || c = '-' || c = '_'
  in
  (* detect "name = ..." pattern: identifier followed by = *)
  let try_binding_start (s : string) : (string * string) option =
    let trimmed = String.trim s in
    match String.index_opt trimmed '=' with
    | Some eq_pos when eq_pos > 0 ->
      let lhs = String.trim (String.sub trimmed 0 eq_pos) in
      (* lhs must be a single identifier *)
      if String.length lhs > 0 &&
         String.to_seq lhs |> Seq.for_all is_ident_char then
        let rhs = String.trim (String.sub trimmed (eq_pos + 1)
                    (String.length trimmed - eq_pos - 1)) in
        Some (lhs, rhs)
      else None
    | _ -> None
  in
  List.iter (fun line ->
    let stripped = strip_comment line in
    let trimmed = String.trim stripped in
    if String.length trimmed > 0 then
      (* try sentence form sugar first (split X into Y, etc.) *)
      match Yantra_sentence_parser.try_sentence_form trimmed with
      | Some (name, expr) ->
        flush ();
        (* stash pre-parsed binding; also add a placeholder in bindings for ordering *)
        sentence_bindings := (name, expr) :: !sentence_bindings;
        bindings := (name, "\x00sentence") :: !bindings
      | None ->
      match try_binding_start trimmed with
      | Some (name, rhs) ->
        flush ();
        cur_name := name;
        Buffer.add_string cur_text rhs
      | None ->
        (* continuation of current binding *)
        if String.length !cur_name > 0 then begin
          Buffer.add_char cur_text ' ';
          Buffer.add_string cur_text trimmed
        end
  ) lines;
  flush ();
  (* parse each binding's text as an expression;
     sentence-form bindings (sentinel "\x00sentence") are looked up pre-parsed *)
  List.filter_map (fun (name, text) ->
    if text = "\x00sentence" then
      List.assoc_opt name !sentence_bindings
      |> Option.map (fun expr -> (name, expr))
    else if String.length (String.trim text) = 0 then None
    else begin
      try Some (name, Yantra_expr_parser.parse_expr_string text)
      with exn ->
        Printf.printf "warning: could not parse let binding '%s': %s [%s]\n%!" name (Printexc.to_string exn) (String.trim text);
        None
    end
  ) (List.rev !bindings)

(* parse a tantra file — supports multi-line let bindings with lambdas,
   cond expressions, let-in chains, etc. *)
let parse_tantra_file (path : string) : tantra option =
  try
    let ic = open_in path in
    let lines = ref [] in
    (try while true do lines := input_line ic :: !lines done
     with End_of_file -> ());
    close_in ic;
    let lines = List.rev !lines in

    (* first pass: split into sections *)
    let name = ref "" in
    let inputs = ref [] in
    let let_lines = ref [] in
    let returns = ref [] in
    let section = ref "header" in

    List.iter (fun line ->
      let stripped = strip_comment line in
      let trimmed = String.trim stripped in
      if String.length trimmed = 0 || trimmed = "done" then ()
      else if String.length trimmed >= 7 && String.sub trimmed 0 7 = "tantra " then
        name := String.trim (String.sub trimmed 7 (String.length trimmed - 7))
      else if trimmed = "inputs" then
        section := "inputs"
      else if trimmed = "let" then
        section := "let"
      else if trimmed = "return" then
        section := "return"
      else begin
        match !section with
        | "inputs" ->
           let parts = String.split_on_char ' ' trimmed
                      |> List.filter (fun s -> String.length s > 0) in
           (match parts with
            | pname :: ptype :: rest ->
              let punit = match rest with u :: _ when u <> "purva" && u <> "uttara" -> Some u | _ -> None in
              let pavastha = List.find_opt (fun s -> s = "purva" || s = "uttara") rest in
              inputs := { tp_name = pname; tp_canonical = pname; tp_type = ptype; tp_unit = punit; tp_avastha = pavastha } :: !inputs
            | _ -> ())
         | "let" ->
           let_lines := line :: !let_lines
         | "return" ->
           let parts = String.split_on_char ' ' trimmed
                      |> List.filter (fun s -> String.length s > 0) in
           (match parts with
            | pname :: ptype :: rest ->
              let punit = match rest with u :: _ when u <> "purva" && u <> "uttara" -> Some u | _ -> None in
              let pavastha = List.find_opt (fun s -> s = "purva" || s = "uttara") rest in
              returns := { tp_name = pname; tp_canonical = pname; tp_type = ptype; tp_unit = punit; tp_avastha = pavastha } :: !returns
            | _ -> ())
        | _ -> ()
      end
    ) lines;

    let lets = parse_let_block (List.rev !let_lines) in

    if String.length !name > 0 then
      Some {
        t_name    = !name;
        t_file    = path;
        t_inputs  = List.rev !inputs;
        t_lets    = lets;
        t_returns = List.rev !returns;
      }
    else None
  with _ -> None
