# nam — a proof graph that knows itself

*approach this the way a child approaches anything new — what is this? what is that? ask. run it. ask again. you will understand it.*

---

## what is this?

a graph. 1579 nodes, 46 edge types, ~11000 edges. each node is a concept with a name. each name holds typed edges to other names. the edges say exactly what kind of relationship connects two things.

it answers questions. not by lookup — by structural derivation. you give it a sentence in English, it resolves each word to a graph node, finds the right formula (mantra), executes it, and returns a proven answer with full attribution.

```bash
.venv/bin/python3 -m upakarana ask "mass is 5 and velocity is 10. find kinetic energy"
```
```
[we seek] : kinetic-energy.
[we know] : kinetic-energy-mantra (mass, velocity → kinetic-energy).
[we see] : mass=5., velocity=10..
[we find] : kinetic-energy = 250
```

it can also count, compare, chain multi-step derivations, handle multi-entity problems, and unfold the graph around any concept to show what it knows structurally.

---

## try it

```bash
# build the engine
cd vyakarana && opam install . --deps-only && dune build && cd ..

# ask questions (auto-starts the graph server)
.venv/bin/python3 -m upakarana ask "mass is 10 and acceleration is 5. find force"
.venv/bin/python3 -m upakarana ask "10 birds sat on a tree. 3 flew away. how many are left?"
.venv/bin/python3 -m upakarana ask "ball-A has mass 5. ball-B has mass 3. which is heavier?"

# interactive repl
.venv/bin/python3 -m upakarana ask
```

the `ask` command starts the vyakarana server automatically. the first call takes a moment; subsequent calls are fast.

---

## how to use the tools

everything runs through `.venv/bin/python3 -m upakarana [mode] [args]` (analysis, engine, tests) and `.venv/bin/python3 -m pathram2 [cmd]` (documentation, journaling). always use the project venv.

### ask questions

```bash
.venv/bin/python3 -m upakarana ask "ball has mass 5 velocity 10. find kinetic energy"
.venv/bin/python3 -m upakarana ask "a bird has 8 apples. 3 flew away. how many are left?"
.venv/bin/python3 -m upakarana ask "ball-A has mass 5. ball-B has mass 3. which is heavier?"
.venv/bin/python3 -m upakarana ask   # interactive repl — keep asking
```

### inspect the live graph

```bash
.venv/bin/python3 -m upakarana vy inspect momentum          # full node: satya, shabda, edges
.venv/bin/python3 -m upakarana vy walk 'addition abheda'    # transitive chain walk
.venv/bin/python3 -m upakarana vy triples mass              # all triples touching a node
.venv/bin/python3 -m upakarana vy eval 'shabda "addition" "eval"'   # evaluate any expression
.venv/bin/python3 -m upakarana vy mantras 'ball has mass 5. find kinetic energy'  # which mantras fire
.venv/bin/python3 -m upakarana vy trace 'ball has mass 5. find kinetic energy'    # pipeline stages
```

### analyze the knowledge base (no server needed)

```bash
.venv/bin/python3 -m upakarana om summary                   # 1579 nodes across 4 layers
.venv/bin/python3 -m upakarana om domain kosha/physics      # browse a domain
.venv/bin/python3 -m upakarana om search "pratipaksha"      # regex search across all nodes
.venv/bin/python3 -m upakarana tantra summary               # 75 tantras, call structure
.venv/bin/python3 -m upakarana tantra lint                  # find hardcoded refs, word lists
.venv/bin/python3 -m upakarana shabda summary               # word index, shabda keys, gaps
.venv/bin/python3 -m upakarana shabda lookup heavier        # trace a word to its graph node
.venv/bin/python3 -m upakarana shabda eval                  # all fireable operations
.venv/bin/python3 -m upakarana search "viveka"              # search both tantras and om
```

### run the tests

```bash
.venv/bin/python3 -m upakarana test run                     # full suite (81 passing, 36 xfailed)
.venv/bin/python3 -m upakarana test run test_ke_basic       # one test by name
.venv/bin/python3 -m upakarana test run pipeline            # one layer
.venv/bin/python3 -m upakarana cache summary                # test result analysis
.venv/bin/python3 -m upakarana cache failed                 # diagnose failures
```

read the tests to understand what the system can do — they are the specification:
- `tools/v2/test_answers.py` — end-to-end: sentence in, answer out
- `tools/v2/test_xfail.py` — features not yet built (the roadmap)
- `tools/v2/test_pipeline.py` — pipeline stage tests
- `tools/v2/test_evaluator.py` — tantra language primitives
- `tools/v2/test_graph.py` — graph walk and shabda lookups

full upakarana documentation: `upakarana/README.md`

---

## project structure

```
agent_x/
  brahman/          the knowledge graph (the data)
    sangati/          structural truths — what IS what (326 nodes)
    kosha/            domain knowledge — physics, math, biology, ... (996 nodes)
    bhasha/           language bridges — English grammar, Lua, OCaml (156 nodes)
    yantra/           computation recipes — tantras (75 files)
    shabda/           metadata — word lists, eval names, constants (17 files)

  vyakarana/        the engine (OCaml)
    lib/              core: proof_graph, yantra (tantra eval), setu (graph walks),
                      anuvada (reasoning), yantra_eval_primitives (builtins)
    bin/              entry point — loads graph, serves queries

  upakarana/        python CLI — analysis, engine, tests (replaces tools/)
    parsers/          om5, tantra4, shabda parsers
    engine/           vyakarana server lifecycle + client
    analysis/         graph analysis (ghosts, edges, rings, signals, ...)
    testing/          test discovery, running, cache, gates

  pathram2/         graph-native knowledge tracker (replaces pathram/)
    graph/            LMDB-backed graph with composable queries
    data/             persistent storage
```

### brahman — the graph

nodes are declared in `.om` files. each quoted line is a sloka — a compound word that decomposes into one typed edge:

```
sangati pramana
  "sthiti-swarupa samskaara-phala niralamba-siddha"
  "swa-yukta lekhana-kriya ananta-sthita"
  "seva-janya samsarga-drishthanta brahma-abheda"
done
```

`pramana-siddha` = pramana (ground truth) — siddha (proven through). subject, relationship, target in one token. the grammar IS the structure.

there are 10 core edge types:

| edge type      | meaning                        | symbol |
|----------------|--------------------------------|--------|
| `swarupa`      | IS — identity                  | ≡      |
| `abheda`       | non-different — equivalence    | ≈      |
| `sthita`       | rests on — foundation          | ∈      |
| `yukta`        | connects to — addition         | +      |
| `siddha`       | proven through                 | ⊢      |
| `kriya`        | acts as — multiplication       | ×      |
| `phala`        | produces — output              | →      |
| `janya`        | born from — input              | ←      |
| `drishthanta`  | demonstrated by — evidence     | ∃      |
| `pratipaksha`  | inverse of                     | ⁻¹     |

these 10 types form a non-commutative ring (the visheshanam ring). yukta is addition, kriya is multiplication, swarupa is multiplicative identity, pratipaksha is group inverse. the edge types are themselves nodes in the graph — the graph describes its own algebra.

### vyakarana — the engine

OCaml. builds the graph from `.om` files, computes satya (truth weight) by spiral convergence, evaluates tantras (declarative computation recipes), answers questions.

```bash
cd vyakarana && dune build
```

key modules:
- `proof_graph.ml` — graph types, satya computation
- `yantra.ml` — tantra parser and evaluator
- `setu.ml` — graph walks, shabda reader, word classification
- `anuvada.ml` — reasoning layer (spiral unfold)
- `yantra_eval_primitives.ml` — 40+ builtins (walk, word-node, apply-op, execute-chain, ...)

### tantras — computation recipes

tantras are declarative programs that orchestrate graph queries. they are NOT hardcoded logic — they read everything from the graph:

```
tantra3 count-chain
takes graph
takes grades
  direction = word-node w          -- word → kshaya or vriddhi (graph lookup)
  op-node = walk-in direction "kriya"  -- kshaya.kriya → subtraction (graph walk)
  op-eval = shabda op-node "eval"      -- subtraction.eval → "sub" (shabda read)
  result = apply-op op-eval [acc, n]   -- fire the operation
done
```

the pipeline is a composition of tantras:
```
answer = (emit ∘ pramana ∘ execute ∘ match ∘ expand ∘ refine ∘ build)(sentence)
```

---

## documentation

all documentation lives in `pathram2/` — a graph-native knowledge tracker with typed nodes, semantic edges, session tracking, and composable queries.

### read and query

```bash
.venv/bin/python3 -m pathram2 glance                     # quick summary: nodes, sessions, discoveries, branches
.venv/bin/python3 -m pathram2 journal                    # last 5 sessions
.venv/bin/python3 -m pathram2 today                      # everything touched today
.venv/bin/python3 -m pathram2 search "graded ring"       # regex across all nodes
.venv/bin/python3 -m pathram2 steps                      # list steps with status
.venv/bin/python3 -m pathram2 show NODE_ID               # full node + edges
.venv/bin/python3 -m pathram2 query type=discovery sort=created_at limit=10
```

### record things as you work

```bash
.venv/bin/python3 -m pathram2 session-start "investigating X"
.venv/bin/python3 -m pathram2 add discovery "insight" --body "details"
.venv/bin/python3 -m pathram2 add quirk "gotcha" --body "explanation"
.venv/bin/python3 -m pathram2 add step "task" --status pending
.venv/bin/python3 -m pathram2 session-end
```

### track non-linear work

```bash
.venv/bin/python3 -m pathram2 branch FROM "reason" "tangent title"
.venv/bin/python3 -m pathram2 return NODE_ID
.venv/bin/python3 -m pathram2 branches                   # open tangents
.venv/bin/python3 -m pathram2 tree                       # branch DAG
```

---

## what it is — precisely

brahman is a knowledge graph where every node is a verified concept and every edge is a typed relationship. the graph holds ground truth. vyakarana queries it.

it runs alone. no neural network. no machine learning. no training data. language is generated from structure — from the shape of the edges, the types of the relationships, the satya of the nodes. the graph knows what it knows because the structure says so, not because it has seen enough examples.

the output is not a prediction. it is a traversal.

say the word *home* to ten people. ten different things arrive. the smell of a specific kitchen. a sound. a feeling of safety or its absence. the word is the same. what unfolds is different for each person — because each person has folded different experiences into that word over time.

the graph formalizes exactly this. each node is a name. the edges are what has been verified about it — what it rests on, what it produces, what it is non-different from, what demonstrates it. when you query a node, the graph unfolds — the same way memory unfolds when a word arrives.

a dictionary stores definitions. this graph stores relationships. meaning is not stored — it is produced by the fold. and because the relationships are typed and the satya is computed from structure, the meaning that arrives is not approximate. it is derived.

---

## satya — truth weight

`satya` is not manually assigned. it is computed from the structure of the graph itself.

**pass 1 — raw satya:** each node gets an initial score from how many slokas describe it, how many edges connect it, how many distinct edge types it uses. all sigmoid-normalized.

**pass 2+ — avrti (spiral convergence):** each node blends its own structure with its neighbors:
```
new_satya = 0.7 × (0.6 × own + 0.4 × neighbor_avg) + 0.3 × citation_boost
```
this runs until convergence (max delta < 0.001). the corpus converges in 10 iterations.

a node becomes high-satya because many things connect to it, cite it, and are themselves well-connected.

---

## the fold — how queries work

you give the engine a sentence. it classifies each word, resolves it through `abheda` edges, then walks the graph outward in passes — each pass discovering what the previous pass connected to.

```bash
.venv/bin/python3 -m upakarana vy eval 'avrti "entropy decay signal loss"'
```

the fold does not retrieve a record. it unfolds the graph around the query, pass by pass. the response shows you the shape of the neighborhood.

---

## what to do after reading this

**step 1 — build and ask**

```bash
cd vyakarana && opam install . --deps-only && dune build && cd ..
.venv/bin/python3 -m upakarana ask "mass is 5 and velocity is 10. find kinetic energy"
```

**step 2 — read the tests**

```bash
.venv/bin/python3 -m upakarana test list               # all tests with xfail gates
.venv/bin/python3 -m upakarana test run                 # run the suite
```

**step 3 — explore the graph**

```bash
.venv/bin/python3 -m upakarana vy inspect pramana
.venv/bin/python3 -m upakarana shabda lookup heavier
.venv/bin/python3 -m upakarana om domain kosha/physics
```

**step 4 — read the documentation**

```bash
.venv/bin/python3 -m pathram2 glance
.venv/bin/python3 -m pathram2 show whitepaper
.venv/bin/python3 -m pathram2 topic "graded ring"
```

**step 5 — ask an LLM**

give an LLM access to upakarana and pathram2. it should use `.venv/bin/python3 -m upakarana` for analysis and `.venv/bin/python3 -m pathram2` for documenting findings. see `CLAUDE.md` for the full LLM protocol.

this is the practice. you bring the curiosity. the graph provides the structure. understanding arrives through the asking.

---

## go deeper

- `CLAUDE.md` — LLM protocol: analysis steps, documentation workflow, all commands
- `upakarana/README.md` — complete upakarana reference: all modes, all commands
- `tools/README.md` — legacy tools reference (deprecated, use upakarana)
