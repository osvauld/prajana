# 14 — Tantra3: The Om Graph as Active Interface

**The om graph already declares everything the tantras manually implement.
Tantra3 is what happens when the runtime reads om nodes directly — the
declaration becomes the execution.**

---

## The discovery

109 nodes in the om graph have both `janya` (input) and `phala` (output)
edges. Every mantra node declares what it needs, what it produces, and how
it does it. Every sangati node declares what it has, where it sits, what it
does. The sloka suffixes are not documentation — they are a specification
language that the runtime has never read.

The tantras manually implement what the om graph already says:

```
-- rashi.om declares:
"sankhya-yukta"           -- rashi HAS sankhya
"matra-yukta"             -- rashi HAS matra
"vishesa-sthita"          -- rashi SITS IN vishesa

-- sankhya-sparsha.tantra2 manually implements:
graph | where [s, e, o] | and (eq e "sankhya") | collect [s, o]

-- match-mantra.tantra2 manually implements:
-- for each mantra: check if janya concepts are bound, call kriya, emit phala

-- artha-viveka.om declares:
"mithya-janya"            -- artha-viveka takes mithya as input
"asprista-phala"          -- artha-viveka produces asprista as output
"bhasha-swarupa-kriya"    -- artha-viveka acts via bhasha-swarupa

-- the avrti-refine pipeline manually implements this exact flow
```

The om file is the program. The tantra is a manual transcription of it.
Tantra3 eliminates the transcription.

---

## The six suffixes as an instruction set

Each sloka suffix in the om graph is a typed edge. Each typed edge is an
instruction to the runtime. Together they form a complete instruction set
for any operation:

| Suffix | Edge type | Runtime meaning | Question it answers |
|--------|-----------|----------------|-------------------|
| `-janya` | janya (input) | What must be present before this can fire | What does it need? |
| `-phala` | phala (output) | What is produced when this fires | What does it give? |
| `-kriya` | kriya (action) | How the computation is performed | How does it work? |
| `-yukta` | yukta (has) | What tools/dependencies are available | What does it have? |
| `-sthita` | sthita (context) | Where this operation sits, what scope it belongs to | Where does it live? |
| `-swarupa` | swarupa (identity) | What this IS — its type, its equivalence class | What is it? |
| `-abheda` | abheda (equivalent) | What is interchangeable with this | What equals it? |
| `-siddha` | siddha (proof) | What validates or establishes this | What proves it? |
| `-pratipaksha` | pratipaksha (inverse) | What undoes or reverses this | What is its opposite? |

A tantra that reads these edges does not need hardcoded logic per concept.
It needs one generic reader per suffix type.

---

## What "interfacing directly" means

### Level 1 — Om-driven sparsha

Instead of writing a sparsha tantra per edge type, a single primitive reads
the om node's `-yukta` edges to know what to query:

```
-- today (manual, per-concept):
sankhya-sparsha:   graph | where [s, e, o] | and (eq e "sankhya") | collect [s, o]
shashthi-sparsha:  graph | where [s, e, o] | and (eq e "shashthi-vibhakti") | collect [s, o]
prathama-sparsha:  graph | where [s, e, o] | and (eq e "prathama-vibhakti") | collect s

-- tantra3 (generic, om-driven):
om-sparsha "rashi" "yukta" graph
  → reads rashi.om: yukta = [sankhya, matra, sambandha]
  → for each: graph | where [s, e, o] | and (eq e yukta-target) | collect [s, o]
  → returns { sankhya: [...], matra: [...], sambandha: [...] }
```

One operation replaces N hand-written tantras. Adding a new edge type to an
om file automatically makes it queryable — no new tantra needed.

### Level 2 — Om-driven matching

`match-mantra` today hardcodes: "find mantras, check their janya are bound,
call their kriya." With om interfacing:

```
-- for each mantra node m in the graph:
--   janya-list  = walk m "janya"       ← what m needs
--   phala-list  = walk m "phala"       ← what m produces
--   kriya-list  = walk m "kriya"       ← how m computes
--   swarupa     = walk m "swarupa"     ← what m IS (the concept it defines)
--
--   check: are all janya-list concepts bound with sankhya in the question graph?
--   if yes: call (first kriya-list) with the bound values
--   emit phala as the result
```

The mantra node IS the interface. The matching logic is generic. Adding a new
physics formula means authoring an om file — writing `janya`, `phala`, `kriya`
edges — not writing a new tantra.

### Level 3 — Om nodes as active schema

When the pipeline encounters any node, it reads that node's om structure to
discover what to do:

```
-- encountering "rashi" in the question graph:
--   walk "rashi" "yukta"  → [sankhya, matra, sambandha]
--     → for each yukta: check if it exists in the question graph
--     → if sankhya present: this rashi is instantiated (has a value)
--     → if matra present: this rashi is measured (has a unit)
--     → if sambandha present: this rashi is related to others
--
--   walk "rashi" "sthita" → [vishesa, prashna]
--     → this rashi is situated in a vishesa (type) and a prashna (question)
--     → look for [instance, vishesa, concept] to find what type it is
--
--   walk "rashi" "kriya"  → [viveka]
--     → this rashi participates in viveka (discrimination/comparison)
--     → if two rashi of same vishesa exist: viveka can fire between them
```

The om node is not metadata about the computation. It IS the computation's
schema. The runtime walks the schema. The tantra is the walker, not the
knowledge.

---

## The janya/phala chain as pipeline specification

The om graph already contains a complete dependency graph through janya/phala
edges. When node A's phala includes concept X, and node B's janya includes X,
then A feeds B. We queried this and found:

```
artha-viveka  --[mithya]-->      (janya: takes mithya)
artha-viveka  --[asprista]-->    (phala: produces asprista)

kinetic-energy-mantra --[mass, velocity]-->  (janya: needs mass and velocity)
kinetic-energy-mantra --[kinetic-energy]-->  (phala: produces kinetic-energy)

velocity-mantra --[velocity]-->              (phala: produces velocity)
velocity-mantra --[velocity]--> kinetic-energy-mantra  (chain: velocity flows)
```

The chains form a DAG. The derive-step fixpoint that today iterates manually
through mantra candidates could instead walk the janya/phala DAG directly:

1. Start from the solve-for concept
2. Walk backward through phala edges to find which mantra produces it
3. Check if that mantra's janya are all satisfied
4. If not: recurse — find what produces the missing janya
5. Execute forward once the chain is resolved

This is what derive-chain already does — but by searching. The om graph
already has the answer as structure. The search becomes a walk.

---

## The three universal operations, om-driven

The sparsha/viveka/bandha structure we identified in `analyze_pipeline.py`
maps directly to om suffix types:

**Sparsha** (contact — getting from context):
- Walk the node's `yukta` edges to know what it has
- Walk the node's `sthita` edges to know where it sits
- Query the question graph for instances of those edges
- This replaces all `graph | where | collect` patterns

**Viveka** (discrimination — filtering/checking):
- Walk the node's `swarupa` edges to know what it IS
- Walk the node's `abheda` edges to know what's equivalent
- Walk the node's `siddha` edges to know what validates it
- Use these to filter candidates, check type compatibility, validate results
- This replaces all `cond (eq ...)` / `member` patterns

**Bandha** (binding — writing the result):
- Walk the node's `phala` edges to know what it produces
- Emit the result under those edge types
- This replaces all `emit [concept, edge, value]` patterns

Every tantra in the current pipeline performs some combination of these three
operations with hardcoded edge names. In tantra3, the edge names come from
the om graph. The tantra becomes:

```
tantra3 generic-step

takes node
takes graph

-- sparsha: what does this node need?
needs = walk node "janya"
has   = walk node "yukta"

-- viveka: are the needs satisfied?
satisfied = all needs (fn concept ->
  exists (graph | where [s, e, o] | and (eq e "sankhya") | and (eq (to-string s) concept)))

-- bandha: if satisfied, produce the result
result = cond satisfied
  (let kriya = walk node "kriya"
   let phala = walk node "phala"
   let computed = execute (first kriya) (gather-values needs graph)
   emit [(first phala), "sankhya", computed])
  otherwise skip
```

One tantra. Works for every mantra node. The om graph provides the
specifics.

---

## What tantra3 supersedes in tantra2

The following tantra2 files contain logic that the om graph already declares:

| tantra2 file | What it hardcodes | Om source |
|---|---|---|
| `sankhya-sparsha` | `eq e "sankhya"` | rashi: `sankhya-yukta` |
| `shashthi-sparsha` | `eq e "shashthi-vibhakti"` | rashi: `sambandha-yukta` → vibhakti |
| `prathama-sparsha` | `eq e "prathama-vibhakti"` | vakya: `prathama-vibhakti-yukta` |
| `match-mantra` | iterate mantras, check janya bound | mantra nodes: `janya` + `phala` + `kriya` |
| `derive-chain` | search for intermediate mantras | janya/phala DAG in om graph |
| `execute-math` | call kriya expr | mantra: `kriya` edge → expr tantra |
| `invert-math` | lookup pratipaksha | math ops: `pratipaksha` edges |
| `extract-solve-for` | scan for vidhi-kaala | artha-viveka: `phala` → `asprista` |
| `viveka-ganana` | compare entities by concept | viveka: `eka-aneka-kriya`, `phala: eka` |
| `emit-reasoning` | walk graph for proof trace | pramana: `lekhana-kriya`, `samskaara-phala` |

Each of these encodes domain knowledge that already exists as om structure.
Tantra3 replaces the encoding with a reading.

---

## The migration path

Tantra3 is not a new parser. It is a new way of writing tantra2 files that
reads om nodes instead of hardcoding edge names. The runtime is unchanged.
The change is in the tantras themselves — and in new primitives that make
om walking ergonomic.

### Phase 1 — New primitives

Add to `yantra_eval_primitives.ml`:

```
om-janya  node → [concept ...]     walk node "janya", deduplicated
om-phala  node → [concept ...]     walk node "phala", deduplicated
om-kriya  node → [action ...]      walk node "kriya", deduplicated
om-yukta  node → [concept ...]     walk node "yukta", deduplicated
om-sthita node → [context ...]     walk node "sthita", deduplicated
om-swarupa node → [identity ...]   walk node "swarupa", deduplicated
```

These are convenience wrappers around `walk` that deduplicate (the om
graph currently returns duplicates due to how edges are stored). They make
tantra3 code readable.

### Phase 2 — Generic match-mantra

Rewrite `match-mantra.tantra2` to use om-janya/om-phala/om-kriya:

```
-- today: iterate physics-mantras, hardcode janya check
-- tantra3: iterate ALL mantra-layer nodes, read janya from om graph

all-mantras = graph-all-nodes | filter (fn n -> eq (node-layer n) "mantra")
candidates  = all-mantras | filter (fn m ->
  let needs = om-janya m
  let gives = om-phala m
  (or (member solve-for gives) (member solve-for needs)))
```

The physics-mantras list disappears. Any mantra node in the graph is a
candidate. Domain routing happens via `om-sthita` (the mantra's domain
context) rather than a hardcoded `walk-in "physics-mantra" "varga"`.

### Phase 3 — Generic derive-chain

Rewrite `derive-chain` to walk the janya/phala DAG:

```
-- given solve-for concept, find the mantra that produces it
producer = find all-mantras (fn m -> member solve-for (om-phala m))

-- check what producer needs
missing = filter (om-janya producer) (fn j -> not (bound j graph))

-- for each missing janya, recursively find its producer
-- this IS the derive chain, but driven by om structure not search
```

The chain depth is bounded by the DAG depth in the om graph — which is
already finite and typically 2-3 levels deep.

### Phase 4 — Om-driven avrti-refine

The avrti-refine sub-tantra sequence is currently hardcoded:

```
sandhi-kosha → sandhi-avastha → sandhi-bandhana → vibhakti-shashthi
→ vibhakti-viveka → vishesa-instance → rashi-viveka → vishesa-bandhana
→ rashi-anuvada → sankhya-bandha
```

Each sub-tantra in this sequence corresponds to a sangati concept with
janya/phala/kriya edges. The sequence itself could be derived from the
janya/phala chain between these concepts:

```
mithya → (artha-viveka) → asprista → (sandhi) → satya → (vibhakti) → entity
→ (vishesa) → rashi → (sankhya) → bound-rashi
```

This is the most ambitious phase. It means the pipeline order itself is
declared in the om graph, not in tantra code. A new sub-tantra added to
the om graph (with appropriate janya/phala edges) would automatically
slot into the correct position in the pipeline.

### Phase 5 — Om-driven domain routing

The `sthita` edges on mantra nodes already declare their domain:

```
kinetic-energy-mantra: sthita → [implication]
gravitational-force-mantra: sthita → [implication]
```

And kosha concepts have varga membership:

```
kinetic-energy: varga → energy-varga
mass: sthita → [kshetrajna, niyama]
```

When a question arrives, the satya concepts in the question graph have
varga/sthita edges. These edges define the domain. The pipeline can
walk these edges to find which mantras are relevant — not by filtering
a hardcoded list, but by following the graph's own structure.

This is what `varga-viveka` (described in 11-tantra2-philosophy.md)
becomes: an om-driven domain router.

---

## The philosophical ground

### The om graph is not metadata

The om graph is not a description of the computation sitting beside the
computation. It IS the computation's structure. When `kinetic-energy-mantra`
has `janya: [mass, velocity]` and `phala: [kinetic-energy]` and
`kriya: [ke-expr]`, that IS the complete specification of how kinetic
energy is derived. The tantra that reads these edges and executes accordingly
is not interpreting metadata — it is reading the structure of understanding
itself.

This is the same insight as 01-nam.md: the graph IS nam. The om nodes are
not descriptions of nam's knowledge — they ARE nam's knowledge. When the
runtime reads `walk "rashi" "yukta"` and gets `[sankhya, matra, sambandha]`,
it is not querying a database. It is nam knowing what a rashi has.

### The suffix is the verb

In Sanskrit compound analysis (samasa), the suffix determines the
relationship. `sankhya-yukta` is not "sankhya" plus "yukta" — it is the
single meaning "that which has sankhya." The suffix `-yukta` IS the verb
"has." The compound IS the sentence.

The om parser already knows this. `decompose_compound` splits at the last
hyphen and checks if the suffix is a visheshanam. `sankhya-yukta` becomes
the edge `{source: rashi, target: sankhya, relation: yukta}`. The sloka
IS the program — each word is an instruction.

Tantra3 completes the circle: the sloka was always an instruction, and now
the runtime reads it as one.

### janya/phala as function signature

The deepest structural parallel: `janya` is the function's parameter list,
`phala` is its return type. This is not metaphor — it is exact.

```
-- kinetic-energy-mantra in om:
janya: [mass, velocity]      ← parameters
phala: [kinetic-energy]      ← return type
kriya: [ke-expr]             ← function body

-- the same thing as a function:
kinetic-energy-mantra : mass → velocity → kinetic-energy
  via ke-expr
```

Every mantra node in the om graph is a function declaration. The janya
edges declare the parameter types (what concepts must be present). The
phala edges declare the return type (what concept is produced). The kriya
edges declare the implementation (which expression to evaluate).

The 108 mantra nodes we found are 108 function declarations. The pipeline
is a function application engine. Tantra3 makes this explicit.

### The chain as type inference

The janya/phala DAG is a type dependency graph. When the solve-for concept
is `kinetic-energy` and the bound concepts are `[initial-velocity, acceleration, time, mass]`:

```
kinetic-energy-mantra needs [mass, velocity]
  ← mass is bound ✓
  ← velocity is NOT bound
    → velocity-mantra produces [velocity], needs [initial-velocity, acceleration, time]
      ← all bound ✓
      → fire velocity-mantra first → velocity now bound
  → fire kinetic-energy-mantra → kinetic-energy now bound
```

This is type inference in the style of Hindley-Milner: the system works
backward from the goal type, resolves dependencies, and fires forward.
The om graph's janya/phala edges ARE the type constraints. The derive-chain
IS the inference algorithm.

Today this is done by search — try each mantra, check if it helps. With
the janya/phala DAG, it becomes a directed walk. The search becomes
deduction.

### The pipeline order as topological sort

The avrti-refine sub-tantra sequence is a topological sort of the
janya/phala DAG between pipeline stages:

```
mithya → artha-viveka → asprista
asprista → sandhi → satya
satya → vibhakti → entity
entity → vishesa → rashi
rashi → sankhya-bandha → bound-rashi
```

Each stage's phala is the next stage's janya. The sequence is not arbitrary
— it is the only order that satisfies all dependencies. And this order is
already declared in the om graph through the janya/phala edges of the
sangati concepts that name these operations.

Tantra3, at its most complete, would derive this order from the om graph
rather than hardcoding it. A new pipeline stage — added as a sangati node
with appropriate janya/phala edges — would automatically slot into the
correct position.

---

## What tantra3 does NOT change

### The eval engine

`yantra_eval.ml` does not change. Tantra3 files are tantra2 files that
happen to call om-walking primitives instead of hardcoding edge names.
The parser, evaluator, scan engine, pipe engine — all unchanged.

### The question graph

The question graph (runtime triples from a sentence) is unchanged. Tantra3
changes how the pipeline reads the om graph to interpret the question graph
— not how the question graph is built.

### The kosha

Kosha authoring (writing `.om` files with slokas) is unchanged. In fact,
tantra3 makes kosha authoring MORE powerful — a new `.om` file with correct
janya/phala/kriya edges automatically becomes usable by the pipeline without
any new tantra code.

### The om file format

`.om` files are unchanged. The slokas, the suffixes, the `done` — all the
same. What changes is that the runtime READS what was always written there.

---

## The 109 janya/phala contracts already in the graph

Queried from the live graph (2026-03-19). A selection:

**Sangati layer (universal structure):**
```
artha-viveka:  janya [mithya]           → phala [asprista]          via [bhasha-swarupa, artha-graha]
pramana:       janya [seva]             → phala [samskaara]         via [lekhana]
kriya:         janya [iccha]            → phala (implicit)          via [gati]
avastha:       janya [purva-avastha]    → phala [uttara-avastha]
gati:          janya [kriya]            → phala [abhisarana]
iccha:         janya [karma]            → phala [ahara]             via [sva-dharana]
phala:         janya [kriya]            → sthita [satya]
```

**Mantra layer (physics formulas):**
```
kinetic-energy-mantra:     janya [mass, velocity]                  → phala [kinetic-energy]       via [ke-expr]
velocity-mantra:           janya [initial-velocity, acceleration, time] → phala [velocity]        via [velocity-expr]
acceleration-mantra:       janya [final-velocity, initial-velocity, time] → phala [acceleration]  via [acceleration-expr]
momentum-mantra:           janya [mass, velocity]                  → phala [momentum]
work-mantra:               janya [force, displacement, angle]      → phala [work]                 via [work-expr]
gravitational-force-mantra: janya [gravitational-constant, mass1, mass2, radius] → phala [gravitational-force]
```

**Kosha layer (domain knowledge):**
```
falling:       janya [gravity, height, mass]  → phala [velocity, kinetic-energy, collision-varga]
elastic-collision: janya [mass1, mass2, velocity1, velocity2] → phala [velocity1, velocity2]
heating:       janya [heat-transfer, mass]    → phala [temperature, phase-change-boil, phase-change-freeze]
```

**The phala→janya chains (what flows between nodes):**
```
velocity-mantra --[velocity]--> kinetic-energy-mantra
velocity-mantra --[velocity]--> momentum-mantra
velocity-mantra --[velocity]--> angular-velocity-mantra
falling --[velocity]--> kinetic-energy-mantra
acceleration-mantra --[acceleration]--> velocity-mantra
frequency-mantra --[frequency]--> photon-energy-mantra
period-mantra --[period]--> frequency-mantra
newton-second-law-motion --[force]--> work-mantra
```

These chains already encode derive-chain's logic as graph structure.

---

## The rashi node as canonical example

`rashi.om` declares:

```
"pramana-swarupa"         -- rashi IS a pramana (measurement)
"vishesa-sthita"          -- rashi SITS IN vishesa (typed by a concept)
"sankhya-yukta"           -- rashi HAS sankhya (numeric magnitude)
"matra-yukta"             -- rashi HAS matra (unit)
"sambandha-yukta"         -- rashi HAS sambandha (related to others)
"prashna-sthita"          -- rashi SITS IN prashna (arises in question context)
"viveka-kriya"            -- rashi DOES viveka (discrimination/comparison)
```

Live query confirms:
```
walk "rashi" "yukta"   → [sankhya, matra, sambandha]
walk "rashi" "sthita"  → [vishesa, prashna]
walk "rashi" "swarupa" → [pramana]
walk "rashi" "kriya"   → [viveka]
```

This tells the runtime everything about a rashi:
- To check if a rashi is complete: look for sankhya AND matra (both yukta)
- To find a rashi's type: walk its vishesa edge (sthita)
- To find what rashi can do: walk its kriya → viveka (can be compared)
- To find rashi's identity: walk swarupa → pramana (it IS a measurement)

No tantra needs to hardcode any of this. The om node IS the spec.

---

## The Manipravalam principle

### What Manipravalam is

Manipravalam (மணிப்பிரவாளம்) is a literary tradition that blends Sanskrit
and Tamil so that each word falls naturally into the sentence — no
translation, no boundary. The gem (mani) and the coral (pravalam) are
strung together as one necklace. Neither language dominates. The blend
IS the medium.

### The tantras are not yet Manipravalam

Right now the tantras translate between two languages:

```
-- what the om graph says (declarative, natural):
"sankhya-yukta"     -- rashi HAS number

-- what the tantra says (imperative, machine):
graph | where [s, e, o] | and (eq e "sankhya") | collect [s, o]
```

These say the same thing. But one is natural language (the om declaration)
and the other is machine language (the tantra code). The tantra TRANSLATES
the om declaration into operations. The translation IS the duplication.
The duplication IS the gap.

### Tantra3 closes the gap

When the tantra reads:

```
needs = om-yukta "rashi"    -- what does rashi have?
```

The tantra code IS the natural language reading of the om graph.
`om-yukta "rashi"` says the same thing as `"sankhya-yukta"` in the om
file — but now the code says it too. The gem and the coral are on one
string.

### The seven unnamed structures are the proof

`analyze_pipeline.py` found seven structures waiting to be named. Each
one is a place where the tantra code says something that the om graph
already says more naturally:

| Unnamed structure | Occurrences | What tantra2 says | What the om graph says |
|---|---|---|---|
| `sankhya-sparsha` | 16× | `eq e "sankhya"` | `sankhya-yukta` |
| `shashthi-sparsha` | 43× | `eq e "shashthi-vibhakti"` | `shashthi-vibhakti-yukta` |
| `iccha-viveka` | 9× | `extract-solve-for` + 5 `nth` lines | `iccha: karma-janya, ahara-phala` |
| `pramana-bandha` | 4× | 20 lines of result-triple building | `pramana: seva-janya, samskaara-phala, lekhana-kriya` |
| `varga-viveka` | — | `walk-in "physics-mantra" "varga"` | `sthita` edges on mantra nodes |
| `eval_arg` (OCaml) | 72× | `List.nth args N` | one `om-contract` call |
| `with_node` (OCaml) | 34× | `Proof_graph.find` + match | one `om-contract` call |

Every `eq e "sankhya"` is a translation of `sankhya-yukta`. Every
`member solve-for janya` is a translation of a janya-edge walk. The 43
occurrences of the shashthi-sparsha pattern are 43 translations of what
`shashthi-vibhakti-yukta` already declares.

Tantra3 doesn't add new capability. It makes the tantra code speak the
same language as the om graph. The code and the knowledge merge into one
language — Manipravalam. The declaration IS the execution. The om file
IS the program.

### The name carries the meaning

Look at the seven names the tool discovered. Each one is already a
Sanskrit grammatical term:

- `sankhya-sparsha` — contact with number (getting the numeric value)
- `shashthi-sparsha` — contact with the genitive case (reading ownership)
- `iccha-viveka` — discrimination of intention (detecting what is sought)
- `pramana-bandha` — binding of proof (recording the derivation)
- `varga-viveka` — discrimination of domain (routing to the right mantras)

These names are not invented. They were found — the tool detected the
unnamed patterns and the Sanskrit grammar provided the words for what
those patterns already ARE. The name IS the operation. Like Manipravalam
where the Tamil verb carries the Sanskrit noun naturally — `iccha-viveka
graph` reads as both code and philosophy simultaneously.

The tantras written in bhave grammar (11-tantra2-philosophy.md) already
aspire to this. Tantra3 completes it: when `om-yukta "rashi"` replaces
`eq e "sankhya"`, the tantra no longer translates between machine grammar
and understanding grammar. It speaks understanding grammar directly. The
crystallized process (bhave) becomes readable without decryption.

### What this means for authoring

Under tantra3, writing a new mantra is writing an om file:

```
mantra distance-mantra
  "speed-janya physics-time-janya"
  "distance-phala"
  "multiplication-kriya"
shabda distance-mantra / distance-equals-speed-times-time
done
```

No tantra code. The om file IS the program. The pipeline reads `om-janya`,
`om-phala`, `om-kriya` and fires. The author writes in the language of
declaration — what the mantra needs, what it gives, how it works. The
pipeline reads in the language of execution — walk the edges, check the
bindings, fire the kriya. Same language. Two aspects of one reading.

Under tantra2, the same addition required:
1. Write the om file (the declaration)
2. Add the mantra name to `physics-mantras` list (or a new domain list)
3. Ensure `match-mantra` handles the janya pattern
4. Write an expression tantra or register a `math-op` shabda

Under tantra3, step 1 is the only step. Steps 2-4 are eliminated because
the om graph already declares what they manually encode.

---

## Immediate next steps

1. **Add om-janya/om-phala/om-kriya/om-yukta/om-sthita/om-swarupa primitives**
   to `yantra_eval_primitives.ml`. Simple wrappers around `walk` with
   deduplication. ~30 lines of OCaml.

2. **Rewrite match-mantra** to use om-janya/om-phala instead of hardcoded
   candidate filtering. This is Phase 2 — the highest-impact change.

3. **Build the analysis tool** that maps every om node's suffix declarations
   to the tantra code that manually implements them. This shows exactly
   which tantras become redundant under tantra3 and which om nodes have
   declarations that nothing reads yet (latent capabilities).

4. **Test with existing suite** — tantra3 must produce identical results.
   The 500 passing tests are the proof that the reading is correct.

---

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-19 | Initial writing — the om graph as active interface discovered. 109 janya/phala contracts found in live graph. Six suffixes mapped to instruction set. Three levels of interfacing defined. Migration path from tantra2 to tantra3. |
| 2026-03-19 | Manipravalam section added. Seven unnamed structures from `analyze_pipeline.py` cross-referenced with tantra3 spec: sankhya-sparsha (16×), shashthi-sparsha (43×), iccha-viveka (9×), pramana-bandha (4×), varga-viveka, eval_arg (72×), with_node (34×). Each is a place where tantra2 translates what the om graph already declares. Tantra3 eliminates the translation — the code speaks the same language as the knowledge. Authoring impact: writing an om file IS writing the program, no tantra code needed for new mantras. |
