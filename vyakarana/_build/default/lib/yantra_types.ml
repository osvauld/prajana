(* extracted from yantra.ml: types + value coercions *)
(* ---- types ---- *)

type tantra_param = {
  tp_name      : string;        (* as written in .tantra: "mass", "velocity" *)
  tp_canonical : string;        (* graph-resolved: "mass", "kaala" *)
  tp_type      : string;        (* "float", "int" *)
  tp_unit      : string option; (* Some "kilogram", None *)
  tp_avastha   : string option; (* Some "purva" | Some "uttara" | None *)
}

(* expression tree for the let-block RHS *)
type expr =
  | Lit      of float
  | Var      of string
  | Call     of string * expr list    (* op name, arguments *)
  | StrLit   of string                (* "hello" *)
  | BoolLit  of bool                  (* true, false *)
  | ListExpr of expr list             (* [a, b, c] *)
  | Lambda   of string list * expr    (* fn x y -> body *)
  | Cond     of (expr * expr) list * expr  (* cond [(guard, body); ...] otherwise *)
  | LetIn    of string * expr * expr  (* let x = e1 in e2 *)

(* runtime value — what expressions evaluate to *)
type value =
  | VFloat   of float
  | VString  of string
  | VBool    of bool
  | VNode    of string              (* graph node name — exists in graph *)
  | VList    of value list
  | VPair    of string * value      (* named pair: (name, classified-value) *)
  | VBinding of string * float      (* concept = number *)
  | VNone                           (* nothing found / lookup miss *)
  | VFn      of string list * expr * env  (* closure: params, body, captured env *)

and env = (string, value) Hashtbl.t

type tantra = {
  t_name    : string;                         (* "force", "addition" *)
  t_file    : string;                         (* file path *)
  t_inputs  : tantra_param list;
  t_lets    : (string * expr) list;           (* [(name, rhs); ...] *)
  t_returns : tantra_param list;
}

type tantra_index = {
  by_name      : (string, tantra) Hashtbl.t;
  by_output    : (string, tantra list) Hashtbl.t;
  by_input     : (string, tantra list) Hashtbl.t;
  constants    : (string, float) Hashtbl.t;
  conversions  : (string * string, tantra) Hashtbl.t;
  all_tantras  : tantra list ref;
  word_index   : (string, string) Hashtbl.t;  (* word: key → node-name *)
}

type binding = {
  b_name       : string;        (* concept name: "mass", "force", "kaala" *)
  b_value      : float;
  b_unit       : string option;
  b_timestamp  : float;         (* Unix.gettimeofday() at write time *)
  b_source     : string;        (* "user" | "tantra:<name>" | "imu" | "inferred" | "problem-sentence-N" *)
  b_confidence : float;         (* 0.0–1.0, default 1.0 *)
  b_ttl        : float option;  (* seconds until stale; None = permanent *)
}

type session = {
  mutable bindings      : binding list;
  mutable last_result   : (string * float) list;
  mutable history       : string list;
  mutable context_seeds : string list;
}

type yantra_result = {
  yr_output     : (string * float) list;   (* [(name, value); ...] *)
  yr_tantra     : string;                  (* tantra name used *)
  yr_code       : string;                  (* emitted OCaml source *)
  yr_raw_output : string;                  (* raw stdout from OCaml *)
}

(* ---- scene comprehension types ---- *)

(* one level in an entity's krama (derivative) stack.
   depth 0 = position/displacement, 1 = velocity, 2 = acceleration, 3 = jerk.
   each depth IS the kramanusara of the one below it wrt time.
   the unit is a consequence of the depth — not stored, derivable via matra-viveka. *)
type krama_state = {
  ks_depth   : int;            (* kramanusara depth: 0,1,2,3,... *)
  ks_concept : string;         (* "displacement","velocity","acceleration","jerk" *)
  ks_binding : binding option; (* measured value + unit; None if unknown/derived *)
}

(* a physical entity — the thing that HAS state and undergoes change.
   e_krama is the full derivative stack, ordered by depth.
   e_spanda is omega — if set, jerk loops back to velocity: j = -ω²·v.
   this is the closure that makes oscillation. *)
type entity = {
  e_id      : int;
  e_label   : string;           (* surface word: "ball", "block", "particle", "spring" *)
  e_krama   : krama_state list; (* ordered derivative stack — the state trajectory *)
  e_spanda  : float option;     (* ω — if non-zero: entity is oscillating (spanda) *)
  e_context : binding list;     (* other properties: mass, charge, radius, etc. *)
}

(* a sandhi — where two or more krama chains meet and interact.
   collision, connection, contact — any junction that changes the trajectory. *)
type sandhi = {
  sh_kind     : string;     (* "collision","connection","contact","compression" *)
  sh_entities : int list;   (* entity ids involved *)
  sh_time     : float option (* when in the krama sequence — None if not specified *)
}

(* a process — what transforms purva-avastha into uttara-avastha for a set of entities.
   the sangati tells you the structural kind: gati, sandhi, spanda.
   purva and uttara hold the before/after bindings per entity. *)
type process = {
  pr_sangati  : string;                       (* "gati","sandhi","spanda","kramanusara" *)
  pr_entities : int list;                     (* which entity ids are involved *)
  pr_purva    : (int * binding list) list;    (* entity_id → measured before-state *)
  pr_uttara   : (int * binding list) list;    (* entity_id → measured after-state *)
  pr_target   : (int option * string) option; (* (entity_id, concept) to compute *)
}

(* the full scene — all entities, all processes, the sandhi interaction points,
   the krama sequence order, and what needs to be found.
   sc_targets: list of (entity_id option, concept) — None entity = any/all. *)
type scene = {
  sc_entities  : entity list;
  sc_processes : process list;
  sc_sandhis   : sandhi list;
  sc_krama_seq : int list;                    (* process ids in time order *)
  sc_targets   : (int option * string) list;  (* what to find *)
}

(* ---- value coercions ---- *)
(* placed here so they are available to all downstream modules without
   creating a circular dependency. yantra_resolver.ml used to define
   these but they logically belong with the value type. *)

(* convenience constructor — fills new metadata fields with defaults *)
let make_binding ?(unit_=None) ?(source="user") ?(confidence=1.0) ?(ttl=None) name value : binding =
  { b_name = name; b_value = value; b_unit = unit_;
    b_timestamp = Unix.gettimeofday (); b_source = source;
    b_confidence = confidence; b_ttl = ttl }

let new_env () : env = Hashtbl.create 16

let as_float = function
  | VFloat f -> f
  | VString s -> (match float_of_string_opt s with Some f -> f | None -> 0.0)
  | VBool b -> if b then 1.0 else 0.0
  | _ -> 0.0

let rec as_string = function
  | VString s -> s
  | VFloat f ->
    if Float.is_integer f && Float.is_finite f then
      Printf.sprintf "%g" f
    else Printf.sprintf "%g" f
  | VBool b -> if b then "true" else "false"
  | VNode n -> n
  | VPair (n, v) -> Printf.sprintf "(%s . %s)" n (as_string v)
  | VBinding (n, v) -> Printf.sprintf "%s=%g" n v
  | VNone -> ""
  | VList items ->
    "[" ^ String.concat ", " (List.map as_string items) ^ "]"
  | VFn _ -> "<fn>"

let as_bool = function
  | VBool b -> b
  | VNone -> false
  | VFloat f -> f <> 0.0
  | VString s -> String.length s > 0
  | VList l -> l <> []
  | VNode _ -> true
  | VPair _ -> true
  | VBinding _ -> true
  | VFn _ -> true

let as_list = function
  | VList l -> l
  | VNone -> []
  | v -> [v]

