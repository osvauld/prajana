"""edges.py — Incoming/outgoing edge analysis, reverse lookups.

The om5 parser gives outgoing edges per node. This module builds
the reverse index: who points TO a given node.
"""

from collections import defaultdict
from upakarana.parsers import om5


def build_reverse_index(root=None):
    """Build {target: [(source, relation)]} for all edges."""
    nodes = om5.load_all(root)
    rev = defaultdict(list)
    for name, node in nodes.items():
        for e in node["edges"]:
            rev[e["target"]].append((name, e["relation"]))
    return dict(rev), nodes


def incoming(name, root=None):
    """All edges pointing TO a node.

    Returns list of {source, relation, source_layer}.
    """
    rev, nodes = build_reverse_index(root)
    edges = rev.get(name, [])
    result = []
    for src, rel in edges:
        src_node = nodes.get(src, {})
        result.append({
            "source": src,
            "relation": rel,
            "source_layer": src_node.get("layer", "?"),
        })
    return result


def hub_nodes(root=None, top_n=20):
    """Nodes with most incoming edges (gravitational centers)."""
    rev, nodes = build_reverse_index(root)
    hubs = []
    for name, edges in rev.items():
        by_rel = defaultdict(int)
        for _, rel in edges:
            by_rel[rel] += 1
        hubs.append({
            "name": name,
            "in_count": len(edges),
            "in_graph": name in nodes,
            "top_relations": sorted(by_rel.items(), key=lambda x: -x[1])[:5],
        })
    hubs.sort(key=lambda h: -h["in_count"])
    return hubs[:top_n]


def orphan_nodes(root=None, exclude_bhasha=True):
    """Nodes with zero incoming edges (nobody references them).

    Bhasha leaf nodes are excluded by default — they're consumed via
    shabda word: lookup, not graph edges. Being unreferenced is normal
    for grammar terminals (articles, copulas, prepositions).
    """
    rev, nodes = build_reverse_index(root)
    orphans = []
    for name, node in nodes.items():
        if name not in rev:
            if exclude_bhasha and node["layer"] == "bhasha":
                continue
            orphans.append({
                "name": name,
                "layer": node["layer"],
                "domain": node["domain"],
                "out_edges": len(node["edges"]),
            })
    return orphans
