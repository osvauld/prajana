"""test_comparison.py — viveka (direct), superlative, computed, proportional, ranking.
"""

import pytest

xfail = pytest.mark.xfail


# ── direct comparison: raw values ─────────────────────────────────────────────


def test_viveka_heavier(vy):
    """Direct mass comparison: ball-A (5) > ball-B (3)"""
    r = vy.answer("ball-A has mass 5. ball-B has mass 3. which is heavier")
    assert "ball-A" in r


def test_viveka_lighter(vy):
    """Inverse: ball-B is lighter"""
    r = vy.answer("ball-A has mass 5. ball-B has mass 3. which is lighter")
    assert "ball-B" in r


def test_viveka_faster(vy):
    """Velocity comparison"""
    r = vy.answer("car-A has velocity 80. car-B has velocity 60. which is faster")
    assert "car-A" in r


def test_viveka_slower(vy):
    r = vy.answer("car-A has velocity 80. car-B has velocity 60. which is slower")
    assert "car-B" in r


def test_viveka_equal(vy):
    """Equal values: both should be mentioned or tied response"""
    r = vy.answer("ball-A has mass 5. ball-B has mass 5. which is heavier")
    rl = r.lower()
    assert "equal" in rl
    assert "ball-a" in rl and "ball-b" in rl


# ── superlative: three entities ───────────────────────────────────────────────


def test_superlative_lightest(vy):
    """Three balls: lightest is ball-B (mass 3)"""
    r = vy.answer("ball-A has mass 5. ball-B has mass 3. ball-C has mass 7. which is lightest")
    assert "ball-B" in r


def test_superlative_heaviest(vy):
    """Three balls: heaviest is ball-C (mass 7)"""
    r = vy.answer("ball-A has mass 5. ball-B has mass 3. ball-C has mass 7. which is heaviest")
    assert "ball-C" in r


def test_superlative_fastest(vy):
    r = vy.answer(
        "car-A has velocity 30. car-B has velocity 50. car-C has velocity 20. which is fastest"
    )
    assert "car-B" in r


# ── computed comparison: derive then compare ──────────────────────────────────


def test_compute_compare_ke(vy):
    """ball-A KE=9, ball-B KE=25. ball-B has more KE"""
    r = vy.answer(
        "ball-A has mass 2 and velocity 3. ball-B has mass 2 and velocity 5. "
        "which has more kinetic energy"
    )
    assert "ball-B" in r and "kinetic" in r.lower()


def test_compute_compare_ke_values_present(vy):
    """Both KE values appear in the answer"""
    r = vy.answer(
        "ball-A has mass 2 and velocity 3. ball-B has mass 2 and velocity 5. "
        "which has more kinetic energy"
    )
    assert "9" in r and "25" in r


def test_compute_compare_momentum(vy):
    """ball-A p=6, ball-B p=20. ball-B has more momentum"""
    r = vy.answer(
        "ball-A has mass 3 and velocity 2. ball-B has mass 4 and velocity 5. "
        "which has more momentum"
    )
    assert "ball-B" in r


# ── count comparison ──────────────────────────────────────────────────────────


def test_count_compare_jars(vy):
    """jar-A=8, jar-B=12 → jar-B has more"""
    r = vy.answer("jar-A has 8 marbles. jar-B has 12 marbles. which jar has more marbles")
    assert "jar-B" in r


@xfail(strict=True, reason="count-then-compare: doesn't integrate the +3 change before comparing; returns box-B as winner; 'box-A' only appears as the loser")
def test_count_compare_after_change(vy):
    """box-A: 5+3=8, box-B: 6 → box-A has more"""
    r = vy.answer(
        "box-A has 5 items. 3 more were added to box-A. box-B has 6 items. which has more items"
    )
    # box-A should be the winner (8 > 6), not just mentioned as the loser
    rl = r.lower()
    assert "box-a" in rl and "than box-a" not in rl


# ── proportional reasoning ────────────────────────────────────────────────────


@xfail(strict=True, reason="proportional: multi-entity compute needs per-entity solve")
def test_proportional_ke_double_velocity(vy):
    """Doubling velocity → 4x KE. ball-A v=10 KE=250, ball-B v=20 KE=1000"""
    r = vy.answer(
        "ball-A has mass 5 and velocity 10. ball-B has mass 5 and velocity 20. "
        "find kinetic energy of ball-A. find kinetic energy of ball-B"
    )
    assert "250" in r and "1000" in r


@xfail(strict=True, reason="proportional: multi-entity compute needs per-entity solve")
def test_proportional_momentum_double_mass(vy):
    """Doubling mass → 2x momentum"""
    r = vy.answer(
        "ball-A has mass 3 and velocity 10. ball-B has mass 6 and velocity 10. "
        "find momentum of ball-A. find momentum of ball-B"
    )
    assert "30" in r and "60" in r


# ── relative comparison ────────────────────────────────────────────────────────


@xfail(strict=True, reason="relative-velocity concept not wired in pipeline")
def test_relative_velocity(vy):
    """ball-A v=10, ball-B v=3 → relative velocity = 7"""
    r = vy.answer(
        "ball-A has velocity 10. ball-B has velocity 3. "
        "find relative velocity of ball-A with respect to ball-B"
    )
    assert "7" in r


# ── complex: multi-entity derived comparison ─────────────────────────────────


def test_three_entity_ke_comparison(vy):
    """3 balls → derive KE for each → find most"""
    r = vy.answer(
        "ball-A has mass 1 and velocity 10. "
        "ball-B has mass 5 and velocity 3. "
        "ball-C has mass 2 and velocity 6. "
        "which ball has the most momentum"
    )
    assert "ball-B" in r  # p: 10, 15, 12 → B wins


def test_three_entity_superlative_least_ke(vy):
    """3 cars → derive KE → find least"""
    r = vy.answer(
        "car-A has mass 1000 and velocity 20. "
        "car-B has mass 2000 and velocity 10. "
        "car-C has mass 500 and velocity 30. "
        "which car has the least kinetic energy"
    )
    assert "car-B" in r  # KE: 200k, 100k, 225k → B least


def test_two_entity_same_mass_momentum(vy):
    """Same mass, different velocity → compare momentum"""
    r = vy.answer(
        "object-A has mass 5 and velocity 3. "
        "object-B has mass 5 and velocity 7. "
        "which has more momentum"
    )
    assert "object-B" in r


def test_count_compare_simple(vy):
    """Direct numeric comparison with entities"""
    r = vy.answer("jar-A has 15 marbles. jar-B has 9 marbles. which jar has more marbles")
    assert "jar-A" in r
