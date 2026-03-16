"""test_rashi_edge_cases.py — adversarial / stress tests for rashi-anuvada bridge.

Probes corner cases in the P8b.6 pipeline:
  - rashi-anuvada.tantra: propagation of [inst, vishesa, concept] + [inst, sankhya, v]
    up to [concept, sankhya, v]
  - anuvada-ganana: mantra match under unusual input conditions

Goal: find real bugs.  All tests here are expected to PASS (no xfail markers),
unless the scenario is genuinely unsupported (marked with a comment explaining why).

Run:
    cd /home/abe/agent_x
    VYAKARANA_SOCKET=/tmp/vy.sock .venv/bin/pytest vyakarana/tests/test_rashi_edge_cases.py -v
"""

import pytest


def bqg(vy, sentence: str) -> list:
    return vy.eval(f'fixpoint (build-question-graph "{sentence}") avrti-refine')


def run(vy, sentence: str) -> str:
    return str(vy.eval(f'anuvada-ganana "{sentence}"'))


def sig(graph: list) -> list:
    return [
        t
        for t in graph
        if isinstance(t, list) and len(t) >= 2 and t[1] != "kosha-janya"
    ]


# ── 1. Zero value propagation ────────────────────────────────────────────────
# sankhya=0. is a valid number. rashi-anuvada must not suppress it.


def test_zero_sankhya_propagates(vy):
    """[v1, sankhya, 0.] must propagate to [velocity, sankhya, 0.]."""
    g = bqg(vy, "ball has velocity v1 of 0 and mass m1 of 5")
    tv = vy.find_triple(g, subj="velocity", pred="sankhya")
    assert tv is not None, f"velocity sankhya missing for zero value: {sig(g)}"
    assert vy.approx_eq(tv[2], 0.0), f"expected 0, got {tv[2]}"


def test_zero_velocity_ke_answer(vy):
    """KE = 0.5 * 5 * 0^2 = 0. Must return 0, not 'no match'."""
    result = run(vy, "find kinetic energy ball has mass m1 of 5 and velocity v1 of 0")
    assert "0" in result, f"expected energy=0 for zero velocity, got: {result}"


# ── 2. Floating-point sankhya values ────────────────────────────────────────


def test_float_sankhya_propagates(vy):
    """Decimal values must propagate exactly."""
    g = bqg(vy, "ball has velocity v1 of 1.5 and mass m1 of 3.0")
    tv = vy.find_triple(g, subj="velocity", pred="sankhya")
    tm = vy.find_triple(g, subj="mass", pred="sankhya")
    assert tv is not None, f"velocity has no sankhya: {sig(g)}"
    assert tm is not None, f"mass has no sankhya: {sig(g)}"
    assert vy.approx_eq(tv[2], 1.5), f"expected 1.5, got {tv[2]}"
    assert vy.approx_eq(tm[2], 3.0), f"expected 3.0, got {tm[2]}"


def test_float_ke_answer(vy):
    """KE = 0.5 * 3.0 * 1.5^2 = 3.375."""
    result = run(
        vy, "find kinetic energy ball has mass m1 of 3.0 and velocity v1 of 1.5"
    )
    assert "3.375" in result or "3.37" in result, (
        f"expected energy≈3.375, got: {result}"
    )


# ── 3. Solve-for correctness: wrong janya set → no match ─────────────────────


def test_find_momentum_needs_velocity_not_acceleration(vy):
    """momentum = m*v; mass+acceleration without velocity → no match."""
    result = run(vy, "find momentum ball has mass m1 of 5 and acceleration a1 of 3")
    assert result == "no match", (
        f"mass+acceleration cannot give momentum, got: {result}"
    )


def test_find_ke_needs_velocity_not_acceleration(vy):
    """KE = 0.5*m*v^2; mass+acceleration without velocity → no match."""
    result = run(
        vy, "find kinetic energy ball has mass m1 of 5 and acceleration a1 of 3"
    )
    assert result == "no match", f"mass+acceleration cannot give KE, got: {result}"


def test_find_force_needs_acceleration_not_velocity(vy):
    """F = m*a; mass+velocity without acceleration → no match (already in tier2 but good to have here too)."""
    result = run(vy, "find force ball has mass m1 of 5 and velocity v1 of 20")
    assert result == "no match", (
        f"mass+velocity without acceleration cannot give force, got: {result}"
    )


# ── 4. Instance name that collides with a kosha node ─────────────────────────
# 'm' is also the node for 'metre' in the kosha (word:m in metre.om).
# build-question-graph runs the word index lookup unconditionally at tokenisation
# time, before any tantra runs, so 'm' is already resolved to 'metre' (satya)
# before vishesa-instance can claim it as a rashi label.
#
# Fix requires context-sensitive word lookup: tokens in label/variable position
# (between a concept and 'of') should not be resolved via the unit word index.
# This is a sandhi-kosha-level change — not yet scheduled in the plan.
# Tracked as Gap 1 variant in ocaml-refactor.md.


def test_instance_named_m_does_not_collide_with_metre(vy):
    """'ball has mass m of 5' — 'm' is a rashi label; sankhya propagates to mass."""
    g = bqg(vy, "ball has mass m of 5 and velocity v1 of 20")
    tm = vy.find_triple(g, subj="mass", pred="sankhya")
    assert tm is not None, f"mass has no sankhya when instance label is 'm': {sig(g)}"
    assert vy.approx_eq(tm[2], 5.0), f"expected 5, got {tm[2]}"


def test_instance_named_m_propagates_to_mass(vy):
    """[m, vishesa, mass] + [m, sankhya, 5.] → [mass, sankhya, 5.]."""
    g = bqg(vy, "ball has mass m of 5 and velocity v1 of 20")
    tm = vy.find_triple(g, subj="mass", pred="sankhya")
    assert tm is not None, f"mass has no sankhya when instance is 'm': {sig(g)}"
    assert vy.approx_eq(tm[2], 5.0), f"expected 5, got {tm[2]}"


def test_ke_with_m_instance_name(vy):
    """KE should fire even when the mass instance is named 'm'."""
    result = run(vy, "find kinetic energy ball has mass m of 5 and velocity v of 20")
    assert "1000" in result, f"expected energy=1000 with 'm' instance, got: {result}"


# ── 5. Two rashi instances of the same concept on one entity ──────────────────
# e.g. "ball has mass m1 of 5 and mass m2 of 10"
# What happens when rashi-anuvada sees two instances pointing to the same concept?
# We don't know the correct answer — this is a stress test to expose crashes/corruption.


def test_duplicate_concept_two_instances_no_crash(vy):
    """Two mass instances on the same entity must not crash the pipeline."""
    try:
        g = bqg(vy, "ball has mass m1 of 5 and mass m2 of 10")
        # both instances should still be typed as mass rashi
        assert vy.has_triple(g, subj="m1", pred="vishesa", obj="mass"), sig(g)
        assert vy.has_triple(g, subj="m2", pred="vishesa", obj="mass"), sig(g)
    except Exception as e:
        pytest.fail(f"pipeline crashed on duplicate concept instances: {e}")


def test_duplicate_concept_instances_have_sankhya(vy):
    """Both mass instances must retain their own sankhya."""
    g = bqg(vy, "ball has mass m1 of 5 and mass m2 of 10")
    t1 = vy.find_triple(g, subj="m1", pred="sankhya")
    t2 = vy.find_triple(g, subj="m2", pred="sankhya")
    assert t1 is not None, f"m1 lost its sankhya: {sig(g)}"
    assert t2 is not None, f"m2 lost its sankhya: {sig(g)}"


# ── 6. Idempotence: running avrti-refine twice ────────────────────────────────
# The pipeline must produce the same result whether run once or wrapped in fixpoint.
# Specifically, [mass, sankhya, 5.] must not appear twice (set semantics).


def test_concept_sankhya_not_duplicated(vy):
    """rashi-anuvada must not produce duplicate [mass, sankhya, ...] triples."""
    g = bqg(vy, "ball has mass m1 of 5 and velocity v1 of 20")
    mass_sankhya_triples = [
        t
        for t in g
        if isinstance(t, list) and len(t) == 3 and t[0] == "mass" and t[1] == "sankhya"
    ]
    assert len(mass_sankhya_triples) <= 1, (
        f"mass sankhya duplicated: {mass_sankhya_triples}"
    )
    vel_sankhya_triples = [
        t
        for t in g
        if isinstance(t, list)
        and len(t) == 3
        and t[0] == "velocity"
        and t[1] == "sankhya"
    ]
    assert len(vel_sankhya_triples) <= 1, (
        f"velocity sankhya duplicated: {vel_sankhya_triples}"
    )


# ── 7. Three rashi instances, only two needed by mantra ───────────────────────
# Extra janya (time) should not interfere with KE derivation.


def test_extra_rashi_instance_does_not_block_ke(vy):
    """Extra time instance must not prevent KE from firing."""
    result = run(
        vy,
        "find kinetic energy ball has mass m1 of 5 and velocity v1 of 20 and time t1 of 3",
    )
    assert "1000" in result, f"extra time instance blocked KE derivation, got: {result}"


# ── 8. Large numbers ──────────────────────────────────────────────────────────


def test_large_value_ke(vy):
    """KE = 0.5 * 1000 * 100^2 = 5000000."""
    result = run(
        vy,
        "find kinetic energy ball has mass m1 of 1000 and velocity v1 of 100",
    )
    assert "5000000" in result or "5e6" in result or "5e+06" in result, (
        f"expected KE=5000000, got: {result}"
    )


# ── 9. Negative sankhya (velocity can be negative) ───────────────────────────
# KE = 0.5 * m * v^2 — squaring makes it positive regardless.


def test_negative_velocity_ke(vy):
    """KE = 0.5 * 2 * (-10)^2 = 100. Negative velocity still gives positive KE."""
    result = run(
        vy,
        "find kinetic energy ball has mass m1 of 2 and velocity v1 of -10",
    )
    assert "100" in result, f"expected KE=100 for v=-10, got: {result}"


# ── 10. Solve-for not present: ambiguous scene → no match ─────────────────────


def test_no_solve_for_mass_velocity_is_ambiguous(vy):
    """mass+velocity without find → ambiguous (momentum vs KE) → no match."""
    result = run(vy, "ball has mass m1 of 5 and velocity v1 of 20")
    assert result == "no match", (
        f"ambiguous scene without solve-for should yield no match, got: {result}"
    )
