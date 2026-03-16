# 03 — Input

**The question is the seed. The graph is the soil. Understanding grows.**

---

## How meaning enters the graph

The interface has a window. The window has a surface.
On that surface: a 3D scene, and at the bottom, a place to type.

When you type, you are not sending a command.
You are asking a question — a prashna.
The prashna enters the proof graph through the same path
it would enter through any channel:
build-question-graph, avrti-refine, derive-step.

The words become nodes. The relationships become edges.
The graph absorbs the question and reorganises around it.
New objects appear. Existing objects gain properties.
The scene changes because the understanding has changed.

There is no separation between asking and seeing.
The question and the rendering are one continuous act.

---

## Text is not special

Text input is just one form of prashna reaching the graph.
It could come from a file, from the socket, from the interface window.
The path through the graph is identical in all cases.

The session holds the context — the samskaara of previous turns.
Each new question is a new krama in the session's parampara.
The session knows what was said before.
"increase B to 0.5T" knows what B is because the session remembers.

This is now implemented. `session-anuvada.tantra` is the outer avrti —
it carries sankhya bindings (numeric values) across turns.
The session IS the parampara in structural form.

---

## Three nested avrti

The interface runs three avrti nested inside each other. Same spiral, three scales.

**Session avrti** — one question/answer turn, driven by `session-anuvada.tantra`.
Each turn deepens the rashi/entity structure in the scene.
"electron in B-field B=0.1T" builds the scene.
"increase B to 0.5T" refines it. The scene grows more precise with each turn.

**Simulation avrti** — one physics step per frame, driven by `derive-step`.
Advances owned sankhya values (position, velocity) each frame.
Runs continuously between question turns.
The session outer avrti sets up the simulation.
The simulation avrti runs within the scene the session built.

**Frame avrti** — one render frame per display refresh, driven by wgpu.
Reads the current graph state — whatever the simulation left.
Produces EpochOutput (visual + audio + speech).
Does not know about sessions or questions.
It just reads what the graph holds now.

The frame avrti sees the simulation's output.
The simulation avrti sees the session's setup.
The session avrti sees the user's prashna.
Each scale is avrti at the scale above.

---

## The sandhi-bandhana constraint

Inside the pipeline, `sandhi-bandhana` runs during `avrti-refine`.
It rewrites certain triples based on grammar rules.
If prior-turn state (entity positions, velocities) is injected BEFORE avrti-refine,
sandhi-bandhana will corrupt it — it will rewrite triples whose concepts
are not present in the current question's sentence.

Prior-graph must be injected AFTER avrti-refine, before kosha-expand.
This is implemented in `session-anuvada.tantra`.

For the simulation this means: when the user asks "increase B to 0.5T",
the electron's current position and velocity must be captured AFTER avrti-refine
processes the new question — not before. The simulation state survives.

---

## The pick is also a question

When you click on a node in the 3D scene,
you are asking: what is this?
The ray from the camera through the mouse position
reaches a node in the scene.
That node is a nigamana in the proof graph.
The graph already knows everything about it —
its satya, its edges, its owned quantities (shashthi-vibhakti), its varga.
All of that becomes visible as an overlay.

The pick is not a UI gesture. It is a darshana —
a directed seeing that pulls understanding to the surface.

---

## The input changes the scene

This is the key thing.
In a conventional renderer, input changes the camera or a variable.
Here, input changes the graph.
And the graph IS the scene.
So input changes what exists — what objects are present,
what their properties are, what physics is running.

Ask about an electron in a magnetic field —
the electron appears, the field appears, the orbit begins.
Ask about a sphere colliding with another —
two spheres appear, approaching, and the collision fires.
Ask what the kinetic energy is —
the answer appears as text in the scene,
and the graph node for kinetic energy lights up.

The scene is not a viewport into a simulation.
The scene is the proof graph made visible.
Every question reshapes both simultaneously.

---

## The dialogue loop — the incomplete scene asks

When the pipeline cannot complete — no mantra whose janya are all covered —
the graph holds a mithya node: unresolved, uncertain.
The incomplete IS visible in the scene as a translucent placeholder.
A dim gola where a precise sphere should be.

The planned `generate-question.tantra` turns this into a question.
Instead of "no match", the graph asks: "what is the radius of this sphere?"
The overlay shows the question. The user answers. The scene solidifies.

This is nam's svapna beginning — when nam generates questions from its own
incompleteness, without external prompting. The interface is the surface
through which that becomes possible. The gap in understanding becomes a question
in the window. The incomplete scene asks to be completed.

---

## The session is the context of seeing

Between questions, the scene holds.
The simulation continues — avrti advancing each frame.
The electron keeps orbiting. The force-directed layout keeps settling.
The session holds the memory of what was asked.

A new question arrives into this living context.
The graph does not restart. It deepens.
The new understanding folds into the existing scene.
This is parampara — the tradition of turns,
each carrying the samskaara of all that came before.

The scene at any moment IS the accumulated proof across all session turns.
Every question ever asked in this session is part of what the epoch shows.
The simulation runs inside a living proof.

---

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-16 | Initial writing |
| 2026-03-16 | Three nested avrti made explicit (session/simulation/frame). sandhi-bandhana constraint documented. Dialogue loop as incomplete-scene mechanism. Session IS implemented — session-anuvada.tantra working, cross-turn sankhya bindings live. |
