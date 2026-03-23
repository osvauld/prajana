"""graph.py — Live graph analysis using the engine client.

Edge density, hubs, components, coverage analysis.
"""

from collections import defaultdict


def edge_density(client):
    """Count edges by relation type in the live graph."""
    # Use eval to get graph stats
    try:
        result = client.eval('graph-stats')
        return result
    except Exception:
        pass

    # Fallback: sample known relation types
    relations = ["swarupa", "abheda", "sthita", "yukta", "kriya",
                 "phala", "janya", "siddha", "pratipaksha", "drishthanta",
                 "varga", "krama"]
    counts = {}
    for rel in relations:
        try:
            nodes = client.eval(f'walk-in "*" "{rel}"')
            if isinstance(nodes, list):
                counts[rel] = len(nodes)
        except Exception:
            pass
    return counts


def hub_nodes(client, top_n=20):
    """Find highest-degree nodes in the live graph."""
    # Get all tantras and sample key nodes
    try:
        tantras = client.list_tantras()
    except Exception:
        tantras = []

    hubs = []
    # Sample some well-known hub candidates
    candidates = ["force", "mass", "velocity", "energy", "acceleration",
                   "monoid", "group", "ring", "field-varga"]
    for name in candidates:
        try:
            node = client.inspect(name)
            out_count = len(node.get("out_edges", []))
            in_count = len(node.get("in_edges", []))
            hubs.append({
                "name": name,
                "out_edges": out_count,
                "in_edges": in_count,
                "total": out_count + in_count,
            })
        except Exception:
            pass

    hubs.sort(key=lambda h: -h["total"])
    return hubs[:top_n]


def orphan_nodes(client, sample_names):
    """Find nodes with zero incoming edges from a list of names."""
    orphans = []
    for name in sample_names:
        try:
            node = client.inspect(name)
            if not node.get("in_edges"):
                orphans.append({
                    "name": name,
                    "out_edges": len(node.get("out_edges", [])),
                })
        except Exception:
            pass
    return orphans


def tantra_coverage(client):
    """Which tantras are loaded and callable."""
    try:
        tantras = client.list_tantras()
        return {
            "total": len(tantras),
            "tantras": sorted(tantras),
        }
    except Exception:
        return {"total": 0, "tantras": []}


def node_detail(client, name):
    """Full detail of a node: edges, shabda, walks."""
    try:
        info = client.inspect(name)
        triples = client.triples_of(name)
        return {
            "inspect": info,
            "triples": triples,
            "triple_count": len(triples),
        }
    except Exception as e:
        return {"error": str(e)}
