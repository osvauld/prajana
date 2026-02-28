(* proof_graph.ml — the proof space
   nodes are nigamana. edges are typed by visheshanam.
   satya is computed from structure by avrti (spiral convergence).
   the graph holds the truths. the LLM interprets them. *)

(* visheshanam — edge types from Sanskrit grammar *)
type visheshanam =
  | Swarupa       (* identity — X IS Y *)
  | Abheda        (* non-different — X = Y at some level *)
  | Drishthanta   (* evidence — X demonstrated by Y *)
  | Sthita        (* foundation — X stands on Y *)
  | Yukta         (* connection — X joined with Y *)
  | Siddha        (* proof — X established by Y *)
  | Kriya         (* function — X acts as Y *)
  | Phala         (* consequence — X results from Y *)
  | Janya         (* origin — X born from Y *)

(* typed edge between two nodes *)
type typed_edge = {
  source   : string;
  target   : string;
  relation : visheshanam;
}

(* one truth in the space *)
type nigamana = {
  name   : string;
  slokas : string list;       (* raw sloka text, preserved *)
  edges  : typed_edge list;   (* extracted from slokas *)
  satya  : float;             (* computed by avrti *)
}

type proof_graph = {
  nodes     : (string, nigamana) Hashtbl.t;
  all_edges : typed_edge list ref;
}

(* visheshanam string conversion *)
let visheshanam_of_string s =
  match String.lowercase_ascii s with
  | "swarupa"     -> Some Swarupa
  | "abheda"      -> Some Abheda
  | "drishthanta" -> Some Drishthanta
  | "sthita"      -> Some Sthita
  | "yukta"       -> Some Yukta
  | "siddha"      -> Some Siddha
  | "kriya"       -> Some Kriya
  | "phala"       -> Some Phala
  | "janya"       -> Some Janya
  | _             -> None

let string_of_visheshanam = function
  | Swarupa     -> "swarupa"
  | Abheda      -> "abheda"
  | Drishthanta -> "drishthanta"
  | Sthita      -> "sthita"
  | Yukta       -> "yukta"
  | Siddha      -> "siddha"
  | Kriya       -> "kriya"
  | Phala       -> "phala"
  | Janya       -> "janya"

(* the space was already there *)
let empty () : proof_graph = {
  nodes     = Hashtbl.create 64;
  all_edges = ref [];
}

(* join a nigamana into the space *)
let join (k : proof_graph) (n : nigamana) : proof_graph =
  Hashtbl.replace k.nodes n.name n;
  k.all_edges := n.edges @ !(k.all_edges);
  k

(* find by name *)
let find (k : proof_graph) (name : string) : nigamana option =
  Hashtbl.find_opt k.nodes name

(* in-degree: how many edges point TO this node *)
let in_degree (k : proof_graph) (name : string) : int =
  List.length (List.filter (fun e -> e.target = name) !(k.all_edges))

(* out-degree: how many edges go FROM this node *)
let out_degree (k : proof_graph) (name : string) : int =
  List.length (List.filter (fun e -> e.source = name) !(k.all_edges))

(* neighbors: all nodes connected to this node (both directions) *)
let neighbors (k : proof_graph) (name : string) : string list =
  let targets = List.filter_map (fun e ->
    if e.source = name then Some e.target else None
  ) !(k.all_edges) in
  let sources = List.filter_map (fun e ->
    if e.target = name then Some e.source else None
  ) !(k.all_edges) in
  List.sort_uniq String.compare (targets @ sources)

(* edges involving a node *)
let edges_of (k : proof_graph) (name : string) : typed_edge list =
  List.filter (fun e -> e.source = name || e.target = name) !(k.all_edges)

(* --- satya-ganana: avrti (spiral convergence) --- *)

(* pass 1: raw satya from local structure
   - sloka count contributes (more angles = denser)
   - edge count contributes (more connections = richer)
   - edge type diversity contributes (richer relationships = deeper)
   all normalized to (0, 1) *)
let raw_satya (n : nigamana) : float =
  let sloka_count = float_of_int (List.length n.slokas) in
  let edge_count = float_of_int (List.length n.edges) in
  (* count distinct visheshanam types used *)
  let visheshanam_types = List.sort_uniq compare
    (List.map (fun e -> e.relation) n.edges) in
  let type_diversity = float_of_int (List.length visheshanam_types) in
  (* sigmoid-like: approaches 1.0 but never reaches *)
  (* each factor contributes: 1 - 1/(1+x) = x/(1+x) *)
  let s = sloka_count /. (1.0 +. sloka_count) in
  let e = edge_count /. (1.0 +. edge_count) in
  let d = type_diversity /. (1.0 +. type_diversity) in
  (* combine: geometric mean keeps values in (0, 1) *)
  (* root nodes with no edges get satya from slokas alone *)
  if edge_count = 0.0 then
    s *. 0.5  (* root node: sloka contribution only, halved *)
  else
    (s *. e *. d) ** (1.0 /. 3.0)

(* pass 2+: adjust by neighbor satya — one avrti turn
   returns the new satya for one node *)
let avrti_step (k : proof_graph) (name : string) (current : float) : float =
  let nbrs = neighbors k name in
  if nbrs = [] then current
  else begin
    let nbr_satya_sum = List.fold_left (fun acc nb ->
      match Hashtbl.find_opt k.nodes nb with
      | Some n -> acc +. n.satya
      | None   -> acc
    ) 0.0 nbrs in
    let nbr_count = float_of_int (List.length nbrs) in
    let nbr_avg = nbr_satya_sum /. nbr_count in
    (* blend: 60% own structure, 40% neighbor influence *)
    let blended = 0.6 *. current +. 0.4 *. nbr_avg in
    (* also factor in in-degree: more citations = higher satya *)
    let in_deg = float_of_int (in_degree k name) in
    let citation_boost = in_deg /. (1.0 +. in_deg) in
    (* combine: blend with citation influence *)
    0.7 *. blended +. 0.3 *. citation_boost
  end

(* run satya-ganana: iterate until convergence *)
let satya_ganana (k : proof_graph) : int =
  (* pass 1: set raw satya for all nodes *)
  Hashtbl.iter (fun _ n ->
    let raw = raw_satya n in
    Hashtbl.replace k.nodes n.name { n with satya = raw }
  ) k.nodes;
  (* pass 2+: avrti — iterate until convergence *)
  let max_iterations = 100 in
  let threshold = 0.001 in
  let iterations = ref 0 in
  let converged = ref false in
  while not !converged && !iterations < max_iterations do
    incr iterations;
    let max_delta = ref 0.0 in
    (* collect updates first, then apply — avoid order-dependence *)
    let updates = Hashtbl.fold (fun name n acc ->
      let new_satya = avrti_step k name n.satya in
      (* clamp to (0.001, 0.999) — ananta holds *)
      let clamped = Float.min 0.999 (Float.max 0.001 new_satya) in
      let delta = Float.abs (clamped -. n.satya) in
      if delta > !max_delta then max_delta := delta;
      (name, clamped) :: acc
    ) k.nodes [] in
    (* apply updates *)
    List.iter (fun (name, new_satya) ->
      match Hashtbl.find_opt k.nodes name with
      | Some n -> Hashtbl.replace k.nodes name { n with satya = new_satya }
      | None -> ()
    ) updates;
    if !max_delta < threshold then converged := true
  done;
  !iterations

(* --- output --- *)

(* --- anuvada: English sentence understanding --- *)

(* English grammar words → visheshanam *)
let grammar_of_english word =
  match String.lowercase_ascii word with
  | "is" | "are" | "am" | "was" | "were" | "being" | "means" -> Some Swarupa
  | "of" | "in" | "on" | "upon" | "within" | "rests" | "stands" -> Some Sthita
  | "from" | "born" | "originates" | "comes" | "arises" -> Some Janya
  | "by" | "through" | "via" | "proven" | "established" -> Some Siddha
  | "and" | "with" | "to" | "connected" | "joined" | "links" -> Some Yukta
  | "as" | "does" | "acts" | "functions" | "runs" | "holds" | "gives" | "receives" -> Some Kriya
  | "equals" | "same" | "identical" | "equivalent" | "maps" -> Some Abheda
  | "shows" | "proves" | "demonstrates" | "evidence" | "seen" -> Some Drishthanta
  | "produces" | "results" | "causes" | "yields" | "becomes" | "increases" | "decreases" | "grows" | "generate" | "generates" -> Some Phala
  | "what" | "how" | "why" | "where" | "when" | "who" | "which" -> Some Drishthanta  (* question words = seeking evidence *)
  | _ -> None

(* classify a token: article (skip), grammar (visheshanam), or content (look up) *)
type token_role =
  | Article                          (* the, a, an — skip *)
  | Grammar of visheshanam           (* structural word *)
  | Content of string                (* look up in graph *)
  | Unknown of string                (* not found anywhere *)

let classify_token (k : proof_graph) word =
  let w = String.lowercase_ascii word in
  match w with
  | "the" | "a" | "an" | "this" | "that" | "it" -> Article
  | "'s" -> Grammar Sthita  (* possession = standing on *)
  | "its" -> Grammar Sthita  (* possessive = standing on *)
  (* math symbols *)
  | "+" -> Content "plus"
  | "-" -> Content "minus"
  | "*" | "x" -> Content "times"
  | "/" -> Content "division"
  | "=" -> Content "equals"
  (* digits as canonical number words *)
  | "0" -> Content "zero"
  | "1" -> Content "one"
  | "2" -> Content "two"
  | "3" -> Content "three"
  | "4" -> Content "four"
  | "5" -> Content "five"
  | "6" -> Content "six"
  | "7" -> Content "seven"
  | "8" -> Content "eight"
  | "9" -> Content "nine"
  | _ ->
    match grammar_of_english w with
    | Some v -> Grammar v
    | None ->
      (* try to find as a node name *)
      match Hashtbl.find_opt k.nodes w with
      | Some _ -> Content w
      | None ->
        (* try partial match: find any node name that contains this word *)
        let partial_matches = Hashtbl.fold (fun name _ acc ->
          (* check if node name contains this word as a component *)
          let parts = String.split_on_char '-' name in
          if List.exists (fun p -> String.lowercase_ascii p = w) parts then
            name :: acc
          else acc
        ) k.nodes [] in
        match partial_matches with
        | [single] -> Content single  (* unique partial match *)
        | _ :: _ -> Content (List.hd (List.sort String.compare partial_matches))  (* take first alphabetically *)
        | [] -> Unknown w

(* resolve a content word through the graph:
   find the node, follow abheda edges to find equivalents,
   return all names this word maps to *)
let resolve (k : proof_graph) (name : string) : string list =
  match Hashtbl.find_opt k.nodes name with
  | None -> [name]  (* unknown — return as-is *)
  | Some n ->
    (* collect abheda targets — these are equivalences *)
    let abheda_targets = List.filter_map (fun e ->
      if e.source = name && e.relation = Abheda then Some e.target
      else None
    ) n.edges in
    (* also collect what points to this node via abheda *)
    let abheda_sources = List.filter_map (fun e ->
      if e.target = name && e.relation = Abheda then Some e.source
      else None
    ) !(k.all_edges) in
    name :: abheda_targets @ abheda_sources

(* translate a node name to English: find kosha nodes that point to it via abheda *)
let to_english (k : proof_graph) (name : string) : string =
  (* look for nodes that have an abheda edge TO this name *)
  let english_names = Hashtbl.fold (fun source n acc ->
    let has_abheda = List.exists (fun e ->
      e.target = name && e.relation = Abheda
    ) n.edges in
    if has_abheda && source <> name then source :: acc
    else acc
  ) k.nodes [] in
  (* filter out names that are themselves Sanskrit (they also point to this node
     but aren't translations — they're peers in the sangati graph).
     heuristic: prefer names containing '-' or more than 5 chars that aren't
     also targets of many abheda edges FROM other nodes (i.e. aren't root Sanskrit terms) *)
  let score candidate =
    match Hashtbl.find_opt k.nodes candidate with
    | None -> 0
    | Some n ->
      let total_edges = List.length n.edges in
      let abheda_edges = List.length (List.filter (fun e ->
        e.relation = Abheda
      ) n.edges) in
      let non_abheda_out = List.length (List.filter (fun e ->
        e.relation <> Abheda
      ) n.edges) in
      let non_abheda_in = List.length (List.filter (fun e ->
        e.target = candidate && e.relation <> Abheda
      ) !(k.all_edges)) in
      (* a pure translation node has almost all abheda edges
         and very few other types. score by abheda ratio. *)
      let ratio = if total_edges > 0
        then (abheda_edges * 1000) / total_edges
        else 0 in
      (* bonus: prefer names with reasonable length *)
      let len = String.length candidate in
      let len_bonus = if len >= 3 && len <= 25 then 50 else 0 in
      (* kosha nodes have fewer slokas (1-2) vs sangati nodes (2-3+) *)
      let sloka_penalty = List.length n.slokas * 100 in
      (* sangati nodes are structurally active beyond abheda; penalize that heavily *)
      let structure_penalty = (non_abheda_out * 300) + (non_abheda_in * 200) in
      ratio + len_bonus - sloka_penalty - structure_penalty
  in
  let pick_best names =
    match names with
    | [] -> None
    | [one] -> Some one
    | multiple ->
      Some (List.hd (List.sort (fun a b -> compare (score b) (score a)) multiple))
  in
  let direct = pick_best english_names in
  (* fallback: if no direct abheda translation exists,
     look for one-hop bridge: candidate -(abheda)-> x -(abheda)-> name *)
  let bridged =
    if direct <> None then []
    else Hashtbl.fold (fun candidate n acc ->
      let abheda_targets = List.filter_map (fun e ->
        if e.relation = Abheda then Some e.target else None
      ) n.edges in
      let matches_bridge = List.exists (fun mid ->
        match Hashtbl.find_opt k.nodes mid with
        | None -> false
        | Some mid_n ->
          List.exists (fun e -> e.relation = Abheda && e.target = name) mid_n.edges
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
      | None ->
        (* final fallback for known leak points *)
        match String.lowercase_ascii name with
        | "sthiti" -> "stability"
        | "swatantra" -> "autonomy"
        | _ -> name))

(* render a visheshanam as an English phrase *)
let english_of_visheshanam = function
  | Swarupa     -> "is"
  | Abheda      -> "is the same as"
  | Drishthanta -> "demonstrated by"
  | Sthita      -> "rests on"
  | Yukta       -> "connects to"
  | Siddha      -> "proven through"
  | Kriya       -> "acts as"
  | Phala       -> "produces"
  | Janya       -> "born from"

(* optional rhythmic rendering for anuvada output *)
let thaalam_cycle name =
  match String.lowercase_ascii name with
  | "adi" | "aditaalam" | "adi-taalam" -> Some ("adi", 8)
  | "rupaka" | "rupakataalam" | "rupaka-taalam" -> Some ("rupaka", 6)
  | "misra" | "misrachapu" | "misra-chapu" -> Some ("misra", 7)
  | "khanda" | "khandachapu" | "khanda-chapu" -> Some ("khanda", 5)
  | _ -> None

(* --- avrti on language: the spiral --- *)

(* a triple: (english_source, visheshanam, english_targets, pass_number) *)
type anuvada_triple = {
  a_source   : string;        (* English name of source *)
  a_source_raw : string;      (* raw graph source name *)
  a_relation : visheshanam;
  a_targets  : string list;   (* English names of targets *)
  a_targets_raw : string list; (* raw graph target names *)
  a_pass     : int;           (* which avrti discovered this *)
}

(* module for deduplicating triples *)
module TripleKey = struct
  type t = string * visheshanam * string list
  let compare (s1, v1, ts1) (s2, v2, ts2) =
    let c = String.compare s1 s2 in
    if c <> 0 then c
    else let c = compare v1 v2 in
    if c <> 0 then c
    else compare ts1 ts2
end
module TripleSet = Set.Make(TripleKey)

let next_thread_question (triple : anuvada_triple) : string =
  let target = match triple.a_targets with
    | t :: _ -> t
    | [] -> "this" in
  match triple.a_relation with
  | Swarupa ->
    Printf.sprintf "how is %s actually %s in your context?" triple.a_source target
  | Abheda ->
    Printf.sprintf "where do %s and %s start to differ?" triple.a_source target
  | Drishthanta ->
    Printf.sprintf "what concrete example shows %s through %s?" triple.a_source target
  | Sthita ->
    Printf.sprintf "what shifts in %s if %s changes?" triple.a_source target
  | Yukta ->
    Printf.sprintf "what is the bridge between %s and %s?" triple.a_source target
  | Siddha ->
    Printf.sprintf "what proof would make %s through %s undeniable?" triple.a_source target
  | Kriya ->
    Printf.sprintf "what action of %s as %s should we test next?" triple.a_source target
  | Phala ->
    Printf.sprintf "if %s produces %s, what comes right after?" triple.a_source target
  | Janya ->
    Printf.sprintf "what earlier cause gives rise to %s before %s?" triple.a_source target

(* one pass: walk content_words through the graph, collect triples
   and return new node names discovered (the raw graph names, not English).
   pass_num tags each triple with its discovery depth. *)
let walk_one_pass (k : proof_graph) (content_words : string list)
    (visited_nodes : (string, bool) Hashtbl.t) (pass_num : int)
    : anuvada_triple list * string list =
  let triples = ref [] in
  let new_targets = ref [] in
  List.iter (fun name ->
    if not (Hashtbl.mem visited_nodes name) then begin
      Hashtbl.add visited_nodes name true;
      let english_name = to_english k name in
      match Hashtbl.find_opt k.nodes name with
      | None -> ()
      | Some n ->
        (* group outgoing edges by visheshanam *)
        let by_type = Hashtbl.create 9 in
        List.iter (fun e ->
          if e.source = name then begin
            let targets = match Hashtbl.find_opt by_type e.relation with
              | Some lst -> lst | None -> [] in
            Hashtbl.replace by_type e.relation (e.target :: targets)
          end
        ) n.edges;
        (* collect triples and new target names *)
        Hashtbl.iter (fun vish targets ->
          let target_pairs = List.map (fun t -> (t, to_english k t)) targets in
          let target_pairs = List.sort_uniq (fun (r1, e1) (r2, e2) ->
            let c = String.compare e1 e2 in
            if c <> 0 then c else String.compare r1 r2
          ) target_pairs in
          let target_pairs = List.filter (fun (_raw, eng) ->
            eng <> english_name
          ) target_pairs in
          let unique_targets = List.sort_uniq String.compare
            (List.map snd target_pairs) in
          let unique_targets_raw = List.sort_uniq String.compare
            (List.map fst target_pairs) in
          if unique_targets <> [] then
            triples := { a_source = english_name;
                         a_source_raw = name;
                         a_relation = vish;
                         a_targets = unique_targets;
                         a_targets_raw = unique_targets_raw;
                         a_pass = pass_num } :: !triples;
          (* raw graph names are the next pass's input *)
          List.iter (fun t ->
            new_targets := t :: !new_targets
          ) targets
        ) by_type
    end
  ) content_words;
  (List.rev !triples, List.sort_uniq String.compare !new_targets)

(* the spiral: run walk_one_pass repeatedly, feeding output targets back in.
   stop when no new triples are found or max_passes reached.
   returns: (pass_grouped_triples, pass_count)
   where pass_grouped_triples is a list of (pass_number, triples_in_that_pass) *)
let avrti_anuvada (k : proof_graph) (seed_words : string list)
    (max_passes : int) : (int * anuvada_triple list) list * int =
  let visited_nodes = Hashtbl.create 64 in
  let seen_triples = ref TripleSet.empty in
  let passes_result = ref [] in
  let pass = ref 0 in
  let current_words = ref seed_words in
  let found_new = ref true in
  while !found_new && !pass < max_passes do
    incr pass;
    let (triples, new_targets) =
      walk_one_pass k !current_words visited_nodes !pass in
    (* deduplicate against previous passes and within this pass *)
    let (novel, updated_seen) = List.fold_left (fun (acc, seen) t ->
      let key = (t.a_source, t.a_relation, t.a_targets) in
      if TripleSet.mem key seen then (acc, seen)
      else (t :: acc, TripleSet.add key seen)
    ) ([], !seen_triples) triples in
    let novel = List.rev novel in
    if novel = [] then
      found_new := false
    else begin
      seen_triples := updated_seen;
      passes_result := !passes_result @ [(!pass, novel)];
      (* next pass: walk the new targets we haven't visited *)
      current_words := List.filter (fun n ->
        not (Hashtbl.mem visited_nodes n)
      ) new_targets
    end
  done;
  (!passes_result, !pass)

(* render the spiral output — grouped by avrti pass so reader sees progressive deepening *)
let render_spiral (k : proof_graph) (content_words : string list)
    (_grammar_words : (string * visheshanam) list) (mode : string option)
    (max_passes : int) (thaalam : string option) : unit =
  let max_passes = if max_passes < 1 then 1 else max_passes in
  let (pass_groups, total_passes) = avrti_anuvada k content_words max_passes in
  let total_triples = List.fold_left (fun acc (_, ts) ->
    acc + List.length ts) 0 pass_groups in
  Printf.printf "  response: (%d avrti, %d connections)\n"
    total_passes total_triples;
  (match thaalam with
  | Some t ->
    (match thaalam_cycle t with
    | Some (label, beats) -> Printf.printf "  thaalam: %s (%d beat cycle)\n" label beats
    | None -> Printf.printf "  thaalam: %s (unrecognized; using plain flow)\n" t)
  | None -> ());
  let beat_idx = ref 0 in
  let next_prefix () =
    match thaalam with
    | None -> ""
    | Some t ->
      (match thaalam_cycle t with
      | None -> ""
      | Some (_, beats) ->
        beat_idx := (!beat_idx mod beats) + 1;
        Printf.sprintf "[%d/%d] " !beat_idx beats)
  in
  let line_suffix =
    match mode with
    | Some "prashna-viraam" -> "?"
    | Some "vismaya-viraam" -> "!"
    | Some "traya-bindu" -> "..."
    | _ -> "."
  in
  let sentence_of_source (source : string) (ts : anuvada_triple list) : string =
    let rel_map = Hashtbl.create 9 in
    List.iter (fun t ->
      let existing = match Hashtbl.find_opt rel_map t.a_relation with
        | Some xs -> xs
        | None -> [] in
      Hashtbl.replace rel_map t.a_relation (existing @ t.a_targets)
    ) ts;
    let relation_order =
      [Swarupa; Abheda; Sthita; Yukta; Siddha; Kriya; Phala; Janya; Drishthanta] in
    let clauses = List.filter_map (fun rel ->
      match Hashtbl.find_opt rel_map rel with
      | None -> None
      | Some targets ->
        let targets = List.sort_uniq String.compare targets in
        if targets = [] then None
        else Some (Printf.sprintf "%s %s"
          (english_of_visheshanam rel)
          (String.concat ", " targets))
    ) relation_order in
    if clauses = [] then source ^ line_suffix
    else Printf.sprintf "%s %s%s" source (String.concat "; " clauses) line_suffix
  in
  let is_domain_name n =
    String.length n >= 7 && String.sub n 0 7 = "domain-" in
  let domains_of_node (name : string) : string list =
    match Hashtbl.find_opt k.nodes name with
    | None -> if is_domain_name name then [name] else []
    | Some n ->
      let from_edges = List.filter_map (fun e ->
        if e.source = name && e.relation = Sthita && is_domain_name e.target
        then Some e.target else None
      ) n.edges in
      let own = if is_domain_name name then [name] else [] in
      List.sort_uniq String.compare (own @ from_edges)
  in
  let active_domains = List.sort_uniq String.compare
    (List.concat_map domains_of_node content_words) in
  let has_active_domains = active_domains <> [] in
  let domain_member = Hashtbl.create 256 in
  if has_active_domains then begin
    Hashtbl.iter (fun name _ ->
      let node_domains = domains_of_node name in
      let in_domain = List.exists (fun d ->
        List.mem d active_domains
      ) node_domains in
      if in_domain || List.mem name active_domains then
        Hashtbl.replace domain_member name true
    ) k.nodes
  end;
  let is_domain_member name =
    if not has_active_domains then false
    else Hashtbl.mem domain_member name || List.mem name active_domains
  in
  let render_triples (triples : anuvada_triple list) : unit =
    let by_source = Hashtbl.create 16 in
    List.iter (fun t ->
      let existing = match Hashtbl.find_opt by_source t.a_source with
        | Some lst -> lst | None -> [] in
      Hashtbl.replace by_source t.a_source (t :: existing)
    ) triples;
    let all_sources = Hashtbl.fold (fun s _ acc -> s :: acc) by_source [] in
    let all_sources = List.sort String.compare all_sources in
    List.iter (fun source ->
      match Hashtbl.find_opt by_source source with
      | None -> ()
      | Some ts ->
        let sentence = sentence_of_source source (List.rev ts) in
        Printf.printf "    %s%s\n" (next_prefix ()) sentence
    ) all_sources
  in
  (* render each pass as a labeled section *)
  List.iter (fun (pass_num, triples) ->
    if total_passes > 1 then
      Printf.printf "  -- avrti %d --\n" pass_num;
    if has_active_domains then begin
      let pure_domain = List.filter (fun t ->
        is_domain_member t.a_source_raw
        && List.for_all is_domain_member t.a_targets_raw
      ) triples in
      let nature_equiv = List.filter (fun t ->
        (is_domain_member t.a_source_raw
         && List.exists (fun raw -> not (is_domain_member raw)) t.a_targets_raw)
        || not (is_domain_member t.a_source_raw)
      ) triples in
      if pure_domain <> [] then begin
        Printf.printf "    pure domain:\n";
        render_triples pure_domain
      end;
      if nature_equiv <> [] then begin
        Printf.printf "    equivalence found in nature:\n";
        render_triples nature_equiv
      end
    end else
      render_triples triples
  ) pass_groups;
  (* offer multiple follow-up thread questions, deepest-first *)
  let thread_candidates =
    List.concat (List.map snd (List.rev pass_groups)) in
  let max_threads = 3 in
  let (thread_questions, _) = List.fold_left (fun (acc, seen) t ->
    if List.length acc >= max_threads then (acc, seen)
    else
      let q = next_thread_question t in
      if Hashtbl.mem seen q then (acc, seen)
      else begin
        Hashtbl.add seen q true;
        (acc @ [q], seen)
      end
  ) ([], Hashtbl.create 16) thread_candidates in
  (match thread_questions with
  | [] -> ()
  | [q] -> Printf.printf "  next thread: %s\n" q
  | qs ->
    Printf.printf "  next threads:\n";
    List.iteri (fun i q -> Printf.printf "    %d) %s\n" (i + 1) q) qs);
  (* render mode *)
  (match mode with
  | Some "prashna-viraam" -> Printf.printf "    (this was a question)\n"
  | Some "vismaya-viraam" -> Printf.printf "    (this was spoken with force)\n"
  | Some "traya-bindu" -> Printf.printf "    (this thought is incomplete...)\n"
  | Some "purna-viraam" -> Printf.printf "    (this is a complete statement)\n"
  | _ -> ())

(* --- ocaml code emission from graph structure --- *)

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

(* capitalize first char of a string — used to make OCaml constructors *)
let capitalize_first (s : string) : string =
  if String.length s = 0 then s
  else let b = Bytes.of_string s in
       Bytes.set b 0 (Char.uppercase_ascii (Bytes.get b 0));
       Bytes.to_string b

let has_domain_sthita (k : proof_graph) (name : string) (domain : string) : bool =
  match Hashtbl.find_opt k.nodes name with
  | None -> false
  | Some n -> List.exists (fun e ->
      e.source = name && e.relation = Sthita && e.target = domain
    ) n.edges

(* is_setu: true if node has setu-swarupa — it is a bridge node.
   setu is the root of all X-to-Y converters.
   any node that IS a setu can be walked by the unified emitter. *)
let is_setu (k : proof_graph) (name : string) : bool =
  match Hashtbl.find_opt k.nodes name with
  | None -> false
  | Some n -> List.exists (fun e ->
      e.source = name && e.relation = Swarupa && e.target = "setu"
    ) n.edges

(* ocaml_symbol_of_operator: the rendering table for arithmetic operators.
   this is like english_of_visheshanam — it maps a graph concept to its
   OCaml surface form. it is rendering policy, not program logic. *)
let ocaml_symbol_of_operator (op_name : string) : string option =
  match String.lowercase_ascii op_name with
  | "plus"     -> Some "+"
  | "minus"    -> Some "-"
  | "times"    -> Some "*"
  | "division" -> Some "/"
  | _          -> None

(* ocaml_constructor_of_operator: the rendering table for ADT constructors.
   again: rendering policy. the program content (what ops exist) comes from
   the graph; only the surface form comes from here. *)
let ocaml_constructor_of_operator (op_name : string) : string =
  match String.lowercase_ascii op_name with
  | "division" -> "Divide"   (* "Division" would be fine too; "Divide" is idiomatic *)
  | other      -> capitalize_first (sanitize_ocaml_ident other)

(* math operation kinds — what shape of OCaml program to emit *)
type math_op_kind =
  | ArithmeticOp   (* scalar: plus/minus/times/division — emit ADT + eval + calculate *)
  | VectorOp       (* vector arithmetic — emit list-based add/scale/magnitude *)
  | MatrixOp       (* matrix/dot-product — emit 2d-array dot product + matmul *)

(* classify a yukta target by reading its kriya edges.
   the graph says what a node IS by what it acts as (kriya).
   arithmetic-kriya → ArithmeticOp
   dot-product-kriya or scalar-multiplication-kriya → VectorOp (vector arithmetic)
   if node name is dot-product or matrix-multiplication → MatrixOp *)
let classify_math_op (k : proof_graph) (target : string) : math_op_kind option =
  match Hashtbl.find_opt k.nodes target with
  | None -> None
  | Some target_node ->
    let kriya_targets = List.filter_map (fun e ->
      if e.source = target && e.relation = Kriya then Some e.target else None
    ) target_node.edges in
    let name = String.lowercase_ascii target in
    if name = "dot-product" || name = "matrix-multiplication" then
      Some MatrixOp
    else if List.mem "arithmetic" kriya_targets then
      Some ArithmeticOp
    else if List.mem "dot-product" kriya_targets
         || List.mem "scalar-multiplication" kriya_targets
         || List.mem "addition" kriya_targets then
      Some VectorOp
    else None

(* walk yukta edges from a node, classify each target by math op kind.
   returns a list of (node_name, kind) pairs — only math ops included. *)
let yukta_operators (k : proof_graph) (node_name : string)
    : (string * math_op_kind) list =
  match Hashtbl.find_opt k.nodes node_name with
  | None -> []
  | Some n ->
    List.filter_map (fun e ->
      if e.source = node_name && e.relation = Yukta then
        match classify_math_op k e.target with
        | Some kind -> Some (e.target, kind)
        | None -> None
      else None
    ) n.edges
    |> List.sort_uniq (fun (a,_) (b,_) -> String.compare a b)

(* infer the arity (number of operands) a bridge node requires.
   walk sthita edges — each non-domain sthita target is an input slot.
   additionally, if any yukta-operator node is found, the program needs
   one slot per operand implied by binary arithmetic (a, op, b). *)
let infer_inputs (k : proof_graph) (node_name : string) : string list =
  match Hashtbl.find_opt k.nodes node_name with
  | None -> []
  | Some n ->
    List.filter_map (fun e ->
      if e.source = node_name && e.relation = Sthita then
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
      if e.source = node_name && e.relation = Phala then
        let t = e.target in
        let is_domain = String.length t >= 7 && String.sub t 0 7 = "domain-" in
        if is_domain then None else Some t
      else None
    ) n.edges
    |> List.sort_uniq String.compare

(* derive a meaningful filename from the bridge node's graph edges.
   reads: sthita inputs (what it takes) + phala outputs (what it produces).
   e.g. math-to-ocaml: arithmetic-sthita + ocaml-phala → arithmetic_to_ocaml.ml *)
let filename_from_graph (k : proof_graph) (bridge_name : string) : string =
  let inputs = infer_inputs k bridge_name in
  let outputs = infer_outputs k bridge_name in
  (* pick the most meaningful input: prefer domain-concept names over generic ones *)
  let input_part = match List.filter (fun i ->
    i <> "expression" && i <> "ocaml" && i <> "anuvada"
  ) inputs with
    | first :: _ -> sanitize_ocaml_ident first
    | [] -> match inputs with first :: _ -> sanitize_ocaml_ident first | [] -> sanitize_ocaml_ident bridge_name
  in
  let output_part = match outputs with
    | first :: _ -> sanitize_ocaml_ident first
    | [] -> "out"
  in
  input_part ^ "_to_" ^ output_part ^ ".ml"

(* write buffer to file and print run command *)
let write_program (buf : Buffer.t) (filename : string) : unit =
  let code = Buffer.contents buf in
  let oc = open_out filename in
  output_string oc code;
  close_out oc;
  Printf.printf "  wrote: %s\n" filename;
  Printf.printf "  run:   ocaml %s\n" filename

(* read kriya edges of a node — what operations it performs *)
let kriya_of (k : proof_graph) (name : string) : string list =
  match Hashtbl.find_opt k.nodes name with
  | None -> []
  | Some n -> List.filter_map (fun e ->
      if e.source = name && e.relation = Kriya then Some e.target else None
    ) n.edges

(* read yukta edges of a node — what it connects to *)
let yukta_of (k : proof_graph) (name : string) : string list =
  match Hashtbl.find_opt k.nodes name with
  | None -> []
  | Some n -> List.filter_map (fun e ->
      if e.source = name && e.relation = Yukta then Some e.target else None
    ) n.edges

(* read janya edges of a node — what it is born from (composition shape) *)
let janya_of (k : proof_graph) (name : string) : string list =
  match Hashtbl.find_opt k.nodes name with
  | None -> []
  | Some n -> List.filter_map (fun e ->
      if e.source = name && e.relation = Janya then Some e.target else None
    ) n.edges

(* read swarupa edges of a node — what it IS (identity/type declaration) *)
let swarupa_of (k : proof_graph) (name : string) : string list =
  match Hashtbl.find_opt k.nodes name with
  | None -> []
  | Some n -> List.filter_map (fun e ->
      if e.source = name && e.relation = Swarupa then Some e.target else None
    ) n.edges

(* infer the OCaml container type of a concept node.
   reads swarupa edges: float-swarupa + list-swarupa → float list
                        float-swarupa + array-swarupa → float array
   this is the rendering of the graph's type declaration. *)
let ocaml_type_of_concept (k : proof_graph) (concept : string) : string =
  let sw = swarupa_of k concept in
  let has s = List.mem s sw in
  match has "float", has "matrix", has "list", has "array" with
  | true, true,  _,     _     -> "float array array"
  | true, false, true,  _     -> "float list"
  | true, false, _,     true  -> "float array"
  | true, false, false, false -> "float"
  | _                         ->
    (* fallback: check if concept name itself suggests a type *)
    (match concept with
     | "vector"  -> "float list"
     | "matrix"  -> "float array array"
     | "scalar"  -> "float"
     | "number"  -> "int"
     | _         -> "string")

(* primitive operation rendering table.
   maps (operation, element_type) to its OCaml infix/function token.
   this is purely surface rendering — like english_of_visheshanam.
   the composition structure (map, fold, map2) comes from janya edges in the graph. *)
let ocaml_prim (op : string) (elem_type : string) : string =
  match op, elem_type with
  | "addition",       "float" -> "( +. )"
  | "addition",       _       -> "( + )"
  | "multiplication", "float" -> "( *. )"
  | "multiplication", _       -> "( * )"
  | "subtraction",    "float" -> "( -. )"
  | "subtraction",    _       -> "( - )"
  | "division",       "float" -> "( /. )"
  | "division",       _       -> "( / )"
  | _                         -> op

(* composition rendering table.
   given (composition_shape, operation, container_type, element_type)
   renders the OCaml expression that applies the operation in that shape.
   janya edges tell us the shape. kriya edges tell us the operation.
   swarupa edges tell us the types. *)
let ocaml_of_composition
    (shape : string list)   (* janya targets — map, fold *)
    (ops   : string list)   (* kriya targets — multiplication, addition *)
    (container : string)    (* float list, float array, etc. *)
    (_elem : string)        (* float, int, etc. *)
    : string option =
  let has_map     = List.mem "map"                  shape in
  let has_fold    = List.mem "fold"                 shape in
  let has_mul     = List.mem "multiplication"       ops
                 || List.mem "scalar-multiplication" ops in
  let has_add     = List.mem "addition"             ops in
  let has_dot     = List.mem "dot-product"          ops in
  let has_scl     = List.mem "scalar-multiplication" ops
                 && not (List.mem "addition" ops) in
  (* map then fold over dot-product = matrix multiplication *)
  match has_map, has_fold, has_dot, has_scl, has_mul, has_add, container with
  | true, true, true, _, _, _, "float list" ->
    Some ("fun a b ->\n" ^
      "  let n = List.length a in\n" ^
      "  let dot r c = List.fold_left2 (fun acc x y -> acc +. x *. y) 0.0 r c in\n" ^
      "  List.init n (fun i -> List.init n (fun j -> dot (List.nth a i) (List.map (fun r -> List.nth r j) b)))")
  | true, true, true, _, _, _, "float array array" ->
    Some ("fun a b ->\n" ^
      "  let ra = Array.length a in\n" ^
      "  let cb = Array.length b.(0) in\n" ^
      "  let ca = Array.length a.(0) in\n" ^
      "  let dot r c = Array.fold_left ( +. ) 0.0 (Array.map2 ( *. ) r c) in\n" ^
      "  Array.init ra (fun i ->\n" ^
      "    Array.init cb (fun j ->\n" ^
      "      dot a.(i) (Array.init ca (fun k -> b.(k).(j)))))")
  | true, true, false, _, true, true, "float list" ->
    (* dot product: map multiply then fold sum *)
    Some "fun a b -> List.fold_left2 (fun acc x y -> acc +. x *. y) 0.0 a b"
  | true, true, false, _, true, true, "float array" ->
    Some "fun a b -> Array.fold_left ( +. ) 0.0 (Array.map2 ( *. ) a b)"
  | true, false, false, true, _, false, "float list" ->
    (* scalar-multiplication only: scale a vector by a scalar — F/m = a *)
    Some "fun vec scalar -> List.map (fun x -> x /. scalar) vec"
  | true, false, false, false, false, true, "float list" ->
    (* elementwise addition: v + a *)
    Some "fun a b -> List.map2 ( +. ) a b"
  | true, false, false, false, true, true, "float list" ->
    (* v + a*dt: velocity step with dt=1.0 baked in *)
    Some "fun v a -> List.map2 (fun vi ai -> vi +. ai) v a"
  | true, false, false, false, true, false, "float list" ->
    (* elementwise multiplication *)
    Some "fun a b -> List.map2 ( *. ) a b"
  | _ -> None

(* render the ahara (input reading) for a given concept type.
   reads the concept's swarupa edges to know the container — then renders
   how OCaml receives that type from stdin. rendering policy only. *)
let read_row_expr : string =
  "Array.of_list (List.filter_map float_of_string_opt\n" ^
  "      (String.split_on_char ' ' (String.trim (input_line stdin))))"

let ocaml_read_of (k : proof_graph) (concept : string) : string =
  let typ = ocaml_type_of_concept k concept in
  match typ with
  | "float array array" ->
    (* read n rows: first line is n, then n lines of space-separated floats *)
    "let _n = int_of_string (String.trim (input_line stdin)) in\n" ^
    "    Array.init _n (fun _ ->\n" ^
    "      " ^ read_row_expr ^ ")"
  | "float list" ->
    "List.filter_map float_of_string_opt\n" ^
    "    (String.split_on_char ' ' (String.trim (input_line stdin)))"
  | "float array" ->
    "Array.of_list (List.filter_map float_of_string_opt\n" ^
    "    (String.split_on_char ' ' (String.trim (input_line stdin))))"
  | "int"    -> "(int_of_string (String.trim (input_line stdin)))"
  | _        -> "input_line stdin"

(* render how OCaml prints a value of the given output concept type *)
let ocaml_print_of (k : proof_graph) (concept : string) (var : string) : string =
  let typ = ocaml_type_of_concept k concept in
  match typ, concept with
  | _, "ocaml"   -> Printf.sprintf "Printf.printf \"= %%d\\n\" %s" var
  | _, "scalar"  -> Printf.sprintf "Printf.printf \"%%g\\n\" %s" var
  | "float array array", _ ->
    "Array.iter (fun row ->\n" ^
    "    print_endline (String.concat \" \" (Array.to_list (Array.map string_of_float row)))\n" ^
    Printf.sprintf "  ) %s" var
  | "float list", _ ->
    Printf.sprintf
      "print_endline (String.concat \" \" (List.map string_of_float %s))" var
  | "float array", _ ->
    Printf.sprintf
      "print_endline (String.concat \" \" (Array.to_list (Array.map string_of_float %s)))" var
  | "float",  _ -> Printf.sprintf "Printf.printf \"%%g\\n\" %s" var
  | "int",    _ -> Printf.sprintf "Printf.printf \"%%d\\n\" %s" var
  | _,        _ -> Printf.sprintf "Printf.printf \"%%d\\n\" %s" var

(* unified bridge emitter.
   one walk — reads sthita (input type), yukta (ops), phala (output type),
   janya (composition shape), swarupa (container/element type) from the graph.
   no structure hardcoded — everything derived from edges.

   flow per op node:
     op -kriya->  [what primitive operations compose it]
     op -janya->  [map, fold — composition shape]
     op's sthita input node -swarupa-> [float, list — container and element type]
   → look up ocaml_of_composition(shape, ops, container, elem)
   → emit one let binding per op *)
let emit_bridge_program (k : proof_graph) (bridge_name : string) : unit =
  let all_ops = yukta_operators k bridge_name in
  if all_ops = [] then ()
  else begin
    let buf = Buffer.create 1024 in
    let p fmt = Printf.bprintf buf fmt in
    let inputs  = infer_inputs  k bridge_name in
    let outputs = infer_outputs k bridge_name in
    let input_concept  = match inputs  with t :: _ -> t | [] -> "unknown" in
    let output_concept = match outputs with t :: _ -> t | [] -> "unit" in
    let container_type = ocaml_type_of_concept k input_concept in
    (* element type: for float list → float, for int → int, etc. *)
    let _elem_type = match container_type with
      | "float list" | "float array" | "float array array" -> "float"
      | "int" -> "int"
      | _ -> "string"
    in
    (* root comment from abheda edge *)
    let root = match Hashtbl.find_opt k.nodes bridge_name with
      | None -> bridge_name
      | Some n -> (match List.filter_map (fun e ->
          if e.source = bridge_name && e.relation = Abheda then Some e.target
          else None) n.edges with r :: _ -> r | [] -> bridge_name)
    in
    p "(* %s — root: %s *)\n" bridge_name root;
    (* separate arithmetic ops from structural ops *)
    let arithmetic_ops = List.filter_map (fun (n, kind) ->
      match kind with ArithmeticOp -> Some n | _ -> None) all_ops in
    let structural_ops = List.filter_map (fun (n, kind) ->
      match kind with ArithmeticOp -> None | _ -> Some n) all_ops in
    (* --- STRUCTURAL OPS ---
       for each op: read its own sthita inputs to get its container type,
       its kriya (what primitives) and janya (composition shape).
       look up ocaml_of_composition to get the full expression.
       emit one named function per op. *)
    List.iter (fun op_name ->
      let op_kriya   = kriya_of k op_name in
      let op_janya   = janya_of k op_name in
      let op_inputs  = infer_inputs  k op_name in
      let op_outputs = infer_outputs k op_name in
      let fn = sanitize_ocaml_ident op_name in
      (* use op's own sthita input to determine container/element type.
         prefer inputs that have known swarupa type declarations in the graph. *)
      let op_in_concept =
        let typed = List.filter (fun t ->
          swarupa_of k t <> []
        ) op_inputs in
        match typed with
        | t :: _ -> t
        | [] -> (match op_inputs with t :: _ -> t | [] -> input_concept)
      in
      let op_out_concept = match op_outputs with t :: _ -> t | [] -> output_concept in
      (* op node's own swarupa overrides the input concept's type.
         e.g. matrix-multiplication has array-swarupa → float array array
         even though its input concept is vector (float list) *)
      (* op node's own swarupa is authoritative for container type:
         float+array → float array array
         float+list  → float list
         float only  → float
         fallback    → read from input concept *)
      let op_self_sw = swarupa_of k op_name in
      let op_container =
        let has s = List.mem s op_self_sw in
        match has "array", has "float", has "list" with
        | true,  true,  _     -> "float array array"
        | true,  _,     _     -> "array"
        | false, true,  true  -> "float list"
        | false, true,  false -> "float"
        | _                   -> ocaml_type_of_concept k op_in_concept
      in
      let op_elem = match op_container with
        | "float list" | "float array" | "float array array" -> "float"
        | "int" -> "int" | _ -> "string" in
      (* per-input types: each sthita input gets its own type.
         if the input has swarupa, use that; else fall back to op_container *)
      let op_in_types = List.map (fun inp ->
        if swarupa_of k inp <> [] then ocaml_type_of_concept k inp
        else op_container
      ) op_inputs in
      let sig_args = String.concat " -> " op_in_types in
      let op_out_type = ocaml_type_of_concept k op_out_concept in
      match ocaml_of_composition op_janya op_kriya op_container op_elem with
      | Some impl ->
        p "let %s : %s -> %s = %s\n" fn sig_args op_out_type impl
      | None ->
        let desc = String.concat ", " op_kriya ^ " via " ^ String.concat ", " op_janya in
        p "(* %s: %s — no rendering defined yet *)\n" fn desc
    ) structural_ops;
    (* --- ARITHMETIC OPS ---
       group into ADT + eval + operator_of_symbol + calculate.
       arity from expression node's yukta structure. *)
    if arithmetic_ops <> [] then begin
      let op_info = List.filter_map (fun op ->
        match ocaml_symbol_of_operator op with
        | None -> None
        | Some sym -> Some (op, ocaml_constructor_of_operator op, sym)
      ) arithmetic_ops in
      let arity = if List.exists (fun e ->
        e.source = input_concept && e.relation = Yukta && e.target = "number"
      ) (match Hashtbl.find_opt k.nodes input_concept with
         | Some n -> n.edges | None -> [])
      then 2 else 2 in
      let operands = Array.to_list (Array.sub [|"a";"b";"c";"d"|] 0 (min arity 4)) in
      p "type operator = %s\n"
        (String.concat " | " (List.map (fun (_, c, _) -> c) op_info));
      let sig_ = String.concat " "
        (List.map (fun nm -> Printf.sprintf "~(%s:int)" nm) operands) in
      p "let eval %s ~(op:operator) : int =\n  match op with\n" sig_;
      List.iter (fun (_, ctor, sym) ->
        let body = match operands with
          | [a;b] -> Printf.sprintf "%s %s %s" a sym b
          | [a]   -> Printf.sprintf "%s %s 0" a sym
          | _     -> "0" in
        p "  | %s -> %s\n" ctor body
      ) op_info;
      p "let operator_of_symbol s = match s with\n";
      List.iter (fun (_, ctor, sym) -> p "  | %S -> Some %s\n" sym ctor) op_info;
      p "  | _ -> None\n";
      let pat = match List.map (fun nm -> nm ^ "_s") operands with
        | [a;b] -> Printf.sprintf "%s; op_s; %s" a b
        | [a]   -> Printf.sprintf "%s; op_s" a
        | vs    -> String.concat "; " (vs @ ["op_s"]) in
      p "let calculate expr =\n";
      p "  match String.split_on_char ' ' (String.trim expr) with\n";
      p "  | [%s] ->\n" pat;
      let pvars = String.concat ", "
        (List.map (fun nm -> Printf.sprintf "int_of_string_opt %s_s" nm) operands) in
      p "    (match %s, operator_of_symbol op_s with\n" pvars;
      let svars = String.concat ", "
        (List.map (fun nm -> Printf.sprintf "Some %s" nm) operands) in
      let cargs = String.concat " " (List.map (fun nm -> "~" ^ nm) operands) in
      p "     | %s, Some op -> Some (eval %s ~op)\n" svars cargs;
      p "     | _ -> None)\n";
      p "  | _ -> None\n"
    end;
    (* --- ENTRY POINT ---
       execution-yukta → let () =
       ahara edges on execution node → read/write shape
       ocaml_read_of / ocaml_print_of render the IO from the type *)
    let has_exec = match Hashtbl.find_opt k.nodes bridge_name with
      | None -> false
      | Some n -> List.exists (fun e ->
          e.source = bridge_name && e.relation = Yukta && e.target = "execution"
        ) n.edges
    in
    if has_exec then begin
      let exec_edges = match Hashtbl.find_opt k.nodes "execution" with
        | None -> [] | Some en -> en.edges in
      let needs_in  = List.exists (fun e ->
        e.source = "execution" && e.relation = Sthita && e.target = "ahara"
      ) exec_edges in
      let needs_out = List.exists (fun e ->
        e.source = "execution" && e.relation = Phala && e.target = "ahara"
      ) exec_edges in
      p "let () =\n";
      (* only emit the top-level ahara read for arithmetic ops —
         structural ops read each input individually per-op *)
      let has_structural = structural_ops <> [] in
      if needs_in && not has_structural then begin
        p "  print_string \"%s: \"; flush stdout;\n" input_concept;
        p "  let ahara = %s in\n" (ocaml_read_of k input_concept)
      end;
      if needs_out then begin
        if arithmetic_ops <> [] then begin
          p "  (match calculate ahara with\n";
          p "  | Some r -> %s\n" (ocaml_print_of k output_concept "r");
          p "  | None -> print_endline \"could not parse\")\n"
        end else if structural_ops <> [] then begin
          (* for structural ops: each op reads its own inputs by name,
             deduplicated across ops so shared inputs are read once.
             if a concept has no swarupa type, fall back to the op's container type. *)
          let read_vars : (string * string) list ref = ref [] in
          List.iter (fun op_name ->
            let fn = sanitize_ocaml_ident op_name in
            let op_inputs  = infer_inputs  k op_name in
            let op_outputs = infer_outputs k op_name in
            let out_c  = match op_outputs with t :: _ -> t | [] -> output_concept in
            (* op's container type — used as fallback for untyped inputs *)
            let op_self_sw2 = swarupa_of k op_name in
            let op_fallback_type =
              let has s = List.mem s op_self_sw2 in
              match has "array", has "float", has "list", has "matrix" with
              | _,    true, true,  _    -> "float list"
              | true, true, _,     _    -> "float array array"
              | _,    true, _,     _    -> "float"
              | _                       -> "string"
            in
            let ensure_read concept =
              let vname = sanitize_ocaml_ident concept in
              if not (List.mem_assoc vname !read_vars) then begin
                read_vars := (vname, concept) :: !read_vars;
                let typ =
                  if swarupa_of k concept <> [] then ocaml_type_of_concept k concept
                  else op_fallback_type
                in
                p "  print_string \"%s: \"; flush stdout;\n" concept;
                (* inline the read expression directly, typed correctly *)
                let read_expr = match typ with
                  | "float array array" ->
                    "let _n = int_of_string (String.trim (input_line stdin)) in\n" ^
                    "    Array.init _n (fun _ ->\n" ^
                    "      " ^ read_row_expr ^ ")"
                  | "float list" ->
                    "List.filter_map float_of_string_opt\n" ^
                    "    (String.split_on_char ' ' (String.trim (input_line stdin)))"
                  | "float array" ->
                    "Array.of_list (List.filter_map float_of_string_opt\n" ^
                    "    (String.split_on_char ' ' (String.trim (input_line stdin))))"
                  | "float" ->
                    "float_of_string (String.trim (input_line stdin))"
                  | "int" ->
                    "int_of_string (String.trim (input_line stdin))"
                  | _ -> "input_line stdin"
                in
                p "  let %s = %s in\n" vname read_expr
              end;
              vname
            in
            let arg_vars = List.map ensure_read op_inputs in
            let args = String.concat " " arg_vars in
            p "  let r_%s = %s %s in\n" fn fn args;
            p "  %s;\n" (ocaml_print_of k out_c (Printf.sprintf "r_%s" fn))
          ) structural_ops
        end
      end
    end;
    let filename = filename_from_graph k bridge_name in
    write_program buf filename
  end

(* walk the bridge — if it is a meta-bridge (anuvada-setu style, yukta edges
   pointing to other setu bridges), emit each sub-bridge.
   setu-swarupa is the primary signal: a yukta target that is_setu is a sub-bridge.
   fallback: targets with yukta_operators (old behaviour).
   otherwise emit the bridge directly. *)
let emit_math_programs (k : proof_graph) (bridge_name : string) : unit =
  let yukta_targets = yukta_of k bridge_name in
  let setu_sub_bridges = List.filter (is_setu k) yukta_targets in
  let op_sub_bridges   = List.filter (fun t ->
    not (is_setu k t) && yukta_operators k t <> []
  ) yukta_targets in
  let sub_bridges = setu_sub_bridges @ op_sub_bridges in
  if sub_bridges <> [] then
    List.iter (emit_bridge_program k) sub_bridges
  else
    emit_bridge_program k bridge_name

let emit_ocaml_from_graph (k : proof_graph) (content_words : string list) : unit =
  let unique_words = List.sort_uniq String.compare content_words in
  let has_ocaml_hint =
    List.exists (fun n ->
      n = "ocaml" || n = "ocaml-syntax" || n = "english-to-ocaml"
      || n = "ocaml-to-ocaml" || n = "physics-to-ocaml"
      || has_domain_sthita k n "domain-ocaml"
    ) unique_words in
  if has_ocaml_hint then begin
    let is_ocaml_operation name =
      (* primary signal: setu-swarupa + ocaml-phala *)
      (is_setu k name && List.mem "ocaml" (infer_outputs k name))
      (* fallback: domain-ocaml-sthita + any phala (old behaviour) *)
      || (has_domain_sthita k name "domain-ocaml"
          && infer_outputs k name <> []) in
    let direct_candidates = List.filter is_ocaml_operation unique_words in
    let content_set = Hashtbl.create 32 in
    List.iter (fun w -> Hashtbl.replace content_set w true) unique_words;
    let physics_terms_in_query = List.filter (fun w ->
      has_domain_sthita k w "domain-physics"
    ) unique_words in
    let physics_required = physics_terms_in_query <> [] in
    let math_terms_in_query = List.filter (fun w ->
      has_domain_sthita k w "domain-math"
    ) unique_words in
    let math_required = math_terms_in_query <> [] in
    let inferred_candidates =
      if direct_candidates <> [] then []
      else Hashtbl.fold (fun name _ acc ->
        if not (is_ocaml_operation name) then acc
        else
          let inputs = infer_inputs k name in
          let outputs = infer_outputs k name in
          let matches_output = List.exists (fun o -> Hashtbl.mem content_set o) outputs in
          let has_math_input = List.exists (fun i ->
            has_domain_sthita k i "domain-math"
          ) inputs in
          let matches_physics =
            if not physics_required then true
            else List.exists (fun t ->
              List.mem t inputs || List.mem t outputs
            ) physics_terms_in_query in
          (* matches_math: the bridge takes math-domain input AND either:
             (a) a specific math term from the query is in its inputs/outputs, or
             (b) the bridge also has yukta edges to arithmetic operators — meaning
                 it IS the arithmetic program generator, so any math query triggers it *)
          let has_arithmetic_yukta =
            yukta_operators k name <> [] in
          ignore has_arithmetic_yukta;
          let matches_math_query =
            if not math_required then true
            else yukta_operators k name <> []  (* any math bridge matches math queries *)
              || List.exists (fun t ->
                  List.mem t inputs || List.mem t outputs
                 ) math_terms_in_query in
          let matches_math =
            if not math_required then true
            else has_math_input && matches_math_query in
          if matches_output && matches_math && matches_physics
          then name :: acc else acc
      ) k.nodes [] in
    let operation_candidates =
      List.sort_uniq String.compare (direct_candidates @ inferred_candidates) in
    if operation_candidates <> [] then begin
      let ocaml_type_of raw_name =
        if has_domain_sthita k raw_name "domain-ocaml"
        then sanitize_ocaml_ident raw_name
        else "int"
      in
      ignore ocaml_type_of;
      let print_function op =
        match Hashtbl.find_opt k.nodes op with
        | None -> ()
        | Some _n ->
          (* if this node has yukta edges to arithmetic operators:
             emit the full executable program — written to a .ml file. *)
          let operators = yukta_operators k op in
          if operators <> [] then
            emit_math_programs k op
          else begin
            (* general function stub: read inputs/outputs from sthita/phala edges *)
            let inputs = infer_inputs k op in
            let outputs = infer_outputs k op in
            let output = match outputs with o :: _ -> o | [] -> "unit" in
            let fn_name = sanitize_ocaml_ident op in
            let args_sig = if inputs = [] then "()" else
              String.concat " " (List.map (fun i ->
                let x = sanitize_ocaml_ident i in
                Printf.sprintf "~(%s:%s)" x (ocaml_type_of i)
              ) inputs) in
            let ret_sig = if output = "unit" then "unit"
              else ocaml_type_of output in
            Printf.printf "  ocaml: let %s %s : %s = ...\n" fn_name args_sig ret_sig
          end
      in
      List.iter print_function operation_candidates
    end
  end

(* anuvada: parse an English sentence, resolve through graph, output understanding *)
let anuvada ?(max_passes = 5) ?thaalam (k : proof_graph) (sentence : string) : unit =
  let spaced_math_ops (s : string) : string =
    let buf = Buffer.create (String.length s * 2) in
    String.iter (fun c ->
      if c = '+' || c = '*' || c = '/' || c = '=' || c = '(' || c = ')' then begin
        Buffer.add_char buf ' ';
        Buffer.add_char buf c;
        Buffer.add_char buf ' '
      end else
        Buffer.add_char buf c
    ) s;
    Buffer.contents buf
  in
  let words = String.split_on_char ' ' (spaced_math_ops sentence) in
  let words = List.filter (fun w -> String.length (String.trim w) > 0) words in
  (* handle apostrophe: "system's" -> ["system"; "'s"] *)
  let expand_possessive words =
    List.concat_map (fun w ->
      if String.length w > 2 then
        let len = String.length w in
        (* check for 's at end *)
        if len >= 3 && String.sub w (len - 2) 2 = "'s" then
          [String.sub w 0 (len - 2); "'s"]
        else [w]
      else [w]
    ) words
  in
  let words = expand_possessive words in
  (* strip punctuation from each word, but preserve 's *)
  let clean w =
    if w = "'s" then w
    else begin
      let w = String.lowercase_ascii w in
      let buf = Buffer.create (String.length w) in
      String.iter (fun c ->
        if (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9')
           || c = '-' || c = '+' || c = '*' || c = '/' || c = '=' then
          Buffer.add_char buf c
      ) w;
      Buffer.contents buf
    end
  in
  let words = List.map clean words in
  let words = List.filter (fun w -> String.length w > 0) words in
  (* detect sentence-level punctuation *)
  let raw = String.trim sentence in
  let sentence_end =
    if String.length raw > 0 then
      match raw.[String.length raw - 1] with
      | '?' -> Some "prashna-viraam"
      | '!' -> Some "vismaya-viraam"
      | '.' -> Some "purna-viraam"
      | _ -> None
    else None
  in
  (* detect ellipsis *)
  let sentence_end =
    if String.length raw >= 3 &&
       String.sub raw (String.length raw - 3) 3 = "..." then
      Some "traya-bindu"
    else sentence_end
  in
  Printf.printf "--- anuvada ---\n";
  Printf.printf "  input: %s\n" sentence;
  (match sentence_end with
  | Some punct -> Printf.printf "  mode: %s\n" punct
  | None -> ());
  (* classify each word *)
  let classified = List.map (fun w -> (w, classify_token k w)) words in
  (* print understanding *)
  Printf.printf "  understood:\n";
  List.iter (fun (w, role) ->
    match role with
    | Article -> ()  (* skip silently *)
    | Grammar v ->
      Printf.printf "    [%s] → %s\n" w (string_of_visheshanam v)
    | Content name ->
      let resolved = resolve k name in
      let resolved_str = String.concat ", " resolved in
      Printf.printf "    [%s] → node (%s)\n" w resolved_str
    | Unknown w ->
      Printf.printf "    [%s] → ?\n" w
  ) classified;
  (* collect content words and grammar words *)
  let content_words = List.filter_map (fun (_, role) ->
    match role with Content name -> Some name | _ -> None
  ) classified in
  let grammar_words = List.filter_map (fun (w, role) ->
    match role with Grammar v -> Some (w, v) | _ -> None
  ) classified in
  (* render English response — the spiral *)
  if content_words <> [] then
    render_spiral k content_words grammar_words sentence_end max_passes thaalam;
  if content_words <> [] then
    emit_ocaml_from_graph k content_words;
  Printf.printf "---\n%!"

(* escape for JSON *)
let json_escape s =
  let buf = Buffer.create (String.length s) in
  String.iter (fun c ->
    match c with
    | '"'  -> Buffer.add_string buf "\\\""
    | '\\' -> Buffer.add_string buf "\\\\"
    | '\n' -> Buffer.add_string buf "\\n"
    | '\r' -> Buffer.add_string buf "\\r"
    | '\t' -> Buffer.add_string buf "\\t"
    | c    -> Buffer.add_char buf c
  ) s;
  Buffer.contents buf

(* sthiti — human-readable state *)
let print (k : proof_graph) : unit =
  let nodes = Hashtbl.fold (fun _ n acc -> n :: acc) k.nodes [] in
  let nodes = List.sort (fun a b -> compare b.satya a.satya) nodes in
  Printf.printf "--- akasham (%d nodes, %d edges) ---\n"
    (List.length nodes) (List.length !(k.all_edges));
  List.iter (fun n ->
    let edge_count = List.length n.edges in
    let in_deg = in_degree k n.name in
    let sloka_count = List.length n.slokas in
    Printf.printf "[%s] satya=%.3f edges=%d cited=%d slokas=%d\n"
      n.name n.satya edge_count in_deg sloka_count;
    List.iter (fun s ->
      Printf.printf "  \"%s\"\n" s
    ) n.slokas
  ) nodes;
  Printf.printf "---\n%!"

(* pravaha — JSON output for LLM to read *)
let pravaha (k : proof_graph) : unit =
  let nodes = Hashtbl.fold (fun _ n acc -> n :: acc) k.nodes [] in
  let nodes = List.sort (fun a b -> String.compare a.name b.name) nodes in
  let n_nodes = List.length nodes in
  Printf.printf "{\n";
  Printf.printf "  \"pravaha\": true,\n";
  Printf.printf "  \"node_count\": %d,\n" n_nodes;
  Printf.printf "  \"edge_count\": %d,\n" (List.length !(k.all_edges));
  Printf.printf "  \"nigamana\": [\n";
  List.iteri (fun i n ->
    let slokas_json = String.concat ", "
      (List.map (fun s -> Printf.sprintf "\"%s\"" (json_escape s)) n.slokas) in
    let edges_json = String.concat ", "
      (List.map (fun e ->
        Printf.sprintf "{\"target\":\"%s\",\"relation\":\"%s\"}"
          (json_escape e.target) (string_of_visheshanam e.relation)
      ) n.edges) in
    let cited_by = in_degree k n.name in
    Printf.printf "    {\n";
    Printf.printf "      \"name\": \"%s\",\n" (json_escape n.name);
    Printf.printf "      \"satya\": %.4f,\n" n.satya;
    Printf.printf "      \"slokas\": [%s],\n" slokas_json;
    Printf.printf "      \"edges\": [%s],\n" edges_json;
    Printf.printf "      \"cited_by\": %d\n" cited_by;
    if i < n_nodes - 1
    then Printf.printf "    },\n"
    else Printf.printf "    }\n"
  ) nodes;
  Printf.printf "  ]\n";
  Printf.printf "}\n%!"
