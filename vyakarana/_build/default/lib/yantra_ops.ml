(* yantra_ops.ml — pure primitive operations with no graph or session dependency.
   covers: string ops, list ops, boolean/comparison ops, constructors, numeric math,
   vector/matrix ops (Category A floor) and composed ops pending tantra migration.

   Category A (irreducible — stay here forever):
     scalar: add mul sub div sqrt power abs neg floor ceil mod min max
     trig:   sin cos tan asin acos atan2 log exp
      list:   map filter reduce fixpoint nth length range flatten append unique sum zip
     string: split join concat substr starts-with ends-with member char-at
             string-length to-string to-number split-numeric
     bool:   eq neq lt le gt ge and or not
     ctor:   pair bind

   Category B (composed — migrate to tantras in brahman, then remove OCaml arm):
     vec-add vec-sub vec-scale vec-dot vec-norm rot2d mat-mul
     square half double first-match frequencies
     (fold-pairs fold-triples iterate already removed — use reduce/fixpoint)

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

  (* split-numeric: "5kg" → ["5.0", "kg"], "3.5m/s" → ["3.5", "m/s"], "42" → ["42.0", ""]
     also handles scientific notation: "1e6" → ["1000000.", ""], "1.6e-19" → ["1.6e-19", ""] *)
  | "split-numeric" ->
    let s = as_string (e_eval k e (List.nth args 0)) in
    let n = String.length s in
    let i = ref 0 in
    (* consume leading sign *)
    if !i < n && s.[!i] = '-' then incr i;
    (* consume digits and decimal point *)
    while !i < n && (s.[!i] = '.' || (s.[!i] >= '0' && s.[!i] <= '9')) do incr i done;
    (* consume scientific notation exponent: e/E followed by optional sign and digits *)
    if !i < n && (s.[!i] = 'e' || s.[!i] = 'E') then begin
      let j = !i + 1 in
      if j < n && (s.[j] = '+' || s.[j] = '-') then begin
        let k2 = j + 1 in
        if k2 < n && s.[k2] >= '0' && s.[k2] <= '9' then begin
          i := k2;
          while !i < n && s.[!i] >= '0' && s.[!i] <= '9' do incr i done
        end
      end else if j < n && s.[j] >= '0' && s.[j] <= '9' then begin
        i := j;
        while !i < n && s.[!i] >= '0' && s.[!i] <= '9' do incr i done
      end
    end;
    let num_part = String.sub s 0 !i in
    let alpha_part = String.sub s !i (n - !i) in
    let num_val = match float_of_string_opt num_part with Some f -> string_of_float f | None -> "" in
    Some (VList [VString num_val; VString alpha_part])

  | "to-string" ->
    Some (VString (as_string (e_eval k e (List.nth args 0))))

  | "upper" ->
    Some (VString (String.uppercase_ascii (as_string (e_eval k e (List.nth args 0)))))

  | "lower" ->
    Some (VString (String.lowercase_ascii (as_string (e_eval k e (List.nth args 0)))))

  (* substr: string × start × length → string  — clamps to string bounds *)
  | "substr" ->
    let s   = as_string (e_eval k e (List.nth args 0)) in
    let pos = int_of_float (as_float (e_eval k e (List.nth args 1))) in
    let len = int_of_float (as_float (e_eval k e (List.nth args 2))) in
    let slen = String.length s in
    let pos' = max 0 (min pos slen) in
    let len' = max 0 (min len (slen - pos')) in
    Some (VString (String.sub s pos' len'))

  (* starts-with: string × prefix → bool *)
  | "starts-with" ->
    let s   = as_string (e_eval k e (List.nth args 0)) in
    let pre = as_string (e_eval k e (List.nth args 1)) in
    let n = String.length pre in
    Some (VBool (String.length s >= n && String.sub s 0 n = pre))

  | "ends-with" ->
    let s   = as_string (e_eval k e (List.nth args 0)) in
    let suf = as_string (e_eval k e (List.nth args 1)) in
    let slen = String.length s in
    let n    = String.length suf in
    Some (VBool (slen >= n && String.sub s (slen - n) n = suf))

  (* member: value × list → bool — O(n) membership test *)
  | "member" ->
    let needle = as_string (e_eval k e (List.nth args 0)) in
    let lst    = as_list (e_eval k e (List.nth args 1)) in
    Some (VBool (List.exists (fun v -> as_string v = needle) lst))

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

  (* reduce: list × init × fn → scalar
     general fold: carry accumulator through every element.
     fold-pairs and fold-triples are specialisations of this.
     reduce list init (fn acc x -> ...) *)
  | "reduce" ->
    let lst     = as_list (e_eval k e (List.nth args 0)) in
    let init    = e_eval k e (List.nth args 1) in
    let fn_val  = e_eval k e (List.nth args 2) in
    (match fn_val with
     | VFn (params, body, captured) ->
       let env_copy c =
         let e2 = Hashtbl.create (Hashtbl.length c) in
         Hashtbl.iter (fun k v -> Hashtbl.replace e2 k v) c; e2
       in
       let acc = List.fold_left (fun acc item ->
         let local = env_copy captured in
         (match params with
          | [pa; pb] -> Hashtbl.replace local pa acc; Hashtbl.replace local pb item
          | _ -> ());
         e_eval k local body
       ) init lst in
       Some acc
     | _ -> Some init)

  (* fixpoint: state × fn → stable-state
     applies fn repeatedly until output = input. safety cap: 20 iterations. *)
  | "fixpoint" ->
    let state0 = e_eval k e (List.nth args 0) in
    let fn_val = e_eval k e (List.nth args 1) in
    let env_copy c =
      let e2 = Hashtbl.create (Hashtbl.length c) in
      Hashtbl.iter (fun kk v -> Hashtbl.replace e2 kk v) c; e2
    in
    let apply_fn s = match fn_val with
      | VFn ([p], body, captured) ->
        let local = env_copy captured in
        Hashtbl.replace local p s;
        e_eval k local body
      | _ -> s
    in
    let rec loop s fuel =
      if fuel <= 0 then s
      else let s' = apply_fn s in
           if s' = s then s' else loop s' (fuel - 1)
    in
    Some (loop state0 20)

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

  (* zip: [a,b,c] [x,y,z] → [[a,x],[b,y],[c,z]]  pairs corresponding elements *)
  | "zip" ->
    let a = as_list (e_eval k e (List.nth args 0)) in
    let b = as_list (e_eval k e (List.nth args 1)) in
    let n = min (List.length a) (List.length b) in
    Some (VList (List.init n (fun i -> VList [List.nth a i; List.nth b i])))

  (* range: n → [0, 1, ..., n-1]  so tantras can map over variable-length sequences *)
  | "range" ->
    let n = int_of_float (as_float (e_eval k e (List.nth args 0))) in
    Some (VList (List.init (max 0 n) (fun i -> VFloat (float_of_int i))))

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

  (* sum: list of floats → float — reduces a list by addition *)
  | "sum" ->
    let lst = as_list (e_eval k e (List.nth args 0)) in
    let total = List.fold_left (fun acc v -> acc +. as_float v) 0.0 lst in
    Some (VFloat total)

  (* frequencies: list → [[value, count], ...] — count occurrences using hash table, O(n) *)
  | "frequencies" ->
    let lst = as_list (e_eval k e (List.nth args 0)) in
    let counts : (string, int) Hashtbl.t = Hashtbl.create 64 in
    let order = ref [] in
    List.iter (fun v ->
      let key = as_string v in
      if not (Hashtbl.mem counts key) then order := key :: !order;
      let prev = match Hashtbl.find_opt counts key with Some c -> c | None -> 0 in
      Hashtbl.replace counts key (prev + 1)
    ) lst;
    let pairs = List.rev_map (fun key ->
      VList [VString key; VFloat (float_of_int (Hashtbl.find counts key))]
    ) !order in
    Some (VList pairs)

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
  | "asin"  -> Some (VFloat (asin     (as_float (e_eval k e (List.nth args 0)))))
  | "acos"  -> Some (VFloat (acos     (as_float (e_eval k e (List.nth args 0)))))
  | "atan2" -> Some (VFloat (atan2    (as_float (e_eval k e (List.nth args 0)))
                                       (as_float (e_eval k e (List.nth args 1)))))
  | "sin"   -> Some (VFloat (sin      (as_float (e_eval k e (List.nth args 0)))))
  | "cos"   -> Some (VFloat (cos      (as_float (e_eval k e (List.nth args 0)))))
  | "tan"   -> Some (VFloat (tan      (as_float (e_eval k e (List.nth args 0)))))
  | "log"   -> Some (VFloat (log      (as_float (e_eval k e (List.nth args 0)))))
  | "exp"   -> Some (VFloat (exp      (as_float (e_eval k e (List.nth args 0)))))
  | "abs"   -> Some (VFloat (abs_float(as_float (e_eval k e (List.nth args 0)))))
  | "neg"   -> Some (VFloat (-.       (as_float (e_eval k e (List.nth args 0)))))
  | "floor" -> Some (VFloat (floor    (as_float (e_eval k e (List.nth args 0)))))
  | "ceil"  -> Some (VFloat (ceil     (as_float (e_eval k e (List.nth args 0)))))
  | "mod"   -> Some (VFloat (mod_float (as_float (e_eval k e (List.nth args 0))) (as_float (e_eval k e (List.nth args 1)))))
  | "min"   -> Some (VFloat (Float.min (as_float (e_eval k e (List.nth args 0))) (as_float (e_eval k e (List.nth args 1)))))
  | "max"   -> Some (VFloat (Float.max (as_float (e_eval k e (List.nth args 0))) (as_float (e_eval k e (List.nth args 1)))))

  (* ---- n-dimensional vector operations ---- *)
  (* all operate on VList of VFloat — works for any n: 2D, 3D, nD *)

  (* vec-add: [a1..an] x [b1..bn] → [a1+b1..an+bn] *)
  | "vec-add" ->
    let va = as_list (e_eval k e (List.nth args 0)) in
    let vb = as_list (e_eval k e (List.nth args 1)) in
    Some (VList (List.map2 (fun a b -> VFloat (as_float a +. as_float b)) va vb))

  (* vec-sub: [a1..an] x [b1..bn] → [a1-b1..an-bn] *)
  | "vec-sub" ->
    let va = as_list (e_eval k e (List.nth args 0)) in
    let vb = as_list (e_eval k e (List.nth args 1)) in
    Some (VList (List.map2 (fun a b -> VFloat (as_float a -. as_float b)) va vb))

  (* vec-scale: scalar x [a1..an] → [s·a1..s·an] *)
  | "vec-scale" ->
    let s  = as_float (e_eval k e (List.nth args 0)) in
    let va = as_list (e_eval k e (List.nth args 1)) in
    Some (VList (List.map (fun a -> VFloat (s *. as_float a)) va))

  (* vec-dot: [a1..an] x [b1..bn] → scalar sum of component products *)
  | "vec-dot" ->
    let va = as_list (e_eval k e (List.nth args 0)) in
    let vb = as_list (e_eval k e (List.nth args 1)) in
    let s = List.fold_left2 (fun acc a b -> acc +. as_float a *. as_float b) 0.0 va vb in
    Some (VFloat s)

  (* vec-norm: [a1..an] → sqrt(a1²+...+an²) *)
  | "vec-norm" ->
    let va = as_list (e_eval k e (List.nth args 0)) in
    let s = List.fold_left (fun acc a -> acc +. as_float a *. as_float a) 0.0 va in
    Some (VFloat (sqrt s))

  (* vec-nth: [a1..an] x i → ai  (0-based index) *)
  | "vec-nth" ->
    let va  = as_list (e_eval k e (List.nth args 0)) in
    let idx = int_of_float (as_float (e_eval k e (List.nth args 1))) in
    Some (if idx >= 0 && idx < List.length va then List.nth va idx else VNone)

  (* rot2d: angle x [x,y] → [x·cos θ - y·sin θ, x·sin θ + y·cos θ]
     applies a 2D rotation matrix to a 2D vector.
     generalises to any plane of rotation for higher dims. *)
  | "rot2d" ->
    let theta = as_float (e_eval k e (List.nth args 0)) in
    let v     = as_list (e_eval k e (List.nth args 1)) in
    let x = as_float (List.nth v 0) in
    let y = as_float (List.nth v 1) in
    let c = cos theta in
    let s = sin theta in
    Some (VList [VFloat (x *. c -. y *. s); VFloat (x *. s +. y *. c)])

  (* mat-mul: flat row-major matrix (n*m floats, ncols) x flat matrix (m*p floats, pcols)
     → flat result matrix (n*p floats).
     mat-mul A ncols B pcols → C
     used for homogeneous transform composition in kinematic chains. *)
  | "mat-mul" ->
    let a_flat = as_list (e_eval k e (List.nth args 0)) in
    let ncols_a = int_of_float (as_float (e_eval k e (List.nth args 1))) in
    let b_flat = as_list (e_eval k e (List.nth args 2)) in
    let ncols_b = int_of_float (as_float (e_eval k e (List.nth args 3))) in
    let a = List.map as_float a_flat in
    let b = List.map as_float b_flat in
    let nrows_a = List.length a / ncols_a in
    let nrows_b = List.length b / ncols_b in
    if ncols_a <> nrows_b then Some VNone
    else
      let result = Array.make (nrows_a * ncols_b) 0.0 in
      for i = 0 to nrows_a - 1 do
        for j = 0 to ncols_b - 1 do
          let s = ref 0.0 in
          for kk = 0 to ncols_a - 1 do
            s := !s +. List.nth a (i * ncols_a + kk) *. List.nth b (kk * ncols_b + j)
          done;
          result.(i * ncols_b + j) <- !s
        done
      done;
      Some (VList (Array.to_list (Array.map (fun f -> VFloat f) result)))

  | "square" ->
    let a = as_float (e_eval k e (List.nth args 0)) in
    Some (VFloat (a *. a))

  | "half" ->
    let a = as_float (e_eval k e (List.nth args 0)) in
    Some (VFloat (a *. 0.5))

  | "double" ->
    let a = as_float (e_eval k e (List.nth args 0)) in
    Some (VFloat (a *. 2.0))

  | "reciprocal" ->
    let a = as_float (e_eval k e (List.nth args 0)) in
    Some (VFloat (1.0 /. a))

  | "reverse" ->
    let lst = as_list (e_eval k e (List.nth args 0)) in
    Some (VList (List.rev lst))

  | "take" ->
    let lst = as_list (e_eval k e (List.nth args 0)) in
    let n   = int_of_float (as_float (e_eval k e (List.nth args 1))) in
    let n'  = max 0 (min n (List.length lst)) in
    Some (VList (List.filteri (fun i _ -> i < n') lst))

  | "drop" ->
    let lst = as_list (e_eval k e (List.nth args 0)) in
    let n   = int_of_float (as_float (e_eval k e (List.nth args 1))) in
    let n'  = max 0 (min n (List.length lst)) in
    Some (VList (List.filteri (fun i _ -> i >= n') lst))

  | _ -> None
