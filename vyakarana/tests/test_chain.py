"""test_chain.py — multi-step chaining via derive-step fixpoint.

Tests that require intermediate derivations before the target mantra can fire.
derive-step.tantra fires all fully-covered mantras each pass; fixpoint in
anuvada-ganana accumulates bindings until the target is reachable.

Run:
    cd /home/abe/agent_x && .venv/bin/pytest vyakarana/tests/test_chain.py -v --socket /tmp/vy.sock
"""

import pytest


# ── two-step chain: u,a,t → v → KE ───────────────────────────────────────────


def test_chain_ke_from_kinematics(vy):
    """KE needs velocity; velocity must be derived from u=0, a=4, t=10, mass=1200.

    Step 1: velocity-mantra fires  (u=0, a=4, t=10)  → velocity = 40
    Step 2: kinetic-energy-mantra fires (mass=1200, velocity=40) → KE = 960000
    """
    answer = vy.eval(
        'anuvada-ganana "find kinetic energy given initial velocity 0 acceleration 4 time 10 mass 1200"'
    )
    assert "960000" in str(answer), f"expected 960000 in answer, got {answer!r}"


# ── two-step chain: u,v,t → a → F ────────────────────────────────────────────


def test_chain_force_from_suvat(vy):
    """Force needs acceleration; acceleration must be derived from u=0, v=20, t=4, mass=5.

    Step 1: acceleration-mantra fires (u=0, v=20, t=4) → acceleration = 5
    Step 2: newton-second-law-motion fires (mass=5, acceleration=5) → force = 25
    """
    answer = vy.eval(
        'anuvada-ganana "find force given initial velocity 0 final velocity 20 time 4 mass 5"'
    )
    assert "25" in str(answer), f"expected 25 in answer, got {answer!r}"
