(* arithmetic-to-ocaml — root: anuvada *)
type operator = Divide | Minus | Plus | Times
let eval ~(a:int) ~(b:int) ~(op:operator) : int =
  match op with
  | Divide -> a / b
  | Minus -> a - b
  | Plus -> a + b
  | Times -> a * b
let operator_of_symbol s = match s with
  | "/" -> Some Divide
  | "-" -> Some Minus
  | "+" -> Some Plus
  | "*" -> Some Times
  | _ -> None
let calculate expr =
  match String.split_on_char ' ' (String.trim expr) with
  | [a_s; op_s; b_s] ->
    (match int_of_string_opt a_s, int_of_string_opt b_s, operator_of_symbol op_s with
     | Some a, Some b, Some op -> Some (eval ~a ~b ~op)
     | _ -> None)
  | _ -> None
let () =
  print_string "arithmetic: "; flush stdout;
  let ahara = input_line stdin in
  (match calculate ahara with
  | Some r -> Printf.printf "= %d\n" r
  | None -> print_endline "could not parse")
