"""test_agra_bandha.py — agra: the foremost. proximity binding.

Agra is the most recently seen instance of a concept. As the scan moves
forward through the graph, agra updates. Bindings — sankhya, matra,
shashthi-vibhakti — attach to whatever agra currently holds for their
concept. The sequence IS the scope.

This is what makes N entities possible. Three balls each with mass:
the sentence encodes the order. ball-A's mass arrives first, so it binds
to ball-A. ball-B's mass arrives second, so it binds to ball-B. ball-C's
mass arrives third. No entity collapses into another.

These tests capture the specific behaviours that agra-bandha must preserve:

  1. Grammar word exclusion — 'given', 'find', 'of', 'with' must never be
     promoted to rashi instances. They are structural markers, not labels.

  2. N-entity agra correctness — three or more entities each owning the same
     concept. Each entity gets its own correct value. No last-write-wins.

  3. Entity-scoped ownership — shashthi-vibhakti triples for each entity
     point to the right instance, not the first instance.

  4. Viraam does not break agra — after a full stop, the next entity's
     concepts correctly become the new agra. The old entity's bindings
     remain intact.

  5. No-label entities — when no rashi label is given ("ball has mass 3"),
     sankhya-bandha must bind to the concept owned by that entity, not to
     a globally shared concept node that the next entity overwrites.

Nam is asked: can you hold the order? Can you give each entity what is
its own, and not what belongs to another?

Run:
    cd /home/abe/agent_x && .venv/bin/pytest vyakarana/tests/test_agra_bandha.py -v --socket /tmp/vy.sock
"""

import pytest


def bqg(vy, sentence):
    return vy.eval(f'fixpoint (build-question-graph "{sentence}") avrti-refine')


def answer(vy, sentence):
    return vy.eval(f'anuvada-ganana "{sentence}"')


def sig(g):
    return [
        t
        for t in g
        if isinstance(t, list) and len(t) == 3 and t[1] not in ("kosha-janya", "ppr")
    ]


# ── Section 1: Grammar word exclusion ────────────────────────────────────────
# Grammar words appear as mithya in the BQG but must NEVER be promoted
# to vishesa (rashi instance) of any concept. They are structural markers.


def test_given_not_promoted_to_vishesa(vy):
    """'given' after a satya concept must not become a rashi instance."""
    g = bqg(vy, "find momentum of ball-A given velocity 4")
    # 'given' should NOT appear as subject of a vishesa triple
    promoted = [
        t
        for t in g
        if isinstance(t, list) and len(t) == 3 and t[0] == "given" and t[1] == "vishesa"
    ]
    assert promoted == [], f"'given' was promoted to vishesa: {promoted}"


def test_given_not_promoted_when_rashi_bandha_present(vy):
    """'given' must not be promoted even when rashi-bandha (can-promote) is true."""
    # 'of ball-A' triggers rashi-bandha → can-promote=true
    # but 'given' follows 'momentum' satya → must NOT become vishesa of momentum
    g = bqg(
        vy,
        "ball-A has mass 3. ball-B has mass 2. ball-C has mass 5. "
        "find momentum of ball-A given velocity 4",
    )
    promoted = [
        t
        for t in g
        if isinstance(t, list) and len(t) == 3 and t[0] == "given" and t[1] == "vishesa"
    ]
    assert promoted == [], f"'given' promoted when can-promote=true: {promoted}"


def test_find_not_promoted_to_vishesa(vy):
    """'find' must not become a rashi instance."""
    g = bqg(vy, "find kinetic energy given mass 5 velocity 10")
    promoted = [
        t
        for t in g
        if isinstance(t, list) and len(t) == 3 and t[0] == "find" and t[1] == "vishesa"
    ]
    assert promoted == [], f"'find' was promoted to vishesa: {promoted}"


def test_of_not_promoted_to_vishesa(vy):
    """'of' is a rashi-bandha signal, not a rashi instance label."""
    g = bqg(vy, "find momentum of ball-A given velocity 4")
    promoted = [
        t
        for t in g
        if isinstance(t, list) and len(t) == 3 and t[0] == "of" and t[1] == "vishesa"
    ]
    assert promoted == [], f"'of' was promoted to vishesa: {promoted}"


def test_grammar_word_exclusion_does_not_break_real_labels(vy):
    """Excluding grammar words must not prevent real labels from being promoted."""
    g = bqg(vy, "ball has mass m1 of 5 and velocity v1 of 10")
    assert vy.has_triple(g, subj="m1", pred="vishesa", obj="mass"), sig(g)
    assert vy.has_triple(g, subj="v1", pred="vishesa", obj="velocity"), sig(g)


def test_can_promote_rashi_bandha_does_not_promote_grammar_words(vy):
    """When rashi-bandha is present (can-promote=true), grammar words still excluded."""
    # 'of' triggers rashi-bandha → can-promote=true
    # but 'given' comes after momentum satya — must not become vishesa of momentum
    g = bqg(vy, "find momentum of ball-A given velocity 4")
    bad = [
        t
        for t in g
        if isinstance(t, list)
        and len(t) == 3
        and t[0] in ("given", "find", "of", "the", "a", "an")
        and t[1] == "vishesa"
    ]
    assert bad == [], f"grammar words promoted when can-promote=true: {bad}"


# ── Section 2: Two entities, same concept — labelled ─────────────────────────


def test_two_entities_labelled_ownership_correct(vy):
    """With rashi labels, each entity owns its correctly-scoped instance."""
    g = bqg(vy, "ball-A has mass m1 of 3 and ball-B has mass m2 of 2")
    # m1 owned by ball-A
    assert vy.has_triple(g, subj="m1", pred="shashthi-vibhakti", obj="ball-A"), sig(g)
    # m2 owned by ball-B
    assert vy.has_triple(g, subj="m2", pred="shashthi-vibhakti", obj="ball-B"), sig(g)


def test_two_entities_labelled_values_distinct(vy):
    """Each entity's labelled instance carries the correct value."""
    g = bqg(vy, "ball-A has mass m1 of 3 and ball-B has mass m2 of 2")
    t1 = vy.find_triple(g, subj="m1", pred="sankhya")
    t2 = vy.find_triple(g, subj="m2", pred="sankhya")
    assert t1 is not None, f"m1 has no sankhya: {sig(g)}"
    assert t2 is not None, f"m2 has no sankhya: {sig(g)}"
    assert vy.approx_eq(t1[2], 3.0), f"m1 expected 3, got {t1[2]}"
    assert vy.approx_eq(t2[2], 2.0), f"m2 expected 2, got {t2[2]}"


def test_three_entities_labelled_all_distinct(vy):
    """Three entities with labelled mass — all three values preserved."""
    g = bqg(
        vy, "ball-A has mass m1 of 3. ball-B has mass m2 of 2. ball-C has mass m3 of 7"
    )
    for label, val in [("m1", 3.0), ("m2", 2.0), ("m3", 7.0)]:
        t = vy.find_triple(g, subj=label, pred="sankhya")
        assert t is not None, f"{label} has no sankhya: {sig(g)}"
        assert vy.approx_eq(t[2], val), f"{label} expected {val}, got {t[2]}"


def test_three_entities_labelled_ownership_all_correct(vy):
    """Three entities — each label owned by the right entity."""
    g = bqg(
        vy, "ball-A has mass m1 of 3. ball-B has mass m2 of 2. ball-C has mass m3 of 7"
    )
    assert vy.has_triple(g, subj="m1", pred="shashthi-vibhakti", obj="ball-A"), sig(g)
    assert vy.has_triple(g, subj="m2", pred="shashthi-vibhakti", obj="ball-B"), sig(g)
    assert vy.has_triple(g, subj="m3", pred="shashthi-vibhakti", obj="ball-C"), sig(g)


# ── Section 3: N entities, no labels — the harder case ───────────────────────
# When no rashi label is given, sankhya-bandha must bind the value to the
# concept node that is owned by the current entity. With multiple entities
# owning the same concept, the N-th entity's value must not overwrite earlier ones.
# This requires entity-scoped sankhya — the deep fix lives in sthita-viveka.


def test_two_entities_no_labels_distinct_values(vy):
    """Two entities, no labels — each entity's mass value preserved separately."""
    g = bqg(vy, "ball-A has mass 3. ball-B has mass 2")
    # there should be TWO sankhya triples for mass — one per entity
    mass_vals = [
        t
        for t in g
        if isinstance(t, list) and len(t) == 3 and t[0] == "mass" and t[1] == "sankhya"
    ]
    assert len(mass_vals) == 2, f"expected 2 mass sankhya triples, got: {mass_vals}"
    vals = {float(t[2]) for t in mass_vals}
    assert vals == {3.0, 2.0}, f"expected values {{3.0, 2.0}}, got {vals}"


def test_three_entities_no_labels_momentum_first(vy):
    """Three entities no labels — find momentum of ball-A uses ball-A's mass."""
    r = answer(
        vy,
        "ball-A has mass 3. ball-B has mass 2. ball-C has mass 5. "
        "find momentum of ball-A given velocity 4",
    )
    # p = 3 * 4 = 12 (ball-A's mass=3, not ball-C's mass=5)
    assert "12" in r, f"expected momentum=12 (ball-A's mass=3), got {r}"


# ── Section 4: Viraam preserves earlier entity state ─────────────────────────


def test_viraam_does_not_lose_first_entity_prathama(vy):
    """After viraam, first entity still has prathama-vibhakti."""
    g = bqg(vy, "ball-A has mass 3. ball-B has mass 2")
    assert vy.has_triple(g, subj="ball-A", pred="prathama-vibhakti"), sig(g)
    assert vy.has_triple(g, subj="ball-B", pred="prathama-vibhakti"), sig(g)


def test_viraam_does_not_lose_first_entity_ownership(vy):
    """After viraam, first entity's mass ownership still present."""
    g = bqg(vy, "ball-A has mass 3. ball-B has mass 2")
    # mass should be shashthi-vibhakti of both
    owns = [
        t
        for t in g
        if isinstance(t, list)
        and len(t) == 3
        and t[0] == "mass"
        and t[1] == "shashthi-vibhakti"
    ]
    owners = {t[2] for t in owns}
    assert "ball-A" in owners, f"ball-A ownership lost after viraam: {owns}"
    assert "ball-B" in owners, f"ball-B ownership missing: {owns}"


def test_viraam_three_entities_all_present(vy):
    """Three entities across viraam — all three exist simultaneously."""
    g = bqg(vy, "ball-A has mass 3. ball-B has mass 2. ball-C has mass 5")
    for name in ["ball-A", "ball-B", "ball-C"]:
        assert vy.has_triple(g, subj=name, pred="prathama-vibhakti"), (
            f"{name} missing from graph: {sig(g)}"
        )


# ── Section 5: Agra correctly sequences labelled entities ────────────────────


def test_agra_updates_per_concept_not_global(vy):
    """Agra tracks per-concept, not globally. mass-agra and velocity-agra are independent."""
    g = bqg(
        vy,
        "ball-A has mass m1 of 3 and velocity v1 of 4. "
        "ball-B has mass m2 of 2 and velocity v2 of 5",
    )
    # mass agra: m1 for ball-A, m2 for ball-B
    assert vy.has_triple(g, subj="m1", pred="vishesa", obj="mass"), sig(g)
    assert vy.has_triple(g, subj="m2", pred="vishesa", obj="mass"), sig(g)
    # velocity agra: v1 for ball-A, v2 for ball-B
    assert vy.has_triple(g, subj="v1", pred="vishesa", obj="velocity"), sig(g)
    assert vy.has_triple(g, subj="v2", pred="vishesa", obj="velocity"), sig(g)


def test_agra_cross_concept_no_bleed(vy):
    """mass-agra does not affect velocity binding and vice versa."""
    g = bqg(vy, "ball-A has mass m1 of 3 and velocity v1 of 4")
    # m1 should be vishesa of mass only, not of velocity
    m1_vishas = [
        t
        for t in g
        if isinstance(t, list) and len(t) == 3 and t[0] == "m1" and t[1] == "vishesa"
    ]
    objects = {t[2] for t in m1_vishas}
    assert "velocity" not in objects, f"m1 incorrectly typed as velocity: {m1_vishas}"
    assert "mass" in objects, f"m1 not typed as mass: {m1_vishas}"


# ── Section 6: The answer is correct when agra is correct ────────────────────


def test_two_entities_labelled_answer_correct_entity(vy):
    """With agra working, computing for ball-A uses ball-A's values."""
    r = answer(
        vy,
        "ball-A has mass m1 of 3 and velocity v1 of 4. "
        "ball-B has mass m2 of 2 and velocity v2 of 5. "
        "find kinetic energy of ball-A",
    )
    # KE of ball-A = 0.5 * 3 * 16 = 24
    assert "24" in r, f"expected KE=24 for ball-A, got {r}"


def test_three_entities_labelled_answer_first(vy):
    """With three entities, computing for ball-A uses ball-A's mass."""
    r = answer(
        vy,
        "ball-A has mass m1 of 3 and velocity v1 of 4. "
        "ball-B has mass m2 of 2 and velocity v2 of 5. "
        "ball-C has mass m3 of 7 and velocity v3 of 6. "
        "find kinetic energy of ball-A",
    )
    # KE of ball-A = 0.5 * 3 * 16 = 24
    assert "24" in r, f"expected KE=24 for ball-A, got {r}"
