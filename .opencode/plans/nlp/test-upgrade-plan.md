# Test Upgrade Plan

**Status**: COMPLETE. 253 passing, 22 xfailed, 0 failing.
**Supersedes**: `tantra-testing.md` (old true/false tantra approach — archived)
**Date**: 2026-03-14
**Completed**: 2026-03-14

---

## What changed and why

The old design used `.tantra` files that returned `bool`. Every test was a single
pass/fail with no visibility into what went wrong. The runner could only report
`got: 'false'`. After a full audit of the 145 existing tantra tests we found:

- **40 files** are debug scaffolding or language-primitive probes — fossils from
  when the code was being built, not real behavioural specs
- **~20 files** are fragmented: 3 files test the same function call on the same
  input, each checking one property
- **26 files** are known-failure stubs that document missing features — they
  always fail and will continue to fail until the feature is implemented
- The pass/fail logic in `socket.ml` (`result = "true" OR non-empty non-false`)
  was accident-driven: a test returning a raw graph accidentally "passed"

The new design:
- **Python owns the test logic** — pytest, real assertions with error messages
- **Server returns JSON** via the new `eval-json` command (`val_to_json` in OCaml)
- **No new tantra test files** — Python passes tantra expressions inline as strings
  to `vy.eval(...)`. No `test-*.tantra` wrapper files, no `return ok bool` pattern.
- **Production tantras stay** — `sandhi-viveka.tantra`, `avrti-refine.tantra`, etc.
  are called by the pipeline and tested by name from Python. They never go away.
- **`test-*.tantra` files disappear** — they were only ever wrappers computing
  `true`/`false` for the old runner. Python absorbs that assertion logic directly.
- **Tests are grouped by system layer** — when OCaml changes, you know which
  module to run

---

## Infrastructure already in place

| Component | Location | Status |
|---|---|---|
| `val_to_json` in OCaml | `yantra_types.ml` | Done |
| `eval-json` socket command | `socket.ml` | Done |
| Virtualenv | `.venv/` (project root) | Done |
| `vy.py` socket client | `vyakarana/tests/vy.py` | Done |
| `conftest.py` pytest fixture | `vyakarana/tests/conftest.py` | Done |
| `requirements.txt` | `vyakarana/tests/requirements.txt` | Done |
| `sahaja_gloss` fixed | `anuvada.ml` | Done — now reads shabda correctly |

### Running tests

```bash
# start server first
cd vyakarana && ./_build/default/bin/vyakarana.exe --quiet-startup --socket /tmp/vy.sock ../brahman &

# run all tests
cd vyakarana/tests && ../../.venv/bin/pytest -v

# run one module
cd vyakarana/tests && ../../.venv/bin/pytest test_sandhi.py -v

# run with custom socket
cd vyakarana/tests && ../../.venv/bin/pytest --socket /tmp/vy.sock -v
```

### The `vy` fixture

Every test receives a `vy` (Client) instance. Full API:

```python
# eval any tantra expression — returns parsed Python value (list, str, float, bool, None)
result = vy.eval('lookup-word "mass"')                   # "mass"
graph  = vy.eval('build-question-graph "find force"')    # [[...], [...], ...]
val, ms = vy.elapsed_ms('build-question-graph "..."')    # (value, elapsed_ms)

# graph search helpers
triple  = vy.find_triple(graph, pred="satya")            # first match or None
found   = vy.has_triple(graph, subj="mass", pred="sankhya")  # bool
matches = vy.all_triples(graph, pred="shashthi-vibhakti")    # all matches (list)
by_pred = vy.triples_by_pred(graph)                     # {pred: triple} last-wins

# kosha walk helpers — call walk/walk-in, return list of node-name strings
units  = vy.walk("mass", "matra")          # ["kilogram"]
owners = vy.walk_in("kilogram", "matra")   # ["mass"]

# numeric comparison with float tolerance (handles "5." string values from server)
assert vy.approx_eq(triple[2], 5.0)        # abs(float(a) - float(b)) < 1e-3

# session questions (test_session.py only)
answer = vy.ask("what is force", session_id="s1")  # returns answer_text string
```

### What goes in `vy.py` vs inline

| Use case | Where |
|---|---|
| Socket connection, send/receive, retry | `vy.py` — `Client` |
| Triple search (find/has/all/by_pred) | `vy.py` — static methods |
| Walk / walk-in kosha graph | `vy.py` — instance methods |
| Float tolerance comparison | `vy.py` — static `approx_eq` |
| Session questions | `vy.py` — instance `ask` |
| Single-predicate filter: `[t for t in g if t[1] == "satya"]` | inline in test |
| Count triples: `sum(1 for t in g if t[1] == "kosha-janya")` | inline in test |
| Extract values: `[t[2] for t in g if t[1] == "sankhya"]` | inline in test |

### No tantra files for tests — inline expressions only

The old `test-*.tantra` files had this shape:

```tantra
tantra test-has-becomes-shashthi
  let
    graph  = [["has", "mithya", "has"]]
    result = sandhi-viveka graph
    tri    = nth result 0
    ok     = and (eq (nth tri 0) "has") (eq (nth tri 1) "shashthi-vibhakti")
  return ok  bool
done
```

The tantra file existed only because the old runner needed a named file to call.
The assertion logic (`ok = and ...`, `return ok bool`) has zero value — it just
converts a real value into `true`/`false` and throws away the actual data.

The new equivalent is a one-liner passed to `vy.eval`:

```python
def test_verb_has_promoted_to_shashthi(vy):
    result = vy.eval('sandhi-viveka [["has","mithya","has"]]')
    # result is [[subj, pred, obj]] — the real graph, not "true"/"false"
    assert result[0][1] == "shashthi-vibhakti", f"got pred={result[0][1]!r}"
```

Multi-line tantra expressions (let/return blocks) are never needed in tests
because Python can compose sub-expressions:

```python
# instead of: let g = build-question-graph "..." then reduce g false (fn ...)
g = vy.eval('build-question-graph "what is kinetic energy"')
assert vy.has_triple(g, subj="kinetic-energy", pred="satya")
```

**Rule**: if you are about to write a `.tantra` file to support a test, stop.
Write the expression inline in Python. The only tantra files that exist are
production pipeline code called by `anuvada_query` or other pipeline stages.

---

## Test modules — one per system layer

```
vyakarana/tests/
  conftest.py              ← session-scoped vy fixture, --socket CLI arg
  vy.py                    ← Client class, graph helpers
  requirements.txt

  test_interpreter.py      ← yantra evaluator: reduce/map/fn/cond/nth/from/scan/fixpoint
  test_word_index.py       ← lookup-word: direct, abbreviations, morpheme rules, misses
  test_graph_primitives.py ← emit-node, walk, walk-in, edges, register-dimension, node-satya
  test_sandhi.py           ← sandhi-viveka: verb promotion, passthroughs
  test_bqg.py              ← build-question-graph: full tokenisation + triple emission
  test_avrti.py            ← avrti-refine + fixpoint: compound, avastha, entity rules
  test_sankhya.py          ← emit-triples + find-context
  test_kosha.py            ← kosha-expand, PPR, kosha graph traversal
  test_match.py            ← match-mantra: disambiguation, arg ordering, no-match
  test_pipeline.py         ← end-to-end: BQG → avrti → match on full sentences
  test_session.py          ← session isolation, turn counting, multi-turn bindings
```

Each module protects a specific OCaml surface area:

| Module | Protects against regressions in |
|---|---|
| `test_interpreter.py` | `yantra_eval.ml`, `yantra_ops.ml` |
| `test_word_index.py` | word-index loading, morpheme rules in tantras |
| `test_graph_primitives.py` | `proof_graph.ml`, `yantra_eval_graph.ml` |
| `test_sandhi.py` | `sandhi-viveka.tantra` |
| `test_bqg.py` | `build-question-graph.tantra`, `emit-triples.tantra` |
| `test_avrti.py` | `avrti-refine.tantra`, `sandhi-*.tantra` sub-passes |
| `test_sankhya.py` | `emit-triples.tantra`, `find-context.tantra` |
| `test_kosha.py` | `kosha-expand.tantra`, PPR primitive, PPR CSR materialisation |
| `test_match.py` | `match-mantra.tantra` |
| `test_pipeline.py` | full pipeline integration |
| `test_session.py` | `socket.ml` session store, `anuvada_query`, multi-turn |

---

## Naming convention

Test names describe **the behaviour**, not the code path:

```python
# Old (tantra names)
test-bqg-has-concept
test-avrti-compound

# New (behaviour names)
def test_known_concept_word_emits_satya_triple(vy): ...
def test_mithya_prefix_plus_satya_concept_compounds(vy): ...
def test_verb_has_promoted_to_shashthi_vibhakti(vy): ...
```

Parametric cases — same function, varying inputs — use `@pytest.mark.parametrize`:

```python
@pytest.mark.parametrize("word,expected_pred", [
    ("has",  "shashthi-vibhakti"),
    ("with", "shashthi-vibhakti"),
    ("was",  "bhuta-kaala"),
])
def test_grammar_verb_promoted_to_relation(word, expected_pred, vy):
    graph = vy.eval(f'sandhi-viveka [["{word}","mithya","{word}"]]')
    assert graph[0][1] == expected_pred, f"'{word}' → expected {expected_pred}, got {graph[0][1]!r}"
```

Known failures use `@pytest.mark.xfail(strict=True, reason="...")`:
- `strict=True` means if the feature gets implemented and it starts passing,
  pytest will **error** to alert you — forces you to promote it to a real test.

---

## What each module covers

### `test_interpreter.py`

Tests the yantra evaluator in isolation — no domain knowledge needed.

**Existing behaviour to capture:**
- `reduce` over list: string acc, numeric sum, cond-select
- `reduce` over empty list → returns accumulator unchanged
- `map` over list, `map` over empty list → `[]`
- `filter` with predicate
- `nth` on list: in-bounds, out-of-bounds → null, negative → null
- `nth` on VPair: index 0 = name, 1 = value, 2 → null
- `cond` multi-arm, `cond` no match → null/false
- `fn` closure: captures outer binding
- `from … where [pat] and guard collect expr`: all items, empty list, failing guard
- `scan … with state when … emit`: basic accumulation, `otherwise` branch, state persist
- `fixpoint`: terminates on stable graph, terminates on 20-iter cap (non-converging fn)
- `split-numeric`: `"5kg"` → `[5, "kg"]`, `"100"` → `[100, ""]`, `"-5m"` → `[-5, "m"]`, `".5m"` → `[0.5, "m"]`, `"m/s"` → `[null, "m/s"]`
- `ends-with`, `starts-with`, `substr`, `string-length`, `split`
- `to-number`: numeric string → float, non-numeric → null
- `append`, `flatten`, `unique`, `range`, `sum`, `length`
- `eq`, `neq`, `lt`, `gt`, `le`, `ge`, `and`, `or`, `not`
- `add`, `sub`, `mul`, `div` (by zero → 0.0, not crash), `abs`, `sqrt`, `pow`

**New edge cases to add:**
- `reduce` with non-function third arg → returns init
- `fixpoint` with never-converging fn → returns after 20 iters, result non-empty
- `div 5 0` → `0.0` (guarded, no exception)
- `sqrt -1` → `nan` or `null` (IEEE special value handling)
- `nth [] 0` → null (empty list)
- `split-numeric` with leading minus: `"-5kg"` → `[-5, "kg"]`
- `from [] where [x] collect x` → `[]` (empty list, no crash)

### `test_word_index.py`

Tests `lookup-word` which reads from `ctx_index.word_index` built at load time.

**Existing:**
- Direct: `"mass"` → `"mass"`, `"force"` → `"force"`, `"velocity"` → `"velocity"`
- Miss: `"xyzfoobar"` → null/not-exists
- Abbreviation: `"kg"` → `"kilogram"`, `"N"` → `"newton"`
- Plural -s: `"metres"` → `"metre"`
- Plural -ies: `"velocities"` → `"velocity"`

**Known failures (xfail):**
- Plural -es: `"masses"` → `"mass"` (morpheme rule not confirmed)
- Concept vs mantra collision: `"acceleration"` → `"acceleration"` not
  `"acceleration-mantra"` (name: slot collision in word_index)
- Concept vs mantra: `"kinetic-energy"` → `"kinetic-energy"` not
  `"kinetic-energy-mantra"`

**New:**
- `"time"` → `"time"` (bhasha node, not kosha, but still in word_index)
- `"displacement"` → `"displacement"`
- `"newton"` → `"newton"` (full unit name resolves to itself)
- Case insensitivity: `"Mass"` → not tested but worth knowing if clean() lowercases

### `test_graph_primitives.py`

Tests the low-level graph ops. These catch regressions when `proof_graph.ml` or
`yantra_eval_graph.ml` changes.

**Existing:**
- `emit-node` + `walk`: emitted node is walkable via satya edge
- `emit-node` + `walk-in`: ownership edge is bidirectional
- `walk-in` non-transitivity: shashthi-vibhakti does not chain 2 hops
- `register-dimension`: returns index ≥ 10, idempotent (same name twice → same index)
- `materialize-question-graph`: all 4 edge types land correctly

**New:**
- `walk "mass" "matra"` → `["kilogram"]` (kosha walk, live node)
- `walk "velocity" "kramanusara"` → contains `"displacement"` (real kosha edge)
- `walk "unknown-node-xyz" "satya"` → `[]` (non-existent node, no crash)
- `walk "mass" "nonexistent-relation-xyz"` → `[]` (unknown relation, no crash)
- `walk-in "kilogram" "matra"` → contains `"mass"` (reverse walk in kosha)
- `node-satya "mass"` → > 0 (live kosha node has non-zero satya)
- `node-satya "unknown-xyz"` → `0` (missing node)
- `register-dimension "satya"` twice → same index both times
- `emit-node` idempotency: calling twice does not duplicate edges

### `test_sandhi.py`

Tests `sandhi-viveka` — the grammar promotion pass.

**Existing (collapsed into parametric):**
- `"has"` → `shashthi-vibhakti` (verb-has sloka: "shashthi-vibhakti-sthita")
- `"with"` → `shashthi-vibhakti`
- `"was"` → `bhuta-kaala`
- satya triple → passes through unchanged
- mithya non-grammar word → passes through unchanged

**New:**
- Multi-triple graph: only mithya grammar words are promoted, others unchanged
- `sandhi-viveka` on empty graph → `[]`
- Word with no slokas (e.g. `"ball"`) → passes through as mithya unchanged
- All triples in result have exactly 3 elements (structure invariant)

### `test_bqg.py`

Tests `build-question-graph` — the full sentence → triple graph pipeline.
This is the highest-value regression module: it exercises tokenisation, context
threading, sandhi-viveka, kosha-expand all in one call.

**Existing (collapsed and renamed):**
- Known concept word → satya triple: `"find force"` has `[force, satya, force]`
- Unknown word → mithya triple: `"xyzfoobar"` has `[xyzfoobar, mithya, xyzfoobar]`
- `"what"` prefix → intent triple: `[what, vidhi-kaala, solve-for]` present
- Number + unit → `[mass, sankhya, 5]` AND `[mass, matra, kilogram]` in one test
- Unitless number → `asprista-sankhya` triple

**New:**
- Sentence with only unknown words → all triples are mithya
- `"ball has mass"` → `"has"` becomes `shashthi-vibhakti` edge (sandhi-viveka fires
  inside BQG)
- `"what is kinetic energy"` → both `kinetic-energy` satya AND vidhi-kaala present
  (compound resolution + intent in same sentence)
- Comma-suffixed numbers: `"10,"` → value 10 extracted correctly
- Possessive `"ball's mass"` → `"ball"` and `"mass"` both present
- Numbers appear as asprista-sankhya before context threading resolves them:
  `"find sum of 10 and 14"` → both 10 and 14 as asprista-sankhya

**Known failures (xfail):**
- `"what is acceleration"` → acceleration lands as satya (currently mithya due to
  word_index collision with acceleration-mantra)
- `"velocity 10 m/s"` → matra = metre-per-second (compound unit not resolved)
- `"what is force given mass 5 kg"` → solve-for target is a separate triple
  (vidhi-kaala emitted but solve-for concept not bound separately)

### `test_avrti.py`

Tests `avrti-refine` and `fixpoint` — the spiral refinement pipeline.

**Existing (collapsed and renamed):**
- `[kinetic, mithya] + [energy, satya]` → `[kinetic-energy, satya]` (compound)
- `[ball, mithya] + [energy, satya]` → unchanged (kosha miss)
- `[initial, mithya] + [velocity, satya]` → `[initial-velocity, satya]` (avastha)
- `[final, mithya] + [velocity, satya]` → `[final-velocity, satya]`
- After avastha synthesis: sankhya reattributed from base concept to compound
  (`[velocity, sankhya, 20]` → `[final-velocity, sankhya, 20]`)
- No stale sankhya on base concept after reattribute
- Stable graph → same length (idempotent)
- fixpoint: terminates, result correct
- Unitless number binds to preceding satya concept (asprista-sankhya rule)
- Bhuta-kaala triple survives unchanged (not renamed)
- No tense → velocity stays velocity, not initial-velocity
- Entity rule R9+R8: ball+A → ball-A entity, mass owned by ball-A
- Entity rule R9+R8: sankhya and matra survive alongside ownership
- Entity rule R9+R4b: symbolic label becomes vishesa instance
- Two named entities: distinct ownership edges, no cross-contamination
- Full SUVAT setup: entity + two avastha + symbolic u, v

**New:**
- `avrti-refine` on empty graph → `[]`
- All triples in result have 3 elements (structure invariant after any pass)
- fixpoint on already-stable graph terminates in 1 pass (not wasteful)
- `"angular velocity"` → `angular-velocity` compound (avastha qualifier variant)
- Consecutive mithya words that have no kosha compound → both pass through unchanged
- asprista-sankhya followed by unit → unit consumes pending, concept gets sankhya+matra

**Known failures (xfail):**
- dvandva collection: consecutive asprista-sankhya under satya concept → dvandva group
- mithya sequence before satya concept → dvandva group typed by bahu-vachana
- "respectively" zips two dvandva groups
- mantra-position type inference for instance typing
- R3 dual-avastha same-base bug: two initial/final from same base word

### `test_sankhya.py`

Tests `emit-triples` and `find-context` — the word-level triple emission logic.

**Existing (all good, just rename):**
- Kosha node → `[node, satya, node]` (reflexive satya)
- Unknown word → `[word, mithya, word]`
- Intent role → `[word, vidhi-kaala, solve-for]`
- Matra word after pending → consumes pending as sankhya binding `[concept, sankhya, val]`
- Concept (not unit) after pending → does NOT consume (guard check)
- `"time"` (bhasha, not kosha) → satya
- Reflexive satya invariant: obj == subj for every satya triple
- `find-context []` → active = `""`, pending = `""`
- `find-context [satya-triple]` → active = node name
- `find-context [asprista-sankhya-triple]` → pending = value
- Reflexive satya triple → active = node (regression: old code checked dead string "concept")

**New:**
- `emit-triples` on a unit node with no pending → emits `[unit, satya, unit]` not
  `[unit, mithya, unit]` (units are kosha nodes)
- Context threads across multiple words: `find-context` after `[mass, satya, mass]`
  gives active=`"mass"`, then `emit-triples "5" ... ctx=["mass",""]` gives
  `asprista-sankhya` triple

### `test_kosha.py`

Tests `kosha-expand`, PPR, and direct kosha graph traversal. This is the module
that tests the knowledge graph itself — catching regressions when kosha nodes change.

**Existing:**
- `kosha-expand []` → `[]` (no crash)
- `kosha-expand` adds kosha-janya triples to graph with satya seeds
- Original triples preserved after expand
- `kosha-expand` idempotent: running twice doesn't duplicate kosha-janya triples
- mass + velocity seeds surface at least one of: momentum, kinetic-energy,
  linear-force, acceleration

**New — kosha graph structure:**
- `walk "mass" "matra"` → `["kilogram"]` (unit edge exists)
- `walk "velocity" "kramanusara"` → contains `"displacement"`
- `walk-in "kilogram" "matra"` → contains `"mass"` (reverse: what uses kilogram?)
- `walk "kinetic-energy" "mass-yukta"` → contains `"mass"` (structural edge)
- `walk "kinetic-energy" "velocity-yukta"` → contains `"velocity"`
- `ancestors-of "velocity"` → non-empty (has inheritance chain)
- `node-satya "mass"` → > 0 (high-degree node has positive satya)
- `walk "momentum" "mass-yukta"` → contains `"mass"`
- `walk "newton-second-law-motion" "krama"` → non-empty (mantra has krama chain)

**New — PPR:**
- `ppr [] "mass" []` → empty or near-empty results (no seeds)
- `ppr [["mass","1.0"]] "mass" []` → non-empty, each entry is a list with name + score
- score field is a number > 0 for top results
- `ppr [["mass","1.0"],["velocity","1.0"]] "mass" []` → results include concepts
  related to both seeds

### `test_match.py`

Tests `match-mantra` — formula matching and disambiguation.

**Existing (renamed):**
- mass + velocity bound → kinetic-energy-mantra found
- Only mass bound → no match (returns `[]`)
- Return value structure: `[name, args]`, name is non-empty string
- Args ordered by krama-rhs: mass-val at index 0, velocity-val at index 1
- solve-for = kinetic-energy → kinetic-energy-mantra not momentum-mantra
- solve-for = momentum → momentum-mantra not kinetic-energy-mantra
- solve-for = acceleration, all krama-rhs bound → acceleration-mantra
- solve-for = force, mass+acceleration bound → newton-second-law-motion

**New:**
- No solve-for triple, all krama-rhs bound → still matches (solve-for is optional)
- solve-for for unknown concept → returns `[]` gracefully
- Extra unknown triples in graph don't prevent match (noise tolerance)
- Partial krama-rhs coverage (missing one arg) → no match

**Known failures (xfail):**
- solve-for = first satya AFTER vidhi-kaala (not first satya overall) — bug 1

### `test_pipeline.py`

End-to-end integration tests: full sentence through BQG → avrti → match.

**Existing (renamed):**
- `"what is kinetic energy"` → after fixpoint, kinetic-energy satya in graph
- `"ball A has mass 5 kg"` → materialize: entity owns mass, bidirectional walk
- SUVAT materialize: entity owns initial-velocity + final-velocity, naama-mudra symbols
- satya bridge: `walk kosha-node "matra"` from satya triple obj reaches real unit
- Ownership non-transitivity
- `avrti-r4b` guard: numeric sankhya prevents vishesa-instance firing
- `kosha-expand` surfaces related concepts for mass+velocity

**New:**
- `"find force given mass 10 and acceleration 2"` → match returns newton-second-law-motion
- `"what is momentum given mass 3 kg and velocity 4 m/s"` → momentum-mantra matched
- `"initial velocity 5 final velocity 20 time 3"` → avrti produces initial-velocity
  and final-velocity with correct values

**Known failures (xfail):**
- `"ball A has mass 5 kg and velocity 10 m/s find kinetic energy"` → match returns
  kinetic-energy-mantra (blocked by solve-for heuristic bug 1)
- `"train T has initial velocity 5 and final velocity 20 and time 3 find acceleration"` →
  acceleration-mantra (blocked by bugs 1 + 2 combined)
- R3 dual-avastha: initial-velocity gets correct value, not final-velocity's value
- solve-for target is first satya after vidhi-kaala, not first satya overall

### `test_session.py`

Tests the session layer in `socket.ml` — entirely new, nothing here currently tested.

The `vy` fixture uses `eval-json`. For session tests we need direct `question`
requests. Add a `vy.ask(question, session_id)` helper to `vy.py` that sends the
question command and returns `answer_text`.

**Session isolation:**
- Two different session_ids → independent turn counts
- Session A binds mass=5 via a question; Session B query for mass → no cross-contamination
- `end-session` then re-query on same session_id → turn count resets to 1

**Turn counting:**
- First question on a new session_id → turn_id = `"prashna-1"` in response
- Second question on same session_id → turn_id = `"prashna-2"`
- Turn count is per-session, not global

**Multi-turn continuity:**
- Turn 1: `"mass is 5 kg"` → session stores binding
- Turn 2: `"what is the kinetic energy if velocity is 10 m/s"` → session can
  recall mass from turn 1 (once session bindings are threaded through anuvada_query)

**Answer text:**
- A question with a known concept → answer_text is non-empty
- A question with only unknown words → answer_text is `""` (empty, not error)
- `max_passes = 1` vs `max_passes = 3` → different answer depth (more triples at 3)

**Error handling:**
- Missing `question` field → status = `"error"`, code = `"INVALID_REQUEST"`
- Empty `question` string → status = `"error"`, code = `"INVALID_REQUEST"`
- Bad eval expression → status = `"error"`, code = `"ENGINE_ERROR"`, next eval works

---

## What to delete from `brahman/yantra/tests/`

**All `test-*.tantra` files are deleted.** Every single one — debug scaffolds,
language-primitive probes, and real behavioural specs alike. The Python modules
absorb the behavioural specs; the debug/scaffold files are just dropped.

The delete happens in Step 12 (after all Python tests pass and are confirmed green).
Do not delete before the Python equivalents are written and passing.

Files to delete (by suite):

| Suite | Files | Count |
|---|---|---|
| `sandhi/` | `test-debug-*.tantra`, `test-has-*.tantra`, `test-mithya-*.tantra` | 21 |
| `avrti/` | all `test-*.tantra` | 20 |
| `primitives/` | `test-ends-with-*.tantra`, `test-split-numeric-*.tantra`, `test-substr.tantra`, `test-ppr-*.tantra`, `test-rashi-*.tantra` | 8 |
| `vishesa/` | `test-vishesa-step-debug.tantra` | 1 |
| `lookup/` | all `test-*.tantra` | (count at delete time) |
| `match/` | all `test-*.tantra` | (count at delete time) |
| `pipeline/` | all `test-*.tantra` | (count at delete time) |
| `sankhya/` | all `test-*.tantra` | (count at delete time) |
| `vibhakti/` | all `test-*.tantra` | (count at delete time) |

**Keep** all tantra files that are production pipeline code (not in `tests/`):
`sandhi-viveka.tantra`, `avrti-refine.tantra`, `build-question-graph.tantra`,
`match-mantra.tantra`, `emit-triples.tantra`, `find-context.tantra`,
`kosha-expand.tantra`, `materialize-question-graph.tantra`, `fixpoint`,
`sandhi-kosha.tantra`, `sandhi-avastha.tantra`, `sandhi-bandhana.tantra`,
`vishesa-instance.tantra`, `vibhakti-shashthi.tantra`.

**Never create new `test-*.tantra` files.** If you need to test something, write
a Python test that passes the expression inline to `vy.eval(...)`.

### Two-category distinction

| File | Location | What it is | Action |
|---|---|---|---|
| `sandhi-viveka.tantra` | `brahman/yantra/sandhi/` | Production pipeline — called by BQG | Keep forever |
| `test-has-becomes-shashthi.tantra` | `brahman/yantra/tests/sandhi/` | Test wrapper — just returned true/false | Delete in Step 12 |
| `test-debug-inner-reduce.tantra` | `brahman/yantra/tests/sandhi/` | Debug scaffold | Delete in Step 12 |

---

## New things to test that weren't tested before

### render-node upgrade

`render-node` returns a plain-text string. The `sahaja_gloss` function has been
fixed to read the shabda `name:` key and `before-/` pattern correctly.

Add to `test_graph_primitives.py`:

```python
def test_render_node_returns_string(vy):
    result = vy.eval('render-node "mass"')
    assert isinstance(result, str) and len(result) > 0

def test_render_node_unknown_returns_not_found(vy):
    result = vy.eval('render-node "unknown-xyz-node"')
    assert "not found" in result

def test_render_node_includes_node_name(vy):
    result = vy.eval('render-node "velocity"')
    assert "velocity" in result
```

Future: add a `node-info` socket command (Option C from design discussion) that
returns structured JSON — name, satya, gloss, slokas, edges, cited_by. This makes
`sahaja_gloss` output testable and makes the Python side able to render node data.

### Kosha structural tests

The kosha contains physics, math, biology, grammar nodes. Test that key structural
relationships hold — these catch regressions when `.om` files are edited:

```python
# physics structure
def test_mass_has_kilogram_unit(vy): ...
def test_velocity_has_displacement_kramanusara(vy): ...
def test_kinetic_energy_yukta_edges(vy): ...  # mass-yukta, velocity-yukta

# mantra structure
def test_kinetic_energy_mantra_has_krama_chain(vy): ...
def test_momentum_mantra_krama_rhs_order(vy): ...
def test_newton_second_law_krama_lhs_is_force(vy): ...
```

### Session continuity (future — once `_active_session` threaded through)

Currently `_active_session` is computed in `socket.ml` but `ignore`d — not yet
passed to `anuvada_query`. Once Step 4 of session-graph.md is done:

```python
def test_session_carries_binding_across_turns(vy):
    vy.ask("mass is 5 kg", session_id="sess-1")
    vy.ask("velocity is 10 m/s", session_id="sess-1")
    result = vy.ask("what is the kinetic energy", session_id="sess-1")
    assert "kinetic energy" in result.lower()

def test_two_sessions_independent(vy):
    vy.ask("mass is 5 kg", session_id="sess-a")
    result = vy.ask("what is mass", session_id="sess-b")
    # sess-b should not know about sess-a's mass binding
    assert "5" not in result
```

---

## Known failures — full list with reasons

These are `@pytest.mark.xfail(strict=True, reason="...")` in the test modules.
When the feature is implemented, pytest errors to force you to promote the test.

| Test | Missing feature |
|---|---|
| `lookup-word "masses"` → `"mass"` | english-plural-es morpheme rule |
| `lookup-word "acceleration"` → `"acceleration"` | mantra name: slot collision in word_index |
| `lookup-word "kinetic-energy"` → `"kinetic-energy"` | mantra name: slot collision |
| `bqg "what is acceleration"` → acceleration is satya | same collision |
| `bqg "velocity 10 m/s"` → matra = metre-per-second | compound unit m/s not in word_index |
| `bqg` solve-for concept is separate triple | vidhi-kaala emitted but target not bound |
| avrti dvandva collection | dvandva-collection rule not in avrti-refine |
| avrti mithya-sequence → group | group-from-mithya-sequence rule missing |
| avrti "respectively" zip | zip rule not implemented |
| avrti R3 dual-avastha same base | flat rename map last-wins bug |
| match solve-for after vidhi-kaala | first-satya-overall heuristic (bug 1) |
| pipeline full kinetic-energy | blocked by match bug 1 |
| pipeline SUVAT acceleration | blocked by match bug 1 + R3 bug 2 |
| vibhakti entity-from-has rule | entity-typed-by-avrti rule not in avrti-refine |
| vibhakti entity-label compounding | ball+A → ball-A rule missing |
| vibhakti entity owns multiple | ownership propagation across "and" |
| vibhakti "with" as possession signal | only "has" handled |
| vibhakti pronoun resolution | "its"/"their" coreference not implemented |
| vibhakti entity-scoped binding | separate mass per entity not implemented |
| session multi-turn binding | _active_session not threaded through anuvada_query (Step 4) |

---

## Implementation order

```
Step 1  test_interpreter.py      ✅ DONE — 71 tests passing
Step 2  test_word_index.py       ✅ DONE — 24 tests (4 xfail)
Step 3  test_graph_primitives.py ✅ DONE — 16 tests passing
Step 4  test_sandhi.py           ✅ DONE — 13 tests (3 xfail)
Step 5  test_bqg.py              ✅ DONE — 18 tests (3 xfail)
Step 6  test_sankhya.py          ✅ DONE — 17 tests (1 xfail)
Step 7  test_avrti.py            ✅ DONE — 21 tests (2 xfail)
Step 8  test_kosha.py            ✅ DONE — 17 tests passing
Step 9  test_match.py            ✅ DONE — 13 tests (1 xfail)
Step 10 test_pipeline.py         ✅ DONE — 12 tests (2 xfail)
Step 11 test_session.py          ✅ DONE — 13 tests (1 xfail)
Step 12 Delete debug tantra files ✅ DONE — all 146 test-*.tantra files deleted
```

## Key discoveries made during implementation

- **`cond` parser bug** — `parse_cond` `_` branch consumes `)` as an else-branch
  value. `reduce [1 2 3] 0 (fn acc x -> cond (gt x 1) acc x)` returns `")"`.
  Workarounds applied in tests; fix tracked in `parser-refactor-plan.md`.
- **`power` not `pow`** — arithmetic primitive is `power 2 10`, not `pow`.
- **`range` takes one argument** — `range 4` → `[0,1,2,3]`. `range 0 4` → `[]`.
- **`cond` at top level fails** — only works inside fn bodies passed to reduce/map/filter.
- **`kosha-expand` is not idempotent** — running twice doubles kosha-janya triples.
- **`vy.ask()` command field bug** — must NOT include `"command":"question"`;
  `json_string_field` finds "question" in the command value first. Fixed in `vy.py`.
- **`sandhi-viveka.tantra` missing** — `build-question-graph.tantra` calls it but
  no file exists; resolver silently no-ops. Verb promotion never fires.
- **Session `turn_id` is echo-only** — response echoes client's submitted turn_id.

## What remains (xfail — features not yet built)

| xfail | Blocking feature |
|---|---|
| `lookup-word "kg"/"N"/"m"/"s"` | abbreviations not in word_index |
| `sandhi-viveka` verb promotion | `sandhi-viveka.tantra` file missing |
| BQG unit binding | unit not in word_index, emit-triples path not firing |
| BQG `vidhi-kaala` intent triple | "what" resolves as satya, intent role not assigned |
| Entity ownership via "has" | avrti R8/R9 rules not in vibhakti-shashthi.tantra |
| dvandva collection | consecutive asprista-sankhya → dvandva rule missing |
| match solve-for heuristic | picks first satya overall, not first after vidhi-kaala |
| Full SUVAT pipeline | blocked by entity ownership + solve-for bugs |
| Cross-turn session binding | `_active_session` not threaded through anuvada_query |
