"""walk.py — Graph traversals: walk, walk_in, chain, ancestors, descendants."""

from pathram2.types import Edge


def walk(store, node: str, relation: str) -> list[str]:
    """Outgoing targets along a relation."""
    targets = []
    for ek_key in store.scan("idx_edges_out", f"{node}:"):
        ek = ek_key.split(":", 1)[1]
        d = store.get("edges", ek)
        if d and d["relation"] == relation:
            targets.append(d["target"])
    return targets


def walk_in(store, node: str, relation: str) -> list[str]:
    """Incoming sources along a relation."""
    sources = []
    for ek_key in store.scan("idx_edges_in", f"{node}:"):
        ek = ek_key.split(":", 1)[1]
        d = store.get("edges", ek)
        if d and d["relation"] == relation:
            sources.append(d["source"])
    return sources


def chain(store, node: str, relation: str, max_depth: int = 100) -> list[str]:
    """Follow a relation forward to its end. Returns ordered list of nodes.

    Useful for walking krama (step sequence) or sthita (hierarchy up).
    """
    result = []
    current = node
    visited = {current}
    for _ in range(max_depth):
        targets = walk(store, current, relation)
        if not targets:
            break
        nxt = targets[0]  # follow first edge
        if nxt in visited:
            break
        visited.add(nxt)
        result.append(nxt)
        current = nxt
    return result


def ancestors(store, node: str, relation: str = "sthita",
              max_depth: int = 50) -> list[str]:
    """Walk UP the hierarchy (follow relation forward from child to parent).

    sthita edges go child → parent, so this follows the forward direction.
    """
    return chain(store, node, relation, max_depth)


def descendants(store, node: str, relation: str = "sthita",
                max_depth: int = 50) -> list[str]:
    """Walk DOWN the hierarchy (find all nodes that point to this via relation).

    Uses BFS on incoming edges.
    """
    result = []
    queue = [node]
    visited = {node}
    depth = 0
    while queue and depth < max_depth:
        depth += 1
        next_queue = []
        for current in queue:
            children = walk_in(store, current, relation)
            for child in children:
                if child not in visited:
                    visited.add(child)
                    result.append(child)
                    next_queue.append(child)
        queue = next_queue
    return result


def neighbors(store, node: str) -> list[str]:
    """All connected nodes (any direction, any relation)."""
    nbrs = set()
    for ek_key in store.scan("idx_edges_out", f"{node}:"):
        ek = ek_key.split(":", 1)[1]
        d = store.get("edges", ek)
        if d:
            nbrs.add(d["target"])
    for ek_key in store.scan("idx_edges_in", f"{node}:"):
        ek = ek_key.split(":", 1)[1]
        d = store.get("edges", ek)
        if d:
            nbrs.add(d["source"])
    return list(nbrs)
