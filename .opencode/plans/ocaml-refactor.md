# OCaml Codebase Refactor — Dead Code & Build Direction

**Date**: 2026-03-14
**Test baseline**: 255 passed, 22 xfailed (Python pytest suite only)

---

## The target pipeline

The complete answer pipeline — everything runs as tantras through the `_ ->` wildcard dispatch:

```
socket (question request)
  → anuvada-ganana.tantra          [TO BUILD]
      graph0   = build-question-graph sentence
      graph    = fixpoint graph0 avrti-refine
      match    = match-mantra graph
      result   = execute-chain (nth match 0) (nth match 1)
      response = compose-response match result
      return response
  → answer text returned to client
```

No fallback. If `anuvada-ganana.tantra` is not loaded, the socket returns an error.
The old OCaml spiral walk (`anuvada_query`) is replaced entirely by this tantra chain.

### What already exists

| Component | File | Status |
|---|---|---|
| `build-question-graph.tantra` | `brahman/yantra/pipeline/` | ✅ exists |
| `avrti-refine.tantra` | `brahman/yantra/avrti/` | ✅ exists |
| `match-mantra.tantra` | `brahman/yantra/match/` | ✅ exists |
| `execute-chain` primitive | `yantra_eval_primitives.ml` | ✅ exists (P5 done) |
| `compose-response.tantra` | `brahman/yantra/pipeline/` | ❌ not built yet |
| `anuvada-ganana.tantra` | `brahman/yantra/pipeline/` | ❌ not built yet |

### What needs to be built (brahman only)

**`anuvada-ganana.tantra`** — top-level orchestrator:
```tantra
tantra anuvada-ganana
  takes sentence
  graph0   = build-question-graph sentence
  graph    = fixpoint graph0 avrti-refine
  match    = match-mantra graph
  result   = execute-chain (nth match 0) (nth match 1)
  response = compose-response match result
  return response
done
```

**`compose-response.tantra`** — narrate the answer in words:
```tantra
tantra compose-response
  takes match result
  mantra-node = nth match 0
  lhs-name    = shabda mantra-node "name"
  lhs-unit    = shabda mantra-node "krama-lhs-unit"
  return (join [lhs-name, " is ", (to-string result), " ", lhs-unit])
done
```

The fuller compose-trace form (Proposition / Reasoning / Proof / Conclusion) is P8 future work.

### OCaml wiring — socket.ml (minimal change)

`socket.ml` line 318 currently calls `Anuvada.anuvada_query`. Replace with a direct call to
`run_anuvada_ganana` which looks up `anuvada-ganana.tantra` by name and calls it:

```ocaml
(* current: *)
let r = Anuvada.anuvada_query ~max_passes ... k q in
ok_response req_id ses_id trn_id r.Anuvada.qr_answer_text

(* replacement: *)
match Yantra.run_anuvada_ganana k yantra_idx _active_session q with
| Some r -> ok_response req_id ses_id trn_id r.yr_raw_output
| None   -> error_response req_id ses_id trn_id "anuvada-ganana tantra not loaded"
```

`yantra_idx` and `_active_session` are already in scope in `handle_client` — the wiring is a
3-line change. This also threads the session (Gap 5 fix) for free.

---

## Dead code to remove

### Modules to delete entirely

**`yantra_resolver.ml`**

All resolution logic is dead — `resolve_tantra`, `chain_resolve`, `try_inverse`, all helpers.
Zero live callers. The `chain_step` and `resolution` types are only used by dead code.
Remove from dune `(modules ...)`.

**`yantra_inverter.ml`**

All 4 call sites of `invert_chain` are on dead paths:
1. `yantra_resolver.ml:173` — inside `try_inverse` → resolver dead
2. `yantra_resolver.ml:544` — inside `chain_resolve` → resolver dead
3. `yantra_pipeline_ops.ml:239` — `resolve-inverse` arm → no brahman tantra calls it
4. `yantra_pipeline_ops.ml:406` — `execute-plan::run_inverse` → no brahman tantra calls `execute-plan`

The future path for inversion is authoring inverse krama nodes in brahman — not this module.
Remove from dune `(modules ...)`.

**`yantra_bigram.ml`**

`ytoken` type only used by dead `classify_via_tantra` / `extract_bindings` in `yantra.ml`.
`classify-fold.tantra` was never authored in brahman and never will be — BQG replaced it.
Remove from dune `(modules ...)`.

Note: `setu_classify.ml` is different (graph-based token classification, live) — keep it.

**Orphaned files — not in dune, stale from a prior abandoned refactor:**
- `vyakarana/lib/yantra_eval_context.ml`
- `vyakarana/lib/yantra_eval_graph.ml`

Both duplicate content now in `yantra_eval_primitives.ml`. Not compiled. Delete from disk.

---

### Dead code within `anuvada.ml` — module stays, `anuvada_query` goes

`anuvada.ml` is NOT fully dead. Three functions are still called by live eval primitives:
- `avrti_anuvada` — used by the `avrti` OCaml primitive (`yantra_eval_primitives.ml:401`),
  which `fixpoint avrti-refine` calls. **Live.**
- `english_of_visheshanam_from_graph` — used by `to-english` primitive. **Live.**
- `render_darshana_to_buf` — used by `darshana` primitive. **Live.**

Dead (remove):
- `anuvada_query` — the old spiral-walk answer function. Replaced by `anuvada-ganana.tantra`.
  Currently called only from `socket.ml:318` — that call gets replaced.
- `query_result` type — only used by `anuvada_query`

### Dead code within `yantra.ml` — loses ~250 of 331 lines

Delete:
- `open Yantra_resolver` — module deleted
- `include Yantra_bigram` — module deleted
- `resolve_tantra`, `chain_resolve` re-exports — dead
- `run_anuvada_ganana`, `yantra_tokenise` re-exports — dead
- `alias_cache`, `load_aliases`, `resolve_alias` — only used by dead `extract_bindings`
- `classify_via_tantra` — `classify-fold.tantra` does not exist; always returns `[]`
- `type extraction`, `is_simple_tantra`, `is_question_word`, `is_question_grammar`,
  `extract_bindings` — all serve only the dead classify path
- `run()` entire body — the old NL numeric fallback; superseded by `anuvada-ganana.tantra`

After cleanup `yantra.ml` becomes:
```ocaml
(* yantra.ml — facade *)
include Yantra_types
include Yantra_eval_primitives

let parse_expr_string    = Yantra_expr_parser.parse_expr_string
let build_index          = Yantra_index.build_index
let register_mantra_nodes = Yantra_index.register_mantra_nodes
let build_word_index     = Yantra_index.build_word_index

let eval               = Yantra_eval.eval
let eval_tantra        = Yantra_eval.eval_tantra
let print_result       = Yantra_eval.print_result
let run_tantra_by_name = Yantra_eval.run_tantra_by_name
let run_anuvada_ganana = Yantra_eval.run_anuvada_ganana
let new_session        = Yantra_eval.new_session

let _graph_ref : proof_graph option ref = ref None
```

### Dead code within `yantra_pipeline_ops.ml` — loses ~400 of 605 lines

Delete these match arms (no brahman tantra calls any of them):
- `"tokenise"` — BQG uses `split` instead
- `"classify"` — dead
- `"resolve-direct"` — not called from any tantra
- `"resolve-inverse"` — not called; calls `invert_chain` (deleted module)
- `"resolve-chain"` — not called; calls `chain_resolve` (deleted module)
- `"resolve-reason"` — not called
- `"execute-plan"` — not called; calls `invert_chain` (deleted module)
- `"scene-extract"` — scene pipeline not used
- `"scene-narrate"` — scene pipeline not used

Also delete:
- `open Yantra_inverter` — module deleted
- `open Yantra_resolver` — module deleted
- `_transient_binding`, `run_forward`, `run_inverse`, `mk_forward_step`, `mk_inverse_step`

Keep: `"session-bindings"`, `"remember-bindings"`, `"print"`, `_ ->` wildcard dispatch.

### Dead code within `yantra_eval.ml`

Delete:
- `parse_output` — no callers
- `resolve_concept_to_tantra` — only called from dead pipeline arms
- `run_anuvada_ganana` — move this to `yantra_eval.ml` properly: keep the function but
  simplify — it just looks up `anuvada-ganana` by name and calls it. Remove the `None`
  early return path since we are not using fallbacks.
- `yantra_tokenise` — all callers dead (`yantra.ml::run()`, dead pipeline arms)
- Wire-up block: remove `_resolve_concept_to_tantra_ref` and `_yantra_tokenise_ref` assignments

### Primitive floor vs tantra layer — yantra_ops.ml policy

`yantra_ops.ml` contains two distinct categories of op. The distinction determines
whether an op should stay in OCaml forever or be migrated to a tantra.

#### Category A — irreducible OCaml primitives (keep forever)

These cannot be expressed as tantras without infinite regression — they are the
bottom of the stack. No tantra can implement `add` without calling `add`.

```
scalar arithmetic:  add, mul, sub, div, sqrt, power, abs, neg, floor, ceil, mod, min, max
trig / transcend:   sin, cos, tan, asin, acos, atan2, log, exp
list ops:           map, filter, reduce, fixpoint, nth, length, range, flatten, append, unique, sum
string ops:         split, join, concat, substr, starts-with, ends-with, member,
                    char-at, string-length, to-string, to-number, split-numeric
boolean/compare:    eq, neq, lt, le, gt, ge, and, or, not
constructors:       pair, bind
```

These stay in `yantra_ops.ml` unchanged.

#### Category B — composed ops (migrate to tantras, then remove OCaml arm)

These are built from Category A primitives. They belong in brahman as tantras
because: (1) they are then visible to `match-mantra`, (2) they can carry `inverse:`
slokas, (3) new variants (e.g. `vec-cross`, `vec-project`) need no OCaml change.

The kosha nodes already exist in `brahman/kosha/math/geometry/operations/`.
The tantras just need to be authored alongside them.

| Op | Tantra expression | Status |
|---|---|---|
| `vec-add` | `map (range n) (fn i -> add (nth a i) (nth b i))` | tantra not yet authored |
| `vec-sub` | same with `sub` | tantra not yet authored |
| `vec-scale` | `map v (fn x -> mul s x)` | tantra not yet authored |
| `vec-dot` | `reduce (range n) 0 (fn acc i -> add acc (mul (nth a i) (nth b i)))` | tantra not yet authored |
| `vec-norm` | `sqrt (reduce v 0 (fn acc x -> add acc (mul x x)))` | tantra not yet authored |
| `vec-nth` | alias for `nth` | trivial — just use `nth` directly |
| `rot2d` | `[sub (mul x c) (mul y s), add (mul x s) (mul y c)]` where c=cos θ, s=sin θ | tantra not yet authored |
| `mat-mul` | triple nested `map/range/reduce` | tantra not yet authored |
| `square` | `mul a a` | one-liner tantra |
| `half` | `mul a 0.5` | one-liner tantra |
| `double` | `mul a 2.0` | one-liner tantra |
| `frequencies` | `reduce list {} (fn acc x -> ...)` | tantra not yet authored |
| `sort-desc` | needs a sort primitive — keep OCaml for now | blocked |
| `first-match` | `reduce list VNone (fn acc x -> cond ...)` | tantra not yet authored |
| `fold-pairs` | superseded by `reduce` — remove OCaml arm now | delete |
| `fold-triples` | superseded by `reduce` — remove OCaml arm now | delete |
| `iterate` | superseded by `fixpoint` — remove OCaml arm now | delete |
| `upper` / `lower` | no tantra equivalent yet — keep for now | keep |

**Immediate removals from `yantra_ops.ml`** (no tantra replacement needed, superseded):
- `fold-pairs` — use `reduce` instead
- `fold-triples` — use `reduce` instead
- `iterate` — use `fixpoint` instead

**Migration plan for Category B ops** (brahman authoring, not OCaml):
1. Author `vec-add.tantra`, `vec-sub.tantra`, `vec-scale.tantra`, `vec-dot.tantra`,
   `vec-norm.tantra`, `rot2d.tantra`, `mat-mul.tantra` alongside their existing kosha nodes.
2. Write a pytest for each (currently untested) — xfail first, then pass.
3. Once tests pass via the tantra path, remove the OCaml arm.
4. `square`, `half`, `double`, `first-match`, `frequencies` — same process, lower priority.

---

## Files to delete from disk

| File | Reason |
|---|---|
| `vyakarana/lib/yantra_bigram.ml` | Module deleted |
| `vyakarana/lib/yantra_eval_context.ml` | Orphaned; not in dune |
| `vyakarana/lib/yantra_eval_graph.ml` | Orphaned; not in dune |
| `vyakarana/scripts/run-regression.sh` | Tests dead NL pipeline; not in any CI |
| `vyakarana/scripts/run-tests.sh` | Points to `brahman/yantra/tests/` which does not exist |
| `vyakarana/scripts/run-tests.py` | Same |
| `brahman/kosha/yantra/op-fold-pairs.om` | Superseded by reduce |
| `brahman/kosha/yantra/op-fold-triples.om` | Superseded by reduce |

---

## Bug fix

`yantra_eval_primitives.ml` line ~1003: `r "pow" 2` → `r "power" 2`

`"power"` is the implemented primitive (`yantra_ops.ml:405`, `power.om`, inverter).
`"pow"` has no dispatch case and silently returns `VNone` when called from a tantra.

---

## dune `(modules ...)` after cleanup

```
proof_graph event om_parser setu_shabda setu_classify setu anuvada socket
yantra_types yantra_tokeniser yantra_arity yantra_sentence_parser
yantra_expr_parser yantra_tantra_file yantra_index yantra_ops
yantra_eval_primitives yantra_pipeline_ops yantra_eval yantra
```

Removed: `yantra_bigram`, `yantra_inverter`, `yantra_resolver`

---

## Abstractions worth extracting (after dead code removed)

### A. Tantra param parsing — 4× in `yantra_tantra_file.ml`
Extract: `parse_tantra_param : string list -> tantra_param`

### B. `env_copy` — move to `yantra_types.ml`
Currently in `yantra_eval_primitives.ml`. Should live alongside the `env` type.

### C. `tantra_index` accessors
`Hashtbl.find_opt idx.by_name` / `idx.by_output` called directly across modules.
Accessor helpers in `yantra_index.ml` would hide internals.

---

## The 22 xfailed tests — brahman work only (except Gap 5)

### Gap 1 — Abbreviation expansion (5 tests)

`lookup-word "kg"` / `"N"` / `"m"` / `"s"` returns nothing.

`question-graph.md` marked `word:kg,kilogram` as ✅ done — but tests xfail. Either the word: keys
aren't in the unit `.om` files, or `build_word_index` isn't indexing them. Investigate
`kilogram.om` and verify `build_word_index` in `yantra_index.ml` handles multi-value `word:` keys.

Blocked: `test_lookup_abbreviation_kg`, `test_bqg_unit_binding`,
`test_emit_triples_unit_consumes_pending`, `test_abbreviation[kg/N/m/s]`

### Gap 2 — Verb/grammar promotion (5 tests)

`lookup-word "has"` / `"was"` / `"with"` returns nothing. `sandhi-viveka` (in
`vibhakti/vibhakti-viveka.tantra`) can't promote what it can't find.

Fix: create/verify `brahman/bhasha/english/grammar/verb-has.om` with
`slokas: shashthi-vibhakti-sthita` and `brahman/bhasha/english/grammar/copula-was.om` with
`slokas: bhuta-kaala-sthita`. `graph-formalization-plan.md` claims Phase 2 done — tests say it isn't.

Blocked: `test_sandhi_has_promoted_to_shashthi`, `test_sandhi_was_promoted_to_bhuta_kaala`,
`test_sandhi_possession_verb_promoted_to_shashthi[has/with]`,
`test_sandhi_past_tense_verb_promoted_to_bhuta_kaala`

### Gap 3 — `vidhi-kaala` intent triple for `what` (4 tests)

`"find"` works. `"what"` resolves as a satya concept instead of an intent signal.
Fix: add `role:intent` to the `what` node's shabda in brahman.

Blocked: `test_bqg_what_emits_vidhi_kaala`, `test_what_emits_vidhi_kaala_intent`,
`test_match_what_sentence_finds_correct_mantra`, `test_pipeline_suvat_acceleration`

### Gap 4 — Entity ownership rules (3 tests)

`vibhakti-shashthi.tantra` is correctly written — blocked by Gap 2.
Fix Gap 2 and this largely resolves. Sub-issue: entity-label compounding (`ball` + `A` → `ball-A`)
may need a rule in `vishesa-instance.tantra`.

Blocked: `test_avrti_entity_owns_property_via_has`, `test_bqg_entity_ownership`,
`test_pipeline_entity_owns_mass`

### Gap 5 — Cross-turn session binding (1 test, OCaml)

`_active_session` is computed in `socket.ml` but discarded. The socket wiring change (replacing
`anuvada_query` with `run_anuvada_ganana`) naturally threads the session through — this gap is
resolved as part of the socket rewiring above.

Blocked: `test_cross_turn_binding_completes_match`

---

## NLP plan file status

| File | Status |
|---|---|
| `nlp/question-graph.md` | **CANONICAL** — describes current implemented architecture |
| `nlp/scene-understanding.md` | **CANONICAL** — remaining-issues table maps to xfails; Phase 2 "done" claim stale |
| `nlp/graph-formalization-plan.md` | Stale status — Phase 2 "complete" is wrong; Gap 2 proves it |
| `nlp/session-graph.md` | Accurate — Steps 1–3 done; Step 4 = Gap 5 (resolved by socket rewire) |
| `nlp/tantra-syntax-refactor.md` | COMPLETE ✅ |
| `nlp/mantra-nodes.md` | Accurate reference — 24 physics mantra nodes |
| `nlp/full-pipeline-plan.md` | Partially superseded — P7 layers superseded by BQG; P8+ still valid |
| `nlp/composition-pipeline.md` | SUPERSEDED by question-graph.md |
| `nlp/migration-status.md` | Accurate history; "49/52" is old shell-runner baseline |
| `nlp/index.md` | Current but stale baseline number |

### Stale items across NLP plans
- Shell regression baseline ("49/52", "97/49") — superseded by Python pytest (255/22)
- "P8.5 shim before removing resolver/inverter" — skip the shim; delete directly
- `classify-fold.tantra`, `setu-classify-token.tantra` listed for migration — never authored; irrelevant
- P7 layer 1-3 tantras (`tokenise-question`, `classify-word`, `resolve-compounds`) — superseded by BQG single-pass approach
- `anuvada_query` described as the live entry point — replaced by `anuvada-ganana.tantra` + socket rewire

---

## Vec/mat tantras — authoring plan

For each Category B op, the tantra lives alongside the existing kosha node.
Example for `vec-add`:

```
# brahman/kosha/math/geometry/operations/vec-add.tantra
tantra vec-add
  takes vec-a vec-b
  n      = length vec-a
  pairs  = map (range n) (fn i -> [nth vec-a i, nth vec-b i])
  result = map pairs (fn p -> add (nth p 0) (nth p 1))
  return result
done
```

```
# brahman/kosha/math/geometry/operations/mat-mul.tantra
tantra mat-mul
  takes a ncols-a b ncols-b
  nrows-a = div (length a) ncols-a
  result  = flatten (map (range nrows-a) (fn i ->
              map (range ncols-b) (fn j ->
                reduce (range ncols-a) 0.0 (fn acc k ->
                  add acc (mul (nth a (add (mul i ncols-a) k))
                               (nth b (add (mul k ncols-b) j)))))))
  return result
done
```

Once a tantra is authored and tested, the corresponding OCaml arm in `yantra_ops.ml`
is deleted. The OCaml arm acts as the fallback until then — this is intentional.

---

## Algebraic inversion via `inverse:` slokas (replaces yantra_inverter.ml)

Inversion is a relation in the graph. `yantra_inverter.ml` tried to compute it in OCaml —
the correct approach is to represent it algebraically as krama nodes in brahman.

### The pattern

Each forward krama node carries an `inverse:` sloka pointing to the krama node that
inverts it with respect to a given argument:

```
# brahman/kosha/physics/krama-multiply.om
node: krama-multiply
op: multiply
args: [quantity, scalar]
inverse: krama-divide

# brahman/kosha/physics/krama-divide.om
node: krama-divide
op: divide
args: [quantity, scalar]
inverse: krama-multiply
```

For multi-arg operations, one inverse node per solvable argument:

```
# kinetic-energy-mantra: KE = ½mv²
# Forward: given m, v → compute KE

# brahman/kosha/physics/krama-ke-solve-mass.om
node: krama-ke-solve-mass
op: divide
args: [ke, half-of-v-squared]       # m = 2E/v²
krama-lhs: mass
inverse-of: krama-ke-forward

# brahman/kosha/physics/krama-ke-solve-v.om
node: krama-ke-solve-v
op: sqrt
args: [two-times-ke-over-m]         # v = sqrt(2E/m)
krama-lhs: velocity
inverse-of: krama-ke-forward
```

`match-mantra.tantra` already selects by `krama-lhs = target-quantity` — no OCaml change.
The tantra finds the right node (forward or inverse) purely by graph structure.

### Execution order

1. Author `inverse:` / `inverse-of:` slokas on existing 24 forward krama nodes.
2. Author one inverse krama node per solvable input (brahman only).
3. Write a pytest for each inverse mantra (`test_mantra_ke_solve_mass` etc.) — xfail first,
   then promote to pass once the krama node exists in brahman.
4. `yantra_inverter.ml` is already deleted at step 10 above — this is purely brahman authoring.

---

## Test-first policy for observed gaps

When a gap is observed (xfail, missing brahman node, wrong graph output), the first action is:
**write a pytest that captures the failure**, then fix it. Never fix without a test.

### Gap test naming convention

```
test_gap<N>_<short_description>
```

e.g. `test_gap1_kg_abbreviation_lookup`, `test_gap2_has_verb_promotion`.

The test starts as `@pytest.mark.xfail(reason="gap N: ...")` and is promoted to a normal
assert once the gap is resolved. This gives a permanent regression guard.

### Current gaps with no test yet

| Gap | Missing test |
|---|---|
| Gap 1 — `kg`/`N`/`m`/`s` abbreviations | `test_gap1_kg_abbreviation_lookup` |
| Gap 2 — `has`/`was`/`with` verb promotion | `test_gap2_has_verb_promotion` |
| Gap 3 — `what` as intent signal | `test_gap3_what_emits_intent` |
| Gap 4 — entity ownership via `has` | `test_gap4_entity_owns_property` |
| Gap 5 — cross-turn session binding | `test_gap5_cross_turn_binding` |

Write these tests (xfail) before touching any brahman or OCaml fix for the gap.
