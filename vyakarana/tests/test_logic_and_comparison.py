"""test_logic_and_comparison.py — comparison, transitivity, syllogism, combined.

These tests document the gap between what the pipeline currently produces
(graph structure is correct) and what it needs to emit (named winner, yes/no,
ranked order).

The graph trace shows the data is already there:
  "ball-A has mass 5. ball-B has mass 3. which is heavier."
  → both entities in graph with prathama-vibhakti
  → both mass sankhya values bound
  → heavier has vishesa→mass (the comparison concept is named)
  → just needs: walk both entity-owned values, gt → name the winner

The logic kosha already has modus-ponens, implication, inference declared.
The gap is the pipeline never dispatches to them.

Sections:
  1. Comparison (viveka) — which entity has more of a property
  2. Comparison + computation — compute then compare
  3. Transitivity — a>b, b>c → a>c (modus-ponens on a relation chain)
  4. Syllogism — IS-A chain + predicate inheritance
  5. Combined — logic + arithmetic + physics together

Run:
    cd /home/abe/agent_x && .venv/bin/pytest vyakarana/tests/test_logic_and_comparison.py -v --socket /tmp/vy.sock
"""

import pytest


def answer(vy, sentence):
    return vy.eval(f'anuvada-ganana "{sentence}"')


# ── Section 1: Comparison / viveka ────────────────────────────────────────────
# The graph already has both entities + both values bound.
# Missing: a comparison-mantra that walks entity-owned values of the same
# concept, applies gt/lt, and names the winning entity.
#
# Graph trace confirms:
#   "ball-A has mass 5. ball-B has mass 3. which is heavier."
#   → [ball-A, prathama-vibhakti, object], [mass, sankhya, 5.]
#   → [ball-B, prathama-vibhakti, object], [mass, sankhya, 3.]
#   → [heavier, vishesa, mass]   ← comparison concept names the property
#   → solve-for = mass, two entities present → comparison dispatch needed


def test_which_is_heavier(vy):
    """ball-A mass=5, ball-B mass=3 → ball-A is heavier."""
    r = answer(vy, "ball-A has mass 5. ball-B has mass 3. which is heavier.")
    assert "ball-A" in r, f"expected ball-A, got {r}"


def test_which_is_faster(vy):
    """car-A velocity=30, car-B velocity=20 → car-A is faster."""
    r = answer(vy, "car-A has velocity 30. car-B has velocity 20. which is faster.")
    assert "car-A" in r, f"expected car-A, got {r}"


def test_which_has_more_ke(vy):
    """object-A KE=50, object-B KE=20 → object-A has more kinetic energy."""
    r = answer(
        vy,
        "object-A has kinetic-energy 50. object-B has kinetic-energy 20. "
        "which has more kinetic energy.",
    )
    assert "object-A" in r, f"expected object-A, got {r}"


def test_which_is_heaviest_three(vy):
    """ball-A=5, ball-B=3, ball-C=8 → ball-C is heaviest."""
    r = answer(
        vy,
        "ball-A has mass 5. ball-B has mass 3. ball-C has mass 8. which is heaviest.",
    )
    assert "we find" in r and "ball-C" in r.split("we find")[-1], (
        f"expected ball-C as answer, got {r}"
    )


def test_which_is_lightest(vy):
    """ball-A=5, ball-B=3 → ball-B is lightest."""
    r = answer(vy, "ball-A has mass 5. ball-B has mass 3. which is lightest.")
    assert "ball-B" in r, f"expected ball-B, got {r}"


# ── Section 2: Comparison after computation ───────────────────────────────────
# Compute a derived quantity for each entity, then compare.
# Requires: viveka-mantra that first computes (e.g. KE) per entity then picks max.
# This is comparison + physics pipeline chained.


@pytest.mark.xfail(
    strict=True,
    reason="Compute-then-compare not implemented. Pipeline computes one entity's KE "
    "(whichever values it picks up) but cannot compute both and compare. "
    "Currently 'ball-B' appears in 'we have' strand, not as the answer.",
)
def test_which_has_more_ke_from_mass_velocity(vy):
    """ball-A (m=2,v=3) KE=9, ball-B (m=2,v=5) KE=25 → ball-B has more KE."""
    r = answer(
        vy,
        "ball-A has mass 2 and velocity 3. "
        "ball-B has mass 2 and velocity 5. "
        "which has more kinetic energy.",
    )
    # ball-B must appear as the answer — not just in 'we have'
    assert "we find" in r and "ball-B" in r.split("we find")[-1], (
        f"expected ball-B as answer, got {r}"
    )


@pytest.mark.xfail(
    strict=True,
    reason="Compute-then-compare not implemented. Viveka compares the first sankhya "
    "per entity (velocity: 4 vs 7) instead of computing momentum (p=mv: 12 vs 14) "
    "first. Needs: compute momentum per entity, then viveka on those derived values.",
)
def test_which_has_more_momentum(vy):
    """ball-A (m=3,v=4) p=12, ball-B (m=2,v=7) p=14 → ball-B has more momentum."""
    r = answer(
        vy,
        "ball-A has mass 3 and velocity 4. "
        "ball-B has mass 2 and velocity 7. "
        "which has more momentum.",
    )
    # ball-B must be the winner — it appears BEFORE "than" in we-find
    found = r.split("we find")[-1] if "we find" in r else ""
    ball_b_pos = found.find("ball-B")
    than_pos = found.find(" than ")
    assert (
        "we find" in r and ball_b_pos >= 0 and (than_pos < 0 or ball_b_pos < than_pos)
    ), f"expected ball-B as winner (before 'than'), got {r}"


# ── Section 3: Transitivity ────────────────────────────────────────────────────
# a > b, b > c → a > c.
# This is modus-ponens on a greater-than chain.
# The logic kosha has modus-ponens declared but it is never dispatched to.
# Needs: assertion-bandha to read "a is greater than b" →
#   [a, greater-than, b] triple in graph, then transitivity walk.


@pytest.mark.xfail(
    strict=True,
    reason="Transitivity not implemented. 'a is greater than b' needs to emit "
    "[a, greater-than, b] in the graph. Then a transitivity-tantra walks "
    "the chain: [a,>b] + [b,>c] → [a,>c]. This IS modus-ponens on > edges. "
    "The logic kosha has modus-ponens but it is never dispatched to.",
)
def test_transitive_greater_than(vy):
    """a > b, b > c → a > c."""
    r = answer(vy, "a is greater than b. b is greater than c. is a greater than c.")
    # "a" is a substring of many words — require "yes" explicitly
    assert "yes" in r.lower(), f"expected yes, got {r}"


@pytest.mark.xfail(
    strict=True,
    reason="Same transitivity gap with named entities and masses.",
)
def test_transitive_mass_ordering(vy):
    """ball-A heavier than ball-B, ball-B heavier than ball-C → ball-A heaviest."""
    r = answer(
        vy,
        "ball-A is heavier than ball-B. ball-B is heavier than ball-C. "
        "which is heaviest.",
    )
    assert "ball-A" in r, f"expected ball-A, got {r}"


@pytest.mark.xfail(
    strict=True,
    reason="Three-step transitivity chain.",
)
def test_transitive_chain_three_steps(vy):
    """a > b, b > c, c > d → a > d."""
    r = answer(
        vy,
        "a is greater than b. b is greater than c. c is greater than d. "
        "is a greater than d.",
    )
    assert "yes" in r.lower(), f"expected yes, got {r}"


# ── Section 4: Syllogism / IS-A chain ─────────────────────────────────────────
# all cats are animals, all animals breathe → cats breathe.
# The kosha already has swarupa/varga IS-A edges for physics concepts.
# The pipeline needs: assertion-bandha to read "all X are Y" →
#   [X, swarupa, Y] in graph, then syllogism-mantra walks the chain.


@pytest.mark.xfail(
    strict=True,
    reason="Syllogism not implemented. 'all cats are animals' needs to emit "
    "[cat, swarupa, animal]. 'all animals breathe' → [animal, swarupa, breathe]. "
    "Then syllogism-mantra walks: cat→animal→breathe → cat breathes. "
    "This IS modus-ponens on swarupa edges — the logic kosha has it declared.",
)
def test_syllogism_cats_breathe(vy):
    """All cats are animals. All animals breathe. Do cats breathe?"""
    r = answer(vy, "all cats are animals. all animals breathe. do cats breathe.")
    assert "yes" in r.lower(), f"expected yes, got {r}"


@pytest.mark.xfail(
    strict=True,
    reason="Same syllogism gap — dogs and mammals.",
)
def test_syllogism_dogs_mammals(vy):
    """All dogs are mammals. All mammals have hearts. Do dogs have hearts?"""
    r = answer(
        vy,
        "all dogs are mammals. all mammals have hearts. do dogs have hearts.",
    )
    assert "yes" in r.lower(), f"expected yes, got {r}"


@pytest.mark.xfail(
    strict=True,
    reason="Syllogism using kosha IS-A edges directly — no assertion needed. "
    "electron swarupa particle already in kosha. particle has mass already declared. "
    "Pipeline should walk the existing edge without being told in the question.",
)
def test_syllogism_from_kosha_electron_is_particle(vy):
    """electron IS-A particle (kosha edge). particle has mass. does electron have mass?"""
    r = answer(vy, "particles have mass. does an electron have mass.")
    assert "yes" in r.lower(), f"expected yes (electron swarupa particle), got {r}"


# ── Section 5: Combined — logic + arithmetic + physics ────────────────────────
# These are the questions that unlock once all three layers work together.
# They mirror real everyday reasoning.


@pytest.mark.xfail(
    strict=True,
    reason="Combined: count arithmetic + comparison. Count each group then compare. "
    "Needs count-bandha (done) + viveka on the two totals.",
)
def test_more_apples_or_oranges(vy):
    """4 apples and 6 oranges — which is more?"""
    r = answer(vy, "i have 4 apples and 6 oranges. do i have more apples or oranges.")
    assert "orange" in r.lower(), f"expected oranges, got {r}"


@pytest.mark.xfail(
    strict=True,
    reason="Combined: syllogism + count. All birds have wings. 3 animals are birds. "
    "How many have wings? Needs syllogism (birds→wings) + count subset.",
)
def test_syllogism_plus_count(vy):
    """All birds have wings. 3 of 10 animals are birds. How many have wings?"""
    r = answer(
        vy,
        "all birds have wings. there are 10 animals. 3 are birds. "
        "how many animals have wings.",
    )
    # Must find exactly 3, not 13 (which is 10+3 from count-add)
    assert "we find" in r and "= 3" in r, f"expected answer=3, got {r}"


@pytest.mark.xfail(
    strict=True,
    reason="Combined: transitivity + physics. ball-A heavier than ball-B "
    "(from masses), ball-B heavier than ball-C → rank them. "
    "Needs comparison to emit greater-than edges, then transitivity to rank.",
)
def test_rank_three_balls_by_mass(vy):
    """ball-A=5, ball-B=3, ball-C=1 → rank: ball-A > ball-B > ball-C."""
    r = answer(
        vy,
        "ball-A has mass 5. ball-B has mass 3. ball-C has mass 1. rank them by mass.",
    )
    # ball-A must appear before ball-C as the ordered ranking answer
    assert (
        "we find" in r
        and "ball-A" in r.split("we find")[-1]
        and "ball-C" in r.split("we find")[-1]
        and r.index("ball-A") < r.index("ball-C")
    ), f"expected ball-A before ball-C in ranking answer, got {r}"
