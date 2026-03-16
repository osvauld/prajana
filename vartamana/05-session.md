# 05 — Session

**The session is a growing formal proof. Each question adds axioms, extends the
implication network, and establishes new theorems. The full session is a coherent
proof document, traversable at any point.**

---

## The question as moving frame

The first question is `sthira-apeksha` — the fixed domain anchor. It establishes
the context: physics, kinematics, this particular scene.

Every subsequent question is `chala-apeksha` — a moving reference frame. Its
meaning is measured against the established context. "What if velocity doubles?"
presupposes the ball, the mass, the previous kinetic energy. These travel with
the question as the transport term of the total derivative.

The session spine is the sequence of questions as `krama` — each one grounding
the next via `parampara`. The answered question collapses into `bhuta-kaala` and
its samskaara — the axioms it established, the theorems it proved — become the
inherited context for the next question.

---

## The session IS avrti of anuvada-ganana

The key understanding that emerged during implementation:

The session is not a wrapper around the pipeline. **The session IS the avrti of
anuvada-ganana itself.** The inner avrti runs within one sentence — words →
graph → fixpoint → answer. The outer avrti runs across turns — answer → seed →
next question → next answer.

Same spiral. Different scale. This is why the architecture is:

```
socket question command
  ├── session_id present → session-anuvada.tantra   (outer avrti, across turns)
  │     prior-graph in → anuvada-ganana → remember → result out
  └── no session_id   → anuvada-ganana.tantra        (inner avrti, one sentence, pure)
```

`anuvada-ganana` is pure — sentence in, answer out, no session state.
`session-anuvada` owns the parampara: receives prior-graph, calls `anuvada-ganana`,
stores this turn's sankhya concepts back for the next turn.

---

## What is done

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

**Cross-turn wiring** — working:
- Turn 1: `"mass is 5"` → `session-anuvada` remembers `[mass → 5.0]`
- Turn 2: `"find kinetic energy given velocity 10"` → socket builds `prior-graph = [[mass, sankhya, 5.]]`
  → `session-anuvada` injects after `avrti-refine` (before `kosha-expand`)
  → match-mantra finds kinetic-energy-mantra with both janya covered → `kinetic-energy = 250`

**Critical constraint discovered**: prior-graph must be injected **after** `avrti-refine`,
not before. `sandhi-bandhana` (inside avrti-refine) rewrites `[concept, sankhya, val]`
subjects based on rename markers — it corrupts prior-turn triples whose concepts
are not present in the current sentence. Injecting after avrti protects them.

**All session tests passing.** `test_cross_turn_binding_completes_match` — done.

**Baseline: 346 passed / 8 xfailed.**

---

## What the plan said vs what was built

The plan said: "thread `se_graph` and `se_yantra` into `anuvada_query`. One OCaml change."

What was actually needed:
1. A new tantra — `session-anuvada.tantra` — as the outer avrti
2. A new OCaml entry point — `run_session_anuvada` — that passes `prior-graph` as an injected env value
3. The socket routes by `session_id` presence: session → `session-anuvada`, no session → `anuvada-ganana`
4. The injection point is after avrti-refine, not before (sandhi-bandhana constraint)

The deeper truth: the session is not "anuvada-ganana with more context".
It is a structurally separate avrti at a higher scale.

---

## The session as parampara

Parampara — the deepening chain. Each answered question IS the ground the next
question stands on. Its samskaara — the mark it left — seeds the next expansion.

This is the structural fact:
- Turn 1's sankhya concepts are remembered into `se_yantra.bindings`
- Turn 2 receives them as `prior-graph` — pre-resolved triples, post-avrti
- `kosha-expand` sees all established concepts as PPR seeds — domain widens with each turn
- `match-mantra` can complete a mantra whose janya were spread across turns

The session IS a filtration — ascending layers, each contained in the next.

---

## What is not yet done

### The session as scene accumulator (Gap 2 — next after Gap 1)

The current session carries sankhya values (numbers). This is correct but
insufficient. The scene is not just numbers — it is entities with owned properties.

Each turn can introduce a new entity:
```
Turn 1: electron-A  (mass, charge, velocity)
Turn 2: field-B     (strength, direction)
Turn 3: proton-C    (mass, charge, velocity)
```

By turn 3, the scene has three objects. The renderer reads all three.
This requires the session to carry entity structure — not just numbers:
- `[entity, prathama-vibhakti, object]`
- `[property, shashthi-vibhakti, entity]`
- `[entity, vishesa, rashi]`

These structural triples must travel in `se_graph` (already in `session_entry`,
currently unused) and be injected into `merged` in `session-anuvada.tantra`
alongside the sankhya `prior-graph` triples — after avrti-refine.

This is Gap 2. It is the next step after Gap 1 (unit label collision).
It is what makes pratibimba's multi-entity scenes possible.

### The formal session graph (future — P7/P8 gated)

The formal proof document structure — logical assertions, axiom/proposition/theorem
type edges, krama/parampara/bhuta-kaala spine — is the `build-session-graph.tantra`,
`formalize-question.tantra`, `assert-samskaara.tantra` layer. Gated on P7 and P8.
This is separate from and later than Gap 2.

### The dialogue loop (future)

When a derivation cannot complete — slot unfilled, no intent — the pipeline
returns "no match". It should instead generate a question targeting the gap.
`generate-question.tantra` — not yet built. Every dead end produces a question.

---

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-16 | Initial writing — synthesized from session-graph.md, socket.ml state, test_session.py |
| 2026-03-16 | Full rewrite after implementation. Session IS outer avrti. sandhi-bandhana constraint discovered. session-anuvada.tantra built. Cross-turn working. |
| 2026-03-16 | Gap 2 clarified: session must carry entity structure (prathama/shashthi-vibhakti), not just sankhya. Each turn adds new entities — scene accumulates. se_graph (already in session_entry) is the vehicle. |
