# Scene Comprehension + Remaining Robotics Plan
## Physics Sentence Understanding · N-Entity Scene Model · Dynamic Graph Dimensions · Binary Cache · Sensor Demo

---

## What This Plan Covers

Three interconnected goals:

1. **Scene comprehension** — the engine builds a structured scene from a sentence:
   N entities (each with their own property context), N processes (collision, sliding,
   compression...), krama sequence, and narrates back what it understood before
   computing anything. Root sangati concepts (`sandhi`, `matra`, `gati`, `spanda`,
   `krama`) serve as the structural grammar of understanding.

2. **Remaining from old plan** — problem ingestion mode (PROBLEM...END), configurable
   chain depth, binary cache, robotics sensor demo. All designed, none yet built.

3. **Dynamic graph dimensions** — root sangati nodes that carry structural relational
   meaning (`sandhi`, `matra`, `krama`) should be promotable to new visheshanam axes
   at startup. The graph self-extends its own dimensionality from `.om` files alone.

---

## Core Architecture: How Scene Comprehension Works

### The Key Insight

The graph already carries everything needed for understanding:

```
kilogram → matra-sthita (it IS a unit)
kilogram → mass-yukta   (it MEASURES mass)
collision → sandhi-swarupa (it IS a junction/interaction)
collision → dvaya-yukta    (it INVOLVES two entities)
collision → samvega-kriya  (it ACTS through momentum)
```

These edges ARE the grammar. The engine doesn't need an English parser — it traverses
the graph edges to understand sentence structure.

### Root Sangati as Structural Grammar

Each root sangati plays a structural role in building a scene:

| Root Sangati | Role | Detected by | Effect on extraction |
|---|---|---|---|
| `matra` | Maps numbers to quantities | `has node "matra-sthita"` | "2 kg" → follow yukta → mass=2 |
| `sandhi` | Junction between entities | `has node "sandhi-swarupa"` | Entity boundary |
| `dvaya` / `aneka` | How many entities | `has sandhi-node "dvaya-yukta"` | Entity count |
| `gati` | Motion (single entity) | `has node "gati-swarupa"` | Single-entity context |
| `spanda` | Periodic/oscillatory | `has node "spanda-swarupa"` | SHM context |
| `krama` | Temporal sequence | `has node "krama-swarupa"` | Phase boundary |
| `pratipaksha` | Zero/absent value | `has node "shunya-abheda"` | Implicit binding (velocity=0) |

### N-Entity Scene Model (not two, not named)

Entities are **not** named "second-mass". They carry their own values in their own
context. The resolver maps entity values to tantra inputs by CONCEPT TYPE (via the
`matra → yukta` chain), not by name.

```
Input: "A 2 kg ball at 5 m/s hits a 3 kg block, which compresses a spring of 500 N/m"

Scene:
  Entity 1: {mass: 2, velocity: 5}      ← ball
  Entity 2: {mass: 3}                    ← block
  Entity 3: {spring-constant: 500}       ← spring

  Process 1: sandhi (collision) — entities [1, 2]
  Process 2: sandhi (compression) — entities [2, 3]

  Sequence: [Process 1] → krama → [Process 2]

Narration:
  "I see 3 objects in 2 processes:
   Object 1: mass 2 kg, moving at 5 m/s
   Object 2: mass 3 kg
   Object 3: spring constant 500 N/m
   Process 1: Object 1 collides with Object 2 (sandhi)
   Process 2: Object 2 compresses Object 3 (sandhi)
   Sequence: collision first, then compression"
```

### Scene-Aware Resolver: Concept-Type Matching

Tantra inputs carry unit annotations. Units are `matra-sthita` nodes with `yukta` edges
to concepts. The resolver groups inputs by concept and fills them from entities in order.

```
tantra asprishta-sanghat (inelastic collision):
  mass       kilogram    ← kilogram yukta mass → "mass" concept
  velocity   m/s         ← m/s yukta velocity → "velocity" concept
  mass-2     kilogram    ← kilogram yukta mass → same "mass" concept (2nd occurrence)

Scene provides:
  mass-concept:     [entity1: 2, entity2: 3]   → 2 values, tantra needs 2
  velocity-concept: [entity1: 5]               → 1 value, tantra needs 1

Mapping (entity order → input order):
  mass   ← 2   (entity 1's mass)
  mass-2 ← 3   (entity 2's mass)
  velocity ← 5 (entity 1's velocity)
```

Internal param names (`mass-2`) are tantra implementation details. Users never see them.
No renaming needed. No "second-mass" naming convention. The scene holds the truth.

### Scene-Aware Chain Resolver (krama sequences)

For multi-process problems, the resolver chains processes in krama order:

```
Process 1 (collision): entities [1, 2]
  → asprishta-sanghat(mass=2, velocity=5, mass-2=3) → v_final = 2.0 m/s

Result binding: velocity = 2.0 (stored as entity 2's new velocity)

Process 2 (compression): entities [2, 3]
  → scene now: entity 2 has {mass: 3, velocity: 2.0}, entity 3 has {spring-constant: 500}
  → KE = ½mv² → spring compression x = √(mv²/k)
  → spanda-urja(spring-constant=500, x) → x = 0.245 m
```

Each process result feeds the next. This is the krama (ordered sequence) property.

---

## Part A: What's Already Done (from old plan)

### Completed ✓

| Item | Status |
|---|---|
| Extended `binding` type (4 new fields: timestamp, source, confidence, ttl) | ✓ done |
| Updated all `binding` construction sites in OCaml | ✓ done |
| 22 new motion tantras (rotational, rolling, circular, projectile, SHM, friction, collision) | ✓ done |
| `seema-pariksha.tantra` (threshold check for robotics) | ✓ done |
| Phase 1 build + test (rolling sphere 6.48 m/s ✓, SHM ✓, friction ✓) | ✓ done |
| CSR-backed PPR (main work of previous session) | ✓ done |

### Discovered: Collision resolver issue

The `asprishta-sanghat`, `sprishta-sanghat`, `atwood-yantra` tantras have params named
`mass-2`. The tokenizer splits on `-`, so user cannot input `mass-2 is 3`. The fix is
NOT to rename to `second-mass` — instead the scene-aware resolver maps entity values
by concept type. Users write natural language; the scene handles the rest.

The tantras themselves are correct as written. The resolver needs to change.

---

## Part B: Process Nodes (graph knowledge layer)

Physics verbs that ARE processes — they have root-sangati edges that tell the extraction
pipeline what role they play. These are NOT vocabulary additions — they are structural
knowledge nodes that happen to have English surface forms in their shabda.

### New nodes: `brahman/kosha/physics/processes/`

**`collision.om`**
```
kosha collision
  "sandhi-swarupa dvaya-yukta samvega-kriya"
  "domain-physics-sthita"
  shabda collides, colliding, collide, hits, hitting, hit, strikes, striking, strike
        impacts, impacting / two-bodies-meet-momentum-changes
done
```

**`rolling.om`**
```
kosha rolling
  "gati-swarupa angular-velocity-yukta"
  "displacement-phala"
  "domain-physics-sthita"
  shabda rolls, rolling, roll / body-moves-with-rotation-no-slipping
done
```

**`sliding.om`**
```
kosha sliding
  "gati-swarupa displacement-phala"
  "domain-physics-sthita"
  shabda slides, sliding, slide, slips, slipping / body-moves-along-surface
done
```

**`compression.om`**
```
kosha compression
  "sandhi-swarupa spring-force-yukta"
  "displacement-phala"
  "domain-physics-sthita"
  shabda compresses, compressing, compress, pushes, pushing / body-contacts-spring
done
```

**`oscillation.om`**
```
kosha oscillation
  "spanda-swarupa avrti-yukta frequency-phala"
  "domain-physics-sthita"
  shabda oscillates, oscillating, vibrates, vibrating, swings, swinging
        bounces, bouncing / periodic-motion-around-equilibrium
done
```

**`suspension.om`**
```
kosha suspension
  "sandhi-swarupa tension-phala"
  "dvaya-yukta gravity-yukta"
  "domain-physics-sthita"
  shabda hangs, hanging, hang, suspended, suspending, dangles, dangling
        attached-to-string, tied-to-string / body-held-by-tension-against-gravity
done
```

**`connection.om`**
```
kosha connection
  "sandhi-swarupa dvaya-yukta"
  "krama-yukta"
  "domain-physics-sthita"
  shabda connected, connecting, tied, tying, attached, attaching
        linked, linking, joined, joining / two-bodies-move-as-system
done
```

### New nodes: `brahman/kosha/language/english/context/`

**`frictionless.om`**
```
kosha frictionless
  "domain-language-sthita yantra-english-sthita"
  "friction-coefficient-abheda shunya-abheda"
  "gati-swarupa"
  shabda frictionless, smooth, no-friction, frictionlessly / friction-coefficient-is-zero
done
```

**`rough.om`**
```
kosha rough
  "domain-language-sthita yantra-english-sthita"
  "friction-coefficient-yukta"
  "gati-swarupa"
  shabda rough, rough-surface, with-friction / friction-coefficient-present
done
```

---

## Part C: Dynamic Graph Dimensions

### What This Solves

Currently `visheshanam` is a fixed 10-element OCaml variant. If you write `"force-sandhi"`
in a sloka, the parser hits `visheshanam_of_string "sandhi"` → `None` → edge silently dropped.

Root sangati that carry structural relational meaning (`sandhi`, `matra`, `krama`) should
become recognized edge types — new axes in the tensor — loaded at startup from `.om` files.

### Self-Declaration Mechanism

A sangati node declares itself as a dimension by including `"visheshanam-swarupa"` in its
slokas. The parser scans all loaded nodes at startup and registers any with this edge as
a new dimension.

```
sangati sandhi
  "samsarga-swarupa abheda-drishthanta svayambhu-abheda"
  "visheshanam-swarupa"       ← declares: I am a graph dimension
  "om-abheda bhasha-swarupa-sthita"
  "artha-phala sparsha-siddha"
  shabda the-joining-that-produces-meaning
done
```

### Architecture Changes

| Component | Before | After |
|---|---|---|
| `visheshanam` type | OCaml variant (10 fixed) | `int` index into dynamic registry |
| `num_relations` | `10` (compile-time) | `Array.length dimension_table` (runtime) |
| `visheshanam_of_string` | 10-way pattern match | `Hashtbl.find_opt dimension_registry` |
| `visheshanam_to_idx` | Fixed function | `Hashtbl.find dimension_idx_table` |
| `string_of_visheshanam` | Fixed match | `Array.get dimension_names` |
| CSR arrays | `10 × nnz` at startup | `num_dimensions × nnz` at startup |
| PPR weight vector | 10 floats | Dynamic array, new dims get default weight |
| `om_parser` decompose | Match against 10 suffixes | Match against registry at parse time |

The core 10 remain as the foundational set (boot-strapped before `.om` parsing).
New dimensions registered from `.om` files during the `build_index` pass.

### Startup Order

```
1. Register 10 base visheshanam in registry (same names as today)
2. Parse all .om files (collect nodes + slokas)
3. Scan nodes for "visheshanam-swarupa" edge → register as new dimensions
4. Re-parse sloka words against expanded registry (second pass for dynamic dims)
5. materialize_csr with num_relations = registry size
6. Load PPR weight vector with default weight for new dims
```

### Which Root Sangati Become Dimensions

| Sangati | Meaning | New sloka addition |
|---|---|---|
| `sandhi` | junction/interaction | add `"visheshanam-swarupa"` |
| `matra` | measure/unit | add `"visheshanam-swarupa"` |
| `krama` | sequence/order | add `"visheshanam-swarupa"` |

These three are enough for scene comprehension. Others can be added later.

With these three new dimensions, sloka edges like:
- `"mass-matra"` → mass has edge type MATRA (measures mass using this)
- `"collision-sandhi"` → collision has edge type SANDHI to what it joins
- `"phase2-krama"` → phase2 follows in krama order

become valid typed edges in the graph tensor.

---

## Part D: Scene Extraction Primitive

### `scene-extract` primitive (OCaml)

```ocaml
(* scene-extract: classified-tokens → scene as VList *)
(* Returns: [entities, processes, sequence, targets]
   entities: [[id, label, [binding,...], [context-word,...]], ...]
   processes: [[root-sangati, surface-word, [entity-ids], [implied-bindings]], ...]
   sequence: [process-id, process-id, ...] in krama order
   targets: [concept-name, ...] *)
```

**Algorithm:**

```
1. Walk tokens left-to-right
2. For each resolved concept node:
   a. has "matra-sthita"? → UNIT TOKEN
      - walk "yukta" → get candidate concepts
      - adjacent number → bind (concept, number) to CURRENT entity
   b. has "sandhi-swarupa"? → PROCESS TOKEN (interaction)
      - check "dvaya-yukta" / "aneka-yukta" → entity count
      - finalise current entity, start new entity scope
      - create process record
   c. has "gati-swarupa"? → MOTION TOKEN (single entity context)
      - implies displacement-phala, adds motion context to current entity
   d. has "spanda-swarupa"? → OSCILLATION CONTEXT
      - implies periodic tantras, frequency-phala
   e. has "krama-swarupa"? (or sequence words: "then", "next", "after")
      → PHASE BOUNDARY — create new scenario
   f. has "shunya-abheda"? (rest, frictionless, stops)
      → IMPLIED BINDING (velocity=0 or friction-coefficient=0)
   g. Unknown word (not in graph) near matra bindings → object label
      - store as entity label (just for narration, not for computation)

3. Multiple numbers for same concept across entity boundaries:
   → different entity contexts, NOT overwriting
   → entity 1 gets its value, entity 2 gets its value

4. Return scene structure
```

### `scene-narrate` primitive (OCaml)

Takes scene structure, returns natural language string:

```
"I understand: 3 objects in 2 processes.
 Object 1: mass 2 kg, moving at 5 m/s.
 Object 2: mass 3 kg, at rest.
 Object 3: spring constant 500 N/m.
 Process 1: collision between Object 1 and Object 2 (sandhi).
 Process 2: compression of Object 3 by Object 2 (sandhi).
 Sequence: Process 1, then Process 2 (krama)."
```

### `scene-understand.tantra`

```
tantra scene-understand
  inputs
    joined  list       -- classified token triples from classify-fold

  let
    scene       = scene-extract joined
    entities    = nth scene 0
    processes   = nth scene 1
    sequence    = nth scene 2
    targets     = nth scene 3
    narration   = scene-narrate scene

  return
    narration   string
    scene       list

done
```

---

## Part E: Scene-Aware Resolver

### Concept-Type Matching

The resolver needs a new entry point for scene-based problems. It receives a scene
(not a flat binding list) and a target. For each tantra candidate:

```ocaml
(* For each input in the tantra, determine what concept it needs *)
let input_concept inp =
  (* look up unit node for this input's unit annotation *)
  (* walk "yukta" edges from unit node *)
  (* return primary concept (first tantra-output in yukta list) *)
  Setu_shabda.read_shabda k inp.tp_unit
  |> find_concept_via_yukta k

(* Group tantra inputs by concept *)
let concept_groups = group_by input_concept tantra.t_inputs

(* Match against scene entities *)
let fill_from_scene scene concept_groups =
  List.map (fun (concept, inputs) ->
    (* find all entities that have this concept *)
    let entity_values = entities_with concept scene.sc_entities in
    (* zip inputs with entity values in ordinal order *)
    List.mapi (fun i inp ->
      (inp.tp_name, (List.nth entity_values i).b_value)
    ) inputs
  ) concept_groups |> List.concat
```

### Krama (Sequence) Chain Resolution

For multi-process scenes, resolve processes in sequence order:

```ocaml
let resolve_scene scene tantra_index =
  List.fold_left (fun (scene_acc, results) proc_id ->
    let proc = List.nth scene.sc_processes proc_id in
    let relevant_entities = List.map (List.nth scene.sc_entities) proc.proc_entities in
    let bindings = flatten_entity_bindings relevant_entities in
    match chain_resolve k tantra_index bindings proc.proc_phala with
    | Some result ->
      (* update scene: add result as new binding to participating entities *)
      let updated = update_entity_with_result scene_acc proc.proc_entities result in
      (updated, result :: results)
    | None -> (scene_acc, results)
  ) (scene, []) scene.sc_sequence
```

---

## Part F: Remaining from Old Plan (Problem Solving + Robotics)

### F1 — Configurable chain depth

`yantra_resolver.ml:189` — change `~max_depth:4` to `~max_depth:config.rc_max_depth`.
Default 4 for simple queries. Problem mode uses 10. Scene mode uses 10.

### F2 — Problem ingestion (PROBLEM...END)

Multi-line block in REPL and socket. Collects all bindings across sentences before
resolving. Uses scene-extract on each sentence.

```
PROBLEM
A 2 kg block slides down a frictionless 30° incline of length 4 m.
At the bottom it compresses a spring of constant 500 N/m.
Find: (a) speed at bottom, (b) spring compression.
END
```

Lives in `problem_solver.ml`. Multi-target: parse `Find:` line, resolve each in order,
feed each result as binding into the next.

### F3 — Binary cache (`--cache` flag)

`Marshal`-based binary of `proof_graph` (includes CSR arrays). Explicit flag only;
default always parses from `.om` source. Checksum = mtime + size of each `.om` file.

```
--cache /path/to/graph.bin
  exists + checksum matches → load ~10ms
  missing or stale → parse → save
  load fails → fallback to parse (never crash)
```

### F4 — Robotics sensor demo

50Hz IMU stream → `command:sense` socket protocol → tantra chain:
`acceleration → force → seema-pariksha (threshold) → action`

`robot_session.ml`: Mutex-protected session. Bindings have TTL (stale after 0.1s for IMU).
`socket.ml`: Domain.spawn per connection (OCaml 5.2 Domain API).
`sensor_sim.ml`: standalone demo executable.

---

## Part G: What's Missing from the Graph (complete list)

### Sangati additions (existing files, new slokas)

| File | Addition | Purpose |
|---|---|---|
| `brahman/sangati/sandhi.om` | `"visheshanam-swarupa"` | Promotes sandhi to graph dimension |
| `brahman/sangati/matra.om` | `"visheshanam-swarupa"` | Promotes matra to graph dimension |
| `brahman/sangati/krama.om` | `"visheshanam-swarupa"` | Promotes krama to graph dimension |

### New .om nodes

| File | Why needed |
|---|---|
| `brahman/kosha/physics/processes/collision.om` | sandhi-swarupa dvaya-yukta: "collides, hits" |
| `brahman/kosha/physics/processes/rolling.om` | gati-swarupa angular-velocity-yukta: "rolls" |
| `brahman/kosha/physics/processes/sliding.om` | gati-swarupa: "slides" |
| `brahman/kosha/physics/processes/compression.om` | sandhi-swarupa spring-force-yukta: "compresses" |
| `brahman/kosha/physics/processes/oscillation.om` | spanda-swarupa: "oscillates, vibrates" |
| `brahman/kosha/physics/processes/suspension.om` | sandhi-swarupa tension-phala: "hangs, suspended" |
| `brahman/kosha/physics/processes/connection.om` | sandhi-swarupa dvaya-yukta: "connected, tied" |
| `brahman/kosha/language/english/context/frictionless.om` | friction-coefficient=0 implied |
| `brahman/kosha/language/english/context/rough.om` | friction-coefficient present |

### New OCaml modules

| Module | What |
|---|---|
| `vyakarana/lib/yantra_entity.ml` | `entity`, `process`, `scene` types + `scene_extract` + `scene_narrate` |
| `vyakarana/lib/problem_solver.ml` | PROBLEM...END ingestion + multi-target resolution |
| `vyakarana/lib/robot_session.ml` | Mutex-protected sensor binding store with TTL |

### Modified OCaml modules

| Module | What changes |
|---|---|
| `proof_graph.ml` | `visheshanam` → dynamic registry; `visheshanam_of_string` → hashtbl lookup; CSR grows with dim count; `save_binary`/`load_binary` |
| `om_parser.ml` | `decompose_compound` checks dynamic registry (not fixed match); two-pass parse |
| `yantra_resolver.ml` | `rc_max_depth` config; scene-aware entry point; krama chain resolution |
| `yantra_eval_primitives.ml` | Register `scene-extract`, `scene-narrate` primitives |
| `yantra_eval.ml` | Register arities |
| `socket.ml` | Domain.spawn per connection; `command:sense` + `command:problem` handlers |
| `vyakarana.ml` | PROBLEM...END in REPL; `--cache` flag; `materialize_csr` uses dynamic dim count |
| `lib/dune` | Add `yantra_entity`, `problem_solver`, `robot_session` modules |

### New tantras

| Tantra | What |
|---|---|
| `brahman/yantra/scene-understand.tantra` | Orchestrates scene-extract + scene-narrate |
| `brahman/yantra/scene-resolve.tantra` | Scene-aware tantra resolution |

---

## Implementation Order

### Phase 1: Graph knowledge + process nodes (no OCaml, low risk)

| Step | What | Files |
|---|---|---|
| 1 | Add `visheshanam-swarupa` to sandhi, matra, krama sangati | 3 existing .om edits |
| 2 | Write 7 process nodes | `brahman/kosha/physics/processes/*.om` |
| 3 | Write frictionless + rough context nodes | `brahman/kosha/language/english/context/` |
| 4 | Build and verify new nodes load | `dune build` |

### Phase 2: Dynamic graph dimensions (OCaml, medium risk)

| Step | What | Files |
|---|---|---|
| 5 | Change `visheshanam` type to int-indexed registry | `proof_graph.ml` |
| 6 | Two-pass parser: first pass loads nodes, second pass resolves dynamic dims | `om_parser.ml` |
| 7 | CSR materialize uses `dimension_registry` size | `proof_graph.ml` |
| 8 | Build + verify: all existing tests still pass, new dims registered | build + regression |

### Phase 3: Scene extraction (OCaml, medium risk)

| Step | What | Files |
|---|---|---|
| 9 | Define `entity`, `process`, `scene` types | `yantra_types.ml` or `yantra_entity.ml` |
| 10 | Implement `scene_extract` (root-dimension traversal) | `yantra_entity.ml` |
| 11 | Implement `scene_narrate` (scene → natural language) | `yantra_entity.ml` |
| 12 | Register `scene-extract`, `scene-narrate` primitives | `yantra_eval_primitives.ml` + `yantra_eval.ml` |
| 13 | Write `scene-understand.tantra` | `brahman/yantra/` |
| 14 | Build + test: "2 kg ball at 5 m/s collides with 3 kg block" → narration ✓ | manual test |

### Phase 4: Scene-aware resolver (OCaml, medium risk)

| Step | What | Files |
|---|---|---|
| 15 | `rc_max_depth` config in resolver | `yantra_resolver.ml` |
| 16 | Concept-type matching: tantra inputs → concepts via matra-yukta traversal | `yantra_resolver.ml` |
| 17 | Scene-aware entry point: fill inputs from entity values by concept | `yantra_resolver.ml` |
| 18 | Krama chain: process sequence → feed result into next process | `yantra_resolver.ml` |
| 19 | Wire into `anuvada-ganana.tantra` for multi-entity input | tantra edit |
| 20 | Build + test: collision, Atwood, 3-entity spring chain | manual test |

### Phase 5: Problem mode (OCaml, low risk)

| Step | What | Files |
|---|---|---|
| 21 | `problem_solver.ml`: parse_problem_block, solve_problem | new module |
| 22 | PROBLEM...END in madakkal REPL | `vyakarana.ml` |
| 23 | `command:problem` in socket server | `socket.ml` |
| 24 | Build + test: 5-step incline+friction, multi-target projectile | manual test |

### Phase 6: Binary cache (low risk)

| Step | What | Files |
|---|---|---|
| 25 | `save_binary` / `load_binary` in proof_graph | `proof_graph.ml` |
| 26 | `--cache` flag in vyakarana.ml | `vyakarana.ml` |
| 27 | Test: cold start → save → restart → load in <60ms | manual test |

### Phase 7: Robotics sensor demo (medium risk)

| Step | What | Files |
|---|---|---|
| 28 | `robot_session.ml`: Mutex + TTL binding store | new module |
| 29 | Domain.spawn per connection in socket.ml | `socket.ml` |
| 30 | `command:sense` handler | `socket.ml` |
| 31 | `sensor_sim.ml` + `vyakarana/demo/dune` | new files |
| 32 | Integration test: sensor_sim at 50Hz → correct chain output | manual test |
| 33 | Update `lib/dune` with new modules | `lib/dune` |

---

## What Is NOT Changing

| Thing | Status |
|---|---|
| `madakkal` REPL for simple queries | Unchanged |
| JSON socket `command:query` interface | Unchanged |
| All 102 existing tantras (+ 22 new motion tantras) | Unchanged |
| Default startup (no `--cache`) | Always parse from `.om` source |
| max_depth=4 for regular single queries | Unchanged (scene + problem mode use 10) |
| Flat `concept is number` extraction for simple queries | Still works, unchanged |

---

## Measured Targets

| Metric | Now | Target |
|---|---|---|
| "2 kg ball hits 3 kg block" → correct answer | ✗ (flat binding collision) | ✓ (scene extract) |
| Scene narration for any N-entity input | ✗ | ✓ |
| Cold start with `--cache` | 577ms | <60ms |
| 50Hz sensor chain latency | N/A | <3ms per reading |
| Graduate mechanics coverage | ~65% | ~90% |
| Multi-step word problem (5+ steps) | ~0% | ~85% |
