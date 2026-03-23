"""merge.py — Consolidation: merge nodes, archive, prune."""

from pathram2.types import _now
from pathram2.graph.crud import (
    add_node, get_node, update_node, delete_node,
    link, edges_of,
)
from pathram2.graph.walk import walk_in


def merge(store, node_ids: list[str], into_type: str, title: str,
          body: str = "") -> "Node":
    """Consolidate multiple nodes into one.

    1. Create new node with given type/title/body.
    2. Add abheda edges from each old node → new node.
    3. Transfer incoming edges from old nodes → new node.
    4. Tag old nodes as consolidated.
    """
    from pathram2.types import Node

    new_node = add_node(store, into_type, title, body)

    for nid in node_ids:
        old = get_node(store, nid)
        if old is None:
            continue

        # abheda: old → new (marks "this became that")
        link(store, nid, new_node.id, "abheda")

        # Transfer incoming edges (things pointing TO old node)
        for edge in edges_of(store, nid):
            if edge.target == nid and edge.source not in node_ids:
                # Someone else points to old node — relink to new
                link(store, edge.source, new_node.id, edge.relation, edge.shabda)

        # Tag old node as consolidated
        update_node(store, nid, tag="consolidated")

    return new_node


def archive(store, node_id: str):
    """Mark a node as consolidated (keeps it in graph for history)."""
    update_node(store, node_id, tag="consolidated")


def prune(store, tag: str = "consolidated", older_than_days: int = 30):
    """Delete nodes with a given tag that are older than N days."""
    from datetime import datetime, timedelta
    cutoff = (datetime.now() - timedelta(days=older_than_days)).isoformat(timespec="seconds")

    from pathram2.graph.query import by_tag
    nodes = by_tag(store, tag)
    for node in nodes:
        if node.updated_at < cutoff:
            delete_node(store, node.id)
