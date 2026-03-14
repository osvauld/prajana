# Entity, Conversation, and Grammar Generation Plan

**Date**: 2026-03-14
**Test baseline**: 246 passed, 46 xfailed (15 new gap tests + 31 pre-existing)
**References**:
- `nlp/scene-understanding.md` — signal-based ownership, mithya/satya, entity signals
- `nlp/question-graph.md` — sentence as graph, stateful reduce, artha-viveka
- `nlp/sanskrit-grammar-layer.md` — purusa, vibhakti, kaala, prayoga; artha-viveka not sankshepa
- `nlp/grammar.md` — vibhakti table, purusa table, vachana, pada
- `nlp/session-graph.md` — session as growing proof, parampara, samskaara
- `nlp/graph-formalization-plan.md` — dimensions, R8 signal-based ownership
- `nlp/bhasha-english.md` — English bhasha layer, tinanta/subanta/avyaya formats
- `ocaml-refactor.md` — current build state, gap 1-5, word-node root cause

---

## The Core Insight — Everything Is the Same Pipeline

Physics questions, logic questions, and normal conversation are not different systems.
They are the same graph pipeline applied to different kosha nodes.

```
"what is kinetic energy given mass 5 and velocity 10?"
→ artha-viveka → sphoTa → match mantra → execute-chain → anuvada → answer

"all objects with mass experience gravity"
→ artha-viveka → sphoTa → match niyama → no compute → anuvada → acknowledgement

"I am tired"
→ artha-viveka → sphoTa → assert axiom → no compute → anuvada → empathy response
```

The difference is what the kosha contains and what the graph walk produces.
- Physics: kosha has mantras with krama chains → compute path
- Logic: kosha has niyama nodes (laws, implications) → inference path
- Conversation: kosha has state nodes, person nodes, relational predicates → assertion path

One pipeline. Three kosha domains.

---

## What an Entity Actually Is

An entity is any **subject that can bear properties**. Not just physical objects.
In Sanskrit grammar: the **kartaa** — the one who stands as subject in prathama-vibhakti.

### Entity classes

| Class | Examples | Sanskrit purusa | How identified |
|---|---|---|---|
| Physical objects | ball, train, block, spring | prathama-purusa (3rd) | possession signal before |
| Named instances | ball-A, mass-m1, joint-1 | prathama-purusa (3rd) | tatpurusha compound + possession |
| 1st person | I, me, we, us | uttama-purusa | word: key on person node |
| 2nd person | you | madhyama-purusa | word: key on person node |
| 3rd person pronoun | it, he, she, they | prathama-purusa | word: key + naama-pratibodha signal |
| Demonstratives | this, that, these, those | prathama-purusa | word: key + deixis signal |
| The graph itself | (when addressed as "you") | madhyama-purusa | self-node in kosha |
| Implicit subject | "the system", "the object" | prathama-purusa | definite article + entity lookup |

All of these reach `prathama-vibhakti` in the graph — the nominative standing.
The purusa distinction (uttama/madhyama/prathama) is additional information on top.

### A property can belong to more than one entity

"ball A has mass 5 and ball B has mass 3"

`mass` is the **concept** (kosha node). `mass-of-ball-A` and `mass-of-ball-B` are
**rashi instances** (`[v, vishesa, mass]` + `[v, vishesa, rashi]`).

The collision problem: without entity ownership edges, both bind to the same `mass`
satya node in match-mantra and the second overwrites the first.

The fix: `vishesa-instance` creates named rashi instances scoped by entity.
This fires only after `vibhakti-shashthi` has established the entity — so the
ordering in `avrti-refine` is correct. But it requires `has` to be recognized first.

---

## The Entity Extraction Pipeline — Full Picture

### What is built and correct (architecturally)

```
vibhakti-shashthi.tantra  — R8: possession signal → prathama + shashthi edges
vishesa-instance.tantra   — R9: entity-label compound + typed rashi instance
vishesa-bandhana.tantra   — transfer value/unit bindings to the rashi instance
sandhi-kosha.tantra       — compound word resolution (kinetic-energy, ball-A)
```

These tantras exist, are designed correctly, and are wired in avrti-refine in the
right order. None of them execute because `word-node` returns None for every
`word:` keyed word in the bhasha/kosha files.

### What is not built yet

| Feature | Needed for | Status |
|---|---|---|
| Person nodes (I, you, we, they) | conversation, 1st/2nd person entities | not in bhasha |
| Quantifier nodes (all, every, some, no) | logic, general claims | not in bhasha |
| Demonstrative nodes (this, that, these, those) | deixis, back-reference | not in bhasha |
| Interaction signals (hits, pushes, transfers) | multi-entity physics | not in bhasha |
| The graph's self-node | graph as conversational participant | not in kosha |
| State predicates (tired, at-rest, moving) | conversation + physics state | partial |
| `sarva-vishesa` (universal quantifier) | "all X have Y" | not in sangati |

### The root cause blocking everything: `word-node` returning None

`word-node` queries `word_index` (a Hashtbl built by `build_word_index`).
`build_word_index` scans all graph nodes for `word:` keys in their shabda.

Both `verb-has.om` (`word:has`) and `kilogram.om` (`word:kg,kilogram`) have correct
`word:` keys. Yet `word-node "has"` → None and `word-node "kg"` → None.

This is the **single blocker** for:
- Gap 1 (kg/N/m/s abbreviations) — 5 xfails
- Gap 2 (has/with/was grammar) — 5 xfails
- Gap 4 (entity ownership) — 5 xfails
- All entity extraction (R8 never fires)
- All unit binding (emit-triples unit path never fires)

Fix this one thing and ~15 xfails promote to passing immediately.

Likely cause: `build_word_index` is not being called on the brahman/bhasha/ path,
or the server is running a stale build. Must be diagnosed before any brahman work.

---

## Conversation as Graph — The Same Walk, Different Kosha

### Physics question
```
"what is kinetic energy given mass 5 and velocity 10?"

sphoTa:
  [mass,           vishesa,  axiom]        ← user-stated, self-grounding
  [mass,           sankhya,  5.]
  [velocity,       vishesa,  axiom]
  [velocity,       sankhya,  10.]
  [kinetic-energy, vishesa,  proposition]  ← open slot = solve-for
  [ke-mantra,      vishesa,  implication]  ← kosha surfaced this via PPR

walk → modus-ponens → substitution → 250J → anuvada
```

### Logic assertion
```
"all objects with mass experience gravity"

sphoTa:
  [objects,  sarva-vishesa,  object]      ← universal: ∀x.object(x)
  [mass,     sambhavana,     objects]     ← conditional: if x has mass
  [gravity,  kramanusara,    objects]     ← then x experiences gravity
  [claim,    vishesa,        niyama]      ← this is a law, not an instance

walk → no compute → match niyama → anuvada: "Yes, that is Newton's law of gravitation."
```

### Conversation — assertion about speaker state
```
"I am tired"

sphoTa:
  [I,      uttama-purusa,    speaker]     ← speaker = uttama-purusa entity
  [I,      prathama-vibhakti, object]     ← I is the nominative subject
  [tired,  vartamana-kaala,  I]           ← current state of speaker
  [tired,  vishesa,          axiom]       ← speaker-stated = self-grounding axiom
  [tired,  mithya → ?]                   ← 'tired' not yet in kosha; stays mithya

walk → no compute → asprista-aware anuvada:
  "I hear that you are tired."  ← madhyama-purusa response, vartamana
```

### Conversation — question to the graph
```
"what do you know about kinetic energy?"

sphoTa:
  [you,           madhyama-purusa,  graph]        ← the graph is being addressed
  [kinetic-energy, vidhi-kaala,      solve-for]    ← what is asked about
  [know,          naama-viveka,     ?]             ← epistemic query: what does graph know?

walk → walk kosha for kinetic-energy → anuvada as uttama-purusa:
  "I know that kinetic energy is ½mv², measured in joules."
```

The **only** difference between these is what the kosha returns during graph walk.
The pipeline structure is identical.

---

## The Graph as Conversational Participant

The proof graph is not a tool. It is an entity in the conversation.

### The graph's purusa identity

When the graph **speaks**: uttama-purusa (I / we)
When the graph is **addressed** ("you"): madhyama-purusa
When the graph **refers to external things**: prathama-purusa

This must be explicit in the graph. The graph needs a self-node:

```
# brahman/kosha/brahman-self.om
kosha brahman-self

  "uttama-purusa-sthita"          ← speaks as first person
  "madhyama-purusa-yukta"         ← can be addressed as second person
  "viveka-swarupa"                ← its nature is discernment
  "artha-viveka-kriya"            ← what it does: meaning-discernment

  shabda brahman / I / the-proof-graph / this-system

done
```

When `you` is the subject and the context is a question to the system,
`lookup-word "you"` → resolves via naama-pratibodha back to `brahman-self`.

### The graph's grammar when speaking

Every response line the graph generates has a grammatical structure. This is not
a template — it is anuvada: the artha already in the sphoTa carried across into
English dhvani as a new utterance by uttama-purusa.

| Response situation | Kaala | Prayoga | Purusa | Example |
|---|---|---|---|---|
| Reporting understanding | bhuta-kaala | kartari | uttama | "I resolved 'kinetic energy' from..." |
| Stating a known fact | vartamana | bhave | — | "Kinetic energy is ½mv²." |
| Giving a computed result | bhuta-kaala | kartari | uttama | "I found kinetic energy = 250 J." |
| Admitting uncertainty | vartamana | kartari | uttama | "I could not resolve 'ball'." |
| Asking for information | vidhi | — | madhyama | "What is the mass?" |
| Acknowledging assertion | vartamana | kartari | uttama | "I hear that you are tired." |
| Citing established theorem | bhuta-kaala | karmani | — | "This was established as a theorem." |

These structures live in the kosha as bhasha nodes — the same pattern as `bhasha reaches`
(tinanta, vartamana, eka-vachana, prathama-purusa, kartari). The anuvada walk selects
the right bhasha node for each response line by matching its grammatical properties.

---

## What We Are Discovering: The Five Layers of Understanding

Any input — physics, logic, conversation — passes through the same five layers:

```
Layer 0: dhvani    — the raw English words (surface, disposable)
Layer 1: artha     — the meaning (entities, properties, relations, intent)
Layer 2: sphoTa    — the Sanskrit inner graph (artha made structurally explicit)
Layer 3: viveka    — the reasoning (what can be derived from sphoTa via kosha walk)
Layer 4: anuvada   — the response (fresh English dhvani generated from viveka result)
```

Entity recognition lives at Layer 1→2: the transition from raw words to typed graph
nodes. This is where `prathama-vibhakti`, `uttama-purusa`, `shashthi-vibhakti` emerge.

The entity IS defined at Layer 2. Before Layer 2 it is mithya. After Layer 2 it has
structural identity: it is reachable, walkable, scopeable.

---

## Implementation Order

### Phase 0 — Fix the foundation (word-node root cause)

**One thing, unblocks everything.**

Diagnose why `build_word_index` is not populating `word_index` for bhasha grammar
nodes and physics unit nodes. Likely suspects:
- Server running stale build (rebuild and restart)
- `build_word_index` not called on `brahman/bhasha/` path
- `word:` key parser not handling multi-value comma-separated strings correctly
- `setu_shabda.parse_shabda` not finding `word` key in node's shabda

Test: `word-node "has"` → should return `"verb-has"`.
Test: `word-node "kg"` → should return `"kilogram"`.

Gate: all 15 gap tests should move from xfail to pass on this fix alone.
(Gaps 1, 2, 4 are directly unblocked. Gap 3 is separate — `what` role:intent fix.)

### Phase 1 — Gap 3: `what` as intent signal

`lookup-word "what"` already returns `"what"` (direct graph hit).
But `shabda "what" "role"` → None. The `prashna.om` node has `word:what role:intent`
but `what` as a direct graph node has no role sloka.

Fix: emit-triples currently checks `role` from the looked-up node. When the node IS
`"what"`, it has no role. The `prashna` node (which has `role:intent`) is a
different node. Two options:
- A: Add `role:intent` to the `what` node's shabda directly in brahman
- B: Make lookup-word return the bhasha node (prashna) not the raw graph node

Option A is simpler. Add to brahman/bhasha/english/grammar/prashna.om or create a
thin `what.om` node with `role:intent`.

### Phase 2 — Person nodes (conversation unblocked)

Create bhasha nodes for first/second/third person pronouns and conversational entities.
These are the minimum for conversation to work:

```
brahman/bhasha/english/grammar/pronoun-i.om
  word:I,me,myself  role:entity  purusa:uttama  vachana:eka

brahman/bhasha/english/grammar/pronoun-we.om
  word:we,us,ourselves  role:entity  purusa:uttama  vachana:bahu

brahman/bhasha/english/grammar/pronoun-you.om
  word:you,yourself,yourselves  role:entity  purusa:madhyama

brahman/bhasha/english/grammar/pronoun-it.om    (already exists — verify role)
brahman/bhasha/english/grammar/pronoun-its.om   (already exists — verify role)
brahman/bhasha/english/grammar/pronoun-they.om
  word:they,them,their,themselves  role:entity  purusa:prathama  vachana:bahu
```

Each must carry `role:entity` (not `role:pronoun`) so that `emit-triples` places
them in the satya layer with prathama-vibhakti. Pronouns that are back-references
(`its`, `their`) carry `role:pronoun` and go through naama-pratibodha resolution.

### Phase 3 — Graph self-node

```
brahman/kosha/brahman-self.om
  word:vyakarana,brahman  role:entity  purusa:uttama
  "uttama-purusa-sthita madhyama-purusa-yukta"
  "viveka-swarupa artha-viveka-kriya"
```

When `you` is used in a question directed at the system, avrti resolves `you` →
naama-pratibodha → brahman-self. The response is then generated as madhyama
being addressed, and the answer is produced as uttama-purusa.

### Phase 4 — Quantifiers (logic unblocked)

```
brahman/bhasha/english/grammar/quantifier-all.om
  word:all,every,each  role:sarva  purusa:prathama
  "sarva-vishesa-sthita"

brahman/bhasha/english/grammar/quantifier-some.om
  word:some,certain  role:eka-drishthanta
  "eka-drishthanta-sthita"

brahman/bhasha/english/grammar/quantifier-no.om
  word:no,none,never  role:shunya
  "pratishedha-sthita"
```

`emit-triples` handles `role:sarva` by emitting `[concept, sarva-vishesa, object]`
instead of `[concept, satya, concept]`. The graph walk for universal claims is
different from the compute walk — no execute-chain, just niyama lookup.

### Phase 5 — Interaction signals (multi-entity physics)

```
brahman/bhasha/english/grammar/verb-hits.om
  word:hits,collides,impacts  role:interaction
  "trtiya-vibhakti-sthita"   ← instrumental: A hits B means A via B

brahman/bhasha/english/grammar/verb-pushes.om
  word:pushes,applies,exerts  role:interaction
```

Interaction signals create a new edge type in the question graph:
`[entity-A, trtiya-vibhakti, entity-B]` — entity A acts on entity B.
avrti then instantiates a momentum-transfer or force-application scenario.

### Phase 6 — compose-response.tantra (anuvada layer)

The response generator must know the graph is uttama-purusa.
Each response section has a grammatical structure from the table above.

```
tantra compose-response
  takes match result graph

  -- what was understood
  understanding = compose-understanding graph

  -- what was matched
  reasoning = compose-reasoning match

  -- what was computed
  conclusion = compose-conclusion match result

  -- what remained asprista
  assumptions = compose-assumptions graph

  response = join [understanding, reasoning, conclusion, assumptions] "\n"
  return response
done
```

Each sub-tantra walks the appropriate graph layer and emits English lines using
bhasha node anuvada — the same mechanism as `to-english` on kosha nodes.

### Phase 7 — anuvada-ganana.tantra (the full orchestrator)

```
tantra anuvada-ganana
  takes sentence

  graph0   = build-question-graph sentence
  graph    = fixpoint graph0 avrti-refine
  match    = match-mantra graph
  result   = cond (gt (length match) 0)
               (execute-chain (nth match 0) (nth match 1))
             otherwise _none
  response = compose-response match result graph

  return response
done
```

This unblocks all 9 session xfails in test_session.py at once.

---

## The Conversation Pipeline vs Physics Pipeline

They share everything except the kosha they walk:

```
Physics pipeline:
  sphoTa → match-mantra (mantra node) → execute-chain → compose-result

Logic pipeline:
  sphoTa → match-niyama (niyama node) → implication-walk → compose-derivation

Conversation pipeline:
  sphoTa → assert-axiom (no match needed) → compose-acknowledgement

Mixed pipeline (theoretical physics):
  sphoTa → match-mantra + match-niyama → both paths → compose-trace
```

The routing lives in `anuvada-ganana.tantra` — it checks what the graph contains
and routes accordingly:
- Has `[X, vishesa, axiom]` + matching mantra → compute
- Has `[X, vishesa, proposition]` only → theoretical (implication-walk)
- Has `[X, uttama-purusa]` or `[X, madhyama-purusa]` → conversation
- Has `[X, sarva-vishesa, Y]` → logic claim (niyama match)

This routing table lives in `anuvada-ganana.tantra` as cond branches — pure brahman.
No OCaml branching logic.

---

## What "Correct Grammar Generation" Means

The response is not a template. It is anuvada — the artha in the sphoTa expressed
as fresh English dhvani through the graph's grammatical identity.

For the graph to generate grammatically correct English as uttama-purusa:

1. The sphoTa contains the result as typed graph nodes (theorem, axiom, rashi)
2. Each node has bhasha edges (to-english walks them)
3. The grammatical context (uttama-purusa, bhuta-kaala, kartari) is asserted on the
   response node before anuvada begins
4. The anuvada walk selects English surface forms by matching grammatical properties:
   - `purusa:uttama` + `kaala:bhuta` → past tense 1st person verb form
   - `vibhakti:prathama` on result → nominative: "kinetic energy IS 250J"
   - `vibhakti:shashthi` on entity → genitive: "of ball-A"
   - `vachana:eka` + `linga:napumsaka` → "it" pronoun for back-reference

5. The composed sentence is the surface form of the walk — not assembled from
   string concatenation but from graph traversal of bhasha nodes.

This is Phase S4 from `sanskrit-grammar-layer.md`. It is not blocked by anything
above — it can be built incrementally, starting with the simplest case (numeric
result with unit) and extending to full reasoning traces.

---

## Where We Are — Honest Assessment

### Working now
- `build-question-graph` — correct, all satya/mithya/sankhya triples
- `avrti-refine` — compound resolution (R1/R2), avastha (R2), sankhya binding (R4)
- `sandhi-kosha`, `sandhi-avastha`, `sandhi-bandhana` — working
- `match-mantra` — working for direct compute questions with explicit named concepts
- `execute-chain` — working for all 24 physics mantras
- `fixpoint` — working, terminates correctly

### Not working (word-node blocked)
- Entity detection (vibhakti-shashthi) — needs `word-node "has"` to work
- Unit binding (emit-triples unit path) — needs `word-node "kg"` to work
- `what` as intent — separate fix (role:intent on what node)

### Not yet built
- Person pronouns (`I`, `you`, `we`)
- Graph self-node (`brahman-self`)
- Quantifiers (`all`, `every`, `some`)
- Interaction signals (`hits`, `pushes`)
- `compose-response.tantra`
- `anuvada-ganana.tantra`
- Conversation routing in `anuvada-ganana`
- Reasoning trace (Proposition / Reasoning / Theorem / Proof / Conclusion)
- Pronoun resolution (R10)
- Definite article back-reference (R11)
- Dvandva groups (R5/R6/R7/R12)

### The immediate path
1. Diagnose `word-node` root cause → fix → 15 xfails promote
2. Fix `what` role:intent → 4 more xfails promote
3. Build `compose-response.tantra` + `anuvada-ganana.tantra` → 9 session xfails promote
4. Add person nodes → conversation unblocked
5. Add quantifiers → logic unblocked

---

## Key Design Decisions Settled in This Session

1. **Physics, logic, and conversation are the same pipeline.** The kosha is the only
   difference. No separate "conversation mode" — just different node types in sphoTa.

2. **The graph is uttama-purusa.** It speaks as "I". It has a self-node in the kosha.
   When addressed as "you", it resolves via naama-pratibodha to its self-node.

3. **Entities are not just physical objects.** I, you, we, they, this, that — all are
   entities with prathama-vibhakti. Purusa (uttama/madhyama/prathama) is additional
   information on top of entity-hood.

4. **A property can belong to multiple entities.** The instance layer (rashi nodes via
   `vishesa-instance`) resolves the collision — `mass-of-ball-A` ≠ `mass-of-ball-B`
   even though both are `[X, vishesa, mass]`.

5. **Entity must be established before binding.** The avrti-refine pipeline order is
   correct: compound resolution → entity detection → instance creation → binding transfer.
   `word-node` working is the prerequisite for all of it.

6. **Grammar generation is graph traversal, not templates.** The response is anuvada:
   artha already in the sphoTa, walked through bhasha nodes, expressed as fresh English.
   The grammatical structure (purusa, kaala, prayoga, vibhakti) lives in the graph.

7. **Conversation routing lives in anuvada-ganana.tantra.** No OCaml branching.
   The cond branches in the tantra route to compute/theoretical/conversation based
   on what the sphoTa contains.
