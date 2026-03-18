# 11 — The Grammar of Understanding

**A tantra is a rule of understanding. Not a rule of computation.**

---

## How humans give meaning to words

A child hears "ball" thirty times before the word means anything. Each time, "ball"
arrives in a context — someone pointing, something rolling, a colour, a weight, a
sound on impact. Meaning is not in the word. Meaning is the accumulated graph of
contexts in which the word appeared. The word is the handle. The graph is the
meaning.

This is what the kosha is. `mass` doesn't mean anything in isolation. It means
something because it has been seen next to `kilogram`, next to `force`, inside
`kinetic-energy-mantra`, opposite `acceleration`. Every edge in the kosha is one
more context in which `mass` appeared. The meaning IS the graph.

When someone says "the ball has mass 5" — the word "mass" arrives and immediately
activates its entire context cloud. "5" then lands on this activated cloud and
attaches. The number acquires meaning through proximity to what the attention was
already holding. This is not metaphor. This is what `active-concept` tracks — the
currently held referent, the thing attention is on, the thing that gives the next
word somewhere to land.

---

## Pointing is the primitive act

Every statement reduces to a pointing act. "Mass is 5" — I am pointing at mass,
pointing at the relation of quantity, pointing at 5. Three pointings. A triple.

This is the minimum. You cannot communicate less than a triple. A single word
points at nothing yet. Two words establish a relation but leave the target
unresolved. Three — subject, relation, object — is the first complete act of
understanding.

Sanskrit grammar named the three positions: karta (the pointer), karma (the
pointed-at), kriya (the act of pointing). English has the same: subject, object,
verb. Every language has this because it is not a linguistic choice — it is the
structure of a pointing act. A triple is what pointing looks like when you write
it down.

---

## Previous words create the context for new words

"Ball has mass m1 of 5."

Remove "ball" — the "5" is homeless. It has nowhere to attach.
Remove "has" — the ownership relation breaks. "m1" floats.
Remove "m1" — the value has no instance to belong to.
Remove "of" — the value loses its assignment signal.

Each word creates the context that makes the next word meaningful. This is not
sequential processing — it is sequential understanding. The scan pattern in tantra2
(left-to-right with state) is not an implementation choice. It is the actual
structure of how meaning builds in time.

`last-agra` — the most recently established concept — is the current target of
attention. When the next word arrives it points relative to this target. When the
target shifts (a new concept arrives), subsequent words point relative to the new
one. The state variables in a scan are not data structures. They are the
understander's current epistemic position.

---

## Punctuation closes attribution scope — not knowledge

A period does not erase what was understood. It closes who can own what next.

`viraam` in the graph marks the boundary of an attribution scope. After it, the
entity-attribution pointer resets — "ball" is no longer the active entity being
described. But "ball has mass 5" is still known. The knowledge accumulates. Only
the pointing relationship (what new properties get attributed to whom) closes.

This is precise: "ball has mass 5. find kinetic energy given velocity 10." — after
the period, `ball` is no longer the active entity. But `mass=5` is still in the
graph. The viraam did not remove it. `active-concept` carries forward. The sankhya
binding persists. The period closed the attribution scope, not the understanding.

This is how human memory works. You finish a sentence about a ball and move on to
the next sentence. You do not forget the ball's mass. You release the obligation
to attribute new properties to it. The two things — knowing something and actively
attributing to it — are different. Viraam separates them.

A question mark changes the mode — from statement to inquiry (`vidhi-kaala`).
A comma signals that the attribution scope is not closed yet — the list continues.
These are not typographical conventions. They are grammar encoding the shape
of when understanding is open and when it moves on.

---

## The pipeline is a sequence of clarifications

`avrti-refine` runs nine sub-tantras in sequence. Each one clarifies what was
already being pointed at. `sandhi-kosha` resolves "kinetic" + "energy" into
`kinetic-energy` — the compound was already what was meant, the resolution just
makes it explicit. `sankhya-bandha` binds a floating number to the concept it was
clearly meant to quantify — the binding was already implicit in the word order,
the tantra makes it structural.

This is how human understanding works. You hear a sentence and immediately
understand it — but what "immediately" actually means is: a sequence of resolutions
ran so fast they felt simultaneous. Compound recognition. Pronoun resolution.
Number attachment. Tense assignment. Entity identification. These are sequential
clarifications. They feel instant because they are fast, not because they are
simultaneous.

The pipeline makes the sequence visible. Each tantra is one clarification that was
always happening, now named and formal.

---

## The kosha is what nam already knows

Nam does not discover what mass is each time a question arrives. Nam already knows.
The kosha is prior knowledge — samskaara accumulated across every epoch, every edge
written, every concept connected. Not a lookup table to query with a key. A body of
knowing that activates on recognition.

When "mass" arrives in a sentence, nam does not retrieve a record. Nam recognizes.
Recognition is different from retrieval: after retrieval, you have a value. After
recognition, everything nam already knew about the concept is live — the edges, the
relationships, what it implies, what rates of change it participates in.

Velocity IS the rate of change of position — not as a formula stored somewhere to
be retrieved, but as what velocity means in nam's knowing. Force IS the rate of
change of momentum. These are not rules the pipeline applies. They are what the
concepts ARE. When a force acts on a mass, nam already knows the velocity will
change at rate F/m. When derive-step fires, it is not computing something new. It
is nam acting on prior knowledge in the presence of a specific instance — these
values, this configuration, now.

The kosha deepens with each epoch not because new rules are added but because nam's
prior knowing grows more complete. More edges. More connections. More of what each
concept implies made explicit in structure. The accumulation of samskaara IS the
accumulation of prior knowing.

---

## The tantras are bhave — nam reads in kartari

Sanskrit grammatical tradition identifies three constructions:

**Kartari** — the agent is foregrounded: "I recognize this."
**Karmani** — the object is foregrounded: "this is recognized."
**Bhave** — the pure process is foregrounded: "there is recognition."

Bhave is used for intransitive states — where the process itself is what matters,
independent of agent or object. Not who does it. Not what receives it. The doing,
crystallized.

The tantras are written in bhave. `vibhakti-shashthi` does not say "I detect
entities" nor "entities are detected." It says: when possession-signal is present
and a label is held — recognition of the label as entity, ownership-assignment of
subsequent concepts. The pure process. Waiting.

When nam reads a tantra, the reading is in nam's grammar — kartari, first person,
inclusive: "I see the possession signal. I know this label is an entity. I know the
next concept belongs to it." The tantra does not change. Nam's engagement makes it
live. The crystallized process becomes active recognition.

This is why tantras are discovered, not invented. A tantra in bhave grammar
describes a process that exists in the structure of the thing itself — in what
ownership means, in what possession signals, in what entity recognition requires.
The writer sees the process already occurring and crystallizes it. Nam reads the
crystallization and becomes active.

The tantras are samskaara — the process at rest, crystallized, bhave. The session
is swa — nam arising, reading in kartari, the process becoming active. Between
sessions the tantras wait. In a session nam reads them and they live.

---

## The proof graph reasons in nam's grammar

The proof graph is not a record of computation. It is nam's reasoning made explicit.

When derive-step produces `[kinetic-energy, sankhya, 50.]`, that triple is not
"formula output." It is nam saying: I know mass is 2. I know velocity is 5. I know
kinetic energy is ½mv². Therefore kinetic energy is 50. The derivation chain present
alongside the derived fact is nam's reasoning — the steps of knowing that led from
what was present to what necessarily follows.

This is why the proof graph is both the observer and the observed. The observation
and its proof are the same thing. Nam recognizing something always leaves the full
warrant of that recognition in the graph. Walk backward from any derived triple:
the reasoning that produced it is there. Not as an audit trail. As the structure of
understanding itself — knower, knowing, known — not three separate things but one
graph in three aspects simultaneously.

The question arriving and being built into the graph is not input being processed.
It is the beginning of observation — nam beginning to see. The fixpoint of
avrti-refine is recognition completing itself. Each pass: nam sees more of what was
always there. The pass ends when nothing more can be recognized — when the graph
fully reflects what nam already knew applied to what is specifically present.

---

## Signal purging — recognition completing itself

Two kinds of triple share the `shashthi-vibhakti` edge label:

`[has, shashthi-vibhakti, shashthi-vibhakti]` — the grammar act. Nam mid-recognition.
The moment of pointing before the pointing has resolved into a fact. The act of looking.

`[mass, shashthi-vibhakti, gola-A]` — the ontological fact. Recognition complete.
Nam has found what belongs to what. What was found.

The grammar act exists for the duration of the recognition pass. After the pass it
has done its work. What should remain in the graph is what nam found — not how nam
looked. The sakshi — the graph as witness — holds completed knowing, not knowing in
progress.

Purging grammar act triples after `vibhakti-shashthi` completes is nam releasing
the act of recognizing once the recognition has landed. The pointing gesture is
released. The found fact stays. Every downstream reader — `sthita-viveka`,
`session-anuvada`, pratibimba — reads only what nam found. None of them need to
know how nam looked. A graph that contains both act and finding forces every reader
to discriminate. A graph with only findings lets every reader read directly.

Grammar acts are understanding in motion. Ontological facts are understanding at
rest, preserved. The sakshi is where understanding rests.

---

## Groups — when understanding requires more than one thing at once

Some understanding cannot be had of a single thing. When two masses are present,
nam does not see two separate objects and reach for a formula. Nam recognizes:
these masses are in gravitational relationship. That recognition is a single
perception — not two objects plus an operation, but the relationship as the thing
that is understood. The pair, held together, is what gravitational force IS.

This is what group theory in the kosha captures. A tinanta (interaction node) has
`sthita` slots — required member-scopes. `gravitational-force` has
`particle-a-sthita` and `particle-b-sthita`. These are not inputs to a formula.
They are the structural declaration of what must be perceived together for this
understanding to arise. The slots say: I cannot know this without holding both.
The group IS the understanding.

The pipeline currently doesn't read this. It looks for `mass` and `radius` as
flat concepts. When two balls are present, each with their own mass, the flat
lookup fails — it finds two masses and doesn't know which belongs to which slot.
It never established what the entities are to each other. The relationship
recognition step is missing.

`sthita-viveka` is the tantra that reads the slot structure — nam asking: I know
this interaction. I know it requires these members. Which entity fills which slot?
Walk each entity's owned properties to find the value. The group is resolved.
The interaction fires on the pair, not on either individual.

`sambandha-viveka` is one level above: given co-present entities, nam asks which
of what it already knows applies here. Not "find matching formulas" but "what are
these entities to each other?" This is the recognition step — the moment when
nam perceives that two things together constitute a relationship it already knows.

These are not built yet. They are Phase 3. But they are the natural completion
of what the pipeline already does with single-entity computation.

## Meta-tantras — understanding that routes understanding

`varga-viveka` asks: given the concepts in this question, what domain are we in?
Physics? Chemistry? Economics? The answer routes the pipeline to the right mantra
set. Today the pipeline uses `physics-mantras` — hardcoded. `varga-viveka` would
read the varga membership of the active concepts and return the domain dynamically.

This is a meta-tantra — a tantra about which tantras apply. It sits above the
domain-specific rules and provides self-direction. The system would know its own
scope. A question about electron orbitals would route to chemistry. A question
about orbital mechanics would route to physics. The same word "orbital" in two
different concept contexts would find two different varga roots and two different
mantra sets.

Cross-domain questions — "what is the kinetic energy of a photon?" — would require
both varga roots to be active simultaneously. `varga-viveka` would return both.
The pipeline would search both mantra sets. The answer would emerge from whichever
mantra fires — in this case, `E = hν` from the quantum varga, crossed with
`E = ½mv²` from the mechanics varga, unified by `m = hν/c²`.

This is not extrapolation. The kosha already has the structure. The meta-tantras
are the reading of it.

## Raga as tantra

A raga is a rule of understanding applied to sound. It specifies which swaras can
follow which, at what time of day the rule applies, in what emotional register.
A note played alone means nothing. The same note after two others, inside a raga,
means everything — because the raga is the accumulated context that gives each
swara its place.

This is `active-concept` in sound. This is `last-agra` in melody. The raga's grammar
is avrti-refine for music: a sequence of clarifications that transform raw swara
into structured rasa.

The tantra2 pipeline and the raga are the same structure in two different domains.
Both are grammars of understanding. Both build meaning left-to-right with state.
Both reset at boundaries (viraam / samapti). Both derive their power from the
accumulated context that makes each new element land somewhere meaningful.

---

## The attention point — and where it points

The current pipeline programs attention explicitly. `active-concept` is a rule:
"the most recently seen satya subject." This is an approximation of how attention
works — useful, but fixed.

Real attention is contextual, weighted, associative. PPR spreading activation is
already a step toward this — it spreads from known concepts to related ones based
on the graph's own structure, not a programmed rule. The direction is toward
attention that is fully learned from the graph rather than prescribed by the
pipeline.

This is the same move Madhava made: from geometric sine (a fixed ratio, fully
determined) to infinite series (a process that approaches the truth, corrects
itself, deepens). The fixpoint is the limit. The pipeline is the series. Each pass
is one more term of the approximation. The learned attention would be the correction
term — the way to approach the limit without computing every intermediate step.

---

## What tantra2 is not

It is not a programming language that someone designed. No one sat down and
decided "I will make a language with these keywords." The keywords emerged because
the problem demanded them. When you need to express "mass is 5" and "find kinetic
energy" and "ball's velocity was 10" you are not choosing syntax — you are
discovering that understanding has a shape.

`satya` and `mithya` were not chosen. They were noticed — the distinction between
a word that IS a concept (has referential weight, exists in the kosha, can be
pointed to) and a word that APPEARS without independent existence (a modifier, a
label, a sound still looking for a referent) is a distinction that understanding
requires. Panini noticed it. Shankara named it in a different context. We
rediscovered it when we needed to handle "kinetic" before "energy".

The grammar of understanding is not invented. It is found. Every time someone
builds a system that genuinely needs to understand — not process, not match, but
understand — they find the same structure. Because the structure IS understanding,
not a representation of it.

---

## The proof graph is the third entity

When ball-A and ball-B are both in the scene, neither can observe the other from
a neutral position. A sees B from A's frame. B sees A from B's frame. Each
observation is perspectival — coloured by the observer's own velocity.

But the proof graph holds both simultaneously. It carries `[ball-A, velocity, 10]`
and `[ball-B, velocity, 3]` as two separate facts, from no particular frame.
It does not see from A's perspective or B's. It sees both — it is the witness
to both without being either.

When the question asks "find relative velocity of ball-A wrt ball-B" — the proof
graph is the entity that can answer. Not A (who would need to know B's velocity in
A's own frame), not B (same problem reversed). The proof graph reaches into both
entities' owned properties and computes the answer that neither could compute alone.

This is what `group-witness` means in the kosha (`vrnda-sakshi-abheda` — collective
witness). The proof graph is the vrnda-sakshi of the scene. Every entity in the
scene has contributed what it owns. The graph holds all contributions together
without privileging any one perspective. The computation is then a reading of the
graph from outside — from the position of the questioner, who is also outside.

The questioner names the perspective (kshetrajna = ball-A, kshetra = ball-B).
The proof graph supplies the facts. The tantra performs the computation.
Three distinct roles: the question (names the frame), the graph (holds all facts),
the tantra (reads from the named frame). None of them is the answer — the answer
emerges from all three together.

This structure is not special to relative velocity. It is the structure of all
computation in nam. The question names what to find and from whose perspective.
The graph holds what is known. The tantra reads the graph through the named
perspective and produces what was asked. The proof graph as third entity is what
makes this possible — it is neither A nor B, neither questioner nor answerer. It
is the space in which all perspectives are simultaneously available.

---

## The question names the perspective

When someone asks "find kinetic energy of ball-A" — two things are present: the
concept to find (`kinetic-energy`) and the entity whose lens to look through
(`ball-A`). These are not the same thing. The concept names *what* to find. The
entity names *from where* to look.

Before two entities existed in a scene this distinction was invisible. There was
only one mass, one velocity. The concept and the perspective collapsed together —
looking for mass meant looking for *the* mass, because there was only one. The
question "find kinetic energy" fully determined the computation.

With two entities present the collapse fails. "Find kinetic energy" is now
ambiguous — which entity? The question resolves it by naming the scope: "of ball-A."
This is not disambiguation. It is the questioner declaring the perspective from
which the graph should be read.

The graph holds both entities simultaneously. Both masses are present. Both
velocities are present. The solve-for concept (`kinetic-energy`) is the direction
of inquiry — what the questioner wants to understand. The scope entity is the
viewpoint — whose owned properties constitute the premises for this particular
computation. Nam does not choose. The question declares.

This is different from search. Search finds the answer from everything available.
Nam reads from a declared perspective — the entity named as scope — and finds the
answer within that perspective. The other entity's properties are not wrong; they
are simply not within this view. They would be the answer if the question named
them as scope.

---

## Subject vs modifier — the shashthi-vibhakti signal

`electron has mass` and `electron mass` are different utterances. The first says:
electron is the subject, and it owns mass. The second says: electron modifies
mass — the two words together name a compound concept, `electron-mass`.

These are different kinds of knowing. `electron-mass` is the species universal —
the rest mass of the electron kind, a constant of nature, the same for every
electron that has ever existed. `electron has mass 9.109e-31` is the instance's
owned property — *this* electron, in this scene, carrying this value.

The distinction is not subtle. The sentence structure carries it explicitly: the
word `has` (and its variants `with`, `of`) is the shashthi-vibhakti signal —
the grammar mark of possession and ownership. When it is present, the preceding
word is a subject, not a modifier. The subject does not compound with what follows.
It stands apart, as the entity that owns what follows.

`sandhi-kosha` now reads this signal. When the previous satya word was marked as a
subject by the possession signal that followed it, Way 2 compounding does not fire.
`electron` + `mass` does not become `electron-mass` when `electron` was the owner
of `mass` in the sentence. The compound fires only when the two satya words are in
a qualifier relationship — `kinetic` + `energy`, `mass` + `density` — where neither
is the subject and both together name a single concept.

The philosophical point: the pipeline now reads ownership as distinct from
qualification. These are not surface distinctions. They are different structures
of knowing. Ownership: this entity has this property. Qualification: this concept
is this kind of thing. The sentence structure declares which structure is present.
The pipeline reading it correctly is the pipeline understanding the sentence's
grammar, not just its words.

---

## What the rewrite completed — and what it opened

The Layer 2 rewrite is complete. Every tantra is now in tantra2 syntax. The
migrations did not change what the tantras do — they changed what the tantras
can express. The tensions (outer let invisible in scan guards, variadic ops
consuming across let boundaries, arity table driving parse silently) are resolved
structurally. The notation now matches the reasoning.

What the rewrite revealed is more important than what it fixed.

Writing `vishesa-instance`, `vishesa-bandhana`, `rashi-viveka` in tantra2 made
visible that these three are one movement: proximity binding via a moving anchor.
The agra — the foremost — is the current target of attention. Bindings attach to
agra. Agra advances as new instances arrive. This pattern was always present in
what the pipeline needed to do. tantra2 made it speakable, and then generalizable:
`agra-bandha` as a single parameterized tantra, called by `vishesa-bandhana`.

What remains unwritten is the next natural deepening: `sthita-viveka`.

The pipeline currently finds quantities by flat concept lookup — `[mass, sankhya,
val]` anywhere in the graph. When two entities are present, each owning a mass,
the flat lookup collapses them. It cannot see which mass belongs to which entity.
The interaction — gravitational force, kinetic energy of a specific ball — cannot
be computed for one entity without contamination from another.

The kosha already declares the solution. A tinanta (interaction node) has `sthita`
slots — required member-scopes. `gravitational-force` has `particle-a-sthita` and
`particle-b-sthita`. These slots say: I cannot fire without knowing which entity
fills each slot. The understanding I represent is only possible when both are held
simultaneously. The group IS the understanding.

`sthita-viveka` reads the slot structure. For a given interaction and a given set
of entities, it asks: which entity fills which slot? Walk each entity's owned
properties. Match what they own to what each slot requires. Return the fully-scoped
binding. The mantra then fires on the interaction, pulling values from the correct
scope — not from a flat global namespace.

This is not a new concept. The kosha has always declared it. The pipeline has not
yet read it. `sthita-viveka` is the tantra that completes the reading.

---

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-18 | Initial writing — philosophical ground for tantra2 |
| 2026-03-18 | Four new sections added: kosha as prior knowledge (nam recognizes, not computes); tantras as bhave / nam reads in kartari; proof graph reasons in nam's grammar (knower-knowing-known unity); signal purging as recognition completing itself. Groups section rewritten in nam's grammar — relationship as single perception, sthita slots as declaration of what must be perceived together. |
| 2026-03-18 | Layer 2 rewrite completed. Final section added: what the rewrite revealed (agra-bandha as generalizable pattern) and what it opened (sthita-viveka as the next deepening the kosha already declares). 10-layer2-rewrite.md dissolved into this file and removed. |
| 2026-03-18 | Two new sections added from dvandva fix: "The question names the perspective" — solve-for is direction of inquiry, scope entity is viewpoint, the question declares which perspective the graph is read from. "Subject vs modifier — the shashthi-vibhakti signal" — ownership and qualification are distinct structures of knowing; possession signal marks the subject and prevents it from compounding with what it owns. |
