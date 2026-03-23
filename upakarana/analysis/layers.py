"""layers.py — Cross-layer edge flow and relation fingerprints.

Answers: how do layers talk to each other? What relation types
does each layer emphasize?
"""

from collections import defaultdict
from upakarana.parsers import om5


def edge_flow(root=None):
    """Count edges flowing between layers.

    Returns {(from_layer, to_layer): count} and per-layer totals.
    """
    nodes = om5.load_all(root)
    names = set(nodes.keys())

    flow = defaultdict(int)
    nowhere = defaultdict(int)

    for name, node in nodes.items():
        src_layer = node["layer"]
        for e in node["edges"]:
            t = e["target"]
            if t in names:
                tgt_layer = nodes[t]["layer"]
                flow[(src_layer, tgt_layer)] += 1
            else:
                nowhere[src_layer] += 1

    # Build matrix
    layers = sorted(set(l for pair in flow for l in pair))
    matrix = {}
    for src in layers:
        row = {}
        for tgt in layers:
            row[tgt] = flow.get((src, tgt), 0)
        row["nowhere"] = nowhere.get(src, 0)
        matrix[src] = row

    return {"matrix": matrix, "layers": layers}


def relation_fingerprint(root=None):
    """Per-layer relation usage percentages.

    Returns {layer: {relation: {count, pct_nodes}}}
    """
    nodes = om5.load_all(root)

    layer_nodes = defaultdict(list)
    for name, node in nodes.items():
        layer_nodes[node["layer"]].append(node)

    result = {}
    for layer, lnodes in sorted(layer_nodes.items()):
        total = len(lnodes)
        if total == 0:
            continue
        rel_users = defaultdict(set)
        rel_count = defaultdict(int)
        for node in lnodes:
            for e in node["edges"]:
                rel = e["relation"]
                rel_users[rel].add(node["name"])
                rel_count[rel] += 1

        fingerprint = {}
        for rel in sorted(rel_count, key=lambda r: -rel_count[r]):
            fingerprint[rel] = {
                "count": rel_count[rel],
                "nodes": len(rel_users[rel]),
                "pct": round(len(rel_users[rel]) / total * 100),
            }
        result[layer] = {"total_nodes": total, "relations": fingerprint}

    return result


def layer_summary(root=None):
    """Quick summary: nodes, edges, domains per layer."""
    nodes = om5.load_all(root)
    layers = defaultdict(lambda: {"nodes": 0, "edges": 0, "domains": set()})
    for name, node in nodes.items():
        l = layers[node["layer"]]
        l["nodes"] += 1
        l["edges"] += len(node["edges"])
        l["domains"].add(node["domain"])
    return {k: {"nodes": v["nodes"], "edges": v["edges"],
                "domains": len(v["domains"])}
            for k, v in sorted(layers.items())}
