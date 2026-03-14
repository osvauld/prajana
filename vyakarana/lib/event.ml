(* event.ml — what moves through the proof space *)

type t =
  | Darshana of { name : string }
  | Anuvada  of { sentence : string; max_passes : int option }
  | Yantra   of { sentence : string }
  | Sthiti                           (* show full graph, human-readable *)
  | Pravaha                          (* show full graph as JSON *)
  | Visarjana                        (* end session *)
