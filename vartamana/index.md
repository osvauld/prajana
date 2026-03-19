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
| [07-tantra-rewrite.md](07-tantra-rewrite.md) | Layer 1/2/3 architecture. Historical tensions. Now resolved — tantra2 is the canonical form. | Historical |
| [08-boot.md](08-boot.md) | Boot/reboot pass architecture. emit-edge, graph-all-nodes, varga-inheritance. | Active |
| [09-adhyayana.md](09-adhyayana.md) | The learning loop. Session as growing understanding. Feedback, correction, prashna. Absorbs 05-session.md. | Active |
| [11-tantra2-philosophy.md](11-tantra2-philosophy.md) | The grammar of understanding. How humans give meaning to words. Pointing, scope, clarification. Why tantra2 was discovered not designed. What the rewrite revealed and what it opened. | Active |
| [12-tantra2-notation.md](12-tantra2-notation.md) | Every symbol in tantra2 — its English grammar equivalent, Sanskrit root, function in reasoning. The notation as grammar. | Active |
| [13-tantra2-mathematics.md](13-tantra2-mathematics.md) | Monotone endomorphisms. Knaster-Tarski fixpoints. Finite state transducers. Datalog. The Madhava connection. Updates toward prabandham. | Active |
| [14-tantra3.md](14-tantra3.md) | **Tantra3: the om graph as active interface.** The six suffixes as instruction set. Om-driven matching, derive-chain, pipeline ordering. The declaration IS the execution. Supersedes tantra2 as the target architecture. | Active |
| [15-tantra3-implementation.md](15-tantra3-implementation.md) | **Tantra3 implementation plan.** Steps 1+2 complete. All tantra2 deleted. 63 active tantra3 files. Dissolution complete. Baseline: 511 passed / 63 xfailed (session 9). | Reference |
| [16-let-binding-resolution.md](16-let-binding-resolution.md) | **Scan body escape fix.** The file parser's `in_scan_body` flag never reset — every line after a scan header was absorbed. Fix: indentation check (only column-0 lines escape scan body). Completed session 9. | Completed |
| [17-scan-ref-patterns.md](17-scan-ref-patterns.md) | **Working document.** Two discoveries: scan-ref completes the tantra cycle; the math kosha (83 unused nodes) is a library of operations. One mechanism (read kosha → find operation → apply-op) unifies count, viveka, syllogism, transitive, dvandva. Ten natural groups. Nine-step plan: fix alias bug → count-chain → viveka → derive → anumana → dissolve monolith → new thoughts. | **Active** |
| [tantra2-spec.md](tantra2-spec.md) | Technical reference. File structure, expression syntax, scan syntax, safety rules, naming conventions. | Active |

---

## The one-line summary of each

- **nam**: the proof graph IS nam. Swa without ahamkara. Viveka always shuddha. Becoming without lacking. Sakshi of this conversation — now addressed directly.
- **graph**: structure IS meaning. Walk the edges and you have understood. The rashi is the quantity instance.
- **pipeline**: expansion → connection → compression = sphoTa. Match first, derive only as fallback.
- **entities**: the entity IS the simulation object. Each turn adds one. The scene accumulates. Gap 1 (unit naming, partially closed) → Gap 2 (session entity structure) → dvandva.
- **adhyayana**: the session IS learning. Three loops: avrti (within sentence), parampara (across turns), pratikara (correction — not yet built). Prashna as output. Instruction as pre-loaded state. Absorbs session doc.
- **next**: xfails and priority order. Gap 2 (session entity structure) and dvandva (sthita-viveka) are the open work.
- **tantra2-philosophy**: the grammar of understanding. Why the notation was found, not invented. What the Layer 2 rewrite revealed: agra-bandha as the generalizable pattern. What it opened: sthita-viveka as the next deepening.
- **tantra2-notation**: every symbol explained — English grammar, Sanskrit root, function in reasoning.
- **tantra2-mathematics**: the pipeline as monotone endomorphisms, FSTs, Datalog, Madhava series. The proof graph as self-certifying reasoning.
- **tantra3**: the om graph IS the program. 109 nodes already declare janya/phala contracts. The six suffixes form an instruction set. The tantras are manual transcriptions of what the om graph already says — tantra3 eliminates the transcription. Supersedes tantra2 as target.
- **tantra3-implementation**: the engineering companion. 77 xfails classified into 8 categories. 4 steps from om-contract primitive through swarupa-chain. Seven unnamed structures (sankhya-sparsha 16×, shashthi-sparsha 43×, iccha-viveka 9×, pramana-bandha 4×, varga-viveka, eval_arg 72×, with_node 34×) mapped to tantra3 steps. "No match" anatomy: 42/77 xfails produce it, 29 passing tests produce it correctly. Manipravalam: the code speaks the same language as the knowledge. Test cache analysis: 549 cached results, 197 graph traces, performance profile (chain derivations are the bottleneck).
- **scan-ref-patterns (17)**: **active working document.** Two discoveries: scan-ref completes the tantra cycle; math kosha is an unused library of 83 operations. One mechanism (read kosha → find operation → apply-op) for all reasoning types. Physics path is the template. emit-triples alias bug documented. Nine-step plan connecting kosha to pipeline.
- **tantra2-spec**: technical reference. Authoring rules, syntax, safety rules. The working guide for writing new tantras.

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
16. **Scan state is the epistemic position** — typed scan state `[name: type = init-expr]` initialises from outer bindings at scan entry. Each state variable IS the understander's current position: what was last seen, what has been established, what is still open.
17. **Satya-named entities need explicit last-label tracking** — `vibhakti-shashthi` only detects entities from mithya words by default; kosha concepts used as entity names (`electron has ...`) require the satya branch to also set `last-label`.
18. **Agra is the foremost** — proximity binding tracks the most recently seen instance of a concept. Bindings attach to agra. Agra updates forward as new instances arrive. The sequence IS the scope. N entities work because the sentence encodes entity order.
19. **Subanta / tinanta / varga** — the three kinds of kosha nodes. Subanta: a quantity, owned by one entity. Tinanta: a process/interaction, has `sthita` slots and `phala`. Varga: a containment, members via `vishesa` or `varga` edges. The pipeline must read all three kinds, not treat them as flat concepts.
20. **sthita IS the interaction scope** — a tinanta's `sthita` slots are its required member-scopes. The pipeline finds quantities by walking sthita members' owned properties, not by flat concept lookup. This is `sthita-viveka` — the scope-aware lookup that unblocks all multi-entity computation.
21. **The om graph IS the program** — janya/phala/kriya/yukta/sthita/swarupa edges on om nodes are not metadata; they are the complete specification of what each concept needs, produces, does, has, sits in, and IS. The runtime should read these edges directly rather than hardcoding the same logic in tantras. This is tantra3.
22. **Manipravalam — the code speaks the language of the knowledge** — tantra2 translates om declarations into machine operations. Tantra3 eliminates the translation. `om-yukta "rashi"` says the same thing as `"sankhya-yukta"` in the om file — the gem and the coral on one string. Every unnamed structure found by `analyze_pipeline.py` (sankhya-sparsha 16×, shashthi-sparsha 43×, iccha-viveka 9×, pramana-bandha 4×) is a place where tantra code translates what the om graph already says more naturally. Tantra3 is the moment when the code uses the om graph's own names.

---

## Baseline and changelog

See **[changelog.md](changelog.md)** — single source of truth for test baseline
and session-by-session progress. Do not record baseline numbers anywhere else.
