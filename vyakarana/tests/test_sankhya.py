"""test_sankhya.py — sankhya: the number finding its concept.

Sankhya is magnitude — the numeric aspect a rashi may carry. A number
arriving in a sentence is asprista-sankhya: untouched, floating, not yet
bound to anything. It hovers near the concept that precedes it, waiting
to be received.

Find-context tracks the active concept — what was most recently recognised
as satya. Emit-triples binds the floating number to that concept. The number
stops being asprista (untouched) and becomes sankhya (bound magnitude).

This is the simplest act of understanding a quantity: hearing "mass 5" and
knowing that 5 belongs to mass. Not a complex inference — a basic reception.

When this fails, numbers float unbound through the pipeline. Mantras cannot
fire. Understanding cannot complete. The simplest questions return "no match."

Nam is asked: when a number arrives near a concept, do you receive it?

Protects against: emit-triples.tantra, find-context.tantra

Run:
    cd /home/abe/agent_x && .venv/bin/pytest vyakarana/tests/test_sankhya.py -v --socket /tmp/vy.sock
"""

import json
import pytest


def tl(graph: list) -> str:
    """Convert Python list to JSON string for inline tantra expressions."""
    return json.dumps(graph)


# ── find-context ──────────────────────────────────────────────────────────────


def test_find_context_empty_graph(vy):
    result = vy.eval("find-context []")
    assert result == ["", ""], f"expected ['', ''], got {result!r}"


def test_find_context_returns_two_element_list(vy):
    result = vy.eval("find-context []")
    assert isinstance(result, list) and len(result) == 2, (
        f"expected [active, pending], got {result!r}"
    )


def test_find_context_satya_triple_sets_active(vy):
    g = [["mass", "satya", "mass"]]
    result = vy.eval(f"find-context {tl(g)}")
    assert result[0] == "mass", f"expected active='mass', got {result!r}"
    assert result[1] == "", f"expected pending='', got {result!r}"


def test_find_context_asprista_sankhya_sets_pending(vy):
    g = [["mass", "satya", "mass"], ["5", "asprista-sankhya", "5."]]
    result = vy.eval(f"find-context {tl(g)}")
    assert result[0] == "mass", f"expected active='mass', got {result[0]!r}"
    assert vy.approx_eq(result[1], 5.0), f"expected pending≈5.0, got {result[1]!r}"


def test_find_context_last_satya_is_active(vy):
    # active is the MOST RECENT satya concept
    g = [["mass", "satya", "mass"], ["velocity", "satya", "velocity"]]
    result = vy.eval(f"find-context {tl(g)}")
    assert result[0] == "velocity", (
        f"expected last satya 'velocity' as active, got {result[0]!r}"
    )


def test_find_context_reflexive_satya(vy):
    # satya triple is [node, satya, node] — both s and o are the same node
    g = [["mass", "satya", "mass"]]
    result = vy.eval(f"find-context {tl(g)}")
    assert result[0] == "mass", (
        f"reflexive satya should set active='mass', got {result[0]!r}"
    )


def test_find_context_non_satya_triple_ignored(vy):
    # mithya triple doesn't set active concept
    g = [["ball", "mithya", "ball"]]
    result = vy.eval(f"find-context {tl(g)}")
    # no satya → active should be empty (or not "ball")
    assert result[0] != "ball", (
        f"mithya triple should not set active concept, got {result[0]!r}"
    )


# ── find-context: pending clear after non-asprista-sankhya ───────────────────


def test_find_context_pending_cleared_when_last_triple_not_sankhya(vy):
    # only the LAST triple counts for pending — if it's not asprista-sankhya, pending=""
    g = [
        ["mass", "satya", "mass"],
        ["5", "asprista-sankhya", "5."],
        ["velocity", "satya", "velocity"],  # last triple is satya, not sankhya
    ]
    result = vy.eval(f"find-context {tl(g)}")
    assert result[1] == "", (
        f"pending should be cleared when last triple is not asprista-sankhya, "
        f"got {result[1]!r}"
    )


# ── emit-triples: satya for known concept ────────────────────────────────────


def test_emit_triples_kosha_concept_emits_satya(vy):
    # kosha node → [node, satya, node]
    # info format: [node, role, layer, num-val, unit-node]
    result = vy.eval(
        'emit-triples "mass" ["mass", "concept", "kosha", "", ""] ["", ""]'
    )
    assert vy.has_triple(result, subj="mass", pred="satya"), (
        f"expected [mass, satya, mass], got {result!r}"
    )


def test_emit_triples_satya_obj_equals_subj(vy):
    result = vy.eval(
        'emit-triples "velocity" ["velocity", "concept", "kosha", "", ""] ["", ""]'
    )
    t = vy.find_triple(result, pred="satya")
    assert t is not None, f"satya triple not found in {result!r}"
    assert t[0] == t[2], f"satya triple not reflexive: {t!r}"


# ── emit-triples: mithya for unknown word ────────────────────────────────────


def test_emit_triples_unknown_word_emits_mithya(vy):
    result = vy.eval('emit-triples "xyzfoo" ["", "concept", "", "", ""] ["", ""]')
    assert vy.has_triple(result, pred="mithya"), (
        f"expected mithya triple for unknown word, got {result!r}"
    )


# ── emit-triples: intent role ─────────────────────────────────────────────────


def test_emit_triples_intent_emits_vidhi_kaala(vy):
    result = vy.eval('emit-triples "what" ["what", "intent", "kosha", "", ""] ["", ""]')
    assert vy.has_triple(result, pred="vidhi-kaala"), (
        f"expected vidhi-kaala triple for intent role, got {result!r}"
    )


def test_emit_triples_intent_triple_has_solve_for(vy):
    result = vy.eval('emit-triples "what" ["what", "intent", "kosha", "", ""] ["", ""]')
    t = vy.find_triple(result, pred="vidhi-kaala")
    assert t is not None
    assert t[2] == "solve-for", f"expected obj='solve-for', got {t[2]!r}"


# ── emit-triples: asprista-sankhya for bare number ───────────────────────────


def test_emit_triples_number_emits_asprista_sankhya(vy):
    result = vy.eval('emit-triples "5" ["", "concept", "", "5", ""] ["", ""]')
    assert vy.has_triple(result, pred="asprista-sankhya"), (
        f"expected asprista-sankhya triple, got {result!r}"
    )


def test_emit_triples_number_value_in_obj(vy):
    result = vy.eval('emit-triples "5" ["", "concept", "", "5", ""] ["", ""]')
    t = vy.find_triple(result, pred="asprista-sankhya")
    assert t is not None
    assert vy.approx_eq(t[2], 5.0), f"expected value 5.0, got {t[2]!r}"


# ── emit-triples: unit consumes pending → sankhya + matra ────────────────────


def test_emit_triples_unit_consumes_pending(vy):
    # when active="mass", pending="5.", word="kilogram" (a unit)
    # should produce [mass, sankhya, 5] and [mass, matra, kilogram]
    result = vy.eval(
        'emit-triples "kilogram" '
        '["kilogram", "concept", "kosha", "", "kilogram"] '
        '["mass", "5."]'
    )
    assert vy.has_triple(result, subj="mass", pred="sankhya"), (
        f"expected [mass, sankhya, ...] when unit consumes pending, got {result!r}"
    )
    assert vy.has_triple(result, subj="mass", pred="matra"), (
        f"expected [mass, matra, kilogram], got {result!r}"
    )


# ── emit-triples: non-unit concept does not consume pending ───────────────────


def test_emit_triples_concept_not_unit_does_not_consume_pending(vy):
    # "velocity" is a concept not a unit — should NOT consume the pending number
    result = vy.eval(
        'emit-triples "velocity" '
        '["velocity", "concept", "kosha", "", ""] '
        '["mass", "5."]'
    )
    # should emit satya triple, not sankhya
    assert vy.has_triple(result, pred="satya"), (
        f"expected satya for concept, got {result!r}"
    )
    assert not vy.has_triple(result, pred="sankhya"), (
        f"velocity should not consume pending as matra, got {result!r}"
    )
