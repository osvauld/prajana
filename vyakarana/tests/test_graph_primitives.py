"""test_graph_primitives.py — graph ops: emit-node, walk, walk-in, register-dimension.

Tests the low-level graph operations against the live kosha. These catch
regressions when proof_graph.ml or yantra_eval_graph.ml changes.

Also tests render-node (sahaja_gloss) — the text rendering of kosha nodes.

Protects against: proof_graph.ml, yantra_eval_graph.ml, anuvada.ml (sahaja_gloss)

Run:
    cd /home/abe/agent_x && .venv/bin/pytest vyakarana/tests/test_graph_primitives.py -v --socket /tmp/vy.sock
"""

import pytest


# ── walk outgoing edges ───────────────────────────────────────────────────────


def test_walk_mass_matra_returns_kilogram(vy):
    # mass has a matra (unit) edge to kilogram in the kosha
    result = vy.walk("mass", "matra")
    assert "kilogram" in result, (
        f"expected 'kilogram' in walk(mass, matra), got {result!r}"
    )


def test_walk_velocity_kramanusara_contains_displacement(vy):
    # velocity has a kramanusara (derived-from) edge to displacement
    result = vy.walk("velocity", "kramanusara")
    assert "displacement" in result, (
        f"expected 'displacement' in walk(velocity, kramanusara), got {result!r}"
    )


def test_walk_unknown_node_returns_empty(vy):
    result = vy.walk("unknown-node-xyz-abc", "satya")
    assert result == [], f"expected [] for unknown node, got {result!r}"


def test_walk_unknown_relation_returns_empty(vy):
    result = vy.walk("mass", "nonexistent-relation-xyz")
    assert result == [], f"expected [] for unknown relation, got {result!r}"


# ── walk incoming edges ───────────────────────────────────────────────────────


def test_walk_in_kilogram_matra_returns_mass(vy):
    # kilogram is the matra of mass — reverse walk should find mass
    result = vy.walk_in("kilogram", "matra")
    assert "mass" in result, (
        f"expected 'mass' in walk_in(kilogram, matra), got {result!r}"
    )


def test_walk_in_unknown_node_returns_empty(vy):
    result = vy.walk_in("unknown-xyz-abc", "matra")
    assert result == [], f"expected [] for unknown node, got {result!r}"


# ── node-satya ────────────────────────────────────────────────────────────────


def test_node_satya_known_node_positive(vy):
    # high-degree physics node should have positive satya score
    result = vy.eval('node-satya "mass"')
    assert isinstance(result, (int, float)), f"expected number, got {result!r}"
    assert result > 0, f"expected satya > 0 for 'mass', got {result!r}"


def test_node_satya_velocity_positive(vy):
    result = vy.eval('node-satya "velocity"')
    assert isinstance(result, (int, float))
    assert result > 0, f"expected satya > 0 for 'velocity', got {result!r}"


def test_node_satya_unknown_returns_zero(vy):
    result = vy.eval('node-satya "unknown-xyz-abc"')
    assert result == 0 or result is None, f"expected 0 for unknown node, got {result!r}"


# ── register-dimension ────────────────────────────────────────────────────────


def test_register_dimension_returns_index(vy):
    idx = vy.eval('register-dimension "satya"')
    assert isinstance(idx, (int, float)), f"expected a numeric index, got {idx!r}"
    assert idx >= 0, f"expected non-negative index, got {idx!r}"


def test_register_dimension_idempotent(vy):
    # calling register-dimension twice with the same name returns the same index
    idx1 = vy.eval('register-dimension "satya"')
    idx2 = vy.eval('register-dimension "satya"')
    assert idx1 == idx2, f"not idempotent: {idx1!r} vs {idx2!r}"


def test_register_dimension_different_names(vy):
    # different dimension names should produce different (or at least valid) indices
    idx_satya = vy.eval('register-dimension "satya"')
    idx_mithya = vy.eval('register-dimension "mithya"')
    assert isinstance(idx_satya, (int, float))
    assert isinstance(idx_mithya, (int, float))
    # both valid; exact values depend on the order registered
    assert idx_satya >= 0 and idx_mithya >= 0


# ── render-node ───────────────────────────────────────────────────────────────


def test_render_node_mass_returns_string(vy):
    result = vy.eval('render-node "mass"')
    assert isinstance(result, str) and len(result) > 0, (
        f"expected non-empty string, got {result!r}"
    )


def test_render_node_mass_includes_name(vy):
    result = vy.eval('render-node "mass"')
    assert "mass" in result, f"expected node name in output, got {result!r}"


def test_render_node_mass_includes_satya_score(vy):
    result = vy.eval('render-node "mass"')
    assert "satya" in result, f"expected satya score in output, got {result!r}"


def test_render_node_velocity_includes_name(vy):
    result = vy.eval('render-node "velocity"')
    assert "velocity" in result, f"expected 'velocity' in output, got {result!r}"


def test_render_node_unknown_returns_not_found(vy):
    result = vy.eval('render-node "unknown-xyz-node"')
    assert isinstance(result, str), f"expected string, got {result!r}"
    assert "not found" in result, (
        f"expected 'not found' in output for unknown node, got {result!r}"
    )
