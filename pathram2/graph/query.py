"""query.py — Filtered queries: by_type, by_tag, by_shabda, search, time-based."""

import re
from datetime import datetime, timedelta
from pathram2.types import Node


def _ids_from_index(store, table: str, prefix: str) -> list[str]:
    """Extract node IDs from an index prefix scan."""
    ids = []
    for key in store.scan(table, prefix):
        # Index keys are "prefix:node_id"
        node_id = key.split(":", 1)[1]
        ids.append(node_id)
    return ids


def _load_nodes(store, ids: list[str]) -> list[Node]:
    """Load nodes by ID list."""
    nodes = []
    for nid in ids:
        d = store.get("nodes", nid)
        if d:
            nodes.append(Node.from_dict(d))
    return nodes


def by_type(store, type: str) -> list[Node]:
    """All nodes of a given type."""
    ids = _ids_from_index(store, "idx_type", f"{type}:")
    return _load_nodes(store, ids)


def by_tag(store, tag: str) -> list[Node]:
    """All nodes with a given tag."""
    ids = _ids_from_index(store, "idx_tag", f"{tag}:")
    return _load_nodes(store, ids)


def by_shabda(store, key: str, value: str | None = None) -> list[Node]:
    """All nodes with a shabda key (optionally matching a value)."""
    results = []
    for d in store.scan_values("nodes"):
        shabda = d.get("shabda", {})
        if key in shabda:
            if value is None or str(shabda[key]) == str(value):
                results.append(Node.from_dict(d))
    return results


def search(store, pattern: str) -> list[Node]:
    """Regex search across all node titles and bodies."""
    try:
        rx = re.compile(pattern, re.IGNORECASE)
    except re.error:
        rx = re.compile(re.escape(pattern), re.IGNORECASE)

    results = []
    for d in store.scan_values("nodes"):
        if rx.search(d.get("title", "")) or rx.search(d.get("body", "")):
            results.append(Node.from_dict(d))
    return results


def since(store, dt: str) -> list[Node]:
    """Nodes created or updated after a datetime string."""
    results = []
    for d in store.scan_values("nodes"):
        if d.get("updated_at", "") >= dt or d.get("created_at", "") >= dt:
            results.append(Node.from_dict(d))
    return results


def between(store, start: str, end: str) -> list[Node]:
    """Nodes created between two datetime strings."""
    results = []
    for d in store.scan_values("nodes"):
        created = d.get("created_at", "")
        if start <= created <= end:
            results.append(Node.from_dict(d))
    return results


def stale(store, days: int) -> list[Node]:
    """Nodes not updated in N days."""
    cutoff = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
    results = []
    for d in store.scan_values("nodes"):
        updated = d.get("updated_at", "")
        if updated and updated < cutoff:
            results.append(Node.from_dict(d))
    return results
