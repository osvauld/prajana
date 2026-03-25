"""om5.py — Parse and serialize .om5 s-expression files.

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

from upakarana.paths import BRAHMAN, BRAHMAN2

LAYERS = ("sangati", "kosha", "bhasha", "mantra")

_HEADER_RE = re.compile(
    r"\(\s*(" + "|".join(LAYERS) + r")\s+([a-zA-Z][a-zA-Z0-9-]*)"
)


def find_all(root=None):
    """Find all .om5 files under brahman2/ (default corpus)."""
    r = str(root or BRAHMAN2)
    files = glob.glob(os.path.join(r, "**", "*.om5"), recursive=True)
    return sorted(files)


def domain_of(path, root=None):
    """Extract domain (directory path) relative to brahman root."""
    r = str(root or BRAHMAN2)
    # Handle brahman2/ paths
    r2 = str(BRAHMAN2)
    if path.startswith(r2):
        return os.path.dirname(os.path.relpath(path, r2))
    return os.path.dirname(os.path.relpath(path, r))


def _parse_node_block(source_block, layer, name, path, root):
    """Parse edges and comments from a single node's source block."""
    # Strip comment lines before edge parsing to avoid false matches
    code_lines = []
    for line in source_block.split("\n"):
        stripped = line.strip()
        if not stripped.startswith(";") and not stripped.startswith("--"):
            code_lines.append(line)
    code_source = "\n".join(code_lines)

    # Parse edge groups: (relation target target ...)
    # Match innermost parens only — [^)(]+ excludes nested groups
    edges = []
    explicit_domain = None
    for em in re.finditer(r"\(([a-zA-Z][a-zA-Z0-9-]*)\s+([^)(]+)\)", code_source):
        rel = em.group(1)
        if rel in LAYERS:
            continue
        # (domain path) is metadata, not an edge
        if rel == "domain":
            explicit_domain = em.group(2).strip()
            continue
        targets = em.group(2).strip().split()
        for t in targets:
            t = t.strip()
            if t:
                edges.append({"target": t, "relation": rel})

    # Comments (only those directly preceding or within this block)
    comments = []
    for line in source_block.split("\n"):
        stripped = line.strip()
        if stripped.startswith("--") or stripped.startswith(";"):
            prefix = "--" if stripped.startswith("--") else ";"
            comments.append(stripped[len(prefix):].strip())

    return {
        "name": name,
        "layer": layer,
        "path": path,
        "domain": explicit_domain or domain_of(path, root),
        "edges": edges,
        "comments": comments,
        "lines": len(source_block.split("\n")),
        "source": source_block,
    }


def parse_multi(path, root=None):
    """Parse an .om5 file into a list of node dicts (multi-node aware).

    Handles files with multiple (layer name ...) blocks and inline
    (mantra name ...) nested inside kosha blocks.
    """
    try:
        with open(path) as f:
            source = f.read()
    except Exception:
        return []

    results = []

    # Find all top-level (layer name ...) blocks
    # A block is top-level if its opening paren is not nested inside another block.
    # We track which regions are "inside" a kosha/sangati/bhasha block and skip
    # mantra matches that fall within those regions.
    _TOP_LEVEL_RE = re.compile(
        r"\(\s*(" + "|".join(LAYERS) + r")\s+([a-zA-Z][a-zA-Z0-9-]*)",
    )
    # First pass: find all block boundaries
    all_matches = list(_TOP_LEVEL_RE.finditer(source))
    # Determine nesting: a match is top-level if it's not inside another match's parens
    block_ranges = []  # (start, end) of top-level blocks
    for m in all_matches:
        start = m.start()
        # Find matching close paren
        depth = 0
        i = start
        block_end = len(source)
        while i < len(source):
            if source[i] == '(':
                depth += 1
            elif source[i] == ')':
                depth -= 1
                if depth == 0:
                    block_end = i + 1
                    break
            i += 1
        # Check if this match is nested inside a previously found block
        nested = False
        for (bs, be) in block_ranges:
            if start > bs and start < be:
                nested = True
                break
        if not nested:
            block_ranges.append((start, block_end))

    # Now iterate only the top-level blocks
    for m in all_matches:
        start = m.start()
        # Skip if nested
        is_top = False
        for (bs, be) in block_ranges:
            if start == bs:
                is_top = True
                break
        if not is_top:
            continue
        layer = m.group(1)
        name = m.group(2)
        start = m.start()

        # Find the matching closing paren by counting depth
        depth = 0
        i = start
        block_end = len(source)
        while i < len(source):
            if source[i] == '(':
                depth += 1
            elif source[i] == ')':
                depth -= 1
                if depth == 0:
                    block_end = i + 1
                    break
            i += 1

        block = source[start:block_end]

        # Extract inline (mantra name ...) blocks as separate nodes
        # and strip them from the parent block before parsing parent edges
        # Only do this for non-mantra top-level blocks (kosha/sangati/bhasha)
        inline_mantras = []
        clean_block = block
        if layer != "mantra":
            mantra_re = re.compile(
                r"\(\s*mantra\s+([a-zA-Z][a-zA-Z0-9-]*)"
            )
        else:
            mantra_re = None
        # Find mantras in reverse order so string positions stay valid
        mantra_matches = list(mantra_re.finditer(block)) if mantra_re else []
        for mm in reversed(mantra_matches):
            mantra_name = mm.group(1)
            # Find this mantra's closing paren
            md = 0
            mi = mm.start()
            mantra_end = len(block)
            while mi < len(block):
                if block[mi] == '(':
                    md += 1
                elif block[mi] == ')':
                    md -= 1
                    if md == 0:
                        mantra_end = mi + 1
                        break
                mi += 1
            mantra_block = block[mm.start():mantra_end]
            mantra_node = _parse_node_block(mantra_block, "mantra", mantra_name, path, root)

            # Auto-add swarupa→parent and phala→parent if missing
            has_swarupa = any(e["relation"] == "swarupa" for e in mantra_node["edges"])
            has_phala = any(e["relation"] == "phala" for e in mantra_node["edges"])
            if not has_swarupa:
                mantra_node["edges"].append({"target": name, "relation": "swarupa"})
            if not has_phala:
                mantra_node["edges"].append({"target": name, "relation": "phala"})

            inline_mantras.append(mantra_node)

            # Remove mantra block from parent source
            clean_block = clean_block[:mm.start()] + clean_block[mantra_end:]

        inline_mantras.reverse()  # restore original order

        # Parse the main node from cleaned block (mantras stripped out)
        main_node = _parse_node_block(clean_block, layer, name, path, root)

        results.append(main_node)
        results.extend(inline_mantras)

    return results


def parse(path, root=None):
    """Parse one .om5 file — returns first node (backward compat)."""
    nodes = parse_multi(path, root)
    return nodes[0] if nodes else None


def load_all(root=None):
    """Load all om5 files, return OrderedDict keyed by name.

    Multi-node aware: files with multiple (layer name ...) blocks
    produce multiple entries in the dict.
    """
    nodes = OrderedDict()
    seen = {}
    for path in find_all(root):
        parsed_list = parse_multi(path, root)
        for parsed in parsed_list:
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

# --- Serialization ---


def serialize_node(name, layer, edges, comments=None):
    """Produce om5 s-expression text.

    edges: dict of {relation: [targets]}
           e.g. {"swarupa": ["velocity"], "sthita": ["kona"]}
    comments: list of comment strings (written as ; lines)

    Returns: string of om5 source text.
    """
    lines = []
    for c in (comments or []):
        lines.append(f"; {c}")
    if comments:
        lines.append("")
    lines.append(f"({layer} {name}")
    for rel, targets in edges.items():
        if targets:
            lines.append(f"  ({rel} {' '.join(targets)})")
    lines.append(")")
    return "\n".join(lines) + "\n"


def write_node(path, name, layer, edges, comments=None):
    """Write a single om5 file to disk.

    Creates parent directories if needed.
    """
    dirpath = os.path.dirname(path)
    if dirpath:
        os.makedirs(dirpath, exist_ok=True)
    with open(path, "w") as f:
        f.write(serialize_node(name, layer, edges, comments))


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
