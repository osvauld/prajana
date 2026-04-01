"""test_graph.py — kosha graph operations + axiom expansion.

Capabilities: walk, walk-in, node-satya, shabda-lookup, plural-stemming,
abbreviation, ppr, register-dimension, axiom expansion (symmetric, dual).

Protects: yantra_eval_primitives.ml, om_parser.ml, proof_graph.ml, jnana.ml
"""

import pytest


# ── walk / walk-in ─────────────────────────────────────────────────────────────


def test_walk_forward(vy):
    """walk follows an outgoing edge."""
    assert "kilogram" in vy.walk("mass", "matra")


def test_walk_in_reverse(vy):
    """walk-in follows an incoming edge."""
    assert "mass" in vy.walk_in("kilogram", "matra")


def test_walk_unknown_node(vy):
    """walk on nonexistent node returns empty list."""
    assert vy.walk("unknown-node-xyz-abc", "satya") == []


# ── node-satya ─────────────────────────────────────────────────────────────────


@pytest.mark.xfail(strict=True, reason="graph primitive: node-satya returns string not number")
def test_node_satya_known(vy):
    """Known kosha node has positive satya score."""
    score = vy.eval('node-satya "mass"')
    assert isinstance(score, (int, float)) and score > 0


@pytest.mark.xfail(strict=True, reason="graph primitive: node-satya returns string not number")
def test_node_satya_unknown(vy):
    """Unknown node has zero satya."""
    score = vy.eval('node-satya "xyzfoobar-unknown"')
    assert isinstance(score, (int, float)) and score == 0


# ── shabda-anveshana (word lookup) ─────────────────────────────────────────────


def test_shabda_direct(vy):
    """Direct word hit: 'mass' → mass."""
    assert vy.eval('shabda-anveshana "mass"') == "mass"


def test_shabda_plural(vy):
    """Plural resolution: 'velocities' → generated node or base concept."""
    result = vy.eval('shabda-anveshana "velocities"')
    assert result in ("velocity", "velocities")


def test_shabda_abbreviation(vy):
    """Abbreviation: 'kg' → kilogram."""
    assert vy.eval('shabda-anveshana "kg"') == "kilogram"


def test_shabda_miss(vy):
    """Unknown word returns None."""
    assert vy.eval('shabda-anveshana "xyzfoobar"') is None


# ── ppr / register-dimension ──────────────────────────────────────────────────


@pytest.mark.xfail(strict=True, reason="graph primitive: register-dimension return value mismatch")
def test_register_dimension_idempotent(vy):
    """register-dimension returns same index on repeat call."""
    idx1 = vy.eval('register-dimension "satya"')
    idx2 = vy.eval('register-dimension "satya"')
    assert idx1 == idx2 and idx1 >= 10


# ── axiom expansion: symmetric ────────────────────────────────────────────────


def test_symmetric_abheda_reverse(vy):
    """abheda is symmetric: A abheda B ⇒ B abheda A.
    visheshanam-abheda (abheda equivalence-relation) in .om5
    → equivalence-relation should walk abheda back to visheshanam-abheda."""
    targets = vy.walk("equivalence-relation", "abheda")
    assert "visheshanam-abheda" in targets


def test_symmetric_pratipaksha_bidirectional(vy):
    """pratipaksha is symmetric: addition ↔ subtraction."""
    assert "subtraction" in vy.walk("addition", "pratipaksha")
    assert "addition" in vy.walk("subtraction", "pratipaksha")


def test_symmetric_yukta_reverse(vy):
    """yukta is symmetric: A yukta B ⇒ B yukta A.
    visheshanam-swarupa (yukta visheshanam-abheda) in .om5
    → visheshanam-abheda should walk yukta back to visheshanam-swarupa."""
    targets = vy.walk("visheshanam-abheda", "yukta")
    assert "visheshanam-swarupa" in targets


# ── axiom expansion: dual (janya ↔ phala) ─────────────────────────────────────


def test_dual_janya_creates_phala(vy):
    """janya dual is phala: A janya B ⇒ B phala A.
    kinetic-energy-mantra (janya mass velocity) in .om5.
    velocity has no explicit phala ke-mantra, so this comes from dual."""
    targets = vy.walk("velocity", "phala")
    assert "kinetic-energy-mantra" in targets


def test_dual_phala_creates_janya(vy):
    """phala dual is janya: A phala B ⇒ B janya A.
    motion (phala displacement) in .om5.
    displacement should have janya motion."""
    targets = vy.walk("displacement", "janya")
    assert "motion" in targets


# ── axiom expansion: ganana walk ──────────────────────────────────────────────


def test_ganana_edge_walkable(vy):
    """ganana edges (system 7) are walkable: addition → add."""
    targets = vy.walk("addition", "ganana")
    assert "add" in targets


def test_ganana_reverse_walkable(vy):
    """ganana reverse: add → addition."""
    targets = vy.walk_in("add", "ganana")
    assert "addition" in targets


# ── naama-mudra: symbol dimension ────────────────────────────────────────────


def test_naama_mudra_base_unit_symbol(vy):
    """Base units have naama-mudra symbol edges: metre → m."""
    assert "m" in vy.walk("metre", "naama-mudra")


def test_naama_mudra_derived_unit_symbol(vy):
    """Derived units have naama-mudra: joule → J."""
    assert "J" in vy.walk("joule", "naama-mudra")


def test_naama_mudra_prefix_symbol(vy):
    """SI prefixes have naama-mudra: kilo → k."""
    assert "k" in vy.walk("kilo", "naama-mudra")


def test_naama_mudra_case_sensitive(vy):
    """naama-mudra is case-sensitive: K → kelvin, k → kilo."""
    assert "kelvin" in vy.walk_in("K", "naama-mudra")
    assert "kilo" in vy.walk_in("k", "naama-mudra")


def test_naama_full_name_only(vy):
    """naama carries full names, not symbols: kilogram naama has no 'kg'."""
    names = vy.walk("kilogram", "naama")
    assert "kilogram" in names
    assert "kg" not in names


def test_symbol_resolves_via_word_node(vy):
    """word-node resolves symbols via naama-mudra fallback: kg → kilogram."""
    assert vy.eval('word-node "kg"') == "kilogram"
    assert vy.eval('word-node "Hz"') == "hertz"
    assert vy.eval('word-node "m/s"') == "metre-per-second"


def test_naama_mudra_collision_both_found(vy):
    """m is both metre (base unit) and milli (prefix) in naama-mudra."""
    candidates = vy.eval('word-node-candidates "m"')
    assert "metre" in candidates
    assert "milli" in candidates


def test_prefix_has_sankhya_exponent(vy):
    """Prefixes carry scale as sankhya: kilo sankhya 3 → 10^3."""
    assert "3" in vy.walk("kilo", "sankhya")
    assert "-3" in vy.walk("milli", "sankhya")


def test_prefix_sthita_upasarga(vy):
    """All prefixes are marked sthita upasarga for disambiguation."""
    assert "upasarga" in vy.walk("kilo", "sthita")
    assert "upasarga" in vy.walk("nano", "sthita")


def test_base_unit_sthita_matra_beeja(vy):
    """Base units are marked sthita matra-beeja for disambiguation."""
    assert "matra-beeja" in vy.walk("metre", "sthita")
    assert "matra-beeja" in vy.walk("gram", "sthita")


# ── decompose-unit: prefix + base symbol parsing ────────────────────────────


def test_decompose_km(vy):
    """km → kilo + metre, exponent 3."""
    result = vy.eval('decompose-unit "km"')
    assert result == ["kilo", "metre", "3"]


def test_decompose_kPa(vy):
    """kPa → kilo + pascal, exponent 3."""
    result = vy.eval('decompose-unit "kPa"')
    assert result == ["kilo", "pascal", "3"]


def test_decompose_MHz(vy):
    """MHz → mega + hertz, exponent 6."""
    result = vy.eval('decompose-unit "MHz"')
    assert result == ["mega", "hertz", "6"]


def test_decompose_mm(vy):
    """mm → milli + metre, exponent -3."""
    result = vy.eval('decompose-unit "mm"')
    assert result == ["milli", "metre", "-3"]


def test_decompose_nA(vy):
    """nA → nano + ampere, exponent -9."""
    result = vy.eval('decompose-unit "nA"')
    assert result == ["nano", "ampere", "-9"]


def test_decompose_kg(vy):
    """kg → kilo + gram, exponent 3."""
    result = vy.eval('decompose-unit "kg"')
    assert result == ["kilo", "gram", "3"]


def test_decompose_single_char_none(vy):
    """Single-character symbol cannot be a compound → None."""
    assert vy.eval('decompose-unit "m"') is None


def test_decompose_unknown_none(vy):
    """Unknown symbol returns None."""
    assert vy.eval('decompose-unit "xyz"') is None


def test_decompose_bare_unit_none(vy):
    """Full unit symbol without prefix returns None (not a compound)."""
    assert vy.eval('decompose-unit "J"') is None
