# pathram/

Living documentation system for the agent-x project. All documentation lives
in structured state — markdown files are emitted views, never edited directly.

Runs as `python3 -m pathram [command] [args]` or imported as `from pathram import discover`.

---

## quick reference

```bash
# ── record things as you work ───────────────────────────────────────
python3 -m pathram discover "karaka was already in sangati roots"
python3 -m pathram note "nested cond causes parse_expr:empty" --type quirk
python3 -m pathram step-add "Dravya promotion guards" --doc 18-impl
python3 -m pathram step-done 18-impl.step-1 "routing working"
python3 -m pathram baseline 85 35 0

# ── query what you have ─────────────────────────────────────────────
python3 -m pathram glance                     # 20-line LLM context summary
python3 -m pathram search "karaka"            # full-text regex search
python3 -m pathram steps                      # plan steps with status
python3 -m pathram topic karaka               # cross-source: entries + om + tantras + shabda

# ── emit views ──────────────────────────────────────────────────────
python3 -m pathram show 18-impl              # render one doc as markdown
python3 -m pathram emit md --out /tmp/docs   # write all docs as .md files
python3 -m pathram index                     # full TOC with live stats
python3 -m pathram report                    # analysis: staleness, coverage, refs
```

---

## when to use pathram

- **Recording a discovery or insight** — `pathram discover "..."`
- **Tracking plan steps** — `pathram step-add`, `pathram step-done`, `pathram step-update`
- **Noting a quirk or gotcha** — `pathram note "..." --type quirk`
- **Marking something wrong or superseded** — `pathram wrong`, `pathram supersede`
- **Updating the test baseline** — `pathram baseline 85 35 0`
- **Getting context before starting work** — `pathram glance`
- **Finding what you wrote about a topic** — `pathram search`, `pathram topic`
- **Generating documentation** — `pathram emit md`

## when NOT to use pathram

- **Don't edit the emitted .md files** — they are regenerated from state
- **Don't store code patterns or architecture** — read the code directly
- **Don't duplicate git history** — use `git log` / `git blame`
- **Don't store debugging solutions** — the fix is in the code
- **Don't track ephemeral task state** — pathram is for durable knowledge

---

## content types

| Type | What | Command |
|------|------|---------|
| **discovery** | An insight learned during work | `pathram discover "..."` |
| **step** | A unit of work with status | `pathram step-add "..."` |
| **philosophy** | Enduring understanding | `pathram add-section doc "..." --type philosophy` |
| **changelog** | What happened in a session | `pathram add-section doc "..." --type changelog` |
| **principle** | A numbered structural rule | `pathram add-section doc "..." --type principle` |
| **gap** | Something known to be missing | `pathram add-section doc "..." --type gap` |
| **quirk** | A codebase behavior worth remembering | `pathram note "..." --type quirk` |

---

## lifecycle tags

Every entry has a tag that tracks its status:

| Tag | Meaning |
|-----|---------|
| **active** | Current understanding (default) |
| **provisional** | New, not yet validated |
| **historical** | Completed, kept for reference |
| **superseded** | Replaced — pointer to replacement |
| **wrong** | Incorrect — pointer to correction |
| **deprecated** | True but no longer the approach |
| **deferred** | Intentionally postponed |

```bash
pathram tag 18-impl.step-3 provisional
pathram wrong 17a.section-3 --correction 18.insight-5
pathram supersede 17a --by 18-philosophy
```

---

## all commands

### mutations — record things

```bash
pathram discover "insight text"                  # record a discovery
pathram step-add "step title" --doc plan         # add a plan step
pathram step-done STEP_ID "completion note"      # mark step complete
pathram step-update STEP_ID --status next        # change step status (next/pending/blocked)
pathram baseline 85 35 0                         # update test baseline (passed xfailed failed)
pathram note "text" --type quirk                 # record a quirk/note/gap
pathram add-section DOC_ID "title" --after 3.0   # add section to a doc
pathram tag ENTRY_ID provisional                 # set lifecycle tag
pathram wrong ENTRY_ID --correction OTHER_ID     # mark wrong + link to correction
pathram supersede ENTRY_ID --by OTHER_ID         # mark superseded + link
pathram ref FROM_ID TO_ID --type link            # add cross-reference
pathram ref FROM_ID om:karaka                    # ref to om node
pathram ref FROM_ID ext:https://example.com      # ref to external doc
pathram create-doc DOC_ID "Title"                # create a new document container
pathram session-start "session title" --id 20    # start a session
pathram session-end 20                           # end a session
```

### queries — find things

```bash
pathram glance                                   # compact 20-line LLM summary
pathram index                                    # full TOC with status + live stats
pathram search "pattern"                         # regex across all titles and bodies
pathram show DOC_ID                              # render one doc as markdown
pathram topic NAME                               # cross-source: pathram + om + tantras + shabda
pathram steps                                    # all plan steps with status
pathram steps --status pending                   # filter by status
pathram tagged superseded                        # all entries with a given tag
pathram session 19                               # everything from session 19
pathram timeline                                 # chronological events
pathram timeline --session 17..19                # scoped to session range
pathram gaps                                     # known data gaps
pathram quirks                                   # recorded quirks/gotchas
pathram stale 7                                  # entries not updated in 7 days
pathram refs ENTRY_ID                            # incoming + outgoing references
pathram refs --broken                            # find dangling references
pathram report                                   # full analysis: staleness, coverage, refs
```

### emission — generate views

```bash
pathram show DOC_ID                              # one doc as markdown (stdout)
pathram emit md --out pathram/output               # all docs as .md files
```

---

## python API

```python
from pathram import discover, step_add, step_done, note, glance

# Record things
discover("karaka was already in sangati roots", session_id=17)
step_add("Dravya promotion guards", doc="18-impl", status="pending")
step_done("18-impl.step-1", note="routing working")
note("nested cond causes parse_expr:empty", note_type="quirk")

# Query
print(glance())   # compact summary with live stats

# Lower-level access
import pathram
state = pathram._get_state()
results = pathram.search(state, "karaka")
steps = pathram.steps(state, status="next")
```

---

## live data integration

pathram pulls live data from the codebase — no stale numbers:

- **Om nodes** — count and search via `tools/om.py`
- **Tantras** — count and search via `tools/tantras.py`
- **Shabda** — word index search via `tools/shabda.py`
- **Test baseline** — from pytest cache via `tools/cache.py`

This appears in `pathram glance`, `pathram index`, and `pathram topic`:

```
## pathram glance

**Baseline**: 85 passed / 35 xfailed / 0 failed
**Live**: 1630 om nodes, 74 tantras
**Next**: Dravya promotion guards

**Recent discoveries**:
  - karaka was already in sangati roots

**Status**: 4 active
**Total**: 4 docs, 4 entries
```

---

## cross-references

Entries can reference other entries, om nodes, tantras, or external docs:

```bash
pathram ref 18-impl.step-3 philosophy.insight-5      # another pathram entry
pathram ref 18-impl.step-3 om:karaka                 # om node
pathram ref 18-impl.step-3 tantra:emit-triples       # tantra file
pathram ref 18-impl.step-3 ext:https://paper.com/x   # external URL
```

Check integrity with `pathram refs --broken`.

---

## storage

State lives in `pathram/data/*.json` — git-friendly, human-readable:

```
pathram/data/
  docs.json         # document containers
  entries.json      # all content entries
  sessions.json     # session records
  baselines.json    # baseline timeseries
  refs.json         # cross-references
  ops.json          # append-only operation log
```

Created automatically on first use. All mutations are logged in `ops.json`.

---

## package layout

```
pathram/
  __init__.py       # public Python API (discover, step_done, glance, ...)
  __main__.py       # entry point (python3 -m pathram)
  cli.py            # argparse dispatch — all commands
  data.py           # JSON storage + State class with in-memory indexes
  store.py          # write operations (CRUD + ops log)
  query.py          # read operations (search, by_tag, steps, topic, ...)
  emit.py           # render to markdown, glance, index, report, timeline
  bridge.py         # live data from tools/ (om, tantras, shabda, cache)
  data/             # JSON state files (auto-created)
```
