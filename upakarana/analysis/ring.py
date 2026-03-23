"""ring.py — Visheshanam ring axiom verification.

Pratipaksha (inverse) MUST be symmetric — if A is the inverse of B,
then B is the inverse of A. This is the involution axiom.

Abheda (non-difference) is NOT required to be symmetric — it's a
declaration by the speaker. "entropy IS kshaya" is kosha grounding
itself in sangati. Sangati doesn't need to say it back.

So: pratipaksha asymmetry = real bug. Abheda asymmetry = normal.
"""

from collections import defaultdict
from upakarana.parsers import om5


def pratipaksha_check(root=None):
    """Check pratipaksha (inverse) involution axiom.

    Pratipaksha MUST be symmetric: if A.pratipaksha = B then B.pratipaksha = A.
    This is algebraically required — inverse of inverse = self.

    Returns:
      symmetric: pairs where both directions exist (correct)
      broken: pairs where only one direction exists (BUG — needs fixing)
    """
    nodes = om5.load_all(root)

    # Collect all pratipaksha edges
    forward = {}
    for name, node in nodes.items():
        for e in node["edges"]:
            if e["relation"] == "pratipaksha":
                forward[name] = e["target"]

    symmetric = []
    broken = []
    for a, b in forward.items():
        if forward.get(b) == a:
            if a < b:  # avoid duplicates
                symmetric.append((a, b))
        else:
            # This is a real issue — pratipaksha must be involutory
            broken.append({
                "from": a,
                "to": b,
                "reverse": forward.get(b, None),
                "target_exists": b in nodes,
            })

    return {
        "symmetric": symmetric,
        "broken": broken,
        "total_edges": len(forward),
        "health": f"{len(symmetric)} ok, {len(broken)} broken",
    }


def abheda_summary(root=None):
    """Summarize abheda (non-difference) declarations.

    Abheda is directional by nature — A declares non-difference with B.
    One-way is normal. Mutual is redundant (both sides independently declared).

    Groups by pattern: which layers declare abheda to which.
    """
    nodes = om5.load_all(root)

    forward = defaultdict(set)
    for name, node in nodes.items():
        for e in node["edges"]:
            if e["relation"] == "abheda":
                forward[name].add(e["target"])

    # Cross-layer flow of abheda
    layer_flow = defaultdict(int)
    for a, targets in forward.items():
        a_layer = nodes[a]["layer"] if a in nodes else "?"
        for b in targets:
            b_layer = nodes[b]["layer"] if b in nodes else "ghost"
            layer_flow[(a_layer, b_layer)] += 1

    # Top targets (most incoming abheda)
    incoming = defaultdict(list)
    for a, targets in forward.items():
        for b in targets:
            incoming[b].append(a)

    top_targets = sorted(incoming.items(), key=lambda x: -len(x[1]))[:20]

    return {
        "total_edges": sum(len(v) for v in forward.values()),
        "declaring_nodes": len(forward),
        "layer_flow": dict(layer_flow),
        "top_targets": [(t, len(srcs)) for t, srcs in top_targets],
    }


def relation_usage(root=None):
    """Count usage of each relation type across the graph.

    Returns {relation: {count, nodes, pct}}.
    """
    nodes = om5.load_all(root)
    total = len(nodes)

    rel_count = defaultdict(int)
    rel_users = defaultdict(set)

    for name, node in nodes.items():
        for e in node["edges"]:
            rel = e["relation"]
            rel_count[rel] += 1
            rel_users[rel].add(name)

    result = {}
    for rel in sorted(rel_count, key=lambda r: -rel_count[r]):
        result[rel] = {
            "count": rel_count[rel],
            "nodes": len(rel_users[rel]),
            "pct": round(len(rel_users[rel]) / total * 100) if total else 0,
        }
    return result
