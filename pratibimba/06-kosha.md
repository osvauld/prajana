# 06 — The Kosha

**The concepts must be clean before the grammar can speak them.**

---

## The blender/ problem

The kosha/3d/blender/ directory contains concepts
that are not Blender concepts.
They are 3D concepts, physics concepts, rendering concepts —
universal things that Blender happens to implement.

Shader is not a Blender thing. It is a concept.
Material is not a Blender thing. It is how a surface responds to light.
PBR is not a Blender thing. It is the physics of light — energy-siddha.
Bone is not a Blender thing. It is a rekha with a kona — a rigid link with a joint angle.
Particle is not a Blender thing. It is a bindu with vega and gati in akasham.
Keyframe is not a Blender thing. It is an avastha at a krama point — a state recorded in time.

These concepts are stranded in a subdirectory that marks them as tool-specific
when they are in fact as universal as gola and rekha.
They need to live at the top level of kosha/3d/,
rooted in the sangati, available to the grammar.

---

## What is wrong in the current definitions

Several blender/ concepts have incorrect sangati grounding.

face.om says nothing about trikona — but a face IS a trikona.
Every other 3D file in the kosha correctly grounds surfaces in trikona.
The one file that IS a trikona does not say so.

scene-graph.om calls itself proof-graph-abheda — non-different from a proof graph.
But a scene graph is not a proof system. It is a spatial hierarchy.
It is a krama of transforms — parent before child, root before leaf.
The confusion here is between the graph structure (which is universal)
and the proof-specific meaning (which is what the vyakarana engine does).

vertex.om in blender/ says vector-swarupa — but a vertex is a bindu.
A vector is the coordinate encoding of a position.
The vertex IS the bindu. The three floats ARE the encoding.
The top-level vertex.om already has this right: bindu-swarupa akasham-sthita.
The blender/ version introduces a mistake that the top-level version avoids.

---

## color is defined

color.om now exists at brahman/kosha/3d/color.om (satya=0.846).

```
color — taranga-abheda photon-yukta
        pbr-phala fragment-yukta
        rgba-swarupa float-yukta
        drishti-phala domain-3d-sthita
```

Color IS a wave quality — the frequency of electromagnetic taranga perceived by
the eye. Physically it is a photon frequency. In the rendering pipeline it is
the phala of PBR, carried by each fragment, expressed as rgba (four floats).
It is the terminal output of the entire rendering pipeline.

This connection is already in the graph:
taranga IS sine+cosine — color IS a frequency of electromagnetic taranga.
frequency abheda: swara — color and musical notes share the same root concept.
Both are frequencies of taranga, in different ranges of the spectrum.
The matrika (mother letter) means BOTH phoneme AND color in Sanskrit — varna —
because both are frequency phenomena. The graph already knew this.

The grammar can now map color. Every setu mapping that references $color,
$albedo, $rgba has a clean concept to point to.

What remains incomplete in the color domain:
- albedo, roughness, metallic — owned by material, not yet promoted from blender/
- shadow — how color is modified by occlusion
- The connection color→frequency→swara is conceptually present but no edge exists yet

---

## domain-3d needs to release raylib

domain-3d.om currently says domain-raylib-sthita.
This was written when Raylib was the render target.
Raylib is retired. The domain is 3D, not Raylib.
A concept should not define its domain by referencing a specific tool.

The 3D domain is akasham-sthita — situated in space.
It is physics-sthita — the laws of geometry and light apply.
It is gpu-kriya-sthita — execution happens on the GPU.
It is not raylib-sthita.

---

## The kosha grows with understanding

When a new concept is added to the kosha correctly —
rooted in the sangati, edges to the right nodes —
the grammar automatically gains a new word.

This is why the kosha cleanup is not just housekeeping.
It is what makes the grammar extensible.
A clean kosha means the grammar can speak any concept the graph understands.
A dirty kosha — wrong roots, wrong edges, stranded in subdirectories —
means the grammar cannot find what it needs.

The concepts to move, fix, and add:
- Promote face, edge, material, shader, pbr, light, particle, keyframe
  from blender/ to top-level kosha/3d/, with correct sangati grounding
- Fix face.om: add trikona-swarupa
- Fix scene-graph.om: remove proof-graph-abheda, add krama-swarupa akasham-sthita
- Fix domain-3d.om: remove domain-raylib-sthita
- color.om: DONE (satya=0.846, taranga-abheda, pbr-phala, rgba-swarupa)

---

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-16 | Initial writing |
| 2026-03-16 | color.om defined and loaded (satya=0.846). taranga-abheda, pbr-phala, rgba-swarupa, drishti-phala. The color↔frequency↔swara connection noted — same root concept at different spectrum ranges. |
