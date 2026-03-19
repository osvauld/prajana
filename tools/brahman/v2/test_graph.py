"""test_graph.py — kosha graph operations.

8 capabilities, ~10 tests. Each test covers one graph operation:
walk, walk-in, node-satya, shabda-lookup, plural-stemming, abbreviation,
ppr, register-dimension.

Protects: yantra_eval_primitives.ml, om_parser.ml, proof_graph.ml
"""

import pytest


# ── walk / walk-in ─────────────────────────────────────────────────────────────


def test_walk_forward(vy):
    """walk follows an outgoing edge."""
    assert "kilogram" in vy.walk("mass", "matra")


def test_walk_in_reverse(vy):
    """walk-in follows an incoming edge."""
    assert "mass" in vy.walk_in("kilogram", "matra")


def test_walk_unknown_node(vy):
    """walk on nonexistent node returns empty list."""
    assert vy.walk("unknown-node-xyz-abc", "satya") == []


# ── node-satya ─────────────────────────────────────────────────────────────────


def test_node_satya_known(vy):
    """Known kosha node has positive satya score."""
    score = vy.eval('node-satya "mass"')
    assert isinstance(score, (int, float)) and score > 0


def test_node_satya_unknown(vy):
    """Unknown node has zero satya."""
    score = vy.eval('node-satya "xyzfoobar-unknown"')
    assert isinstance(score, (int, float)) and score == 0


# ── shabda-anveshana (word lookup) ─────────────────────────────────────────────


def test_shabda_direct(vy):
    """Direct word hit: 'mass' → mass."""
    assert vy.eval('shabda-anveshana "mass"') == "mass"


def test_shabda_plural(vy):
    """Plural stemming: 'velocities' → velocity."""
    assert vy.eval('shabda-anveshana "velocities"') == "velocity"


def test_shabda_abbreviation(vy):
    """Abbreviation: 'kg' → kilogram."""
    assert vy.eval('shabda-anveshana "kg"') == "kilogram"


def test_shabda_miss(vy):
    """Unknown word returns None."""
    assert vy.eval('shabda-anveshana "xyzfoobar"') is None


# ── ppr / register-dimension ──────────────────────────────────────────────────


def test_register_dimension_idempotent(vy):
    """register-dimension returns same index on repeat call."""
    idx1 = vy.eval('register-dimension "satya"')
    idx2 = vy.eval('register-dimension "satya"')
    assert idx1 == idx2 and idx1 >= 10
