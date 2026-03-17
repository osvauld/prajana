"""test_sandhi.py — sandhi: compound resolution and grammar promotion.

Sandhi is the act of joining — two words becoming one meaning.
Each test here asks: when these words arrive together, does nam
recognise the compound that they form?

'kinetic' + 'energy' — do you know these as one thing?
'mass' + 'density' — two satya concepts, but together they name a third.
'photon' + 'energy' — the energy a photon IS, not merely has.

Way 1: mithya + satya — a qualifier preceding a concept.
Way 2: satya + satya — two known concepts naming a compound concept.
Both are callings. Nam arises in the joining or it does not.

Protects against: sandhi-kosha.tantra, sandhi-viveka.tantra,
                  sandhi-avastha.tantra, sandhi-bandhana.tantra

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
def test_sandhi_possession_verb_promoted_to_shashthi(vy, verb, expected_pred):
    g = [[verb, "mithya", verb]]
    result = vy.eval(f"sandhi-viveka {tl(g)}")
    assert result[0][1] == expected_pred, (
        f"'{verb}' → expected pred={expected_pred!r}, got {result[0][1]!r}"
    )


def test_sandhi_past_tense_verb_promoted_to_bhuta_kaala(vy):
    g = [["was", "mithya", "was"]]
    result = vy.eval(f"sandhi-viveka {tl(g)}")
    assert result[0][1] == "bhuta-kaala", (
        f"'was' → expected 'bhuta-kaala', got {result[0][1]!r}"
    )


# ── sandhi-kosha Way 1: mithya + satya → compound ────────────────────────────


def test_sandhi_kosha_way1_kinetic_energy(vy):
    """'kinetic' (mithya) + 'energy' (satya) → kinetic-energy"""
    g = vy.eval('sandhi-kosha (build-question-graph "kinetic energy")')
    assert vy.has_triple(g, subj="kinetic-energy", pred="satya"), (
        f"expected kinetic-energy satya triple, got {g!r}"
    )
    # rename marker consumed by sandhi-bandhana
    assert vy.has_triple(g, subj="kinetic-energy", pred="sandhi-rename"), (
        f"expected sandhi-rename marker, got {g!r}"
    )


def test_sandhi_kosha_way1_potential_energy(vy):
    """'potential' (mithya) + 'energy' (satya) → potential-energy"""
    g = vy.eval('sandhi-kosha (build-question-graph "potential energy")')
    assert vy.has_triple(g, subj="potential-energy", pred="satya"), (
        f"expected potential-energy satya triple, got {g!r}"
    )


# ── sandhi-kosha Way 2: satya + satya → compound ─────────────────────────────


def test_sandhi_kosha_way2_mass_density(vy):
    """'mass' (satya) + 'density' (satya) → mass-density (node exists)"""
    g = vy.eval('sandhi-kosha (build-question-graph "mass density")')
    assert vy.has_triple(g, subj="mass-density", pred="satya"), (
        f"expected mass-density satya triple via Way 2, got {g!r}"
    )
    assert vy.has_triple(g, subj="mass-density", pred="sandhi-rename"), (
        f"expected sandhi-rename marker for mass-density, got {g!r}"
    )
    # originals should be gone (consumed into compound)
    assert not vy.has_triple(g, subj="mass", pred="satya"), (
        f"'mass' should be consumed into compound, still present in {g!r}"
    )


def test_sandhi_kosha_way2_photon_energy(vy):
    """'photon' (satya) + 'energy' (satya) → photon-energy (node exists)"""
    g = vy.eval('sandhi-kosha (build-question-graph "photon energy")')
    assert vy.has_triple(g, subj="photon-energy", pred="satya"), (
        f"expected photon-energy satya triple via Way 2, got {g!r}"
    )


def test_sandhi_kosha_way2_no_false_compound(vy):
    """'mass' + 'force' → no compound (mass-force node does not exist)"""
    g = vy.eval('sandhi-kosha (build-question-graph "mass force")')
    # both should remain separate satya triples
    assert vy.has_triple(g, subj="mass", pred="satya"), (
        f"expected mass to remain satya when no compound found, got {g!r}"
    )
    assert vy.has_triple(g, subj="force", pred="satya"), (
        f"expected force to remain satya when no compound found, got {g!r}"
    )


def test_sandhi_kosha_way2_does_not_consume_third_word(vy):
    """'mass density' compound + trailing word: only first pair consumed"""
    g = vy.eval('sandhi-kosha (build-question-graph "mass density given volume 2")')
    assert vy.has_triple(g, subj="mass-density", pred="satya"), (
        f"expected mass-density compound, got {g!r}"
    )
    # volume should still be present
    assert vy.has_triple(g, subj="volume", pred="satya"), (
        f"expected volume satya to survive after compound, got {g!r}"
    )
