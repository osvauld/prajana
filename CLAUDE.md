# Agent-X — LLM Protocol

## Environment

Always use the project venv for all Python commands:

```bash
.venv/bin/python3 -m upakarana2 [cmd] [action] [args]
.venv/bin/python3 -m pathram2 [cmd] [args]
```

Never use system python. Never use `python3 -m upakarana`, `python3 -m tools`, or `python3 -m patra` — those are deprecated.

## Build

```bash
cd vyakarana && dune build && cd ..
```

---

## Starting a session

**Always run this first** at the start of any non-trivial conversation:

```bash
.venv/bin/python3 -m pathram2 context
```

This gives you: current open session, open branches (tangents in progress), pending steps, recent sessions, and recent discoveries — everything needed to orient yourself before doing any work.

---

## Tooling: upakarana2 (analysis + engine)

All graph analysis, tantra inspection, shabda queries, live engine interaction, and testing goes through upakarana2. Usage is tracked automatically. Always use the CLI; do not read .om/.tantra files directly with cat/Read when upakarana2 can surface the same information.

### Commands

| command | what it does |
|---------|-------------|
| `om summary` | Node counts by layer + domain tree |
| `om source NAME` | Dump one .om node |
| `om search PATTERN` | Regex across all om files |
| `om domain PATH` | Browse a domain subtree |
| `om with-relation REL` | Nodes with a specific edge type |
| `tantra summary` | All tantras with line counts |
| `tantra source NAME` | Dump one tantra |
| `tantra search PATTERN` | Regex across all tantras |
| `tantra group [NAME]` | Tantras grouped by function |
| `tantra callgraph` | Full call graph + hub tantras |
| `tantra reachability NAME` | What a tantra can reach |
| `shabda summary` | Word index, keys, collisions |
| `shabda node NAME` | Full shabda metadata for one node |
| `shabda search PATTERN` | Search words + shabda files |
| `shabda gaps` | Nodes with kriya/phala but no shabda |
| `vy start` | Start vyakarana server |
| `vy stop` | Stop server |
| `vy status` | Server health |
| `vy reload` | Reload graph data |
| `vy eval EXPR` | Evaluate tantra expression |
| `vy ask QUESTION` | Ask a natural language question |
| `vy walk NODE REL` | Walk edges from a node |
| `vy inspect NODE` | Full node: satya, shabda, edges |
| `vy drift` | Live drift detection |
| `vy pratipaksha` | Live pratipaksha analysis |
| `vy signal-trace` | Live signal tracing |
| `vy panchaavayava` | Live panchaavayava check |
| `test list` | All tests with xfail gates |
| `test summary` | Test counts by layer |
| `test run [FILTER]` | Run tests (layer, gate:NAME, test name) |
| `test failed` | Show last run failures |
| `cache summary` | Pass/fail/xfail + gates + slow calls |
| `cache gates [NAME]` | Xfail gates breakdown |
| `cache slow` | Slowest calls and tests |
| `search PATTERN` | Cross-search tantras + om files |
| `lint` | Static lint (hardcoded refs, smells) |
| `health` | Combined health report |
| `a ghosts` | Ghost nodes (referenced but undefined) |
| `a incoming NODE` | Reverse edge lookup |
| `a hubs` | Most-connected nodes |
| `a orphans` | Unconnected nodes |
| `a flow` | Cross-layer edge flow |
| `a ring` | Visheshanam ring axiom verification |
| `a components` | Connected components |
| `a swarupa` | Swarupa chain analysis |
| `a signals` | Signal producer/consumer map |
| `a signals-gap` | Dead signals (dispatch wiring gaps) |
| `a compose` | Compound node overview |
| `a compose-gen` | Generatability: auto/semi/manual |
| `a compose-inverse` | Pratipaksha pair completeness |
| `a gen-gaps [DOMAIN]` | Missing compound nodes |
| `a gen-validate NAME` | Validate one compound vs expected |
| `ocaml report` | OCaml codebase analysis |
| `ocaml darshana` | Darshana analysis |
| `ocaml patterns` | Pattern detection |
| `ocaml coupling` | Module coupling |
| `ocaml functions` | Function listing |
| `usage report` | Usage statistics |
| `usage never` | Commands never used |

---

## Tooling: pathram2 (documentation + journaling)

pathram2 is a graph-native knowledge tracker. Use it to document sessions, record discoveries, track steps, and maintain a living journal. Node IDs and name slugs are interchangeable in all commands that take a node argument.

### Naming convention

Prefer descriptive IDs for important nodes. Use `--name slug` (or `--id slug`) when creating nodes that will be referenced repeatedly:

```bash
.venv/bin/python3 -m pathram2 add step "Migrate shabda to graph" --name step-shabda-migration --status pending
.venv/bin/python3 -m pathram2 show step-shabda-migration   # works by slug
```

### Commands

| command | what it does |
|---------|-------------|
| `context [--json]` | **LLM startup dump**: session + branches + pending steps + recent discoveries |
| `cleanup [--json]` | **Workflow health**: open sessions, tangent branches in flight, pending steps, steps missing status |
| `usage [report\|reset] [--json]` | Command usage statistics (which commands are called, how often) |
| `glance [--json]` | Quick summary: node counts, pending steps, open branches |
| `add TYPE TITLE [--name SLUG] [--body] [--tag] [--parent] [--session] [--status]` | Create a node. Types: `discovery` (non-obvious finding), `step` (action item, add `--status pending\|done`), `quirk` (gotcha), `note` (detail, attach with `--parent`), `doc` (container) |
| `show ID\_OR\_NAME [--json]` | Display node + edges |
| `update ID\_OR\_NAME [--title] [--body] [--tag] [--status] [--name]` | Modify a node |
| `delete ID\_OR\_NAME` | Remove node and edges |
| `resolve NAME [--json]` | Resolve a slug → node ID |
| `link SRC TGT REL [--reason]` | Create an edge (src/tgt accept slugs) |
| `unlink SRC TGT [REL]` | Remove edge(s) |
| `walk ID\_OR\_NAME REL [--incoming] [--json]` | Follow edges |
| `search PATTERN [--json]` | Regex on titles/bodies |
| `steps [--pending] [--done] [--status S] [--tag T] [--json] [--verbose]` | List steps |
| `session-start TITLE [--id]` | Begin a session |
| `session-end [ID\_OR\_NAME]` | End current session |
| `journal [-n N] [--json]` | Last N sessions |
| `today [--json]` | Nodes created/updated today |
| `branch FROM REASON TITLE` | Create tangent from a node (from accepts slug) |
| `return ID\_OR\_NAME [--session-id]` | Mark return to original task |
| `branches [--json]` | Show open branches |
| `tree [ROOT]` | Visualize branch DAG |
| `merge IDS... --into TYPE --title TITLE` | Consolidate nodes |
| `stale DAYS [--json]` | Untouched nodes |
| `abandoned [--days N] [--json]` | Stale pending steps |
| `query EXPRS... [--json] [--count] [--ids] [--verbose]` | Composable query |
| `relations` | List all 16 relation types |
| `types` | List node types + tags |

### Relations

Core 10 visheshanam: `swarupa`, `abheda`, `drishthanta`, `sthita`, `yukta`, `siddha`, `kriya`, `phala`, `janya`, `pratipaksha`

Extensions: `krama`, `branches-from`, `returns-to`, `fixes`, `references`, `depends-on`

### Node types

`philosophy`, `discovery`, `session`, `step`, `branch`, `note`, `quirk`, `report`, `doc`

### Tags

`active`, `done`, `consolidated`, `abandoned`, `wrong`, `deferred`

### `query` expression syntax

```bash
.venv/bin/python3 -m pathram2 query type=step shabda.status=pending sort=created_at --json
.venv/bin/python3 -m pathram2 query type=discovery search=vibhakti rsort=created_at limit=5
.venv/bin/python3 -m pathram2 query type=step node=plan-nlp descendants=sthita --count
```

Supported keys: `type`, `tag`, `shabda.KEY`, `search`, `since`, `before`, `stale`, `walk`, `walk_in`, `descendants`, `ancestors`, `sort`, `rsort`, `limit`, `node`

---

## Protocol: session start

```bash
# 1. Get full context (open branches, pending steps, recent work)
.venv/bin/python3 -m pathram2 context

# 2. Start a session with a descriptive title
.venv/bin/python3 -m pathram2 session-start "topic: what you are doing"
```

## Protocol: analyzing .om files

1. **Read the node**: `.venv/bin/python3 -m upakarana2 om source <name>`
2. **Check edges** (if relevant): `.venv/bin/python3 -m upakarana2 om with-relation <rel>`
3. **Check shabda metadata**: `.venv/bin/python3 -m upakarana2 shabda node <name>`
4. **Live inspection** (if server running): `.venv/bin/python3 -m upakarana2 vy inspect <name>`
5. **Document** if the analysis reveals something non-obvious:
   `.venv/bin/python3 -m pathram2 add discovery "<title>" --body "<finding>"`

## Protocol: analyzing .tantra files

1. **Read the tantra**: `.venv/bin/python3 -m upakarana2 tantra source <name>`
2. **Understand dependencies**: `.venv/bin/python3 -m upakarana2 tantra callgraph`
3. **Test live** (if server running): `.venv/bin/python3 -m upakarana2 vy eval '<expr>'`
4. **Document** if modifying: `.venv/bin/python3 -m pathram2 add step "<what>" --body "<why>"`

## Protocol: documentation during work

**Node type decision guide** — use the right type, not just `discovery`:

| What happened | Type to use | Example |
|---|---|---|
| Starting work | `session-start` | The session IS the journal entry |
| Found something non-obvious about the codebase | `discovery` | "shunya-bandha walks sthita not abheda" |
| Work to be done | `step --status pending` | "migrate shabda keys" |
| Work just completed | `step --status done` | update existing step |
| A gotcha to avoid repeating | `quirk` | "nested cond causes parse_expr:empty" |
| Implementation detail on a node | `note --parent <id>` | attach to the node it describes |
| Status update / what happened | **session title + body** | `session-start "fixed X by doing Y"` |

**DO NOT** use `discovery` as a catch-all journal entry. A discovery is a finding — something that would surprise someone reading the codebase. Session titles and bodies are the journal.

- **Before starting a non-trivial session**: `pathram2 session-start "<what you're doing>"`
- **Record non-obvious codebase findings**: `pathram2 add discovery "<title>" --body "<details>" --session <id>`
- **Record gotchas**: `pathram2 add quirk "<title>" --body "<details>"`
- **Branching to a tangent**: `pathram2 branch <from-id-or-name> "<reason>" "<title>"`
- **Returning from tangent**: `pathram2 return <origin-id>`
- **End session**: `pathram2 session-end`
- **Workflow health check**: `pathram2 cleanup`
- **Quick status**: `pathram2 glance`
- **Full LLM context**: `pathram2 context`
- **Review journal**: `pathram2 journal`

## Protocol: running tests

```bash
.venv/bin/python3 -m upakarana2 test run                 # full suite
.venv/bin/python3 -m upakarana2 test run pipeline         # one layer
.venv/bin/python3 -m upakarana2 test run gate:arithmetic  # xfails for a gate
.venv/bin/python3 -m upakarana2 test run test_ke_basic    # one test
.venv/bin/python3 -m upakarana2 cache summary             # results analysis
```

---

## Typical workflow

```bash
# 0. Orient yourself
.venv/bin/python3 -m pathram2 context

# 1. Start a session
.venv/bin/python3 -m pathram2 session-start "investigating X"

# 2. Understand what you're about to change
.venv/bin/python3 -m upakarana2 tantra source derive-chain
.venv/bin/python3 -m upakarana2 shabda node addition
.venv/bin/python3 -m upakarana2 vy inspect momentum

# 3. Run relevant tests before changing anything
.venv/bin/python3 -m upakarana2 test run pipeline
.venv/bin/python3 -m upakarana2 cache summary

# 4. Make your change (tantra, om, or OCaml)
#    for OCaml: cd vyakarana && dune build && cd .. then vy reload

# 5. Document what you found/changed
.venv/bin/python3 -m pathram2 add discovery "title" --body "details"

# 6. Run targeted tests
.venv/bin/python3 -m upakarana2 test run test_ke_basic

# 7. Full suite
.venv/bin/python3 -m upakarana2 test run

# 8. End session
.venv/bin/python3 -m pathram2 session-end

# 9. Check usage
.venv/bin/python3 -m upakarana2 usage report
```
