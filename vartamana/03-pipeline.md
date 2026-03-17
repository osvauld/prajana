# 03 — The Pipeline

**The pipeline is not a transformation sequence. It is an accumulation.
Each stage reads the graph state the previous stage left. Nothing is discarded.**

---

## The movement: expansion → connection → compression

Every question passes through one movement with three phases:

**Expansion** — the English sentence unfolds. Words become nodes. Relationships
become typed edges. The surface (dhvani) is dissolved into structure (artha).
This is artha-viveka: meaning-discernment, not compression.

**Connection** — the expanded graph connects to the kosha. Satya nodes surface
their domain. PPR over the kosha pulls in the mantras and related concepts that
are structurally connected. The implication network attaches.

**Compression** — everything that can be resolved collapses. Avrti runs to
fixpoint. Mithya resolves to satya. The graph reaches its minimal, internally
consistent, dhvani-free form.

The result is sphoTa — the whole meaning, surface-free, arrived whole.
Not assembled from parts. The triple graph IS sphoTa made traversable.

---

## What is done — the working pipeline

```
English sentence
  ↓
build-question-graph          ✓ done — word-by-word stateful reduce → triple graph
  sandhi-viveka               ✓ done — grammar promotion (has→shashthi, was→bhuta-kaala)
  emit-triples                ✓ done — word → satya/mithya; rashi-label guard (word≠node)
  find-context                ✓ done — tracks active concept, pending number

  ↓ avrti-refine (fixpoint)
  compound resolution         ✓ done — Way 1: mithya+satya "kinetic energy" → kinetic-energy
                                     Way 2: satya+satya "mass density" → mass-density,
                                             "photon energy" → photon-energy
  avastha resolution          ✓ done — "initial velocity" → velocity+bhuta-kaala
  rashi-viveka                ✓ done — "v1 of 20" → rashi instance with sankhya
  vishesa-bandhana            ✓ done — [v1, vishesa, velocity] binding
  rashi-anuvada               ✓ done — instance sankhya → concept level sankhya
  sankhya-bandha              ✓ done — number binds to active concept

  ↓
kosha-expand (PPR)            ✓ done — satya nodes as seeds → relevant kosha structure

  ↓
match-mantra                  ✓ done — find mantra whose janya are all covered
  if found → execute          ✓ done — forward computation via krama
  if not found → derive-step  ✓ done — fire intermediate mantras to build toward target
    → match-mantra again      ✓ done — chained derivation

  ↓
anuvada                       ✓ done — result → English answer text
```

**Baseline: see [changelog.md](changelog.md).**

---

## The pipeline order that matters

The key decision made in P8b.6:

```
WRONG (old): avrti → kosha-expand → derive-step (fires ALL) → match-mantra
RIGHT (now): avrti → kosha-expand → match-mantra (ONE, solve-for driven)
                → if no match: derive-step → match-mantra again
```

The system understands first, then matches one target, then executes.
Not: compute everything and pick from the pile.

This means `vidhi-kaala solve-for` is not optional — a sentence with `mass`
and `velocity` but no stated intent is genuinely ambiguous between KE and momentum.
The intent (`find kinetic energy`) resolves the ambiguity before any mantra fires.

---

## Two layers, one structure

Every mantra bridges two layers simultaneously:

**Sankhya layer** — numeric computation. `mass=5, velocity=10 → KE=250`.
The value lands as `[kinetic-energy, sankhya, 250.]`.

**Satya (nyaya) layer** — not yet built (P8c). When the sankhya layer produces
a result, it simultaneously establishes a truth: `kinetic-energy-known`. This
satya phala becomes available as janya for logical mantras. Logical questions
("can energy be negative?", "does conservation hold?") are answered by chaining
satya phalas through nyaya mantras.

The physics/logic split is surface only. The graph unifies them.
Both layers use identical edge vocabulary: janya/phala/krama/sthita.

---

## Inversion — finding the unknown

When the solve-for target is an input (not an output) of a mantra — "find
current given voltage=5 and resistance=10" — the mantra fires in reverse.

**The math kosha already encodes all inversions.** Every arithmetic operation
node has `pratipaksha` shabda entries:
- `multiplication` → `pratipaksha-0: div`, `pratipaksha-1: div`
- `division` → `pratipaksha-0: mul`, `pratipaksha-1: div` (+ flip)
- `addition` → `pratipaksha-0: sub`, `pratipaksha-1: sub`
- `subtraction` → `pratipaksha-0: add`, `pratipaksha-1: sub` (+ flip)
- `square` → `pratipaksha-0: sqrt`
- `power` → `pratipaksha-0: logarithm`
- `sine` → `pratipaksha-0: arcsine`, etc.

**The architecture (P8f):** Physics mantras declare which math operation they
use (`shabda math-op:multiplication`). The math operation node knows how to
execute forward (`eval: mul`) and how to invert (`pratipaksha-0: div`).

For simple mantras (`V = IR`, `p = mv`): `invert-math.tantra` reads `math-op`
from the mantra, looks up `pratipaksha-N` for the solve-for janya position,
applies the inverse op with remaining bound values.

For composed mantras (`KE = ½mv²`): the expression subgraph (P8f Phase B)
encodes the composition as graph nodes. `invert-math.tantra` walks the graph
top-down, applying `pratipaksha` at each node, isolating the unknown.

**One generic `invert-math.tantra` works for all mantras.** No per-formula
authored inverse. The math kosha is the algebra engine. Physics mantras are
pure knowledge — no computation code.

This also applies to vector/matrix operations (`vec-scale`, `dot-product`) and
SAS/DSP formulas (`dB = 20×log(gain)`, `τ = RC`, `ω = 2πf`) — all use the
same math kosha nodes with the same `pratipaksha` structure.

---

## The two kinds of questions

**Compute question** — all janya values present, one unknown.
Path: axioms → mantra match → substitution → theorem (number).

**Theoretical question** — no numeric axioms, only conceptual relationships.
Path: implication walk → modus-ponens chain → theorem (derivation).
Not yet built (P8d nyaya-step).

**Chain question** — intermediate derivation needed.
`u=0, a=10, t=3, m=2 → find KE`
→ velocity-mantra fires first (v = u+at = 30)
→ kinetic-energy-mantra fires second (KE = ½mv² = 900)
Chain tests pass for both the direct numeric case and via rashi instances.

---

## What comes after the pipeline

`compose-response` — not yet built (P8 composition-pipeline). Currently the answer
is assembled from a simple OCaml template. The full version reads every graph phase
— axioms stated, mantra matched, implication applied, theorem established — and
produces a reasoning trace: "axioms: mass=5kg, velocity=10m/s. By ke-mantra
(implication). By substitution: KE = ½×5×100 = 250J."

The session graph (05-session.md) extends the pipeline across turns.
`session-anuvada.tantra` is the outer avrti — across turns.
`anuvada-ganana.tantra` is the inner avrti — one sentence. Pure, no session state.

---

## What has changed

For baseline and session progress see [changelog.md](changelog.md).

| Date | What shifted in this doc |
|------|-------------|
| 2026-03-16 | Initial writing — synthesized from nyaya-plan.md P8a–P8b.6, scene-understanding.md |
| 2026-03-17 | Inversion section rewritten. P8e subsumed by P8f. Math kosha pratipaksha algebra documented. |
| 2026-03-17 | Sandhi Way 2 added to pipeline stages. Boot/reboot pass added to startup sequence. |
