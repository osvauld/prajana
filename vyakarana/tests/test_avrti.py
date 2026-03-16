"""test_avrti.py — avrti-refine and fixpoint: the spiral refinement pipeline.

avrti-refine orchestrates:
  sandhi-kosha      → compound resolution (kinetic + energy → kinetic-energy)
  sandhi-avastha    → avastha qualification (initial/final/angular + concept)
  sandhi-bandhana   → reattribute sankhya/matra after rename
  vibhakti-shashthi → entity + ownership from possession signal
  vishesa-instance  → owned concept + label → typed rashi instance
  vishesa-bandhana  → move bindings from concept to instance
  sankhya-bandha    → bind floating asprista-sankhya to preceding concept

fixpoint runs avrti-refine until the graph stabilises (or 20 iterations).

Protects against: avrti-refine.tantra, sandhi-*.tantra, vibhakti-*.tantra,
                  vishesa-*.tantra, sankhya-bandha.tantra

Run:
    cd /home/abe/agent_x && .venv/bin/pytest vyakarana/tests/test_avrti.py -v --socket /tmp/vy.sock
"""

import json
import pytest


def tl(graph: list) -> str:
    """Convert Python list to JSON string for inline tantra expressions."""
    return json.dumps(graph)


def sig_triples(graph: list) -> list:
    """Filter out kosha-janya triples (noise) for cleaner assertions."""
    return [
        t
        for t in graph
        if isinstance(t, list) and len(t) >= 2 and t[1] != "kosha-janya"
    ]


# ── empty graph ───────────────────────────────────────────────────────────────


def test_avrti_empty_graph_returns_empty(vy):
    result = vy.eval("avrti-refine []")
    assert result == [], f"expected [], got {result!r}"


# ── structure invariant ───────────────────────────────────────────────────────


def test_avrti_all_triples_have_three_elements(vy):
    g = [["kinetic", "mithya", "kinetic"], ["energy", "satya", "energy"]]
    result = vy.eval(f"avrti-refine {tl(g)}")
    for t in result:
        assert isinstance(t, list) and len(t) == 3, (
            f"expected [s, p, o] triple, got {t!r}"
        )


# ── compound resolution (sandhi-kosha) ────────────────────────────────────────


def test_avrti_mithya_plus_satya_compounds(vy):
    g = [["kinetic", "mithya", "kinetic"], ["energy", "satya", "energy"]]
    result = vy.eval(f"avrti-refine {tl(g)}")
    assert vy.has_triple(result, subj="kinetic-energy", pred="satya"), (
        f"expected [kinetic-energy, satya, kinetic-energy], got {sig_triples(result)!r}"
    )


def test_avrti_compound_no_kosha_miss(vy):
    # "ball" + "energy" → no kosha compound "ball-energy"
    g = [["ball", "mithya", "ball"], ["energy", "satya", "energy"]]
    result = vy.eval(f"avrti-refine {tl(g)}")
    assert vy.has_triple(result, subj="ball", pred="mithya"), (
        f"'ball' should stay mithya when no kosha compound found"
    )
    assert vy.has_triple(result, subj="energy", pred="satya"), (
        f"'energy' satya should be preserved"
    )


def test_avrti_two_mithya_words_without_compound_unchanged(vy):
    g = [["mass", "mithya", "mass"], ["energy", "mithya", "energy"]]
    result = vy.eval(f"avrti-refine {tl(g)}")
    sig = sig_triples(result)
    assert vy.has_triple(sig, subj="mass", pred="mithya"), (
        f"'mass' (mithya) should stay mithya when no satya concept paired"
    )
    assert vy.has_triple(sig, subj="energy", pred="mithya"), (
        f"'energy' (mithya) should stay mithya"
    )


# ── avastha qualification (sandhi-avastha) ────────────────────────────────────


@pytest.mark.parametrize(
    "qualifier,concept,expected",
    [
        ("initial", "velocity", "initial-velocity"),
        ("final", "velocity", "final-velocity"),
        ("angular", "velocity", "angular-velocity"),
        ("initial", "acceleration", "initial-acceleration"),
    ],
)
def test_avrti_avastha_synthesises_compound(vy, qualifier, concept, expected):
    g = [[qualifier, "mithya", qualifier], [concept, "satya", concept]]
    result = vy.eval(f"avrti-refine {tl(g)}")
    assert vy.has_triple(result, subj=expected, pred="satya"), (
        f"expected [{expected}, satya, {expected}], got {sig_triples(result)!r}"
    )


def test_avrti_no_tense_no_avastha_synthesis(vy):
    # plain "velocity" without a qualifier — stays as velocity
    g = [["velocity", "satya", "velocity"]]
    result = vy.eval(f"avrti-refine {tl(g)}")
    assert vy.has_triple(result, subj="velocity", pred="satya"), (
        f"expected [velocity, satya, velocity] unchanged"
    )
    assert not vy.has_triple(result, subj="initial-velocity", pred="satya"), (
        f"initial-velocity should not appear without qualifier"
    )


# ── sankhya reattribute (sandhi-bandhana) ─────────────────────────────────────


def test_avrti_sankhya_reattributed_to_compound(vy):
    # [final, mithya] + [velocity, satya] + [velocity, sankhya, 20]
    # → sankhya moves from velocity to final-velocity
    g = [
        ["final", "mithya", "final"],
        ["velocity", "satya", "velocity"],
        ["velocity", "sankhya", "20."],
    ]
    result = vy.eval(f"avrti-refine {tl(g)}")
    assert vy.has_triple(result, subj="final-velocity", pred="sankhya"), (
        f"sankhya should be reattributed to final-velocity, got {sig_triples(result)!r}"
    )


def test_avrti_stale_sankhya_removed_after_reattribute(vy):
    g = [
        ["final", "mithya", "final"],
        ["velocity", "satya", "velocity"],
        ["velocity", "sankhya", "20."],
    ]
    result = vy.eval(f"avrti-refine {tl(g)}")
    stale = vy.all_triples(result, subj="velocity", pred="sankhya")
    assert len(stale) == 0, (
        f"stale [velocity, sankhya] should be removed after reattribute, got {stale!r}"
    )


# ── sankhya-bandha: unitless float binds to preceding concept ─────────────────


def test_avrti_unitless_sankhya_binds_to_concept(vy):
    # asprista-sankhya after a satya concept → binds to that concept
    g = [["mass", "satya", "mass"], ["5", "asprista-sankhya", "5."]]
    result = vy.eval(f"avrti-refine {tl(g)}")
    assert vy.has_triple(result, subj="mass", pred="sankhya"), (
        f"expected [mass, sankhya, 5.], got {sig_triples(result)!r}"
    )


def test_avrti_sankhya_value_preserved(vy):
    g = [["mass", "satya", "mass"], ["5", "asprista-sankhya", "5."]]
    result = vy.eval(f"avrti-refine {tl(g)}")
    t = vy.find_triple(result, subj="mass", pred="sankhya")
    assert t is not None, "mass sankhya triple not found"
    assert vy.approx_eq(t[2], 5.0), f"expected value 5.0, got {t[2]!r}"


# ── bhuta-kaala passthrough ───────────────────────────────────────────────────


def test_avrti_bhuta_kaala_triple_preserved(vy):
    g = [
        ["mass", "satya", "mass"],
        ["bhuta-kaala", "bhuta-kaala", "bhuta-kaala"],
    ]
    result = vy.eval(f"avrti-refine {tl(g)}")
    assert vy.has_triple(result, pred="bhuta-kaala"), (
        f"bhuta-kaala triple should survive avrti-refine, got {sig_triples(result)!r}"
    )


# ── fixpoint ──────────────────────────────────────────────────────────────────


def test_fixpoint_terminates_on_kinetic_energy(vy):
    g = [["kinetic", "mithya", "kinetic"], ["energy", "satya", "energy"]]
    result = vy.eval(f"fixpoint {tl(g)} avrti-refine")
    assert vy.has_triple(result, subj="kinetic-energy", pred="satya"), (
        f"fixpoint should resolve kinetic-energy, got {sig_triples(result)!r}"
    )


def test_fixpoint_stable_graph_terminates_quickly(vy):
    # already-stable graph: fixpoint should terminate (no infinite loop)
    g = [["mass", "satya", "mass"]]
    result = vy.eval(f"fixpoint {tl(g)} avrti-refine")
    assert vy.has_triple(result, subj="mass", pred="satya"), (
        f"stable graph should be unchanged by fixpoint, got {sig_triples(result)!r}"
    )


def test_fixpoint_result_is_non_empty(vy):
    g = [["kinetic", "mithya", "kinetic"], ["energy", "satya", "energy"]]
    result = vy.eval(f"fixpoint {tl(g)} avrti-refine")
    assert isinstance(result, list) and len(result) > 0, (
        f"fixpoint result should be non-empty, got {result!r}"
    )


# ── idempotency ───────────────────────────────────────────────────────────────


def test_avrti_second_pass_same_length(vy):
    # running avrti-refine twice on a stable graph shouldn't change it
    g = [["kinetic-energy", "satya", "kinetic-energy"]]
    r1 = vy.eval(f"avrti-refine {tl(g)}")
    r2 = vy.eval(f"avrti-refine {tl(r1)}")
    sig1 = sig_triples(r1)
    sig2 = sig_triples(r2)
    assert len(sig1) == len(sig2), (
        f"second pass changed graph size: {len(sig1)} → {len(sig2)}"
    )


# ── entity ownership via "has" (not yet built) ────────────────────────────────


def test_avrti_entity_owns_property_via_has(vy):
    # sandhi-viveka (inside build-question-graph) promotes "has" →
    # [has, shashthi-vibhakti, shashthi-vibhakti] before avrti-refine runs.
    # vibhakti-shashthi then recognises the signal and establishes ownership.
    result = vy.eval('fixpoint (build-question-graph "ball has mass") avrti-refine')
    assert vy.has_triple(result, subj="ball", pred="prathama-vibhakti"), (
        f"ball should get prathama-vibhakti (entity subject)"
    )
    assert vy.has_triple(result, subj="mass", pred="shashthi-vibhakti"), (
        f"mass should get shashthi-vibhakti (owned by ball)"
    )


# ── dvandva collection (not yet built) ────────────────────────────────────────


@pytest.mark.xfail(
    strict=True,
    reason="dvandva collection not implemented: consecutive asprista-sankhya under "
    "a satya concept should form a dvandva group — rule missing from avrti-refine",
)
def test_avrti_dvandva_collection_of_two_values(vy):
    g = [
        ["mass", "satya", "mass"],
        ["3", "asprista-sankhya", "3."],
        ["5", "asprista-sankhya", "5."],
    ]
    result = vy.eval(f"fixpoint {tl(g)} avrti-refine")
    # both values should be grouped under mass as a dvandva
    dvandva = vy.all_triples(result, subj="mass", pred="dvandva")
    assert len(dvandva) == 2, f"expected 2 dvandva triples for mass, got {dvandva!r}"
