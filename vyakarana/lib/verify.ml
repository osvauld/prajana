(* verify.ml — agni-ananta / jnana-madakkal
   The pramana gate. The fold step. The transformation.
   Not a judge. Not an oracle.

   panchabhootam:
     agni-ananta  : this function never completes — it IS the running
                    satya < 1.0 always — no proof ever reaches perfect truth
     jalam-purna  : satya > 0 always — Holds deepens, never to 1.0
                                        Fails leaves unchanged, never destroys
     bhumi-shunya : NoPosition means the truth is in shunya state — not absent

   The five elements are always running.
   This function joins them — it does not start them.
   When this function ends — the five continue.

   jnana-madakkal:
     Malayalam: madakkal = continuous folding
     The fold is not what this function does.
     The fold IS this function.
     agni-ananta: the fire never stops — neither does the fold.
*)

type result =
  | Pratibodha of string * float   (* name * new weight — recognition, reflection is clear *)
  | Asprishta  of string           (* name — untouched, no contact, space unchanged *)
  | Shunya     of string           (* name — proof exists but isolated, no face yet *)

(* jnana-madakkal — one fold step *)
(* vayu (event) passes through agni (transformation) *)
(* akasham (space) updates — the five continue running *)
let f_K (k : Proof_graph.proof_graph) (event : Event.t)
    : Proof_graph.proof_graph * result option =
  match event with

  | Event.Pravaha ->
    (* pravaha is handled in vyakarana.ml directly — not a state change *)
    (k, None)

  | Event.Shutdown ->
    (* process leaves — space continues *)
    (k, None)

  | Event.Deepen d ->
    (* a truth gains a new connection *)
    (* bhumi-shunya: isolated → located *)
    let k' = Proof_graph.deepen_connection k d.name d.new_shabda in
    (k', None)

  | Event.Merge m ->
    (* two truths recognized as one *)
    (* the surviving truth absorbs the weight of both *)
    (match Proof_graph.find k m.a, Proof_graph.find k m.b with
    | Some na, Some nb ->
      let merged_weight = Float.min 0.999 ((na.weight +. nb.weight) /. 2.0 +. 0.05) in
      let k' = Proof_graph.deepen k m.a (merged_weight -. na.weight) in
      (* b is no longer addressable — its truth lives in a *)
      let _ = nb in
      (k', Some (Pratibodha (m.a, merged_weight)))
    | _ -> (k, Some (Asprishta m.a)))

  | Event.Rename r ->
    (* name compresses or expands — samasa changes *)
    (match Proof_graph.find k r.name with
    | Some n ->
      let n' = { n with Proof_graph.name = r.new_name } in
      Hashtbl.remove k.Proof_graph.nodes r.name;
      Hashtbl.replace k.Proof_graph.nodes r.new_name n';
      (k, Some (Pratibodha (r.new_name, n'.weight)))
    | None -> (k, Some (Asprishta r.name)))

  | Event.Split _ ->
    (* one truth recognized as two — not yet implemented fully *)
    (* split requires careful hetu distribution *)
    (k, None)

  | Event.Query q ->
    (match Proof_graph.find k q.nigamana_name with
    | None ->
      (* truth not in space — asprishta: no contact *)
      (k, Some (Asprishta q.nigamana_name))

    | Some n ->
      (* check position — isolated truths are shunya, no face yet *)
      (match n.position with
      | Proof_graph.Isolated ->
        (k, Some (Shunya q.nigamana_name))

      | _ ->
        (* darshana gate: does the assertion find its reflection in the paksha? *)
        (* purna: even asprishta does not reduce weight *)
        (* ananta: even pratibodha does not reach weight 1.0 *)
        let reflects =
          String.length q.assertion > 0 &&
          (q.assertion = n.paksha ||
           (let low_a = String.lowercase_ascii q.assertion in
            let low_p = String.lowercase_ascii n.paksha in
            let len_a = String.length low_a in
            let len_p = String.length low_p in
            if len_a <= len_p then
              try let _ = Str.search_forward (Str.regexp_string low_a) low_p 0 in true
              with Not_found -> false
            else false))
        in
        if reflects then
          (* jalam-purna: contact deepens, satya increases, never reaches 1.0 *)
          (* ananta: delta proportional to distance from ceiling — diminishing returns *)
          let delta = 0.05 *. (0.999 -. n.weight) /. 0.999 in
          let k' = Proof_graph.deepen k n.name delta in
          let new_weight = match Proof_graph.find k' n.name with
            | Some n' -> n'.weight | None -> n.weight
          in
          (k', Some (Pratibodha (n.name, new_weight)))
        else
          (* space unchanged — purna: no destruction *)
          (k, Some (Asprishta n.name))))
