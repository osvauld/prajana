(* om_edit.ml — combined disk + graph operations.
   each operation: validate → write to disk → update live graph → re-materialize CSR.
   disk is the source of truth. graph is a materialized view.

   pattern for node edits:
     1. edit file on disk (om_writer)
     2. re-parse file (om_parser) — this is the safest way to get correct edges
     3. replace node in graph (proof_graph.replace_node)
     4. re-init satya + re-materialize CSR *)

open Proof_graph

(* ---- result type ---- *)

type edit_result =
  | Ok of string   (* success message *)
  | Err of string  (* error message *)

(* ---- helpers ---- *)

(* re-parse a file and replace the node in the graph *)
let reparse_and_replace (k : proof_graph) (path : string) : edit_result =
  let known_names = Hashtbl.fold (fun name _ acc -> name :: acc) k.nodes [] in
  match Om_parser.parse_file known_names path with
  | None -> Err (Printf.sprintf "re-parse failed: %s" path)
  | Some n ->
    replace_node k n;
    init_satya k;
    materialize_csr k;
    Ok n.name

(* find the file path for a node name *)
let path_of_node (k : proof_graph) (name : string) : string option =
  (* nodes don't store their path — we need to find it.
     search kosha_root and search_dirs for a file containing this node. *)
  let dirs = !(k.search_dirs) in
  let rec find_in_dirs = function
    | [] -> None
    | dir :: rest ->
      let files = Om_parser.om_files_recursive dir in
      let found = List.fold_left (fun acc path ->
        match acc with
        | Some _ -> acc
        | None ->
          try
            let ic = open_in path in
            let result = ref None in
            (try while true do
              let line = input_line ic in
              match Om_parser.parse_node_header line with
              | Some (_layer, n) when n = name ->
                result := Some path; raise Exit
              | _ -> ()
            done with Exit | End_of_file -> ());
            close_in ic;
            !result
          with _ -> None
      ) None files in
      (match found with
       | Some p -> Some p
       | None -> find_in_dirs rest)
  in
  find_in_dirs dirs

(* ---- node operations ---- *)

(* create a new .om node: write file + join into graph *)
let create_node (k : proof_graph) (path : string) (layer : string) (name : string)
    (comments : (string option * string) list)
    (slokas : string list) (shabda : string) : edit_result =
  if Sys.file_exists path then
    Err (Printf.sprintf "file already exists: %s" path)
  else if Hashtbl.mem k.nodes name then
    Err (Printf.sprintf "node already exists in graph: %s" name)
  else begin
    Om_writer.create_om path layer name comments slokas shabda;
    reparse_and_replace k path
  end

(* add a sloka to an existing node *)
let add_sloka (k : proof_graph) (name : string) (sloka : string) : edit_result =
  match path_of_node k name with
  | None -> Err (Printf.sprintf "node not found: %s" name)
  | Some path ->
    Om_writer.add_sloka path sloka;
    reparse_and_replace k path

(* remove a sloka from an existing node *)
let remove_sloka (k : proof_graph) (name : string) (sloka : string) : edit_result =
  match path_of_node k name with
  | None -> Err (Printf.sprintf "node not found: %s" name)
  | Some path ->
    Om_writer.remove_sloka path sloka;
    reparse_and_replace k path

(* update shabda on a node *)
let set_shabda (k : proof_graph) (name : string) (shabda : string) : edit_result =
  match path_of_node k name with
  | None -> Err (Printf.sprintf "node not found: %s" name)
  | Some path ->
    Om_writer.set_shabda path shabda;
    reparse_and_replace k path

(* delete a node: remove file + remove from graph *)
let delete_node (k : proof_graph) (name : string) : edit_result =
  match path_of_node k name with
  | None -> Err (Printf.sprintf "node not found: %s" name)
  | Some path ->
    Om_writer.delete_file path;
    remove_node k name;
    init_satya k;
    materialize_csr k;
    Ok name

(* add a single edge: compose sloka text + write to source file + reparse *)
let add_edge (k : proof_graph) (source : string) (target : string)
    (relation : string) : edit_result =
  match path_of_node k source with
  | None -> Err (Printf.sprintf "source node not found: %s" source)
  | Some path ->
    let sloka = Printf.sprintf "%s-%s" target relation in
    Om_writer.add_sloka path sloka;
    reparse_and_replace k path

(* remove a single edge: find and remove matching sloka + reparse *)
let remove_edge (k : proof_graph) (source : string) (target : string)
    (relation : string) : edit_result =
  match path_of_node k source with
  | None -> Err (Printf.sprintf "source node not found: %s" source)
  | Some path ->
    (* the sloka text is "target-relation" — remove it *)
    let sloka = Printf.sprintf "%s-%s" target relation in
    Om_writer.remove_sloka path sloka;
    reparse_and_replace k path

(* ---- comment operations ---- *)

(* set a typed comment on a node *)
let set_comment (k : proof_graph) (name : string) (prefix : string)
    (text : string) : edit_result =
  ignore k;  (* comments don't affect graph — but we validate node exists *)
  match path_of_node k name with
  | None -> Err (Printf.sprintf "node not found: %s" name)
  | Some path ->
    Om_writer.set_comment path prefix text;
    Ok name

(* remove a typed comment from a node *)
let remove_comment (k : proof_graph) (name : string) (prefix : string) : edit_result =
  match path_of_node k name with
  | None -> Err (Printf.sprintf "node not found: %s" name)
  | Some path ->
    Om_writer.remove_comment path prefix;
    Ok name

(* add a free-form comment to a node *)
let add_comment (k : proof_graph) (name : string) (text : string) : edit_result =
  match path_of_node k name with
  | None -> Err (Printf.sprintf "node not found: %s" name)
  | Some path ->
    Om_writer.add_freeform_comment path text;
    Ok name

(* ---- shabda file operations ---- *)

let add_shabda_entry (_k : proof_graph) (path : string) (word : string)
    (abheda : string list) (yukta : string list) : edit_result =
  Om_writer.add_shabda_entry path word abheda yukta;
  Ok word

let remove_shabda_entry (_k : proof_graph) (path : string)
    (word : string) : edit_result =
  Om_writer.remove_shabda_entry path word;
  Ok word

let update_shabda_entry (_k : proof_graph) (path : string) (word : string)
    (abheda : string list) (yukta : string list) : edit_result =
  Om_writer.update_shabda_entry path word abheda yukta;
  Ok word

(* ---- tantra operations ---- *)

let write_tantra (_k : proof_graph) (path : string) (source : string) : edit_result =
  Om_writer.write_tantra path source;
  Ok path
