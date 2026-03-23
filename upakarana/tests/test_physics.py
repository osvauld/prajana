"""test_physics.py — all 22 physics mantras: forward, inverse, chains, edge cases.

One test per mantra forward. Key inverses. Chain derives. Zero-value edge cases.
No xfail — run everything, let upakarana classify what passes.
"""


# ── forward: single mantra ──────────────────────────────────────────────────


def test_ke_basic(vy):
    """KE = ½mv²: m=5, v=10 → 250"""
    r = vy.answer("mass is 5 and velocity is 10. find kinetic energy")
    assert "250" in r


def test_momentum_basic(vy):
    """p = mv: m=5, v=10 → 50"""
    r = vy.answer("mass is 5 and velocity is 10. find momentum")
    assert "50" in r


def test_force_basic(vy):
    """F = ma: m=10, a=5 → 50"""
    r = vy.answer("mass is 10 and acceleration is 5. find force")
    assert "50" in r


def test_velocity_suvat(vy):
    """v = u + at: u=0, a=4, t=5 → 20"""
    r = vy.answer("initial velocity is 0. acceleration is 4. time is 5. find velocity")
    assert "20" in r


def test_acceleration_from_suvat(vy):
    """a = (v-u)/t: v=30, u=10, t=4 → 5"""
    r = vy.answer("final velocity is 30. initial velocity is 10. time is 4. find acceleration")
    assert "5" in r


def test_pressure_basic(vy):
    """P = F/A: F=100, A=5 → 20"""
    r = vy.answer("force is 100 and area is 5. find pressure")
    assert "20" in r


def test_frequency_from_period(vy):
    """f = 1/T: T=0.5 → 2"""
    r = vy.answer("period is 0.5. find frequency")
    assert "2" in r


def test_angular_velocity_basic(vy):
    """ω = v/r: v=10, r=2 → 5"""
    r = vy.answer("velocity is 10 and radius is 2. find angular velocity")
    assert "5" in r


def test_potential_energy_basic(vy):
    """PE = mgh: m=5, g=9.8, h=10 → 490"""
    r = vy.answer("mass is 5. gravity is 9.8. height is 10. find potential energy")
    assert "490" in r


def test_work_basic(vy):
    """W = F·d·cos(θ): F=50, d=10, angle=0 → 500"""
    r = vy.answer("force is 50. displacement is 10. angle is 0. find work")
    assert "500" in r


def test_capacitance_basic(vy):
    """C = q/V: q=5, V=10 → 0.5"""
    r = vy.answer("charge is 5 and voltage is 10. find capacitance")
    assert "0.5" in r


def test_electric_power_basic(vy):
    """P = VI: V=220, I=5 → 1100"""
    r = vy.answer("voltage is 220 and current is 5. find electric power")
    assert "1100" in r


def test_torque_basic(vy):
    """τ = Iα: I=4, α=3 → 12"""
    r = vy.answer("moment of inertia is 4 and angular acceleration is 3. find torque")
    assert "12" in r


def test_centripetal_force_basic(vy):
    """Fc = mv²/r: m=2, v=10, r=5 → 40"""
    r = vy.answer("mass is 2. velocity is 10. radius is 5. find centripetal force")
    assert "40" in r


def test_friction_force_basic(vy):
    """Ff = μN: μ=0.3, N=100 → 30"""
    r = vy.answer("coefficient is 0.3 and normal force is 100. find friction force")
    assert "30" in r


def test_spring_force_basic(vy):
    """Fs = kx: k=200, x=0.05 → 10"""
    r = vy.answer("spring constant is 200 and displacement is 0.05. find spring force")
    assert "10" in r


def test_mass_density_basic(vy):
    """ρ = m/V: m=500, V=2 → 250"""
    r = vy.answer("mass is 500 and volume is 2. find mass density")
    assert "250" in r


def test_period_from_angular_velocity(vy):
    """T = 2π/ω: ω≈6.283 → T≈1"""
    r = vy.answer("angular velocity is 6.283. find period")
    assert "1" in r


def test_photon_energy_basic(vy):
    """E = hf: h=6.626e-34, f=5e14 → ~3.313e-19"""
    r = vy.answer("planck constant is 6.626e-34. frequency is 5e14. find photon energy")
    assert "3.3" in r


# ── forward: scientific notation and units ──────────────────────────────────


def test_ke_scientific_notation(vy):
    """KE with small mass (electron-scale): m=9.109e-31, v=1e6"""
    r = vy.answer("mass is 9.109e-31 and velocity is 1e6. find kinetic energy")
    assert "4.5" in r


def test_momentum_with_units(vy):
    """p = mv with explicit unit words"""
    r = vy.answer("mass is 2 kg and velocity is 5 m/s. find momentum")
    assert "10" in r


# ── forward: chains (multi-mantra derive) ───────────────────────────────────


def test_chain_ke_via_suvat(vy):
    """u=0, a=4, t=5, m=10 → v=20 → KE=2000"""
    r = vy.answer(
        "initial velocity is 0. acceleration is 4. time is 5. mass is 10. find kinetic energy"
    )
    assert "2000" in r


def test_chain_momentum_via_suvat(vy):
    """u=0, a=5, t=4, m=3 → v=20 → p=60"""
    r = vy.answer(
        "initial velocity is 0. acceleration is 5. time is 4. mass is 3. find momentum"
    )
    assert "60" in r


def test_chain_force_via_suvat(vy):
    """u=0, v=20, t=4, m=10 → a=5 → F=50"""
    r = vy.answer(
        "initial velocity is 0. final velocity is 20. time is 4. mass is 10. find force"
    )
    assert "50" in r


# ── inverse: solve for input given output ────────────────────────────────────


def test_inverse_ke_find_velocity(vy):
    """KE=50, m=2 → v=sqrt(50)≈7.07"""
    r = vy.answer("kinetic energy is 50 and mass is 2. find velocity")
    assert "7.07" in r


def test_inverse_ke_find_mass(vy):
    """KE=50, v=10 → m=1"""
    r = vy.answer("kinetic energy is 50 and velocity is 10. find mass")
    assert "1" in r


def test_inverse_momentum_find_mass(vy):
    """p=50, v=10 → m=5"""
    r = vy.answer("momentum is 50 and velocity is 10. find mass")
    assert "5" in r


def test_inverse_momentum_find_velocity(vy):
    """p=60, m=3 → v=20"""
    r = vy.answer("momentum is 60 and mass is 3. find velocity")
    assert "20" in r


def test_inverse_suvat_find_time(vy):
    """v=20, u=0, a=5 → t=4"""
    r = vy.answer("final velocity is 20. initial velocity is 0. acceleration is 5. find time")
    assert "4" in r


def test_inverse_suvat_find_initial_velocity(vy):
    """v=30, a=5, t=4 → u=10"""
    r = vy.answer("final velocity is 30. acceleration is 5. time is 4. find initial velocity")
    assert "10" in r


def test_inverse_pressure_find_area(vy):
    """P=20, F=100 → A=5"""
    r = vy.answer("pressure is 20 and force is 100. find area")
    assert "5" in r


def test_inverse_angular_velocity_find_radius(vy):
    """ω=5, v=10 → r=2"""
    r = vy.answer("angular velocity is 5 and velocity is 10. find radius")
    assert "2" in r


def test_inverse_electric_power_find_current(vy):
    """P=1100, V=220 → I=5"""
    r = vy.answer("electric power is 1100 and voltage is 220. find current")
    assert "5" in r


# ── edge cases: zero values, missing data ────────────────────────────────────


def test_zero_velocity_ke(vy):
    """KE with v=0 → 0, not no-match"""
    r = vy.answer("mass is 5 and velocity is 0. find kinetic energy")
    assert "0" in r


def test_zero_initial_velocity_suvat(vy):
    """SUVAT starting from rest: u=0 explicitly given"""
    r = vy.answer("initial velocity is 0. acceleration is 3. time is 4. find velocity")
    assert "12" in r


def test_missing_data_no_match(vy):
    """Only mass given, no velocity → can't compute KE"""
    r = vy.answer("mass is 5. find kinetic energy")
    assert "no match" in r or "we seek" in r


# ── reasoning strands ────────────────────────────────────────────────────────


def test_strands_complete(vy):
    """Full proof has all four strands"""
    r = vy.answer("mass is 5 and velocity is 10. find kinetic energy")
    for strand in ("we have", "we seek", "we know", "we find"):
        assert strand in r


def test_chain_strand_intermediate(vy):
    """Chain proof shows intermediate result"""
    r = vy.answer(
        "initial velocity is 0. acceleration is 4. time is 5. mass is 10. find kinetic energy"
    )
    assert "we find" in r
