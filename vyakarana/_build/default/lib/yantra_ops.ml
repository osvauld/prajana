(* yantra_ops.ml — pure primitive operations with no graph or session dependency.
   covers: string ops, list ops, boolean/comparison ops, constructors, numeric math.
   all operations take e_eval as a parameter (the forward-ref'd core evaluator)
   and return value option — Some v if the op name matched, None to fall through.

   dependency: Yantra_types only. *)

open Yantra_types

(* e_eval type alias for clarity *)
type evaluator = proof_graph -> env -> expr -> value
and proof_graph = Proof_graph.proof_graph

let eval_pure_op (e_eval : evaluator) (k : proof_graph) (e : env) (op : string) (args : expr list)
    : value option =
  match op with

  (* ---- string operations ---- *)

  | "split" ->
    let s = as_string (e_eval k e (List.nth args 0)) in
    let delim = as_string (e_eval k e (List.nth args 1)) in
    let parts = if String.length delim = 1 then
      String.split_on_char delim.[0] s
      |> List.filter (fun p -> String.length (String.trim p) > 0)
      |> List.map String.trim
    else
      Str.split (Str.regexp_string delim) s
      |> List.filter (fun p -> String.length (String.trim p) > 0)
      |> List.map String.trim
    in
    Some (VList (List.map (fun s -> VString s) parts))

  | "concat" ->
    let vals = List.map (e_eval k e) args in
    Some (VString (String.concat "" (List.map as_string vals)))

  | "join" ->
    let lst = as_list (e_eval k e (List.nth args 0)) in
    let sep = as_string (e_eval k e (List.nth args 1)) in
    Some (VString (String.concat sep (List.map as_string lst)))

  | "char-at" ->
    let s = as_string (e_eval k e (List.nth args 0)) in
    let i = int_of_float (as_float (e_eval k e (List.nth args 1))) in
    Some (if i >= 0 && i < String.length s then VString (String.make 1 s.[i]) else VNone)

  | "string-length" ->
    let s = as_string (e_eval k e (List.nth args 0)) in
    Some (VFloat (Float.of_int (String.length s)))

  | "to-number" ->
    let s = as_string (e_eval k e (List.nth args 0)) in
    Some (match float_of_string_opt s with Some f -> VFloat f | None -> VNone)

  | "to-string" ->
    Some (VString (as_string (e_eval k e (List.nth args 0))))

  | "upper" ->
    Some (VString (String.uppercase_ascii (as_string (e_eval k e (List.nth args 0)))))

  | "lower" ->
    Some (VString (String.lowercase_ascii (as_string (e_eval k e (List.nth args 0)))))

  (* ---- list operations ---- *)

  | "map" ->
    let lst = as_list (e_eval k e (List.nth args 0)) in
    let fn_val = e_eval k e (List.nth args 1) in
    (match fn_val with
     | VFn (params, body, captured) ->
       let env_copy c =
         let e2 = Hashtbl.create (Hashtbl.length c) in
         Hashtbl.iter (fun k v -> Hashtbl.replace e2 k v) c; e2
       in
       let results = List.map (fun item ->
         let local = env_copy captured in
         (match params with [p] -> Hashtbl.replace local p item | _ -> ());
         e_eval k local body
       ) lst in
       Some (VList results)
     | _ -> Some (VList []))

  | "filter" ->
    let lst = as_list (e_eval k e (List.nth args 0)) in
    let fn_val = e_eval k e (List.nth args 1) in
    (match fn_val with
     | VFn (params, body, captured) ->
       let env_copy c =
         let e2 = Hashtbl.create (Hashtbl.length c) in
         Hashtbl.iter (fun k v -> Hashtbl.replace e2 k v) c; e2
       in
       let results = List.filter (fun item ->
         let local = env_copy captured in
         (match params with [p] -> Hashtbl.replace local p item | _ -> ());
         as_bool (e_eval k local body)
       ) lst in
       Some (VList results)
     | _ -> Some (VList []))

  | "first-match" ->
    let lst = as_list (e_eval k e (List.nth args 0)) in
    let fn_val = e_eval k e (List.nth args 1) in
    (match fn_val with
     | VFn (params, body, captured) ->
       let env_copy c =
         let e2 = Hashtbl.create (Hashtbl.length c) in
         Hashtbl.iter (fun k v -> Hashtbl.replace e2 k v) c; e2
       in
       let result = List.find_map (fun item ->
         let local = env_copy captured in
         (match params with [p] -> Hashtbl.replace local p item | _ -> ());
         let r = e_eval k local body in
         match r with VNone -> None | _ -> Some r
       ) lst in
       Some (match result with Some v -> v | None -> VNone)
     | _ -> Some VNone)

  | "fold-pairs" ->
    let lst = as_list (e_eval k e (List.nth args 0)) in
    let fn_val = e_eval k e (List.nth args 1) in
    (match fn_val with
     | VFn (params, body, captured) ->
       let env_copy c =
         let e2 = Hashtbl.create (Hashtbl.length c) in
         Hashtbl.iter (fun k v -> Hashtbl.replace e2 k v) c; e2
       in
       let rec process = function
         | [] -> []
         | [x] -> [x]
         | a :: b :: rest ->
           let local = env_copy captured in
           (match params with
            | [pa; pb] -> Hashtbl.replace local pa a; Hashtbl.replace local pb b
            | _ -> ());
           let result = e_eval k local body in
            (match result with
             | VNone -> a :: process (b :: rest)
             | v    -> v :: process rest)
       in
       Some (VList (process lst))
     | _ -> Some (VList lst))

  | "fold-triples" ->
    let lst = as_list (e_eval k e (List.nth args 0)) in
    let fn_val = e_eval k e (List.nth args 1) in
    (match fn_val with
     | VFn (params, body, captured) ->
       let env_copy c =
         let e2 = Hashtbl.create (Hashtbl.length c) in
         Hashtbl.iter (fun k v -> Hashtbl.replace e2 k v) c; e2
       in
       let results = ref [] in
       let rec process = function
         | [] | [_] | [_; _] -> ()
         | a :: b :: c :: rest ->
           let local = env_copy captured in
           (match params with
            | [pa; pb; pc] ->
              Hashtbl.replace local pa a;
              Hashtbl.replace local pb b;
              Hashtbl.replace local pc c
            | _ -> ());
           let result = e_eval k local body in
           (match result with
            | VNone -> process (b :: c :: rest)
            | v -> results := v :: !results; process rest)
       in
       process lst;
       Some (VList (List.rev !results))
     | _ -> Some (VList []))

  | "length" ->
    let lst = as_list (e_eval k e (List.nth args 0)) in
    Some (VFloat (Float.of_int (List.length lst)))

  | "nth" ->
    let container = e_eval k e (List.nth args 0) in
    let idx = int_of_float (as_float (e_eval k e (List.nth args 1))) in
    Some (match container with
     | VPair (n, v) ->
       if idx = 0 then VString n else if idx = 1 then v else VNone
     | VBinding (n, f) ->
       if idx = 0 then VString n else if idx = 1 then VFloat f else VNone
     | _ ->
       let lst = as_list container in
       if idx >= 0 && idx < List.length lst then List.nth lst idx else VNone)

  | "flatten" ->
    let lst = as_list (e_eval k e (List.nth args 0)) in
    Some (VList (List.concat_map as_list lst))

  | "append" ->
    let a = as_list (e_eval k e (List.nth args 0)) in
    let b = as_list (e_eval k e (List.nth args 1)) in
    Some (VList (a @ b))

  | "sort-desc" ->
    let lst = as_list (e_eval k e (List.nth args 0)) in
    let score_of_pair = function
      | VList [_; score] -> as_float score
      | VPair (_, score) -> as_float score
      | _ -> 0.0
    in
    Some (VList (List.sort (fun a b -> compare (score_of_pair b) (score_of_pair a)) lst))

  | "unique" ->
    let lst = as_list (e_eval k e (List.nth args 0)) in
    let seen = Hashtbl.create 16 in
    let unique = List.filter (fun v ->
      let key = as_string v in
      if Hashtbl.mem seen key then false
      else (Hashtbl.replace seen key true; true)
    ) lst in
    Some (VList unique)

  (* ---- boolean / comparison operations ---- *)

  | "eq" ->
    let a = e_eval k e (List.nth args 0) in
    let b = e_eval k e (List.nth args 1) in
    Some (VBool (as_string a = as_string b))

  | "neq" ->
    let a = e_eval k e (List.nth args 0) in
    let b = e_eval k e (List.nth args 1) in
    Some (VBool (as_string a <> as_string b))

  | "and" ->
    Some (VBool (List.for_all Fun.id (List.map (fun arg -> as_bool (e_eval k e arg)) args)))

  | "or" ->
    Some (VBool (List.exists Fun.id (List.map (fun arg -> as_bool (e_eval k e arg)) args)))

  | "not" ->
    Some (VBool (not (as_bool (e_eval k e (List.nth args 0)))))

  | "lt" -> Some (VBool (as_float (e_eval k e (List.nth args 0)) <  as_float (e_eval k e (List.nth args 1))))
  | "le" -> Some (VBool (as_float (e_eval k e (List.nth args 0)) <= as_float (e_eval k e (List.nth args 1))))
  | "gt" -> Some (VBool (as_float (e_eval k e (List.nth args 0)) >  as_float (e_eval k e (List.nth args 1))))
  | "ge" -> Some (VBool (as_float (e_eval k e (List.nth args 0)) >= as_float (e_eval k e (List.nth args 1))))

  (* ---- constructors ---- *)

  | "pair" ->
    let name = as_string (e_eval k e (List.nth args 0)) in
    let v = e_eval k e (List.nth args 1) in
    Some (match args with
     | [_; _] -> VPair (name, v)
     | [_; _; _] -> VList [VString name; v; e_eval k e (List.nth args 2)]
     | _ -> VPair (name, v))

  | "bind" ->
    let name = as_string (e_eval k e (List.nth args 0)) in
    let v = as_float (e_eval k e (List.nth args 1)) in
    Some (VBinding (name, v))

  (* ---- numeric operations ---- *)

  | "add"   ->
    (* monoid: variadic fold over addition; 0.0 is the identity *)
    Some (VFloat (List.fold_left (fun acc arg -> acc +. as_float (e_eval k e arg)) 0.0 args))
  | "mul"   ->
    (* monoid: variadic fold over multiplication; 1.0 is the identity *)
    Some (VFloat (List.fold_left (fun acc arg -> acc *. as_float (e_eval k e arg)) 1.0 args))
  | "sub"   -> Some (VFloat (as_float (e_eval k e (List.nth args 0)) -. as_float (e_eval k e (List.nth args 1))))
  | "div" ->
    let b = as_float (e_eval k e (List.nth args 1)) in
    Some (if b = 0.0 then VFloat 0.0 else VFloat (as_float (e_eval k e (List.nth args 0)) /. b))
  | "power" -> Some (VFloat (as_float (e_eval k e (List.nth args 0)) ** as_float (e_eval k e (List.nth args 1))))
  | "sqrt"  -> Some (VFloat (sqrt     (as_float (e_eval k e (List.nth args 0)))))
  | "sin"   -> Some (VFloat (sin      (as_float (e_eval k e (List.nth args 0)))))
  | "cos"   -> Some (VFloat (cos      (as_float (e_eval k e (List.nth args 0)))))
  | "tan"   -> Some (VFloat (tan      (as_float (e_eval k e (List.nth args 0)))))
  | "log"   -> Some (VFloat (log      (as_float (e_eval k e (List.nth args 0)))))
  | "abs"   -> Some (VFloat (abs_float(as_float (e_eval k e (List.nth args 0)))))
  | "neg"   -> Some (VFloat (-.       (as_float (e_eval k e (List.nth args 0)))))
  | "floor" -> Some (VFloat (floor    (as_float (e_eval k e (List.nth args 0)))))
  | "ceil"  -> Some (VFloat (ceil     (as_float (e_eval k e (List.nth args 0)))))
  | "mod"   -> Some (VFloat (mod_float (as_float (e_eval k e (List.nth args 0))) (as_float (e_eval k e (List.nth args 1)))))
  | "min"   -> Some (VFloat (Float.min (as_float (e_eval k e (List.nth args 0))) (as_float (e_eval k e (List.nth args 1)))))
  | "max"   -> Some (VFloat (Float.max (as_float (e_eval k e (List.nth args 0))) (as_float (e_eval k e (List.nth args 1)))))

  | _ -> None
