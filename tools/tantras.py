"""tantras.py — parse, group, and query all tantra3 files.

No server needed. Reads .tantra3 source directly from disk.
"""

import glob
import os
import re
from collections import defaultdict, OrderedDict

from .paths import YANTRA

TANTRA_GROUPS = OrderedDict(
    [
        ("pipeline", "orchestrator — sentence → answer"),
        ("construct", "layer 1 — sentence → raw question graph"),
        ("assert", "layer 2 — raw graph → asserted graph (categorical claims)"),
        ("refine", "layer 3 — asserted → refined graph (fixpoint avrti-refine)"),
        ("expand", "layer 4 — refined → expanded graph (kosha janya injection)"),
        ("detect", "layer 5 — expanded → intent signals (parallel reads)"),
        ("dispatch", "layer 6 — signals → answer (anumana|viveka|count|derive)"),
        ("emit", "layer 7 — answer + graph → formatted output (proof + reasoning)"),
        ("equations", "physics equation tantras (ke, momentum, etc.)"),
        ("boot", "bootstrap + reload"),
    ]
)

_KEYWORDS = {
    "tantra",
    "tantra3",
    "takes",
    "return",
    "done",
    "otherwise",
    "cond",
    "let",
    "scan",
    "from",
    "where",
    "collect",
    "emit",
    "set",
    "fn",
    "to-string",
    "to-number",
    "string-length",
    "nth",
    "length",
    "append",
    "filter",
    "reduce",
    "map",
    "exists",
    "member",
    "unique",
    "gt",
    "lt",
    "eq",
    "neq",
    "and",
    "or",
    "not",
    "sub",
    "mul",
    "add",
    "div",
    "apply-op",
    "debug-print",
    "walk",
    "walk-in",
    "emit-node",
    "inspect-node",
    "shabda",
    "shabda-anveshana",
    "word-node",
    "call-tantra",
    "fixpoint",
    "ppr",
    "has-edge",
}


def find_all():
    """Find all .tantra3 and .tantra4 files under brahman/yantra/."""
    t3 = glob.glob(os.path.join(YANTRA, "**", "*.tantra3"), recursive=True)
    t4 = glob.glob(os.path.join(YANTRA, "**", "*.tantra4"), recursive=True)
    pr = glob.glob(os.path.join(YANTRA, "**", "*.prakriya"), recursive=True)
    return sorted(t3 + t4 + pr)


def group_of(path):
    """Extract group name from path (directory under yantra/)."""
    rel = os.path.relpath(path, YANTRA)
    parts = rel.split(os.sep)
    return parts[0] if len(parts) > 1 else "root"


def name_of(path):
    """Extract tantra name from path (filename without extension)."""
    return os.path.splitext(os.path.basename(path))[0]


def parse_sexp(path):
    """Parse a .tantra4 s-expression file into a structured dict."""
    try:
        with open(path) as f:
            source = f.read()
    except Exception:
        return None

    lines = source.split("\n")

    # strip leading comments (-- or ;) before matching the tantra header
    stripped_source = re.sub(r'(?m)^\s*(?:--|;).*\n', '', source)

    # extract (tantra name (params...) body...)
    m = re.match(r'\(\s*tantra\s+([a-z][a-z0-9-]*)\s*\(([^)]*)\)', stripped_source)
    if not m:
        return None
    name = m.group(1)
    params_str = m.group(2).strip()
    takes = params_str.split() if params_str else []

    comments = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("--"):
            comments.append(stripped[2:].strip())
        elif stripped.startswith(";"):
            comments.append(stripped[1:].strip())

    # extract bindings: (name expr...) at top level inside the tantra body
    # simplified: find all (identifier ...) forms after the params
    body_start = m.end()
    body_text = stripped_source[body_start:]
    bindings = []
    for bm in re.finditer(r'\(([a-z][a-z0-9-]*)\s+', body_text):
        bname = bm.group(1)
        if bname not in _KEYWORDS and bname not in {"tantra"}:
            # extract up to matching close paren
            depth = 1
            pos = bm.end()
            while pos < len(body_text) and depth > 0:
                if body_text[pos] == '(':
                    depth += 1
                elif body_text[pos] == ')':
                    depth -= 1
                pos += 1
            expr = body_text[bm.start() + 1:pos - 1].strip()
            # only count as binding if the name part looks like an assignment
            # (not a function call — bindings have the name as first token)
            bindings.append({
                "name": bname,
                "expr": expr[:120] + "..." if len(expr) > 120 else expr,
            })

    scan_count = len(re.findall(r'\bscan\s+\S+\s+\[', source))
    cond_count = source.count(" cond ") + source.count("(cond ")
    from_count = len(re.findall(r'\|\s*where\b', source))
    reduce_count = len(re.findall(r'\breduce\b', source))

    all_ids = set(re.findall(r'\b([a-z][a-z0-9]*(?:-[a-z0-9]+)+)\b', source))
    own = {name} | set(takes) | {b["name"] for b in bindings}
    call_candidates = all_ids - own - _KEYWORDS

    return {
        "name": name,
        "path": path,
        "group": group_of(path),
        "takes": takes,
        "bindings": bindings,
        "returns": "result",
        "comments": comments,
        "scans": scan_count,
        "conds": cond_count,
        "froms": from_count,
        "reduces": reduce_count,
        "lines": len(lines),
        "calls": sorted(call_candidates),
        "source": source,
    }


def parse(path):
    """Parse a tantra3 or tantra4 file into a structured dict."""
    if path.endswith(".tantra4") or path.endswith(".prakriya"):
        return parse_sexp(path)

    try:
        with open(path) as f:
            source = f.read()
    except Exception:
        return None

    lines = source.split("\n")
    name_match = re.match(r"^tantra3\s+([a-z][a-z0-9-]*)", source)
    name = name_match.group(1) if name_match else name_of(path)
    takes = re.findall(r"^takes\s+([a-z][a-z0-9-]*)", source, re.MULTILINE)

    comments = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("--"):
            comments.append(stripped[2:].strip())

    bindings = []
    for line in lines:
        m = re.match(r"^([a-z][a-z0-9-]*)\s*=\s*(.+)", line)
        if m:
            expr = m.group(2).strip()
            bindings.append(
                {
                    "name": m.group(1),
                    "expr": expr[:120] + "..." if len(expr) > 120 else expr,
                }
            )

    ret_match = re.search(r"^return\s+(.+)", source, re.MULTILINE)
    returns = ret_match.group(1).strip() if ret_match else None

    scan_count = len(re.findall(r"\bscan\s+\S+\s+\[", source))
    cond_count = source.count(" cond ") + source.count("(cond ")
    from_count = len(re.findall(r"\|\s*where\b", source))
    reduce_count = len(re.findall(r"\breduce\b", source))

    all_ids = set(re.findall(r"\b([a-z][a-z0-9]*(?:-[a-z0-9]+)+)\b", source))
    own = {name} | set(takes) | {b["name"] for b in bindings}
    call_candidates = all_ids - own - _KEYWORDS

    return {
        "name": name,
        "path": path,
        "group": group_of(path),
        "takes": takes,
        "bindings": bindings,
        "returns": returns,
        "comments": comments,
        "scans": scan_count,
        "conds": cond_count,
        "froms": from_count,
        "reduces": reduce_count,
        "lines": len(lines),
        "calls": sorted(call_candidates),
        "source": source,
    }


def load_all():
    """Load and parse all tantras, return OrderedDict keyed by name."""
    tantras = OrderedDict()
    for path in find_all():
        parsed = parse(path)
        if parsed:
            tantras[parsed["name"]] = parsed
    return tantras


def call_graph(tantras):
    """Forward call graph: name -> [called tantra names]."""
    known = set(tantras.keys())
    return {
        name: sorted({c for c in t["calls"] if c in known and c != name})
        for name, t in tantras.items()
    }


def reverse_call_graph(cg):
    """Reverse: name -> [tantras that call this one]."""
    rev = defaultdict(list)
    for caller, callees in cg.items():
        for callee in callees:
            rev[callee].append(caller)
    return {k: sorted(v) for k, v in rev.items()}


def by_group(tantras):
    """Group tantras by their group name."""
    groups = defaultdict(list)
    for t in tantras.values():
        groups[t["group"]].append(t)
    return groups


def search(tantras, pattern):
    """Search all tantra source for a regex."""
    regex = re.compile(pattern, re.IGNORECASE)
    results = []
    for t in tantras.values():
        matches = []
        for i, line in enumerate(t["source"].split("\n"), 1):
            if regex.search(line):
                matches.append({"line": i, "text": line.rstrip()})
        if matches:
            results.append(
                {
                    "name": t["name"],
                    "group": t["group"],
                    "path": t["path"],
                    "matches": matches,
                }
            )
    return results


def to_json_summary(tantras):
    """Summary without source."""
    result = {
        "total": len(tantras),
        "total_lines": sum(t["lines"] for t in tantras.values()),
        "groups": {},
        "tantras": {},
    }
    for gname, desc in TANTRA_GROUPS.items():
        gt = [t for t in tantras.values() if t["group"] == gname]
        if gt:
            result["groups"][gname] = {
                "description": desc,
                "count": len(gt),
                "lines": sum(t["lines"] for t in gt),
                "tantras": sorted(t["name"] for t in gt),
            }
    for t in tantras.values():
        result["tantras"][t["name"]] = {
            "group": t["group"],
            "path": t["path"],
            "lines": t["lines"],
            "takes": t["takes"],
            "bindings": [b["name"] for b in t["bindings"]],
            "calls": t["calls"],
            "returns": t["returns"],
            "scans": t["scans"],
            "conds": t["conds"],
            "froms": t["froms"],
            "reduces": t["reduces"],
            "comments": t["comments"],
        }
    return result


def to_json_full(tantras, group=None):
    """Full JSON with source. Optional group filter."""
    result = {}
    for t in tantras.values():
        if group and t["group"] != group:
            continue
        result[t["name"]] = {
            "group": t["group"],
            "path": t["path"],
            "lines": t["lines"],
            "takes": t["takes"],
            "bindings": t["bindings"],
            "calls": t["calls"],
            "returns": t["returns"],
            "scans": t["scans"],
            "conds": t["conds"],
            "froms": t["froms"],
            "reduces": t["reduces"],
            "comments": t["comments"],
            "source": t["source"],
        }
    return result
