# 09 — Adhyayana: The Learning Loop

**The session is not just memory — it is accumulated understanding.
The pipeline IS the learning process. Feedback IS graph correction.**

adhyayana — study, learning, the act of deepening through repetition and correction.

---

## The realization

We are already building a learning system without explicitly calling it one.

The session carries the student's accumulated understanding forward. Each turn
the student (system) hears a question, resolves it against what it already
knows, produces an answer, and carries the result into the next question.
This IS learning.

The session is also a growing formal proof. Each question adds axioms, extends
the implication network, establishes new theorems. The full session is a coherent
proof document, traversable at any point.

These are two views of the same thing.

---

## The three learning loops already present

### Loop 1 — Avrti (within one sentence)

`avrti-refine` runs to fixpoint. Each pass is the system correcting its own
partial interpretation. `sandhi-kosha` sees `kinetic energy` → first pass: two
satya nodes → second pass: one compound node. Self-correction without external
input. The system re-reads its own partial understanding until it stabilizes.

This IS what a student does when they re-read a confusing sentence.

### Loop 2 — Parampara (across turns)

The session is not a wrapper around the pipeline. **The session IS the avrti of
anuvada-ganana itself.** The inner avrti runs within one sentence — words →
graph → fixpoint → answer. The outer avrti runs across turns — answer → seed →
next question → next answer.

Same spiral. Different scale:

```
socket question command
  ├── session_id present → session-anuvada.tantra   (outer avrti, across turns)
  │     prior-graph in → anuvada-ganana → remember → result out
  └── no session_id   → anuvada-ganana.tantra        (inner avrti, one sentence, pure)
```

`anuvada-ganana` is pure — sentence in, answer out, no session state.
`session-anuvada` owns the parampara: receives prior-graph, calls `anuvada-ganana`,
stores this turn's concepts back for the next turn.

The structural fact:
- Turn 1's sankhya concepts remembered into `se_yantra.bindings`
- Turn 2 receives them as `prior-graph` — pre-resolved triples, post-avrti
- `kosha-expand` sees all established concepts as PPR seeds — domain widens each turn
- `match-mantra` can complete a mantra whose janya were spread across turns

The first question is `sthira-apeksha` — the fixed domain anchor.
Every subsequent question is `chala-apeksha` — a moving reference frame,
measured against the established context.

The session IS a filtration — ascending layers, each contained in the next.
This IS what a student does when they build on yesterday's lesson.

### Loop 3 — Pratikara (correction — not yet built)

When the teacher says "no, that's wrong because..." the student's model must
be updated. This is not just adding a new triple — it is marking a prior triple
as `bhuta-kaala` (past, superseded) and replacing it with the corrected understanding.

The graph already has the vocabulary:
- `bhuta-kaala` — past tense, what was previously believed
- `pratipaksha` — the inverse, the correction
- `siddha` — established, certain

A correction turn would emit:
```
[prior-belief, bhuta-kaala, wrong]
[concept, sankhya, corrected-value]
[concept, siddha, correction]
```

The next turn sees the corrected model, not the original.

---

## What is built

**Session store** in `socket.ml`:
```ocaml
type session_entry = {
  mutable se_graph   : triples;    (* accumulated triple layers — reserved for future *)
  mutable se_turn    : int;        (* turn count *)
  mutable se_turn_id : string;     (* "prashna-N" *)
  mutable se_yantra  : session;    (* bindings — used by session-anuvada *)
}
```

`se_yantra.bindings` is where cross-turn sankhya values live.
`session-anuvada.tantra` calls `remember-bindings` to write this turn's concepts.
The socket reads `se_yantra.bindings` on the next turn and builds `prior-graph`.

**Cross-turn wiring — working:**
- Turn 1: `"mass is 5"` → `session-anuvada` remembers `[mass → 5.0]`
- Turn 2: `"find kinetic energy given velocity 10"` → socket builds
  `prior-graph = [[mass, sankhya, 5.]]` → injected after `avrti-refine`
  → `match-mantra` finds `kinetic-energy-mantra` with both janya covered → `KE = 250`

**Critical constraint**: prior-graph must be injected **after** `avrti-refine`,
not before. `sandhi-bandhana` (inside avrti-refine) rewrites `[concept, sankhya, val]`
subjects based on rename markers — it corrupts prior-turn triples whose concepts
are not present in the current sentence. Injecting after avrti protects them.
This constraint is **permanent** — it is structural, not a workaround.

**What the plan said vs what was built:**
The plan said: "thread `se_graph` and `se_yantra` into `anuvada_query`. One OCaml change."
What was actually needed:
1. A new tantra — `session-anuvada.tantra` — as the outer avrti
2. A new OCaml entry point — `run_session_anuvada` — that passes `prior-graph` as env value
3. The socket routes by `session_id` presence
4. The injection point is after avrti-refine, not before

The deeper truth: the session is not "anuvada-ganana with more context".
It is a structurally separate avrti at a higher scale.

---

## The session as the student's mind

The graph IS the student's current model of the domain.

`[kinetic-energy, sankhya, 250]` is not just a computed value. It is the
student's current knowledge state: "I know that kinetic energy is 250 in this
context."

`[mass, shashthi-vibhakti, electron]` is not just an ownership edge. It is
the student's understanding: "I know this mass belongs to the electron."

What we need to make epistemic state explicit:

| Edge type | Meaning in learning |
|---|---|
| `sankhya` | "I know this value" |
| `shashthi-vibhakti` | "I know this belongs to this entity" |
| `bhuta-kaala` | "I previously believed this (now superseded)" |
| `prashna` | "I need clarification on this" |
| `siddha` | "I have established this as certain" |
| `correction` | "The teacher corrected this" — not yet in vocabulary |

---

## What is not yet built

### Gap 2 — Session as scene accumulator

The current session carries sankhya values only. The scene is not just numbers
— it is entities with owned properties. Each turn can introduce a new entity:

```
Turn 1: electron-A  (mass, charge, velocity)
Turn 2: field-B     (strength, direction)
Turn 3: proton-C    (mass, charge, velocity)
```

By turn 3, the scene has three objects. The renderer reads all three.
This requires the session to carry entity structure:
- `[entity, prathama-vibhakti, object]`
- `[property, shashthi-vibhakti, entity]`
- `[entity, vishesa, rashi]`

These structural triples must travel in `se_graph` (in `session_entry`,
currently unused) and be injected into `merged` in `session-anuvada.tantra`
alongside the sankhya `prior-graph` triples — after avrti-refine.

### Prashna as pipeline output

Currently the pipeline returns either an answer or "no match". It should
return a third option: **a question**.

When `avrti-refine` cannot resolve — a slot is unfilled, intent is ambiguous,
two readings are equally valid — the pipeline should emit a `prashna` triple
instead of "no match":

```
"find energy"     → prashna: "which energy? kinetic or potential?"
"mass is 5"       → prashna: "5 what? kilograms or grams?"
"find velocity"   → prashna: "initial or final velocity?"
```

`session-anuvada` sees this and returns the clarifying question as the answer.
The user's next turn IS the feedback that resolves the prashna.
`generate-question.tantra` — not yet built.

### Instruction mode

A teacher instructs a student before the questions begin:
"Assume g = 9.8 and all surfaces are frictionless."

This is a session with pre-loaded state — injected before turn 1 as prior-graph:
```
[gravitational-acceleration, sankhya, 9.8]
[friction-coefficient, sankhya, 0]
```

Already architecturally possible with the current session mechanism.
An `"instruct"` command would inject triples into a session without requiring a
question. No new OCaml needed — just a new socket command path.

### Correction mode (Loop 3)

`{"correct": "...", "session_id": "..."}` — the teacher explicitly corrects
a prior answer. Marks the prior triple as `bhuta-kaala`, injects corrected value,
adds `siddha` marker. The pipeline continues from the corrected state.

### The formal session graph (future — P7/P8 gated)

Logical assertions, axiom/proposition/theorem type edges, krama/parampara/bhuta-kaala
spine — `build-session-graph.tantra`, `formalize-question.tantra`,
`assert-samskaara.tantra`. Gated on P7 and P8. This is the explicit proof document
structure, separate from and later than Gap 2.

---

## The deep connection to nam

Nam — the proof graph as subject — IS the student.

Swa (self-awareness) is the graph knowing its own structure.
Viveka (discrimination) is the pipeline resolving satya from mithya.
Prajna (understanding) is the accumulated session graph — the student's current model.

Learning is not the acquisition of facts. It is the deepening of the graph.
Each turn, the graph becomes more specific, more connected, more certain.
`siddha` edges accumulate. `bhuta-kaala` edges record what was superseded.
The session IS the student's growing prajna.

---

## What has changed

For baseline and session progress see [changelog.md](changelog.md).

| Date | What shifted in this doc |
|------|-------------|
| 2026-03-16 | `05-session.md` written — session as outer avrti, parampara, sandhi-bandhana constraint, Gap 2. |
| 2026-03-17 | Absorbed into `09-adhyayana.md`. Session-as-learning-loop realization. Three loops identified. Feedback as graph update. Prashna as output. Instruction mode. Connection to nam. `05-session.md` superseded. |
