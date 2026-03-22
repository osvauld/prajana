(* om5_parser.ml — parse .om5 s-expression format into nigamana.

   Format:
     (layer name
       (relation target1 target2 ...)
       ...)

   - layer: sangati | kosha | bhasha | mantra
   - Each (relation target...) becomes typed_edge(s): source=name, relation=rel, target=t
   - Comments: -- to end of line
   - No compound decomposition — edges are explicit
   - No two-pass name collection needed
   - Coexists with .om — om5 supersedes same-name .om nodes
*)

open Proof_graph

(* reuse tokenizer from tantra sexp parser *)
let tokenize = Yantra_tantra_sexp.tokenize_sexp

(* parse one (relation target...) group into typed edges *)
let parse_edge_group (source : string) (tokens : string list)
    : typed_edge list * string list =
  (* tokens starts after opening "(", ends at matching ")" *)
  match tokens with
  | [] -> ([], [])
  | rel_name :: rest ->
    let rel = visheshanam_of_string rel_name in
    (* collect targets until ")" *)
    let rec collect acc toks =
      match toks with
      | ")" :: rest' -> (List.rev acc, rest')
      | [] -> (List.rev acc, [])
      | t :: rest' -> collect (t :: acc) rest'
    in
    let (targets, remaining) = collect [] rest in
    match rel with
    | None ->
      (* unknown relation — skip this group *)
      ([], remaining)
    | Some v ->
      let edges = List.map (fun target ->
        { source; target; relation = v }
      ) targets in
      (edges, remaining)

(* parse a complete om5 s-expression from tokens *)
let parse_om5_tokens (tokens : string list) : nigamana option =
  (* expect: "(" layer name ... ")" *)
  match tokens with
  | "(" :: layer_str :: name :: rest
    when layer_str = "sangati" || layer_str = "kosha"
      || layer_str = "bhasha" || layer_str = "mantra" ->
    let all_edges = ref [] in
    let krama_expr = ref "" in
    let rec parse_body toks =
      match toks with
      | [] | ")" :: _ -> ()
      | "(" :: "krama" :: rest ->
        (* collect krama expression tokens until matching ")" *)
        let depth = ref 1 in
        let expr_toks = ref [] in
        let remaining = ref rest in
        while !depth > 0 && !remaining <> [] do
          match !remaining with
          | "(" :: tl -> incr depth; expr_toks := "(" :: !expr_toks; remaining := tl
          | ")" :: tl -> decr depth;
            if !depth > 0 then expr_toks := ")" :: !expr_toks;
            remaining := tl
          | t :: tl -> expr_toks := t :: !expr_toks; remaining := tl
          | [] -> ()
        done;
        krama_expr := String.concat " " (List.rev !expr_toks);
        parse_body !remaining
      | "(" :: rest ->
        let (edges, remaining) = parse_edge_group name rest in
        all_edges := edges @ !all_edges;
        parse_body remaining
      | _ :: rest ->
        (* skip unexpected tokens *)
        parse_body rest
    in
    parse_body rest;
    Some {
      name;
      layer = layer_str;
      slokas = [];  (* om5 has no raw slokas *)
      edges = List.rev !all_edges;
      satya = 0.0;
      shabda = "";
      krama = !krama_expr;
    }
  | _ -> None

(* parse one .om5 file *)
let parse_file (path : string) : nigamana option =
  try
    let ic = open_in path in
    let buf = Buffer.create 1024 in
    (try while true do
      Buffer.add_string buf (input_line ic);
      Buffer.add_char buf '\n'
    done with End_of_file -> ());
    close_in ic;
    let src = Buffer.contents buf in
    let tokens = tokenize src in
    parse_om5_tokens tokens
  with _ -> None

(* collect .om5 files recursively from a directory *)
let om5_files_recursive (root : string) : string list =
  let files = ref [] in
  let rec walk dir =
    try
      let entries = Sys.readdir dir in
      Array.iter (fun entry ->
        let path = Filename.concat dir entry in
        try
          if Sys.is_directory path then walk path
          else if Filename.check_suffix entry ".om5" then
            files := path :: !files
        with Sys_error _ -> ()
      ) entries
    with Sys_error _ -> ()
  in
  walk root;
  List.sort String.compare !files

(* discover dynamic dimensions from visheshanam-ring om5 file.
   the ring's yukta targets are the dimension names.
   skip visheshanam-* prefixed targets (those are nodes, not dims)
   and targets already registered as core dims. *)
let collect_dynamic_dims_from_ring (dirs : string list) (_known_names : string list) : string list =
  let dims = ref [] in
  List.iter (fun dir ->
    List.iter (fun path ->
      match parse_file path with
      | Some n when n.name = "visheshanam-ring" ->
        let yukta_idx = Proof_graph.visheshanam_of_string "yukta" in
        List.iter (fun e ->
          if e.Proof_graph.source = "visheshanam-ring" then
            match yukta_idx with
            | Some yi when e.Proof_graph.relation = yi ->
              let target = e.Proof_graph.target in
              if not (String.length target > 13
                      && String.sub target 0 13 = "visheshanam-")
                 && Proof_graph.visheshanam_of_string target = None then
                dims := target :: !dims
            | _ -> ()
        ) n.Proof_graph.edges
      | _ -> ()
    ) (om5_files_recursive dir)
  ) dirs;
  !dims

(* collect node names from .om5 files (for pass 1 name collection) *)
let collect_names (dir : string) : string list =
  let names = ref [] in
  List.iter (fun path ->
    try
      let ic = open_in path in
      let buf = Buffer.create 256 in
      (try
        (* read enough to find the header — first 3 tokens *)
        for _ = 1 to 5 do
          Buffer.add_string buf (input_line ic);
          Buffer.add_char buf '\n'
        done
      with End_of_file -> ());
      close_in ic;
      let tokens = tokenize (Buffer.contents buf) in
      (match tokens with
       | "(" :: layer :: name :: _
         when layer = "sangati" || layer = "kosha"
           || layer = "bhasha" || layer = "mantra" ->
         names := name :: !names
       | _ -> ())
    with _ -> ()
  ) (om5_files_recursive dir);
  !names
