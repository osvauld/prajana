"""chains.py — Swarupa chain walks and connected components.

Traces IS-A hierarchy to roots. Finds disconnected subgraphs.
"""

from collections import defaultdict, deque
from upakarana.parsers import om5


def swarupa_chains(root=None, max_depth=20):
    """Walk swarupa (IS-A) chains to their roots.

    Returns:
      roots: list of root names (no outgoing swarupa)
      chains: {node: [chain to root]}
      depth_histogram: {depth: count}
    """
    nodes = om5.load_all(root)

    # Build swarupa graph: node → swarupa targets
    swarupa = {}
    for name, node in nodes.items():
        targets = [e["target"] for e in node["edges"] if e["relation"] == "swarupa"]
        if targets:
            swarupa[name] = targets

    # Walk each node to root
    chains = {}
    for name in nodes:
        chain = [name]
        visited = {name}
        current = name
        for _ in range(max_depth):
            targets = swarupa.get(current, [])
            if not targets:
                break
            nxt = targets[0]  # follow first swarupa
            if nxt in visited:
                chain.append(f"{nxt} (cycle)")
                break
            chain.append(nxt)
            visited.add(nxt)
            current = nxt
        chains[name] = chain

    # Find roots (end of chains)
    roots = defaultdict(int)
    for chain in chains.values():
        root = chain[-1]
        if "(cycle)" not in root:
            roots[root] += 1

    # Depth histogram
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
    """Find connected components in the graph (treating edges as undirected).

    If layer is specified, only consider nodes in that layer.
    """
    nodes = om5.load_all(root)
    if layer:
        nodes = {n: v for n, v in nodes.items() if v["layer"] == layer}

    names = set(nodes.keys())

    # Build undirected adjacency
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
        # BFS
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
        "islands": [{"size": len(c), "members": c[:10]}
                    for c in components[1:]],
        "components": components,
    }
