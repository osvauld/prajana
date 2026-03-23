# upakarana/

Modular analysis, engine, and test pipeline for the nam proof-graph. Replaces `tools/`.

Everything runs as `.venv/bin/python3 -m upakarana [cmd] [action] [args]`.

---

## quick reference

```bash
# static analysis (no server needed)
.venv/bin/python3 -m upakarana om summary
.venv/bin/python3 -m upakarana om source addition
.venv/bin/python3 -m upakarana om search "pratipaksha"
.venv/bin/python3 -m upakarana om domain kosha/math
.venv/bin/python3 -m upakarana om with-relation kriya

.venv/bin/python3 -m upakarana tantra summary
.venv/bin/python3 -m upakarana tantra source execute-mantra
.venv/bin/python3 -m upakarana tantra search "viveka"
.venv/bin/python3 -m upakarana tantra group pipeline
.venv/bin/python3 -m upakarana tantra callgraph

.venv/bin/python3 -m upakarana shabda summary
.venv/bin/python3 -m upakarana shabda node addition
.venv/bin/python3 -m upakarana shabda search "eval"
.venv/bin/python3 -m upakarana shabda gaps

.venv/bin/python3 -m upakarana search "viveka"
.venv/bin/python3 -m upakarana lint
.venv/bin/python3 -m upakarana health

# live graph queries (auto-starts vyakarana server)
.venv/bin/python3 -m upakarana vy eval 'walk "viveka-max" "abheda"'
.venv/bin/python3 -m upakarana vy inspect momentum
.venv/bin/python3 -m upakarana vy walk mass swarupa
.venv/bin/python3 -m upakarana vy ask "mass is 5 velocity is 10. find kinetic energy"

# graph analysis
.venv/bin/python3 -m upakarana a ghosts
.venv/bin/python3 -m upakarana a ring
.venv/bin/python3 -m upakarana a hubs
.venv/bin/python3 -m upakarana a components
.venv/bin/python3 -m upakarana a signals
.venv/bin/python3 -m upakarana a patterns

# ocaml analysis
.venv/bin/python3 -m upakarana ocaml report

# query primitives
.venv/bin/python3 -m upakarana q overview
.venv/bin/python3 -m upakarana q node velocity
.venv/bin/python3 -m upakarana q op addition

# live analysis
.venv/bin/python3 -m upakarana live drift
.venv/bin/python3 -m upakarana live pratipaksha
.venv/bin/python3 -m upakarana live signal-trace

# tests
.venv/bin/python3 -m upakarana test run
.venv/bin/python3 -m upakarana test run pipeline
.venv/bin/python3 -m upakarana test run gate:arithmetic
.venv/bin/python3 -m upakarana cache summary
.venv/bin/python3 -m upakarana cache gates

# usage
.venv/bin/python3 -m upakarana usage report
.venv/bin/python3 -m upakarana usage never
```

---

## package layout

```
upakarana/
  __init__.py       — package init
  __main__.py       — entry point
  cli.py            — unified CLI dispatcher (14 commands)
  query.py          — composable query API (LLM-friendly)
  usage.py          — usage tracking (shared with pathram2)
  paths.py          — shared path constants
  parsers/
    om5.py          — .om5 s-expression parser
    tantra4.py      — .tantra4/.prakriya parser
    shabda.py       — .shabda s-expression parser
  engine/
    server.py       — vyakarana server lifecycle
    client.py       — unix socket client (JSON protocol)
  analysis/
    ghosts.py       — ghost nodes (referenced but undefined)
    edges.py        — edge analysis + reverse lookups
    layers.py       — cross-layer edge flow
    chains.py       — swarupa walks, connected components
    ring.py         — visheshanam ring axiom verification
    signals.py      — signal flow tracing
    tantras.py      — pattern classification
    ocaml.py        — OCaml codebase analysis
    static.py       — lint, dead code, complexity
    live.py         — live graph analysis
    health.py       — combined health report
  testing/
    discover.py     — test discovery (AST parse)
    run.py          — pytest subprocess wrapper
    cache.py        — test result cache read/query
    gates.py        — xfail gate definitions
  data/
    usage.json      — command usage tracking
```

---

## modes

### om — static om5 analysis

```bash
om summary              # node counts by layer + domain
om source NAME          # dump one node
om search PATTERN       # regex search
om domain PATH          # browse domain subtree
om with-relation REL    # nodes with edge type
```

### tantra — static tantra4 analysis

```bash
tantra summary          # all tantras with line counts
tantra source NAME      # dump one tantra
tantra search PATTERN   # regex search
tantra group [NAME]     # by function group
tantra callgraph        # call graph + hubs
```

### shabda — word/metadata analysis

```bash
shabda summary          # word index, keys, collisions
shabda node NAME        # full metadata for one node
shabda search PATTERN   # search words + shabda files
shabda gaps             # nodes with kriya/phala but no shabda
```

### vy — live engine

```bash
vy start                # start server
vy stop                 # stop server
vy status               # health check
vy reload               # reload graph data
vy eval EXPR            # evaluate expression
vy ask QUESTION         # NLP question
vy walk NODE REL        # edge walk
vy inspect NODE         # full node dump
```

### test — test suite

```bash
test summary            # counts by layer
test list               # all tests with gates
test run [FILTER]       # run (layer, gate:NAME, test name)
test failed             # show failures
```

### cache — test results

```bash
cache summary           # pass/fail/xfail breakdown
cache gates [NAME]      # gate breakdown
cache slow              # slowest calls
```

### a — graph analysis

```bash
a ghosts                # referenced but undefined nodes
a incoming NODE         # reverse edge lookup
a hubs                  # most connected
a orphans               # unconnected nodes
a flow                  # cross-layer edge flow
a ring                  # visheshanam ring axioms
a components            # connected components
a signals               # signal flow
a patterns              # pattern classification
a swarupa               # swarupa chain analysis
a fingerprint           # graph fingerprint
a vocabulary            # vocabulary coverage
a grounding             # grounding analysis
a siblings              # sibling analysis
```

### ocaml — OCaml analysis

```bash
ocaml report            # full report
ocaml darshana          # darshana analysis
ocaml patterns          # patterns
ocaml coupling          # module coupling
ocaml functions         # function listing
```

### q — query primitives

```bash
q overview              # system overview
q node NAME             # node details
q op NAME               # operation metadata
q ops                   # all operations
q dispatch              # dispatch table
q missing               # missing mappings
q eval EXPR             # evaluate
```

### live — live graph analysis

```bash
live drift              # drift detection
live pratipaksha        # pratipaksha analysis
live signal-trace       # signal tracing
live panchaavayava      # panchaavayava check
```

### Other

```bash
search PATTERN          # cross-search tantras + om
lint                    # static lint
health                  # combined health report
usage report            # usage statistics
usage never             # commands never used
```

---

## usage tracking

Every CLI invocation is automatically tracked in `upakarana/data/usage.json`. pathram2 commands are also tracked in the same file. Check with:

```bash
.venv/bin/python3 -m upakarana usage report    # top commands, totals
.venv/bin/python3 -m upakarana usage never     # commands you haven't tried
```
