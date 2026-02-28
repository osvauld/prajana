(* physics-to-ocaml — root: anuvada *)
let force_apply : float list -> float -> float list = fun vec scalar -> List.map (fun x -> x /. scalar) vec
let position_step : float list -> float list -> float list = fun v a -> List.map2 (fun vi ai -> vi +. ai) v a
let velocity_step : float list -> float list -> float list = fun v a -> List.map2 (fun vi ai -> vi +. ai) v a
let () =
  print_string "force: "; flush stdout;
  let force = List.filter_map float_of_string_opt
    (String.split_on_char ' ' (String.trim (input_line stdin))) in
  print_string "mass: "; flush stdout;
  let mass = float_of_string (String.trim (input_line stdin)) in
  let r_force_apply = force_apply force mass in
  print_endline (String.concat " " (List.map string_of_float r_force_apply));
  print_string "displacement: "; flush stdout;
  let displacement = List.filter_map float_of_string_opt
    (String.split_on_char ' ' (String.trim (input_line stdin))) in
  print_string "velocity: "; flush stdout;
  let velocity = List.filter_map float_of_string_opt
    (String.split_on_char ' ' (String.trim (input_line stdin))) in
  let r_position_step = position_step displacement velocity in
  print_endline (String.concat " " (List.map string_of_float r_position_step));
  print_string "acceleration: "; flush stdout;
  let acceleration = List.filter_map float_of_string_opt
    (String.split_on_char ' ' (String.trim (input_line stdin))) in
  let r_velocity_step = velocity_step acceleration velocity in
  print_endline (String.concat " " (List.map string_of_float r_velocity_step));
