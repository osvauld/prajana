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

(* dynamic boundary keyword registry — populated at runtime by register_primitive_arities.
   starts empty; callers must register all keywords before parsing begins. *)
let _boundary_keywords : (string, unit) Hashtbl.t = Hashtbl.create 32

let register_boundary_keyword (kw : string) : unit =
  Hashtbl.replace _boundary_keywords kw ()

(* is this token a boundary that stops argument collection? *)
let is_boundary (tok : string) : bool =
  Hashtbl.mem _boundary_keywords tok

exception Arg_overconsumed
