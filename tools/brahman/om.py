"""
om.py — parse, group, and query all .om files.

No server needed. Reads .om source directly from disk.
The folder structure IS the domain taxonomy — we use it as-is.

Layers:
  kosha    — domain knowledge (physics, math, etc.)
  sangati  — universal structural truth (pure concepts)
  bhasha   — linguistic surface (word forms, grammar)
  mantra   — formula/computation nodes
"""

import glob
import os
import re
from collections import defaultdict, OrderedDict

from .paths import BRAHMAN

# ── relation suffixes (the philosophical grammar) ──────────────────────────────

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


# ── discovery ──────────────────────────────────────────────────────────────────


def find_all():
    """Find all .om files under brahman/, return sorted list."""
    return sorted(glob.glob(os.path.join(BRAHMAN, "**", "*.om"), recursive=True))


def domain_of(path):
    """Extract domain path from file path relative to brahman/.

    e.g. kosha/math/number/operations/addition.om -> kosha/math/number/operations
    """
    rel = os.path.relpath(path, BRAHMAN)
    return os.path.dirname(rel)


def domain_depth(domain, n=1):
    """Truncate domain path to n levels.

    e.g. domain_depth("kosha/math/number/operations", 2) -> "kosha/math"
    """
    parts = domain.split(os.sep)
    return os.sep.join(parts[:n])


# ── parsing ────────────────────────────────────────────────────────────────────


def parse(path):
    """Parse one .om file into a structured dict."""
    try:
        source = open(path).read()
    except Exception:
        return None

    # header: layer + name
    header = _HEADER_RE.search(source)
    if not header:
        return None

    layer = header.group(1)
    name = header.group(2)

    # slokas: quoted strings
    slokas = _SLOKA_RE.findall(source)

    # decompose slokas into edges (suffix -> target)
    edges = []
    for sloka in slokas:
        for m in _SLOKA_SUFFIX_RE.finditer(sloka):
            edges.append(
                {
                    "target": m.group(1),
                    "relation": m.group(2),
                }
            )

    # shabda: key:value pairs and word aliases
    shabda_raw = ""
    shabda_keys = {}
    shabda_words = []
    for m in _SHABDA_RE.finditer(source):
        shabda_raw = m.group(1).strip()
        # parse key:value pairs
        for kv in re.findall(r"([a-z][a-z0-9_-]*):([^\s,/]+)", shabda_raw):
            shabda_keys[kv[0]] = kv[1]
        # parse bare words (not key:value, not after /)
        # split on whitespace, comma, then filter
        before_slash = shabda_raw.split("/")[0]
        for token in re.split(r"[\s,]+", before_slash):
            token = token.strip()
            if token and ":" not in token:
                shabda_words.append(token)

    # comments
    comments = []
    for line in source.split("\n"):
        stripped = line.strip()
        if stripped.startswith("--"):
            comments.append(stripped[2:].strip())

    lines = source.split("\n")

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
        "lines": len(lines),
        "source": source,
    }


# ── loading ────────────────────────────────────────────────────────────────────


def load_all():
    """Load and parse all om files, return OrderedDict keyed by name.

    On name collision (different domains, same node name), key by
    domain/name to keep both.
    """
    oms = OrderedDict()
    seen_names = {}  # name -> first path
    for path in find_all():
        parsed = parse(path)
        if not parsed:
            continue
        name = parsed["name"]
        if name in seen_names:
            # collision: re-key both by domain/name
            first_path = seen_names[name]
            if name in oms:
                first_parsed = oms.pop(name)
                key1 = f"{first_parsed['domain']}/{name}"
                oms[key1] = first_parsed
            key = f"{parsed['domain']}/{name}"
            oms[key] = parsed
        else:
            seen_names[name] = path
            oms[name] = parsed
    return oms


# ── grouping ───────────────────────────────────────────────────────────────────


def by_domain(oms, depth=2):
    """Group om nodes by domain path truncated to depth levels.

    depth=1: kosha, sangati, bhasha
    depth=2: kosha/math, kosha/physics, sangati/jiva, bhasha/english, ...
    depth=3: kosha/math/number, kosha/physics/kinematics, ...
    """
    groups = defaultdict(list)
    for om in oms.values():
        key = domain_depth(om["domain"], depth)
        groups[key].append(om)
    # sort by key
    return OrderedDict(sorted(groups.items()))


def by_layer(oms):
    """Group by layer: kosha, sangati, bhasha, mantra."""
    groups = defaultdict(list)
    for om in oms.values():
        groups[om["layer"]].append(om)
    return dict(groups)


def domain_tree(oms):
    """Build a flat tree of domain -> count for overview."""
    tree = defaultdict(int)
    for o in oms.values():
        tree[o["domain"]] += 1
    return OrderedDict(sorted(tree.items()))


def subdomains(oms, parent):
    """Return immediate child domains under parent.

    e.g. subdomains(oms, "kosha/math") ->
         {"kosha/math/algebra": 15, "kosha/math/number": 42, ...}

    Only returns direct children (one level deeper), not grandchildren.
    Also includes nodes directly in the parent domain itself.
    """
    parent_norm = parent.rstrip("/")
    parent_depth = len(parent_norm.split(os.sep))

    children = {}  # child_key -> {count, lines, nodes}
    direct_count = 0
    direct_lines = 0
    direct_names = []

    for o in oms.values():
        dom = o["domain"]
        if not dom.startswith(parent_norm):
            continue
        if dom == parent_norm:
            # node directly in this domain
            direct_count += 1
            direct_lines += o["lines"]
            direct_names.append(o["name"])
        else:
            # child domain — truncate to one level deeper
            parts = dom.split(os.sep)
            child_key = os.sep.join(parts[: parent_depth + 1])
            if child_key not in children:
                children[child_key] = {"count": 0, "lines": 0, "nodes": []}
            children[child_key]["count"] += 1
            children[child_key]["lines"] += o["lines"]
            # only list names for direct children, not grandchildren
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
    """Full info for a domain: direct nodes + subdomains + total counts."""
    domain_prefix = domain_prefix.rstrip("/")

    # direct nodes in this exact domain
    direct_nodes = [o for o in oms.values() if o["domain"] == domain_prefix]

    # all nodes under this prefix (including subdomain descendants)
    all_under = [o for o in oms.values() if o["domain"].startswith(domain_prefix)]

    # subdomains
    subs = subdomains(oms, domain_prefix)

    return {
        "domain": domain_prefix,
        "direct_count": len(direct_nodes),
        "total_count": len(all_under),
        "total_lines": sum(o["lines"] for o in all_under),
        "direct_nodes": sorted(o["name"] for o in direct_nodes),
        "subdomains": subs,
    }


# ── query helpers ──────────────────────────────────────────────────────────────


def search(oms, pattern):
    """Search all om source for a regex."""
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
    """Find all om nodes that have a particular shabda key (e.g. 'eval', 'math-op')."""
    return [om for om in oms.values() if key in om["shabda_keys"]]


def with_edge_relation(oms, relation):
    """Find all om nodes that have edges with a particular relation suffix."""
    return [
        om for om in oms.values() if any(e["relation"] == relation for e in om["edges"])
    ]


# ── JSON serialization ─────────────────────────────────────────────────────────


def to_json_summary(oms):
    """Summary without source."""
    layers = defaultdict(int)
    for om in oms.values():
        layers[om["layer"]] += 1

    domains = domain_tree(oms)

    result = {
        "total": len(oms),
        "total_lines": sum(om["lines"] for om in oms.values()),
        "layers": dict(layers),
        "domains": dict(domains),
    }
    return result


def to_json_domain(oms, domain_prefix):
    """All om nodes under a domain prefix, with source."""
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
    """Full JSON for a single om node."""
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
