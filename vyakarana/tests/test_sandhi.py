"""test_sandhi.py — sandhi-viveka: grammar promotion pass.

Tests the sandhi-viveka tantra that takes a raw token graph (from BQG) and
promotes grammar words (verbs/prepositions) from mithya to their grammatical
predicate (shashthi-vibhakti, bhuta-kaala, etc.).

Verb promotion is NOT yet built — those tests are xfail.

Protects against: sandhi-viveka.tantra

Run:
    cd /home/abe/agent_x && .venv/bin/pytest vyakarana/tests/test_sandhi.py -v --socket /tmp/vy.sock
"""

import json
import pytest


def tl(graph: list) -> str:
    """Convert Python list to JSON string for inline tantra expressions."""
    return json.dumps(graph)


# ── empty and structure invariants ───────────────────────────────────────────


def test_sandhi_empty_graph_returns_empty(vy):
    result = vy.eval("sandhi-viveka []")
    assert result == [], f"expected [], got {result!r}"


def test_sandhi_all_triples_have_three_elements(vy):
    g = [["mass", "satya", "mass"], ["ball", "mithya", "ball"]]
    result = vy.eval(f"sandhi-viveka {tl(g)}")
    for t in result:
        assert isinstance(t, list) and len(t) == 3, (
            f"expected [s, p, o] triple, got {t!r}"
        )


# ── passthrough: satya triples unchanged ─────────────────────────────────────


@pytest.mark.parametrize("node", ["mass", "force", "velocity", "kinetic-energy"])
def test_sandhi_satya_triple_unchanged(vy, node):
    g = [[node, "satya", node]]
    result = vy.eval(f"sandhi-viveka {tl(g)}")
    # the satya triple should pass through unchanged
    satya_triples = [t for t in result if t[1] == "satya"]
    assert len(satya_triples) >= 1, (
        f"satya triple missing after sandhi-viveka for {node!r}"
    )
    assert satya_triples[0][0] == node, f"subject changed: {satya_triples[0]!r}"


# ── passthrough: mithya non-grammar words unchanged ──────────────────────────


@pytest.mark.parametrize("word", ["ball", "train", "robot", "xyzunknown"])
def test_sandhi_mithya_non_grammar_word_unchanged(vy, word):
    g = [[word, "mithya", word]]
    result = vy.eval(f"sandhi-viveka {tl(g)}")
    # non-grammar mithya words stay mithya
    mithya_triples = [t for t in result if t[1] == "mithya"]
    assert len(mithya_triples) >= 1, (
        f"mithya triple missing after sandhi-viveka for {word!r}"
    )


# ── multi-triple graph: mixed types passthrough ───────────────────────────────


def test_sandhi_multi_triple_graph(vy):
    g = [
        ["mass", "satya", "mass"],
        ["ball", "mithya", "ball"],
        ["5", "asprista-sankhya", "5."],
    ]
    result = vy.eval(f"sandhi-viveka {tl(g)}")
    # all triples survive; sandhi may add or transform but must not drop non-grammar
    assert vy.has_triple(result, subj="mass", pred="satya"), "satya triple lost"
    # non-grammar mithya word stays
    mithya = [t for t in result if t[0] == "ball"]
    assert len(mithya) >= 1, "ball triple lost"


# ── verb promotion (not yet built) ────────────────────────────────────────────


@pytest.mark.parametrize(
    "verb,expected_pred",
    [
        ("has", "shashthi-vibhakti"),
        ("with", "shashthi-vibhakti"),
    ],
)
@pytest.mark.xfail(
    strict=True,
    reason="sandhi-viveka verb promotion not yet built: lookup-word 'has'/'with' returns None",
)
def test_sandhi_possession_verb_promoted_to_shashthi(vy, verb, expected_pred):
    g = [[verb, "mithya", verb]]
    result = vy.eval(f"sandhi-viveka {tl(g)}")
    assert result[0][1] == expected_pred, (
        f"'{verb}' → expected pred={expected_pred!r}, got {result[0][1]!r}"
    )


@pytest.mark.xfail(
    strict=True,
    reason="sandhi-viveka verb promotion not yet built: lookup-word 'was' returns None",
)
def test_sandhi_past_tense_verb_promoted_to_bhuta_kaala(vy):
    g = [["was", "mithya", "was"]]
    result = vy.eval(f"sandhi-viveka {tl(g)}")
    assert result[0][1] == "bhuta-kaala", (
        f"'was' → expected 'bhuta-kaala', got {result[0][1]!r}"
    )
