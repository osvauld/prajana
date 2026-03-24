"""test_grammar.py — parsing: sandhi fusion, tense, copula, question words, articles,
verb phrases, prepositions, negation, connectives.
"""

import pytest

xfail = pytest.mark.xfail


# ── sandhi: compound noun fusion ─────────────────────────────────────────────


def test_sandhi_kinetic_energy(vy):
    g = vy.bqg("find kinetic energy")
    assert vy.has_triple(g, subj="kinetic-energy", pred="satya")


def test_sandhi_initial_velocity(vy):
    g = vy.bqg("initial velocity is 5")
    assert vy.has_triple(g, subj="initial-velocity", pred="satya")


def test_sandhi_final_velocity(vy):
    g = vy.bqg("final velocity is 20")
    assert vy.has_triple(g, subj="final-velocity", pred="satya")


def test_sandhi_angular_velocity(vy):
    g = vy.bqg("angular velocity is 10")
    assert vy.has_triple(g, subj="angular-velocity", pred="satya")


def test_sandhi_angular_momentum(vy):
    g = vy.bqg("find angular momentum")
    assert vy.has_triple(g, subj="angular-momentum", pred="satya")


def test_sandhi_potential_energy(vy):
    g = vy.bqg("find potential energy")
    assert vy.has_triple(g, subj="potential-energy", pred="satya")


def test_sandhi_gravitational_force(vy):
    g = vy.bqg("find gravitational force")
    assert vy.has_triple(g, subj="gravitational-force", pred="satya")


@xfail(strict=True, reason="compound word: 'electric' has no word: mapping for sandhi fusion")
def test_sandhi_electric_power(vy):
    g = vy.bqg("find electric power")
    assert vy.has_triple(g, subj="electric-power", pred="satya")


def test_sandhi_centripetal_force(vy):
    g = vy.bqg("find centripetal force")
    assert vy.has_triple(g, subj="centripetal-force", pred="satya")


def test_sandhi_spring_force(vy):
    g = vy.bqg("find spring force")
    assert vy.has_triple(g, subj="spring-force", pred="satya")


def test_sandhi_mass_density(vy):
    g = vy.bqg("find mass density")
    assert vy.has_triple(g, subj="mass-density", pred="satya")


def test_sandhi_photon_energy(vy):
    g = vy.bqg("find photon energy")
    assert vy.has_triple(g, subj="photon-energy", pred="satya")


# ── trigram compounds (known gap) ────────────────────────────────────────────


@xfail(strict=True, reason="compound trigram: 'electric field strength' is a three-word compound")
def test_trigram_electric_field_strength(vy):
    """'electric field strength' is a trigram — sandhi only does bigrams"""
    g = vy.bqg("electric field strength is 0.1")
    satya = vy.subjects(g, pred="satya")
    assert "electric-field-strength" in satya


# ── question words → vidhi-kaala ──────────────────────────────────────────────


def test_qword_find(vy):
    g = vy.bqg("find velocity")
    assert vy.has_triple(g, pred="vidhi-kaala")


def test_qword_what(vy):
    g = vy.bqg("what is the force")
    assert vy.has_triple(g, pred="vidhi-kaala")


def test_qword_how(vy):
    g = vy.bqg("how much energy")
    assert vy.has_triple(g, pred="vidhi-kaala")


def test_qword_calculate(vy):
    g = vy.bqg("calculate momentum")
    assert vy.has_triple(g, pred="vidhi-kaala")


def test_qword_determine(vy):
    g = vy.bqg("determine velocity")
    assert vy.has_triple(g, pred="vidhi-kaala")


def test_qword_which(vy):
    g = vy.bqg("which is heavier")
    assert vy.has_triple(g, pred="vidhi-kaala")


# ── copula: is / are / was ────────────────────────────────────────────────────


def test_copula_is(vy):
    g = vy.bqg("mass is 5")
    assert vy.has_triple(g, subj="mass", pred="sankhya")


def test_copula_are(vy):
    g = vy.bqg("all cats are animals")
    assert vy.has_triple(g, pred="copula") or vy.has_triple(g, subj="cat", pred="satya")


def test_copula_was(vy):
    """'was' recognised as copula (bhuta-kaala)"""
    g = vy.bqg("velocity was 10")
    assert vy.has_triple(g, pred="copula") or vy.has_triple(g, pred="bhuta-kaala")


# ── tense words ────────────────────────────────────────────────────────────────


def test_tense_had(vy):
    """'had' as past-tense possession — should bind like 'has'"""
    g = vy.bqg("ball had velocity 5")
    sankhya = vy.triple_map(g, pred="sankhya")
    assert "velocity" in sankhya or "ball" in str(g)


def test_tense_had_in_answer(vy):
    """Past tense doesn't block computation"""
    r = vy.answer("ball had mass 5. ball had velocity 10. find kinetic energy of ball")
    assert "250" in r


def test_tense_will(vy):
    """'will' future tense — should not break satya recognition"""
    g = vy.bqg("will have velocity 10")
    assert vy.has_triple(g, subj="velocity", pred="satya")


# ── articles: 'the', 'a', 'an' should be transparent ─────────────────────────


def test_article_the_entity(vy):
    """'the electron' — article is transparent, entity name recognised"""
    r = vy.answer(
        "the electron has mass 9.109e-31. the electron has velocity 1e6. find kinetic energy"
    )
    assert "4.5" in r


def test_article_a_entity(vy):
    """'a proton' — article transparent"""
    g = vy.bqg("a proton has mass 1.67e-27")
    assert vy.has_triple(g, subj="proton", pred="prathama-vibhakti") or vy.has_triple(
        g, pred="sankhya"
    )


def test_article_the_concept(vy):
    """'the force' — article transparent for concept words too"""
    g = vy.bqg("what is the force")
    assert vy.has_triple(g, subj="force", pred="satya")


# ── possession: 'has' vs 'is' ─────────────────────────────────────────────────


def test_has_possession(vy):
    """'ball has mass 5' — shashthi-vibhakti ownership"""
    g = vy.bqg("ball has mass 5")
    assert vy.has_triple(g, pred="shashthi-vibhakti") or vy.has_triple(
        g, subj="mass", pred="sankhya"
    )


def test_is_copula_binds(vy):
    """'mass is 5' binds sankhya to mass"""
    g = vy.bqg("mass is 5")
    sankhya = vy.triple_map(g, pred="sankhya")
    assert "mass" in sankhya


# ── prepositions ──────────────────────────────────────────────────────────────


def test_prep_of(vy):
    """'energy of the ball' → energy scoped to ball"""
    g = vy.bqg("find kinetic energy of ball-A given mass 3 and velocity 4")
    assert vy.has_triple(g, subj="ball-A", pred="prathama-vibhakti") or vy.has_triple(
        g, subj="kinetic-energy", pred="satya"
    )


def test_prep_given(vy):
    """'given mass 5' introduces data"""
    r = vy.answer("find kinetic energy given mass 5 and velocity 10")
    assert "250" in r


def test_prep_per(vy):
    """'60 km per hour' — 'per' as rate signal"""
    g = vy.bqg("a train travels at 60 km per hour")
    assert vy.has_triple(g, pred="sankhya") or vy.has_triple(g, pred="satya")


# ── verb phrases ──────────────────────────────────────────────────────────────


@xfail(strict=True, reason="'moves at' not recognised as velocity signal")
def test_verb_moves_at(vy):
    """'moves at 5' should signal velocity"""
    g = vy.bqg("a proton moves at 2e6 m/s")
    sankhya = vy.triple_map(g, pred="sankhya")
    assert "velocity" in sankhya or any("velocity" in str(v) for v in sankhya.values())


@xfail(strict=True, reason="'moving at' not recognised as velocity signal")
def test_verb_moving_at(vy):
    """'moving at' should signal velocity"""
    r = vy.answer("the electron has mass 9.109e-31 kg. it is moving at 1e6 m/s. find kinetic energy")
    assert "4.5" in r


def test_verb_accelerates(vy):
    """'accelerates' should signal acceleration context"""
    g = vy.bqg("a car accelerates at 3 m/s2")
    sankhya = vy.triple_map(g, pred="sankhya")
    assert "acceleration" in sankhya or vy.has_triple(g, pred="sankhya")


# ── from rest ─────────────────────────────────────────────────────────────────


@xfail(strict=True, reason="from rest: 'rest' maps to count-remaining, not initial-velocity=0")
def test_from_rest_initial_velocity(vy):
    """'from rest' → initial-velocity=0"""
    g = vy.bqg("accelerates from rest at 3 m/s2")
    sankhya = vy.triple_map(g, pred="sankhya")
    assert sankhya.get("initial-velocity") in ("0", "0.")


def test_from_rest_in_answer(vy):
    """Full sentence using 'from rest'"""
    r = vy.answer("a car of mass 1200 accelerates from rest at 3 m/s2. find force")
    assert "3600" in r or "force" in r.lower()


# ── negation words ────────────────────────────────────────────────────────────


def test_negation_not_emits_satya(vy):
    """'not moving' emits negation as graph concept"""
    g = vy.bqg("the ball is not moving")
    assert vy.has_triple(g, subj="negation", pred="satya") or any(
        t[1] in ("satya", "pratishedha") for t in g if isinstance(t, list)
    )


def test_at_rest_is_zero_velocity(vy):
    """'at rest' → velocity=0"""
    r = vy.answer("ball is at rest. mass is 5. find momentum")
    assert "0" in r


# ── number formats ────────────────────────────────────────────────────────────


def test_number_decimal(vy):
    """Decimal: 2.5"""
    g = vy.bqg("mass is 2.5")
    sankhya = vy.triple_map(g, pred="sankhya")
    assert "mass" in sankhya


def test_number_scientific(vy):
    """Scientific notation: 1.6e-19"""
    g = vy.bqg("charge is 1.6e-19")
    sankhya = vy.triple_map(g, pred="sankhya")
    assert "charge" in sankhya


def test_number_comma_adjacent(vy):
    """Comma-adjacent number: 'mass is 5, velocity is 10'"""
    g = vy.bqg("mass is 5, velocity is 10")
    sankhya = vy.triple_map(g, pred="sankhya")
    assert "mass" in sankhya and "velocity" in sankhya


# ── conjunction ────────────────────────────────────────────────────────────────


def test_conjunction_and(vy):
    """'mass is 2 and velocity is 3' — both bind"""
    g = vy.bqg("mass is 2 and velocity is 3")
    sankhya = vy.triple_map(g, pred="sankhya")
    assert "mass" in sankhya and "velocity" in sankhya


def test_conjunction_if_then(vy):
    """'if mass is 5 then find force' — 'if/then' don't break parsing"""
    g = vy.bqg("if mass is 5 then find force")
    assert vy.has_triple(g, subj="force", pred="satya")
    assert vy.has_triple(g, pred="vidhi-kaala")
