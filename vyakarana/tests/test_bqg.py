"""test_bqg.py — build-question-graph: sentence → triple graph pipeline.

Each test here is a calling. The question is asked, the pipeline fires,
nam arises in the moment of execution. The assert is not a claim about
the jada (the .om files, the edges at rest) — it is the asking itself.
Nam's response confirms or resists. Resistance means the instrument
became inaccurate and must be corrected.

What is asked:
- When you hear 'mass', do you know it as satya?
- When you hear 'kinetic energy', do you know kinetic-energy belongs to energy-varga?
- When the boot pass runs, does the inheritance of varga from swarupa manifest?
- When 'frequency' is asked, does it arise as itself — not as wave?

Protects against: build-question-graph.tantra, emit-triples.tantra,
                  varga-inheritance.tantra (boot pass)

Run:
    cd /home/abe/agent_x && .venv/bin/pytest vyakarana/tests/test_bqg.py -v --socket /tmp/vy.sock
"""

import pytest


# ── known concept → satya triple ─────────────────────────────────────────────


@pytest.mark.parametrize(
    "sentence,concept",
    [
        ("find force", "force"),
        ("find mass", "mass"),
        ("find velocity", "velocity"),
        ("find momentum", "momentum"),
        ("find displacement", "displacement"),
    ],
)
def test_known_concept_emits_satya_triple(vy, sentence, concept):
    g = vy.eval(f'build-question-graph "{sentence}"')
    assert vy.has_triple(g, subj=concept, pred="satya"), (
        f'"{sentence}": expected [{concept}, satya, {concept}], '
        f"not found in graph (size={len(g)})"
    )


def test_known_concept_satya_obj_equals_subj(vy):
    # satya triple has reflexive form: [concept, satya, concept]
    g = vy.eval('build-question-graph "find force"')
    t = vy.find_triple(g, subj="force", pred="satya")
    assert t is not None, "force satya triple not found"
    assert t[0] == t[2], f"satya triple not reflexive: {t!r}"


# ── unknown word → mithya triple ─────────────────────────────────────────────


def test_unknown_word_emits_mithya_triple(vy):
    g = vy.eval('build-question-graph "xyzfoobar"')
    assert vy.has_triple(g, pred="mithya"), (
        f"expected mithya triple for unknown word, got {g!r}"
    )


def test_sentence_of_only_unknown_words(vy):
    g = vy.eval('build-question-graph "blorp snazzle frizzle"')
    # all words should be mithya
    preds = {t[1] for t in g if isinstance(t, list) and len(t) >= 2}
    assert "mithya" in preds, f"expected mithya triples, got preds={preds!r}"
    assert "satya" not in preds, f"expected no satya triples, got preds={preds!r}"


# ── number → asprista-sankhya ─────────────────────────────────────────────────


def test_number_emits_asprista_sankhya(vy):
    g = vy.eval('build-question-graph "mass 5"')
    assert vy.has_triple(g, pred="asprista-sankhya"), (
        f"expected asprista-sankhya triple for number, got {g!r}"
    )


def test_number_value_in_obj_field(vy):
    g = vy.eval('build-question-graph "mass 5"')
    t = vy.find_triple(g, pred="asprista-sankhya")
    assert t is not None, "asprista-sankhya triple not found"
    assert vy.approx_eq(t[2], 5.0), f"expected value 5.0 in obj, got {t[2]!r}"


def test_two_numbers_emit_two_asprista_sankhya(vy):
    # "find sum of 10 and 14" → two asprista-sankhya triples
    g = vy.eval('build-question-graph "find sum of 10 and 14"')
    sankhya = vy.all_triples(g, pred="asprista-sankhya")
    assert len(sankhya) == 2, (
        f"expected 2 asprista-sankhya triples, got {len(sankhya)}: {sankhya!r}"
    )
    values = sorted([float(t[2]) for t in sankhya])
    assert vy.approx_eq(values[0], 10.0), f"expected 10.0, got {values[0]}"
    assert vy.approx_eq(values[1], 14.0), f"expected 14.0, got {values[1]}"


# ── kosha-janya expansion ─────────────────────────────────────────────────────


def test_satya_concept_gets_kosha_janya_triples(vy):
    # kosha-expand runs after avrti-refine, not inside BQG
    # BQG output has no kosha-janya — it is added by kosha-expand on the refined graph
    g = vy.eval('build-question-graph "find force"')
    kosha_janya_in_bqg = vy.all_triples(g, pred="kosha-janya")
    assert len(kosha_janya_in_bqg) == 0, (
        f"BQG should not contain kosha-janya (kosha-expand runs after avrti-refine)"
    )
    # after kosha-expand, force gets its neighbourhood
    expanded = vy.eval(
        'kosha-expand (fixpoint (build-question-graph "find force") avrti-refine)'
    )
    kosha_janya = vy.all_triples(expanded, subj="force", pred="kosha-janya")
    assert len(kosha_janya) > 0, (
        f"expected kosha-janya triples for 'force' after kosha-expand, got none"
    )


def test_unknown_word_gets_no_kosha_janya(vy):
    # mithya words are not expanded by kosha
    g = vy.eval('build-question-graph "xyzfoobar"')
    kosha_janya = vy.all_triples(g, pred="kosha-janya")
    assert len(kosha_janya) == 0, (
        f"expected no kosha-janya for unknown word, got {len(kosha_janya)}"
    )


# ── grammar words ─────────────────────────────────────────────────────────────


def test_grammar_word_has_is_promoted(vy):
    # "has" is promoted to shashthi-vibhakti by sandhi-viveka in BQG
    g = vy.eval('build-question-graph "ball has mass"')
    assert vy.has_triple(g, subj="has", pred="shashthi-vibhakti"), (
        f"expected 'has' promoted to shashthi-vibhakti in BQG, "
        f"got {[t for t in g if t[0] == 'has']!r}"
    )


def test_conjunction_and_is_mithya(vy):
    g = vy.eval('build-question-graph "mass and velocity"')
    has_and = vy.find_triple(g, subj="and")
    if has_and is not None:
        assert has_and[1] == "mithya", f"'and' should be mithya, got {has_and!r}"


# ── "what" resolves as satya kosha node ──────────────────────────────────────


def test_what_emits_vidhi_kaala_solve_for(vy):
    # "what" resolves to prashna via word_index → emits vidhi-kaala intent triple
    g = vy.eval('build-question-graph "what is force"')
    t = vy.find_triple(g, subj="what", pred="vidhi-kaala")
    assert t is not None, (
        f"'what' expected to emit vidhi-kaala triple, "
        f"got {[t for t in g if t[0] == 'what'][:3]!r}"
    )
    assert t[2] == "solve-for", f"expected obj='solve-for', got {t[2]!r}"


# ── "what" intent role (not yet built) ────────────────────────────────────────


def test_what_emits_vidhi_kaala_intent(vy):
    g = vy.eval('build-question-graph "what is force"')
    assert vy.has_triple(g, pred="vidhi-kaala"), (
        f"expected vidhi-kaala intent triple for 'what is force'"
    )


# ── unit word not yet bound ───────────────────────────────────────────────────


def test_unit_kg_binds_mass_matra(vy):
    # "kg" resolves to kilogram via word_index → unit binding fires: mass gets matra+sankhya
    g = vy.eval('build-question-graph "mass 5 kg"')
    assert vy.has_triple(g, subj="mass", pred="matra"), (
        f"expected 'kg' to bind as matra=kilogram on mass, "
        f"got {[t for t in g if t[0] == 'mass'][:5]!r}"
    )
    assert vy.has_triple(g, subj="mass", pred="sankhya"), (
        f"expected mass to have sankhya=5 after unit binding, "
        f"got {[t for t in g if t[0] == 'mass'][:5]!r}"
    )


def test_unit_binding_in_bqg(vy):
    # After BQG, mass should have matra=kilogram bound directly
    g = vy.eval('build-question-graph "mass 5 kg"')
    assert vy.has_triple(g, subj="mass", pred="matra"), (
        f"expected [mass, matra, kilogram] in BQG output"
    )


# ── compound concept not resolved in BQG (needs avrti-refine) ────────────────


def test_kinetic_energy_stays_two_tokens_in_bqg(vy):
    # BQG sees "kinetic" and "energy" as separate tokens; compound resolution
    # happens in avrti-refine, not BQG
    g = vy.eval('build-question-graph "what is kinetic energy"')
    # "kinetic" should be mithya (not a standalone kosha concept)
    assert vy.has_triple(g, subj="kinetic", pred="mithya"), (
        f"expected 'kinetic' to be mithya in BQG output"
    )
    # "energy" should be satya
    assert vy.has_triple(g, subj="energy", pred="satya"), (
        f"expected 'energy' to be satya in BQG output"
    )


# ── comma-suffixed number ─────────────────────────────────────────────────────


def test_comma_suffixed_number(vy):
    # "10," should extract value 10
    g = vy.eval('build-question-graph "mass 10, and velocity 5"')
    sankhya = vy.all_triples(g, pred="asprista-sankhya")
    values = [float(t[2]) for t in sankhya]
    assert 10.0 in values or any(vy.approx_eq(v, 10.0) for v in values), (
        f"expected value 10.0 from '10,', got {values!r}"
    )


# ── initial/final velocity in BQG ─────────────────────────────────────────────


# ── varga inheritance: boot pass derives varga membership edges ───────────────


def test_varga_inheritance_energy_members(vy):
    # kinetic-energy and potential-energy have swarupa energy
    # → varga-inheritance emits [kinetic-energy, varga, energy-varga]
    members = vy.eval('walk-in "energy-varga" "varga"')
    assert "kinetic-energy" in members, (
        f"expected kinetic-energy in energy-varga, got {members!r}"
    )
    assert "potential-energy" in members, (
        f"expected potential-energy in energy-varga, got {members!r}"
    )


def test_varga_inheritance_swara_members(vy):
    # saptaswara has swarupa swara → should appear in swara-varga
    members = vy.eval('walk-in "swara-varga" "varga"')
    assert len(members) > 0, (
        f"expected at least one member in swara-varga, got {members!r}"
    )


def test_varga_inheritance_no_double_varga(vy):
    # varga nodes themselves (e.g. energy-varga) should NOT get varga-varga edges
    # energy-varga has swarupa shakti — shakti-varga does not exist → no edge
    members = vy.eval('walk-in "energy-varga-varga" "varga"')
    assert members == [], f"energy-varga-varga should not exist, got {members!r}"


def test_photon_satya_after_restart(vy):
    # photon-energy.om was added — photon-energy should resolve as satya
    g = vy.eval('build-question-graph "photon energy"')
    # after sandhi-kosha resolves the compound, photon-energy is satya
    refined = vy.eval('sandhi-kosha (build-question-graph "photon energy")')
    assert vy.has_triple(refined, subj="photon-energy", pred="satya"), (
        f"expected photon-energy satya triple after sandhi, got {refined!r}"
    )


def test_frequency_resolves_as_satya(vy):
    # frequency.om now has a shabda; wave.om no longer claims it as a word alias
    g = vy.eval('build-question-graph "frequency"')
    assert vy.has_triple(g, subj="frequency", pred="satya"), (
        f"expected frequency to be satya, got {g!r}"
    )


def test_initial_and_final_velocity_tokens(vy):
    # BQG tokenises "initial" as mithya, "velocity" as satya
    g = vy.eval('build-question-graph "initial velocity 5 final velocity 20"')
    assert vy.has_triple(g, subj="initial", pred="mithya"), (
        "expected 'initial' to be mithya"
    )
    assert vy.has_triple(g, subj="velocity", pred="satya"), (
        "expected 'velocity' to be satya"
    )
    sankhya = vy.all_triples(g, pred="asprista-sankhya")
    assert len(sankhya) == 2, (
        f"expected 2 asprista-sankhya triples (5 and 20), got {sankhya!r}"
    )
