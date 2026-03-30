"""tantra4.py — Parse .tantra4 and .prakriya s-expression files.

Format:
    (tantra name (params...)
      (let-binding expr)
      ...)

No server needed. Reads directly from disk.
"""

import glob
import os
import re
from collections import defaultdict, OrderedDict

from upakarana2.paths import YANTRA

TANTRA_GROUPS = OrderedDict([
    ("pipeline", "orchestrator — sentence → answer"),
    ("construct", "layer 1 — sentence → raw question graph"),
    ("assert", "layer 2 — raw graph → asserted graph"),
    ("refine", "layer 3 — asserted → refined graph (fixpoint)"),
    ("expand", "layer 4 — refined → expanded graph (kosha injection)"),
    ("detect", "layer 5 — expanded → intent signals"),
    ("dispatch", "layer 6 — signals → answer"),
    ("emit", "layer 7 — answer + graph → formatted output"),
    ("equations", "physics equation tantras"),
    ("boot", "bootstrap + reload"),
])

# Keywords that are NOT tantra calls
_KEYWORDS = {
    "tantra", "takes", "return", "done", "otherwise", "cond", "let",
    "scan", "from", "where", "collect", "emit", "set", "fn",
    "to-string", "to-number", "string-length", "nth", "length",
    "append", "filter", "reduce", "map", "exists", "member", "unique",
    "gt", "lt", "eq", "neq", "ge", "le", "and", "or", "not",
    "sub", "mul", "add", "div", "apply-op", "debug-print",
    "walk", "walk-in", "emit-node", "inspect-node",
    "shabda", "shabda-anveshana", "word-node",
    "call-tantra", "fixpoint", "ppr", "has-edge",
    "concat", "split", "starts-with", "ends-with", "substr",
    "pair", "first", "second", "range", "flatten", "sort-by",
    "max", "min", "abs", "power", "half", "double", "square",
}


def find_all(root=None):
    """Find all .tantra4 and .prakriya files."""
    r = str(root or YANTRA)
    t4 = glob.glob(os.path.join(r, "**", "*.tantra4"), recursive=True)
    pr = glob.glob(os.path.join(r, "**", "*.prakriya"), recursive=True)
    return sorted(t4 + pr)


def group_of(path, root=None):
    """Extract group name from path (directory under yantra/)."""
    r = str(root or YANTRA)
    rel = os.path.relpath(path, r)
    parts = rel.split(os.sep)
    return parts[0] if len(parts) > 1 else "root"


def parse(path, root=None):
    """Parse one .tantra4/.prakriya file into a structured dict."""
    try:
        with open(path) as f:
            source = f.read()
    except Exception:
        return None

    lines = source.split("\n")

    # Strip leading comments
    stripped = re.sub(r'(?m)^\s*(?:--|;).*\n', '', source)

    # Match header: (tantra name (params...))
    m = re.match(r'\(\s*tantra\s+([a-z][a-z0-9-]*)\s*\(([^)]*)\)', stripped)
    if not m:
        return None

    name = m.group(1)
    params_str = m.group(2).strip()
    takes = params_str.split() if params_str else []

    # Comments
    comments = []
    for line in lines:
        s = line.strip()
        if s.startswith("--"):
            comments.append(s[2:].strip())
        elif s.startswith(";"):
            comments.append(s[1:].strip())

    # Let bindings
    body_text = stripped[m.end():]
    bindings = []
    for bm in re.finditer(r'\(([a-z][a-z0-9-]*)\s+', body_text):
        bname = bm.group(1)
        if bname in _KEYWORDS or bname == "tantra":
            continue
        depth = 1
        pos = bm.end()
        while pos < len(body_text) and depth > 0:
            if body_text[pos] == '(':
                depth += 1
            elif body_text[pos] == ')':
                depth -= 1
            pos += 1
        expr = body_text[bm.start() + 1:pos - 1].strip()
        bindings.append({
            "name": bname,
            "expr": expr[:120] + "..." if len(expr) > 120 else expr,
        })

    # Counts
    cond_count = source.count(" cond ") + source.count("(cond ")
    reduce_count = len(re.findall(r'\breduce\b', source))
    from_count = len(re.findall(r'\|\s*where\b', source))

    # Call detection
    all_ids = set(re.findall(r'\b([a-z][a-z0-9]*(?:-[a-z0-9]+)+)\b', source))
    own = {name} | set(takes) | {b["name"] for b in bindings}
    calls = sorted(all_ids - own - _KEYWORDS)

    return {
        "name": name,
        "path": path,
        "group": group_of(path, root),
        "takes": takes,
        "bindings": bindings,
        "comments": comments,
        "conds": cond_count,
        "reduces": reduce_count,
        "froms": from_count,
        "lines": len(lines),
        "calls": calls,
        "source": source,
    }


def load_all(root=None):
    """Load and parse all tantras, return OrderedDict keyed by name."""
    tantras = OrderedDict()
    for path in find_all(root):
        parsed = parse(path, root)
        if parsed:
            tantras[parsed["name"]] = parsed
    return tantras


# --- Call graph ---

# OCaml entry points: tantras invoked from vyakarana.ml / kriya_eval.ml
_OCAML_ENTRY_POINTS = {
    "anuvada-ganana",    # kriya_eval.ml — main pipeline
    "session-anuvada",   # kriya_eval.ml — session-aware pipeline
    "darshana",          # vyakarana.ml — node inspection
    "reboot",            # vyakarana.ml — graph reboot
    "execute-mantra",    # kriya_graph.ml — mantra execution
    "varga-inheritance", # vyakarana.ml — boot-time generation
}


def call_graph(tantras):
    """Forward call graph: name → [called tantra names].

    Uses the loaded tantra name set as the ground truth for what counts as a
    tantra call, rather than relying on a hand-maintained keyword exclusion list.
    Also detects dynamic call-tantra invocations with string literals.
    """
    known = set(tantras.keys())
    cg = {}
    for name, t in tantras.items():
        source = t["source"]
        # strip comments
        source_nc = re.sub(r'(?m)\s*--.*$', '', source)
        # find all identifiers, then keep only known tantra names (minus self)
        all_ids = set(re.findall(r'\b([a-z][a-z0-9]*(?:-[a-z0-9]+)+)\b', source_nc))
        calls = {c for c in all_ids if c in known and c != name}

        # also detect dynamic call-tantra "name"
        dynamic = set(re.findall(r'call-tantra\s+"([a-z][a-z0-9-]*)"', source_nc))
        calls |= {c for c in dynamic if c in known}

        cg[name] = sorted(calls)
    return cg


def reverse_call_graph(cg):
    """Reverse: name → [tantras that call this one]."""
    rev = defaultdict(list)
    for caller, callees in cg.items():
        for callee in callees:
            rev[callee].append(caller)
    return {k: sorted(v) for k, v in rev.items()}


def reachability(tantras):
    """BFS from OCaml entry points through the call graph.

    Returns dict with:
      reachable: set of tantra names reachable from entry points
      unreachable: set of tantra names NOT reachable
      entry_points: the OCaml entry points that exist
      layers: dict of depth → [names] (BFS distance from nearest entry)
    """
    cg = call_graph(tantras)
    known = set(tantras.keys())
    entry = _OCAML_ENTRY_POINTS & known

    visited = set()
    layers = defaultdict(list)
    queue = [(name, 0) for name in sorted(entry)]
    for name, _ in queue:
        visited.add(name)
        layers[0].append(name)

    while queue:
        current, depth = queue.pop(0)
        for callee in cg.get(current, []):
            if callee not in visited:
                visited.add(callee)
                layers[depth + 1].append(callee)
                queue.append((callee, depth + 1))

    return {
        "reachable": visited,
        "unreachable": known - visited,
        "entry_points": sorted(entry),
        "layers": {d: sorted(names) for d, names in sorted(layers.items())},
    }


# --- Grouping ---

def by_group(tantras):
    """Group tantras by group name."""
    groups = defaultdict(list)
    for t in tantras.values():
        groups[t["group"]].append(t)
    return groups


# --- Queries ---

def search(tantras, pattern):
    """Regex search across tantra source."""
    rx = re.compile(pattern, re.IGNORECASE)
    results = []
    for t in tantras.values():
        matches = []
        for i, line in enumerate(t["source"].split("\n"), 1):
            if rx.search(line):
                matches.append({"line": i, "text": line.rstrip()})
        if matches:
            results.append({
                "name": t["name"], "group": t["group"],
                "path": t["path"], "matches": matches,
            })
    return results


# --- Summary ---

def summary(tantras):
    """Compact summary dict."""
    groups = defaultdict(int)
    for t in tantras.values():
        groups[t["group"]] += 1
    return {
        "total": len(tantras),
        "total_lines": sum(t["lines"] for t in tantras.values()),
        "groups": dict(groups),
    }
