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
  compound resolution         ✓ done — "kinetic energy" → kinetic-energy
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

**Baseline: 358 passed / 18 xfailed / 0 failing.**

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

When the solve-for target is an input (not an output) of a mantra — "find mass
given KE=250 and velocity=10" — the mantra fires in reverse.

The `pratipaksha` edges on each operation node encode the inverse operation:
- `square` → `pratipaksha-0: sqrt`
- `multiplication` → `pratipaksha-0: div` (solve for arg0)
- `multiplication` → `pratipaksha-1: div` (solve for arg1)
- `subtraction` → `pratipaksha-0: add`, `pratipaksha-1: sub`

Walking the expression subgraph top-down, applying pratipaksha at each op,
isolates the unknown without any per-formula authored inverse.
One generic `invert-expr` works for all mantras. Not yet built (P8e).

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

| Date | What shifted |
|------|-------------|
| 2026-03-16 | Initial writing — synthesized from nyaya-plan.md P8a–P8b.6, scene-understanding.md |
| 2026-03-16 | Baseline updated to 346/8. Chain via rashi instances confirmed working. Session architecture added. |
| 2026-03-16 | emit-triples rashi-label guard implemented. Baseline 355/19xfail/2xpass. |
