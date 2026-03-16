"""test_mantra_rashi.py — rashi instances feeding mantra derivation.

After the P8b.6 bridge (rashi-anuvada.tantra) is wired in, rashi instances
propagate their sankhya up to the concept level so derive-step and match-mantra
can see them as bound concepts.

Three tiers of tests:

Tier 1 — Single entity, direct mantra fire
  A single object with two named rashi instances where both janya concepts of a
  mantra are satisfied.  The simplest possible case.

Tier 2 — solve-for / match-mantra path
  The sentence explicitly names the quantity to derive (vidhi-kaala intent).
  match-mantra must pick the right mantra.

Tier 3 — Chained derivation (fixpoint)
  An intermediate concept is derived first (e.g. velocity from kinematics),
  then that derived value feeds a second mantra (e.g. kinetic energy).

All tests use anuvada-ganana as the top-level call — it orchestrates
  build-question-graph → avrti-refine (fixpoint) → derive-step (fixpoint)
  → match-mantra → execute-chain → format.

The bqg() helper is kept for graph-level assertions (Tier 1 graph checks).
The run() helper calls anuvada-ganana and returns the answer string.

Run (all will xfail until bridge is built):
    cd /home/abe/agent_x
    .venv/bin/pytest vyakarana/tests/test_mantra_rashi.py -v
"""

import pytest


# ── helpers ──────────────────────────────────────────────────────────────────


def bqg(vy, sentence: str) -> list:
    """Full avrti-refine pipeline — returns refined graph (list of triples)."""
    return vy.eval(f'fixpoint (build-question-graph "{sentence}") avrti-refine')


def run(vy, sentence: str) -> str:
    """Full anuvada-ganana pipeline — returns answer string like 'energy = 1000.'"""
    return str(vy.eval(f'anuvada-ganana "{sentence}"'))


def sig(graph: list) -> list:
    """Filter kosha-janya noise for cleaner assertion messages."""
    return [
        t
        for t in graph
        if isinstance(t, list) and len(t) >= 2 and t[1] != "kosha-janya"
    ]


# ── Tier 1: single entity, direct mantra fire ────────────────────────────────
#
# After rashi-anuvada runs:
#   [v1, vishesa, velocity] + [v1, sankhya, 20.] → [velocity, sankhya, 20.]
#   [m1, vishesa, mass]     + [m1, sankhya, 5.]  → [mass, sankhya, 5.]
# Now kinetic-energy-mantra sees mass + velocity both bound → fires.
# KE = 0.5 * m * v^2 = 0.5 * 5 * 400 = 1000


def test_tier1_ke_graph_has_concept_sankhya(vy):
    """After rashi-anuvada, [velocity, sankhya, 20.] must exist in the graph."""
    g = bqg(vy, "ball1 has velocity v1 of 20 and mass m1 of 5")
    assert vy.has_triple(g, subj="velocity", pred="sankhya"), (
        f"velocity has no sankhya after bridge: {sig(g)}"
    )
    assert vy.has_triple(g, subj="mass", pred="sankhya"), (
        f"mass has no sankhya after bridge: {sig(g)}"
    )


def test_tier1_ke_concept_sankhya_values(vy):
    """Propagated sankhya values must match the instance values."""
    g = bqg(vy, "ball1 has velocity v1 of 20 and mass m1 of 5")
    tv = vy.find_triple(g, subj="velocity", pred="sankhya")
    tm = vy.find_triple(g, subj="mass", pred="sankhya")
    assert tv is not None, f"velocity has no sankhya: {sig(g)}"
    assert tm is not None, f"mass has no sankhya: {sig(g)}"
    assert vy.approx_eq(tv[2], 20.0), f"velocity sankhya expected 20, got {tv[2]}"
    assert vy.approx_eq(tm[2], 5.0), f"mass sankhya expected 5, got {tm[2]}"


def test_tier1_ke_answer(vy):
    """KE = 0.5 * 5 * 20^2 = 1000. solve-for required: 'find kinetic energy'."""
    result = run(vy, "find kinetic energy ball1 has velocity v1 of 20 and mass m1 of 5")
    assert "1000" in result, f"expected energy=1000, got: {result}"


def test_tier1_ke_answer_different_values(vy):
    """KE = 0.5 * 3 * 4^2 = 24."""
    result = run(vy, "find kinetic energy ball has mass m1 of 3 and velocity v1 of 4")
    assert "24" in result, f"expected energy=24, got: {result}"


def test_tier1_momentum_answer(vy):
    """momentum = m * v = 1.5 * 10 = 15."""
    result = run(vy, "find momentum particle has mass m1 of 1.5 and velocity v1 of 10")
    assert "15" in result, f"expected momentum=15, got: {result}"


def test_tier1_force_answer(vy):
    """F = m * a = 2 * 9.8 = 19.6 (Newton's second law)."""
    result = run(vy, "find force ball1 has mass m1 of 2 and acceleration a1 of 9.8")
    assert "19.6" in result or "19.8" in result, f"expected force≈19.6, got: {result}"


def test_tier1_does_not_fire_without_all_janya(vy):
    """Mantra must not fire if only one janya is bound (mass only, no velocity)."""
    result = run(vy, "ball has mass m1 of 5")
    assert result == "no match", f"expected no match (only one janya), got: {result}"


# ── Tier 2: solve-for / match-mantra path ────────────────────────────────────
#
# The sentence contains "find <concept>" which sets vidhi-kaala intent.
# match-mantra first filters mantras whose phala matches the solve-for concept,
# then checks janya coverage.  This tests the solve-for branch explicitly.


def test_tier2_find_energy_answer(vy):
    """'find kinetic energy' → match-mantra picks kinetic-energy-mantra → 1000."""
    result = run(vy, "find kinetic energy ball has mass m1 of 5 and velocity v1 of 20")
    assert "1000" in result, f"expected energy=1000, got: {result}"


def test_tier2_find_force_answer(vy):
    """'find force' → newton-second-law-motion → F = 5 * 3 = 15."""
    result = run(vy, "find force ball has mass m1 of 5 and acceleration a1 of 3")
    assert "15" in result, f"expected force=15, got: {result}"


def test_tier2_find_momentum_answer(vy):
    """'find momentum' → momentum-mantra → p = 4 * 6 = 24."""
    result = run(vy, "find momentum ball has mass m1 of 4 and velocity v1 of 6")
    assert "24" in result, f"expected momentum=24, got: {result}"


def test_tier2_solve_for_prefers_target_mantra(vy):
    """When solve-for is 'force', kinetic-energy-mantra must NOT fire even if mass+velocity are both bound."""
    # mass + velocity satisfies both momentum-mantra AND kinetic-energy-mantra.
    # But solve-for=force means only newton-second-law-motion is a candidate.
    # velocity-mantra phala is velocity, not force — so should not fire.
    # We need acceleration too; without it → no match.
    result = run(vy, "find force ball has mass m1 of 5 and velocity v1 of 20")
    # no acceleration → force mantra can't fire → no match
    assert result == "no match", (
        f"without acceleration, find-force should yield no match, got: {result}"
    )


@pytest.mark.xfail(reason="P8b.6 rashi-anuvada bridge not built yet")
def test_tier2_two_entities_ke_each(vy):
    """Two entities, both have mass+velocity — mantra should fire for one of them."""
    # After rashi-anuvada both [mass, sankhya, ...] entries exist.
    # kinetic-energy-mantra janya=[mass, velocity] — ambiguous which entity.
    # anuvada-ganana should return *some* energy value (either 1000 or 2450).
    result = run(
        vy,
        "ball1 has mass m1 of 5 and velocity v1 of 20 and ball2 has mass m2 of 7 and velocity v2 of 7",
    )
    assert "no match" not in result, (
        f"expected energy result for two-entity scene, got: {result}"
    )


# ── Tier 3: chained derivation via fixpoint derive-step ──────────────────────
#
# An intermediate concept is derived in one pass of derive-step, then the
# derived value feeds a second mantra in the next pass.  fixpoint stops when
# nothing new is added.  The chain depth is unlimited — fixpoint handles n steps.
#
# Key sentence rules:
#   - "initial velocity" (two words) — sandhi-avastha compounds → initial-velocity (satya)
#   - "initial-velocity" (hyphenated) — single token, no kosha hit, stays mithya → WRONG
#   - "find X" is required — without a solve-for, the answer is in the graph but
#     match-mantra cannot surface a single result from multiple fired mantras
#
# Example chain (2-step):
#   velocity-mantra:       janya=[initial-velocity, acceleration, time] → phala=velocity
#   kinetic-energy-mantra: janya=[mass, velocity]                       → phala=energy
#
#   initial-velocity=0, acceleration=10, time=5, mass=2
#     pass 1: velocity = 0 + 10×5 = 50
#     pass 2: KE = 0.5 × 2 × 50² = 2500


def test_tier3_velocity_then_ke_chain(vy):
    """derive-step pass 1: velocity=50  pass 2: KE=2500."""
    result = run(
        vy,
        "find kinetic energy ball has initial velocity iv1 of 0 and acceleration a1 of 10 and time t1 of 5 and mass m1 of 2",
    )
    assert "2500" in result, f"expected KE=2500 after v=50 chain, got: {result}"


def test_tier3_velocity_then_momentum_chain(vy):
    """derive-step pass 1: velocity=12  pass 2: momentum=60."""
    # v = 0 + 4×3 = 12, p = 5×12 = 60
    result = run(
        vy,
        "find momentum ball has initial velocity iv1 of 0 and acceleration a1 of 4 and time t1 of 3 and mass m1 of 5",
    )
    assert "60" in result, f"expected momentum=60 after v=12 chain, got: {result}"


def test_tier3_intermediate_velocity_in_graph(vy):
    """After derive-step fixpoint, [velocity, sankhya, 50.] must exist in graph."""
    enriched = vy.eval(
        'fixpoint (kosha-expand (fixpoint (build-question-graph "ball has initial velocity iv1 of 0 and acceleration a1 of 10 and time t1 of 5 and mass m1 of 2") avrti-refine)) derive-step'
    )
    t = vy.find_triple(enriched, subj="velocity", pred="sankhya")
    assert t is not None, f"velocity not derived: {sig(enriched)}"
    assert vy.approx_eq(t[2], 50.0), f"expected velocity=50, got {t[2]}"


def test_tier3_force_then_work_chain(vy):
    """derive-step pass 1: force=12  pass 2: work = F×d×cos(0°) = 60."""
    # F = 3×4 = 12, W = 12×5×cos(0°) = 60
    # work-mantra krama-rhs: force, displacement, angle — currently uses raw angle,
    # not cos(angle), so angle=0 gives W=0 instead of W=60
    result = run(
        vy,
        "find work ball has mass m1 of 3 and acceleration a1 of 4 and displacement d1 of 5 and angle theta1 of 0",
    )
    assert "60" in result, f"expected work=60 after F=12 chain, got: {result}"
