"""test_chain.py — chained derivation: understanding building on itself.

Some relations cannot fire until others have established their phala.
To find kinetic energy from initial conditions, velocity must first be derived.
The chain is: axioms → velocity-mantra → kinetic-energy-mantra → answer.

This is not sequential computation. It is the accumulation of understanding.
Each mantra that fires adds its phala to what is known. The next mantra
recognises that the new knowledge satisfies its janya. Understanding deepens
until the target is reachable.

Derive-step runs to fixpoint — the same spiral as avrti, but at the mantra
level. Each pass: fire what is fully covered. Stop when nothing new can fire.

These tests ask: when the direct path is blocked, does nam find the chain?
Does understanding accumulate correctly across multiple mantra firings?

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
