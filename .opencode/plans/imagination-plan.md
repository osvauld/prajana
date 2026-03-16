# Imagination Plan — Spatial Reasoning as Graph State

**Created**: 2026-03-14
**Updated**: 2026-03-16
**Status**: Active — companion to nyaya-plan.md
**Theme**: The proof graph imagines. 3D is not rendering — it is thinking.

---

## The Core Insight

The proof graph does not just compute answers. It **imagines** the situation.

When a physics question arrives, the graph does not just fire mantras and return a number.
It constructs a scene — objects with positions, shapes, properties, moving through space
and time. That scene IS the understanding. The answer is a consequence of the imagination.

This is how all vargas work:
- `sangeetham-varga` imagines sound — thaalam, naada, gati through time
- `biology-varga` imagines a cell — metabolism, replication, folding in space
- `geometry-varga` imagines shape — gola, vrtta, rekha in akasham
- `3d-varga` imagines the scene — all of the above, simultaneously, rendered

**The graph IS the imagination. derive-step IS the simulation. anuvada IS the render.**

---

## What the Graph Already Knows

### The spatial frame
- `akasham` — the container of all geometry (`swarupa world-space, vector-space`)
- `sthira-apeksha` — fixed/inertial/world frame (`pratipaksha chala-apeksha`)
- `chala-apeksha` — moving/body/local frame — attached to each object
- `aayaama-eka` → `rekha` (1D number line)
- `aayaama-dvaya` → `tala` (2D plane)
- `aayaama-traya` (missing) → `akasham` (3D space — three orthogonal rekha through bindu)

### The time frame
- `kaala` — `brahma-swarupa`, `sthita kshetra` — time IS situated in space
- `kaala` — `laya-varga-swarupa`, `thaalam-janaka` — time IS rhythm
- `kaala` — `vartamana/bhuta/bhavishya-kaala-janaka` — time generates tense
- `avastha` — state at a moment: `janya purva-avastha`, `phala uttara-avastha`
- `trajectory` — `sthita akasham + yukta kaala + siddha bindu-krama` — path through spacetime
- `keyframe` — `sthita timeline`, `abheda samskaara` — a moment in time IS an impression

### The object
- `gola` — `sama-dura-sthita`, `dura-yukta` — sphere defined by radius from center
- `vrtta-stambha` — `vrtta-janya`, `rekha-sthita` — cylinder = circle swept along line
- Every object carries properties via `shashthi-vibhakti` (ownership):
  - `[mass, shashthi-vibhakti, gola-A]` — mass belongs to the sphere
  - `[radius, shashthi-vibhakti, gola-A]` — radius belongs to the sphere
  - `[velocity, shashthi-vibhakti, gola-A]` — velocity belongs to the sphere

### The GPU pipeline (already fully defined in the kosha)

The kosha has defined the complete rasterization pipeline from first principles:

```
vertex      — bindu-swarupa, float-yukta, position-yukta normal-yukta
              the atom of a mesh: position + normal + uv as floats in world-space

mesh        — trikona-swarupa, vertex-yukta, face-yukta, edge-yukta
              collection of triangles — the bridge between sangati geometry and pixels

rasterization — trikona-ahara, fragment-phala, bindu-janya prasarana-abheda
              converts triangles in akasham to fragments on screen-tala
              finds which pixels fall inside each projected triangle
              interpolates vertex attributes (the "prasarana" — spreading)

fragment    — tala-sthita, rasterization-janya
              screen-space bindu born from rasterization
              the smallest unit of rendered output

shader      — vertex-ahara, fragment-phala, gpu-kriya
              the program that runs on the GPU
              vertex stage: transforms position to clip-space
              fragment stage: computes color from material + light

material    — shader-swarupa, pbr-sthita, roughness-yukta metallic-yukta albedo-yukta
              how a surface responds to light

pbr         — light-ahara, color-phala, energy-siddha, photon-abheda
              physically-based rendering: energy is conserved
              IS the Cook-Torrance BRDF written in graph terms

light       — photon-abheda, energy-sthita, position-yukta direction-yukta
              point / directional / spot — the energy source

camera-3d   — darshana-swarupa, projection-kriya, viewport-phala
              collapses 3D world-space into a 2D frame
              IS the view × projection matrix

viewport    — camera-3d-janya, trikona-yukta, rasterization-yukta
              the 2D screen rectangle that receives the projected scene
```

The kosha IS the specification. The GLSL shaders and C VBO code IS the implementation
of that specification. No translation needed — they are the same thing at different levels.

### The scene graph IS the proof graph

```
scene-graph — proof-graph-abheda
```

This is not a metaphor. The `nigamana` nodes in the proof graph ARE the 3D objects.
The `shashthi-vibhakti` edges carry position/rotation/scale ownership.
The render loop reads the proof graph directly and draws what it finds.

There is no separate scene graph data structure to build or maintain.
The proof graph is the scene. Walking it IS reading the scene.

### The simulation
- `velocity kramanusara displacement` — velocity IS rate of change of position
- `acceleration kramanusara velocity` — acceleration IS rate of change of velocity
- `angular-velocity kramanusara kona` — angular velocity IS rate of change of angle
- `position-step: sthita displacement+velocity → phala displacement` — Euler step for position
- `velocity-step: sthita velocity+acceleration → phala velocity` — Euler step for velocity
- `derive-step` fixpoint = the simulation loop — each pass IS one conceptual frame
- `avrti` = the loop — `kaala-darshana` = "seeing-time / the vision that reveals the spiral"

### The render
- `3d-to-native` — new direct anuvada: reads proof graph → emits `VRenderCmd` values → GPU
- `physics-to-ocaml` — `yukta velocity-step, position-step, force-apply`, `phala displacement`
- `anuvada` — the full translation family:
  - `physics-to-english` → textual answer
  - `3d-to-native` → native OpenGL: VBO upload + GLSL draw calls (direct, no intermediary)
  - `physics-to-ocaml` → executable simulation
  - `math-to-ocaml` → computed result
  - `ornament-to-strudel` → musical render

Note: `3d-to-lua` (the Lua/Raylib path) is retired. It was an indirect route through
a subprocess — graph → shabda templates → Lua strings → Raylib. Three lossy hops.
The new path is: proof graph → `VRenderCmd` values → C stubs → GPU. One hop.

### The events
- `collision` — `janya samvega+tvarana` — has input structure, no phala yet
- `total-momentum` — `abheda samskaara` — conservation IS a persistent impression
- `kshaya` — `satya=0.943` — dissolution, destruction, the moment of breaking
- `refraction` — `phala kona` — angle IS the output of deflection
- `vec-dot` — `phala scalar, pratipaksha vec-cross` — gives cosine of angle between vectors

---

## The Architecture

### The native engine stack

```
SDL2      — window creation, OpenGL context, keyboard/mouse input
            already installed (sdl2-compat 2.32.58), libSDL2.so present
libGL.so  — OpenGL 3.3 core profile, direct rendering confirmed
libX11.so — X11 display (:0), Wayland (wayland-1) also present
            SDL2 handles both transparently
```

Three files form the engine:

```
vyakarana/lib/render_stubs.c    — C: SDL2 + OpenGL 3.3
                                   window, context, VAO/VBO, GLSL compile+link
                                   draw calls, force-directed loop, ray-picking
                                   implements what the kosha defines

vyakarana/lib/render.ml         — OCaml: C FFI wrapper
                                   VRenderCmd type
                                   exposes: begin_frame, end_frame, draw_sphere,
                                   draw_line, set_camera, pick_ray → nigamana

vyakarana/lib/shaders/          — GLSL: the GPU programs
  vert.glsl                        vertex shader: model×view×proj transform
  frag.glsl                        fragment shader: PBR — implements pbr.om
                                   light-ahara × (roughness,metallic,albedo) → color-phala
```

### VRenderCmd — the bridge type

```ocaml
type render_cmd =
  | BeginFrame
  | EndFrame
  | SetCamera of { pos: float*float*float;
                   target: float*float*float;
                   fov: float }
  | DrawSphere of { center: float*float*float;
                    radius: float;
                    color: float*float*float*float }
  | DrawLine   of { a: float*float*float;
                    b: float*float*float;
                    color: float*float*float*float }
  | DrawMesh   of { vbo: int; count: int; material: material_ref }
  | PickRay    of { x: float; y: float }   (* mouse → nigamana option *)
```

These are `VRenderCmd` values in the yantra evaluator. Tantra expressions produce them.
The C layer reads them and submits to OpenGL. The proof graph never touches pixels.

### One graph, multiple readers

```
QUESTION arrives (or graph is already loaded)
     ↓
build-question-graph
     ↓
avrti-refine → scene construction
  objects identified (shashthi-vibhakti)
  properties owned
  shapes resolved (gola, vrtta-stambha)
  avastha established (purva-avastha)
     ↓
derive-step fixpoint = SIMULATION
  each pass: mantras fire on owned properties
  velocity-step: v(t+dt) = v(t) + a·dt
  position-step: x(t+dt) = x(t) + v·dt
  volume-mantra: volume = f(shape, dura)
  density-mantra: density = mass/volume
  → uttara-avastha established
     ↓
nyaya-step fixpoint = REASONING
  collision detected: |bindu-A - bindu-B| ≤ r-A + r-B
  kshaya fires: force > threshold → destruction
  conservation holds: total-momentum unchanged
     ↓
anuvada = RENDER (multiple simultaneously)
  match-mantra     → answer text
  3d-to-native     → VRenderCmd list → SDL2 window → GPU
  physics-to-ocaml → executable OCaml
  ornament-to-strudel → Strudel pattern
```

### The GPU pipeline — kosha to GLSL

Every kosha concept maps directly to a GPU construct. No translation layer:

```
vertex (bindu, float-yukta, normal-yukta)
  → VBO layout: [x,y,z, nx,ny,nz, u,v] × N
  → glBufferData, glVertexAttribPointer

mesh (trikona-swarupa, vertex-yukta, face-yukta)
  → VAO: vertex array + index buffer (EBO)
  → gola generates sphere mesh procedurally (latitude/longitude tesselation)
  → rekha generates line segment (2 vertices)

shader (vertex-ahara, fragment-phala, gpu-kriya)
  → vert.glsl: gl_Position = proj × view × model × vec4(pos, 1.0)
               also passes: normal, uv to fragment stage
  → frag.glsl: implements pbr.om
               albedo × (diffuse + specular) where energy is conserved

pbr (light-ahara, color-phala, energy-siddha)
  → Cook-Torrance BRDF in frag.glsl
  → D (GGX normal distribution) × F (Fresnel) × G (geometry) / (4·NdotL·NdotV)
  → IS what pbr.om says: energy-siddha photon-abheda light-ahara color-phala

rasterization (trikona-ahara, fragment-phala, bindu-janya prasarana-abheda)
  → hardware rasterizer (OpenGL does this)
  → the "prasarana" (spreading) IS barycentric interpolation of vertex attributes

camera-3d (darshana-swarupa, projection-kriya)
  → view matrix: lookAt(position, target, up)
  → projection matrix: perspective(fov, aspect, near, far)
  → IS the collapse of world-space to 2D viewport

force-directed (spring-force-yukta, repulsion-yukta, alpha-cooling-yukta)
  → runs in OCaml each frame before VBO upload
  → spring: F = k × (|d| - rest) × normalize(d)
  → repulsion: F = c / dist²
  → velocity: v = v + F × dt, pos = pos + v × dt, v = v × damping
  → alpha cools each tick until convergence

ray-picking (rekha-swarupa, camera-3d-sthita, mouse-yukta, collision-phala)
  → unproject mouse (x,y) through inv(proj×view) into world-space ray
  → ray-sphere test for each gola: |cross(d, oc)|² ≤ r² × |d|²
  → returns the nearest nigamana hit → proof graph can respond
```

### The unit IS the scale of the coordinate rekha

Not metre the SI standard — `metre` is the **name of the scale**.
The coordinate system is three `rekha` through `bindu` (origin) in `sthira-apeksha`.
Each `rekha` has a `matra` edge: `[rekha-x, matra, metre]`.
The value `3.0` on that rekha means "3 metres from origin along x".

```
sthira-apeksha (world frame)
  rekha-x: matra=metre
  rekha-y: matra=metre
  rekha-z: matra=metre

gola-A:
  bindu = (3, 0, 0) in sthira-apeksha
  dura = 0.5 m (radius)
  mass = 5 kg
  velocity = (10, 0, 0) m/s

3d-to-native reads this →
  DrawSphere { center=(3,0,0); radius=0.5*scale; color=... }
  → VBO upload → glDrawElements → GPU
```

Scale factor = pixels-per-metre (or world-units-per-metre). Changes the render, not the graph.

### Frame as avastha

Each frame of the simulation IS an `avastha`:
```
avastha-0 (purva):
  gola-A: bindu=(3,0,0), velocity=(10,0,0)
  gola-B: bindu=(-3,0,0), velocity=(-10,0,0)

derive-step fires velocity-step + position-step:

avastha-1:
  gola-A: bindu=(3+10·dt, 0, 0), velocity=(10,0,0)
  gola-B: bindu=(-3-10·dt, 0, 0), velocity=(-10,0,0)

...

avastha-n (collision):
  |bindu-A - bindu-B| ≤ r-A + r-B
  nyaya-step fires collision-mantra
  → velocities updated by conservation of momentum
  → kona = vec-dot(v-A, v-B) / (|v-A|·|v-B|) = deflection angle

avastha-n+k (destruction, if force > threshold):
  kshaya fires
  → gola-A fragments into parts
  → new objects with distributed momentum
  → pratishedha of original object's integrity
```

### Imagination vargas as rendering modes

Every varga IS an imagination mode — a way of reading the same graph:

| Varga | Imagination | Render |
|---|---|---|
| `geometry-varga` | shape, distance, angle | mathematical diagram |
| `3d-varga` | spatial scene | native OpenGL: VBO + GLSL shaders |
| `physics-varga` | forces, motion, energy | equations, numbers |
| `sangeetham-varga` | sound, rhythm, melody | Strudel/TidalCycles |
| `biology-varga` | cell, metabolism, folding | molecular diagram |
| `cs-varga` | computation, recursion | OCaml code |
| `kaala-varga` | time, sequence, tense | animation timeline |

The graph does not change between modes. Only the `anuvada` (reader) changes.
The same `gola moving through akasham` is:
- geometry: a sphere tracing a path
- 3d: `DrawSphere` at each avastha, uploaded to VBO, drawn via GLSL
- physics: kinetic energy = ½mv²
- sangeetham: the arc of a rising note
- All simultaneously true. All from the same graph state.

---

## What Needs to be Built

### Engine layer (new — enables all 3D rendering)

```
vyakarana/lib/render_stubs.c
  SDL2 window + OpenGL 3.3 core context
  GLSL compile + link (vert.glsl + frag.glsl)
  VAO/VBO management: upload vertex data, draw indexed triangles
  Procedural mesh generation: sphere (gola), cylinder (vrtta-stambha), line (rekha)
  Force-directed layout: spring + repulsion + alpha-cooling, per-frame OCaml→C→GPU
  Ray-picking: unproject mouse → world-space ray → sphere intersection

vyakarana/lib/render.ml
  OCaml C FFI: external "caml_render_begin_frame" etc.
  VRenderCmd type + eval_render : proof_graph -> render_cmd list
  Reads nigamana nodes directly — no template expansion

vyakarana/lib/shaders/vert.glsl
  Inputs: position (vec3), normal (vec3), uv (vec2)
  Uniforms: model, view, proj matrices
  Output: gl_Position, vNormal, vUV to fragment stage

vyakarana/lib/shaders/frag.glsl
  Inputs: vNormal, vUV from vertex stage
  Uniforms: albedo, roughness, metallic, lightPos, lightColor
  Cook-Torrance PBR: implements pbr.om (energy-siddha photon-abheda)
  Output: FragColor

New tantra primitives in yantra_eval_primitives.ml:
  draw-sphere  "node-name"        → VRenderCmd
  draw-line    "node-a" "node-b"  → VRenderCmd
  set-camera   pos target fov     → VRenderCmd
  begin-frame                     → VRenderCmd
  end-frame                       → VRenderCmd
  pick-ray     x y                → nigamana option
```

### Kosha nodes to update (domain-raylib-sthita → domain-3d-sthita)

The old `domain-raylib-sthita` references were anchored to the Lua/Raylib path.
These nodes should be updated to `domain-3d-sthita` — the domain is 3D, not Raylib:

```
brahman/kosha/3d/camera-3d.om      domain-raylib-sthita → domain-3d-sthita
brahman/kosha/3d/viewport.om       domain-raylib-sthita → domain-3d-sthita
brahman/kosha/3d/ray-picking.om    domain-raylib-sthita → domain-3d-sthita
```

### Missing nodes (immediate)

```
brahman/kosha/3d/3d-varga.om
  "geometry-varga-vishesa"     ← 3d IS geometry, spatially rendered
  "physics-varga-vishesa"      ← 3d IS physics, in space and time
  "kaala-yukta"                ← 3d involves time (animation)
  "akasham-yukta"              ← 3d lives in akasham
  "scene-graph-yukta"          ← 3d organises as scene-graph (= proof-graph)
  "gati-yukta"                 ← 3d involves motion
  "anuvada-swarupa"            ← 3d IS a render/translation mode
  shabda 3d-varga / the-spatial-imagination-varga

brahman/kosha/3d/aayaama-traya.om
  "aayaama-swarupa"
  "akasham-abheda"
  "rekha-traya-sthita"         ← three orthogonal rekha
  "bindu-sthita"               ← through an origin point
  "sthira-apeksha-sthita"      ← in the fixed frame
  shabda three-dimensional / the-full-spatial-frame

brahman/sangati/geometry/aayaama-traya.om
  "aayaama-swarupa akasham-abheda"
  "rekha-traya-sthita bindu-sthita"
  shabda three-dimensional / three-independent-directions-of-extension-through-one-origin
```

### Missing geometry quantities (unblocks physics-in-3d)

```
brahman/kosha/math/geometry/quantities/
  volume.om        word:volume,volumes  matra:cubic-metre
  area.om          word:area            matra:square-metre
  circumference.om word:circumference   matra:metre
  surface-area.om  word:surface-area    matra:square-metre
  diameter.om      word:diameter        matra:metre
  depth.om         word:depth           matra:metre
  width.om         word:width           matra:metre
```

Note: `dura` is already the radius primitive (`satya=0.839`, `swarupa matra`).
Note: `height` already exists (`word: height altitude elevation`) via displacement.om.

### Missing unit nodes

```
brahman/kosha/physics/units/
  cubic-metre.om       word:m3,cubic-metre,cubic-meter,m³
  square-metre.om      word:m2,square-metre,square-meter,m²
  metre-per-second.om  word:m/s,metres-per-second
  joule.om             word:J,joule,joules
  pascal.om            word:Pa,pascal,pascals
  watt.om              word:W,watt,watts
  hertz.om             word:Hz,hertz
  volt.om              word:V,volt,volts
  ampere.om            word:A,ampere,amps
```

### Missing shape word keys (so BQG resolves shapes)

```
gola.om update:          shabda word:sphere,ball,spheres,balls
vrtta-stambha.om update: shabda word:cylinder,cylinders
vrtta.om update:         shabda word:circle,circles,disc
trikona.om update:       shabda word:triangle,triangles
tala.om update:          shabda word:plane,surface,flat
rekha.om update:         shabda word:line,lines,axis,rod,bar
```

### Missing geometry mantras (shape → volume/area)

```
brahman/kosha/math/geometry/mantras/
  vrtta-area-mantra.om              π·r²        janya:dura  phala:area
  vrtta-circumference-mantra.om     2·π·r       janya:dura  phala:circumference
  gola-volume-mantra.om             (4/3)·π·r³  janya:dura  phala:volume
  gola-surface-area-mantra.om       4·π·r²      janya:dura  phala:surface-area
  vrtta-stambha-volume-mantra.om    π·r²·h      janya:dura,height  phala:volume
  vrtta-stambha-surface-area.om     2πr²+2πrh   janya:dura,height  phala:surface-area
  trikona-area-mantra.om            ½·b·h       janya:rekha,height  phala:area
```

### Missing simulation nodes

```
brahman/kosha/physics/simulation/
  purva-avastha.om    word:initial,start,beginning  — the initial state
  uttara-avastha.om   word:final,end,after          — the final state
  samvega.om          word:momentum,impulse         — momentum vector (Sanskrit)
  tvarana.om          word:impulse,jerk             — impulse = force×time

brahman/kosha/physics/collision/
  elastic-collision.om     janya:samvega-A,samvega-B  phala:samvega-A',samvega-B'
  inelastic-collision.om   janya:samvega-A,samvega-B,coefficient  phala:samvega-final
  collision-detection.om   janya:bindu-A,bindu-B,dura-A,dura-B  phala:collision
```

### Missing kaala-varga

```
brahman/kosha/physics/kaala-varga.om
  "physics-varga-vishesa"
  "3d-varga-vishesa"          ← kaala IS part of 3d imagination
  "spanda-yukta"              ← time pulses
  "avastha-yukta"             ← time carries states
  "kramanusara-yukta"         ← time is the axis of rate-of-change
  "keyframe-swarupa"          ← each moment is a keyframe
  shabda kaala-varga / the-time-imagination-varga
```

---

## The Simulation Loop (tantra sketch)

```
tantra simulate-step
  -- one frame of the physics simulation
  -- advances all object states by dt

  takes graph dt

  -- update velocities: v(t+dt) = v(t) + a·dt
  after-velocity = map-owned-quantities graph "velocity" "acceleration"
    (fn v a -> v + a * dt)

  -- update positions: x(t+dt) = x(t) + v·dt
  after-position = map-owned-quantities after-velocity "bindu" "velocity"
    (fn x v -> x + v * dt)

  -- collision detection: nyaya check
  after-collision = nyaya-step after-position

  -- render: read graph state → native draw commands
  render = 3d-to-native after-collision

  return [after-collision, render]
done
```

This tantra does not exist yet — but its shape is already in the graph:
- `velocity-step` and `position-step` are the OCaml implementations
- `3d-to-native` reads proof graph nodes → emits `VRenderCmd` list → C stubs → GPU
- `nyaya-step` (P8d) is the collision check

The event loop runs in C (SDL2 polls input, controls frame timing).
On each tick: SDL2 → OCaml update (simulate-step) → VRenderCmd list → C render → swap buffers.

---

## Key Principles

1. **The graph IS the imagination** — not a description of something elsewhere; the graph state IS the scene
2. **derive-step IS the physics engine** — each fixpoint pass IS one conceptual frame advancing
3. **anuvada IS the renderer** — reads the graph, produces output in the target medium
4. **The scene graph IS the proof graph** — `scene-graph proof-graph-abheda` — no separate structure
5. **The kosha IS the GPU spec** — `pbr.om` IS the BRDF, `rasterization.om` IS the hardware rasterizer, `vertex.om` IS the VBO layout
6. **The unit is the scale of the coordinate rekha** — metre, cm, pixel are all the same structure
7. **kaala is the 4th varga** — time is not a parameter; it IS a frame, like the 3 spatial aayaama
8. **Every object owns its properties** — via shashthi-vibhakti; the graph walks ownership to fire mantras
9. **Destruction IS kshaya** — the dissolution of form when force exceeds threshold; already the richest node
10. **All vargas render simultaneously** — the same graph state produces text, 3D, sound, code at once
11. **No separate simulation system** — the proof graph IS the simulation; imagination IS proof
12. **No intermediary** — old path: graph → templates → Lua → Raylib (broken). New path: graph → VRenderCmd → C stubs → GPU (direct)

---

## Relationship to Nyaya Plan

The nyaya-plan builds the reasoning layer (P8a–P8g).
This plan builds the imagination layer — what the reasoning IS reasoning about.

They are not separate:
- `derive-step` (nyaya-plan P8b) fires geometry mantras (this plan) to get volume
- `nyaya-step` (nyaya-plan P8d) detects collision (this plan) to update avastha
- `3d-to-native` renders the graph state that nyaya-plan's pipeline produces

Implementation order relative to nyaya-plan:
- **Now**: build engine layer (render_stubs.c, render.ml, GLSL shaders) — unblocks all visual output
- **After P8a**: build geometry quantities + shape word keys (unblocks volume→density chain)
- **After P8b**: build geometry mantras (janya/phala edges needed for derive-step to fire them)
- **After P8d**: build simulation nodes + kaala-varga (nyaya-step needed for collision detection)
- **Longer term**: simulate-step tantra, full collision resolution, destruction via kshaya
