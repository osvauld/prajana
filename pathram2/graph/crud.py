"""crud.py — Node and Edge create/read/update/delete with index maintenance."""

from pathram2.types import Node, Edge, _now


def _make_id(store, type: str, id: str | None) -> str:
    """Generate a unique ID if none provided."""
    if id:
        return id
    # Auto-generate: type-N where N is next available
    existing = store.scan("idx_type", f"{type}:")
    n = len(existing) + 1
    candidate = f"{type}-{n}"
    while store.exists("nodes", candidate):
        n += 1
        candidate = f"{type}-{n}"
    return candidate


def _index_node(store, node: Node):
    """Add a node to all indexes."""
    store.put("idx_type", f"{node.type}:{node.id}")
    store.put("idx_tag", f"{node.tag}:{node.id}")
    store.put("idx_time", f"{node.created_at}:{node.id}")


def _deindex_node(store, node: Node):
    """Remove a node from all indexes."""
    store.delete("idx_type", f"{node.type}:{node.id}")
    store.delete("idx_tag", f"{node.tag}:{node.id}")
    store.delete("idx_time", f"{node.created_at}:{node.id}")


def _index_edge(store, edge: Edge):
    """Add an edge to all indexes."""
    ek = edge.key
    store.put("idx_edges_out", f"{edge.source}:{ek}")
    store.put("idx_edges_in", f"{edge.target}:{ek}")
    store.put("idx_edges_rel", f"{edge.relation}:{ek}")


def _deindex_edge(store, edge: Edge):
    """Remove an edge from all indexes."""
    ek = edge.key
    store.delete("idx_edges_out", f"{edge.source}:{ek}")
    store.delete("idx_edges_in", f"{edge.target}:{ek}")
    store.delete("idx_edges_rel", f"{edge.relation}:{ek}")


# --- Node CRUD ---

def add_node(store, type: str, title: str, body: str = "", tag: str = "active",
             shabda: dict | None = None, id: str | None = None) -> Node:
    """Create a new node and index it."""
    node_id = _make_id(store, type, id)
    if store.exists("nodes", node_id):
        raise ValueError(f"Node already exists: {node_id}")

    node = Node(
        id=node_id,
        type=type,
        title=title,
        body=body,
        tag=tag,
        shabda=shabda or {},
    )
    store.put("nodes", node_id, node.to_dict())
    _index_node(store, node)
    return node


def get_node(store, id: str) -> Node | None:
    """Retrieve a node by ID."""
    d = store.get("nodes", id)
    if d is None:
        return None
    return Node.from_dict(d)


def update_node(store, id: str, **fields) -> Node:
    """Update specific fields on a node."""
    node = get_node(store, id)
    if node is None:
        raise KeyError(f"Node not found: {id}")

    _deindex_node(store, node)

    for k, v in fields.items():
        if k == "shabda" and isinstance(v, dict):
            node.shabda.update(v)
        elif hasattr(node, k):
            setattr(node, k, v)
    node.updated_at = _now()

    store.put("nodes", id, node.to_dict())
    _index_node(store, node)
    return node


def delete_node(store, id: str):
    """Delete a node and all edges touching it."""
    node = get_node(store, id)
    if node is None:
        return

    # Remove all edges touching this node
    for edge in _edges_touching(store, id):
        _deindex_edge(store, edge)
        store.delete("edges", edge.key)

    _deindex_node(store, node)
    store.delete("nodes", id)


def all_nodes(store) -> list[Node]:
    """Return all nodes."""
    return [Node.from_dict(d) for d in store.scan_values("nodes")]


# --- Edge CRUD ---

def link(store, source: str, target: str, relation: str,
         shabda: dict | None = None) -> Edge:
    """Create an edge between two nodes."""
    edge = Edge(
        source=source,
        target=target,
        relation=relation,
        shabda=shabda or {},
    )
    store.put("edges", edge.key, edge.to_dict())
    _index_edge(store, edge)
    return edge


def unlink(store, source: str, target: str, relation: str | None = None):
    """Remove edge(s) between two nodes. If relation is None, removes all."""
    if relation:
        ek = f"{source}|{relation}|{target}"
        d = store.get("edges", ek)
        if d:
            edge = Edge.from_dict(d)
            _deindex_edge(store, edge)
            store.delete("edges", ek)
    else:
        # Remove all edges between source and target
        for edge in _edges_between(store, source, target):
            _deindex_edge(store, edge)
            store.delete("edges", edge.key)


def get_edge(store, source: str, target: str, relation: str) -> Edge | None:
    """Get a specific edge."""
    ek = f"{source}|{relation}|{target}"
    d = store.get("edges", ek)
    if d is None:
        return None
    return Edge.from_dict(d)


def edges_of(store, node_id: str) -> list[Edge]:
    """All edges touching a node (both directions)."""
    return _edges_touching(store, node_id)


# --- Internal helpers ---

def _edges_touching(store, node_id: str) -> list[Edge]:
    """All edges where node is source or target."""
    edges = []
    seen = set()

    # Outgoing
    for ek_key in store.scan("idx_edges_out", f"{node_id}:"):
        ek = ek_key.split(":", 1)[1]
        if ek not in seen:
            seen.add(ek)
            d = store.get("edges", ek)
            if d:
                edges.append(Edge.from_dict(d))

    # Incoming
    for ek_key in store.scan("idx_edges_in", f"{node_id}:"):
        ek = ek_key.split(":", 1)[1]
        if ek not in seen:
            seen.add(ek)
            d = store.get("edges", ek)
            if d:
                edges.append(Edge.from_dict(d))

    return edges


def _edges_between(store, source: str, target: str) -> list[Edge]:
    """All edges from source to target (any relation)."""
    edges = []
    for ek_key in store.scan("idx_edges_out", f"{source}:"):
        ek = ek_key.split(":", 1)[1]
        d = store.get("edges", ek)
        if d and d["target"] == target:
            edges.append(Edge.from_dict(d))
    return edges
