"""pipe.py — Composable query chains for graph traversal.

Lets you build multi-step queries like the main graph:
    g.q().type("step").tag("active").shabda("status", "pending").walk("sthita").nodes()
    g.q().type("session").since("2026-03-20").sort("created_at").limit(5).nodes()
    g.q().node("plan-nlp").descendants("sthita").type("step").tag("done").count()
"""

import re
from datetime import datetime, timedelta
from pathram2.types import Node, Edge


class Query:
    """Chainable query builder over the graph."""

    def __init__(self, store, node_ids: list[str] | None = None):
        self._store = store
        # Start with all nodes or a specific set
        if node_ids is not None:
            self._ids = list(node_ids)
        else:
            self._ids = self._store.keys("nodes")

    def _load(self, nid: str) -> dict | None:
        return self._store.get("nodes", nid)

    def _clone(self, ids: list[str]) -> "Query":
        q = Query(self._store, ids)
        return q

    # --- Filters (narrow the set) ---

    def type(self, t: str) -> "Query":
        """Keep only nodes of this type."""
        from pathram2.graph.query import _ids_from_index
        idx_ids = set(_ids_from_index(self._store, "idx_type", f"{t}:"))
        return self._clone([i for i in self._ids if i in idx_ids])

    def tag(self, t: str) -> "Query":
        """Keep only nodes with this tag."""
        from pathram2.graph.query import _ids_from_index
        idx_ids = set(_ids_from_index(self._store, "idx_tag", f"{t}:"))
        return self._clone([i for i in self._ids if i in idx_ids])

    def shabda(self, key: str, value: str | None = None) -> "Query":
        """Keep only nodes with a shabda key (optionally matching value)."""
        filtered = []
        for nid in self._ids:
            d = self._load(nid)
            if d:
                s = d.get("shabda", {})
                if key in s:
                    if value is None or str(s[key]) == str(value):
                        filtered.append(nid)
        return self._clone(filtered)

    def search(self, pattern: str) -> "Query":
        """Keep only nodes matching regex in title or body."""
        try:
            rx = re.compile(pattern, re.IGNORECASE)
        except re.error:
            rx = re.compile(re.escape(pattern), re.IGNORECASE)
        filtered = []
        for nid in self._ids:
            d = self._load(nid)
            if d and (rx.search(d.get("title", "")) or rx.search(d.get("body", ""))):
                filtered.append(nid)
        return self._clone(filtered)

    def since(self, dt: str) -> "Query":
        """Keep only nodes created/updated after datetime."""
        filtered = []
        for nid in self._ids:
            d = self._load(nid)
            if d and (d.get("updated_at", "") >= dt or d.get("created_at", "") >= dt):
                filtered.append(nid)
        return self._clone(filtered)

    def before(self, dt: str) -> "Query":
        """Keep only nodes created before datetime."""
        filtered = []
        for nid in self._ids:
            d = self._load(nid)
            if d and d.get("created_at", "") <= dt:
                filtered.append(nid)
        return self._clone(filtered)

    def stale(self, days: int) -> "Query":
        """Keep only nodes not updated in N days."""
        cutoff = (datetime.now() - timedelta(days=days)).isoformat(timespec="seconds")
        filtered = []
        for nid in self._ids:
            d = self._load(nid)
            if d and d.get("updated_at", "") < cutoff:
                filtered.append(nid)
        return self._clone(filtered)

    # --- Graph traversals (expand the set) ---

    def walk(self, relation: str) -> "Query":
        """Replace current set with outgoing targets along relation."""
        targets = set()
        for nid in self._ids:
            for ek_key in self._store.scan("idx_edges_out", f"{nid}:"):
                ek = ek_key.split(":", 1)[1]
                d = self._store.get("edges", ek)
                if d and d["relation"] == relation:
                    targets.add(d["target"])
        return self._clone(list(targets))

    def walk_in(self, relation: str) -> "Query":
        """Replace current set with incoming sources along relation."""
        sources = set()
        for nid in self._ids:
            for ek_key in self._store.scan("idx_edges_in", f"{nid}:"):
                ek = ek_key.split(":", 1)[1]
                d = self._store.get("edges", ek)
                if d and d["relation"] == relation:
                    sources.add(d["source"])
        return self._clone(list(sources))

    def descendants(self, relation: str = "sthita") -> "Query":
        """Expand to all descendants (BFS on incoming edges)."""
        from pathram2.graph.walk import descendants as _desc
        all_ids = set()
        for nid in self._ids:
            all_ids.update(_desc(self._store, nid, relation))
        return self._clone(list(all_ids))

    def ancestors(self, relation: str = "sthita") -> "Query":
        """Expand to all ancestors (follow relation forward)."""
        from pathram2.graph.walk import ancestors as _anc
        all_ids = set()
        for nid in self._ids:
            all_ids.update(_anc(self._store, nid, relation))
        return self._clone(list(all_ids))

    def neighbors(self) -> "Query":
        """Expand to all neighbors (any relation, any direction)."""
        from pathram2.graph.walk import neighbors as _nbrs
        all_ids = set()
        for nid in self._ids:
            all_ids.update(_nbrs(self._store, nid))
        return self._clone(list(all_ids))

    # --- Starting points ---

    def node(self, nid: str) -> "Query":
        """Start from a specific node."""
        return self._clone([nid])

    def nodes_by_ids(self, ids: list[str]) -> "Query":
        """Start from specific node IDs."""
        return self._clone(ids)

    # --- Sorting ---

    def sort(self, field: str = "created_at", reverse: bool = False) -> "Query":
        """Sort current set by a node field."""
        pairs = []
        for nid in self._ids:
            d = self._load(nid)
            if d:
                val = d.get(field, "") or d.get("shabda", {}).get(field, "")
                pairs.append((nid, val))
        pairs.sort(key=lambda p: p[1], reverse=reverse)
        return self._clone([p[0] for p in pairs])

    def limit(self, n: int) -> "Query":
        """Keep only first N nodes."""
        return self._clone(self._ids[:n])

    # --- Terminal operations (return results) ---

    def ids(self) -> list[str]:
        """Return matching node IDs."""
        return list(self._ids)

    def load(self) -> list[Node]:
        """Return matching nodes as Node objects."""
        nodes = []
        for nid in self._ids:
            d = self._load(nid)
            if d:
                nodes.append(Node.from_dict(d))
        return nodes

    def count(self) -> int:
        """Return count of matching nodes."""
        return len(self._ids)

    def first(self) -> Node | None:
        """Return first matching node or None."""
        if not self._ids:
            return None
        d = self._load(self._ids[0])
        return Node.from_dict(d) if d else None

    def edges(self) -> list[Edge]:
        """Return all edges between nodes in the current set."""
        id_set = set(self._ids)
        edges = []
        seen = set()
        for nid in self._ids:
            for ek_key in self._store.scan("idx_edges_out", f"{nid}:"):
                ek = ek_key.split(":", 1)[1]
                if ek in seen:
                    continue
                d = self._store.get("edges", ek)
                if d and d["target"] in id_set:
                    seen.add(ek)
                    edges.append(Edge.from_dict(d))
        return edges

    def titles(self) -> list[str]:
        """Return titles of matching nodes."""
        titles = []
        for nid in self._ids:
            d = self._load(nid)
            if d:
                titles.append(d.get("title", nid))
        return titles
