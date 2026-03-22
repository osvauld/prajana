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

   dependency: Proof_graph, Yantra_types, Setu, Anuvada. *)

open Proof_graph
open Yantra_types

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

(* ---- with_node: collapse the node_lookup match ----
   Before (14+ occurrences, always 3–5 lines):
     match Hashtbl.find_opt k.nodes name with
     | None -> default
     | Some n -> f n
   After:
     with_node k name default (fun n -> ...) *)

let with_node (k : proof_graph) (name : string) (default : 'a)
    (f : Proof_graph.nigamana -> 'a) : 'a =
  match Proof_graph.find k name with
  | None   -> default
  | Some n -> f n

(* ---- call_tantra_opt: collapse the find_opt by_name + eval_tantra pattern ----
   Before (8+ occurrences):
     match !eval_ctx with
     | Some ctx ->
       (match Hashtbl.find_opt ctx.ctx_index.by_name name with
        | Some t -> !_eval_tantra_ref k t inputs
        | None -> default)
     | None -> default
   After:
     call_tantra_opt k name inputs ~default *)

let call_tantra_opt (k : proof_graph) (name : string)
    (inputs : (string * value) list) ~(default : value) : value =
  match !eval_ctx with
  | Some ctx ->
    (match Hashtbl.find_opt ctx.ctx_index.by_name name with
     | Some t -> !_eval_tantra_ref k t inputs
     | None   -> default)
  | None -> default

(* ---- eval_graph_op: graph, field-accessor, and context operations ---- *)

let eval_graph_op (e_eval : proof_graph -> env -> expr -> value)
    (k : proof_graph) (e : env) (op : string) (args : expr list) : value option =
  let (eval_arg, eval_str, eval_flt, eval_lst, eval_int) =
    make_eval_arg e_eval k e args in
  ignore (eval_arg, eval_flt, eval_lst, eval_int); (* silence unused-var warnings for ops that don't use all *)
  match op with

  (* lookup: string → VNode if found, VNone if not — raw table hit only *)
  | "lookup" ->
    let name = eval_str 0 in
    Some (match Proof_graph.find k name with
     | Some _ -> VNode name
     | None   -> VNone)

  (* walk: node × relation → [node] — follow edges of a given type *)
  | "walk" ->
    let node_name = eval_str 0 in
    let rel_name = eval_str 1 in
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
    let node_name = eval_str 0 in
    let rel_name = eval_str 1 in
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

  (* ---- om-* primitives: deduplicated edge walkers for om graph interfacing ----
     the om graph stores edges via slokas; a node may declare the same edge
     multiple times (e.g. "mass-janya velocity-janya" in two slokas).
     walk returns duplicates. om-* deduplicates by target name so tantras
     get clean contract lists.

     dedup_walk: shared helper — walk outgoing edges of rel, unique targets *)
  | "om-janya" | "om-phala" | "om-kriya" | "om-yukta"
  | "om-sthita" | "om-swarupa" | "om-abheda" ->
    let node_name = eval_str 0 in
    let rel_name = String.sub op 3 (String.length op - 3) in (* strip "om-" prefix *)
    let rel = Proof_graph.visheshanam_of_string rel_name in
    Some (match rel with
     | None -> VList []
     | Some vish ->
       let edges = Proof_graph.edges_of k node_name in
       let seen = Hashtbl.create 8 in
       let targets = List.filter_map (fun edge ->
         if edge.relation = vish && edge.source = node_name
            && not (Hashtbl.mem seen edge.target) then begin
           Hashtbl.replace seen edge.target true;
           Some (VNode edge.target)
         end else None
       ) edges in
       VList targets)

  (* om-contract: node-name → [janya, phala, kriya, yukta, sthita, swarupa, abheda]
     returns all seven suffix-typed edge lists in one call, all deduplicated.
     one graph-touch instead of seven — used by generic match-mantra walker. *)
  | "om-contract" ->
    let node_name = eval_str 0 in
    let edges = Proof_graph.edges_of k node_name in
    let dedup rel_name =
      let rel = Proof_graph.visheshanam_of_string rel_name in
      match rel with
      | None -> VList []
      | Some vish ->
        let seen = Hashtbl.create 8 in
        VList (List.filter_map (fun edge ->
          if edge.relation = vish && edge.source = node_name
             && not (Hashtbl.mem seen edge.target) then begin
            Hashtbl.replace seen edge.target true;
            Some (VNode edge.target)
          end else None
        ) edges)
    in
    Some (VList [dedup "janya"; dedup "phala"; dedup "kriya";
                 dedup "yukta"; dedup "sthita"; dedup "swarupa";
                 dedup "abheda"])

  (* has: node × edge-pattern → bool
     edge-pattern is "relation-target" e.g. "matra-sthita" *)
  | "has" ->
    let node_name = eval_str 0 in
    let pattern = eval_str 1 in
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
    let node_name = eval_str 0 in
    let edges = Proof_graph.edges_of k node_name in
    Some (VList (List.map (fun edge ->
      VList [VString edge.source;
             VString (Proof_graph.string_of_visheshanam edge.relation);
             VString edge.target]
    ) edges))



  (* neighbors: node-name → [neighbor-names] (all adjacent nodes, in + out) *)
  | "neighbors" ->
    let name = eval_str 0 in
    Some (VList (List.map (fun n -> VNode n) (Proof_graph.neighbors k name)))





  (* avrti: seed-names × max-passes -> flat triples [source-raw, relation-name, [target-raws]] *)
  | "avrti" ->
    let seeds = eval_lst 0 in
    let max_passes = eval_int 1 in
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
    let v = eval_arg 0 in
    let word = as_string v in
    let pairs = Setu.read_shabda k "english-grammar" in
    Some (match List.find_opt (fun (w, _) -> w = word) pairs with
     | Some (_, rel) -> VString rel
     | None -> VNone)

  (* shabda: node × key → string — read shabda data (with inheritance) *)
  | "shabda" ->
    let node_name = eval_str 0 in
    let key = eval_str 1 in
    let pairs = Setu.read_shabda k node_name in
    Some (match List.find_opt (fun (k, _) -> k = key) pairs with
     | Some (_, v) -> VString v
     | None -> VNone)


  (* node-layer: node-name → "kosha" | "bhasha" | "sangati" | ""
     reads n.layer directly — no inheritance, no shabda walk. *)
  | "node-layer" ->
    let name = eval_str 0 in
    Some (with_node k name (VString "") (fun n -> VString n.Proof_graph.layer))

  (* node-slokas: node-name → [sloka-string, ...]
     returns the raw slokas list of a node as a list of strings.
     tantras use this to inspect the grammar structure of a node —
     e.g. filter for "-sthita" suffix to find vibhakti/kaala roots. *)
  | "node-slokas" ->
    let name = eval_str 0 in
    Some (with_node k name (VList []) (fun n ->
      VList (List.map (fun s -> VString s) n.Proof_graph.slokas)))


  (* exists: value → bool — true unless VNone or empty *)
  | "exists" ->
    Some (VBool (as_bool (eval_arg 0)))


  (* ppr: seed-pairs × target × binding-names → [(name, score)] sorted descending.
     calls the CSR-backed run_ppr. seed-pairs is a list of [VList[VString,VFloat]
     or VBinding(name,weight)]. binding-names is a list of VString.
     returns VList of VBinding(name, score) sorted by score descending. *)
  | "ppr" ->
    let seeds_v    = eval_lst 0 in
    let target     = eval_str 1 in
    let bindings_v = eval_lst 2 in
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

  (* emit-node: name × layer × slokas × shabda → VNode
     creates or merges a node in the live graph. slokas is a list of strings.
     edges are decomposed from slokas using the current dimension registry.
     used by unit-generation tantra and learning tantras. *)
  | "emit-node" ->
    let name   = eval_str 0 in
    let layer  = eval_str 1 in
    let slokas = List.map as_string (eval_lst 2) in
    let shabda = eval_str 3 in
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
      satya = 0.0; shabda; krama = "";
    } in
    ignore (Proof_graph.join k n);
    (* update satya for this node *)
    let r = Proof_graph.raw_satya n in
    Hashtbl.replace k.nodes name { n with satya = r };
    ignore all_names;
    Some (VNode name)

  (* emit-edge: source × relation × target → VNode source
     adds a single typed edge to the live graph. idempotent via join.
     used by boot/reboot tantras to add derived structural edges. *)
  | "emit-edge" ->
    let source   = eval_str 0 in
    let rel_name = eval_str 1 in
    let target   = eval_str 2 in
    (match Proof_graph.visheshanam_of_string rel_name with
     | None -> Some VNone
     | Some rel ->
       let edge : Proof_graph.typed_edge = { source; target; relation = rel } in
       (* join a minimal nigamana carrying just this edge *)
       let n : Proof_graph.nigamana = {
         name = source; layer = "kosha"; slokas = []; edges = [edge];
         satya = 0.0; shabda = ""; krama = "";
       } in
       ignore (Proof_graph.join k n);
       Some (VNode source))

  (* dim-vector: unit-name → [M, L, T, I, θ, N, J, scale]
     reads the SI dimension exponent vector from matra-aayaama.
     the exponent vector IS the unit. kramanusara depth = |T exponent|. *)
  | "dim-vector" ->
    let unit_name = eval_str 0 in
    let pairs = Setu.read_shabda k "matra-aayaama" in
    Some (match List.find_opt (fun (name, _) -> name = unit_name) pairs with
     | Some (_, dims_str) ->
       let parts = String.split_on_char ' ' (String.trim dims_str)
         |> List.filter (fun s -> String.length s > 0) in
       VList (List.map (fun s ->
         match float_of_string_opt s with Some f -> VFloat f | None -> VFloat 0.0
       ) parts)
     | None -> VNone)

  (* word-node: word → node-name or VNone
     O(1) lookup in the word_index built from all nodes' word: shabda keys.
     "word-node "squared"" → "square", "word-node "was"" → "copula-was" *)
  | "word-node" ->
    let word = eval_str 0 in
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
    let tname = eval_str 0 in
    let arg_list = eval_lst 1 in
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

        (* apply-op: op-name × [arg-vals] → value
           looks up eval: name from op node's shabda, then dispatches. *)
        | "apply-op" ->
          let op_name = as_string (e_eval k e (List.nth args 0)) in
          let op_args_v = as_list (e_eval k e (List.nth args 1)) in
          let prim_name =
            let sh = Setu_shabda.raw_shabda_for_node k op_name in
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
  (* from construct keywords *)
  List.iter b ["where" ; "collect" ; "with"];
  (* graph ops *)
  r "lookup"              1;   (* name → node or VNone *)
  r "walk"                2;   (* node rel → [nodes] *)
  r "walk-in"             2;   (* node rel → [nodes] inbound *)
  r "has"                 2;   (* node rel → bool *)
  r "edges"               1;   (* node → [(src,rel,tgt)] *)
  r "neighbors"           1;   (* node → [names] *)
  r "ppr"                 3;   (* seeds target bindings → [(name,score)] *)
  r "emit-node"           4;   (* name layer slokas shabda → VNode *)
  r "emit-edge"           3;   (* source relation target → VNode source *)
  (* om-* primitives — deduplicated edge walkers *)
  r "om-janya"            1;
  r "om-phala"            1;
  r "om-kriya"            1;
  r "om-yukta"            1;
  r "om-sthita"           1;
  r "om-swarupa"          1;
  r "om-abheda"           1;
  r "om-contract"         1;
  (* field accessors *)
  r "shabda"              2;   (* node key → string *)
  r "node-layer"          1;   (* node → "kosha"|"bhasha"|"sangati" *)
  r "node-slokas"         1;   (* node → [sloka-string,...] *)
  r "word-node"           1;   (* word → node or VNone *)
  r "lookup-word"         1;   (* word → node via bhasha word: key *)
  (* pipeline ops *)
  r "apply-op"            2;   (* op-name args → value *)
  r "call-tantra"         2;   (* tantra-name [args] → value *)
  r "split-numeric"       1;   (* "5kg" → ["5.0","kg"] *)
  r "find-context"        1;   (* graph → context *)
  r "scene-extract"       1;   (* sentence → VNode root *)
  r "scene-narrate"       1;   (* VNode root → VString *)
  r "dim-vector"          1;   (* unit → [M,L,T,...] *)
  (* math *)
  r "square"              1;   (* x → x² *)
  r "half"                1;   (* x → x/2 *)
  r "double"              1;   (* x → x*2 *)
  r "reciprocal"          1;   (* x → 1/x *)
  r "abs"                 1;
  r "sqrt"                1;
  r "floor"               1;
  r "ceil"                1;
  r "sum"                 1;   (* [list] → float *)
  (* logic *)
  r "not"                 1;   (* bool → bool *)
  r "exists"              1;   (* value → bool *)
  r "eq"                  2;
  r "neq"                 2;
  r "lt"                  2;
  r "gt"                  2;
  r "and"                (-1); (* variadic *)
  r "or"                 (-1); (* variadic *)
  (* string *)
  r "string-length"       1;
  r "to-string"           1;
  r "to-number"           1;
  r "concat"             (-1); (* variadic *)
  r "substr"              3;
  r "starts-with"         2;
  r "ends-with"           2;
  r "split"               2;
  r "join"                2;
  r "char-at"             2;
  (* list *)
  r "nth"                 2;
  r "length"              1;
  r "append"              2;
  r "flatten"             1;
  r "unique"              1;
  r "member"              2;
  r "range"               1;
  r "map"                 2;
  r "filter"              2;
  r "reduce"              3;
  r "fixpoint"            2;
  r "iterate"             3;
  (* arithmetic *)
  r "add"                (-1); (* variadic *)
  r "mul"                (-1); (* variadic *)
  r "sub"                 2;
  r "div"                 2;
  r "max"                 2;
  r "min"                 2;
  r "power"               2

