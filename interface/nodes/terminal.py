"""
nodes/terminal.py — TerminalNode.

Ask the human directly. Parse their response into triples.
This is the "open book, ask the author" source.
Last resort — only fires when everything else fails.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from triples import BusResponse, Triple
from node_base import BusNode
from pada_viveka import PadaResult, ASPRISTA


class TerminalNode(BusNode):
    """
    Prompts the human at the terminal for unknown words.
    Input is parsed into triples via simple heuristics.
    Responses are cached within the session so the same question
    is never asked twice.

    Protocol (terminal output):
        jnana-bus: unknown word 'zhabotinsky' (naama, 95% confidence)
        session knows: {mass: 5, velocity: 10}
        What is 'zhabotinsky'? (Enter to skip)
        → Anatol Zhabotinsky, Soviet chemist, oscillating reactions
        → [zhabotinsky, satya, person]
        → [zhabotinsky, domain, chemistry]
        → [zhabotinsky, kriya, oscillating]
    """

    name = "terminal"
    priority = 90

    def __init__(self, prompt_prefix: str = "jnana-bus"):
        self.prompt_prefix = prompt_prefix
        self._cache: dict[str, list[Triple]] = {}

    def available(self) -> bool:
        return sys.stdin.isatty()

    def query(self, word: str, pada: PadaResult, context: dict) -> BusResponse:
        wl = word.lower()

        if wl in self._cache:
            cached = self._cache[wl]
            return BusResponse(
                "terminal", word, pada.pada, cached, 1.0 if cached else 0.0, "cached"
            )

        # display context
        print(f"\n  [{self.prompt_prefix}] unknown word: {word!r}")
        print(f"  classification: {pada.pada}  ({pada.confidence:.0%} confidence)")
        print(f"  reason: {pada.reason}")
        if pada.alternatives:
            alts = ", ".join(f"{p}({c:.0%})" for p, c in pada.alternatives[:2])
            print(f"  alternatives: {alts}")
        known = context.get("known_concepts", {})
        if known:
            print(f"  session knows: {list(known.keys())}")
        print(f"  What is {word!r}? (Enter to skip)")

        try:
            answer = input("  → ").strip()
        except (EOFError, KeyboardInterrupt):
            answer = ""

        if not answer:
            self._cache[wl] = []
            return BusResponse("terminal", word, pada.pada, [], 0.0, "skipped")

        triples = _parse_answer(word, answer, pada)
        self._cache[wl] = triples
        return BusResponse(
            "terminal", word, pada.pada, triples, 0.85, f"user: {answer!r}"
        )


def _parse_answer(word: str, answer: str, pada: PadaResult) -> list[Triple]:
    """
    Parse a free-text human answer into triples.
    Heuristics only — no NLP required.

    "Anatol Zhabotinsky, Soviet chemist"
        → [zhabotinsky, satya, person]
        → [zhabotinsky, domain, chemistry]

    "0.511 MeV, rest mass energy"
        → [zhabotinsky, sankhya, 0.511]
        → [zhabotinsky, matra, MeV]

    "oscillating chemical reaction"
        → [zhabotinsky, kriya, oscillating]
        → [zhabotinsky, vishesa, chemical]
    """
    triples: list[Triple] = []
    w = word.lower()
    ans = answer.lower()

    # number + unit: "0.511 MeV"
    m = re.search(r"(\d+\.?\d*(?:[eE][+-]?\d+)?)\s*([a-zA-Z/⋅·]+)", answer)
    if m:
        triples.append((w, "sankhya", m.group(1)))
        triples.append((w, "matra", m.group(2)))

    # person type
    if any(
        p in ans
        for p in (
            "person",
            "physicist",
            "chemist",
            "biologist",
            "mathematician",
            "scientist",
            "researcher",
            "engineer",
            "philosopher",
        )
    ):
        triples.append((w, "satya", "person"))

    # domain detection
    for kw, domain in (
        ("chemistry", "chemistry"),
        ("chemical", "chemistry"),
        ("physics", "physics"),
        ("physical", "physics"),
        ("biology", "biology"),
        ("quantum", "quantum-physics"),
        ("nuclear", "nuclear-physics"),
        ("math", "mathematics"),
    ):
        if kw in ans:
            triples.append((w, "domain", domain))
            break

    # action/process
    for pat in (
        r"discover",
        r"invent",
        r"oscillat",
        r"react",
        r"emit",
        r"absorb",
        r"transform",
        r"convert",
    ):
        m2 = re.search(pat, ans)
        if m2:
            triples.append((w, "kriya", m2.group(0)))
            break

    # fallback: store raw answer as sloka
    if not triples:
        triples.append((w, "satya", pada.pada))
        triples.append((w, "sloka", answer[:80]))

    return triples
