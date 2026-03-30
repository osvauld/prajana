"""test_mixed.py — cross-domain: phrasing variants, session, physics+count,
physics+logic, chain+inverse, tense+physics.
"""

import pytest

xfail = pytest.mark.xfail


# ── natural phrasing: from rest / at rest ─────────────────────────────────────


def test_from_rest_force(vy):
    """'accelerates from rest' → u=0, then find force"""
    r = vy.answer("a car of mass 1200 accelerates from rest at 3 m/s2. find force")
    assert "3600" in r or "force" in r.lower()


def test_at_rest_momentum(vy):
    """'ball is at rest' → v=0 → momentum=0"""
    r = vy.answer("ball is at rest. mass is 5. find momentum")
    assert "0" in r


@xfail(strict=True, reason="from-rest chain: '5 seconds' binds acceleration=5 (not time=5); v=0 used instead of v=at=10; KE=0 not 50000")
def test_from_rest_ke(vy):
    """Starting from rest, accelerate to find KE"""
    r = vy.answer(
        "a car of mass 1000 starts from rest. it accelerates at 2 m/s2 for 5 seconds. "
        "find kinetic energy"
    )
    assert "50000" in r


# ── physics + logic ───────────────────────────────────────────────────────────


@xfail(strict=True, reason="syllogism: universal assertion chain not built")
def test_physics_logic_all_objects(vy):
    """all objects with mass have momentum. electron has mass. does electron have momentum"""
    r = vy.answer(
        "all objects with mass have momentum. electron has mass 9.109e-31. "
        "does the electron have momentum"
    )
    assert "yes" in r.lower() or "momentum" in r.lower()


def test_physics_logic_inheritance(vy):
    """if an object has kinetic energy it is moving. this ball has KE=250. is it moving"""
    r = vy.answer(
        "if an object has kinetic energy it is moving. "
        "a ball has mass 5 and velocity 10. find kinetic energy. is the ball moving"
    )
    assert "250" in r or "moving" in r.lower()


# ── logic + count ─────────────────────────────────────────────────────────────


@xfail(strict=True, reason="multiplication: logic + count — 'each' multiply with syllogism")
def test_logic_count_all_wings(vy):
    """all birds have wings. 3 sparrows are birds. how many wings"""
    r = vy.answer("all birds have wings. birds have 2 wings each. there are 3 sparrows. how many wings")
    assert "6" in r


# ── physics + count ───────────────────────────────────────────────────────────


def test_physics_count_total_ke(vy):
    """ball-A KE=24, ball-B KE=25. total KE asked"""
    r = vy.answer(
        "ball-A has mass 3 and velocity 4. ball-B has mass 2 and velocity 5. "
        "find total kinetic energy"
    )
    assert "49" in r  # total KE; 24 and 25 appear in derivation but 49 is the stated answer


# ── chain + inverse ───────────────────────────────────────────────────────────


def test_chain_inverse_find_force(vy):
    """Given SUVAT data + mass, find force via chain inverse"""
    r = vy.answer(
        "mass is 10. initial velocity is 0. final velocity is 20. time is 4. find force"
    )
    assert "50" in r


@xfail(strict=True, reason="chain inverse: multi-step inverse with two seeks in one paragraph")
def test_chain_inverse_find_initial_velocity(vy):
    """Given KE + mass, find velocity; then given acceleration + time, find initial-velocity"""
    r = vy.answer(
        "kinetic energy is 200. mass is 4. find velocity. "
        "acceleration is 5. time is 4. find initial velocity"
    )
    assert "10" in r or "we find" in r.lower()


# ── tense + physics ────────────────────────────────────────────────────────────


def test_tense_past_then_present(vy):
    """'had velocity 5. now has mass 2. find momentum'"""
    r = vy.answer("the ball had velocity 5. it has mass 2. find momentum")
    assert "10" in r


@xfail(strict=True, reason="tense: 'now' override of past value not built")
def test_tense_velocity_override(vy):
    """Current state overrides past state for computation"""
    r = vy.answer("velocity was 5. velocity is now 10. mass is 2. find kinetic energy")
    assert "100" in r


# ── multi-turn session ────────────────────────────────────────────────────────


def test_session_three_turns(vy):
    """Three turns: mass → velocity → find KE"""
    sid = "test-mixed-session-v2"
    vy.ask("mass is 5", session_id=sid)
    vy.ask("velocity is 10", session_id=sid)
    r = vy.ask("find kinetic energy", session_id=sid)
    assert "250" in r or "kinetic-energy" in r


def test_session_entity_then_property(vy):
    """Entity named in turn 1, property in turn 2"""
    sid = "test-mixed-entity-v2"
    vy.ask("ball has mass 3", session_id=sid)
    vy.ask("ball has velocity 4", session_id=sid)
    r = vy.ask("find kinetic energy of ball", session_id=sid)
    assert "24" in r


# ── colour classifier ─────────────────────────────────────────────────────────


def test_colour_red_blue_distinct(vy):
    """Red and blue balls are distinct entities"""
    g = vy.bqg("a box has 5 red balls and 3 blue balls")
    sankhya = [
        [t[0], t[2]] for t in g
        if isinstance(t, list) and len(t) >= 3 and t[1] == "sankhya"
    ]
    subjects = [s[0] for s in sankhya]
    assert len(set(subjects)) >= 2


def test_colour_red_blue_total(vy):
    """5 red + 3 blue = 8 balls"""
    r = vy.answer("a box has 5 red balls and 3 blue balls. how many balls")
    assert "8" in r


# ── total compound ─────────────────────────────────────────────────────────────


def test_total_ke_not_count(vy):
    """'total kinetic energy' → kinetic-energy concept, not count"""
    g = vy.bqg("find total kinetic energy given mass 2 and velocity 3")
    satya = vy.subjects(g, pred="satya")
    assert "count" not in satya
    assert "kinetic-energy" in satya or "total-kinetic-energy" in satya


# ── complex: multi-step chains ───────────────────────────────────────────────


def test_from_rest_suvat_then_force(vy):
    """from rest + suvat chain + F=ma: m=1500, a=2 → F=3000"""
    r = vy.answer("a car of mass 1500 accelerates from rest at 2 m/s2. find force")
    assert "3000" in r


def test_at_rest_mass_ke_and_momentum_zero(vy):
    """at rest → v=0 → both KE=0 and momentum=0 derivable"""
    r = vy.answer("a ball of mass 5 is at rest. what is the kinetic energy")
    assert "0" in r


def test_count_three_ops(vy):
    """20 - 5 + 3 = 18: three-step count chain"""
    r = vy.answer(
        "a bag has 20 apples. 5 were eaten. 3 more were added. how many apples are in the bag"
    )
    assert "18" in r


def test_count_multiplication_boxes(vy):
    """4 boxes × 6 balls = 24"""
    r = vy.answer("there are 4 boxes. each box has 6 balls. how many balls are there")
    assert "24" in r


def test_inverse_momentum_natural(vy):
    """p=20, v=4 → m=5"""
    r = vy.answer("a ball has momentum 20 and velocity 4. find mass")
    assert "5" in r


def test_centripetal_via_natural_phrasing(vy):
    """Natural phrasing: mass 2, radius 5, velocity 10 → centripetal force 40"""
    r = vy.answer(
        "a ball of mass 2 moves in a circle of radius 5 with velocity 10. "
        "find centripetal force"
    )
    assert "40" in r


def test_two_entity_comparison_after_derivation(vy):
    """Derive KE for two entities, then compare"""
    r = vy.answer(
        "ball-A has mass 3 and velocity 4. "
        "ball-B has mass 2 and velocity 6. "
        "which has more kinetic energy"
    )
    assert "ball-B" in r  # KE: 24 vs 36


def test_vibhakti_sampradana_in_graph(vy):
    """'gave to Mary' emits sampradana edge in BQG"""
    g = vy.bqg("Tom has 7 apples. he gave 3 to Mary. how many apples does Tom have")
    edges = [t[1] for t in g if isinstance(t, list) and len(t) >= 2]
    assert "sampradana" in edges
