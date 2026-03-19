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
}

_SLOKA_SUFFIX_RE = re.compile(
    r"\b([a-z][a-z0-9-]*?)-(swarupa|yukta|sthita|kriya|phala|janya|abheda|siddha|vishesa|varga|pratipaksha)\b"
)
_SHABDA_RE = re.compile(r"^\s*shabda\s+(.+)", re.MULTILINE)
_HEADER_RE = re.compile(r"^(sangati|kosha|bhasha|mantra)\s+([a-z][a-z0-9-]*)")
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
