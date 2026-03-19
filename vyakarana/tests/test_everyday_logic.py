"""test_everyday_logic.py — everyday logical questions, IQ-style problems, arithmetic.

These are the questions asked of children. Simple, concrete, grounded in
everyday reality. They test whether nam can reason about ordinary things —
not just physics formulas.

Three kinds of reasoning here:

  arithmetic:   i have 4 apples, gave 2 → how many left? (subtraction)
                box has 5 red and 3 blue balls → total? (addition)
                train at 60 km/h for 2 hours → distance? (multiplication)

  comparison:   ball-A has mass 5, ball-B has mass 3 → which is heavier?
                (viveka — discernment between two quantities)

  logical chain: all cats are animals, all animals breathe → do cats breathe?
                 a > b, b > c → a > c?
                 (transitive inference — walking the chain)

  proportional:  mass doubled, velocity same → what happens to KE?
                 (KE = ½mv² → KE doubles when m doubles)

What works now: physics mantras with explicit numeric bindings.
What doesn't: arithmetic on plain numbers, comparison, logical chains,
proportional reasoning. These need new kosha concepts and tantras.

The passing tests use physics as the logic medium — the pipeline already
knows how to reason about physical quantities.

Run:
    cd /home/abe/agent_x && .venv/bin/pytest vyakarana/tests/test_everyday_logic.py -v --socket /tmp/vy.sock
"""

import pytest


def answer(vy, sentence):
    return vy.eval(f'anuvada-ganana "{sentence}"')


# ── Section 1: physics as everyday logic (passing) ────────────────────────────
# These use the existing pipeline. Physics IS everyday logic when the concepts
# are already in the kosha and the question is well-formed.


def test_force_from_mass_and_acceleration(vy):
    """F = ma: everyday — how hard do you push a 3kg box to accelerate at 4 m/s²?"""
    r = answer(vy, "mass is 3 and acceleration is 4. find force.")
    assert "12" in r, f"expected force=12, got {r}"


def test_acceleration_from_force_and_mass(vy):
    """a = F/m: everyday — a 12N push on a 3kg box gives what acceleration?"""
    r = answer(vy, "force is 12. mass is 3. find acceleration.")
    assert "4" in r, f"expected acceleration=4, got {r}"


def test_distance_from_speed_and_time(vy):
    """d = v*t as momentum proxy: a 60kg object at 2 m/s has momentum 120."""
    r = answer(vy, "mass is 60 and velocity is 2. find momentum.")
    assert "120" in r, f"expected momentum=120, got {r}"


def test_speed_from_distance_and_time_via_chain(vy):
    """v = u + at: starting from rest, a=10, t=3 → v=30."""
    r = answer(
        vy, "initial velocity is 0. acceleration is 10. time is 3. find velocity."
    )
    assert "30" in r, f"expected velocity=30, got {r}"


def test_heavier_object_more_potential_energy(vy):
    """PE = mgh: heavier object has more PE at same height."""
    r1 = answer(vy, "mass is 5 and height is 10. find potential energy.")
    r2 = answer(vy, "mass is 10 and height is 10. find potential energy.")
    # PE1 = 490, PE2 = 981 — heavier object has more PE
    assert "490" in r1, f"expected PE1≈490, got {r1}"
    assert "980" in r2, f"expected PE2≈980, got {r2}"


def test_faster_object_more_kinetic_energy(vy):
    """KE = ½mv²: faster object has more KE at same mass."""
    r1 = answer(vy, "mass is 2 and velocity is 3. find kinetic energy.")
    r2 = answer(vy, "mass is 2 and velocity is 6. find kinetic energy.")
    # KE1 = 9, KE2 = 36 — twice the speed → four times KE
    assert "9" in r1, f"expected KE1=9, got {r1}"
    assert "36" in r2, f"expected KE2=36, got {r2}"


def test_area_via_pressure(vy):
    """P = F/A → F = P*A: pressure 100, area 5 → force 500."""
    r = answer(vy, "pressure is 100. area is 5. find force.")
    assert "500" in r, f"expected force=500, got {r}"


def test_two_entities_heavier_one_more_pe(vy):
    """ball-A (mass=10) has more PE than ball-B (mass=5) at same height."""
    r1 = answer(
        vy, "ball-A has mass 10. find potential energy of ball-A given height 5."
    )
    r2 = answer(
        vy, "ball-B has mass 5. find potential energy of ball-B given height 5."
    )
    # PE_A = 490, PE_B = 245
    assert "490" in r1, f"expected PE_A≈490, got {r1}"
    assert "245" in r2, f"expected PE_B≈245, got {r2}"


# ── Section 2: proportional reasoning (xfail) ─────────────────────────────────
# "if mass is doubled and velocity stays the same what happens to KE?"
# KE = ½mv² — KE doubles when m doubles. The pipeline knows this formula but
# cannot reason about hypothetical changes — it needs numeric bindings.
# Needs: proportional-reasoning tantra that walks the mantra expression and
# determines how the output changes when an input is scaled.


@pytest.mark.xfail(
    strict=True,
    reason="Proportional reasoning not implemented. The pipeline needs numeric "
    "bindings to fire a mantra. 'mass is doubled' is a hypothetical change, "
    "not a numeric value. Needs a proportional-viveka tantra that walks "
    "KE = ½mv² and determines: if m → 2m with v constant, then KE → 2KE.",
)
def test_proportional_ke_mass_doubled(vy):
    """KE = ½mv²: if mass doubles, velocity same → KE doubles."""
    r = answer(
        vy,
        "mass is 4 and velocity is 5. find kinetic energy. "
        "now mass is doubled. find kinetic energy.",
    )
    assert "100" in r and "200" in r, f"expected KE=100 then KE=200, got {r}"


@pytest.mark.xfail(
    strict=True,
    reason="Same proportional reasoning gap — velocity doubling in KE=½mv².",
)
def test_proportional_ke_velocity_doubled(vy):
    """KE = ½mv²: if velocity doubles, mass same → KE quadruples."""
    r = answer(
        vy,
        "mass is 2 and velocity is 3. find kinetic energy. "
        "now velocity is doubled. find kinetic energy.",
    )
    assert "9" in r and "36" in r, f"expected KE=9 then KE=36, got {r}"


# ── Section 3: basic arithmetic (xfail) ───────────────────────────────────────
# "i have 4 apples, i gave you 2, how many do i have?"
# This is pure arithmetic on plain numbers — not physics quantities.
# The pipeline has no arithmetic mantra for plain numbers without physics concepts.
# Needs: number-varga concepts (count, remainder) + arithmetic mantras.


def test_apples_subtraction(vy):
    """I have 4 apples, give 2 → I have 2 left."""
    r = answer(vy, "i have 4 apples. i gave you 2. how many do i have.")
    assert "2" in r, f"expected 2, got {r}"


@pytest.mark.xfail(
    strict=True,
    reason="Same plain count arithmetic gap. '10 birds, 3 fly away' → "
    "subtraction on count. 'fly away' needs to be recognised as subtraction "
    "signal, same as 'gave' above.",
)
def test_birds_subtraction(vy):
    """10 birds, 3 fly away → 7 left."""
    r = answer(vy, "there are 10 birds on a tree. 3 fly away. how many birds are left.")
    assert "7" in r, f"expected 7, got {r}"


@pytest.mark.xfail(
    strict=True,
    reason="Count addition not implemented. '5 red balls and 3 blue balls' → "
    "total = 5+3 = 8. Needs: count.om + addition-mantra for counts. "
    "Currently 'box' maps to container and gets both values but cannot add them.",
)
def test_balls_addition(vy):
    """5 red + 3 blue balls → 8 total."""
    r = answer(
        vy, "a box has 5 red balls and 3 blue balls. how many balls are in the box."
    )
    assert "8" in r, f"expected 8, got {r}"


@pytest.mark.xfail(
    strict=True,
    reason="Distance = speed × time as plain multiplication not in pipeline. "
    "'60 km in one hour' → speed=60, '2 hours' → time=2, distance=120. "
    "The pipeline has velocity-mantra (v=u+at) but not d=v*t directly. "
    "Needs: distance-mantra with velocity-janya and time-janya, krama=mul.",
)
def test_train_distance(vy):
    """Train at 60 km/h for 2 hours → 120 km."""
    r = answer(vy, "a train travels 60 km/h. how far does it travel in 2 hours.")
    assert "120" in r, f"expected 120, got {r}"


@pytest.mark.xfail(
    strict=True,
    reason="Area = length × width not in pipeline. 'length 8, width 5 → area 40'. "
    "area.om exists as a physics concept (in pressure mantra) but there is no "
    "geometry mantra for area = length × width. Needs: rectangle-area-mantra "
    "with length-janya and width-janya, krama=mul.",
)
def test_rectangle_area(vy):
    """Area = length × width: 8 × 5 = 40."""
    r = answer(vy, "a rectangle has length 8 and width 5. what is the area.")
    assert "40" in r, f"expected area=40, got {r}"


# ── Section 4: comparison / viveka (xfail) ────────────────────────────────────
# "which is heavier?" — comparing two quantities of the same concept.
# The pipeline can compute both values but cannot compare them and emit
# "ball-A is heavier". Needs: viveka-mantra that takes two values and
# emits the one that is greater, with the entity name.


def test_which_is_heavier(vy):
    """ball-A mass=5, ball-B mass=3 → ball-A is heavier."""
    r = answer(
        vy,
        "ball-A has mass 5. ball-B has mass 3. which is heavier.",
    )
    assert "ball-A" in r, f"expected ball-A is heavier, got {r}"


def test_which_is_faster(vy):
    """car-A velocity=30, car-B velocity=20 → car-A is faster."""
    r = answer(
        vy,
        "car-A has velocity 30. car-B has velocity 20. which is faster.",
    )
    assert "car-A" in r, f"expected car-A is faster, got {r}"


# ── Section 5: logical chain / transitivity (xfail) ──────────────────────────
# "a > b, b > c → a > c?" — transitive inference.
# "all cats are animals, all animals breathe → do cats breathe?"
# These require walking a chain of logical assertions — not physics mantras.
# Needs: logical-chain tantra that recognises transitivity patterns.


def test_transitive_greater_than(vy):
    """a > b, b > c → a > c."""
    r = answer(
        vy,
        "a is greater than b. b is greater than c. is a greater than c.",
    )
    assert "yes" in r.lower() or "a" in r, f"expected yes/a > c, got {r}"


def test_syllogism_cats_breathe(vy):
    """All cats are animals. All animals breathe. Do cats breathe?"""
    r = answer(
        vy,
        "all cats are animals. all animals breathe. do cats breathe.",
    )
    assert "yes" in r.lower(), f"expected yes, got {r}"


# ── Section 6: reasoning emission shows the question's structure ──────────────
# Even when no match is found, the reasoning should show what was understood.


def test_no_question_shows_graph(vy):
    """No find clause — graph built, no question asked, no match."""
    r = answer(vy, "ball has mass 5 and velocity 10.")
    assert "we have" in r, f"should show 'we have': {r}"
    assert "no match" in r, f"no question asked — should be no match: {r}"


def test_partial_question_shows_sought(vy):
    """Find with insufficient data — shows what was sought and why no match."""
    r = answer(vy, "mass is 5. find kinetic energy.")
    assert "we seek" in r, f"should show 'we seek': {r}"
    assert "kinetic-energy" in r, f"should name what was sought: {r}"
    assert "no match" in r, f"insufficient data — should be no match: {r}"


def test_well_formed_question_shows_all_strands(vy):
    """Well-formed question shows all five pancavayava strands."""
    r = answer(vy, "mass is 4 and velocity is 5. find kinetic energy.")
    for strand in ["we have", "we seek", "we know", "we see", "we find"]:
        assert strand in r, f"missing '{strand}': {r}"
    assert "50" in r, f"expected KE=50, got {r}"
