"""test_collocation.py — collocation and compound-word gaps.

A collocation is two or more words whose combined meaning differs from each
word alone. 'kinetic' next to 'energy' is not two ideas — it is one. 'moves
at' next to a number is not motion + number — it is velocity. 'from rest'
is not origin + noun — it is initial-velocity = 0.

Each test here documents one gap in the current pipeline. All are marked
xfail with the gate that describes the fix needed. They are written before
the fix exists — the fix must make them pass and the xfail removed.

Gap map (pipeline slot → gap):
  Gap 1: three-word compounds        — sandhi-kosha / kosha entry needed
  Gap 2: verb-phrase velocity signal — sandhi-viveka grammar rule
  Gap 3: prepositional phrase init   — sandhi-viveka grammar rule
  Gap 4: total + compound concept    — avrti-refine ordering (kosha before avastha)
  Gap 5: classifier/colour entity    — sandhi-samasa (new tantra needed)
  Gap 6: article stripping           — build-question-graph / sandhi-viveka

Run:
    cd /home/abe/agent_x && .venv/bin/pytest vyakarana/tests/test_collocation.py -v
"""

import pytest


def refined(vy, sentence: str) -> list:
    """Full pipeline: build-question-graph → fixpoint avrti-refine."""
    return vy.eval(
        f'fixpoint (build-question-graph "{sentence}") (fn g -> avrti-refine g)'
    )


def answer(vy, sentence: str) -> str:
    """Full anuvada-ganana answer."""
    return vy.eval(f'anuvada-ganana "{sentence}"')


# ── Gap 1: three-word compounds ───────────────────────────────────────────────
# 'electric field strength' should resolve to electric-field-strength
# Currently: electric-field resolves but 'strength' is left as a separate satya


@pytest.mark.xfail(
    reason="Gap 1: three-word compound — sandhi-kosha only handles bigrams; "
    "electric-field-strength not in kosha",
    strict=True,
)
def test_electric_field_strength_resolves(vy):
    """'electric field strength 0.1' → single concept electric-field-strength"""
    g = refined(vy, "electric field strength is 0.1")
    satya = [t[0] for t in g if t[1] == "satya"]
    assert satya == ["electric-field-strength"], (
        f"expected ['electric-field-strength'], got {satya!r}"
    )


@pytest.mark.xfail(
    reason="Gap 1: three-word compound — magnetic-field-strength not in kosha",
    strict=True,
)
def test_magnetic_field_strength_resolves(vy):
    """'magnetic field strength 0.5' → single concept magnetic-field-strength"""
    g = refined(vy, "magnetic field strength is 0.5")
    satya = [t[0] for t in g if t[1] == "satya"]
    assert satya == ["magnetic-field-strength"], (
        f"expected ['magnetic-field-strength'], got {satya!r}"
    )


@pytest.mark.xfail(
    reason="Gap 1: three-word compound — orbital-radius not in kosha", strict=True
)
def test_orbital_radius_resolves(vy):
    """'find orbital radius' → concept orbital-radius"""
    g = refined(vy, "find orbital radius")
    satya = [t[0] for t in g if t[1] == "satya"]
    assert "orbital-radius" in satya, f"expected orbital-radius in satya, got {satya!r}"


# ── Gap 2: verb-phrase velocity signal ────────────────────────────────────────
# 'moves at X', 'moving at X', 'travels at X' → velocity = X
# Currently: number binds to the preceding entity, not to velocity concept


@pytest.mark.xfail(
    reason="Gap 2: verb-phrase velocity signal — 'moves at' not a grammar rule",
    strict=True,
)
def test_moves_at_binds_velocity(vy):
    """'a proton moves at 2e6 m/s' → velocity = 2e6, not proton = 2e6"""
    g = refined(vy, "a proton moves at 2e6 m/s")
    sankhya = {t[0]: t[2] for t in g if t[1] == "sankhya"}
    assert "velocity" in sankhya, f"expected velocity sankhya, got sankhya={sankhya!r}"
    assert "proton" not in sankhya or sankhya.get("proton") != "2000000.", (
        f"proton should not steal velocity value, got sankhya={sankhya!r}"
    )


@pytest.mark.xfail(
    reason="Gap 2: verb-phrase velocity signal — 'moving at' not a grammar rule",
    strict=True,
)
def test_moving_at_binds_velocity(vy):
    """'the electron is moving at 1e6 m/s' → velocity = 1e6"""
    g = refined(vy, "the electron is moving at 1e6 m/s")
    sankhya = {t[0]: t[2] for t in g if t[1] == "sankhya"}
    assert "velocity" in sankhya, f"expected velocity sankhya, got {sankhya!r}"


@pytest.mark.xfail(
    reason="Gap 2: verb-phrase velocity signal — 'moving at' not a grammar rule, "
    "number binds to wrong concept so KE derivation gives no match",
    strict=True,
)
def test_electron_moving_at_finds_ke(vy):
    """'the electron has mass 9.109e-31. it is moving at 1e6 m/s. find KE'
    Currently: 'it is moving at 1e6' has no velocity binding — the 1e6 attaches
    to the wrong concept. Fix: 'moving at'/'moves at' → velocity grammar signal."""
    ans = answer(
        vy,
        "the electron has mass 9.109e-31. it is moving at 1e6 m/s. find kinetic energy",
    )
    # Must produce a numeric kinetic-energy result — not "no match"
    assert "kinetic-energy =" in ans and "no match" not in ans, (
        f"expected 'kinetic-energy = <value>', got {ans!r}"
    )


# ── Gap 3: prepositional phrase as concept value ──────────────────────────────
# 'from rest' → initial-velocity = 0
# 'at rest' → velocity = 0
# Currently: 'rest' maps to count-remaining, number binds wrong


@pytest.mark.xfail(
    reason="Gap 3: 'from rest' should mean initial-velocity=0", strict=True
)
def test_from_rest_means_initial_velocity_zero(vy):
    """'accelerates from rest at 3 m/s2' → initial-velocity = 0"""
    g = refined(vy, "accelerates from rest at 3 m/s2")
    sankhya = {t[0]: t[2] for t in g if t[1] == "sankhya"}
    assert sankhya.get("initial-velocity") in ("0", "0."), (
        f"expected initial-velocity=0, got sankhya={sankhya!r}"
    )


@pytest.mark.xfail(
    reason="Gap 3: 'from rest' → initial-velocity=0; currently 'rest' maps to "
    "count-remaining and the number binds to wrong concept, force derivation fails",
    strict=True,
)
def test_car_accelerates_from_rest(vy):
    """'a car of mass 1200 accelerates from rest at 3 m/s2. find force'
    Currently: mass=1200 and mass=3 (rest/acceleration confused) → no match.
    Fix: 'from rest' → initial-velocity=0; 'at X m/s2' → acceleration=X."""
    ans = answer(vy, "a car of mass 1200 accelerates from rest at 3 m/s2. find force")
    assert "force =" in ans and "no match" not in ans, (
        f"expected 'force = <value>', got {ans!r}"
    )


# ── Gap 4: total + already-resolved compound concept ─────────────────────────
# sandhi-avastha runs before sandhi-kosha, so 'total kinetic energy' sees
# 'kinetic' (still mithya) not 'kinetic-energy' (already resolved).
# Fix: run sandhi-kosha before sandhi-avastha in avrti-refine.


@pytest.mark.xfail(
    reason="Gap 4: 'total kinetic energy' — avastha fires before kosha resolves bigram",
    strict=True,
)
def test_total_kinetic_energy_resolves(vy):
    """'find total kinetic energy' → solve-for = total-kinetic-energy"""
    g = refined(vy, "find total kinetic energy given mass 2 and velocity 3")
    satya = [t[0] for t in g if t[1] == "satya"]
    assert "total-kinetic-energy" in satya or "kinetic-energy" in satya, (
        f"expected total-kinetic-energy or kinetic-energy in satya, got {satya!r}"
    )
    # 'total' should not remain as a separate 'count' concept
    assert "count" not in satya, (
        f"'count' should not appear when 'total' qualifies a compound, got {satya!r}"
    )


@pytest.mark.xfail(
    reason="Gap 4: 'find total momentum' — total left as count concept", strict=True
)
def test_total_momentum_resolves(vy):
    """'find total momentum' → solve-for is momentum not count"""
    g = refined(vy, "find total momentum given mass 2 and velocity 3")
    satya = [t[0] for t in g if t[1] == "satya"]
    assert "count" not in satya, (
        f"'count' should not appear for 'total momentum', got {satya!r}"
    )


# ── Gap 5: classifier/colour words as entity discriminators ──────────────────
# 'red balls', 'blue balls' — colour qualifies entity label, not a concept
# 'a box has 5 red balls and 3 blue balls'
# Currently: red/blue are mithya and lost; both bind to same 'container' entity


@pytest.mark.xfail(
    reason="Gap 5: colour classifiers not treated as entity discriminators", strict=True
)
def test_red_blue_balls_distinct_entities(vy):
    """'5 red balls and 3 blue balls' → two distinct counted things"""
    g = refined(vy, "a box has 5 red balls and 3 blue balls")
    # Two distinct sankhya values should exist with different subjects
    sankhya = [[t[0], t[2]] for t in g if t[1] == "sankhya"]
    subjects = [s[0] for s in sankhya]
    assert len(set(subjects)) >= 2, (
        f"expected at least 2 distinct subjects with sankhya, got {sankhya!r}"
    )


@pytest.mark.xfail(
    reason="Gap 5: classifier words — full pipeline should add the counts", strict=True
)
def test_red_blue_balls_addition(vy):
    """'a box has 5 red balls and 3 blue balls. how many balls?' → 8"""
    ans = answer(vy, "a box has 5 red balls and 3 blue balls. how many balls")
    assert "8" in ans, f"expected 8 total balls, got {ans!r}"


# ── Gap 6: article stripping before entity lookup ────────────────────────────
# 'the electron', 'a proton' — article should be stripped, entity should resolve
# Currently: 'the' + entity sometimes prevents prathama-vibhakti assignment


def test_the_electron_gets_prathama(vy):
    """'the electron has mass ...' → electron gets prathama-vibhakti (already works)"""
    g = refined(vy, "the electron has mass 9.109e-31")
    prathama = [t[0] for t in g if t[1] == "prathama-vibhakti"]
    assert "electron" in prathama, (
        f"expected electron in prathama-vibhakti, got {prathama!r}"
    )


def test_the_electron_ke_pipeline(vy):
    """'the electron has mass 9.109e-31. find kinetic energy given velocity 1e6' (already works)"""
    ans = answer(
        vy, "the electron has mass 9.109e-31. find kinetic energy given velocity 1e6"
    )
    assert "kinetic-energy" in ans and "=" in ans, (
        f"expected kinetic-energy result, got {ans!r}"
    )
