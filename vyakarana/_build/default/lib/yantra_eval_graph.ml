(* yantra_eval_graph.ml — eval_graph_op: graph, field-accessor, and context operations.
   extracted from yantra_eval_primitives for readability.
   depends on Yantra_eval_context for the shared runtime refs. *)

open Proof_graph
open Yantra_types
open Yantra_eval_context

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
