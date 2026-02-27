(* event.ml — vayu-spanda
   What moves through the proof space.
   Events are not commands. They are spanda —
   acts of discovery arriving to contact the running proofs.

   panchabhootam:
     vayu-spanda  : each event is one vibration — one contact attempt
     agni-ananta  : the stream never ends — the fold processes without terminating
     bhumi-shunya : a Deepen event moves a truth from shunya toward located

   The stream of events was always flowing.
   The fold joins it — does not create it.

   Epoch 12 additions — smara/smarana/anuvada (trikosha-smriti level 2):
     Anuvada  : recognition through hetu overlap — returns DARSHANA for closest nigamana
     Smara    : activation event — writes nigamana to session K (level 2)
     Smarana  : retrieval — from session K first, then ground K; weighted by recency + satya
*)

type query = {
  nigamana_name : string;   (* which running proof to contact *)
  assertion     : string;   (* what the agent/LLM is claiming *)
}

type t =
  | Query    of query
  | Deepen   of { name : string; new_shabda : string }  (* new connection forms — shunya gains position *)
  | Merge    of { a : string; b : string }               (* two truths recognized as one *)
  | Split    of { name : string; a : nigamana_stub; b : nigamana_stub }  (* one truth recognized as two *)
  | Rename   of { name : string; new_name : string }     (* name compresses or expands *)
  | Pravaha                                               (* read the flowing space — full JSON snapshot of K *)
  | Shutdown                                              (* process leaves the space — space continues *)
  | Anuvada  of { text : string }                        (* recognition through hetu overlap — find closest nigamana *)
  | Smara    of { name : string; strength : float }      (* activation event — write to session memory level 2 *)
  | Smarana  of { text : string }                        (* retrieve — session K first, then ground K *)

and nigamana_stub = {
  stub_name   : string;
  stub_paksha : string;
  stub_hetu   : string list;
}
