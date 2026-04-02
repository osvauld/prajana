(* kriya_ops.ml — pure primitive operations with no graph or session dependency.
   covers: string ops, list ops, boolean/comparison ops, constructors, numeric math.

   dependency: Prakriti, Kriya_types only.

   env is now immutable StringMap — no env_copy needed, just share. *)

open Kriya_types

(* spawn_chunks: spawn one domain per chunk of arr, run f on each, join all results.
   Falls back to sequential when n_workers <= 1 or list is tiny. *)
let spawn_chunks (arr : 'a array) (f : 'a array -> int -> int -> 'b list) : 'b list =
  let n = Array.length arr in
  let n_workers = min (max 1 (Domain.recommended_domain_count () - 1)) n in
  if n_workers <= 1 then f arr 0 n
  else begin
    let parent_ctx = Domain.DLS.get _eval_ctx in
    let chunk_size = (n + n_workers - 1) / n_workers in
    let domains = List.init n_workers (fun i ->
      let lo = i * chunk_size in
      let hi = min ((i + 1) * chunk_size) n in
      if lo >= n then None
      else Some (Domain.spawn (fun () ->
        Domain.DLS.set _eval_ctx parent_ctx;
        f arr lo hi))
    ) in
    List.concat_map (function None -> [] | Some d -> Domain.join d) domains
  end

type evaluator = Prakriti.proof_graph -> env -> expr -> value

let eval_pure_op (e_eval : evaluator) (k : Prakriti.proof_graph) (e : env) (op : string) (args : expr list)
    : value option =
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

  | "split-numeric" ->
    let s = eval_str 0 in
    let n = String.length s in
    let i = ref 0 in
    if !i < n && s.[!i] = '-' then incr i;
    while !i < n && (s.[!i] = '.' || (s.[!i] >= '0' && s.[!i] <= '9')) do incr i done;
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
    let num_val = match float_of_string_opt num_part with Some f -> Printf.sprintf "%g" f | None -> "" in
    Some (VList [VString num_val; VString alpha_part])

  | "to-string" ->
    Some (VString (eval_str 0))

  | "substr" ->
    let s   = eval_str 0 in
    let pos = eval_int 1 in
    let len = eval_int 2 in
    let slen = String.length s in
    let pos' = max 0 (min pos slen) in
    let len' = max 0 (min len (slen - pos')) in
    Some (VString (String.sub s pos' len'))

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
       let results = List.map (fun item ->
         let local = match params with
           | [p] -> StringMap.add p item captured
           | _ -> captured in
         e_eval k local body
       ) lst in
       Some (VList results)
     | _ -> Some (VList []))

  | "filter" ->
    let lst = eval_lst 0 in
    let fn_val = eval_arg 1 in
    (match fn_val with
     | VFn (params, body, captured) ->
       let results = List.filter (fun item ->
         let local = match params with
           | [p] -> StringMap.add p item captured
           | _ -> captured in
         as_bool (e_eval k local body)
       ) lst in
       Some (VList results)
     | _ -> Some (VList []))

  (* ---- parallel list operations (Domain.spawn + DLS propagation) ---- *)

  | "pmap" ->
    let lst = eval_lst 0 in
    let fn_val = eval_arg 1 in
    (match fn_val with
     | VFn (params, body, captured) ->
       let apply item =
         let local = match params with
           | [p] -> StringMap.add p item captured | _ -> captured in
         e_eval k local body in
       let arr = Array.of_list lst in
       let results = spawn_chunks arr (fun a lo hi ->
         let r = ref [] in
         for j = hi - 1 downto lo do r := apply a.(j) :: !r done;
         !r) in
       Some (VList results)
     | _ -> Some (VList []))

  | "pfilter" ->
    let lst = eval_lst 0 in
    let fn_val = eval_arg 1 in
    (match fn_val with
     | VFn (params, body, captured) ->
       let test item =
         let local = match params with
           | [p] -> StringMap.add p item captured | _ -> captured in
         as_bool (e_eval k local body) in
       let arr = Array.of_list lst in
       let results = spawn_chunks arr (fun a lo hi ->
         let r = ref [] in
         for j = hi - 1 downto lo do
           if test a.(j) then r := a.(j) :: !r
         done;
         !r) in
       Some (VList results)
     | _ -> Some (VList []))

  | "preduce" ->
    (* parallel reduce for list-append accumulators.
       (preduce list [] fn) — same signature as reduce.
       Each chunk reduces independently from init, then chunk results
       are merged by list concatenation (O(1) per chunk, not O(n) re-eval). *)
    let lst    = eval_lst 0 in
    let init   = eval_arg 1 in
    let fn_val = eval_arg 2 in
    (match fn_val with
     | VFn (params, body, captured) ->
       let fold item acc =
         let local = match params with
           | [pa; pb] -> captured |> StringMap.add pa acc |> StringMap.add pb item
           | _ -> captured in
         e_eval k local body in
       let arr = Array.of_list lst in
       let chunk_results = spawn_chunks arr (fun a lo hi ->
         let acc = ref init in
         for j = lo to hi - 1 do acc := fold a.(j) !acc done;
         [!acc]) in
       let merged = List.concat_map (function
         | VList items -> items | v -> [v]) chunk_results in
       Some (VList merged)
     | _ -> Some init)

  | "reduce" ->
    let lst     = eval_lst 0 in
    let init    = eval_arg 1 in
    let fn_val  = eval_arg 2 in
    (match fn_val with
     | VFn (params, body, captured) ->
       let acc = List.fold_left (fun acc item ->
         let local = match params with
           | [pa; pb] -> captured |> StringMap.add pa acc |> StringMap.add pb item
           | _ -> captured in
         e_eval k local body
       ) init lst in
       Some acc
     | _ -> Some init)

  | "fixpoint" ->
    let state0 = eval_arg 0 in
    let fn_val = eval_arg 1 in
    let apply_fn s = match fn_val with
      | VFn ([p], body, captured) ->
        let local = StringMap.add p s captured in
        e_eval k local body
      | _ -> s
    in
    let triple_count = function
      | VList a -> List.length a
      | VGraph g -> List.length g.gi_triples
      | _ -> -1
    in
    let rec loop s fuel =
      if fuel <= 0 then s
      else let n_before = triple_count s in
           let s' = apply_fn s in
           let n_after = triple_count s' in
           if n_before >= 0 && n_before = n_after then s'
           else loop s' (fuel - 1)
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

  | "str" ->
    (* str container idx — extract element at idx and coerce to string.
       Shorthand for (to-string (nth container idx)). *)
    let container = eval_arg 0 in
    let idx = eval_int 1 in
    let v = match container with
      | VPair (n, v) ->
        if idx = 0 then VString n else if idx = 1 then v else VNone
      | VBinding (n, f) ->
        if idx = 0 then VString n else if idx = 1 then VFloat f else VNone
      | _ ->
        let lst = as_list container in
        if idx >= 0 && idx < List.length lst then List.nth lst idx else VNone
    in
    Some (VString (as_string v))

  | "flatten" ->
    Some (VList (List.concat_map as_list (eval_lst 0)))

  | "append" ->
    let a = eval_lst 0 in
    let b = eval_lst 1 in
    Some (VList (a @ b))

  | "range" ->
    let n = eval_int 0 in
    Some (VList (List.init (max 0 n) (fun i -> VFloat (float_of_int i))))

  | "unique" ->
    let lst = eval_lst 0 in
    let seen = Hashtbl.create 16 in
    let unique = List.filter (fun v ->
      let key = as_string v in
      if Hashtbl.mem seen key then false
      else (Hashtbl.replace seen key true; true)
    ) lst in
    Some (VList unique)

  | "sum" ->
    let lst = eval_lst 0 in
    let total = List.fold_left (fun acc v -> acc +. as_float v) 0.0 lst in
    Some (VFloat total)

  (* ---- boolean / comparison ---- *)

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

  (* ---- numeric ---- *)

  | "add"   ->
    Some (VFloat (List.fold_left (fun acc arg -> acc +. as_float (e_eval k e arg)) 0.0 args))
  | "mul"   ->
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
  | "sin" | "sine"   -> Some (VFloat (sin   (eval_flt 0)))
  | "cos" | "cosine" -> Some (VFloat (cos   (eval_flt 0)))
  | "tan" | "tangent" -> Some (VFloat (tan  (eval_flt 0)))
  | "log"   -> Some (VFloat (log   (eval_flt 0)))
  | "exp"   -> Some (VFloat (exp   (eval_flt 0)))
  | "abs"   -> Some (VFloat (abs_float (eval_flt 0)))
  | "neg"   -> Some (VFloat (-. (eval_flt 0)))
  | "floor" -> Some (VFloat (floor (eval_flt 0)))
  | "ceil"  -> Some (VFloat (ceil  (eval_flt 0)))
  | "min"   -> Some (VFloat (Float.min (eval_flt 0) (eval_flt 1)))
  | "max"   -> Some (VFloat (Float.max (eval_flt 0) (eval_flt 1)))
  | "square" ->
    let a = eval_flt 0 in Some (VFloat (a *. a))
  | "half" ->
    Some (VFloat (eval_flt 0 *. 0.5))
  | "double" ->
    Some (VFloat (eval_flt 0 *. 2.0))
  | "reciprocal" ->
    Some (VFloat (1.0 /. eval_flt 0))

  (* ═══════════════════════════════════════════════════════════════════
     migrated tantras — trivial utility ops, formerly interpreted .tantra4
     ═══════════════════════════════════════════════════════════════════ *)

  (* ---- triple accessors ---- *)

  | "triple-subj" ->
    let t = as_list (eval_arg 0) in
    Some (VString (match List.nth_opt t 0 with Some v -> as_string v | None -> ""))

  | "triple-edge" ->
    Some (match List.nth_opt (as_list (eval_arg 0)) 1 with Some v -> v | None -> VNone)

  | "triple-obj" ->
    let t = as_list (eval_arg 0) in
    Some (VString (match List.nth_opt t 2 with Some v -> as_string v | None -> ""))

  | "triples-by-edge" ->
    let triples = eval_lst 0 in
    let edge_type = eval_str 1 in
    Some (VList (List.filter (fun t ->
      match t with
      | VList (_ :: VString e :: _) -> e = edge_type
      | VList (_ :: VNode e :: _)   -> e = edge_type
      | _ -> false
    ) triples))

  | "non-reflexive" ->
    let triples = eval_lst 0 in
    Some (VList (List.filter (fun t ->
      match t with
      | VList (s :: _ :: o :: _) -> as_string s <> as_string o
      | _ -> true
    ) triples))

  (* ---- simple predicates ---- *)

  | "has-text" ->
    Some (VBool (String.length (eval_str 0) > 0))

  | "has-items" ->
    Some (VBool (List.length (eval_lst 0) > 0))

  | "is-empty" ->
    Some (VBool (String.length (eval_str 0) = 0))

  | "is-system-concept" ->
    let w = eval_str 0 in
    Some (VBool (List.mem w ["count"; "count-total"; "count-remaining";
                             "viveka-max"; "viveka-min"]))

  (* ---- list / string utilities ---- *)

  | "last-of" ->
    let xs = eval_lst 0 in
    Some (match xs with [] -> VList [] | _ -> List.nth xs (List.length xs - 1))

  | "join-with" ->
    let items = eval_lst 0 in
    let sep = eval_str 1 in
    let non_empty = List.filter (fun s ->
      String.length (as_string s) > 0) items in
    Some (VString (String.concat sep (List.map as_string non_empty)))

  | "words-to-str" ->
    let words = eval_lst 0 in
    let non_empty = List.filter (fun s ->
      String.length (as_string s) > 0) words in
    Some (VString (String.concat " " (List.map as_string non_empty)))

  | "format-strand" ->
    let label = eval_str 0 in
    let content = eval_str 1 in
    Some (VString (if String.length content > 0
      then label ^ " " ^ content else ""))

  | "word-bigrams" ->
    let words = eval_lst 0 in
    let arr = Array.of_list words in
    let n = Array.length arr in
    Some (VList (List.init (max 0 (n - 1)) (fun i ->
      VString (as_string arr.(i) ^ "-" ^ as_string arr.(i + 1)))))

  (* ---- grade / graph query utilities ---- *)

  | "grade-mithya" ->
    let grade = eval_lst 0 in
    Some (VList (List.filter_map (fun t ->
      match t with
      | VList (s :: VString "mithya" :: _) -> Some (VString (as_string s))
      | VList (s :: VNode "mithya" :: _) -> Some (VString (as_string s))
      | _ -> None
    ) grade))

  | "grade-numbers" ->
    let grade = eval_lst 0 in
    Some (VList (List.filter_map (fun t ->
      match t with
      | VList (_ :: VString "asprista-sankhya" :: o :: _) -> Some o
      | VList (_ :: VNode "asprista-sankhya" :: o :: _) -> Some o
      | _ -> None
    ) grade))

  | "is-question-grade" ->
    let grade = eval_lst 0 in
    Some (VBool (List.exists (fun t ->
      match t with
      | VList (_ :: VString "vidhi-kaala" :: _) -> true
      | VList (_ :: VNode "vidhi-kaala" :: _) -> true
      | _ -> false
    ) grade))

  | "concept-in-grade" ->
    let concept = eval_str 0 in
    let grade = eval_lst 1 in
    Some (VBool (List.exists (fun t ->
      match t with
      | VList (s :: VString "satya" :: _) -> as_string s = concept
      | VList (s :: VNode "satya" :: _) -> as_string s = concept
      | _ -> false
    ) grade))

  | "last-concept" ->
    let grade = eval_lst 0 in
    let last = List.fold_left (fun acc t ->
      match t with
      | VList (s :: VString "satya" :: _) -> as_string s
      | VList (s :: VNode "satya" :: _) -> as_string s
      | _ -> acc
    ) "" grade in
    Some (VString last)

  | "user-concepts" ->
    let graph = eval_lst 0 in
    let system = ["count"; "count-total"; "count-remaining";
                   "viveka-max"; "viveka-min"] in
    let seen = Hashtbl.create 16 in
    let result = List.filter_map (fun t ->
      match t with
      | VList (s :: VString "satya" :: _)
      | VList (s :: VNode "satya" :: _) ->
        let name = as_string s in
        if List.mem name system || Hashtbl.mem seen name then None
        else (Hashtbl.replace seen name true; Some (VString name))
      | _ -> None
    ) graph in
    Some (VList result)

  (* ---- signal read / write ---- *)

  | "read-signal" ->
    let graph = eval_lst 0 in
    let signal_name = eval_str 1 in
    let found = List.find_map (fun t ->
      match t with
      | VList [VString "_signal"; VString e; o] when e = signal_name -> Some o
      | VList [VString "_signal"; VNode e; o] when e = signal_name -> Some o
      | _ -> None
    ) graph in
    Some (match found with Some v -> v | None -> VNone)

  | "write-signals" ->
    let graph = eval_lst 0 in
    let pairs = eval_lst 1 in
    let signals = List.filter_map (fun kv ->
      match as_list kv with
      | [k; v] -> Some (VList [VString "_signal"; VString (as_string k); v])
      | _ -> None
    ) pairs in
    Some (VList (graph @ signals))

  (* ---- word-info field accessor ---- *)

  | "word-info" ->
    let info = eval_lst 0 in
    let field = eval_str 1 in
    let idx = match field with
      | "node" -> 0 | "role" -> 1 | "layer" -> 2
      | "num-val" -> 3 | "unit" -> 4 | "candidates" -> 5
      | _ -> -1 in
    Some (if idx >= 0 && idx < List.length info
      then List.nth info idx else VString "")

  (* ---- verb stem matching ---- *)

  | "word-stem" ->
    (* crude verb stem: strip -ing, -ed, -s for surface-form matching *)
    let w = eval_str 0 in
    let n = String.length w in
    let stem =
      if n > 4 && String.sub w (n-3) 3 = "ing" then String.sub w 0 (n-3)
      else if n > 3 && String.sub w (n-2) 2 = "ed" then String.sub w 0 (n-2)
      else if n > 2 && w.[n-1] = 's' then String.sub w 0 (n-1)
      else w
    in
    Some (VString stem)

  | "stems-match" ->
    (* true if two words share the same crude stem *)
    let stem w =
      let n = String.length w in
      if n > 4 && String.sub w (n-3) 3 = "ing" then String.sub w 0 (n-3)
      else if n > 3 && String.sub w (n-2) 2 = "ed" then String.sub w 0 (n-2)
      else if n > 2 && w.[n-1] = 's' then String.sub w 0 (n-1)
      else w
    in
    Some (VBool (stem (eval_str 0) = stem (eval_str 1)))

  | "question-words" ->
    (* find question grade (has vidhi-kaala), return its mithya subjects *)
    let grades = eval_lst 0 in
    let q_grade = List.fold_left (fun acc grade ->
      let items = as_list grade in
      if List.exists (fun t -> match t with
        | VList (_ :: VString "vidhi-kaala" :: _) -> true
        | VList (_ :: VNode "vidhi-kaala" :: _) -> true
        | _ -> false) items
      then items else acc
    ) [] grades in
    Some (VList (List.filter_map (fun t ->
      match t with
      | VList (s :: VString "mithya" :: _) -> Some (VString (as_string s))
      | VList (s :: VNode "mithya" :: _) -> Some (VString (as_string s))
      | _ -> None
    ) q_grade))

  | _ -> None
