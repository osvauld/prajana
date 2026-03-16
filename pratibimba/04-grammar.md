# 04 — The Grammar

**The grammar is what makes the graph speak — in light, in sound, in words.**

---

## Pratibimba IS another anuvada

The proof graph pipeline ends with `anuvada` — the stage that reads the graph
state after derive-step and produces an expression of what was understood.

Currently `anuvada-ganana.tantra` produces English text.
`physics-to-ocaml` produces OCaml code.
`ornament-to-strudel` produces Strudel patterns.

`3d-to-pratibimba.om` is another member of the same family.
It reads the same graph state after derive-step.
It produces EpochOutput (visual + audio + speech) instead of English.

They run simultaneously. Same pipeline, same graph state, different readers.
The English answer and the 3D scene and the audio tone are all the same
`anuvada` applied to the same graph, simultaneously.

The pipeline does not need to change.
The `anuvada` stage runs all registered readers at once.
Pratibimba is just another reader registered at that stage.

---

## Grammar not translation

There is a distinction between translation and grammar.

Translation takes something expressed in one form
and re-expresses it in another, losing nothing, changing the medium.
This is what a dictionary does — word for word, concept for concept.

Grammar is different. Grammar is the set of rules
by which meaning is composed into expression.
It does not translate. It generates.
Given a state of understanding, grammar produces the expression of it.

The bhasha/english/ layer is grammar, not translation.
It does not translate nodes one by one.
It reads the graph state as a whole and generates a sentence
according to the rules of English composition.

The bhasha/pratibimba/ layer will be the same.
It reads the graph state as a whole and generates an epoch output —
a sequence of commands that express what the graph understands
as light, sound, and speech simultaneously.
The rules of pratibimba composition determine how they are ordered and shaped.

---

## What the grammar maps

The grammar has two sides: what it reads and what it produces.

What it reads — the graph concepts:
- gola: a sphere in akasham, with a bindu (center) and dura (radius)
- rekha: a line between two bindus
- avrti: the loop itself — the epoch boundary (begin and end)
- material: how a surface responds to light
- camera-3d: the darshana — how the scene is projected
- light: the photon source that makes things visible
- trajectory: the krama of bindu positions through kaala
- force: a directed push with magnitude and direction
- swara: a musical note — a frequency in time
- varna: a phoneme — a unit of speech sound

What it produces — the epoch output commands:
- a sphere at a position with a material (visual)
- a line between two points (visual)
- the beginning and end of an epoch
- a camera transform
- a light position and color
- a trail of positions fading behind
- an arrow showing direction and magnitude
- a tone at a frequency with duration and envelope (audio)
- a phoneme with pitch contour and duration (speech)

The grammar is the mapping between these two sides.
A concept on one side becomes an expression on the other.
The pratibimba-setu.shabda file is where this mapping lives.

---

## The setu

The setu (bridge) is the established pattern for this in the system.
There is already an ocaml-setu.shabda that bridges
kosha concepts to OCaml syntax.
There is already a strudel-setu.shabda that bridges
music concepts to Strudel patterns.

The pratibimba-setu.shabda is the same kind of file.
It maps kosha concepts to EpochOutput command descriptors.
The format is the same: key: value pairs,
where the key is a concept name and the value is the epoch expression.

The 3d-to-pratibimba.om is the visual anuvada that uses the setu.
It reads the proof graph, applies the setu mappings,
and composes the result into the visual part of EpochOutput.

The naada-to-pratibimba.om is the audio anuvada.
The vak-to-pratibimba.om is the speech anuvada.

Together they are the bhasha/pratibimba/ layer.
The same structure as every other language layer in the system.

---

## What already exists

This is not starting from nothing. `bhasha/render/` already contains:

- `pratibimba.om` — the parent concept, already defined:
  `naada-swarupa spanda-phala domain-language-sthita`
  IS naada, produces spanda, the parent of all renderers.

- `music-ir.om` — the audio intermediate representation:
  `pratibimba-yukta setu-swarupa naada-phala`
  `thaalam-yukta swara-yukta voice-yukta event-yukta`
  Already maps graph concepts to timed audio events.

- `resonance-ir.om` — graph animation representation:
  Maps satya scores and relation flow to animation parameters.

- `music-ir-setu.shabda` — maps graph relation types (swarupa, abheda, yukta...)
  to audio parameters: timbre, octave, gain, articulation.
  Already working. Already used.

- `resonance-ir-setu.shabda` — maps satya to energy, relations to flow strength.

`bhasha/render/` IS the predecessor to `bhasha/pratibimba/`.
It needs renaming and updating — `pratibimba.om` still says `raylib-yukta`
which is retired. But the structure, the concept, the setu pattern
are all already there and working.

The 3d-to-pratibimba.om (visual anuvada for wgpu) and
vak-to-pratibimba.om (speech anuvada) are genuinely new.
Everything else already exists in some form.

---

## The epoch is a sentence

A sentence in English has a structure:
subject, verb, object, perhaps modifiers.
The grammar rules determine what can appear where.

An epoch in pratibimba has a structure:
begin, camera, lights, objects, sounds, speech, end.
The grammar rules determine what can appear where.

The proof graph provides the subject matter —
what objects exist, where they are, what they look like, what they sound like.
The grammar provides the structure —
how that subject matter becomes an ordered sequence of epoch commands.

The result is a sentence spoken in light and sound simultaneously.

---

## The grammar grows with the kosha

This is the deep consequence.

As the kosha gains new concepts, the grammar gains new words.
When lorentz-force is defined in the kosha,
the grammar can learn to express it as an arrow showing the force vector
and as a tone whose pitch encodes the force magnitude.
When trajectory is defined, the grammar can express it as a visual trail
and as a melody following the path.
When collision is defined, the grammar can express it as a flash of light
and as an impact sound.

The grammar does not need to be rewritten.
The setu grows. The anuvada reads more kinds of nodes.
The epoch becomes richer as the understanding deepens.

This is why the grammar approach is right.
A hardcoded renderer knows only what it was told at the time of writing.
A grammar-driven epoch knows whatever the graph knows.
The epoch IS the understanding made present.
They grow together.

---

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-16 | Initial writing — named bhasha/gl/, focused on visual output only |
| 2026-03-16 | Renamed to bhasha/pratibimba/. Grammar now covers visual + audio + speech. pratibimba-setu.shabda replaces gl-setu.shabda. Three anuvada (3d, naada, vak) replace one. The epoch is the sentence, not just the frame. |
| 2026-03-16 | Discovered: bhasha/render/ already IS the pratibimba layer. pratibimba.om (naada-swarupa), music-ir.om, resonance-ir.om, music-ir-setu.shabda all exist and work. bhasha/render/ needs renaming to bhasha/pratibimba/ and pratibimba.om needs raylib removed. 3d-to-pratibimba and vak-to-pratibimba are the genuinely new additions. |
| 2026-03-16 | Clarified: pratibimba IS another anuvada in the same family as physics-to-english and physics-to-ocaml. Runs at the same pipeline stage, reads the same graph state. The pipeline does not change — just another reader registered at the anuvada stage. |
