# Question Graph — Sentence as Graph Fragment

## Core Insight

A question is not a sequence of tokens to be matched against formulas.
A question IS a partial instantiation of a mantra node.

The sentence "what is kinetic energy of a 5kg ball at 10m/s" assembles
a graph fragment that is structurally identical to the kinetic-energy-mantra
node with some krama-rhs slots filled and the krama-lhs slot empty (the unknown).

The answer is the missing slot. The graph walk finds it.

```
sentence
  → stateful reduce (word by word)
  → question graph (partial mantra instantiation)
  → match: which mantra has all krama-rhs slots bound?
  → execute-chain
  → answer (fills krama-lhs slot)
```

## The Shift from Pipeline to Graph

**Before (pipeline)**:
```
sentence → token list → decompose → match-formula → execute → respond
```
Each step is a transformation on a linear sequence. Matching is separate from parsing.

**After (graph)**:
```
sentence → question graph → graph walk → answer
```
Parsing IS matching. The question graph merges with the knowledge graph.
The mantra that fits is found by structural overlap, not formula search.

## Stateful Reduce as Graph Builder

There is no separate tokenizer or classifier. The reduction IS the classification.
Each word hits the knowledge graph directly. The graph structure tells you what
the word means — no classification logic needed in the tantra.

```
reduce words [] (fn graph word ->
  node = word-node word          -- O(1) hit or miss
  -- the node's own structure (role, layer, krama-rhs) drives the graph extension
  -- the partial graph so far IS the context
  extend graph node word)
```

The partial graph at each step IS the context. No separate `context-of` call.
No separate `extend-graph` sub-tantra. One reduce, one tantra.

The connections made during reduction ARE the question.
Mantra convergence happens incrementally — as bound concepts accumulate,
the matching mantra surfaces naturally from dimensional overlap.

Each word falls into one of these graph operations:

| Word hits                  | Graph operation                                           |
|---|---|
| node with role=intent      | set solve-for dimension                                   |
| kosha concept node         | add to known dimension space; connects to active mantra   |
| value+unit (split-numeric) | bind value to active concept slot                         |
| grammar node               | structural edge — sets relationship for next concept      |
| no hit (unknown)           | enters mithya layer (provisional — see below)             |

## Mithya-Satya: Unknowns as Provisional Truth

An unknown word is not an error. It is not discarded. It is **mithya** — apparent,
provisional. It exists at the conventional level. Context pressure during the
reduction determines whether it becomes **satya** (real, enters the dimensional space)
or remains mithya (holds but does not affect matching).

This also makes unknowns **avidya** — not-yet-known. Avidya is not ignorance to be
discarded but the ground from which vidya (knowledge) emerges. The unknown word is
a seed — context pressure is what allows it to germinate into a known dimension.

The question graph therefore has two layers:

```
Satya layer  — resolved, confirmed dimensions. These drive mantra matching.
               mass: 5.0 kg, velocity: 10.0 m/s, solve-for: kinetic-energy

Mithya layer — provisional unknowns. Held, not discarded. Not yet real.
               "ball" → candidate entity label
               "kgm/s" → candidate unit string (high pressure → may become satya)
```

### Context Pressure

Context pressure is what collapses mithya → satya:

| Condition                                    | Pressure |
|---|---|
| Previous word was a number                   | high     |
| Active concept has unfilled unit slot        | high     |
| Unknown adjacent to a known value-unit       | medium   |
| Unknown isolated, no active slot nearby      | low      |

High pressure: unknown enters satya layer (e.g. `"kgm/s"` after `50` → unit candidate).
Low pressure: unknown stays mithya — available for dialogue generation ("did you mean...?")
but does not participate in mantra matching.

Mantra matching operates ONLY on the satya layer.
The mithya layer is available for dialogue, narration, and future resolution.

## Graded Ring Structure

The question graph is graded:

```
Grade 0 — structural:   grammar edges (copula, prepositions, articles)
Grade 1 — quantities:   concept nodes (mass, velocity, kinetic-energy)
Grade 2 — values:       bindings (5kg → mass, 10m/s → velocity)
Grade 3 — intent:       solve-for directive (what, find, calculate)
```

Grade boundaries are sentence boundaries (period = reset).
Additive op (⊕): comma / "and" = parallel slots at same grade.
Multiplicative op (⊗): cross-reference ("the second joint", "joint 1").

## Morphological Word Lookup — Algebraic, Not Hardcoded

Word lookup is not a flat key match. A surface word form is a stem composed with
a morpheme. The lookup must invert the morpheme to find the stem.

```
word-form = stem ⊗ morpheme
lookup(word) = word-node(inverse-morpheme(word)) → node
```

Morphemes are graph nodes in `brahman/bhasha/english/grammar/morphology/`:

```
english-plural-regular   suffix:s              (metre → metres, kilogram → kilograms)
english-plural-es        suffix:es             (mass → masses, torque → torques)
english-plural-ies       suffix:ies stem-suffix:y  (velocity → velocities, frequency → frequencies, density → densities)
english-plural-irregular                       (no rule — explicit plural-form: key on node)
```

### Morpheme nodes as graph connectors

A morpheme node is not just a rule — it is a **connector** between singular and plural
in the graph. It has the same bidirectional structure as mantra nodes (krama/pratipaksha):

```
velocity  --vachana-bahu-->  english-plural-ies
english-plural-ies  --vachana-eka-->  velocity
```

This gives both directions from one node:
- **Lookup** (inverse): "velocities" → strip `ies`, add `y` → "velocity" → word-node hit
- **Generation** (forward): `to-english` on velocity in plural context → follow `vachana-bahu`
  edge → `english-plural-ies` → apply suffix → "velocities"

**Regular morphemes do not need explicit edges on every concept node.**
The suffix rule handles them automatically during lookup (strip suffix → retry) and
generation (inspect character ending → infer morpheme → apply suffix).

**Only irregular nodes need explicit edges:**
`datum → data` cannot be inferred. That node gets `vachana-bahu: english-plural-irregular`
and `plural-form:data` in its shabda.

### lookup-word — tantra (bridge) ✅ done

`lookup-word.tantra` is fully graph-native. Three steps:
1. **Graph lookup** — `lookup word` (direct `Proof_graph.find` — kosha concept wins)
2. **Abbreviation lookup** — `word-node word` (word: keys only — kg, N, m, rad)
3. **Graph-walk morpheme inversion** — `try-morpheme-rules word`
   walks `walk-in "vachana-bahu" "sthita"` to get all rule nodes,
   reads `suffix`/`stem-suffix` from each rule's shabda,
   applies inverse, returns first `lookup` hit

No hardcoded suffix list. Adding a new morpheme `.om` file is picked up automatically.

**Future**: when `execute-chain` gains short-circuit support, `lookup-word-mantra`
becomes a krama chain where each step is a graph op. Until then `lookup-word.tantra`
is the bridge implementation.

Lookup strategy:
1. **Direct graph hit** — `lookup word` → kosha node if it exists → done
2. **Abbreviation** — `word-node word` → word: key hit (kg→kilogram, N→newton)
3. **Morpheme inversion** — walk bahu-vachana rules from graph, apply inverse suffix
4. **Miss** → `_none` → mithya layer

**Why `lookup` before `word-node`**: `word-node` uses the `word_index` hashtable
which is built by `build_word_index` in a single non-deterministic `Hashtbl.iter` pass.
Mantra nodes with `name:acceleration` in their shabda can claim the slot before the
kosha node `acceleration` is auto-indexed — purely an iteration order accident.
`lookup` goes directly to `Proof_graph.find k word` which always returns the actual
graph node if one exists by that name. Concept nodes (`acceleration`, `kinetic-energy`)
are always in the graph as kosha nodes. `lookup` hits them correctly every time.

This is the same mechanism as Sanskrit vibhakti (case endings) projected onto English.
`vachana` (number: singular/plural) is already a grammar dimension — plural is just
`vachana=bahu` applied through the morpheme operation.

The morpheme IS the morphism. Forward application = generation. Inverse = lookup.
Same node, same edge, both directions.

### SI Units — English surface forms (scope: physics)

Focus is English + physics. All SI unit plurals in physics are regular or invariant —
no irregular forms exist. No explicit `vachana-bahu` edges needed on any SI unit node.

**Plural patterns in physics:**

| Morpheme | Physics examples |
|---|---|
| +s (regular) | metres, kilograms, newtons, joules, watts, pascals, amperes, radians |
| +es | no physics SI units |
| -y+ies | no physics SI units (velocity/frequency are concepts, not units) |
| invariant | hertz (singular = plural), kelvin (used as invariant) |

Invariants are handled by direct hit — `word-node "hertz"` → `hertz`. No morpheme needed.

**Physics concept plurals** (mass, velocity, frequency etc.) are all regular:
- `masses` → strip `es` → `mass` ✓
- `velocities` → strip `ies`, add `y` → `velocity` ✓
- `frequencies` → strip `ies`, add `y` → `frequency` ✓
- `accelerations` → strip `s` → `acceleration` ✓

Concept nodes are auto-indexed by node name — `word-node "mass"` → `mass` without any
explicit `word:` key. Plural lookup goes through lookup-word-mantra suffix rules.

### Word: keys carry only canonical + abbreviations:

Singular stems and abbreviations only. Plurals handled by morpheme inversion.

**Base unit .om files** — need explicit `word:` keys for abbreviation lookup:

```
kilogram.om:  word:kg,kilogram          ✅ done
metre.om:     word:m,metre,meter        ✅ done
second.om:    word:s,sec,second         ✅ done
newton.om:    word:N,newton             ✅ done
radian.om:    word:rad,radian           ✅ done
```

**matra-beeja generated units** — the third field in matra-beeja.shabda is now
formatted as `word:joule,J description` (✅ done — concepts-for-unit removed).
Symbol abbreviations (J, W, Pa, Hz, A, V, etc.) are now indexed via word_index.

## Unit Resolution — Algebraic, Not Tokenized

Unit strings like `kgm/s`, `m/s2`, `Nm` are algebraic expressions.
They are NOT parsed with a hardcoded abbreviation table.

### Resolution priority:

1. **word-node direct** (with morpheme inversion) — `word:kg` on kilogram.om → exact hit
2. **Context prior** — if question graph already has concept `momentum`,
   and momentum's unit (via unit-of-concept-mantra) is `kilogram-metre-per-second`,
   check dimensional compatibility of the unknown unit string
3. **Dimensional similarity** — compute dim-vector by composing
   known base-unit dim-vectors (from word-node hits on substrings),
   then `dim-to-unit` → canonical unit node
4. **Unresolved** — stays in mithya layer as `unresolved-unit` triple

## Mantra vs Tantra — The Core Distinction

**Mantra = raw computation.** Fixed structure, no branching. A formula, a lookup, a
transform. The krama chain executes it deterministically. Mantras don't reason —
they compute.

**Tantra = chain of thought.** Reasoning, decision, orchestration. Connects concepts,
branches on context, strings mantras together to answer a question. Tantras don't
compute — they reason.

```
tantra (chain of thought)
  calls mantras (raw computation)
  reads graph (knowledge)
  returns understanding
```

Tantras are written in the graph's own vocabulary. Graph node names (`lookup`,
`get`, `find`, `walk`, `emit`) serve as verbs. Connectives (`and`, `of`, `in`,
`for`, `with`) are grammar nodes. The meaning lives in the nodes — a tantra reads
as a sentence because it IS a sentence over the graph.

A tantra sentence:
```
lookup word and get role and find active-concept in g
emit triples for word with role and active-concept
walk g and append triples
```

### Decision Table

| Component | Type | Reason |
|---|---|---|
| `lookup-word-mantra` | **Mantra** | Fixed krama chain: direct→strip-s→strip-es→strip-ies. Ordered attempts, not reasoning. |
| `unit-compose-mantra` | **Mantra** | Fixed krama chain: dim-vector×2 → dim-op → dim-to-unit. Pure computation. |
| `unit-of-concept-mantra` | **Mantra** (deferred) | Requires graph-walk krama steps not yet in stack machine. Tantra for now. |
| `lookup-word` | **Tantra** (bridge) | Backs `lookup-word-mantra` until stack machine has short-circuit. Branching = reasoning. |
| `emit-triples` | **Tantra** (P8-B) | Chain of thought: given word sense + graph context, decide what to assert. |
| `build-question-graph` | **Tantra** (P8-A) | Chain of thought: orchestrates lookup → emit → extend across all words. |
| `match-mantra` | **Tantra** (P8-D) | Chain of thought: reason over graph to find which mantra fits the question. |
| `narrate-response` | **Tantra** (P8-D2) | Chain of thought: compose understanding + matching + execution into natural language. |
| `anuvada-ganana` | **Tantra** | Top-level chain of thought: build graph → match → execute → narrate. |
| `classify-question` | **Tantra** (deferred) | Reasoning: route compute/theoretical/proof/mixed. |
| `implication-walk` | **Tantra** (deferred) | Reasoning: BFS over implication edges. |
| `generate-question` | **Tantra** (deferred) | Reasoning: dialogue slot filling. |

### Why `lookup-word-mantra` is a mantra despite its branching appearance

The sequence `try-direct → try-strip-s → try-strip-es → try-strip-ies` is a
**fixed-structure krama chain** — ordered attempts with early exit. The structure
(which morphemes, in which order) is declarative graph knowledge, not reasoning.
Once `execute-chain` gains short-circuit support, `lookup-word.tantra` becomes
purely internal to the mantra. Until then it is the bridge implementation.

### Why `unit-compose-mantra` is a mantra today

`unit-compose-mantra` krama steps are:
1. `dim-vector` (existing OCaml primitive) — get dim of unit-a
2. `dim-vector` — get dim of unit-b
3. `dim-op` (existing OCaml primitive) — apply dimensional operation
4. `dim-to-unit` (existing OCaml primitive) — map back to unit node

All four steps are backed by OCaml primitives already reachable via `apply-op`.
The stack machine can execute this chain today. No short-circuit needed.
This replaces `matra-ganana.tantra` calls for composed unit resolution.

### Why `unit-of-concept-mantra` is deferred

Getting a concept's unit requires walking `kramanusara`/`apeksha` graph edges and
then composing results. Graph-walk is not a krama step the current stack machine
handles. This stays as a `unit-of-concept.tantra` for now — the same logic as the
old `matra-viveka.tantra` but cleanly named and placed in `brahman/yantra/`.

## Unit Composition as Mantra (P8-E)

`matra-ganana.tantra` and `matra-viveka.tantra` are superseded.
Unit composition is a **mantra** — a krama chain in the graph.

```
unit-compose-mantra
  krama: get-dim-a → get-dim-b → dim-op → dim-to-unit
  krama-rhs: unit-a, unit-b, op
  krama-lhs: composed-unit
```

Executable via `execute-chain`. Invertible via `pratipaksha`.
The composition IS a first-class graph operation, not a script.

Similarly `unit-of-concept` (currently matra-viveka) becomes a mantra node
when graph-walk krama steps are supported. Until then: `unit-of-concept.tantra`.

## New Tantras and Mantra Nodes Required

### P8-B: `emit-triples.tantra`
Chain of thought: given the sense of a word and the current graph state, decide
what triples to emit. This is the reasoning layer — it reads the word's role,
checks context, and returns the right triples for the satya or mithya layer.

Called from `build-question-graph`. Replaces the inline cond block.

```
tantra emit-triples
  inputs
    word   string
    sense  list    -- [node, role, layer, num-val, unit-node]
    g      list    -- current graph (for context)
  ...
  return
    triples  list
done
```

### P8-A: `build-question-graph.tantra`
Chain of thought over sentence words. Calls `lookup-word` for word resolution,
`emit-triples` for deciding what to assert. Context = partial graph accumulated so far.
Replaces: `tokenise-question`, `classify-word`, `resolve-compounds`, `decompose-question`,
          `anuvada-ganana` migration tantra (OCaml pipeline).

Reads as three sentences:
```
words  = split sentence
graph  = reduce words [] (fn g word ->
  sense   = lookup-word word
  triples = emit-triples word sense g
  append g triples
)
```

`substr` OCaml primitive (3-arg) required by `lookup-word.tantra` — ✅ done.

```
tantra build-question-graph
  inputs
    sentence  string
  let
    words = split sentence " "
    graph = reduce words [] (fn g word ->
      let node    = lookup-word word   -- morpheme-inverting, see P8-G
      let role    = cond (exists node) (shabda node "role") otherwise ""
      let layer   = cond (exists node) (node-layer node) otherwise ""
      let parts   = split-numeric word
      let num-str = nth parts 0
      let unit-str = nth parts 1
      -- emit triples into satya or mithya layer based on role/layer/context
      ...
    )
  return
    graph  list  -- satya + mithya layers as triples
done
```

### P8-C: `avrti-refine.tantra` ← next
One refinement pass over the question graph. Resolves patterns requiring full-graph
context — things the single-pass linear reduce cannot handle.

Applied as `fixpoint graph avrti-refine` until the graph stabilises.

**Refinement rules (ordered by priority):**

| Pass | Pattern | Action |
|---|---|---|
| 2 | `[w, mithya]` immediately before `[c, active, concept]` | try `lookup "w-c"` → if hit replace both with `[compound, active, concept]` |
| 3 | `[c, active, concept]` + unresolved unit string (mithya) | try unit match against c's expected unit (future) |
| N | any remaining mithya adjacent to satya with high context pressure | collapse mithya → satya (future) |

**Example (compound resolution):**
```
before: [[kinetic, mithya, kinetic], [energy, active, concept]]
after:  [[kinetic-energy, active, concept]]
```

`fixpoint` terminates when no new triples change — naturally stable after O(sentence-length) passes.

OCaml: `fixpoint` and `iterate` primitives added to `yantra_ops.ml`. ✅ done.

### P8-D: `match-mantra.tantra`
Given question graph → find mantra node whose krama-rhs nodes are
all bound in the satya layer. Returns mantra + bindings map.
Walks `all-edges` filtered by layer=mantra + has krama-rhs.
Replaces: `match-formula.tantra` from old composition-pipeline.md,
          `chain_resolve` BFS in `yantra_resolver.ml` (P8.5).

### P8-D2: `narrate-response.tantra`
Takes understanding-trace + match-trace + execution-trace.
Produces natural language response showing all three layers.
Every answer goes through this — no bare values, no bare proofs.
Vocabulary comes from `to-english` on graph nodes, not hardcoded strings.

### P8-E: `unit-compose-mantra` (graph node, not tantra) ✅ implementable now
Mantra node for unit composition via dim-op.
Krama chain: `dim-vector` × 2 → `dim-op` → `dim-to-unit`.
All backed by existing OCaml primitives reachable via `apply-op`.
Replaces: `matra-ganana.tantra`.
Location: `brahman/kosha/yantra/` or `brahman/kosha/physics/`.

### P8-F: `unit-of-concept.tantra` (tantra for now, mantra later)
Derives the unit for a concept node by walking graph edges.
Replaces: `matra-viveka.tantra`.
Becomes `unit-of-concept-mantra` when graph-walk krama steps supported.

### P8-G: `lookup-word.tantra` + `try-morpheme-rules.tantra` ✅ done

`lookup-word.tantra` — 2-step graph-native lookup:
  1. direct `word-node` hit (exact match + abbreviations)
  2. `try-morpheme-rules` — walks `walk-in "vachana-bahu" "sthita"` from the graph,
     reads `suffix`/`stem-suffix` shabda from each rule, applies inverse, returns hit
  3. miss → `_none`

`try-morpheme-rules.tantra` — fully graph-driven morpheme inversion.
No hardcoded suffix list. New morpheme `.om` files are picked up automatically.

`lookup-word-mantra` (future) — krama chain version once `execute-chain` has short-circuit.

### New `anuvada-ganana.tantra` (replaces migration version)
Top-level orchestrator. Drops in as direct replacement — OCaml `run_anuvada_ganana`
looks up the tantra named `"anuvada-ganana"` automatically.

```
tantra anuvada-ganana
  inputs
    sentence  string
  let
    graph0   = build-question-graph sentence    -- pass 1: linear word scan
    graph    = fixpoint graph0 avrti-refine     -- passes 2+: compound + unit resolution
    match    = match-mantra graph
    result   = cond (exists match)
                 (execute-chain (nth match 0) (nth match 1))
               otherwise _none
    response = narrate-response graph match result
  return
    response  string
done
```

The fixpoint loop is the avrti spiral:
- pass 1 (`build-question-graph`): rough graph, mithya words held as seeds
- pass 2+ (`avrti-refine`): compound resolution, mithya→satya where context pressure resolves
- terminates when graph stops changing (structural equality)

## Natural Language Tantra Design (P8-NL)

Tantras are written IN the graph's own vocabulary. Graph node names are verbs.
Connectives (`and`, `of`, `in`, `for`, `with`) are grammar nodes. The meaning
lives in the nodes — not in the parser.

**Target form — `lookup-word.tantra`:** ✅ done
```
tantra lookup-word
  inputs
    word  string

  let
    direct = word-node word
    result = cond (exists direct) direct
             otherwise (try-morpheme-rules word)

  return result
done
```

`try X and try Y` form is NOT needed — `lookup-word` is now just two branches.
The old strip chain (`try-strip-s`, `try-strip-es`, `try-strip-ies`) is replaced by
`try-morpheme-rules` which walks the graph to find all bahu-vachana rules automatically.

**Target form — `build-question-graph.tantra`:**
```
tantra build-question-graph
  inputs
    sentence  string

  split sentence into words
  for each word lookup and get role and find context
  emit triples and build graph

  return graph
done
```

Each sub-operation (`try-morpheme-rules`, `emit-triples`, `find-context`)
is a standalone graph node — a mantra or tantra — that holds its own logic.
Most computation lives in the graph, not in parser rules.

### Sentence forms needed (smallest to largest)

| Form | Sugar for | Needed by | Status |
|---|---|---|---|
| `split X into Y` | `Y = split X " "` | `build-question-graph` | partial (scoping bug) |
| `for each X in Y A and B and C` | `reduce Y [] (fn g x -> A x; B x; C x)` | `build-question-graph` | pending |

`try X and try Y` is dropped — `lookup-word` no longer needs it.
`and` is the key composition operator inside `for each` bodies.

### Standalone sub-tantra nodes ✅ done

```
tantra try-morpheme-rules  -- walk bahu-vachana rules from graph → node or _none  ✅
tantra find-context        -- active-concept and pending-number from graph         ✅
tantra emit-triples        -- given word + sense + context → triples               ✅
```

These exist as graph vocabulary. `lookup-word` and `build-question-graph` call them
by name.

## Parser + Eval Modularization (P8-M)

Current state is monolithic. Given the natural language tantra direction, the parser
needs a `sentence_parser` module for new sentence forms. Split now so additions
are clean.

### Parser split

```
yantra_parser.ml (441 lines) → split into:

  yantra_tokeniser.ml      -- tokenise_expr only (~30 lines)
  yantra_arity.ml          -- arity tables, register_*, pre_scan (~60 lines)
  yantra_expr_parser.ml    -- parse_expr, parse_cond (current forms) (~200 lines)
  yantra_sentence_parser.ml-- NEW: try/and, for-each, split-into forms (~0 now, grows)
  yantra_tantra_file.ml    -- parse_let_block, parse_tantra_file (~150 lines)
```

### Eval split

```
yantra_eval_primitives.ml (884 lines) → split into:

  yantra_eval_graph.ml     -- eval_graph_op: graph/field/context ops (~400 lines)
  yantra_eval_call.ml      -- eval_call dispatch + tantra-by-name fallback (~100 lines)
  yantra_ops.ml            -- pure math/string/list ops (already separate, fine)
```

```
yantra_pipeline_ops.ml (604 lines) → DELETE after tantras replace pipeline:
  match-mantra.tantra replaces chain_resolve BFS
  build-question-graph.tantra replaces classify pipeline
```

### Order

1. ✅ Split `yantra_parser.ml` — created `yantra_sentence_parser.ml`
2. ✅ Write standalone sub-tantras — `try-morpheme-rules`, `find-context`, `emit-triples`
   - `try-strip-s/es/ies` replaced by graph-walk `try-morpheme-rules`
   - `ends-with` primitive added (OCaml + op node)
3. ✅ Rewrite `lookup-word.tantra` — graph-native: direct hit + try-morpheme-rules
4. ✅ `split X into Y` — implemented in `yantra_sentence_parser.ml` (scoping bug to fix)
5. → Implement `for each X in Y A and B and C` sentence form
6. → Fix `split X into Y` scoping bug
7. → Rewrite `build-question-graph.tantra` in natural form
8. Split eval modules
9. Delete `yantra_pipeline_ops.ml` once covered by tantras

## OCaml Primitives Required

### ✅ `substr` — string × start × length → string
Used by `try-morpheme-rules.tantra` for suffix stripping in morpheme inversion.

### ✅ `ends-with` — string × suffix → bool
Used by `try-morpheme-rules.tantra` to check if word ends with a morpheme's suffix.
Added to `yantra_ops.ml` + `brahman/kosha/yantra/op-ends-with.om`.

### Already exists (P8-E): `dim-vector`, `dim-op`, `dim-to-unit`
These back `unit-compose-mantra` krama steps via `apply-op`. No new OCaml needed.

## OCaml Code to Remove (P8.5 — after tantras working)

| Target | Lines | Replacement |
|---|---|---|
| `build_word_index` — `name:` registration block | ~15 | `lookup` primitive handles concept nodes directly |
| `build_word_index` — kosha auto-index block | ~10 | `lookup` primitive handles concept nodes directly |
| `yantra_resolver.ml` — `chain_resolve` BFS | ~300 | `match-mantra.tantra` |
| `yantra_inverter.ml` — `invert_chain` | ~200 | mantra `pratipaksha` walk (future) |
| `setu_classify.ml` — `classify_token` | 144 | `build-question-graph.tantra` |
| `classify_via_tantra` + `extract_bindings` in `yantra.ml` | ~80 | `build-question-graph.tantra` |
| `run_anuvada_ganana` pipeline fallback in `yantra.ml` | ~120 | new `anuvada-ganana.tantra` |

After removing `name:` and kosha auto-index from `build_word_index`, the function
becomes word:-keys-only. `word-node` is then purely an abbreviation lookup.
Concept resolution goes through `lookup` (graph-native, always correct).

Gate: 49/52 regression throughout.

## Question Graph Structure

The question graph is a set of triples `(node, edge, node)` plus:
- `solve-for`: the unknown node
- `bindings`: map from concept-node → value

It lives in tantra-space as a list of lists (no `emit-node` calls).
It is NOT persisted into the knowledge graph — it is ephemeral.

```
question-graph structure:
  [
    ["solve-for", "intent", "kinetic-energy"],
    ["mass",      "value",  "5.0"],
    ["mass",      "unit",   "kilogram"],
    ["velocity",  "value",  "10.0"],
    ["velocity",  "unit",   "metre-per-second"],
  ]
```

This is a flat list of triples. The `match-mantra.tantra` walks this
to find which mantra node's krama-rhs are all bound.

## Execution Flow (Full)

```
sentence: "what is the kinetic energy of a 5kg ball moving at 10m/s"

build-question-graph (pass 1 — linear scan):
  "what"    → intent: [what, intent, solve-for]
  "is"      → grammar: []
  "the"     → grammar: []
  "kinetic" → miss: [kinetic, mithya, kinetic]
  "energy"  → kosha concept: [energy, active, concept]
  "of"      → grammar: []
  "a"       → grammar: []
  "5kg"     → value+unit: [energy, value, 5.0], [energy, unit, kilogram]
  "ball"    → miss: [ball, mithya, ball]
  "moving"  → miss: [moving, mithya, moving]
  "at"      → grammar: []
  "10m/s"   → number+unknown-unit: [10m/s, pending-number, 10.0]

avrti-refine (pass 2 — compound resolution):
  sees [kinetic, mithya] before [energy, active]
  → lookup "kinetic-energy" → HIT (kosha node)
  → replace both with [kinetic-energy, active, concept]
  graph now: [what, intent, solve-for]
             [kinetic-energy, active, concept]
             [kinetic-energy, value, 5.0], [kinetic-energy, unit, kilogram]
             [ball, mithya, ball], [moving, mithya, moving]

avrti-refine (pass 3 — no new compounds, graph stable → fixpoint done)

match-mantra:
  bound = [kinetic-energy]  ← but kinetic-energy-mantra needs mass + velocity → no match
  (this sentence doesn't bind mass/velocity individually — needs better unit parsing)
```

---

```
sentence: "calculate velocity given momentum 50kgm/s and mass 2kg"

build-question-graph:
  "calculate"  → intent: solve-for (unknown)
  "velocity"   → concept node: velocity → solve-for target
  "given"      → grammar: marks what follows as known
  "momentum"   → concept node: momentum → active, unfilled
  "50"         → number: 50.0 → pending-number
  "kgm/s"      → unknown-short, prev=number, active=momentum
                  context: momentum.unit = kilogram-metre-per-second (via unit-of-concept)
                  dim-check: kgm/s ~ kilogram-metre-per-second? → YES
                  → bind: momentum = 50.0 kilogram-metre-per-second
  "and"        → grammar: parallel slot
  "mass"       → concept node: mass → active, unfilled
  "2kg"        → value-unit: 2.0 kilogram
                  word-node "kg" → kilogram (direct hit)
                  → bind: mass = 2.0 kilogram

question-graph:
  solve-for: velocity
  momentum: 50.0 kilogram-metre-per-second
  mass: 2.0 kilogram

match-mantra:
  velocity-mantra: krama-rhs = [momentum, mass] → both bound → MATCH

execute-chain:
  velocity = momentum / mass = 50.0 / 2.0 = 25.0 metre-per-second

narrate-response (ALL three layers, always):
  [understanding]
    "I understood: find velocity
     given momentum = 50.0 kg·m/s (matched kgm/s to kilogram-metre-per-second,
     which is the unit of momentum)
     and mass = 2.0 kg"

  [matching]
    "velocity = momentum / mass
     (velocity-mantra: krama-rhs covers momentum and mass — both present)"

  [execution]
    "velocity = 50.0 / 2.0
              = 25.0 metre-per-second"
```

The response IS the reasoning. The final value is the last line of the trace,
not a standalone answer.

## Relationship to Existing Plans

- Supersedes `composition-pipeline.md` P8 tantras — graph-native approach replaces pipeline
- Supersedes `engine-tantra-migration.md` P7/P8 (tokenise-question, decompose-question)
- Supersedes `anuvada-ganana` migration tantra — new `anuvada-ganana.tantra` replaces it
- Extends `mantra-nodes.md` — mantras are now partial query templates
- `session-graph.md` builds on top of this — session = accumulated question graphs
- `execute-chain` and `match-mantra` stay; `decompose-question` absorbed into `build-question-graph`

## What is NOT Changed

- `execute-chain` primitive — still the execution engine
- Mantra node structure (`krama`, `krama-lhs`, `krama-rhs`, `implication-sthita`)
- `dim-vector`, `dim-op`, `dim-to-unit` primitives
- `lookup` primitive (`Proof_graph.find`) — the correct primary path for concept nodes
- `word-node` and word_index — retained but now abbreviation-only (word: keys)
- Regression baseline: 49/52

## Resolved Design Decisions

1. **No sub-tantras for classify/context**: one `build-question-graph.tantra`,
   inline reduce. No `extend-graph.tantra`, no `context-of.tantra`.
   The partial graph IS the context at each step.

2. **Unit composition via mantra node, not tantra call**: `matra-ganana.tantra`
   is replaced by `unit-compose-mantra` krama node, called via `execute-chain`.
   `matra-viveka.tantra` replaced by `unit-of-concept.tantra` (mantra when stack
   machine supports graph-walk krama steps).

3. **Unknowns are mithya (provisional) and avidya (not-yet-known)**:
   not discarded, not blindly included. Context pressure during reduction
   collapses mithya → satya. Mantra matching only on satya layer.
   Mithya layer available for dialogue generation and future resolution.

4. **Unresolved unit strings stay in mithya layer**: held as `unresolved-unit`
   triple. Mantra match proceeds from concept bindings alone.
   Dialogue generation can ask user to confirm unit.

5. **Context depth = full partial graph**: recency weighting by position,
   not a window. The whole accumulated graph is the context.

6. **`lookup-word` is both a tantra and a mantra**: tantra is the current
   implementation (uses `cond`/`exists` branching + `substr`). Mantra is the
   declared graph structure (krama chain). Both coexist — the tantra backs
   the mantra steps. When stack machine gains short-circuit support, the tantra
   becomes purely internal to the mantra execution.

7. **`concepts-for-unit` removed**: superseded by `word:` keys on unit nodes
   and `unit-of-concept.tantra` walking the graph. No active OCaml consumer.
   Removed from `matra-beeja.shabda`. ✅ done.

8. **Session state deferred**: `session-graph.md` multi-turn state not in this
   phase. `anuvada-ganana.tantra` is stateless — each call is independent.
   Session bindings via existing `session-bindings`/`remember-bindings` primitives
   added in a later phase.

9. **`lookup` before `word-node` in `lookup-word.tantra`**: `lookup word` hits
   `Proof_graph.find` directly — always returns the kosha concept node if one exists
   by that name. `word-node` (word_index) is only consulted as fallback for
   abbreviations (kg, N, m) that have no corresponding graph node by that name.
   `build_word_index` is simplified to word:-keys-only — the `name:` registration
   and kosha auto-index blocks are removed as they are made redundant by `lookup`.
