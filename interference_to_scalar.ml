(* dot-product — root: sparsha *)
let matrix_multiplication : float list -> float list -> float array array = fun a b ->
  let n = List.length a in
  let dot r c = List.fold_left2 (fun acc x y -> acc +. x *. y) 0.0 r c in
  List.init n (fun i -> List.init n (fun j -> dot (List.nth a i) (List.map (fun r -> List.nth r j) b)))
