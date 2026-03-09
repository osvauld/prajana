(* prayoga.ml — execution on the proof graph
   the graph knows. the code only walks and composes.

   all domain knowledge lives in .om files:
     swara-to-strudel   — swara names → Strudel pitch letters
     ornament-to-strudel — ornament concepts → Strudel syntax magnitudes
     strudel             — synth names, rhythm patterns
     codon-table         — 64 codon → amino-acid mappings
     transcription       — T→U substitution rule

   prayoga reads shabda fields from these nodes.
   no tables. no literal strings. the graph generates from its own knowledge. *)

open Proof_graph

(* --- context --- *)

type prayoga_context = {
  instruction  : string;
  input        : string;
  seeds        : string list;
  recognised   : nigamana list;
  ocaml_forms  : (string * string) list;
  walk_path    : string list;
  domain       : string;
}

(* --- strudel delegated --- *)
let compose_music (k : proof_graph) seeds walk input =
  Prayoga_strudel.compose_music k seeds walk input


(* --- compose_biology: read codon table and transcription rule from graph --- *)

let compose_biology (k : proof_graph) seeds walk input =
  let has n = List.mem n seeds || List.mem n walk in
  (* all labels and sentinels come from the graph *)
  let setu = Setu.read_shabda k "biology-setu" in
  let get key fallback = match Setu.shabda_get setu key with Some v -> v | None -> fallback in

  Printf.printf "%s\n" (get "header-sequence" "");
  Printf.printf "%s\n" (get "header-bridge" "");
  if has "transcription" || has "dna" then
    Printf.printf "%s\n" (get "header-transcription" "");
  if has "translation" || has "codon-table" then
    Printf.printf "%s\n" (get "header-translation" "");
  if has "folding" then
    Printf.printf "%s\n" (get "header-folding" "");
  Printf.printf "\n";

  (* codon table from graph — codon-table.om shabda *)
  let codons = Setu.read_shabda k "codon-table" in

  Printf.printf "let codon_table = [\n";
  List.iter (fun (codon, aa) ->
    Printf.printf "  \"%s\", \"%s\";\n" codon aa
  ) codons;
  Printf.printf "]\n\n";

  (* transcription rule from graph — transcription.om shabda: T:U *)
  let trans_rule = Setu.read_shabda k "transcription" in

  Printf.printf "%s\n" (get "header-transcription" "");
  Printf.printf "let transcribe dna =\n";
  Printf.printf "  String.map (function\n";
  List.iter (fun (from, too) ->
    Printf.printf "    | '%s' -> '%s'\n" from too
  ) trans_rule;
  Printf.printf "    | c -> c) (String.uppercase_ascii dna)\n\n";

  (* sentinel values from graph *)
  let start_codon   = get "start-codon"    "AUG" in
  let stop_sentinel = get "stop-sentinel"  "Stop" in
  let no_start      = get "no-start-codon" "no-start-codon" in
  let unknown_codon = get "unknown-codon"  "[?]" in

  Printf.printf "%s\n" (get "header-translation" "");
  Printf.printf "let translate rna =\n";
  Printf.printf "  let n = String.length rna in\n";
  Printf.printf "  let result = Buffer.create 64 in\n";
  Printf.printf "  let start = ref (-1) in\n";
  Printf.printf "  for i = 0 to n - 3 do\n";
  Printf.printf "    if !start = -1 && String.sub rna i 3 = \"%s\" then start := i\n" start_codon;
  Printf.printf "  done;\n";
  Printf.printf "  if !start = -1 then \"%s\"\n" no_start;
  Printf.printf "  else begin\n";
  Printf.printf "    let i = ref !start in\n";
  Printf.printf "    let running = ref true in\n";
  Printf.printf "    while !running && !i + 3 <= n do\n";
  Printf.printf "      let codon = String.sub rna !i 3 in\n";
  Printf.printf "      (match List.assoc_opt codon codon_table with\n";
  Printf.printf "      | Some \"%s\" -> running := false\n" stop_sentinel;
  Printf.printf "      | Some aa ->\n";
  Printf.printf "        if Buffer.length result > 0 then Buffer.add_char result '-';\n";
  Printf.printf "        Buffer.add_string result aa\n";
  Printf.printf "      | None -> Buffer.add_string result \"%s\");\n" unknown_codon;
  Printf.printf "      i := !i + 3\n";
  Printf.printf "    done;\n";
  Printf.printf "    Buffer.contents result\n";
  Printf.printf "  end\n\n";

  if has "folding" then
    Printf.printf "%s\n\n" (get "header-folding" "");

  if String.length input > 0 then begin
    Printf.printf "let () =\n";
    Printf.printf "  let dna = \"%s\" in\n" (String.uppercase_ascii input);
    Printf.printf "  let rna = transcribe dna in\n";
    Printf.printf "  Printf.printf \"dna:  %%s\\n\" dna;\n";
    Printf.printf "  Printf.printf \"rna:  %%s\\n\" rna;\n";
    Printf.printf "  Printf.printf \"protein: %%s\\n\" (translate rna)\n"
  end

(* --- compose_from_setu: relation-driven generic emitter ---

   walks each seed concept through the proof graph.
   for each concept and its related nodes, looks up the Lua form
   in the setu node shabda.
   relation type determines composition role:
     swarupa    -> type/declaration context
     kriya      -> action/function body
     sthita     -> dependency/field (stands on)
     phala      -> result/return
     yukta      -> argument/connected parameter
     abheda     -> same-as / alias
     janya      -> born-from / origin

   no hardcoded code. the graph structure IS the grammar.
*)

let form_of (setu_map : (string * string) list) (concept : string) : string option =
  (* try exact key, then strip domain prefix *)
  match List.assoc_opt concept setu_map with
  | Some f -> Some f
  | None ->
    (* try without domain- prefix *)
    let stripped = if String.length concept > 7 && String.sub concept 0 7 = "domain-"
      then String.sub concept 7 (String.length concept - 7)
      else concept in
    List.assoc_opt stripped setu_map

let relation_role (r : visheshanam) : string =
  if r = swarupa then "is"
  else if r = kriya then "does"
  else if r = sthita then "on"
  else if r = phala then "produces"
  else if r = yukta then "with"
  else if r = abheda then "="
  else if r = drishthanta then "eg"
  else if r = siddha then "via"
  else if r = janya then "from"
  else if r = pratipaksha then "inverts"
  else string_of_visheshanam r

let dedupe lst =
  List.fold_left (fun acc x ->
    if List.mem x acc then acc else acc @ [x]
  ) [] lst


let compose_from_setu (k : proof_graph) (setu_node : string) (_seeds : string list) (walk : string list) (input : string) : unit =
  let setu_map = Setu.read_shabda k setu_node in
  let comment     = match List.assoc_opt "comment"     setu_map with Some c -> c | None -> "--" in
  let comment_end = match List.assoc_opt "comment-end" setu_map with Some c -> c | None -> "" in

  (* concepts to walk = input tokens + walk path, deduped *)
  let input_tokens = if String.length input > 0
    then String.split_on_char ' ' (String.trim input)
    else [] in
  let concepts = dedupe (input_tokens @ walk) in

  (* for each concept, find its graph node and emit relation-annotated forms *)
  let emitted = ref false in
  List.iter (fun concept ->
    match Proof_graph.find k concept with
    | None -> ()
    | Some n ->
      emitted := true;
      let self_form = form_of setu_map n.name in
      (match self_form with
      | Some f ->
        Printf.printf "%s [%s] %s%s\n" comment n.name f comment_end
      | None ->
        Printf.printf "%s [%s]%s\n" comment n.name comment_end);
      (* walk outgoing edges — emit relation role + target form *)
      List.iter (fun (e : typed_edge) ->
        if e.source = n.name then begin
          match form_of setu_map e.target with
          | Some target_form ->
            Printf.printf "  %s %s -> %s\n" (relation_role e.relation) e.target target_form
          | None -> ()
        end
      ) n.edges;
      Printf.printf "\n"
  ) concepts;
  if not !emitted then
    Printf.printf "%s no known concepts found in input%s\n" comment comment_end

(* --- main entry --- *)

let run ?(emit_meta = true) (k : proof_graph) ~(instruction : string) ~(input : string) ~(domain_hint : string option) : unit =
  let tokens = Setu.tokenise instruction in
  let all_candidates = tokens @ Setu.bigrams tokens in

  let recognised = List.filter_map (find k) all_candidates in
  let seeds = tokens in

  let walk_path = List.rev (List.fold_left (fun acc n ->
    Setu.walk_chain k n.name 3 acc
  ) [] recognised) in

  let domain = match domain_hint with
    | Some d -> d
    | None -> Setu.detect_domain k seeds
  in

  (* resolve setu node for this domain — used for comment markers + generic emit *)
  let setu_node_name = domain ^ "-setu" in
  let setu_map = Setu.read_shabda k setu_node_name in
  (* if setu node exists, use its comment markers; else fall back by domain *)
  let has_setu = find k setu_node_name <> None in
  let c  = match List.assoc_opt "comment"     setu_map with Some v -> v
           | None -> if has_setu then "--"
                     else if domain = "music" || domain = "sangeetham" then "//" else "(*" in
  let ce = match List.assoc_opt "comment-end" setu_map with Some v -> v
           | None -> if has_setu then ""
                     else if domain = "music" || domain = "sangeetham" then "" else " *)" in

  let ocaml_forms = match domain with
    | "biology" -> Setu.resolve_ocaml_forms k seeds
    | _ -> [] in

  let ctx = { instruction; input; seeds; recognised; ocaml_forms; walk_path; domain } in

  if emit_meta then begin
    Printf.printf "%s prayoga%s\n" c ce;
    Printf.printf "%s instruction: %s%s\n" c ctx.instruction ce;
    if String.length ctx.input > 0 then
      Printf.printf "%s input: %s%s\n" c ctx.input ce;
    if ctx.ocaml_forms <> [] then
      Printf.printf "%s setu resolved: %s%s\n" c
        (String.concat ", " (List.map (fun (s, cv) -> s ^ " -> " ^ cv) ctx.ocaml_forms)) ce;
    Printf.printf "\n"
  end;

  (match domain with
  | "biology"     -> compose_biology k ctx.seeds ctx.walk_path ctx.input
  | "music" | "sangeetham" -> compose_music k ctx.seeds ctx.walk_path ctx.input
  | _ ->
    (* generic: try <domain>-setu node *)
    (match find k setu_node_name with
    | Some _ ->
      compose_from_setu k setu_node_name ctx.seeds ctx.walk_path ctx.input
    | None ->
      Printf.printf "%s domain: %s — no setu node found%s\n" c domain ce;
      Printf.printf "%s walk: %s%s\n" c (String.concat " -> " ctx.walk_path) ce));

  Printf.printf "%!"
