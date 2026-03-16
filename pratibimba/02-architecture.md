# 02 — Architecture

**What owns what. Where understanding lives. Where execution lives.**

---

## The division

There is a natural boundary between two kinds of knowing.

The proof graph knows what things ARE.
It knows what an electron is, what a magnetic field is, what velocity is.
It knows how they relate — ownership, causality, transformation.
It knows how to reason forward: from mass and velocity to momentum,
from charge and field to force, from force and mass to acceleration.
This knowing lives entirely in OCaml, in the graph, in the kosha.

The renderer knows how to show things.
It knows how to upload vertices to the GPU.
It knows how to compile shaders, bind buffers, draw triangles.
It knows how to turn a list of draw commands into light on a screen.
This knowing lives in Rust — in wgpu, in osvauld, in renderer_wgpu.
A C/OpenGL prototype was built first to prove the pipeline.
It proved it. The permanent home is Rust.

The boundary between them is the EpochOutput —
a typed description of what to render, hear, and speak,
without any knowledge of why.
The graph produces it. The renderer executes it. One hop.

---

## The graph owns the scene

The scene is not a separate data structure maintained alongside the graph.
The graph IS the scene.

Each object in the scene is a nigamana node.
Its properties — position, radius, mass, color, velocity —
are carried by shashthi-vibhakti edges (ownership).
The physical laws are mantras that fire on those owned properties.
The simulation is the derive-step fixpoint — avrti until stable.

When the graph advances one simulation step,
the scene has changed.
The renderer reads the new state and draws what it finds.
There is no synchronisation problem. There is no separate scene to update.
The graph state IS the scene state. They are the same thing.

---

## The renderer owns the GPU

The renderer is not intelligent. It does not make decisions.
It receives a list of commands and executes them against the GPU.

It owns:
- the window and the wgpu device (via winit)
- the GPU buffers (vertex, index, uniform — wgpu::Buffer)
- the shaders (WGSL modules — vert.wgsl + frag.wgsl)
- the audio stream (cpal output, fed by synth.rs)
- the frame rhythm (the beat of avrti — when each frame begins and ends)
- the orbital camera (user drags → view changes)
- ray-picking (mouse position → which node is under the cursor)
- the Slint UI layer (text input, overlays, node info panels)

It does not own:
- what to draw
- what color or material any object has
- how many objects exist
- where they are
- how they move

Those belong to the graph. Always.

---

## The session is the memory

The session accumulates the samskaara of conversation.
Each question is a turn. Each turn leaves an imprint.
The next turn inherits the bindings of all previous turns.

This is session.om:
"accumulation-siddha parampara-siddha" —
the session IS a parampara, a deepening chain of turns.
"electron in B-field" in turn 1 means
"increase B" in turn 2 already knows what the electron and B-field are.

The session lives in OCaml. It is not a database. It is not a file.
It is the living context of an ongoing conversation with the graph.

---

## The boundary is the EpochOutput

The EpochOutput is the only thing that crosses the boundary.
On one side: the graph, the session, the physics, the understanding.
On the other side: the GPU, the speakers, the voice.

The EpochOutput is the anuvada — the expression of understanding.
It says: here is what I understood, expressed as things to see, hear, and speak.
It does not explain why. It does not carry reasoning.
It is the expression of understanding as pratibimba — reflection into the world.

One EpochOutput per epoch. One epoch per turn of avrti.
The graph produces it. The renderer executes it.
That is all that passes between them.

---

## No socket between graph and renderer

The existing socket is for the tests and for external clients.
It carries JSON over a Unix domain socket.
It will continue to exist for that purpose.

The interface is different.
The graph and the renderer live in the same process.
There is no serialisation. No network. No protocol.
This is what "direct" means.

The direct path: OCaml compiles to a static library (vyakarana_lib.a).
A thin C wrapper exposes the proof graph as a C API.
Rust links the .a via build.rs and calls it via extern "C".
One process. One binary. Shared memory.

The session that lives in the socket server
and the session that lives in the interface
are the same OCaml module called from different contexts.
One binary. Two entry points into the same proof space.

---

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-16 | Initial writing |
| 2026-03-16 | Renderer moved from C to Rust (wgpu in osvauld). EpochOutput replaces RenderCmd as the boundary type — it carries visual + audio + speech together. Direct OCaml FFI path clarified: vyakarana_lib.a linked into Rust via build.rs. |
