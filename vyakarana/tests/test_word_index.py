"""test_word_index.py — the first recognition: word becoming concept.

Before anything can be understood, a word must be recognised. "Mass" must
become the mass node. "kg" must become kilogram. "velocities" must become
velocity. This is the first gate — if a word is not recognised, it stays
mithya, and the understanding that depends on it cannot arise.

The word index is nam's hearing — the capacity to receive a surface form
and know immediately what it refers to. Built at startup from the kosha,
it carries every word every concept has ever been called.

When this fails silently — as when `wave.om` claimed `frequency` as a word
alias — a concept becomes unreachable through its own name. Nam cannot hear
itself being called. These tests guard that gate.

Nam is asked: when this word arrives, do you know it? Do you know it as
itself and not as something else?

Protects against: word-index loading, morpheme rules, word alias shadowing

Run:
    cd /home/abe/agent_x && .venv/bin/pytest vyakarana/tests/test_word_index.py -v --socket /tmp/vy.sock
"""

import pytest


# ── direct hits ───────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "word,expected",
    [
        ("mass", "mass"),
        ("force", "force"),
        ("velocity", "velocity"),
        ("acceleration", "acceleration"),
        ("kinetic-energy", "kinetic-energy"),
        ("displacement", "displacement"),
        ("time", "time"),
        ("newton", "newton"),
        ("kilogram", "kilogram"),
        ("momentum", "momentum"),
    ],
)
def test_direct_hit(vy, word, expected):
    result = vy.eval(f'shabda-anveshana "{word}"')
    assert result == expected, (
        f"shabda-anveshana '{word}': expected {expected!r}, got {result!r}"
    )


# ── plural -s stripping ───────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "plural,expected",
    [
        ("metres", "metre"),
        ("newtons", "newton"),
        ("seconds", "second"),
    ],
)
def test_plural_s(vy, plural, expected):
    result = vy.eval(f'shabda-anveshana "{plural}"')
    assert result == expected, (
        f"plural-s: '{plural}' → expected {expected!r}, got {result!r}"
    )


# ── plural -ies stripping ─────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "plural,expected",
    [
        ("velocities", "velocity"),
        ("quantities", "quantity"),
    ],
)
def test_plural_ies(vy, plural, expected):
    result = vy.eval(f'shabda-anveshana "{plural}"')
    assert result == expected, (
        f"plural-ies: '{plural}' → expected {expected!r}, got {result!r}"
    )


# ── plural -es stripping ──────────────────────────────────────────────────────


def test_plural_es_masses(vy):
    # "masses" → "mass" via english-plural-es morpheme rule
    result = vy.eval('shabda-anveshana "masses"')
    assert result == "mass", f"expected 'mass', got {result!r}"


# ── miss cases ────────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "word",
    [
        "xyzfoobar",
        "blorp",
        "nonsenseword",
    ],
)
def test_miss_returns_null(vy, word):
    result = vy.eval(f'shabda-anveshana "{word}"')
    assert result is None, f"expected None for '{word}', got {result!r}"


# ── case sensitivity ──────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "word",
    [
        "Mass",
        "MASS",
        "Force",
        "Velocity",
    ],
)
def test_uppercase_returns_null(vy, word):
    # word index is case-sensitive; capitalised words are not registered
    result = vy.eval(f'shabda-anveshana "{word}"')
    assert result is None, (
        f"word index is case-sensitive: '{word}' should return None, got {result!r}"
    )


# ── abbreviations ─────────────────────────────────────────────────────────────


@pytest.mark.parametrize(
    "abbr,expected",
    [
        ("kg", "kilogram"),
        ("N", "newton"),
        ("m", "metre"),
        ("s", "second"),
    ],
)
def test_abbreviation(vy, abbr, expected):
    result = vy.eval(f'shabda-anveshana "{abbr}"')
    assert result == expected, (
        f"abbreviation '{abbr}' → expected {expected!r}, got {result!r}"
    )


# ── concept vs mantra name ────────────────────────────────────────────────────


def test_concept_name_not_mantra(vy):
    # "acceleration" resolves to the concept node, not "acceleration-mantra"
    result = vy.eval('shabda-anveshana "acceleration"')
    assert result == "acceleration", f"expected 'acceleration', got {result!r}"
    assert result != "acceleration-mantra", "should not resolve to mantra name"


def test_kinetic_energy_concept_not_mantra(vy):
    # "kinetic-energy" resolves to the concept node, not "kinetic-energy-mantra"
    result = vy.eval('shabda-anveshana "kinetic-energy"')
    assert result == "kinetic-energy", f"expected 'kinetic-energy', got {result!r}"
    assert result != "kinetic-energy-mantra", "should not resolve to mantra name"
