(* matrix: float array array — root is vrnda-ganita (group-math/linear algebra) *)
type matrix = float array array
let dot_product (a:float array) (b:float array) : float =
  Array.fold_left ( +. ) 0.0 (Array.map2 ( *. ) a b)
let parse_row (s:string) : float array =
  Array.of_list (List.filter_map float_of_string_opt
    (String.split_on_char ' ' (String.trim s)))
let read_matrix (prompt:string) (rows:int) : matrix =
  print_string prompt; flush stdout;
  Array.init rows (fun _ -> parse_row (input_line stdin))
let print_matrix (m:matrix) : unit =
  Array.iter (fun row ->
    print_endline (String.concat " "
      (Array.to_list (Array.map string_of_float row)))) m
let () =
  print_string "matrix size: ";
  flush stdout;
  print_string "rows: "; flush stdout;
  let n = int_of_string (String.trim (input_line stdin)) in
  let a = read_matrix "matrix A (one row per line):\n" n in
  let b = read_matrix "matrix B (one row per line):\n" n in
  ignore (a, b); print_endline "no ops defined"
