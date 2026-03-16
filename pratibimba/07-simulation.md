# 07 — Simulation

**The simulation is not separate from understanding. It IS the understanding made dynamic.**

---

## The simulation object IS a rashi

Before we can simulate anything, we need to understand what a simulation object IS
in the graph's terms.

A simulation object is a rashi — a quantity instance.
Not the concept `gola` — but `gola-A`, a specific sphere in a specific scene.
The rashi structure is what makes it a real object, not just a concept:

```
[gola-A, prathama-vibhakti, object]     ← gola-A IS an entity in this scene
[gola-A, vishesa,           rashi]      ← gola-A IS a quantity instance
[mass,   shashthi-vibhakti, gola-A]     ← mass BELONGS TO gola-A
[mass,   sankhya,           9.109e-31]  ← mass value
[bindu,  shashthi-vibhakti, gola-A]     ← position BELONGS TO gola-A
[bindu,  sankhya,           (0,0,0)]    ← position value
[velocity, shashthi-vibhakti, gola-A]
[velocity, sankhya,           (1e6,0,0)]
```

This is not aspirational. The entity+rashi+shashthi-vibhakti structure is implemented
and working (`test_pipeline_entity_owns_mass` passes). The graph can already build
this structure from a well-formed sentence.

The render reads this directly — `shashthi-vibhakti` edges tell it what
properties the object owns, and `sankhya` edges give the values.
`DrawSphere` at `bindu` with `dura` comes from walking these edges.
No separate scene data structure. The graph IS the simulation state.

---

## The electron as first case

The electron in a magnetic field is the first physical simulation to render.
It is chosen because it is simple, precise, and beautiful.

The Lorentz force is always perpendicular to velocity.
Perpendicular force means the speed never changes — only direction.
Constant speed, changing direction, at constant distance from a center —
this is avrti. This is a vrtta.
The electron does not move in a circle because we programmed a circle.
It moves in a circle because the Lorentz force IS the definition of avrti at constant dura.

This is what the graph should understand and what the render should show.

---

## What the graph already knows

The graph already has:
- electron — with mass and charge as owned constants
- magnetic-field — connected to force, velocity, charge
- velocity-step and position-step — the Euler integrators
- avastha — state before and after each step
- force — connected to acceleration

What is missing:
- lorentz-force — the specific relation: F = q(v × B)
- vec-cross — the cross product operation that gives perpendicular force
- The numeric constants bound to electron-mass and elementary-charge
- A tantra that chains these into one simulation step

These are small additions. The concepts are already conceptually present
in the connections between electron, velocity, magnetic-field, and force.
The missing pieces are the precise formulation and the numeric values.

---

## The simulation is avrti of the graph state

Each frame of the simulation is one turn of avrti.
The graph holds the current avastha of the electron —
position, velocity, the current Lorentz force.

One turn:
The force is computed from charge, velocity, and field.
The velocity is updated from force and mass.
The position is updated from velocity.
This is derive-step — the proof graph's own fixpoint mechanism,
now running not to convergence but continuously,
each pass advancing the simulation by dt.

The position-step and velocity-step already exist in the kosha.
They know what they are: integrators that advance state through time.
The simulation is just asking them to run on the electron's owned quantities.

---

## The trajectory is the path of avrti

As the simulation runs, the electron traces a path through akasham.
Each frame, its position is one more bindu in the trajectory.
The trajectory IS the krama of bindu through time — bindu-krama-siddha.

This is trajectory.om: gati-swarupa, kaala-yukta, akasham-sthita bindu-krama-siddha.
The trajectory is already defined as a concept. The simulation fills it.

From above (camera looking along the B-field axis):
the trajectory draws a vrtta — avrti in tala.
From the side: a helix if the electron has velocity along the field,
a circle if it does not.
The darshana determines what shape is visible.

---

## The simulation is also a sound

The electron's orbit has a frequency — the cyclotron frequency.
ω = qB/m. For B=0.1T and an electron: ω ≈ 1.76×10¹⁰ Hz.
Shifted down by octaves into the audible range, this IS a tone.

The simulation produces audio naturally. The same owned quantities
that determine the visual orbit (charge, mass, field strength)
also determine the pitch of the tone. The EpochOutput carries both:
the visual orbit and the audio tone are the same physical fact
expressed through two senses simultaneously.

A stronger field → smaller orbit AND higher pitch.
A heavier particle → larger orbit AND lower pitch.
The audio is not decoration. It IS the simulation, heard.

This is why the epoch output carries visual + audio together.
They both come from the same graph state. They are the same anuvada
applied to the same truth through different senses.

---

## The graph reveals the answer

While the simulation runs, the graph also holds the answer.
The orbital radius: r = mv / (qB).
The orbital period: T = 2πm / (qB).
These are derived from the same quantities the simulation uses.

The graph can compute these from the owned properties of the electron node.
The answer appears as text in the scene — DrawLabel.
The simulation shows the answer in motion and sounds it as a tone.
They are the same truth, three darshanas.

---

## The dvandva gap — two objects in one scene

Two spheres colliding requires dvandva — the multi-entity architecture.
Currently the pipeline handles one entity at a time.
"Two spheres approach each other" has two entities (gola-A, gola-B),
each with their own rashi structure, their own owned mass and velocity.

The dvandva tantra (Phase 4, not yet built) walks `prathama-vibhakti` nodes,
scopes `shashthi-vibhakti` per entity, fires mantras within each scope.
Until this exists, the collision simulation requires the entities to be
established separately — one sentence for each — rather than from one scene description.

This does not prevent building the simulation. It means the current path is:
Turn 1: "electron, charge 1.6e-19, mass 9.109e-31, velocity 1e6 along x"
Turn 2: "magnetic field 0.1T along z"
Turn 3: "run lorentz simulation"

Each turn deepens the rashi structure. The dvandva tantra will allow
all of this in one sentence. Until then, turns do the same work.

---

## Beyond the electron

The electron case establishes the pattern for all simulations:
- Define the force law as a kosha concept with janya and phala edges
- Define the simulation step as a tantra that applies the force law
- The rashi structure carries the per-object values
- Run derive-step on the scene objects each frame — reads shashthi-vibhakti
- The render reads positions and draws what it finds

The same pattern works for:
- Two spheres colliding — collision mantra fires when distance ≤ sum of radii
  (requires dvandva for natural language input — one entity at a time until Phase 4)
- Planets orbiting — gravitational force law, same Euler integration
- A spring-mass system — spring-force.om already exists in the kosha
- Fluid flow — navier-stokes.om already exists in the kosha

Each new physics concept added to the kosha
becomes a new kind of simulation the interface can run.
The graph grows. The simulation space grows with it.

---

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-16 | Initial writing |
| 2026-03-16 | Added: simulation produces audio naturally. Cyclotron frequency IS a tone. The same owned quantities determine orbit AND pitch. EpochOutput carries both simultaneously. |
| 2026-03-16 | Added: simulation object IS a rashi (entity+vishesa+shashthi-vibhakti). The rashi structure IS the simulation object. dvandva gap noted — two entities require Phase 4. Current path: establish entities across session turns. |
