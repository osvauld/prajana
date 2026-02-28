(* verify.ml — the gate
   the graph is read-only at runtime. satya is computed at load time.
   darshana returns what the graph holds for a name. *)

type result =
  | Pratibodha of string * float   (* found — name and satya *)
  | Asprishta  of string           (* not found *)

let f_K (k : Proof_graph.proof_graph) (event : Event.t)
    : Proof_graph.proof_graph * result option =
  match event with
  | Event.Sthiti -> (k, None)
  | Event.Pravaha -> (k, None)
  | Event.Visarjana -> (k, None)
  | Event.Anuvada a ->
    let max_passes = match a.max_passes with
      | Some n -> n
      | None -> 5 in
    (match a.thaalam with
    | Some t -> Proof_graph.anuvada ~max_passes ~thaalam:t k a.sentence
    | None -> Proof_graph.anuvada ~max_passes k a.sentence);
    (k, None)
  | Event.Darshana d ->
    (match Proof_graph.find k d.name with
    | None -> (k, Some (Asprishta d.name))
    | Some n ->
      (* print the node detail *)
      Printf.printf "--- %s (satya=%.4f) ---\n" n.name n.satya;
      List.iter (fun s -> Printf.printf "  \"%s\"\n" s) n.slokas;
      let edges = Proof_graph.edges_of k n.name in
      if edges <> [] then begin
        Printf.printf "  edges:\n";
        List.iter (fun e ->
          let dir = if e.Proof_graph.source = n.name
            then Printf.sprintf "-> %s" e.target
            else Printf.sprintf "<- %s" e.source
          in
          Printf.printf "    %s (%s)\n" dir
            (Proof_graph.string_of_visheshanam e.relation)
        ) edges
      end;
      let cited = Proof_graph.in_degree k n.name in
      Printf.printf "  cited_by: %d\n---\n%!" cited;
      (k, Some (Pratibodha (n.name, n.satya))))
