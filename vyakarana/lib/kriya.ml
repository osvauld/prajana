(* kriya.ml — facade: re-exports all kriya split modules.
   replaces yantra.ml (26L). *)

include Kriya_types
include Kriya_graph

let parse_expr_string    = Vakya.parse_expr_string
let build_index          = Jnana.build_index

let eval               = Kriya_eval.eval
let eval_tantra        = Kriya_eval.eval_tantra
let print_result       = Kriya_eval.print_result
let run_tantra_by_name = Kriya_eval.run_tantra_by_name
let run_anuvada_ganana = Kriya_eval.run_anuvada_ganana
let run_session_anuvada = Kriya_eval.run_session_anuvada
let new_session        = Kriya_eval.new_session
let with_eval_ctx      = Kriya_eval.with_eval_ctx
