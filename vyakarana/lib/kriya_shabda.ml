(* kriya_shabda.ml — word/shabda resolution and unit decomposition.
   Extracted from kriya_graph.ml.

   Handles: word-node, word-node-candidates, word-node-compound,
   decompose-unit, concept-display, capitalize-first, dim-vector. *)

open Prakriti
open Kriya_types

let call_tantra_opt (k : proof_graph) (name : string)
    (inputs : (string * value) list) ~(default : value) : value =
  match Domain.DLS.get _eval_ctx with
  | Some ctx ->
    (match Hashtbl.find_opt ctx.ctx_index.by_name name with
     | Some t -> (Atomic.get _engine).eval_tantra k t inputs
     | None   -> default)
  | None -> default

let eval_shabda_op
    (e_eval : Prakriti.proof_graph -> Kriya_types.env -> Kriya_types.expr -> Kriya_types.value)
    (k : proof_graph) (e : env) (op : string) (args : expr list)
    : value option =
  let (_eval_arg, eval_str, _eval_flt, _eval_lst, _eval_int) =
    make_eval_arg e_eval k e args in

  match op with
  | "concept-display" ->
    let name = eval_str 0 in
    Some (VString (String.concat " " (String.split_on_char '-' name)))

  | "capitalize-first" ->
    let s = eval_str 0 in
    let s = String.trim s in
    if String.length s = 0 then Some (VString "")
    else
      let c = Char.uppercase_ascii s.[0] in
      Some (VString (String.make 1 c ^ String.sub s 1 (String.length s - 1)))

  | "dim-vector" ->
    let unit_name = eval_str 0 in
    let pairs = Vidya.read_shabda k "matra-aayaama" in
    Some (match List.find_opt (fun (name, _) -> name = unit_name) pairs with
     | Some (_, dims_str) ->
       let parts = String.split_on_char ' ' (String.trim dims_str)
         |> List.filter (fun s -> String.length s > 0) in
       VList (List.map (fun s ->
         match float_of_string_opt s with Some f -> VFloat f | None -> VFloat 0.0
       ) parts)
     | None -> VNone)

  | "word-node" ->
    let word = eval_str 0 in
    let naama_dim = match visheshanam_of_string "naama" with
      | Some d -> d | None -> -1 in
    let mudra_dim = match visheshanam_of_string "naama-mudra" with
      | Some d -> d | None -> -1 in
    if naama_dim < 0 then Some VNone
    else begin
      (* step 1: CSR walk-in via naama (full word forms, case-insensitive) *)
      let candidates = csr_walk_in_by_rel k word naama_dim in
      let candidates = if candidates = [] then
        let lower = String.lowercase_ascii word in
        if lower <> word then csr_walk_in_by_rel k lower naama_dim
        else []
      else candidates in
      (* step 2: CSR walk-in via naama-mudra (symbols, case-sensitive) *)
      let candidates = if candidates = [] && mudra_dim >= 0 then
        let mudra = csr_walk_in_by_rel k word mudra_dim in
        if mudra = [] then
          let lower = String.lowercase_ascii word in
          if lower <> word then csr_walk_in_by_rel k lower mudra_dim
          else []
        else mudra
      else candidates in
      let candidates = List.sort_uniq String.compare candidates in
      Some (match candidates with
       | [single] -> VString single
       | _ :: _ ->
         (* multiple candidates: PPR disambiguation *)
         (match Domain.DLS.get _eval_ctx with
          | Some ctx ->
            let best = List.fold_left (fun (best_name, best_score) name ->
              let ppr_score = match Hashtbl.find_opt ctx.ctx_ppr name with
                | Some s -> s | None -> 0.0 in
              if ppr_score > best_score then (name, ppr_score)
              else (best_name, best_score)
            ) ("", -1.0) candidates in
            VString (fst best)
          | None -> VString (List.hd candidates))
       | [] ->
         (* step 3: direct node name match — fallback when no naama edges *)
         match Prakriti.find k word with
         | Some _ -> VString word
         | None ->
           let lower = String.lowercase_ascii word in
           if lower <> word then
             match Prakriti.find k lower with
             | Some _ -> VString lower | None -> VNone
           else VNone)
    end

  | "word-node-candidates" ->
    (* return ALL candidate nodes for a word — naama first, then naama-mudra,
       then direct name as fallback *)
    let word = eval_str 0 in
    let naama_dim = match visheshanam_of_string "naama" with
      | Some d -> d | None -> -1 in
    let mudra_dim = match visheshanam_of_string "naama-mudra" with
      | Some d -> d | None -> -1 in
    if naama_dim < 0 then Some (VList [])
    else begin
      let candidates = csr_walk_in_by_rel k word naama_dim in
      let candidates = if candidates = [] then
        let lower = String.lowercase_ascii word in
        if lower <> word then csr_walk_in_by_rel k lower naama_dim
        else []
      else candidates in
      let candidates = if candidates = [] && mudra_dim >= 0 then
        let mudra = csr_walk_in_by_rel k word mudra_dim in
        if mudra = [] then
          let lower = String.lowercase_ascii word in
          if lower <> word then csr_walk_in_by_rel k lower mudra_dim
          else []
        else mudra
      else candidates in
      (* fallback: direct name match when no naama/mudra edges found *)
      let candidates = if candidates = [] then
        match find k word with Some _ -> [word] | None ->
          let lower = String.lowercase_ascii word in
          if lower <> word then
            match find k lower with Some _ -> [lower] | None -> []
          else []
      else candidates in
      let deduped = List.sort_uniq String.compare candidates in
      Some (VList (List.map (fun s -> VString s) deduped))
    end

  | "decompose-unit" ->
    (* step-108: decompose a symbol like "km","kPa","MHz" into prefix+base.
       (1) full string via naama-mudra → if single match, not a compound, return VNone.
       (2) for each split i=1..len-1: left via naama-mudra check sthita:upasarga,
           right via naama-mudra check sthita:matra or matra-beeja.
       (3) return VList [VString prefix; VString base; VString exponent] or VNone. *)
    let sym = eval_str 0 in
    let mudra_dim = match visheshanam_of_string "naama-mudra" with
      | Some d -> d | None -> -1 in
    let sthita_dim = match visheshanam_of_string "sthita" with
      | Some d -> d | None -> -1 in
    let sankhya_dim = match visheshanam_of_string "sankhya" with
      | Some d -> d | None -> -1 in
    if mudra_dim < 0 || sthita_dim < 0 then Some VNone
    else begin
      let len = String.length sym in
      if len < 2 then Some VNone
      else begin
        (* helper: check if node has sthita edge to a given target *)
        let has_sthita node target =
          let edges = edges_of k node in
          List.exists (fun e ->
            e.relation = sthita_dim && e.source = node && e.target = target
          ) edges
        in
        (* helper: get sankhya value from a node *)
        let get_sankhya node =
          let edges = edges_of k node in
          List.fold_left (fun acc e ->
            if e.relation = sankhya_dim && e.source = node then e.target
            else acc
          ) "" edges
        in
        (* try each split point *)
        let result = ref VNone in
        for i = 1 to len - 1 do
          if !result = VNone then begin
            let left = String.sub sym 0 i in
            let right = String.sub sym i (len - i) in
            let prefix_candidates = csr_walk_in_by_rel k left mudra_dim in
            let base_candidates = csr_walk_in_by_rel k right mudra_dim in
            (* find a prefix (sthita:upasarga) and base (sthita:matra or matra-beeja) *)
            let prefix_node = List.find_opt (fun n -> has_sthita n "upasarga") prefix_candidates in
            let base_node = List.find_opt (fun n ->
              has_sthita n "matra" || has_sthita n "matra-beeja"
            ) base_candidates in
            match prefix_node, base_node with
            | Some pn, Some bn ->
              let exp = if sankhya_dim >= 0 then get_sankhya pn else "" in
              result := VList [VString pn; VString bn; VString exp]
            | _ -> ()
          end
        done;
        Some !result
      end
    end

  | "word-node-compound" ->
    (* reverse of expand_avastha: check if two words form a known compound.
       e.g., word-node-compound "elastic" "energy" → "elastic-energy" *)
    let w1 = eval_str 0 in
    let w2 = eval_str 1 in
    let key = w1 ^ " " ^ w2 in
    Some (match Domain.DLS.get _eval_ctx with
     | Some ctx ->
       (match Hashtbl.find_opt ctx.ctx_index.compound_word_index key with
        | Some compound_name -> VString compound_name | None -> VNone)
     | None -> VNone)

  (* ── migrated tantras: word resolution + grammar check ────────────── *)

  | "word-resolve" ->
    let w = eval_str 0 in
    let wn = call_tantra_opt k "shabda-anveshana"
      [("word", VString w)] ~default:VNone in
    Some (VString (if as_bool wn then as_string wn else ""))

  | "resolve-or-self" ->
    let w = eval_str 0 in
    let wn = call_tantra_opt k "shabda-anveshana"
      [("word", VString w)] ~default:VNone in
    let resolved = if as_bool wn then as_string wn else "" in
    Some (VString (if String.length resolved > 0 then resolved else w))

  | "has-grammar-sthita" ->
    let nd = e_eval k e (List.nth args 0) in
    let rl = eval_str 1 in
    let sthita_name = eval_str 2 in
    let is_grammar = as_bool nd && rl = "grammar" in
    Some (VBool (if is_grammar then
      let node_name = as_string nd in
      match visheshanam_of_string "sthita" with
      | None -> false
      | Some vish ->
        let edges = edges_of k node_name in
        List.exists (fun edge ->
          edge.relation = vish && edge.source = node_name
          && edge.target = sthita_name
        ) edges
    else false))

  (* is-viveka-node: graph-driven check with lazy cache.
     On first call, scans graph for all nodes that are swarupa→viveka (direct)
     or sthita→(swarupa→viveka) (indirect). Caches the set for O(1) lookups. *)
  | "is-viveka-node" ->
    let w = eval_str 0 in
    let viveka_set = Prakriti.get_viveka_cache k in
    Some (VBool (Hashtbl.mem viveka_set w))

  (* viveka-direction: returns "max" or "min" via cached viveka-direction map.
     Built lazily alongside the viveka cache. *)
  | "viveka-direction" ->
    let w = eval_str 0 in
    let dir_map = Prakriti.get_viveka_dir_cache k in
    let dir = match Hashtbl.find_opt dir_map w with Some d -> d | None -> "" in
    Some (VString dir)

  | _ -> None
