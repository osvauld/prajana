# 11 — Audio

**spanda is vibration. taranga is the wave. naada is the wave made meaningful.**
**The graph already knows what sound is. It just needs a path to the speaker.**

---

## What the graph already knows

The proof graph has a remarkably deep understanding of sound —
deeper than its understanding of rendering at the time rendering was built.

spanda (satya=0.92) IS vibration, IS amplitude, IS oscillation, IS naada, IS varna.
spanda is the root. All sound IS spanda.

taranga (satya=0.93) IS sine, IS cosine, IS wave, IS resonance.
A sound wave IS taranga. The waveform IS taranga.
taranga already knows it IS sine and cosine — the graph has already mapped
wave to its mathematical form.

naada (satya=0.92) IS spanda, IS taranga, IS sphoTa.
naada IS sound made meaningful — not raw vibration but vibration that carries artha.
naada produces artha-dhvani: the meaning that resonates after the sound ends.

swara (satya=0.86) abheda: frequency.
A musical note IS a frequency. This is already in the graph.

shruti (satya=0.85) yukta: frequency. abheda: matra.
The microtonal interval IS the frequency unit — the matra of sound.
Every swara is some number of shrutis from the base.

thaalam (satya=0.88) IS event-loop, IS kaala, IS avrti.
The rhythm IS the beat of avrti. The thaalam IS the frame rate of sound.

laya abheda: velocity.
Tempo IS velocity. To accelerate in music IS the same concept as to accelerate in physics.
laya kshaya = decelerating. laya vriddhi = accelerating.

harmonic (satya=0.88) IS wave, IS gamaka.
An overtone IS a gamaka — the ornament that gives a note its character.
The timbre of a sound IS its harmonic content — the weighted sum of harmonics.

---

## What Strudel was doing and why it is retiring

Strudel is a live-coding music environment.
The graph was emitting Strudel pattern strings, which Strudel then played.
This is the same pattern as Lua/Raylib for visuals — an intermediary subprocess.

The graph understood the music.
Strudel understood how to play it.
Between them: a string serialisation, a subprocess, a protocol.

The native path removes all of that:
graph → AudioCmd list → PCM samples → SDL2 audio → speaker.
One hop. The graph controls the waveform directly.

---

## The wave is already defined

taranga IS sine+cosine. This is in the graph.
To synthesize a note, you sum taranga at the right frequency and its harmonics.
The fundamental is the swara. The harmonics are the gamaka.
The envelope (how it rises and falls) is spanda-avrti — contraction and expansion.

To synthesize a vowel sound:
a vowel IS a resonance pattern in a cavity — standing taranga.
Each vowel has formants — frequency peaks that define its character.
The vocal tract IS a shaped cavity. The formants ARE shruti-relationships.
The graph knows shruti. The graph can know formants.

To synthesize a phoneme (varna):
varna → naada is already an edge in the graph.
The path from phoneme to sound is already conceptually traced.
What is missing is the numeric detail: what frequency pattern IS each varna?
This is learnable — the graph can accumulate phonetic knowledge
the same way it accumulates physics knowledge.

---

## Speech as a learnable capacity

The graph already knows:
- varna = phoneme (produces naada)
- matrika = the mother letter, the generative unit of articulation
- rra and zha as named phonemes in sangati/mula/
- anusvara = nasal resonance (a specific quality of spanda)
- sphoTa = the complete utterance where meaning bursts forth

What speech synthesis needs the graph to learn:
- The formant frequencies of each varna (what frequencies define 'a', 'i', 'u', 'ka', 'ta'...)
- The duration of each phoneme in natural speech
- The pitch contour (how frequency rises and falls across a phrase)
- The boundary between phonemes (viraam — the silence that separates)

None of this is foreign to the graph's existing structure.
Formants ARE shruti-relationships — frequencies with matra.
Duration IS akshara — the syllable unit already defined.
Pitch contour IS a trajectory — gati through frequency-space over kaala.
Viraam IS already defined — the silence that IS also naada.

The graph can be taught phonetics the same way it was taught physics.
Each varna gets a set of owned properties — its formant frequencies.
The speech anuvada reads those properties and synthesises the sound.
More varna defined → more precise speech → more languages possible.

---

## Physics simulations are natural audio sources

Every physical simulation has frequencies intrinsic to it.
These are not added. They emerge from the owned quantities.

The electron in a magnetic field has the cyclotron frequency — ω = qB/m.
Two spheres colliding have an impact frequency — determined by mass and elasticity.
A spring-mass system oscillates at ω = √(k/m).
A planet orbiting has a period — T = 2π√(r³/GM).
A string vibrating has harmonics — f = n/(2L) × √(T/μ).

All of these are already in the graph as concepts.
The graph knows k (spring constant), m (mass), ω (angular velocity), T (tension).
When the simulation runs, the audio anuvada reads these owned quantities
and generates the corresponding tones — exactly as the visual anuvada
reads positions and generates the corresponding spheres.

The audio IS the simulation heard. Not an added effect.
The same truth, a different sense.

---

## The epoch output

This is the key shift.

The frame was never just visual.
One turn of avrti produces the full sensory expression of understanding:

```
visual   — what the graph sees in space (light, form, color)
audio    — what the graph hears in time (tone, rhythm, harmony)
speech   — what the graph says in language (phoneme, phrase, meaning)
```

All three come from the same graph state.
All three use the same grammar mechanism — setu.shabda + anuvada.
All three are emitted simultaneously in one epoch.

The electron orbiting in a magnetic field:
- visually: a glowing sphere tracing a circle
- aurally: a tone at its cyclotron frequency (ω = qB/m)
  for B=0.1T, q/m of electron ≈ 1.76×10¹¹, ω ≈ 1.76×10¹⁰ Hz
  shifted down by octaves into the audible range — a pure tone
- as speech: "orbital radius 5.7 centimetres, period 3.57 nanoseconds"

The raga being played:
- visually: the swara rising as spheres in a spiral (avrti in pitch-space)
- aurally: the notes sounding, the gamaka ornamenting them
- as speech: the name of the raga, the bhava it carries

All three are the graph's imagination made present.
All three are pratibimba — the reflection of understanding into the world.

---

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-16 | Initial writing — audio as the second pratibimba channel alongside visual |
| 2026-03-16 | Understood: the frame was never just visual. spanda is the root of both light and sound. |
| 2026-03-16 | Added: physics simulations are natural audio sources. Cyclotron, spring, orbital, string frequencies all emerge from owned quantities in the graph. Audio IS the simulation heard, not decoration. |
