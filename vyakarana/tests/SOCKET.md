# Vyakarana Socket Protocol

The vyakarana server listens on a Unix domain socket (default `/tmp/vy.sock`).
The wire format is **newline-delimited JSON** — one JSON object per line in each
direction, no length prefix.

The Python `Client` class in `vy.py` wraps the protocol. All examples below
use it directly.

---

## Connecting

```python
import sys
sys.path.insert(0, "vyakarana/tests")
from vy import Client

vy = Client("/tmp/vy.sock")   # or use DEFAULT_SOCKET env var VYAKARANA_SOCKET
```

The client keeps a single persistent connection and reconnects automatically on
disconnect.

---

## Commands

### `eval-json` — evaluate a tantra expression

Returns the result as a native Python value (list, str, float, bool, None).

```python
# simple lookup
result = vy.eval('lookup-word "mass"')          # "mass"

# build a question graph — returns list of [s, p, o] triples
g = vy.eval('build-question-graph "ball has mass"')

# call any loaded tantra directly
g = vy.eval('avrti-refine (build-question-graph "find velocity")')
```

Wire request:
```json
{"command": "eval-json", "expr": "lookup-word \"mass\""}
```

Wire response:
```json
{"status": "ok", "command": "eval-json", "result": "mass", "elapsed_ms": 2}
```

---

### `graph` — dump the full proof graph

Returns every node and its edges as JSON. Useful for inspection.

```python
resp = vy._send_with_retry({"command": "graph"})
nodes = resp["nodes"]   # list of {name, satya, edges: [{target, relation}]}
```

Wire request:
```json
{"command": "graph"}
```

---

### `reload-all` — resync all tantras from disk

Re-reads every `.tantra` file from all startup dirs and rebuilds the tantra
index in place. Use this after editing existing tantras.

```python
r = vy.reload_all()
# r == {"status": "ok", "command": "reload-all", "tantras_loaded": 47}
```

Wire request:
```json
{"command": "reload-all"}
```

Wire response:
```json
{"status": "ok", "command": "reload-all", "tantras_loaded": 47}
```

---

### `attach` — live-load a single file without restarting

Attach a `.tantra` or `.om` file directly into the running server.

- **`.tantra`** — parsed and registered into the tantra index immediately.
  Subsequent `eval` calls can invoke it by name.
- **`.om`** — node is joined into the proof graph; CSR adjacency matrix is
  rebuilt. Use for new sangati/kosha nodes.

The path must be **absolute** and readable by the server process.

```python
# attach a new tantra
r = vy.attach("/home/abe/agent_x/brahman/yantra/vishesa/rashi-anuvada.tantra")
# r == {"status": "ok", "command": "attach", "kind": "tantra", "name": "rashi-anuvada", ...}

# attach a new .om knowledge node
r = vy.attach("/home/abe/agent_x/brahman/sangati/prashna/new-signal.om")
# r == {"status": "ok", "command": "attach", "kind": "om", "name": "new-signal", ...}
```

Wire request:
```json
{"command": "attach", "path": "/abs/path/to/file.tantra"}
```

Wire response:
```json
{"status": "ok", "command": "attach", "kind": "tantra", "name": "rashi-anuvada", "path": "..."}
```

> **Note**: for `.tantra` files that are *updated* (not just new), `attach`
> overwrites the existing registration via `Hashtbl.replace` — so edits to an
> existing tantra take effect immediately without restart.  For `.om` files,
> `join` deduplicates edges, so re-attaching an unchanged file is safe.

---

### `question` — natural-language query

Send a question and get an `answer_text` back. Uses the full NLP pipeline.

```python
answer = vy.ask("what is the velocity of ball1", session_id="s1")
```

Wire request (note: **no `command` field** — the server dispatches on absence):
```json
{"question": "what is the velocity of ball1", "session_id": "s1"}
```

Wire response:
```json
{"status": "ok", "request_id": "", "session_id": "s1", "turn_id": "", "answer_text": "..."}
```

---

### `end-session` — clear session state

```python
vy._send_with_retry({"command": "end-session", "session_id": "s1"})
```

---

## Debug commands

### `inspect-node` — single node with in + out edges

Returns a node's outgoing **and** incoming edges in one call. Replaces the
pattern of `vy.walk()` + `vy.walk_in()` when you want everything at once.

```python
node = vy.inspect("velocity")
# {
#   "name": "velocity", "satya": 0.9,
#   "out_edges": [{"target": "displacement", "relation": "kramanusara"}],
#   "in_edges":  [{"source": "v1", "relation": "vishesa"}]
# }
```

Wire request:
```json
{"command": "inspect-node", "name": "velocity"}
```

Wire response:
```json
{
  "status": "ok", "command": "inspect-node",
  "name": "velocity", "satya": 0.9,
  "out_edges": [{"target": "displacement", "relation": "kramanusara"}],
  "in_edges":  [{"source": "v1", "relation": "vishesa"}]
}
```

Raises `VyakaranaError(NOT_FOUND)` if the node does not exist.

---

### `list-tantras` — enumerate all loaded tantras

Use to confirm that `attach` or `reload-all` registered a tantra correctly.

```python
names = vy.list_tantras()
assert "rashi-anuvada" in names   # confirm bridge is loaded
```

Wire request:
```json
{"command": "list-tantras"}
```

Wire response:
```json
{"status": "ok", "command": "list-tantras", "count": 47, "tantras": ["avrti-refine", ...]}
```

---

### `triples-of` — all triples touching a node

Returns every triple where `node` is either subject or object. More
convenient than `walk` + `walk_in` when you want a complete picture of
what the graph knows about a node.

```python
ts = vy.triples_of("velocity")
# [["velocity","sankhya","20."], ["v1","vishesa","velocity"], ["velocity","satya","velocity"], ...]
```

Wire request:
```json
{"command": "triples-of", "node": "velocity"}
```

Wire response:
```json
{
  "status": "ok", "command": "triples-of", "node": "velocity",
  "triples": [["v1","vishesa","velocity"], ["velocity","satya","velocity"]]
}
```

---

### `pipeline-trace` — avrti-refine step by step

Runs the full `avrti-refine` pipeline on a sentence and returns the graph
**after each stage**. The single most useful debugging tool — shows exactly
which stage added (or failed to add) a particular triple.

```python
trace = vy.pipeline_trace("ball has mass m1 of 5 and velocity v1 of 20")
for step in trace:
    print(step["stage"], "→", len(step["triples"]), "triples")
# build-question-graph → 10 triples
# sandhi-kosha         → 10 triples
# vibhakti-shashthi    → 13 triples   ← shashthi + prathama triples added here
# vishesa-instance     → 15 triples   ← [m1,vishesa,mass] etc added here
# rashi-viveka         → 17 triples   ← [m1,sankhya,5.] added here
# ...
```

Wire request:
```json
{"command": "pipeline-trace", "sentence": "ball has mass m1 of 5 and velocity v1 of 20"}
```

Wire response:
```json
{
  "status": "ok", "command": "pipeline-trace",
  "sentence": "ball has mass m1 of 5 and velocity v1 of 20",
  "stages": [
    {"stage": "build-question-graph", "triples": [[...], ...]},
    {"stage": "sandhi-kosha",         "triples": [[...], ...]},
    {"stage": "sandhi-avastha",       "triples": [[...], ...]},
    {"stage": "sandhi-bandhana",      "triples": [[...], ...]},
    {"stage": "vibhakti-shashthi",    "triples": [[...], ...]},
    {"stage": "vishesa-instance",     "triples": [[...], ...]},
    {"stage": "rashi-viveka",         "triples": [[...], ...]},
    {"stage": "vishesa-bandhana",     "triples": [[...], ...]},
    {"stage": "sankhya-bandha",       "triples": [[...], ...]}
  ]
}
```

Stages follow the `avrti-refine` pipeline order. Adding a new stage (e.g.
`rashi-anuvada`) requires updating both `avrti-refine.tantra` and the
`stages` list in `pipeline_trace_response` in `socket.ml`.

---

### `mantra-status` — which mantras fire and why

Runs the full `avrti-refine` fixpoint on a sentence, then for every loaded
mantra reports: bound janya, missing janya, whether it fires. The primary
tool for debugging P8b.6-type gaps where a mantra should fire but doesn't.

```python
s = vy.mantra_status("ball has mass m1 of 5 and velocity v1 of 20")

# Before rashi-anuvada bridge:
s["bound_concepts"]  # []  — instances not propagated to concept level
# kinetic-energy-mantra: fires=False, covered=[], missing=["mass","velocity"]

# After bridge:
s["bound_concepts"]  # [["mass","5."], ["velocity","20."]]
# kinetic-energy-mantra: fires=True, covered=["mass","velocity"], missing=[]
```

`bound_concepts` is populated by the `debug-bound-concepts` tantra
(in `brahman/yantra/debug/`). `mantras` is populated by `mantra-coverage`
tantra. Both must be loaded for full output; if not loaded the fields return
`[]` gracefully.

Wire request:
```json
{"command": "mantra-status", "sentence": "ball has mass m1 of 5 and velocity v1 of 20"}
```

Wire response:
```json
{
  "status": "ok", "command": "mantra-status",
  "sentence": "...",
  "refined_graph":   [[...], ...],
  "bound_concepts":  [["mass","5."], ["velocity","20."]],
  "mantras":         [["kinetic-energy-mantra", true, ["mass","velocity"], []], ...]
}
```

---

## `vy.py` debug helpers

These are thin wrappers around the debug commands above:

```python
# inspect one node — out + in edges in one shot
node = vy.inspect("velocity")

# confirm a tantra is loaded
assert "rashi-anuvada" in vy.list_tantras()

# all triples touching a node
ts = vy.triples_of("velocity")

# step-by-step pipeline trace
trace = vy.pipeline_trace("ball has mass m1 of 5")

# mantra firing analysis for a sentence
status = vy.mantra_status("ball has mass m1 of 5 and velocity v1 of 20")

# bound-concepts from a pre-built graph (calls debug-bound-concepts tantra)
g = vy.eval('fixpoint (build-question-graph "ball has mass m1 of 5") avrti-refine')
bc = vy.bound_concepts(g)   # [["m1","5."]] before bridge
```

---

## Graph helpers (`vy.py` static methods)

These operate on a graph returned by `eval('build-question-graph ...')` or
`eval('avrti-refine ...')` — a Python list of `[subject, predicate, object]`
triples.

```python
g = vy.eval('avrti-refine (build-question-graph "ball has mass m1 of 5")')

# check presence of a triple
vy.has_triple(g, subj="m1", pred="vishesa", obj="mass")   # True/False

# find the first matching triple
t = vy.find_triple(g, subj="m1", pred="sankhya")          # [m1, sankhya, 5.0] or None

# find all matching triples
ts = vy.all_triples(g, pred="prathama-vibhakti")           # [[ball, prathama-vibhakti, object]]

# numeric comparison with float tolerance (server sends "5." not 5.0)
vy.approx_eq(t[2], 5.0)                                    # True
```

---

## Kosha walk helpers

```python
# outgoing edges: walk "mass" along "matra" → unit nodes
units = vy.walk("mass", "matra")             # ["kilogram"]

# incoming edges: which concepts have "matra" → kilogram
owners = vy.walk_in("kilogram", "matra")     # ["mass"]
```

---

## Typical test pattern

```python
def test_something(vy):
    # 1. optionally attach new tantras/nodes for this test
    vy.attach("/abs/path/brahman/yantra/vishesa/rashi-anuvada.tantra")

    # 2. build a graph from a sentence
    g = vy.eval('avrti-refine (build-question-graph "ball has mass m1 of 5")')

    # 3. assert triples
    assert vy.has_triple(g, subj="m1", pred="vishesa", obj="mass")
    t = vy.find_triple(g, subj="m1", pred="sankhya")
    assert t and vy.approx_eq(t[2], 5.0)
```

See `conftest.py` for the session-scoped `vy` fixture, and `test_rashi.py` /
`test_rashi_entities.py` for worked examples.
