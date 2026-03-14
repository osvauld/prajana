# Session Graph — Persistent State, Formal Proof, Dialogue

**Status**: Architecture complete. Steps 1–3 done. Step 4+ pending.
**Last updated**: 2026-03-14

---

## The Fundamental Cycle

**Expansion → Connection → Compression = sphoTa.**

This is the architectural principle everything follows from. Not three separate steps — one movement with three phases:

- **Expansion**: the English sentence unfolds. `build-question-graph` produces structural triples. `artha-viveka` dissolves the dhvani (surface form). Words become nodes, relationships become typed edges.
- **Connection**: the expanded graph connects to the kosha. `satya` edges reach physics concept nodes. `implication` edges from the kosha mantras attach to the solve-for target. `formalize-question` asserts logic type edges (`axiom`, `proposition`, `implication`, `proof`) via `vishesa` to the existing `brahman/kosha/math/logic/` nodes. The session's `parampara` edges connect this question to prior questions.
- **Compression**: everything that can be resolved collapses. `avrti-refine` runs to fixpoint. `mithya` resolves to `satya`. The graph reaches its minimal, internally consistent, dhvani-free form.

The result of this full movement is **sphoTa** — `artha-swarupa dhvani-rahita vakya-yukta` — the whole meaning, surface-free, arrived whole. Not assembled from parts. The triple graph IS sphoTa made traversable.

The cycle is reversible:
- From sphoTa: **expand** → walk bhasha nodes → `anuvada` → English answer (disposable surface)
- From sphoTa: **compute** → walk krama chain → substitution → numeric result (cached as edge, not separate)
- From sphoTa: **connect forward** → `parampara` edge → next question's expansion begins from this condensed state

---

## sphoTa as Canonical Form

The Sanskrit inner graph IS the answer. In condensed form. Already.

"what is kinetic energy of a 5kg ball at 10m/s?" condenses to:

```
[mass-rashi,     sankhya,   5.]
[mass-rashi,     matra,     kilogram]
[mass-rashi,     vishesa,   axiom]          ← user-stated = self-grounding axiom
[velocity-rashi, sankhya,   10.]
[velocity-rashi, matra,     metre-per-second]
[velocity-rashi, vishesa,   axiom]
[kinetic-energy, vishesa,   proposition]    ← solve-for = open proposition
[ke-mantra,      vishesa,   implication]    ← mantra IS the implication A→B
[ball-A,         prathama-vibhakti, object]
[prashna-1,      vishesa,   tarka-dvaara]   ← passed through the logic gate
[prashna-1,      vishesa,   sphoTa]         ← this graph IS sphoTa
```

Walking from `kinetic-energy` through `ke-mantra`'s krama chain with the bound axiom values gives 250J. The answer is latent in the structure. The computation is a graph walk.

The English "kinetic energy is 250 joules" is `anuvada` — carrying the artha (already fully present in the graph) across into English dhvani for the user. The English is disposable after delivery. The graph remains. The next question connects to the graph, not to the English.

The numeric result is cached as a new edge on the same graph node — not separate state:
```
[ke-result, sankhya,  250.]
[ke-result, matra,    joule]
[ke-result, vishesa,  theorem]              ← the computed result IS a theorem
[ke-result, niyama-siddha, prashna-1-proof] ← established by this proof
```

The cache is just another edge. Visiting `ke-result` again: cache hit, no recomputation.

---

## The Question as Logical Assertion

The structural triple graph from `build-question-graph` is the raw form.
`formalize-question` makes it a **logical object** by asserting type edges to the existing logic nodes.

All logic nodes are already in `brahman/kosha/math/logic/`:
- `axiom` — `niralamba-yukta svayambhu-yukta` — self-grounding, no proof needed
- `proposition` — `satya-yukta viveka-yuktu` — truth-valued, open to discrimination
- `theorem` — `niyama-siddha` — established by proof from axioms
- `proof` — `krama-yukta theorem-phala` — ordered chain, produces theorem
- `inference` — `kramanusara-yukta` — follows from premises in order
- `modus-ponens` — `implication-janya` — if A and A→B then B
- `substitution` — replace variable with known value
- `inversion` — rearrange formula to solve for a different variable
- `implication` — `sambandha-yukta krama-yuktu` — A→B, directional
- `tarka-dvaara` — `rachana-swarupa shuddhi-kriya sphoTa-yuktu nyaya-abheda` — the logic gate

`formalize-question` is a **mantra** (declarative formula, not imperative tantra) because the mapping is fixed:

```
sankhya/matra binding    → [node, vishesa, axiom]
vidhi-kaala triple       → [target, vishesa, proposition]    (open slot)
matched kosha mantra     → [mantra, vishesa, implication]
proof node               → [proof-node, vishesa, proof]
                           [proof-node, vishesa, modus-ponens]
the question itself      → [prashna-N, vishesa, tarka-dvaara]
                           [prashna-N, vishesa, sphoTa]
```

All using the standard `vishesa` IS-A edge — the same pattern as `[v1, vishesa, rashi]`.

For a **compute question**: axioms + implication → modus-ponens → substitution → theorem (number).
For a **theoretical question**: no axioms → proposition only → implication-walk → modus-ponens chain → theorem (derivation).
For an **inverse question** (find mass given KE and velocity): axioms + inversion → theorem (rearranged formula).

The session across turns is a **growing proof document**: axioms accumulate, theorems reference prior theorems, the full conversation is a formal derivation.

---

## The Session as Parampara Chain

### The Question IS a chala-apeksha

`chala-apeksha`: `krama-sthita kramanusara-yukta parampara-sthita` — a moving reference frame.
The question is the denominator of all derivatives in this turn. Everything is measured wrt it.

The first question is `sthira-apeksha` — the fixed domain anchor, the base joint in the kinematic chain. Every subsequent question is `chala-apeksha` — its own frame moves relative to the parampara.

`kramanusara` wrt a `chala-apeksha` = total derivative (includes transport term). In session terms: the transport term is the carry-over of context from the previous frame — the entities, bindings, established theorems that "travel with" the question as it moves. This is why context propagates between turns: the question-frame carries its own velocity.

### The Collapse

The question goes through three states within a single turn:

1. **Vartamana** (present) — the question has just arrived. It is alive, unresolved. Expansion begins.
2. **Answered** — the proof completes. The answer is established as a theorem. The question has acted.
3. **Bhuta-kaala** — the act of answering itself collapses the question into the past. `bhuta-kaala: purva-avastha-sthita samskaara-yukta`. This happens inside the turn, after execute-chain returns, before the response is sent. The question does not wait for the next question to become past — answering makes it past.

After collapse, the answered question becomes **parampara** for the next:
`parampara: avrti-swarupa pramana-kriya samskaara-phala` — tradition as spiral. The answered question IS the ground the next question stands on. Its samskaara (imprint) — the axioms, theorems, entities established — become the inherited context.

### Session Graph Triples

**Turn spine (temporal structure):**
```
[prashna-1, krama,                    prashna-2]   ← sequence: prashna-1 grounds prashna-2
[prashna-1, bhuta-kaala,              prashna-1]   ← on answering: prashna-1 is now past
[prashna-1, samskaara,                s1]          ← imprint: what it established
[prashna-2, parampara,                prashna-1]   ← prashna-2 stands on prashna-1
[prashna-2, chala-apeksha-swarupa,    chala-apeksha] ← prashna-2 is a moving frame
[prashna-1, sthira-apeksha-swarupa,   sthira-apeksha] ← prashna-1 was the anchor
```

**Samskaara (what the answered question left):**
```
[s1, sankhya-kinetic-energy, 250.]
[s1, matra-kinetic-energy,   joule]
[s1, prathama-vibhakti,      ball-A]
[s1, vishesa,                theorem]
```

**Avastha transitions (when something changes between questions):**
```
-- turn 2: "what if velocity doubles?"
[velocity, avastha-purva,   10.]           ← what it was (from parampara)
[velocity, avastha-uttara,  20.]           ← what it became (in vartamana)
[velocity, kramanusara,     prashna-2]     ← changed wrt this question-frame
[mass,     sthira-apeksha-swarupa, prashna-2] ← mass held constant (sthira)
```

The detected delta IS a partial derivative of the session state wrt the question-frame:
`∂(session-state)/∂(prashna-N)` — all others held constant (sthira-apeksha), one variable
changed (chala-apeksha). `partial-derivative: chala-apeksha-siddha sthira-apeksha-yukta` —
already describes this exactly.

### No New Sangati Nodes Required

Everything needed is already in the sangati/kosha:

| Concept | Sangati/kosha node | Meaning in session |
|---|---|---|
| Question as moving frame | `chala-apeksha` | The question IS the derivative denominator |
| First question as anchor | `sthira-apeksha` | Domain establishment, fixed frame |
| Sequence ordering | `krama` | Each step grounds the next |
| State transition | `avastha` | `purva-avastha-janya uttara-avastha-phala` |
| Derivative wrt question | `kramanusara` | What changed in this frame |
| Past question | `bhuta-kaala` | Answered question enters the past (on answering) |
| Lineage/ground | `parampara` | Answered question becomes tradition |
| Answer imprint | `samskaara` | The mark that seeds the next turn |
| Property inheritance | `dharma-anvaya` | Properties run through the lineage |
| User-stated fact | `axiom` | `niralamba-yukta`: self-grounding |
| Open slot | `proposition` | `viveka-yuktu`: subject to discrimination |
| Physics mantra | `implication` | A→B: inputs → output |
| Execution trace | `proof` | `krama-yukta theorem-phala` |
| Inference rule | `modus-ponens` | If A and A→B then B |
| Numeric solve | `substitution` | Replace variable with known value |
| Inverse solve | `inversion` | Rearrange formula |
| Logic gate | `tarka-dvaara` | The door that reason opens |
| Canonical inner form | `sphoTa` | The whole meaning, dhvani-free |
| English output | `anuvada` | Carrying artha across into dhvani |

---

## Abstract Math Operations as Active Participants

These are not documentation — they are structural types asserted on session graph nodes.
Each one makes the session graph machine-walkable for that operation.

### kramanusara (partial derivative)
`build-session-graph` detects avastha transitions by comparing new triples against the session graph. This IS `partial-derivative` applied to session state wrt the question-frame. Assert `[transition-node, vishesa, partial-derivative]` on each detected change. The narration can then walk this edge and say "the partial derivative of velocity wrt prashna-2 is 10 m/s (from 10 to 20)."

### filtration
The session graph across turns IS a filtration: `ascending-chain-of-substructures-each-contained-in-the-next-imposing-a-depth-grading`. Each turn's additions form one layer. `session-at-turn-N` = filter by `krama-depth ≤ N`. The session graph naturally supports "what was the state at turn 2?" by walking the krama chain. Assert `[session-id, vishesa, filtration]`.

### fixed-point
`avrti-refine` already reaches fixed-point per question. Across turns: when the new question graph is entirely contained within the session graph (no new triples, only queries over existing ones), the session is at a fixed-point of comprehension — `sphoTa` at the session level. Assert `[session-id, vishesa, fixed-point]` when this condition is detected.

### morphism / composition
The pipeline IS a morphism chain: each tantra is a structure-preserving map from one triple-list to another. `composition: parampara-swarupa` — the composition IS the parampara of the pipeline. Assert `[pipeline-step, vishesa, morphism]` on each step node. The narration can walk the composition chain to describe reasoning.

### equivalence-relation
Entity coreference across turns. "the ball" in question 3 refers to `ball-A` from question 1. This IS an equivalence relation over session entity references. Assert `[ball, equivalence-relation-sthita, ball-A]` when detected. The narration can say "by equivalence with ball-A established at prashna-1."

### antiderivative (integration)
The session graph is the antiderivative of all the questions — the gathering of all tat-kshana (instants) into wholeness. `parampara-swarupa: the-gathering-of-all-tat-kshana-into-wholeness`. "Summarise what we've established" = integrate over the session graph: walk the krama chain, collect all theorem nodes. Assert `[session-summary, vishesa, antiderivative]`.

---

## Two Kinds of Questions

The same graph machinery handles both. The difference is in what the proof walk produces.

### Compute Question
"what is kinetic energy of a 5kg ball at 10m/s?"

Graph has: axioms (sankhya/matra bindings) + open proposition (solve-for quantity).
Path: axioms satisfy mantra krama-rhs → modus-ponens → substitution → theorem (number).
Narration: "axioms: mass=5kg, velocity=10m/s. By ke-mantra (implication). By modus-ponens and substitution: KE = ½×5×100 = 250J. Theorem: KE = 250J."

### Theoretical Question
"why does kinetic energy depend on velocity squared?"

Graph has: open proposition (a relationship, not a quantity) + no axioms (or irrelevant).
Path: implication-walk from kinetic-energy → work-energy-theorem → newton-second-law → integration → modus-ponens at each step.
Narration: proof chain, each step an implication application.

### Mixed Question
"given mass 5kg and v=10m/s, show why kinetic energy is 250J"
Path: compute (substitution) AND theoretical (implication-walk). Both paths, narrated together.

### Detection (from formalize-question output)
- Has `axiom` nodes + `proposition` with matching mantra → compute
- Has `proposition` only (no matching axioms) → theoretical
- Has both + "why"/"show"/"prove" intent marker → mixed

---

## The Pipeline

`build-session-graph` is the outer tantra. It owns the full turn. It calls `build-question-graph` internally, measuring the new question wrt the previous session state.

```
sentence + session-graph
    ↓
build-session-graph (tantra — outer orchestrator)
    ├── build-question-graph sentence        (tantra — existing, structural triples)
    ├── formalize-question triples           (mantra — logic type edges)
    ├── detect-avastha-transitions           (from/where/collect over session-graph)
    ├── assert krama/parampara/bhuta-kaala   (session-krama-mantra)
    └── merge all layers → extended session-graph
    ↓
avrti-refine / fixpoint                     (tantra — existing, reaches sphoTa)
    ↓
match-mantra                                (tantra — existing, implication identified)
    ↓
execute-chain (compute) / implication-walk (theoretical)
    ↓
assert-samskaara (mantra)                   (prashna-N → bhuta-kaala, answer → theorem)
    ↓
compose-response (tantra — future P8)       (anuvada: graph → English narration)
```

### Tantra vs Mantra for each component

| Component | Type | Reason |
|---|---|---|
| `build-question-graph` | tantra | control flow, word-by-word reduce |
| `formalize-question` | **mantra** | fixed declarative formula: triple-type → logic vishesa edge |
| `build-session-graph` | tantra | calls other tantras, avastha detection, layer merge |
| `session-krama-mantra` | **mantra** | fixed formula: prev-id + curr-id → spine triples |
| `assert-samskaara` | **mantra** | fixed formula: answer triples → theorem + samskaara edges |
| `match-mantra` | tantra | graph walk with control flow |
| `implication-walk` | tantra | recursive implication chain walk |
| `compose-response` | tantra | bhasha node walk, sentence construction |

### Pipeline ↔ Math operation mapping

| Stage | Math/logic operation | Node |
|---|---|---|
| `build-question-graph` | artha-viveka | `artha-viveka`, `sphoTa` |
| `formalize-question` | tarka-dvaara opening | `tarka-dvaara`, `axiom`, `proposition` |
| `build-session-graph` | partial-derivative, filtration | `partial-derivative`, `filtration`, `chala-apeksha` |
| `avrti-refine` | fixed-point | `fixed-point` |
| `match-mantra` | implication identification | `implication` |
| `execute-chain` | substitution | `substitution` |
| `implication-walk` | modus-ponens chain | `modus-ponens`, `inference` |
| `assert-samskaara` | theorem assertion | `theorem`, `proof`, `karma` |
| `compose-response` | anuvada | `anuvada`, `dhvani` |
| Session spine | parampara + avastha | `parampara`, `avastha`, `kramanusara` |

---

## Session Graph Layers

All four layers are the same graph — different edge types on the same nodes.
Walking any node reaches all layers.

### Layer 1 — Structural (from `build-question-graph`)
```
[mass-rashi,     sankhya,          5.]
[mass-rashi,     matra,            kilogram]
[velocity-rashi, sankhya,          10.]
[ball-A,         prathama-vibhakti, object]
[kinetic-energy, vidhi-kaala,      solve-for]
```

### Layer 2 — Logical (from `formalize-question` — vishesa edges)
```
[mass-rashi,      vishesa, axiom]
[velocity-rashi,  vishesa, axiom]
[kinetic-energy,  vishesa, proposition]
[ke-mantra,       vishesa, implication]
[prashna-1-proof, vishesa, proof]
[prashna-1-proof, vishesa, modus-ponens]
[prashna-1,       vishesa, tarka-dvaara]
[prashna-1,       vishesa, sphoTa]
```

### Layer 3 — Temporal (from `build-session-graph`)
```
[prashna-1, krama,                  prashna-2]
[prashna-1, bhuta-kaala,            prashna-1]
[prashna-1, samskaara,              s1]
[prashna-2, parampara,              prashna-1]
[prashna-2, chala-apeksha-swarupa,  chala-apeksha]
[velocity,  avastha-purva,          10.]
[velocity,  avastha-uttara,         20.]
[velocity,  kramanusara,            prashna-2]
```

### Layer 4 — Computation cache (after execute-chain)
```
[ke-result, sankhya,         250.]
[ke-result, matra,           joule]
[ke-result, vishesa,         theorem]
[ke-result, niyama-siddha,   prashna-1-proof]
[prashna-1, samskaara-phala, ke-result]
```

---

## Socket and Session Store

### In-memory session store (OCaml, `socket.ml`)

```ocaml
type session_entry = {
  mutable se_graph   : (string * string * string) list;  (* accumulated triple layers *)
  mutable se_turn    : int;                              (* turn count *)
  mutable se_turn_id : string;                           (* "prashna-N" *)
  mutable se_yantra  : Yantra.session;                   (* bindings/context_seeds *)
}

let session_store : (string, session_entry) Hashtbl.t = Hashtbl.create 16
```

- Keyed by `session_id` from the JSON request
- Created on first message, reused on all subsequent messages with same `session_id`
- In-memory only — lost on server restart (persistence deferred)
- Explicit `{"command":"end-session","session_id":"..."}` to clear

### Socket protocol additions

**Eval command (for testing):**
```json
{"command": "eval", "expr": "test-avrti-fixpoint"}
→ {"status":"ok","command":"eval","expr":"test-avrti-fixpoint",
   "result":"true","passed":true,"elapsed_ms":14}
```
Terminal: `[eval] test-avrti-fixpoint → true (14ms)`

**Question with session — response gains `"session"` field:**
```json
"session": {
  "turn":      2,
  "prashna_id":"prashna-2",
  "parampara": "prashna-1",
  "avastha":   [{"subj":"velocity","purva":"10.","uttara":"20."}],
  "sthira":    ["mass","ball-A"]
}
```

**Terminal per turn:**
```
[session abc / prashna-2 ← parampara: prashna-1]
  avastha: velocity 10 → 20  (kramanusara wrt prashna-2)
  sthira:  mass=5kg, ball-A
  → kinetic energy is 1000 J (was 250 J — ×4 because KE ∝ v²)
```

---

## Dialogue Generation (later)

When a derivation cannot complete because a slot is unfilled, the system generates the question needed to continue. This is a natural consequence of `formalize-question`: an open `proposition` with no matching `axiom` in the session graph → `generate-question` tantra produces the follow-up.

```
"calculate kinetic energy"
  → proposition: kinetic-energy (open)
  → match-mantra: ke-mantra needs mass AND velocity
  → session has neither → two open slots
  → generate: "what is the mass of the object?"
  → user: "5kg" → [mass, vishesa, axiom] asserted
  → generate: "what is its velocity?"
  → user: "10m/s" → [velocity, vishesa, axiom] asserted
  → all slots filled → execute-chain → theorem: KE = 250J
```

Each generated question IS a question graph with its own proof skeleton — recursive structure. Implementation: P8+.

---

## Implementation Steps

| Step | What | Type | Files | Status |
|---|---|---|---|---|
| 1 | Socket `eval` command | OCaml | `vyakarana/lib/socket.ml` | ✅ done |
| 2 | Python test runner | Python | `vyakarana/scripts/run-tests.py` | ✅ done |
| 3 | Session store (Hashtbl + session_entry) | OCaml | `socket.ml` | ✅ done |
| 4 | Wire active yantra_session through question handler | OCaml | `socket.ml`, `anuvada.ml` | pending — `_active_session` is computed but ignored; `anuvada_query` does not yet take a session param |
| 5 | `build-session-graph` tantra | tantra | `brahman/yantra/pipeline/build-session-graph.tantra` | pending |
| 6 | `formalize-question` mantra node | mantra | `brahman/kosha/yantra/pipeline/formalize-question.om` | pending |
| 7 | `session-krama-mantra` node | mantra | `brahman/kosha/yantra/pipeline/session-krama-mantra.om` | pending |
| 8 | `assert-samskaara` mantra node | mantra | `brahman/kosha/yantra/pipeline/assert-samskaara.om` | pending |
| 9 | Avastha transition detection | in step 5 | — | pending |
| 10 | Krama/parampara/bhuta-kaala spine | in step 5 | — | pending |
| 11 | Terminal narration (parampara, avastha) | OCaml | `socket.ml` | partial — turn/parampara line printed; no avastha delta yet |
| 12 | Response `"session"` JSON field | OCaml | `socket.ml` | pending — response is currently `{status, request_id, session_id, turn_id, answer_text}` only |
| 13 | `build-session-graph` replaces OCaml pipeline | OCaml | `anuvada.ml` | pending (P7/P8 gate) |
| 14 | `implication-walk` tantra | tantra | `brahman/yantra/pipeline/` | pending (P8) |
| 15 | `compose-response` tantra | tantra | `brahman/yantra/pipeline/` | pending (P8) |
| 16 | `generate-question` tantra | tantra | `brahman/yantra/pipeline/` | pending (P8+) |
| 17 | Session graph persistence to disk | OCaml | `socket.ml` | pending (P9+) |

Steps 1–3 are done. Step 4 is the immediate next OCaml task.
Steps 5–12 are the full session graph — can proceed once step 4 is wired.
Steps 13+ gate on the tantra pipeline being complete (P7/P8).

---

## Relationship to Existing Work

| Component | Previous role | New role |
|---|---|---|
| `build-question-graph` | standalone tantra called from tests | called by `build-session-graph` internally |
| `avrti-refine` / `fixpoint` | standalone refinement | final compression pass within `build-session-graph` |
| `match-mantra` | standalone tantra | receives sphoTa graph, identifies implication |
| `execute-chain` | runs physics formula | IS substitution (logic type asserted) |
| `anuvada_query` (OCaml) | full inline pipeline | thin wrapper → will call `build-session-graph` at P7/P8 |
| `yantra_resolver.ml` | BFS chain resolve | removed after `match-mantra` walking implication edges |
| `yantra_inverter.ml` | symbolic algebra | removed after `inversion` mantra handles it |
| `yantra_session` (OCaml) | single global session object | one per `session_id` in `session_store` Hashtbl |
| `question_chain` (socket field) | documented but unused | replaced by `parampara` edges in session graph |
| Logic nodes in `math/logic/` | kosha documentation | active via `vishesa` edges from `formalize-question` |
| `tarka-dvaara` sangati | structural concept | the connection point: question graph → logic layer |
| `sphoTa` sangati | linguistic concept | canonical form of the formalized question graph |
| `artha-viveka` sangati | linguistic concept | names the expansion phase of `build-question-graph` |
| `anuvada` sangati | linguistic concept | names the English generation in `compose-response` |

---

## Design Invariants

1. **sphoTa is canonical.** The Sanskrit inner graph IS the answer. English is anuvada — disposable surface. Numeric results are cached edges on the same graph, not separate state.

2. **Expansion → connection → compression = sphoTa.** One movement, three phases. No shortcut.

3. **The act of answering collapses the question into bhuta-kaala.** Not the arrival of the next question. Within the same turn, after execute-chain returns.

4. **The answered question becomes parampara.** It is the ground the next question stands on. Its samskaara is the inherited context.

5. **The question IS a chala-apeksha.** The moving reference frame. All session derivatives are taken wrt it.

6. **formalize-question uses only vishesa edges.** The same IS-A pattern as rashi. No new edge types.

7. **No new sangati nodes required.** Everything needed is already in the sangati and kosha. The implementation is type assertion, not new structure.

8. **The session graph is never reset, only extended.** Information is never discarded. Avastha transitions preserve purva (old) values alongside uttara (new).

9. **Logic nodes are active participants, not documentation.** `axiom`, `theorem`, `proof`, `modus-ponens` are asserted as vishesa types on session graph nodes. They are walkable. The narration uses them.

10. **Every response shows its reasoning.** Axioms stated → implication matched → inference applied → theorem established. Always all three layers.

11. **The session IS a growing formal proof.** Each question adds axioms (user-stated), extends the implication network (from kosha), and establishes new theorems (computed or derived). The full session is a coherent proof document, traversable at any point.

12. **The pipeline IS a morphism chain.** Each tantra is a structure-preserving map. The composition of tantras IS the parampara of the pipeline — readable, walkable, self-describing.
