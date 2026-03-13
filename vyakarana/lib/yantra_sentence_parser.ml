(* yantra_sentence_parser.ml — natural language sentence forms.
   extension point for P8-NL tantra sentence sugar.

   Implemented forms:

     split X into Y
       → Y = split X " "
       → used by: build-question-graph.tantra

   Planned forms (not yet implemented):

     avrti X resolving each into graph until stable
       → graph = avrti X [] (fn pass g word -> ...)
       → used by: build-question-graph.tantra

   Each form desugars into (name, expr) pairs consumed by parse_let_block.
   Returns Some (name, expr) if the line matched a sentence form, None otherwise. *)

open Yantra_types

(* try_sentence_form: attempt to parse a trimmed let-block line as a sentence form.
   returns Some (binding_name, expr) if matched, None to fall through to normal parsing. *)
let try_sentence_form (line : string) : (string * expr) option =
  let tokens = String.split_on_char ' ' line
               |> List.filter (fun s -> String.length s > 0) in
  match tokens with

  (* split X into Y  →  Y = split X " " *)
  | ["split"; x; "into"; y] ->
    Some (y, Call ("split", [Var x; StrLit " "]))

  (* split X by Z into Y  →  Y = split X Z  (generalised delimiter) *)
  | ["split"; x; "by"; z; "into"; y] ->
    Some (y, Call ("split", [Var x; StrLit z]))

  | _ -> None
