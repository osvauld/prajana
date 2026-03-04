(* event.ml — what moves through the proof space
   five events. the LLM does the semantic work.
   vyakarana holds the structure. *)

type t =
  | Darshana  of { name : string; sahaja : bool }   (* show one node *)
  | Anuvada   of {
      sentence : string;
      max_passes : int option;  (* optional avrti depth override *)
      thaalam : string option;  (* optional rhythmic rendering mode *)
      sahaja : bool;            (* if true: render as "gloss (sanskrit)" *)
    }  (* translate: english in, english out *)
  | Prayoga   of {
      instruction : string;     (* the question / behaviour description *)
      input       : string;     (* what to run it on — sequence, string, etc. *)
      domain      : string option; (* optional: force emit domain *)
    }  (* execution: read the question, recognise, act, emit *)
  | Sthiti                           (* show full graph, human-readable *)
  | Pravaha                          (* show full graph as JSON *)
  | Visarjana                        (* end session *)
