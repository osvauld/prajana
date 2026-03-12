# Full Pipeline Plan — Canonical Reference

**Created**: 2026-03-12
**Status**: P0–P6c + logic enrichment + OCaml primitives done. P7 next.
**Supersedes**: composition-pipeline.md (incorporated here), hollerith.md
**Regression baseline**: 49/52 (do not break)

---

## Core Principles

1. **Nothing hardcoded** — every word list, grammar pattern, formula pattern lives in the graph
2. **Sphota** — meaning emerges from the whole; PPR over token seeds surfaces what the question IS about before parsing finishes
3. **Krama = narrative** — the computation chain narrates itself using `word:` keys on operations + kaala copula keys
4. **Bhava prayoga** — all output is impersonal/process-focused ("velocity was squared... kinetic energy is 22.5 joules")
5. **No fallback paths** — old OCaml paths are removed, not kept as fallbacks. Regression gate enforces this.
6. **Decomposition is the inverse of composition** — parsing and generation walk the same graph in opposite directions

---

## What Is Complete

### OCaml Primitives (done, in working tree)
- `word-node word` — O(1) bhasha `word:` key lookup via `word_index` hashtbl built at startup
- `call-tantra name args-list` — tantras calling other tantras by name (composition + recursion)
- `execute-chain` — stack machine over krama edges (was done earlier, P5)
- `apply-op` — apply op node by eval: key to value args
- `half`, `double`, `square` new ops in `yantra_ops.ml`
- `build_word_index` in `yantra_index.ml` — scans all nodes for `word:` keys at startup

### Graph Nodes (done)
- **Math operation word: keys** — addition, subtraction, multiplication, division, square, square-root, half, double, power, sine, cosine, tangent all have `word:` + `eval:` + `arity:`
- **Logic operations enriched** — conjunction (word:and,both eval:and arity:2), disjunction (word:or,either eval:or arity:2), negation (word:not,without eval:not arity:1), implication (word:if,implies,therefore), quantifier (word:all,every,some)
- **Proof-rule nodes** — modus-ponens.om, substitution.om, inversion.om (narration anchors, word: keys only)
- **PPR graph node** — brahman/kosha/math/graph/operations/ppr-mantra.om

### Grammar Layer (done)
All in `brahman/bhasha/english/grammar/`. Multi-node files split into individual files (multi-node parsing bug: `parse_file` returns only last node).

**Parent nodes** (category, not individually loaded):
- `copula.om` — is/are/was/were/equals/gives
- `article.om` — a/an/the
- `preposition.om` — of/by/per/from/over/at
- `conjunction.om` — and/or/given/where

**Individual nodes** (each in own file, all with `word:` keys):
- Copula: `copula-is`, `copula-are`, `copula-was`, `copula-were`, `copula-equals`, `copula-gives`
- Articles: `article-the`, `article-a`, `article-an`
- Prepositions: `prep-of`, `prep-by`, `prep-per`, `prep-from`, `prep-over`, `prep-at`
- Conjunctions: `conj-and`, `conj-or`, `conj-given`, `conj-where`

### Kaala Nodes with copula: keys
| Kaala | copula: | copula-formula: | use for |
|---|---|---|---|
| vartamana | is | equals | definitions, present facts |
| bhuta | was | equaled | computed results |
| bhavishya | will-be | will-equal | predictions |
| vidhi | find | compute | commands/instructions |
| sambhavana | may-be | may-equal | conditional |

### Physics Mantra Nodes (done, P5.5 + P6c)
All 21+ physics mantra nodes: `name:`, `krama-lhs-unit:`, implication-sthita edges.
Full list in `brahman/kosha/physics/*/quantities/*-mantra.om`.

### Sangati Bhasha Forms (done, P6a)
All ~50 sangati root bhasha nodes in `brahman/bhasha/english/` with `word:` keys.

---

## Tantra Migration Plan

### Keep (active, used in new pipeline)
| Tantra | Why keep |
|---|---|
| `darshana.tantra` | inspection / debug |
| `ppr.tantra` | PPR scores (first called from disambiguate-tokens P7.5) |
| `context-score-impl.tantra` | scoring primitive |
| `weighted-context-score.tantra` | weighted scoring |
| `sthita-depth.tantra` | graph depth utility |
| `visheshanam-entropy-weights.tantra` | scoring weights |
| `per-relation-score.tantra` | per-edge scoring |
| `compose-degrees.tantra` | degree multiplication (P5) |
| `is-identity-composition.tantra` | inverse check (P5) |
| `graph-dimensions.tantra` | graph analysis |
| `matra-ganana.tantra` | unit computation (real logic, future mantra) |
| `matra-viveka.tantra` | unit type inference |
| `to-malayalam.tantra` | localization |
| `pramana/` tantras | verification layer |

### Move to `brahman/yantra/_migration/` (old pipeline, to be removed after P8)
**Subdirectories** — entire contents:
- `brahman/yantra/bhautika/` — physics computation (replaced by mantra nodes + execute-chain)
- `brahman/yantra/ganaka/` — old computation pipeline
- `brahman/yantra/parivartana/` — transformation pipeline
- `brahman/yantra/scene/` — scene understanding (replaced by tantra-native pipeline)
- `brahman/yantra/robotics/` — robotics pipeline
- `brahman/yantra/vidnyana/` — knowledge pipeline
- `brahman/yantra/niyata/` — constraint pipeline

**Root-level old pipeline tantras**:
- `classify-fold.tantra`, `classify-fold-resolve.tantra`, `setu-classify-token.tantra`
- `domain-of.tantra` — callers going to migration, trivially replaced by varga-vishesa walk
- `infer-inputs.tantra`, `infer-outputs.tantra` — trivially `walk node "sthita"` / `walk node "phala"`
- `matra-nirmana.tantra` — stub, real work is 43 lines of OCaml in vyakarana.ml
- `to-english.tantra` — replaced by `shabda node "name"` (one primitive call)
- `format-response.tantra` — replaced by compose-response.tantra (P8)
- `compose-answer.tantra` — old relation→English morphism, replaced by compose-response
- `anuvada-ganana.tantra` — old orchestrator, replaced by full 7-layer pipeline
- `anuvada.tantra` — old reasoning pipeline
- `query-intents.tantra` — subsumed into decompose-question.tantra
- `yantra-plan-extraction.tantra`, `yantra-plan-resolution.tantra` — replaced by new pipeline

---

## 7-Layer Pipeline Architecture

```
INPUT: sentence or paragraph
          ↓
┌─────────────────────────────────────────────────┐
│  Layer 1: TOKENISE  (P7)                        │
│  tokenise-question.tantra                       │
│  → split by space (split primitive)             │
│  → classify each word (classify-word.tantra)    │
│  → merge compounds (resolve-compounds.tantra)   │
│  OUTPUT: [[word, kind, resolved], ...]          │
└─────────────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────────────┐
│  Layer 2: SPHOTA  (P7.5)                        │
│  disambiguate-tokens.tantra                     │
│  → extract confident concept tokens as seeds    │
│  → PPR over seeds → surface related concepts    │
│  → reinterpret unknown/ambiguous tokens         │
│    via PPR score (sphota: meaning from whole)   │
│  OUTPUT: tokens enriched with ppr-context       │
└─────────────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────────────┐
│  Layer 3: DECOMPOSE  (P8)                       │
│  decompose-question.tantra                      │
│  → if paragraph: split by period, grade each   │
│    sentence (grade-sentences.tantra)            │
│  → extract intent (from prashna/vidhi-kaala)   │
│  → extract target concept (implication target) │
│  → extract value-unit bindings                 │
│  → extract selectors for paragraph coreference │
│  OUTPUT: {intent, target, anchors, bindings}   │
└─────────────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────────────┐
│  Layer 4: MATCH FORMULA  (P8)                   │
│  match-formula.tantra                           │
│  → walk implication-sthita edges from target   │
│  → check janya inputs coverage                 │
│  → if missing inputs: try pratipaksha inverse  │
│  → rank candidates (PPR score)                 │
│  OUTPUT: best mantra + bound inputs            │
└─────────────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────────────┐
│  Layer 5: EXECUTE  (EXISTS — P5)                │
│  execute-chain mantra-name [arg-vals]           │
│  → stack machine over krama edges              │
│  OUTPUT: result value + unit                   │
└─────────────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────────────┐
│  Layer 6: COMPOSE RESPONSE  (P8)                │
│  compose-response.tantra                        │
│  → narrate krama chain in bhava prayoga:        │
│    "velocity was squared, multiplied by mass,   │
│     halved"  (word: keys + bhuta-kaala copula) │
│  → append result: "kinetic energy is 22.5 J"   │
│    (krama-lhs + vartamana-kaala + value + unit) │
│  OUTPUT: full response sentence                 │
└─────────────────────────────────────────────────┘
          ↓
┌─────────────────────────────────────────────────┐
│  Layer 7: SHOW THINKING  (P8)                   │
│  compose-trace.tantra                           │
│  → token trace: what each word resolved to     │
│  → sphota trace: what PPR surfaced              │
│  → formula trace: which implication matched    │
│  → krama trace: step-by-step computation       │
│  OUTPUT: understanding trace + answer          │
└─────────────────────────────────────────────────┘
```

---

## Phase Plan (P7 → P10)

### P7 — Tokeniser Tantra (NEXT)

**Goal**: Replace OCaml char-loop + `setu_classify.ml` + classify-fold tantras.
**Gate**: 49/52 regression maintained.

**Token types**:
- `[word, "intent", "solve-for"]` — from prashna/vidhi-kaala word: match
- `[word, "number", "5.0"]` — pure numeric
- `[word, "value-unit", value, unit-node]` — "5kg" split by split-numeric primitive
- `[word, "concept", node-name]` — via word-node lookup
- `[word, "grammar", role-node]` — copula/article/preposition/conjunction
- `[word, "unknown", word]` — fallback

**New OCaml needed**:
- `split-numeric word` → `[numeric-str, alpha-str]` for "5kg", "3m/s" (~8 lines in yantra_ops.ml)
- Add `word:what,how,which,when` to `prashna` node shabda
- Add unit symbols to word_index: extend `build_word_index` or add `word:kg,kilogram` etc.

**New tantras**:
```
brahman/yantra/classify-word.tantra
brahman/yantra/resolve-compounds.tantra
brahman/yantra/tokenise-question.tantra
```

**Delete after P7 passes**:
- `classify-fold.tantra`, `classify-fold-resolve.tantra`, `setu-classify-token.tantra`
- `setu_classify.ml` (143 lines OCaml)
- `yantra_tokenise` char loop in `yantra_eval.ml`

---

### P7.5 — Sphota Layer

**Goal**: PPR-based contextual disambiguation. First use of ppr-scores.tantra.
**Insight**: "angular" alone is unknown. PPR over confident tokens surfaces "rotational" domain → "angular" resolves to `angular-velocity` or `angular-momentum` via context.

**New tantra**: `brahman/yantra/disambiguate-tokens.tantra`

```tantra
tantra disambiguate-tokens
  inputs
    tokens  list
  let
    concepts   = filter tokens (fn t -> eq (nth t 1) "concept")
    seeds      = map concepts (fn t -> nth t 2)
    ppr-result = cond (gt (length seeds) 0)
                   (call-tantra "ppr-scores" [nth seeds 0, seeds, []])
                   otherwise []
    top-node   = cond (gt (length ppr-result) 0) (nth (nth ppr-result 0) 0) otherwise ""
    enriched   = map tokens (fn t ->
      cond
        (eq (nth t 1) "unknown")
          (let probe = concat (nth t 0) "-" top-node
           let found = word-node probe
           cond (exists found) [nth t 0, "concept", found] otherwise t)
        otherwise t)
  return enriched list
done
```

---

### P8 — Composition Pipeline

**Depends on**: P7 (tokeniser), P6b (grammar nodes done), P6c (implication edges done).

**New tantras**:

| Tantra | Purpose |
|---|---|
| `grade-sentences.tantra` | paragraph → [sentence, grade, tokens] |
| `decompose-question.tantra` | tokens → {intent, target, anchors, bindings} |
| `match-formula.tantra` | implication walk → formula candidates + coverage check |
| `compose-response.tantra` | formula + result + grammar → full sentence |
| `narrate-krama.tantra` | mantra → computation narrative in bhava prayoga |
| `compose-trace.tantra` | full thinking trace (tokens + formula + krama + result) |
| `invert-mantra.tantra` | pratipaksha walk → inverse formula |
| `chain-implication.tantra` | multi-step inference chain |

**Decompose-question key logic**:
- `word-node word` for each token → if found, classify by node type (bhasha → grammar/intent, kosha → concept)
- Values: `split-numeric` primitive splits "5kg" → classify alpha part via matra-beeja
- Target: prashna word + anchor concept → intent + target node
- Bindings: value-unit pairs → `matra-ganana.tantra` resolves to quantity nodes

**Match-formula key logic**:
- Walk `implication-sthita` edges from target node
- For each candidate: check krama-rhs covered by bound quantities
- If none covered: walk pratipaksha → invert-mantra
- If still none: chain-implication (depth 2)

**Compose-response key logic**:
- krama-lhs `name:` shabda = subject noun
- bhuta-kaala `copula:` = "was" (bhava prayoga for krama narrative)
- krama steps: each op node `word:` key = narrative verb
- vartamana-kaala `copula:` = "is" (result statement)
- Full: "[inputs] [ops narrative] — [lhs-name] is [value] [unit]"

---

### P8.5 — OCaml Removal

**Depends on**: P8 working.

**Remove**:
| Target | Replacement |
|---|---|
| `yantra_resolver.ml` (`chain_resolve` BFS) | `match-formula.tantra` implication walk |
| `yantra_inverter.ml` (symbolic algebra) | `invert-mantra.tantra` krama structure walk |
| `resolve-direct` in `yantra_pipeline_ops.ml` | thin shim → call-tantra "match-formula" |
| `chain_resolve` in `yantra_resolver.ml` | thin shim → call-tantra "match-formula" |

**Gate**: 49/52.

**Also remove old tantras** (moved to _migration/ in P7/P8):
- `anuvada-ganana.tantra` (orchestrator replaced by full pipeline)
- All tantras in `_migration/` dir

---

### P9 — Tantra Tests

New runner: `vyakarana/scripts/run-tantra-tests.sh`
Each test tantra returns `bool`. Runner calls `EVAL test-name brahman/` and checks `true`.

**Phase 1 (unblocked now)**:
- `brahman/yantra/tests/primitives/` — add, mul, sqrt, split, map, filter, word-node, call-tantra
- `brahman/yantra/tests/math/` — degree fields, pratipaksha, compose-degrees
- `brahman/yantra/tests/grammar/` — copula: and word: keys on all grammar nodes
- `brahman/yantra/tests/graph/` — walk, ancestors-of, shabda lookups
- `brahman/yantra/tests/bhasha/` — bhasha nodes load, satya weight = 0.5x

**Phase 2 (after P7)**:
- `brahman/yantra/tests/mantra/` — execute-chain on all 21 physics mantra nodes

**Phase 3 (after P8)**:
- `brahman/yantra/tests/pipeline/` — full decompose→match→execute→compose
- `brahman/yantra/tests/inference/` — chain-implication, inverse via pratipaksha
- `brahman/yantra/tests/logic/` — implication/theorem/proof node structure

---

### P10 — CS Kosha Restructure

Full details in `phase-cs-restructure.md`. Not started.

---

## Verification Smoke Tests

```bash
cd /home/abe/agent_x/vyakarana
dune build
bash scripts/run-regression.sh   # must stay 49/52

# P7 smoke test
EVAL tokenise-question brahman/ "what is the kinetic energy if mass is 5 and velocity is 3"
# expect: [[what,intent,solve-for],[is,grammar,copula-is],[kinetic,concept,...],[energy,concept,...],[if,grammar,conj-given],[mass,concept,...],[is,grammar,...],[5,number,5.0],[and,grammar,conj-and],[velocity,concept,...],[is,grammar,...],[3,number,3.0]]

# P7.5 smoke test
EVAL disambiguate-tokens brahman/ "what is the angular velocity if radius is 2 and velocity is 10"
# expect: "angular" resolves via PPR context

# P8 smoke test
EVAL compose-trace brahman/ "find kinetic energy when mass is 10kg and velocity is 3m/s"
# expect: token trace + formula matched + krama narration + "kinetic energy is 45.0 joules"
```

---

## Key Files Reference

```
vyakarana/lib/yantra_eval_primitives.ml  -- word-node, call-tantra (done)
vyakarana/lib/yantra_index.ml            -- word_index, build_word_index (done)
vyakarana/lib/yantra_ops.ml              -- split-numeric (TODO P7)
vyakarana/lib/setu_classify.ml           -- TARGET REMOVAL (P7)
vyakarana/lib/yantra_resolver.ml         -- TARGET REMOVAL (P8.5)
vyakarana/lib/yantra_inverter.ml         -- TARGET REMOVAL (P8.5)
brahman/bhasha/english/grammar/          -- all grammar nodes (done)
brahman/kosha/math/logic/operations/     -- logic + proof-rule nodes (done)
brahman/kosha/physics/*/quantities/      -- 21 mantra nodes (done)
brahman/yantra/ppr.tantra                -- PPR scores (not yet called, first use P7.5)
brahman/yantra/_migration/               -- TODO: move old tantras here
```

---

## Remaining Non-Blocking Items

- Trig function `word:` keys (sin/cos/tan/asin/acos/atan) — 6 nodes missing
- Algebra/set/graph/probability/complexity `degree:` enrichment — ~26 nodes
- `conj-and` ↔ `conjunction` abheda edges (grammar ↔ logic bridge)
- `conj-given` ↔ `implication` abheda edge
- `brahman/kosha/math/graph/operations/bfs-mantra.om` — BFS as graph algorithm node
- Phase 2.7: brahman/engine/ → brahman/kosha/engine/ move
- `domain-X-sthita` in OCaml (setu.ml, anuvada.ml) — leave for now, non-blocking
