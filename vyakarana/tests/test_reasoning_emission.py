"""test_reasoning_emission.py — complex questions testing the full reasoning emission.

These tests verify:
  - The "we have / we seek / we know / we find" structure from emit-reasoning
  - Multi-step chains (u, a, t → v → KE)
  - Inverse mantras (F=ma → find a)
  - Entity-scoped computation via scope entity
  - Natural science questions (photon, proton, potential energy, work)
  - The reasoning structure itself — not just the numeric answer

The reasoning tantra (emit-reasoning.tantra2) walks the proof graph's edges
and speaks in uttama-purusa-bahu-vachana kartari-prayoga — the inclusive we.
All speech acts come from anuvada-setu.shabda. No hardcoded strings.
The sphoTa lands at "we find" — the meaning flashing whole.

Run:
    cd /home/abe/agent_x && .venv/bin/pytest vyakarana/tests/test_reasoning_emission.py -v --socket /tmp/vy.sock
"""

import pytest


def answer(vy, sentence):
    return vy.eval(f'anuvada-ganana "{sentence}"')


# ── Section 1: reasoning structure ───────────────────────────────────────────


def test_reasoning_has_four_strands(vy):
    """The reasoning emission has: we have, we seek, we know, we find."""
    r = answer(vy, "mass is 5 and velocity is 10. find kinetic energy.")
    assert "we have" in r, f"missing 'we have': {r}"
    assert "we seek" in r, f"missing 'we seek': {r}"
    assert "we know" in r, f"missing 'we know': {r}"
    assert "we find" in r, f"missing 'we find': {r}"


def test_reasoning_given_shows_values(vy):
    """The 'we have' strand lists the known quantities."""
    r = answer(vy, "mass is 5 and velocity is 10. find kinetic energy.")
    assert "mass" in r and "5" in r, f"mass not in given: {r}"
    assert "velocity" in r and "10" in r, f"velocity not in given: {r}"


def test_reasoning_sought_names_concept(vy):
    """The 'we seek' strand names the concept being found."""
    r = answer(vy, "mass is 5 and velocity is 10. find kinetic energy.")
    assert "kinetic-energy" in r, f"kinetic-energy not in sought: {r}"


def test_reasoning_recognises_mantra(vy):
    """The 'we know' strand names the mantra that fired."""
    r = answer(vy, "mass is 5 and velocity is 10. find kinetic energy.")
    assert "kinetic-energy-mantra" in r, f"mantra not in recognised: {r}"


def test_reasoning_find_contains_result(vy):
    """The 'we find' strand contains the computed result."""
    r = answer(vy, "mass is 5 and velocity is 10. find kinetic energy.")
    assert "250" in r, f"result not in found: {r}"


def test_reasoning_entity_grouped(vy):
    """When entity present: 'we have: ball (mass=5, velocity=10)'."""
    r = answer(vy, "ball has mass 5 and velocity 10. find kinetic energy.")
    assert "ball" in r, f"entity not in given: {r}"
    assert "mass" in r and "5" in r, f"mass not grouped with entity: {r}"


def test_reasoning_scope_entity_in_sought(vy):
    """Scope entity appears in 'we seek': 'we seek: kinetic-energy of ball-A'."""
    r = answer(
        vy,
        "ball-A has mass 3 and velocity 4. ball-B has mass 2 and velocity 5. "
        "find kinetic energy of ball-A.",
    )
    assert "of ball-A" in r, f"scope entity not in sought: {r}"
    assert "24" in r, f"wrong result for ball-A: {r}"


# ── Section 2: chain derivation ───────────────────────────────────────────────


def test_chain_u_a_t_to_ke(vy):
    """u=0, a=4, t=5 → v=20 → KE = ½×3×400 = 600"""
    r = answer(
        vy,
        "initial velocity is 0. acceleration is 4. time is 5. "
        "find kinetic energy given mass 3.",
    )
    assert "600" in r, f"expected KE=600 via chain, got {r}"
    assert "we find" in r, f"missing we find: {r}"


def test_chain_shows_derived_velocity(vy):
    """Chain reasoning: velocity derived before KE computed."""
    r = answer(
        vy,
        "initial velocity is 0. acceleration is 10. time is 3. "
        "find kinetic energy given mass 2.",
    )
    # v = 0 + 10*3 = 30, KE = ½*2*900 = 900
    assert "900" in r, f"expected KE=900, got {r}"


def test_chain_u_a_t_to_momentum(vy):
    """u=5, a=3, t=4 → v=17 → p = mv = 2*17 = 34"""
    r = answer(
        vy,
        "initial velocity is 5. acceleration is 3. time is 4. "
        "find momentum given mass 2.",
    )
    assert "34" in r, f"expected momentum=34, got {r}"


# ── Section 3: inverse mantras ────────────────────────────────────────────────


def test_inverse_fma_find_acceleration(vy):
    """F=ma inverted: F=50, m=10 → a=5"""
    r = answer(vy, "force is 50. mass is 10. find acceleration.")
    assert "5" in r, f"expected acceleration=5, got {r}"
    assert "newton-second-law-motion" in r, f"mantra not shown: {r}"


def test_inverse_fma_find_mass(vy):
    """F=ma inverted: F=40, a=8 → m=5"""
    r = answer(vy, "force is 40. acceleration is 8. find mass.")
    assert "5" in r, f"expected mass=5, got {r}"


def test_inverse_ke_find_mass(vy):
    """KE=½mv² inverted: KE=50, v=10 → m=1"""
    r = answer(vy, "kinetic energy is 50 and velocity is 10. find mass")
    assert "1" in r, f"expected mass=1, got {r}"


def test_inverse_momentum_find_velocity(vy):
    """p=mv inverted: p=30, m=6 → v=5"""
    r = answer(vy, "momentum is 30 and mass is 6. find velocity.")
    assert "5" in r, f"expected velocity=5, got {r}"


# ── Section 4: physics mantras ────────────────────────────────────────────────


def test_potential_energy(vy):
    """PE = mgh: m=5, h=20 → PE=980.665"""
    r = answer(vy, "mass is 5 and height is 20. find potential energy.")
    assert "980" in r, f"expected PE≈980, got {r}"
    assert "potential-energy-mantra" in r, f"mantra not shown: {r}"


def test_photon_energy(vy):
    """E = hf: f=6e14 → E≈3.975e-19 J"""
    r = answer(vy, "frequency is 6e14. find photon energy.")
    assert "3.97" in r, f"expected E≈3.97e-19, got {r}"
    assert "planck-constant" in r, f"planck constant not shown: {r}"


def test_work_with_angle_zero(vy):
    """W = F·d·cos(0) = F·d: F=30, d=4, angle=0 → W=120"""
    r = answer(vy, "force is 30 and displacement is 4 and angle is 0. find work.")
    assert "120" in r, f"expected work=120, got {r}"


def test_work_with_angle_nonzero(vy):
    """W = F·d·cos(angle_rad): F=20, d=5, angle=1.047rad (≈60°) → W≈50"""
    r = answer(vy, "force is 20 and displacement is 5 and angle is 1.047. find work.")
    # cos(1.047 rad) ≈ 0.5, W = 20*5*0.5 = 50
    assert "50" in r, f"expected work≈50, got {r}"


def test_proton_kinetic_energy(vy):
    """KE of proton: m=1.67e-27, v=3e7 → KE≈7.515e-13 J"""
    r = answer(
        vy, "proton has mass 1.67e-27 and velocity 3e7. find kinetic energy of proton."
    )
    assert "7.515e-13" in r, f"expected KE≈7.515e-13, got {r}"
    assert "proton" in r, f"entity not shown: {r}"


def test_electron_momentum(vy):
    """p = mv: m=9.109e-31, v=2e6 → p≈1.82e-24 kg·m/s"""
    r = answer(
        vy,
        "electron has mass 9.109e-31 and velocity 2e6. find momentum of electron.",
    )
    assert "1.82" in r, f"expected p≈1.82e-24, got {r}"


# ── Section 5: multi-entity reasoning ────────────────────────────────────────


def test_two_entities_both_shown_in_given(vy):
    """The 'we have' strand shows both entities grouped."""
    r = answer(
        vy,
        "ball-A has mass 3 and velocity 4. ball-B has mass 2 and velocity 5. "
        "find kinetic energy of ball-A.",
    )
    assert "ball-A" in r, f"ball-A not in given: {r}"
    assert "ball-B" in r, f"ball-B not in given: {r}"
    assert "24" in r, f"wrong KE for ball-A: {r}"


def test_two_entities_correct_scope_second(vy):
    """Scope entity ball-B: KE = ½×2×64 = 64"""
    r = answer(
        vy,
        "ball-A has mass 4 and velocity 6 and ball-B has mass 2 and velocity 8. "
        "find kinetic energy of ball-B.",
    )
    assert "64" in r, f"expected KE=64 for ball-B, got {r}"


def test_two_entities_momentum_first(vy):
    """p = mv of ball-A: m=5, v=3 → p=15"""
    r = answer(
        vy,
        "ball-A has mass 5 and velocity 3. ball-B has mass 2 and velocity 7. "
        "find momentum of ball-A.",
    )
    assert "15" in r, f"expected momentum=15 for ball-A, got {r}"


def test_two_entities_momentum_second(vy):
    """p = mv of ball-B: m=2, v=7 → p=14 (viraam-separated ownership)"""
    r = answer(
        vy,
        "ball-A has mass 5 and velocity 3. "
        "ball-B has mass 2 and velocity 7. "
        "find momentum of ball-B.",
    )
    assert "14" in r, f"expected momentum=14 for ball-B, got {r}"


def test_proton_electron_scene_proton_momentum(vy):
    """Two-entity scene: find proton momentum, not electron's."""
    r = answer(
        vy,
        "proton has mass 1.67e-27 and velocity 2e6. "
        "electron has mass 9.109e-31 and velocity 1e7. "
        "find momentum of proton.",
    )
    assert "3.34e-21" in r, f"expected proton momentum=3.34e-21, got {r}"


# ── Section 6: no match cases ────────────────────────────────────────────────


def test_no_match_insufficient_janya(vy):
    """Only mass given — cannot compute KE without velocity."""
    r = answer(vy, "mass is 5. find kinetic energy.")
    assert "no match" in r, f"expected no match, got {r}"


def test_no_match_wrong_janya_combination(vy):
    """mass + acceleration cannot give momentum."""
    r = answer(vy, "mass is 5 and acceleration is 3. find momentum.")
    assert "no match" in r, f"expected no match, got {r}"


def test_no_match_still_shows_given(vy):
    """Even on no match, 'we have' and 'we seek' are shown."""
    r = answer(vy, "mass is 5. find kinetic energy.")
    assert "we have" in r, f"no match should still show 'we have': {r}"
    assert "we seek" in r, f"no match should still show 'we seek': {r}"


# ── Section 7: xfails — known gaps ───────────────────────────────────────────


@pytest.mark.xfail(
    strict=True,
    reason="Natural phrasing: 'from rest' = initial-velocity=0, 'to 30 m/s' = "
    "final-velocity, 'in 10 seconds' = time. These positional avastha signals "
    "not yet handled by sandhi-avastha or avrti. 'rest' is mithya, '30' "
    "unbound (no satya concept preceding it), 'second' satya but number lost.",
)
def test_natural_car_force(vy):
    """'accelerates from rest to 30 m/s in 10 seconds' → find force"""
    r = answer(
        vy,
        "a car of mass 1200 kg accelerates from rest to 30 m/s in 10 seconds. "
        "find the force.",
    )
    # a = (30-0)/10 = 3, F = 1200*3 = 3600
    assert "3600" in r, f"expected F=3600, got {r}"


@pytest.mark.xfail(
    strict=True,
    reason="period-mantra currently requires angular-velocity, not frequency. "
    "T = 1/f is the relation but no frequency→period mantra declared. "
    "Needs frequency-period-mantra.om with f as janya and T as phala, "
    "krama: reciprocal.",
)
def test_period_from_frequency(vy):
    """T = 1/f: f=440 → T≈0.00227 s"""
    r = answer(vy, "frequency is 440. find period.")
    assert "0.00227" in r, f"expected T≈0.00227, got {r}"


@pytest.mark.xfail(
    strict=True,
    reason="KE inverse for velocity uses solve-for across a viraam boundary. "
    "extract-solve-for loses has-intent after viraam separates 'mass is 2.' "
    "from 'find velocity.' The inverse path requires has-intent=True. "
    "Viraam resets the sentence context but the intent should carry across "
    "to the next sentence in the same question.",
)
def test_inverse_ke_find_velocity_viraam(vy):
    """KE=½mv² inverted across viraam: KE=900, m=2 → v=30"""
    r = answer(vy, "kinetic energy is 900 and mass is 2. find velocity.")
    assert "30" in r, f"expected velocity=30, got {r}"


def test_two_entities_viraam_scope_second(vy):
    """Scope second entity across viraam: ball-B KE = ½×2×64 = 64"""
    r = answer(
        vy,
        "ball-A has mass 4 and velocity 6. "
        "ball-B has mass 2 and velocity 8. "
        "find kinetic energy of ball-B.",
    )
    assert "64" in r, f"expected KE=64 for ball-B across viraam, got {r}"
