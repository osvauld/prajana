# 17 — Dissolving Hardcoded Tantra Logic into Kosha-Driven Operations

**The working document. Index to the structural plan for what the codebase becomes.**

---

## The Thesis

The pipeline hardcodes what the kosha already declares. 62 hardcoded string
references across 72 tantras. 16 of 32 fireable math operations never fire.
No tantra reads `siddha` edges. The algebraic structures (ring, lattice,
partial-order) declare composition laws that the pipeline re-implements in
tantra code.

**One mechanism** should replace all of it: read the kosha, find the operation,
fire via `apply-op`.

Physics already works this way. Count, viveka, syllogism, transitive reasoning,
and dvandva aggregation should follow the same pattern.

---

## Sub-documents

| File | What | Status |
|------|------|--------|
| [17a-discoveries.md](17a-discoveries.md) | **Reference.** Three core discoveries + 11 trace-verified findings, full math kosha inventory (259 nodes, 4 levels), ten natural tantra groups, performance profile. | Reference |
| [17b-algebraic-types.md](17b-algebraic-types.md) | **Research.** The algebraic hierarchy (field -> ring -> group -> set) as a type system for operations. How varga-inheritance works and where it breaks. Five concrete integration points: count dispatch, dvandva, inverse math, transitivity, mantra narrowing. | Research |
| [17c-implementation.md](17c-implementation.md) | **Plan.** 12 steps (10 original + 1b, 1c). Phase 1 (connect math kosha), Phase 2 (dissolve monolith), Phase 3 (new thoughts), Phase 4 (performance). Xfail mapping. Verification commands per step. | **Active** |

---

## Current State

**HISTORICAL** — this document and its sub-documents (17a, 17b, 17c) are superseded by:
- [18-philosophy.md](18-philosophy.md) — insights and discoveries
- [18-implementation.md](18-implementation.md) — current implementation plan

**Final baseline:** 78 passed / 39 xfailed / 0 failed (session 19)
All steps through 2.5 complete. See changelog.md for details.

| Step | What | Status |
|------|------|--------|
| 1 | Fix emit-triples alias bug (85 words, 3 nodes) | **DONE** |
| 3 | viveka-ganana → apply-op "max"/"min" | **DONE** |
| 1d | grade-sparsha sentence partitioning (graded-ring) | **DONE** |
| 1c | Common-sense event shabda table + vriddhi/kshaya | **DONE** |
| 1e | BQG last-satya viraam reset | **DONE** |
| **2** | **count-chain rewrite via kosha fold** | **NEXT** |
| 2a | Set operation runtime primitives | Pending |
| 4 | derive-chain → DAG walk + match-first | Pending |
| 5 | anumana-viveka → scan-ref loop | Pending |
| 6 | Dissolve anuvada-ganana (swarupa-driven dispatch) | Pending |
| 7 | viveka-derive (per-entity derive + max) | Pending |
| 8 | dvandva-ganana (distributivity + fold(sum)) | Pending |
| 9 | krama-viveka (partial-order → transitive) | Pending |
| 10 | anumana-ganana (logic ops + premise graph construction) | Pending |
| 1b | sankhya-bandha number-before-noun | **DEFERRED** |

**Best case: 17 xfails promoted, 31 → 14.**

---

## The Structural Principle

### Sparsha -> Viveka -> Bandha at every scale

**Inside a tantra:** scan perceives, cond discriminates, emit binds.
**Across tantras:** perception group -> comparison group -> refinement group.
**Across the pipeline:** anuvada-ganana sequences perceive -> discriminate -> bind.

Every tantra should be one complete cycle. The equation tantras (12 lines each)
are the template.

### The algebra is not decorative

`ring --[kriya]--> addition, multiplication` declares valid operations.
`distributivity --[kriya]--> [multiplication, addition]` declares the dvandva pattern.
`partial-order --[siddha]--> transitive` declares A>B ^ B>C -> A>C.
`monoid --[drishthanta]--> addition` guarantees fold is well-defined.

These are structural properties the pipeline can USE -- to validate compositions,
optimize operation order, or choose between equivalent paths. See [17b](17b-algebraic-types.md).

### walk-in IS the type system

`walk-in "mass" "janya"` returns every mantra that needs mass as input.
The janya edges ARE type declarations. The walk IS the type checker.
The graph doesn't need a separate index because the edges ARE the index.

---

## What Has Changed

| Date | Session | Event |
|------|---------|-------|
| 2026-03-19 | 9 | Document created. Five scan-ref patterns. 22 xfails mapped. |
| 2026-03-19 | 10 | Rewritten. Architecture-driven plan. Ten groups. Four phases. |
| 2026-03-19 | 11 | Consolidated with tool-verified observations. Full math inventory. |
| 2026-03-20 | 12 | **Split into 17/17a/17b/17c.** New: algebraic structures research (17b). This file is now the index. |
| 2026-03-20 | 13 | **shabda tool built + plan revised.** `python3 -m tools shabda` unifies .om inline + .shabda file analysis. Live tracing revealed: alias bug scope = 85 words (not just "many"), sankhya-bandha can't bind number-before-noun, 12+ event verbs unmapped. Steps 1b+1c added as prerequisites for Step 2. |
| 2026-03-20 | 17 | **1c DONE, 1e DONE, 1b DEFERRED, plan reordered.** Event verb shabda table (32 verbs → kshaya/vriddhi). BQG last-satya viraam reset. vriddhi/kshaya kriya edges on 9 operations (addition→vriddhi was missing). 1b deferred — blocks nothing, "2 more came" reveals container semantics needed. Set operation gap: 6 tantras use inline, kosha nodes have wrong eval values. Step 2a added. Step 2 unblocked. |
