"""test_word_index.py — lookup-word: word index, morpheme rules, misses.

Tests the word index that is built at server load time from the kosha .om files.
Covers direct hits, plural morpheme stripping, concept vs mantra name collision,
abbreviations, and miss cases.

Protects against regressions in: word-index loading, morpheme rules in tantras.

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
    result = vy.eval(f'lookup-word "{word}"')
    assert result == expected, (
        f"lookup-word '{word}': expected {expected!r}, got {result!r}"
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
    result = vy.eval(f'lookup-word "{plural}"')
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
    result = vy.eval(f'lookup-word "{plural}"')
    assert result == expected, (
        f"plural-ies: '{plural}' → expected {expected!r}, got {result!r}"
    )


# ── plural -es stripping ──────────────────────────────────────────────────────


def test_plural_es_masses(vy):
    # "masses" → "mass" via english-plural-es morpheme rule
    result = vy.eval('lookup-word "masses"')
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
    result = vy.eval(f'lookup-word "{word}"')
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
    result = vy.eval(f'lookup-word "{word}"')
    assert result is None, (
        f"word index is case-sensitive: '{word}' should return None, got {result!r}"
    )


# ── abbreviations (not yet built) ─────────────────────────────────────────────


@pytest.mark.xfail(
    strict=True,
    reason="abbreviation expansion not built: 'kg', 'N' not registered in word_index",
)
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
    result = vy.eval(f'lookup-word "{abbr}"')
    assert result == expected, (
        f"abbreviation '{abbr}' → expected {expected!r}, got {result!r}"
    )


# ── concept vs mantra name ────────────────────────────────────────────────────


def test_concept_name_not_mantra(vy):
    # "acceleration" resolves to the concept node, not "acceleration-mantra"
    result = vy.eval('lookup-word "acceleration"')
    assert result == "acceleration", f"expected 'acceleration', got {result!r}"
    assert result != "acceleration-mantra", "should not resolve to mantra name"


def test_kinetic_energy_concept_not_mantra(vy):
    # "kinetic-energy" resolves to the concept node, not "kinetic-energy-mantra"
    result = vy.eval('lookup-word "kinetic-energy"')
    assert result == "kinetic-energy", f"expected 'kinetic-energy', got {result!r}"
    assert result != "kinetic-energy-mantra", "should not resolve to mantra name"
