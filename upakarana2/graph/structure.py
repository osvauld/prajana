"""structure.py — Edge walks, swarupa chains, ring axioms, layer flow.

Consolidates: edges.py + chains.py + ring.py + layers.py
"""

from collections import defaultdict, deque
from upakarana2.parsers import om5


# ---------------------------------------------------------------------------
# Reverse index
# ---------------------------------------------------------------------------

def build_reverse_index(root=None):
    """Build {target: [(source, relation)]} for all edges."""
    nodes = om5.load_all(root)
    rev = defaultdict(list)
    for name, node in nodes.items():
        for e in node["edges"]:
            rev[e["target"]].append((name, e["relation"]))
    return dict(rev), nodes


def incoming(name, root=None):
    """All edges pointing TO a node."""
    rev, nodes = build_reverse_index(root)
    edges = rev.get(name, [])
    return [
        {"source": src, "relation": rel,
         "source_layer": nodes.get(src, {}).get("layer", "?")}
        for src, rel in edges
    ]


def hub_nodes(root=None, top_n=20):
    """Nodes with most incoming edges."""
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
    """Nodes with zero incoming edges."""
    rev, nodes = build_reverse_index(root)
    orphans = []
    for name, node in nodes.items():
        if name not in rev or not rev[name]:
            if exclude_bhasha and node.get("layer") == "bhasha":
                continue
            orphans.append({"name": name, "layer": node.get("layer", "?"),
                            "domain": node.get("domain", "?")})
    orphans.sort(key=lambda n: (n["layer"], n["name"]))
    return orphans


# ---------------------------------------------------------------------------
# Swarupa chains + connected components
# ---------------------------------------------------------------------------

def swarupa_chains(root=None, max_depth=20):
    """Walk swarupa (IS-A) chains to their roots."""
    nodes = om5.load_all(root)

    swarupa = {}
    for name, node in nodes.items():
        targets = [e["target"] for e in node["edges"] if e["relation"] == "swarupa"]
        if targets:
            swarupa[name] = targets

    chains = {}
    for name in nodes:
        chain = [name]
        visited = {name}
        current = name
        for _ in range(max_depth):
            targets = swarupa.get(current, [])
            if not targets:
                break
            nxt = targets[0]
            if nxt in visited:
                chain.append(f"{nxt} (cycle)")
                break
            chain.append(nxt)
            visited.add(nxt)
            current = nxt
        chains[name] = chain

    roots = defaultdict(int)
    for chain in chains.values():
        r = chain[-1]
        if "(cycle)" not in r:
            roots[r] += 1

    depths = defaultdict(int)
    for chain in chains.values():
        depths[len(chain) - 1] += 1

    return {
        "roots": sorted(roots.items(), key=lambda x: -x[1]),
        "depth_histogram": dict(sorted(depths.items())),
        "no_swarupa": [n for n, node in nodes.items()
                       if not any(e["relation"] == "swarupa" for e in node["edges"])],
    }


def connected_components(root=None, layer=None):
    """Find connected components (edges treated as undirected)."""
    nodes = om5.load_all(root)
    if layer:
        nodes = {n: v for n, v in nodes.items() if v["layer"] == layer}

    names = set(nodes.keys())
    adj = defaultdict(set)
    for name, node in nodes.items():
        for e in node["edges"]:
            t = e["target"]
            if t in names:
                adj[name].add(t)
                adj[t].add(name)

    visited = set()
    components = []
    for name in names:
        if name in visited:
            continue
        component = []
        queue = deque([name])
        while queue:
            n = queue.popleft()
            if n in visited:
                continue
            visited.add(n)
            component.append(n)
            for neighbor in adj.get(n, []):
                if neighbor not in visited:
                    queue.append(neighbor)
        components.append(sorted(component))

    components.sort(key=lambda c: -len(c))
    return {
        "total_components": len(components),
        "main_size": len(components[0]) if components else 0,
        "islands": [{"size": len(c), "members": c[:10]} for c in components[1:]],
        "components": components,
    }


# ---------------------------------------------------------------------------
# Ring axioms (pratipaksha + abheda)
# ---------------------------------------------------------------------------

def pratipaksha_check(root=None):
    """Check pratipaksha involution axiom (must be symmetric)."""
    nodes = om5.load_all(root)

    forward = {}
    for name, node in nodes.items():
        for e in node["edges"]:
            if e["relation"] == "pratipaksha":
                forward[name] = e["target"]

    symmetric = []
    broken = []
    for a, b in forward.items():
        if forward.get(b) == a:
            if a < b:
                symmetric.append((a, b))
        else:
            broken.append({
                "from": a, "to": b,
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
    """Summarize abheda (non-difference) declarations by layer flow."""
    nodes = om5.load_all(root)

    forward = defaultdict(set)
    for name, node in nodes.items():
        for e in node["edges"]:
            if e["relation"] == "abheda":
                forward[name].add(e["target"])

    layer_flow = defaultdict(int)
    for a, targets in forward.items():
        a_layer = nodes[a]["layer"] if a in nodes else "?"
        for b in targets:
            b_layer = nodes[b]["layer"] if b in nodes else "ghost"
            layer_flow[(a_layer, b_layer)] += 1

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
    """Count usage of each relation type across the graph."""
    nodes = om5.load_all(root)
    total = len(nodes)

    rel_count = defaultdict(int)
    rel_users = defaultdict(set)

    for name, node in nodes.items():
        for e in node["edges"]:
            rel = e["relation"]
            rel_count[rel] += 1
            rel_users[rel].add(name)

    return {
        rel: {
            "count": rel_count[rel],
            "nodes": len(rel_users[rel]),
            "pct": round(len(rel_users[rel]) / total * 100) if total else 0,
        }
        for rel in sorted(rel_count, key=lambda r: -rel_count[r])
    }


# ---------------------------------------------------------------------------
# Layer flow + fingerprint
# ---------------------------------------------------------------------------

def edge_flow(root=None):
    """Count edges flowing between layers."""
    nodes = om5.load_all(root)
    names = set(nodes.keys())

    flow = defaultdict(int)
    nowhere = defaultdict(int)

    for name, node in nodes.items():
        src_layer = node["layer"]
        for e in node["edges"]:
            t = e["target"]
            if t in names:
                flow[(src_layer, nodes[t]["layer"])] += 1
            else:
                nowhere[src_layer] += 1

    layers = sorted(set(l for pair in flow for l in pair))
    matrix = {}
    for src in layers:
        row = {tgt: flow.get((src, tgt), 0) for tgt in layers}
        row["nowhere"] = nowhere.get(src, 0)
        matrix[src] = row

    return {"matrix": matrix, "layers": layers}


def relation_fingerprint(root=None):
    """Per-layer relation usage percentages."""
    nodes = om5.load_all(root)

    layer_nodes = defaultdict(list)
    for name, node in nodes.items():
        layer_nodes[node["layer"]].append(node)

    result = {}
    for layer, lnodes in sorted(layer_nodes.items()):
        total = len(lnodes)
        if not total:
            continue
        rel_users = defaultdict(set)
        rel_count = defaultdict(int)
        for node in lnodes:
            for e in node["edges"]:
                rel = e["relation"]
                rel_users[rel].add(node["name"])
                rel_count[rel] += 1

        result[layer] = {
            "total_nodes": total,
            "relations": {
                rel: {
                    "count": rel_count[rel],
                    "nodes": len(rel_users[rel]),
                    "pct": round(len(rel_users[rel]) / total * 100),
                }
                for rel in sorted(rel_count, key=lambda r: -rel_count[r])
            },
        }

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
    return {k: {"nodes": v["nodes"], "edges": v["edges"], "domains": len(v["domains"])}
            for k, v in sorted(layers.items())}
