"""test_complex_sentences.py — complex sentence patterns and group interactions.

These tests push beyond single-entity scalar computation into:
  - Natural verb variation (moves, travels, is moving)
  - Article words before known concepts (the electron, a proton)
  - Entity scope in second position (find X of ball-B)
  - KE inverse: find mass or velocity from kinetic energy
  - Two-entity group interactions (relative velocity, gravitational force)

Relative velocity is not a new physical law. Both velocities are dx/dt with
the same dt — same scene, same time frame (sthira-apeksha). v_rel = v_A - v_B
is the arithmetic of that shared reference. The graph already knows this shape:
initial-velocity and final-velocity are velocity wearing an avastha. Relative
velocity is velocity wearing an apeksha (reference frame). Same pattern, different
qualifier. The kosha needs to declare it; the pipeline reads it the same way.

Group interactions (gravitational force) require sthita-viveka: the pipeline
must ask which entity fills which janya slot (mass1, mass2), not collapse both
to a flat 'mass'. This is the next structural piece after entity-scoped lookup.

Run:
    cd /home/abe/agent_x && .venv/bin/pytest vyakarana/tests/test_complex_sentences.py -v --socket /tmp/vy.sock
"""

import pytest


# ── helpers ──────────────────────────────────────────────────────────────────


def answer(vy, sentence):
    return vy.eval(f'anuvada-ganana "{sentence}"')


def bqg(vy, sentence):
    return vy.eval(f'fixpoint (build-question-graph "{sentence}") avrti-refine')


# ── Section 1: entity scope in second position ────────────────────────────────
# "find X of ball-B" — scope entity is not the first entity in the scene.
# Currently extract-solve-for only detects the first mithya/satya entity after
# the solve-for concept. When ball-B appears after ball-A in the graph, the
# first entity detected is ball-A (which appears earlier as prathama-vibhakti).


def test_find_second_entity_momentum(vy):
    """find momentum of ball-B when ball-A appears first in the scene."""
    r = answer(
        vy,
        "ball-A has mass 3 and velocity 4. "
        "ball-B has mass 5 and velocity 6. "
        "find momentum of ball-B",
    )
    # p = 5 * 6 = 30
    assert "30" in r, f"expected momentum=30 (ball-B), got {r}"


def test_find_second_entity_ke(vy):
    """find kinetic energy of ball-B when ball-A appears first."""
    r = answer(
        vy,
        "ball-A has mass 2 and velocity 3. "
        "ball-B has mass 4 and velocity 5. "
        "find kinetic energy of ball-B",
    )
    # KE = 0.5 * 4 * 25 = 50
    assert "50" in r, f"expected KE=50 (ball-B), got {r}"


# ── Section 2: article words before known concepts ────────────────────────────
# "the electron", "a proton" — the article is mithya, sits between "of" and
# the entity word, breaking scope detection. "of the electron" → the rashi-bandha
# signal fires on "of", then "the" is pending mithya, then "electron" is satya.
# The article needs to be transparent to scope detection.


@pytest.mark.xfail(
    strict=True,
    reason="'the' as pending mithya between 'of' and 'electron' breaks scope "
    "detection. extract-solve-for sees 'the-electron' compound attempt then "
    "loses the scope signal. Articles must be transparent to scope resolution.",
)
def test_find_ke_of_the_electron_given_values(vy):
    """'find kinetic energy of the electron' — article before entity name."""
    r = answer(
        vy,
        "find kinetic energy of the electron given mass 9.109e-31 and velocity 1e6",
    )
    assert "4.5545e-19" in r, f"expected KE=4.5545e-19, got {r}"


def test_find_momentum_of_a_proton(vy):
    """'find momentum of a proton' — article before entity name."""
    r = answer(
        vy,
        "a proton has mass 1.67e-27 and velocity 2e6. find momentum of a proton",
    )
    assert "3.34e-21" in r, f"expected momentum=3.34e-21, got {r}"


# ── Section 3: KE inverse — find mass or velocity ────────────────────────────
# "kinetic energy is 50 and velocity is 10. find mass." — inversion of KE = ½mv²
# Currently bound-vals returns [] when called on a graph that comes from fixpoint
# directly (server-side graph passing issue). The inverse path exists in the
# tantra (invert-math.tantra2) but the val-pairs are empty so it cannot fire.


def test_inverse_ke_find_mass(vy):
    """KE = ½mv² inverted: KE=50, v=10 → mass=1"""
    r = answer(vy, "kinetic energy is 50 and velocity is 10. find mass")
    assert "1" in r, f"expected mass=1, got {r}"


@pytest.mark.xfail(
    strict=True,
    reason="Same bound-vals issue — graph from fixpoint not normalised for reduce.",
)
def test_inverse_ke_find_velocity(vy):
    """KE = ½mv² inverted: KE=50, m=2 → velocity≈7.07"""
    r = answer(vy, "kinetic energy is 50 and mass is 2. find velocity")
    assert "7.07" in r, f"expected velocity≈7.07, got {r}"


def test_inverse_momentum_find_mass(vy):
    """p = mv inverted: p=20, v=5 → mass=4"""
    r = answer(vy, "momentum is 20 and velocity is 5. find mass")
    assert "4" in r, f"expected mass=4, got {r}"


# ── Section 4: relative velocity ─────────────────────────────────────────────
# Relative velocity is not a new law. Both velocities are dx/dt with the same
# dt — same scene, same sthira-apeksha (fixed time frame). v_rel = v_A - v_B.
# The kosha already declares initial-velocity and final-velocity as velocity
# wearing an avastha. Relative velocity is velocity wearing an apeksha
# (reference body). Same structural pattern: two velocity janya slots, krama=sub.
# Neither the kosha concept nor the mantra exist yet.


@pytest.mark.xfail(
    strict=True,
    reason="relative-velocity not in kosha. Needs: relative-velocity.om concept, "
    "relative-velocity-mantra.om with velocity1-janya + velocity2-janya + "
    "krama=sub, and sthita-viveka to assign each entity's velocity to the "
    "correct slot. Same pattern as initial/final velocity avastha — apeksha "
    "changes the reference body, not the concept.",
)
def test_relative_velocity_two_entities(vy):
    """v_rel = v_A - v_B: ball-A at 10, ball-B at 3 → relative velocity = 7"""
    r = answer(
        vy,
        "ball-A has velocity 10. ball-B has velocity 3. "
        "find relative velocity of ball-A with respect to ball-B",
    )
    assert "7" in r, f"expected relative velocity=7, got {r}"


@pytest.mark.xfail(
    strict=True,
    reason="Same — relative-velocity kosha concept not yet authored.",
)
def test_relative_velocity_opposite_directions(vy):
    """v_rel = v_A - v_B: A at 5, B at -3 → relative velocity = 8"""
    r = answer(
        vy,
        "ball-A has velocity 5. ball-B has velocity -3. "
        "find relative velocity of ball-A with respect to ball-B",
    )
    assert "8" in r, f"expected relative velocity=8, got {r}"


# ── Section 5: group interactions — gravitational force ──────────────────────
# F = G*m1*m2/r² requires sthita-viveka: the pipeline must assign each entity's
# mass to mass1-janya or mass2-janya, not collapse both to a flat 'mass'.
# The mantra already declares mass1-janya and mass2-janya as distinct slots.
# The missing piece: a tantra that reads the slot structure and asks
# "which entity fills which slot?" — sthita-viveka.


@pytest.mark.xfail(
    strict=True,
    reason="gravitational-force-mantra has mass1-janya and mass2-janya as distinct "
    "slots, but match-mantra only does flat concept lookup ('is mass in "
    "bound-concepts?'). With two entities each owning mass, the flat lookup "
    "cannot distinguish which mass fills which slot. Needs sthita-viveka: "
    "assign entity-owned properties to named janya slots.",
)
def test_gravitational_force_two_entities(vy):
    """F = G*m1*m2/r²: two entities, each owning a mass."""
    r = answer(
        vy,
        "particle-A has mass 5.972e24. "
        "particle-B has mass 7.34e22. "
        "find gravitational force given radius 3.84e8",
    )
    # F = 6.674e-11 * 5.972e24 * 7.34e22 / (3.84e8)^2 ≈ 1.98e20
    assert "1.98" in r, f"expected ~1.98e20, got {r}"


@pytest.mark.xfail(
    strict=True,
    reason="Same sthita-viveka gap — two masses need slot assignment.",
)
def test_gravitational_force_earth_moon(vy):
    """F = G*m1*m2/r²: earth and moon natural language."""
    r = answer(
        vy,
        "the earth has mass 5.972e24 kg. "
        "the moon has mass 7.34e22 kg. "
        "find gravitational force given radius 3.84e8",
    )
    assert "1.98" in r, f"expected ~1.98e20, got {r}"


# ── Section 6: natural verb variations ───────────────────────────────────────
# "moves at", "travels at", "is moving at" — these verbs signal motion/velocity
# ownership the same way "has" signals general ownership. Currently only
# shashthi-vibhakti (has/with) is recognised as a possession signal.


@pytest.mark.xfail(
    strict=True,
    reason="'moves' is not recognised as a possession/motion verb. Only 'has' "
    "and 'with' trigger shashthi-vibhakti. 'moves at velocity X' should "
    "bind velocity to the preceding entity the same way 'has velocity X' does. "
    "Needs motion verbs added to sandhi-viveka possession signal list.",
)
def test_proton_moves_at_velocity(vy):
    """'a proton moves at 2e6 m/s' — motion verb signals velocity ownership."""
    r = answer(
        vy,
        "a proton moves at 2e6 m/s. it has mass 1.67e-27 kg. find momentum",
    )
    assert "3.34e-21" in r, f"expected momentum=3.34e-21, got {r}"


@pytest.mark.xfail(
    strict=True,
    reason="Same — 'is moving at' not recognised as motion possession signal.",
)
def test_electron_is_moving_at(vy):
    """'the electron is moving at 1e6 m/s' — motion verb signals velocity."""
    r = answer(
        vy,
        "the electron has mass 9.109e-31 kg. "
        "it is moving at 1e6 m/s. "
        "find kinetic energy",
    )
    assert "4.5545e-19" in r, f"expected KE=4.5545e-19, got {r}"


# ── Section 7: inverse SUVAT — find time or initial velocity ─────────────────
# a = (v - u) / t is already in the kosha. Inversion should give t = (v - u) / a
# and u = v - a*t. The tantra (invert-math.tantra2) exists. The same bound-vals
# server-side issue blocks these — val-pairs empty, mantra cannot fire inverse.


@pytest.mark.xfail(
    strict=True,
    reason="bound-vals returns [] on graph from fixpoint (server-side VGraph vs "
    "VList issue). invert-math path exists but val-pairs are empty so it "
    "cannot fire. Same root cause as KE inverse tests.",
)
def test_inverse_suvat_find_time(vy):
    """a = (v-u)/t inverted: u=0, a=5, v=20 → t=4"""
    r = answer(
        vy,
        "initial velocity is 0. acceleration is 5. final velocity is 20. find time",
    )
    assert "4" in r, f"expected time=4, got {r}"


@pytest.mark.xfail(
    strict=True,
    reason="Same bound-vals issue.",
)
def test_inverse_suvat_find_initial_velocity(vy):
    """v = u + at inverted: v=30, a=5, t=4 → u=10"""
    r = answer(
        vy,
        "final velocity is 30. acceleration is 5. time is 4. find initial velocity",
    )
    assert "10" in r, f"expected initial-velocity=10, got {r}"


# ── Section 8: compound word lookup — spring-constant ────────────────────────
# "spring constant" should resolve via sandhi Way 2 (satya+satya) to
# spring-constant. Currently "spring" is mithya (not in kosha as satya) so
# Way 2 never fires — only Way 1 (mithya+satya) applies, and "spring-constant"
# is the correct compound. The pipeline sees "spring" as an unknown mithya
# modifier rather than recognising "spring constant" as a compound concept.


def test_spring_force_from_constant_and_displacement(vy):
    """F = k*x: k=200, x=0.1 → F=20"""
    r = answer(vy, "spring constant is 200 and displacement is 0.1. find spring force")
    assert "20" in r, f"expected spring-force=20, got {r}"


def test_spring_force_labelled(vy):
    """F = k*x with labelled rashi: k1=100, x1=0.05 → F=5"""
    r = answer(
        vy,
        "a spring has spring constant k1 of 100 and displacement x1 of 0.05. "
        "find spring force",
    )
    assert "5" in r, f"expected spring-force=5, got {r}"


# ── Section 9: total momentum — dvandva group sum ────────────────────────────
# Total momentum = sum of all entity momenta: P = m1*v1 + m2*v2.
# This is not a single-step mantra — it requires iterating over a group
# (dvandva collection) of entities and accumulating. The kosha declares
# total-momentum with samgraha-sthita (accumulation) and is not a mantra node.
# Needs dvandva group iteration (Phase 4) — not yet implemented.


@pytest.mark.xfail(
    strict=True,
    reason="total-momentum is a samgraha (accumulation) over a dvandva group. "
    "Not a single mantra — requires iterating over all entity-owned momenta "
    "and summing. dvandva group collection not yet implemented (Phase 4). "
    "total-momentum.om declares it as a kosha concept only, not a mantra node.",
)
def test_total_momentum_two_entities(vy):
    """P_total = m1*v1 + m2*v2: ball-A (3,4) + ball-B (2,5) → 12+10=22"""
    r = answer(
        vy,
        "ball-A has mass 3 and velocity 4. "
        "ball-B has mass 2 and velocity 5. "
        "find total momentum",
    )
    assert "22" in r, f"expected total-momentum=22, got {r}"


@pytest.mark.xfail(
    strict=True,
    reason="Same dvandva group iteration gap.",
)
def test_total_momentum_three_entities(vy):
    """P_total = 3*4 + 2*5 + 5*6 = 12+10+30 = 52"""
    r = answer(
        vy,
        "ball-A has mass 3 and velocity 4. "
        "ball-B has mass 2 and velocity 5. "
        "ball-C has mass 5 and velocity 6. "
        "find total momentum",
    )
    assert "52" in r, f"expected total-momentum=52, got {r}"


# ── Section 10: coulomb force — two charged particles ────────────────────────
# F = k*q1*q2/r² — same aneka-eka-swarupa (many-to-one) structure as
# gravitational force. coulomb.om declares particle-a-sthita and
# particle-b-sthita as required slots. Same sthita-viveka gap as gravitational.


@pytest.mark.xfail(
    strict=True,
    reason="coulomb interaction has particle-a-sthita and particle-b-sthita slots "
    "(declared in coulomb.om). match-mantra cannot assign each entity's charge "
    "to the correct slot — flat lookup collapses both charges. Same sthita-viveka "
    "gap as gravitational-force.",
)
def test_coulomb_force_two_charged_particles(vy):
    """F = kq1q2/r²: q1=q2=1.6e-19, r=1e-10 → F≈2.3e-8 N"""
    r = answer(
        vy,
        "particle-A has charge 1.6e-19. "
        "particle-B has charge 1.6e-19. "
        "find coulomb force given radius 1e-10",
    )
    # k = 8.99e9, F = 8.99e9 * (1.6e-19)^2 / (1e-10)^2 ≈ 2.3e-8
    assert "2.3" in r, f"expected ~2.3e-8, got {r}"
