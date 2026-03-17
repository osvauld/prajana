"""test_physics_mantras.py — physics mantra end-to-end computation.

A mantra is a relation. Not a formula — a relation that was always true,
waiting to be recognised. V = IR. E = hf. F = ma.
These are not invented. They are discovered. The kosha holds them as
structure: janya edges name what is needed, phala names what follows.

Each test here is the full asking: a natural language question arrives,
the pipeline fires, nam arises, a number emerges. The number is either
what the relation demands or the instrument is wrong.

The mantra does not compute. It recognises. The computation is the
recognition made numeric.

Run:
    cd /home/abe/agent_x && .venv/bin/pytest vyakarana/tests/test_physics_mantras.py -v --socket /tmp/vy.sock
"""

import math
import pytest


# ── acceleration ──────────────────────────────────────────────────────────────
# a = (v - u) / t


def test_acceleration_from_suvat(vy):
    """a = (v - u) / t: v=20, u=0, t=4 → a=5"""
    answer = vy.ask(
        "find acceleration given initial velocity 0 final velocity 20 time 4"
    )
    assert "5" in answer, f"expected 5 in answer, got {answer!r}"


# ── mass density ──────────────────────────────────────────────────────────────
# ρ = m / V


def test_mass_density(vy):
    """ρ = m / V: m=60, V=2 → ρ=30"""
    answer = vy.ask("find density given mass 60 volume 2")
    assert "30" in answer, f"expected 30 in answer, got {answer!r}"


# ── pressure ──────────────────────────────────────────────────────────────────
# P = F / A


def test_pressure(vy):
    """P = F / A: F=100, A=5 → P=20"""
    answer = vy.ask("find pressure given force 100 area 5")
    assert "20" in answer, f"expected 20 in answer, got {answer!r}"


# ── angular velocity ──────────────────────────────────────────────────────────
# ω = v / r


def test_angular_velocity(vy):
    """ω = v / r: v=30, r=3 → ω=10"""
    answer = vy.ask("find angular velocity given velocity 30 radius 3")
    assert "10" in answer, f"expected 10 in answer, got {answer!r}"


# ── centripetal force ─────────────────────────────────────────────────────────
# F = m * v² / r


def test_centripetal_force(vy):
    """F = m*v²/r: m=2, v=10, r=5 → F=40"""
    answer = vy.ask("find centripetal force given mass 2 velocity 10 radius 5")
    assert "40" in answer, f"expected 40 in answer, got {answer!r}"


# ── capacitance ───────────────────────────────────────────────────────────────
# C = Q / V


def test_capacitance(vy):
    """C = Q / V: Q=0.006, V=12 → C=0.0005"""
    answer = vy.ask("find capacitance given charge 0.006 voltage 12")
    assert "0.0005" in answer or "5e-4" in answer.lower(), (
        f"expected 0.0005 in answer, got {answer!r}"
    )


# ── frequency ─────────────────────────────────────────────────────────────────
# f = 1 / T  (structural fix needed: missing constant 1 in krama-rhs — deferred to P8f)


def test_frequency(vy):
    """f = 1 / T: T=0.5 → f=2"""
    answer = vy.ask("find frequency given period 0.5")
    assert "2" in answer, f"expected 2 in answer, got {answer!r}"


# ── period ────────────────────────────────────────────────────────────────────
# T = 2π / ω  (structural fix needed: missing pi,2 constants — deferred to P8f)


def test_period(vy):
    """T = 2π / ω: ω=2 → T=π≈3.14159"""
    answer = vy.ask("find period given angular velocity 2")
    assert "3.14" in answer, f"expected 3.14... in answer, got {answer!r}"


# ── gravitational force ───────────────────────────────────────────────────────
# F = G*m1*m2 / r²  (stack machine cannot express this cleanly — deferred to P8f)


@pytest.mark.xfail(
    reason="structural: gravitational-force-mantra krama=[mul,mul,square,div] "
    "cannot correctly square r with current stack machine; "
    "deferred to P8f (expression graph)",
    strict=True,
)
def test_gravitational_force(vy):
    """F = G*m1*m2/r²: G=6.674e-11, m1=5.972e24, m2=7.34e22, r=3.84e8 → F≈1.98e20"""
    answer = vy.ask(
        "find gravitational force given gravitational constant 6.674e-11 "
        "mass1 5.972e24 mass2 7.34e22 radius 3.84e8"
    )
    # 1.98e20 — check order of magnitude is right
    assert "1.98" in answer or "1.984" in answer, (
        f"expected ~1.98e20 in answer, got {answer!r}"
    )


# ── photon energy (P8f Way 2 sandhi + math-domain) ───────────────────────────
# E = h * f  — planck-constant auto-supplied from physics-constants.shabda


def test_photon_energy_from_frequency(vy):
    """E = h*f: h=6.626e-34, f=5e14 → E≈3.313e-19 J"""
    answer = vy.ask("find photon energy given frequency 5e14")
    # 6.62607015e-34 * 5e14 = 3.31303508e-19
    assert "3.31" in answer or "3.313" in answer, (
        f"expected ~3.313e-19 in answer, got {answer!r}"
    )


def test_photon_energy_different_frequency(vy):
    """E = h*f: h=6.626e-34, f=6e14 → E≈3.976e-19 J"""
    answer = vy.ask("find photon energy given frequency 6e14")
    assert "3.97" in answer or "3.976" in answer, (
        f"expected ~3.976e-19 in answer, got {answer!r}"
    )


def test_photon_energy_high_frequency(vy):
    """E = h*f: h=6.626e-34, f=1e15 → E≈6.626e-19 J"""
    answer = vy.ask("find photon energy given frequency 1e15")
    assert "6.62" in answer or "6.626" in answer, (
        f"expected ~6.626e-19 in answer, got {answer!r}"
    )


def test_planck_constant_auto_supplied(vy):
    """planck-constant has constants-key → auto-supplied without explicit value"""
    # no 'planck constant' given in query — must be looked up automatically
    answer = vy.ask("find photon energy given frequency 5e14")
    assert "no match" not in answer, (
        "planck-constant should be auto-supplied from constants, got no match"
    )


# ── mass density via satya+satya compound (Way 2) ────────────────────────────
# ρ = m / V  — "mass density" resolves as compound via sandhi Way 2


def test_mass_density_satya_compound(vy):
    """'mass density' as satya+satya compound → mass-density node"""
    answer = vy.ask("find mass density given mass 500 volume 0.25")
    # ρ = 500 / 0.25 = 2000
    assert "2000" in answer, f"expected 2000 in answer, got {answer!r}"


def test_mass_density_compound_matches_direct(vy):
    """'mass density' compound query gives same result as direct 'density' query"""
    answer_compound = vy.ask("find mass density given mass 60 volume 2")
    answer_direct = vy.ask("find density given mass 60 volume 2")
    assert "30" in answer_compound, (
        f"expected 30 via compound query, got {answer_compound!r}"
    )
    assert "30" in answer_direct, f"expected 30 via direct query, got {answer_direct!r}"
