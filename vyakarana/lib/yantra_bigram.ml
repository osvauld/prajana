(* yantra_bigram.ml — yantra token type.
   ytoken is the typed token used throughout the classification pipeline.
   bigram joining is now handled by classify-fold.tantra (graph-walk avrti).

   dependency: Proof_graph. *)

open Proof_graph

(* yantra-specific token type — wraps a classified word *)
type ytoken =
  | YConcept  of string
  | YNumber   of float
  | YOperator of string
  | YGrammar  of visheshanam
  | YUnknown  of string
