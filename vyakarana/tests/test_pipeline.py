"""test_pipeline.py — end-to-end integration: BQG → avrti → match.

Tests the full pipeline: natural language sentence → BQG → fixpoint(avrti-refine)
→ match-mantra. These tests catch regressions that span multiple subsystems.

Each test represents a complete user query flow.

Protects against: regressions across build-question-graph, avrti-refine,
                  match-mantra, materialize-question-graph

Run:
    cd /home/abe/agent_x && .venv/bin/pytest vyakarana/tests/test_pipeline.py -v --socket /tmp/vy.sock
"""

import json
import pytest


def full_pipeline(vy, sentence: str) -> tuple[list, list]:
    """Run BQG → fixpoint(avrti-refine). Return (raw_graph, refined_graph)."""
    raw = vy.eval(f'build-question-graph "{sentence}"')
    refined = vy.eval(f"fixpoint {json.dumps(raw)} avrti-refine")
    return raw, refined


def sig(graph: list) -> list:
    """Filter out kosha-janya triples for cleaner assertions."""
    return [
        t
        for t in graph
        if isinstance(t, list) and len(t) >= 2 and t[1] != "kosha-janya"
    ]


# ── BQG output sanity ─────────────────────────────────────────────────────────


def test_pipeline_find_force_has_force_satya(vy):
    raw, refined = full_pipeline(vy, "find force")
    assert vy.has_triple(raw, subj="force", pred="satya"), (
        "BQG should emit satya for 'force'"
    )


def test_pipeline_kinetic_energy_compound_resolved(vy):
    # BQG: kinetic=mithya, energy=satya
    # After avrti: kinetic-energy=satya
    raw, refined = full_pipeline(vy, "what is kinetic energy")
    assert vy.has_triple(raw, subj="kinetic", pred="mithya"), (
        "BQG: 'kinetic' should be mithya"
    )
    assert vy.has_triple(refined, subj="kinetic-energy", pred="satya"), (
        f"After avrti fixpoint: kinetic-energy should be satya, "
        f"got {sig(refined)[:5]!r}"
    )


# ── avrti-refine: avastha resolution in context ───────────────────────────────


def test_pipeline_initial_velocity_resolved(vy):
    raw, refined = full_pipeline(vy, "initial velocity 5 final velocity 20")
    assert vy.has_triple(refined, subj="initial-velocity", pred="satya"), (
        f"initial-velocity should be satya after avrti, got {sig(refined)[:5]!r}"
    )
    assert vy.has_triple(refined, subj="final-velocity", pred="satya"), (
        f"final-velocity should be satya after avrti, got {sig(refined)[:5]!r}"
    )


def test_pipeline_initial_velocity_sankhya_reattributed(vy):
    raw, refined = full_pipeline(vy, "initial velocity 5 final velocity 20")
    assert vy.has_triple(refined, subj="initial-velocity", pred="sankhya"), (
        "sankhya 5 should be reattributed to initial-velocity"
    )
    assert vy.has_triple(refined, subj="final-velocity", pred="sankhya"), (
        "sankhya 20 should be reattributed to final-velocity"
    )


# ── full pipeline: BQG → avrti → match ───────────────────────────────────────


def test_pipeline_find_kinetic_energy_matches(vy):
    raw, refined = full_pipeline(vy, "find kinetic energy given mass 5 and velocity 10")
    result = vy.eval(f"match-mantra {json.dumps(refined)}")
    assert isinstance(result, list) and len(result) == 2, (
        f"expected [name, args], got {result!r}"
    )
    assert result[0] == "kinetic-energy-mantra", (
        f"expected kinetic-energy-mantra, got {result[0]!r}"
    )


def test_pipeline_find_momentum_matches(vy):
    raw, refined = full_pipeline(vy, "find momentum given mass 3 and velocity 4")
    result = vy.eval(f"match-mantra {json.dumps(refined)}")
    assert isinstance(result, list) and len(result) == 2
    assert result[0] == "momentum-mantra", (
        f"expected momentum-mantra, got {result[0]!r}"
    )


def test_pipeline_find_force_newton_matches(vy):
    raw, refined = full_pipeline(vy, "find force given mass 2 and acceleration 5")
    result = vy.eval(f"match-mantra {json.dumps(refined)}")
    assert isinstance(result, list) and len(result) == 2
    assert result[0] == "newton-second-law-motion", (
        f"expected newton-second-law-motion, got {result[0]!r}"
    )


def test_pipeline_partial_args_no_match(vy):
    # only mass provided — match should fail
    raw, refined = full_pipeline(vy, "find kinetic energy given mass 5")
    result = vy.eval(f"match-mantra {json.dumps(refined)}")
    assert result == [], f"expected [] for incomplete args, got {result!r}"


# ── satya bridge: unit reachable via kosha walk ────────────────────────────────


def test_pipeline_satya_bridge_mass_to_kilogram(vy):
    # From the refined graph, mass has a satya triple; kosha walk reaches kilogram
    raw, refined = full_pipeline(vy, "find mass")
    assert vy.has_triple(refined, subj="mass", pred="satya"), (
        "mass should be satya after pipeline"
    )
    # via kosha walk: mass → matra → kilogram
    units = vy.walk("mass", "matra")
    assert "kilogram" in units, f"kilogram should be reachable via matra from mass"


# ── kosha-expand surfaces related concepts ─────────────────────────────────────


def test_pipeline_kosha_expand_in_bqg_surfaces_momentum(vy):
    # kosha-expand runs after avrti-refine in anuvada-ganana, not inside BQG
    # the enriched graph (post kosha-expand) surfaces related concepts
    enriched = vy.eval(
        'kosha-expand (fixpoint (build-question-graph "find mass velocity") avrti-refine)'
    )
    janya_objs = {
        t[2]
        for t in enriched
        if isinstance(t, list) and len(t) >= 3 and t[1] == "kosha-janya"
    }
    assert "momentum" in janya_objs or "kinetic-energy" in janya_objs, (
        f"expected momentum or kinetic-energy in kosha-janya expansion after kosha-expand, got {janya_objs}"
    )


# ── entity ownership (not yet built) ─────────────────────────────────────────


def test_pipeline_entity_owns_mass(vy):
    raw, refined = full_pipeline(vy, "ball A has mass 5 kg")
    # ball should be an entity that owns mass
    assert vy.has_triple(refined, pred="prathama-vibhakti"), (
        f"expected entity (prathama-vibhakti) in graph"
    )
    assert vy.has_triple(refined, pred="shashthi-vibhakti"), (
        f"expected ownership (shashthi-vibhakti) in graph"
    )


def test_pipeline_suvat_acceleration(vy):
    # "train T: u=5, v=20, t=3 → find acceleration"
    raw, refined = full_pipeline(
        vy,
        "train T has initial velocity 5 and final velocity 20 and time 3 find acceleration",
    )
    result = vy.eval(f"match-mantra {json.dumps(refined)}")
    assert isinstance(result, list) and len(result) == 2
    assert "acceleration" in result[0].lower(), (
        f"expected acceleration mantra, got {result[0]!r}"
    )
