(* physics-to-ocaml — root: anuvada *)
let force_apply : float list -> float list -> string = fun vec scalar -> List.map (fun x -> x /. scalar) vec
let velocity_step : float list -> float list -> string = fun v a -> List.map2 (fun vi ai -> vi +. ai) v a
let () =
  print_string "force: "; flush stdout;
  let force = List.filter_map float_of_string_opt
    (String.split_on_char ' ' (String.trim (input_line stdin))) in
  print_string "mass: "; flush stdout;
  let mass = float_of_string (String.trim (input_line stdin)) in
  let r_force_apply = force_apply force mass in
  Printf.printf "%d\n" r_force_apply;
  print_string "acceleration: "; flush stdout;
  let acceleration = List.filter_map float_of_string_opt
    (String.split_on_char ' ' (String.trim (input_line stdin))) in
  print_string "velocity: "; flush stdout;
  let velocity = List.filter_map float_of_string_opt
    (String.split_on_char ' ' (String.trim (input_line stdin))) in
  let r_velocity_step = velocity_step acceleration velocity in
  Printf.printf "%d\n" r_velocity_step;
