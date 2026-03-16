# 10 — Technical Reference

**Implementation details. Types, function names, file paths, build specifics.**

---

## System

```
OS:       Arch Linux (EndeavourOS), x86_64
GPU:      Intel Iris Xe, Mesa 25.2.6, OpenGL 4.6 / Vulkan available
Display:  X11 (:0) + Wayland (wayland-1)
SDL2:     sdl2-compat 2.32.58 — installed (used by C prototype only)
libGL:    libGL.so — installed (used by C prototype only)
Vulkan:   available — wgpu uses Vulkan backend on this machine
OCaml:    5.2.0 native compiler, libasmrun.a available
          proof graph live at /tmp/vy.sock
Rust:     osvauld workspace — wgpu 28, slint 1.14, loro 1.5, mlua 0.10
```

---

## Files

### Proof of concept: vyakarana/render/ (standalone C — proven, not the target)

```
main.c       SDL2 window, OpenGL 3.3, PBR sphere, FD layout, ray-picking
gl.h         GL function loader — no GLAD/GLEW
vert.glsl    vertex shader: model × view × proj — the specification
frag.glsl    fragment shader: Cook-Torrance PBR — the specification
Makefile     gcc, pkg-config sdl2, -lGL -lm
```

Build: `cd vyakarana/render && make && ./render`
Status: confirmed running. Proved: pipeline works, PBR correct, FD converges.
Role: specification and proof. Not the permanent renderer.

### brahman/bhasha/pratibimba/ (grammar — backend-agnostic)

bhasha/render/ already exists and IS this layer. Needs renaming + updating.

Already exists (in bhasha/render/):
```
pratibimba.om           naada-swarupa, spanda-phala — NEEDS: remove raylib-yukta
music-ir.om             audio IR — thaalam, swara, voice, event
resonance-ir.om         graph animation — satya→energy, relation→flow
music-ir-setu.shabda    relation types → audio params (timbre, octave, gain...)
resonance-ir-setu.shabda satya/flow → animation energy
```

To add (genuinely new):
```
pratibimba-setu.shabda  kosha concepts → EpochOutput visual commands
3d-to-pratibimba.om     the visual anuvada (wgpu path)
vak-to-pratibimba.om    the speech anuvada (phoneme synthesis)
```

EpochOutput commands are backend-agnostic.
wgpu executes visual. cpal + synth.rs executes audio (music-ir → PCM).
Phoneme synthesis executes speech (vak-to-pratibimba → formants → PCM).

### To build: OCaml C API (direct FFI into Rust)

```
vyakarana/lib/vyakarana_c_api.c     C wrapper exposing proof graph to Rust
  vyakarana_init(dirs, n) → handle
  vyakarana_query(h, session, q) → JSON string
  vyakarana_graph(h) → JSON string
  vyakarana_close(h)

vyakarana/lib/dune update:
  (c_names vyakarana_c_api)
  produces vyakarana_lib.a linkable by Rust
```

### To build: osvauld/renderer_wgpu/ (the permanent renderer)

```
renderer_wgpu/
  Cargo.toml        wgpu, winit, cpal, slint (optional)
  src/
    lib.rs           WgpuRenderer, EpochOutput
    pipeline.rs      wgpu render pipeline (replaces gl.h + main.c setup)
    buffers.rs       wgpu::Buffer management (replaces VAO/VBO)
    scene.rs         EpochOutput → wgpu draw calls + cpal audio
    input.rs         winit events → OCaml (text, pick, keyboard)
    shaders/
      vert.wgsl      vertex shader (same as vert.glsl, WGSL syntax)
      frag.wgsl      fragment shader (same PBR, WGSL syntax)
    synth.rs         moved from renderer_raylib — unchanged

osvauld/vyakarana_bridge/build.rs update:
  links vyakarana_lib.a + libasmrun.a + libunix.a + libstr.a
  extern "C" { fn vyakarana_init(...); fn vyakarana_query(...); }
```

---

## RenderCmd type

```ocaml
type vec3 = { x: float; y: float; z: float }
type vec4 = { r: float; g: float; b: float; a: float }

type render_cmd =
  | BeginFrame
  | EndFrame
  | SetCamera   of { pos: vec3; target: vec3; fov: float }
  | SetLight    of { pos: vec3; color: vec3; intensity: float }
  | DrawSphere  of { center: vec3; radius: float;
                     albedo: vec3; roughness: float; metallic: float }
  | DrawLine    of { a: vec3; b: vec3; color: vec4 }
  | DrawTrail   of { points: vec3 array; color: vec4; fade: bool }
  | DrawArrow   of { base: vec3; dir: vec3; color: vec4 }
  | DrawLabel   of { pos: vec3; text: string; color: vec4; size: float }
  | ClearColor  of { r: float; g: float; b: float }
```

---

## EpochOutput type (what the graph produces each frame)

```ocaml
(* OCaml side — produced by eval_epoch *)
type epoch_output = {
  visual  : render_cmd list;
  audio   : audio_cmd list;
  speech  : speech_cmd list;
}
```

```rust
// Rust side — received from OCaml, executed by wgpu + cpal
struct EpochOutput {
    visual:  Vec<RenderCmd>,
    audio:   Vec<AudioCmd>,
    speech:  Vec<SpeechCmd>,
}
```

## Event type (winit → OCaml)

```rust
// Rust side — winit events translated for OCaml
enum InputEvent {
    Quit,
    KeyPress(String),
    TextCommit(String),      // Enter pressed — full question
    MousePick(Option<String>), // ray hit → node name or None
    Resize(u32, u32),
}
```

## OCaml C API (Rust calls OCaml directly)

```c
/* vyakarana_c_api.c — C interface over OCaml */
VyakaranaHandle vyakarana_init(const char** dirs, int n);
const char*     vyakarana_query(VyakaranaHandle h,
                                const char* session_id,
                                const char* question);
const char*     vyakarana_graph(VyakaranaHandle h);
void            vyakarana_free_result(const char* s);
void            vyakarana_close(VyakaranaHandle h);
```

```rust
// Rust build.rs: links OCaml .a files
// extern "C" wraps the C API
extern "C" {
    fn vyakarana_init(dirs: *const *const c_char, n: c_int) -> *mut c_void;
    fn vyakarana_query(h: *mut c_void, sid: *const c_char,
                       q: *const c_char) -> *const c_char;
    fn vyakarana_graph(h: *mut c_void) -> *const c_char;
    fn vyakarana_free_result(s: *const c_char);
    fn vyakarana_close(h: *mut c_void);
}
```

---

## pratibimba-setu.shabda (draft mappings)

Visual mappings (3d-to-pratibimba — new):
```
avrti-begin:   Visual.BeginEpoch
avrti-end:     Visual.EndEpoch
camera-3d:     Visual.SetCamera { pos=$bindu, target=$target, fov=$fovy }
light:         Visual.SetLight  { pos=$bindu, color=$color, intensity=$energy }
gola:          Visual.DrawSphere { center=$bindu, radius=$dura,
                                   albedo=$albedo, roughness=$roughness, metallic=$metallic }
rekha:         Visual.DrawLine  { a=$bindu-a, b=$bindu-b, color=$color }
particle:      Visual.DrawSphere { center=$bindu, radius=$dura, color=$color }
trajectory:    Visual.DrawTrail { points=$bindu-krama, color=$color, fade=true }
force:         Visual.DrawArrow { base=$bindu, dir=$direction, color=$color }
label:         Visual.DrawLabel { pos=$bindu, text=$text, color=$color }
```

Audio mappings (music-ir-setu.shabda — already exists, extended):
```
# relation types → voice/timbre (existing pattern in music-ir-setu.shabda)
swarupa-timbre: piano
abheda-timbre:  piano
yukta-timbre:   strings
phala-timbre:   bells

# physics simulation frequencies (new — derived from owned quantities)
frequency:     Audio.PlayTone { freq=$sankhya, dur=$duration, amp=$amplitude }
thaalam:       Audio.SetTempo { bpm=$laya }
gamaka:        Audio.Modulate { lfo_freq=$andolan, depth=$intensity }
```

Speech mappings (vak-to-pratibimba — new):
```
vak:           Speech.Speak { phonemes=$varna-krama, pitch=$swara, rate=$laya }
answer-text:   Speech.Speak { text=$answer_text, rate=1.0 }
```

---

## Physics constants needed

```
elementary-charge:  1.6021766e-19 C   (already in kosha, needs sankhya edge)
electron-mass:      9.1093837e-31 kg  (already in kosha, needs sankhya edge)
```

---

## Lorentz simulation step (tantra sketch)

```
tantra lorentz-step
  takes graph dt

  -- F = q(v × B)
  v       = owned-value graph electron "velocity"
  B       = owned-value graph magnetic-field "direction-scaled"
  q       = owned-value graph electron "charge"
  F_mag   = scalar-mul q (vec-cross v B)

  -- a = F/m
  m       = owned-value graph electron "mass"
  a       = scalar-div F_mag m

  -- velocity-step: v(t+dt) = v(t) + a·dt
  v_next  = vec-add v (scalar-mul a dt)

  -- position-step: x(t+dt) = x(t) + v·dt
  x       = owned-value graph electron "bindu"
  x_next  = vec-add x (scalar-mul v dt)

  -- update graph
  graph'  = set-owned graph electron "velocity" v_next
  graph'' = set-owned graph' electron "bindu" x_next

  return graph''
done
```

---

## Keyboard shortcuts (winit-side, Rust)

```
Enter      commit input as question → OCaml via vyakarana_query
Escape     clear input buffer
Backspace  delete last character
r          reset simulation
Space      pause / resume
Tab        cycle modes (graph / sim / both)
Mouse drag orbit camera
Scroll     zoom
Left click ray-pick → node inspect → vyakarana_query "inspect <name>"
```

---

## Build order

```
Phase 1 — Grammar (brahman/bhasha/pratibimba/ — 6 files)
  domain-pratibimba.om, pratibimba-setu.om, pratibimba-setu.shabda
  3d-to-pratibimba.om, naada-to-pratibimba.om, vak-to-pratibimba.om
  backend-agnostic — maps concepts to EpochOutput commands

Phase 2 — Kosha cleanup
  color.om, fix domain-3d.om (remove raylib), promote blender/ concepts

Phase 3 — OCaml C API + Rust direct FFI
  vyakarana_c_api.c + dune update → vyakarana_lib.a
  osvauld/vyakarana_bridge/build.rs → links .a files
  replaces socket subprocess with direct function calls

Phase 4 — renderer_wgpu in osvauld
  wgpu pipeline + WGSL shaders (from C/OpenGL prototype spec)
  cpal audio (synth.rs from renderer_raylib)
  Slint UI overlay
  winit input → OCaml events

Phase 5 — Simulation
  lorentz-force.om, vec-cross.om, constants, lorentz-step.tantra
  electron orbit as first physical simulation

Phase 6 — Both modes simultaneously
  graph visualisation + physics simulation in same window
  Tab to switch, both active at once
  Loro CRDT holds shared scene state
```

---

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-16 | Initial writing — described C/OpenGL as the renderer |
| 2026-03-16 | Major update: renderer_wgpu in osvauld is the permanent path. C/OpenGL prototype is proof-of-concept only. OCaml C API replaces OCaml calling C stubs. EpochOutput replaces RenderCmd as the boundary type. Build order updated with Phase 3 = OCaml C API + Rust FFI, Phase 4 = renderer_wgpu. |
| 2026-03-16 | bhasha/gl/ → bhasha/pratibimba/. gl-setu.shabda → pratibimba-setu.shabda. 3d-to-gl → 3d-to-pratibimba. Added naada-to-pratibimba and vak-to-pratibimba for audio and speech. Draft setu mappings updated to include audio (swara, thaalam, gamaka) and speech (vak) alongside visual. |
