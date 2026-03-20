# 18 — Implementation Plan

**What to build next. Clean slate from session 19.**

Philosophy: [18-philosophy.md](18-philosophy.md)
Changelog: [changelog.md](changelog.md)

---

## Baseline

**78 passed / 39 xfailed / 0 failed** (v2 test suite, 117 tests, session 19)

---

## Architecture In Place

What already works (from sessions 14-19):

- **One mechanism**: kosha → eval → apply-op for physics, count, comparison
- **Graded ring**: grade-sparsha splits at viraam + dvandva boundaries
- **Count-chain**: fold over grades with kosha-driven kshaya/vriddhi detection
- **Subgraph architecture**: emit-triples receives [current-grade, entity-registry, binding-ledger, grammar-trail]
- **Dravya promotion**: unknown words promoted to satya with guards (verb form, locative, binding)
- **Karaka nodes**: 6 karakas connecting vibhakti ↔ sangati roots
- **Verb morphology**: kta-pratyaya (-ed), shatr-pratyaya (-ing) as guard signals
- **Locative prepositions**: prep-on, prep-in, prep-at → saptami-vibhakti → adhikarana edge
- **Analysis tools**: `vy parse`, `shabda verbs`, `shabda karaka`

---

## The Three Modes of Address

Every utterance to the proof graph is a vibhakti relation to vyakarana.
The pipeline must detect the mode and route accordingly.

### Step 3.0: Sambodhana — existence acknowledgment

**What**: "Hello", "Hi", "Hey" → `[word, sambodhana, vyakarana]`

The speaker acknowledges the proof graph exists and opens a sambandha.
This is not a greeting — it is the vocative case. Everything after this
is addressed to the graph.

**Done (session 20):**
- Signal detection via shabda (not individual .om nodes): `english-grammar-signals.shabda`
  maps hello→sambodhana, hi→sambodhana, hey→abhisambodhana, yo→abhisambodhana, greetings→aamantrana
- emit-triples reads signal via `shabda "english-grammar-signals" word`
- Emits `[word, signal-degree, word]` triple (preserves sambodhana/abhisambodhana/aamantrana degree)
- Three degrees formalized in sangati/grammar/vibhakti/: sambodhana, abhisambodhana, aamantrana
- I/you as apeksha markers: vacaka=chala-apeksha (moving frame), addressee=sthira-apeksha (fixed frame)
- anuvada-setu.shabda has speech-sambodhana/speech-abhisambodhana/speech-aamantrana responses

**Remaining:** emit-reasoning needs to speak when sambodhana is the only signal in the graph.

**Verify:**
```
python3 -m tools vy eval 'shabda "english-grammar-signals" "hello"'
  → sambodhana
python3 -m tools vy trace 'hello'
  → [hello, sambodhana, hello] triple emitted
```

### Step 3.1: Darshana — "what is X?"

**What**: "What is mass?", "Tell me about velocity" → inspect the graph node

When vidhi-kaala (intent) is present but no computable values exist, the question
asks what the graph **knows** about a concept, not what it can **compute**.

**Build:**
1. Detect: has vidhi-kaala + has satya concept + NO sankhya values → darshana mode
2. Route to darshana tantra (already exists as `node-info` builtin in OCaml)
3. Emit: concept's edges, shabda, connections — formatted via anuvada-setu

**Verify:**
```
python3 -m tools ask 'what is mass'
  → "mass is a quantity. it has units: kilogram. it appears in: momentum, kinetic-energy, ..."
```

### Step 3.2: Prajna-dana — knowledge intake

**What**: "A ball has mass 5kg" (statement, no question) → accept as axiom

Currently the pipeline always tries to compute an answer. When there's no
vidhi-kaala and no prashna, the sentence is a **declaration** — the speaker
is giving knowledge to the graph.

**Build:**
1. Detect: NO vidhi-kaala + NO prashna → statement mode
2. Accept the BQG triples as session state (prajna-dana)
3. Respond with acknowledgment: "understood" or echo back the parsed knowledge

**Verify:**
```
python3 -m tools ask 'a ball has mass 5kg'
  → "ball: mass = 5 kg"
```

---

## Entity Recognition

### Step 3.3: Proper nouns (prathama-vibhakti)

**What**: "Tom", "Mary", "India" — unknown words that are entities, not substances

**The signal**: capitalization. In English, a capitalized word that isn't sentence-initial
is a proper noun. This is prathama-vibhakti — the word names an entity.

**Build:**
1. In BQG: detect capitalized words that don't resolve via shabda-anveshana
2. If not sentence-initial AND capitalized → emit `[word, prathama-vibhakti, word]`
3. This declares the word as an entity (karta/karma) rather than dravya
4. Entity enters entity-registry subgraph for cross-sentence reference

**Data needed:**
- Add `"prathama-vibhakti-yukta"` already in visheshanam-ring ✓
- Tantra builtin or shabda check for capitalization (may need OCaml primitive `is-capitalized`)

**Verify:**
```
python3 -m tools vy parse 'Tom has 5 apples'
  → Tom [prathama-vibhakti] proper noun entity
```

### Step 3.4: Pronoun resolution

**What**: "He", "She", "It", "They" → resolve to last entity in entity-registry

**Build:**
1. Add bhasha grammar nodes for pronouns: `pronoun-he.om`, `pronoun-she.om`, etc.
   - `shabda word:he role:grammar` + `"purusa-prathama-sthita eka-vachana-sthita"`
2. In emit-triples: when a pronoun is detected, look up entity-registry subgraph
   - Last entity → replace pronoun with entity name
3. Emit: `[entity-name, naama-pratibodha, pronoun-word]` (reference triple)

**Verify:**
```
python3 -m tools vy parse 'Tom has 5 apples. He gives 2 to Mary.'
  → He [naama-pratibodha] → Tom (resolved from entity-registry)
```

---

## Analysis Tantras

### Step 3.5: karaka-viveka — role assignment

**What**: Given a sentence graph, classify each word's karaka role.

**Build:**
1. New tantra `brahman/yantra/vibhakti/karaka-viveka.tantra3`
2. Walk grammar-trail + entity-registry + verb detection
3. Emit role triples: `[Tom, karta, gives]`, `[apples, karma-karaka, gives]`, `[Mary, sampradana, gives]`
4. Wire into pipeline after BQG, before or during avrti-refine

**Unlocks:** sentence structure understanding → correct answer generation

### Step 3.6: prayoga-viveka — voice detection

**What**: Active ("Tom ate"), passive ("cookies were eaten"), impersonal ("there are 5")

**Build:**
1. New tantra `brahman/yantra/vibhakti/prayoga-viveka.tantra3`
2. Detect: bhuta-kaala + kta-pratyaya = karmani-prayoga (passive)
3. Detect: copula + no verb = bhave-prayoga (impersonal)
4. Default: kartari-prayoga (active)
5. Emit: `[sentence, prayoga, kartari/karmani/bhave]`

**Unlocks:** correct answer sentence construction (active vs passive vs impersonal)

---

## Data Gaps (from analysis tools)

### Verb coverage

87 verbs in common-sense-events. 10 still missing:
`asked, carried, kept, let, moved, put, said, split, told, washed`

These are **neutral verbs** (neither clearly kshaya nor vriddhi). They need a
third category or case-by-case classification:
- moved, carried, put → **transfer** (kshaya from source, vriddhi to destination)
- kept, saved → **neutral** (no change in count)
- said, told, asked → **speech** (not a count operation)

### Preposition gaps

| Preposition | Vibhakti | Status |
|---|---|---|
| prep-of | ? | Unconnected — possessive? partitive? |
| prep-over | ? | Unconnected — saptami (locative) or path? |
| prep-per | ? | Unconnected — rate/ratio signal |

### Missing from visheshanam-ring

- `"sambodhana-yukta"` — needed for Step 3.0
- `"prathama-vibhakti-yukta"` — already present ✓
- `"prayoga-yukta"` — already present ✓

---

## Remaining Steps (from 17c, updated)

These steps from the original plan are still pending:

| Step | What | Prerequisite | Xfails |
|---|---|---|---|
| 2a | Set operation runtime primitives | — | 0 |
| 4 | derive-chain → DAG walk + match-first | — | 0 |
| 5 | anumana-viveka → scan-ref loop | — | 0 |
| 6 | Dissolve anuvada-ganana (mode dispatch) | 3.0-3.2 | 0 |
| 7 | viveka-derive (per-entity + max) | entity scoping | +3 |
| 8 | dvandva-ganana (distributivity + fold) | entity scoping | +3 |
| 9 | krama-viveka (transitive) | step 6 | +2 |
| 10 | anumana-ganana (logic ops + premise graph) | step 6 | +1 |

**Step 6 absorbs Steps 3.0-3.2** — dissolving anuvada-ganana into mode dispatch
IS the implementation of the three modes of address.

---

## Implementation Order

| Step | What | Type | Status |
|---|---|---|---|
| **3.0** | **Sambodhana — greeting/acknowledgment** | Mode | **Signal done, response pending** |
| **3.1** | **Darshana — "what is X?" inspection** | Mode | Next |
| **3.2** | **Prajna-dana — knowledge intake** | Mode | Next |
| **3.3** | **Proper noun recognition (capitalization)** | Entity | Next |
| **3.4** | **Pronoun resolution (entity-registry)** | Entity | Next |
| **3.5** | **karaka-viveka tantra** | Analysis | Next |
| **3.6** | **prayoga-viveka tantra** | Analysis | Next |
| 2a | Set operation primitives | Infrastructure | Pending |
| 4 | derive-chain → DAG walk | Performance | Pending |
| 7 | viveka-derive (per-entity) | Computation | Pending |
| 8 | dvandva-ganana (per-entity sum) | Computation | Pending |
| 9 | krama-viveka (transitive) | Computation | Pending |
| 10 | anumana-ganana (logic) | Computation | Pending |

**Priority**: 3.0 → 3.1 → 3.3 → 3.4 → 3.5 (each builds on the previous).
3.2 and 3.6 can be done in parallel after 3.1.

---

## Verification Commands

```bash
# New analysis tools (session 19)
python3 -m tools vy parse 'Tom has 5 apples. He gives 2 to Mary.'
python3 -m tools shabda verbs
python3 -m tools shabda karaka

# Standard verification
python3 -m tools test run
python3 -m tools vy restart
python3 -m tools ask 'hello'
python3 -m tools ask 'what is mass'
```

---

## What Has Changed

| Date | Session | Event |
|---|---|---|
| 2026-03-20 | 19 | Document created. Clean implementation plan from Step 2.5 completion. Three modes of address as organizing principle. |

done
