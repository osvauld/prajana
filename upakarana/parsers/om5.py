"""om5.py — Parse .om5 s-expression files.

Format:
    (layer name
      (relation target target ...)
      (relation target ...)
      ...)

No server needed. Reads directly from disk.
"""

import glob
import os
import re
from collections import defaultdict, OrderedDict

from upakarana.paths import BRAHMAN

LAYERS = ("sangati", "kosha", "bhasha", "mantra")

_HEADER_RE = re.compile(
    r"\(\s*(" + "|".join(LAYERS) + r")\s+([a-zA-Z][a-zA-Z0-9-]*)"
)


def find_all(root=None):
    """Find all .om5 files under brahman/."""
    r = str(root or BRAHMAN)
    return sorted(glob.glob(os.path.join(r, "**", "*.om5"), recursive=True))


def domain_of(path, root=None):
    """Extract domain (directory path) relative to brahman root."""
    r = str(root or BRAHMAN)
    return os.path.dirname(os.path.relpath(path, r))


def parse(path, root=None):
    """Parse one .om5 file into a structured dict."""
    try:
        with open(path) as f:
            source = f.read()
    except Exception:
        return None

    m = _HEADER_RE.search(source)
    if not m:
        return None

    layer = m.group(1)
    name = m.group(2)

    # Parse edge groups: (relation target target ...)
    # Match innermost parens only — [^)(]+ excludes nested groups
    edges = []
    for em in re.finditer(r"\(([a-zA-Z][a-zA-Z0-9-]*)\s+([^)(]+)\)", source):
        rel = em.group(1)
        # Skip the header match itself
        if rel in LAYERS:
            continue
        targets = em.group(2).strip().split()
        for t in targets:
            t = t.strip()
            if t:
                edges.append({"target": t, "relation": rel})

    # Comments
    comments = []
    for line in source.split("\n"):
        stripped = line.strip()
        if stripped.startswith("--") or stripped.startswith(";"):
            prefix = "--" if stripped.startswith("--") else ";"
            comments.append(stripped[len(prefix):].strip())

    return {
        "name": name,
        "layer": layer,
        "path": path,
        "domain": domain_of(path, root),
        "edges": edges,
        "comments": comments,
        "lines": len(source.split("\n")),
        "source": source,
    }


def load_all(root=None):
    """Load all om5 files, return OrderedDict keyed by name."""
    nodes = OrderedDict()
    seen = {}
    for path in find_all(root):
        parsed = parse(path, root)
        if not parsed:
            continue
        name = parsed["name"]
        if name in seen:
            # Collision: prefix with domain
            if name in nodes:
                first = nodes.pop(name)
                nodes[f"{first['domain']}/{name}"] = first
            nodes[f"{parsed['domain']}/{name}"] = parsed
        else:
            seen[name] = path
            nodes[name] = parsed
    return nodes


# --- Grouping ---

def by_layer(nodes):
    """Group nodes by layer."""
    groups = defaultdict(list)
    for n in nodes.values():
        groups[n["layer"]].append(n)
    return dict(groups)


def by_domain(nodes, depth=2):
    """Group nodes by domain at specified depth."""
    groups = defaultdict(list)
    for n in nodes.values():
        parts = n["domain"].split(os.sep)
        key = os.sep.join(parts[:depth])
        groups[key].append(n)
    return OrderedDict(sorted(groups.items()))


def domain_tree(nodes):
    """Count nodes per domain."""
    tree = defaultdict(int)
    for n in nodes.values():
        tree[n["domain"]] += 1
    return OrderedDict(sorted(tree.items()))


# --- Queries ---

def search(nodes, pattern):
    """Regex search across om5 source."""
    rx = re.compile(pattern, re.IGNORECASE)
    results = []
    for n in nodes.values():
        matches = []
        for i, line in enumerate(n["source"].split("\n"), 1):
            if rx.search(line):
                matches.append({"line": i, "text": line.rstrip()})
        if matches:
            results.append({
                "name": n["name"], "layer": n["layer"],
                "domain": n["domain"], "path": n["path"],
                "matches": matches,
            })
    return results


def with_relation(nodes, relation):
    """Nodes that have edges with given relation."""
    return [n for n in nodes.values()
            if any(e["relation"] == relation for e in n["edges"])]


def with_target(nodes, target):
    """Nodes that have edges pointing to given target."""
    return [n for n in nodes.values()
            if any(e["target"] == target for e in n["edges"])]


def edges_by_relation(node):
    """Group a node's edges by relation."""
    by_rel = defaultdict(list)
    for e in node["edges"]:
        by_rel[e["relation"]].append(e["target"])
    return dict(by_rel)


# --- Summary ---

def summary(nodes):
    """Compact summary dict."""
    layers = defaultdict(int)
    for n in nodes.values():
        layers[n["layer"]] += 1
    return {
        "total": len(nodes),
        "total_lines": sum(n["lines"] for n in nodes.values()),
        "layers": dict(layers),
        "domains": dict(domain_tree(nodes)),
    }
