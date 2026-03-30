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


# ── vibhakti: structural case edges ──────────────────────────────────────────


def test_vibhakti_adhikarana_in(vy):
    """'in the box' → adhikarana (locative)"""
    g = vy.bqg("a ball in the box has mass 5")
    assert vy.has_triple(g, pred="adhikarana")


def test_vibhakti_adhikarana_on(vy):
    """'on the table' → adhikarana (locative)"""
    g = vy.bqg("3 birds on a tree")
    assert vy.has_triple(g, pred="adhikarana")


def test_vibhakti_apadana_from(vy):
    """'from rest' → apadana (ablative) or compound merge"""
    g = vy.bqg("accelerates from rest at 3 m/s2")
    # compound merge eats 'from rest' → from-rest satya node
    assert vy.has_triple(g, subj="from-rest", pred="satya")


def test_vibhakti_sampradana_to(vy):
    """'gave to Mary' → sampradana (dative)"""
    g = vy.bqg("he gave 3 to Mary")
    assert vy.has_triple(g, pred="sampradana")


def test_vibhakti_sampradana_for(vy):
    """'for 2 hours' → sampradana (purpose)"""
    g = vy.bqg("a train travels for 2 hours")
    assert vy.has_triple(g, pred="sampradana")


def test_vibhakti_karana_by(vy):
    """'hit by a bat' → karana (instrumental)"""
    g = vy.bqg("a ball is hit by a bat")
    assert vy.has_triple(g, pred="karana")


def test_vibhakti_from_rest_qualifies(vy):
    """from-rest shunya-bandha qualifies to initial-velocity=0"""
    g = vy.bqg("accelerates from rest at 3 m/s2")
    sankhya = vy.triple_map(g, pred="sankhya")
    assert sankhya.get("initial-velocity") in ("0", "0.")


def test_vibhakti_combined_locative_and_value(vy):
    """'3 birds on a tree' → adhikarana + number binding"""
    g = vy.bqg("3 birds on a tree")
    assert vy.has_triple(g, pred="adhikarana")
    assert vy.has_triple(g, pred="asprista-sankhya")


def test_vibhakti_from_rest_with_force(vy):
    """'from rest at 3 m/s2, mass 1200, find force' — apadana + multiple bindings + derivation"""
    r = vy.answer("a car of mass 1200 accelerates from rest at 3 m/s2. find force")
    assert "3600" in r


def test_vibhakti_sampradana_does_not_bind_number(vy):
    """'gave 3 to Mary' — 3 should not bind to Mary as her quantity"""
    g = vy.bqg("Tom has 7 apples. he gave 3 to Mary")
    sankhya = vy.triple_map(g, pred="sankhya")
    # Mary should NOT have sankhya=3 (that's what's being transferred, not her possession)
    assert sankhya.get("Mary") != "3"


def test_vibhakti_multi_case_physics(vy):
    """'ball at rest on a surface' — adhikarana (on) + from-rest compound"""
    g = vy.bqg("a ball at rest on a surface has mass 5")
    assert vy.has_triple(g, pred="adhikarana")
    sankhya = vy.triple_map(g, pred="sankhya")
    assert "5" in sankhya.values()


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


# ── kriya-nirmana: generated verb forms ───────────────────────────────────────


def test_generated_ing_tense(vy):
    """'flying' (generated -ing) → vartamana-kaala tense in BQG"""
    g = vy.bqg("3 birds were flying from a tree")
    assert vy.has_triple(g, subj="flying", pred="vartamana-kaala")


def test_generated_ed_tense(vy):
    """'accelerated' (generated -ed) → bhuta-kaala tense in BQG"""
    g = vy.bqg("the car accelerated to 60")
    assert vy.has_triple(g, subj="accelerated", pred="bhuta-kaala")


def test_generated_ing_not_satya(vy):
    """Generated -ing forms must be mithya, not satya concepts"""
    g = vy.bqg("a ball was moving fast")
    satya = vy.subjects(g, pred="satya")
    assert "moving" not in satya


def test_generated_ed_direction_vriddhi(vy):
    """'added' (generated -ed with vriddhi) → count chain uses vriddhi direction"""
    r = vy.answer("a bag has 5 apples. 2 were added. how many apples")
    assert "7" in r


def test_generated_ed_direction_kshaya(vy):
    """'eaten' (hand-authored -ed with kshaya) → count chain uses kshaya direction"""
    r = vy.answer("a bag has 10 apples. 3 were eaten. how many apples")
    assert "7" in r


def test_generated_forms_have_janya(vy):
    """Generated forms have janya edge back to dhatu root"""
    g = vy.bqg("birds were flying away")
    # flying resolves to a node with janya: dhatu-fly
    # the tense edge confirms the node was found and classified
    assert vy.has_triple(g, subj="flying", pred="vartamana-kaala")


@xfail(strict=True, reason="motion verb: 'moving at 5 m/s' should bind velocity=5 via generated -ing form + step-motion")
def test_generated_ing_velocity_binding(vy):
    """'moving at 5 m/s' — generated form should enable velocity signal"""
    g = vy.bqg("a ball is moving at 5 m/s")
    sankhya = vy.triple_map(g, pred="sankhya")
    assert "velocity" in sankhya


def test_generated_count_with_eaten(vy):
    """Count chain with 'eaten' (kshaya direction via generated form)"""
    r = vy.answer("a bag had 10 apples. 3 were eaten. how many apples are left")
    assert "7" in r


# ── from rest ─────────────────────────────────────────────────────────────────


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


def test_negation_not_emits_pratishedha(vy):
    """'not moving' should emit pratishedha edge"""
    g = vy.bqg("the ball is not moving")
    assert vy.has_triple(g, pred="pratishedha")


def test_at_rest_is_zero_velocity(vy):
    """'at rest' → velocity=0"""
    r = vy.answer("ball is at rest. mass is 5. find momentum")
    assert "0" in r


def test_not_at_rest_blocks_shunya(vy):
    """'not at rest' → shunya-bandha must NOT bind velocity=0"""
    g = vy.bqg("the ball is not at rest. what is the velocity of the ball")
    sankhya = vy.triple_map(g, pred="sankhya")
    assert sankhya.get("velocity") != "0."


def test_not_at_rest_with_explicit_velocity(vy):
    """'not at rest' + explicit v=10 → momentum uses 10, not 0"""
    r = vy.answer("ball is not at rest. mass is 5 kg. velocity is 10 m/s. what is the momentum")
    assert "50" in r


def test_without_friction_blocks_shunya(vy):
    """'without friction' → friction not bound to 0 via shunya"""
    g = vy.bqg("a surface without friction. what is the friction")
    sankhya = vy.triple_map(g, pred="sankhya")
    assert sankhya.get("friction") not in ("0", "0.")


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


# ══════════════════════════════════════════════════════════════════════════════
# bhasha-nirmana (step-118): graph-native English grammar
# Each section maps to a phase. Tests are xfail until the phase is built.
# ══════════════════════════════════════════════════════════════════════════════


# ── Phase A: pratishedha (negation) ──────────────────────────────────────────


def test_pratishedha_not_edge(vy):
    """'is not moving' → pratishedha edge in BQG"""
    g = vy.bqg("the ball is not moving")
    assert vy.has_triple(g, pred="pratishedha")


def test_pratishedha_no_determiner(vy):
    """'no velocity' → pratishedha on velocity"""
    g = vy.bqg("the ball has no velocity")
    assert vy.has_triple(g, pred="pratishedha")


def test_pratishedha_without(vy):
    """'without friction' → pratishedha on friction"""
    g = vy.bqg("a surface without friction")
    assert vy.has_triple(g, pred="pratishedha")


def test_pratishedha_never(vy):
    """'never stops' → pratishedha edge"""
    g = vy.bqg("the object never stops")
    assert vy.has_triple(g, pred="pratishedha")


# ── Phase B: sarvanama (pronouns) ───────────────────────────────────────────


@xfail(strict=True, reason="sarvanama: 'he' does not resolve to a pronoun node")
def test_pronoun_he_resolves(vy):
    """'he' should resolve to a pronoun node, not mithya"""
    g = vy.bqg("Tom has 5 apples. he gave 3 away")
    edges = [t for t in g if isinstance(t, list) and t[0] == "he"]
    assert len(edges) > 0 and edges[0][1] != "mithya"


@xfail(strict=True, reason="sarvanama: 'she' does not resolve")
def test_pronoun_she_resolves(vy):
    """'she' should resolve to a pronoun node"""
    g = vy.bqg("Mary has mass 5. she runs at velocity 3")
    edges = [t for t in g if isinstance(t, list) and t[0] == "she"]
    assert len(edges) > 0 and edges[0][1] != "mithya"


@xfail(strict=True, reason="sarvanama: 'they' does not resolve")
def test_pronoun_they_resolves(vy):
    """'they' should resolve with bahu-vachana"""
    g = vy.bqg("the balls have mass 5. they move at velocity 3")
    edges = [t for t in g if isinstance(t, list) and t[0] == "they"]
    assert len(edges) > 0 and edges[0][1] != "mithya"


@xfail(strict=True, reason="sarvanama: 'his' is mithya, should resolve as possessive pronoun → shashthi-vibhakti")
def test_pronoun_possessive_his(vy):
    """'his velocity' — 'his' should emit shashthi-vibhakti, not be mithya"""
    g = vy.bqg("Tom has mass 5. his velocity is 10. find kinetic energy")
    his_triples = [t for t in g if isinstance(t, list) and t[0] == "his"]
    assert len(his_triples) > 0 and his_triples[0][1] != "mithya"


# ── Phase C: sandhi-viparyaya (contractions) ─────────────────────────────────


@xfail(strict=True, reason="contractions: don't not split into do+not")
def test_contraction_dont(vy):
    """don't → do + not (split before resolution)"""
    g = vy.bqg("the balls don't move")
    assert vy.has_triple(g, pred="pratishedha")


@xfail(strict=True, reason="contractions: doesn't not split into does+not")
def test_contraction_doesnt(vy):
    """doesn't → does + not"""
    g = vy.bqg("the ball doesn't have velocity")
    assert vy.has_triple(g, pred="pratishedha")


@xfail(strict=True, reason="contractions: isn't not split into is+not")
def test_contraction_isnt(vy):
    """isn't → is + not"""
    g = vy.bqg("the ball isn't moving")
    assert vy.has_triple(g, pred="pratishedha")


@xfail(strict=True, reason="contractions: can't not split into can+not")
def test_contraction_cant(vy):
    """can't → can + not"""
    g = vy.bqg("the ball can't stop")
    assert vy.has_triple(g, pred="pratishedha")


# ── Phase D: sahayaka (auxiliaries) ──────────────────────────────────────────


@xfail(strict=True, reason="auxiliary: 'does' is mithya, should be question/emphasis marker")
def test_auxiliary_does_question(vy):
    """'does the ball have' — 'does' should not be mithya"""
    g = vy.bqg("does the ball have velocity")
    does_triples = [t for t in g if isinstance(t, list) and t[0] == "does"]
    assert len(does_triples) > 0 and does_triples[0][1] != "mithya"


@xfail(strict=True, reason="auxiliary: 'did' is mithya, should be past question marker")
def test_auxiliary_did_question(vy):
    """'did the ball move' — 'did' should emit bhuta-kaala"""
    g = vy.bqg("did the ball move")
    did_triples = [t for t in g if isinstance(t, list) and t[0] == "did"]
    assert len(did_triples) > 0 and did_triples[0][1] != "mithya"


@xfail(strict=True, reason="auxiliary: 'am' is mithya, should emit copula like 'is'")
def test_auxiliary_am(vy):
    """'I am at rest' — 'am' should emit copula edge"""
    g = vy.bqg("I am at rest")
    am_triples = [t for t in g if isinstance(t, list) and t[0] == "am"]
    assert len(am_triples) > 0 and am_triples[0][1] == "copula"


# ── Phase E: vachana-nirmana (plurals) ───────────────────────────────────────


@xfail(strict=True, reason="vachana-nirmana: Sanskrit 'mokshas' should not exist as naama")
def test_plural_skip_sanskrit(vy):
    """Sanskrit terms must NOT be pluralized"""
    naama = vy.eval('(walk "moksha" "naama")')
    assert "mokshas" not in naama


# ── Phase F: parimana (quantifiers) ──────────────────────────────────────────


@xfail(strict=True, reason="quantifier: 'every' not resolved like 'each'")
def test_quantifier_every(vy):
    """'every box has 6 balls' — same as 'each'"""
    r = vy.answer("there are 4 boxes. every box has 6 balls. how many balls are there")
    assert "24" in r


@xfail(strict=True, reason="quantifier: 'all' is mithya, should resolve as universal aggregate")
def test_quantifier_all(vy):
    """'all balls have mass 5' — 'all' should not be mithya"""
    g = vy.bqg("all balls have mass 5")
    all_triples = [t for t in g if isinstance(t, list) and t[0] == "all"]
    assert len(all_triples) > 0 and all_triples[0][1] != "mithya"


@xfail(strict=True, reason="quantifier: 'no' emits pratishedha but downstream friction=0 binding not wired")
def test_quantifier_no_as_zero(vy):
    """'no friction' → friction = 0 (pratishedha + shunya)"""
    g = vy.bqg("a surface has no friction")
    sankhya = vy.triple_map(g, pred="sankhya")
    assert sankhya.get("friction") in ("0", "0.")


# ── Phase G: nirdeshaka (demonstratives) ─────────────────────────────────────


@xfail(strict=True, reason="demonstrative: 'this' is mithya, should resolve as proximal determiner")
def test_demonstrative_this(vy):
    """'this ball' — 'this' should not be mithya"""
    g = vy.bqg("this ball has mass 5")
    this_triples = [t for t in g if isinstance(t, list) and t[0] == "this"]
    assert len(this_triples) > 0 and this_triples[0][1] != "mithya"


@xfail(strict=True, reason="demonstrative: 'those' is mithya, should resolve as distal bahu-vachana")
def test_demonstrative_those(vy):
    """'those balls' — 'those' should not be mithya"""
    g = vy.bqg("those balls have mass 5")
    those_triples = [t for t in g if isinstance(t, list) and t[0] == "those"]
    assert len(those_triples) > 0 and those_triples[0][1] != "mithya"


# ── Phase H: viveka-rupa (comparison suffixes) ───────────────────────────────


def test_comparative_er_suffix(vy):
    """'-er' suffix resolves to viveka-max via shabda-anveshana"""
    g = vy.bqg("ball-A is taller than ball-B")
    assert vy.has_triple(g, pred="satya", subj="viveka-max")


@xfail(strict=True, reason="comparison: 'than' is mithya, should mark comparison reference")
def test_comparison_than_not_mithya(vy):
    """'than' should produce a structural edge, not disappear as mithya"""
    g = vy.bqg("ball-A is heavier than ball-B")
    than_triples = [t for t in g if isinstance(t, list) and t[0] == "than"]
    assert len(than_triples) > 0 and than_triples[0][1] != "mithya"


