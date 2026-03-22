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
  (* use the shared eval_arg helpers from Yantra_types *)
  let (eval_arg, eval_str, eval_flt, eval_lst, eval_int) =
    make_eval_arg e_eval k e args in
  ignore (eval_arg, eval_str, eval_flt, eval_lst, eval_int);
  match op with

  (* ---- string operations ---- *)

  | "split" ->
    let s = eval_str 0 in
    let delim = eval_str 1 in
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
    let lst = eval_lst 0 in
    let sep = eval_str 1 in
    Some (VString (String.concat sep (List.map as_string lst)))

  | "char-at" ->
    let s = eval_str 0 in
    let i = eval_int 1 in
    Some (if i >= 0 && i < String.length s then VString (String.make 1 s.[i]) else VNone)

  | "string-length" ->
    Some (VFloat (Float.of_int (String.length (eval_str 0))))

  | "to-number" ->
    let s = eval_str 0 in
    Some (match float_of_string_opt s with Some f -> VFloat f | None -> VNone)

  (* split-numeric: "5kg" → ["5.0", "kg"], "3.5m/s" → ["3.5", "m/s"], "42" → ["42.0", ""]
     also handles scientific notation: "1e6" → ["1000000.", ""], "1.6e-19" → ["1.6e-19", ""] *)
  | "split-numeric" ->
    let s = eval_str 0 in
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

  | "debug-print" ->
    (* debug-print val — prints to stderr and returns val unchanged *)
    let v = eval_arg 0 in
    let rec show = function
      | VString s -> Printf.sprintf "'%s'" s
      | VBool b   -> string_of_bool b
      | VFloat f  -> string_of_float f
      | VNone     -> "none"
      | VList l   -> "[" ^ String.concat ", " (List.map show l) ^ "]"
      | _         -> "?" in
    Printf.eprintf "[debug-print] %s\n%!" (show v);
    Some v

  | "to-string" ->
    Some (VString (eval_str 0))

  | "upper" ->
    Some (VString (String.uppercase_ascii (eval_str 0)))

  | "lower" ->
    Some (VString (String.lowercase_ascii (eval_str 0)))

  (* substr: string × start × length → string  — clamps to string bounds *)
  | "substr" ->
    let s   = eval_str 0 in
    let pos = eval_int 1 in
    let len = eval_int 2 in
    let slen = String.length s in
    let pos' = max 0 (min pos slen) in
    let len' = max 0 (min len (slen - pos')) in
    Some (VString (String.sub s pos' len'))

  (* starts-with: string × prefix → bool *)
  | "starts-with" ->
    let s   = eval_str 0 in
    let pre = eval_str 1 in
    let n = String.length pre in
    Some (VBool (String.length s >= n && String.sub s 0 n = pre))

  | "ends-with" ->
    let s   = eval_str 0 in
    let suf = eval_str 1 in
    let slen = String.length s in
    let n    = String.length suf in
    Some (VBool (slen >= n && String.sub s (slen - n) n = suf))

  (* member: value × list → bool — O(n) membership test *)
  | "member" ->
    let needle = eval_str 0 in
    let lst    = eval_lst 1 in
    Some (VBool (List.exists (fun v -> as_string v = needle) lst))

  (* ---- list operations ---- *)

  | "map" ->
    let lst = eval_lst 0 in
    let fn_val = eval_arg 1 in
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
    let lst = eval_lst 0 in
    let fn_val = eval_arg 1 in
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
    let lst = eval_lst 0 in
    let fn_val = eval_arg 1 in
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
    let lst     = eval_lst 0 in
    let init    = eval_arg 1 in
    let fn_val  = eval_arg 2 in
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
    let state0 = eval_arg 0 in
    let fn_val = eval_arg 1 in
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
           (* pipeline fns only append triples — equal length means stable *)
           let stable = match s, s' with
             | VList a, VList b -> List.length a = List.length b
             | _ -> s' = s
           in
           if stable then s' else loop s' (fuel - 1)
    in
    Some (loop state0 20)

  | "length" ->
    Some (VFloat (Float.of_int (List.length (eval_lst 0))))

  | "nth" ->
    let container = eval_arg 0 in
    let idx = eval_int 1 in
    Some (match container with
     | VPair (n, v) ->
       if idx = 0 then VString n else if idx = 1 then v else VNone
     | VBinding (n, f) ->
       if idx = 0 then VString n else if idx = 1 then VFloat f else VNone
     | _ ->
       let lst = as_list container in
       if idx >= 0 && idx < List.length lst then List.nth lst idx else VNone)

  | "flatten" ->
    Some (VList (List.concat_map as_list (eval_lst 0)))

  | "append" ->
    let a = eval_lst 0 in
    let b = eval_lst 1 in
    Some (VList (a @ b))

  (* zip: [a,b,c] [x,y,z] → [[a,x],[b,y],[c,z]]  pairs corresponding elements *)
  | "zip" ->
    let a = eval_lst 0 in
    let b = eval_lst 1 in
    let n = min (List.length a) (List.length b) in
    Some (VList (List.init n (fun i -> VList [List.nth a i; List.nth b i])))

  (* range: n → [0, 1, ..., n-1]  so tantras can map over variable-length sequences *)
  | "range" ->
    let n = eval_int 0 in
    Some (VList (List.init (max 0 n) (fun i -> VFloat (float_of_int i))))

  | "sort-desc" ->
    let lst = eval_lst 0 in
    let score_of_pair = function
      | VList [_; score] -> as_float score
      | VPair (_, score) -> as_float score
      | _ -> 0.0
    in
    Some (VList (List.sort (fun a b -> compare (score_of_pair b) (score_of_pair a)) lst))

  | "unique" ->
    let lst = eval_lst 0 in
    let seen = Hashtbl.create 16 in
    let unique = List.filter (fun v ->
      let key = as_string v in
      if Hashtbl.mem seen key then false
      else (Hashtbl.replace seen key true; true)
    ) lst in
    Some (VList unique)

  (* sum: list of floats → float — reduces a list by addition *)
  | "sum" ->
    let lst = eval_lst 0 in
    let total = List.fold_left (fun acc v -> acc +. as_float v) 0.0 lst in
    Some (VFloat total)

  (* frequencies: list → [[value, count], ...] — count occurrences using hash table, O(n) *)
  | "frequencies" ->
    let lst = eval_lst 0 in
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
    Some (VBool (eval_str 0 = eval_str 1))

  | "neq" ->
    Some (VBool (eval_str 0 <> eval_str 1))

  | "and" ->
    Some (VBool (List.for_all Fun.id (List.map (fun arg -> as_bool (e_eval k e arg)) args)))

  | "or" ->
    Some (VBool (List.exists Fun.id (List.map (fun arg -> as_bool (e_eval k e arg)) args)))

  | "not" ->
    Some (VBool (not (as_bool (eval_arg 0))))

  | "lt" -> Some (VBool (eval_flt 0 <  eval_flt 1))
  | "le" -> Some (VBool (eval_flt 0 <= eval_flt 1))
  | "gt" -> Some (VBool (eval_flt 0 >  eval_flt 1))
  | "ge" -> Some (VBool (eval_flt 0 >= eval_flt 1))

  (* ---- constructors ---- *)

  | "pair" ->
    let name = eval_str 0 in
    let v = eval_arg 1 in
    Some (match args with
     | [_; _] -> VPair (name, v)
     | [_; _; _] -> VList [VString name; v; eval_arg 2]
     | _ -> VPair (name, v))

  | "bind" ->
    let name = eval_str 0 in
    let v = eval_flt 1 in
    Some (VBinding (name, v))

  (* ---- numeric operations ---- *)

  | "add"   ->
    (* monoid: variadic fold over addition; 0.0 is the identity *)
    Some (VFloat (List.fold_left (fun acc arg -> acc +. as_float (e_eval k e arg)) 0.0 args))
  | "mul"   ->
    (* monoid: variadic fold over multiplication; 1.0 is the identity *)
    Some (VFloat (List.fold_left (fun acc arg -> acc *. as_float (e_eval k e arg)) 1.0 args))
  | "sub"   -> Some (VFloat (eval_flt 0 -. eval_flt 1))
  | "div" ->
    let b = eval_flt 1 in
    Some (if b = 0.0 then VFloat 0.0 else VFloat (eval_flt 0 /. b))
  | "power" -> Some (VFloat (eval_flt 0 ** eval_flt 1))
  | "sqrt"  -> Some (VFloat (sqrt  (eval_flt 0)))
  | "asin"  -> Some (VFloat (asin  (eval_flt 0)))
  | "acos"  -> Some (VFloat (acos  (eval_flt 0)))
  | "atan2" -> Some (VFloat (atan2 (eval_flt 0) (eval_flt 1)))
  | "sin"   -> Some (VFloat (sin   (eval_flt 0)))
  | "cos"   -> Some (VFloat (cos   (eval_flt 0)))
  | "tan"   -> Some (VFloat (tan   (eval_flt 0)))
  | "log"   -> Some (VFloat (log   (eval_flt 0)))
  | "exp"   -> Some (VFloat (exp   (eval_flt 0)))
  | "abs"   -> Some (VFloat (abs_float (eval_flt 0)))
  | "neg"   -> Some (VFloat (-. (eval_flt 0)))
  | "floor" -> Some (VFloat (floor (eval_flt 0)))
  | "ceil"  -> Some (VFloat (ceil  (eval_flt 0)))
  | "mod"   -> Some (VFloat (mod_float (eval_flt 0) (eval_flt 1)))
  | "min"   -> Some (VFloat (Float.min (eval_flt 0) (eval_flt 1)))
  | "max"   -> Some (VFloat (Float.max (eval_flt 0) (eval_flt 1)))

  (* ---- n-dimensional vector operations ---- *)
  (* all operate on VList of VFloat — works for any n: 2D, 3D, nD *)

  (* vec-add: [a1..an] x [b1..bn] → [a1+b1..an+bn] *)
  | "vec-add" ->
    let va = eval_lst 0 in
    let vb = eval_lst 1 in
    Some (VList (List.map2 (fun a b -> VFloat (as_float a +. as_float b)) va vb))

  (* vec-sub: [a1..an] x [b1..bn] → [a1-b1..an-bn] *)
  | "vec-sub" ->
    let va = eval_lst 0 in
    let vb = eval_lst 1 in
    Some (VList (List.map2 (fun a b -> VFloat (as_float a -. as_float b)) va vb))

  (* vec-scale: scalar x [a1..an] → [s·a1..s·an] *)
  | "vec-scale" ->
    let s  = eval_flt 0 in
    let va = eval_lst 1 in
    Some (VList (List.map (fun a -> VFloat (s *. as_float a)) va))

  (* vec-dot: [a1..an] x [b1..bn] → scalar sum of component products *)
  | "vec-dot" ->
    let va = eval_lst 0 in
    let vb = eval_lst 1 in
    let s = List.fold_left2 (fun acc a b -> acc +. as_float a *. as_float b) 0.0 va vb in
    Some (VFloat s)

  (* vec-norm: [a1..an] → sqrt(a1²+...+an²) *)
  | "vec-norm" ->
    let va = eval_lst 0 in
    let s = List.fold_left (fun acc a -> acc +. as_float a *. as_float a) 0.0 va in
    Some (VFloat (sqrt s))

  (* vec-nth: [a1..an] x i → ai  (0-based index) *)
  | "vec-nth" ->
    let va  = eval_lst 0 in
    let idx = eval_int 1 in
    Some (if idx >= 0 && idx < List.length va then List.nth va idx else VNone)

  (* rot2d: angle x [x,y] → [x·cos θ - y·sin θ, x·sin θ + y·cos θ]
     applies a 2D rotation matrix to a 2D vector.
     generalises to any plane of rotation for higher dims. *)
  | "rot2d" ->
    let theta = eval_flt 0 in
    let v     = eval_lst 1 in
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
    let a_flat = eval_lst 0 in
    let ncols_a = eval_int 1 in
    let b_flat = eval_lst 2 in
    let ncols_b = eval_int 3 in
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
    let a = eval_flt 0 in Some (VFloat (a *. a))

  | "half" ->
    Some (VFloat (eval_flt 0 *. 0.5))

  | "double" ->
    Some (VFloat (eval_flt 0 *. 2.0))

  | "reciprocal" ->
    Some (VFloat (1.0 /. eval_flt 0))

  | "reverse" ->
    Some (VList (List.rev (eval_lst 0)))

  | "take" ->
    let lst = eval_lst 0 in
    let n'  = max 0 (min (eval_int 1) (List.length lst)) in
    Some (VList (List.filteri (fun i _ -> i < n') lst))

  | "drop" ->
    let lst = eval_lst 0 in
    let n'  = max 0 (min (eval_int 1) (List.length lst)) in
    Some (VList (List.filteri (fun i _ -> i >= n') lst))

  (* ---- prakriya primitives: positional awareness for stratified scans ---- *)

  (* with-index: graph → [[0, w, e, o], [1, w, e, o], ...]
     enriches each triple with its position index. *)
  | "with-index" ->
    let items = eval_lst 0 in
    Some (VList (List.mapi (fun i item ->
      match as_list item with
      | [w; e; o] -> VList [VFloat (Float.of_int i); w; e; o]
      | _ -> VList [VFloat (Float.of_int i); item]
    ) items))

  (* nearest-before: indexed-graph pos edge-type → [idx, w, e, o] or VNone
     finds the nearest triple BEFORE pos with the given edge type.
     scans backward from pos-1 to 0. *)
  | "nearest-before" ->
    let ig = eval_lst 0 in
    let pos = eval_int 1 in
    let edge = eval_str 2 in
    let result = ref VNone in
    let i = ref (pos - 1) in
    while !i >= 0 && !result = VNone do
      (match as_list (List.nth ig !i) with
       | VFloat _ :: _ :: VString e :: _ when e = edge ->
         result := List.nth ig !i
       | _ -> ());
      decr i
    done;
    Some !result

  (* sentence-of: indexed-graph pos → sentence-index (float)
     counts how many viraam/dvandva boundaries appear before pos.
     two positions in the same sentence have the same sentence-of value. *)
  | "sentence-of" ->
    let ig = eval_lst 0 in
    let pos = eval_int 1 in
    let count = ref 0 in
    for j = 0 to pos - 1 do
      match as_list (List.nth ig j) with
      | _ :: _ :: VString e :: _ when e = "viraam" || e = "dvandva" ->
        incr count
      | _ -> ()
    done;
    Some (VFloat (Float.of_int !count))

  | _ -> None
