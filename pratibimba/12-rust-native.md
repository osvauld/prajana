# 12 — The Rust-Native Surface

**One Rust binary. wgpu for the GPU. cpal for sound. OCaml linked directly.**
**The C/OpenGL prototype proved the concepts. This is where they live.**

---

## Why Rust-native

The C/OpenGL path in `vyakarana/render/` was built first because it was the
shortest path to proving the GPU pipeline works. It does work.
But it lives outside the osvauld workspace, uses SDL2 and C for what Rust
already does better, and requires a separate binary.

The osvauld workspace already has everything needed for a complete native surface:
- wgpu for GPU rendering (pure Rust, Vulkan on Linux)
- Slint for UI (text input, overlays, node panels)
- synth.rs for audio (already written, music_ir → PCM → stream)
- Loro CRDT for shared state (already in lua_runtime)
- Lua runtime for scripting between OCaml and renderers
- vyakarana_bridge for the OCaml connection (socket today, direct FFI tomorrow)

Everything in one place. One binary. No SDL2. No C in the rendering path.

---

## wgpu is the GPU layer

wgpu is the Rust implementation of the WebGPU standard.
It sits directly on top of Vulkan on Linux — the Intel Iris Xe on this machine
supports Vulkan, so wgpu has full GPU access.

wgpu is not a wrapper around OpenGL. It is a modern GPU API:
- Explicit pipeline state (render pipelines, bind groups)
- Type-safe buffers (vertex, index, uniform, storage)
- WGSL shaders — WebGPU Shading Language, Rust-syntax
- Compute shaders for GPU-side physics
- No global state, no implicit context

The kosha concepts map to wgpu identically to how they mapped to OpenGL.
The concepts have not changed. The implementation language has.

```
vertex (bindu-swarupa, float-yukta)    → wgpu::VertexBufferLayout
mesh   (trikona-swarupa)               → wgpu::Buffer (vertex + index)
shader (vertex-ahara, fragment-phala)  → WGSL module (vert.wgsl + frag.wgsl)
pbr    (energy-siddha, light-ahara)    → fs_main in frag.wgsl — same BRDF
rasterization (trikona-ahara)          → wgpu::RenderPipeline
camera-3d (projection-kriya)           → uniform buffer: model, view, proj
avrti (the frame boundary)             → encoder.begin_render_pass / submit
```

---

## WGSL is GLSL in Rust syntax

The vert.glsl and frag.glsl we wrote are the specification.
The WGSL versions are the same mathematics, different syntax.

The vertex shader implements camera-3d — darshana-swarupa, projection-kriya.
The fragment shader implements pbr — energy-siddha, photon-abheda, light-ahara.
These have not changed. Only the notation has.

The BRDF in WGSL is still Cook-Torrance: D × F × G / (4 · NdotL · NdotV).
The PBR is still energy-siddha — energy is conserved.
The camera is still darshana — projection from aayaama-traya to aayaama-dvaya.

The kosha IS the specification. The shaders implement it.
Whether those shaders are written in GLSL or WGSL is irrelevant to the graph.

---

## cpal replaces SDL2 audio

`synth.rs` in renderer_raylib already implements the audio synthesis:
- music_ir → note queue → per-frame PCM generation
- Additive oscillators: sine, sawtooth, triangle, square
- Pitch table: scientific notation (a4 = 440 Hz) → Hz
- gamaka / andolan modulation via resonance_ir energy field
- 44100 Hz, f32 mono, 512 frames per buffer

This is already the right design — spanda → taranga → PCM.
It just needs cpal as the output instead of Raylib's AudioStream.
cpal is cross-platform, pure Rust, no C dependency.

The audio path:
```
proof graph → music_ir (swara, thaalam, gamaka)
    ↓ synth.rs (already written)
PCM f32 samples (512 frames at a time)
    ↓ cpal output stream
speakers
```

---

## Slint is the UI layer

Slint (FemtoVG backend) renders the UI that surrounds the 3D scene:
- Text input field at the bottom (the question / prashna)
- Node info panel on the right (picked node: name, satya, edges)
- Answer text overlay
- Mode switcher (graph view / simulation / both)

Slint and wgpu can coexist in the same window.
Slint renders to its own framebuffer, wgpu renders the 3D scene,
both composite into the final frame.

The Slint UI is driven by Lua — the existing page_runtime.rs pattern.
A Lua script defines the UI layout and how it responds to events.
This is already how all sthalam apps work.

---

## OCaml direct FFI

The current vyakarana_bridge spawns the OCaml binary as a subprocess
and communicates via Unix socket and JSON.
This works and is already used in the osvauld workspace.

For the direct path — same binary, no subprocess:
1. `vyakarana_lib` compiled as a static library (`vyakarana_lib.a`)
2. A thin C wrapper (`vyakarana_c_api.c`) exposes a clean C interface:
   `vyakarana_init`, `vyakarana_query`, `vyakarana_graph`, `vyakarana_close`
3. Rust `build.rs` links `vyakarana_lib.a + libasmrun.a + libunix.a + libstr.a`
4. `extern "C"` declarations in Rust call through directly

The current socket bridge remains for the existing tests, explore.py,
and any external clients. The direct FFI is a new path alongside it —
same OCaml code, different entry point.

No subprocess. No serialisation. Shared memory.
The proof graph lives in the same process as the renderer.

---

## Loro CRDT as shared state

The Loro CRDT (already in lua_runtime) is the shared state store
for the scene and for the living documents (plans, whitepaper).

The proof graph writes to the CRDT via the Rust layer:
- Each simulation step updates node positions in the CRDT
- Each answer updates the session state in the CRDT
- The CRDT holds the current scene state

The renderer reads from the CRDT each frame:
- Node positions → DrawSphere commands
- Edge list → DrawLine commands
- Camera state → SetCamera command

Multiple clients can share the same CRDT state via the network
(iroh QUIC transport — already in osvauld, not needed now).
The living documents in `.opencode/plans/pratibimba/` can be
stored as Loro documents — the history of every understanding update
preserved as a CRDT operation sequence.

---

## The epoch output

One turn of avrti in the Rust-native binary produces:

```rust
struct EpochOutput {
    visual:  Vec<RenderCmd>,   // → wgpu draw calls
    audio:   Vec<AudioCmd>,    // → cpal PCM via synth.rs
    speech:  Vec<SpeechCmd>,   // → phoneme synthesis → cpal
}
```

wgpu submits the visual commands to the GPU.
cpal submits the audio commands to the speakers.
Slint overlays the UI.
All from one frame. All from one graph state.

---

## The crate in osvauld

A new crate: `osvauld/renderer_wgpu/`

```
renderer_wgpu/
  Cargo.toml     wgpu, winit, cpal, slint (optional)
  src/
    lib.rs       public API: WgpuRenderer, EpochOutput
    pipeline.rs  wgpu render pipeline setup
    buffers.rs   vertex, index, uniform buffer management
    shaders/
      vert.wgsl  vertex shader (camera-3d — projection-kriya)
      frag.wgsl  fragment shader (pbr — energy-siddha)
    synth.rs     (moved from renderer_raylib, unchanged)
    scene.rs     reads EpochOutput → wgpu draw calls + cpal audio
    input.rs     winit events → OCaml events (text, pick, keyboard)
```

The C/OpenGL prototype in `agent_x/vyakarana/render/` served its purpose:
- Proved the GL pipeline works
- Proved force-directed layout works
- Proved PBR shaders work
- Proved ray-picking works

Those proofs stand. The Rust-native path inherits them.

---

## The Slint renderer alongside

`renderer_slint` (already built) handles the UI apps —
chat, documents, structured data, the whitepaper as a live app.

`renderer_wgpu` handles the 3D scene — physics, simulation, graph visualisation.

They can run in the same window:
- wgpu renders the 3D scene to a texture
- Slint displays that texture + renders UI on top
- Or: separate windows, one for each renderer

The Lua runtime connects them — the same Lua script can
call into both renderers, driven by the same proof graph state.

---

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-16 | Initial writing — wgpu as Rust-native GPU path in osvauld |
| 2026-03-16 | Understood: the C/OpenGL prototype proved the concepts; renderer_wgpu is where they live permanently |
