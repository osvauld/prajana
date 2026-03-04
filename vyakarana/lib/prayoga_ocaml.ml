let has seeds walk name =
  List.mem name seeds || List.mem name walk

let iteration_form seeds walk =
  if has seeds walk "vibhajana" || has seeds walk "milan" || has seeds walk "vruksha" then `Recursive
  else if has seeds walk "dhruva" then `Recursive
  else `Imperative

let data_form seeds walk =
  if has seeds walk "vibhajana" || has seeds walk "milan" || has seeds walk "dhruva" then `List
  else `Array

let selection_form seeds walk =
  if has seeds walk "laghu" || has seeds walk "chaya" then `Minimum
  else if has seeds walk "dhruva" then `Pivot
  else if has seeds walk "mula" then `Root
  else `Compare

let combination_form seeds walk =
  if has seeds walk "milan" then `Merge
  else if has seeds walk "pravesa" then `Insert
  else if has seeds walk "vivartana" then `Swap
  else `None

let termination_form seeds walk =
  if has seeds walk "viraam" || has seeds walk "kshaya-rahita" then `Stable
  else `Fixed

let compose_computation seeds walk input =
  let iter = iteration_form seeds walk in
  let data = data_form seeds walk in
  let sel = selection_form seeds walk in
  let comb = combination_form seeds walk in
  let term = termination_form seeds walk in

  Printf.printf "(* iteration: %s | data: %s | selection: %s | combination: %s | termination: %s *)\n"
    (match iter with `Recursive -> "recursive" | `Imperative -> "imperative")
    (match data with `List -> "list" | `Array -> "array")
    (match sel with `Minimum -> "minimum" | `Pivot -> "pivot" | `Root -> "root" | `Compare -> "compare-adjacent")
    (match comb with `Merge -> "merge" | `Insert -> "insert" | `Swap -> "swap" | `None -> "none")
    (match term with `Stable -> "stable-pass" | `Fixed -> "fixed-passes");
  Printf.printf "\n";

  (match iter, data, sel, comb with
  | `Imperative, `Array, `Compare, `Swap ->
    (match term with
    | `Stable ->
      Printf.printf "let order arr =\n";
      Printf.printf "  let n = Array.length arr in\n";
      Printf.printf "  let changed = ref true in\n";
      Printf.printf "  while !changed do\n";
      Printf.printf "    changed := false;\n";
      Printf.printf "    for i = 0 to n - 2 do\n";
      Printf.printf "      if arr.(i) > arr.(i + 1) then begin\n";
      Printf.printf "        let tmp = arr.(i) in\n";
      Printf.printf "        arr.(i) <- arr.(i + 1);\n";
      Printf.printf "        arr.(i + 1) <- tmp;\n";
      Printf.printf "        changed := true\n";
      Printf.printf "      end\n";
      Printf.printf "    done\n";
      Printf.printf "  done;\n";
      Printf.printf "  arr\n"
    | `Fixed ->
      Printf.printf "let order arr =\n";
      Printf.printf "  let n = Array.length arr in\n";
      Printf.printf "  for i = 0 to n - 2 do\n";
      Printf.printf "    for j = 0 to n - i - 2 do\n";
      Printf.printf "      if arr.(j) > arr.(j + 1) then begin\n";
      Printf.printf "        let tmp = arr.(j) in\n";
      Printf.printf "        arr.(j) <- arr.(j + 1);\n";
      Printf.printf "        arr.(j + 1) <- tmp\n";
      Printf.printf "      end\n";
      Printf.printf "    done\n";
      Printf.printf "  done;\n";
      Printf.printf "  arr\n")

  | `Imperative, `Array, `Minimum, (`Swap | `None) ->
    Printf.printf "let order arr =\n";
    Printf.printf "  let n = Array.length arr in\n";
    Printf.printf "  for i = 0 to n - 2 do\n";
    Printf.printf "    let min_i = ref i in\n";
    Printf.printf "    for j = i + 1 to n - 1 do\n";
    Printf.printf "      if arr.(j) < arr.(!min_i) then min_i := j\n";
    Printf.printf "    done;\n";
    Printf.printf "    if !min_i <> i then begin\n";
    Printf.printf "      let tmp = arr.(i) in\n";
    Printf.printf "      arr.(i) <- arr.(!min_i);\n";
    Printf.printf "      arr.(!min_i) <- tmp\n";
    Printf.printf "    end\n";
    Printf.printf "  done;\n";
    Printf.printf "  arr\n"

  | `Imperative, `Array, `Compare, `Insert ->
    Printf.printf "let order arr =\n";
    Printf.printf "  let n = Array.length arr in\n";
    Printf.printf "  for i = 1 to n - 1 do\n";
    Printf.printf "    let key = arr.(i) in\n";
    Printf.printf "    let j = ref (i - 1) in\n";
    Printf.printf "    while !j >= 0 && arr.(!j) > key do\n";
    Printf.printf "      arr.(!j + 1) <- arr.(!j);\n";
    Printf.printf "      decr j\n";
    Printf.printf "    done;\n";
    Printf.printf "    arr.(!j + 1) <- key\n";
    Printf.printf "  done;\n";
    Printf.printf "  arr\n"

  | `Recursive, `List, (`Compare | `Minimum), `Merge ->
    Printf.printf "let rec join a b =\n";
    Printf.printf "  match a, b with\n";
    Printf.printf "  | [], x | x, [] -> x\n";
    Printf.printf "  | h1 :: t1, h2 :: _ ->\n";
    Printf.printf "    if h1 <= h2 then h1 :: join t1 b\n";
    Printf.printf "    else h2 :: join a (List.tl b)\n";
    Printf.printf "\n";
    Printf.printf "let rec order = function\n";
    Printf.printf "  | ([] | [_]) as x -> x\n";
    Printf.printf "  | lst ->\n";
    Printf.printf "    let n = List.length lst / 2 in\n";
    Printf.printf "    let left  = List.filteri (fun i _ -> i < n) lst in\n";
    Printf.printf "    let right = List.filteri (fun i _ -> i >= n) lst in\n";
    Printf.printf "    join (order left) (order right)\n"

  | `Recursive, `List, `Pivot, _ ->
    Printf.printf "let rec order = function\n";
    Printf.printf "  | [] -> []\n";
    Printf.printf "  | dhruva :: rest ->\n";
    Printf.printf "    let before = List.filter (fun x -> x <= dhruva) rest in\n";
    Printf.printf "    let after  = List.filter (fun x -> x > dhruva) rest in\n";
    Printf.printf "    order before @ [dhruva] @ order after\n"

  | `Recursive, `Array, `Root, (`Swap | `None) ->
    Printf.printf "let restore arr n i =\n";
    Printf.printf "  let root = ref i in\n";
    Printf.printf "  let running = ref true in\n";
    Printf.printf "  while !running do\n";
    Printf.printf "    let l = 2 * !root + 1 and r = 2 * !root + 2 in\n";
    Printf.printf "    let largest = ref !root in\n";
    Printf.printf "    if l < n && arr.(l) > arr.(!largest) then largest := l;\n";
    Printf.printf "    if r < n && arr.(r) > arr.(!largest) then largest := r;\n";
    Printf.printf "    if !largest <> !root then begin\n";
    Printf.printf "      let tmp = arr.(!root) in\n";
    Printf.printf "      arr.(!root) <- arr.(!largest);\n";
    Printf.printf "      arr.(!largest) <- tmp;\n";
    Printf.printf "      root := !largest\n";
    Printf.printf "    end else running := false\n";
    Printf.printf "  done\n";
    Printf.printf "\n";
    Printf.printf "let order arr =\n";
    Printf.printf "  let n = Array.length arr in\n";
    Printf.printf "  for i = n / 2 - 1 downto 0 do restore arr n i done;\n";
    Printf.printf "  for i = n - 1 downto 1 do\n";
    Printf.printf "    let tmp = arr.(0) in\n";
    Printf.printf "    arr.(0) <- arr.(i);\n";
    Printf.printf "    arr.(i) <- tmp;\n";
    Printf.printf "    restore arr i 0\n";
    Printf.printf "  done;\n";
    Printf.printf "  arr\n"

  | _ ->
    Printf.printf "(* combination of primitives not yet composable: %s *)\n" (String.concat " + " seeds)
  );

  if String.length input > 0 then begin
    (match data with
    | `Array ->
      let arr_input = String.concat "; " (String.split_on_char ' ' (String.trim input)) in
      Printf.printf "\nlet () =\n";
      Printf.printf "  let result = order [| %s |] in\n" arr_input;
      Printf.printf "  Array.iter (fun x -> print_int x; print_char ' ') result;\n";
      Printf.printf "  print_newline ()\n"
    | `List ->
      Printf.printf "\nlet () =\n";
      Printf.printf "  let result = order [%s] in\n" (String.concat "; " (String.split_on_char ' ' (String.trim input)));
      Printf.printf "  List.iter (fun x -> print_int x; print_char ' ') result;\n";
      Printf.printf "  print_newline ()\n")
  end
