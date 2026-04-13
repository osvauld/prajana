"""test_answers.py — end-to-end: sentence in, answer out.

8 capabilities, ~20 tests. The pipeline is a black box here —
we feed natural language and assert the answer text.

Uses vy.answer() from shared helpers.
Protects: the entire pipeline as an integrated system.
"""

import pytest


# ── single mantra (one concept → one formula → one number) ─────────────────────


def test_ke_basic(vy):
    """KE = ½mv²: mass=5, v=10 → 250."""
    r = vy.answer("mass is 5 and velocity is 10. find kinetic energy")
    assert "250" in r


def test_momentum_basic(vy):
    """p = mv: mass=5, v=10 → 50."""
    r = vy.answer("mass is 5 and velocity is 10. find momentum")
    assert "50" in r


def test_force_basic(vy):
    """F = ma: mass=10, a=5 → 50."""
    r = vy.answer("mass is 10 and acceleration is 5. find force")
    assert "50" in r


def test_ke_different_values(vy):
    """KE with different numbers to verify computation, not memorization."""
    r = vy.answer("mass is 2 and velocity is 4. find kinetic energy")
    assert "16" in r


# ── chain derive (intermediate compute → final) ───────────────────────────────


def test_chain_ke_via_suvat(vy):
    """KE via chain: initial-velocity + acceleration → velocity → KE."""
    r = vy.answer(
        "find kinetic energy given initial velocity 0 acceleration 4 time 5 mass 10"
    )
    assert "2000" in r, f"expected KE=2000 (v=at=20, KE=½·10·400), got: {r}"


def test_chain_force_via_suvat(vy):
    """Force via chain: v, u, t → acceleration → force."""
    r = vy.answer(
        "find force given initial velocity 0 final velocity 20 time 4 mass 10"
    )
    assert "50" in r, f"expected F=50 (a=(20-0)/4=5, F=10·5), got: {r}"


# ── two entity scope ──────────────────────────────────────────────────────────


def test_two_entity_ke_first(vy):
    """ball-A (m=3, v=4) KE=24. Ask for ball-A specifically."""
    r = vy.answer(
        "ball-A has mass 3 and velocity 4. "
        "ball-B has mass 2 and velocity 5. "
        "find kinetic energy of ball-A"
    )
    assert "24" in r


def test_two_entity_ke_second(vy):
    """ball-B (m=2, v=5) KE=25. Ask for ball-B specifically."""
    r = vy.answer(
        "ball-A has mass 3 and velocity 4. "
        "ball-B has mass 2 and velocity 5. "
        "find kinetic energy of ball-B"
    )
    assert "25" in r


# ── reasoning strands (we have / we seek / we know / we find) ──────────────────


def test_strands_present(vy):
    """Full answer has all four reasoning strands."""
    r = vy.answer("mass is 5 and velocity is 10. find kinetic energy")
    rl = r.lower()
    for strand in ("we have", "we seek", "we know", "we find"):
        assert strand in rl, f"missing '{strand}': {r}"


def test_strand_entity_names(vy):
    """Entity name appears in the 'we have' section."""
    r = vy.answer("ball-A has mass 5 and velocity 10. find kinetic energy of ball-A")
    we_have = vy.strand(r, "we have")
    assert "ball-A" in we_have, f"ball-A not in we-have: {r}"


# ── multi-turn session ────────────────────────────────────────────────────────


def test_session_accumulate(vy):
    """Multi-turn: properties set in turn 1 are used in turn 2."""
    sid = "test-session-accumulate-v2"
    vy.ask("mass is 5", session_id=sid)
    vy.ask("velocity is 10", session_id=sid)
    r = vy.ask("find kinetic energy", session_id=sid)
    assert "250" in r, f"expected KE=250 from accumulated session, got: {r}"


def test_session_entity_persists(vy):
    """Entity established in turn 1 is present in turn 2."""
    sid = "test-entity-persist-v2"
    vy.ask("electron has mass 9.109e-31", session_id=sid)
    r = vy.ask("find momentum given velocity 1e6", session_id=sid)
    assert "9.109e-25" in r, f"expected p=mv=9.109e-25, got: {r}"


# ── no match (insufficient data) ──────────────────────────────────────────────


def test_no_match_missing_data(vy):
    """Not enough data → no match."""
    r = vy.answer("mass is 5. find kinetic energy")
    assert "no match" in r.lower(), f"expected 'no match' for missing velocity, got: {r}"


# ── comparison / viveka ───────────────────────────────────────────────────────


def test_viveka_heavier(vy):
    """'which is heavier' with direct mass comparison."""
    r = vy.answer("ball-A has mass 5. ball-B has mass 3. which is heavier")
    assert "ball-A" in r


def test_viveka_faster(vy):
    """'which is faster' with direct velocity comparison."""
    r = vy.answer("car-A has velocity 80. car-B has velocity 60. which is faster")
    assert "car-A" in r


def test_viveka_lightest(vy):
    """Superlative: 'which is lightest' picks minimum."""
    r = vy.answer(
        "ball-A has mass 5. ball-B has mass 3. ball-C has mass 7. which is lightest"
    )
    assert "ball-B" in r


# ── paragraph: multi-sentence accumulation ────────────────────────────────────


def test_paragraph_statement_then_question(vy):
    """Statement provides data, question asks for computation."""
    r = vy.answer("ball has mass 5 and velocity 10. find kinetic energy")
    assert "250" in r


# ── count arithmetic (grade-sparsha: sentence-local binding) ───────────────────


def test_count_addition(vy):
    """3 birds + 2 more = 5. Period boundary separates sentences."""
    r = vy.answer("3 birds sat on a tree. 2 more came. how many birds are there in total")
    assert "5" in r


def test_count_subtraction(vy):
    """10 birds - 3 flew away = 7. Period boundary separates sentences."""
    r = vy.answer("10 birds sat on a tree. 3 flew away. how many birds are left")
    assert "7" in r


def test_count_subtraction_comma_boundary(vy):
    """Comma is also a viraam boundary. 3 must not bind to tree."""
    r = vy.answer("10 birds sat on a tree, 3 flew away. how many birds are left")
    assert "7" in r


def test_count_number_before_noun(vy):
    """3 birds - 2 flew away = 1. Numbers-before-noun stay loose; ordering preserved."""
    r = vy.answer("3 birds sat on a tree. 2 flew away. how many birds are left")
    assert "1" in r


def test_count_named_entity_total(vy):
    """box-A has 5, box-B has 3. Total = 8."""
    r = vy.answer(
        "box-A has 5 apples. box-B has 3 apples. how many apples are there in total"
    )
    assert "8" in r


def test_count_gave_away(vy):
    """Maria had 10, gave 4 away. 10 - 4 = 6."""
    r = vy.answer(
        "Maria had 10 apples. she gave 4 to Tom. how many apples does Maria have"
    )
    assert "6" in r


def test_paragraph_entity_across_sentences(vy):
    """Properties split across sentences bind to same entity."""
    r = vy.answer("ball has mass 5. velocity is 10. find kinetic energy")
    assert "250" in r, f"expected KE=250 from cross-sentence binding, got: {r}"
