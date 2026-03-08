# Prabandam Starlight Documentation Plan

Status: Draft v1.0  
Owner: OpenCode + user  
Scope: Build a multi-file, math-first documentation system (Prabandam) for the graph+tantra engine using Starlight with KaTeX notation support.

---

## Intention

This documentation is not marketing copy. It is a verifiable technical prabandam.

Primary thesis:
- The system is **predictable** because behavior is derived from explicit graph structure, relation algebra, and query-time equations.
- It is **not** an opaque neural black box. No LLM inference compute is required for core graph reasoning.
- It is **math-grounded**: priors, conductance, PPR posterior, and beam blending are all explicit.
- It is **engineering-applicable** for robotics and real-world modeling because relations, constraints, and transformations are inspectable and editable as data.

---

## Root Claim Chain (Mula-Pratijna)

All downstream behavior rests on explicit root nodes:

- `brahma` -> `/home/abe/agent_x/brahman/sangati/brahma.om`
- `om` -> `/home/abe/agent_x/brahman/sangati/om.om`
- `spanda` -> `/home/abe/agent_x/brahman/sangati/spanda.om`
- `karma` -> `/home/abe/agent_x/brahman/sangati/karma.om`
- `brahmam` -> `/home/abe/agent_x/brahman/sangati/brahmam.om`
- `brahman` -> `/home/abe/agent_x/brahman/sangati/brahman.om`

Documentation must treat these as claim anchors, not prose decoration.

---

## Scientific Model Statement (for docs front page)

The engine has two levels of truth handling:

1. **Static declarative prior**
   - Node structure and relation properties from `.om` files.
   - Base relation conductance from `vp_satya_weight` in `brahman/kosha/yantra/visheshanam/*.om`.
   - Node prior score `raw_satya` from local topology.

2. **Dynamic query-time posterior**
   - Seed-conditioned conductance boost.
   - Query-conditioned depth affinity.
   - Personalized PageRank score landscape.
   - Beam selection using blended score.

Therefore: the model is neither static-only nor heuristic-only. It is deterministic structure + dynamic equations.

---

## Equations That Must Be Shown (KaTeX)

From `proof_graph.ml` and resolver logic:

1. Raw satya prior:

\[
s=\frac{\text{sloka\_count}}{1+\text{sloka\_count}},\quad
e=\frac{\text{edge\_count}}{1+\text{edge\_count}},\quad
d=\frac{\text{type\_diversity}}{1+\text{type\_diversity}}
\]

\[
\sigma(n)=\begin{cases}
s\cdot 0.5,& \text{if edge\_count}=0\\
(s\cdot e\cdot d)^{1/3},& \text{otherwise}
\end{cases}
\]

2. Seed-conditioned relation conductance:

\[
f_r=\frac{\#(r\text{ in seed edges})}{\max(1,\#\text{seed edges})},\qquad
\kappa_r=w_r\,(1+f_r)
\]

3. Depth affinity:

\[
\phi=\operatorname{clamp}_{[0,1]}\left(
\left(
\text{binding\_density}\cdot\text{link\_ratio}\cdot\text{computational\_ratio}
\right)^{1/3}
\right)
\]

4. PPR recurrence (`alpha=0.30`):

\[
p_{t+1}(v)=\alpha s(v) + (1-\alpha)\sum_{u\to v}
\frac{p_t(u)\,\kappa_{rel(u,v)}}{\max(1,\text{out\_cond}(u))}
\]

5. Beam blend:

\[
\text{depth\_score}=\frac{1}{d+1},\qquad
\text{blend}=ppr\cdot(1-\phi)+\text{depth\_score}\cdot\phi
\]

---

## Documentation Architecture (Starlight)

Target docs root: `prabandam/`

Proposed page tree (20 pages):

1. `index.md`
2. `pravesha/build-and-run.md`
3. `pravesha/first-queries.md`
4. `pravesha/terminology-and-notation.md`
5. `tattva/system-overview.md`
6. `tattva/sangati-kosha-yantra-layer-model.md`
7. `tattva/satya-and-avrti.md`
8. `tattva/anuvada-fold-and-resolution.md`
9. `tattva/tantra-pipeline.md`
10. `rachana/om-node-spec.md`
11. `rachana/shabda-and-english-bridge.md`
12. `rachana/tantra-authoring-spec.md`
13. `rachana/layer-governance-and-migration.md`
14. `prayoga/regression-and-verification.md`
15. `prayoga/sessions-and-graph-viz.md`
16. `reference/relation-types.md`
17. `reference/equations-appendix.md`
18. `reference/worked-traces/index.md`
19. `reference/worked-traces/life-query.md`
20. `reference/worked-traces/computation-query.md`

Additional generation track pages:

21. `prayoga/music-generation-from-graph.md`
22. `prayoga/code-generation-from-graph.md`
23. `prayoga/programming-with-tantra.md`
24. `reference/worked-traces/music-strudel-trace.md`
25. `reference/worked-traces/codegen-trace.md`

---

## Phase Plan (Exploration-first, then writing)

### Phase 0 — Canonical Claims Lock
Goal:
- Freeze root claims and exact source references.

Exploration:
- Read root files in `brahman/sangati/` and doctrine plan (`firstness-rank-and-brahmam.md`).

Output:
- `claims/root-claims.md` draft notes (internal) and source map.

Gate:
- Every claim maps to a file path and line-snippet; no uncited metaphysical statement.

### Phase 1 — Formula Extraction Lock
Goal:
- Extract all equations from implementation and normalize notation.

Exploration:
- `vyakarana/lib/proof_graph.ml`, `vyakarana/lib/yantra_resolver.ml`, `vyakarana/lib/yantra_eval_primitives.ml`.

Output:
- Equation sheet + symbol table (`alpha`, `sigma`, `kappa`, `phi`, `p_t`).

Gate:
- Every equation has source path and variable-name correspondence.

### Phase 2 — Starlight + KaTeX Setup
Goal:
- Establish rendering substrate for scientific notation.

Build steps:
- Create Starlight site in `prabandam/`.
- Add `remark-math` and `rehype-katex`.
- Import KaTeX CSS.

Gate:
- A sample page renders inline math (`$...$`) and block math (`$$...$$`) correctly.

### Phase 3 — Core Structural Pages
Goal:
- Write foundational pages that explain layers, data model, and pipeline.

Exploration for each page:
- Re-read referenced source files immediately before writing.

Gate:
- Each page includes:
  - at least 3 file references,
  - at least 1 equation block,
  - at least 2 testable claims.

### Phase 4 — Scoring & Predictability Pages
Goal:
- Explain why outcomes are predictable and auditable.

Content:
- raw prior vs dynamic posterior,
- relation weights vs seed-conditioned boost,
- beam blending and intent-conditioned tiers.

Gate:
- Include one numeric worked example with real node/relation values.

### Phase 5 — Worked Traces
Goal:
- End-to-end proof by execution.

Trace set:
- `what is force`
- `kinetic energy when mass is 5 and velocity is 6`
- `force when mass is 10`
- `what is life`

Gate:
- Each trace shows: input -> token/classify -> intent -> resolution path -> final output.

### Phase 6 — Robotics Applicability Chapter
Goal:
- Connect graph+tantra architecture to robotics modeling use-cases.

Topics:
- state-transition modeling as explicit relations,
- controllable inference paths,
- explainable world models,
- deterministic safety constraints,
- symbolic+numeric hybrid planning.

Gate:
- Must avoid vague claims; each robotics claim tied to an existing mechanism in code.

### Phase 6b — Music + Code Generation Chapters
Goal:
- Document how graph structure is turned into executable artifacts (music patterns and source code).

Exploration:
- `vyakarana/lib/prayoga.ml`
- `vyakarana/lib/prayoga_strudel.ml`
- `vyakarana/lib/anuvada.ml` (strudel + ocaml emission sections)
- setu maps loaded via `Setu.read_shabda` (e.g., `strudel`, `swara-to-strudel`, `ocaml-setu`).

Content requirements:
- Explain the data-driven generation principle: no hardcoded domain tables; mapping comes from graph shabda nodes.
- Explain `music_ir` and `strudel` emission paths.
- Explain code emission path for OCaml/Lua-style generation via setu forms.
- Include one trace where concept walk generates strudel stack.
- Include one trace where concept walk generates code file.

Gate:
- Each generated artifact chapter must include:
  - source function references,
  - input concept set,
  - output artifact,
  - deterministic replay command.

### Phase 7 — Governance + Drift Control
Goal:
- Keep docs and implementation synchronized.

Output:
- Drift checklist and invariant list.

Gate:
- Every page ends with “validated against” file list and date.

---

## Quality Bar for Every Page

Required sections:
1. Purpose
2. Mechanism
3. Equations
4. Trace/Example
5. Verify it yourself
6. Source files

Hard constraints:
- No unsupported claim.
- No formula without source provenance.
- No terminology drift (`swarupa`, `abheda`, `sthita`, etc. must stay consistent).

---

## Starlight + KaTeX Implementation Checklist

1. Initialize Starlight app under `prabandam/`.
2. Install:
   - `remark-math`
   - `rehype-katex`
   - `katex`
3. Wire Astro markdown config with math plugins.
4. Import KaTeX stylesheet globally.
5. Add notation conventions page before writing technical chapters.

---

## Risks and Mitigations

Risk 1: docs drift from implementation
- Mitigation: page-level source references + validation date.

Risk 2: math notation diverges across pages
- Mitigation: single canonical symbol table in appendix.

Risk 3: over-claiming predictability
- Mitigation: every predictability claim backed by executable trace.

Risk 4: confusion between static weights and dynamic scoring
- Mitigation: separate dedicated page “Prior vs Posterior” with explicit equations.

---

## Immediate Next Step

Execute Phase 2 first (Starlight + KaTeX scaffold), then write Phase 3 core pages in this order:
1. `tattva/system-overview.md`
2. `tattva/sangati-kosha-yantra-layer-model.md`
3. `tattva/tantra-pipeline.md`
4. `reference/equations-appendix.md`

Only after these are stable proceed to traces, generation chapters, and robotics chapter.
