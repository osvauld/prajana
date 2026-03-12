# Migration Status

## Done

### Phase 0 — Shabda Inheritance
`walk_inheritance`, `raw_shabda_for_node`, `merge_shabda_priority`

### Phase 0.5 — Bhasha Layer Recognition
`om_parser.ml` recognizes `bhasha` header

### Phase 0.6 — Bhasha Satya Weighting
`raw_satya` applies `*. 0.5` for `"bhasha"` layer

### Phase 1 — Ring Extension
7 new dims added to `visheshanam-ring.om`:
`ahara-yukta dhatu-yukta vrnda-yukta kala-yukta prayoga-yukta vachana-yukta purusa-yukta`

### Phase 1.5 — Sangati Grammar Nodes
48 files written in `brahman/sangati/grammar/`:
- tense: vartamana-kaala, bhuta-kaala, bhavishya-kaala, vidhi-kaala, sambhavana-kaala
- voice: kartari-prayoga, karmani-prayoga, bhave-prayoga
- number: eka-vachana, dvi-vachana, bahu-vachana
- person: prathama-purusa, madhyama-purusa, uttama-purusa
- vibhakti: prathama through saptami + sambodhana
- pada: subanta, tinanta, avyaya, nipata, upasarga
- pratyaya: shatr, kta, tvaa, tumun
- samasa: tatpurusha, karmadharaya, dvandva, bahuvrihi

### Phase 2 — Kosha Process Nodes
- Annotated existing physics process nodes with bhave-prayoga-swarupa tinanta-swarupa subanta-swarupa
- 21 new process nodes created
- 525 kosha headers corrected sangati→kosha
- aarambham/abhava/niyama moved to brahman/sangati/

### Phase 2.5 — Kosha Varga Nodes + Inheritance Restructure
- vishesa and amsha added to visheshanam-ring.om; walk_inheritance updated
- All domain varga nodes created (physics, math, cs, chemistry, biology, etc.)
- Physics/math/cs subdomain vargas created
- Full physics kosha subdir restructure complete
- All domain-physics-sthita removed from leaves
- Sangati fixes on matra.om, sambandha.om, prasarana.om

### Phase 2.6 — Sangati Subdir Restructure
Full restructure of brahman/sangati/ from 263 flat files into hierarchy:
mula/ spanda/ parampara/ jiva/ bhava/ chetan/ vak/ grammar/ geometry/
Sthalam nodes rewritten as thin anchors (direction flipped to upward).
**Regression: 49/52 — same 3 pre-existing failures.**

### Bhasha migration
- brahman/bhasha/ocaml/   — 30 files, headers → bhasha
- brahman/bhasha/lua/     — 12 files, headers → bhasha
- brahman/bhasha/strudel/ — 6 files, headers → bhasha
- brahman/bhasha/render/  — 5 files, headers → bhasha
- _migration/kosha-language/ — 138 English language files kept as reference

### Loader fix
om_parser.ml expand_dir handles both kosha and bhasha subdirs.

### Phase 5 — Math Kosha Restructure (COMPLETE)
Full structure: algebra/ geometry/ calculus/ number/ set/ graph/ logic/ probability/ complexity/
CS information/ upgrade + bit.om upgraded
compose-degrees.tantra written
is-identity-composition.tantra written
Core math operation word: keys written (half, double, mul, div, add, sub, square, sqrt, power)
Pratipaksha edges on operation pairs (square↔square-root, derivative↔antiderivative, etc.)
Degree enrichment on number/geometry/calculus operations

### Phase 5.5 — Physics Mantra Shabda Cleanup (COMPLETE)
All 22 physics mantra nodes updated: name: + krama-lhs-unit: fields.
Hyphenated descriptions removed.

### Phase 6a — Sangati Root Bhasha Forms (COMPLETE)
All ~50 sangati root bhasha nodes in brahman/bhasha/english/

Original 31 (sangati root → English filename):
ahara→input, anu→element, anuvada→translation, avrti→iteration, dvaya→pair,
kaala→time, kriya→action, kshaya→decay, matra→quantity, nyaya→logic,
phala→result, pramana→proof, prasarana→extension, pratishedha→negation,
prayojana→purpose, rachana→composition, sama→equal, sambandha→relation,
samsarga→combination, sangati→truth, sankshepa→summary, sparsha→contact,
spanda→motion, sthiti→state, swa→self, swatantra→independent,
vakya→sentence, vidya→knowledge, vriddhi→growth, vrnda→collection, english

Final 15 added:
shakha→branch, seema→boundary, niyama→rule, satya→true, purna→complete,
svabhava→inherent, niralamba→foundational, taranga→wave, kona→angle,
viparita→inverse, eka→one, dvandva→dual, chala→variable,
parampara→sequence, ananta→infinite

### Phase 6b — Grammar Composition Layer (COMPLETE)
brahman/bhasha/english/grammar/:
- copula.om — is/are/was/were/equals/gives + copula nodes
- articles.om — a/an/the
- prepositions.om — of/by/per/from/over/at
- conjunctions.om — and/or/given/where
Kaala nodes updated with copula: and word: keys.

### Phase 6c — Implication Edges (COMPLETE)
All 21 physics mantra nodes carry implication-sthita edges.
These replace the BFS beam search in yantra_resolver.ml for formula matching.

### Strudel / IR Removal (COMPLETE)
Removed from anuvada.ml (1388 → ~530 lines):
- build_music_ir, build_resonance_ir, emit_strudel_from_graph, emit_strudel_to_string, emit_ir
- renderer_voice type, note_of_node, satya_to_gain, build_voices
- thaalam_context, js_str/js_float/js_int/js_bool helpers
- qr_music_ir, qr_resonance_ir, qr_strudel from query_result
- show_strudel, show_music, show_resonance from output_flags
- socket.ml strudel/IR JSON lines
Build clean. 49/52 passing.
Will add back as tantras later when needed.

---

## Not Yet Done

### Phase 7 — Tokeniser Tantra (NEXT)

Replace:
- yantra_tokenise (OCaml char loop in yantra_eval.ml)
- setu_classify.ml (143 lines)
- classify-fold.tantra + classify-fold-resolve.tantra
- setu-classify-token.tantra

With:
- tokenise-question.tantra — single pass, space boundary, graph-native classification

Token output format:
```
{intent, "solve-for"}
{value-unit, 5.0, "kilogram"}
{concept, "kinetic-energy"}
{grammar, "vartamana-kaala"}
{unknown, "word"}
```

New primitive needed in OCaml: none (split already exists).
setu_classify.ml removable after this phase.

### Phase 8 — Composition Pipeline Tantras

Depends on: P7 (tokeniser), P6b (grammar layer done), P6c (implication edges done).

New tantras:
- decompose-question.tantra
- match-formula.tantra
- compose-response.tantra
- invert-mantra.tantra
- chain-implication.tantra

Full spec in composition-pipeline.md.

### Phase 8.5 — yantra_resolver.ml + yantra_inverter.ml Removal

Depends on: P8 working.

1. resolve-direct in yantra_pipeline_ops.ml → shim to match-formula.tantra
2. chain_resolve in yantra_resolver.ml → shim to match-formula.tantra
3. Remove invert_chain calls once all inversions covered
4. Remove yantra_resolver.ml + yantra_inverter.ml from lib/dune

Gate: 49/52.

### Phase 9 — Testing

Tantra-native tests in brahman/yantra/tests/

Phase 1 (unblocked now):
- tests/primitives/  — basic OCaml primitive correctness
- tests/math/        — degree fields, pratipaksha, compose-degrees
- tests/grammar/     — copula: and word: keys on grammar nodes
- tests/graph/       — walk, ancestors-of, shabda lookups on known nodes
- tests/bhasha/      — bhasha nodes load correctly, satya weight = 0.5x

Phase 2 (after P7):
- tests/mantra/      — execute-chain on all 21 physics mantra nodes

Phase 3 (after P8):
- tests/pipeline/    — full decompose→match→execute→compose
- tests/inference/   — chain-implication, inverse via pratipaksha
- tests/logic/       — implication/theorem/proof node structure

New runner: vyakarana/scripts/run-tantra-tests.sh
Each test returns bool. Runner checks true.
Combined target: all tantra tests pass + 49/52 shell tests.

### Phase 10 — CS Kosha Restructure

Full details in phase-cs-restructure.md. Not started.

### Remaining non-blocking items

- Trig function word: keys (sin, cos, tan, asin, acos, atan) — 6 nodes
- Algebra/set/graph/probability/complexity degree enrichment — ~26 nodes
- cardinality.om + bijection.om in number/properties/ — 2 nodes
- Phase 2.7: brahman/engine/ → brahman/kosha/engine/ move
- Phase 2.8: collatz to kosha/math/number/structures/
- domain-X-sthita in OCaml (setu.ml, anuvada.ml) — leave for now, non-blocking

---

## Pre-existing test failures (3 — do not fix, do not worsen)

Regression target is always 49/52.
