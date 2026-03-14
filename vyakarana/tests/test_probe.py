"""test_probe.py — smoke tests across all groups before full suite is written.

2-3 tests per group, covering the key primitives of each layer.
Run this first to confirm the infrastructure works end-to-end before
expanding to the full 11-module suite.

    cd vyakarana/tests && ../../.venv/bin/pytest test_probe.py -v

## What we learned from the first run

### Infrastructure rule: always use json.dumps() for inline graphs
    f'avrti-refine {json.dumps(g)}'   ✓ double-quoted strings
    f'avrti-refine {g}'               ✗ Python single-quotes → parser wraps them

### xfail = not yet built (feature is missing, test documents the intention)
The old tantra suite had tests that always failed because the feature wasn't
implemented yet. Those become xfail here. When the feature is built, pytest
errors on an unexpected pass, forcing promotion to a real test.

### Current baseline (from old tantra runner):
  PASS: avrti compound/avastha/fixpoint, match all, sankhya find-context,
        kosha-expand, materialize, graph primitives, BQG concept/mithya
  FAIL (not yet built):
    - sandhi-viveka verb promotion (has→shashthi, was→bhuta-kaala)
    - BQG vidhi-kaala intent triple for "what"
    - BQG/emit-triples unit binding (sankhya+matra from value+unit)
    - lookup-word abbreviations (kg, N)
    - entity ownership via "has" (avrti R8/R9 rules)
    - dvandva collection, "respectively" zip
    - full pipeline end-to-end with entity+match
"""

import json
import pytest


def tl(graph: list) -> str:
    """Convert a Python list to a JSON string for use in tantra expressions.

    Always use this when passing a constructed graph to vy.eval():
        vy.eval(f'avrti-refine {tl(g)}')
    """
    return json.dumps(graph)


# ── Group 1: interpreter ─────────────────────────────────────────────────────


def test_reduce_numeric_sum(vy):
    result = vy.eval("reduce [1, 2, 3] 0 (fn a x -> add a x)")
    assert vy.approx_eq(result, 6.0), f"expected 6.0, got {result!r}"


def test_map_over_list(vy):
    result = vy.eval('map ["a", "b", "c"] (fn x -> x)')
    assert result == ["a", "b", "c"], f"got {result!r}"


def test_split_numeric_value_and_unit(vy):
    result = vy.eval('split-numeric "5kg"')
    assert vy.approx_eq(result[0], 5.0), f"value: {result[0]!r}"
    assert result[1] == "kg", f"unit: {result[1]!r}"


def test_div_by_zero_returns_zero(vy):
    result = vy.eval("div 5 0")
    assert vy.approx_eq(result, 0.0), f"expected 0.0, got {result!r}"


# ── Group 2: word index ───────────────────────────────────────────────────────


def test_lookup_direct_hit(vy):
    assert vy.eval('lookup-word "mass"') == "mass"


def test_lookup_direct_hit_kilogram(vy):
    assert vy.eval('lookup-word "kilogram"') == "kilogram"


def test_lookup_plural_ies(vy):
    assert vy.eval('lookup-word "velocities"') == "velocity"


def test_lookup_plural_s(vy):
    assert vy.eval('lookup-word "metres"') == "metre"


def test_lookup_miss_returns_null(vy):
    assert vy.eval('lookup-word "xyzfoobar"') is None


def test_lookup_abbreviation_kg(vy):
    assert vy.eval('lookup-word "kg"') == "kilogram"


# ── Group 3: graph primitives ─────────────────────────────────────────────────


def test_walk_mass_matra(vy):
    assert "kilogram" in vy.walk("mass", "matra")


def test_walk_in_kilogram_matra(vy):
    assert "mass" in vy.walk_in("kilogram", "matra")


def test_walk_unknown_node_returns_empty(vy):
    assert vy.walk("unknown-node-xyz-abc", "satya") == []


def test_register_dimension_idempotent(vy):
    idx1 = vy.eval('register-dimension "satya"')
    idx2 = vy.eval('register-dimension "satya"')
    assert idx1 == idx2, f"not idempotent: {idx1!r} vs {idx2!r}"
    assert idx1 >= 10, f"expected >= 10, got {idx1!r}"


# ── Group 4: sandhi-viveka ────────────────────────────────────────────────────


def test_sandhi_empty_graph(vy):
    assert vy.eval("sandhi-viveka []") == []


def test_sandhi_mithya_passthrough(vy):
    # non-grammar mithya word passes through unchanged
    g = [["ball", "mithya", "ball"]]
    result = vy.eval(f"sandhi-viveka {tl(g)}")
    assert result[0][1] == "mithya"


def test_sandhi_satya_passthrough(vy):
    # satya triple passes through unchanged
    g = [["mass", "satya", "mass"]]
    result = vy.eval(f"sandhi-viveka {tl(g)}")
    assert result[0][1] == "satya"


def test_sandhi_has_promoted_to_shashthi(vy):
    g = [["has", "mithya", "has"]]
    result = vy.eval(f"sandhi-viveka {tl(g)}")
    assert result[0][1] == "shashthi-vibhakti"


def test_sandhi_was_promoted_to_bhuta_kaala(vy):
    g = [["was", "mithya", "was"]]
    result = vy.eval(f"sandhi-viveka {tl(g)}")
    assert result[0][1] == "bhuta-kaala"


# ── Group 5: build-question-graph ────────────────────────────────────────────


def test_bqg_known_concept_is_satya(vy):
    g = vy.eval('build-question-graph "find force"')
    assert vy.has_triple(g, subj="force", pred="satya")


def test_bqg_unknown_word_is_mithya(vy):
    g = vy.eval('build-question-graph "xyzfoobar"')
    assert vy.has_triple(g, pred="mithya")


def test_bqg_number_emits_asprista_sankhya(vy):
    # BQG emits asprista-sankhya; avrti-refine binds it to the concept
    g = vy.eval('build-question-graph "mass 5 kg"')
    assert vy.has_triple(g, pred="asprista-sankhya")


def test_bqg_unit_binding(vy):
    # "mass 5 kg" should bind matra=kilogram directly in BQG output
    g = vy.eval('build-question-graph "mass 5 kg"')
    assert vy.has_triple(g, subj="mass", pred="matra")


def test_bqg_what_emits_vidhi_kaala(vy):
    g = vy.eval('build-question-graph "what is force"')
    assert vy.has_triple(g, pred="vidhi-kaala")


# ── Group 6: avrti-refine ─────────────────────────────────────────────────────


def test_avrti_compound_kinetic_energy(vy):
    g = [["kinetic", "mithya", "kinetic"], ["energy", "satya", "energy"]]
    result = vy.eval(f"avrti-refine {tl(g)}")
    assert vy.has_triple(result, subj="kinetic-energy", pred="satya"), (
        f"compound not formed, got {[t for t in result if t[1] != 'kosha-janya']!r}"
    )


def test_avrti_no_compound_miss(vy):
    g = [["ball", "mithya", "ball"], ["energy", "satya", "energy"]]
    result = vy.eval(f"avrti-refine {tl(g)}")
    assert vy.has_triple(result, subj="ball", pred="mithya"), f"ball should stay mithya"


def test_avrti_avastha_initial_velocity(vy):
    g = [["initial", "mithya", "initial"], ["velocity", "satya", "velocity"]]
    result = vy.eval(f"avrti-refine {tl(g)}")
    assert vy.has_triple(result, subj="initial-velocity", pred="satya"), (
        f"initial-velocity not synthesised"
    )


def test_avrti_sankhya_reattribute(vy):
    # after synthesis, sankhya moves from base concept to compound
    g = [
        ["final", "mithya", "final"],
        ["velocity", "satya", "velocity"],
        ["velocity", "sankhya", "20."],
    ]
    result = vy.eval(f"avrti-refine {tl(g)}")
    assert vy.has_triple(result, subj="final-velocity", pred="sankhya"), (
        f"sankhya not reattributed to final-velocity"
    )
    # and the stale base triple is removed
    assert not vy.has_triple(result, subj="velocity", pred="sankhya"), (
        f"stale [velocity, sankhya] should be gone"
    )


@pytest.mark.xfail(
    strict=True,
    reason="entity ownership via 'has' not yet built: avrti R8/R9 rules missing",
)
def test_avrti_entity_ownership(vy):
    g = [
        ["ball", "mithya", "ball"],
        ["has", "mithya", "has"],
        ["mass", "satya", "mass"],
    ]
    result = vy.eval(f"fixpoint {tl(g)} avrti-refine")
    assert vy.has_triple(result, subj="ball", pred="prathama-vibhakti")
    assert vy.has_triple(result, subj="mass", pred="shashthi-vibhakti")
