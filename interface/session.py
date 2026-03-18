"""
session.py — BusSession: the open-book question/answer session.

The session is the open book.
The question is not lost.
What was unknown in turn 1 is resolved by turn 2 in the same session.

A BusSession wraps a JnanaBus and a proof graph session ID.
It handles the ask/tell/retry loop transparently.
"""

import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))

from transport import send
from triples import BusResponse, Triple, extract_known, extract_asprista
from pada_viveka import classify, ASPRISTA, SANKHYA, AVYAYA


class BusSession:
    """
    A session on the jnana bus.

    ask(sentence) → {status, answer, known, unknown, resolved, ...}

      status='complete' → answer is ready
      status='partial'  → some words unknown, derivation incomplete

    tell(fact)    → inject a fact without deriving an answer
    what_do_i_know() → {session_id, memory, turn_id}
    end()         → close the session on the server

    The session accumulates knowledge across turns via prior_graph
    (handled server-side by session-anuvada). The bus extends this
    by injecting provisional triples for unknown words.
    """

    def __init__(
        self,
        bus,  # JnanaBus
        session_id: str = "",
        auto_anveshana: bool = True,
    ):
        self.bus = bus
        self.session_id = session_id or f"session-{os.getpid()}"
        self.auto_anveshana = auto_anveshana
        self.turn_id = 0
        self.memory: dict = {}  # accumulated known concepts

    # ── public API ─────────────────────────────────────────────────────────────

    def ask(self, sentence: str) -> dict:
        """
        Ask a question. Returns a structured response dict.
        If auto_anveshana is True and words are unknown,
        seeks them via the bus and re-asks automatically.
        """
        self.turn_id += 1

        # first attempt
        resp = self._question(sentence)
        answer = resp.get("answer_text", "")
        no_match = _is_no_match(answer)

        if not no_match:
            return self._complete(answer, sentence)

        if not self.auto_anveshana:
            return self._partial(answer, sentence, [], {})

        # classify words to find unknowns
        unknown = _detect_unknown(sentence)
        if not unknown:
            # words are known but derivation failed (missing janya, no intent, etc.)
            return self._partial(answer, sentence, [], {})

        # seek via bus — inject into session graph
        resolved: dict[str, list[Triple]] = {}
        context = {
            "session_id": self.session_id,
            "known_concepts": self.memory,
            "sentence": sentence,
            "mid_sentence": True,
        }
        for w in unknown:
            triples = self.bus.seek_one(w, session_id=self.session_id, context=context)
            if triples:
                resolved[w] = triples

        if not resolved:
            return self._partial(answer, sentence, unknown, {})

        # tell the session what was resolved as fact sentences
        # so session-anuvada binds the values into prior_graph via sankhya triples
        for word, triples in resolved.items():
            fact = _triples_to_fact(word, triples)
            if fact:
                self.tell(fact)

        # re-ask — the session now has the resolved bindings in prior_graph
        self.turn_id += 1
        resp2 = self._question(sentence)
        answer2 = resp2.get("answer_text", "")

        if not _is_no_match(answer2) and answer2:
            return {**self._complete(answer2, sentence), "resolved": resolved}

        return self._partial(answer2 or answer, sentence, unknown, resolved)

    def tell(self, fact: str) -> dict:
        """
        Tell the session a fact without deriving an answer.
        e.g. session.tell("electron rest mass energy is 0.511 MeV")
        """
        self.turn_id += 1
        resp = self._question(fact)
        return {
            "status": "noted",
            "session_id": self.session_id,
            "turn_id": self.turn_id,
            "response": resp.get("answer_text", ""),
        }

    def what_do_i_know(self) -> dict:
        return {
            "session_id": self.session_id,
            "turn_id": self.turn_id,
            "memory": self.memory,
        }

    def end(self) -> None:
        send(self.bus._sock, {"command": "end-session", "session_id": self.session_id})

    # ── helpers ────────────────────────────────────────────────────────────────

    def _question(self, sentence: str) -> dict:
        # NO "command" key — the question handler is the catch-all (| _) in
        # socket.ml. Including "command":"question" would route to the wrong handler.
        # see vyakarana/tests/vy.py line 168 for the canonical pattern.
        return send(
            self.bus._sock,
            {
                "question": sentence,
                "session_id": self.session_id,
            },
            timeout=30.0,
        )

    def _complete(self, answer: str, sentence: str) -> dict:
        return {
            "status": "complete",
            "answer": answer,
            "session_id": self.session_id,
            "turn_id": self.turn_id,
            "sentence": sentence,
        }

    def _partial(
        self, answer: str, sentence: str, unknown: list, resolved: dict
    ) -> dict:
        return {
            "status": "partial",
            "answer": answer or "no match",
            "unknown": unknown,
            "resolved": resolved,
            "session_id": self.session_id,
            "turn_id": self.turn_id,
            "sentence": sentence,
        }


# ── partial knowledge convenience wrapper ─────────────────────────────────────


class PartialKnowledge:
    """
    Wraps a session response dict to provide convenient property access.
    Acts as a dict so callers can also use ['key'] notation.

    Philosophically: samskaara — the impression of what has passed.
    The partial is not failure. It is the current state of understanding.
    """

    def __init__(self, data: dict):
        self._data = data

    def __getitem__(self, key):
        return self._data[key]

    def __contains__(self, key):
        return key in self._data

    def get(self, key, default=None):
        return self._data.get(key, default)

    def to_dict(self) -> dict:
        return dict(self._data)

    @property
    def is_complete(self) -> bool:
        return self._data.get("status") == "complete"

    @property
    def answer(self) -> str:
        return self._data.get("answer", "")

    @property
    def known(self) -> dict:
        return self._data.get("known", {})

    @property
    def unknown(self) -> list:
        return self._data.get("unknown", [])

    @property
    def seeking(self) -> str:
        return self._data.get("seeking", "")

    @property
    def resolved(self) -> dict:
        return self._data.get("resolved", {})

    def __repr__(self) -> str:
        if self.is_complete:
            return f"<complete: {self.answer!r}>"
        return (
            f"<partial: known={list(self.known.keys())}, "
            f"unknown={self.unknown}, seeking={self.seeking!r}>"
        )


# ── helpers ────────────────────────────────────────────────────────────────────


def _triples_to_fact(word: str, triples: list) -> str:
    """
    Convert resolved triples into a natural-language fact sentence
    that session-anuvada can process and bind as sankhya values.

    [electron, sankhya, 0.511] + [electron, matra, MeV]
        → "electron has rest mass energy of 0.511 MeV"

    [electron, satya, particle]
        → "electron is particle"   (tells the session what it is)
    """
    val = next((str(o) for s, e, o in triples if e == "sankhya"), "")
    unit = next((str(o) for s, e, o in triples if e == "matra"), "")
    label = next((str(o) for s, e, o in triples if e == "satya"), "")
    prop = next(
        (
            e
            for s, e, o in triples
            if e not in ("satya", "matra", "sankhya", "sloka", "source", "domain")
        ),
        "",
    )

    if val and unit:
        prop_name = prop.replace("-", " ") if prop else "value"
        return f"{word} has {prop_name} of {val} {unit}"
    if val:
        return f"{word} has value {val}"
    if label and label != word:
        return f"{word} is {label}"
    return ""


def _is_no_match(answer: str) -> bool:
    return answer.strip().lower() in ("no match", "", "none")


def _detect_unknown(sentence: str) -> list[str]:
    """
    Find words in the sentence that pada_viveka classifies as ASPRISTA.
    Skips numbers, particles, and very short tokens.
    """
    words = re.split(r"[\s,;.!?]+", sentence)
    unknown = []
    for i, w in enumerate(words):
        w = w.strip()
        if len(w) <= 1:
            continue
        pada = classify(
            w, position=i, is_capitalized_mid_sentence=bool(i > 0 and w[0].isupper())
        )
        if pada.pada == ASPRISTA:
            unknown.append(w)
    return unknown
