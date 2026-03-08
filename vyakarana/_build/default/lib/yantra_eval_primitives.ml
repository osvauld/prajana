(* yantra_eval_primitives.ml — primitive operation dispatch table.
   contains eval_call: the match on operation names that drives all tantra
   built-in operations (graph ops, string ops, list ops, math, pipeline ops).

   kept separate from yantra_eval.ml so the core evaluator (eval, LetIn,
   Lambda, Cond) is readable on its own. the mutual recursion between eval
   and eval_call is broken by a forward reference _eval_ref, wired at init
   in yantra_eval.ml.

   the dispatch is split into three groups:
     eval_graph_op  — graph, field-accessor, and context ops (here, lines below)
     eval_pure_op   — string/list/bool/math/constructors (Yantra_ops)
     eval_pipeline_op — pipeline and session ops (Yantra_pipeline_ops)

   the ops modules are wired via forward references to avoid cycles.

   dependency: Proof_graph, Yantra_types, Yantra_resolver, Setu, Anuvada. *)

open Proof_graph
open Yantra_types
open Yantra_resolver

(* ---- runtime context ---- *)
(* gives the evaluator access to the tantra index and session
   without changing the eval signature everywhere. set before calling eval_tantra. *)
type eval_context = {
  ctx_index   : tantra_index;
  ctx_session : session;
}
let eval_ctx : eval_context option ref = ref None

(* ---- forward references ---- *)
(* wired at module init in yantra_eval.ml *)

(* _eval_ref: forward reference to eval — breaks the mutual recursion
   between eval_call (here) and eval (in yantra_eval.ml) *)
let _eval_ref : (proof_graph -> env -> expr -> value) ref =
  ref (fun _ _ _ -> VNone)

let _yantra_tokenise_ref : (string -> string list) ref = ref (fun _ -> [])
let _resolve_concept_to_tantra_ref : (proof_graph -> tantra_index -> string -> string option) ref =
  ref (fun _ _ _ -> None)
let _resolve_tantra_ref : (proof_graph -> tantra_index -> binding list -> string -> resolution) ref =
  ref (fun _ _ _ target -> NotFound (Printf.sprintf "not initialized: %s" target))
let _eval_tantra_ref : (proof_graph -> tantra -> (string * value) list -> value) ref =
  ref (fun _ _ _ -> VNone)

(* forward refs to the ops sub-modules — wired by yantra_eval.ml after all modules load *)
let _eval_pure_op_ref :
    (proof_graph -> env -> expr -> value) ->
    proof_graph -> env -> string -> expr list -> value option =
  ref (fun _e_eval _k _e _op _args -> None) |> fun r -> (fun e_eval k e op args -> !r e_eval k e op args)

let _eval_pipeline_op_ref :
    (proof_graph -> env -> expr -> value) ->
    proof_graph -> env -> string -> expr list -> value option =
  ref (fun _e_eval _k _e _op _args -> None) |> fun r -> (fun e_eval k e op args -> !r e_eval k e op args)

(* raw refs for wiring *)
let _eval_pure_op_raw : ((proof_graph -> env -> expr -> value) -> proof_graph -> env -> string -> expr list -> value option) ref =
  ref (fun _e_eval _k _e _op _args -> None)
let _eval_pipeline_op_raw : ((proof_graph -> env -> expr -> value) -> proof_graph -> env -> string -> expr list -> value option) ref =
  ref (fun _e_eval _k _e _op _args -> None)

(* tracks the last tantra name used for result attribution (set by execute-plan) *)
let last_invoked_tantra : string ref = ref ""

(* ---- env utilities ---- *)

let env_copy (e : env) : env =
  let e2 = Hashtbl.create (Hashtbl.length e) in
  Hashtbl.iter (fun k v -> Hashtbl.replace e2 k v) e;
  e2

(* ---- pair_field: extract a named field from a list of VPair/VList items ---- *)

let pair_field (items : value list) (key : string) : value option =
  List.find_map (function
    | VPair (k, v) when k = key -> Some v
    | VList [VString k; v] when k = key -> Some v
    | _ -> None
  ) items

(* ---- eval_graph_op: graph, field-accessor, and context operations ---- *)

let eval_graph_op (e_eval : proof_graph -> env -> expr -> value)
    (k : proof_graph) (e : env) (op : string) (args : expr list) : value option =
  match op with

  (* lookup: string → VNode if found, VNone if not — raw table hit only *)
  | "lookup" ->
    let name = as_string (e_eval k e (List.nth args 0)) in
    Some (match Proof_graph.find k name with
     | Some _ -> VNode name
     | None   -> VNone)

  (* walk: node × relation → [node] — follow edges of a given type *)
  | "walk" ->
    let node_name = as_string (e_eval k e (List.nth args 0)) in
    let rel_name = as_string (e_eval k e (List.nth args 1)) in
    let rel = Proof_graph.visheshanam_of_string rel_name in
    Some (match rel with
     | None -> VList []
     | Some vish ->
       let edges = Proof_graph.edges_of k node_name in
       let targets = List.filter_map (fun edge ->
         if edge.relation = vish && edge.source = node_name then
           Some (VNode edge.target)
         else None
       ) edges in
       VList targets)

  (* walk-in: node × relation → [node] — follow INCOMING edges *)
  | "walk-in" ->
    let node_name = as_string (e_eval k e (List.nth args 0)) in
    let rel_name = as_string (e_eval k e (List.nth args 1)) in
    let rel = Proof_graph.visheshanam_of_string rel_name in
    Some (match rel with
     | None -> VList []
     | Some vish ->
       let edges = Proof_graph.edges_of k node_name in
       let sources = List.filter_map (fun edge ->
         if edge.relation = vish && edge.target = node_name then
           Some (VNode edge.source)
         else None
       ) edges in
       VList sources)

  (* has: node × edge-pattern → bool
     edge-pattern is "relation-target" e.g. "matra-sthita" *)
  | "has" ->
    let node_name = as_string (e_eval k e (List.nth args 0)) in
    let pattern = as_string (e_eval k e (List.nth args 1)) in
    let edges = Proof_graph.edges_of k node_name in
    let parts = String.split_on_char '-' pattern in
    let found = match List.rev parts with
      | rel_str :: target_parts ->
        let target = String.concat "-" (List.rev target_parts) in
        let rel = Proof_graph.visheshanam_of_string rel_str in
        (match rel with
         | Some vish ->
           List.exists (fun edge ->
             edge.relation = vish && edge.source = node_name && edge.target = target
           ) edges
         | None ->
           let rel2 = Proof_graph.visheshanam_of_string (List.hd parts) in
           match rel2 with
           | Some vish ->
             let target2 = String.concat "-" (List.tl parts) in
             List.exists (fun edge ->
               edge.relation = vish && edge.source = node_name && edge.target = target2
             ) edges
           | None -> false)
      | [] -> false
    in
    Some (VBool found)

  (* edges: node → [(source, relation, target)] as list of strings *)
  | "edges" ->
    let node_name = as_string (e_eval k e (List.nth args 0)) in
    let edges = Proof_graph.edges_of k node_name in
    Some (VList (List.map (fun edge ->
      VList [VString edge.source;
             VString (Proof_graph.string_of_visheshanam edge.relation);
             VString edge.target]
    ) edges))

  (* all-edges: () → [(source, relation, target)] for every edge in the graph.
     used by visheshanam-entropy-weights tantra to compute relation conductances. *)
  | "all-edges" ->
    Some (VList (List.map (fun (edge : Proof_graph.typed_edge) ->
      VList [VString edge.source;
             VString (Proof_graph.string_of_visheshanam edge.relation);
             VString edge.target]
    ) !(k.all_edges)))

  (* to-english: node-name → English name
     dispatches to to-english.tantra if loaded; falls back to shabda "name" field,
     then node name if node exists, otherwise returns "asprista". *)
  | "to-english" ->
    let name = as_string (e_eval k e (List.nth args 0)) in
    Some (match !eval_ctx with
     | Some ctx ->
       (match Hashtbl.find_opt ctx.ctx_index.by_name "to-english" with
        | Some t ->
          let result = !_eval_tantra_ref k t [("node", VString name)] in
          (match result with
           | VString s when String.length s > 0 -> VString s
           | _ -> VString "asprista")
        | None ->
          let pairs = Setu.read_shabda k name in
          (match List.assoc_opt "name" pairs with
           | Some v -> VString v
           | None   ->
             (match Hashtbl.find_opt k.nodes name with
              | Some _ -> VString name
              | None -> VString "asprista")))
     | None -> VString "asprista")

  (* describe: node-name → shabda description string (the part after /) *)
  | "describe" ->
    let name = as_string (e_eval k e (List.nth args 0)) in
    Some (match Hashtbl.find_opt k.nodes name with
     | None -> VString ""
     | Some n ->
       let s = n.shabda in
       match String.split_on_char '/' s with
       | _ :: rest when rest <> [] ->
         VString (String.trim (String.concat "/" rest))
       | _ -> VString "")

  (* to-english-relation: visheshanam-string → English phrase *)
  | "to-english-relation" ->
    let rel_str = as_string (e_eval k e (List.nth args 0)) in
    let vish = Proof_graph.visheshanam_of_string rel_str in
    Some (match vish with
     | Some v -> VString (Anuvada.english_of_visheshanam_from_graph k v)
     | None -> VString rel_str)

  (* incoming-to: node-name -> incoming typed edges [source, relation, target].
     delegates to incoming-to.tantra when loaded; OCaml fallback otherwise. *)
  | "incoming-to" ->
    let name = as_string (e_eval k e (List.nth args 0)) in
    (match !eval_ctx with
     | Some ctx when Hashtbl.mem ctx.ctx_index.by_name "incoming-to" ->
       let t = Hashtbl.find ctx.ctx_index.by_name "incoming-to" in
       Some (!_eval_tantra_ref k t [("n", VString name)])
     | _ ->
       let edges = Proof_graph.edges_of k name in
       let incoming = List.filter_map (fun edge ->
         if edge.Proof_graph.target = name && edge.Proof_graph.source <> name then
           Some (VList [ VString edge.Proof_graph.source;
                         VString (Proof_graph.string_of_visheshanam edge.Proof_graph.relation);
                         VString edge.Proof_graph.target ])
         else
           None
       ) edges in
       Some (VList incoming))

  (* domain-of: node-name -> list of domain-* names linked to this node.
     delegates to domain-of.tantra when loaded; OCaml fallback otherwise. *)
  | "domain-of" ->
    let name = as_string (e_eval k e (List.nth args 0)) in
    (match !eval_ctx with
     | Some ctx when Hashtbl.mem ctx.ctx_index.by_name "domain-of" ->
       let t = Hashtbl.find ctx.ctx_index.by_name "domain-of" in
       Some (!_eval_tantra_ref k t [("n", VString name)])
     | _ ->
       let is_domain_name n =
         String.length n >= 7 && String.sub n 0 7 = "domain-"
       in
       let own = if is_domain_name name then [name] else [] in
       let domains =
         match Hashtbl.find_opt k.nodes name with
         | None -> own
         | Some n ->
           let from_outgoing = List.filter_map (fun edge ->
             if edge.Proof_graph.source = name
                && edge.Proof_graph.relation = Proof_graph.Sthita
                && is_domain_name edge.Proof_graph.target
             then Some edge.Proof_graph.target
             else None
           ) n.edges in
           let from_incoming = List.filter_map (fun edge ->
             if edge.Proof_graph.target = name && is_domain_name edge.Proof_graph.source
             then Some edge.Proof_graph.source
             else None
           ) (Proof_graph.edges_of k name) in
           List.sort_uniq String.compare (own @ from_outgoing @ from_incoming)
       in
       Some (VList (List.map (fun d -> VString d) domains)))

  (* context-score: node-name x [seed-names] -> edge connectivity score.
     delegates to context-score.tantra when loaded; OCaml fallback otherwise. *)
  | "context-score" ->
    let name = as_string (e_eval k e (List.nth args 0)) in
    let seeds_v = e_eval k e (List.nth args 1) in
    (match !eval_ctx with
      | Some ctx when Hashtbl.mem ctx.ctx_index.by_name "context-score-impl" ->
        let t = Hashtbl.find ctx.ctx_index.by_name "context-score-impl" in
        Some (!_eval_tantra_ref k t [("n", VString name); ("seeds", seeds_v)])
     | _ ->
       let seeds = List.map as_string (as_list seeds_v) in
       let seed_set = Hashtbl.create 16 in
       List.iter (fun s -> Hashtbl.replace seed_set s true) seeds;
       let edges = Proof_graph.edges_of k name in
       let score = List.fold_left (fun acc edge ->
         if Hashtbl.mem seed_set edge.Proof_graph.source
            || Hashtbl.mem seed_set edge.Proof_graph.target
         then acc + 1
         else acc
       ) 0 edges in
       Some (VFloat (Float.of_int score)))

  (* node-satya: node-name -> float — structural importance score *)
  | "node-satya" ->
    let name = as_string (e_eval k e (List.nth args 0)) in
    let satya = match Hashtbl.find_opt k.nodes name with
      | Some n -> n.Proof_graph.satya
      | None   -> 0.0 in
    Some (VFloat satya)

  (* edge-weight: relation-name-string -> float — vp_satya_weight conductance *)
  | "edge-weight" ->
    let rel_str = as_string (e_eval k e (List.nth args 0)) in
    let w = match Proof_graph.visheshanam_of_string rel_str with
      | Some v -> (Proof_graph.vish_props_of v).vp_satya_weight
      | None   -> 0.0 in
    Some (VFloat w)

  (* iccha-status: node-name -> "sthita" | "rahita" | "none" *)
  | "iccha-status" ->
    let name = as_string (e_eval k e (List.nth args 0)) in
    let has_sthita =
      match Hashtbl.find_opt k.nodes name with
      | None -> false
      | Some n ->
        List.exists (fun edge ->
          edge.Proof_graph.source = name
          && edge.Proof_graph.target = "iccha"
          && edge.Proof_graph.relation = Proof_graph.Sthita
        ) n.edges
    in
    let has_rahita =
      match Hashtbl.find_opt k.nodes name with
      | None -> false
      | Some n ->
        List.exists (fun sloka ->
          let marker = "iccha-rahita" in
          let s = String.lowercase_ascii sloka in
          let m = String.lowercase_ascii marker in
          try
            ignore (Str.search_forward (Str.regexp_string m) s 0);
            true
          with Not_found -> false
        ) n.slokas
    in
    Some (VString (if has_sthita then "sthita" else if has_rahita then "rahita" else "none"))

  (* abheda-of: node-name -> outgoing abheda targets.
     delegates to abheda-of.tantra when loaded; OCaml fallback otherwise. *)
  | "abheda-of" ->
    let name = as_string (e_eval k e (List.nth args 0)) in
    (match !eval_ctx with
     | Some ctx when Hashtbl.mem ctx.ctx_index.by_name "abheda-of" ->
       let t = Hashtbl.find ctx.ctx_index.by_name "abheda-of" in
       Some (!_eval_tantra_ref k t [("n", VString name)])
     | _ ->
       let targets =
         match Hashtbl.find_opt k.nodes name with
         | None -> []
         | Some n ->
           List.filter_map (fun edge ->
             if edge.Proof_graph.source = name
                && edge.Proof_graph.relation = Proof_graph.Abheda
             then Some edge.Proof_graph.target
             else None
           ) n.edges
       in
       Some (VList (List.map (fun t -> VString t) (List.sort_uniq String.compare targets))))

  (* avrti: seed-names × max-passes -> flat triples [source-raw, relation-name, [target-raws]] *)
  | "avrti" ->
    let seeds = as_list (e_eval k e (List.nth args 0)) in
    let max_passes = int_of_float (as_float (e_eval k e (List.nth args 1))) in
    let seed_names = List.map as_string seeds in
    let (pass_groups, _) = Anuvada.avrti_anuvada k seed_names max_passes in
    let connections = List.concat_map (fun (_pass_num, triples) ->
      List.map (fun (t : Anuvada.anuvada_triple) ->
        VList [ VString t.a_source_raw;
                VString (Proof_graph.string_of_visheshanam t.a_relation);
                VList (List.map (fun s -> VString s) t.a_targets_raw) ]
      ) triples
    ) pass_groups in
    Some (VList connections)

  (* render-node: name → formatted node inspection text *)
  | "render-node" ->
    let name = as_string (e_eval k e (List.nth args 0)) in
    let rname =
      match Proof_graph.find k name with
      | Some _ -> name
      | None ->
        (match Setu.classify_token k name with
         | Setu.Content c when c <> name -> c
         | _ -> name)
    in
    Some (match Proof_graph.find k rname with
     | None -> VString (Printf.sprintf "not found: %s." name)
     | Some n ->
       let buf = Buffer.create 256 in
       Anuvada.render_darshana_to_buf k n buf;
       VString (Buffer.contents buf))

  (* ---- field accessors ---- *)

  (* name: extract name from VNode, VPair, VBinding *)
  | "name" ->
    let v = e_eval k e (List.nth args 0) in
    Some (match v with
     | VNode n -> VString n
     | VPair (n, _) -> VString n
     | VBinding (n, _) -> VString n
     | VString s -> VString s
     | _ -> VString (as_string v))

  (* kind: extract the kind/type tag from a VPair *)
  | "kind" ->
    let v = e_eval k e (List.nth args 0) in
    Some (match v with
     | VPair (_, inner) -> inner
     | _ -> VNone)

  (* node: extract the node from a classified token triple *)
  | "node" ->
    let v = e_eval k e (List.nth args 0) in
    Some (match v with
     | VList [_; _; n] -> n
     | VNode _ -> v
     | _ -> VNone)

  (* value: extract numeric value from VFloat, VBinding *)
  | "value" ->
    let v = e_eval k e (List.nth args 0) in
    Some (match v with
     | VFloat f -> VFloat f
     | VBinding (_, f) -> VFloat f
     | VString s ->
       (match float_of_string_opt s with Some f -> VFloat f | None -> VNone)
     | _ -> VNone)

  (* role: look up what grammar role a word has via english-grammar shabda *)
  | "role" ->
    let v = e_eval k e (List.nth args 0) in
    let word = as_string v in
    let pairs = Setu.read_shabda k "english-grammar" in
    Some (match List.find_opt (fun (w, _) -> w = word) pairs with
     | Some (_, rel) -> VString rel
     | None -> VNone)

  (* shabda: node × key → string — read shabda data *)
  | "shabda" ->
    let node_name = as_string (e_eval k e (List.nth args 0)) in
    let key = as_string (e_eval k e (List.nth args 1)) in
    let pairs = Setu.read_shabda k node_name in
    Some (match List.find_opt (fun (k, _) -> k = key) pairs with
     | Some (_, v) -> VString v
     | None -> VNone)

  (* exists: value → bool — true unless VNone or empty *)
  | "exists" ->
    let v = e_eval k e (List.nth args 0) in
    Some (VBool (as_bool v))

  (* op-to-tantra: operator symbol → tantra name or VNone *)
  | "op-to-tantra" ->
    let op = as_string (e_eval k e (List.nth args 0)) in
    let pairs = Setu.read_shabda k "chihna-ganaka" in
    let tname = List.assoc_opt op pairs in
    Some (match tname with Some n -> VString n | None -> VNone)

  (* is-tantra: name → bool — does a tantra with this name exist?
     also resolves through graph: "plus" → abheda → "addition" → true *)
  | "is-tantra" ->
    let tname = as_string (e_eval k e (List.nth args 0)) in
    Some (match !eval_ctx with
     | Some ctx ->
       let direct = Hashtbl.mem ctx.ctx_index.by_name tname in
       if direct then VBool true
       else
         let resolved = !_resolve_concept_to_tantra_ref k ctx.ctx_index tname in
         VBool (resolved <> None)
     | None ->
       match Hashtbl.find_opt e "_tantra_index" with
       | Some (VList names) ->
         VBool (List.exists (fun v -> as_string v = tname) names)
       | _ -> VBool false)

  | _ -> None

(* ---- eval_call: primitive operation dispatch ---- *)
(* chains eval_graph_op → eval_pure_op → eval_pipeline_op → unknown fallback.
   all calls to eval go through !_eval_ref — the forward reference to the
   core evaluator defined in yantra_eval.ml. aliased as e_eval for brevity. *)

let eval_call (k : proof_graph) (e : env) (op : string) (args : expr list) : value =
  let e_eval = !_eval_ref in
  match eval_graph_op e_eval k e op args with
  | Some v -> v
  | None ->
    match !_eval_pure_op_raw e_eval k e op args with
    | Some v -> v
    | None ->
      match !_eval_pipeline_op_raw e_eval k e op args with
      | Some v -> v
      | None ->
        Printf.printf "eval: unknown operation '%s'\n%!" op;
        VNone
