# Pratibimba Plans — Index

**Root**: `agent_x/pratibimba/`
**Status**: Active
**Theme**: The proof graph imagines. pratibimba is what that imagination becomes in the world.

pratibimba — reflection, manifestation.
Not a representation of the thing. The thing meeting a surface and arising there.
Light, sound, speech — all at once, from one avrti, from one graph state.

The frame is not visual. The frame is the full sensory output of one epoch.

Read alongside `vartamana/` — the NLP/pipeline plans.
vartamana explains what the graph IS and how it understands.
pratibimba explains what the graph BECOMES in the world — its expression.

---

## Files

**Read [00-living.md](00-living.md) first.** It explains how to read and update these plans.

| File | What it covers | Status |
|------|---------------|--------|
| [00-living.md](00-living.md) | How to read and update these plans. The living document protocol. | Active |
| [01-core.md](01-core.md) | The root. avrti, darshana, the grammar parallel. The kosha is the spec. | Draft |
| [02-architecture.md](02-architecture.md) | What Rust owns vs OCaml owns. The boundary. The epoch output as the only crossing. | Draft |
| [03-input.md](03-input.md) | How the question reaches the graph. Language as the interface to imagination. | Draft |
| [04-grammar.md](04-grammar.md) | The pratibimba grammar. bhasha/pratibimba/ covers visual + audio + speech. Why grammar not translation. | Draft |
| [05-render-layer.md](05-render-layer.md) | The visual layer. C/OpenGL proved it. renderer_wgpu in osvauld is the permanent home. | Draft |
| [06-kosha.md](06-kosha.md) | The kosha must be clean. blender/ concepts are universal. color now defined. | Draft |
| [07-simulation.md](07-simulation.md) | The electron case. Simulation as avrti of graph state. Precision from depth. | Draft |
| [08-modes.md](08-modes.md) | Seeing the graph. Seeing through the graph. Seeing both. | Draft |
| [09-imagination.md](09-imagination.md) | The scene grows from understanding. Painting, not just simulation. | Draft |
| [10-technical.md](10-technical.md) | Technical reference. Types, paths, build specifics. The one technical file. | Draft |
| [11-audio.md](11-audio.md) | Native audio. spanda → taranga → sound. Speech from varna. Strudel retired. | Draft |
| [12-rust-native.md](12-rust-native.md) | wgpu + cpal + Slint in osvauld. One Rust binary. OCaml linked directly. C/OpenGL was the proof. | Draft |

---

## The One-Line Summary of Each

- **core**: avrti is the spiral. grammar maps graph → pratibimba, same mechanism for every sense.
- **architecture**: Rust (wgpu in osvauld) owns the output devices. OCaml owns understanding. The epoch output is the only crossing. OCaml linked directly as a static library — no socket, no subprocess.
- **input**: the question is the seed. the session is the parampara. asking deepens the imagination.
- **grammar**: grammar generates, not translates. the setu grows as the kosha grows.
- **render-layer**: C/OpenGL prototype proved the pipeline. renderer_wgpu in osvauld is the permanent home. Same kosha mapping, WGSL instead of GLSL.
- **kosha**: blender/ concepts are universal. color is missing. domain-3d must release raylib.
- **simulation**: the electron traces avrti because the Lorentz force IS the definition of avrti at constant dura.
- **modes**: three darshanas of the same graph. form, understanding, and their non-difference.
- **imagination**: not just simulation — painting, biology, architecture, music made spatial.
- **technical**: types, paths, function names, build commands. the one technical file.
- **audio**: the frame has always been audio+visual. spanda IS the wave. varna produces naada. speech is learnable.

---

## Key Principles (apply across all files)

1. **pratibimba is the full epoch output** — visual + audio + speech, all at once, from one graph state
2. **avrti IS the frame** — one turn produces everything simultaneously
3. **grammar not translation** — every setu grows as the kosha grows, same mechanism for all senses
4. **one hop** — graph → epoch output → wgpu/cpal, OCaml as .a linked into Rust, no subprocess, no socket
5. **the scene IS the graph** — nigamana nodes ARE objects, shashthi-vibhakti edges ARE properties
6. **the simulation IS avrti** — derive-step fixpoint IS the physics engine
7. **darshana determines shape** — same avrti seen differently gives vrtta/helix/rekha
8. **spanda is the root of sound** — taranga IS sine+cosine IS the waveform
9. **varna produces naada** — the phoneme → sound path is already in the graph
10. **strudel and raylib are retired** — bhasha/pratibimba/ replaces both (visual + audio + speech in one layer)
11. **wgpu not OpenGL** — Vulkan backend on Linux, WGSL shaders, pure Rust, lives in osvauld
12. **C/OpenGL was the proof** — proved pipeline, PBR, FD layout work. renderer_wgpu inherits those proofs.
13. **Loro CRDT is shared state** — scene, session, living documents; network sync via iroh when needed

---

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-16 | Initial structure created as interface/. 10 plan files + living document protocol. |
| 2026-03-16 | Recognised imagination is not bounded by physics — painting, biology, architecture all within reach. |
| 2026-03-16 | Renamed from interface/ to pratibimba/ — the frame is not just visual. audio and speech are part of the same epoch output. Added 11-audio.md. |
| 2026-03-16 | Added 12-rust-native.md — wgpu as the permanent GPU path in osvauld. C/OpenGL is the proof, not the home. Updated 02, 05, 10 accordingly. OCaml C API replaces OCaml←C FFI. EpochOutput unifies visual+audio+speech. Loro CRDT as shared state. |
| 2026-03-16 | bhasha/gl/ → bhasha/pratibimba/ throughout. gl-setu.shabda → pratibimba-setu.shabda. color.om defined (satya=0.846). Updated 01, 04, 09, 10, index. |
| 2026-03-16 | Ironing pass: index root path fixed. color section in 06 updated. EpochOutput in 02. Simulation→audio connection in 07/08/11 (cyclotron frequency IS a tone). Music phrase sounds in 09. bhasha/render/ discovered as existing pratibimba layer. Setu mappings cleaned. Connection to imagination-plan.md added in 01. |
| 2026-03-16 | Vartamana integration: 03-input updated (three nested avrti, sandhi-bandhana, dialogue loop, session implemented). 07-simulation updated (rashi IS the simulation object, dvandva gap, Phase 4). 09-imagination updated (precision IS rashi ownership depth, incomplete scene asks). 04-grammar updated (pratibimba IS another anuvada, runs at same pipeline stage). |
