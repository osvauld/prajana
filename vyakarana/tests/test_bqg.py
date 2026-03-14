"""test_bqg.py — build-question-graph: sentence → triple graph pipeline.

Tests the full BQG pipeline: tokenisation, kosha lookup, kosha-expand, sandhi.
This is the highest-value regression module — it exercises multiple subsystems
in one call.

Key observations from probing:
- BQG output contains satya, mithya, asprista-sankhya, and kosha-janya triples
- "what" resolves as satya (it's a kosha node), not vidhi-kaala — xfail
- "has"/"was" stay mithya — verb promotion not yet built
- "kg" stays mithya — abbreviations not in word_index
- Numbers produce asprista-sankhya triples (value in obj field)
- kosha-janya triples are added for every satya concept

Protects against: build-question-graph.tantra, emit-triples.tantra

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
    # every satya concept gets kosha-janya expansion triples
    g = vy.eval('build-question-graph "find force"')
    kosha_janya = vy.all_triples(g, subj="force", pred="kosha-janya")
    assert len(kosha_janya) > 0, f"expected kosha-janya triples for 'force', got none"


def test_unknown_word_gets_no_kosha_janya(vy):
    # mithya words are not expanded by kosha
    g = vy.eval('build-question-graph "xyzfoobar"')
    kosha_janya = vy.all_triples(g, pred="kosha-janya")
    assert len(kosha_janya) == 0, (
        f"expected no kosha-janya for unknown word, got {len(kosha_janya)}"
    )


# ── grammar words ─────────────────────────────────────────────────────────────


def test_grammar_word_has_is_mithya(vy):
    # "has" stays mithya — verb promotion not built
    g = vy.eval('build-question-graph "ball has mass"')
    assert vy.has_triple(g, subj="has", pred="mithya"), (
        f"expected 'has' to be mithya before sandhi-viveka, "
        f"got {[t for t in g if t[0] == 'has']!r}"
    )


def test_conjunction_and_is_mithya(vy):
    g = vy.eval('build-question-graph "mass and velocity"')
    has_and = vy.find_triple(g, subj="and")
    if has_and is not None:
        assert has_and[1] == "mithya", f"'and' should be mithya, got {has_and!r}"


# ── "what" resolves as satya kosha node ──────────────────────────────────────


def test_what_is_satya_kosha_node(vy):
    # "what" is in the kosha as a question concept → resolves to satya
    g = vy.eval('build-question-graph "what is force"')
    assert vy.has_triple(g, subj="what", pred="satya"), (
        f"'what' expected to be satya (it's a kosha node), "
        f"got {[t for t in g if t[0] == 'what'][:3]!r}"
    )


# ── "what" intent role (not yet built) ────────────────────────────────────────


@pytest.mark.xfail(
    strict=True,
    reason="vidhi-kaala intent triple not built: 'what' resolves as satya kosha "
    "node; intent role assignment not in BQG pipeline",
)
def test_what_emits_vidhi_kaala_intent(vy):
    g = vy.eval('build-question-graph "what is force"')
    assert vy.has_triple(g, pred="vidhi-kaala"), (
        f"expected vidhi-kaala intent triple for 'what is force'"
    )


# ── unit word not yet bound ───────────────────────────────────────────────────


def test_unit_kg_is_mithya_in_bqg(vy):
    # "kg" not in word_index → stays mithya
    g = vy.eval('build-question-graph "mass 5 kg"')
    assert vy.has_triple(g, subj="kg", pred="mithya"), (
        f"expected 'kg' to be mithya (abbreviation not in word_index), "
        f"got {[t for t in g if t[0] == 'kg']!r}"
    )


@pytest.mark.xfail(
    strict=True,
    reason="BQG unit binding not built: 'kg' not in word_index; "
    "emit-triples unit-consumes-pending path not firing",
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
