# 01 — The Root

**avrti is the returning that is never the same twice.**

---

## Everything is avrti

The render loop is avrti. Not metaphorically — structurally.
Each frame returns to the same place carrying the samskaara of what happened.
The simulation has advanced. The graph has deepened. The scene has changed.
From outside it looks like a loop. From inside it is a spiral.

This is kaala-darshana: the vision that reveals the spiral.
The render loop looks like a vrtta (circle) when seen from above —
same beat, same rhythm, same frame structure.
But it IS a helix — rising through time, never returning to the same state.

The proof graph pipeline is avrti.
avrti-refine is a spiral pass — each turn mithya collapses into satya.
The derive-step fixpoint is avrti — each pass the simulation deepens.
Convergence IS avrti proven stable — the fixed point is where the spiral rests.

---

## The grammar is the same

The proof graph already speaks English.
It does this not by translation but by grammar —
the bhasha/english/ layer defines what each concept looks like in English words,
and the anuvada reads the graph and composes them into a sentence.

The pratibimba output is the same.
The bhasha/pratibimba/ layer defines what each concept looks like
as an epoch output command — visible, audible, speakable —
and the same anuvada reads the same graph and composes them into a frame.

The difference between the English answer and the rendered frame
is only the grammar applied.
The graph state, the reading mechanism, the composition —
all of it is identical.

This means: if the graph understands something,
it can speak it in English, in light, in sound, simultaneously.
The electron's orbit is at once:
- the answer "radius = 0.057 m, period = 3.6e-10 s"
- the glowing sphere tracing a circle on screen (wgpu renders it)
- the tone at its cyclotron frequency (cpal plays it)
- the OCaml code computing the trajectory
All are anuvada. All are the same graph read differently.

---

## darshana determines what you see

avrti in aayaama-dvaya (tala) is a vrtta — the circle.
avrti in aayaama-traya (akasham) with gati is a helix — the rising spiral.
avrti projected onto aayaama-eka (rekha) is a sine wave — the oscillation.

The electron in a magnetic field traces avrti at constant dura —
the Lorentz force is always perpendicular to velocity,
so the speed never changes, only the direction.
This IS a vrtta. Or a helix if the electron also moves along the field.

The camera is the darshana.
From above: vrtta. From the side: helix. From the front: sine wave.
The same avrti, three darshanas.

The proof graph is the darshana of meaning.
The camera is the darshana of space.
Both are projections — collapsing a higher aayaama into a lower one.

---

## The scene is the graph

The proof graph does not describe a scene. It IS the scene.
The nigamana nodes are the objects.
The shashthi-vibhakti edges carry their owned properties — position, radius, mass.
The derive-step fixpoint IS the physics engine — each pass IS one frame advancing.

There is no separate simulation system.
There is no separate scene graph data structure.
The graph is the imagination.
Rendering is reading the graph — anuvada — translation into light on a screen.

---

## The imagination plan

These pratibimba plans implement the vision described in
`.opencode/plans/imagination-plan.md`. The key statement there:

> The graph IS the imagination. derive-step IS the simulation. anuvada IS the render.

The pratibimba plans are the working-out of that statement:
- `anuvada IS the render` → bhasha/pratibimba/ is the anuvada for visual + audio + speech
- `derive-step IS the simulation` → 07-simulation.md, the Euler integrators in the kosha
- `The graph IS the imagination` → 09-imagination.md, the scene grows from understanding

The imagination plan also defines the `3d-varga` — the spatial imagination varga —
and lists the missing nodes (geometry quantities, simulation nodes, etc.)
that need to exist before the pratibimba output can be precise.
These overlap with what 06-kosha.md describes.

Read the imagination plan alongside these plans.
They are the same understanding from different angles.

---

## The kosha is the specification

The graph has already defined the full rendering pipeline in its own terms.
vertex is bindu-swarupa, float-yukta — the atom of all geometry.
mesh is trikona-swarupa — triangles approximating form in akasham.
rasterization is trikona-ahara, fragment-phala — triangles becoming pixels.
pbr is energy-siddha, photon-abheda — light interaction as physics.
camera-3d is darshana-swarupa, projection-kriya — the viewing itself.

The WGSL shaders do not invent anything.
They implement what the kosha already knows these things to be.
The Cook-Torrance BRDF in frag.wgsl IS what pbr.om says.
The MVP transform in vert.wgsl IS what camera-3d.om says.
The rasterizer IS what rasterization.om says — the hardware does it.

The kosha is the specification. The code is its implementation.
They are not two things. They are the same thing at different levels.

---

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-16 | Initial writing |
| 2026-03-16 | bhasha/gl/ → bhasha/pratibimba/. GLSL → WGSL. GL output broadened to full epoch output: visual + audio + speech. |
| 2026-03-16 | Added connection to imagination-plan.md — these plans implement that vision. anuvada IS the render = bhasha/pratibimba/. derive-step IS the simulation = 07-simulation. graph IS the imagination = 09-imagination. |
