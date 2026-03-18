"""
nodes/graph.py — ProofGraphNode and SecondGraphNode.

The proof graph is the primary knower.
A second graph is the same system with a different kosha.
Both speak via Unix socket. Both return triples.
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from transport import send
from triples import BusResponse, Triple
from node_base import BusNode
from pada_viveka import PadaResult, MATRA


class ProofGraphNode(BusNode):
    """
    The primary vyakarana proof graph.

    Queries in order:
      1. lookup — direct node lookup by name
      2. lookup-word — via word: shabda index (abbreviations, aliases)
      3. walk matra-aayaama — for unit queries
    """

    name = "proof-graph"
    priority = 10

    def __init__(self, sock_path: str = "/tmp/vy.sock"):
        self.sock_path = sock_path

    def available(self) -> bool:
        return os.path.exists(self.sock_path)

    def query(self, word: str, pada: PadaResult, context: dict) -> BusResponse:
        triples: list[Triple] = []

        # 1. direct node lookup
        r = send(self.sock_path, {"command": "eval-json", "expr": f'lookup "{word}"'})
        node = r.get("result")
        if node and str(node) not in ("null", "None", ""):
            node = str(node)
            triples.append((word, "satya", node))
            # get slokas for additional structural edges
            r2 = send(
                self.sock_path,
                {"command": "eval-json", "expr": f'node-slokas "{node}"'},
            )
            for sloka in (r2.get("result") or [])[:3]:
                triples.append((node, "sloka", str(sloka)))

        # 2. word-node lookup (word: shabda index)
        if not triples:
            r = send(
                self.sock_path,
                {"command": "eval-json", "expr": f'lookup-word "{word}"'},
            )
            node = r.get("result")
            if node and str(node) not in ("null", "None", ""):
                triples.append((word, "satya", str(node)))

        # 3. unit lookup via matra-aayaama
        if not triples and pada.pada == MATRA:
            r = send(
                self.sock_path,
                {"command": "eval-json", "expr": 'walk "matra-aayaama" "varga"'},
            )
            for u in r.get("result") or []:
                if str(u).lower() == word.lower():
                    triples.append((word, "satya", str(u)))
                    triples.append((word, "matra-sthita", "matra-kosha"))
                    break

        conf = 0.95 if triples else 0.0
        return BusResponse("proof-graph", word, pada.pada, triples, conf)


class SecondGraphNode(BusNode):
    """
    A second vyakarana instance — different kosha, different language, different domain.
    Same socket protocol as ProofGraphNode but different address.

    Use cases:
      - biology-only kosha at /tmp/bio.sock
      - Malayalam-primary graph at /tmp/ml.sock
      - historical texts graph at /tmp/history.sock
    """

    priority = 30

    def __init__(self, sock_path: str, label: str = "second-graph"):
        self.sock_path = sock_path
        self.name = label

    def available(self) -> bool:
        return os.path.exists(self.sock_path)

    def query(self, word: str, pada: PadaResult, context: dict) -> BusResponse:
        triples: list[Triple] = []

        r = send(self.sock_path, {"command": "eval-json", "expr": f'lookup "{word}"'})
        node = r.get("result")
        if node and str(node) not in ("null", "None", ""):
            triples.append((word, "satya", str(node)))
            triples.append((word, "source", self.name))

        r2 = send(
            self.sock_path, {"command": "eval-json", "expr": f'lookup-word "{word}"'}
        )
        node2 = r2.get("result")
        if not triples and node2 and str(node2) not in ("null", "None", ""):
            triples.append((word, "satya", str(node2)))
            triples.append((word, "source", self.name))

        conf = 0.85 if triples else 0.0
        return BusResponse(self.name, word, pada.pada, triples, conf)
