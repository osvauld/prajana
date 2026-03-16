# 05 — The Render Layer

**The render layer is not the renderer. It is the surface through which the graph speaks.**

---

## What it is

The render layer is the thinnest possible thing between the graph and the GPU.
It receives what the graph says and executes it faithfully.
It does not interpret. It does not decide. It does not add.

This is right because all intelligence lives in the graph.
The render layer's job is to be transparent —
to let the graph's understanding appear on screen
without distortion, without addition, without loss.

A thick render layer would mean the renderer is making decisions
that should belong to the graph.
A thin render layer means the graph is fully in control.

---

## The GPU pipeline is already understood

The kosha has already defined the full GPU pipeline from first principles.
vertex is bindu in akasham, carrying position and normal as floats.
rasterization takes triangles and produces screen fragments.
The shader runs on the GPU, transforming vertices and computing colors.
pbr is the physics of light — energy conserved, photon interaction.

The render layer does not invent any of this.
It implements what the kosha already knows.
The vertex shader is what camera-3d.om says projection is.
The fragment shader is what pbr.om says light interaction is.
The rasterizer is what rasterization.om says — the hardware runs it.

This is not incidental. It is the proof that the architecture is right.
When the kosha concept and the GPU implementation say the same thing,
the understanding is sound.

---

## What is already built (the proof)

A C/OpenGL prototype exists and runs in `agent_x/vyakarana/render/`.
A window opens. A 3D scene appears.
Six spheres in a force-directed layout, PBR shaded,
orbiting camera, mouse ray-picking, alpha-cooling convergence.

All of this was built directly from what the kosha describes.
The force-directed physics came from force-directed.om.
The sphere geometry came from gola.om — sama-dura-sthita.
The PBR shading came from pbr.om — energy-siddha, photon-abheda.
The ray-picking came from ray-picking.om — rekha-swarupa, collision-phala.

This prototype proved the concepts. The GPU pipeline works.
The shaders implement the kosha correctly.
The force-directed layout converges.
Ray-picking resolves to a node.

The permanent render layer is `renderer_wgpu` in osvauld.
It inherits everything the prototype proved —
the same concepts, the same pipeline, the same kosha mapping —
implemented in Rust with wgpu and WGSL instead of C and GLSL.
The prototype is the specification. renderer_wgpu is the implementation.

---

## The shaders implement the kosha

The vertex shader implements camera-3d —
the darshana that collapses aayaama-traya into aayaama-dvaya.
It takes a position in world-space (akasham)
and projects it to clip-space (the viewport).
This is projection-kriya, literally.

The fragment shader implements pbr —
the energy-siddha computation of how light meets material.
The three terms — normal distribution, Fresnel, geometry shadowing —
together ensure energy conservation, exactly as pbr.om states.
The result is color. This is color-phala, literally.

The rasterizer runs in hardware.
It takes triangles (trikona) and converts them to fragments.
This is trikona-ahara, fragment-phala, literally.
The hardware IS what rasterization.om defines.

---

## The render layer does not know about concepts

This is important.

The render layer does not know what a gola is.
It does not know what an electron is.
It does not know what a magnetic field is.

It knows how to draw a sphere at a position with a material.
It knows how to draw a line between two points.
It knows how to set a camera.

The meaning of these things — why this sphere is here,
what this line represents, why the camera faces this way —
all of that lives in the graph.

The render layer is like a skilled craftsman
who builds exactly what the architect specifies
without needing to know what the building is for.
The graph is the architect. The render layer is the craft.

---

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-16 | Initial writing |
| 2026-03-16 | C/OpenGL prototype is the proof, not the permanent home. renderer_wgpu in osvauld is where this lives. The prototype specification stands — same kosha mapping, same pipeline logic, different language (WGSL not GLSL, wgpu not OpenGL). |
