"""graph/ — Core graph engine.

Composes CRUD, walk, query, and merge into a single Graph class.
"""

from pathram2.types import Node, Edge
from pathram2.storage import Storage
from pathram2.graph.crud import (
    add_node, get_node, update_node, delete_node, all_nodes,
    link, unlink, get_edge, edges_of, resolve_id,
)
from pathram2.graph.walk import walk, walk_in, chain, ancestors, descendants, neighbors
from pathram2.graph.query import by_type, by_tag, by_shabda, search, since, between, stale
from pathram2.graph.merge import merge, archive, prune


class Graph:
    """Graph-native knowledge store backed by LMDB."""

    def __init__(self, storage: Storage | None = None, path=None):
        self.store = storage or Storage(path=path)

    # --- Node CRUD ---

    def add(self, type: str, title: str, body: str = "", tag: str = "active",
            shabda: dict | None = None, id: str | None = None) -> Node:
        return add_node(self.store, type, title, body, tag, shabda, id)

    def get(self, id: str) -> Node | None:
        return get_node(self.store, id)

    def update(self, id: str, **fields) -> Node:
        return update_node(self.store, id, **fields)

    def delete(self, id: str):
        delete_node(self.store, id)

    def all(self) -> list[Node]:
        return all_nodes(self.store)

    # --- Edge CRUD ---

    def link(self, source: str, target: str, relation: str,
             shabda: dict | None = None) -> Edge:
        return link(self.store, source, target, relation, shabda)

    def unlink(self, source: str, target: str, relation: str | None = None):
        unlink(self.store, source, target, relation)

    def edges_of(self, node_id: str) -> list[Edge]:
        return edges_of(self.store, node_id)

    # --- Walks ---

    def walk(self, node: str, relation: str) -> list[str]:
        return walk(self.store, node, relation)

    def walk_in(self, node: str, relation: str) -> list[str]:
        return walk_in(self.store, node, relation)

    def chain(self, node: str, relation: str) -> list[str]:
        return chain(self.store, node, relation)

    def ancestors(self, node: str, relation: str = "sthita") -> list[str]:
        return ancestors(self.store, node, relation)

    def descendants(self, node: str, relation: str = "sthita") -> list[str]:
        return descendants(self.store, node, relation)

    def neighbors(self, node: str) -> list[str]:
        return neighbors(self.store, node)

    # --- Queries ---

    def by_type(self, type: str) -> list[Node]:
        return by_type(self.store, type)

    def by_tag(self, tag: str) -> list[Node]:
        return by_tag(self.store, tag)

    def by_shabda(self, key: str, value: str | None = None) -> list[Node]:
        return by_shabda(self.store, key, value)

    def search(self, pattern: str) -> list[Node]:
        return search(self.store, pattern)

    def since(self, dt: str) -> list[Node]:
        return since(self.store, dt)

    def between(self, start: str, end: str) -> list[Node]:
        return between(self.store, start, end)

    def stale(self, days: int) -> list[Node]:
        return stale(self.store, days)

    # --- Merge / Consolidation ---

    def merge(self, node_ids: list[str], into_type: str, title: str,
              body: str = "") -> Node:
        return merge(self.store, node_ids, into_type, title, body)

    def archive(self, node_id: str):
        archive(self.store, node_id)

    def prune(self, tag: str = "consolidated", older_than_days: int = 30):
        prune(self.store, tag, older_than_days)

    # --- Composable queries ---

    def q(self, node_id: str | None = None) -> "Query":
        """Start a composable query chain.

        Usage:
            g.q().type("step").tag("active").shabda("status", "pending").load()
            g.q("plan-nlp").descendants("sthita").type("step").count()
            g.q().type("session").sort("created_at", reverse=True).limit(5).load()
        """
        from pathram2.graph.pipe import Query
        if node_id:
            return Query(self.store, [node_id])
        return Query(self.store)

    def resolve(self, id_or_name: str) -> str | None:
        """Resolve a slug or ID to a confirmed node ID."""
        return resolve_id(self.store, id_or_name)

    # --- Lifecycle ---

    def close(self):
        self.store.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
