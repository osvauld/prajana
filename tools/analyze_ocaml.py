#!/usr/bin/env python3
"""
analyze_ocaml.py — structural analysis of the vyakarana OCaml source.

Finds:
  - Tantra1 vs tantra2 boundary: which files/features belong to each
  - Recurring patterns: arg extraction, node lookup, ctx set/restore, json fields
  - Abstractions worth extracting: named helpers that collapse repeated shapes
  - Dead code: tantra1-only features safe to remove if all .tantra → .tantra2
  - Module responsibility map: what each .ml file does

Does NOT require a running server — reads source files directly.

Usage:
    python3 tools/analyze_ocaml.py [--vyakarana ./vyakarana] [--json]
    python3 tools/analyze_ocaml.py --report patterns
    python3 tools/analyze_ocaml.py --report tantra1

Reports: all, modules, tantra1, patterns, abstractions, dead
"""

import re, os, sys, json, glob, argparse
from collections import Counter, defaultdict

VYAKARANA_DEFAULT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vyakarana"
)


def load_sources(vyakarana_dir: str) -> dict[str, list[str]]:
    """Load all .ml files (excluding _build) as {filename: [lines]}."""
    files = {}
    for path in sorted(
        glob.glob(os.path.join(vyakarana_dir, "**", "*.ml"), recursive=True)
    ):
        if "/_build/" in path:
            continue
        name = os.path.basename(path)
        try:
            files[name] = open(path).readlines()
        except:
            pass
    return files


def all_lines(files: dict) -> list[tuple[str, str]]:
    return [(fname, line.rstrip()) for fname, lines in files.items() for line in lines]


# ── tantra1 vs tantra2 detection ─────────────────────────────────────────────

TANTRA1_MARKERS = [
    r"parse_tantra_file\b",
    r"yantra_tantra_file\b",
    r"Yantra_tantra_file\b",
    r'\.tantra"',
    r'check_suffix.*\.tantra"',
    r"tantra1",
    r"try_sentence_form",
    r'section.*"inputs"',
    r'section.*"let"',
    r'section.*"return"',
    r"tp_avastha",
    r"yr_code",
    r"yr_output",
]

TANTRA2_MARKERS = [
    r"parse_tantra2_file\b",
    r"yantra_tantra_file2\b",
    r"Yantra_tantra_file2\b",
    r'\.tantra2"',
    r'check_suffix.*\.tantra2"',
    r"parse_scan_block",
    r"parse2_expr",
    r"tantra2",
]

# ── recurring pattern detectors ──────────────────────────────────────────────

PATTERNS = {
    "arg_extract": {
        "regex": r"e_eval k e \(List\.nth args \d+\)",
        "desc": "eval + arg extraction (e_eval k e (List.nth args N))",
        "abstraction": "eval_arg N e_eval k e args  — typed helper, removes index errors",
    },
    "node_lookup": {
        "regex": r"Hashtbl\.find_opt.*\.nodes\b|Proof_graph\.find k\b",
        "desc": "graph node lookup (Hashtbl.find_opt k.nodes / Proof_graph.find k)",
        "abstraction": "with_node k name ~default (fun n -> ...)  — one line, exception-safe",
    },
    "eval_ctx_set": {
        "regex": r"eval_ctx :=",
        "desc": "eval_ctx set/restore (eval_ctx := Some / None)",
        "abstraction": "with_eval_ctx idx session (fun () -> ...)  — automatic restore",
    },
    "json_field": {
        "regex": r'json_string_field|json_int_field|Option\.value ~default:""',
        "desc": "JSON field extraction (json_string_field / Option.value ~default)",
        "abstraction": 'req_field line "f" / opt_field line "f" ~default:""',
    },
    "error_response": {
        "regex": r"error_response\b",
        "desc": "socket error response emission",
        "abstraction": "already one call — consistent, no change needed",
    },
    "edge_filter": {
        "regex": r"List\.filter_map \(fun edge ->.*edge\.(source|relation|target)",
        "desc": "edge filter (List.filter_map on typed_edge with field checks)",
        "abstraction": "edges_where k name ~src ~rel ~tgt  — named args",
    },
    "tantra_call": {
        "regex": r"Hashtbl\.find_opt.*by_name.*\n.*eval_tantra\b|find_opt.*by_name.*Some t.*eval_tantra",
        "desc": "tantra lookup + eval (find_opt by_name + eval_tantra)",
        "abstraction": "call_tantra_opt k idx name inputs ~default:VNone",
    },
    "as_string_coerce": {
        "regex": r"as_string \(e_eval k e",
        "desc": "as_string coercion after eval",
        "abstraction": "eval_string e_eval k e expr  — combined",
    },
}


# ── OCaml → tantra migration analysis ────────────────────────────────────────
#
# The question: which OCaml ops in yantra_ops.ml and yantra_eval_primitives.ml
# could be expressed as tantra2 and removed from OCaml?
#
# The boundary: an op CAN move to tantra if and only if:
#   1. It is DEFINED purely in terms of other primitives (not C FFI, not mutable state)
#   2. It takes no proof_graph reference for node lookup — or only uses ops
#      that ARE primitives (walk, walk-in, edges, etc.)
#   3. It adds NO new computational power — it is a composition of existing ops
#   4. The tantra form is MORE readable and MORE testable than the OCaml form
#   5. Performance is not critical (graph operations that run O(E) per call
#      should stay in OCaml until the evaluator is fast enough)
#
# The boundary the OTHER way — things that MUST stay in OCaml:
#   A. Anything that touches Hashtbl / proof_graph internal representation
#   B. Anything that touches mutable state (all_edges ref, CSR matrix)
#   C. Anything that requires the OCaml type system (VFn application, as_list coerce)
#   D. Anything that is a control structure (eval, scan, fixpoint, reduce)
#      — these ARE the interpreter; they cannot be expressed in the language they run
#   E. Anything that bridges OCaml modules (Setu, Anuvada, Proof_graph calls)
#   F. Performance-critical inner loops (PPR, CSR SpMV, large graph walks)
#
# Philosophy: the line is sthita (situated-ness).
#   An op belongs in tantra if its sthita is the graph-of-tantras (brahman).
#   An op belongs in OCaml if its sthita is the evaluator (yantra) itself.
#   Composition belongs in brahman. Execution belongs in yantra.

# Category A: IRREDUCIBLE — must stay in OCaml forever
# These are the substrate. Tantra is written in terms of these.
OCAML_CATEGORY_A = {
    # control structures — the interpreter cannot interpret itself
    "eval": "core evaluator — IS the interpreter",
    "scan": "stateful graph scan — requires mutable OCaml state per item",
    "fixpoint": "convergence loop — requires mutable comparison across iterations",
    "reduce": "fold with accumulator — fn application requires VFn dispatch",
    "map": "list transform — fn application requires VFn dispatch",
    "filter": "list predicate filter — fn application requires VFn dispatch",
    # graph substrate — direct proof_graph structure access
    "walk": "outgoing edge traversal — CSR/adjacency direct access",
    "walk-in": "incoming edge traversal — reverse adjacency direct access",
    "edges": "all edges of node — raw typed_edge list",
    "all-edges": "full graph edge dump — raw all_edges ref",
    "outgoing-edges": "filtered edge dump — raw all_edges ref",
    "incoming-to": "incoming edge filter — raw typed_edge fields",
    "emit-node": "graph mutation — Hashtbl.replace on k.nodes",
    "emit-edge": "graph mutation — appends to k.all_edges ref",
    "graph-node-count": "graph introspection — Hashtbl.length k.nodes",
    "graph-all-nodes": "graph introspection — Hashtbl.fold k.nodes",
    "graph-edge-count": "graph introspection — List.length !k.all_edges",
    "ppr": "PPR algorithm — CSR SpMV inner loop, performance-critical",
    "register-dimension": "dimension registry mutation — Hashtbl side-effect",
    "lookup": "node existence check — raw Hashtbl.find_opt k.nodes",
    "exists": "list membership — O(n) scan, structural",
    # type coercions and primitives — required by the type system
    "eq": "string equality — as_string coercion, polymorphic",
    "neq": "string inequality — as_string coercion, polymorphic",
    "and": "variadic boolean and — requires lazy eval of args",
    "or": "variadic boolean or — requires lazy eval of args",
    "not": "boolean negation — structural",
    "nth": "positional extraction — handles VPair/VBinding/VList polymorphically",
    "length": "list/string length — structural",
    "append": "list concat — structural",
    "flatten": "list of lists → list — structural",
    "pair": "VPair constructor — type system",
    "bind": "VBinding constructor — type system",
    # math: irreducible — these ARE the math domain
    "add": "addition — monoid primitive",
    "mul": "multiplication — monoid primitive",
    "sub": "subtraction — primitive",
    "div": "division with zero guard — primitive",
    "power": "exponentiation — primitive",
    "sqrt": "square root — C math",
    "sin": "sine — C math",
    "cos": "cosine — C math",
    "tan": "tangent — C math",
    "asin": "arcsine — C math",
    "acos": "arccosine — C math",
    "atan2": "2-arg arctangent — C math",
    "log": "natural log — C math",
    "exp": "exponential — C math",
    "abs": "absolute value — C math",
    "neg": "negation — primitive",
    "floor": "floor — C math",
    "ceil": "ceiling — C math",
    "mod": "modulo — C math",
    "min": "minimum — C math",
    "max": "maximum — C math",
    # string: irreducible
    "split": "string split — OCaml Str.split",
    "concat": "string concat — variadic, requires args list",
    "join": "list join with sep — OCaml String.concat",
    "char-at": "character access — string index",
    "string-length": "string length — String.length",
    "to-string": "value coercion — as_string dispatch",
    "to-number": "string→float — float_of_string_opt",
    "split-numeric": "numeric prefix split — stateful index scan",
    "starts-with": "prefix check — String.sub",
    "ends-with": "suffix check — String.sub",
    "member": "list membership — as_string comparison fold",
    "upper": "uppercase — String.uppercase_ascii",
    "lower": "lowercase — String.lowercase_ascii",
    "substr": "substring — String.sub with clamping",
    # graph field accessors — require proof_graph struct access
    "shabda": "shabda field lookup — raw node.shabda field",
    "raw-shabda": "raw shabda string — raw node.shabda field",
    "shabda-pairs": "shabda key-value pairs — Setu.read_shabda",
    "name": "node name field — node.name",
    "kind": "node kind — node.layer",
    "node": "VNode constructor — type constructor",
    "value": "node raw value — node.raw_value",
    "node-satya": "satya score — node.satya field",
    "node-layer": "layer string — node.layer field",
    "node-slokas": "raw slokas — node.slokas field",
    "context-score": "PPR score — run_ppr result",
    "ancestors-of": "inheritance walk — walk_inheritance internal",
    "walk-chain": "BFS over kriya/phala — Setu.walk_chain",
    "resolve-node": "abheda resolution — Setu.resolve",
    "session-bindings": "session state read — se_yantra.bindings",
    "remember-bindings": "session state write — se_yantra.bindings mutation",
    "debug-print": "stderr print — Printf.eprintf side effect",
    "print": "stdout print — Printf.printf side effect",
}

# Category B: COMPOSED — currently in OCaml, expressible as tantra
# These are the migration targets. Each one is a composition of Category A ops.
# Moving them to brahman/yantra/ makes them:
#   - testable (every tantra can be eval'd directly)
#   - readable (the composition is visible in the graph language)
#   - modifiable (no rebuild needed to change them)
#   - philosophically named (their role in the knowledge graph is clear)
OCAML_CATEGORY_B = {
    "square": {
        "ocaml": "a *. a",
        "tantra": "mul x x",
        "philosophy": "square = self-multiplication. kriya of a number applied to itself. already in math kosha as 'power 2' — square is one path, power is another. both belong in brahman.",
        "file": "yantra_ops.ml",
        "calls_in_tantras": 0,  # filled by analysis
        "already_in_kosha": True,  # math kosha has 'square' as a node
    },
    "half": {
        "ocaml": "a *. 0.5",
        "tantra": "mul x 0.5",
        "philosophy": "half = division by two. already in math kosha as 'halving'. the tantra form makes the relation to the math graph explicit.",
        "file": "yantra_ops.ml",
        "calls_in_tantras": 0,
        "already_in_kosha": True,
    },
    "double": {
        "ocaml": "a *. 2.0",
        "tantra": "mul x 2",
        "philosophy": "double = multiplication by two. symmetric to half. its pratipaksha (inverse) is half.",
        "file": "yantra_ops.ml",
        "calls_in_tantras": 0,
        "already_in_kosha": True,
    },
    "reciprocal": {
        "ocaml": "1.0 /. a",
        "tantra": "div 1 x",
        "philosophy": "reciprocal = the inverse under multiplication. the pratipaksha of multiplication is division. 1/x is the generator of that inverse.",
        "file": "yantra_ops.ml",
        "calls_in_tantras": 0,
        "already_in_kosha": True,
    },
    "sum": {
        "ocaml": "List.fold_left (+.) 0.0",
        "tantra": "reduce list 0 (fn acc x -> add acc x)",
        "philosophy": "sum = total sankhya. the bandha of all sankhya values into one. already expressible as reduce + add.",
        "file": "yantra_ops.ml",
        "calls_in_tantras": 0,
        "already_in_kosha": False,
    },
    "sort-desc": {
        "ocaml": "List.sort compare (score_of_pair b) (score_of_pair a)",
        "tantra": "reduce + sort pattern — complex, defer",
        "philosophy": "sort-desc = viveka applied to a list. the highest satya rises to the top. direction of inquiry determines the ordering.",
        "file": "yantra_ops.ml",
        "calls_in_tantras": 0,
        "already_in_kosha": False,
        "note": "deferred — sort requires comparison that tantra2 doesn't have natively yet",
    },
    "reverse": {
        "ocaml": "List.rev lst",
        "tantra": "reduce list [] (fn acc x -> append [x] acc)",
        "philosophy": "reverse = pratipaksha of sequence order. the last becomes first.",
        "file": "yantra_ops.ml",
        "calls_in_tantras": 0,
        "already_in_kosha": False,
    },
    "take": {
        "ocaml": "List.filteri (fun i _ -> i < n)",
        "tantra": "filter list (fn x -> lt (index x) n)  -- index not available; use reduce with count",
        "philosophy": "take = apeksha (selection with bound). bounded sparsha — touch only the first N.",
        "file": "yantra_ops.ml",
        "calls_in_tantras": 0,
        "already_in_kosha": False,
        "note": "deferred — requires index tracking not yet in tantra2",
    },
    "drop": {
        "ocaml": "List.filteri (fun i _ -> i >= n)",
        "tantra": "symmetric to take — same deferred status",
        "philosophy": "drop = visarjana (release of the first N). the complement of take.",
        "file": "yantra_ops.ml",
        "calls_in_tantras": 0,
        "already_in_kosha": False,
        "note": "deferred — requires index tracking",
    },
    "first-match": {
        "ocaml": "List.find_map (fn item -> match result with VNone -> None | _ -> Some r)",
        "tantra": "nth (filter list fn) 0",
        "philosophy": "first-match = sparsha at its sharpest. the first contact that yields something real (not VNone). already expressible as filter + nth.",
        "file": "yantra_ops.ml",
        "calls_in_tantras": 0,
        "already_in_kosha": False,
    },
    "frequencies": {
        "ocaml": "Hashtbl count fold",
        "tantra": "reduce list {} (fn acc x -> ...)  -- requires dict not yet in tantra2",
        "philosophy": "frequencies = the count of each distinct sparsha. viveka at the aggregate level — how many times was each thing touched?",
        "file": "yantra_ops.ml",
        "calls_in_tantras": 0,
        "already_in_kosha": False,
        "note": "deferred — requires dict/map value type",
    },
    "unique": {
        "ocaml": "Hashtbl dedup via seen table",
        "tantra": "reduce list [] (fn acc x -> cond (member x acc) acc otherwise (append acc [x]))",
        "philosophy": "unique = viveka applied to a sequence. each element appears once — the first time it is seen, it is bound; subsequent appearances are visarjana (released).",
        "file": "yantra_ops.ml",
        "calls_in_tantras": 0,
        "already_in_kosha": False,
    },
    "zip": {
        "ocaml": "List.init n (fun i -> VList [nth a i; nth b i])",
        "tantra": "map (range (length a)) (fn i -> [(nth a i), (nth b i)])",
        "philosophy": "zip = dvandva of two sequences. each element is paired with its counterpart. the pairing is the relation.",
        "file": "yantra_ops.ml",
        "calls_in_tantras": 0,
        "already_in_kosha": False,
    },
    "range": {
        "ocaml": "List.init n (fun i -> VFloat i)",
        "tantra": "-- recursive: not expressible without fixpoint over counter; defer",
        "philosophy": "range = the sequence of integers from 0 to n-1. kriyakrama (sequential action). already used by tantras that need indexed iteration.",
        "file": "yantra_ops.ml",
        "calls_in_tantras": 0,
        "already_in_kosha": False,
        "note": "borderline — used as loop counter. keep in OCaml for now",
    },
    # Vec ops — Category B but lower priority
    "vec-add": {
        "ocaml": "List.map2 (+.)",
        "tantra": "map (zip a b) (fn xy -> add (nth xy 0) (nth xy 1))",
        "philosophy": "vec-add = component-wise addition. spatial translation in the pratibimba layer. already expressed by zip + map + add.",
        "file": "yantra_ops.ml",
        "calls_in_tantras": 0,
        "already_in_kosha": False,
    },
    "vec-sub": {
        "ocaml": "List.map2 (-.)  ",
        "tantra": "map (zip a b) (fn xy -> sub (nth xy 0) (nth xy 1))",
        "philosophy": "vec-sub = component-wise subtraction. the pratipaksha of vec-add.",
        "file": "yantra_ops.ml",
        "calls_in_tantras": 0,
        "already_in_kosha": False,
    },
    "vec-scale": {
        "ocaml": "List.map (s *. a_i)",
        "tantra": "map vec (fn x -> mul s x)",
        "philosophy": "vec-scale = scalar multiplication. the simplest kriya on a vector.",
        "file": "yantra_ops.ml",
        "calls_in_tantras": 0,
        "already_in_kosha": False,
    },
    "vec-dot": {
        "ocaml": "List.fold_left2 (acc + a*b) 0.0",
        "tantra": "sum (map (zip a b) (fn xy -> mul (nth xy 0) (nth xy 1)))",
        "philosophy": "vec-dot = inner product. the total affinity between two vectors. sum of component-wise multiplications.",
        "file": "yantra_ops.ml",
        "calls_in_tantras": 0,
        "already_in_kosha": False,
    },
    "vec-norm": {
        "ocaml": "sqrt(fold_left (acc + a*a) 0.0)",
        "tantra": "sqrt (sum (map vec (fn x -> mul x x)))",
        "philosophy": "vec-norm = the magnitude. the self-inner-product under sqrt. pratipaksha of projection.",
        "file": "yantra_ops.ml",
        "calls_in_tantras": 0,
        "already_in_kosha": False,
    },
    "rot2d": {
        "ocaml": "cos/sin matrix application hardcoded",
        "tantra": "let c = cos theta  let s = sin theta  [(sub (mul x c) (mul y s)), (add (mul x s) (mul y c))]",
        "philosophy": "rot2d = rotation in 2D. a kriya of the spatial plane. expressible but verbose — keep in OCaml until pratibimba needs it frequently.",
        "file": "yantra_ops.ml",
        "calls_in_tantras": 0,
        "already_in_kosha": False,
        "note": "deferred — verbose but expressible",
    },
    "mat-mul": {
        "ocaml": "nested loop over Array — O(n³)",
        "tantra": "-- not expressible cleanly without nested map + range; defer",
        "philosophy": "mat-mul = composition of linear transforms. required for kinematic chains in pratibimba. the composition IS the pratipaksha structure.",
        "file": "yantra_ops.ml",
        "calls_in_tantras": 0,
        "already_in_kosha": False,
        "note": "deferred — O(n³), performance-sensitive, needs indexed array access",
    },
    # From yantra_eval_primitives — ops that delegate to a tantra anyway
    "to-english": {
        "ocaml": "dispatches to to-english.tantra if loaded, else Setu fallback",
        "tantra": "already a tantra — OCaml arm is the fallback only",
        "philosophy": "to-english = the shabda surface form of a node. the English name is the abheda of the node in natural language. the tantra already exists; the OCaml arm is dead once the tantra is loaded.",
        "file": "yantra_eval_primitives.ml",
        "calls_in_tantras": 0,
        "already_in_kosha": False,
        "note": "migration = remove OCaml fallback, require to-english.tantra to always be loaded",
    },
    "domain-of": {
        "ocaml": "dispatches to domain-of.tantra if loaded, else inline fallback",
        "tantra": "already a tantra — same pattern as to-english",
        "philosophy": "domain-of = the sthita (domain-situation) of a node. the graph already encodes this via sthita edges. the tantra walks those edges.",
        "file": "yantra_eval_primitives.ml",
        "calls_in_tantras": 0,
        "already_in_kosha": False,
        "note": "migration = remove OCaml fallback, require domain-of.tantra",
    },
}

# Migration readiness score: how close is each Category B op to being moved?
# Score: (0=not ready, 1=expressible but verbose, 2=expressible and clean, 3=already a tantra pattern)
MIGRATION_SCORES = {
    "square": (3, "mul x x — one line"),
    "half": (3, "mul x 0.5 — one line"),
    "double": (3, "mul x 2 — one line"),
    "reciprocal": (3, "div 1 x — one line"),
    "first-match": (2, "nth (filter list fn) 0 — already used this pattern in tantras"),
    "unique": (2, "reduce with member check — already used in tantras"),
    "vec-scale": (2, "map vec (fn x -> mul s x) — clean"),
    "vec-dot": (2, "sum (map (zip a b) ...) — needs zip"),
    "vec-norm": (2, "sqrt (sum (map ...)) — clean"),
    "vec-add": (2, "map (zip a b) ... — needs zip"),
    "vec-sub": (2, "map (zip a b) ... — needs zip"),
    "sum": (2, "reduce list 0 add — clean"),
    "zip": (1, "map range ... — needs range, which is borderline"),
    "reverse": (1, "reduce with prepend — works but O(n²) cons"),
    "to-english": (3, "already tantra — remove OCaml fallback"),
    "domain-of": (3, "already tantra — remove OCaml fallback"),
    "range": (1, "borderline — used as loop infra"),
    "sort-desc": (0, "needs comparison primitive first"),
    "frequencies": (0, "needs dict/map value type"),
    "take": (0, "needs index tracking"),
    "drop": (0, "needs index tracking"),
    "rot2d": (1, "expressible but verbose"),
    "mat-mul": (0, "performance-sensitive, nested loops"),
}


def analyze_migration_candidates(brahman_dir: str, files: dict) -> dict:
    """
    For each Category B op, count how many times it appears in tantras
    (as a call) vs how many times it appears in OCaml (as a dispatch case).
    This tells us: is it already being used from tantras? Is removing it safe?
    """
    # Load tantra sources
    tantra_src = {}
    for path in glob.glob(
        os.path.join(brahman_dir, "yantra", "**", "*.tantra2"), recursive=True
    ):
        try:
            name = os.path.basename(path).replace(".tantra2", "")
            tantra_src[name] = open(path).read()
        except:
            pass

    all_tantra = "\n".join(tantra_src.values())
    all_ocaml = "\n".join("".join(lines) for lines in files.values())

    results = {}
    for op_name, info in OCAML_CATEGORY_B.items():
        # count tantra call sites (the op name as a token)
        tantra_calls = len(re.findall(r"\b" + re.escape(op_name) + r"\b", all_tantra))
        # count which tantras call it
        calling_tantras = [
            name
            for name, src in tantra_src.items()
            if re.search(r"\b" + re.escape(op_name) + r"\b", src)
        ]
        score, score_note = MIGRATION_SCORES.get(op_name, (0, "unknown"))
        results[op_name] = {
            "tantra_call_count": tantra_calls,
            "calling_tantras": calling_tantras,
            "ocaml_form": info["ocaml"],
            "tantra_form": info["tantra"],
            "philosophy": info["philosophy"],
            "already_in_kosha": info.get("already_in_kosha", False),
            "note": info.get("note", ""),
            "migration_score": score,
            "migration_note": score_note,
            "file": info["file"],
        }

    # Sort by migration score desc, then by tantra_calls asc
    # (high score + low calls = easiest wins — ready to migrate, not yet depending on OCaml arm)
    return dict(
        sorted(
            results.items(),
            key=lambda x: (-x[1]["migration_score"], x[1]["tantra_call_count"]),
        )
    )


def analyze_patterns(files: dict) -> dict:
    results = {}
    lines = all_lines(files)
    full_src = {fname: "\n".join(l for l in lns) for fname, lns in files.items()}

    for pat_name, pat in PATTERNS.items():
        matches = []
        rx = re.compile(pat["regex"], re.MULTILINE | re.DOTALL)
        for fname, src in full_src.items():
            count = len(rx.findall(src))
            if count > 0:
                matches.append((fname, count))
        total = sum(c for _, c in matches)
        results[pat_name] = {
            "total": total,
            "by_file": sorted(matches, key=lambda x: x[1], reverse=True),
            "desc": pat["desc"],
            "abstraction": pat["abstraction"],
        }
    return results


def analyze_tantra1(files: dict, brahman_dir: str) -> dict:
    """Find all tantra1 usage and .tantra files."""
    lines = all_lines(files)
    full_src = {fname: "\n".join(l for l in lns) for fname, lns in files.items()}

    tantra1_by_file = {}
    tantra2_by_file = {}

    for fname, src in full_src.items():
        t1 = sum(1 for m in TANTRA1_MARKERS if re.search(m, src))
        t2 = sum(1 for m in TANTRA2_MARKERS if re.search(m, src))
        if t1 > 0:
            tantra1_by_file[fname] = t1
        if t2 > 0:
            tantra2_by_file[fname] = t2

    # count actual .tantra vs .tantra2 files
    tantra1_files = glob.glob(
        os.path.join(brahman_dir, "**", "*.tantra"), recursive=True
    )
    tantra2_files = glob.glob(
        os.path.join(brahman_dir, "**", "*.tantra2"), recursive=True
    )

    # tantra1-only features (safe to remove if all .tantra migrate)
    t1_only = {
        "yantra_sentence_parser.ml": "try_sentence_form sugar — only used by tantra1 parser",
        "tp_avastha on tantra_param": '"purva"/"uttara" state annotations — not used in tantra2',
        "tp_canonical / tp_unit": "graph-resolved canonical names, unit annotations — tantra2 unused",
        "by_output / by_input in tantra_index": "old planner indexes — replaced by match-mantra.tantra2",
        "yr_code / yr_output on yantra_result": '"emitted OCaml source" era artefacts — yr_raw_output only used',
        'section = "inputs"/"let"/"return"': "old block-section syntax — new-style inline takes/return used",
    }

    return {
        "tantra1_files_count": len(tantra1_files),
        "tantra2_files_count": len(tantra2_files),
        "tantra1_by_file": tantra1_by_file,
        "tantra2_by_file": tantra2_by_file,
        "tantra1_only_features": t1_only,
        "tantra1_sample_files": sorted(
            os.path.relpath(f, brahman_dir) for f in tantra1_files[:20]
        ),
    }


def analyze_modules(files: dict) -> dict:
    """Summarize each module's role based on content."""
    MODULE_ROLES = {
        "yantra_types.ml": "type definitions: expr, value, scan_stmt, tantra, session, entity, scene; coercions; AST→JSON",
        "yantra_eval.ml": "core evaluator: eval, eval_from, eval_scan, eval_tantra; pipeline entry points",
        "yantra_eval_primitives.ml": "primitive dispatch: eval_graph_op (walk,ppr,emit-node...); eval_call; arity registration",
        "yantra_ops.ml": "pure operations: string, list, math, logic primitives (eval_pure_op)",
        "yantra_pipeline_ops.ml": "pipeline operations: avrti-refine, kosha-expand, etc. (eval_pipeline_op)",
        "yantra_tantra_file.ml": "tantra1 parser: parse_tantra_file, parse_let_block, strip_comment",
        "yantra_tantra_file2.ml": "tantra2 parser: parse_tantra2_file, parse_scan_block_lines (922 lines)",
        "yantra_expr_parser.ml": "expression parser: parse_expr, parse_from, parse_scan, parse_cond",
        "yantra_tokeniser.ml": "tokeniser: tokenise_expr — splits tantra source into tokens",
        "yantra_arity.ml": "arity registry: op_arity, register_graph_op_arity, is_boundary",
        "yantra_sentence_parser.ml": "tantra1 sugar: try_sentence_form (sentence-style binding syntax)",
        "yantra_index.ml": "index builder: build_index, register_tantra, scan_graph_op_arities, apply_relation_axioms",
        "proof_graph.ml": "proof graph: nigamana, typed_edge, visheshanam; add/find/join; PPR (run_ppr)",
        "om_parser.ml": "om file parser: parse_om_dir, parse_om_file, shabda/slokas/edges",
        "setu.ml": "semantic bridge: classify_token, resolve, walk_chain, read_shabda",
        "setu_shabda.ml": "shabda reader: parse_shabda, raw_shabda_for_node",
        "setu_classify.ml": "token classification: Content/Number/Unit/Operator/...",
        "anuvada.ml": "translation: avrti_anuvada, render_darshana_to_buf, english_of_visheshanam",
        "socket.ml": "socket server: handle_client, all socket command handlers, session management",
        "vyakarana.ml": "main entry: arg parsing, server startup, graph loading",
        "event.ml": "event type definitions",
    }

    result = {}
    for fname, lines in files.items():
        src = "\n".join(lines)
        n_lines = len(lines)
        n_fns = len(re.findall(r"^let\b", src, re.MULTILINE))
        n_types = len(re.findall(r"^type\b", src, re.MULTILINE))
        has_t1 = any(re.search(m, src) for m in TANTRA1_MARKERS)
        has_t2 = any(re.search(m, src) for m in TANTRA2_MARKERS)
        result[fname] = {
            "lines": n_lines,
            "fns": n_fns,
            "types": n_types,
            "tantra1": has_t1,
            "tantra2": has_t2,
            "role": MODULE_ROLES.get(fname, "(no description)"),
        }
    return result


def print_report(files, patterns, tantra1, modules, migration=None, report="all"):
    SEP = "═" * 72

    if report in ("all", "modules"):
        print(SEP)
        print("  MODULE MAP")
        print(SEP)
        print(f"  {'module':<40} {'lines':>5} {'fns':>4} {'t1':>3} {'t2':>3}  role")
        print("  " + "-" * 90)
        for fname, m in sorted(
            modules.items(), key=lambda x: x[1]["lines"], reverse=True
        ):
            t1 = "✓" if m["tantra1"] else " "
            t2 = "✓" if m["tantra2"] else " "
            role = m["role"][:55]
            print(
                f"  {fname:<40} {m['lines']:>5} {m['fns']:>4} {t1:>3} {t2:>3}  {role}"
            )

    if report in ("all", "tantra1"):
        print(f"\n{SEP}")
        print("  TANTRA1 vs TANTRA2")
        print(SEP)
        print(f"  .tantra  files in brahman: {tantra1['tantra1_files_count']}")
        print(f"  .tantra2 files in brahman: {tantra1['tantra2_files_count']}")
        print()
        print("  tantra1 markers by file:")
        for f, c in sorted(
            tantra1["tantra1_by_file"].items(), key=lambda x: x[1], reverse=True
        ):
            print(f"    {f:<40} {c} markers")
        print()
        print("  tantra1-only features (safe to remove if all .tantra → .tantra2):")
        for feat, desc in tantra1["tantra1_only_features"].items():
            print(f"    {feat}")
            print(f"      → {desc}")
        if tantra1["tantra1_sample_files"]:
            print()
            print("  remaining .tantra files:")
            for f in tantra1["tantra1_sample_files"][:15]:
                print(f"    {f}")

    if report in ("all", "patterns"):
        print(f"\n{SEP}")
        print("  RECURRING PATTERNS")
        print(SEP)
        for pat_name, p in sorted(
            patterns.items(), key=lambda x: x[1]["total"], reverse=True
        ):
            print(f"\n  {pat_name} ({p['total']} total occurrences)")
            print(f"    pattern:     {p['desc']}")
            print(f"    abstraction: {p['abstraction']}")
            for fname, c in p["by_file"][:5]:
                print(f"    {fname:<40} {c}×")

    if report in ("all", "abstractions"):
        print(f"\n{SEP}")
        print("  ABSTRACTIONS TO EXTRACT")
        print(SEP)
        HIGH_VALUE = [
            (
                "eval_arg N e_eval k e args",
                "A",
                "yantra_eval_primitives.ml: eval + List.nth args N pattern (70+ occurrences)",
                "let eval_arg n e_eval k e args = e_eval k e (List.nth args n)",
                "removes index errors, makes arity visible at call site",
            ),
            (
                "with_node k name ~default f",
                "B",
                "eval_primitives + anuvada + socket: match Hashtbl.find_opt k.nodes (30+ occurrences)",
                "let with_node k name ~default f = match Proof_graph.find k name with Some n -> f n | None -> default",
                "one line instead of 3, named default, type-safe",
            ),
            (
                "with_eval_ctx idx session f",
                "C",
                "yantra_eval.ml: eval_ctx set/restore (4 occurrences, all identical)",
                "let with_eval_ctx idx session f = let prev = !eval_ctx in eval_ctx := Some{...}; let r = f() in eval_ctx := prev; r",
                "exception-safe restore, no prev_ctx boilerplate",
            ),
            (
                "req_field / opt_field line key",
                "D",
                "socket.ml: json_string_field + Option.value (20+ occurrences)",
                "let req_field l k = match json_string_field l k with Some v -> v | None -> raise Missing\nlet opt_field ~default l k = Option.value ~default (json_string_field l k)",
                "2x shorter, distinguishes required vs optional",
            ),
            (
                "edges_where k name ~src ~rel ~tgt",
                "E",
                "eval_primitives + proof_graph: List.filter_map on edges with field checks (15+ occurrences)",
                "let edges_where k name ?src ?rel ?tgt () = ...",
                "named args, no repetitive field access",
            ),
            (
                "call_tantra_opt k name inputs ~default",
                "F",
                "eval_primitives: find_opt by_name + eval_tantra (8+ occurrences)",
                "let call_tantra_opt k name inputs ~default = match !eval_ctx with Some ctx -> (match Hashtbl.find_opt ctx.ctx_index.by_name name with Some t -> !_eval_tantra_ref k t inputs | None -> default) | None -> default",
                "one line, consistent fallback",
            ),
        ]
        for sig, label, where, impl, benefit in HIGH_VALUE:
            print(f"\n  [{label}] {sig}")
            print(f"       where:   {where}")
            print(f"       impl:    {impl}")
            print(f"       benefit: {benefit}")

    if report in ("all", "dead"):
        print(f"\n{SEP}")
        print("  DEAD / LEGACY CODE (tantra1-only, safe to remove)")
        print(SEP)
        print("""
   yantra_sentence_parser.ml (36 lines)
     try_sentence_form: only called from yantra_tantra_file.ml
     if all .tantra → .tantra2: entirely dead

   tp_avastha / tp_canonical / tp_unit on tantra_param
     tantra2 uses plain string params — these fields unused after load
     present in type definition but never read at eval time

   by_output / by_input / conversions in tantra_index
     from old planner: "what produces force?" (now: match-mantra.tantra2)
     still populated but never read by any current tantra or socket command

   yr_code / yr_output on yantra_result
     yr_code: "emitted OCaml source" — code generation era artefact
     yr_output: [(name,float)] — numeric extraction era artefact
     only yr_raw_output and yr_tantra are used today

   "inputs" / "let" / "return" section keywords in parse_tantra_file
     old block-section syntax — superseded by inline "takes param" / "return val"
     still parsed for backwards compat — dead once all old .tantra files migrate
""")

    if report in ("all", "migration") and migration:
        print(f"\n{SEP}")
        print("  OCAML → TANTRA MIGRATION CANDIDATES")
        print(SEP)
        print("""
  BOUNDARY RULES — what can move and what cannot:

  CAN move (Category B — composed, expressible in tantra2):
    - Ops that are pure compositions of Category A primitives
    - Ops with no Hashtbl/proof_graph internal access
    - Ops where the tantra form is MORE readable than OCaml
    - Ops not performance-critical (not O(E) graph inner loops)

  CANNOT move (Category A — substrate, stays in OCaml forever):
    - Control structures: eval, scan, fixpoint, reduce, map, filter
      (these ARE the interpreter — cannot run in the language they run)
    - Graph substrate: walk, walk-in, emit-node, emit-edge, ppr
      (direct proof_graph struct access — Hashtbl, CSR matrix)
    - Type coercions: eq, neq, nth, append (polymorphic dispatch)
    - OCaml bridge calls: Setu.*, Anuvada.*, Proof_graph.*
    - Mutable state: session-bindings, remember-bindings, register-dimension

  Philosophy: composition belongs in brahman. execution belongs in yantra.
    The line is sthita (situated-ness): where does this op live naturally?
    If it lives in the graph-of-tantras, it belongs in brahman/yantra/.
    If it lives in the evaluator itself, it stays in yantra OCaml.
""")

        # Group by migration score
        score_3 = [
            (op, info) for op, info in migration.items() if info["migration_score"] == 3
        ]
        score_2 = [
            (op, info) for op, info in migration.items() if info["migration_score"] == 2
        ]
        score_1 = [
            (op, info) for op, info in migration.items() if info["migration_score"] == 1
        ]
        score_0 = [
            (op, info) for op, info in migration.items() if info["migration_score"] == 0
        ]

        def _print_group(label, ops):
            if not ops:
                return
            print(f"\n  ── {label}")
            for op, info in ops:
                calls = info["tantra_call_count"]
                callers = ", ".join(info["calling_tantras"][:3])
                print(f"  {op:<20} tantras using it: {calls:>3}×  ({callers})")
                print(f"    ocaml:   {info['ocaml_form']}")
                print(f"    tantra:  {info['tantra_form']}")
                print(f"    why:     {info['migration_note']}")
                if info["note"]:
                    print(f"    note:    {info['note']}")
                print(f"    philosophy: {info['philosophy'][:120]}")
                print()

        _print_group(
            "SCORE 3 — migrate immediately (one line, already in kosha)", score_3
        )
        _print_group("SCORE 2 — migrate next (expressible and clean)", score_2)
        _print_group("SCORE 1 — defer (expressible but verbose or borderline)", score_1)
        _print_group("SCORE 0 — keep in OCaml (not expressible yet)", score_0)

    print()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--vyakarana", default=VYAKARANA_DEFAULT)
    parser.add_argument("--brahman", default=None)
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--report",
        default="all",
        choices=[
            "all",
            "modules",
            "tantra1",
            "patterns",
            "abstractions",
            "dead",
            "migration",
        ],
    )
    args = parser.parse_args()

    if args.brahman is None:
        args.brahman = os.path.join(os.path.dirname(args.vyakarana), "brahman")

    files = load_sources(args.vyakarana)
    patterns = analyze_patterns(files)
    t1 = analyze_tantra1(files, args.brahman)
    modules = analyze_modules(files)
    migration = analyze_migration_candidates(args.brahman, files)

    if args.json:
        json.dump(
            {
                "patterns": patterns,
                "tantra1": t1,
                "modules": modules,
                "migration": migration,
            },
            sys.stdout,
            indent=2,
        )
    else:
        print_report(files, patterns, t1, modules, migration, args.report)
