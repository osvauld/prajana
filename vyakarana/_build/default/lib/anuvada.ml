(* anuvada.ml — graph reasoning and text output layer.
   reads the proof graph via Setu, answers questions by walking edges.

   load-bearing surface:
     english_of_visheshanam_from_graph  — used by yantra primitives
     avrti_anuvada                      — the spiral walk; used by yantra 'avrti' primitive
     render_darshana_to_buf             — used by yantra 'render-node' primitive
     anuvada_query                      — called by socket.ml per question request
     output_flags / flags_default / parse_inline_flags / flags_of_show_string
                                        — used by socket.ml and vyakarana.ml for --show / +flags
     print                              — SHOW/STHITI command in stdin mode
     pravaha                            — FLOW/PRAVAHA command in stdin mode

   removed: ocaml code-emission (~470 lines), anuvada stdout wrapper,
            sahaja_gloss / sahaja_render (only needed by verify.ml which is deleted).

   dependency: Proof_graph, Setu. *)

open Proof_graph

(* ---- visheshanam → English phrase ---- *)

let english_of_visheshanam_cache : (string, string) Hashtbl.t = Hashtbl.create 16
let english_of_visheshanam_loaded = ref false

let load_english_of_visheshanam (k : proof_graph) : unit =
  if not !english_of_visheshanam_loaded then begin
    english_of_visheshanam_loaded := true;
    let pairs = Setu.read_shabda k "visheshanam-english" in
    List.iter (fun (vish, eng) ->
      Hashtbl.replace english_of_visheshanam_cache vish eng
    ) pairs
  end

let english_of_visheshanam_from_graph (k : proof_graph) (v : visheshanam) : string =
  load_english_of_visheshanam k;
  let key = string_of_visheshanam v in
  match Hashtbl.find_opt english_of_visheshanam_cache key with
  | Some s -> s
  | None -> key

(* ---- avrti: the spiral walk over graph edges ---- *)

type anuvada_triple = {
  a_source      : string;
  a_source_raw  : string;
  a_relation    : visheshanam;
  a_targets     : string list;
  a_targets_raw : string list;
  a_pass        : int;
}

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

let walk_one_pass (k : proof_graph) (content_words : string list)
    (visited_nodes : (string, bool) Hashtbl.t) (pass_num : int)
    : anuvada_triple list * string list =
  let triples = ref [] in
  let new_targets = ref [] in
  List.iter (fun name ->
    if not (Hashtbl.mem visited_nodes name) then begin
      Hashtbl.add visited_nodes name true;
      let english_name = Setu.to_english k name in
      match Hashtbl.find_opt k.nodes name with
      | None -> ()
      | Some n ->
        let by_type = Hashtbl.create 9 in
        List.iter (fun e ->
          if e.source = name then begin
            let targets = match Hashtbl.find_opt by_type e.relation with
              | Some lst -> lst | None -> [] in
            Hashtbl.replace by_type e.relation (e.target :: targets)
          end
        ) n.edges;
        Hashtbl.iter (fun vish targets ->
          let target_pairs = List.map (fun t -> (t, Setu.to_english k t)) targets in
          let target_pairs = List.sort_uniq (fun (r1, e1) (r2, e2) ->
            let c = String.compare e1 e2 in
            if c <> 0 then c else String.compare r1 r2
          ) target_pairs in
          let target_pairs = List.filter (fun (_raw, eng) ->
            eng <> english_name
          ) target_pairs in
          let unique_targets     = List.sort_uniq String.compare (List.map snd target_pairs) in
          let unique_targets_raw = List.sort_uniq String.compare (List.map fst target_pairs) in
          if unique_targets <> [] then
            triples := { a_source      = english_name;
                         a_source_raw  = name;
                         a_relation    = vish;
                         a_targets     = unique_targets;
                         a_targets_raw = unique_targets_raw;
                         a_pass        = pass_num } :: !triples;
          List.iter (fun t -> new_targets := t :: !new_targets) targets
        ) by_type
    end
  ) content_words;
  (List.rev !triples, List.sort_uniq String.compare !new_targets)

let avrti_anuvada (k : proof_graph) (seed_words : string list)
    (max_passes : int) : (int * anuvada_triple list) list * int =
  let visited_nodes = Hashtbl.create 64 in
  let seen_triples  = ref TripleSet.empty in
  let passes_result = ref [] in
  let pass          = ref 0 in
  let current_words = ref seed_words in
  let found_new     = ref true in
  while !found_new && !pass < max_passes do
    incr pass;
    let (triples, new_targets) = walk_one_pass k !current_words visited_nodes !pass in
    let (novel, updated_seen) = List.fold_left (fun (acc, seen) t ->
      let key = (t.a_source, t.a_relation, t.a_targets) in
      if TripleSet.mem key seen then (acc, seen)
      else (t :: acc, TripleSet.add key seen)
    ) ([], !seen_triples) triples in
    let novel = List.rev novel in
    if novel = [] then
      found_new := false
    else begin
      seen_triples  := updated_seen;
      passes_result := !passes_result @ [(!pass, novel)];
      current_words := List.filter (fun n ->
        not (Hashtbl.mem visited_nodes n)
      ) new_targets
    end
  done;
  (!passes_result, !pass)

(* ---- render helpers ---- *)

let render_pass_groups_simple ?(context : string option = None)
    (k : proof_graph) (pass_groups : (int * anuvada_triple list) list) : string =
  let buf = Buffer.create 512 in
  let render_name raw = Setu.to_english ~context k raw in
  let render_triple (t : anuvada_triple) =
    let rel  = english_of_visheshanam_from_graph k t.a_relation in
    let tgts = String.concat ", " (List.map render_name t.a_targets_raw) in
    Printf.sprintf "  %s %s %s.\n" (render_name t.a_source_raw) rel tgts
  in
  List.iter (fun (_p, triples) ->
    List.iter (fun t -> Buffer.add_string buf (render_triple t)) triples
  ) pass_groups;
  Buffer.contents buf

(* sahaja helpers — gloss + render for node inspection *)

let sahaja_gloss (k : proof_graph) (name : string) : string =
  (* Priority:
     1. shabda "name" key  — e.g.  shabda name:render-node
     2. text before "/"   — e.g.  shabda velocity / rate-of-change-...
     3. Setu.to_english fallback *)
  match find k name with
  | Some n when String.trim n.shabda <> "" ->
    let pairs = Setu.parse_shabda n.shabda in
    (match List.assoc_opt "name" pairs with
    | Some v when String.trim v <> "" -> String.trim v
    | _ ->
      (* try text before "/" in raw shabda *)
      let raw = String.trim n.shabda in
      (match String.index_opt raw '/' with
      | Some i ->
        let before = String.trim (String.sub raw 0 i) in
        if String.length before > 0 then before
        else Setu.to_english k name
      | None -> Setu.to_english k name))
  | _ -> Setu.to_english k name

let sahaja_render (k : proof_graph) (name : string) : string =
  let gloss = sahaja_gloss k name in
  if gloss = name then name
  else Printf.sprintf "%s (%s)" gloss name

(* render darshana (node inspection) to a buffer — used by yantra render-node primitive *)
let render_darshana_to_buf (k : proof_graph) (n : nigamana) (buf : Buffer.t) : unit =
  let gloss = sahaja_gloss k n.name in
  Buffer.add_string buf (Printf.sprintf "--- %s (%s) satya=%.4f ---\n" gloss n.name n.satya);
  List.iter (fun s ->
    Buffer.add_string buf (Printf.sprintf "  \"%s\"\n" s)
  ) n.slokas;
  let edges = Proof_graph.edges_of k n.name in
  if edges <> [] then begin
    Buffer.add_string buf "  edges:\n";
    List.iter (fun e ->
      let rel_str = Proof_graph.string_of_visheshanam e.Proof_graph.relation in
      if e.Proof_graph.source = n.name then
        Buffer.add_string buf (Printf.sprintf "    -> %s [%s]\n"
          (sahaja_render k e.target) rel_str)
      else
        Buffer.add_string buf (Printf.sprintf "    <- %s [%s]\n"
          (sahaja_render k e.source) rel_str)
    ) edges
  end;
  let cited = Proof_graph.in_degree k n.name in
  Buffer.add_string buf (Printf.sprintf "  cited_by: %d\n---" cited)

(* ---- query result ---- *)

type query_result = {
  qr_answer_text   : string;
  qr_steps         : (int * anuvada_triple list) list;
  qr_next_qs       : string list;
  qr_content_words : string list;
  qr_passes        : int;
  qr_connections   : int;
  qr_confidence    : float;
}

(* anuvada_query — pure: tokenise sentence, walk graph, return structured result *)
let anuvada_query ?(max_passes = 2)
    ?(request_id = "") ?(session_id = "") ?(turn_id = "")
    (k : proof_graph) (sentence : string) : query_result =
  ignore (request_id, session_id, turn_id);
  let spaced_math_ops s =
    let buf = Buffer.create (String.length s * 2) in
    String.iter (fun c ->
      if c = '+' || c = '*' || c = '/' || c = '=' || c = '(' || c = ')' then begin
        Buffer.add_char buf ' '; Buffer.add_char buf c; Buffer.add_char buf ' '
      end else Buffer.add_char buf c
    ) s;
    Buffer.contents buf
  in
  let words = String.split_on_char ' ' (spaced_math_ops sentence) in
  let words = List.filter (fun w -> String.length (String.trim w) > 0) words in
  let expand_possessive =
    List.concat_map (fun w ->
      let len = String.length w in
      if len >= 3 && String.sub w (len - 2) 2 = "'s"
      then [String.sub w 0 (len - 2); "'s"]
      else [w]
    )
  in
  let words = expand_possessive words in
  let clean w =
    if w = "'s" then w
    else begin
      let w   = String.lowercase_ascii w in
      let len = String.length w in
      let buf = Buffer.create len in
      String.iteri (fun i c ->
        if (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9')
           || c = '-' || c = '+' || c = '*' || c = '/' || c = '=' then
          Buffer.add_char buf c
        else if c = '.' then begin
          let prev_digit = i > 0     && w.[i-1] >= '0' && w.[i-1] <= '9' in
          let next_digit = i < len-1 && w.[i+1] >= '0' && w.[i+1] <= '9' in
          if prev_digit && next_digit then Buffer.add_char buf c
        end
      ) w;
      Buffer.contents buf
    end
  in
  let words = List.filter (fun w -> String.length w > 0) (List.map clean words) in
  let classified  = List.map (fun w -> (w, Setu.classify_token k w)) words in
  let content_words = List.filter_map (fun (_, role) ->
    match role with Setu.Content name -> Some name | _ -> None
  ) classified in
  let context_anchor =
    let rec find_after_sthita = function
      | [] -> None
      | (_, Setu.Grammar v) :: (w, role) :: _ when v = sthita ->
        (match role with
         | Setu.Content name -> Some name
         | Setu.Unknown _ ->
           (match Setu.classify_token k w with
            | Setu.Content name -> Some name
            | _ -> None)
         | _ -> None)
      | _ :: rest -> find_after_sthita rest
    in
    find_after_sthita classified
  in
  let (pass_groups, total_passes) =
    if content_words <> [] then avrti_anuvada k content_words max_passes
    else ([], 0)
  in
  let answer_text =
    if content_words <> []
    then render_pass_groups_simple ~context:context_anchor k pass_groups
    else ""
  in
  let total_triples = List.fold_left (fun acc (_, ts) -> acc + List.length ts) 0 pass_groups in
  let confidence    = List.fold_left (fun best w ->
    match Hashtbl.find_opt k.nodes w with
    | Some n -> if n.satya > best then n.satya else best
    | None   -> best
  ) 0.0 content_words in
  { qr_answer_text   = answer_text
  ; qr_steps         = pass_groups
  ; qr_next_qs       = []
  ; qr_content_words = content_words
  ; qr_passes        = total_passes
  ; qr_connections   = total_triples
  ; qr_confidence    = confidence
  }

(* ---- output flags (used by socket + CLI for --show / inline +flags) ---- *)
(* show_prayoga removed — code emission is gone. flags kept as a type so
   callers compile without change; extend here when new show-sections are added. *)

type output_flags = unit

let flags_default : output_flags = ()

let parse_inline_flags ?(base : output_flags = ()) (sentence : string)
    : string * output_flags =
  ignore base;
  (* strip any +flag tokens; none are currently active *)
  let tokens = String.split_on_char ' ' sentence in
  let rest = List.filter (fun t ->
    let t = String.lowercase_ascii (String.trim t) in
    not (String.length t > 0 && t.[0] = '+')
  ) tokens in
  (String.concat " " (List.filter (fun s -> String.length (String.trim s) > 0) rest), ())

let flags_of_show_string ?(base : output_flags = ()) (s : string)
    : output_flags =
  ignore (base, s); ()

(* ---- sthiti — human-readable graph dump (SHOW/STHITI stdin command) ---- *)

let print (k : proof_graph) : unit =
  let nodes = Hashtbl.fold (fun _ n acc -> n :: acc) k.nodes [] in
  let nodes = List.sort (fun a b -> compare b.satya a.satya) nodes in
  Printf.printf "--- space (akasham): %d nodes, %d edges ---\n"
    (List.length nodes) (List.length !(k.all_edges));
  List.iter (fun n ->
    Printf.printf "[%s] satya=%.3f edges=%d cited=%d slokas=%d\n"
      n.name n.satya
      (List.length n.edges)
      (in_degree k n.name)
      (List.length n.slokas);
    List.iter (fun s -> Printf.printf "  \"%s\"\n" s) n.slokas
  ) nodes;
  Printf.printf "---\n%!"

(* ---- pravaha — full graph as JSON (FLOW/PRAVAHA stdin command) ---- *)

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

let pravaha (k : proof_graph) : unit =
  let nodes   = Hashtbl.fold (fun _ n acc -> n :: acc) k.nodes [] in
  let nodes   = List.sort (fun a b -> String.compare a.name b.name) nodes in
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
    Printf.printf "    {\n";
    Printf.printf "      \"name\": \"%s\",\n"    (json_escape n.name);
    Printf.printf "      \"layer\": \"%s\",\n"   (json_escape n.layer);
    Printf.printf "      \"satya\": %.4f,\n"     n.satya;
    Printf.printf "      \"slokas\": [%s],\n"    slokas_json;
    Printf.printf "      \"edges\": [%s],\n"     edges_json;
    Printf.printf "      \"cited_by\": %d\n"     (in_degree k n.name);
    if i < n_nodes - 1
    then Printf.printf "    },\n"
    else Printf.printf "    }\n"
  ) nodes;
  Printf.printf "  ]\n";
  Printf.printf "}\n%!"
