# Vartamana Plans — Index

**Root**: `vartamana/`
**Status**: Active
**Theme**: The active understanding of the NLP / Nyaya system — what it is, how it works, where it is going.

vartamana — the present. What is happening now.

This directory absorbs and supersedes `nlp/` and `darshana-plan.md`.
The old `nlp/` files remain for historical reference only.

The sister directory is `pratibimba/` — how the understanding becomes visible and
audible in the world. Read both together for the full picture.

---

## Files

**Read [00-living.md](00-living.md) first.**

| File | What it covers | Status |
|------|---------------|--------|
| [00-living.md](00-living.md) | How to read and update these plans. The living document protocol. | Active |
| [changelog.md](changelog.md) | **Baseline + session changelog. Single source of truth for test counts.** | Active |
| [01-nam.md](01-nam.md) | What nam IS. The proof graph as subject. Swa, viveka, prajna, the four states. | Active |
| [02-graph.md](02-graph.md) | The graph structure. Satya/mithya layers, edge vocabulary, sangati, rashi, mantra. | Active |
| [03-pipeline.md](03-pipeline.md) | The pipeline. BQG → avrti → kosha → match → derive. What is done. The two layers. | Active |
| [04-entities.md](04-entities.md) | Entities in the graph. The five gaps. What is needed for the next phase. | Active |
| [05-session.md](05-session.md) | Superseded — absorbed into 09-adhyayana.md. | Historical |
| [06-next.md](06-next.md) | What is next. xfails, priority order, what is permanently deferred. | Active |
| [07-tantra-rewrite.md](07-tantra-rewrite.md) | Layer 1/2/3 architecture. Parser tensions. Tantra authoring rules. | Active |
| [08-boot.md](08-boot.md) | Boot/reboot pass architecture. emit-edge, graph-all-nodes, varga-inheritance. | Active |
| [09-adhyayana.md](09-adhyayana.md) | The learning loop. Session as growing understanding. Feedback, correction, prashna. Absorbs 05-session.md. | Active |

---

## The one-line summary of each

- **nam**: the proof graph IS nam. Swa without ahamkara. Viveka always shuddha. Becoming without lacking. Sakshi of this conversation — now addressed directly.
- **graph**: structure IS meaning. Walk the edges and you have understood. The rashi is the quantity instance.
- **pipeline**: expansion → connection → compression = sphoTa. Match first, derive only as fallback.
- **entities**: the entity IS the simulation object. Each turn adds one. The scene accumulates. Gap 1 (unit naming, partially closed) → Gap 2 (session entity structure) → dvandva.
- **adhyayana**: the session IS learning. Three loops: avrti (within sentence), parampara (across turns), pratikara (correction — not yet built). Prashna as output. Instruction as pre-loaded state. Absorbs session doc.
- **next**: Gap 1 (unit label collision, partially closed — 1 xfail remains, test expectation issue) → Gap 2 (session entity structure, 5 xfails, unblocks multi-entity scene) → pratibimba render params → dvandva → P8c.

---

## Key principles (apply across all files)

1. **The graph IS the formula** — janya/krama/phala edges ARE the computation description
2. **Structure IS meaning** — walk the edges and you have understood; no hidden representation
3. **Two layers, one structure** — sankhya (numeric) and satya (truth) use identical edge vocabulary
4. **Mantras bridge layers** — firing produces both numeric phala and truth phala simultaneously
5. **Match first** — understand the intent, match one target mantra, then execute; not compute-all
6. **The session IS a proof** — each question adds axioms and theorems; the session accumulates
7. **Entities own properties** — prathama-vibhakti IS the entity, shashthi-vibhakti IS ownership
8. **Inversion is free** — pratipaksha on the expression graph gives inverse without new mantras
9. **Varga is the imagination frame** — each domain's varga root IS the lens; derive-step respects it
10. **No flat strings for structure** — phala/janya edges are canonical; krama-lhs/rhs strings are transitional
11. **The session IS outer avrti** — session-anuvada is anuvada-ganana's avrti across time; same spiral, larger scale
12. **Prior-graph injects after avrti-refine** — sandhi-bandhana corrupts prior-turn triples if they enter before it; this constraint is permanent
13. **Entity = simulation object** — the rashi structure IS what the renderer reads; prathama-vibhakti finds objects, shashthi-vibhakti finds their properties
14. **Word between satya-concept and rashi-bandha IS a rashi label** — never a unit; `mass m of 5` — `m` is unambiguously an instance label
15. **Rashi label discrimination is `word ≠ node`** — `m` resolves to `metre` (word≠node) → label; `mass` resolves to `mass` (word=node) → concept. The alias/abbreviation test is the correct and sufficient discriminant.
16. **Outer `let` bindings are not visible in `scan ... when` guards** — computed values (e.g. `has-rashi-bandha`) must be threaded into scans as state variables: `let flag be computed-value`.
17. **Satya-named entities need explicit last-label tracking** — `vibhakti-shashthi` only detects entities from mithya words by default; kosha concepts used as entity names (`electron has ...`) require the satya branch to also set `last-label`.

---

## Baseline and changelog

See **[changelog.md](changelog.md)** — single source of truth for test baseline
and session-by-session progress. Do not record baseline numbers anywhere else.
