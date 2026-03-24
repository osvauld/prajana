# Agent-X — LLM Protocol

## Environment

Always use the project venv for all Python commands:

```bash
.venv/bin/python3 -m upakarana [cmd] [action] [args]
.venv/bin/python3 -m pathram2 [cmd] [args]
```

Never use system python. Never use `python3 -m tools` or `python3 -m patra` — those are deprecated.

## Build

```bash
cd vyakarana && dune build && cd ..
```

---

## Tooling: upakarana (analysis + engine)

All graph analysis, tantra inspection, shabda queries, live engine interaction, and testing goes through upakarana. Usage is tracked automatically — every CLI call increments counters in `upakarana/data/usage.json`. Always use the CLI; do not read .om/.tantra files directly with cat/Read when upakarana can surface the same information. This keeps usage data accurate.

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
| `test summary` | Test counts by layer |
| `test list` | All tests with xfail gates |
| `test run [FILTER]` | Run tests (layer, gate:NAME, test name) |
| `test failed` | Show failures |
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
| `a signals` | Signal flow tracing |
| `a patterns` | Pattern classification |
| `a swarupa` | Swarupa chain analysis |
| `a fingerprint` | Graph fingerprint |
| `a vocabulary` | Vocabulary coverage |
| `a grounding` | Grounding analysis |
| `a siblings` | Sibling node analysis |
| `a compose` | Composition overview (compounds, bases, chains) |
| `a compose-gen` | Generatability: auto/semi/manual classification |
| `a compose-curated` | Curated validity matrix for generation |
| `a compose-inherit` | Edge inheritance analysis per compound |
| `a compose-rules` | Which relations inherit vs override |
| `a compose-words` | Shabda/word coverage gaps |
| `a compose-logic` | Logic node generation plan |
| `a compose-lift` | Space-lift analysis (scalar→vec/mat/complex) |
| `a compose-inverse` | Pratipaksha pair completeness |
| `ocaml report` | OCaml codebase analysis |
| `ocaml darshana` | Darshana analysis |
| `ocaml patterns` | Pattern detection |
| `ocaml coupling` | Module coupling |
| `ocaml functions` | Function listing |
| `q op NAME` | Operation metadata |
| `q ops` | All operations |
| `q node NAME` | Graph node details |
| `q dispatch` | Dispatch table |
| `q missing` | Missing mappings |
| `q overview` | System overview |
| `q eval EXPR` | Evaluate expression |
| `live drift` | Live drift detection |
| `live pratipaksha` | Live pratipaksha analysis |
| `live signal-trace` | Live signal tracing |
| `live panchaavayava` | Live panchaavayava check |
| `usage report` | Usage statistics |
| `usage never` | Commands never used |

---

## Tooling: pathram2 (documentation + journaling)

pathram2 is a graph-native knowledge tracker. Use it to document analysis sessions, record discoveries, track steps, and maintain a living journal of work. Its usage is also tracked in the shared usage.json.

### Commands

| command | what it does |
|---------|-------------|
| `add TYPE TITLE [--body] [--tag] [--parent] [--session] [--status]` | Create a node (types: philosophy, discovery, session, step, branch, note, quirk, report, doc) |
| `show ID` | Display node + edges |
| `update ID [--title] [--body] [--tag] [--status]` | Modify a node |
| `delete ID` | Remove node and edges |
| `link SRC TGT REL [--reason]` | Create an edge |
| `unlink SRC TGT [REL]` | Remove edge(s) |
| `walk ID REL [--incoming]` | Follow edges |
| `search PATTERN` | Regex on titles/bodies |
| `steps [--status] [--tag]` | List steps |
| `session-start TITLE [--id]` | Begin a session |
| `session-end [ID]` | End current session |
| `journal [-n N]` | Last N sessions |
| `today` | Nodes created/updated today |
| `branch FROM REASON TITLE` | Create tangent from a node |
| `return ID [--session-id]` | Mark return to original task |
| `branches` | Show open branches |
| `tree [ROOT]` | Visualize branch DAG |
| `merge IDS... --into TYPE --title TITLE` | Consolidate nodes |
| `stale DAYS` | Untouched nodes |
| `abandoned [--days N]` | Stale pending steps |
| `glance` | Quick summary |
| `query EXPRS... [--json] [--count] [--ids] [--verbose]` | Composable query |
| `relations` | List all 16 relation types |
| `types` | List node types + tags |

### Relations

Core 10 visheshanam: swarupa, abheda, drishthanta, sthita, yukta, siddha, kriya, phala, janya, pratipaksha
Extensions: krama, branches-from, returns-to, fixes, references, depends-on

### Node types

philosophy, discovery, session, step, branch, note, quirk, report, doc

### Tags

active, done, consolidated, abandoned, wrong, deferred

---

## Protocol: analyzing .om files

When examining an om node, follow these steps:

1. **Read the node**: `.venv/bin/python3 -m upakarana om source <name>`
2. **Check edges** (if relevant): `.venv/bin/python3 -m upakarana om with-relation <rel>`
3. **Check shabda metadata**: `.venv/bin/python3 -m upakarana shabda node <name>`
4. **Live inspection** (if server running): `.venv/bin/python3 -m upakarana vy inspect <name>`
5. **Document** if the analysis reveals something non-obvious:
   `.venv/bin/python3 -m pathram2 add discovery "<title>" --body "<finding>"`

## Protocol: analyzing .tantra files

When examining a tantra, follow these steps:

1. **Read the tantra**: `.venv/bin/python3 -m upakarana tantra source <name>`
2. **Understand dependencies**: `.venv/bin/python3 -m upakarana tantra callgraph` or use callers/callees for one tantra
3. **Test live** (if server running): `.venv/bin/python3 -m upakarana vy eval '<expr>'`
4. **Document** if modifying: `.venv/bin/python3 -m pathram2 add step "<what>" --body "<why>"`

## Protocol: documentation during work

- **Before starting a non-trivial session**: `.venv/bin/python3 -m pathram2 session-start "<topic>"`
- **Record discoveries**: `.venv/bin/python3 -m pathram2 add discovery "<title>" --body "<details>"`
- **Record quirks/gotchas**: `.venv/bin/python3 -m pathram2 add quirk "<title>" --body "<details>"`
- **Branching to a tangent**: `.venv/bin/python3 -m pathram2 branch <from> "<reason>" "<title>"`
- **End session**: `.venv/bin/python3 -m pathram2 session-end`
- **Quick status**: `.venv/bin/python3 -m pathram2 glance`
- **What happened today**: `.venv/bin/python3 -m pathram2 today`
- **Review journal**: `.venv/bin/python3 -m pathram2 journal`

## Protocol: running tests

```bash
.venv/bin/python3 -m upakarana test run                 # full suite
.venv/bin/python3 -m upakarana test run pipeline         # one layer
.venv/bin/python3 -m upakarana test run gate:arithmetic  # xfails for a gate
.venv/bin/python3 -m upakarana test run test_ke_basic    # one test
.venv/bin/python3 -m upakarana cache summary             # results analysis
```

---

## Typical workflow

```bash
# 1. start a session
.venv/bin/python3 -m pathram2 session-start "investigating X"

# 2. understand what you're about to change
.venv/bin/python3 -m upakarana tantra source derive-chain
.venv/bin/python3 -m upakarana shabda node addition
.venv/bin/python3 -m upakarana vy inspect momentum

# 3. run relevant tests before changing anything
.venv/bin/python3 -m upakarana test run pipeline
.venv/bin/python3 -m upakarana cache summary

# 4. make your change (tantra, om, or OCaml)
#    for OCaml: dune build from vyakarana/ then reload

# 5. document what you found/changed
.venv/bin/python3 -m pathram2 add discovery "title" --body "details"

# 6. run targeted tests
.venv/bin/python3 -m upakarana test run test_ke_basic

# 7. full suite
.venv/bin/python3 -m upakarana test run

# 8. end session
.venv/bin/python3 -m pathram2 session-end

# 9. check usage
.venv/bin/python3 -m upakarana usage report
```
