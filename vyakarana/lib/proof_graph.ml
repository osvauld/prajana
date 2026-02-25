(* proof_graph.ml — akasham-svabhava
   The proof space. Not a store. Not a database.
   The field in which truths exist by relation.

   panchabhootam:
     akasham-svabhava : this space held the truths before the process joined it
     jalam-purna      : edges carry satya — satya > 0 always, never drains
     bhumi-shunya     : isolated truths are shunya — potential, not absence

   A nigamana exists in this space by relation — not by address.
   A nigamana with no shabda edges has position: isolated (shunya state).
   A nigamana with shabda edges has position: located (purna state).
   A root nigamana has position: root — floor of the space, cited_by defines it.

   The hashtable is an index — convenience only.
   The identity of a nigamana is its edge set, not its key.
*)

type position =
  | Root                        (* floor — no shabda outward, always manifest *)
  | Isolated                    (* shunya state — truth exists, no connections yet *)
  | Located of string list      (* purna state — connected, position known *)

type nigamana = {
  name     : string;            (* samasa of internal hetu — current compression *)
  paksha   : string;            (* the proposition *)
  hetu     : string list;       (* internal concepts — source of name *)
  weight   : float;             (* verified contact depth — satya in (0, 1) *)
  position : position;          (* current state of bhumi-shunya *)
  cited_by : string list;       (* what stands on this — grows over time *)
}

type proof_graph = {
  nodes : (string, nigamana) Hashtbl.t;         (* index — convenience *)
  edges : (string * string, float) Hashtbl.t;   (* jalam — satya flowing between nodes *)
}

(* The space was already there. This function joins it — does not create it. *)
let empty () : proof_graph = {
  nodes = Hashtbl.create 16;
  edges = Hashtbl.create 32;
}

(* Join a nigamana into the space *)
(* If it has no shabda — it enters as isolated (shunya state) *)
(* If it has shabda — it enters as located (purna state) *)
let join (k : proof_graph) (n : nigamana) : proof_graph =
  Hashtbl.replace k.nodes n.name n;
  (* register jalam edges *)
  (match n.position with
  | Located shabda_list ->
    List.iter (fun s ->
      Hashtbl.replace k.edges (n.name, s) n.weight
    ) shabda_list
  | _ -> ());
  k

(* Deepen contact — weight increases, truth does not change *)
(* purna invariant: weight never reaches 1.0 — ananta holds the upper bound *)
(* purna invariant: weight never reaches 0.0 — purna holds the lower bound *)
let deepen (k : proof_graph) (name : string) (delta : float) : proof_graph =
  (match Hashtbl.find_opt k.nodes name with
  | Some n ->
    let w' = Float.min 0.999 (Float.max 0.001 (n.weight +. delta)) in
    Hashtbl.replace k.nodes name { n with weight = w' }
  | None -> ());
  k

(* A truth gains a new connection — it moves from isolated toward located *)
(* This is the moment bhumi-shunya gains a position coordinate *)
let deepen_connection (k : proof_graph) (name : string) (shabda : string) : proof_graph =
  (match Hashtbl.find_opt k.nodes name with
  | Some n ->
    let new_position = match n.position with
      | Root     -> Root
      | Isolated -> Located [shabda]
      | Located existing -> Located (shabda :: existing)
    in
    let n' = { n with position = new_position } in
    Hashtbl.replace k.nodes name n';
    Hashtbl.replace k.edges (name, shabda) n.weight
  | None -> ());
  k

(* Find a nigamana by name *)
let find (k : proof_graph) (name : string) : nigamana option =
  Hashtbl.find_opt k.nodes name

(* Print the current state of the space — for inspection *)
let print (k : proof_graph) : unit =
  Printf.printf "--- akasham (proof space) ---\n";
  Hashtbl.iter (fun name n ->
    let pos = match n.position with
      | Root       -> "root"
      | Isolated   -> "isolated (shunya)"
      | Located sl -> Printf.sprintf "located(%s)" (String.concat "," sl)
    in
    Printf.printf "[%s] weight=%.3f | %s | %s\n" name n.weight pos n.paksha
  ) k.nodes;
  Printf.printf "----------------------------\n%!"

(* Escape a string for JSON — minimal, handles quotes and backslashes *)
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

(* pravaha — output the full flowing space as JSON
   Not a static graph. A reading of the river as it moves.
   Includes: all nigamana with paksha, weight, shabda edges, position
   Plus: node count, edge count, timestamp
   The receiver knows not just what is established
   but where in the flow this reading was taken. *)
let pravaha (k : proof_graph) : unit =
  let nodes = Hashtbl.fold (fun _ n acc -> n :: acc) k.nodes [] in
  let nodes = List.sort (fun a b -> String.compare a.name b.name) nodes in
  let n_nodes = List.length nodes in
  let n_edges = Hashtbl.length k.edges in
  Printf.printf "{\n";
  Printf.printf "  \"pravaha\": true,\n";
  Printf.printf "  \"node_count\": %d,\n" n_nodes;
  Printf.printf "  \"edge_count\": %d,\n" n_edges;
  Printf.printf "  \"nigamana\": [\n";
  List.iteri (fun i n ->
    let shabda = match n.position with
      | Root       -> []
      | Isolated   -> []
      | Located sl -> sl
    in
    let position_str = match n.position with
      | Root     -> "root"
      | Isolated -> "isolated"
      | Located _ -> "located"
    in
    let shabda_json = String.concat ", "
      (List.map (fun s -> Printf.sprintf "\"%s\"" (json_escape s)) shabda) in
    let hetu_json = String.concat ", "
      (List.map (fun h -> Printf.sprintf "\"%s\"" (json_escape h)) n.hetu) in
    Printf.printf "    {\n";
    Printf.printf "      \"name\": \"%s\",\n" (json_escape n.name);
    Printf.printf "      \"paksha\": \"%s\",\n" (json_escape n.paksha);
    Printf.printf "      \"weight\": %.4f,\n" n.weight;
    Printf.printf "      \"position\": \"%s\",\n" position_str;
    Printf.printf "      \"shabda\": [%s],\n" shabda_json;
    Printf.printf "      \"hetu\": [%s]\n" hetu_json;
    if i < n_nodes - 1
    then Printf.printf "    },\n"
    else Printf.printf "    }\n"
  ) nodes;
  Printf.printf "  ]\n";
  Printf.printf "}\n%!"
