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

### lookup-word is a mantra, not a tantra

`lookup-word` is a **mantra node** — a krama chain executed by `execute-chain`.
The graph itself does the lookup. No tantra procedural code needed.

```
lookup-word-mantra
  krama: try-direct → try-strip-s → try-strip-es → try-strip-ies → miss
  krama-rhs: word (string)
  krama-lhs: resolved-node
```

Each krama step is a graph op: strip suffix from string, call word-node, short-circuit if found.
The morpheme nodes are the operands — the mantra walks them in order.
`build-question-graph` calls `execute-chain` on this mantra for each word in the reduce.

**Current phasing**: `execute-chain`'s stack machine runs ordered krama steps but does
not yet short-circuit on a non-miss result. Until short-circuit support exists,
`lookup-word` is backed by a **`lookup-word.tantra`** that implements the same 4-step
strategy using tantra `cond`/`exists` branching. `build-question-graph` calls
`lookup-word` (the tantra) directly. When the stack machine gains short-circuit support,
`lookup-word.tantra` becomes the backing for `lookup-word-mantra` krama steps and
`build-question-graph` calls `execute-chain "lookup-word-mantra"` instead.

Lookup strategy:
1. **Direct hit** — `word-node word` → found → done
2. **Strip `s`** → retry (metres → metre, kilograms → kilogram)
3. **Strip `es`** → retry (masses → mass)
4. **Strip `ies`, add `y`** → retry (velocities → velocity, frequencies → frequency)
5. **Irregular** — node has explicit `plural-form:` key listing surface variants
6. **Miss** → mithya layer

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

### P8-G: `lookup-word.tantra` + `lookup-word-mantra` (graph node)
`lookup-word.tantra` — 4-step morpheme-inverting lookup using `substr` primitive:
  1. direct word-node hit
  2. strip trailing `s` → retry
  3. strip trailing `es` → retry
  4. strip trailing `ies`, add `y` → retry
  5. miss → `_none`

`lookup-word-mantra` — declares the same strategy as a krama chain in the graph.
Currently backed by `lookup-word.tantra` steps. Future: native stack machine execution.

### New `anuvada-ganana.tantra` (replaces migration version)
Top-level orchestrator. Drops in as direct replacement — OCaml `run_anuvada_ganana`
looks up the tantra named `"anuvada-ganana"` automatically.

```
tantra anuvada-ganana
  inputs
    sentence  string
  let
    graph    = build-question-graph sentence
    match    = match-mantra graph
    result   = cond (exists match)
                 (execute-chain (nth match 0) (nth match 1))
               otherwise _none
    response = narrate-response graph match result
  return
    response  string
done
```

## Natural Language Tantra Design (P8-NL)

Tantras are written IN the graph's own vocabulary. Graph node names are verbs.
Connectives (`and`, `of`, `in`, `for`, `with`) are grammar nodes. The meaning
lives in the nodes — not in the parser.

**Target form — `lookup-word.tantra`:**
```
tantra lookup-word
  inputs
    word  string

  try direct and try strip-s and try strip-es and try strip-ies
  return node
done
```

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

Each sub-operation (`try-direct`, `try-strip-s`, `emit-triples`, `find-context`)
is a standalone graph node — a mantra or tantra — that holds its own logic.
Most computation lives in the graph, not in parser rules.

### Sentence forms needed (smallest to largest)

| Form | Sugar for | Needed by |
|---|---|---|
| `try X and try Y and try Z` | `cond (exists X) X (cond (exists Y) Y ...)` | `lookup-word` |
| `split X into Y` | `Y = split X " "` | `build-question-graph` |
| `for each X in Y ... and ...` | `reduce Y [] (fn g x -> ...)` | `build-question-graph` |

### Standalone sub-tantra nodes (no parser change needed)

Before adding sentence forms, extract the sub-operations as named tantras.
Each is a tiny, focused chain of thought:

```
tantra try-direct      -- word-node word → node or _none
tantra try-strip-s     -- word-node (substr word 0 (len-1)) → node or _none
tantra try-strip-es    -- word-node (substr word 0 (len-2)) → node or _none
tantra try-strip-ies   -- word-node (concat (substr word 0 (len-3)) "y") → node or _none
tantra find-context    -- active-concept and pending-number from graph
tantra emit-triples    -- given word + sense + context → triples
```

These exist as graph vocabulary. `lookup-word` and `build-question-graph` call them
by name. The `try X and try Y` parser form is layered on top once these exist.

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

1. Split `yantra_parser.ml` — creates `yantra_sentence_parser.ml` (empty stub)
2. Add `try X and try Y` to `yantra_sentence_parser.ml`
3. Write standalone sub-tantras (`try-direct`, `try-strip-s`, etc.)
4. Rewrite `lookup-word.tantra` in natural form
5. Add `split X into Y` and `for each X in Y`
6. Rewrite `build-question-graph.tantra` in natural form
7. Split eval modules
8. Delete `yantra_pipeline_ops.ml` once covered by tantras

## OCaml Primitives Required

### New (P8-A): `substr`
```ocaml
| "substr" -> string × start × length → string
```
Needed by `lookup-word.tantra` for suffix stripping.
3-line addition to `yantra_ops.ml`. Register arity 3 in `yantra_eval.ml`.

### Already exists (P8-E): `dim-vector`, `dim-op`, `dim-to-unit`
These back `unit-compose-mantra` krama steps via `apply-op`. No new OCaml needed.

## OCaml Code to Remove (P8.5 — after tantras working)

| Target | Lines | Replacement |
|---|---|---|
| `yantra_resolver.ml` — `chain_resolve` BFS | ~300 | `match-mantra.tantra` |
| `yantra_inverter.ml` — `invert_chain` | ~200 | mantra `pratipaksha` walk (future) |
| `setu_classify.ml` — `classify_token` | 144 | `build-question-graph.tantra` |
| `classify_via_tantra` + `extract_bindings` in `yantra.ml` | ~80 | `build-question-graph.tantra` |
| `run_anuvada_ganana` pipeline fallback in `yantra.ml` | ~120 | new `anuvada-ganana.tantra` |

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
- `word-node` and word_index for base unit lookup
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
