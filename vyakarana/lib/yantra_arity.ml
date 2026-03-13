(* yantra_arity.ml — arity tables and boundary detection.
   graph-derived and tantra-scanned op arities, pre_scan for quick header reads,
   and the Arg_overconsumed exception used by the expression parser. *)

(* dynamic arity table — populated by pre-scanning .tantra files.
   tantra-to-tantra calls are discovered automatically. *)
let _tantra_arities : (string, int) Hashtbl.t = Hashtbl.create 64

let register_tantra_arity (name : string) (arity : int) : unit =
  Hashtbl.replace _tantra_arities name arity

(* graph-derived arity table — populated from the .om kosha/yantra/ nodes.
   op nodes encode their algebraic class via a kriya edge; the class node
   carries parse-arity in its shabda. *)
let _graph_arities : (string, int) Hashtbl.t = Hashtbl.create 128

let register_graph_op_arity (name : string) (arity : int) : unit =
  Hashtbl.replace _graph_arities name arity

(* pre-scan a .tantra file: extract name and input count only.
   does NOT parse the let block — just reads the header. *)
let pre_scan_tantra_file (path : string) : (string * int) option =
  try
    let ic = open_in path in
    let lines = ref [] in
    (try while true do lines := input_line ic :: !lines done
     with End_of_file -> ());
    close_in ic;
    let lines = List.rev !lines in
    let name = ref "" in
    let input_count = ref 0 in
    let section = ref "header" in
    List.iter (fun line ->
      let trimmed = String.trim line in
      (* strip comments *)
      let trimmed = match String.index_opt trimmed '-' with
        | Some i when i + 1 < String.length trimmed && trimmed.[i+1] = '-' ->
          String.trim (String.sub trimmed 0 i)
        | _ -> trimmed
      in
      if String.length trimmed >= 7 && String.sub trimmed 0 7 = "tantra " then
        name := String.trim (String.sub trimmed 7 (String.length trimmed - 7))
      else if trimmed = "inputs" then
        section := "inputs"
      else if trimmed = "let" || trimmed = "return" || trimmed = "done" then
        section := trimmed
      else if !section = "inputs" && String.length trimmed > 0 then
        incr input_count
    ) lines;
    if String.length !name > 0 then
      Some (!name, !input_count)
    else None
  with _ -> None

(* op arity lookup — pure graph-class model.
   priority: graph-derived class arity → tantra-scanned arity → 0 (unknown). *)
let op_arity name =
  match Hashtbl.find_opt _graph_arities name with
  | Some n -> n
  | None ->
    match Hashtbl.find_opt _tantra_arities name with
    | Some n -> n
    | None -> 0

let is_known_op name = op_arity name <> 0

(* is this token a boundary that stops argument collection? *)
let is_boundary = function
  | ")" | "]" | "," | "in" | "otherwise" | "done" | "let" -> true
  | _ -> false

exception Arg_overconsumed
