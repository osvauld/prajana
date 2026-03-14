"""test_match.py — match-mantra: formula matching and disambiguation.

Tests the match-mantra tantra that takes a refined question graph and returns
the best matching mantra (formula) with its argument values.

Key observations from probing:
- match-mantra needs a full BQG→fixpoint graph (with kosha-janya triples)
  to work correctly; a bare graph with just satya+sankhya triples returns []
- Return format: [mantra_name, [arg0, arg1, ...]] or []
- Disambiguation via solve-for: vidhi-kaala triple selects the target concept
- mass + velocity → kinetic-energy-mantra (if solve-for=kinetic-energy)
- mass + velocity → momentum-mantra (if solve-for=momentum)
- mass + acceleration → newton-second-law-motion
- Partial args (one missing) → []

Protects against: match-mantra.tantra

Run:
    cd /home/abe/agent_x && .venv/bin/pytest vyakarana/tests/test_match.py -v --socket /tmp/vy.sock
"""

import json
import pytest


def bqg_then_avrti(vy, sentence: str) -> list:
    """Run the full BQG→fixpoint pipeline and return the refined graph.

    This is the correct input for match-mantra: it includes both the domain
    triples (satya, sankhya) and the kosha-janya triples that match-mantra
    uses to find the relevant mantra.
    """
    g = vy.eval(f'build-question-graph "{sentence}"')
    return vy.eval(f"fixpoint {json.dumps(g)} avrti-refine")


# ── basic matching ────────────────────────────────────────────────────────────


def test_match_kinetic_energy_returns_mantra_name(vy):
    g = bqg_then_avrti(vy, "find kinetic energy given mass 5 and velocity 10")
    result = vy.eval(f"match-mantra {json.dumps(g)}")
    assert isinstance(result, list) and len(result) == 2, (
        f"expected [name, args], got {result!r}"
    )
    assert result[0] == "kinetic-energy-mantra", (
        f"expected kinetic-energy-mantra, got {result[0]!r}"
    )


def test_match_kinetic_energy_returns_two_args(vy):
    g = bqg_then_avrti(vy, "find kinetic energy given mass 5 and velocity 10")
    result = vy.eval(f"match-mantra {json.dumps(g)}")
    assert isinstance(result[1], list) and len(result[1]) == 2, (
        f"expected 2 args [mass_val, velocity_val], got {result[1]!r}"
    )


def test_match_kinetic_energy_arg_values(vy):
    g = bqg_then_avrti(vy, "find kinetic energy given mass 5 and velocity 10")
    result = vy.eval(f"match-mantra {json.dumps(g)}")
    args = result[1]
    values = sorted([float(a) for a in args])
    assert vy.approx_eq(values[0], 5.0), f"expected mass=5.0, got {values[0]}"
    assert vy.approx_eq(values[1], 10.0), f"expected velocity=10.0, got {values[1]}"


def test_match_momentum_mantra(vy):
    g = bqg_then_avrti(vy, "find momentum given mass 3 and velocity 4")
    result = vy.eval(f"match-mantra {json.dumps(g)}")
    assert isinstance(result, list) and len(result) == 2
    assert result[0] == "momentum-mantra", (
        f"expected momentum-mantra, got {result[0]!r}"
    )


def test_match_newton_second_law(vy):
    g = bqg_then_avrti(vy, "find force given mass 2 and acceleration 5")
    result = vy.eval(f"match-mantra {json.dumps(g)}")
    assert isinstance(result, list) and len(result) == 2
    assert result[0] == "newton-second-law-motion", (
        f"expected newton-second-law-motion, got {result[0]!r}"
    )


# ── no match cases ────────────────────────────────────────────────────────────


def test_match_missing_arg_returns_empty(vy):
    # only mass provided — velocity missing → no kinetic-energy-mantra match
    g = bqg_then_avrti(vy, "find kinetic energy given mass 5")
    result = vy.eval(f"match-mantra {json.dumps(g)}")
    assert result == [], f"expected [] for incomplete args, got {result!r}"


def test_match_no_concept_returns_empty(vy):
    # only unknown words → no satya concepts → no match
    g = bqg_then_avrti(vy, "xyzfoobar blorp snazzle")
    result = vy.eval(f"match-mantra {json.dumps(g)}")
    assert result == [], f"expected [] for no concept, got {result!r}"


# ── disambiguation via solve-for ──────────────────────────────────────────────


def test_match_solve_for_kinetic_energy_not_momentum(vy):
    # mass + velocity present; solve-for = kinetic-energy → kinetic-energy-mantra
    g = bqg_then_avrti(vy, "find kinetic energy given mass 5 and velocity 10")
    result = vy.eval(f"match-mantra {json.dumps(g)}")
    assert result[0] == "kinetic-energy-mantra", (
        f"with solve-for=kinetic-energy, should not match momentum-mantra"
    )


def test_match_solve_for_momentum_not_kinetic_energy(vy):
    # mass + velocity present; solve-for = momentum → momentum-mantra
    g = bqg_then_avrti(vy, "find momentum given mass 3 and velocity 4")
    result = vy.eval(f"match-mantra {json.dumps(g)}")
    assert result[0] == "momentum-mantra", (
        f"with solve-for=momentum, should not match kinetic-energy-mantra"
    )


# ── result structure ──────────────────────────────────────────────────────────


def test_match_result_is_list(vy):
    g = bqg_then_avrti(vy, "find kinetic energy given mass 5 and velocity 10")
    result = vy.eval(f"match-mantra {json.dumps(g)}")
    assert isinstance(result, list), f"expected list, got {type(result).__name__}"


def test_match_name_is_non_empty_string(vy):
    g = bqg_then_avrti(vy, "find kinetic energy given mass 5 and velocity 10")
    result = vy.eval(f"match-mantra {json.dumps(g)}")
    assert isinstance(result[0], str) and len(result[0]) > 0, (
        f"expected non-empty string name, got {result[0]!r}"
    )


def test_match_args_is_list(vy):
    g = bqg_then_avrti(vy, "find kinetic energy given mass 5 and velocity 10")
    result = vy.eval(f"match-mantra {json.dumps(g)}")
    assert isinstance(result[1], list), (
        f"expected list of args, got {type(result[1]).__name__}"
    )


# ── solve-for after vidhi-kaala (not yet correct) ─────────────────────────────


@pytest.mark.xfail(
    strict=True,
    reason="match solve-for heuristic bug: solve-for target is first satya triple "
    "overall, not the first satya after vidhi-kaala. When 'what' is a satya "
    "kosha node before the target concept, match picks 'what' as solve-for "
    "instead of the intended concept.",
)
def test_match_what_sentence_finds_correct_mantra(vy):
    # "what is kinetic energy..." — 'what' is satya before kinetic-energy
    # the first satya after vidhi-kaala should be kinetic-energy, not what
    g = bqg_then_avrti(vy, "what is kinetic energy given mass 5 and velocity 10")
    result = vy.eval(f"match-mantra {json.dumps(g)}")
    assert isinstance(result, list) and len(result) == 2
    assert result[0] == "kinetic-energy-mantra", (
        f"expected kinetic-energy-mantra, got {result[0]!r}"
    )
