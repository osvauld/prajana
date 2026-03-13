(* yantra_eval_context.ml — shared runtime context and forward references.
   placed before yantra_eval_graph and yantra_eval_primitives in the build order
   so both can reference the same mutable refs without circular dependency.

   yantra_eval.ml wires these refs at module init (let () = ... section). *)

open Proof_graph
open Yantra_types
open Yantra_resolver

(* gives the evaluator access to the tantra index and session
   without changing the eval signature everywhere. *)
type eval_context = {
  ctx_index   : tantra_index;
  ctx_session : session;
}
let eval_ctx : eval_context option ref = ref None

(* ---- forward references ---- *)

(* _eval_ref: forward reference to eval — breaks the mutual recursion
   between eval_call (yantra_eval_primitives) and eval (yantra_eval). *)
let _eval_ref : (proof_graph -> env -> expr -> value) ref =
  ref (fun _ _ _ -> VNone)

let _yantra_tokenise_ref : (string -> string list) ref = ref (fun _ -> [])

let _resolve_concept_to_tantra_ref : (proof_graph -> tantra_index -> string -> string option) ref =
  ref (fun _ _ _ -> None)

let _resolve_tantra_ref : (proof_graph -> tantra_index -> binding list -> string -> resolution) ref =
  ref (fun _ _ _ target -> NotFound (Printf.sprintf "not initialized: %s" target))

let _eval_tantra_ref : (proof_graph -> tantra -> (string * value) list -> value) ref =
  ref (fun _ _ _ -> VNone)

(* raw refs for wiring to yantra_ops and yantra_pipeline_ops — set at init *)
let _eval_pure_op_raw : ((proof_graph -> env -> expr -> value) -> proof_graph -> env -> string -> expr list -> value option) ref =
  ref (fun _e_eval _k _e _op _args -> None)

let _eval_pipeline_op_raw : ((proof_graph -> env -> expr -> value) -> proof_graph -> env -> string -> expr list -> value option) ref =
  ref (fun _e_eval _k _e _op _args -> None)

(* tracks the last tantra name used for result attribution *)
let last_invoked_tantra : string ref = ref ""

(* ---- shared utilities ---- *)

let env_copy (e : env) : env =
  let e2 = Hashtbl.create (Hashtbl.length e) in
  Hashtbl.iter (fun k v -> Hashtbl.replace e2 k v) e;
  e2

(* pair_field: extract a named field from a list of VPair/VList items *)
let pair_field (items : value list) (key : string) : value option =
  List.find_map (function
    | VPair (k, v) when k = key -> Some v
    | VList [VString k; v] when k = key -> Some v
    | _ -> None
  ) items
