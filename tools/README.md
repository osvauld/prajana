# tools/

Analysis, knowledge, and test pipeline tools for the nam proof-graph
reasoning system. Everything runs from this directory.

These tools read the live codebase and the test result cache — they do not
simulate or approximate. Every number they emit came from an actual run.

---

## brahman — the unified control plane

### `read_brahman.py` / `brahman/`

One tool for everything: reading tantras and om files, running tests,
querying the result cache, and serving all of the above over a Unix socket
so an LLM can query it directly.

**Package layout:**

```
tools/brahman/
  tantras.py      — parse + query 72 .tantra3 files (static, no server)
  om.py           — parse + query 1614 .om files, grouped by domain
  tests.py        — static test discovery (AST parse, no server)
  runner.py       — pytest subprocess wrapper for targeted test runs
  cache.py        — read/query/act on the pytest result cache
  server.py       — Unix socket server + BrahmanClient
  cli.py          — CLI dispatcher (all modes)
  vy.py           — vyakarana socket client (used by tests)
  conftest.py     — pytest fixtures + per-test cache writer
  pyproject.toml  — anchors pytest rootdir to tools/brahman/
  v2/             — the test suite (98 tests: 67 passing + 31 xfail)
    test_evaluator.py
    test_graph.py
    test_pipeline.py
    test_answers.py
    test_xfail.py
  .pytest_cache/
    vyakarana/    — per-test JSON entries + summary.json
```

---

## running tests

The vyakarana server must be running first:

```bash
cd vyakarana && ./_build/default/bin/vyakarana.exe --socket /tmp/vy.sock ../brahman &
```

Then run tests:

```bash
# run everything
cd tools/brahman && ../../.venv/bin/pytest v2/ --socket /tmp/vy.sock -q

# or via the brahman tool (handles paths automatically)
python3 tools/read_brahman.py test run

# run one layer
python3 tools/read_brahman.py test run evaluator
python3 tools/read_brahman.py test run pipeline
python3 tools/read_brahman.py test run answers

# run one test by name
python3 tools/read_brahman.py test run test_ke_basic

# run xfails for a specific gate (when implementing a feature)
python3 tools/read_brahman.py test run gate:arithmetic
python3 tools/read_brahman.py test run gate:dvandva
```

**Test layers** — 98 tests total:

| layer | tests | what it covers |
|---|---|---|
| `evaluator` | 17 | reduce, map, filter, cond, fn, let, from/where, fixpoint, arithmetic, strings, lists, split-numeric |
| `graph` | 10 | walk, walk-in, node-satya, shabda lookup, plural stemming, abbreviation |
| `pipeline` | 22 | bqg, sandhi, avrti-refine, rashi, entity scope, match, agra-bandha, paragraph |
| `answers` | 18 | end-to-end: sentence → answer, strands, multi-turn, comparison |
| `xfail` | 31 | features not yet built (the roadmap) |

**Xfail gates** — what each pending group is waiting on:

| gate | tests | needs |
|---|---|---|
| `arithmetic` | 4 | plain count add/subtract, distance, area |
| `dvandva` | 3 | per-entity instance-map + variadic sum |
| `inverse_math` | 3 | bound-vals / invert-math path |
| `sthita_viveka` | 2 | multi-slot entity assignment (gravity, coulomb) |
| `compute_compare` | 2 | compute-then-compare viveka |
| `transitive` | 2 | graph-walk chain inference |
| `motion_verb` | 3 | 'moves at' / 'moving at' → velocity signal |
| `from_rest` | 2 | 'from rest' → initial-velocity = 0 |
| `syllogism` | 1 | modus-ponens + assertion chain |
| `proportional` | 1 | proportional reasoning |
| `compound_trigram` | 2 | three-word compounds (electric-field-strength) |
| `colour_classifier` | 2 | colour words as entity discriminators |
| `article` | 1 | 'the electron' article transparency |
| `relative_velocity` | 1 | relative-velocity kosha concept |

---

## cache

Every test run writes per-test JSON to `tools/brahman/.pytest_cache/vyakarana/`.

```bash
# summary: passed/failed/xfailed counts, gates, slowest calls
python3 tools/read_brahman.py cache summary

# all failed tests with diagnosis + call chain
python3 tools/read_brahman.py cache failed

# xfail gates — what is each group waiting on
python3 tools/read_brahman.py cache gates
python3 tools/read_brahman.py cache gates arithmetic

# compare against a previous run
python3 tools/read_brahman.py cache diff /tmp/old_summary.json

# show slowest calls and tests
python3 tools/read_brahman.py cache slow

# remove @xfail markers from tests that now pass (dry-run first)
python3 tools/read_brahman.py cache fix-xpass
python3 tools/read_brahman.py cache fix-xpass --apply
```

**Cache entry fields** (per test):

| field | meaning |
|---|---|
| `calls[].input` | exact string sent to the server (eval expr or sentence) |
| `calls[].output` | exact server response |
| `calls[].elapsed_ms` | per-call timing |
| `calls[].error` | exception string if the call threw |
| `failure.last_call` | the specific call that caused the assertion to fail |
| `failure.expected` / `.got` | extracted from the assertion message |
| `outcome` | `passed` / `failed` / `xfailed` / `xpassed` |
| `duration` | total test wall time in seconds |
| `xfail.gate` | which feature gate this xfail belongs to |

---

## knowledge queries

Read tantras and om files from disk — no server needed.

```bash
# ── tantras ─────────────────────────────────────────────────────────────

# one-line summary: name, lines, takes, bindings, calls, scans
python3 tools/read_brahman.py tantra summary

# list the 12 tantra groups
python3 tools/read_brahman.py tantra groups

# dump all tantras with source, grouped by directory
python3 tools/read_brahman.py tantra all

# dump one group
python3 tools/read_brahman.py tantra group pipeline

# dump one tantra by name (no path needed)
python3 tools/read_brahman.py tantra source execute-mantra

# static call graph: who calls whom
python3 tools/read_brahman.py tantra callgraph

# who calls derive-chain?
python3 tools/read_brahman.py tantra callers derive-chain

# what does anuvada-ganana call?
python3 tools/read_brahman.py tantra callees anuvada-ganana

# regex search across all tantras
python3 tools/read_brahman.py tantra search "viveka"


# ── om files ─────────────────────────────────────────────────────────────

# overview: layer counts + domain tree at depth 2
python3 tools/read_brahman.py om summary

# domain tree at depth 3
python3 tools/read_brahman.py om domains 3

# browse a domain — shows subdomains then direct nodes with source
python3 tools/read_brahman.py om domain kosha/math
python3 tools/read_brahman.py om domain kosha/math/number/operations
python3 tools/read_brahman.py om domain kosha/physics/kinematics/linear
python3 tools/read_brahman.py om domain sangati/jiva

# dump one om node by name
python3 tools/read_brahman.py om source velocity
python3 tools/read_brahman.py om source addition
python3 tools/read_brahman.py om source viveka-max

# find nodes with a specific shabda key
python3 tools/read_brahman.py om with-key eval
python3 tools/read_brahman.py om with-key arity

# find nodes with a specific edge relation
python3 tools/read_brahman.py om with-relation pratipaksha
python3 tools/read_brahman.py om with-relation kriya

# regex search across all om files
python3 tools/read_brahman.py om search "pratipaksha"


# ── cross-cutting ─────────────────────────────────────────────────────────

# search both tantras AND om files at once
python3 tools/read_brahman.py search "viveka"

# run one JSON command inline (same protocol as socket)
python3 tools/read_brahman.py json '{"command":"ping"}'
python3 tools/read_brahman.py json '{"command":"tantra-callers","name":"derive-chain"}'
python3 tools/read_brahman.py json '{"command":"cache-summary"}'
```

---

## socket server

Start the brahman server (separate from the vyakarana server):

```bash
python3 tools/read_brahman.py serve                    # /tmp/brahman.sock
python3 tools/read_brahman.py serve /tmp/custom.sock
```

Query from the command line:

```bash
echo '{"command":"ping"}' | socat - UNIX-CONNECT:/tmp/brahman.sock
echo '{"command":"test-summary"}' | socat - UNIX-CONNECT:/tmp/brahman.sock | jq .
echo '{"command":"cache-summary"}' | socat - UNIX-CONNECT:/tmp/brahman.sock | jq .
echo '{"command":"test-run","socket":"/tmp/vy.sock"}' | socat - UNIX-CONNECT:/tmp/brahman.sock
```

Query from Python:

```python
from tools.brahman.server import BrahmanClient

c = BrahmanClient("/tmp/brahman.sock")

# knowledge
c.ping()
c.tantra_source("execute-mantra")
c.tantra_callers("derive-chain")
c.om_domain("kosha/math/logic")
c.om_with_key("eval")
c.search("viveka")
c.reload()

# tests
c._call({"command": "test-summary"})
c._call({"command": "test-list", "layer": "evaluator"})
c._call({"command": "test-list", "gate": "arithmetic"})
c._call({"command": "test-run", "socket": "/tmp/vy.sock"})
c._call({"command": "test-run", "layer": "pipeline", "socket": "/tmp/vy.sock"})
c._call({"command": "test-run", "name": "test_ke_basic", "socket": "/tmp/vy.sock"})

# cache
c._call({"command": "cache-summary"})
c._call({"command": "cache-failed"})
c._call({"command": "cache-gates"})
c._call({"command": "cache-gates", "gate": "arithmetic"})
c._call({"command": "cache-diff", "previous": "/tmp/old_summary.json"})
c._call({"command": "cache-fix-xpass", "dry_run": True})
c._call({"command": "cache-slow"})
```

**Full socket command reference:**

| command | required | optional | returns |
|---|---|---|---|
| `ping` | — | — | tantra + om counts |
| `tantra-summary` | — | — | per-tantra metadata |
| `tantra-source` | `name` | — | full source + bindings + calls |
| `tantra-group` | `group` | — | all tantras in group with source |
| `tantra-groups` | — | — | group list with counts |
| `tantra-callgraph` | — | — | forward `calls` + `called_by` |
| `tantra-callers` | `name` | — | list of callers |
| `tantra-callees` | `name` | — | list of callees |
| `om-summary` | — | `depth` | layer counts + domain tree |
| `om-source` | `name` | — | full source + slokas + edges + shabda |
| `om-domain` | `domain` | — | subdomains + all nodes under prefix |
| `om-domains` | — | `depth` (default 2) | domain tree |
| `om-with-key` | `key` | — | nodes with that shabda key |
| `om-with-relation` | `relation` | — | nodes with that edge relation |
| `search` | `pattern` | `scope` (all/tantras/om) | matches in tantras/om |
| `reload` | — | — | re-read all files from disk |
| `test-summary` | — | — | 98 total / 67 passing / 31 xfail by layer+gate |
| `test-list` | — | `layer`, `gate`, `pattern`, `xfail_only`, `passing_only` | test metadata |
| `test-run` | `socket` | `layer`, `gate`, `name`, `pattern`, `verbose`, `timeout` | pytest result |
| `cache-summary` | — | `cache_dir` | totals + failed list + gates + slow calls |
| `cache-entry` | `test` | `cache_dir` | full entry for one test |
| `cache-failed` | — | `cache_dir` | all failed entries with diagnosis |
| `cache-gates` | — | `gate`, `cache_dir` | xfailed entries by gate |
| `cache-diff` | `previous` | `cache_dir` | newly failing/passing vs previous run |
| `cache-fix-xpass` | — | `dry_run` (default true), `cache_dir` | remove @xfail from passing tests |
| `cache-slow` | — | `top_n`, `cache_dir` | slowest calls and tests |
| `dump-om` | `path` | — | **vyakarana server only** — om AST as JSON |

---

## domain taxonomy

The om file directory structure IS the domain taxonomy:

```
brahman/
  kosha/              — domain knowledge (1048 nodes)
    math/             — 259 nodes (algebra, calculus, geometry, graph,
                        logic, number, probability, set)
    physics/          — 215 nodes (kinematics, dynamics, energy,
                        electromagnetism, thermodynamics, oscillation)
    chemistry/        — 84 nodes
    biology/          — 50 nodes
    common-sense/     — 46 nodes
    computation/      — 66 nodes
    engineering/      — 24 nodes
    philosophy/       — 26 nodes
    robotics/         — 12 nodes
    yantra/           — 110 nodes (graph edge types, visheshanam)
  sangati/            — universal structural truth (317 nodes)
  bhasha/             — linguistic surface (148 nodes)
```

---

## tantra groups

The 72 tantras in `brahman/yantra/` grouped by function:

| group | files | role |
|---|---|---|
| `pipeline` | 22 | orchestrator, derive/execute, proof graph |
| `avrti` | 5 | refinement passes (fixpoint, anumana) |
| `sankhya` | 4 | number handling, count chain |
| `match` | 7 | mantra matching, scope, forward/inverse |
| `anuvada` | 9 | proof/reasoning emission (pratijna, hetu, etc.) |
| `equations` | 11 | physics equations (ke, momentum, velocity, etc.) |
| `vishesa` | 5 | entity typing, rashi, agra-bandha |
| `sandhi` | 3 | compound word resolution |
| `vibhakti` | 2 | grammar case handling |
| `boot` | 2 | bootstrap + reload |
| `debug` | 1 | mantra coverage |
| `lookup` | 1 | shabda lookup |

---

## structure analysis tools

These are read-only analysis tools that cross-reference tantras, OCaml
source, and the test cache. They do not run tests.

### `analyze_pipeline.py`

Cross-layer pattern analysis: recurring patterns, abstraction candidates,
anti-patterns across tantra source.

```bash
python3 tools/analyze_pipeline.py
python3 tools/analyze_pipeline.py --report patterns
python3 tools/analyze_pipeline.py --report abstractions
python3 tools/analyze_pipeline.py --json
```

### `analyze_ocaml.py`

OCaml module map, migration candidates, dead code analysis.

```bash
python3 tools/analyze_ocaml.py
python3 tools/analyze_ocaml.py --report migration
python3 tools/analyze_ocaml.py --report patterns
python3 tools/analyze_ocaml.py --json
```

**Migration boundary:**

| score | meaning | examples |
|---|---|---|
| 3 | migrate immediately | `square → mul x x`, `half → mul x 0.5` |
| 2 | migrate next | `unique`, `sum`, `vec-scale`, `vec-dot` |
| 1 | defer | `reverse`, `zip`, `rot2d` |
| 0 | keep in OCaml | `sort-desc`, `frequencies`, `mat-mul` |

### `analyze_tantras.py`

Deep tantra AST analysis. Requires the vyakarana server.

```bash
python3 tools/analyze_tantras.py
python3 tools/analyze_tantras.py --report tests
python3 tools/analyze_tantras.py --report philosophical
python3 tools/analyze_tantras.py --json
```

### `analyze_shabda.py`

Surface vocabulary analysis: word index, aliases, collisions.

```bash
python3 tools/analyze_shabda.py
python3 tools/analyze_shabda.py --json
```

### `analyze_test_results.py`

Legacy pipeline runner — still works but `read_brahman.py` is preferred.
Reads the same cache and provides `--run`, `--full`, `--gate`, `--diff`,
`--fix-xpass` options.

```bash
python3 tools/analyze_test_results.py           # report from cache
python3 tools/analyze_test_results.py --full    # run full suite
python3 tools/analyze_test_results.py --gate arithmetic
```

---

## typical workflow

```bash
# 1. understand what you're about to change
python3 tools/read_brahman.py tantra source derive-chain
python3 tools/read_brahman.py tantra callers derive-chain
python3 tools/read_brahman.py om domain kosha/math/number/operations

# 2. run the relevant tests before changing anything
python3 tools/read_brahman.py test run pipeline
python3 tools/read_brahman.py cache summary

# 3. make your change (tantra, om, or OCaml)
#    for OCaml: dune build from vyakarana/ then restart server

# 4. run targeted tests
python3 tools/read_brahman.py test run test_ke_basic
python3 tools/read_brahman.py test run pipeline

# 5. if a gate is now implemented, run its xfails
python3 tools/read_brahman.py test run gate:arithmetic

# 6. full suite
python3 tools/read_brahman.py test run

# 7. if any xfails now pass, remove their markers
python3 tools/read_brahman.py cache fix-xpass
python3 tools/read_brahman.py cache fix-xpass --apply

# 8. for LLM-assisted development: start the brahman server
python3 tools/read_brahman.py serve &
# then query over socket:
echo '{"command":"test-run","socket":"/tmp/vy.sock","layer":"pipeline"}' \
  | socat - UNIX-CONNECT:/tmp/brahman.sock | jq '{passed,failed,summary}'
```
