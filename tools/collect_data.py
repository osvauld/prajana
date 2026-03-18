#!/usr/bin/env python3
"""
collect_data.py — gather all analysis data from the live server into /tmp/*.json

Runs first. All other tools read from these cached files.
Requires: vyakarana server running on --socket path.

Usage:
    python3 tools/collect_data.py [--socket /tmp/vy.sock] [--brahman ../brahman]
    python3 tools/collect_data.py --only graph   # just graph_deep.json
    python3 tools/collect_data.py --only vocab   # just om_vocab.json
    python3 tools/collect_data.py --only scan    # just scan_machines.json
    python3 tools/collect_data.py --only deps    # just dep_order.json

Outputs (all in /tmp/):
    analysis.json     — full tantra/om/philosophical/test analysis
    graph_deep.json   — graph node data: satya, degree, abheda rings, orphans
    om_vocab.json     — om vocabulary: dangling, hapax, dead refs, unique shabda
    scan_machines.json — scan state machine transition tables
    dep_order.json    — topological migration order + zero-satya stub data
"""

import json, sys, os, re, glob, socket as socket_mod, argparse
from collections import defaultdict, Counter

BRAHMAN_DEFAULT = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "brahman"
)
SOCKET_DEFAULT = "/tmp/vy.sock"
OUT_DIR = "/tmp"


# ── socket ─────────────────────────────────────────────────────────────────────


def q(sock_path, cmd):
    with socket_mod.socket(socket_mod.AF_UNIX, socket_mod.SOCK_STREAM) as s:
        s.connect(sock_path)
        s.sendall((json.dumps(cmd) + "\n").encode())
        data = b""
        while True:
            c = s.recv(65536)
            if not c:
                break
            data += c
            try:
                return json.loads(data)
            except:
                continue
    return {}


# ── collectors ────────────────────────────────────────────────────────────────


def collect_analysis(sock_path, brahman_dir):
    """Full tantra/om/philosophical/test analysis via analyze_tantras.py"""
    script = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "analyze_tantras.py"
    )
    yantra_dir = os.path.join(brahman_dir, "yantra")
    import subprocess, tempfile

    out_path = os.path.join(OUT_DIR, "analysis.json")
    print("  collecting analysis.json...", end=" ", flush=True)
    result = subprocess.run(
        [sys.executable, script, "--socket", sock_path, "--dir", brahman_dir, "--json"],
        capture_output=True,
        text=True,
        timeout=300,
    )
    if result.returncode != 0 or not result.stdout.strip():
        print(f"FAILED: {result.stderr[:200]}")
        return False
    with open(out_path, "w") as f:
        f.write(result.stdout)
    print(f"done ({os.path.getsize(out_path):,} bytes)")
    return True


def collect_graph_deep(sock_path):
    """Deep graph inspection: satya, degree, abheda rings, orphans, ungrounded hubs."""
    out_path = os.path.join(OUT_DIR, "graph_deep.json")
    print("  collecting graph_deep.json...", end=" ", flush=True)

    nodes_r = q(sock_path, {"command": "eval-json", "expr": "graph-all-nodes"})
    nodes = nodes_r.get("result", [])
    if not nodes:
        print("FAILED: no nodes returned")
        return False

    node_data = {}
    for node in nodes:
        if not isinstance(node, str):
            continue
        r = q(sock_path, {"command": "inspect-node", "name": node})
        if r and r.get("status") == "ok":
            out_rels = Counter(e["relation"] for e in r.get("out_edges", []))
            node_data[node] = {
                "satya": r.get("satya", 0),
                "in": len(r.get("in_edges", [])),
                "out": dict(out_rels),
                "out_total": sum(out_rels.values()),
            }

    orphans = {
        n: d for n, d in node_data.items() if d["in"] == 0 and d["out_total"] > 0
    }
    terminals = [n for n, d in node_data.items() if d["out_total"] == 0]
    hubs = sorted(
        node_data.items(), key=lambda x: x[1]["in"] + x[1]["out_total"], reverse=True
    )[:50]
    ungrounded = sorted(
        [
            (n, d)
            for n, d in node_data.items()
            if d["satya"] == 0 and d["in"] + d["out_total"] >= 3
        ],
        key=lambda x: x[1]["in"] + x[1]["out_total"],
        reverse=True,
    )[:50]

    # abheda rings — concepts with 3+ abheda equivalences
    abheda_rings = {}
    for node in node_data:
        r = q(sock_path, {"command": "inspect-node", "name": node})
        if r and r.get("status") == "ok":
            ab = [
                e["target"] for e in r.get("out_edges", []) if e["relation"] == "abheda"
            ]
            sw = [
                e["target"]
                for e in r.get("out_edges", [])
                if e["relation"] == "swarupa"
            ]
            if len(ab) >= 3:
                abheda_rings[node] = {"abheda": ab, "swarupa": sw}

    result = {
        "total_nodes": len(node_data),
        "orphans": dict(
            sorted(orphans.items(), key=lambda x: x[1]["out_total"], reverse=True)[:100]
        ),
        "orphan_count": len(orphans),
        "terminals": sorted(terminals)[:100],
        "terminal_count": len(terminals),
        "hubs": [[n, d] for n, d in hubs],
        "ungrounded_hubs": [[n, d] for n, d in ungrounded],
        "abheda_rings": abheda_rings,
    }
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(
        f"done ({os.path.getsize(out_path):,} bytes, "
        f"{len(abheda_rings)} rings, {len(orphans)} orphans)"
    )
    return True


def collect_om_vocab(brahman_dir):
    """Om vocabulary: dangling nodes, hapax legomena, dead sloka targets, unique shabda."""
    out_path = os.path.join(OUT_DIR, "om_vocab.json")
    print("  collecting om_vocab.json...", end=" ", flush=True)

    FIRST_WORD_RE = re.compile(r"^([a-z]+)\s+([a-z][a-z0-9-]*)", re.MULTILINE)
    SHABDA_RE = re.compile(r"\bshabda\s+([^\n]+)", re.MULTILINE)
    SLOKA_TARGET_RE = re.compile(
        r"\b([a-z][a-z0-9-]*?)-(swarupa|yukta|sthita|kriya|phala|janya|abheda|"
        r"siddha|vishesa|varga|pratipaksha|amsha)\b"
    )
    WORD_RE = re.compile(r"\b([a-z][a-z0-9-]{2,})\b")
    OM_KEYWORDS = {
        "kosha",
        "sangati",
        "mantra",
        "bhasha",
        "done",
        "shabda",
        "tantra",
        "swarupa",
        "yukta",
        "sthita",
        "kriya",
        "phala",
        "janya",
        "abheda",
        "siddha",
        "vishesa",
        "varga",
        "pratipaksha",
        "amsha",
        "engine",
        "identity",
        "hypothesis",
        "proof",
        "process",
        "read",
        "derived",
        "confidence",
        "sthalam",
        "write",
        "found",
        "observed",
        "and",
        "for",
        "got",
        "count",
        "from",
        "test",
        "verify",
        "tier",
        "system",
        "capability",
    }

    all_node_names = set()
    all_shabda_words = set()
    all_sloka_targets = set()
    no_shabda_nodes = set()
    file_data = []
    word_occurrences = Counter()
    word_to_files = defaultdict(set)

    for path in sorted(
        glob.glob(os.path.join(brahman_dir, "**", "*.om"), recursive=True)
    ):
        try:
            content = open(path).read()
        except:
            continue
        rel = os.path.relpath(path, brahman_dir)
        m = FIRST_WORD_RE.search(content)
        if not m:
            continue
        node_type, node_name = m.group(1), m.group(2)
        all_node_names.add(node_name)

        # shabda
        shabda_words = []
        for sm in SHABDA_RE.finditer(content):
            for token in re.split(r"[\s,/]+", sm.group(1).strip()):
                token = token.strip()
                if not token:
                    continue
                alias = token.split(":", 1)[1].strip() if ":" in token else token
                if alias:
                    shabda_words.append(alias)
                    all_shabda_words.add(alias)
        if not shabda_words and node_type in ("kosha", "sangati"):
            no_shabda_nodes.add(node_name)

        # sloka targets
        for sm in SLOKA_TARGET_RE.finditer(content):
            all_sloka_targets.add(sm.group(1))

        # word frequency
        seen = set()
        for wm in WORD_RE.finditer(content):
            w = wm.group(1)
            if len(w) >= 4 and w not in OM_KEYWORDS and w not in seen:
                seen.add(w)
                word_occurrences[w] += 1
                word_to_files[w].add(rel)

        file_data.append(
            {
                "node_type": node_type,
                "node_name": node_name,
                "shabda": shabda_words,
                "path": rel,
            }
        )

    # dangling: node names never referenced as sloka targets
    dangling_nodes = set()
    for node in all_node_names:
        parts = re.split(r"-", node)
        if not (
            node in all_sloka_targets
            or any(p in all_sloka_targets for p in parts if len(p) > 3)
        ):
            dangling_nodes.add(node)

    # unique shabda: words in exactly one file
    unique_shabda = {
        w: list(word_to_files[w])[0]
        for w in all_shabda_words
        if word_occurrences.get(w, 0) == 1
    }

    # dead sloka targets: referenced in slokas but never declared as nodes
    dead_sloka_targets = {
        t
        for t in all_sloka_targets
        if t not in all_node_names and len(t) > 3 and word_occurrences.get(t, 0) <= 1
    }

    # hapax legomena: words in exactly one file
    hapax = {
        w: list(word_to_files[w])[0]
        for w, c in word_occurrences.items()
        if c == 1
        and len(w) >= 5
        and w not in ("done", "takes", "return", "result", "tantra", "kosha", "sangati")
    }

    result = {
        "total_nodes": len(all_node_names),
        "total_shabda_words": len(all_shabda_words),
        "total_sloka_targets": len(all_sloka_targets),
        "dangling_nodes": sorted(dangling_nodes)[:300],
        "dangling_node_count": len(dangling_nodes),
        "unique_shabda": dict(list(sorted(unique_shabda.items()))[:300]),
        "unique_shabda_count": len(unique_shabda),
        "dead_sloka_targets": sorted(dead_sloka_targets)[:300],
        "dead_sloka_count": len(dead_sloka_targets),
        "no_shabda_nodes": sorted(no_shabda_nodes)[:300],
        "no_shabda_count": len(no_shabda_nodes),
        "hapax_legomena": dict(list(sorted(hapax.items()))[:400]),
        "hapax_count": len(hapax),
        "word_frequency": dict(
            sorted(word_occurrences.items(), key=lambda x: x[1], reverse=True)[:150]
        ),
    }
    with open(out_path, "w") as f:
        json.dump(result, f, indent=2)
    print(
        f"done ({os.path.getsize(out_path):,} bytes, "
        f"{len(dangling_nodes)} dangling, {len(hapax)} hapax)"
    )
    return True


def collect_scan_machines(sock_path, yantra_dir):
    """Scan state machine transition tables from AST."""
    out_path = os.path.join(OUT_DIR, "scan_machines.json")
    print("  collecting scan_machines.json...", end=" ", flush=True)

    SCAN_FILES = [
        "vibhakti/vibhakti-shashthi.tantra2",
        "vishesa/vishesa-instance.tantra2",
        "vishesa/agra-bandha.tantra2",
        "vishesa/rashi-viveka.tantra2",
        "vishesa/vishesa-bandhana.tantra2",
        "sandhi/sandhi-bandhana.tantra2",
        "sankhya/sankhya-bandha.tantra2",
        "sankhya/count-bandha.tantra2",
    ]

    def find_scans(expr):
        if not isinstance(expr, dict):
            return []
        out = []
        if expr.get("kind") == "scan":
            out.append(expr)
        for key in (
            "args",
            "body",
            "value",
            "collect",
            "source",
            "otherwise",
            "items",
            "guards",
        ):
            c = expr.get(key)
            if isinstance(c, list):
                for i in c:
                    out.extend(find_scans(i))
            elif isinstance(c, dict):
                out.extend(find_scans(c))
        for b in expr.get("branches", []):
            out.extend(find_scans(b.get("guard") or {}))
            for s in b.get("body", []):
                out.extend(find_scans_stmt(s))
        return out

    def find_scans_stmt(s):
        if not isinstance(s, dict):
            return []
        out = []
        for key in ("expr", "guard"):
            c = s.get(key)
            if c:
                out.extend(find_scans(c))
        for key in ("body", "otherwise"):
            for ss in s.get(key, []):
                out.extend(find_scans_stmt(ss))
        return out

    def dexpr(e, d=0):
        if not isinstance(e, dict):
            return str(e)
        k = e.get("kind")
        if k == "var":
            return e.get("name", "?")
        if k == "str":
            return f'"{e.get("value", "")}"'
        if k == "lit":
            return str(e.get("value", ""))
        if k == "bool":
            return str(e.get("value", ""))
        if k == "call":
            op = e.get("op", "?")
            if d > 2:
                return f"{op}(...)"
            return f"{op}({', '.join(dexpr(a, d + 1) for a in e.get('args', []))})"
        if k == "from":
            fs = []
            for g in e.get("guards", []):
                if isinstance(g, dict) and g.get("op") in ("eq", "neq"):
                    for a in g.get("args", []):
                        if isinstance(a, dict) and a.get("kind") == "str":
                            fs.append(f"{g['op']}:{a['value']}")
            return f"from[{','.join(fs)}]→{dexpr(e.get('collect', {}), d + 1)}"
        if k == "list":
            return f"[{','.join(dexpr(i, d + 1) for i in e.get('items', [])[:3])}]"
        return k

    def dstmt(s, indent=0):
        if not isinstance(s, dict):
            return str(s)
        k = s.get("kind")
        pad = "  " * indent
        if k == "emit":
            return f"{pad}emit {dexpr(s.get('expr', {}))}"
        if k == "skip":
            return f"{pad}skip"
        if k == "set":
            return f"{pad}{s.get('name', '?')} ← {dexpr(s.get('expr', {}))}"
        if k == "clear":
            return f"{pad}clear {s.get('name', '?')}"
        if k == "slet":
            return f"{pad}let {s.get('name', '?')} = {dexpr(s.get('expr', {}))}"
        if k == "when":
            body = "\n".join(dstmt(x, indent + 1) for x in s.get("body", []))
            alt = "\n".join(dstmt(x, indent + 1) for x in s.get("otherwise", []))
            r = f"{pad}when {dexpr(s.get('guard', {}))}:\n{body}"
            if alt:
                r += f"\n{pad}otherwise:\n{alt}"
            return r
        return f"{pad}{k}"

    machines = {}
    for rel_path in SCAN_FILES:
        full_path = os.path.join(yantra_dir, rel_path)
        resp = q(sock_path, {"command": "dump-ast", "path": full_path})
        t = (resp or {}).get("tantra", {})
        name = t.get("name", os.path.basename(rel_path).replace(".tantra2", ""))
        scans = []
        for binding in t.get("bindings", []):
            for scan in find_scans(binding.get("expr", {})):
                state = [
                    (sd["name"], dexpr(sd.get("init", {})))
                    for sd in scan.get("state", [])
                ]
                transitions = []
                for br in scan.get("branches", []):
                    guard = br.get("guard")
                    writes = []
                    for s in br.get("body", []):
                        if s.get("kind") in ("set", "clear"):
                            writes.append(s.get("name", "?"))
                        elif s.get("kind") == "when":
                            for ss in s.get("body", []) + s.get("otherwise", []):
                                if ss.get("kind") in ("set", "clear"):
                                    writes.append(ss.get("name", "?"))
                    transitions.append(
                        {
                            "guard": dexpr(guard) if guard else "OTHERWISE",
                            "is_default": guard is None,
                            "writes": sorted(set(writes)),
                            "body": [dstmt(s) for s in br.get("body", [])],
                        }
                    )
                scans.append(
                    {
                        "binding": binding.get("name", "?"),
                        "state_vars": state,
                        "transitions": transitions,
                    }
                )
        machines[name] = scans

    with open(out_path, "w") as f:
        json.dump(machines, f, indent=2)
    print(f"done ({os.path.getsize(out_path):,} bytes)")
    return True


def collect_dep_order(sock_path, yantra_dir):
    """Topological migration order + zero-satya stub data."""
    out_path = os.path.join(OUT_DIR, "dep_order.json")
    print("  collecting dep_order.json...", end=" ", flush=True)

    try:
        analysis = json.load(open(os.path.join(OUT_DIR, "analysis.json")))
    except:
        print("FAILED: analysis.json not found, run --only analysis first")
        return False

    call_graph = analysis["tantra"]["call_graph"]
    reverse_graph = analysis["tantra"]["reverse_graph"]
    complexity = analysis["tantra"]["complexity"]

    from collections import deque

    all_tantras = set(call_graph.keys())
    in_degree = {n: len(reverse_graph.get(n, [])) for n in all_tantras}
    queue = deque(n for n in all_tantras if in_degree[n] == 0)
    topo = []
    visited = set()
    while queue:
        n = queue.popleft()
        if n in visited:
            continue
        visited.add(n)
        topo.append(n)
        for callee in call_graph.get(n, []):
            in_degree[callee] = in_degree.get(callee, 1) - 1
            if in_degree.get(callee, 0) <= 0 and callee not in visited:
                queue.append(callee)
    for n in all_tantras:
        if n not in visited:
            topo.append(n)

    migration = []
    for name in topo:
        callers = reverse_graph.get(name, [])
        callees = call_graph.get(name, [])
        c = complexity.get(name, {})
        risk = "low"
        if len(callers) >= 3:
            risk = "high"
        elif len(callers) >= 1:
            risk = "medium"
        if c.get("scan_count", 0) > 0:
            risk = "medium" if risk == "low" else risk
        migration.append(
            {
                "name": name,
                "callers": callers,
                "callees": callees,
                "caller_count": len(callers),
                "callee_count": len(callees),
                "ast_nodes": c.get("ast_nodes", 0),
                "max_depth": c.get("max_depth", 0),
                "has_scan": c.get("scan_count", 0) > 0,
                "migration_risk": risk,
                "reason": (
                    "leaf — no callers, safe to migrate first"
                    if not callers
                    else f"called by {len(callers)}: {', '.join(callers[:3])}"
                ),
            }
        )

    # zero-satya tantra nodes
    zero_satya = []
    for name, d in complexity.items():
        r = q(sock_path, {"command": "inspect-node", "name": name})
        satya = r.get("satya", -1) if r and r.get("status") == "ok" else -1
        if satya == 0.0:
            resp = q(
                sock_path,
                {"command": "dump-ast", "path": os.path.join(yantra_dir, d["file"])},
            )
            t = (resp or {}).get("tantra", {})
            zero_satya.append(
                {
                    "name": name,
                    "satya": satya,
                    "inputs": [p["name"] for p in t.get("inputs", [])],
                    "returns": [p["name"] for p in t.get("returns", [])],
                    "calls": call_graph.get(name, []),
                    "called_by": reverse_graph.get(name, []),
                    "file": d["file"],
                }
            )

    with open(out_path, "w") as f:
        json.dump(
            {"topological_order": migration, "zero_satya_tantras": zero_satya},
            f,
            indent=2,
        )
    print(
        f"done ({os.path.getsize(out_path):,} bytes, "
        f"{len(zero_satya)} zero-satya nodes)"
    )
    return True


# ── main ───────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--socket", default=SOCKET_DEFAULT)
    parser.add_argument("--brahman", default=None)
    parser.add_argument(
        "--only", default=None, choices=["analysis", "graph", "vocab", "scan", "deps"]
    )
    args = parser.parse_args()

    if args.brahman is None:
        args.brahman = BRAHMAN_DEFAULT

    yantra_dir = os.path.join(args.brahman, "yantra")

    if not os.path.exists(args.socket):
        print(f"ERROR: socket not found: {args.socket}")
        print("Start the server first: vyakarana.exe --socket /tmp/vy.sock ../brahman")
        sys.exit(1)

    print(f"Collecting data → {OUT_DIR}/")
    ok = True
    if args.only in (None, "analysis"):
        ok &= collect_analysis(args.socket, args.brahman)
    if args.only in (None, "graph"):
        ok &= collect_graph_deep(args.socket)
    if args.only in (None, "vocab"):
        ok &= collect_om_vocab(args.brahman)
    if args.only in (None, "scan"):
        ok &= collect_scan_machines(args.socket, yantra_dir)
    if args.only in (None, "deps"):
        ok &= collect_dep_order(args.socket, yantra_dir)

    print(f"\n{'All done.' if ok else 'Some collections failed.'}")
    print(f"Run: python3 tools/generate_reports.py")
