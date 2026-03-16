"""test_rashi.py — rashi: quantity instances in the question graph.

rashi is the quantity instance — the particular, situated thing being measured.
  [v1, vishesa, velocity]  — v1 IS a velocity (type)
  [v1, vishesa, rashi]     — v1 is a measurable quantity (general)
  [v1, sankhya, "20.0"]    — v1's magnitude is 20.0  (optional — may be absent)
  [v1, matra, metre-per-second]  — v1's unit (optional)

sankhya is NOT the quantity. it is the numeric magnitude aspect a rashi may carry.
a rashi without sankhya is a symbolic quantity — still valid, still reasoned over.

Three cases:
  A. concept with number  — [mass, sankhya, 5.]        (concept directly bound)
  B. named instance only  — [v1, vishesa, velocity]    (instance, no sankhya)
  C. named instance + number — [v1, sankhya, 20.]      (instance with magnitude)

Run:
    cd /home/abe/agent_x && .venv/bin/pytest vyakarana/tests/test_rashi.py -v --socket /tmp/vy.sock
"""

import json
import pytest


def tl(graph: list) -> str:
    return json.dumps(graph)


def sig(graph: list) -> list:
    """Filter kosha-janya noise for cleaner assertions."""
    return [
        t
        for t in graph
        if isinstance(t, list) and len(t) >= 2 and t[1] != "kosha-janya"
    ]


def bqg(vy, sentence: str) -> list:
    """Run full avrti-refine fixpoint on a sentence."""
    return vy.eval(f'fixpoint (build-question-graph "{sentence}") avrti-refine')


# ── Case A: concept directly bound to a number ────────────────────────────────
# "mass 5" — the concept mass is given numeric magnitude 5
# rashi here is mass itself (the concept acting as its own instance)


def test_concept_with_number_has_satya(vy):
    g = bqg(vy, "mass 5")
    assert vy.has_triple(g, subj="mass", pred="satya"), (
        f"mass should be resolved as satya concept, got {sig(g)!r}"
    )


def test_concept_with_number_has_sankhya(vy):
    g = bqg(vy, "mass 5")
    assert vy.has_triple(g, subj="mass", pred="sankhya"), (
        f"mass should carry sankhya after binding, got {sig(g)!r}"
    )


def test_concept_with_number_sankhya_value(vy):
    g = bqg(vy, "mass 5")
    t = vy.find_triple(g, subj="mass", pred="sankhya")
    assert t is not None, "mass sankhya triple not found"
    assert vy.approx_eq(t[2], 5.0), f"expected 5.0, got {t[2]!r}"


def test_concept_with_number_no_spurious_sankhya(vy):
    # sankhya on mass should be exactly the given value — not duplicated
    g = bqg(vy, "mass 5")
    triples = vy.all_triples(g, subj="mass", pred="sankhya")
    assert len(triples) == 1, f"expected exactly 1 sankhya for mass, got {triples!r}"


# ── concept without a number has no sankhya ───────────────────────────────────


def test_concept_without_number_has_no_sankhya(vy):
    g = bqg(vy, "find force given mass and acceleration")
    # mass and acceleration mentioned but no values given
    assert not vy.has_triple(g, subj="mass", pred="sankhya"), (
        f"mass with no number should have no sankhya, got {sig(g)!r}"
    )
    assert not vy.has_triple(g, subj="acceleration", pred="sankhya"), (
        f"acceleration with no number should have no sankhya, got {sig(g)!r}"
    )


def test_concept_without_number_still_satya(vy):
    g = bqg(vy, "find force given mass and acceleration")
    assert vy.has_triple(g, subj="mass", pred="satya"), (
        f"mass without number should still resolve as satya concept"
    )


# ── Case B: named instance without a number ───────────────────────────────────
# "ball1 has velocity v1" — v1 is a rashi instance: vishesa→velocity, NO sankhya
# this is a symbolic quantity — valid, just unmeasured


def test_named_instance_is_rashi(vy):
    g = bqg(vy, "ball1 has velocity v1 and ball2 has velocity v2")
    assert vy.has_triple(g, subj="v1", pred="vishesa", obj="rashi"), (
        f"v1 should be identified as a rashi instance, got {sig(g)!r}"
    )
    assert vy.has_triple(g, subj="v2", pred="vishesa", obj="rashi"), (
        f"v2 should be identified as a rashi instance, got {sig(g)!r}"
    )


def test_named_instance_has_no_sankhya(vy):
    # symbolic instance — no number given → no sankhya
    g = bqg(vy, "ball1 has velocity v1 and ball2 has velocity v2")
    assert not vy.has_triple(g, subj="v1", pred="sankhya"), (
        f"v1 without a number should have no sankhya, got {sig(g)!r}"
    )
    assert not vy.has_triple(g, subj="v2", pred="sankhya"), (
        f"v2 without a number should have no sankhya, got {sig(g)!r}"
    )


def test_two_instances_both_rashi(vy):
    # both v1 and v2 are rashi — two distinct instances of velocity
    g = bqg(vy, "ball1 has velocity v1 and ball2 has velocity v2")
    rashi_subjects = [
        t[0]
        for t in g
        if isinstance(t, list) and len(t) == 3 and t[1] == "vishesa" and t[2] == "rashi"
    ]
    assert "v1" in rashi_subjects, f"v1 not found in rashi subjects: {rashi_subjects!r}"
    assert "v2" in rashi_subjects, f"v2 not found in rashi subjects: {rashi_subjects!r}"


def test_named_instance_vishesa_links_to_concept(vy):
    # v1 should know it IS a velocity — [v1, vishesa, velocity]
    g = bqg(vy, "ball1 has velocity v1 and ball2 has velocity v2")
    assert vy.has_triple(g, subj="v1", pred="vishesa", obj="velocity"), (
        f"v1 should have [v1, vishesa, velocity] — its type; got {sig(g)!r}"
    )
    assert vy.has_triple(g, subj="v2", pred="vishesa", obj="velocity"), (
        f"v2 should have [v2, vishesa, velocity] — its type; got {sig(g)!r}"
    )


# ── Case C: named instance with a number ─────────────────────────────────────
# "ball1 has velocity v1 of 20" — v1 is a rashi with vishesa→velocity AND sankhya→20
# currently not handled correctly — documented as xfail


def test_named_instance_with_number_has_sankhya(vy):
    g = bqg(vy, "ball1 has velocity v1 of 20")
    assert vy.has_triple(g, subj="v1", pred="sankhya"), (
        f"v1 should carry the sankhya 20, got {sig(g)!r}"
    )


def test_named_instance_with_number_is_still_rashi(vy):
    g = bqg(vy, "ball1 has velocity v1 of 20")
    assert vy.has_triple(g, subj="v1", pred="vishesa", obj="rashi"), (
        f"v1 should still be a rashi even when it carries a sankhya, got {sig(g)!r}"
    )


# ── sankhya is the magnitude, not the identity ────────────────────────────────


def test_sankhya_is_not_the_identity_of_rashi(vy):
    # two different rashi can share the same sankhya value — they are still distinct
    g = bqg(vy, "ball1 has mass 5 and ball2 has mass 5")
    mass_sankhya = vy.all_triples(g, subj="mass", pred="sankhya")
    # both values should be 5 — the rashi are distinguished by their owner (shashthi-vibhakti)
    for t in mass_sankhya:
        assert vy.approx_eq(t[2], 5.0), f"expected sankhya 5.0, got {t[2]!r}"


def test_rashi_identity_is_vishesa_not_sankhya(vy):
    # the type (vishesa) is what makes v1 a velocity — not the number
    g = bqg(vy, "ball1 has velocity v1 and ball2 has velocity v2")
    # both v1 and v2 are velocity rashi — their identity is vishesa→velocity
    assert vy.has_triple(g, subj="v1", pred="vishesa", obj="rashi"), (
        f"v1 is a rashi regardless of having a sankhya"
    )
    assert vy.has_triple(g, subj="v2", pred="vishesa", obj="rashi"), (
        f"v2 is a rashi regardless of having a sankhya"
    )
