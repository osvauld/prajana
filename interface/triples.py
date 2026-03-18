"""
triples.py — the fundamental unit of knowledge exchange.

A triple is [subject, edge, object] — the same structure as a proof graph edge.
Everything the bus exchanges is triples. Every source speaks triples.
Every injection into the session graph is triples.

This file also holds BusResponse (what a node returns) and
helper functions that extract triples from proof graph state.
"""

from dataclasses import dataclass, field
from typing import Optional
from transport import send


# A triple: (subject, edge, object) — all strings
Triple = tuple[str, str, str]


@dataclass
class BusResponse:
    """
    What a bus node returns for a query.
    Always triples — never prose, never structured JSON beyond triples.

    The source is recorded so the session can weight confidence
    and the user can see where knowledge came from.
    """

    source: str  # which node answered
    word: str  # the queried word
    pada: str  # pada classification at query time
    triples: list[Triple]  # what it knows as triples
    confidence: float  # 0.0-1.0
    note: str = ""  # optional explanation

    @property
    def found(self) -> bool:
        return bool(self.triples)

    def __repr__(self) -> str:
        status = f"{len(self.triples)} triples" if self.triples else "empty"
        return f"<BusResponse source={self.source!r} word={self.word!r} {status} conf={self.confidence:.0%}>"


# ── graph triple extraction ────────────────────────────────────────────────────


def extract_asprista(graph_triples: list) -> list[str]:
    """
    Find all words that survived avrti as asprista (untouched by the graph).
    asprista-sankhya: a number with no concept to bind to.
    mithya that survived fixpoint: a word the graph could not ground.
    """
    asprista = []
    for triple in graph_triples:
        if isinstance(triple, (list, tuple)) and len(triple) == 3:
            s, e, o = triple
            if str(e) in ("asprista-sankhya", "mithya"):
                asprista.append(str(s))
    return list(set(asprista))


def extract_known(graph_triples: list) -> dict[str, str]:
    """
    Extract all bound concept-value pairs (sankhya triples).
    These are what the graph currently knows numerically.
    Returns {concept: value}.
    """
    known = {}
    for triple in graph_triples:
        if isinstance(triple, (list, tuple)) and len(triple) == 3:
            s, e, o = triple
            if str(e) == "sankhya":
                known[str(s)] = str(o)
    return known


def extract_missing_janya(
    graph_triples: list,
    sock_path: str,
) -> list[str]:
    """
    Find which mantra janya are uncovered in the current graph.
    These are the concepts needed to complete a derivation.
    Uses the mantra-coverage tantra via socket.
    """
    g_json = __import__("json").dumps(graph_triples)
    r = send(sock_path, {"command": "eval-json", "expr": f"mantra-coverage {g_json}"})
    mantras = r.get("result", [])
    missing = []
    for m in mantras if isinstance(mantras, list) else []:
        if isinstance(m, dict):
            missing.extend(str(j) for j in m.get("uncovered", []))
    return list(set(missing))


def extract_solve_for(graph_triples: list) -> str:
    """
    Find the concept the question is asking for (vidhi-kaala / sought edge).
    Returns empty string if no explicit question was asked.
    """
    for triple in graph_triples:
        if isinstance(triple, (list, tuple)) and len(triple) == 3:
            s, e, o = triple
            if str(e) in ("sought", "vidhi-kaala"):
                return str(s)
    return ""
