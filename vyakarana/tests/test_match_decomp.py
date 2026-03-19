"""test_match_decomp.py — match-mantra decomposition.

match-mantra is currently one large tantra doing five distinct jobs:

  1. scope-vps     — build val-pairs scoped to a named entity
  2. eff-vps       — merge scoped + flat, dedup by concept (scope wins)
  3. relative-vps  — two-entity velocity pair for relative-velocity
  4. mantra-select — filter mantra candidates by solve-for
  5. forward-match — all janya present → return [mantra, vps, "forward"]
  6. inverse-match — phala bound + partial janya → return [mantra, vps, "inverse"]

Each responsibility should become its own named tantra so that:
  - failures have a precise address
  - each piece can be tested and reasoned about independently
  - the top-level match-mantra becomes a thin orchestrator

These tests document the INTERFACE each sub-tantra should expose.
They are xfail now because the sub-tantras do not exist yet.
Once split, xfail markers come off and the tests protect the decomposition.

Run:
    cd /home/abe/agent_x && .venv/bin/pytest vyakarana/tests/test_match_decomp.py -v
"""

import json
import pytest


def bqg(vy, sentence: str) -> list:
    return vy.eval(
        f'fixpoint (build-question-graph "{sentence}") (fn g -> avrti-refine g)'
    )


# ── 1. scope-vps: scoped val-pair extraction ──────────────────────────────────
# Tantra: scope-vps graph entity → [[concept, val], ...]
# Given a graph and a named entity, return only that entity's val-pairs.


@pytest.mark.xfail(reason="decomp: scope-vps not yet a named tantra", strict=True)
def test_scope_vps_returns_only_named_entity_values(vy):
    """scope-vps ball-A returns mass=3, velocity=4 not ball-B's values"""
    g = bqg(vy, "ball-A has mass 3 and velocity 4. ball-B has mass 2 and velocity 5")
    vps = vy.eval(f'scope-vps {json.dumps(g)} "ball-A"')
    assert isinstance(vps, list), f"expected list, got {vps!r}"
    concepts = {kv[0]: kv[1] for kv in vps}
    assert concepts.get("mass") in ("3", "3."), f"expected mass=3, got {concepts!r}"
    assert concepts.get("velocity") in ("4", "4."), (
        f"expected velocity=4, got {concepts!r}"
    )
    assert concepts.get("mass") != "2.", (
        f"ball-B mass should not appear, got {concepts!r}"
    )


@pytest.mark.xfail(reason="decomp: scope-vps not yet a named tantra", strict=True)
def test_scope_vps_second_entity(vy):
    """scope-vps ball-B returns mass=2, velocity=5"""
    g = bqg(vy, "ball-A has mass 3 and velocity 4. ball-B has mass 2 and velocity 5")
    vps = vy.eval(f'scope-vps {json.dumps(g)} "ball-B"')
    concepts = {kv[0]: kv[1] for kv in vps}
    assert concepts.get("mass") in ("2", "2."), f"expected mass=2, got {concepts!r}"
    assert concepts.get("velocity") in ("5", "5."), (
        f"expected velocity=5, got {concepts!r}"
    )


@pytest.mark.xfail(reason="decomp: scope-vps not yet a named tantra", strict=True)
def test_scope_vps_empty_entity_returns_all(vy):
    """scope-vps with empty entity returns all val-pairs (flat mode)"""
    g = bqg(vy, "mass is 4 and velocity is 3")
    vps = vy.eval(f'scope-vps {json.dumps(g)} ""')
    concepts = {kv[0]: kv[1] for kv in vps}
    assert "mass" in concepts and "velocity" in concepts, (
        f"expected mass+velocity, got {concepts!r}"
    )


# ── 2. mantra-select: candidate filtering ────────────────────────────────────
# Tantra: mantra-select solve-for → [mantra, ...]
# Filter all loaded mantras to those whose phala/swarupa/janya match solve-for.


@pytest.mark.xfail(reason="decomp: mantra-select not yet a named tantra", strict=True)
def test_mantra_select_ke_returns_ke_mantra(vy):
    """mantra-select 'kinetic-energy' → list containing kinetic-energy-mantra"""
    result = vy.eval('mantra-select "kinetic-energy"')
    assert isinstance(result, list) and len(result) > 0, (
        f"expected non-empty list, got {result!r}"
    )
    names = [vy.eval(f'shabda "{m}" "name"') for m in result]
    assert "kinetic-energy-mantra" in names, (
        f"expected kinetic-energy-mantra in candidates, got {names!r}"
    )


@pytest.mark.xfail(
    reason="decomp: mantra-select not yet a named tantra — returns string not list",
    strict=True,
)
def test_mantra_select_velocity_returns_multiple(vy):
    """mantra-select 'velocity' → list of ≥2 mantras where velocity is a janya"""
    result = vy.eval('mantra-select "velocity"')
    # When tantra exists this will be a list; currently returns string "mantra-select"
    assert isinstance(result, list) and len(result) >= 2, (
        f"expected ≥2 mantras with velocity as janya, got {result!r}"
    )


@pytest.mark.xfail(
    reason="decomp: mantra-select not yet a named tantra — returns string not list",
    strict=True,
)
def test_mantra_select_unknown_returns_all(vy):
    """mantra-select '' returns all loaded mantras as a list"""
    result = vy.eval('mantra-select ""')
    # When tantra exists this will be a list; currently returns string "mantra-select"
    assert isinstance(result, list) and len(result) > 5, (
        f"expected list of all mantras, got {result!r}"
    )


# ── 3. forward-match: janya-complete → phala ─────────────────────────────────
# Tantra: forward-match candidates vps bcs solve-for → [mantra, vps, "forward"] or []


@pytest.mark.xfail(reason="decomp: forward-match not yet a named tantra", strict=True)
def test_forward_match_ke_when_mass_velocity_present(vy):
    """forward-match with mass+velocity → kinetic-energy-mantra forward"""
    g = bqg(vy, "mass is 4 and velocity is 3. find kinetic energy")
    result = vy.eval(f"forward-match {json.dumps(g)}")
    assert isinstance(result, list) and len(result) == 3, (
        f"expected [mantra, vps, mode], got {result!r}"
    )
    assert result[0] == "kinetic-energy-mantra", (
        f"expected ke-mantra, got {result[0]!r}"
    )
    assert result[2] == "forward", f"expected forward mode, got {result[2]!r}"


@pytest.mark.xfail(reason="decomp: forward-match not yet a named tantra", strict=True)
def test_forward_match_returns_empty_when_janya_missing(vy):
    """forward-match with only mass (no velocity) → [] for ke"""
    g = bqg(vy, "mass is 4. find kinetic energy")
    result = vy.eval(f"forward-match {json.dumps(g)}")
    assert result == [], f"expected [] when janya incomplete, got {result!r}"


# ── 4. inverse-match: phala-bound + partial janya → missing janya ────────────
# Tantra: inverse-match candidates vps bcs solve-for → [mantra, vps, "inverse"] or []


@pytest.mark.xfail(
    reason="decomp: inverse-match not yet a named tantra — also fixes inverse-math gate",
    strict=True,
)
def test_inverse_match_ke_find_velocity(vy):
    """inverse-match with ke=50 mass=2 solve-for=velocity → ke-mantra inverse"""
    g = bqg(vy, "kinetic energy is 50 and mass is 2. find velocity")
    result = vy.eval(f"inverse-match {json.dumps(g)}")
    assert isinstance(result, list) and len(result) == 3, (
        f"expected [mantra, vps, mode], got {result!r}"
    )
    assert result[2] == "inverse", f"expected inverse mode, got {result[2]!r}"
    assert result[0] == "kinetic-energy-mantra", (
        f"expected ke-mantra, got {result[0]!r}"
    )


@pytest.mark.xfail(reason="decomp: inverse-match not yet a named tantra", strict=True)
def test_inverse_match_suvat_find_time(vy):
    """inverse-match with u=0 a=5 v=20 solve-for=time → suvat-mantra inverse"""
    g = bqg(
        vy, "initial velocity is 0. acceleration is 5. final velocity is 20. find time"
    )
    result = vy.eval(f"inverse-match {json.dumps(g)}")
    assert isinstance(result, list) and len(result) == 3, (
        f"expected [mantra, vps, mode], got {result!r}"
    )
    assert result[2] == "inverse", f"expected inverse mode, got {result[2]!r}"


@pytest.mark.xfail(reason="decomp: inverse-match not yet a named tantra", strict=True)
def test_inverse_match_returns_empty_when_phala_missing(vy):
    """inverse-match with only partial janya, no phala → []"""
    g = bqg(vy, "mass is 2. find velocity")
    result = vy.eval(f"inverse-match {json.dumps(g)}")
    assert result == [], f"expected [] when phala not bound, got {result!r}"


# ── 5. relative-vps: two-entity velocity extraction ──────────────────────────
# Tantra: relative-vps graph scope-entity → [[observer-velocity, v], [observed-velocity, v]]


@pytest.mark.xfail(reason="decomp: relative-vps not yet a named tantra", strict=True)
def test_relative_vps_returns_two_velocity_pairs(vy):
    """relative-vps ball-A → observer=10, observed=3"""
    g = bqg(
        vy,
        "ball-A has velocity 10. ball-B has velocity 3. find relative velocity of ball-A",
    )
    vps = vy.eval(f'relative-vps {json.dumps(g)} "ball-A"')
    assert isinstance(vps, list) and len(vps) == 2, (
        f"expected 2 velocity pairs, got {vps!r}"
    )
    concepts = {kv[0]: kv[1] for kv in vps}
    assert "observer-velocity" in concepts, f"missing observer-velocity in {concepts!r}"
    assert "observed-velocity" in concepts, f"missing observed-velocity in {concepts!r}"


@pytest.mark.xfail(reason="decomp: relative-vps not yet a named tantra", strict=True)
def test_relative_vps_empty_when_no_scope(vy):
    """relative-vps with no scope entity → []"""
    g = bqg(vy, "ball-A has velocity 10. ball-B has velocity 3. find relative velocity")
    vps = vy.eval(f'relative-vps {json.dumps(g)} ""')
    assert vps == [], f"expected [] with no scope entity, got {vps!r}"


# ── 6. match-mantra as thin orchestrator ─────────────────────────────────────
# After decomposition, match-mantra should just call the sub-tantras in order.
# These test the CURRENT match-mantra interface is preserved after refactor.


def test_match_mantra_forward_still_works(vy):
    """match-mantra forward path still works after decomposition"""
    g = bqg(vy, "mass is 4 and velocity is 3. find kinetic energy")
    result = vy.eval(f"match-mantra {json.dumps(g)}")
    assert isinstance(result, list) and len(result) == 3
    assert result[0] == "kinetic-energy-mantra"
    assert result[2] == "forward"


def test_match_mantra_scope_still_works(vy):
    """match-mantra scoped to ball-A still returns correct entity's values"""
    g = bqg(
        vy,
        "ball-A has mass 3 and velocity 4. ball-B has mass 2. find kinetic energy of ball-A",
    )
    result = vy.eval(f"match-mantra {json.dumps(g)}")
    assert result and result[0] == "kinetic-energy-mantra"
    vps = {kv[0]: kv[1] for kv in result[1]}
    assert vps.get("mass") in ("3", "3."), f"expected ball-A mass=3, got {vps!r}"
