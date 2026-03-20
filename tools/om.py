"""om.py — parse, group, and query all .om files.

No server needed. Reads .om source directly from disk.
The folder structure IS the domain taxonomy.

Layers: kosha (domain knowledge), sangati (structural truth),
        bhasha (linguistic surface), mantra (formulas).
"""

import glob
import os
import re
from collections import defaultdict, OrderedDict

from .paths import BRAHMAN

RELATION_SUFFIXES = {
    "swarupa": "IS-A identity",
    "yukta": "endowed-with, connected-to",
    "sthita": "situated-in, domain-membership",
    "kriya": "action, process",
    "phala": "output, result",
    "janya": "input, generator",
    "abheda": "non-difference, equivalence",
    "siddha": "established, proven",
    "vishesa": "specialization",
    "varga": "category membership",
    "pratipaksha": "inverse, opposite",
    "amsha": "part-of, member-of",
    "drishthanta": "example, illustration",
    "rahita": "devoid-of, without",
}

_SLOKA_SUFFIX_RE = re.compile(
    r"\b([a-z][a-z0-9-]*)-(" + "|".join(RELATION_SUFFIXES.keys()) + r")\b"
)
_SHABDA_RE = re.compile(r"^\s*shabda\s+(.+)", re.MULTILINE)
LAYERS = ["sangati", "kosha", "bhasha", "mantra"]
_HEADER_RE = re.compile(r"^(" + "|".join(LAYERS) + r")\s+([a-z][a-z0-9-]*)")
_SLOKA_RE = re.compile(r'"([^"]+)"')


def find_all():
    return sorted(glob.glob(os.path.join(BRAHMAN, "**", "*.om"), recursive=True))


def domain_of(path):
    return os.path.dirname(os.path.relpath(path, BRAHMAN))


def domain_depth(domain, n=1):
    parts = domain.split(os.sep)
    return os.sep.join(parts[:n])


def parse(path):
    """Parse one .om file into a structured dict."""
    try:
        with open(path) as f:
            source = f.read()
    except Exception:
        return None

    header = _HEADER_RE.search(source)
    if not header:
        return None

    layer = header.group(1)
    name = header.group(2)
    slokas = _SLOKA_RE.findall(source)

    edges = []
    for sloka in slokas:
        for m in _SLOKA_SUFFIX_RE.finditer(sloka):
            edges.append({"target": m.group(1), "relation": m.group(2)})

    shabda_raw = ""
    shabda_keys = {}
    shabda_words = []
    for m in _SHABDA_RE.finditer(source):
        shabda_raw = m.group(1).strip()
        for kv in re.findall(r"([a-z][a-z0-9_-]*):([^\s,/]+)", shabda_raw):
            shabda_keys[kv[0]] = kv[1]
        before_slash = shabda_raw.split("/")[0]
        for token in re.split(r"[\s,]+", before_slash):
            token = token.strip()
            if token and ":" not in token:
                shabda_words.append(token)

    comments = []
    for line in source.split("\n"):
        stripped = line.strip()
        if stripped.startswith("--"):
            comments.append(stripped[2:].strip())

    return {
        "name": name,
        "layer": layer,
        "path": path,
        "domain": domain_of(path),
        "slokas": slokas,
        "edges": edges,
        "shabda_raw": shabda_raw,
        "shabda_keys": shabda_keys,
        "shabda_words": shabda_words,
        "comments": comments,
        "lines": len(source.split("\n")),
        "source": source,
    }


def load_all():
    """Load all om files, return OrderedDict keyed by name (domain/name on collision)."""
    oms = OrderedDict()
    seen_names = {}
    for path in find_all():
        parsed = parse(path)
        if not parsed:
            continue
        name = parsed["name"]
        if name in seen_names:
            if name in oms:
                first_parsed = oms.pop(name)
                oms[f"{first_parsed['domain']}/{name}"] = first_parsed
            oms[f"{parsed['domain']}/{name}"] = parsed
        else:
            seen_names[name] = path
            oms[name] = parsed
    return oms


def by_domain(oms, depth=2):
    groups = defaultdict(list)
    for om in oms.values():
        groups[domain_depth(om["domain"], depth)].append(om)
    return OrderedDict(sorted(groups.items()))


def by_layer(oms):
    groups = defaultdict(list)
    for om in oms.values():
        groups[om["layer"]].append(om)
    return dict(groups)


def domain_tree(oms):
    tree = defaultdict(int)
    for o in oms.values():
        tree[o["domain"]] += 1
    return OrderedDict(sorted(tree.items()))


def subdomains(oms, parent):
    """Immediate child domains under parent."""
    parent_norm = parent.rstrip("/")
    parent_depth = len(parent_norm.split(os.sep))
    children = {}
    direct_count = 0
    direct_lines = 0
    direct_names = []

    for o in oms.values():
        dom = o["domain"]
        if not dom.startswith(parent_norm):
            continue
        if dom == parent_norm:
            direct_count += 1
            direct_lines += o["lines"]
            direct_names.append(o["name"])
        else:
            parts = dom.split(os.sep)
            child_key = os.sep.join(parts[: parent_depth + 1])
            if child_key not in children:
                children[child_key] = {"count": 0, "lines": 0, "nodes": []}
            children[child_key]["count"] += 1
            children[child_key]["lines"] += o["lines"]
            if dom == child_key:
                children[child_key]["nodes"].append(o["name"])

    result = OrderedDict()
    if direct_count > 0:
        result[parent_norm] = {
            "count": direct_count,
            "lines": direct_lines,
            "nodes": sorted(direct_names),
        }
    for key in sorted(children.keys()):
        c = children[key]
        c["nodes"] = sorted(c["nodes"])
        result[key] = c
    return result


def domain_info(oms, domain_prefix):
    domain_prefix = domain_prefix.rstrip("/")
    direct_nodes = [o for o in oms.values() if o["domain"] == domain_prefix]
    all_under = [o for o in oms.values() if o["domain"].startswith(domain_prefix)]
    subs = subdomains(oms, domain_prefix)
    return {
        "domain": domain_prefix,
        "direct_count": len(direct_nodes),
        "total_count": len(all_under),
        "total_lines": sum(o["lines"] for o in all_under),
        "direct_nodes": sorted(o["name"] for o in direct_nodes),
        "subdomains": subs,
    }


def search(oms, pattern):
    regex = re.compile(pattern, re.IGNORECASE)
    results = []
    for om in oms.values():
        matches = []
        for i, line in enumerate(om["source"].split("\n"), 1):
            if regex.search(line):
                matches.append({"line": i, "text": line.rstrip()})
        if matches:
            results.append(
                {
                    "name": om["name"],
                    "layer": om["layer"],
                    "domain": om["domain"],
                    "path": om["path"],
                    "matches": matches,
                }
            )
    return results


def with_shabda_key(oms, key):
    return [om for om in oms.values() if key in om["shabda_keys"]]


def with_edge_relation(oms, relation):
    return [
        om for om in oms.values() if any(e["relation"] == relation for e in om["edges"])
    ]


def classify(oms, name, layer=None):
    """Classify a node by its edge affinities → suggest subdirectory grouping.

    Works for any layer (sangati, kosha, bhasha, mantra).
    Returns dict with edge targets by relation, affinity scores, and suggested subdir.
    """
    om = oms.get(name)
    if not om:
        return None

    if layer is None:
        layer = om["layer"]

    by_rel = defaultdict(list)
    for e in om["edges"]:
        by_rel[e["relation"]].append(e["target"])

    # Check sthalam membership (X-sthalam-sthita convention) — sangati only
    sthalams = [t for t in by_rel.get("sthita", []) if t.endswith("-sthalam")]

    # Build affinity: which existing subdirectories of this layer do our targets belong to?
    layer_nodes = {
        n: o for n, o in oms.items()
        if o["layer"] == layer
    }
    target_domains = defaultdict(int)
    for rel in ("swarupa", "abheda", "sthita", "janya", "phala", "kriya", "siddha"):
        for target in by_rel.get(rel, []):
            if target in layer_nodes:
                dom = layer_nodes[target]["domain"]
                parts = dom.split(os.sep)
                if len(parts) > 1 and parts[0] == layer:
                    subdir = parts[1]
                    weight = 3 if rel in ("swarupa", "abheda") else 1
                    target_domains[subdir] += weight

    suggested = None
    if sthalams:
        suggested = sthalams[0].replace("-sthalam", "")
    elif target_domains:
        suggested = max(target_domains, key=target_domains.get)

    return {
        "name": name,
        "layer": om["layer"],
        "domain": om["domain"],
        "swarupa": by_rel.get("swarupa", []),
        "abheda": by_rel.get("abheda", []),
        "sthita": by_rel.get("sthita", []),
        "janya": by_rel.get("janya", []),
        "phala": by_rel.get("phala", []),
        "kriya": by_rel.get("kriya", []),
        "siddha": by_rel.get("siddha", []),
        "pratipaksha": by_rel.get("pratipaksha", []),
        "sthalams": sthalams,
        "target_domains": dict(target_domains),
        "suggested": suggested,
    }


def ungrouped(oms, layer="sangati"):
    """Find all nodes of a layer that sit in the top-level directory (not in a subdirectory).

    Returns list of classify() results for each ungrouped node.
    """
    results = []
    for name, om in oms.items():
        if om["layer"] != layer:
            continue
        dom_parts = om["domain"].split(os.sep)
        if len(dom_parts) == 1:
            if name.endswith("-sthalam"):
                continue
            cl = classify(oms, name, layer=layer)
            if cl:
                results.append(cl)
    return results


def structure(oms, layer="sangati"):
    """Subdirectory-wise breakdown of a layer with node counts and affinity stats.

    Returns dict of subdir → {count, lines, nodes, affinity} where affinity
    shows how many edges point to nodes in other subdirs (cross-affinity).
    """
    # Collect all nodes in this layer
    layer_nodes = {n: o for n, o in oms.items() if o["layer"] == layer}

    # Group by subdirectory
    by_subdir = defaultdict(lambda: {"count": 0, "lines": 0, "nodes": [], "cross_affinity": defaultdict(int)})
    top_level = {"count": 0, "lines": 0, "nodes": [], "cross_affinity": defaultdict(int)}

    for name, om in layer_nodes.items():
        parts = om["domain"].split(os.sep)
        if len(parts) == 1:
            top_level["count"] += 1
            top_level["lines"] += om["lines"]
            top_level["nodes"].append(name)
        else:
            subdir = parts[1]
            by_subdir[subdir]["count"] += 1
            by_subdir[subdir]["lines"] += om["lines"]
            by_subdir[subdir]["nodes"].append(name)

    # Build cross-affinity: for each subdir, where do its nodes' edges point?
    all_subdirs = {}
    for name, om in layer_nodes.items():
        parts = om["domain"].split(os.sep)
        if len(parts) > 1:
            all_subdirs[name] = parts[1]

    for name, om in layer_nodes.items():
        parts = om["domain"].split(os.sep)
        src_subdir = parts[1] if len(parts) > 1 else None
        bucket = by_subdir[src_subdir] if src_subdir else top_level

        for e in om["edges"]:
            target = e["target"]
            if target in all_subdirs:
                tgt_subdir = all_subdirs[target]
                if tgt_subdir != src_subdir:
                    bucket["cross_affinity"][tgt_subdir] += 1

    # Convert defaultdicts
    result = OrderedDict()
    for subdir in sorted(by_subdir.keys()):
        entry = by_subdir[subdir]
        entry["nodes"] = sorted(entry["nodes"])
        entry["cross_affinity"] = dict(sorted(entry["cross_affinity"].items(), key=lambda x: -x[1]))
        result[subdir] = entry

    if top_level["count"] > 0:
        top_level["nodes"] = sorted(top_level["nodes"])
        top_level["cross_affinity"] = dict(sorted(top_level["cross_affinity"].items(), key=lambda x: -x[1]))
        result["(top-level)"] = top_level

    return {
        "layer": layer,
        "total_nodes": len(layer_nodes),
        "total_lines": sum(om["lines"] for om in layer_nodes.values()),
        "subdirs": result,
    }


def sthalam_members(oms, sthalam_name, layer="sangati"):
    """Find all nodes that should belong to a subdirectory based on edge affinity.

    Works for any layer. For sangati, also checks explicit sthalam-sthita edges.
    Returns nodes grouped by: current (already there), explicit (declared),
    strong (swarupa/abheda), and weak (other edges).
    """
    subdir = sthalam_name.replace("-sthalam", "")

    # Nodes already in this subdirectory
    current = []
    for name, om in oms.items():
        if om["layer"] == layer:
            parts = om["domain"].split(os.sep)
            if len(parts) > 1 and parts[1] == subdir:
                current.append(name)

    # Nodes with explicit sthalam-sthita (sangati convention)
    explicit = []
    if layer == "sangati":
        for name, om in oms.items():
            if om["layer"] != layer:
                continue
            for e in om["edges"]:
                if e["relation"] == "sthita" and e["target"] == f"{subdir}-sthalam":
                    if name not in current:
                        explicit.append(name)

    # Get all nodes in this subdir for affinity matching
    subdir_nodes = set(current)

    # Check ungrouped top-level nodes for affinity
    strong = []
    weak = []
    for name, om in oms.items():
        if om["layer"] != layer:
            continue
        if name in current or name in explicit:
            continue
        dom_parts = om["domain"].split(os.sep)
        if len(dom_parts) != 1:
            continue
        if name.endswith("-sthalam"):
            continue

        strong_score = 0
        weak_score = 0
        for e in om["edges"]:
            if e["target"] in subdir_nodes:
                if e["relation"] in ("swarupa", "abheda"):
                    strong_score += 3
                else:
                    weak_score += 1

        if strong_score >= 3:
            strong.append((name, strong_score))
        elif weak_score >= 2:
            weak.append((name, weak_score))

    strong.sort(key=lambda x: -x[1])
    weak.sort(key=lambda x: -x[1])

    return {
        "sthalam": sthalam_name,
        "subdir": subdir,
        "current": sorted(current),
        "explicit": sorted(explicit),
        "strong": strong,
        "weak": weak,
    }


def to_json_summary(oms):
    layers = defaultdict(int)
    for om in oms.values():
        layers[om["layer"]] += 1
    return {
        "total": len(oms),
        "total_lines": sum(om["lines"] for om in oms.values()),
        "layers": dict(layers),
        "domains": dict(domain_tree(oms)),
    }


def to_json_domain(oms, domain_prefix):
    result = {}
    for om in oms.values():
        if om["domain"].startswith(domain_prefix):
            result[om["name"]] = {
                "layer": om["layer"],
                "domain": om["domain"],
                "path": om["path"],
                "lines": om["lines"],
                "slokas": om["slokas"],
                "edges": om["edges"],
                "shabda_keys": om["shabda_keys"],
                "shabda_words": om["shabda_words"],
                "comments": om["comments"],
                "source": om["source"],
            }
    return result


def to_json_node(om):
    return {
        "name": om["name"],
        "layer": om["layer"],
        "domain": om["domain"],
        "path": om["path"],
        "lines": om["lines"],
        "slokas": om["slokas"],
        "edges": om["edges"],
        "shabda_raw": om["shabda_raw"],
        "shabda_keys": om["shabda_keys"],
        "shabda_words": om["shabda_words"],
        "comments": om["comments"],
        "source": om["source"],
    }
