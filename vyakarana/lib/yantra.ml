(* yantra.ml — thin facade: re-exports all yantra split modules.
   dependency order: Yantra_types → Yantra_tokeniser → Yantra_arity →
     Yantra_sentence_parser → Yantra_expr_parser → Yantra_tantra_file →
     Yantra_index → Yantra_ops → Yantra_eval_primitives →
     Yantra_pipeline_ops → Yantra_eval *)

open Proof_graph

include Yantra_types        (* tantra_index, session, binding, value, env, as_float … *)

let parse_expr_string    = Yantra_expr_parser.parse_expr_string
let build_index          = Yantra_index.build_index
let build_word_index     = Yantra_index.build_word_index

include Yantra_eval_primitives   (* eval_ctx, eval_call, env_copy, last_invoked_tantra … *)

let eval               = Yantra_eval.eval
let eval_tantra        = Yantra_eval.eval_tantra
let print_result       = Yantra_eval.print_result
let run_tantra_by_name = Yantra_eval.run_tantra_by_name
let run_anuvada_ganana = Yantra_eval.run_anuvada_ganana
let run_session_anuvada = Yantra_eval.run_session_anuvada
let new_session        = Yantra_eval.new_session

let _graph_ref : proof_graph option ref = ref None
