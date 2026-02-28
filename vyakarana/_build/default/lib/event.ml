(* event.ml — what moves through the proof space
   five events. the LLM does the semantic work.
   vyakarana holds the structure. *)

type t =
  | Darshana  of { name : string }   (* show one node *)
  | Anuvada   of {
      sentence : string;
      max_passes : int option;  (* optional avrti depth override *)
      thaalam : string option;  (* optional rhythmic rendering mode *)
    }  (* translate: english in, english out *)
  | Sthiti                           (* show full graph, human-readable *)
  | Pravaha                          (* show full graph as JSON *)
  | Visarjana                        (* end session *)
