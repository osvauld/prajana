"""
bus.py — JnanaBus: the knowledge routing layer.

Routes queries to the right nodes based on pada classification.
Injects found triples into the session graph.
Knows nothing about sessions — that is session.py's job.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(__file__))

from transport import send
from triples import BusResponse, Triple
from node_base import BusNode
from pada_viveka import (
    classify,
    PadaResult,
    ASPRISTA,
    SUBANTA,
    TINANTA,
    VISHESHANA,
    SANKHYA,
    MATRA,
    NAAMA,
    AVYAYA,
)
from nodes.graph import ProofGraphNode, SecondGraphNode
from nodes.terminal import TerminalNode
from nodes.static import StaticNode
from nodes.llm import LLMNode


# routing table: pada → which node names to include
# lower priority = queried first within the set
_ROUTE: dict[str, set[str] | None] = {
    SANKHYA: set(),  # number — no lookup needed
    AVYAYA: set(),  # particle — no lookup needed
    MATRA: {"proof-graph", "static"},  # unit — graph + constants
    TINANTA: {"proof-graph", "llm", "terminal"},  # verb — graph, then LLM
    VISHESHANA: {"proof-graph", "llm"},  # adjective — graph, then LLM
    SUBANTA: {"proof-graph", "static", "llm", "terminal"},  # noun — all non-wikidata
    NAAMA: {"proof-graph", "static", "llm", "terminal"},  # entity — all sources
    ASPRISTA: None,  # None = all sources
}


class JnanaBus:
    """
    The knowledge bus.

    Nodes are queried in priority order.
    First confident answer wins (for non-asprista words).
    For asprista: all sources are tried.

    Usage:
        bus = JnanaBus('/tmp/vy.sock')
        bus.add(TerminalNode())
        bus.add(LLMNode(http_url='http://localhost:11434/api/generate'))

        triples = bus.seek('electron', session_id='s1',
                           context={'sentence': 'find rest energy of electron'})
    """

    def __init__(self, proof_graph_socket: str = "/tmp/vy.sock"):
        self._sock = proof_graph_socket
        self._nodes: list[BusNode] = [
            ProofGraphNode(proof_graph_socket),
            StaticNode(),
        ]

    def add(self, node: BusNode) -> "JnanaBus":
        """Add a knowledge source. Returns self for chaining."""
        self._nodes.append(node)
        return self

    def remove(self, name: str) -> "JnanaBus":
        self._nodes = [n for n in self._nodes if n.name != name]
        return self

    @property
    def node_names(self) -> list[str]:
        return [n.name for n in sorted(self._nodes, key=lambda n: n.priority)]

    def seek(
        self,
        word: str,
        session_id: str = "",
        context: dict | None = None,
    ) -> list[BusResponse]:
        """
        Seek knowledge about a word across available nodes.
        Returns all responses (including empty) for full transparency.
        Injects found triples into the session graph automatically.
        """
        if context is None:
            context = {}

        pada = classify(
            word,
            position=context.get("position", 1),
            is_capitalized_mid_sentence=bool(context.get("mid_sentence", False)),
        )

        nodes = self._route(pada)
        results = []

        for node in sorted(nodes, key=lambda n: n.priority):
            if not node.available():
                continue
            try:
                resp = node.query(word, pada, context)
            except Exception as e:
                resp = BusResponse(node.name, word, pada.pada, [], 0.0, f"error: {e}")
            results.append(resp)

            # stop early if confident answer found (except for asprista — try all)
            if resp.found and resp.confidence >= 0.85 and pada.pada != ASPRISTA:
                break

        # inject all found triples into the session graph
        if session_id:
            all_triples: list[Triple] = []
            for resp in results:
                all_triples.extend(resp.triples)
            if all_triples:
                self._inject(all_triples, session_id)

        return results

    def seek_one(
        self,
        word: str,
        session_id: str = "",
        context: dict | None = None,
    ) -> list[Triple]:
        """
        Seek and return the best triples found (across all responses).
        Convenience wrapper over seek().
        """
        responses = self.seek(word, session_id=session_id, context=context)
        triples: list[Triple] = []
        for resp in responses:
            triples.extend(resp.triples)
        return triples

    def _route(self, pada: PadaResult) -> list[BusNode]:
        allowed = _ROUTE.get(pada.pada)
        if allowed is None:
            return list(self._nodes)  # asprista: all sources
        if not allowed:
            return []  # sankhya/avyaya: none
        return [
            n
            for n in self._nodes
            if n.name in allowed or any(n.name.startswith(a) for a in allowed)
        ]

    def open_session(
        self,
        session_id: str = "",
        auto_anveshana: bool = True,
    ):
        """Open a BusSession backed by this bus. Returns BusSession."""
        from session import BusSession  # deferred — avoids circular import

        return BusSession(self, session_id=session_id, auto_anveshana=auto_anveshana)

    def _inject(self, triples: list[Triple], session_id: str) -> None:
        """
        Inject triples into the session proof graph.
        Uses emit-edge — idempotent, goes to 'prashna' layer.
        Does not write to the permanent brahman kosha.
        """
        for s, e, o in triples:
            send(
                self._sock,
                {
                    "command": "eval-json",
                    "expr": f'emit-edge "{s}" "{e}" "{o}"',
                    "session_id": session_id,
                },
                timeout=5.0,
            )
