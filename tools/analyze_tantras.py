#!/usr/bin/env python3
"""
analyze_tantras.py — deep structural + philosophical analysis of the brahman.

Uses the OCaml dump-ast socket command for tantra ASTs (canonical parser).
Uses direct om file parsing for kosha/sangati structure.
Uses the live graph (inspect-node, eval-json) for satya scores and edges.

WHAT THIS REVEALS:

  Mechanical (tantra AST):
    - complexity: binding count, AST nodes, max nesting depth
    - call graph: which tantra calls which
    - hub tantras: structural load-bearers
    - recurring patterns: op shapes, query shapes, scan anatomy

  Philosophical (om + graph):
    - sloka suffix → graph edge equivalence (the fourfold identity)
    - domain coverage: which kosha domains have no tantra querying them
    - yukta gap: richest graph relation, almost never queried by tantras
    - satya scores of philosophical nodes (the graph knows its own uncertainty)
    - pratipaksha completeness: which concepts lack their inverse
    - recursive identity: avrti in sangati vs fixpoint in tantras

  Bridge (tantra ↔ om):
    - which edge types tantras query vs which edge types om files declare
    - which sangati nodes are referenced by tantras vs only in the graph
    - philosophical concept → tantra entry point mapping
    - test gaps: philosophical concepts with no test coverage

Usage:
    python3 tools/analyze_tantras.py [--socket /tmp/vy.sock] [--report SECTION]
    python3 tools/analyze_tantras.py --json | jq '.philosophical.yukta_gap'

Sections: all, tantra, om, philosophical, bridge, tests
"""

import json
import os
import sys
import re
import glob
import argparse
from collections import defaultdict, Counter
from typing import Any

# ── vy client import ───────────────────────────────────────────────────────────
# Use the canonical vy.Client from vyakarana/tests/vy.py so tools share the
# same persistent connection, retry logic, and rich API as the test suite.
# Falls back to a minimal inline implementation if vy.py is not reachable
# (e.g. running tools standalone without a checkout of vyakarana/tests).


def _load_vy_client():
    _here = os.path.dirname(os.path.abspath(__file__))
    _vy_path = os.path.join(_here, "..", "vyakarana", "tests")
    if os.path.isdir(_vy_path) and _vy_path not in sys.path:
        sys.path.insert(0, _vy_path)
    try:
        from vy import Client as _Client

        return _Client
    except ImportError:
        pass
    # minimal fallback — one-shot socket call per request
    import socket as _socket_mod

    class _Client:
        def __init__(self, socket_path):
            self._path = socket_path

        def _call(self, payload):
            with _socket_mod.socket(_socket_mod.AF_UNIX, _socket_mod.SOCK_STREAM) as s:
                s.connect(self._path)
                s.sendall((json.dumps(payload) + "\n").encode())
                data = b""
                while True:
                    chunk = s.recv(65536)
                    if not chunk:
                        break
                    data += chunk
                    try:
                        return json.loads(data.decode())
                    except json.JSONDecodeError:
                        continue
            return {"status": "error"}

        def eval(self, expr):
            r = self._call({"command": "eval-json", "expr": expr})
            return r.get("result") if r.get("status") == "ok" else None

        def inspect(self, name):
            r = self._call({"command": "inspect-node", "name": name})
            return r if r.get("status") == "ok" else None

        def walk(self, node, rel):
            r = self.eval(f'walk "{node}" "{rel}"')
            return [str(n) for n in r] if isinstance(r, list) else []

        def walk_in(self, node, rel):
            r = self.eval(f'walk-in "{node}" "{rel}"')
            return [str(n) for n in r] if isinstance(r, list) else []

        def list_tantras(self):
            r = self._call({"command": "list-tantras"})
            return r.get("tantras", []) if r.get("status") == "ok" else []

        def close(self):
            pass

    return _Client


VyClient = _load_vy_client()


# ── thin wrappers used by analysis functions (accept either sock_path str or Client) ──


def _client(sock_path_or_client) -> Any:
    """Return a VyClient, creating one from a path string if needed."""
    if isinstance(sock_path_or_client, str):
        return VyClient(sock_path_or_client)
    return sock_path_or_client


def dump_ast(sock_path, path):
    import socket as _sm, json as _j

    # dump-ast is not in vy.Client API — keep a direct call for this one
    with _sm.socket(_sm.AF_UNIX, _sm.SOCK_STREAM) as s:
        s.connect(sock_path if isinstance(sock_path, str) else sock_path._path)
        s.sendall((_j.dumps({"command": "dump-ast", "path": path}) + "\n").encode())
        data = b""
        while True:
            chunk = s.recv(65536)
            if not chunk:
                break
            data += chunk
            try:
                r = _j.loads(data.decode())
                return r.get("tantra") if r.get("status") == "ok" else None
            except _j.JSONDecodeError:
                continue
    return None


def inspect_node(sock_path, name):
    return _client(sock_path).inspect(name)


def eval_expr(sock_path, expr):
    return _client(sock_path).eval(expr)


# ── tantra AST traversal (same as before, extended) ───────────────────────────


def walk_expr(expr, visitor):
    if not isinstance(expr, dict):
        return
    visitor(expr)
    kind = expr.get("kind")
    if kind == "call":
        for a in expr.get("args", []):
            walk_expr(a, visitor)
    elif kind == "lambda":
        walk_expr(expr.get("body"), visitor)
    elif kind == "cond":
        for b in expr.get("branches", []):
            walk_expr(b.get("guard"), visitor)
            walk_expr(b.get("body"), visitor)
        walk_expr(expr.get("otherwise"), visitor)
    elif kind == "let_in":
        walk_expr(expr.get("value"), visitor)
        walk_expr(expr.get("body"), visitor)
    elif kind == "from":
        walk_expr(expr.get("source"), visitor)
        for g in expr.get("guards", []):
            walk_expr(g, visitor)
        walk_expr(expr.get("collect"), visitor)
    elif kind == "scan":
        walk_expr(expr.get("source"), visitor)
        for sd in expr.get("state", []):
            walk_expr(sd.get("init"), visitor)
        for br in expr.get("branches", []):
            walk_scan_branch(br, visitor)
    elif kind == "list":
        for item in expr.get("items", []):
            walk_expr(item, visitor)


def walk_scan_stmt(stmt, visitor):
    if not isinstance(stmt, dict):
        return
    kind = stmt.get("kind")
    if kind in ("emit", "set", "slet"):
        walk_expr(stmt.get("expr"), visitor)
    elif kind == "when":
        walk_expr(stmt.get("guard"), visitor)
        for s in stmt.get("body", []):
            walk_scan_stmt(s, visitor)
        for s in stmt.get("otherwise", []):
            walk_scan_stmt(s, visitor)


def walk_scan_branch(br, visitor):
    if not isinstance(br, dict):
        return
    walk_expr(br.get("guard"), visitor)
    for stmt in br.get("body", []):
        walk_scan_stmt(stmt, visitor)


def walk_tantra(tantra, visitor):
    for b in tantra.get("bindings", []):
        walk_expr(b.get("expr"), visitor)


def count_nodes(tantra):
    n = [0]

    def v(node):
        n[0] += 1

    walk_tantra(tantra, v)
    return n[0]


def extract_calls(tantra, all_names):
    calls = []

    def v(node):
        if node.get("kind") == "call" and node.get("op") in all_names:
            calls.append(node["op"])

    walk_tantra(tantra, v)
    return list(set(calls))


def extract_ops(tantra):
    ops = Counter()

    def v(node):
        if node.get("kind") == "call":
            ops[node["op"]] += 1

    walk_tantra(tantra, v)
    return ops


def extract_edge_refs(tantra):
    """All string literals used as edge type arguments in eq/neq calls."""
    edges = Counter()

    def v(node):
        if node.get("kind") == "call" and node.get("op") in ("eq", "neq"):
            for a in node.get("args", []):
                if isinstance(a, dict) and a.get("kind") == "str":
                    val = a.get("value", "")
                    if val:
                        edges[val] += 1

    walk_tantra(tantra, v)
    return edges


def extract_str_literals(tantra):
    """All string literals — reveals which graph concepts a tantra knows about."""
    strs = Counter()

    def v(node):
        if node.get("kind") == "str":
            strs[node.get("value", "")] += 1

    walk_tantra(tantra, v)
    return strs


def extract_vars(tantra):
    """All variable names — reveals what a tantra calls its internal concepts."""
    vars_ = Counter()

    def v(node):
        if node.get("kind") == "var":
            vars_[node.get("name", "")] += 1

    walk_tantra(tantra, v)
    return vars_


def extract_from_shapes(tantra):
    shapes = []

    def v(node):
        if node.get("kind") == "from":
            edge_filters = []
            for g in node.get("guards", []):
                if isinstance(g, dict) and g.get("op") in ("eq", "neq"):
                    for a in g.get("args", []):
                        if isinstance(a, dict) and a.get("kind") == "str":
                            edge_filters.append(g["op"] + ":" + a["value"])
            collect = node.get("collect", {})
            shapes.append(
                {
                    "edge_filters": edge_filters,
                    "collect_kind": collect.get("kind")
                    if isinstance(collect, dict)
                    else "?",
                }
            )

    walk_tantra(tantra, v)
    return shapes


def extract_scans(tantra):
    scans = []

    def v(node):
        if node.get("kind") == "scan":
            state = [sd["name"] for sd in node.get("state", []) if "name" in sd]
            branches = node.get("branches", [])
            has_otherwise = any(b.get("otherwise") for b in branches)
            guard_kinds = []
            for b in branches:
                g = b.get("guard")
                guard_kinds.append(
                    "otherwise"
                    if g is None
                    else (
                        g.get("op", g.get("kind", "?")) if isinstance(g, dict) else "?"
                    )
                )
            scans.append(
                {
                    "state_vars": state,
                    "branch_count": len(branches),
                    "has_otherwise": has_otherwise,
                    "guard_kinds": guard_kinds,
                }
            )

    walk_tantra(tantra, v)
    return scans


def max_depth(expr, d=0):
    if not isinstance(expr, dict):
        return d
    kind = expr.get("kind")
    children = []
    if kind == "call":
        children = expr.get("args", [])
    elif kind in ("cond", "let_in", "lambda", "from", "scan", "list"):
        for key in ("body", "value", "collect", "source", "otherwise"):
            c = expr.get(key)
            if c:
                children.append(c)
        for lst in (
            expr.get("branches", []),
            expr.get("items", []),
            expr.get("guards", []),
            expr.get("args", []),
        ):
            children.extend(lst)
    return max([d] + [max_depth(c, d + 1) for c in children])


def tantra_max_depth(tantra):
    return max([0] + [max_depth(b.get("expr", {})) for b in tantra.get("bindings", [])])


# ── om file parsing ────────────────────────────────────────────────────────────

SLOKA_SUFFIX_RE = re.compile(
    r"\b([a-z][a-z0-9-]*?)-(swarupa|yukta|sthita|kriya|phala|janya|abheda|siddha|vishesa|varga|pratipaksha)\b"
)
SHABDA_RE = re.compile(r"^shabda\s+(.+)", re.MULTILINE)
FIRST_WORD_RE = re.compile(r"^([a-z]+)\s+([a-z][a-z0-9-]*)", re.MULTILINE)


def parse_om_file(path):
    """Parse one .om file into a structured dict."""
    try:
        content = open(path).read()
    except:
        return None

    m = FIRST_WORD_RE.search(content)
    if not m:
        return None

    node_type = m.group(1)  # kosha / sangati / mantra / bhasha / etc.
    node_name = m.group(2)

    # sloka suffix occurrences: {suffix: [concept, ...]}
    suffix_refs = defaultdict(Counter)
    for sm in SLOKA_SUFFIX_RE.finditer(content):
        suffix_refs[sm.group(2)][sm.group(1)] += 1

    # shabda entries: word aliases
    shabda_words = []
    for sm in SHABDA_RE.finditer(content):
        raw = sm.group(1).strip()
        # split on space, comma, slash — get individual words
        words = re.split(r"[\s,/]+", raw)
        shabda_words.extend(w.strip() for w in words if w.strip() and ":" not in w)

    # comments (lines starting with --)
    comments = [
        l.strip()[2:].strip() for l in content.split("\n") if l.strip().startswith("--")
    ]

    return {
        "name": node_name,
        "type": node_type,
        "file": path,
        "suffix_refs": {k: dict(v) for k, v in suffix_refs.items()},
        "shabda": shabda_words,
        "comments": comments,
        "has_mantra": "mantra" in content and node_type != "mantra",
        "line_count": content.count("\n"),
    }


def load_om_files(brahman_dir):
    """Load all .om files from brahman, return dict by node name."""
    nodes = {}
    for path in glob.glob(os.path.join(brahman_dir, "**", "*.om"), recursive=True):
        parsed = parse_om_file(path)
        if parsed:
            # key by relative path to avoid name collisions
            rel = os.path.relpath(path, brahman_dir)
            nodes[rel] = parsed
    return nodes


# ── philosophical analysis ────────────────────────────────────────────────────

# The eight relation types that encode the philosophical grammar
RELATION_TYPES = {
    "swarupa": "IS-A identity — what something fundamentally is",
    "yukta": "endowed-with, connected-to — the richest fabric",
    "sthita": "situated-in, domain-membership — context anchor",
    "kriya": "action, process — how something operates",
    "phala": "output, result — what something produces",
    "janya": "input, generator — what something requires",
    "abheda": "non-difference, equivalence — structural identity",
    "siddha": "established, proven — what is certain",
    "vishesa": "particular-of — specific instance of universal",
    "pratipaksha": "inverse, opposite — the mirror operation",
    "amsha": "member-of-partition — closed set membership",
}

# Philosophical nodes whose satya scores reveal the graph's self-knowledge
PHILOSOPHICAL_NODES = [
    "satya",
    "mithya",
    "viveka",
    "pramana",
    "avrti",
    "spanda",
    "parampara",
    "samskaara",
    "brahmam",
    "brahma",
    "tat-kshana",
    "sandhi",
    "pratipaksha",
    "sankhya",
    "matra",
    "vishesa",
    "swarupa",
    "kriya",
    "phala",
    "janya",
    "abheda",
    "siddha",
    "yukta",
    "sthita",
    "lekhana",
    "visarjana",
    "iccha",
    "jnana",
    "sparsha",
    "sphota",
    "nibandha",
]

# Sloka suffix → graph edge type equivalence
# When an om file says "velocity-yukta" it produces a "yukta" edge to "velocity"
# When a tantra does: graph | where [s,e,o] | and (eq e "yukta") it reads that edge
SUFFIX_TO_EDGE = {
    "swarupa": "swarupa",
    "yukta": "yukta",  # NOTE: almost never queried by tantras
    "sthita": "sthita",
    "kriya": "kriya",
    "phala": "phala",
    "janya": "janya",
    "abheda": "abheda",
    "siddha": "siddha",
    "vishesa": "vishesa",
    "pratipaksha": "pratipaksha",
    "amsha": "amsha",
    "varga": "varga",
}


def analyze_philosophical(sock_path_or_client, om_nodes, tantra_edge_refs):
    """
    The deep philosophical analysis.
    Accepts either a socket path string or a VyClient instance.
    Returns a dict of named insights.
    """
    vy = _client(sock_path_or_client)
    result = {}

    # 1. Satya scores of philosophical nodes — the graph's self-knowledge
    node_satyas = {}
    for node in PHILOSOPHICAL_NODES:
        n = vy.inspect(node)
        if n:
            node_satyas[node] = {
                "satya": n.get("satya", 0),
                "out_edges": n.get("out_edges", [])[:6],
                "in_degree": len(n.get("in_edges", [])),
                "out_degree": len(n.get("out_edges", [])),
            }
    result["node_satyas"] = node_satyas

    # 2. The yukta gap: most-declared edge in om, barely queried in tantras
    # tantra_edge_refs is Counter of all edge strings seen in tantras
    om_suffix_totals = Counter()
    for om in om_nodes.values():
        for suffix, refs in om.get("suffix_refs", {}).items():
            om_suffix_totals[suffix] += sum(refs.values())

    tantra_edge_totals = Counter(tantra_edge_refs)

    yukta_gap = {
        suffix: {
            "declared_in_om": om_suffix_totals.get(suffix, 0),
            "queried_in_tantras": tantra_edge_totals.get(suffix, 0),
            "ratio": (
                tantra_edge_totals.get(suffix, 0)
                / max(1, om_suffix_totals.get(suffix, 0))
            ),
        }
        for suffix in SUFFIX_TO_EDGE
    }
    # sort by ratio ascending: lowest ratio = biggest gap
    result["relation_gap"] = sorted(yukta_gap.items(), key=lambda x: x[1]["ratio"])

    # 3. Domain coverage: which kosha domains do tantras NOT reference?
    # Build: domain → set of concept names declared
    domain_concepts = defaultdict(set)
    for rel_path, om in om_nodes.items():
        parts = rel_path.split("/")
        if len(parts) >= 2:
            domain = "/".join(parts[:2])
        else:
            domain = parts[0]
        domain_concepts[domain].add(om["name"])

    # All string literals across all tantras
    tantra_str_refs = Counter()
    for name, t in _tantra_cache.items():
        tantra_str_refs.update(extract_str_literals(t["ast"]))

    tantra_var_refs = Counter()
    for name, t in _tantra_cache.items():
        tantra_var_refs.update(extract_vars(t["ast"]))

    all_tantra_words = set(tantra_str_refs.keys()) | set(tantra_var_refs.keys())

    domain_coverage = {}
    for domain, concepts in sorted(domain_concepts.items()):
        referenced = {c for c in concepts if c in all_tantra_words}
        domain_coverage[domain] = {
            "total_nodes": len(concepts),
            "referenced_by_tantras": len(referenced),
            "coverage_pct": round(100 * len(referenced) / max(1, len(concepts)), 1),
            "unreferenced_sample": sorted(concepts - referenced)[:5],
            "referenced_sample": sorted(referenced)[:5],
        }
    result["domain_coverage"] = dict(
        sorted(
            domain_coverage.items(), key=lambda x: x[1]["coverage_pct"], reverse=True
        )
    )

    # 4. Recursive identity: avrti in sangati vs fixpoint in tantras
    fixpoint_uses = sum(
        1
        for t in _tantra_cache.values()
        for _ in [None]
        if _count_op(t["ast"], "fixpoint") > 0
    )
    avrti_satya = node_satyas.get("avrti", {}).get("satya", 0)
    result["recursive_identity"] = {
        "avrti_satya": avrti_satya,
        "avrti_graph_meaning": "swarupa:spanda, abheda:parampara — recursion IS oscillation IS lineage",
        "fixpoint_tantra_count": fixpoint_uses,
        "tantras_using_fixpoint": [
            name
            for name, t in _tantra_cache.items()
            if _count_op(t["ast"], "fixpoint") > 0
        ],
        "insight": (
            "avrti in the sangati (satya=%.3f) and fixpoint in tantras are the same concept "
            "named twice. The sangati knows this: avrti → swarupa:spanda (vibration), "
            "abheda:parampara (lineage). Every fixpoint call is an instance of the sangati node."
            % avrti_satya
        ),
    }

    # 5. One-word meaning changes: where a single edge string flip changes everything
    # Find From patterns where only the edge type differs
    from_patterns = []
    for name, t in _tantra_cache.items():
        for shape in extract_from_shapes(t["ast"]):
            if shape["edge_filters"]:
                from_patterns.append({"tantra": name, **shape})

    edge_flip_pairs = []
    seen = set()
    for i, p1 in enumerate(from_patterns):
        for p2 in from_patterns[i + 1 :]:
            if p1["tantra"] == p2["tantra"]:
                continue
            e1 = set(p1["edge_filters"])
            e2 = set(p2["edge_filters"])
            # same structure, one edge differs
            if len(e1) == len(e2) and len(e1.symmetric_difference(e2)) == 2:
                diff = sorted(e1.symmetric_difference(e2))
                key = tuple(sorted([p1["tantra"], p2["tantra"]])) + tuple(diff)
                if key not in seen:
                    seen.add(key)
                    edge_flip_pairs.append(
                        {
                            "tantras": [p1["tantra"], p2["tantra"]],
                            "only_difference": diff,
                            "shared": sorted(e1 & e2),
                            "insight": f"same query shape, one edge changed: {diff[0]} vs {diff[1]}",
                        }
                    )
    result["one_word_flips"] = edge_flip_pairs[:20]

    # 6. Pratipaksha completeness: which concepts lack their inverse?
    # The math kosha should have pratipaksha for every operation
    math_ops = vy.eval('walk-in "math-varga" "varga"')
    pratipaksha_check = {}
    if isinstance(math_ops, list):
        for op in math_ops[:20]:
            op_name = op if isinstance(op, str) else str(op)
            n = vy.inspect(op_name)
            if n:
                has_pratipaksha = any(
                    e.get("relation") == "pratipaksha" for e in n.get("out_edges", [])
                )
                pratipaksha_check[op_name] = {
                    "has_inverse": has_pratipaksha,
                    "satya": n.get("satya", 0),
                }
    result["pratipaksha_completeness"] = pratipaksha_check

    # 7. Decomposition = vibhakti: reduce/filter/map as grammatical case analysis
    decomp_ops = ["reduce", "filter", "map", "collect", "from"]
    decomp_counts = {}
    for name, t in _tantra_cache.items():
        ops = extract_ops(t["ast"])
        total = sum(ops.get(op, 0) for op in decomp_ops)
        if total > 0:
            decomp_counts[name] = {op: ops.get(op, 0) for op in decomp_ops}
    result["decomposition_tantras"] = dict(
        sorted(decomp_counts.items(), key=lambda x: sum(x[1].values()), reverse=True)[
            :15
        ]
    )

    return result


def _count_op(ast, op_name):
    count = [0]

    def v(node):
        if node.get("kind") == "call" and node.get("op") == op_name:
            count[0] += 1

    walk_tantra(ast, v)
    return count[0]


# ── test gap analysis ──────────────────────────────────────────────────────────


# ── xfail gap table — known-failing tests grouped by gate ─────────────────────
# These are not bugs — they are deferred work, gated on infrastructure that
# does not yet exist. Each group has a philosophical name for what it IS,
# not just what it does.
XFAIL_GROUPS = {
    "dvandva": {
        "description": "vishesa-bandhana instance-map: per-entity not per-concept",
        "gate": "vishesa-bandhana must use per-entity instance-map",
        "philosophy": "dvandva = pairing. two entities owning the same concept are two distinct dvandva. the current collapse to first-seen is mithya — provisional, not yet discriminated.",
        "tests": [
            "test_avrti_dvandva_collection_of_two_values",
            "test_tier2_two_entities_ke_each",
            "test_two_entity_rashi_feeds_mantra",
        ],
    },
    "session_gap2": {
        "description": "session entity structure: prathama/shashthi triples across turns",
        "gate": "dvandva fix first — same structural gap at session scale",
        "philosophy": "parampara = lineage. the session IS the student's accumulated prajna. entities must persist as structural triples (prathama, shashthi), not just sankhya numbers.",
        "tests": [
            "test_session_entity_identity_persists",
            "test_two_entities_across_turns_both_present",
            "test_two_entities_across_turns_scoped",
            "test_electron_and_field_across_turns",
        ],
    },
    "pratibimba": {
        "description": "visual output: sphere, position, simulation scene",
        "gate": "gated on session Gap 2",
        "philosophy": "pratibimba = reflection. the scene is the proof graph made visible. entities without structural identity cannot be reflected into the output layer.",
        "tests": [
            "test_sphere_shape_swarupa",
            "test_position_ownership",
            "test_electron_simulation_scene_full",
        ],
    },
    "p8f_gravity": {
        "description": "gravitational force: G constant + r² composition",
        "gate": "P8f Phase B — composed expression subgraph (power + multiply)",
        "philosophy": "G is the universal constant — constants-key auto-supply. r² requires the power(2) composition node. one expression subgraph in the kosha replaces the expr tantra.",
        "tests": [
            "test_gravitational_force",
            "test_gravitational_force_two_entities",
            "test_gravitational_force_earth_moon",
        ],
    },
    "unit_rate": {
        "description": "compound unit m/s not in word index",
        "gate": "split-numeric must handle slash-separated compound units",
        "philosophy": "matra = measure. m/s is one matra — rate of distance per time. the slash is not a separator; it is the grammatical mark of the rate relation.",
        "tests": ["test_unit_in_rate_not_stolen"],
    },
    "logic_nyaya": {
        "description": "syllogism, transitive ordering, rank comparison",
        "gate": "P8c satya-phala layer + P8d nyaya mantras — not yet started",
        "philosophy": "nyaya = logical inference. the pancavayava (five-membered syllogism) is the proof form. anumana (inference) is not yet wired — only pratyaksha (perception/measurement) works today.",
        "tests": [
            "test_syllogism_cats_breathe",
            "test_syllogism_dogs_mammals",
            "test_transitive_greater_than",
            "test_transitive_mass_ordering",
            "test_more_apples_or_oranges",
            "test_rank_three_balls_by_mass",
        ],
    },
    "complex_natural_language": {
        "description": "full natural-language physics sentences, SUVAT inversion, Coulomb",
        "gate": "mix of dvandva, session Gap 2, and P8f Phase B",
        "philosophy": "these sentences describe a full scene in human language. each is a pancavayava in sphota form — the whole meaning arrives at once. they will be answerable when the infrastructure catches up.",
        "tests": [
            "test_find_second_entity_momentum",
            "test_find_second_entity_ke",
            "test_inverse_ke_find_velocity",
            "test_relative_velocity_two_entities",
            "test_inverse_suvat_find_time",
            "test_coulomb_force_two_charged_particles",
        ],
    },
}


def analyze_test_gaps(sock_path, brahman_dir, tantra_cache):
    """
    Find philosophical concepts and tantra capabilities with no test coverage.
    Maps: concept → tests that reference it.
    Also cross-references xfail groups with actual test files.
    """
    test_dir = os.path.join(os.path.dirname(brahman_dir), "vyakarana", "tests")
    if not os.path.isdir(test_dir):
        return {"error": f"test dir not found: {test_dir}"}

    # load all test files
    test_content = {}
    for f in glob.glob(os.path.join(test_dir, "**", "*.py"), recursive=True):
        try:
            test_content[os.path.basename(f)] = open(f).read()
        except:
            pass

    all_test_text = "\n".join(test_content.values())

    # ── xfail gap cross-reference ─────────────────────────────────────────────
    # For each xfail group: which tests are actually in the test files?
    # Which are missing entirely? Which have wrong xfail markers?
    xfail_status = {}
    for group_name, group in XFAIL_GROUPS.items():
        found = []
        missing = []
        has_xfail_marker = []
        for test_name in group["tests"]:
            in_files = any(test_name in src for src in test_content.values())
            if in_files:
                found.append(test_name)
                # check if it has an xfail marker
                for fname, src in test_content.items():
                    if test_name in src:
                        # look for xfail marker within a few lines above the def
                        idx = src.find(f"def {test_name}")
                        if idx > 0:
                            preceding = src[max(0, idx - 300) : idx]
                            if "xfail" in preceding:
                                has_xfail_marker.append(test_name)
            else:
                missing.append(test_name)
        xfail_status[group_name] = {
            "found": found,
            "missing": missing,
            "has_xfail": has_xfail_marker,
            "description": group["description"],
            "gate": group["gate"],
            "philosophy": group["philosophy"],
        }

    # which tantra names appear in tests?
    tested_tantras = {name for name in tantra_cache if name in all_test_text}
    untested_tantras = sorted(set(tantra_cache.keys()) - tested_tantras)

    # which philosophical nodes appear in tests?
    tested_concepts = {node for node in PHILOSOPHICAL_NODES if node in all_test_text}
    untested_concepts = sorted(set(PHILOSOPHICAL_NODES) - tested_concepts)

    # which edge types are tested?
    tested_edges = set()
    for edge in SUFFIX_TO_EDGE:
        if edge in all_test_text:
            tested_edges.add(edge)
    untested_edges = sorted(set(SUFFIX_TO_EDGE.keys()) - tested_edges)

    # suggested new tests based on gaps
    suggestions = []

    # 1. avrti/fixpoint: test that avrti matches the sangati description
    if "avrti" not in tested_concepts:
        suggestions.append(
            {
                "category": "philosophical_identity",
                "name": "test_avrti_is_spanda_parampara",
                "rationale": "avrti sangati says: swarupa=spanda, abheda=parampara. "
                "Test that the graph actually has these edges. "
                "Confirms the code matches its philosophical ground.",
                "sketch": 'r = client.eval(\'walk avrti "swarupa"\')\nassert "spanda" in r',
            }
        )

    # 2. yukta gap: the richest edge type, never queried
    suggestions.append(
        {
            "category": "yukta_gap",
            "name": "test_yukta_edges_reachable_via_kosha_expand",
            "rationale": "yukta is the most-declared edge type (2694 in kosha) but no tantra "
            "queries it directly. kosha-expand (PPR) should surface yukta neighbors. "
            "Test that PPR seeds include yukta-connected concepts.",
            "sketch": (
                "r = client.eval('kosha-expand (build-question-graph \"kinetic energy\")')\n"
                "# should include velocity-yukta neighbors of kinetic-energy"
            ),
        }
    )

    # 3. pratipaksha: the philosophical inverse should be structurally testable
    suggestions.append(
        {
            "category": "pratipaksha",
            "name": "test_every_math_op_has_pratipaksha",
            "rationale": "pratipaksha satya=0.0 in the graph — structurally present but "
            "philosophically ungrounded. invert-math depends on it. "
            "Test that every math operation node has at least one pratipaksha edge.",
            "sketch": (
                'ops = client.eval(\'walk-in "math-varga" "varga"\')\n'
                "for op in ops:\n"
                "    pp = client.eval(f'walk {op} \"pratipaksha\"')\n"
                '    assert len(pp) > 0, f"{op} has no pratipaksha"'
            ),
        }
    )

    # 4. mithya resolution: test the philosophical meaning of mithya
    suggestions.append(
        {
            "category": "mithya_resolution",
            "name": "test_mithya_resolves_under_context_pressure",
            "rationale": "mithya (satya=0.708) means provisional/not-yet-known. "
            "avrti applies context pressure to collapse mithya into satya. "
            "Test that after avrti-refine, mithya count strictly decreases.",
            "sketch": (
                "raw = client.eval('build-question-graph \"ball has mass m1 of 5\"')\n"
                "refined = client.eval('fixpoint raw (fn g -> avrti-refine g)')\n"
                "mithya_before = count triples with edge=mithya in raw\n"
                "mithya_after  = count triples with edge=mithya in refined\n"
                "assert mithya_after < mithya_before"
            ),
        }
    )

    # 5. one-word flip tests: sankhya vs sankhya + scope
    suggestions.append(
        {
            "category": "one_word_flip",
            "name": "test_scope_entity_changes_result_not_just_value",
            "rationale": "Changing 'find KE' to 'find KE of ball-A' is one word. "
            "The graph query changes from eq:sankhya to eq:shashthi-vibhakti+eq:sankhya. "
            "Test that the scoped result differs from the flat result when two "
            "entities have different values.",
            "sketch": (
                'r_flat   = client.query("ball-A has mass 3 and ball-B has mass 5. find KE")\n'
                'r_scoped = client.query("ball-A has mass 3 and ball-B has mass 5. find KE of ball-A")\n'
                "assert r_scoped != r_flat"
            ),
        }
    )

    # 6. decomposition identity: reduce IS vibhakti
    suggestions.append(
        {
            "category": "decomposition_identity",
            "name": "test_vibhakti_shashthi_produces_ownership_partition",
            "rationale": "vibhakti = grammatical case = decomposition of a whole into relational parts. "
            "The shashthi (genitive) case is 'X belongs to Y'. "
            "After vibhakti-shashthi runs, every property should be partitioned "
            "to exactly one entity. Test this partition property.",
            "sketch": (
                'graph = refine("electron has mass 9.1e-31 and proton has mass 1.67e-27")\n'
                "owned = graph | where [s,e,o] | and eq e shashthi-vibhakti | collect [s,o]\n"
                "# every concept appears at most once per entity\n"
                "assert no duplicates in owned"
            ),
        }
    )

    # 7. sphota test: the whole meaning arrived at once
    suggestions.append(
        {
            "category": "sphota",
            "name": "test_sphota_is_surface_free",
            "rationale": "sphota = the whole meaning arrived at once, surface-free. "
            "After avrti to fixpoint, no raw surface words should remain "
            "as mithya unless they are genuinely ungrounded (asprista). "
            "Test that every mithya triple at fixpoint has no kosha entry.",
            "sketch": (
                'refined = fixpoint(build_question_graph("ball has mass 5 velocity 10"))\n'
                "for s,e,o in refined:\n"
                '    if e == "mithya":\n'
                '        assert lookup(s) is None, f"{s} should be asprista"'
            ),
        }
    )

    # 8. untested hub tantras
    for hub in ["bound-concept-names", "extract-solve-for", "viveka-ganana"]:
        if hub not in tested_tantras:
            suggestions.append(
                {
                    "category": "untested_hub",
                    "name": f"test_{hub.replace('-', '_')}_directly",
                    "rationale": f"{hub} is called by multiple tantras but has no direct tests. "
                    f"Hub tantras are the highest-leverage test targets.",
                    "sketch": f"result = client.eval('{hub} <graph>')\nassert result is structured correctly",
                }
            )

    return {
        "tested_tantras": sorted(tested_tantras),
        "untested_tantras": untested_tantras,
        "untested_hub_tantras": [
            t
            for t in untested_tantras
            if t
            in (
                "bound-concept-names",
                "extract-solve-for",
                "viveka-ganana",
                "emit-reasoning",
                "derive-chain",
            )
        ],
        "tested_concepts": sorted(tested_concepts),
        "untested_concepts": untested_concepts,
        "untested_edges": untested_edges,
        "test_file_count": len(test_content),
        "suggestions": suggestions,
        "xfail_groups": xfail_status,
    }


# ── micro-pattern analysis ───────────────────────────────────────────────────
#
# Finds concrete repeated expressions across tantra source files that are
# candidates for named micro-tantras. Works on raw source text (no server).
# Each pattern has:
#   name        — proposed tantra name (philosophical)
#   sanskrit    — what the Sanskrit root names
#   regex       — what to find in source
#   replaces    — the expression it would replace
#   hits        — [{file, lineno, text}]
#   note        — why this is the right abstraction


MICRO_PATTERNS = [
    {
        "name": "sattva",
        "sanskrit": "sattva — existence, being",
        "regex": r"gt \(string-length \(to-string [^\)]+\)\) 0",
        "replaces": "gt (string-length (to-string X)) 0",
        "note": "OCaml 'exists' primitive already does this — tantras don't use it consistently",
        # graph grounding: satya (truth/existence) is spanda-janya, brahman-phala.
        # the OCaml 'exists' op implements: as_bool v. sattva = that check, named.
        "graph_node": "satya",  # sattva (being) IS satya in this graph
        "graph_meaning": "satya: spanda-janya brahman-phala — existence is what spanda produces. "
        "The check 'does this value exist?' is asking 'has contact (sparsha) produced structure?'",
        "body": "takes x\nresult = exists x\nreturn result",
    },
    {
        "name": "prathama",
        "sanskrit": "prathama — the nominative subjects (kartri, the agents)",
        "regex": r'\| where \[[^\]]+\] \| and \(eq e "prathama-vibhakti"\) \| collect s',
        "replaces": 'graph | where [s,e,o] | and (eq e "prathama-vibhakti") | collect s',
        "note": "pure graph reader — who are the named entities in this question",
        # graph grounding: prathama-vibhakti is the nominative case.
        # vibhakti swarupa = sambandha (relation). the nominative IS the relation of being a subject.
        # prathama-vibhakti is yukta:vakya (sentence) and yukta:visheshanam-ring (dimension registry).
        "graph_node": "prathama-vibhakti",
        "graph_meaning": "prathama-vibhakti: vibhakti-amsha, yukta:vakya — the subject-relation in a sentence. "
        "Querying it extracts kartri: the agents who own the question's quantities.",
        "body": 'takes graph\nresult = graph | where [s, e, o] | and (eq e "prathama-vibhakti") | collect s\nreturn result',
    },
    {
        "name": "sankhya-sparsha",
        "sanskrit": "sankhya-sparsha — number-contact, the bound numeric values",
        "regex": r'\| where \[[^\]]+\] \| and \(eq e "sankhya"\) \| collect',
        "replaces": 'graph | where [s,e,o] | and (eq e "sankhya") | collect [s,o]',
        "note": "bound-concepts already IS this — callers should use bound-concepts instead of inlining",
        # graph grounding: sankhya has swarupa = [count, dvaya, traya] and yukta = [rashi, matra, parampara].
        # sankhya is the number. sparsha is the contact. sankhya-sparsha = the moment a number
        # lands on a concept — the touch of measurement.
        "graph_node": "sankhya",  # the numeric-binding concept
        "graph_meaning": "sankhya: rashi-yukta matra-yukta — number is always yukta with measure and instance. "
        "sankhya-sparsha = the contact that binds a float to its concept. "
        "bound-concepts is already the canonical tantra for this — inline queries should call it.",
        "body": 'takes graph\nresult = graph | where [s, e, o] | and (eq e "sankhya") | collect [s, o]\nreturn result',
    },
    {
        "name": "shashthi-sparsha",
        "sanskrit": "shashthi-sparsha — genitive contact, what belongs to an entity",
        "regex": r'\| and \(eq e "shashthi-vibhakti"\) \| and \(eq \(to-string [^\)]+\) \(to-string [^\)]+\)\) \| collect',
        "replaces": 'graph | where [s,e,owner] | and (eq e "shashthi-vibhakti") | and (eq (to-string owner) ENTITY) | collect s',
        "note": "ownership lookup — which concepts does this entity own",
        # graph grounding: shashthi-vibhakti (genitive case) is triggered by verb-have/verb-has/prep-with.
        # vibhakti swarupa = sambandha. shashthi IS the relation of possession/belonging.
        # sparsha = the contact event. shashthi-sparsha = the contact of possession.
        "graph_node": "shashthi-vibhakti",
        "graph_meaning": "shashthi-vibhakti: sthita←verb-have,verb-has,prep-with — the genitive is possession. "
        "shashthi-sparsha = querying what a named entity owns. "
        "The graph's ownership structure is already there; this tantra makes the query named.",
        "body": 'takes graph\ntakes entity\nresult = graph | where [s, e, owner]\n  | and (eq e "shashthi-vibhakti")\n  | and (eq (to-string owner) (to-string entity))\n  | collect s\nreturn result',
    },
    {
        "name": "agra",
        "sanskrit": "agra — the foremost, safe head of list",
        "regex": r"cond \(gt \(length [^\)]+\) 0\) \(nth [^\)]+0\) otherwise",
        "replaces": "cond (gt (length lst) 0) (nth lst 0) otherwise fallback",
        "note": "safe list head — appears wherever a single result is extracted from a query",
        # graph grounding: agra means 'foremost, tip, front'. satya=0.0 in graph (not yet grounded).
        # agra yukta = shakha (branch). agra is the tip of the branch — the first element.
        # This tantra gives the 'safe first' operation its proper name: agra.
        "graph_node": "agra",
        "graph_meaning": "agra: the foremost, the tip (yukta:shakha). "
        "In list operations: the first valid element. In the question graph: "
        "the first match. agra(list, fallback) = the safe head with a named default.",
        "body": "takes lst\ntakes fallback\nresult = cond (gt (length lst) 0) (nth lst 0) otherwise fallback\nreturn result",
    },
    {
        "name": "bandha-triples",
        "sanskrit": "bandha-triples — binding pairs lifted to typed graph triples",
        "regex": r"append acc \[\[\(nth kv 0\), \"[^\"]+\", \(nth kv 1\)\]\]",
        "replaces": 'append acc [[(nth kv 0), "EDGE", (nth kv 1)]]',
        "note": "kv-pairs → graph triples — only the edge label differs each time",
        # graph grounding: bandha = binding (Rasayana: shodhana→mardana→jarana→bandha).
        # bandha is fixation, the step that makes something permanent.
        # kv-pairs are mutable; triples are bandha — fixed in the proof graph.
        "graph_node": None,  # bandha is a rasayana concept, not a simple kosha node
        "graph_meaning": "bandha (Rasayana): the fixation step — binding volatile material into permanent form. "
        "kv-pairs are provisional; lifting them to [s, edge, o] triples IS the bandha. "
        "The edge label is the relation that holds the binding.",
        "body": "takes pairs\ntakes edge\nresult = reduce pairs [] (fn acc kv ->\n  append acc [[(nth kv 0), edge, (nth kv 1)]])\nreturn result",
    },
    {
        "name": "graph-samskaara",
        "sanskrit": "graph-samskaara — graph impression, fold derived triples in",
        "regex": r"reduce [a-z-]+ graph \(fn \w+ t -> .?append \w+ \[t\]\)",
        "replaces": "reduce new-triples graph (fn g t -> append g [t])",
        "note": "standard pattern for injecting derived triples back into the graph",
        # graph grounding: samskaara = keyframe, impression, latent form.
        # samskaara kriya = avrti (the graph knows: samskaara operates through avrti).
        # samskaara swarupa = rachana (composition) + sthiti (stability).
        # folding new triples into the graph IS samskaara: leaving an impression.
        "graph_node": "samskaara",  # keyframe — kriya:avrti, swarupa:rachana+sthiti
        "graph_meaning": "samskaara: keyframe — kriya:avrti, swarupa:rachana+sthiti. "
        "Folding derived triples into the proof graph is leaving a samskaara: "
        "a structural impression that persists. Each new triple is one keyframe added.",
        "body": "takes graph\ntakes triples\nresult = reduce triples graph (fn g t -> append g [t])\nreturn result",
    },
]


def _enrich_micro_patterns_from_graph(patterns: list, vy) -> None:
    """
    For each micro-pattern, query the live graph to verify its philosophical
    grounding node exists, pull its satya score, and find how many tantras
    currently query that graph node directly (vs inlining the pattern).

    Mutates patterns in-place, adding 'graph_grounding' dict to each entry.
    vy can be a VyClient instance or None (skips enrichment).
    """
    if vy is None:
        return

    for pat in patterns:
        gnode = pat.get("graph_node")
        if not gnode:
            continue
        try:
            info = vy.inspect(gnode)
            if not info or info.get("status") == "error":
                pat["graph_grounding"] = {"found": False}
                continue

            satya = info.get("satya", 0.0)
            out_edges = info.get("out_edges", [])
            in_edges = info.get("in_edges", [])

            # key structural edges — what does the graph say this concept IS?
            swarupa = vy.walk(gnode, "swarupa")
            kriya = vy.walk(gnode, "kriya")
            janya = vy.walk(gnode, "janya")
            phala = vy.walk(gnode, "phala")

            # also check: does a tantra with this name already exist?
            tantra_exists = gnode in (vy.list_tantras() or [])
            proposed_name = pat["name"]
            proposed_exists = proposed_name in (vy.list_tantras() or [])

            pat["graph_grounding"] = {
                "found": True,
                "satya": satya,
                "out_degree": len(out_edges),
                "in_degree": len(in_edges),
                "swarupa": swarupa[:4],
                "kriya": kriya[:4],
                "janya": janya[:4],
                "phala": phala[:4],
                "graph_node_exists": True,
                "tantra_exists": tantra_exists,
                "proposed_exists": proposed_exists,
                "ready": satya > 0.3 and not proposed_exists,
            }
        except Exception as exc:
            pat["graph_grounding"] = {"found": False, "error": str(exc)}


def analyze_micro_patterns(yantra_dir: str, vy=None) -> dict:
    """
    Scan all tantra2 source files for recurring micro-expressions.
    Returns per-pattern hit lists and a ranked summary.
    No server required — pure text analysis.
    """
    files = sorted(
        glob.glob(os.path.join(yantra_dir, "**", "*.tantra2"), recursive=True)
    )

    # load raw source per tantra
    sources: dict[str, tuple[str, list[str]]] = {}  # name → (path, lines)
    for f in files:
        name = os.path.basename(f).replace(".tantra2", "")
        try:
            lines = open(f).readlines()
            sources[name] = (f, lines)
        except OSError:
            pass

    results = []
    for pat in MICRO_PATTERNS:
        rx = re.compile(pat["regex"])
        hits = []
        files_hit: set[str] = set()
        for name, (path, lines) in sorted(sources.items()):
            for lineno, line in enumerate(lines, 1):
                stripped = line.strip()
                if stripped.startswith("--"):
                    continue
                if rx.search(stripped):
                    hits.append(
                        {
                            "tantra": name,
                            "lineno": lineno,
                            "text": stripped[:100],
                        }
                    )
                    files_hit.add(name)

        results.append(
            {
                "name": pat["name"],
                "sanskrit": pat["sanskrit"],
                "replaces": pat["replaces"],
                "note": pat["note"],
                "graph_node": pat.get("graph_node"),
                "graph_meaning": pat.get("graph_meaning", ""),
                "body": pat.get("body", ""),
                "hit_count": len(hits),
                "file_count": len(files_hit),
                "files": sorted(files_hit),
                "hits": hits,
            }
        )

    # sort by hit_count descending
    results.sort(key=lambda x: -x["hit_count"])

    # enrich with live graph data if a client was passed
    _enrich_micro_patterns_from_graph(results, vy)

    # also find from-shapes that appear 3+ times (candidate micro-tantras via AST)
    from_shape_files: dict[str, list[str]] = defaultdict(list)
    for name, (path, lines) in sources.items():
        src = "".join(l for l in lines if not l.strip().startswith("--"))
        for m in re.finditer(
            r'\| where \[[^\]]+\] \| and \(eq e "([^"]+)"\)(?: \| and [^\|]+)* \| collect ([^\n]+)',
            src,
        ):
            shape = f'eq:"{m.group(1)}" → collect:{m.group(2).strip()[:40]}'
            from_shape_files[shape].append(name)

    repeated_shapes = [
        {"shape": shape, "count": len(tnames), "tantras": sorted(tnames)}
        for shape, tnames in from_shape_files.items()
        if len(tnames) >= 3
    ]
    repeated_shapes.sort(key=lambda x: -x["count"])

    return {
        "patterns": results,
        "repeated_query_shapes": repeated_shapes,
        "total_tantras_scanned": len(sources),
    }


# ── tantra role classification ─────────────────────────────────────────────────
#
# Classifies each tantra by its structural role based on:
#   - call graph (what it calls)
#   - reverse graph (what calls it)
#   - takes count (input arity)
#   - body complexity (AST nodes)
#
# Roles:
#   ENTRY      — sentence→answer, top-level entry point
#   WRAPPER    — thin delegation to one or two core workers
#   WORKER     — real logic, called by multiple others
#   AVRTI-PASS — called only by avrti-refine (one refinement sub-step)
#   QG-PASS    — called only by build-question-graph
#   READER     — pure graph extraction, no side effects
#   EQUATION   — pure math, no graph operations
#   EMIT-HELPER — produces strings for pancavayava emission
#   EXEC-HELPER — dispatches to equation tantras


def analyze_tantra_roles(tantra_data: dict) -> dict:
    """
    Classify each tantra by structural role using its call graph and complexity.
    tantra_data is the result of analyze_tantras().
    """
    call_graph = tantra_data["call_graph"]  # name → [callees]
    reverse_graph = tantra_data["reverse_graph"]  # name → [callers]
    complexity = tantra_data["complexity"]

    # known structural anchors
    AVRTI_PASS_CALLERS = {"avrti-refine"}
    QG_PASS_CALLERS = {"build-question-graph", "sandhi-viveka"}
    EMIT_HELPERS = {
        "entity-props-str",
        "list-join",
        "mantra-known-str",
        "mantra-seen-str",
    }
    EXEC_HELPERS = {"execute-chain", "execute-math"}
    ENTRY_NAMES = {"anuvada-ganana", "tantra3", "session-anuvada"}
    EQUATION_RE = re.compile(r"-expr$|-inv-")

    def callers_of(name):
        return set(reverse_graph.get(name, []))

    def callees_of(name):
        return set(call_graph.get(name, []))

    def ast_nodes(name):
        return complexity.get(name, {}).get("ast_nodes", 0)

    def takes_count(name):
        return len(
            complexity.get(name, {}).get("file", "")
        )  # proxy; real takes from AST

    classified = {}
    for name in sorted(call_graph.keys()):
        callers = callers_of(name)
        callees = callees_of(name)
        nodes = ast_nodes(name)

        if name in ENTRY_NAMES:
            role = "ENTRY"
            why = "top-level sentence→answer entry point"

        elif name in EMIT_HELPERS:
            role = "EMIT-HELPER"
            why = "produces string fragments for pancavayava emission"

        elif name in EXEC_HELPERS:
            role = "EXEC-HELPER"
            why = "dispatches to equation tantra, returns numeric result"

        elif EQUATION_RE.search(name) or (
            not callees and nodes < 20 and not callers - ENTRY_NAMES
        ):
            role = "EQUATION"
            why = "pure math expression, no graph operations"

        elif (
            callers <= AVRTI_PASS_CALLERS | {"avrti-refine"}
            and "avrti-refine" in callers
        ):
            role = "AVRTI-PASS"
            why = f"called exclusively by avrti-refine (callers: {sorted(callers)})"

        elif callers <= QG_PASS_CALLERS and callers:
            role = "QG-PASS"
            why = f"called exclusively by build-question-graph pipeline (callers: {sorted(callers)})"

        elif not callees and nodes < 15:
            role = "READER"
            why = "pure graph extraction, no sub-calls, small body"

        elif len(callees) <= 2 and nodes < 30:
            role = "WRAPPER"
            callees_str = ", ".join(sorted(callees)) if callees else "—"
            why = f"thin delegation to: {callees_str}"

        else:
            role = "WORKER"
            why = f"core logic — {nodes} AST nodes, calls {len(callees)} sub-tantras"

        classified[name] = {
            "role": role,
            "why": why,
            "callers": sorted(callers),
            "callees": sorted(callees),
            "ast_nodes": nodes,
            "caller_count": len(callers),
            "callee_count": len(callees),
        }

    # group by role
    by_role: dict[str, list[str]] = defaultdict(list)
    for name, info in classified.items():
        by_role[info["role"]].append(name)

    # find WRAPPER tantras that are pure renames (≤1 callee, ≤15 AST nodes)
    pure_renames = [
        name
        for name, info in classified.items()
        if info["role"] == "WRAPPER"
        and info["callee_count"] <= 1
        and info["ast_nodes"] <= 15
    ]

    # find redundant ENTRY points (more than one does the same thing)
    entry_names = by_role.get("ENTRY", [])

    return {
        "classified": classified,
        "by_role": {role: sorted(names) for role, names in sorted(by_role.items())},
        "pure_renames": sorted(pure_renames),
        "redundant_entries": entry_names,
        "role_counts": {role: len(names) for role, names in sorted(by_role.items())},
    }


# ── tantra analysis ────────────────────────────────────────────────────────────

_tantra_cache = {}  # name → {ast, file}


def analyze_tantras(sock_path, yantra_dir):
    files = sorted(
        glob.glob(os.path.join(yantra_dir, "**", "*.tantra2"), recursive=True)
    )
    files = [f for f in files if "/tests/" not in f]

    print(f"  Loading {len(files)} tantra ASTs...", file=sys.stderr)
    for f in files:
        name = os.path.basename(f).replace(".tantra2", "")
        ast = dump_ast(sock_path, f)
        if ast:
            _tantra_cache[name] = {"ast": ast, "file": f}

    all_names = set(_tantra_cache.keys())

    # complexity
    complexity = {}
    for name, t in _tantra_cache.items():
        ast = t["ast"]
        complexity[name] = {
            "file": os.path.relpath(t["file"], yantra_dir),
            "binding_count": len(ast.get("bindings", [])),
            "ast_nodes": count_nodes(ast),
            "max_depth": tantra_max_depth(ast),
            "scan_count": len(extract_scans(ast)),
            "from_count": len(extract_from_shapes(ast)),
        }

    # call graph
    call_graph = {}
    reverse_graph = defaultdict(list)
    for name, t in _tantra_cache.items():
        calls = extract_calls(t["ast"], all_names)
        call_graph[name] = sorted(calls)
        for callee in calls:
            reverse_graph[callee].append(name)

    # global aggregates
    global_ops = Counter()
    global_edges = Counter()
    global_str_refs = Counter()
    call_shapes = Counter()

    for name, t in _tantra_cache.items():
        ops = extract_ops(t["ast"])
        global_ops.update(ops)
        global_edges.update(extract_edge_refs(t["ast"]))
        global_str_refs.update(extract_str_literals(t["ast"]))
        for op, count in ops.items():
            call_shapes[f"{op}/{min(count, 9)}+"] += 1

    from_shape_counter = Counter()
    for name, t in _tantra_cache.items():
        for s in extract_from_shapes(t["ast"]):
            key = " ".join(sorted(s["edge_filters"])) + " → " + s["collect_kind"]
            from_shape_counter[key] += 1

    scan_anatomy = {
        name: extract_scans(t["ast"])
        for name, t in _tantra_cache.items()
        if extract_scans(t["ast"])
    }

    hub_scores = sorted(
        {name: len(callers) for name, callers in reverse_graph.items()}.items(),
        key=lambda x: x[1],
        reverse=True,
    )

    return {
        "summary": {
            "total_tantras": len(_tantra_cache),
            "total_ast_nodes": sum(c["ast_nodes"] for c in complexity.values()),
            "most_complex": sorted(
                complexity.items(), key=lambda x: x[1]["ast_nodes"], reverse=True
            )[:10],
            "deepest": sorted(
                complexity.items(), key=lambda x: x[1]["max_depth"], reverse=True
            )[:10],
        },
        "complexity": complexity,
        "call_graph": call_graph,
        "reverse_graph": {k: sorted(v) for k, v in reverse_graph.items()},
        "hub_scores": hub_scores,
        "global_ops": global_ops.most_common(30),
        "global_edges": dict(global_edges.most_common(30)),
        "global_str_refs": dict(global_str_refs.most_common(40)),
        "from_shapes": from_shape_counter.most_common(20),
        "scan_anatomy": scan_anatomy,
        "call_shapes": call_shapes.most_common(30),
    }


# ── om analysis ───────────────────────────────────────────────────────────────


def analyze_om(brahman_dir):
    print("  Loading om files...", file=sys.stderr)
    om_nodes = load_om_files(brahman_dir)

    # domain distribution
    def _ds():
        return {
            "files": 0,
            "suffix_totals": Counter(),
            "shabda_count": 0,
            "types": Counter(),
        }

    domain_stats: dict = defaultdict(_ds)
    for rel_path, om in om_nodes.items():
        parts = rel_path.split("/")
        domain = "/".join(parts[:2]) if len(parts) >= 2 else parts[0]
        domain_stats[domain]["files"] += 1
        domain_stats[domain]["types"][om["type"]] += 1
        domain_stats[domain]["shabda_count"] += len(om["shabda"])
        for suffix, refs in om.get("suffix_refs", {}).items():
            domain_stats[domain]["suffix_totals"][suffix] += sum(refs.values())

    # global suffix frequency
    global_suffix = Counter()
    for om in om_nodes.values():
        for suffix, refs in om.get("suffix_refs", {}).items():
            global_suffix[suffix] += sum(refs.values())

    # which concepts most cross-referenced (appear as suffix target in many nodes)
    global_target_refs = Counter()
    for om in om_nodes.values():
        for suffix, refs in om.get("suffix_refs", {}).items():
            global_target_refs.update(refs)

    return {
        "total_files": len(om_nodes),
        "domain_stats": {
            domain: {
                "files": s["files"],
                "shabda": s["shabda_count"],
                "top_suffixes": s["suffix_totals"].most_common(5),
                "types": dict(s["types"]),
            }
            for domain, s in sorted(
                domain_stats.items(), key=lambda x: x[1]["files"], reverse=True
            )
        },
        "global_suffix_freq": dict(global_suffix.most_common()),
        "most_referenced_concepts": dict(global_target_refs.most_common(30)),
        "nodes": om_nodes,
    }


# ── full analysis ──────────────────────────────────────────────────────────────


def run_full_analysis(sock_path, yantra_dir, brahman_dir):
    # single persistent client shared across all analyses that need graph queries
    vy = VyClient(sock_path)

    print("Running tantra analysis...", file=sys.stderr)
    tantra_result = analyze_tantras(sock_path, yantra_dir)

    print("Running om analysis...", file=sys.stderr)
    om_result = analyze_om(brahman_dir)

    print("Running philosophical analysis...", file=sys.stderr)
    tantra_edge_refs = tantra_result["global_edges"]
    phil_result = analyze_philosophical(vy, om_result["nodes"], tantra_edge_refs)

    print("Running test gap analysis...", file=sys.stderr)
    test_result = analyze_test_gaps(sock_path, brahman_dir, _tantra_cache)

    print("Running micro-pattern analysis...", file=sys.stderr)
    micro_result = analyze_micro_patterns(yantra_dir, vy=vy)

    print("Running tantra role classification...", file=sys.stderr)
    roles_result = analyze_tantra_roles(tantra_result)

    vy.close()
    return {
        "tantra": tantra_result,
        "om": {k: v for k, v in om_result.items() if k != "nodes"},
        "philosophical": phil_result,
        "tests": test_result,
        "micro": micro_result,
        "roles": roles_result,
    }


# ── pretty report ─────────────────────────────────────────────────────────────


def print_report(result, section="all"):
    t = result.get("tantra", {})
    o = result.get("om", {})
    p = result.get("philosophical", {})
    ts = result.get("tests", {})

    def header(title):
        print(f"\n{'═' * 70}")
        print(f"  {title}")
        print("═" * 70)

    def section_header(title):
        print(f"\n── {title} {'─' * (65 - len(title))}")

    if section in ("all", "tantra"):
        header(
            f"TANTRA ANALYSIS  ({t['summary']['total_tantras']} tantras, "
            f"{t['summary']['total_ast_nodes']} AST nodes)"
        )

        section_header("COMPLEXITY (by AST nodes)")
        for name, c in t["summary"]["most_complex"]:
            print(
                f"  {name:<35} nodes={c['ast_nodes']:<5} depth={c['max_depth']:<3} "
                f"scans={c['scan_count']}  queries={c['from_count']}"
            )

        section_header("DEEPEST NESTING")
        for name, c in t["summary"]["deepest"]:
            print(f"  {name:<35} depth={c['max_depth']}")

        section_header("HUB TANTRAS (called by most others)")
        for name, score in t["hub_scores"][:12]:
            callers = t["reverse_graph"].get(name, [])
            print(f"  {name:<35} ×{score}  ← {', '.join(callers)}")

        section_header("CALL GRAPH")
        for name, calls in sorted(t["call_graph"].items()):
            if calls:
                print(f"  {name:<35} → {', '.join(calls)}")

        section_header("RECURRING QUERY SHAPES (From patterns)")
        for shape, count in t["from_shapes"]:
            print(f"  {count:>3}×  {shape}")

        section_header("SCAN ANATOMY")
        for name, scans in sorted(t["scan_anatomy"].items()):
            for sc in scans:
                print(
                    f"  {name:<35} state={sc['state_vars']}  "
                    f"branches={sc['branch_count']}  otherwise={sc['has_otherwise']}"
                )

        section_header("TOP OPS (global)")
        for op, count in t["global_ops"][:15]:
            print(f"  {op:<30} {count}")

    if section in ("all", "om"):
        header(f"OM ANALYSIS  ({o['total_files']} files)")

        section_header("DOMAIN DISTRIBUTION")
        print(f"  {'domain':<30} {'files':>5} {'shabda':>6}  top suffixes")
        print(f"  {'-' * 65}")
        for domain, s in o["domain_stats"].items():
            tops = ", ".join(f"{k}({v})" for k, v in s["top_suffixes"][:3])
            print(f"  {domain:<30} {s['files']:>5} {s['shabda']:>6}  {tops}")

        section_header("GLOBAL SUFFIX FREQUENCY (sloka grammar)")
        print("  (these suffixes in om files produce graph edges of the same name)")
        for suffix, count in sorted(
            o["global_suffix_freq"].items(), key=lambda x: x[1], reverse=True
        ):
            meaning = RELATION_TYPES.get(suffix, "")
            print(f"  {suffix:<15} {count:>5}  — {meaning}")

        section_header("MOST CROSS-REFERENCED CONCEPTS (appear as targets in slokas)")
        for concept, count in list(o["most_referenced_concepts"].items())[:20]:
            print(f"  {concept:<30} {count}")

    if section in ("all", "philosophical"):
        header("PHILOSOPHICAL ANALYSIS")

        section_header("SATYA SCORES OF PHILOSOPHICAL NODES")
        print(
            "  (the graph's self-knowledge — how certain it is of its own foundations)"
        )
        for node, info in sorted(
            p["node_satyas"].items(), key=lambda x: x[1]["satya"], reverse=True
        ):
            print(
                f"  {node:<20} satya={info['satya']:.3f}  "
                f"out={info['out_degree']}  in={info['in_degree']}"
            )

        section_header("RELATION GAP (declared in om vs queried in tantras)")
        print("  (ratio = tantra_queries / om_declarations — lower = bigger gap)")
        print(f"  {'edge':<15} {'om_decl':>8} {'tantra_q':>9} {'ratio':>7}  meaning")
        print(f"  {'-' * 70}")
        for suffix, g in p["relation_gap"]:
            meaning = RELATION_TYPES.get(suffix, "")[:35]
            print(
                f"  {suffix:<15} {g['declared_in_om']:>8} {g['queried_in_tantras']:>9} "
                f"  {g['ratio']:>6.3f}  {meaning}"
            )

        section_header("RECURSIVE IDENTITY: avrti (sangati) = fixpoint (tantra)")
        ri = p["recursive_identity"]
        print(f"  avrti satya = {ri['avrti_satya']:.3f}")
        print(f"  sangati meaning: {ri['avrti_graph_meaning']}")
        print(
            f"  fixpoint used in {ri['fixpoint_tantra_count']} tantras: "
            f"{', '.join(ri['tantras_using_fixpoint'])}"
        )
        print(f"  insight: {ri['insight']}")

        section_header("ONE-WORD FLIPS (same query shape, one edge type changed)")
        for flip in p["one_word_flips"][:10]:
            print(f"  {flip['tantras'][0]} ↔ {flip['tantras'][1]}")
            print(f"    shared: {flip['shared']}")
            print(
                f"    differs: {flip['only_difference'][0]}  vs  {flip['only_difference'][1]}"
            )

        section_header("DECOMPOSITION = VIBHAKTI (reduce/filter/map per tantra)")
        print(
            "  (grammatical case analysis = structural decomposition — same operation)"
        )
        for name, ops in list(p["decomposition_tantras"].items())[:10]:
            total = sum(ops.values())
            op_str = ", ".join(f"{k}={v}" for k, v in ops.items() if v > 0)
            print(f"  {name:<35} total={total}  [{op_str}]")

        section_header("PRATIPAKSHA COMPLETENESS (math ops with/without inverse)")
        has_pp = [
            (op, info)
            for op, info in p["pratipaksha_completeness"].items()
            if info["has_inverse"]
        ]
        no_pp = [
            (op, info)
            for op, info in p["pratipaksha_completeness"].items()
            if not info["has_inverse"]
        ]
        print(f"  HAS pratipaksha ({len(has_pp)}): {', '.join(op for op, _ in has_pp)}")
        print(
            f"  MISSING pratipaksha ({len(no_pp)}): {', '.join(op for op, _ in no_pp)}"
        )

        section_header("DOMAIN COVERAGE (tantra awareness of kosha domains)")
        cov = p.get("domain_coverage", {})
        for domain, info in list(cov.items())[:20]:
            bar = "█" * int(info["coverage_pct"] / 5)
            print(f"  {domain:<30} {info['coverage_pct']:>5.1f}%  {bar}")

    if section in ("all", "tests"):
        header("TEST GAP ANALYSIS")

        section_header("UNTESTED TANTRAS")
        print(f"  {len(ts.get('untested_tantras', []))} tantras with no test coverage:")
        for t_name in ts.get("untested_tantras", []):
            marker = " ← HUB" if t_name in ts.get("untested_hub_tantras", []) else ""
            print(f"  {t_name}{marker}")

        section_header("UNTESTED PHILOSOPHICAL CONCEPTS")
        for c in ts.get("untested_concepts", []):
            print(f"  {c}")

        section_header("UNTESTED RELATION TYPES")
        for e in ts.get("untested_edges", []):
            print(f"  {e}")

        section_header("SUGGESTED NEW TESTS")
        for s in ts.get("suggestions", []):
            print(f"\n  [{s['category']}] {s['name']}")
            print(f"  rationale: {s['rationale']}")
            print(f"  sketch:")
            for line in s["sketch"].split("\n"):
                print(f"    {line}")

        section_header("XFAIL GAP TABLE — deferred work by philosophical gate")
        print(
            "  (tests that are expected to fail — grouped by what must be built first)\n"
        )
        xfail_groups = ts.get("xfail_groups", {})
        for group_name, ginfo in xfail_groups.items():
            total = len(ginfo["found"]) + len(ginfo["missing"])
            marked = len(ginfo["has_xfail"])
            print(f"  [{group_name}]  {ginfo['description']}")
            print(f"    gate:      {ginfo['gate']}")
            print(
                f"    tests:     {len(ginfo['found'])}/{total} in codebase, {marked} with xfail marker"
            )
            print(f"    philosophy: {ginfo['philosophy'][:120]}")
            if ginfo["found"]:
                for t in ginfo["found"][:5]:
                    marker = (
                        " ✓xfail" if t in ginfo["has_xfail"] else " (no xfail marker!)"
                    )
                    print(f"      {t}{marker}")
            if ginfo["missing"]:
                print(f"    missing from codebase:")
                for t in ginfo["missing"][:3]:
                    print(f"      {t}")
            print()
    if section in ("all", "micro"):
        m = result.get("micro", {})
        header(
            f"MICRO-PATTERN ANALYSIS  "
            f"({m.get('total_tantras_scanned', 0)} tantras scanned)"
        )

        section_header("CANDIDATE MICRO-TANTRAS (ranked by hit count)")
        print(
            "  These repeated inline expressions are candidates for named philosophical\n"
            "  micro-tantras — small, one-purpose tantras with Sanskrit names.\n"
        )
        print(f"  {'name':<20} {'hits':>4}  {'files':>5}  sanskrit root")
        print(f"  {'─' * 70}")
        for pat in m.get("patterns", []):
            if pat["hit_count"] == 0:
                continue
            print(
                f"  {pat['name']:<20} {pat['hit_count']:>4}  "
                f"{pat['file_count']:>5}  {pat['sanskrit']}"
            )

        print()
        for pat in m.get("patterns", []):
            if pat["hit_count"] == 0:
                continue
            print(f"  ── {pat['name']}  ({pat['sanskrit']})")
            print(f"     replaces: {pat['replaces']}")
            print(f"     note:     {pat['note']}")

            # graph grounding — what the live graph knows about this concept
            gg = pat.get("graph_grounding", {})
            if gg.get("found"):
                satya = gg.get("satya", 0)
                sw = ", ".join(gg.get("swarupa", []))
                kr = ", ".join(gg.get("kriya", []))
                ready = "✓ ready" if gg.get("ready") else "⚠ not ready"
                exists = " (tantra already exists)" if gg.get("proposed_exists") else ""
                print(
                    f"     graph:    {pat['graph_node']}  satya={satya:.3f}  {ready}{exists}"
                )
                if sw:
                    print(f"               swarupa: {sw}")
                if kr:
                    print(f"               kriya:   {kr}")
                print(f"     meaning:  {pat['graph_meaning'][:120]}")
            elif "graph_node" in pat:
                print(f"     graph:    {pat['graph_node']}  (not found in live graph)")

            print(f"     body:")
            for line in pat.get("body", "").split("\n"):
                print(f"       {line}")
            print(f"     files ({pat['file_count']}): {', '.join(pat['files'])}")
            for hit in pat["hits"][:3]:
                print(f"       {hit['tantra']}:{hit['lineno']}  {hit['text'][:80]}")
            if len(pat["hits"]) > 3:
                print(f"       ... and {len(pat['hits']) - 3} more")
            print()

        section_header("REPEATED QUERY SHAPES (3+ tantras, candidate readers)")
        print(
            "  Same pipe-query pattern appearing across many tantras —\n"
            "  each is a candidate named READER tantra.\n"
        )
        for shape in m.get("repeated_query_shapes", [])[:15]:
            print(f"  {shape['count']:>3}×  {shape['shape']}")
            print(f"       {', '.join(shape['tantras'])}")

    if section in ("all", "roles"):
        r = result.get("roles", {})
        header("TANTRA ROLE CLASSIFICATION")

        section_header("ROLE COUNTS")
        for role, count in sorted(r.get("role_counts", {}).items()):
            names = r.get("by_role", {}).get(role, [])
            print(
                f"  {role:<15} {count:>3}   {', '.join(names[:8])}"
                + ("..." if len(names) > 8 else "")
            )

        section_header("PURE RENAMES (WRAPPER tantras with ≤1 callee, ≤15 AST nodes)")
        print(
            "  These WRAPPERs add only a philosophical name — no logic.\n"
            "  They exist for tantra3's benefit. If tantra3 is retired or\n"
            "  collapsed into anuvada-ganana, these become deletable.\n"
        )
        for name in r.get("pure_renames", []):
            info = r["classified"].get(name, {})
            print(f"  {name:<28} → {info.get('why', '')}")

        section_header("REDUNDANT ENTRY POINTS")
        print(
            "  Multiple tantras do sentence→answer. Only one should be the\n"
            "  canonical entry point. The others are candidates for deletion\n"
            "  or consolidation.\n"
        )
        for name in r.get("redundant_entries", []):
            info = r["classified"].get(name, {})
            print(f"  {name:<28} {info.get('ast_nodes', 0)} AST nodes")
            callees = info.get("callees", [])
            print(f"    calls: {', '.join(callees[:8])}")

        section_header("FULL CLASSIFICATION")
        classified = r.get("classified", {})
        role_order = [
            "ENTRY",
            "WORKER",
            "WRAPPER",
            "AVRTI-PASS",
            "QG-PASS",
            "READER",
            "EQUATION",
            "EMIT-HELPER",
            "EXEC-HELPER",
        ]
        for role in role_order:
            names = r.get("by_role", {}).get(role, [])
            if not names:
                continue
            print(f"\n  {role} ({len(names)})")
            for name in names:
                info = classified.get(name, {})
                callers_str = (
                    f"  ← {', '.join(info['callers'][:3])}" if info["callers"] else ""
                )
                print(
                    f"    {name:<30} {info['ast_nodes']:>4} nodes  {info.get('why', '')[:50]}{callers_str}"
                )

    print()


# ── entry point ───────────────────────────────────────────────────────────────


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--socket", default="/tmp/vy.sock")
    parser.add_argument("--dir", default=None, help="brahman root dir")
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--report",
        default="all",
        choices=[
            "all",
            "tantra",
            "om",
            "philosophical",
            "bridge",
            "tests",
            "micro",
            "roles",
        ],
    )
    args = parser.parse_args()

    if args.dir is None:
        script_dir = os.path.dirname(os.path.abspath(__file__))
        repo_root = os.path.dirname(script_dir)
        args.dir = os.path.join(repo_root, "brahman")

    yantra_dir = os.path.join(args.dir, "yantra")
    brahman_dir = args.dir

    if not os.path.isdir(yantra_dir):
        print(f"ERROR: yantra dir not found: {yantra_dir}", file=sys.stderr)
        sys.exit(1)

    if not os.path.exists(args.socket):
        print(f"ERROR: socket not found: {args.socket}", file=sys.stderr)
        print("Start the server first.", file=sys.stderr)
        sys.exit(1)

    result = run_full_analysis(args.socket, yantra_dir, brahman_dir)

    if args.json:
        # om nodes are large — exclude raw om data from json output
        print(json.dumps(result, indent=2, default=str))
    else:
        print_report(result, args.report)
