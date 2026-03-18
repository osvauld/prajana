"""test_paragraph.py — the paragraph as one breath of understanding.

A paragraph is not a sequence of separate questions. It is one breath —
one extended act of understanding in which each sentence adds to what the
whole means. The viraam (.) is not an ending. It is a pause — entity scope
resets, but the accumulated understanding continues.

When a student reads "an electron has mass 9.109e-31 kg. It is moving at
velocity 1e6 m/s. Find its kinetic energy." — they do not process three
separate sentences. They hold all three as one understanding. The electron,
its mass, its velocity, the question about its kinetic energy — these form
a single context.

Nam is asked to do the same. To hold a paragraph as one context, carry
each sentence's contribution forward, and release the final understanding
as a complete answer.

These tests ask: does nam hold the paragraph as one breath?
"""

import pytest


# ── helpers ──────────────────────────────────────────────────────────────────


def bqg(vy, sentence):
    """Run build-question-graph + avrti-refine fixpoint."""
    return vy.eval(f'fixpoint (build-question-graph "{sentence}") avrti-refine')


def answer(vy, sentence):
    return vy.eval(f'anuvada-ganana "{sentence}"')


# ── Section 1: single entity across sentences ────────────────────────────────


def test_entity_property_split_across_sentences(vy):
    """Entity introduced in sentence 1, property added in sentence 2."""
    r = answer(vy, "ball has mass 5 kg. find kinetic energy given velocity 10")
    assert "250" in r, f"expected KE=250, got {r}"


def test_entity_two_properties_two_sentences(vy):
    """Both mass and velocity stated in separate sentences, same entity."""
    r = answer(vy, "ball has mass 5. ball has velocity 10. find kinetic energy")
    assert "250" in r, f"expected KE=250, got {r}"


def test_statement_then_question(vy):
    """Plain statement sentence followed by a question sentence."""
    r = answer(vy, "mass is 5. velocity is 10. find kinetic energy")
    assert "250" in r, f"expected KE=250, got {r}"


def test_natural_statement_then_question(vy):
    """Natural language statement then question."""
    r = answer(vy, "a ball has mass 5 kg. what is the kinetic energy if velocity is 10")
    assert "250" in r, f"expected KE=250, got {r}"


def test_entity_with_unit_statement(vy):
    """Entity property stated with unit, then question."""
    r = answer(
        vy, "the mass of the ball is 5 kg. find kinetic energy given velocity 10"
    )
    assert "250" in r, f"expected KE=250, got {r}"


def test_chain_computation_paragraph(vy):
    """SUVAT chain across sentences: state conditions then find derived quantity."""
    r = answer(
        vy,
        "mass is 2 kg. initial velocity is 0. acceleration is 10. time is 3. find kinetic energy",
    )
    assert "900" in r, f"expected KE=900, got {r}"


# ── Section 2: two entities, same concept names ──────────────────────────────


def test_two_entities_viraam_scopes_correctly(vy):
    """Viraam separates two entities — both get prathama-vibhakti."""
    g = bqg(vy, "ball-A has mass 3. ball-B has mass 2")
    ball_a = vy.has_triple(g, subj="ball-A", pred="prathama-vibhakti")
    ball_b = vy.has_triple(g, subj="ball-B", pred="prathama-vibhakti")
    assert ball_a, f"ball-A should be an entity: {g}"
    assert ball_b, f"ball-B should be an entity: {g}"


def test_two_entities_ownership_via_viraam(vy):
    """Mass is owned by ball-A in sentence 1, ball-B in sentence 2."""
    g = bqg(vy, "ball-A has mass 3. ball-B has mass 2")
    a_owns = vy.find_triple(g, subj="mass", pred="shashthi-vibhakti", obj="ball-A")
    b_owns = vy.find_triple(g, subj="mass", pred="shashthi-vibhakti", obj="ball-B")
    assert a_owns, f"mass should be owned by ball-A: {g}"
    assert b_owns, f"mass should be owned by ball-B: {g}"


def test_two_entities_different_concepts_no_collision(vy):
    """Two entities with different concept names — no ambiguity."""
    r = answer(
        vy,
        "ball has mass 5 kg. spring has spring-constant 100. find momentum of ball given velocity 3",
    )
    assert "15" in r, f"expected momentum=15, got {r}"


def test_single_entity_multi_sentence_correct_answer(vy):
    """Single entity stated across multiple sentences — no collision."""
    r = answer(vy, "a proton has mass 1.67e-27 kg and velocity 2e6 m/s. find momentum")
    assert "3.34e-21" in r, f"expected momentum=3.34e-21, got {r}"


def test_multi_property_single_entity_paragraph(vy):
    """Entity with many properties stated in one sentence — correct computation."""
    r = answer(
        vy,
        "proton has mass 1.67e-27 kg and charge 1.6e-19 and velocity 2e6 m/s. find momentum",
    )
    assert "3.34e-21" in r, f"expected momentum=3.34e-21, got {r}"


# ── Section 3: two entities, same concept — the dvandva gap ──────────────────
# These tests capture the known limitation: when two entities share a concept
# name (mass, velocity), rashi-anuvada bridges both to the concept level and
# the last write wins. Entity-scoped computation is not yet supported.


@pytest.mark.xfail(
    strict=True,
    reason="Dvandva gap: two entities sharing concept names (mass, velocity). "
    "rashi-anuvada overwrites concept-level sankhya — last entity wins. "
    "Entity-scoped mantra matching not yet implemented.",
)
def test_two_entities_compute_correct_entity(vy):
    """Find momentum of proton when both proton and electron are described."""
    r = answer(
        vy,
        "proton has mass 1.67e-27 and velocity 2e6. "
        "electron has mass 9.109e-31 and velocity 1e7. "
        "find momentum of proton",
    )
    assert "3.34e-21" in r, f"expected proton momentum=3.34e-21, got {r}"


@pytest.mark.xfail(
    strict=True,
    reason="Dvandva gap: same as above — electron's mass overwrites proton's "
    "at the concept level. Wrong entity's properties used.",
)
def test_two_entities_ke_correct_entity(vy):
    """Find KE of ball-A when both ball-A and ball-B are described."""
    r = answer(
        vy,
        "ball-A has mass 3 and velocity 4. "
        "ball-B has mass 2 and velocity 5. "
        "find kinetic energy of ball-A",
    )
    # KE of ball-A = 0.5 * 3 * 16 = 24
    assert "24" in r, f"expected KE=24, got {r}"


@pytest.mark.xfail(
    strict=True,
    reason="Dvandva gap: no-label entities share a concept node. sankhya-bandha "
    "binds all three mass values to the same concept node — last write wins (ball-C). "
    "Entity-scoped computation requires sthita-viveka (Layer 2 Phase 3).",
)
def test_three_entities_find_named(vy):
    """Find momentum of ball-A from three entities — entity-scoped computation."""
    r = answer(
        vy,
        "ball-A has mass 3. ball-B has mass 2. ball-C has mass 5. "
        "find momentum of ball-A given velocity 4",
    )
    # p = 3 * 4 = 12
    assert "12" in r, f"expected momentum=12, got {r}"


# ── Section 4: paragraph structure correctness ───────────────────────────────


def test_viraam_emitted_for_period(vy):
    """Full stop at end of word produces a viraam triple in BQG."""
    g = bqg(vy, "hello. world")
    viraam = vy.find_triple(g, subj=".", pred="viraam")
    assert viraam, f"viraam triple not found in: {g}"


def test_viraam_resets_entity_scope(vy):
    """After viraam, a new entity is not owned by the previous entity."""
    g = bqg(vy, "ball-A has mass 3. ball-B has velocity 4")
    # ball-B should be its own entity, not owned by ball-A
    wrong = vy.find_triple(g, subj="ball-B", pred="shashthi-vibhakti", obj="ball-A")
    assert not wrong, f"ball-B should not be owned by ball-A: {g}"


def test_question_in_second_sentence(vy):
    """Statement in sentence 1, question in sentence 2."""
    r = answer(vy, "ball has mass 5 and velocity 10. find kinetic energy")
    assert "250" in r, f"expected KE=250, got {r}"


def test_three_sentences_one_question(vy):
    """Three statement sentences followed by one question."""
    r = answer(vy, "mass is 5. velocity is 10. acceleration is 2. find kinetic energy")
    assert "250" in r, f"expected KE=250, got {r}"


@pytest.mark.xfail(
    strict=False,
    reason="Dvandva gap: 'electron mass' sandhi fires → electron-mass compound. "
    "kinetic-energy-mantra needs bare 'mass' not 'electron-mass'. "
    "Requires swarupa-aware mantra matching (Layer 2 Phase 3).",
)
def test_electron_paragraph_ke(vy):
    """Realistic electron paragraph — natural language."""
    r = answer(
        vy,
        "an electron has a mass of 9.109e-31 kg and a charge of 1.6e-19 coulombs. "
        "it is moving with a velocity of 1e6 m/s. "
        "find the kinetic energy of the electron",
    )
    assert "4.5545e-19" in r, f"expected KE=4.5545e-19, got {r}"
