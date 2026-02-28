(* matrix-to-ocaml — root: anuvada *)
let matrix_multiplication : float list -> string -> float array array = fun a b ->
  let ra = Array.length a in
  let cb = Array.length b.(0) in
  let ca = Array.length a.(0) in
  let dot r c = Array.fold_left ( +. ) 0.0 (Array.map2 ( *. ) r c) in
  Array.init ra (fun i ->
    Array.init cb (fun j ->
      dot a.(i) (Array.init ca (fun k -> b.(k).(j)))))
let () =
  print_string "vector: "; flush stdout;
  let vector = List.filter_map float_of_string_opt
    (String.split_on_char ' ' (String.trim (input_line stdin))) in
  print_string "vrnda-ganita: "; flush stdout;
  let vrnda_ganita = input_line stdin in
  let r_matrix_multiplication = matrix_multiplication vector vrnda_ganita in
  Array.iter (fun row ->
    print_endline (String.concat " " (Array.to_list (Array.map string_of_float row)))
  ) r_matrix_multiplication;
