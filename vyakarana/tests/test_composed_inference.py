"""test_composed_inference.py — compositional pancavayava inference.

Real reasoning composes the five members recursively:

  Multiple "we seek" — when answering requires intermediate results:
    "find KE, given mass and velocity" is one step.
    "find KE of ball-A, then compare to ball-B" is two seeks composed.

  Multiple "we know" — when the rule has layers:
    "which has more KE?" needs:
      we know: KE = ½mv²          (udaharana 1 — the formula)
      we know: greater KE → more  (udaharana 2 — the comparison rule)

  Nested "we see" — each application step is its own upanaya:
    "KE_A = ½×2×9 = 9"  (upanaya 1)
    "KE_B = ½×2×25 = 25" (upanaya 2)
    "9 < 25"              (upanaya 3 — the comparison)

The proof graph holds all intermediate results simultaneously.
The derive-step chain is exactly this composition: each step is one
more udaharana + upanaya. The emission walks the chain.

Run:
    cd /home/abe/agent_x && .venv/bin/pytest vyakarana/tests/test_composed_inference.py -v --socket /tmp/vy.sock
"""

import pytest


def answer(vy, sentence):
    return vy.eval(f'anuvada-ganana "{sentence}"')


# ── Section 1: chained physics (two seeks) ────────────────────────────────────
# The pipeline already handles derive-step chaining.
# These test that the emission shows BOTH steps of the chain.


def test_chain_shows_intermediate_result(vy):
    """v = u + at chain: intermediate velocity visible in reasoning."""
    r = answer(
        vy, "initial velocity is 0. acceleration is 10. time is 3. find velocity."
    )
    assert "30" in r, f"final velocity=30 missing: {r}"
    assert "we find" in r, f"we find missing: {r}"


@pytest.mark.xfail(
    strict=True,
    reason="Chained emission not implemented. When derive-step fires two rules "
    "(e.g. v=u+at then KE=½mv²), only the final result is emitted. "
    "Each intermediate step should appear as its own we-know/we-see pair.",
)
def test_chain_emits_both_knows(vy):
    """Two-step chain: both rules named in we-know."""
    r = answer(
        vy,
        "initial velocity is 0. acceleration is 10. time is 3. "
        "mass is 2. find kinetic energy.",
    )
    # step 1: v = u + at → v = 30
    # step 2: KE = ½mv² → KE = 900
    assert "900" in r, f"KE=900 missing: {r}"
    # both rules should appear in reasoning
    we_know_count = r.count("we know")
    assert we_know_count >= 2, (
        f"expected 2+ we-know strands for two-step chain, got {we_know_count}: {r}"
    )


def test_chain_emits_intermediate_in_we_see(vy):
    """Two-step chain: intermediate value visible in we-see."""
    r = answer(
        vy,
        "initial velocity is 0. acceleration is 10. time is 3. "
        "mass is 2. find kinetic energy.",
    )
    assert "900" in r, f"KE=900 missing: {r}"
    # velocity=30 should appear as an intermediate result
    assert "30" in r, f"intermediate velocity=30 missing from reasoning: {r}"


# ── Section 2: compute-then-compare (two seeks + viveka) ──────────────────────
# Requires: compute a derived quantity per entity, then compare.
# This is the hardest composition: physics chain + viveka.


@pytest.mark.xfail(
    strict=True,
    reason="Compute-then-compare not implemented. Viveka compares raw property "
    "values (first sankhya per entity) not derived quantities. "
    "Needs: run physics mantra per entity → derive KE_A and KE_B → viveka.",
)
def test_which_has_more_ke_shows_both_computations(vy):
    """ball-A (m=2,v=3) KE=9, ball-B (m=2,v=5) KE=25 — reasoning shows both."""
    r = answer(
        vy,
        "ball-A has mass 2 and velocity 3. "
        "ball-B has mass 2 and velocity 5. "
        "which has more kinetic energy.",
    )
    # both KE values should appear in reasoning
    assert "9" in r and "25" in r, f"both KE values missing: {r}"
    assert "ball-B" in r.split("we find")[-1], f"ball-B not the answer: {r}"


@pytest.mark.xfail(
    strict=True,
    reason="Same compute-then-compare gap. Reasoning should show: "
    "we seek: KE of each entity. we see: KE_A=9, KE_B=25. we find: ball-B has more.",
)
def test_which_has_more_ke_two_seeks(vy):
    """Compute-then-compare shows two seeks: KE of each entity."""
    r = answer(
        vy,
        "ball-A has mass 2 and velocity 3. "
        "ball-B has mass 2 and velocity 5. "
        "which has more kinetic energy.",
    )
    # should seek KE twice (once per entity)
    we_seek_count = r.count("we seek")
    assert we_seek_count >= 2, f"expected 2+ we-seek strands, got {we_seek_count}: {r}"


# ── Section 3: viveka with two knows ──────────────────────────────────────────
# "which is heavier?" needs two udaharana:
#   we know: greater mass means heavier
#   we know: (optionally) mass is a measure of matter
# Currently only one we-know fires.


def test_viveka_has_we_know(vy):
    """Viveka question has at least one we-know (udaharana)."""
    r = answer(vy, "ball-A has mass 5. ball-B has mass 3. which is heavier.")
    assert "we know" in r, f"we know missing: {r}"
    assert "mass" in r.split("we know")[-1].split("we see")[0], (
        f"mass not named in we-know: {r}"
    )


@pytest.mark.xfail(
    strict=True,
    reason="Viveka with compute: two udaharana needed. "
    "First: the formula for the derived quantity. "
    "Second: greater <quantity> means <comparative>. "
    "Currently only the comparison rule fires, not the formula.",
)
def test_viveka_computed_quantity_two_knows(vy):
    """Compute-then-compare: two we-know strands (formula + comparison rule)."""
    r = answer(
        vy,
        "ball-A has mass 2 and velocity 3. "
        "ball-B has mass 2 and velocity 5. "
        "which has more kinetic energy.",
    )
    we_know_count = r.count("we know")
    assert we_know_count >= 2, (
        f"expected 2 we-know (KE formula + comparison rule), got {we_know_count}: {r}"
    )


# ── Section 4: transitivity as composed inference ─────────────────────────────
# a > b, b > c → a > c is modus-ponens applied twice.
# Each application is one udaharana + upanaya.


@pytest.mark.xfail(
    strict=True,
    reason="Transitivity not implemented. 'a is greater than b. b is greater than c.' "
    "needs to emit [a, greater-than, b] and [b, greater-than, c] triples, "
    "then a transitivity-tantra walks the chain to derive [a, greater-than, c].",
)
def test_transitive_shows_chain_in_reasoning(vy):
    """Transitive inference: reasoning shows the chain a>b, b>c → a>c."""
    r = answer(vy, "a is greater than b. b is greater than c. is a greater than c.")
    assert "yes" in r.lower(), f"expected yes: {r}"
    # the chain should be visible
    assert "a" in r and "b" in r and "c" in r, f"chain members missing: {r}"


@pytest.mark.xfail(
    strict=True,
    reason="Transitivity emission: two we-know strands expected. "
    "we know: a > b (premise 1). we know: b > c (premise 2). "
    "we see: by transitivity. we find: a > c.",
)
def test_transitive_two_knows(vy):
    """Transitive inference emits two we-know (one per premise)."""
    r = answer(vy, "a is greater than b. b is greater than c. is a greater than c.")
    we_know_count = r.count("we know")
    assert we_know_count >= 2, (
        f"expected 2 we-know for two premises, got {we_know_count}: {r}"
    )


# ── Section 5: syllogism as composed inference ────────────────────────────────
# all cats are animals, all animals breathe → cats breathe.
# Two IS-A premises, one conclusion.
# Each premise is one we-know. The walk is one we-see.


@pytest.mark.xfail(
    strict=True,
    reason="Syllogism not implemented. Needs assertion-bandha to read "
    "'all X are Y' → [X, swarupa, Y] triples, then walk the chain.",
)
def test_syllogism_shows_premises_in_reasoning(vy):
    """Syllogism: reasoning shows both premises and the conclusion."""
    r = answer(vy, "all cats are animals. all animals breathe. do cats breathe.")
    assert "yes" in r.lower(), f"expected yes: {r}"
    # both premises should appear
    assert "cat" in r and "animal" in r and "breathe" in r, (
        f"premises missing from reasoning: {r}"
    )


@pytest.mark.xfail(
    strict=True,
    reason="Syllogism emission: two we-know strands (one per IS-A premise). "
    "we know: cats are animals. we know: animals breathe. "
    "we see: cat → animal → breathe. we find: yes.",
)
def test_syllogism_two_knows(vy):
    """Syllogism emits two we-know (one per IS-A premise)."""
    r = answer(vy, "all cats are animals. all animals breathe. do cats breathe.")
    we_know_count = r.count("we know")
    assert we_know_count >= 2, (
        f"expected 2 we-know for two premises, got {we_know_count}: {r}"
    )


# ── Section 6: count + comparison composition ─────────────────────────────────
# "i have 4 apples and 6 oranges — which is more?"
# Needs: count each group → compare totals.
# Two seeks composed.


@pytest.mark.xfail(
    strict=True,
    reason="Count + comparison not implemented. Viveka fires on the first "
    "sankhya values (4 vs 6) without recognising them as separate counts. "
    "Needs: count-bandha to bind each group, then viveka on the totals.",
)
def test_more_apples_or_oranges_shows_reasoning(vy):
    """4 apples vs 6 oranges: reasoning shows both counts then comparison."""
    r = answer(vy, "i have 4 apples and 6 oranges. do i have more apples or oranges.")
    assert "orange" in r.lower(), f"expected oranges: {r}"
    # both counts should appear
    assert "4" in r and "6" in r, f"both counts missing: {r}"
    assert "we find" in r, f"we find missing: {r}"
