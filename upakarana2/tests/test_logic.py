"""test_logic.py — 12 distinct logic patterns:
taxonomy IS-A, syllogism, modus ponens/tollens, transitivity,
negation, disjunction, conditional chain, quantifiers.
"""

import re

import pytest

xfail = pytest.mark.xfail


# ── taxonomy: IS-A direct ─────────────────────────────────────────────────────


@xfail(strict=True, reason="IS-A: resolver checks wrong-subject (wings inherit bird?) instead of sparrow inherit wings")
def test_is_a_direct(vy):
    """a sparrow is a bird. birds have wings. does a sparrow have wings"""
    r = vy.answer("a sparrow is a bird. birds have wings. does a sparrow have wings")
    rl = r.lower()
    assert re.search(r'\byes\b', rl) is not None and "sparrow" in rl


def test_is_a_property_inheritance(vy):
    """metals conduct electricity. copper is a metal. does copper conduct electricity"""
    r = vy.answer(
        "metals conduct electricity. copper is a metal. does copper conduct electricity"
    )
    assert "yes" in r.lower() or "copper" in r.lower()


# ── transitive IS-A ───────────────────────────────────────────────────────────


@xfail(strict=True, reason="IS-A transitive: resolver asks 'does animal inherit animal?' instead of 'does sparrow inherit animal?'")
def test_transitive_is_a(vy):
    """sparrows are birds. birds are animals. is a sparrow an animal"""
    r = vy.answer("sparrows are birds. birds are animals. is a sparrow an animal")
    rl = r.lower()
    # "yes" must appear AND conclusion must mention sparrow (not just input echo)
    yes_idx = rl.rfind("yes")
    assert yes_idx >= 0 and "sparrow" in rl[yes_idx:]


@xfail(strict=True, reason="IS-A transitive: resolver asks 'does animal inherit animal?' instead of 'does poodle inherit animal?'")
def test_transitive_is_a_three_hop(vy):
    """poodles are dogs. dogs are mammals. mammals are animals. is a poodle an animal"""
    r = vy.answer(
        "poodles are dogs. dogs are mammals. mammals are animals. is a poodle an animal"
    )
    rl = r.lower()
    yes_idx = rl.rfind("yes")
    assert yes_idx >= 0 and "poodle" in rl[yes_idx:]


# ── syllogism / classical modus ponens (assertion chain) ─────────────────────


@xfail(strict=True, reason="IS-A syllogism: resolver checks terminal→terminal ('animal has animal'), not cat→breathe")
def test_syllogism_breathe(vy):
    """all cats are animals. all animals breathe. do cats breathe"""
    r = vy.answer("all cats are animals. all animals breathe. do cats breathe")
    rl = r.lower()
    assert re.search(r'\byes\b', rl) is not None and "cat" in rl and "breathe" in rl


@xfail(strict=True, reason="IS-A syllogism: response says 'animal has animal', does not cite cat premise")
def test_syllogism_cites_rule(vy):
    """Answer cites both premises"""
    r = vy.answer("all cats are animals. all animals breathe. do cats breathe")
    rl = r.lower()
    assert "cat" in rl and "breathe" in rl


# ── modus ponens / implication ────────────────────────────────────────────────


@xfail(strict=True, reason="syllogism: modus ponens implication not built")
def test_modus_ponens(vy):
    """if it rains the ground is wet. it rained. is the ground wet"""
    r = vy.answer("if it rains the ground is wet. it rained. is the ground wet")
    assert "yes" in r.lower() or "wet" in r.lower()


@xfail(strict=True, reason="modus-tollens: says 'no' via IS-A, not contrapositive; rain/wet not in reasoning")
def test_modus_tollens(vy):
    """if it rains the ground is wet. the ground is not wet. did it rain"""
    r = vy.answer(
        "if it rains the ground is wet. the ground is not wet. did it rain"
    )
    rl = r.lower()
    assert rl != "no match", "must be real inference, not 'no match'"
    assert re.search(r'\bno\b', rl) is not None
    assert "rain" in rl, "reasoning must reference rain"


# ── transitivity: comparison chain ────────────────────────────────────────────


@xfail(strict=True, reason="transitivity: comparison chain walk not built")
def test_transitive_greater(vy):
    """a is greater than b. b is greater than c. is a greater than c"""
    r = vy.answer("a is greater than b. b is greater than c. is a greater than c")
    assert "yes" in r.lower()


@xfail(strict=True, reason="transitivity: entity ranking via comparison chain")
def test_transitive_entities_ranking(vy):
    """ball-A heavier than ball-B. ball-B heavier than ball-C. which is heaviest"""
    r = vy.answer(
        "ball-A is heavier than ball-B. ball-B is heavier than ball-C. which is the heaviest"
    )
    assert "ball-A" in r


@xfail(strict=True, reason="transitivity: 3-step comparison chain walk")
def test_transitive_three_step(vy):
    """a > b. b > c. c > d. is a > d"""
    r = vy.answer("a is greater than b. b is greater than c. c is greater than d. is a greater than d")
    assert "yes" in r.lower()


# ── negation ──────────────────────────────────────────────────────────────────


@xfail(strict=True, reason="negation+at-rest: response says 'no — velocity is absent' (checks velocity existence, not ball state); 'rest' only matches via 'at-rest' header")
def test_negation_not_moving(vy):
    """the ball is not moving → ball is at rest"""
    r = vy.answer("the ball is not moving. is the ball at rest")
    assert "yes" in r.lower()


def test_negation_blocks_inheritance(vy):
    """a cat is not a fish. fish live in water. does a cat live in water"""
    r = vy.answer("a cat is not a fish. fish live in water. does a cat live in water")
    assert "no" in r.lower()


@xfail(strict=True, reason="negation: double negation cancellation not built")
def test_double_negation(vy):
    """it is not true that the ball is not moving. is the ball moving"""
    r = vy.answer("it is not true that the ball is not moving. is the ball moving")
    assert "yes" in r.lower() or "moving" in r.lower()


# ── disjunction ───────────────────────────────────────────────────────────────


@xfail(strict=True, reason="disjunctive: disjunctive syllogism not built")
def test_disjunctive_syllogism(vy):
    """the ball is red or blue. the ball is not red. what color is the ball"""
    r = vy.answer("the ball is red or blue. the ball is not red. what color is the ball")
    assert "blue" in r.lower()


@xfail(strict=True, reason="neither-nor: system returns 'no match' (pattern not parsed); passes only because 'no' is a substring of 'no match'")
def test_neither_nor(vy):
    """neither A nor B is true. is A true"""
    r = vy.answer("neither the ball is red nor is it blue. is the ball red")
    rl = r.lower()
    assert "no match" not in rl, "should reason about neither/nor, not fall through to no-match"
    assert re.search(r'\bno\b', rl) is not None


# ── conditional chain ─────────────────────────────────────────────────────────


@xfail(strict=True, reason="conditional chain: chained implications not built")
def test_conditional_chain(vy):
    """if temperature rises then ice melts. if ice melts then water appears.
    temperature rose. is water present"""
    r = vy.answer(
        "if temperature rises then ice melts. if ice melts then water appears. "
        "temperature rose. is water present"
    )
    assert "yes" in r.lower() or "water" in r.lower()


# ── quantifiers ───────────────────────────────────────────────────────────────


@xfail(strict=True, reason="IS-A universal: response says 'sparrow has bird' (sparrow IS-A bird confirmed), not 'sparrow can fly'")
def test_universal_all_fly(vy):
    """all birds can fly. is a sparrow able to fly"""
    r = vy.answer("all birds can fly. a sparrow is a bird. can a sparrow fly")
    rl = r.lower()
    assert re.search(r'\byes\b', rl) is not None and "fly" in rl


@xfail(strict=True, reason="universal+exception: says 'yes' via IS-A but ignores penguin exception; 'fly' not in reasoning")
def test_universal_with_exception(vy):
    """all birds fly. penguins are birds. penguins cannot fly. can sparrows fly"""
    r = vy.answer(
        "all birds can fly. penguins are birds. penguins cannot fly. can sparrows fly"
    )
    assert "yes" in r.lower()
    assert "fly" in r.lower(), "reasoning must reference flying"


def test_existential(vy):
    """some metals are magnetic. iron is a magnetic metal. is iron a metal"""
    r = vy.answer("some metals are magnetic. iron is a magnetic metal. is iron a metal")
    assert "yes" in r.lower()


# ── shunya: absence signal ───────────────────────────────────────────────────


def test_shunya_rest_no_velocity(vy):
    """ball is at rest. does it have velocity → no (direct shunya, not just 'no match')"""
    r = vy.answer("the ball is at rest. does the ball have velocity")
    assert "no match" not in r.lower(), "should reason about shunya, not fall through"
    assert "no" in r.lower()


def test_shunya_rest_no_momentum(vy):
    """ball is at rest. does it have momentum → no (inherited: momentum needs velocity)"""
    r = vy.answer("the ball is at rest. does the ball have momentum")
    assert "no match" not in r.lower(), "should reason about shunya, not fall through"
    assert "no" in r.lower()


def test_shunya_rest_no_ke(vy):
    """ball is at rest. does it have kinetic energy → no (inherited: KE needs velocity)"""
    r = vy.answer("the ball is at rest. does the ball have kinetic energy")
    assert "no match" not in r.lower(), "should reason about shunya, not fall through"
    assert "no" in r.lower()


def test_shunya_frictionless_no_friction(vy):
    """surface is frictionless. is there friction → no"""
    r = vy.answer("the surface is frictionless. is there friction")
    assert "no match" not in r.lower(), "should reason about shunya, not fall through"
    assert "no" in r.lower()


def test_shunya_stationary_no_velocity(vy):
    """the car is stationary. does it have velocity → no"""
    r = vy.answer("the car is stationary. does the car have velocity")
    assert "shunya" in r.lower() or "stationary" in r.lower(), "should reason about stationary → shunya"
    assert re.search(r'\bno\b', r.lower()) is not None


def test_shunya_rest_compute_momentum_zero(vy):
    """ball at rest, mass=5 → momentum=0 (shunya on v feeds mantra)"""
    r = vy.answer("ball is at rest. mass is 5. find momentum")
    assert "0" in r


def test_shunya_rest_compute_ke_zero(vy):
    """ball at rest, mass=5 → KE=0 (shunya on v feeds mantra)"""
    r = vy.answer("ball is at rest. mass is 5. find kinetic energy")
    assert "0" in r


# ── pratishedha: negation of shunya ──────────────────────────────────────────


@xfail(strict=True, reason="negation: pratishedha flip of shunya not built")
def test_pratishedha_not_at_rest_has_velocity(vy):
    """ball is not at rest → it has velocity (negation flips shunya)"""
    r = vy.answer("the ball is not at rest. does the ball have velocity")
    assert "yes" in r.lower()


# ── kaala-avastha: temporal state logic ──────────────────────────────────────


def test_kaala_past_vs_present_physics(vy):
    """past tense binds to initial, present to current — acceleration derived"""
    r = vy.answer("velocity was 0. velocity is 20. time is 4. find acceleration")
    assert "5" in r


@xfail(strict=True, reason="kaala-logic: qualitative state change via tense not built")
def test_kaala_state_was_now_is(vy):
    """'was at rest, is moving' — tense flips state"""
    r = vy.answer("the ball was at rest. the ball is moving. is the ball at rest")
    assert r.lower() != "no match", "must reason about state, not default no-match"
    assert "moving" in r.lower() or re.search(r'\bno\b.*at rest', r.lower())


@xfail(strict=True, reason="kaala-logic: 'had N, now has M' count mutation via tense")
def test_kaala_count_had_has(vy):
    """'had 10 apples, has 7' — how many lost = 3 via tense"""
    r = vy.answer("he had 10 apples. he has 7 apples. how many apples were lost")
    assert "3" in r


@xfail(strict=True, reason="kaala-logic: boolean state override via tense")
def test_kaala_boolean_state_override(vy):
    """'light was off, light is on' → current state is on"""
    r = vy.answer("the light was off. the light is on. is the light on")
    assert "on" in r.lower() and "off" not in r.lower(), f"should say on, got: {r}"


@xfail(strict=True, reason="kaala-logic: location state change via tense")
def test_kaala_location_state(vy):
    """'was in room, is in garden' → current location is garden"""
    r = vy.answer("he was in the room. he is in the garden. where is he")
    assert "garden" in r.lower()
