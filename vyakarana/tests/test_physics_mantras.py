"""test_physics_mantras.py — end-to-end computation tests for physics mantras.

Tests that each mantra produces the correct numeric result via the full pipeline:
natural language question → BQG → avrti → derive-step → answer.

These tests cover mantras that use division or subtraction, which are affected
by the List.rev stack machine bug in execute-chain. The fix is to correct the
krama-rhs arg order in each .om file so the reversed stack yields the right result.

Status:
  - acceleration, mass-density, pressure, angular-velocity,
    centripetal, capacitance: fixed by krama-rhs swap (P8a)
  - frequency, period, gravitational: structural fix deferred to P8f
    (expression graph replaces stack machine entirely)

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


@pytest.mark.xfail(
    reason="structural: frequency-mantra needs constant 1 in krama-rhs; "
    "deferred to P8f (expression graph)",
    strict=True,
)
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
