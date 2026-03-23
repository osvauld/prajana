(* vak.ml — reasoning walks + English rendering.
   replaces anuvada.ml (291L). Uses Prakriti.json_escape (no local copy).

   sections:
     1. visheshanam → English phrase cache
     2. avrti — spiral walk over graph edges
     3. render helpers — pass groups, sahaja gloss
     4. darshana — node inspection rendering
     5. output flags
     6. sthiti — human-readable graph dump
     7. pravaha — full graph as JSON *)

open Prakriti

(* ═══════════════════════════════════════════════════════════════════════════
   1. VISHESHANAM → ENGLISH PHRASE CACHE
   ═══════════════════════════════════════════════════════════════════════════ *)

let english_of_visheshanam_cache : (string, string) Hashtbl.t = Hashtbl.create 16
let english_of_visheshanam_loaded = ref false

let load_english_of_visheshanam (k : proof_graph) : unit =
  if not !english_of_visheshanam_loaded then begin
    english_of_visheshanam_loaded := true;
    let pairs = Vidya.read_shabda k "visheshanam-english" in
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

(* ═══════════════════════════════════════════════════════════════════════════
   2. AVRTI — spiral walk over graph edges
   ═══════════════════════════════════════════════════════════════════════════ *)

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
      let english_name = Vidya.to_english k name in
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
          let target_pairs = List.map (fun t -> (t, Vidya.to_english k t)) targets in
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

(* ═══════════════════════════════════════════════════════════════════════════
   3. RENDER HELPERS
   ═══════════════════════════════════════════════════════════════════════════ *)

let render_pass_groups_simple ?(context : string option = None)
    (k : proof_graph) (pass_groups : (int * anuvada_triple list) list) : string =
  let buf = Buffer.create 512 in
  let render_name raw = Vidya.to_english ~context k raw in
  let render_triple (t : anuvada_triple) =
    let rel  = english_of_visheshanam_from_graph k t.a_relation in
    let tgts = String.concat ", " (List.map render_name t.a_targets_raw) in
    Printf.sprintf "  %s %s %s.\n" (render_name t.a_source_raw) rel tgts
  in
  List.iter (fun (_p, triples) ->
    List.iter (fun t -> Buffer.add_string buf (render_triple t)) triples
  ) pass_groups;
  Buffer.contents buf

let sahaja_gloss (k : proof_graph) (name : string) : string =
  let pairs = Vidya.raw_shabda_for_node k name in
  if pairs <> [] then
    (match List.assoc_opt "name" pairs with
    | Some v when String.trim v <> "" -> String.trim v
    | _ ->
      let store_pairs = match Hashtbl.find_opt Vidya._shabda_store name with
        | Some p -> p | None -> [] in
      (match List.assoc_opt "desc" store_pairs with
      | Some d when String.trim d <> "" ->
        let trimmed = String.trim d in
        (match String.index_opt trimmed '-' with
        | Some _ -> trimmed
        | None -> trimmed)
      | _ -> Vidya.to_english k name))
  else Vidya.to_english k name

let sahaja_render (k : proof_graph) (name : string) : string =
  let gloss = sahaja_gloss k name in
  if gloss = name then name
  else Printf.sprintf "%s (%s)" gloss name

(* ═══════════════════════════════════════════════════════════════════════════
   4. DARSHANA — node inspection rendering
   ═══════════════════════════════════════════════════════════════════════════ *)

let render_darshana_to_buf (k : proof_graph) (n : nigamana) (buf : Buffer.t) : unit =
  let gloss = sahaja_gloss k n.name in
  Buffer.add_string buf (Printf.sprintf "--- %s (%s) satya=%.4f ---\n" gloss n.name n.satya);
  List.iter (fun s ->
    Buffer.add_string buf (Printf.sprintf "  \"%s\"\n" s)
  ) n.slokas;
  let edges = edges_of k n.name in
  if edges <> [] then begin
    Buffer.add_string buf "  edges:\n";
    List.iter (fun e ->
      let rel_str = string_of_visheshanam e.relation in
      if e.source = n.name then
        Buffer.add_string buf (Printf.sprintf "    -> %s [%s]\n"
          (sahaja_render k e.target) rel_str)
      else
        Buffer.add_string buf (Printf.sprintf "    <- %s [%s]\n"
          (sahaja_render k e.source) rel_str)
    ) edges
  end;
  let cited = in_degree k n.name in
  Buffer.add_string buf (Printf.sprintf "  cited_by: %d\n---" cited)

(* ═══════════════════════════════════════════════════════════════════════════
   5. OUTPUT FLAGS
   ═══════════════════════════════════════════════════════════════════════════ *)

type output_flags = unit

let flags_default : output_flags = ()

let parse_inline_flags ?(base : output_flags = ()) (sentence : string)
    : string * output_flags =
  ignore base;
  let tokens = String.split_on_char ' ' sentence in
  let rest = List.filter (fun t ->
    let t = String.lowercase_ascii (String.trim t) in
    not (String.length t > 0 && t.[0] = '+')
  ) tokens in
  (String.concat " " (List.filter (fun s -> String.length (String.trim s) > 0) rest), ())

let flags_of_show_string ?(base : output_flags = ()) (s : string)
    : output_flags =
  ignore (base, s); ()

(* ═══════════════════════════════════════════════════════════════════════════
   6. STHITI — human-readable graph dump
   ═══════════════════════════════════════════════════════════════════════════ *)

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

(* ═══════════════════════════════════════════════════════════════════════════
   7. PRAVAHA — full graph as JSON
   ═══════════════════════════════════════════════════════════════════════════ *)

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
