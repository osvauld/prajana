# Linguistic Graph & NLP Plan — Index

**Status**: P0–P6c done. P7 (tokeniser tantra) is next.

## Key decisions (quick reference)

- `kaala.om` IS the tense parent. Tense values use `-kaala` suffix.
- Three IS-A edges: `swarupa` (identity), `vishesa` (particular of universal), `amsha` (member of set).
- Sangati cluster anchors use `-sthalam` suffix. Members point UP via `X-sthalam-sthita`. Thin anchors only.
- Engine nodes belong in `brahman/kosha/engine/` — NOT sangati.
- Kosha cluster nodes use `-varga` suffix. Pure organisational anchors.
- Directory structure IS the inheritance topology.
- `domain-X-sthita` on leaves replaced by `X-varga-vishesa`.
- Math uses `structures/` + `properties/` + `operations/` subdirs.
- `lakshana` is the math property edge suffix.
- `krama` IS a registered dynamic dimension.
- Mantra nodes: any kosha node with `krama` + `implication` IS a mantra node.
- Mantra node = formula + sentence + question. Same structure, three directions.
- Sangati roots (~50 nodes) ARE the atomic vocabulary.
- Grammar composition is a second pass: krama chain → narrative → grammar → sentence.
- The engine is self-describing: its own operations are nodes in the graph it walks.
- `domain-X-sthita` references in OCaml: leave for now (non-blocking).
- Strudel / music_ir / resonance_ir removed from OCaml — add back later as tantras.

## Files in this directory

| File | Contents |
|---|---|
| [architecture.md](architecture.md) | Three-layer model, bhave-prayoga principle, domain splits |
| [inheritance.md](inheritance.md) | Varga/vishesa/amsha system, full varga hierarchy, subdir pattern |
| [grammar.md](grammar.md) | Sanskrit grammar nodes: kaala, vibhakti, prayoga, vachana, purusa |
| [kosha-nodes.md](kosha-nodes.md) | Bhave process nodes + subanta quantity nodes catalog |
| [bhasha-english.md](bhasha-english.md) | English bhasha layer — sangati root vocab (~50 nodes) + grammar layer |
| [shabda-extraction.md](shabda-extraction.md) | Shabda inheritance, lookup chain, extraction pipeline |
| [phase-2.9-math.md](phase-2.9-math.md) | Math kosha restructure — DONE |
| [phase-cs-restructure.md](phase-cs-restructure.md) | CS kosha restructure — not started |
| [migration-status.md](migration-status.md) | What is done, what is not done, full phase sequence |
| [engine-tantra-migration.md](engine-tantra-migration.md) | OCaml → tantra migration map |
| [graph-native-computation.md](graph-native-computation.md) | Graph edges ARE the formula. Walk = execution. |
| [graded-morphisms.md](graded-morphisms.md) | degree: + pratipaksha on operation nodes |
| [graph-computation-tantras.md](graph-computation-tantras.md) | compute-from-node, execute-chain, scene-walk, compose-degrees |
| [mantra-nodes.md](mantra-nodes.md) | krama + pratipaksha + kriya edges. yantra_inverter.ml removal path. |
| [scene-understanding.md](scene-understanding.md) | End-to-end pipeline. Worked examples. |
| [composition-pipeline.md](composition-pipeline.md) | decompose-question → match-formula → execute-chain → compose-response |
| [question-graph.md](question-graph.md) | **NEW** — sentence as graph fragment. Stateful reduce builds partial mantra instantiation. Replaces P8 pipeline. |
| [session-graph.md](session-graph.md) | **NEW** — session as persistent graph. Compute vs theoretical routing. Formal proof via implication walk. Dialogue generation when slots unfilled. |
| [tantra-testing.md](tantra-testing.md) | Tantra-native testing plan — test categories, runner design |

## Regression baseline

49/52 passing. 3 pre-existing failures. Do not break further.

```
vyakarana/scripts/run-regression.sh
```

## Key source files

```
vyakarana/lib/proof_graph.ml           dynamic visheshanam registry, walk_inheritance, raw_satya
vyakarana/lib/om_parser.ml             decompose_compound, expand_dir (bhasha fix done)
vyakarana/lib/setu.ml                  read_shabda, raw_shabda_for_node, merge_shabda_priority
vyakarana/lib/setu_classify.ml         classify_token — TARGET FOR TANTRA MIGRATION (P7)
vyakarana/lib/yantra_eval.ml           tantra evaluator
vyakarana/lib/yantra_eval_primitives.ml  primitives; split primitive to add at P7
vyakarana/lib/yantra_pipeline_ops.ml   tokenise + session ops — tokenise to migrate at P7
vyakarana/lib/yantra_resolver.ml       chain_resolve BFS+PPR — TARGET FOR REMOVAL (P8.5)
vyakarana/lib/yantra_inverter.ml       symbolic algebra — TARGET FOR REMOVAL (P8.5)
vyakarana/lib/anuvada.ml               query/answer layer (strudel/IR removed)
brahman/kosha/yantra/visheshanam/visheshanam-ring.om  krama-yukta already present
brahman/bhasha/                        surface language forms (P6 complete)
```

---

## Full Priority Stack

### DONE: P0–P6c

| Phase | What | Status |
|---|---|---|
| P0 | Tantra dead-code cleanup | ✅ |
| P1 | setu.ml forwarding aliases | ✅ |
| P2 | Higher-order tantra VFn wrapping | ✅ |
| P3 | New primitives: in-degree, out-degree, neighbors, walk-chain, resolve-node | ✅ |
| P4 | Semantic tantras: has-domain, resolve-node, infer-inputs, infer-outputs, domain-of-seeds | ✅ |
| P4.5 | krama dimension in ring + sangati krama.om | ✅ |
| P5 | Math kosha full restructure | ✅ |
| P5 remaining | compose-degrees.tantra, is-identity-composition.tantra, operation word: keys | ✅ |
| P5.5 | Physics mantra shabda cleanup (name:, krama-lhs-unit:) | ✅ |
| P6a | ~50 sangati root bhasha nodes in `brahman/bhasha/english/` | ✅ |
| P6b | Grammar composition layer (copula.om, articles.om, prepositions.om, conjunctions.om) | ✅ |
| P6c | Implication edges on all 21 physics mantra nodes | ✅ |

### DONE: Strudel / IR removal

| What | Status |
|---|---|
| `build_music_ir`, `build_resonance_ir`, `emit_strudel_*` removed from `anuvada.ml` | ✅ |
| `qr_music_ir`, `qr_resonance_ir`, `qr_strudel` removed from `query_result` | ✅ |
| `show_strudel`, `show_music`, `show_resonance` removed from `output_flags` | ✅ |
| `socket.ml` strudel/IR lines removed | ✅ |
| Build clean, 49/52 passing | ✅ |

---

### P7 — Tokeniser tantra (NEXT)

Replace the OCaml tokenise char-loop + `setu_classify.ml` + `classify-fold` pipeline
with a single `tokenise-question.tantra`. Space is the only hard OCaml boundary.
Everything else is graph-native.

**Token types produced:**
- `{intent, "solve-for"}` — from question words (what, find, calculate)
- `{intent, "define"}` — from "what is X" with no values
- `{value-unit, value, unit-node}` — from `5kg`, `3m/s`, `9.8m/s²`
- `{concept, node-name}` — from graph node lookup (O(1) via bhasha word: key)
- `{grammar, role}` — from grammar role nodes (article, preposition, copula)
- `{unknown, word}` — fallback

**What collapses:**
- `yantra_tokenise` OCaml char loop → `split sentence " "` primitive (one line)
- `setu_classify.ml` (143 lines) → removed entirely
- `classify-fold.tantra` + `classify-fold-resolve.tantra` → merged into tokenise-question
- `setu-classify-token.tantra` → replaced

**New OCaml primitive needed:** `split` (string → separator → list) — already exists.

**Design:**
```
tantra tokenise-question
  inputs
    sentence  string
  let
    words    = split sentence " "
    tokens   = map words (fn w -> classify-word w)
    merged   = fold-forward tokens
  return
    tokens  list
done
```

Where `classify-word`:
1. Matches digit prefix + alpha suffix → value-unit pair (matra-beeja lookup)
2. Pure number → `{number, value}`
3. Graph node by name → `{concept, node-name}`
4. Bhasha `word:` key match → `{concept, node-name}` (O(1))
5. Grammar role → `{grammar, role}`
6. Otherwise → `{unknown, word}`

`fold-forward` handles compound merges (e.g. "kinetic energy" → one concept token).

---

### P8 — Composition pipeline tantras

**Depends on**: P7 (tokeniser), P6b (grammar connectives), P6c (implication edges done).

**Full spec**: `composition-pipeline.md`

New tantras:
- `decompose-question.tantra` — token list → intent + anchor nodes + value bindings
- `match-formula.tantra` — implication walk → formula candidates → coverage check
- `compose-response.tantra` — formula + result + grammar context → sentence
- `invert-mantra.tantra` — reads krama-lhs/rhs → symbolic inversion (replaces yantra_inverter)
- `chain-implication.tantra` — multi-step inference chain walk

---

### P8.5 — yantra_resolver.ml + yantra_inverter.ml removal

**Depends on**: P8 (match-formula + invert-mantra working).

Once `match-formula` walks `implication` edges, `chain_resolve` BFS is redundant.
Once `invert-mantra` handles symbolic inversion via graph structure, `invert_chain` in OCaml is redundant.

Steps:
1. `resolve-direct` in `yantra_pipeline_ops.ml`: thin shim → call `match-formula.tantra`
2. `chain_resolve` in `yantra_resolver.ml`: thin shim → call `match-formula.tantra`
3. Remove `invert_chain` calls once all inversions covered by `invert-mantra`
4. Remove `yantra_resolver.ml` + `yantra_inverter.ml` from `lib/dune`

Gate: 49/52.

---

### P9 — Testing

All test categories from `tantra-testing.md`. Implementation order:

```
Phase 1 (now, unblocked):
  brahman/yantra/tests/primitives/    -- add, mul, sqrt, split, map, filter, etc.
  brahman/yantra/tests/math/          -- degree fields, pratipaksha, compose-degrees
  brahman/yantra/tests/grammar/       -- copula:, word: keys on grammar nodes
  brahman/yantra/tests/graph/         -- walk, ancestors-of, shabda lookups
  brahman/yantra/tests/bhasha/        -- bhasha nodes load, layer weight

Phase 2 (after P7):
  brahman/yantra/tests/mantra/        -- execute-chain on physics mantra nodes

Phase 3 (after P8):
  brahman/yantra/tests/pipeline/      -- full decompose→match→execute→compose
  brahman/yantra/tests/inference/     -- chain-implication, inverse resolution
  brahman/yantra/tests/logic/         -- implication/theorem/proof node structure
```

New runner: `vyakarana/scripts/run-tantra-tests.sh`
Each test tantra returns `bool`. Runner calls `EVAL test-name brahman/` and checks `true`.

---

### P10 — CS kosha restructure

Full details in `phase-cs-restructure.md`. Not started.

---

## What changes in execution with full pipeline

| Path | Before | After |
|---|---|---|
| Tokenisation | OCaml char loop + classify pipeline | `tokenise-question.tantra` one pass |
| Formula matching | BFS beam search in `yantra_resolver.ml` | `match-formula.tantra` implication walk |
| Inverse resolution | `invert_chain` OCaml AST | `invert-mantra.tantra` krama structure walk |
| Response sentence | hardcoded templates | `compose-response.tantra` grammar + krama narrative |
| Testing | shell expected-output `.test` files | tantra tests returning `bool` |
| Strudel / IR | OCaml IR builders | tantras (future, when needed) |
