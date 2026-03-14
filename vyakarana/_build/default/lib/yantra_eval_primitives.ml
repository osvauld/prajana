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

  (* outgoing-edges: node-name → [(source, relation, target)] outgoing only *)
  (* ancestors-of: node-name → [ancestor-names] via inheritance edges (vishesa/abheda/swarupa/dhatu).
     depth-limited to 4 hops (same as walk_inheritance). *)
  | "ancestors-of" ->
    let node_name = as_string (e_eval k e (List.nth args 0)) in
    let ancestors = Proof_graph.walk_inheritance k node_name in
    Some (VList (List.map (fun a -> VNode a) ancestors))

  | "outgoing-edges" ->
    let node_name = as_string (e_eval k e (List.nth args 0)) in
    let edges = List.filter (fun e -> e.source = node_name) !(k.all_edges) in
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

  (* in-degree: node-name → float (count of incoming edges) *)
  | "in-degree" ->
    let name = as_string (e_eval k e (List.nth args 0)) in
    Some (VFloat (float_of_int (Proof_graph.in_degree k name)))

  (* out-degree: node-name → float (count of outgoing edges) *)
  | "out-degree" ->
    let name = as_string (e_eval k e (List.nth args 0)) in
    Some (VFloat (float_of_int (Proof_graph.out_degree k name)))

  (* neighbors: node-name → [neighbor-names] (all adjacent nodes, in + out) *)
  | "neighbors" ->
    let name = as_string (e_eval k e (List.nth args 0)) in
    Some (VList (List.map (fun n -> VNode n) (Proof_graph.neighbors k name)))

  (* walk-chain: node × depth → [node-names]
     BFS N hops over kriya/phala/swarupa/abheda edges *)
  | "walk-chain" ->
    let name = as_string (e_eval k e (List.nth args 0)) in
    let depth = int_of_float (as_float (e_eval k e (List.nth args 1))) in
    Some (VList (List.map (fun n -> VNode n) (Setu.walk_chain k name depth [])))

  (* resolve-node: node-name → [node + abheda aliases] *)
  | "resolve-node" ->
    let name = as_string (e_eval k e (List.nth args 0)) in
    Some (VList (List.map (fun n -> VString n) (Setu.resolve k name)))

  (* incoming-to: node-name -> incoming typed edges [source, relation, target]. *)
  | "incoming-to" ->
    let name = as_string (e_eval k e (List.nth args 0)) in
    let edges = Proof_graph.edges_of k name in
    let incoming = List.filter_map (fun edge ->
      if edge.Proof_graph.target = name && edge.Proof_graph.source <> name then
        Some (VList [ VString edge.Proof_graph.source;
                      VString (Proof_graph.string_of_visheshanam edge.Proof_graph.relation);
                      VString edge.Proof_graph.target ])
      else
        None
    ) edges in
    Some (VList incoming)

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
        let domains_for node_name =
          match Hashtbl.find_opt k.nodes node_name with
          | None -> []
          | Some n ->
            let from_outgoing = List.filter_map (fun edge ->
              if edge.Proof_graph.source = node_name
                  && edge.Proof_graph.relation = Proof_graph.sthita
                 && is_domain_name edge.Proof_graph.target
              then Some edge.Proof_graph.target
              else None
            ) n.edges in
            let from_incoming = List.filter_map (fun edge ->
              if edge.Proof_graph.target = node_name && is_domain_name edge.Proof_graph.source
              then Some edge.Proof_graph.source
              else None
            ) (Proof_graph.edges_of k node_name) in
            from_outgoing @ from_incoming
        in
        let ancestors = Proof_graph.walk_inheritance k name in
        let all = own @ domains_for name @ List.concat_map domains_for ancestors in
        Some (VList (List.map (fun d -> VString d) (List.sort_uniq String.compare all))))

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
          && edge.Proof_graph.relation = Proof_graph.sthita
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

  (* abheda-of: node-name -> outgoing abheda targets. *)
  | "abheda-of" ->
    let name = as_string (e_eval k e (List.nth args 0)) in
    let targets =
      match Hashtbl.find_opt k.nodes name with
      | None -> []
      | Some n ->
        List.filter_map (fun edge ->
          if edge.Proof_graph.source = name
              && edge.Proof_graph.relation = Proof_graph.abheda
          then Some edge.Proof_graph.target
          else None
        ) n.edges
    in
    Some (VList (List.map (fun t -> VString t) (List.sort_uniq String.compare targets)))

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

  (* shabda: node × key → string — read shabda data (with inheritance) *)
  | "shabda" ->
    let node_name = as_string (e_eval k e (List.nth args 0)) in
    let key = as_string (e_eval k e (List.nth args 1)) in
    let pairs = Setu.read_shabda k node_name in
    Some (match List.find_opt (fun (k, _) -> k = key) pairs with
     | Some (_, v) -> VString v
     | None -> VNone)

  (* raw-shabda: node × key → string — own-node shabda only, no inheritance.
     use this when you need the node's own classification (role:, word:, name:)
     without bleed from IS-A ancestors. *)
  | "raw-shabda" ->
    let node_name = as_string (e_eval k e (List.nth args 0)) in
    let key = as_string (e_eval k e (List.nth args 1)) in
    let pairs = Setu_shabda.raw_shabda_for_node k node_name in
    Some (match List.assoc_opt key pairs with
     | Some v -> VString v
     | None -> VNone)

  (* node-layer: node-name → "kosha" | "bhasha" | "sangati" | ""
     reads n.layer directly — no inheritance, no shabda walk. *)
  | "node-layer" ->
    let name = as_string (e_eval k e (List.nth args 0)) in
    Some (match Proof_graph.find k name with
     | None -> VString ""
     | Some n -> VString n.Proof_graph.layer)

  (* node-slokas: node-name → [sloka-string, ...]
     returns the raw slokas list of a node as a list of strings.
     tantras use this to inspect the grammar structure of a node —
     e.g. filter for "-sthita" suffix to find vibhakti/kaala roots. *)
  | "node-slokas" ->
    let name = as_string (e_eval k e (List.nth args 0)) in
    Some (match Proof_graph.find k name with
     | None   -> VList []
     | Some n -> VList (List.map (fun s -> VString s) n.Proof_graph.slokas))

  (* shabda-pairs: node-name → [[key, value], ...]
     returns all key:value pairs from a node's shabda field as a list of
     [VString key, VString value] pairs. tantras use this to iterate over
     lookup tables stored in kosha nodes (e.g. goal-words, unit-aliases). *)
  | "shabda-pairs" ->
    let node_name = as_string (e_eval k e (List.nth args 0)) in
    let pairs = Setu.read_shabda k node_name in
    Some (VList (List.map (fun (k_s, v_s) ->
      VList [VString k_s; VString v_s]
    ) pairs))

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

  (* ppr: seed-pairs × target × binding-names → [(name, score)] sorted descending.
     calls the CSR-backed run_ppr. seed-pairs is a list of [VList[VString,VFloat]
     or VBinding(name,weight)]. binding-names is a list of VString.
     returns VList of VBinding(name, score) sorted by score descending. *)
  | "ppr" ->
    let seeds_v    = as_list (e_eval k e (List.nth args 0)) in
    let target     = as_string (e_eval k e (List.nth args 1)) in
    let bindings_v = as_list (e_eval k e (List.nth args 2)) in
    let seed_nodes = List.filter_map (fun v ->
      match v with
      | VList [VString nm; w]  -> Some (nm, as_float w)
      | VBinding (nm, w)        -> Some (nm, w)
      | VPair (nm, w)           -> Some (nm, as_float w)
      | _                       -> None
    ) seeds_v in
    let binding_names = List.filter_map (fun v ->
      match v with
      | VString s    -> Some s
      | VBinding (s,_) -> Some s
      | _              -> None
    ) bindings_v in
    let scores = Proof_graph.run_ppr k ~seed_nodes ~target ~binding_names in
    let pairs = Hashtbl.fold (fun name score acc -> (name, score) :: acc) scores [] in
    let sorted = List.sort (fun (_, a) (_, b) -> Float.compare b a) pairs in
    Some (VList (List.map (fun (nm, s) -> VBinding (nm, s)) sorted))

  (* graph-node-count: () → float — number of nodes in the proof graph *)
  | "graph-node-count" ->
    Some (VFloat (float_of_int (Hashtbl.length k.nodes)))

  (* graph-edge-count: () → float — number of edges in the proof graph *)
  | "graph-edge-count" ->
    Some (VFloat (float_of_int (List.length !(k.all_edges))))

  (* emit-node: name × layer × slokas × shabda → VNode
     creates or merges a node in the live graph. slokas is a list of strings.
     edges are decomposed from slokas using the current dimension registry.
     used by unit-generation tantra and learning tantras. *)
  | "emit-node" ->
    let name   = as_string (e_eval k e (List.nth args 0)) in
    let layer  = as_string (e_eval k e (List.nth args 1)) in
    let slokas = List.map as_string (as_list (e_eval k e (List.nth args 2))) in
    let shabda = as_string (e_eval k e (List.nth args 3)) in
    (* decompose slokas into edges using the full dimension registry *)
    let all_names = Hashtbl.fold (fun n _ acc -> n :: acc) k.nodes [] in
    let edges = List.concat_map (fun sloka ->
      let words = String.split_on_char ' ' sloka in
      List.filter_map (fun word ->
        let word = String.trim word in
        if String.length word = 0 then None
        else
          (* split at last '-' to find suffix *)
          let rec try_split i =
            if i <= 0 then None
            else if word.[i] = '-' then
              let suffix = String.sub word (i + 1) (String.length word - i - 1) in
              match Proof_graph.visheshanam_of_string suffix with
              | Some rel ->
                let target = String.sub word 0 i in
                Some { Proof_graph.source = name; target; relation = rel }
              | None -> try_split (i - 1)
            else try_split (i - 1)
          in
          try_split (String.length word - 1)
      ) words
    ) slokas in
    let n : Proof_graph.nigamana = {
      name; layer; slokas; edges;
      satya = 0.0; shabda;
    } in
    ignore (Proof_graph.join k n);
    (* update satya for this node *)
    let r = Proof_graph.raw_satya n in
    Hashtbl.replace k.nodes name { n with satya = r };
    ignore all_names;
    Some (VNode name)

  (* register-dimension: name → int index
     registers a new graph dimension at runtime. idempotent. *)
  | "register-dimension" ->
    let name = as_string (e_eval k e (List.nth args 0)) in
    let idx = Proof_graph.register_dimension name in
    Some (VFloat (float_of_int idx))

  (* dimension-count: () → float — current number of dimensions *)
  | "dimension-count" ->
    Some (VFloat (float_of_int (Proof_graph.dimension_count ())))

  (* dim-vector: unit-name → [M, L, T, I, θ, N, J, scale]
     reads the SI dimension exponent vector from matra-aayaama.
     the exponent vector IS the unit. kramanusara depth = |T exponent|. *)
  | "dim-vector" ->
    let unit_name = as_string (e_eval k e (List.nth args 0)) in
    let pairs = Setu.read_shabda k "matra-aayaama" in
    Some (match List.find_opt (fun (name, _) -> name = unit_name) pairs with
     | Some (_, dims_str) ->
       let parts = String.split_on_char ' ' (String.trim dims_str)
         |> List.filter (fun s -> String.length s > 0) in
       VList (List.map (fun s ->
         match float_of_string_opt s with Some f -> VFloat f | None -> VFloat 0.0
       ) parts)
     | None -> VNone)

  (* dim-op: vector-a × vector-b × op → result-vector
     op = "mul" → add exponents, multiply scales
     op = "div" → subtract exponents, divide scales
     op = "kramanusara" → subtract [0,0,1,0,0,0,0] from vector-a (d/dt)
     op = "sama-kalana" → add [0,0,1,0,0,0,0] to vector-a (∫dt)
     the result IS the unit of the composed quantity. *)
  | "dim-op" ->
    let va = as_list (e_eval k e (List.nth args 0)) in
    let vb = if List.length args > 1 then as_list (e_eval k e (List.nth args 1)) else [] in
    let op_name = if List.length args > 2 then as_string (e_eval k e (List.nth args 2))
      else if List.length args > 1 then as_string (e_eval k e (List.nth args 1))
      else "" in
    let fa = List.map as_float va in
    let fb = List.map as_float vb in
    let n = 8 in (* M L T I θ N J scale *)
    let pad lst = let len = List.length lst in
      if len >= n then lst
      else lst @ List.init (n - len) (fun i -> if i = n - len - 1 then 1.0 else 0.0) in
    let fa = pad fa in
    let fb = pad fb in
    let result = match op_name with
      | "mul" ->
        (* add exponents for dims 0-6, multiply scales *)
        List.mapi (fun i a ->
          let b = List.nth fb i in
          if i < 7 then a +. b else a *. b
        ) fa
      | "div" ->
        (* subtract exponents for dims 0-6, divide scales *)
        List.mapi (fun i a ->
          let b = List.nth fb i in
          if i < 7 then a -. b else if b <> 0.0 then a /. b else a
        ) fa
      | "kramanusara" ->
        (* d/dt: subtract 1 from T exponent (index 2) *)
        List.mapi (fun i a -> if i = 2 then a -. 1.0 else a) fa
      | "sama-kalana" ->
        (* ∫dt: add 1 to T exponent (index 2) *)
        List.mapi (fun i a -> if i = 2 then a +. 1.0 else a) fa
      | "pow" ->
        (* raise to power: multiply all exponents by scalar, raise scale to power *)
        let exp = List.nth fb 0 in
        List.mapi (fun i a ->
          if i < 7 then a *. exp else Float.pow a exp
        ) fa
      | "inv" ->
        (* invert: negate exponents, reciprocal scale *)
        List.mapi (fun i a ->
          if i < 7 then (-. a) else if a <> 0.0 then 1.0 /. a else 0.0
        ) fa
      | _ -> fa
    in
    Some (VList (List.map (fun f -> VFloat f) result))

  (* dim-to-unit: vector → unit-name
     reverse lookup: find the unit whose exponent vector matches.
     compares only the 7 dimension exponents (not scale). *)
  | "dim-to-unit" ->
    let vr = as_list (e_eval k e (List.nth args 0)) in
    let fr = List.map as_float vr in
    let target_dims = if List.length fr >= 7 then
      List.filteri (fun i _ -> i < 7) fr else fr in
    let pairs = Setu.read_shabda k "matra-aayaama" in
    let match_unit = List.find_opt (fun (_, dims_str) ->
      let parts = String.split_on_char ' ' (String.trim dims_str)
        |> List.filter (fun s -> String.length s > 0) in
      let dims = List.filteri (fun i _ -> i < 7)
        (List.map (fun s -> match float_of_string_opt s with
           | Some f -> f | None -> 0.0) parts) in
      List.length dims = List.length target_dims &&
      List.for_all2 (fun a b -> Float.equal a b) dims target_dims
    ) pairs in
    Some (match match_unit with
     | Some (name, _) -> VString name
     | None ->
       (* build a human-readable dimension string *)
       let dim_names = [|"M"; "L"; "T"; "I"; "\xce\xb8"; "N"; "J"|] in
       let parts = List.mapi (fun i exp ->
         if Float.equal exp 0.0 then ""
         else if Float.equal exp 1.0 then dim_names.(i)
         else Printf.sprintf "%s^%g" dim_names.(i) exp
       ) target_dims |> List.filter (fun s -> String.length s > 0) in
       if parts = [] then VString "dimensionless"
       else VString (String.concat "\xc2\xb7" parts))

  (* dim-kramanusara-depth: vector → float
     returns the absolute value of the T exponent — how many times
     rate-of-change has been applied. *)
  | "dim-kramanusara-depth" ->
    let v = as_list (e_eval k e (List.nth args 0)) in
    let floats = List.map as_float v in
    let t_exp = if List.length floats > 2 then List.nth floats 2 else 0.0 in
    Some (VFloat (Float.abs t_exp))

  (* word-node: word → node-name or VNone
     O(1) lookup in the word_index built from all nodes' word: shabda keys.
     "word-node "squared"" → "square", "word-node "was"" → "copula-was" *)
  | "word-node" ->
    let word = as_string (e_eval k e (List.nth args 0)) in
    Some (match !eval_ctx with
     | Some ctx ->
       (match Hashtbl.find_opt ctx.ctx_index.word_index word with
        | Some node_name -> VString node_name
        | None -> VNone)
     | None -> VNone)

  (* call-tantra: tantra-name × [arg-vals] → value
     calls a tantra by name, mapping args positionally to tantra inputs.
     enables tantras to invoke other tantras by name at runtime. *)
  | "call-tantra" ->
    let tname = as_string (e_eval k e (List.nth args 0)) in
    let arg_list = as_list (e_eval k e (List.nth args 1)) in
    Some (match !eval_ctx with
     | Some ctx ->
       (match Hashtbl.find_opt ctx.ctx_index.by_name tname with
        | None -> VNone
        | Some t ->
          let input_values = List.mapi (fun i v ->
            let param_name = if i < List.length t.t_inputs
              then (List.nth t.t_inputs i).tp_name
              else Printf.sprintf "arg%d" i in
            (param_name, v)
          ) arg_list in
          !_eval_tantra_ref k t input_values)
     | None -> VNone)

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
        (* helper: apply a primitive op by name to a list of values *)
        let apply_op_vals prim_name op_args =
          let lifted = List.map (fun v -> match v with
            | VFloat f -> Lit f
            | VString s -> StrLit s
            | VBool b -> BoolLit b
            | _ -> Lit (as_float v)) op_args in
          match !_eval_pure_op_raw e_eval k e prim_name lifted with
          | Some v -> v
          | None ->
            (match eval_graph_op e_eval k e prim_name lifted with
             | Some v -> v
             | None -> VNone)
        in
        (match op with

        (* execute-chain: mantra-name × [arg-vals] → value
           runs a stack machine over the krama edges of a mantra node.
           krama edges are read in node-edge-list order (= file order).
           stack starts with args reversed (first arg at bottom, last at top). *)
        | "execute-chain" ->
          let mantra_name = as_string (e_eval k e (List.nth args 0)) in
          let arg_vals = as_list (e_eval k e (List.nth args 1)) in
          (match Proof_graph.find k mantra_name with
           | None -> VString ("no-mantra-" ^ mantra_name)
           | Some n ->
             (match Proof_graph.visheshanam_of_string "krama" with
              | None -> VString "krama-not-registered"
              | Some krama_rel ->
                let steps = List.filter_map (fun edge ->
                  if edge.source = mantra_name && edge.relation = krama_rel
                  then Some edge.target else None
                ) n.edges in
                let stack = ref (List.rev arg_vals) in
                let pop () = match !stack with
                  | v :: rest -> stack := rest; v
                  | [] -> VFloat 0.0
                in
                let get_shabda_key node_name key =
                  match Proof_graph.find k node_name with
                  | None -> None
                  | Some op_n ->
                    let sh = Setu_shabda.parse_shabda op_n.shabda in
                    List.assoc_opt key sh
                in
                List.iter (fun step_name ->
                  let arity = match get_shabda_key step_name "arity" with
                    | Some s -> (try int_of_string (String.trim s) with _ -> 1)
                    | None -> 1
                  in
                  let prim_name = match get_shabda_key step_name "eval" with
                    | Some s -> String.trim s
                    | None -> step_name
                  in
                  let op_args = List.init arity (fun _ -> pop ()) in
                  let result = apply_op_vals prim_name op_args in
                  stack := result :: !stack
                ) steps;
                (match !stack with v :: _ -> v | [] -> VNone)))

        (* apply-op: op-name × [arg-vals] → value
           looks up eval: name from op node's shabda, then dispatches. *)
        | "apply-op" ->
          let op_name = as_string (e_eval k e (List.nth args 0)) in
          let op_args_v = as_list (e_eval k e (List.nth args 1)) in
          let prim_name = match Proof_graph.find k op_name with
            | None -> op_name
            | Some n ->
              let sh = Setu_shabda.parse_shabda n.shabda in
              (match List.assoc_opt "eval" sh with
               | Some s -> String.trim s
               | None -> op_name)
          in
          apply_op_vals prim_name op_args_v

        (* tantra-by-name fallback: if op matches a loaded tantra, call it *)
        | _ ->
          (match !eval_ctx with
           | Some ctx ->
             (match Hashtbl.find_opt ctx.ctx_index.by_name op with
              | Some t ->
                let arg_vals = List.map (e_eval k e) args in
                let input_values = List.mapi (fun i v ->
                  let param_name = if i < List.length t.t_inputs
                    then (List.nth t.t_inputs i).tp_name
                    else Printf.sprintf "arg%d" i in
                  (param_name, v)
                ) arg_vals in
                !_eval_tantra_ref k t input_values
              | None ->
                Printf.printf "eval: unknown operation '%s'\n%!" op;
                VNone)
           | None ->
               Printf.printf "eval: unknown operation '%s'\n%!" op;
              VNone))

(* ---- register_primitive_arities ----------------------------------------
   ONE SOURCE OF TRUTH for every primitive arity.
   Called once from yantra_eval.ml during init.
   Adding a new primitive: add the implementation above AND an entry here.
   Never add arities anywhere else. *)
let register_primitive_arities () =
  let r = Yantra_arity.register_graph_op_arity in
  (* boundary keywords — structural delimiters always stop argument collection *)
  let b = Yantra_arity.register_boundary_keyword in
  List.iter b [")" ; "]" ; "," ; "in" ; "done" ; "let" ; "otherwise"];
  (* scan construct keywords *)
  List.iter b ["when" ; "emit" ; "set" ; "clear" ; "return"];
  (* from construct keywords *)
  List.iter b ["where" ; "collect" ; "with"];
  (* graph ops *)
  r "lookup"              1;   (* name → node or VNone *)
  r "walk"                2;   (* node rel → [nodes] *)
  r "walk-in"             2;   (* node rel → [nodes] inbound *)
  r "has"                 2;   (* node rel → bool *)
  r "edges"               1;   (* node → [(src,rel,tgt)] *)
  r "outgoing-edges"      1;   (* node → outgoing edges only *)
  r "ancestors-of"        1;   (* node → [ancestor-names] *)
  r "all-edges"          (-1); (* () → all edges *)
  r "in-degree"           1;   (* node → float *)
  r "out-degree"          1;   (* node → float *)
  r "neighbors"           1;   (* node → [names] *)
  r "walk-chain"          2;   (* node depth → [names] *)
  r "resolve-node"        1;   (* node → [names] *)
  r "ppr"                 3;   (* seeds target bindings → [(name,score)] *)
  r "emit-node"           4;   (* name layer slokas shabda → VNode *)
  r "register-dimension"  1;   (* name → float *)
  r "dimension-count"    (-1); (* () → float *)
  r "graph-node-count"   (-1); (* () → float *)
  r "graph-edge-count"   (-1); (* () → float *)
  (* field accessors *)
  r "shabda"              2;   (* node key → string *)
  r "raw-shabda"          2;   (* node key → own-only string *)
  r "shabda-pairs"        1;   (* node → [[key,val],...] *)
  r "node-layer"          1;   (* node → "kosha"|"bhasha"|"sangati" *)
  r "node-slokas"         1;   (* node → [sloka-string,...] *)
  r "word-node"           1;   (* word → node or VNone *)
  r "lookup-word"         1;   (* word → node via bhasha word: key *)
  (* pipeline ops *)
  r "execute-chain"       2;   (* mantra args → value *)
  r "apply-op"            2;   (* op-name args → value *)
  r "call-tantra"         2;   (* tantra-name [args] → value *)
  r "split-numeric"       1;   (* "5kg" → ["5.0","kg"] *)
  r "find-context"        1;   (* graph → context *)
  r "scene-extract"       1;   (* sentence → VNode root *)
  r "scene-narrate"       1;   (* VNode root → VString *)
  r "dim-vector"          1;   (* unit → [M,L,T,...] *)
  r "dim-op"              3;   (* vec-a vec-b op → vec *)
  r "dim-to-unit"         1;   (* vec → unit-name *)
  r "dim-kramanusara-depth" 1; (* vec → float *)
  (* math *)
  r "square"              1;   (* x → x² *)
  r "half"                1;   (* x → x/2 *)
  r "double"              1;   (* x → x*2 *)
  r "abs"                 1;   (* float → float *)
  r "sqrt"                1;   (* float → float *)
  r "floor"               1;   (* float → float *)
  r "ceil"                1;   (* float → float *)
  r "sum"                 1;   (* [list] → float *)
  r "frequencies"         1;   (* [list] → [[val,count],...] *)
  (* logic *)
  r "not"                 1;   (* bool → bool *)
  r "exists"              1;   (* value → bool *)
  r "eq"                  2;   (* a b → bool *)
  r "neq"                 2;   (* a b → bool *)
  r "lt"                  2;   (* a b → bool *)
  r "le"                  2;   (* a b → bool *)
  r "gt"                  2;   (* a b → bool *)
  r "ge"                  2;   (* a b → bool *)
  r "and"                 2;   (* a b → bool *)
  r "or"                  2;   (* a b → bool *)
  (* string *)
  r "string-length"       1;   (* string → float *)
  r "to-string"           1;   (* value → string *)
  r "to-number"           1;   (* string → float *)
  r "concat"             (-1); (* variadic string concat *)
  r "substr"              3;   (* string start len → string *)
  r "starts-with"         2;   (* string prefix → bool *)
  r "ends-with"           2;   (* string suffix → bool *)
  r "split"               2;   (* string delim → list *)
  r "join"                2;   (* list sep → string *)
  r "char-at"             2;   (* string idx → char *)
  (* list *)
  r "nth"                 2;   (* list idx → element *)
  r "length"              1;   (* list → float *)
  r "append"              2;   (* list item → list *)
  r "flatten"             1;   (* [[...]] → [...] *)
  r "unique"              1;   (* list → dedup *)
  r "member"              2;   (* value list → bool *)
  r "range"               1;   (* n → [0..n-1] *)
  r "map"                 2;   (* list fn → list *)
  r "filter"              2;   (* list fn → list *)
  r "reduce"              3;   (* list init fn → value *)
  r "fixpoint"            2;   (* state fn → stable-state *)
  r "iterate"             3;   (* n state fn → state *)
  (* arithmetic *)
  r "add"                (-1); (* variadic add *)
  r "mul"                (-1); (* variadic mul *)
  r "sub"                 2;   (* a b → float *)
  r "div"                 2;   (* a b → float *)
  r "mod"                 2;   (* a b → float *)
  r "max"                 2;   (* a b → float *)
  r "min"                 2;   (* a b → float *)
  r "pow"                 2    (* base exp → float *)

