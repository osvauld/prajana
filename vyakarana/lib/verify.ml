(* verify.ml — the gate
   the graph is read-only at runtime. satya is computed at load time.
   darshana returns what the graph holds for a name. *)

type result =
  | Pratibodha of string * float   (* found — name and satya *)
  | Asprishta  of string           (* not found *)

let f_K ?(flags = Anuvada.flags_default) (k : Proof_graph.proof_graph) (event : Event.t)
    : Proof_graph.proof_graph * result option =
  match event with
  | Event.Sthiti -> (k, None)
  | Event.Pravaha -> (k, None)
  | Event.Visarjana -> (k, None)
  | Event.Prayoga _ -> (k, None)  (* handled directly in main loop *)
  | Event.Yantra _ -> (k, None)   (* handled directly in main loop *)
  | Event.Anuvada a ->
    let max_passes = match a.max_passes with
      | Some n -> n
      | None -> 2 in
    (match a.thaalam with
    | Some t -> Anuvada.anuvada ~max_passes ~thaalam:t ~sahaja:a.sahaja ~flags k a.sentence
    | None -> Anuvada.anuvada ~max_passes ~sahaja:a.sahaja ~flags k a.sentence);
    (k, None)
  | Event.Darshana d ->
    (* resolve name — try direct lookup first, then classify_token for English aliases
       so that "life" → jiva, "story" → katha, etc. work as single-word queries *)
    let rname =
      match Proof_graph.find k d.name with
      | Some _ -> d.name
      | None ->
        (match Setu.classify_token k d.name with
         | Setu.Content name when name <> d.name -> name
         | _ -> d.name)
    in
    (match Proof_graph.find k rname with
    | None -> (k, Some (Asprishta d.name))
    | Some n ->
      if d.sahaja then begin
        let gloss = Anuvada.sahaja_gloss k n.name in
        Printf.printf "--- %s (%s) satya=%.4f ---\n" gloss n.name n.satya
      end else
        Printf.printf "--- %s (satya=%.4f) ---\n" n.name n.satya;
      List.iter (fun s -> Printf.printf "  \"%s\"\n" s) n.slokas;
      let edges = Proof_graph.edges_of k n.name in
      if edges <> [] then begin
        Printf.printf "  edges:\n";
        List.iter (fun e ->
          let rel_str = Proof_graph.string_of_visheshanam e.Proof_graph.relation in
          if e.Proof_graph.source = n.name then begin
            if d.sahaja then
              Printf.printf "    -> %s [%s]\n"
                (Anuvada.sahaja_render k e.target) rel_str
            else
              Printf.printf "    -> %s (%s)\n" e.target rel_str
          end else begin
            if d.sahaja then
              Printf.printf "    <- %s [%s]\n"
                (Anuvada.sahaja_render k e.source) rel_str
            else
              Printf.printf "    <- %s (%s)\n" e.source rel_str
          end
        ) edges
      end;
      let cited = Proof_graph.in_degree k n.name in
      Printf.printf "  cited_by: %d\n---\n%!" cited;
      (k, Some (Pratibodha (n.name, n.satya))))
