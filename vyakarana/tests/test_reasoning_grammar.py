"""test_reasoning_grammar.py — grammar quality of the reasoning emission.

The reasoning speaks in uttama-purusa-bahu-vachana kartari-prayoga:
first-person-inclusive-plural active voice — "we have, we seek, we find."

These tests verify that the grammar is correct and complete:
  - entities are named with their properties (ball-A with mass=5)
  - plural conjunction ("ball-A and ball-B", not "ball-A; ball-B" in we-have)
  - viveka answers name the winner WITH the comparative ("ball-A is heavier")
  - viveka seeks name the question correctly ("which is heavier")
  - physics answers show concept = value with unit

Run:
    cd /home/abe/agent_x && .venv/bin/pytest vyakarana/tests/test_reasoning_grammar.py -v --socket /tmp/vy.sock
"""

import pytest


def answer(vy, sentence):
    return vy.eval(f'anuvada-ganana "{sentence}"')


# ── Section 1: entity grouping in "we have" ───────────────────────────────────


def test_single_entity_named_in_we_have(vy):
    """Single entity: 'we have: ball-A (mass=5., velocity=10.)'"""
    r = answer(vy, "ball-A has mass 5 and velocity 10. find kinetic energy of ball-A.")
    assert "ball-A" in r, f"entity name missing: {r}"
    assert "we have" in r, f"we have missing: {r}"
    # ball-A should appear grouped with its properties
    we_have = (
        r.split("we have")[-1].split("we seek")[0]
        if "we seek" in r
        else r.split("we have")[-1]
    )
    assert "ball-A" in we_have, f"ball-A not in we-have section: {r}"


def test_two_entities_both_named_in_we_have(vy):
    """Two entities both appear in we-have with their values."""
    r = answer(vy, "ball-A has mass 5. ball-B has mass 3. which is heavier.")
    assert "ball-A" in r, f"ball-A missing: {r}"
    assert "ball-B" in r, f"ball-B missing: {r}"
    we_have = (
        r.split("we have")[-1].split("we seek")[0]
        if "we seek" in r
        else r.split("we have")[-1]
    )
    assert "ball-A" in we_have and "ball-B" in we_have, (
        f"both entities not in we-have: {r}"
    )
    assert "5" in we_have and "3" in we_have, f"values missing from we-have: {r}"


def test_viveka_we_have_entity_grouped(vy):
    """Viveka we-have should group values by entity: 'ball-A (mass=5.) and ball-B (mass=3.)'"""
    r = answer(vy, "ball-A has mass 5. ball-B has mass 3. which is heavier.")
    we_have = (
        r.split("we have")[-1].split("we seek")[0]
        if "we seek" in r
        else r.split("we have")[-1]
    )
    # both entities should appear with their values grouped
    assert (
        "ball-A" in we_have and "5" in we_have.split("ball-A")[1].split("ball-B")[0]
    ), f"ball-A not grouped with mass=5: {r}"
    assert "ball-B" in we_have and "3" in we_have.split("ball-B")[1], (
        f"ball-B not grouped with mass=3: {r}"
    )


# ── Section 2: "we seek" for viveka ───────────────────────────────────────────


def test_viveka_we_seek_names_comparison(vy):
    """Viveka we-seek should say what is being compared, not just the concept."""
    r = answer(vy, "ball-A has mass 5. ball-B has mass 3. which is heavier.")
    assert "we seek" in r, f"we seek missing: {r}"
    sought = (
        r.split("we seek")[-1].split("we find")[0]
        if "we find" in r
        else r.split("we seek")[-1]
    )
    # should name the comparison, not just "mass"
    assert "heavier" in sought or "greater" in sought or "which" in sought, (
        f"comparison intent not in we-seek: {r}"
    )


# ── Section 3: "we find" for viveka ───────────────────────────────────────────


def test_viveka_we_find_names_winner_with_comparative(vy):
    """Viveka we-find should say 'ball-A is heavier', not just 'ball-A'."""
    r = answer(vy, "ball-A has mass 5. ball-B has mass 3. which is heavier.")
    assert "we find" in r, f"we find missing: {r}"
    found = r.split("we find")[-1]
    assert "ball-A" in found and "heavier" in found, (
        f"winner not named with comparative in we-find: {r}"
    )


def test_viveka_min_we_find_names_winner_with_comparative(vy):
    """Min viveka we-find should say 'ball-B is lighter'."""
    r = answer(vy, "ball-A has mass 5. ball-B has mass 3. which is lighter.")
    assert "we find" in r, f"we find missing: {r}"
    found = r.split("we find")[-1]
    assert "ball-B" in found and "lighter" in found, (
        f"winner not named with comparative in we-find: {r}"
    )


def test_viveka_three_entity_we_find(vy):
    """Three entities: we-find should say 'ball-C is heaviest'."""
    r = answer(
        vy,
        "ball-A has mass 5. ball-B has mass 3. ball-C has mass 8. which is heaviest.",
    )
    assert "we find" in r, f"we find missing: {r}"
    found = r.split("we find")[-1]
    assert "ball-C" in found and "heaviest" in found, (
        f"winner not named with superlative in we-find: {r}"
    )


# ── Section 4: physics reasoning grammar ──────────────────────────────────────


def test_physics_we_find_has_equals(vy):
    """Physics we-find: 'we find: force = 12'"""
    r = answer(vy, "mass is 3 and acceleration is 4. find force.")
    assert "we find" in r, f"we find missing: {r}"
    found = r.split("we find")[-1]
    assert "force" in found and "12" in found, f"force=12 not in we-find: {r}"


def test_physics_we_know_names_mantra(vy):
    """Physics we-know (udaharana) names the mantra and its rule."""
    r = answer(vy, "mass is 3 and acceleration is 4. find force.")
    assert "we know" in r, f"we know missing: {r}"
    assert "newton-second-law-motion" in r, f"mantra name missing: {r}"


def test_physics_we_see_shows_substitution(vy):
    """Physics we-see (upanaya) shows the specific values applied."""
    r = answer(vy, "mass is 3 and acceleration is 4. find force.")
    assert "we see" in r, f"we see missing: {r}"
    seen = r.split("we see")[-1].split("we find")[0]
    assert "3" in seen and "4" in seen, f"values not shown in we-see: {r}"


def test_physics_all_five_strands(vy):
    """Well-formed physics question shows all five pancavayava strands."""
    r = answer(vy, "mass is 4 and velocity is 5. find kinetic energy.")
    for strand in ["we have", "we seek", "we know", "we see", "we find"]:
        assert strand in r, f"missing strand '{strand}': {r}"
    assert "50" in r, f"KE=50 not in result: {r}"


# ── Section 5: count arithmetic grammar ───────────────────────────────────────


def test_count_add_we_find_names_total(vy):
    """Count addition we-find should name the total."""
    r = answer(vy, "i have 4 apples and 3 oranges how many total.")
    assert "we find" in r, f"we find missing: {r}"
    assert "7" in r, f"total=7 not in result: {r}"


def test_count_sub_we_find_names_remaining(vy):
    """Count subtraction we-find should name what remains."""
    r = answer(vy, "i have 10 apples i gave away 3 how many remaining.")
    assert "we find" in r, f"we find missing: {r}"
    assert "7" in r, f"remaining=7 not in result: {r}"


# ── Section 6: conjunction in plural we-have ──────────────────────────────────


def test_two_entities_joined_with_and(vy):
    """Two entities in we-have joined with 'and', not just ';'."""
    r = answer(
        vy,
        "ball-A has mass m1 of 5 and velocity v1 of 10. ball-B has mass m2 of 3 and velocity v2 of 4. find kinetic energy of ball-A.",
    )
    we_have = (
        r.split("we have")[-1].split("we seek")[0]
        if "we seek" in r
        else r.split("we have")[-1]
    )
    assert " and " in we_have, f"'and' conjunction missing in we-have: {r}"


def test_three_entities_oxford_comma(vy):
    """Three entities: 'ball-A, ball-B, and ball-C' in we-have."""
    r = answer(
        vy,
        "ball-A has mass 5. ball-B has mass 3. ball-C has mass 8. which is heaviest.",
    )
    we_have = (
        r.split("we have")[-1].split("we seek")[0]
        if "we seek" in r
        else r.split("we have")[-1]
    )
    assert "ball-A" in we_have and "ball-B" in we_have and "ball-C" in we_have, (
        f"not all entities in we-have: {r}"
    )
    assert " and " in we_have, f"'and' conjunction missing for last entity: {r}"
