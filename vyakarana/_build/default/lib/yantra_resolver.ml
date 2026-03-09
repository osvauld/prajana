(* yantra_resolver.ml — tantra resolution strategies.
   given a set of known bindings and a target concept, finds a resolution:
   Direct (tantra whose output = target, all inputs satisfied),
   Inverse (tantra whose input = target, output known, others satisfied),
   Chain (multi-hop BFS across multiple tantras), or
   NotFound (with a diagnostic reason).

   symbolic inversion is delegated to Yantra_inverter.
   bigram/token types live in Yantra_bigram.

   dependency: Proof_graph, Yantra_types, Yantra_bigram, Yantra_inverter, Setu. *)

open Proof_graph
open Yantra_types
open Yantra_inverter

(* ---- resolution types ---- *)

type chain_step =
  | CForward of tantra * (string * float) list
  | CInverse of tantra * string * (string * expr) list * (string * float) list

type resolution =
  | Direct  of tantra * (string * float) list
  | Inverse of tantra * string * (string * expr) list * (string * float) list
  | Chain   of chain_step list
  | NotFound of string

(* ---- input matching ---- *)

(* check if all tantra inputs can be satisfied by the bindings.
   uses canonical names resolved at parse time; no graph walks needed here. *)
let try_match_inputs (_k : proof_graph) (tantra : tantra) (bindings : binding list)
    (idx : tantra_index) : (string * float) list option =
  let find_binding (inp : tantra_param) : float option =
    match List.find_opt (fun b ->
      b.b_name = inp.tp_name || b.b_name = inp.tp_canonical
    ) bindings with
    | Some b -> Some b.b_value
    | None ->
      (* partial compound match: "velocity" matches input "initial-velocity" *)
      let parts = String.split_on_char '-' inp.tp_name in
      let canon_parts = String.split_on_char '-' inp.tp_canonical in
      match List.find_opt (fun b ->
        not (String.contains b.b_name '-') &&
        (List.mem b.b_name parts || List.mem b.b_name canon_parts)
      ) bindings with
      | Some b -> Some b.b_value
      | None ->
        Hashtbl.find_opt idx.constants inp.tp_name
  in
  let find_binding_positional (i : int) (inp : tantra_param) : float option =
    match find_binding inp with
    | Some _ as hit -> hit
    | None ->
      let argname = Printf.sprintf "arg%d" i in
      match List.find_opt (fun b -> b.b_name = argname) bindings with
      | Some b -> Some b.b_value
      | None -> None
  in
  let assignments = List.mapi (fun i inp ->
    match find_binding_positional i inp with
    | Some v -> Some (inp.tp_name, v)
    | None -> None
  ) tantra.t_inputs in
  let assignments = List.filter_map Fun.id assignments in
  if List.length assignments = List.length tantra.t_inputs then
    Some assignments
  else None

(* ---- forward references (wired at module init in yantra_eval.ml) ---- *)

let _eval_chain_ref : (proof_graph -> env -> expr -> value) ref =
  ref (fun _ _ _ -> VNone)
let _eval_tantra_chain_ref : (proof_graph -> tantra -> (string * value) list -> value) ref =
  ref (fun _ _ _ -> VNone)

(* ---- resolve_tantra: top-level resolution strategy ---- *)

let rec resolve_tantra (k : proof_graph) (idx : tantra_index) (bindings : binding list)
    (target : string) : resolution =
  (* flexible name matching: exact, component, or canonical *)
  let names_match (a : string) (b : string) : bool =
    a = b ||
    let ap = String.split_on_char '-' a in
    let bp = String.split_on_char '-' b in
    List.exists (fun p -> String.length p > 2 && List.mem p bp) ap ||
    List.exists (fun p -> String.length p > 2 && List.mem p ap) bp ||
    let ca = Setu.resolve_to_canonical k a in
    let cb = Setu.resolve_to_canonical k b in
    ca = cb || ca = b || a = cb
  in

  (* 1. DIRECT — tantra name or output name matches target, inputs satisfied *)
  let try_direct () =
    let candidates =
      (match Hashtbl.find_opt idx.by_name target with Some t -> [t] | None -> []) @
      (match Hashtbl.find_opt idx.by_output target with Some l -> l | None -> [])
    in
    List.find_map (fun t ->
      match try_match_inputs k t bindings idx with
      | Some assignments -> Some (Direct (t, assignments))
      | None -> None
    ) candidates
  in

  (* 2. INVERSE — target is an INPUT of a tantra whose OUTPUT we have *)
  let try_inverse () =
    let inverse_candidates =
      match Hashtbl.find_opt idx.by_input target with
      | Some l when l <> [] -> l
      | _ ->
        List.filter (fun t ->
          List.exists (fun inp ->
            names_match inp.tp_name target || names_match inp.tp_canonical target
          ) t.t_inputs
        ) !(idx.all_tantras)
    in
    List.find_map (fun t ->
      let target_inp = List.find_opt (fun inp ->
        inp.tp_name = target || inp.tp_canonical = target ||
        names_match inp.tp_name target || names_match inp.tp_canonical target
      ) t.t_inputs in
      match target_inp with
      | None -> None
      | Some target_inp ->
        let target_inp_name = target_inp.tp_name in
        let output_bound = List.find_map (fun ret ->
          List.find_map (fun b ->
            if b.b_name = ret.tp_name || b.b_name = t.t_name
               || names_match b.b_name ret.tp_name
               || names_match b.b_name t.t_name
               || (match ret.tp_unit with
                   | Some unit_name ->
                     let yuktas = Setu.yukta_of k b.b_name in
                     List.mem unit_name yuktas ||
                     (String.length b.b_name >= String.length unit_name &&
                      String.sub b.b_name 0 (String.length unit_name) = unit_name)
                   | None -> false)
            then Some (ret.tp_name, b.b_value)
            else None
          ) bindings
        ) t.t_returns in
        match output_bound with
        | None -> None
        | Some (result_name, result_value) ->
          let other_inputs = List.filter (fun inp ->
            inp.tp_name <> target_inp_name) t.t_inputs in
          let other_values = List.filter_map (fun inp ->
            match List.find_opt (fun b -> names_match b.b_name inp.tp_name) bindings with
            | Some b -> Some (inp.tp_name, b.b_value)
            | None -> Hashtbl.find_opt idx.constants inp.tp_name
                      |> Option.map (fun v -> (inp.tp_name, v))
          ) other_inputs in
          if List.length other_values <> List.length other_inputs then None
          else begin
            let known_values = (result_name, result_value) :: other_values in
            let ret_binding_name = match List.find_opt (fun (name, _) ->
              name = result_name ||
              List.exists (fun ret -> ret.tp_name = name) t.t_returns
            ) t.t_lets with
            | Some (name, _) -> name | None -> result_name in
            let known_names = List.map fst known_values in
            let known_with_inputs = known_names @
              List.map (fun inp -> inp.tp_name) other_inputs in
            match invert_chain k t.t_lets known_with_inputs
                    target_inp_name ret_binding_name with
            | Some plan -> Some (Inverse (t, target, plan, known_values))
            | None -> None
          end
    ) inverse_candidates
  in

  (* 3. GRAPH — target resolves to a known output via abheda *)
  let try_graph () =
    let resolved = Setu.resolve k target in
    let candidates = List.concat_map (fun name ->
      match Hashtbl.find_opt idx.by_output name with Some l -> l | None -> []
    ) resolved in
    List.find_map (fun t ->
      match try_match_inputs k t bindings idx with
      | Some assignments -> Some (Direct (t, assignments))
      | None -> None
    ) candidates
  in

  (* 4. CHAIN — BFS through multiple tantras *)
  let try_chain () =
    match chain_resolve ~max_depth:4 k idx bindings target with
    | Some steps -> Some (Chain steps)
    | None -> None
  in

  let not_found_reason () =
    let direct_candidates =
      (match Hashtbl.find_opt idx.by_name target with Some t -> [t] | None -> []) @
      (match Hashtbl.find_opt idx.by_output target with Some l -> l | None -> [])
    in
    let graph_candidates =
      let resolved = Setu.resolve k target in
      List.concat_map (fun name ->
        match Hashtbl.find_opt idx.by_output name with Some l -> l | None -> []
      ) resolved
    in
    let all_candidates =
      let seen = Hashtbl.create 16 in
      List.filter (fun t ->
        if Hashtbl.mem seen t.t_name then false
        else (Hashtbl.replace seen t.t_name true; true)
      ) (direct_candidates @ graph_candidates)
    in
    let missing_for (t : tantra) =
      List.filter_map (fun inp ->
        let has_binding = List.exists (fun b ->
          names_match b.b_name inp.tp_name || names_match b.b_name inp.tp_canonical
        ) bindings in
        let has_const = Hashtbl.mem idx.constants inp.tp_name in
        if has_binding || has_const then None else Some inp.tp_name
      ) t.t_inputs
      |> List.sort_uniq String.compare
    in
    match all_candidates with
    | [] -> Printf.sprintf "no tantra found for target '%s'" target
    | _ ->
      let ranked = List.map (fun t -> (t, missing_for t)) all_candidates in
      let ranked = List.sort (fun (_, m1) (_, m2) -> compare (List.length m1) (List.length m2)) ranked in
      (match ranked with
       | (t, []) :: _ ->
         Printf.sprintf "tantra '%s' exists but could not be resolved from current bindings" t.t_name
       | (t, missing) :: _ ->
         Printf.sprintf "tantra '%s' exists but missing inputs: %s"
           t.t_name (String.concat ", " missing)
       | [] -> Printf.sprintf "no tantra found for target '%s'" target)
  in

  match try_direct () with
  | Some r -> r
  | None ->
    match try_inverse () with
    | Some r -> r
    | None ->
      match try_graph () with
      | Some r -> r
      | None ->
        match try_chain () with
        | Some r -> r
        | None -> NotFound (not_found_reason ())

(* ---- chain_resolve: BFS across multiple tantras ---- *)

and names_match_fast (a : string) (b : string) : bool = a = b

and names_match_resolved (k : proof_graph) (a : string) (b : string) : bool =
  names_match_fast a b ||
  let ca = Setu.resolve_to_canonical k a in
  let cb = Setu.resolve_to_canonical k b in
  ca = cb || ca = b || a = cb

(* chain input matching — exact on canonical names only *)
and try_match_chain (_k : proof_graph) (t : tantra) (known : binding list) (idx : tantra_index)
    : (string * float) list option =
  let find_binding (inp : tantra_param) : float option =
    match List.find_opt (fun b ->
      b.b_name = inp.tp_name || b.b_name = inp.tp_canonical
    ) known with
    | Some b -> Some b.b_value
    | None -> Hashtbl.find_opt idx.constants inp.tp_name
  in
  let assignments = List.map (fun inp ->
    match find_binding inp with
    | Some v -> Some (inp.tp_name, v)
    | None -> None
  ) t.t_inputs in
  let assignments = List.filter_map Fun.id assignments in
  if List.length assignments = List.length t.t_inputs then Some assignments
  else None

and tantras_producing (idx : tantra_index) (name : string) : tantra list =
  let by_out = match Hashtbl.find_opt idx.by_output name with Some l -> l | None -> [] in
  let by_name = match Hashtbl.find_opt idx.by_name name with Some t -> [t] | None -> [] in
  let combined = by_out @ by_name in
  if combined <> [] then combined
  else
    List.filter (fun t ->
      t.t_name = name ||
      List.exists (fun ret ->
        names_match_fast ret.tp_name name || names_match_fast ret.tp_canonical name
      ) t.t_returns
    ) !(idx.all_tantras)

and tantras_consuming (idx : tantra_index) (name : string) : tantra list =
  let by_inp = match Hashtbl.find_opt idx.by_input name with Some l -> l | None -> [] in
  let by_out = match Hashtbl.find_opt idx.by_output name with Some l -> l | None -> [] in
  let by_name = match Hashtbl.find_opt idx.by_name name with Some t -> [t] | None -> [] in
  let combined = by_inp @ by_out @ by_name in
  if combined <> [] then combined
  else
    List.filter (fun t ->
      t.t_name = name ||
      List.exists (fun inp ->
        names_match_fast inp.tp_name name || names_match_fast inp.tp_canonical name
      ) t.t_inputs ||
      List.exists (fun ret ->
        names_match_fast ret.tp_name name || names_match_fast ret.tp_canonical name
      ) t.t_returns
    ) !(idx.all_tantras)

and chain_resolve ?(max_depth = 4) ?(beam_width = 8) (k : proof_graph) (idx : tantra_index)
    (bindings : binding list) (target : string) : chain_step list option =
  let known_names = List.map (fun b -> b.b_name) bindings in
  let known_names_expanded = List.concat_map (fun name ->
    let canon = Setu.resolve_to_canonical k name in
    if canon <> name then [name; canon] else [name]
  ) known_names in
  let candidate_tantras =
    let from_target = tantras_producing idx target in
    let from_knowns = List.concat_map (fun name -> tantras_consuming idx name) known_names_expanded in
    let target_inputs = List.concat_map (fun t ->
      List.concat_map (fun inp ->
        if inp.tp_canonical <> inp.tp_name
        then [inp.tp_name; inp.tp_canonical]
        else [inp.tp_name]
      ) t.t_inputs
    ) from_target in
    let bridge = List.concat_map (fun name -> tantras_producing idx name) target_inputs in
    let seen = Hashtbl.create 16 in
    List.filter (fun t ->
      if Hashtbl.mem seen t.t_name then false
      else (Hashtbl.replace seen t.t_name true; true)
    ) (from_target @ from_knowns @ bridge)
  in

  (* PPR: seed on target (weight 1.0) and all known bindings (weight 0.5).
     Conductances are structure-derived from the seed neighbourhood.
     Runs once per chain_resolve call; scores guide beam expansion.
     depth_affinity encodes how strongly BFS-ordering is preferred over PPR score. *)
  let seed_nodes =
    (target, 1.0) ::
    List.map (fun b -> (b.b_name, 0.5)) bindings
  in
  let binding_names = List.map (fun b -> b.b_name) bindings in
  let ppr_scores = Proof_graph.run_ppr k ~seed_nodes ~target ~binding_names in
  let depth_affinity = Proof_graph.query_depth_affinity k target binding_names in
  let ppr_score name =
    match Hashtbl.find_opt ppr_scores name with
    | Some s -> s
    | None   ->
      match Proof_graph.find k name with
      | Some n -> n.Proof_graph.satya
      | None   -> 0.0
  in
  (* beam_score: blend of PPR signal and depth preference.
     depth_affinity=1.0 → prefer shallow (tight computation query)
     depth_affinity=0.0 → follow PPR signal only (open conceptual query) *)
  let blend_score ppr_s depth =
    let depth_score = 1.0 /. (float_of_int depth +. 1.0) in
    ppr_s *. (1.0 -. depth_affinity) +. depth_score *. depth_affinity
  in

  (* beam state: (known_bindings, steps_so_far, depth, beam_score)
     beam_score = blend_score(ppr_score(last_tantra), depth) at the step that created this state.
     beam is a list sorted descending by beam_score; we keep top beam_width states. *)
  let make_state known steps depth score = (known, steps, depth, score) in
  let state_score (_, _, _, s) = s in

  let insert_beam beam state =
    (* insert in descending score order, keep top beam_width.
       beam is maintained sorted: highest score first. *)
    let rec take n = function
      | [] -> []
      | _ when n <= 0 -> []
      | x :: rest -> x :: take (n-1) rest
    in
    let rec insert_sorted = function
      | [] -> [state]
      | s :: rest ->
        if state_score state >= state_score s then state :: s :: rest
        else s :: insert_sorted rest
    in
    take beam_width (insert_sorted beam)
  in

  let beam = ref [make_state bindings [] 0 0.0] in
  let found = ref None in

  while !beam <> [] && !found = None do
    (* pop highest beam_score state. depth preference is already encoded in the score
       via blend_score, so no separate depth-tier logic is needed. *)
    let (best_state, rest_beam) =
      let indexed = List.mapi (fun i s -> (i, s)) !beam in
      let (best_i, best_s) = List.fold_left (fun (bi, bs) (i, s) ->
        let (_, _, _, sc) = s and (_, _, _, bsc) = bs in
        if sc > bsc then (i, s) else (bi, bs)
      ) (List.hd indexed) (List.tl indexed) in
      let rest = List.filter_map (fun (i, s) ->
        if i = best_i then None else Some s
      ) indexed in
      (best_s, rest)
    in
    beam := rest_beam;
    let (known, steps, depth, _path_score) = best_state in
    if depth <= max_depth then begin
      let knames = List.map (fun b -> b.b_name) known in
      if List.exists (fun n -> names_match_fast n target) knames then
        found := Some (List.rev steps)
      else begin
        (* 1. direct: tantra that produces target with current knowns *)
        let direct_done = ref false in
        List.iter (fun t ->
          if !found <> None || !direct_done then ()
          else
            let produces_target = List.exists (fun ret ->
              names_match_fast ret.tp_name target ||
              names_match_fast ret.tp_canonical target ||
              names_match_fast t.t_name target
            ) t.t_returns in
            if produces_target then
              match try_match_chain k t known idx with
              | Some assignments ->
                found := Some (List.rev (CForward (t, assignments) :: steps));
                direct_done := true
              | None -> ()
        ) candidate_tantras;

        if !found = None then begin
          (* 2. forward: tantras whose inputs are all satisfied — enqueue with PPR score *)
          let new_states = ref [] in
          List.iter (fun t ->
            if !found <> None then ()
            else
              match try_match_chain k t known idx with
              | Some assignments ->
                let produces_new = List.exists (fun ret ->
                  not (List.exists (fun n -> names_match_fast n ret.tp_name) knames)
                ) t.t_returns in
                if produces_new then begin
                  let input_values = List.map (fun (n, f) -> (n, VFloat f)) assignments in
                  (try
                    let result = !_eval_tantra_chain_ref k t input_values in
                    let new_bindings = match t.t_returns with
                      | [ret] ->
                        let v = as_float result in
                        let ts = Unix.gettimeofday () in
                        let mk n u = { b_name = n; b_value = v; b_unit = u;
                                       b_timestamp = ts; b_source = "tantra:" ^ t.t_name;
                                       b_confidence = 1.0; b_ttl = None } in
                        let base = [mk ret.tp_name ret.tp_unit] in
                        let aliases = ref base in
                        if t.t_name <> ret.tp_name then
                          aliases := mk t.t_name ret.tp_unit :: !aliases;
                        if ret.tp_canonical <> ret.tp_name && ret.tp_canonical <> t.t_name then
                          aliases := mk ret.tp_canonical ret.tp_unit :: !aliases;
                        (match String.rindex_opt t.t_name '-' with
                         | Some i ->
                           let last = String.sub t.t_name (i+1) (String.length t.t_name - i - 1) in
                           if last <> ret.tp_name && last <> t.t_name then
                             aliases := mk last ret.tp_unit :: !aliases
                         | None -> ());
                        !aliases
                      | rets ->
                        let ts = Unix.gettimeofday () in
                        let values = as_list result in
                        List.mapi (fun i ret ->
                          let v = if i < List.length values then List.nth values i else VNone in
                          { b_name = ret.tp_name; b_value = as_float v; b_unit = ret.tp_unit;
                            b_timestamp = ts; b_source = "tantra:" ^ t.t_name;
                            b_confidence = 1.0; b_ttl = None }
                        ) rets
                    in
                    let step_s = ppr_score t.t_name in
                     let new_depth = depth + 1 in
                     (* beam_score: blend of PPR signal and depth preference.
                        depth_affinity encodes how strongly shallow paths are preferred. *)
                     let new_score = blend_score step_s new_depth in
                    let new_state = make_state
                      (known @ new_bindings)
                      (CForward (t, assignments) :: steps)
                      new_depth new_score in
                    new_states := new_state :: !new_states
                  with _ -> ())
                end
              | None -> ()
          ) candidate_tantras;

          (* 3. inverse: tantra whose output we have, one input missing *)
          List.iter (fun t ->
            if !found <> None then ()
            else
              List.iter (fun (ret : tantra_param) ->
                if !found <> None then ()
                else
                  let output_binding = List.find_opt (fun b ->
                    names_match_resolved k b.b_name ret.tp_name ||
                    names_match_resolved k b.b_name ret.tp_canonical ||
                    names_match_resolved k b.b_name t.t_name
                  ) known in
                  match output_binding with
                  | None -> ()
                  | Some ob ->
                    let missing = List.filter (fun inp ->
                      not (List.exists (fun b ->
                        names_match_resolved k b.b_name inp.tp_name ||
                        names_match_resolved k b.b_name inp.tp_canonical
                      ) known) &&
                      Hashtbl.find_opt idx.constants inp.tp_name = None
                    ) t.t_inputs in
                    match missing with
                    | [missing_inp] ->
                      let other_inputs = List.filter (fun inp ->
                        inp.tp_name <> missing_inp.tp_name
                      ) t.t_inputs in
                      let other_values = List.filter_map (fun (inp : tantra_param) ->
                        match List.find_opt (fun b ->
                          names_match_resolved k b.b_name inp.tp_name
                        ) known with
                        | Some b -> Some (inp.tp_name, b.b_value)
                        | None ->
                          match Hashtbl.find_opt idx.constants inp.tp_name with
                          | Some v -> Some (inp.tp_name, v)
                          | None -> None
                      ) other_inputs in
                      if List.length other_values = List.length other_inputs then begin
                        let ret_name = ret.tp_name in
                        let known_values = (ret_name, ob.b_value) :: other_values in
                        let known_names_for_inv = List.map fst known_values @
                          List.map (fun inp -> inp.tp_name) other_inputs in
                        match invert_chain k t.t_lets known_names_for_inv
                                missing_inp.tp_name ret_name with
                        | Some plan ->
                          let env = new_env () in
                          List.iter (fun (n, f) -> Hashtbl.replace env n (VFloat f)) known_values;
                          (try
                            List.iter (fun (n, rhs) ->
                              let v = !_eval_chain_ref k env rhs in
                              Hashtbl.replace env n v
                            ) plan;
                            let result_v = match Hashtbl.find_opt env missing_inp.tp_name with
                              | Some v -> as_float v | None -> 0.0 in
                            let new_b = { b_name = missing_inp.tp_name;
                                          b_value = result_v;
                                          b_unit = missing_inp.tp_unit;
                                          b_timestamp = Unix.gettimeofday ();
                                          b_source = "tantra:" ^ t.t_name;
                                          b_confidence = 1.0; b_ttl = None } in
                             (* inverse step: PPR score weighted by pratipaksha vp_satya_weight,
                                then blended with depth preference via depth_affinity. *)
                             let pratipaksha_w =
                                (Proof_graph.vish_props_of Proof_graph.pratipaksha).Proof_graph.vp_satya_weight in
                             let step_s = ppr_score t.t_name *. pratipaksha_w in
                             let new_depth = depth + 1 in
                             let new_score = blend_score step_s new_depth in
                            let new_state = make_state
                              (new_b :: known)
                              (CInverse (t, missing_inp.tp_name, plan, known_values) :: steps)
                              new_depth new_score in
                            new_states := new_state :: !new_states
                          with _ -> ())
                        | None -> ()
                      end
                    | _ -> ()
              ) t.t_returns
          ) candidate_tantras;

          (* insert new states into beam, keeping top beam_width by score *)
          List.iter (fun state ->
            beam := insert_beam !beam state
          ) !new_states
        end
      end
    end
  done;
  !found
