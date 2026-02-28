(* vector-to-ocaml — root: anuvada *)
let dot_product : float list -> float = fun a b -> List.fold_left2 (fun acc x y -> acc +. x *. y) 0.0 a b
let () =
  print_string "vector: "; flush stdout;
  let vector = List.filter_map float_of_string_opt
    (String.split_on_char ' ' (String.trim (input_line stdin))) in
  let r_dot_product = dot_product vector in
  Printf.printf "%g\n" r_dot_product;
