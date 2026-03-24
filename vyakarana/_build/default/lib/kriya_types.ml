(* kriya_types.ml — AST, values, tantra, env, session.
   all type definitions for the evaluator layer.

   sections:
     1. tantra params
     2. expression AST (scan_stmt, scan_branch, expr)
     3. runtime values + env (StringMap — immutable, zero-cost share)
     4. tantra + tantra_index
     5. binding + session + result
     6. scene comprehension types
     7. value coercions + json
     8. eval_engine record (replaces forward refs)
     9. make_eval_arg *)

open Prakriti

(* immutable persistent map for environments — zero-cost "copy" via structural sharing *)
module StringMap = Map.Make(String)

(* ═══════════════════════════════════════════════════════════════════════════
   1. TANTRA PARAMS
   ═══════════════════════════════════════════════════════════════════════════ *)

type tantra_param = {
  tp_name      : string;
  tp_canonical : string;
  tp_type      : string;
  tp_unit      : string option;
  tp_avastha   : string option;
}

(* ═══════════════════════════════════════════════════════════════════════════
   2. EXPRESSION AST
   ═══════════════════════════════════════════════════════════════════════════ *)

type scan_stmt =
  | SEmit    of expr
  | SSkip
  | SSet     of string * expr
  | SClear   of string
  | SLet     of string * expr
  | SWhen    of expr * scan_stmt list * scan_stmt list

and scan_branch = {
  sb_guard : expr option;
  sb_body  : scan_stmt list;
}

and expr =
  | Lit      of float
  | Var      of string
  | Call     of string * expr list
  | StrLit   of string
  | BoolLit  of bool
  | ListExpr of expr list
  | Lambda   of string list * expr
  | Cond     of (expr * expr) list * expr
  | LetIn    of string * expr * expr
  | From     of expr * string list * expr list * expr
  | Scan     of expr * (string * expr) list * scan_branch list

(* ═══════════════════════════════════════════════════════════════════════════
   3. RUNTIME VALUES + ENV
   ═══════════════════════════════════════════════════════════════════════════ *)

type value =
  | VFloat   of float
  | VString  of string
  | VBool    of bool
  | VNode    of string
  | VList    of value list
  | VPair    of string * value
  | VBinding of string * float
  | VNone
  | VFn      of string list * expr * env
  | VGraph   of graph_index

(* indexed triple-list: flat triples + edge-type index. pure value, no mutation. *)
and graph_index = {
  gi_triples : value list;                           (* [[s,e,o], ...] *)
  gi_by_edge : (string, (string * string) list) Hashtbl.t;  (* edge → [(s,o), ...] *)
}

and env = value StringMap.t

(* ═══════════════════════════════════════════════════════════════════════════
   4. TANTRA + TANTRA_INDEX
   ═══════════════════════════════════════════════════════════════════════════ *)

type tantra = {
  t_name    : string;
  t_file    : string;
  t_inputs  : tantra_param list;
  t_lets    : (string * expr) list;
  t_returns : tantra_param list;
}

type tantra_index = {
  by_name      : (string, tantra) Hashtbl.t;
  by_output    : (string, tantra list) Hashtbl.t;
  by_input     : (string, tantra list) Hashtbl.t;
  constants    : (string, float) Hashtbl.t;
  conversions  : (string * string, tantra) Hashtbl.t;
  all_tantras  : tantra list ref;
  word_index   : (string, string) Hashtbl.t;
  eval_index   : (string, string) Hashtbl.t;
  compound_word_index : (string, string) Hashtbl.t;
}

(* ═══════════════════════════════════════════════════════════════════════════
   5. BINDING + SESSION + RESULT
   ═══════════════════════════════════════════════════════════════════════════ *)

type binding = {
  b_name       : string;
  b_value      : float;
  b_unit       : string option;
  b_timestamp  : float;
  b_source     : string;
  b_confidence : float;
  b_ttl        : float option;
}

type session = {
  mutable bindings      : binding list;
  mutable last_result   : (string * float) list;
  mutable history       : string list;
  mutable context_seeds : string list;
}

type yantra_result = {
  yr_output     : (string * float) list;
  yr_tantra     : string;
  yr_code       : string;
  yr_raw_output : string;
}

(* ═══════════════════════════════════════════════════════════════════════════
   5b. EVAL CONTEXT + ENGINE (replaces 4 forward refs with 1 Atomic record)
   ═══════════════════════════════════════════════════════════════════════════ *)

type eval_context = {
  ctx_index   : tantra_index;
  ctx_session : session;
}

(* bundled evaluator dispatch — single Atomic ref replaces 4 mutable forward refs *)
type eval_engine = {
  eval         : proof_graph -> env -> expr -> value;
  eval_tantra  : proof_graph -> tantra -> (string * value) list -> value;
  eval_pure_op : (proof_graph -> env -> expr -> value) ->
                 proof_graph -> env -> string -> expr list -> value option;
  eval_pipeline_op : (proof_graph -> env -> expr -> value) ->
                     proof_graph -> env -> string -> expr list -> value option;
}

let _engine : eval_engine Atomic.t = Atomic.make {
  eval = (fun _ _ _ -> VNone);
  eval_tantra = (fun _ _ _ -> VNone);
  eval_pure_op = (fun _ _ _ _ _ -> None);
  eval_pipeline_op = (fun _ _ _ _ _ -> None);
}

(* domain-local eval context — each Domain gets its own, no cross-request clobber *)
let _eval_ctx : eval_context option Domain.DLS.key =
  Domain.DLS.new_key (fun () -> None)

let last_invoked_tantra : string Atomic.t = Atomic.make ""

(* ═══════════════════════════════════════════════════════════════════════════
   5c. SESSION OVERLAY — per-domain triple subgraph
   ═══════════════════════════════════════════════════════════════════════════ *)

(* session subgraph: BQG triples live here instead of flat list.
   dual-indexed for O(1) lookup by source node AND by edge type.
   domain-local: each concurrent request has its own overlay. *)
type session_overlay = {
  by_source : (string, Prakriti.typed_edge list) Hashtbl.t;
  by_edge   : (int, (string * string) list) Hashtbl.t;  (* dimension → (source, target) pairs *)
  triples   : (string * int * string) list ref;          (* all triples for reconstruction *)
}

let new_session_overlay () = {
  by_source = Hashtbl.create 32;
  by_edge   = Hashtbl.create 16;
  triples   = ref [];
}

let _session_overlay : session_overlay Domain.DLS.key =
  Domain.DLS.new_key (fun () -> new_session_overlay ())

(* ═══════════════════════════════════════════════════════════════════════════
   6. SCENE COMPREHENSION TYPES
   ═══════════════════════════════════════════════════════════════════════════ *)

type krama_state = {
  ks_depth   : int;
  ks_concept : string;
  ks_binding : binding option;
}

type entity = {
  e_id      : int;
  e_label   : string;
  e_krama   : krama_state list;
  e_spanda  : float option;
  e_context : binding list;
}

type sandhi = {
  sh_kind     : string;
  sh_entities : int list;
  sh_time     : float option;
}

type process = {
  pr_sangati  : string;
  pr_entities : int list;
  pr_purva    : (int * binding list) list;
  pr_uttara   : (int * binding list) list;
  pr_target   : (int option * string) option;
}

type scene = {
  sc_entities  : entity list;
  sc_processes : process list;
  sc_sandhis   : sandhi list;
  sc_krama_seq : int list;
  sc_targets   : (int option * string) list;
}

(* ═══════════════════════════════════════════════════════════════════════════
   7. VALUE COERCIONS + JSON
   ═══════════════════════════════════════════════════════════════════════════ *)

let make_binding ?(unit_=None) ?(source="user") ?(confidence=1.0) ?(ttl=None) name value : binding =
  { b_name = name; b_value = value; b_unit = unit_;
    b_timestamp = Unix.gettimeofday (); b_source = source;
    b_confidence = confidence; b_ttl = ttl }

let new_env () : env = StringMap.empty

let as_float = function
  | VFloat f -> f
  | VString s -> (match float_of_string_opt s with Some f -> f | None -> 0.0)
  | VBool b -> if b then 1.0 else 0.0
  | _ -> 0.0

let rec as_string = function
  | VString s -> s
  | VFloat f ->
    if Float.is_integer f && Float.is_finite f then
      Printf.sprintf "%g" f
    else Printf.sprintf "%g" f
  | VBool b -> if b then "true" else "false"
  | VNode n -> n
  | VPair (n, v) -> Printf.sprintf "(%s . %s)" n (as_string v)
  | VBinding (n, v) -> Printf.sprintf "%s=%g" n v
  | VNone -> ""
  | VList items ->
    "[" ^ String.concat ", " (List.map as_string items) ^ "]"
  | VFn _ -> "<fn>"
  | VGraph g -> as_string (VList g.gi_triples)

let rec val_to_json = function
  | VString s  -> "\"" ^ json_escape s ^ "\""
  | VFloat f   ->
    if Float.is_nan f || Float.is_infinite f then "null"
    else if Float.is_integer f && Float.is_finite f then Printf.sprintf "%.0f" f
    else Printf.sprintf "%g" f
  | VBool b    -> if b then "true" else "false"
  | VNode n    -> "\"" ^ json_escape n ^ "\""
  | VNone      -> "null"
  | VFn _      -> "\"<fn>\""
  | VGraph g   -> val_to_json (VList g.gi_triples)
  | VPair (n, v) ->
    Printf.sprintf "{\"name\":%s,\"value\":%s}" (je n) (val_to_json v)
  | VBinding (n, v) ->
    Printf.sprintf "{\"name\":%s,\"value\":%g}" (je n) v
  | VList items ->
    "[" ^ String.concat "," (List.map val_to_json items) ^ "]"

let as_bool = function
  | VBool b -> b
  | VNone -> false
  | VFloat f -> f <> 0.0
  | VString s -> String.length s > 0
  | VList l -> l <> []
  | VNode _ -> true
  | VPair _ -> true
  | VBinding _ -> true
  | VFn _ -> true
  | VGraph g -> g.gi_triples <> []

let as_list = function
  | VList l -> l
  | VGraph g -> g.gi_triples
  | VNone -> []
  | v -> [v]

(* build graph index from flat triple list — O(n) *)
let index_triples (triples : value list) : graph_index =
  let by_edge = Hashtbl.create 16 in
  List.iter (fun triple ->
    match triple with
    | VList (VString s :: VString e :: rest) ->
      let o_str = match rest with
        | [VString o] -> o | [VNode o] -> o
        | [v] -> as_string v | _ -> "" in
      let existing = match Hashtbl.find_opt by_edge e with Some l -> l | None -> [] in
      Hashtbl.replace by_edge e ((s, o_str) :: existing)
    | _ -> ()
  ) triples;
  { gi_triples = triples; gi_by_edge = by_edge }

(* ═══════════════════════════════════════════════════════════════════════════
   8. AST → JSON SERIALIZATION
   ═══════════════════════════════════════════════════════════════════════════ *)

let rec json_of_expr = function
  | Lit f ->
    Printf.sprintf "{\"kind\":\"lit\",\"value\":%s}" (val_to_json (VFloat f))
  | Var s ->
    Printf.sprintf "{\"kind\":\"var\",\"name\":%s}" (je s)
  | StrLit s ->
    Printf.sprintf "{\"kind\":\"str\",\"value\":%s}" (je s)
  | BoolLit b ->
    Printf.sprintf "{\"kind\":\"bool\",\"value\":%s}" (if b then "true" else "false")
  | ListExpr items ->
    Printf.sprintf "{\"kind\":\"list\",\"items\":[%s]}"
      (String.concat "," (List.map json_of_expr items))
  | Call (op, args) ->
    Printf.sprintf "{\"kind\":\"call\",\"op\":%s,\"args\":[%s]}"
      (je op) (String.concat "," (List.map json_of_expr args))
  | Lambda (params, body) ->
    Printf.sprintf "{\"kind\":\"lambda\",\"params\":[%s],\"body\":%s}"
      (String.concat "," (List.map je params)) (json_of_expr body)
  | Cond (branches, otherwise) ->
    let branches_json = String.concat "," (List.map (fun (g, b) ->
      Printf.sprintf "{\"guard\":%s,\"body\":%s}" (json_of_expr g) (json_of_expr b)
    ) branches) in
    Printf.sprintf "{\"kind\":\"cond\",\"branches\":[%s],\"otherwise\":%s}"
      branches_json (json_of_expr otherwise)
  | LetIn (name, e1, e2) ->
    Printf.sprintf "{\"kind\":\"let_in\",\"name\":%s,\"value\":%s,\"body\":%s}"
      (je name) (json_of_expr e1) (json_of_expr e2)
  | From (src, pattern, guards, collect) ->
    Printf.sprintf "{\"kind\":\"from\",\"source\":%s,\"pattern\":[%s],\"guards\":[%s],\"collect\":%s}"
      (json_of_expr src)
      (String.concat "," (List.map je pattern))
      (String.concat "," (List.map json_of_expr guards))
      (json_of_expr collect)
  | Scan (src, state_decls, branches) ->
    let state_json = String.concat "," (List.map (fun (name, init) ->
      Printf.sprintf "{\"name\":%s,\"init\":%s}" (je name) (json_of_expr init)
    ) state_decls) in
    let branches_json = String.concat "," (List.map json_of_scan_branch branches) in
    Printf.sprintf "{\"kind\":\"scan\",\"source\":%s,\"state\":[%s],\"branches\":[%s]}"
      (json_of_expr src) state_json branches_json

and json_of_scan_stmt = function
  | SEmit e ->
    Printf.sprintf "{\"kind\":\"emit\",\"expr\":%s}" (json_of_expr e)
  | SSkip ->
    "{\"kind\":\"skip\"}"
  | SSet (name, e) ->
    Printf.sprintf "{\"kind\":\"set\",\"name\":%s,\"expr\":%s}" (je name) (json_of_expr e)
  | SClear name ->
    Printf.sprintf "{\"kind\":\"clear\",\"name\":%s}" (je name)
  | SLet (name, e) ->
    Printf.sprintf "{\"kind\":\"slet\",\"name\":%s,\"expr\":%s}" (je name) (json_of_expr e)
  | SWhen (guard, body, otherwise) ->
    Printf.sprintf "{\"kind\":\"when\",\"guard\":%s,\"body\":[%s],\"otherwise\":[%s]}"
      (json_of_expr guard)
      (String.concat "," (List.map json_of_scan_stmt body))
      (String.concat "," (List.map json_of_scan_stmt otherwise))

and json_of_scan_branch b =
  let guard_json = match b.sb_guard with
    | None   -> "null"
    | Some g -> json_of_expr g
  in
  Printf.sprintf "{\"guard\":%s,\"otherwise\":%s,\"body\":[%s]}"
    guard_json
    (if b.sb_guard = None then "true" else "false")
    (String.concat "," (List.map json_of_scan_stmt b.sb_body))

let json_of_tantra (t : tantra) : string =
  let lets_json = String.concat "," (List.map (fun (name, e) ->
    Printf.sprintf "{\"name\":%s,\"expr\":%s}" (je name) (json_of_expr e)
  ) t.t_lets) in
  let inputs_json = String.concat "," (List.map (fun p ->
    Printf.sprintf "{\"name\":%s,\"type\":%s}" (je p.tp_name) (je p.tp_type)
  ) t.t_inputs) in
  let returns_json = String.concat "," (List.map (fun p ->
    Printf.sprintf "{\"name\":%s,\"type\":%s}" (je p.tp_name) (je p.tp_type)
  ) t.t_returns) in
  Printf.sprintf
    "{\"name\":%s,\"file\":%s,\"inputs\":[%s],\"returns\":[%s],\"bindings\":[%s]}"
    (je t.t_name) (je t.t_file) inputs_json returns_json lets_json

(* ═══════════════════════════════════════════════════════════════════════════
   9. MAKE_EVAL_ARG — typed accessor factory
   ═══════════════════════════════════════════════════════════════════════════ *)

let make_eval_arg
    (e_eval : 'g -> env -> expr -> value)
    (k : 'g) (e : env) (args : expr list) =
  let eval_arg n  = e_eval k e (List.nth args n) in
  let eval_str n  = as_string (eval_arg n) in
  let eval_flt n  = as_float  (eval_arg n) in
  let eval_lst n  = as_list   (eval_arg n) in
  let eval_int n  = int_of_float (eval_flt n) in
  (eval_arg, eval_str, eval_flt, eval_lst, eval_int)
