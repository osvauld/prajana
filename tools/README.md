# tools/

Analysis, knowledge, and test pipeline tools for the nam proof-graph
reasoning system. Everything runs as `python3 -m tools [mode] [subcmd] [args]`.

These tools read the live codebase and the test result cache — they do not
simulate or approximate. Every number they emit came from an actual run.

---

## quick reference

```bash
# ── static analysis (no server needed) ────────────────────────────────
python3 -m tools tantra summary          # 72 tantras: lines, takes, calls
python3 -m tools tantra lint             # hardcoded refs, word lists, smells
python3 -m tools om summary              # 1614 nodes across 4 layers
python3 -m tools shabda summary          # unified word index + shabda keys + gaps

# ── shabda (word/metadata analysis) ───────────────────────────────────
python3 -m tools shabda summary          # full landscape: words, files, keys, collisions
python3 -m tools shabda lookup heavier   # trace a word to its node + all shabda keys
python3 -m tools shabda lookup died      # find gaps — words the graph doesn't know
python3 -m tools shabda eval             # all 32 fireable operations (nodes with eval:)
python3 -m tools shabda gaps             # nodes that should have word mappings but don't
python3 -m tools shabda words            # word index grouped by domain
python3 -m tools shabda words count      # all words mapping to the 'count' node
python3 -m tools shabda node addition    # full shabda metadata for a node
python3 -m tools shabda files            # list all 17 .shabda template files
python3 -m tools shabda files physics-constants  # show entries in a .shabda file
python3 -m tools shabda search "died|flew|gave"  # search words + .shabda file contents

# ── live graph queries (auto-starts vyakarana server) ─────────────────
python3 -m tools vy eval 'walk "viveka-max" "abheda"'
python3 -m tools vy eval 'shabda "addition" "eval"'
python3 -m tools vy eval 'word-node "many"'
python3 -m tools vy inspect momentum
python3 -m tools vy walk 'viveka-max abheda'
python3 -m tools vy triples mass
python3 -m tools vy mantras 'ball has mass 5 velocity 10. find kinetic energy'
python3 -m tools vy trace 'ball has mass 5 velocity 10. find kinetic energy'

# ── tests ─────────────────────────────────────────────────────────────
python3 -m tools test run                # full v2 suite (98 tests)
python3 -m tools test run pipeline       # one layer
python3 -m tools test run gate:arithmetic  # xfails for a specific gate
python3 -m tools test run test_ke_basic  # one test by name

# ── ask ───────────────────────────────────────────────────────────────
python3 -m tools ask "ball has mass 5 velocity 10. find kinetic energy"

# ── patra (living documentation) ────────────────────────────────────
python3 -m patra glance                 # 20-line LLM context summary
python3 -m patra discover "insight"     # record a discovery
python3 -m patra steps                  # plan steps with status
python3 -m patra topic karaka           # cross-source search
```

---

## package layout

```
tools/
  __main__.py       — entry point (python3 -m tools)
  cli.py            — CLI dispatcher (all modes)
  cli_tantra.py     — tantra subcommands
  cli_om.py         — om subcommands
  cli_shabda.py     — shabda subcommands (word index, gaps, eval, lookup)
  cli_vy.py         — vyakarana live-graph subcommands
  tantras.py        — parse + query 72 .tantra3 files (static)
  om.py             — parse + query 1614 .om files by domain (static)
  shabda.py         — unified shabda analysis: .om inline + .shabda files
  vy.py             — vyakarana socket client
  vyakarana.py      — server lifecycle (start/stop/restart)
  tests.py          — static test discovery (AST parse)
  runner.py         — pytest subprocess wrapper
  cache.py          — pytest result cache read/query/act
  gates.py          — xfail gate definitions
  paths.py          — shared path constants
  server.py         — brahman static knowledge server
  conftest.py       — pytest fixtures + per-test cache writer
  v2/               — the test suite (98 tests)
    test_evaluator.py   — 17 tests: reduce, map, filter, cond, fn, let, fixpoint
    test_graph.py       — 10 tests: walk, walk-in, satya, shabda, stemming
    test_pipeline.py    — 22 tests: bqg, sandhi, avrti, rashi, entity, match
    test_answers.py     — 18 tests: end-to-end sentence -> answer
    test_xfail.py       — 31 tests: features not yet built (the roadmap)
```

---

## modes

### tantra — static tantra analysis

```bash
python3 -m tools tantra summary          # one-line per tantra: lines, takes, bindings
python3 -m tools tantra groups           # 12 tantra groups by function
python3 -m tools tantra all              # dump all tantras with source
python3 -m tools tantra group pipeline   # one group
python3 -m tools tantra source execute-mantra  # one tantra by name
python3 -m tools tantra callgraph        # full call graph + hub tantras
python3 -m tools tantra callers derive-chain   # who calls this tantra
python3 -m tools tantra callees anuvada-ganana # what does this tantra call
python3 -m tools tantra search "viveka"  # regex search across all tantras
python3 -m tools tantra lint             # hardcoded refs, word lists, scan vs reduce
```

### om — static om file analysis

```bash
python3 -m tools om summary              # layer counts + domain tree
python3 -m tools om domains 3            # domain tree at depth 3
python3 -m tools om domain kosha/math    # browse a domain: subdomains + nodes
python3 -m tools om source addition      # dump one om node by name
python3 -m tools om with-key eval        # nodes with a specific shabda key
python3 -m tools om with-relation kriya  # nodes with a specific edge relation
python3 -m tools om search "pratipaksha" # regex search across all om files
```

### shabda — unified word/metadata analysis

Unifies both sources of shabda data:
- **inline shabda** in 1614 .om files (`shabda word:x,y eval:add arity:2 ...`)
- **17 .shabda template files** (physics-constants, matra-aayaama, anuvada-setu, ...)

```bash
python3 -m tools shabda summary          # full landscape
python3 -m tools shabda lookup WORD      # trace word -> node + all shabda keys
python3 -m tools shabda eval             # 32 fireable operations (eval: nodes)
python3 -m tools shabda gaps             # nodes missing word: declarations
python3 -m tools shabda words            # word index by domain
python3 -m tools shabda words NODE       # all words mapping to a node
python3 -m tools shabda node NODE        # full shabda metadata for one node
python3 -m tools shabda files            # list .shabda template files
python3 -m tools shabda files NAME       # show entries in a .shabda file
python3 -m tools shabda search PATTERN   # search words + .shabda file contents
```

**Key capabilities:**

| command | what it answers |
|---------|----------------|
| `shabda summary` | How many words does the graph know? What keys exist? Any collisions? |
| `shabda lookup died` | Does the graph know this word? If not, what's close? |
| `shabda eval` | What operations can be fired? What words trigger them? |
| `shabda gaps` | Which nodes should have words but don't? (eval: without word:) |
| `shabda words count` | What words all map to the `count` node? |
| `shabda node addition` | What's the full shabda on `addition`? eval, arity, inverse, edges? |

### vy — live graph queries

Requires the vyakarana server (auto-started by the tool).

```bash
python3 -m tools vy eval '<expr>'        # evaluate any tantra expression
python3 -m tools vy inspect <node>       # full node: satya, shabda keys, edges
python3 -m tools vy walk '<node> <rel>'  # transitive chain walk
python3 -m tools vy triples <node>       # all triples touching a node
python3 -m tools vy mantras '<sentence>' # which mantras fire and why
python3 -m tools vy trace '<sentence>'   # pipeline stages with +/- triple diff
```

### test — test discovery and execution

```bash
python3 -m tools test summary            # 98 total / 67 passing / 31 xfail
python3 -m tools test list               # all tests with xfail gates
python3 -m tools test run                # run everything
python3 -m tools test run pipeline       # one layer
python3 -m tools test run gate:arithmetic  # xfails for a feature gate
python3 -m tools test run test_ke_basic  # one test by name
```

### cache — test result analysis

```bash
python3 -m tools cache summary           # passed/failed/xfailed + gates + slow calls
python3 -m tools cache failed            # all failures with diagnosis + call chain
python3 -m tools cache gates             # xfail gates with test counts
python3 -m tools cache gates arithmetic  # tests in one gate
python3 -m tools cache slow              # slowest calls and tests
python3 -m tools cache diff /tmp/old.json  # compare against previous run
python3 -m tools cache fix-xpass         # find tests that now pass (dry run)
python3 -m tools cache fix-xpass --apply # actually remove @xfail markers
```

### search — cross-cutting search

```bash
python3 -m tools search "viveka"         # search both tantras AND om files
```

---

## test suite (v2)

**Current baseline:** 67 passed / 31 xfailed / 0 failing (98 total)

| layer | tests | what it covers |
|---|---|---|
| `evaluator` | 17 | reduce, map, filter, cond, fn, let, from/where, fixpoint, arithmetic |
| `graph` | 10 | walk, walk-in, node-satya, shabda lookup, plural stemming, abbreviation |
| `pipeline` | 22 | bqg, sandhi, avrti-refine, rashi, entity scope, match, agra-bandha |
| `answers` | 18 | end-to-end: sentence -> answer, strands, multi-turn, comparison |
| `xfail` | 31 | features not yet built (the roadmap) |

**Xfail gates:**

| gate | tests | needs |
|---|---|---|
| `arithmetic` | 4 | count add/subtract via kosha, distance, area |
| `dvandva` | 3 | per-entity derive + variadic sum |
| `inverse_math` | 3 | bound-vals / invert-math path |
| `sthita_viveka` | 2 | multi-slot entity assignment |
| `compute_compare` | 2 | compute-then-compare viveka |
| `transitive` | 2 | graph-walk chain inference |
| `motion_verb` | 3 | 'moves at' / 'moving at' -> velocity signal |
| `from_rest` | 2 | 'from rest' -> initial-velocity = 0 |
| `syllogism` | 1 | modus-ponens + assertion chain |
| `proportional` | 1 | proportional reasoning |
| `compound_trigram` | 2 | three-word compounds |
| `colour_classifier` | 2 | colour words as entity discriminators |
| `article` | 1 | 'the electron' article transparency |
| `relative_velocity` | 1 | relative-velocity kosha concept |

---

## typical workflow

```bash
# 1. understand what you're about to change
python3 -m tools tantra source derive-chain
python3 -m tools tantra callers derive-chain
python3 -m tools shabda node addition
python3 -m tools shabda lookup remaining

# 2. run relevant tests before changing anything
python3 -m tools test run pipeline
python3 -m tools cache summary

# 3. make your change (tantra, om, or OCaml)
#    for OCaml: dune build from vyakarana/ then restart server

# 4. run targeted tests
python3 -m tools test run test_ke_basic
python3 -m tools test run pipeline

# 5. if a gate is now implemented, run its xfails
python3 -m tools test run gate:arithmetic

# 6. full suite
python3 -m tools test run

# 7. if any xfails now pass, remove their markers
python3 -m tools cache fix-xpass
python3 -m tools cache fix-xpass --apply
```

---

## shabda landscape

The word/metadata system has three sources:

1. **Inline shabda in .om files** — 220 nodes declare `word:` keys, mapping
   English words to graph concepts. 32 nodes have `eval:` (fireable operations).
   Example: `shabda word:plus eval:add arity:2 inverse:subtraction`

2. **17 .shabda template files** — standalone key:value tables for constants,
   unit dimensions, grammar labels, and code-generation bridges.
   Linked from .om nodes via `shabda-tmpl:physics` etc.

3. **The engine's word index** — built at boot from all `word:` declarations.
   `word-node "heavier"` -> `viveka-max`. `shabda-anveshana "birds"` -> `bird`.

Use `python3 -m tools shabda summary` to see the full picture.
Use `python3 -m tools shabda gaps` to find where word mappings are missing.
Use `python3 -m tools shabda lookup WORD` to trace any word through the system.

---

## patra — living documentation

Separate package at `patra/`. See `patra/README.md` for full docs.

```bash
python3 -m patra glance                         # compact LLM context summary
python3 -m patra discover "insight text"         # record a discovery
python3 -m patra step-add "step title" --doc plan  # add plan step
python3 -m patra step-done STEP_ID "note"        # mark step complete
python3 -m patra baseline 85 35 0                # update test baseline
python3 -m patra search "pattern"                # regex search across docs
python3 -m patra topic karaka                    # cross-source: patra + om + tantras
python3 -m patra steps                           # plan steps with status
python3 -m patra index                           # full TOC with live stats
python3 -m patra report                          # analysis report
python3 -m patra emit md                         # generate .md files from state
```
