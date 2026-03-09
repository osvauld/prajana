(* anuvada.ml — sentence understanding + emit-from-graph + output
   the reasoning/text output layer. reads the graph via Setu. emits text and Strudel.

   responsibility: question answering, concept explanation, resonance reasoning.
   not responsible for code generation — that is prayoga's domain.

   setu nodes used here:
     visheshanam-english  — relation types -> English phrases
     thaalam              — beat cycle names and counts
     ocaml-setu           — OCaml forms for math/physics bridge programs
     swara-to-strudel     — swara names -> pitch letters
     strudel              — synth/rhythm defaults

   dependency: Proof_graph, Setu. *)

open Proof_graph

(* sahaja gloss now comes directly from each node's shabda field. *)

(* render a visheshanam as an English phrase — reads from visheshanam-english node *)
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

(* rhythmic cycle — reads beat counts from thaalam node shabda *)
let thaalam_cycle_cache : (string, (string * int)) Hashtbl.t = Hashtbl.create 8

let thaalam_cycle_loaded = ref false

let load_thaalam_cycle (k : proof_graph) : unit =
  if not !thaalam_cycle_loaded then begin
    thaalam_cycle_loaded := true;
    let pairs = Setu.read_shabda k "thaalam" in
    List.iter (fun (name, beats_str) ->
      match int_of_string_opt beats_str with
      | Some beats -> Hashtbl.replace thaalam_cycle_cache name (name, beats)
      | None -> ()
    ) pairs
  end

let thaalam_cycle (k : proof_graph) name =
  load_thaalam_cycle k;
  let n = String.lowercase_ascii name in
  (* try exact match first, then prefix match *)
  match Hashtbl.find_opt thaalam_cycle_cache n with
  | Some pair -> Some pair
  | None ->
    Hashtbl.fold (fun key pair acc ->
      match acc with
      | Some _ -> acc
      | None ->
         if String.length n >= String.length key
            && String.sub n 0 (String.length key) = key
         then Some pair
         else None
     ) thaalam_cycle_cache None

let thaalam_default (k : proof_graph) : string option =
  let pairs = Setu.read_shabda k "thaalam" in
  Setu.shabda_get pairs "default"

(* --- avrti on language: the spiral --- *)

type anuvada_triple = {
  a_source   : string;
  a_source_raw : string;
  a_relation : visheshanam;
  a_targets  : string list;
  a_targets_raw : string list;
  a_pass     : int;
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
          let unique_targets = List.sort_uniq String.compare
            (List.map snd target_pairs) in
          let unique_targets_raw = List.sort_uniq String.compare
            (List.map fst target_pairs) in
          if unique_targets <> [] then
            triples := { a_source = english_name;
                         a_source_raw = name;
                         a_relation = vish;
                         a_targets = unique_targets;
                         a_targets_raw = unique_targets_raw;
                         a_pass = pass_num } :: !triples;
          List.iter (fun t ->
            new_targets := t :: !new_targets
          ) targets
        ) by_type
    end
  ) content_words;
  (List.rev !triples, List.sort_uniq String.compare !new_targets)

let avrti_anuvada (k : proof_graph) (seed_words : string list)
    (max_passes : int) : (int * anuvada_triple list) list * int =
  let visited_nodes = Hashtbl.create 64 in
  let seen_triples = ref TripleSet.empty in
  let passes_result = ref [] in
  let pass = ref 0 in
  let current_words = ref seed_words in
  let found_new = ref true in
  while !found_new && !pass < max_passes do
    incr pass;
    let (triples, new_targets) =
      walk_one_pass k !current_words visited_nodes !pass in
    let (novel, updated_seen) = List.fold_left (fun (acc, seen) t ->
      let key = (t.a_source, t.a_relation, t.a_targets) in
      if TripleSet.mem key seen then (acc, seen)
      else (t :: acc, TripleSet.add key seen)
    ) ([], !seen_triples) triples in
    let novel = List.rev novel in
    if novel = [] then
      found_new := false
    else begin
      seen_triples := updated_seen;
      passes_result := !passes_result @ [(!pass, novel)];
      current_words := List.filter (fun n ->
        not (Hashtbl.mem visited_nodes n)
      ) new_targets
    end
  done;
  (!passes_result, !pass)

let sahaja_gloss (k : proof_graph) (name : string) : string =
  match find k name with
  | Some n when String.trim n.shabda <> "" ->
    let tokens = String.split_on_char ' ' (String.trim n.shabda) in
    let gloss_tokens = List.filter (fun t -> not (String.contains t ':')) tokens in
    let gloss = String.concat " " gloss_tokens |> String.trim in
    if gloss <> "" then gloss else Setu.to_english k name
  | _ ->
    let sw = Setu.swarupa_of k name in
    let kr = Setu.kriya_of k name in
    let eng_of n =
      let e = Setu.to_english k n in
      if e = n then None else Some e
    in
    let sw_eng = List.filter_map eng_of sw in
    let kr_eng = List.filter_map eng_of kr in
    (match sw_eng, kr_eng with
    | s :: _, k_ :: _ -> s ^ "-" ^ k_
    | s :: _, []      -> s
    | [],     k_ :: _ -> k_
    | [],     []      -> Setu.to_english k name)

let sahaja_render (k : proof_graph) (name : string) : string =
  let gloss = sahaja_gloss k name in
  if gloss = name then name
  else Printf.sprintf "%s (%s)" gloss name

let render_pass_groups_simple ?(context : string option = None)
    (k : proof_graph) (pass_groups : (int * anuvada_triple list) list) : string =
  let buf = Buffer.create 512 in
  let render_name raw = Setu.to_english ~context k raw in
  let render_triple (t : anuvada_triple) =
    let rel = english_of_visheshanam_from_graph k t.a_relation in
    let tgts = String.concat ", " (List.map render_name t.a_targets_raw) in
    Printf.sprintf "  %s %s %s.\n" (render_name t.a_source_raw) rel tgts
  in
  List.iter (fun (_p, triples) ->
    List.iter (fun t -> Buffer.add_string buf (render_triple t)) triples
  ) pass_groups;
  Buffer.contents buf

(* render darshana (node inspection) to a buffer *)
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

(* --- ocaml code emission from graph structure --- *)

let ocaml_setu_pairs (k : proof_graph) : (string * string) list =
  Setu.read_shabda k "ocaml-setu"

let ocaml_symbol_of_operator (k : proof_graph) (op_name : string) : string option =
  let key = String.lowercase_ascii op_name in
  Setu.shabda_get (ocaml_setu_pairs k) key

let ocaml_constructor_of_operator (k : proof_graph) (op_name : string) : string =
  let key = Printf.sprintf "%s-constructor" (String.lowercase_ascii op_name) in
  match Setu.shabda_get (ocaml_setu_pairs k) key with
  | Some ctor -> ctor
  | None -> Setu.capitalize_first (Setu.sanitize_ocaml_ident op_name)

type math_op_kind =
  | ArithmeticOp
  | VectorOp
  | MatrixOp

let classify_math_op (k : proof_graph) (target : string) : math_op_kind option =
  match Hashtbl.find_opt k.nodes target with
  | None -> None
  | Some target_node ->
    let kriya_targets = List.filter_map (fun e ->
      if e.source = target && e.relation = kriya then Some e.target else None
    ) target_node.edges in
    let name = String.lowercase_ascii target in
    if name = "dot-product" || name = "matrix-multiplication" then
      Some MatrixOp
    else if List.mem "arithmetic" kriya_targets then
      Some ArithmeticOp
    else if List.mem "dot-product" kriya_targets
         || List.mem "scalar-multiplication" kriya_targets
         || List.mem "addition" kriya_targets then
      Some VectorOp
    else None

let yukta_operators (k : proof_graph) (node_name : string)
    : (string * math_op_kind) list =
  match Hashtbl.find_opt k.nodes node_name with
  | None -> []
  | Some n ->
    List.filter_map (fun e ->
      if e.source = node_name && e.relation = yukta then
        match classify_math_op k e.target with
        | Some kind -> Some (e.target, kind)
        | None -> None
      else None
    ) n.edges
    |> List.sort_uniq (fun (a,_) (b,_) -> String.compare a b)

let filename_from_graph (k : proof_graph) (bridge_name : string) : string =
  let inputs = Setu.infer_inputs k bridge_name in
  let outputs = Setu.infer_outputs k bridge_name in
  let input_part = match List.filter (fun i ->
    i <> "expression" && i <> "ocaml" && i <> "anuvada"
  ) inputs with
    | first :: _ -> Setu.sanitize_ocaml_ident first
    | [] -> match inputs with first :: _ -> Setu.sanitize_ocaml_ident first | [] -> Setu.sanitize_ocaml_ident bridge_name
  in
  let output_part = match outputs with
    | first :: _ -> Setu.sanitize_ocaml_ident first
    | [] -> "out"
  in
  input_part ^ "_to_" ^ output_part ^ ".ml"

let write_program (buf : Buffer.t) (filename : string) : unit =
  let code = Buffer.contents buf in
  let oc = open_out filename in
  output_string oc code;
  close_out oc;
  Printf.printf "  wrote: %s\n" filename;
  Printf.printf "  run:   ocaml %s\n" filename

let ocaml_type_of_concept (k : proof_graph) (concept : string) : string =
  let concept_key = String.lowercase_ascii concept in
  (match Setu.shabda_get (ocaml_setu_pairs k) concept_key with
   | Some mapped -> String.map (fun c -> if c = '-' then ' ' else c) mapped
   | None ->
  let sw = Setu.swarupa_of k concept in
  let has s = List.mem s sw in
  match has "float", has "matrix", has "list", has "array" with
  | true, true,  _,     _     -> "float array array"
  | true, false, true,  _     -> "float list"
  | true, false, _,     true  -> "float array"
  | true, false, false, false -> "float"
  | _                         -> "string")

let ocaml_prim (k : proof_graph) (op : string) (elem_type : string) : string =
  let key = Printf.sprintf "%s-%s" (String.lowercase_ascii op) elem_type in
  match Setu.shabda_get (ocaml_setu_pairs k) key with
  | Some prim -> prim
  | None -> op

let ocaml_of_composition
    (k : proof_graph)
    (shape : string list)
    (ops   : string list)
    (container : string)
    (_elem : string)
    : string option =
  (* Build a canonical key from the combination and look it up in ocaml-setu.
     Key format: impl-<shape-flags>-<op-flags>-<container-short>
     e.g. impl-map-fold-dot-list, impl-map-fold-dot-aa, impl-map-fold-mul-add-list *)
  let has_map  = List.mem "map"                   shape in
  let has_fold = List.mem "fold"                  shape in
  let has_dot  = List.mem "dot-product"           ops   in
  let has_mul  = List.mem "multiplication"        ops
              || List.mem "scalar-multiplication" ops   in
  let has_add  = List.mem "addition"              ops   in
  let has_scl  = List.mem "scalar-multiplication" ops
              && not (List.mem "addition"          ops) in
  let cshort = match container with
    | "float list"        -> "list"
    | "float array"       -> "array"
    | "float array array" -> "aa"
    | _                   -> "other"
  in
  let flags = List.filter_map (fun (b, s) -> if b then Some s else None)
    [ has_map,  "map"
    ; has_fold, "fold"
    ; has_dot,  "dot"
    ; has_scl,  "scl"
    ; has_mul,  "mul"
    ; has_add,  "add"
    ] in
  let key = "impl-" ^ String.concat "-" (flags @ [cshort]) in
  Setu.shabda_get (ocaml_setu_pairs k) key

let read_row_expr : string =
  "Array.of_list (List.filter_map float_of_string_opt\n" ^
  "      (String.split_on_char ' ' (String.trim (input_line stdin))))"

let ocaml_read_of (k : proof_graph) (concept : string) : string =
  let typ = ocaml_type_of_concept k concept in
  match typ with
  | "float array array" ->
    "let _n = int_of_string (String.trim (input_line stdin)) in\n" ^
    "    Array.init _n (fun _ ->\n" ^
    "      " ^ read_row_expr ^ ")"
  | "float list" ->
    "List.filter_map float_of_string_opt\n" ^
    "    (String.split_on_char ' ' (String.trim (input_line stdin)))"
  | "float array" ->
    "Array.of_list (List.filter_map float_of_string_opt\n" ^
    "    (String.split_on_char ' ' (String.trim (input_line stdin))))"
  | "int"    -> "(int_of_string (String.trim (input_line stdin)))"
  | _        -> "input_line stdin"

let ocaml_print_of (k : proof_graph) (concept : string) (var : string) : string =
  let typ = ocaml_type_of_concept k concept in
  match typ, concept with
  | _, "ocaml"   -> Printf.sprintf "Printf.printf \"= %%d\\n\" %s" var
  | _, "scalar"  -> Printf.sprintf "Printf.printf \"%%g\\n\" %s" var
  | "float array array", _ ->
    "Array.iter (fun row ->\n" ^
    "    print_endline (String.concat \" \" (Array.to_list (Array.map string_of_float row)))\n" ^
    Printf.sprintf "  ) %s" var
  | "float list", _ ->
    Printf.sprintf
      "print_endline (String.concat \" \" (List.map string_of_float %s))" var
  | "float array", _ ->
    Printf.sprintf
      "print_endline (String.concat \" \" (Array.to_list (Array.map string_of_float %s)))" var
  | "float",  _ -> Printf.sprintf "Printf.printf \"%%g\\n\" %s" var
  | "int",    _ -> Printf.sprintf "Printf.printf \"%%d\\n\" %s" var
  | _,        _ -> Printf.sprintf "Printf.printf \"%%d\\n\" %s" var

let emit_bridge_program (k : proof_graph) (bridge_name : string) : unit =
  let all_ops = yukta_operators k bridge_name in
  if all_ops = [] then ()
  else begin
    let buf = Buffer.create 1024 in
    let p fmt = Printf.bprintf buf fmt in
    let inputs  = Setu.infer_inputs  k bridge_name in
    let outputs = Setu.infer_outputs k bridge_name in
    let input_concept  = match inputs  with t :: _ -> t | [] -> "unknown" in
    let output_concept = match outputs with t :: _ -> t | [] -> "unit" in
    let container_type = ocaml_type_of_concept k input_concept in
    let _elem_type = match container_type with
      | "float list" | "float array" | "float array array" -> "float"
      | "int" -> "int"
      | _ -> "string"
    in
    let root = match Hashtbl.find_opt k.nodes bridge_name with
      | None -> bridge_name
      | Some n -> (match List.filter_map (fun e ->
          if e.source = bridge_name && e.relation = abheda then Some e.target
          else None) n.edges with r :: _ -> r | [] -> bridge_name)
    in
    p "(* %s — root: %s *)\n" bridge_name root;
    let arithmetic_ops = List.filter_map (fun (n, kind) ->
      match kind with ArithmeticOp -> Some n | _ -> None) all_ops in
    let structural_ops = List.filter_map (fun (n, kind) ->
      match kind with ArithmeticOp -> None | _ -> Some n) all_ops in
    List.iter (fun op_name ->
      let op_kriya   = Setu.kriya_of k op_name in
      let op_janya   = Setu.janya_of k op_name in
      let op_inputs  = Setu.infer_inputs  k op_name in
      let op_outputs = Setu.infer_outputs k op_name in
      let fn = Setu.sanitize_ocaml_ident op_name in
      let op_in_concept =
        let typed = List.filter (fun t ->
          Setu.swarupa_of k t <> []
        ) op_inputs in
        match typed with
        | t :: _ -> t
        | [] -> (match op_inputs with t :: _ -> t | [] -> input_concept)
      in
      let op_out_concept = match op_outputs with t :: _ -> t | [] -> output_concept in
      let op_self_sw = Setu.swarupa_of k op_name in
      let op_container =
        let has s = List.mem s op_self_sw in
        match has "array", has "float", has "list" with
        | true,  true,  _     -> "float array array"
        | true,  _,     _     -> "array"
        | false, true,  true  -> "float list"
        | false, true,  false -> "float"
        | _                   -> ocaml_type_of_concept k op_in_concept
      in
      let op_elem = match op_container with
        | "float list" | "float array" | "float array array" -> "float"
        | "int" -> "int" | _ -> "string" in
      let op_in_types = List.map (fun inp ->
        if Setu.swarupa_of k inp <> [] then ocaml_type_of_concept k inp
        else op_container
      ) op_inputs in
      let sig_args = String.concat " -> " op_in_types in
      let op_out_type = ocaml_type_of_concept k op_out_concept in
      match ocaml_of_composition k op_janya op_kriya op_container op_elem with
      | Some impl ->
        p "let %s : %s -> %s = %s\n" fn sig_args op_out_type impl
      | None ->
        let desc = String.concat ", " op_kriya ^ " via " ^ String.concat ", " op_janya in
        p "(* %s: %s — no rendering defined yet *)\n" fn desc
    ) structural_ops;
    if arithmetic_ops <> [] then begin
      let op_info = List.filter_map (fun op ->
        match ocaml_symbol_of_operator k op with
        | None -> None
        | Some sym -> Some (op, ocaml_constructor_of_operator k op, sym)
      ) arithmetic_ops in
      let arity = if List.exists (fun e ->
        e.source = input_concept && e.relation = yukta && e.target = "number"
      ) (match Hashtbl.find_opt k.nodes input_concept with
         | Some n -> n.edges | None -> [])
      then 2 else 2 in
      let operands = Array.to_list (Array.sub [|"a";"b";"c";"d"|] 0 (min arity 4)) in
      p "type operator = %s\n"
        (String.concat " | " (List.map (fun (_, c, _) -> c) op_info));
      let sig_ = String.concat " "
        (List.map (fun nm -> Printf.sprintf "~(%s:int)" nm) operands) in
      p "let eval %s ~(op:operator) : int =\n  match op with\n" sig_;
      List.iter (fun (_, ctor, sym) ->
        let body = match operands with
          | [a;b] -> Printf.sprintf "%s %s %s" a sym b
          | [a]   -> Printf.sprintf "%s %s 0" a sym
          | _     -> "0" in
        p "  | %s -> %s\n" ctor body
      ) op_info;
      p "let operator_of_symbol s = match s with\n";
      List.iter (fun (_, ctor, sym) -> p "  | %S -> Some %s\n" sym ctor) op_info;
      p "  | _ -> None\n";
      let pat = match List.map (fun nm -> nm ^ "_s") operands with
        | [a;b] -> Printf.sprintf "%s; op_s; %s" a b
        | [a]   -> Printf.sprintf "%s; op_s" a
        | vs    -> String.concat "; " (vs @ ["op_s"]) in
      p "let calculate expr =\n";
      p "  match String.split_on_char ' ' (String.trim expr) with\n";
      p "  | [%s] ->\n" pat;
      let pvars = String.concat ", "
        (List.map (fun nm -> Printf.sprintf "int_of_string_opt %s_s" nm) operands) in
      p "    (match %s, operator_of_symbol op_s with\n" pvars;
      let svars = String.concat ", "
        (List.map (fun nm -> Printf.sprintf "Some %s" nm) operands) in
      let cargs = String.concat " " (List.map (fun nm -> "~" ^ nm) operands) in
      p "     | %s, Some op -> Some (eval %s ~op)\n" svars cargs;
      p "     | _ -> None)\n";
      p "  | _ -> None\n"
    end;
    let has_exec = match Hashtbl.find_opt k.nodes bridge_name with
      | None -> false
      | Some n -> List.exists (fun e ->
          e.source = bridge_name && e.relation = yukta && e.target = "execution"
        ) n.edges
    in
    if has_exec then begin
      let exec_edges = match Hashtbl.find_opt k.nodes "execution" with
        | None -> [] | Some en -> en.edges in
      let needs_in  = List.exists (fun e ->
        e.source = "execution" && e.relation = sthita && e.target = "ahara"
      ) exec_edges in
      let needs_out = List.exists (fun e ->
        e.source = "execution" && e.relation = phala && e.target = "ahara"
      ) exec_edges in
      p "let () =\n";
      let has_structural = structural_ops <> [] in
      if needs_in && not has_structural then begin
        p "  print_string \"%s: \"; flush stdout;\n" input_concept;
        p "  let ahara = %s in\n" (ocaml_read_of k input_concept)
      end;
      if needs_out then begin
        if arithmetic_ops <> [] then begin
          p "  (match calculate ahara with\n";
          p "  | Some r -> %s\n" (ocaml_print_of k output_concept "r");
          p "  | None -> print_endline \"could not parse\")\n"
        end else if structural_ops <> [] then begin
          let read_vars : (string * string) list ref = ref [] in
          List.iter (fun op_name ->
            let fn = Setu.sanitize_ocaml_ident op_name in
            let op_inputs  = Setu.infer_inputs  k op_name in
            let op_outputs = Setu.infer_outputs k op_name in
            let out_c  = match op_outputs with t :: _ -> t | [] -> output_concept in
            let op_self_sw2 = Setu.swarupa_of k op_name in
            let op_fallback_type =
              let has s = List.mem s op_self_sw2 in
              match has "array", has "float", has "list", has "matrix" with
              | _,    true, true,  _    -> "float list"
              | true, true, _,     _    -> "float array array"
              | _,    true, _,     _    -> "float"
              | _                       -> "string"
            in
            let ensure_read concept =
              let vname = Setu.sanitize_ocaml_ident concept in
              if not (List.mem_assoc vname !read_vars) then begin
                read_vars := (vname, concept) :: !read_vars;
                let typ =
                  if Setu.swarupa_of k concept <> [] then ocaml_type_of_concept k concept
                  else op_fallback_type
                in
                p "  print_string \"%s: \"; flush stdout;\n" concept;
                let read_expr = match typ with
                  | "float array array" ->
                    "let _n = int_of_string (String.trim (input_line stdin)) in\n" ^
                    "    Array.init _n (fun _ ->\n" ^
                    "      " ^ read_row_expr ^ ")"
                  | "float list" ->
                    "List.filter_map float_of_string_opt\n" ^
                    "    (String.split_on_char ' ' (String.trim (input_line stdin)))"
                  | "float array" ->
                    "Array.of_list (List.filter_map float_of_string_opt\n" ^
                    "    (String.split_on_char ' ' (String.trim (input_line stdin))))"
                  | "float" ->
                    "float_of_string (String.trim (input_line stdin))"
                  | "int" ->
                    "int_of_string (String.trim (input_line stdin))"
                  | _ -> "input_line stdin"
                in
                p "  let %s = %s in\n" vname read_expr
              end;
              vname
            in
            let arg_vars = List.map ensure_read op_inputs in
            let args = String.concat " " arg_vars in
            p "  let r_%s = %s %s in\n" fn fn args;
            p "  %s;\n" (ocaml_print_of k out_c (Printf.sprintf "r_%s" fn))
          ) structural_ops
        end
      end
    end;
    let filename = filename_from_graph k bridge_name in
    write_program buf filename
  end

let emit_math_programs (k : proof_graph) (bridge_name : string) : unit =
  let yukta_targets = Setu.yukta_of k bridge_name in
  let setu_sub_bridges = List.filter (Setu.is_setu k) yukta_targets in
  let op_sub_bridges   = List.filter (fun t ->
    not (Setu.is_setu k t) && yukta_operators k t <> []
  ) yukta_targets in
  let sub_bridges = setu_sub_bridges @ op_sub_bridges in
  if sub_bridges <> [] then
    List.iter (emit_bridge_program k) sub_bridges
  else
    emit_bridge_program k bridge_name

let emit_ocaml_from_graph (k : proof_graph) (content_words : string list) : unit =
  let unique_words = List.sort_uniq String.compare content_words in
  let has_ocaml_hint =
    List.exists (fun n ->
      n = "ocaml" || n = "ocaml-syntax" || n = "english-to-ocaml"
      || n = "ocaml-to-ocaml" || n = "physics-to-ocaml"
      || Setu.has_domain_sthita k n "domain-ocaml"
    ) unique_words in
  if has_ocaml_hint then begin
    let is_ocaml_operation name =
      (Setu.is_setu k name && List.mem "ocaml" (Setu.infer_outputs k name))
      || (Setu.has_domain_sthita k name "domain-ocaml"
          && Setu.infer_outputs k name <> []) in
    let direct_candidates = List.filter is_ocaml_operation unique_words in
    let content_set = Hashtbl.create 32 in
    List.iter (fun w -> Hashtbl.replace content_set w true) unique_words;
    let physics_terms_in_query = List.filter (fun w ->
      Setu.has_domain_sthita k w "domain-physics"
    ) unique_words in
    let physics_required = physics_terms_in_query <> [] in
    let math_terms_in_query = List.filter (fun w ->
      Setu.has_domain_sthita k w "domain-math"
    ) unique_words in
    let math_required = math_terms_in_query <> [] in
    let chemistry_terms_in_query = List.filter (fun w ->
      Setu.has_domain_sthita k w "domain-chemistry"
    ) unique_words in
    let chemistry_required = chemistry_terms_in_query <> [] in
    let inferred_candidates =
      if direct_candidates <> [] then []
      else Hashtbl.fold (fun name _ acc ->
        if not (is_ocaml_operation name) then acc
        else
          let inputs = Setu.infer_inputs k name in
          let outputs = Setu.infer_outputs k name in
          let matches_output = List.exists (fun o -> Hashtbl.mem content_set o) outputs in
          let has_math_input = List.exists (fun i ->
            Setu.has_domain_sthita k i "domain-math"
          ) inputs in
          let matches_physics =
            if not physics_required then true
            else List.exists (fun t ->
              List.mem t inputs || List.mem t outputs
            ) physics_terms_in_query in
          let has_arithmetic_yukta =
            yukta_operators k name <> [] in
          ignore has_arithmetic_yukta;
          let matches_math_query =
            if not math_required then true
            else yukta_operators k name <> []
              || List.exists (fun t ->
                  List.mem t inputs || List.mem t outputs
                 ) math_terms_in_query in
          let matches_math =
            if not math_required then true
            else has_math_input && matches_math_query in
          let has_chemistry_input = List.exists (fun i ->
            Setu.has_domain_sthita k i "domain-chemistry"
          ) inputs in
          let matches_chemistry =
            if not chemistry_required then true
            else has_chemistry_input
              || List.exists (fun t ->
                  List.mem t inputs || List.mem t outputs
                 ) chemistry_terms_in_query in
          if matches_output && matches_math && matches_physics && matches_chemistry
          then name :: acc else acc
      ) k.nodes [] in
    let operation_candidates =
      List.sort_uniq String.compare (direct_candidates @ inferred_candidates) in
    if operation_candidates <> [] then begin
      let ocaml_type_of raw_name =
        if Setu.has_domain_sthita k raw_name "domain-ocaml"
        then Setu.sanitize_ocaml_ident raw_name
        else "int"
      in
      ignore ocaml_type_of;
      let print_function op =
        match Hashtbl.find_opt k.nodes op with
        | None -> ()
        | Some _n ->
          let operators = yukta_operators k op in
          if operators <> [] then
            emit_math_programs k op
          else begin
            let inputs = Setu.infer_inputs k op in
            let outputs = Setu.infer_outputs k op in
            let output = match outputs with o :: _ -> o | [] -> "unit" in
            let fn_name = Setu.sanitize_ocaml_ident op in
            let args_sig = if inputs = [] then "()" else
              String.concat " " (List.map (fun i ->
                let x = Setu.sanitize_ocaml_ident i in
                Printf.sprintf "~(%s:%s)" x (ocaml_type_of i)
              ) inputs) in
            let ret_sig = if output = "unit" then "unit"
              else ocaml_type_of output in
            Printf.printf "  ocaml: let %s %s : %s = ...\n" fn_name args_sig ret_sig
          end
      in
      List.iter print_function operation_candidates
    end
  end

(* --- strudel mini-notation emission from graph structure --- *)

(* --- renderer voice layer ---
   reads from strudel.shabda flat keys: <relation>-sound, -octave, -gain, -speed
   shared by strudel emit, music_ir, and resonance_ir *)

type renderer_voice = {
  v_source  : string;
  v_label   : string;
  v_relation: visheshanam;
  v_targets : string list;
  v_notes   : string list;
  v_sound   : string;
  v_timbre  : string;   (* music_ir field — same concept as sound *)
  v_octave  : int;
  v_gain    : float;
  v_pan     : float;
  v_speed   : float;
  v_articulation : string;
}

let note_of_node (k : proof_graph) (name : string) (octave : int) : string =
  let pairs = Setu.read_shabda k "swara-to-strudel" in
  let ordered = ["shadja";"rishabha";"gandhara";"madhyama";"panchama";"dhaivata";"nishada"] in
  let note_names = List.filter_map (fun s -> Setu.shabda_get pairs s) ordered in
  match note_names with
  | [] -> Printf.sprintf "c%d" octave
  | names ->
    let arr = Array.of_list names in
    let idx = (Hashtbl.hash name land 0x7fffffff) mod (Array.length arr) in
    Printf.sprintf "%s%d" arr.(idx) octave

let satya_to_gain (satya : float) (energy_min : float) (energy_max : float) : float =
  energy_min +. satya *. (energy_max -. energy_min)

let build_voices (k : proof_graph) (name : string) : renderer_voice list =
  match Hashtbl.find_opt k.nodes name with
  | None -> []
  | Some n ->
    let strudel_pairs  = Setu.read_shabda k "strudel" in
    let music_pairs    = Setu.read_shabda k "music-ir" in
    let swara_pairs    = Setu.read_shabda k "swara-to-strudel" in
    let rir_pairs      = Setu.read_shabda k "resonance-ir" in
    let sg pairs key fb = match Setu.shabda_get pairs key with Some v -> v | None -> fb in
    let energy_min = float_of_string_opt (sg rir_pairs "energy-min" "0.1") |> Option.value ~default:0.1 in
    let energy_max = float_of_string_opt (sg rir_pairs "energy-max" "1.0") |> Option.value ~default:1.0 in
    let groups : (visheshanam, string list) Hashtbl.t = Hashtbl.create 9 in
    List.iter (fun e ->
      if e.source = name then begin
        let existing = match Hashtbl.find_opt groups e.relation with
          | Some xs -> xs | None -> [] in
        Hashtbl.replace groups e.relation (existing @ [e.target])
      end
    ) n.edges;
    let relation_order = [swarupa; abheda; sthita; janya; yukta; phala; kriya; siddha; drishthanta] in
    List.filter_map (fun rel ->
      match Hashtbl.find_opt groups rel with
      | None -> None
      | Some targets ->
        let targets = List.filter (fun t ->
          not (String.length t >= 7 && String.sub t 0 7 = "domain-")
        ) targets in
        if targets = [] then None
        else
          let rk = string_of_visheshanam rel in
          let sound  = sg strudel_pairs (rk ^ "-sound")  "" in
          let octave = int_of_string_opt (sg strudel_pairs (rk ^ "-octave") "4") |> Option.value ~default:4 in
          let role_gain = float_of_string_opt (sg strudel_pairs (rk ^ "-gain") "0.4") |> Option.value ~default:0.4 in
          let speed  = float_of_string_opt (sg strudel_pairs (rk ^ "-speed") "1.0") |> Option.value ~default:1.0 in
          if sound = "" then None
          else
            let timbre = sg music_pairs (rk ^ "-timbre") sound in
            let pan    = float_of_string_opt (sg music_pairs (rk ^ "-pan") "0.0") |> Option.value ~default:0.0 in
            let articulation = sg music_pairs (rk ^ "-articulation") "legato" in
            let base_gain = satya_to_gain n.satya energy_min energy_max in
            let final_gain = Float.min 1.0 (base_gain *. role_gain) in
            let notes = List.map (fun t ->
              match Setu.shabda_get swara_pairs (String.lowercase_ascii t) with
              | Some sn -> Printf.sprintf "%s%d" sn octave
              | None    -> note_of_node k t octave
            ) targets in
            Some {
              v_source   = name;
              v_label    = Printf.sprintf "%s -> %s [%s]"
                             name (english_of_visheshanam_from_graph k rel)
                             (String.concat ", " targets);
              v_relation = rel;
              v_targets  = targets;
              v_notes    = notes;
              v_sound    = sound;
              v_timbre   = timbre;
              v_octave   = octave;
              v_gain     = final_gain;
              v_pan      = pan;
              v_speed    = speed;
              v_articulation = articulation;
            }
    ) relation_order

let thaalam_context (k : proof_graph) (thaalam_opt : string option)
    : string option * string * int =
  (* returns (selected_thaalam_name, label, beats) *)
  let ss = Setu.read_shabda k "strudel-setu" in
  let sg key fb = match Setu.shabda_get ss key with Some v -> v | None -> fb in
  let selected = match thaalam_opt with Some t -> Some t | None -> thaalam_default k in
  let (label, beats) = match selected with
    | None ->
      ("none", int_of_string_opt (sg "beat-default" "8") |> Option.value ~default:8)
    | Some t ->
      match thaalam_cycle k t with
      | Some (lbl, b) -> (lbl, b)
      | None -> (t, int_of_string_opt (sg "beat-fallback" "8") |> Option.value ~default:8)
  in
  (selected, label, beats)

let emit_strudel_from_graph (k : proof_graph) (content_words : string list)
    (thaalam_opt : string option) : unit =
  let ss = Setu.read_shabda k "strudel-setu" in
  let sg key fb = match Setu.shabda_get ss key with Some v -> v | None -> fb in
  let rest        = sg "pattern-rest"  "~" in
  let stack_open  = sg "stack-open"    "stack(" in
  let stack_close = sg "stack-close"   ")" in
  let comment     = sg "comment"       "//" in
  let emit_header = sg "emit-header"   "graph->strudel" in
  let (_, thaalam_label, beats) = thaalam_context k thaalam_opt in
  let base_cpm = beats * 4 in
  let all_voices = List.concat_map (build_voices k) content_words in
  if all_voices = [] then ()
  else begin
    let section_open = sg "section-open" "--- strudel ---" in
    Printf.printf "\n  %s\n" section_open;
    Printf.printf "  %s %s\n" comment emit_header;
    Printf.printf "  %s thaalam: %s (%d beats per cycle)\n" comment thaalam_label beats;
    Printf.printf "  %s nodes: %s\n" comment (String.concat ", " content_words);
    Printf.printf "  %s voices: %d (one per edge-type group per node)\n\n"
      comment (List.length all_voices);
    let pattern_of_voice v =
      let n = List.length v.v_notes in
      if n = 0 then rest
      else if n = 1 then
        let note = List.hd v.v_notes in
        String.concat " " (List.init beats (fun i ->
          if i = 0 || i = beats / 2 then note else rest))
      else if n <= beats then
        String.concat " " (List.init beats (fun i ->
          if i < n then List.nth v.v_notes i else rest))
      else
        let per_beat = (n + beats - 1) / beats in
        String.concat " " (List.init beats (fun i ->
          let start = i * per_beat in
          let group = List.filteri (fun j _ -> j >= start && j < start + per_beat) v.v_notes in
          match group with [] -> rest | [x] -> x | xs -> "[" ^ String.concat " " xs ^ "]"))
    in
    Printf.printf "  %s\n" stack_open;
    let num_voices = List.length all_voices in
    List.iteri (fun i v ->
      let pattern = pattern_of_voice v in
      let cpm = int_of_float (float_of_int base_cpm *. v.v_speed) in
      let note_wrapper = sg "note-wrapper" "note(\"%s\")" in
      let wrapped = match String.split_on_char '%' note_wrapper with
        | [pre; sfx] when String.length sfx > 0 && sfx.[0] = 's' ->
          pre ^ pattern ^ String.sub sfx 1 (String.length sfx - 1)
        | _ -> note_wrapper
      in
      Printf.printf "    %s %s\n" comment v.v_label;
      Printf.printf "    %s\n" wrapped;
      Printf.printf "      .sound(\"%s\").gain(%.1f).cpm(%d)" v.v_sound v.v_gain cpm;
      if i < num_voices - 1 then Printf.printf ",\n\n" else Printf.printf "\n"
    ) all_voices;
    Printf.printf "  %s\n" stack_close;
    Printf.printf "\n  %s\n" (sg "section-close" "--- /strudel ---")
  end

(* escape for JSON — used by IR builders *)
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

(* --- IR builders — pure data, no printing ---
   build_music_ir: graph energy/relations -> structured timed voice+event data
   build_resonance_ir: graph satya/pass/flow -> animation dynamics data
   both read from their respective pratibimba setu nodes *)

let js_str s = "\"" ^ json_escape s ^ "\""
let js_float f = Printf.sprintf "%.4f" f
let js_int i = string_of_int i
let js_bool b = if b then "true" else "false"

let build_music_ir (k : proof_graph) (content_words : string list)
    (thaalam_opt : string option) (request_id : string) (session_id : string)
    (turn_id : string) : string =
  let mp = Setu.read_shabda k "music-ir" in
  let sg key fb = match Setu.shabda_get mp key with Some v -> v | None -> fb in
  let (_, _thaalam_label, beats) = thaalam_context k thaalam_opt in
  let bpm = int_of_string_opt (sg "thaalam-bpm" "96") |> Option.value ~default:96 in
  let ticks = int_of_string_opt (sg "ticks-per-beat" "24") |> Option.value ~default:24 in
  let all_voices = List.concat_map (build_voices k) content_words in
  (* deduplicate voices by voice_id = source-relation *)
  let seen = Hashtbl.create 16 in
  let unique_voices = List.filter (fun v ->
    let vid = v.v_source ^ "-" ^ string_of_visheshanam v.v_relation in
    if Hashtbl.mem seen vid then false
    else (Hashtbl.add seen vid true; true)
  ) all_voices in
  let buf = Buffer.create 512 in
  let a = Buffer.add_string buf in
  a "{\n";
  a (Printf.sprintf "  \"meta\": { \"request_id\": %s, \"session_id\": %s, \"turn_id\": %s,\n"
    (js_str request_id) (js_str session_id) (js_str turn_id));
  a (Printf.sprintf "    \"source_nodes\": [%s] },\n"
    (String.concat ", " (List.map js_str content_words)));
  a (Printf.sprintf "  \"timing\": { \"bpm\": %s, \"cycle_beats\": %s, \"ticks_per_beat\": %s },\n"
    (js_int bpm) (js_int beats) (js_int ticks));
  a "  \"voices\": [\n";
  List.iteri (fun i v ->
    let vid = js_str (v.v_source ^ "-" ^ string_of_visheshanam v.v_relation) in
    a (Printf.sprintf "    { \"voice_id\": %s, \"label\": %s, \"timbre\": %s,\n"
      vid (js_str v.v_label) (js_str v.v_timbre));
    a (Printf.sprintf "      \"gain\": %s, \"pan\": %s, \"octave\": %s, \"speed\": %s }"
      (js_float v.v_gain) (js_float v.v_pan) (js_int v.v_octave) (js_float v.v_speed));
    if i < List.length unique_voices - 1 then a ",\n" else a "\n"
  ) unique_voices;
  a "  ],\n";
  (* events: one event per note per voice, spread across ticks *)
  a "  \"events\": [\n";
  let all_events = List.concat_map (fun v ->
    List.mapi (fun i note ->
      let t_start = i * ticks in
      (t_start, ticks, v.v_source ^ "-" ^ string_of_visheshanam v.v_relation,
       note, v.v_gain, v.v_articulation, v.v_source)
    ) v.v_notes
  ) all_voices in
  List.iteri (fun i (t_start, t_dur, vid, pitch, vel, artic, tag) ->
    a (Printf.sprintf "    { \"t_start_tick\": %s, \"t_dur_tick\": %s, \"voice_id\": %s,\n"
      (js_int t_start) (js_int t_dur) (js_str vid));
    a (Printf.sprintf "      \"pitch\": %s, \"velocity\": %s, \"articulation\": %s, \"tags\": [%s] }"
      (js_str pitch) (js_float vel) (js_str artic) (js_str tag));
    if i < List.length all_events - 1 then a ",\n" else a "\n"
  ) all_events;
  a "  ],\n";
  a "  \"automation\": [],\n";
  a "  \"provenance\": [\n";
  List.iteri (fun i v ->
    List.iteri (fun j tgt ->
      let last = i = List.length all_voices - 1 && j = List.length v.v_targets - 1 in
      a (Printf.sprintf "    { \"source\": %s, \"relation\": %s, \"target\": %s }"
        (js_str v.v_source) (js_str (string_of_visheshanam v.v_relation)) (js_str tgt));
      if not last then a ",\n" else a "\n"
    ) v.v_targets
  ) all_voices;
  a "  ]\n}";
  Buffer.contents buf

let build_resonance_ir (k : proof_graph) (content_words : string list)
    (pass_groups : (int * anuvada_triple list) list)
    (thaalam_opt : string option) (request_id : string) (session_id : string)
    (turn_id : string) : string =
  let rp = Setu.read_shabda k "resonance-ir" in
  let sg key fb = match Setu.shabda_get rp key with Some v -> v | None -> fb in
  let (_, _thaalam_label, beats) = thaalam_context k thaalam_opt in
  let bpm   = int_of_string_opt (sg "thaalam-bpm" "96")   |> Option.value ~default:96 in
  let ticks = int_of_string_opt (sg "ticks-per-beat" "24") |> Option.value ~default:24 in
  let focus_threshold = float_of_string_opt (sg "focus-threshold" "0.75") |> Option.value ~default:0.75 in
  let energy_min = float_of_string_opt (sg "energy-min" "0.1") |> Option.value ~default:0.1 in
  let energy_max = float_of_string_opt (sg "energy-max" "1.0") |> Option.value ~default:1.0 in
  let breath    = sg "camera-breath"    "0.25" in
  let zoom_bias = sg "camera-zoom-bias" "0.12" in
  (* collect activated nodes from all passes *)
  let activated = List.sort_uniq String.compare
    (content_words @ List.concat_map (fun (_, ts) ->
      List.concat_map (fun t -> t.a_source_raw :: t.a_targets_raw) ts
    ) pass_groups) in
  (* accent pattern — read from setu, default to flat *)
  let accent_str = match thaalam_opt with
    | Some t ->
      let key = String.lowercase_ascii t ^ "-accent" in
      (match Setu.shabda_get rp key with
       | Some v -> v
       | None -> sg "adi-accent" "1.0 0.4 0.6 0.8 0.4 0.6 0.8 0.4")
    | None -> sg "adi-accent" "1.0 0.4 0.6 0.8 0.4 0.6 0.8 0.4"
  in
  let accent_floats = List.filter_map float_of_string_opt
    (String.split_on_char ' ' accent_str) in
  let buf = Buffer.create 512 in
  let a = Buffer.add_string buf in
  a "{\n";
  a (Printf.sprintf "  \"meta\": { \"request_id\": %s, \"session_id\": %s, \"turn_id\": %s,\n"
    (js_str request_id) (js_str session_id) (js_str turn_id));
  a (Printf.sprintf "    \"source_nodes\": [%s] },\n"
    (String.concat ", " (List.map js_str content_words)));
  a (Printf.sprintf "  \"timing\": { \"bpm\": %s, \"cycle_beats\": %s, \"ticks_per_beat\": %s,\n"
    (js_int bpm) (js_int beats) (js_int ticks));
  a (Printf.sprintf "    \"accent_pattern\": [%s] },\n"
    (String.concat ", " (List.map js_float accent_floats)));
  (* nodes *)
  a "  \"nodes\": [\n";
  List.iteri (fun i name ->
    let satya = match Hashtbl.find_opt k.nodes name with
      | Some n -> n.satya | None -> 0.1 in
    let energy = satya_to_gain satya energy_min energy_max in
    let rk = "swarupa" in
    let relevance = float_of_string_opt (sg (rk ^ "-relevance") "0.8")
      |> Option.value ~default:0.8 in
    let focus = energy >= focus_threshold in
    a (Printf.sprintf "    { \"node_id\": %s, \"energy\": %s, \"relevance\": %s"
      (js_str name) (js_float energy) (js_float relevance));
    if focus then a (Printf.sprintf ", \"focus\": %s" (js_bool focus));
    a " }";
    if i < List.length activated - 1 then a ",\n" else a "\n"
  ) activated;
  a "  ],\n";
  (* edges — from pass_groups triples *)
  let edges = List.concat_map (fun (_, ts) ->
    List.concat_map (fun t ->
      List.map (fun tgt -> (t.a_source_raw, t.a_relation, tgt)) t.a_targets_raw
    ) ts
  ) pass_groups in
  let edges = List.sort_uniq compare edges in
  a "  \"edges\": [\n";
  List.iteri (fun i (src, rel, tgt) ->
    let rk = string_of_visheshanam rel in
    let flow = float_of_string_opt (sg (rk ^ "-flow") "0.7") |> Option.value ~default:0.7 in
    let dir  = float_of_string_opt (sg (rk ^ "-direction") "0.7") |> Option.value ~default:0.7 in
    a (Printf.sprintf "    { \"source\": %s, \"target\": %s, \"flow\": %s, \"direction_bias\": %s }"
      (js_str src) (js_str tgt) (js_float flow) (js_float dir));
    if i < List.length edges - 1 then a ",\n" else a "\n"
  ) edges;
  a "  ],\n";
  (* events — one focus_shift per pass start *)
  a "  \"events\": [\n";
  let pass_start_kind = sg "pass-start-kind" "focus_shift" in
  List.iteri (fun i (pass_num, ts) ->
    let target = match ts with t :: _ -> t.a_source_raw | [] -> "" in
    if String.length target > 0 then begin
      let t_tick = (pass_num - 1) * beats * ticks in
      a (Printf.sprintf "    { \"t_tick\": %s, \"kind\": %s, \"target\": %s, \"strength\": %s }"
        (js_int t_tick) (js_str pass_start_kind) (js_str target) (js_float 0.8));
      if i < List.length pass_groups - 1 then a ",\n" else a "\n"
    end
  ) pass_groups;
  a "  ],\n";
  (* camera *)
  let center = match content_words with w :: _ -> w | [] -> "" in
  a (Printf.sprintf "  \"camera\": { \"center_node\": %s, \"zoom_bias\": %s, \"breath\": %s }\n"
    (js_str center) zoom_bias breath);
  a "}";
  Buffer.contents buf

let emit_ir (k : proof_graph) (content_words : string list)
    (pass_groups : (int * anuvada_triple list) list)
    (thaalam_opt : string option) : unit =
  if content_words = [] then ()
  else begin
    let req = "anuvada" and ses = "session" and trn = "turn" in
    let music = build_music_ir k content_words thaalam_opt req ses trn in
    let res   = build_resonance_ir k content_words pass_groups thaalam_opt req ses trn in
    Printf.printf "\n  --- music_ir ---\n%s\n" music;
    Printf.printf "\n  --- resonance_ir ---\n%s\n" res
  end







(* --- query result type ---
   single source of truth consumed by both stdout and socket modes *)

type query_result = {
  qr_answer_text  : string;                              (* rendered spiral output *)
  qr_steps        : (int * anuvada_triple list) list;    (* pass_groups *)
  qr_next_qs      : string list;                         (* thread questions *)
  qr_content_words: string list;                         (* resolved seed nodes *)
  qr_thaalam      : string option;
  qr_music_ir     : string;                              (* JSON string *)
  qr_resonance_ir : string;                              (* JSON string *)
  qr_strudel      : string;                              (* strudel mini-notation *)
  qr_passes       : int;
  qr_connections  : int;
  qr_confidence   : float;                               (* top node satya *)
}

(* emit_strudel_to_string — same as emit_strudel_from_graph but returns string *)
let emit_strudel_to_string (k : proof_graph) (content_words : string list)
    (thaalam : string option) : string =
  let buf = Buffer.create 256 in
  let voices = List.concat_map (fun w ->
    build_voices k w
  ) content_words in
  let strudel_map = Setu.read_shabda k "strudel" in
  let sg key fb = match Setu.shabda_get strudel_map key with Some v -> v | None -> fb in
  let rhythm = match thaalam with
    | Some t -> sg (String.lowercase_ascii t ^ "-rhythm") (sg "default-rhythm" "x x x x")
    | None -> sg "default-rhythm" "x x x x"
  in
  if voices <> [] then begin
    Buffer.add_string buf "stack(\n";
    List.iteri (fun i v ->
      let notes = String.concat " " v.v_notes in
      Buffer.add_string buf
        (Printf.sprintf "  note(\"%s\").sound(\"%s\").gain(%.2f)"
          notes v.v_sound v.v_gain);
      if i < List.length voices - 1 then Buffer.add_string buf ",\n"
      else Buffer.add_char buf '\n'
    ) voices;
    Buffer.add_string buf (Printf.sprintf ").cpm(%s)" rhythm)
  end else
    Buffer.add_string buf (Printf.sprintf "silence // no nodes resolved\n// rhythm: %s" rhythm);
  Buffer.contents buf

(* anuvada_query — pure: takes a question, returns a structured result.
   both stdout mode and socket mode call this; they differ only in how they render it. *)
let anuvada_query ?(max_passes = 2) ?thaalam ?(sahaja = false)
    ?(request_id = "anuvada") ?(session_id = "session") ?(turn_id = "turn")
    (k : proof_graph) (sentence : string) : query_result =
  let _ = sahaja in
  let spaced_math_ops (s : string) : string =
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
  let expand_possessive words =
    List.concat_map (fun w ->
      if String.length w > 2 then
        let len = String.length w in
        if len >= 3 && String.sub w (len - 2) 2 = "'s" then
          [String.sub w 0 (len - 2); "'s"]
        else [w]
      else [w]
    ) words
  in
  let words = expand_possessive words in
  let clean w =
    if w = "'s" then w
    else begin
      let w = String.lowercase_ascii w in
      let len = String.length w in
      let buf = Buffer.create len in
      String.iteri (fun i c ->
        if (c >= 'a' && c <= 'z') || (c >= '0' && c <= '9')
           || c = '-' || c = '+' || c = '*' || c = '/' || c = '=' then
          Buffer.add_char buf c
        else if c = '.' then begin
          (* preserve '.' between digits — floats like 9.8 *)
          let prev_digit = i > 0 && w.[i-1] >= '0' && w.[i-1] <= '9' in
          let next_digit = i < len - 1 && w.[i+1] >= '0' && w.[i+1] <= '9' in
          if prev_digit && next_digit then Buffer.add_char buf c
        end
      ) w;
      Buffer.contents buf
    end
  in
  let clean_words ws =
    let ws = List.map clean ws in
    List.filter (fun w -> String.length w > 0) ws
  in
  let words = clean_words words in
  let classified = List.map (fun w -> (w, Setu.classify_token k w)) words in
  let content_words = List.filter_map (fun (_, role) ->
    match role with Setu.Content name -> Some name | _ -> None
  ) classified in
  (* extract context anchor: content word immediately following a Sthita ("in") token
     e.g. "polarity in wave" → context_anchor = Some "wave"
           "shiva-shakti in dna" → context_anchor = Some "dna"
     works for any node, not just domains *)
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
  let (pass_groups_final, total_passes) =
    if content_words <> [] then
      avrti_anuvada k content_words max_passes
    else
      ([], 0)
  in
  let answer_buf =
    if content_words <> []
    then render_pass_groups_simple ~context:context_anchor k pass_groups_final
    else ""
  in
  let total_triples = List.fold_left (fun acc (_, ts) ->
    acc + List.length ts) 0 pass_groups_final in
  let music_ir = if content_words <> [] then
    build_music_ir k content_words thaalam request_id session_id turn_id
  else "{}" in
  let resonance_ir = if content_words <> [] then
    build_resonance_ir k content_words pass_groups_final thaalam request_id session_id turn_id
  else "{}" in
  let strudel = emit_strudel_to_string k content_words thaalam in
  let confidence = List.fold_left (fun best w ->
    match Hashtbl.find_opt k.nodes w with
    | Some n -> if n.satya > best then n.satya else best
    | None -> best
  ) 0.0 content_words in
  { qr_answer_text   = answer_buf
  ; qr_steps         = pass_groups_final
  ; qr_next_qs       = []
  ; qr_content_words = content_words
  ; qr_thaalam       = thaalam
  ; qr_music_ir      = music_ir
  ; qr_resonance_ir  = resonance_ir
  ; qr_strudel       = strudel
  ; qr_passes        = total_passes
  ; qr_connections   = total_triples
  ; qr_confidence    = confidence
  }

(* --- output flags ---
   controls which sections are printed. default: reasoning only.
   inline query syntax:  "what is avrti +strudel +resonance"
   session flag:         --show strudel,music,resonance
   socket field:         "show": ["resonance","music"]

   flags: reasoning (always on), strudel, music, resonance, prayoga, all *)

type output_flags = {
  show_strudel   : bool;
  show_music     : bool;
  show_resonance : bool;
  show_prayoga   : bool;
}

let flags_default = {
  show_strudel   = false;
  show_music     = false;
  show_resonance = false;
  show_prayoga   = false;
}

let flags_all = {
  show_strudel   = true;
  show_music     = true;
  show_resonance = true;
  show_prayoga   = true;
}

(* parse +flag tokens out of a query string, return (clean_query, flags) *)
let parse_inline_flags ?(base = flags_default) (sentence : string) : string * output_flags =
  let tokens = String.split_on_char ' ' sentence in
  let flags = ref base in
  let rest = List.filter (fun t ->
    match String.lowercase_ascii (String.trim t) with
    | "+strudel"   -> flags := { !flags with show_strudel   = true }; false
    | "+music"     -> flags := { !flags with show_music     = true }; false
    | "+resonance" -> flags := { !flags with show_resonance = true }; false
    | "+prayoga"   -> flags := { !flags with show_prayoga   = true }; false
    | "+all"       -> flags := flags_all; false
    | _            -> true
  ) tokens in
  (String.concat " " (List.filter (fun s -> String.length (String.trim s) > 0) rest), !flags)

(* parse --show csv string into flags, e.g. "strudel,music,resonance" *)
let flags_of_show_string ?(base = flags_default) (s : string) : output_flags =
  let parts = String.split_on_char ',' s in
  List.fold_left (fun f p ->
    match String.trim (String.lowercase_ascii p) with
    | "strudel"   -> { f with show_strudel   = true }
    | "music"     -> { f with show_music     = true }
    | "resonance" -> { f with show_resonance = true }
    | "prayoga"   -> { f with show_prayoga   = true }
    | "all"       -> flags_all
    | _           -> f
  ) base parts

(* anuvada: parse an English sentence, resolve through graph, output understanding.
   thin wrapper over anuvada_query — same result, rendered to stdout. *)
let anuvada ?(max_passes = 2) ?thaalam ?(sahaja = false) ?(flags = flags_default) (k : proof_graph) (sentence : string) : unit =
  let (clean_sentence, flags) = parse_inline_flags ~base:flags sentence in
  let as_ = Setu.read_shabda k "anuvada-setu" in
  let ag key fallback = match Setu.shabda_get as_ key with Some v -> v | None -> fallback in
  let r = anuvada_query ~max_passes ?thaalam ~sahaja k clean_sentence in
  Printf.printf "%s\n" (ag "header" "--- reasoning (anuvada) ---");
  Printf.printf "  %s %s\n" (ag "input-label" "input:") clean_sentence;
  Printf.printf "  %s\n" (ag "understood-label" "understood:");
  List.iter (fun w ->
    Printf.printf "    [%s] → %s\n" w (ag "node-label" "node")
  ) r.qr_content_words;
  if r.qr_answer_text <> "" then
    print_string r.qr_answer_text;
  if flags.show_prayoga then
    emit_ocaml_from_graph k r.qr_content_words;
  if flags.show_strudel then
    emit_strudel_from_graph k r.qr_content_words thaalam;
  if r.qr_content_words <> [] then begin
    if flags.show_music     then Printf.printf "\n  --- music_ir ---\n%s\n" r.qr_music_ir;
    if flags.show_resonance then Printf.printf "\n  --- resonance_ir ---\n%s\n" r.qr_resonance_ir
  end;
  Printf.printf "%s\n%!" (ag "separator" "---")

(* sthiti — human-readable state *)
let print (k : proof_graph) : unit =
  let nodes = Hashtbl.fold (fun _ n acc -> n :: acc) k.nodes [] in
  let nodes = List.sort (fun a b -> compare b.satya a.satya) nodes in
  Printf.printf "--- space (akasham): %d nodes, %d edges ---\n"
    (List.length nodes) (List.length !(k.all_edges));
  List.iter (fun n ->
    let edge_count = List.length n.edges in
    let in_deg = in_degree k n.name in
    let sloka_count = List.length n.slokas in
    Printf.printf "[%s] satya=%.3f edges=%d cited=%d slokas=%d\n"
      n.name n.satya edge_count in_deg sloka_count;
    List.iter (fun s ->
      Printf.printf "  \"%s\"\n" s
    ) n.slokas
  ) nodes;
  Printf.printf "---\n%!"

(* pravaha — JSON output for LLM to read *)
let pravaha (k : proof_graph) : unit =
  let nodes = Hashtbl.fold (fun _ n acc -> n :: acc) k.nodes [] in
  let nodes = List.sort (fun a b -> String.compare a.name b.name) nodes in
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
    let cited_by = in_degree k n.name in
    Printf.printf "    {\n";
    Printf.printf "      \"name\": \"%s\",\n" (json_escape n.name);
    Printf.printf "      \"layer\": \"%s\",\n" (json_escape n.layer);
    Printf.printf "      \"satya\": %.4f,\n" n.satya;
    Printf.printf "      \"slokas\": [%s],\n" slokas_json;
    Printf.printf "      \"edges\": [%s],\n" edges_json;
    Printf.printf "      \"cited_by\": %d\n" cited_by;
    if i < n_nodes - 1
    then Printf.printf "    },\n"
    else Printf.printf "    }\n"
  ) nodes;
  Printf.printf "  ]\n";
  Printf.printf "}\n%!"
