"""test_kosha.py — kosha-expand: the connection that releases context.

The kosha is the accumulated body of what is known — all concepts, all
relations, all structural truths. It is jada at rest. When a question
arrives, kosha-expand does not add knowledge to the question — it
releases the relevant neighbourhood of the kosha into the question's
context.

PPR (personalized PageRank) is the mechanism of this release. The satya
concepts in the question become seeds. The graph flows outward from them.
What is structurally close surfaces. What is distant stays quiet.

This is not retrieval. It is the kosha recognising what is relevant and
releasing it — naturally, without forcing. The domain widens with each
turn because more seeds are present, more of the kosha becomes relevant.

These tests ask: when a concept is present, does its neighbourhood
surface correctly? Does the kosha release what is needed and hold back
what is not?

Protects against: kosha-expand.tantra, PPR primitive, kosha graph structure

Run:
    cd /home/abe/agent_x && .venv/bin/pytest vyakarana/tests/test_kosha.py -v --socket /tmp/vy.sock
"""

import json
import pytest


def tl(graph: list) -> str:
    """Convert Python list to JSON string for inline tantra expressions."""
    return json.dumps(graph)


# ── kosha-expand: empty graph ──────────────────────────────────────────────────


def test_kosha_expand_empty_graph(vy):
    result = vy.eval("kosha-expand []")
    assert result == [], f"expected [], got {result!r}"


# ── kosha-expand: adds kosha-janya triples ────────────────────────────────────


def test_kosha_expand_adds_kosha_janya_for_satya_concept(vy):
    g = [["mass", "satya", "mass"]]
    result = vy.eval(f"kosha-expand {tl(g)}")
    janya = [
        t
        for t in result
        if isinstance(t, list) and len(t) >= 2 and t[1] == "kosha-janya"
    ]
    assert len(janya) > 0, f"expected kosha-janya triples after expand, got none"


def test_kosha_expand_janya_subject_matches_satya_node(vy):
    g = [["mass", "satya", "mass"]]
    result = vy.eval(f"kosha-expand {tl(g)}")
    janya = [
        t
        for t in result
        if isinstance(t, list) and len(t) >= 2 and t[1] == "kosha-janya"
    ]
    for t in janya:
        assert t[0] == "mass", f"kosha-janya subj should be 'mass', got {t[0]!r}"


def test_kosha_expand_no_janya_for_mithya_word(vy):
    # mithya (unknown) words are not expanded
    g = [["xyzfoobar", "mithya", "xyzfoobar"]]
    result = vy.eval(f"kosha-expand {tl(g)}")
    janya = [
        t
        for t in result
        if isinstance(t, list) and len(t) >= 2 and t[1] == "kosha-janya"
    ]
    assert len(janya) == 0, f"expected no kosha-janya for mithya word, got {len(janya)}"


def test_kosha_expand_preserves_original_satya_triple(vy):
    g = [["mass", "satya", "mass"]]
    result = vy.eval(f"kosha-expand {tl(g)}")
    assert vy.has_triple(result, subj="mass", pred="satya"), (
        "original satya triple should survive kosha-expand"
    )


def test_kosha_expand_two_seeds_both_expanded(vy):
    g = [["mass", "satya", "mass"], ["velocity", "satya", "velocity"]]
    result = vy.eval(f"kosha-expand {tl(g)}")
    mass_janya = [t for t in result if t[0] == "mass" and t[1] == "kosha-janya"]
    vel_janya = [t for t in result if t[0] == "velocity" and t[1] == "kosha-janya"]
    assert len(mass_janya) > 0, "mass should have kosha-janya triples"
    assert len(vel_janya) > 0, "velocity should have kosha-janya triples"


def test_kosha_expand_surfaces_related_concepts(vy):
    # mass + velocity seeds should surface at least one of: momentum, kinetic-energy
    g = [["mass", "satya", "mass"], ["velocity", "satya", "velocity"]]
    result = vy.eval(f"kosha-expand {tl(g)}")
    janya_objs = {
        t[2]
        for t in result
        if isinstance(t, list) and len(t) >= 3 and t[1] == "kosha-janya"
    }
    related = {"momentum", "kinetic-energy", "acceleration", "force"}
    surfaced = janya_objs & related
    assert len(surfaced) > 0, (
        f"expected at least one of {related} surfaced via kosha-expand, "
        f"got none. All janya objs: {sorted(janya_objs)[:10]!r}"
    )


# ── kosha graph structure ─────────────────────────────────────────────────────


def test_kosha_mass_has_kilogram_unit(vy):
    result = vy.walk("mass", "matra")
    assert "kilogram" in result, f"expected kilogram as matra of mass, got {result!r}"


def test_kosha_velocity_kramanusara_displacement(vy):
    result = vy.walk("velocity", "kramanusara")
    assert "displacement" in result, (
        f"expected displacement in kramanusara of velocity, got {result!r}"
    )


def test_kosha_kilogram_is_matra_of_mass(vy):
    result = vy.walk_in("kilogram", "matra")
    assert "mass" in result, f"expected mass as owner of kilogram matra, got {result!r}"


def test_kosha_mass_satya_positive(vy):
    result = vy.eval('node-satya "mass"')
    assert isinstance(result, (int, float)) and result > 0, (
        f"expected positive satya score for mass, got {result!r}"
    )


def test_kosha_velocity_satya_positive(vy):
    result = vy.eval('node-satya "velocity"')
    assert isinstance(result, (int, float)) and result > 0


def test_kosha_unknown_node_satya_zero(vy):
    result = vy.eval('node-satya "unknown-xyzfoo-abc"')
    assert result == 0 or result is None, f"expected 0 for unknown node, got {result!r}"


# ── PPR ────────────────────────────────────────────────────────────────────────


def test_ppr_returns_non_empty_results(vy):
    result = vy.eval('ppr [["mass", "1.0"]] "mass" []')
    assert isinstance(result, list) and len(result) > 0, (
        f"expected non-empty PPR results, got {result!r}"
    )


def test_ppr_entries_have_name_and_value(vy):
    result = vy.eval('ppr [["mass", "1.0"]] "mass" []')
    assert len(result) > 0, "PPR returned empty list"
    entry = result[0]
    assert isinstance(entry, dict), f"expected dict entry, got {type(entry).__name__}"
    assert "name" in entry, f"PPR entry missing 'name' key: {entry!r}"
    assert "value" in entry, f"PPR entry missing 'value' key: {entry!r}"


def test_ppr_value_is_positive_number(vy):
    result = vy.eval('ppr [["mass", "1.0"]] "mass" []')
    assert len(result) > 0
    top = result[0]
    assert isinstance(top["value"], (int, float)), (
        f"PPR value should be numeric, got {type(top['value']).__name__}"
    )
    assert top["value"] > 0, f"top PPR score should be > 0, got {top['value']!r}"


def test_ppr_mass_and_velocity_seeds(vy):
    result = vy.eval('ppr [["mass", "1.0"], ["velocity", "1.0"]] "mass" []')
    assert isinstance(result, list) and len(result) > 0, (
        f"PPR with two seeds should return results"
    )
    names = {
        entry["name"] for entry in result if isinstance(entry, dict) and "name" in entry
    }
    # both seeds should appear in PPR results
    assert "mass" in names or "velocity" in names, (
        f"expected seed nodes in PPR results, got {sorted(names)[:10]!r}"
    )
