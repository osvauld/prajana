# tools/

Analysis and test pipeline tools for the nam proof-graph reasoning system.

These tools read the live codebase and the test result cache — they do not
simulate or approximate. Every number they emit came from an actual run.

---

## test pipeline

### `analyze_test_results.py`

The primary tool. Owns the test run lifecycle.

```bash
# report only — read cache, print analysis (no tests run)
python3 tools/analyze_test_results.py

# run only the tests that failed last time
# if they all pass → automatically runs full suite
python3 tools/analyze_test_results.py --run

# run full suite unconditionally
python3 tools/analyze_test_results.py --full

# run failures first, then promote to full if clean
python3 tools/analyze_test_results.py --run --full

# start the server automatically if not running
python3 tools/analyze_test_results.py --run --auto-server

# compare against a previous summary
python3 tools/analyze_test_results.py --diff /tmp/old_summary.json

# emit JSON (pipe to jq)
python3 tools/analyze_test_results.py --json | jq '.summary'
```

**Pipeline logic (`--run`):**

1. Read `.pytest_cache/vyakarana/*.json` — one file per test, written by `conftest.py`
2. Find all tests with `outcome: failed|error`
3. Run only those node IDs: `pytest tests/test_foo.py::test_bar ...`
4. Re-read cache — if still failing: show full diagnosis and stop
5. If now clean: promote to full suite (`pytest` with no filter)
6. Print final report after every run

**What the cache gives us per test:**

| field | meaning |
|---|---|
| `calls[].input` | exact string sent to the server (eval expr or sentence) |
| `calls[].output` | exact server response |
| `calls[].elapsed_ms` | per-call timing |
| `calls[].error` | exception string if the call threw |
| `failure.last_call` | the specific call that caused the assertion to fail |
| `failure.expected` / `.got` | extracted from the assertion message |
| `outcome` | `passed` / `failed` / `skipped` (xfail) / `xpassed` |
| `duration` | total test wall time in seconds |

**What the report shows:**

- Full eval chain for every failing test (input → output → elapsed_ms)
- The triggering call isolated from `failure.last_call`
- Failure categories: `has-intent-guard-missing`, `scope-entity`,
  `derive-chain-contamination`, `relative-velocity-spurious`, etc.
- Xfailed tests grouped by philosophical gate (what must be built first)
- Slowest individual calls across the entire suite
- Diff from a previous summary (newly failing / newly passing)

**Xfail gates** — tests grouped by what they're waiting on:

| gate | what it needs |
|---|---|
| `dvandva` | per-entity instance-map in vishesa-bandhana |
| `session_gap2` | prathama/shashthi triples across session turns |
| `pratibimba` | gated on session_gap2 |
| `p8f_gravity` | G constant + r² composition (P8f Phase B) |
| `unit_rate` | slash-separated compound unit in split-numeric |
| `logic_nyaya` | P8d anumana mantras (not yet built) |

---

## structure analysis

### `analyze_pipeline.py`

Cross-layer pattern analysis: sparsha / viveka / bandha at every scale —
tantra2 source, OCaml source, shabda vocabulary, graph edges, test calls.

```bash
python3 tools/analyze_pipeline.py                  # full report
python3 tools/analyze_pipeline.py --report patterns
python3 tools/analyze_pipeline.py --report abstractions
python3 tools/analyze_pipeline.py --report tantras
python3 tools/analyze_pipeline.py --report live     # live cache cross-reference only
python3 tools/analyze_pipeline.py --json
```

What it finds:

- **26×** `gt (string-length (to-string X)) 0` — the `exists?` anti-pattern
- **40×** inline `shashthi-vibhakti` ownership queries — candidate for `shashthi-sparsha` tantra
- **13×** `extract-solve-for` call sites — candidate for rename to `iccha-viveka`
- Duplicate tantra groups: bandha-reduce, ownership-query, sankhya-reader,
  intent-scope, proof-graph-emitter
- Test suggestions derived from structural gaps (not invented)
- Live cache cross-reference: which tantras appear in failing test eval calls

---

### `analyze_ocaml.py`

OCaml module map, recurring patterns, tantra1 dead code, and the
**OCaml → tantra migration analysis**.

```bash
python3 tools/analyze_ocaml.py                     # full report
python3 tools/analyze_ocaml.py --report migration  # migration candidates only
python3 tools/analyze_ocaml.py --report patterns
python3 tools/analyze_ocaml.py --report dead
python3 tools/analyze_ocaml.py --json
```

**Migration boundary** — the line between what stays in OCaml and what can move:

- **Category A (stays in OCaml forever):** control structures (`eval`, `scan`,
  `fixpoint`, `reduce`, `map`, `filter`), graph substrate (`walk`, `emit-node`,
  `ppr`), type coercions (`eq`, `nth`, `append`), OCaml bridge calls
  (`Setu.*`, `Proof_graph.*`), mutable state (`session-bindings`)
- **Category B (can move to tantra):** composed ops that are pure combinations
  of Category A — `square`, `half`, `double`, `reciprocal`, `first-match`,
  `unique`, `vec-scale`, `vec-dot`, `vec-norm`, `sum`, `zip`, `reverse`

Migration scores (from `--report migration`):

| score | meaning | examples |
|---|---|---|
| 3 | migrate immediately — one line | `square → mul x x`, `half → mul x 0.5` |
| 2 | migrate next — clean tantra form | `unique`, `sum`, `vec-scale`, `vec-dot` |
| 1 | defer — expressible but verbose | `reverse`, `zip`, `rot2d` |
| 0 | keep in OCaml — not expressible yet | `sort-desc`, `frequencies`, `mat-mul` |

Philosophy: *composition belongs in brahman. execution belongs in yantra.*
The line is sthita (situated-ness): if the op lives in the graph-of-tantras,
it belongs in `brahman/yantra/`. If it lives in the evaluator itself, it stays.

---

### `analyze_tantras.py`

Deep tantra AST analysis. Requires the server to be running (uses `dump-ast`).

```bash
python3 tools/analyze_tantras.py                   # full report
python3 tools/analyze_tantras.py --report tantra
python3 tools/analyze_tantras.py --report tests    # test gap + xfail table
python3 tools/analyze_tantras.py --report philosophical
python3 tools/analyze_tantras.py --json
```

What it finds:

- Complexity by AST node count and nesting depth
- Hub tantras (called by most others): `extract-solve-for`, `bound-concept-names`,
  `match-mantra`, `derive-chain`, `emit-reasoning`
- Recurring query shapes (`from` patterns) — how many tantras share the same
  graph-traversal structure
- Scan anatomy: state variables, branch count, has-otherwise
- Relation gap: edges declared in om files vs edges queried in tantras
  (`yukta` has 3276 declared, 0 queried)
- Pratipaksha completeness: which math ops have inverses
- **Xfail gap table:** live cross-reference of xfail groups against actual
  test files — shows which tests are missing xfail markers, which are missing
  entirely, and the philosophical gate for each group

---

### `analyze_shabda.py`

Surface vocabulary analysis: word index, aliases, collisions, hapax legomena.

```bash
python3 tools/analyze_shabda.py
python3 tools/analyze_shabda.py --json
```

---

### `collect_data.py`

Batch data collector that runs all analyses and writes to `/tmp/analysis.json`.
Used by `analyze_test_results.py` for tantra cross-reference.

```bash
python3 tools/collect_data.py
```

---

## cache location

```
vyakarana/.pytest_cache/vyakarana/
  summary.json                          — session totals + slow tests
  tests__test_foo.py__test_bar.json     — one file per test
```

Written by `vyakarana/tests/conftest.py` after every pytest run.
Read by all tools above without running any tests.

---

## typical workflow

```bash
# after making a change to a tantra or OCaml file:
python3 tools/analyze_test_results.py --run

# if failures remain, inspect them:
python3 tools/analyze_test_results.py

# after a clean run, check what the structure says:
python3 tools/analyze_pipeline.py --report abstractions
python3 tools/analyze_ocaml.py --report migration

# full structural picture (needs server):
python3 tools/analyze_tantras.py --report tests
```
