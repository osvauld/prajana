(* setu_classify.ml — token classification for the yantra pipeline.
   maps natural language words to graph nodes or grammatical roles.
   depends on Setu_shabda for reading english-grammar / english-token-roles.
   dependency: Proof_graph, Setu_shabda. *)

open Proof_graph

(* --- grammar classification ---
   reads from english-grammar node shabda: word:visheshanam pairs *)

let grammar_of_english_cache : (string, visheshanam option) Hashtbl.t = Hashtbl.create 64

let grammar_of_english_loaded = ref false

let load_grammar_of_english (k : proof_graph) : unit =
  if not !grammar_of_english_loaded then begin
    grammar_of_english_loaded := true;
    let pairs = Setu_shabda.read_shabda k "english-grammar" in
    List.iter (fun (word, vish_str) ->
      let v = visheshanam_of_string vish_str in
      Hashtbl.replace grammar_of_english_cache word v
    ) pairs
  end

let grammar_of_english (k : proof_graph) word =
  load_grammar_of_english k;
  let w = String.lowercase_ascii word in
  match Hashtbl.find_opt grammar_of_english_cache w with
  | Some v -> v
  | None   -> None

let english_token_roles_cache : (string, string) Hashtbl.t = Hashtbl.create 64

let english_token_roles_loaded = ref false

let load_english_token_roles (k : proof_graph) : unit =
  if not !english_token_roles_loaded then begin
    english_token_roles_loaded := true;
    let pairs = Setu_shabda.read_shabda k "english-token-roles" in
    List.iter (fun (token, role) ->
      Hashtbl.replace english_token_roles_cache token role
    ) pairs
  end

let english_number_words_cache : (string, string) Hashtbl.t = Hashtbl.create 32

let english_number_words_loaded = ref false

let load_english_number_words (k : proof_graph) : unit =
  if not !english_number_words_loaded then begin
    english_number_words_loaded := true;
    let pairs = Setu_shabda.read_shabda k "english-number-words" in
    List.iter (fun (n, word) ->
      Hashtbl.replace english_number_words_cache n word
    ) pairs
  end

let english_number_word (k : proof_graph) (n : string) : string option =
  load_english_number_words k;
  Hashtbl.find_opt english_number_words_cache n

type token_role =
  | Article
  | Grammar of int  (* visheshanam dimension index *)
  | Content of string
  | Number of float
  | Operator of string
  | Unknown of string

let classify_token (k : proof_graph) word =
  let w = String.lowercase_ascii word in
  (* detect operators first *)
  let is_op = w = "+" || w = "-" || w = "*" || w = "/" || w = "=" in
  if is_op then Operator w
  else
  (* detect numbers: try float first (handles "9.8", "3.14"), then int *)
  match float_of_string_opt w with
  | Some f -> Number f
  | None ->
  let is_number =
    match int_of_string_opt w with
    | Some _ -> true
    | None -> false
  in
  if is_number then
    match english_number_word k w with
    | Some mapped -> Content mapped
    | None -> Content w
  else begin
    load_english_token_roles k;
    match Hashtbl.find_opt english_token_roles_cache w with
    | Some "article" -> Article
    | Some "sthita" -> Grammar Proof_graph.sthita
    | Some role ->
      (match grammar_of_english k role with
       | Some v -> Grammar v
       | None -> Content role)
    | None ->
      match grammar_of_english k w with
      | Some v -> Grammar v
      | None ->
        match Hashtbl.find_opt k.nodes w with
        | Some _ -> Content w
        | None ->
          (* search node shabda lines for this English word — checked before partial name match *)
          let shabda_match = Hashtbl.fold (fun name _n acc ->
            (match acc with
            | Some _ -> acc
            | None ->
              let raw = match Setu_shabda.(Hashtbl.find_opt _shabda_store name) with
                | Some s -> s | None -> "" in
              let shabda = String.lowercase_ascii (String.trim raw) in
              if shabda = "" then None
              else
                let before_slash = (match String.index_opt shabda '/' with
                  | Some i -> String.sub shabda 0 i
                  | None -> shabda)
                in
                let tokens = String.split_on_char ',' before_slash
                  |> List.map String.trim
                  |> List.concat_map (fun t -> String.split_on_char ' ' t)
                  |> List.map String.trim
                  |> List.filter (fun t -> String.length t > 0)
                in
                if List.mem w tokens then Some name else None)
          ) k.nodes None in
          (match shabda_match with
          | Some name -> Content name
          | None ->
            let partial_matches = Hashtbl.fold (fun name _ acc ->
              let parts = String.split_on_char '-' name in
              if List.exists (fun p -> String.lowercase_ascii p = w) parts then
                name :: acc
              else acc
            ) k.nodes [] in
            match partial_matches with
            | [single] -> Content single
            | _ :: _ ->
              (* prefer domain-<word> exact match first, then word itself, then alphabetical *)
              let domain_name = "domain-" ^ w in
              if List.mem domain_name partial_matches then Content domain_name
              else if List.mem w partial_matches then Content w
              else Content (List.hd (List.sort String.compare partial_matches))
            | [] -> Unknown w)
  end
