(* setu.ml — graph walk utilities + shabda reader
   the bridge between raw graph structure and domain renderers.
   reads the graph. does not emit. does not print.

   dependency: Proof_graph, Setu_shabda, Setu_classify. *)

open Proof_graph

(* --- shabda reader: forwarding to Setu_shabda ---
   canonical implementations live in setu_shabda.ml — this forwards for callers
   that still refer to Setu.read_shabda etc. *)

let parse_shabda = Setu_shabda.parse_shabda
let parse_shabda_file = Setu_shabda.parse_shabda_file
let raw_shabda_for_node = Setu_shabda.raw_shabda_for_node
let merge_shabda_priority = Setu_shabda.merge_shabda_priority
let read_shabda = Setu_shabda.read_shabda
let shabda_get = Setu_shabda.shabda_get

(* --- tokenise --- *)

let tokenise s =
  let buf = Buffer.create 16 in
  let tokens = ref [] in
  String.iter (fun c ->
    match c with
    | ' ' | '\t' | '\n' | ',' | '.' | '?' | '!' | ':' | ';' | '(' | ')' ->
      if Buffer.length buf > 0 then begin
        tokens := Buffer.contents buf :: !tokens;
        Buffer.clear buf
      end
    | '-' -> Buffer.add_char buf c
    | c   -> Buffer.add_char buf (Char.lowercase_ascii c)
  ) s;
  if Buffer.length buf > 0 then tokens := Buffer.contents buf :: !tokens;
  List.rev !tokens

(* --- domain detection --- *)

let domain_of_edge_target t =
  if String.length t > 7 && String.sub t 0 7 = "domain-" then
    Some (String.sub t 7 (String.length t - 7))
  else None

let detect_domain (k : proof_graph) (seeds : string list) : string =
  let found = List.find_map (fun seed ->
    match find k seed with
    | None -> None
    | Some n ->
      List.find_map (fun e ->
        if e.source = n.name && e.relation = sthita then
          domain_of_edge_target e.target
        else None
      ) n.edges
  ) seeds in
  match found with
  | Some d -> d
  | None -> "computation"

(* --- graph walk: edge readers --- *)

let kriya_of (k : proof_graph) (name : string) : string list =
  match Hashtbl.find_opt k.nodes name with
  | None -> []
  | Some n -> List.filter_map (fun e ->
      if e.source = name && e.relation = Proof_graph.kriya then Some e.target else None
    ) n.edges

let swarupa_of (k : proof_graph) (name : string) : string list =
  match Hashtbl.find_opt k.nodes name with
  | None -> []
  | Some n -> List.filter_map (fun e ->
      if e.source = name && e.relation = Proof_graph.swarupa then Some e.target else None
    ) n.edges

let yukta_of (k : proof_graph) (name : string) : string list =
  match Hashtbl.find_opt k.nodes name with
  | None -> []
  | Some n -> List.filter_map (fun e ->
      if e.source = name && e.relation = Proof_graph.yukta then Some e.target else None
    ) n.edges

let janya_of (k : proof_graph) (name : string) : string list =
  match Hashtbl.find_opt k.nodes name with
  | None -> []
  | Some n -> List.filter_map (fun e ->
      if e.source = name && e.relation = Proof_graph.janya then Some e.target else None
    ) n.edges

let has_domain_sthita (k : proof_graph) (name : string) (domain : string) : bool =
  (* check the node itself and all ancestors reachable via inheritance (vishesa, abheda, swarupa) *)
  let has_direct node_name =
    match Hashtbl.find_opt k.nodes node_name with
    | None -> false
    | Some n -> List.exists (fun e ->
        e.source = node_name && e.relation = Proof_graph.sthita && e.target = domain
      ) n.edges
  in
  has_direct name ||
  List.exists has_direct (Proof_graph.walk_inheritance k name)

let is_setu (k : proof_graph) (name : string) : bool =
  match Hashtbl.find_opt k.nodes name with
  | None -> false
  | Some n -> List.exists (fun e ->
      e.source = name && e.relation = Proof_graph.swarupa && e.target = "setu"
    ) n.edges

let infer_inputs (k : proof_graph) (node_name : string) : string list =
  match Hashtbl.find_opt k.nodes node_name with
  | None -> []
  | Some n ->
    List.filter_map (fun e ->
      if e.source = node_name && e.relation = Proof_graph.sthita then
        let t = e.target in
        let is_domain = String.length t >= 7 && String.sub t 0 7 = "domain-" in
        if is_domain then None else Some t
      else None
    ) n.edges
    |> List.sort_uniq String.compare

let infer_outputs (k : proof_graph) (node_name : string) : string list =
  match Hashtbl.find_opt k.nodes node_name with
  | None -> []
  | Some n ->
    List.filter_map (fun e ->
      if e.source = node_name && e.relation = Proof_graph.phala then
        let t = e.target in
        let is_domain = String.length t >= 7 && String.sub t 0 7 = "domain-" in
        if is_domain then None else Some t
      else None
    ) n.edges
    |> List.sort_uniq String.compare

(* --- name resolution --- *)

let sanitize_ocaml_ident (s : string) : string =
  let buf = Buffer.create (String.length s) in
  String.iter (fun c ->
    if (c >= 'a' && c <= 'z') || (c >= 'A' && c <= 'Z')
       || (c >= '0' && c <= '9') || c = '_' then
      Buffer.add_char buf (Char.lowercase_ascii c)
    else if c = '-' then Buffer.add_char buf '_'
    else ()
  ) s;
  let out = Buffer.contents buf in
  if out = "" then "x" else out

let capitalize_first (s : string) : string =
  if String.length s = 0 then s
  else let b = Bytes.of_string s in
       Bytes.set b 0 (Char.uppercase_ascii (Bytes.get b 0));
       Bytes.to_string b

let resolve (k : proof_graph) (name : string) : string list =
  match Hashtbl.find_opt k.nodes name with
  | None -> [name]
  | Some n ->
    let abheda_targets = List.filter_map (fun e ->
      if e.source = name && e.relation = Proof_graph.abheda then Some e.target
      else None
    ) n.edges in
    let abheda_sources = List.filter_map (fun e ->
      if e.target = name && e.relation = Proof_graph.abheda then Some e.source
      else None
    ) !(k.all_edges) in
    name :: abheda_targets @ abheda_sources

(* collect all neighbours of a node within 1 hop — all edge targets and sources *)
let neighbours_of (k : proof_graph) (name : string) : string list =
  match Hashtbl.find_opt k.nodes name with
  | None -> []
  | Some n ->
    let out_targets = List.map (fun e -> e.target) n.edges in
    let in_sources = List.filter_map (fun e ->
      if e.target = name then Some e.source else None
    ) !(k.all_edges) in
    List.sort_uniq String.compare (out_targets @ in_sources)

(* shared-neighbour count between two nodes — context proximity score *)
let context_proximity (k : proof_graph) (candidate : string) (context : string) : int =
  let cn = neighbours_of k candidate in
  let ctx_n = neighbours_of k context in
  let ctx_set = Hashtbl.create 32 in
  List.iter (fun n -> Hashtbl.replace ctx_set n true) ctx_n;
  (* direct connection is strongest signal *)
  let direct_bonus =
    if Hashtbl.mem ctx_set candidate || List.mem context cn then 2000
    else 0
  in
  let shared = List.fold_left (fun acc n ->
    if Hashtbl.mem ctx_set n then acc + 1 else acc
  ) 0 cn in
  direct_bonus + (shared * 300)

let to_english ?(context : string option = None)
               ?(ppr : (string, float) Hashtbl.t option = None)
               (k : proof_graph) (name : string) : string =
  let english_names = Hashtbl.fold (fun source n acc ->
    let has_abheda = List.exists (fun e ->
      e.target = name && e.relation = abheda
    ) n.edges in
    if has_abheda && source <> name then source :: acc
    else acc
  ) k.nodes [] in
  let score candidate =
    match Hashtbl.find_opt k.nodes candidate with
    | None -> 0
    | Some n ->
      let total_edges = List.length n.edges in
      let abheda_edges = List.length (List.filter (fun e ->
        e.relation = abheda
      ) n.edges) in
      let non_abheda_out = List.length (List.filter (fun e ->
        e.relation <> abheda
      ) n.edges) in
      let non_abheda_in = List.length (List.filter (fun e ->
        e.target = candidate && e.relation <> abheda
      ) !(k.all_edges)) in
      let ratio = if total_edges > 0
        then (abheda_edges * 1000) / total_edges
        else 0 in
      let len = String.length candidate in
      let len_bonus = if len >= 3 && len <= 25 then 50 else 0 in
      let sloka_penalty = List.length n.slokas * 100 in
      let structure_penalty = (non_abheda_out * 300) + (non_abheda_in * 200) in
      let context_bonus = match context with
        | None -> 0
        | Some ctx -> context_proximity k candidate ctx
      in
      let ppr_bonus = match ppr with
        | None -> 0
        | Some tbl ->
          (match Hashtbl.find_opt tbl candidate with
           | Some s -> int_of_float (s *. 500.0)
           | None   -> 0)
      in
      ratio + len_bonus - sloka_penalty - structure_penalty + context_bonus + ppr_bonus
  in
  let pick_best names =
    match names with
    | [] -> None
    | [one] -> Some one
    | multiple ->
      Some (List.hd (List.sort (fun a b -> compare (score b) (score a)) multiple))
  in
  let direct = pick_best english_names in
  let bridged =
    if direct <> None then []
    else Hashtbl.fold (fun candidate n acc ->
      let abheda_targets = List.filter_map (fun e ->
        if e.relation = abheda then Some e.target else None
      ) n.edges in
      let matches_bridge = List.exists (fun mid ->
        match Hashtbl.find_opt k.nodes mid with
        | None -> false
        | Some mid_n ->
          List.exists (fun e -> e.relation = abheda && e.target = name) mid_n.edges
      ) abheda_targets in
      if matches_bridge && candidate <> name then candidate :: acc else acc
    ) k.nodes []
  in
  let bridged = List.sort_uniq String.compare bridged in
  match english_names with
  | _ ->
    (match direct with
    | Some best -> best
    | None ->
      (match pick_best bridged with
      | Some best -> best
      | None -> name))

(* --- token classification: forwarding to Setu_classify ---
   canonical implementations live in setu_classify.ml.
   type equality declaration makes Setu.token_role = Setu_classify.token_role. *)

type token_role = Setu_classify.token_role =
  | Article
  | Grammar of int
  | Content of string
  | Number of float
  | Operator of string
  | Unknown of string

let classify_token = Setu_classify.classify_token

(* --- setu walk: find OCaml construct for a seed --- *)

let rec find_setu_form (k : proof_graph) (name : string) (depth : int) (visited : string list) : string option =
  if depth = 0 || List.mem name visited then None
  else begin
    let visited = name :: visited in
    let is_ocaml_node = match find k name with
      | None -> false
      | Some n -> List.exists (fun e ->
          e.source = name && e.relation = sthita
           && (e.target = "domain-ocaml" || e.target = "domain-language")
        ) n.edges
    in
    if is_ocaml_node then Some name
    else begin
      let next = List.filter_map (fun e ->
        if e.source = name &&
           (e.relation = abheda || e.relation = kriya || e.relation = swarupa || e.relation = yukta)
        then Some e.target
        else None
      ) !(k.all_edges) in
      List.find_map (fun t -> find_setu_form k t (depth - 1) visited) next
    end
  end

let resolve_ocaml_forms (k : proof_graph) (seeds : string list) : (string * string) list =
  let setu_map = read_shabda k "ocaml-setu" in
  List.filter_map (fun seed ->
    match find_setu_form k seed 5 [] with
    | Some setu_node ->
      (match shabda_get setu_map setu_node with
       | Some construct -> Some (seed, construct)
       | None -> None)
    | None -> None
  ) seeds

(* --- walk: follow kriya/phala chains from seeds --- *)

(* resolve_to_canonical: given a name (as written in a tantra file),
   find the canonical graph node name.
   1. If the name is already a graph node, return it as-is.
   2. Search all nodes' shabda fields for the name → return that node's name.
   3. Otherwise return the name unchanged. *)
let resolve_to_canonical (k : proof_graph) (name : string) : string =
  (* 1. direct node lookup *)
  match Hashtbl.find_opt k.nodes name with
  | Some _ -> name
  | None ->
    (* 2. search shabda fields for this name *)
    let shabda_hit = Hashtbl.fold (fun node_name n acc ->
      match acc with
      | Some _ -> acc
      | None ->
        let raw = String.lowercase_ascii (String.trim n.shabda) in
        if raw = "" then None
        else
          (* shabda format: "key:val key:val ..." or just words before '/' *)
          let before_slash = match String.index_opt raw '/' with
            | Some i -> String.sub raw 0 i
            | None -> raw
          in
          (* tokenize: split on spaces/commas, check if any token = name *)
          let tokens = String.split_on_char ',' before_slash
            |> List.map String.trim
            |> List.concat_map (fun t -> String.split_on_char ' ' t)
            |> List.map String.trim
            |> List.filter (fun t -> String.length t > 0)
          in
          if List.mem (String.lowercase_ascii name) tokens then Some node_name
          else None
    ) k.nodes None in
    match shabda_hit with
    | Some canonical -> canonical
    | None -> name

let rec walk_chain (k : proof_graph) (name : string) (depth : int) (visited : string list) : string list =
  if depth = 0 || List.mem name visited then visited
  else
    let visited = name :: visited in
    match find k name with
    | None -> visited
    | Some n ->
      let next = List.filter_map (fun e ->
        if e.source = name &&
           (e.relation = kriya || e.relation = phala || e.relation = swarupa || e.relation = abheda)
        then Some e.target else None) n.edges in
      List.fold_left (fun acc t -> walk_chain k t (depth - 1) acc) visited next
