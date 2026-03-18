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

## Groups — when understanding requires more than one thing at once

Some understanding cannot be had of a single thing. Gravitational force is not a
property of mass A alone, nor of mass B alone. It is a property of the pair (A, B)
at distance r. The understanding requires the group.

This is what group theory in the kosha captures. A tinanta (interaction node) has
`sthita` slots — required member-scopes. `gravitational-force` has
`particle-a-sthita` and `particle-b-sthita`. These are not just inputs to a
formula. They are the declaration that this understanding requires two members.
The group IS the understanding.

The pipeline currently doesn't read this. It looks for `mass` and `radius` as
flat concepts. When two balls are present, each with their own mass, the flat
lookup fails — it finds two masses and doesn't know which belongs to which slot.

`sthita-viveka` is the tantra that reads the slot structure — it takes the
interaction node and the question graph and finds which entity fills each slot,
then walks that entity's owned properties to find the value. The group is resolved.
The interaction fires on the pair, not on either individual.

`sambandha-viveka` is one level above: given co-present entities, it finds which
interactions are possible. It answers "what groups can be formed here?" before
even asking "what is the value?" This is the discovery step — the moment when
understanding notices that two things together constitute a new kind of thing.

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

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-18 | Initial writing — philosophical ground for tantra2 |
