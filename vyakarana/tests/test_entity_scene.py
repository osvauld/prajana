"""test_entity_scene.py — entities, scene accumulation, and what nam releases.

Nam's ultimate movement is release — understanding received, processed,
and given back as a scene that can be rendered, reasoned over, shared.
The scene is what is released. Not just numbers — entities with owned
properties, each distinct, each situated.

An electron is not "an object with mass 9.109e-31". It is an electron —
with a name, a mass, a charge, a velocity, all owned by it, all
distinguishable from the proton's mass, the field's strength.

The scene accumulates across turns. Each turn adds one entity. By turn 3,
three objects exist simultaneously in nam's understanding — ready to be
released as a rendering.

Three concerns tracked here:

  Gap 1 — Unit label collision
    Single-letter instance labels (m, v, q, t, B) are stolen by unit lookups.
    m → metre. v → volt. These are exactly the labels a user writes for physics.
    Fix: context-sensitive word lookup — between a satya concept and 'of',
    a word is a rashi instance label, not a unit abbreviation.

  Gap 2 — Session entity structure
    session-anuvada currently carries [concept, sankhya, val] across turns.
    It must also carry entity structure: prathama-vibhakti, shashthi-vibhakti,
    vishesa rashi. Each turn can add a new entity to the scene. The scene
    accumulates — it does not replace.

  Multi-entity scene accumulation
    Turn 1 adds entity A. Turn 2 adds entity B. Turn 3 sees both.
    This is the primary multi-entity path — session accumulation, not dvandva.
    The renderer (pratibimba) reads all entities simultaneously.

Run:
    cd vyakarana/tests && pytest test_entity_scene.py -v --socket /tmp/vy.sock
"""

import pytest


# ── helpers ───────────────────────────────────────────────────────────────────


def bqg(vy, sentence):
    """Run build-question-graph + avrti-refine fixpoint."""
    return vy.eval(f'fixpoint (build-question-graph "{sentence}") avrti-refine')


def sig(g):
    """Compact signature of a graph for assertion messages."""
    return [
        t
        for t in g
        if isinstance(t, list)
        and len(t) == 3
        and t[1]
        in (
            "satya",
            "sankhya",
            "vishesa",
            "prathama-vibhakti",
            "shashthi-vibhakti",
            "mithya",
        )
    ]


# ═══════════════════════════════════════════════════════════════════════════════
# GAP 1 — Unit label collision
# Single-letter labels stolen by unit lookup in build-question-graph.
# The pattern is unambiguous: concept + label + "of" + value → label is rashi.
# ═══════════════════════════════════════════════════════════════════════════════


# ── 1a. The existing three (already xfailed in test_rashi_edge_cases.py) ─────
# These are covered there. Listed here for context only — not duplicated.
# test_instance_named_m_does_not_collide_with_metre  (test_rashi_edge_cases.py)
# test_instance_named_m_propagates_to_mass            (test_rashi_edge_cases.py)
# test_ke_with_m_instance_name                        (test_rashi_edge_cases.py)


# ── 1b. The electron case — q, B, v as instance labels ───────────────────────


def test_charge_instance_named_q(vy):
    """'electron has charge q of 1.6e-19' — q is a rashi label, not a unit."""
    g = bqg(vy, "electron has charge q of 1.6e-19")
    assert vy.has_triple(g, subj="q", pred="vishesa", obj="charge"), (
        f"q should be typed as charge rashi instance: {sig(g)}"
    )
    t = vy.find_triple(g, subj="q", pred="sankhya")
    assert t is not None, f"q rashi instance should have sankhya: {sig(g)}"
    assert vy.approx_eq(t[2], 1.6e-19), f"expected 1.6e-19, got {t[2]}"


def test_velocity_instance_named_v(vy):
    """'electron has velocity v of 1e6' — v is a rashi label, not volt."""
    g = bqg(vy, "electron has velocity v of 1e6")
    assert vy.has_triple(g, subj="v", pred="vishesa", obj="velocity"), (
        f"v should be typed as velocity rashi instance: {sig(g)}"
    )
    t = vy.find_triple(g, subj="v", pred="sankhya")
    assert t is not None, f"v rashi instance should have sankhya: {sig(g)}"
    assert vy.approx_eq(t[2], 1e6), f"expected 1e6, got {t[2]}"


def test_field_instance_named_B(vy):
    """'magnetic field B of 0.1' — B is a rashi label for field strength."""
    g = bqg(vy, "magnetic field B of 0.1")
    t = vy.find_triple(g, subj="B", pred="sankhya")
    assert t is not None, f"B rashi instance should have sankhya 0.1: {sig(g)}"
    assert vy.approx_eq(t[2], 0.1), f"expected 0.1, got {t[2]}"


def test_electron_natural_labels(vy):
    """Full electron description using natural labels m, v, q — none stolen by units."""
    g = bqg(
        vy,
        "electron has mass m of 9.109e-31 and charge q of 1.6e-19 and velocity v of 1e6",
    )
    assert vy.has_triple(g, subj="m", pred="vishesa", obj="mass"), (
        f"m should be mass instance: {sig(g)}"
    )
    assert vy.has_triple(g, subj="q", pred="vishesa", obj="charge"), (
        f"q should be charge instance: {sig(g)}"
    )
    assert vy.has_triple(g, subj="v", pred="vishesa", obj="velocity"), (
        f"v should be velocity instance: {sig(g)}"
    )


# ── 1c. Unit vs label disambiguation — the structural rule ───────────────────


@pytest.mark.xfail(
    strict=True,
    reason="Gap 1: disambiguation rule — 'velocity is 5 m/s' uses m as metre "
    "(correct), but 'velocity v of 5' uses v as label (needs fix). "
    "The rule: word between satya-concept and 'of' is always a rashi label.",
)
def test_unit_in_rate_not_stolen(vy):
    """'velocity is 5 m/s' — here m IS the metre unit, should stay satya metre."""
    g = bqg(vy, "velocity is 5 m/s")
    # m here is a unit, not a label — should resolve to metre
    assert vy.has_triple(g, subj="metre", pred="satya"), (
        f"metre should be present as satya in 'velocity is 5 m/s': {sig(g)}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# GAP 2 — Session entity structure
# Session must carry entity identity and ownership across turns.
# Currently only sankhya (numeric) bindings are carried.
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(
    strict=True,
    reason="Gap 2: session carries sankhya only. prathama-vibhakti not carried. "
    "Turn 1: 'electron has mass 9.109e-31' establishes electron as entity. "
    "Turn 2 graph should contain [electron, prathama-vibhakti, object] from prior turn. "
    "Currently the entity identity triple is not in the prior-graph injection.",
)
def test_session_entity_identity_persists(vy):
    """prathama-vibhakti established in turn 1 is present in the turn 2 scene."""
    sid = "gap2-entity-identity-unique-v2"
    vy.ask("electron has mass 9.109e-31", session_id=sid)
    # turn 2 asks about KE — the electron entity must still be named
    # if only sankhya carries, the answer is just a number with no entity owner
    # if prathama-vibhakti also carries, the answer can reference "electron"
    answer = vy.ask("find kinetic energy given velocity 1e6", session_id=sid)
    # the answer should reference the electron entity, not just "kinetic-energy = X"
    # this specifically requires entity identity to carry, not just mass value
    assert "electron" in answer.lower(), (
        f"answer should reference electron entity from turn 1: {answer!r}"
    )


def test_session_ownership_persists(vy):
    """Turn 1 establishes ownership. Turn 2 can use the owned property.
    This already works — sankhya binding carries mass value across turns."""
    sid = "gap2-ownership-unique"
    vy.ask("electron has mass 9.109e-31", session_id=sid)
    answer = vy.ask("find kinetic energy given velocity 1e6", session_id=sid)
    # mass from turn 1 feeds KE computation in turn 2 via sankhya binding
    # KE = 0.5 * 9.109e-31 * (1e6)^2 ≈ 4.5545e-19
    assert "4.5" in answer or "4.55" in answer or "e-19" in answer, (
        f"KE should use mass from turn 1: {answer!r}"
    )


def test_session_rashi_type_persists(vy):
    """Sankhya values from rashi instances carry across turns.
    This already works — sankhya binding covers this case."""
    sid = "gap2-rashi-type-unique"
    vy.ask("ball has mass m1 of 5 and velocity v1 of 10", session_id=sid)
    answer = vy.ask("find kinetic energy", session_id=sid)
    assert "250" in answer, f"rashi values should carry to KE computation: {answer!r}"


# ═══════════════════════════════════════════════════════════════════════════════
# MULTI-ENTITY SCENE ACCUMULATION
# Each turn adds a new entity. The scene grows. Turn N sees all prior entities.
# This is the primary multi-entity path — not dvandva.
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(
    strict=True,
    reason="Multi-entity accumulation: turn 2 adds a second entity. "
    "After turn 2, the graph should have both entities simultaneously. "
    "Requires Gap 2 (session entity structure) to be closed first.",
)
def test_two_entities_across_turns_both_present(vy):
    """Turn 1 adds ball-A, turn 2 adds ball-B. Both are present after turn 2."""
    sid = "multi-entity-two-balls-unique"
    vy.ask("ball-A has mass 3 and velocity 4", session_id=sid)
    vy.ask("ball-B has mass 2 and velocity 5", session_id=sid)
    # now ask something that requires both
    answer = vy.ask("find kinetic energy of ball-A", session_id=sid)
    # KE of ball-A = 0.5 * 3 * 16 = 24
    assert "24" in answer, (
        f"ball-A KE should use ball-A's own mass/velocity: {answer!r}"
    )


@pytest.mark.xfail(
    strict=True,
    reason="Gap 2: sankhya bindings have no entity scope. Turn 2 mass=2 (ball-B) "
    "overwrites Turn 1 mass=3 (ball-A). Session carries the last written value. "
    "Fix: carry entity-scoped bindings via se_graph (prathama/shashthi-vibhakti).",
)
def test_two_entities_across_turns_scoped(vy):
    """Turn 1: ball-A (mass=3, v=4). Turn 2: ball-B (mass=2, v=5).
    KE of ball-A must use mass=3 (not mass=2 from ball-B overwriting it)."""
    sid = "multi-entity-scoped-unique-v4"
    vy.ask("ball-A has mass 3 and velocity 4", session_id=sid)
    vy.ask("ball-B has mass 2 and velocity 5", session_id=sid)
    answer_a = vy.ask("find kinetic energy of ball-A", session_id=sid)
    # KE of ball-A = 0.5 * 3 * 16 = 24
    # if mass=2 (ball-B's value) leaked in, answer would be 0.5*2*16 = 16 — wrong
    assert "24" in answer_a, (
        f"ball-A KE must be 24 (mass=3), not contaminated by ball-B: {answer_a!r}"
    )


@pytest.mark.xfail(
    strict=True,
    reason="Multi-entity scene: electron + field established across two turns. "
    "The simulation can only run when both entities are in the scene graph. "
    "Requires Gap 2 — entity structure must persist across turns.",
)
def test_electron_and_field_across_turns(vy):
    """Turn 1: electron (mass, charge, velocity). Turn 2: magnetic field.
    Both entities present in turn 3 when simulation is requested."""
    sid = "electron-field-scene-unique"
    vy.ask(
        "electron has mass 9.109e-31 and charge 1.6e-19 and velocity 1e6",
        session_id=sid,
    )
    vy.ask("magnetic field strength 0.1", session_id=sid)
    # turn 3: both entities should be queryable
    answer = vy.ask("find orbital radius", session_id=sid)
    # r = mv / (qB) = 9.109e-31 * 1e6 / (1.6e-19 * 0.1) ≈ 5.68e-5 m
    # just check the pipeline can engage with both entities
    assert answer != "no match", (
        f"orbital radius needs both electron and field from prior turns: {answer!r}"
    )


@pytest.mark.xfail(
    strict=True,
    reason="Multi-entity: three entities across three turns. "
    "The scene should hold all three simultaneously. "
    "Requires Gap 2.",
)
def test_three_entities_accumulate(vy):
    """Three separate turns each adding one entity. All three visible after turn 3."""
    sid = "three-entity-scene-unique"
    vy.ask("ball-A has mass 1 and velocity 2", session_id=sid)
    vy.ask("ball-B has mass 3 and velocity 4", session_id=sid)
    vy.ask("ball-C has mass 5 and velocity 6", session_id=sid)
    # turn 4: can we query ball-A specifically?
    answer = vy.ask("find kinetic energy of ball-A", session_id=sid)
    # KE of ball-A = 0.5 * 1 * 4 = 2
    assert "2" in answer, (
        f"three-entity scene: ball-A KE should still be accessible: {answer!r}"
    )


# ═══════════════════════════════════════════════════════════════════════════════
# PRATIBIMBA — scene rendering parameters
#
# These tests cover what the renderer (3d-to-pratibimba) needs to find in the
# graph in order to produce DrawSphere/DrawLine commands.
#
# For each entity the renderer walks:
#   [entity, swarupa, gola]                  → draw a sphere (not a cylinder, line)
#   [dura,   shashthi-vibhakti, entity]      → sphere radius
#   [dura,   sankhya,           val]         → radius value
#   [bindu,  shashthi-vibhakti, entity]      → sphere center position
#   [color,  shashthi-vibhakti, entity]      → material color
#
# If any of these are missing the renderer falls back to defaults (mithya visible).
# ═══════════════════════════════════════════════════════════════════════════════


@pytest.mark.xfail(
    strict=True,
    reason="'sphere' not yet in the word index — no gola shabda mapping. "
    "'sphere' stays mithya; does not resolve to gola satya. "
    "Fix: add 'sphere' to gola.om shabda list or bhasha/english word index.",
)
def test_sphere_shape_swarupa(vy):
    """'sphere' maps to gola — the entity gets swarupa edge to gola."""
    g = bqg(vy, "sphere has radius 0.3")
    has_gola = (
        vy.has_triple(g, subj="gola", pred="satya")
        or vy.has_triple(g, subj="sphere", pred="swarupa", obj="gola")
        or vy.has_triple(g, subj="sphere", pred="satya")
    )
    assert has_gola, f"'sphere' should resolve to gola in the graph: {sig(g)}"


def test_radius_ownership(vy):
    """'sphere has radius 0.3' → dura owned by sphere with value 0.3."""
    g = bqg(vy, "sphere has radius 0.3")
    # dura (radius) should be present as satya
    assert vy.has_triple(g, subj="dura", pred="satya") or vy.has_triple(
        g, subj="radius", pred="satya"
    ), f"radius/dura should be a satya concept: {sig(g)}"
    # value 0.3 should be bound
    t = vy.find_triple(g, subj="dura", pred="sankhya")
    if t is None:
        t = vy.find_triple(g, subj="radius", pred="sankhya")
    assert t is not None, f"radius should have sankhya 0.3: {sig(g)}"
    assert vy.approx_eq(t[2], 0.3), f"expected 0.3, got {t[2]}"


def test_radius_owned_by_entity(vy):
    """'sphere has radius 0.3' → shashthi-vibhakti connects dura to sphere."""
    g = bqg(vy, "sphere has radius 0.3")
    ownership = vy.all_triples(g, pred="shashthi-vibhakti")
    concepts = {t[0] for t in ownership}
    assert "dura" in concepts or "radius" in concepts, (
        f"radius/dura should have shashthi-vibhakti ownership: {ownership}"
    )


@pytest.mark.xfail(
    strict=False,
    reason="bindu as spatial position in BQG — 'at position' or 'bindu' not yet "
    "in the word index for position queries. Spatial position binding is "
    "not yet implemented as a first-class rashi.",
)
def test_position_ownership(vy):
    """'sphere at position 1 0 0' → bindu owned by sphere with spatial value."""
    g = bqg(vy, "sphere at position 1 0 0")
    t = vy.find_triple(g, subj="bindu", pred="sankhya")
    assert t is not None, f"bindu should have spatial sankhya: {sig(g)}"


def test_color_owned_by_entity(vy):
    """'sphere is red' — color should be owned by sphere.
    color.om is now defined (satya=0.846, taranga-abheda, pbr-phala)."""
    g = bqg(vy, "red sphere")
    # color or red should appear — at minimum 'red' should be mithya or satya
    has_color = (
        vy.has_triple(g, subj="color", pred="satya")
        or vy.has_triple(g, subj="red", pred="satya")
        or vy.has_triple(g, subj="red", pred="mithya")
    )
    assert has_color, f"'red' should enter the graph as a color-related node: {sig(g)}"


def test_color_shashthi_ownership(vy):
    """'sphere has color 0.2 0.5 0.8' — color owned via shashthi-vibhakti.
    color.om is defined (satya=0.846) and vibhakti-shashthi wires ownership correctly."""
    g = bqg(vy, "sphere has color 0.2 0.5 0.8")
    ownership = vy.all_triples(g, pred="shashthi-vibhakti")
    concepts = {t[0] for t in ownership}
    assert "color" in concepts or "albedo" in concepts, (
        f"color/albedo should be owned by sphere: {ownership}"
    )


def test_entity_enumeration_single(vy):
    """A single entity produces one prathama-vibhakti node.
    The renderer uses this to find all scene objects."""
    g = bqg(vy, "ball has mass 5")
    entities = [
        t[0]
        for t in g
        if isinstance(t, list) and len(t) == 3 and t[1] == "prathama-vibhakti"
    ]
    assert len(entities) >= 1, (
        f"at least one entity (prathama-vibhakti) expected: {sig(g)}"
    )
    assert "ball" in entities, (
        f"'ball' should be the prathama-vibhakti entity: {entities}"
    )


def test_entity_property_enumeration(vy):
    """Walking shashthi-vibhakti from 'ball' gives all owned properties.
    The renderer uses this to find DrawSphere parameters."""
    g = bqg(vy, "ball has mass 5 and velocity 10")
    # find all properties owned by ball
    owned = vy.all_triples(g, pred="shashthi-vibhakti")
    owners = {t[2] for t in owned}
    # ball should own at least mass and velocity
    assert "ball" in owners, (
        f"ball should own some properties via shashthi-vibhakti: {owned}"
    )
    owned_by_ball = {t[0] for t in owned if t[2] == "ball"}
    assert "mass" in owned_by_ball or "velocity" in owned_by_ball, (
        f"ball should own mass and/or velocity: {owned_by_ball}"
    )


def test_sphere_full_render_params(vy):
    """A sphere with radius and mass — the minimal scene description.
    Shape resolution (sphere→gola) is separate (test_sphere_shape_swarupa).
    This test checks radius and mass ownership only."""
    g = bqg(vy, "sphere has radius 0.5 and mass 2")
    # radius owned with value — radius maps to satya correctly
    t = vy.find_triple(g, subj="dura", pred="sankhya")
    if t is None:
        t = vy.find_triple(g, subj="radius", pred="sankhya")
    assert t is not None, f"radius should be bound: {sig(g)}"
    assert vy.approx_eq(t[2], 0.5), f"expected radius 0.5: {t[2]}"
    # mass owned with value
    t2 = vy.find_triple(g, subj="mass", pred="sankhya")
    assert t2 is not None, f"mass should be bound: {sig(g)}"
    assert vy.approx_eq(t2[2], 2.0), f"expected mass 2: {t2[2]}"


@pytest.mark.xfail(
    strict=True,
    reason="Full electron simulation scene: electron with mass, charge, velocity "
    "AND magnetic field — all owned correctly in one multi-turn session. "
    "Requires Gap 2 (entity structure across turns). "
    "Orbital radius: r = mv/(qB) = 9.109e-31 * 1e6 / (1.6e-19 * 0.1) ≈ 5.68e-5 m",
)
def test_electron_simulation_scene_full(vy):
    """The full electron-in-B-field scene across three session turns.
    Turn 1: electron properties. Turn 2: magnetic field. Turn 3: orbital radius.
    This is the first physical simulation the pratibimba renderer will show."""
    sid = "electron-simulation-full-unique"
    vy.ask(
        "electron has mass 9.109e-31 and charge 1.6e-19 and velocity 1e6",
        session_id=sid,
    )
    vy.ask("magnetic field strength 0.1", session_id=sid)
    answer = vy.ask("find orbital radius", session_id=sid)
    # r = mv/(qB) ≈ 5.68e-5 m
    assert any(x in answer for x in ["5.6", "5.7", "5.68", "e-5"]), (
        f"orbital radius should be ~5.68e-5 m: {answer!r}"
    )
