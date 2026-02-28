(* vector — root: taranga *)
let dot_product : float list -> float list -> float = fun a b -> List.fold_left2 (fun acc x y -> acc +. x *. y) 0.0 a b
