# Sanskrit Grammar Layer — artha-viveka Pipeline

**Status**: S0 ✅ S1 ✅ S1.6 ✅ S2 ✅ S1.5 (reflexive satya) ✅ kosha-expand next  
**Created**: 2026-03-13  
**Depends on**: graph-formalization-plan.md (Phases 0–5 complete), session baseline 83 pass / 11 fail  
**Current baseline**: 124 pass / 11 fail (2026-03-13, after reflexive satya + 2 new tests)

---

## Core Insight

The pipeline currently works in English-named concepts throughout: edge labels are `"active"`,
`"mithya"`, `"value"`, `"owner"`, `"intent"`. These are English descriptions of what are
actually Sanskrit grammatical relations. Sanskrit is not a translation target — it is the
**canonical inner form**. English is a surface projection.

The operation of moving from English input to Sanskrit inner form is not compression
(`sankshepa`) — that implies byte-reversal, recovering the same surface. It is
**artha-viveka**: the discernment of meaning (artha) from its surface vehicle (dhvani).

- `dhvani` = the English words, word order, articles, prepositions, punctuation
- `artha` = the physics scenario, the relations, the intent
- `viveka` = precise discernment: separating what is pointed-at from what does the pointing
- `sphoTa` = the meaning that arrives whole at the sentence level (Bhartrhari) — not
  assembled word-by-word but grasped as a unit

The Sanskrit inner form IS the sphoTa made structurally explicit as a triple graph.

---

## Why artha-viveka, not sankshepa

| | sankshepa (compression) | artha-viveka (meaning-discernment) |
|---|---|---|
| Preserves | surface form (bytes) | artha (meaning/physics) |
| Reversal | exact reconstruction of input | anuvada: re-expression of artha in new dhvani |
| Loss | lossless in bytes | dhvani-lossy, artha-lossless |
| Output | shorter version of same surface | fresh English expression of extracted meaning |
| Analogy | zip file | pressing sugarcane — juice preserved, fibre dissolved |

The English output is NOT the input recovered. It is a new dhvani for the same artha:
```
Input:  "ball A has mass 5 kg and velocity 10 m/s find kinetic energy"
Output: "The kinetic energy of ball-A is 250.0 joules."
```
Different surface. Same artha. This is correct and expected.

The losslessness is **artha-losslessness**: every physical quantity, every relation,
every intent is preserved. What dissolves is grammatical noise — articles, copulas,
word order, prepositions — which carry no independent artha.

`parishishtha` (the remainder after integration) = the dhvani-fragments without
independent artha. After artha-viveka, parishishtha should be shunya.

`asprista` = parishishtha that genuinely has no artha even after all passes.
Distinct from `mithya` — see below.

---

## mithya vs asprista — precise distinction

These are NOT synonyms.

**mithya**: A word present in the sentence, apparently a concept, not yet confirmed in
the kosha. Provisionally held. Avrti passes may still resolve it. In Indian philosophy:
"apparently real but not yet grounded" — like rope before you determine it's not a snake.

**asprista**: "not yet touched by understanding" (`sangati/asprista.om` = "the term
not yet touched by understanding"). This is the epistemic state AFTER multiple passes
have tried and failed. The concept genuinely has no kosha grounding yet.

Pipeline stages:
```
word enters BQG → mithya  (provisional — not yet known)
  → avrti pass 1 → still mithya (no compound found)
  → avrti pass N → still mithya (fixpoint reached, nothing resolved it)
  → NOW → asprista (genuinely untouched after all attempts)
```

The BQG correctly uses `mithya`. `asprista` is a post-fixpoint state.
`avrti` IS `parishishtha-sankshepa` — each pass compresses the residual mithya
triples further. What cannot be compressed after fixpoint IS asprista.

---

## The Full Pipeline (corrected terms)

```
English dhvani
    ↓  artha-viveka   (BQG + sandhi-viveka)
       dhvani → artha extraction
       mithya = provisional (not yet grounded)
       sphoTa begins to form

    ↓  avrti fixpoint  (parishishtha-sankshepa)
       iterative residue compression
       mithya → satya where possible
       parishishtha → shunya at fixpoint
       unresolved after fixpoint → asprista

Sanskrit inner form (pure artha, sphoTa)

    ↓  mantra matching
       operates on artha directly
       kramanusara(X, apeksha=Y) not just d/dt

    ↓  execute-chain
       result artha

    ↓  anuvada  (re-expression, not decompression)
       result artha → fresh English dhvani
       grammar structure from visheshanam ring
       vibhakti → prepositions, shashthi → "of", prathama → subject

English output dhvani
    correctness-check-siddha: artha preserved
    kaizen-siddha: each epoch improves
```

This pipeline is already described in `kosha/cross-domain/epoch-in-language.om`:
```
sankshepa-kriya       (artha-viveka: extract from English)
aayaama-vistara-kriya (anuvada: express back in English)
translation-phala
correctness-check-siddha
kaizen-siddha
```

---

## Sanskrit Canonical Edge Names

The q-* dimensions in `visheshanam-ring.om` are English aliases for Sanskrit
grammatical relations. Sanskrit should be the canonical name; English the alias.

| Current edge string | Sanskrit canonical | Sangati grounding |
|---|---|---|
| `"active"` | `satya` | resolved/grounded in kosha |
| `"mithya"` | `mithya` | already Sanskrit — keep |
| `"value"` | `sankhya` | numeric measure |
| `"unit"` | `matra` | unit of measure |
| `"owner"` | `shashthi` | genitive — "of" (possession) |
| `"entity"` | `prathama` | nominative — the subject standing |
| `"intent"` | `vidhi` | imperative — solve-for |
| `"symbol"` | `naama-mudra` | name-seal (label) |
| `"pending-number"` | `asprista-sankhya` | unattached number |
| `"punct"` | `viraam` | pause (`sangati/viraam.om` exists!) |
| `"dvandva"` | `dvandva` | already Sanskrit — keep |
| `"refers-to"` | `naama-pratibodha` | pronoun reference |
| `"paired-with"` | `krama` | ordered pairing |
| `"instance-of"` | `vishesa` | particular of a universal |

**Migration strategy**: Rename edge string literals in pipeline tantras and tests.
Ring dimensions get Sanskrit canonical names. The q-* labels become aliases.
This is a mechanical find-replace across:
- `emit-triples.tantra`
- `avrti-refine.tantra`
- `match-mantra.tantra`
- `materialize-question-graph.tantra`
- all test files under `brahman/yantra/tests/`

Gate: 83 pass / 11 fail must be maintained.

---

## kramanusara + apeksha — General Derivative

`kramanusara` is NOT "rate of change with respect to time". It is the general
derivative operation. `sangati/parampara/kramanusara.om`:
```
"krama-swarupa apeksha-yukta"
shabda derivative / rate-of-change-of-one-quantity-with-respect-to-another
```

**kaala ≠ time**. `sangati/kaala.om`:
```
"brahma-swarupa spanda-kriya"
"prakaasha-poorva thaalam-janaka"
```
Kaala IS the ordering principle — the pulse that becomes sequence. Time (thaalam,
measured in seconds) is ONE manifestation of kaala. Kaala generates thaalam the
way spanda generates rhythm.

The full map:

| X | apeksha | kramanusara(X, apeksha) |
|---|---|---|
| displacement | physics-time (thaalam) | velocity (vega) |
| velocity | physics-time | acceleration (vivartana) |
| angle (kona) | physics-time | angular-velocity |
| entropy | temperature (ushna) | dS/dT (Clausius) |
| potential | position (kshetra) | electric field |
| force | area | pressure |
| probability | itself | information content |
| value (finance) | physics-time | interest rate |

**Partial derivative** already exists: `kosha/math/calculus/operations/partial-derivative.om`
with `"kramanusara-swarupa"` + `"apeksha-yukta"` + `"sthira-apeksha-yukta"`.
This confirms the general form: kramanusara(X, apeksha=Y, others=sthira).

**Bug in `time.om`** line 9:
> "every kramanusara in physics divides by time unless otherwise stated"

Should be:
> "every kramanusara in MECHANICS has apeksha=physics-time by default.
>  In thermodynamics: apeksha=ushna (temperature).
>  In electromagnetism: apeksha=kshetra (position).
>  The apeksha is always explicitly declared on the kosha node."

**All existing kinematics kramanusara edges should declare `sthira-apeksha` explicitly**
— `sthira-apeksha.om` itself says they "implicitly" use it. Make it explicit.

---

## Logic and Math — Sanskrit Equivalents

The visheshanam ring IS already a type theory and a category. The 10 core dimensions
ARE the type constructors and morphisms.

### Propositional Logic

| Symbol | Sanskrit | Node |
|---|---|---|
| ⊤ (true) | `satya` | grounded in kosha |
| ⊥ (false/provisional) | `mithya` | ungrounded — not absolute false |
| ¬ syntactic | `pratishedha` | `sangati/pratishedha.om` — grammatical denial |
| ¬ semantic | `pratipaksha` | `visheshanam-pratipaksha` — involutive, group inverse |
| ∧ (AND) | `dvandva` / `yuktu` | `visheshanam-yuktu` = ring-op:add |
| ∨ (OR) | `vikalpa` | `grammar/conj-or.om` |
| → (implies) | `janya → phala` | dual pair: `visheshanam-janya` dual:phala |
| ↔ (iff) | `abheda` | `visheshanam-abheda` symmetric+transitive+congruence |
| ⊢ (proves) | `siddha` | `visheshanam-siddha` antisymmetric |
| ⊨ (models/witness) | `drishthanta` | `visheshanam-drishthanta` antisymmetric |

Note: `pratishedha` ≠ `pratipaksha`.
- `pratipaksha`: hot ↔ cold — both exist, semantic opposition (ring group inverse)
- `pratishedha`: not-hot — the state is grammatically denied, shunya-abheda

### Predicate Logic

| Symbol | Sanskrit | Note |
|---|---|---|
| ∀x.P(x) | `sarva-vishesa` | every particular of a universal |
| ∃x.P(x) | `eka-drishthanta` | one witness/example suffices |
| x ∈ S (closed) | `amsha` | exhaustive partition membership |
| x ∈ S (open) | `vishesa` | extensional IS-A, always additive |
| x : T (type) | `x vishesa T` | x is a particular of type T |

### Set Theory

| Symbol | Sanskrit | Note |
|---|---|---|
| S (set) | `vrnda` | `sangati/vrnda.om` — the gathering |
| ∅ | `shunya` | empty / zero |
| A ∪ B | `dvandva-vrnda` | union as dvandva of gatherings |
| A ∩ B | `sandhi` | the meeting point |
| Aᶜ | `pratipaksha-vrnda` | complement via involution |
| A ⊆ B | `amsha-swarupa` | A is a sub-gathering of B |
| 𝒫(A) | `vrnda-vrnda` | gathering of gatherings |

### Category Theory — the visheshanam ring IS this

| Concept | Sanskrit | In ring? |
|---|---|---|
| Category | `varga` | yes |
| Object | any node | yes |
| Morphism | `kriya` | `visheshanam-kriya` ring-op:mul composable:yes |
| Identity morphism | `swarupa` | `visheshanam-swarupa` ring-op:mul-identity |
| Composition | `krama` | composable:yes on kriya |
| Functor | `anuvada` | `sangati/anuvada.om` — carrying structure across |
| Adjunction L ⊣ R | `janya ⊣ phala` | dual:phala on janya, dual:janya on phala |
| Limit | `seema` + `abhisarana` | `kosha/math/calculus/limit.om` |
| Initial object | `purna` | complete/full |
| Terminal object | `shunya` | empty/zero |

The visheshanam ring is a **graded ring** (`graded-ring-janya` on `visheshanam-sthita`).
The filtration depth runs: sangati → kosha → bhasha → mantra → yantra.
The `visheshanam-ring.om` node IS the ring of morphisms in the knowledge graph category.

### Calculus

| Symbol | Sanskrit | Node |
|---|---|---|
| d/d(apeksha) | `kramanusara` | `sangati/parampara/kramanusara.om` apeksha-yukta |
| ∂/∂x | `kramanusara` + sthira others | `partial-derivative.om` — already exists |
| ∫ | `sama-kalana` | `sangati/sama-kalana.om` — gathering into wholeness |
| lim | `seema` | `kosha/math/calculus/limit.om` |
| ∇f (gradient) | `prasarana` | directed outward flow |
| ∇· (divergence) | `abhisarana` | convergence/divergence |
| ∇× (curl) | `avrti` | spiral/rotation — avrti IS curl in continuous setting |
| ∇² (Laplacian) | `sama-kalana` of `prasarana` | |

### Inheritance — vishesa vs amsha

Two distinct IS-A relations, already in use throughout:

| | `vishesa` | `amsha` |
|---|---|---|
| Meaning | particular of a universal | member of a constituted set |
| Openness | **open** — more can always join | **closed** — exhaustive partition |
| Example | `dog vishesa animal` | `prathama-vibhakti amsha vibhakti` |
| Walk | follows chain upward | enumerates all members of closed set |

`dhatu-yuktu` enables runtime inheritance walks. `filtration.om` gives the lattice.

---

## New Sangati Nodes Needed

Two nodes discussed this session that do not yet exist as standalone nodes:

### `artha-viveka.om`

The act of discerning artha from dhvani. This is what BQG + sandhi-viveka together perform.

```
sangati artha-viveka

  "bhasha-swarupa-kriya viveka-sthita"
  "artha-dhvani-viveka-swarupa"
  "dhvani-rahita artha-graha-kriya"
  "sphoTa-siddha anuvada-poorva"
  -- the act of discerning artha from dhvani
  -- separates what is pointed-at (artha) from the vehicle that points (dhvani)
  -- artha-lossless: meaning is preserved, dhvani is dissolved
  -- precedes anuvada: artha-viveka extracts, anuvada re-expresses

shabda artha-viveka / the-discernment-that-separates-meaning-from-its-surface-vehicle

done
```

### `sphoTa.om`

Currently only appears as an attribute (`sphoTa-swarupa`). Needs its own node.

```
sangati sphoTa

  "vak-sthalam-sthita"
  "artha-swarupa dhvani-rahita"
  "vakya-yukta pada-atita"
  -- the unitary meaning-unit that arrives whole at sentence level (Bhartrhari)
  -- not assembled word-by-word — present all at once when dhvani is heard
  -- the Sanskrit inner form IS sphoTa made structurally explicit
  -- dhvani is the path; sphoTa is the destination

shabda sphoTa / the-unitary-meaning-that-arrives-whole-not-assembled-from-parts

done
```

---

## Fixes Required in Existing Nodes

### `brahman/kosha/physics/time.om`
Fix line 9 comment: "every kramanusara in physics divides by time unless otherwise stated"
→ "kramanusara in mechanics has apeksha=physics-time by default. In thermodynamics
   apeksha=ushna. In electromagnetism apeksha=kshetra. Apeksha must be declared explicitly."

### `brahman/kosha/physics/thermodynamics/quantities/entropy.om`
Currently only has `"disorder-abheda kshaya-sthita"`. Missing:
- `"vrnda-sankhya-janya"` — S = k·ln(W), W = number of microstates (vrnda-sankhya)
- `"sankshepa-pratipaksha"` — entropy IS inverse compression (max entropy = min compressibility)
- `"ushna-apeksha-kramanusara"` — dS/dT is the thermodynamic kramanusara
- `"kaala-rahita-swarupa"` — entropy's definition is atemporal; kaala gives its DIRECTION

### `brahman/kosha/physics/thermodynamics/thermodynamics-varga.om`
Fix the note on `"kaala-yukta"`: "entropy increases with time (second law is time-directional)"
→ "kaala gives the DIRECTION of entropy change (second law: dS/dt ≥ 0) but entropy's
   definition S = k·ln(W) is atemporal. kaala is the ordering principle, not the apeksha."

### All kinematics kramanusara edges
Make `sthira-apeksha` explicit on velocity.om, acceleration.om, jerk.om, angular-velocity.om,
angular-acceleration.om. Currently `sthira-apeksha.om` says these "implicitly" use it.
Add `"sthira-apeksha-sthita"` to each.

---

## Implementation Phases

### Phase S0 — New sangati nodes (additive, no regressions)
1. Create `brahman/sangati/artha-viveka.om`
2. Create `brahman/sangati/sphoTa.om`
3. Fix `time.om`, `entropy.om`, `thermodynamics-varga.om` comments/slokas
4. Add `sthira-apeksha-sthita` to kinematics kramanusara chain nodes
5. Gate: 83/11 maintained

### Phase S1 — Sanskrit canonical edge names ✅ DONE (2026-03-13)
Final rename map (all in 58 tantra/test files):
- `"active"` → `"satya"` (sangati/mula/satya.om)
- `"owner"` → `"shashthi-vibhakti"` (sangati/grammar/vibhakti/shashthi-vibhakti.om)
- `"entity"` → `"prathama-vibhakti"` (sangati/grammar/vibhakti/prathama-vibhakti.om)
- `"intent"` → `"vidhi-kaala"` (sangati/grammar/kaala/vidhi-kaala.om)
- `"value"` → `"sankhya"` (kosha/sankhya.om)
- `"unit"` → `"matra"` (sangati/matra.om — already in ring)
- `"symbol"` → `"naama-mudra"` (sangati/vak/naama-mudra.om)
- `"pending-number"` → `"asprista-sankhya"` (new: sangati/prashna/asprista-sankhya.om)
- `"punct"` → `"viraam"` (sangati/viraam.om)
- `"dvandva"` → `"dvandva"` (sangati/grammar/samasa/dvandva.om — unchanged)
- `"refers-to"` → `"naama-pratibodha"` (new: sangati/vak/naama-pratibodha.om)
- `"paired-with"` → `"krama"` (sangati/parampara/krama.om — already in ring)
- `"instance-of"` → `"vishesa"` (vishesa-yukta already in ring — no new node needed)
- 12 redundant q-* prashna nodes deleted; visheshanam-ring.om updated
- Gate: 83/11 maintained

### Phase S1.5 — Kosha expansion via PPR

**The core insight**: artha-viveka converts semantic meaning to structural meaning. The meaning
of a word IS its edges in the kosha. Once a word resolves to satya, its full structural meaning
is available — but we must pull it into the question graph selectively.

**Why selective?** A kosha node like `mass` has dozens of edges. Pulling all of them into every
question would create noise and false connections. What we want is: the edges most relevant to
THIS question, given what we already know.

**The mechanism: PPR as relevance filter**

```
satya nodes in question graph → PPR seeds
    ↓  PPR over kosha graph
ranked kosha nodes (by relevance to current question context)
    ↓  threshold filter
relevant kosha nodes pulled into question graph as expansion context
    ↓  next avrti pass runs with wider context
more mithya words resolve
    ↓  new satya nodes → new PPR seeds → re-run
fixpoint = sphoTa
```

**Adaptive threshold:**
- Start with a high threshold (only pull top-ranked nodes)
- If mithya words remain unresolved after a pass → lower threshold → run again
- More context admitted with each iteration until mithya resolves or threshold hits floor
- Floor = genuine `asprista`: even full kosha context cannot resolve this word

**Domain boundary constraint (hard, not soft):**

The PPR walk is explicitly bounded by domain. Three directions:

```
UPWARD   — allowed freely
  mass → linear-force-varga → physics-varga → kosha (full generalization chain)
  walk vishesa/amsha edges upward: always permitted

DOWNWARD — allowed only within domains already established by the question
  mass → initial-mass, gravitational-mass  (avastha/specializations — allowed)
  physics-varga → linear-force-varga       (question owns this domain — allowed)
  physics-varga → thermodynamics-varga     (question does NOT own this — BLOCKED)

LATERAL  — blocked unconditionally
  mass → entropy: both are physics, but different vargas — BLOCKED
  velocity → electric-field: BLOCKED
  even with high PPR score — the hard boundary overrides
```

The rule: **go up freely, come down only into domains the question already owns.**

This is NOT just a soft PPR threshold. It is an explicit structural constraint: when descending
from a shared ancestor, only follow paths to vargas that contain at least one of the question's
seed satya nodes. Any path that would enter an unseeded varga is pruned before PPR scoring.

**What PPR surfaces from `mass` + `velocity` seeds (after boundary filter):**
- `kinetic-energy` — high rank (direct implication chain via KE mantra, same domain)
- `momentum` — medium rank (p = mv, linear-motion-varga, domain already owned)
- `force` — medium rank (F = ma, linear-force-varga, domain already owned)
- `displacement` — lower rank (via kramanusara chain, linear-motion-varga, owned)
- `entropy` — BLOCKED (thermodynamics-varga, not seeded by question)

**Effect on mithya resolution**: mithya words are now resolved against the PPR-ranked context,
not just the raw kosha. `"KE"` alone is mithya; but with `kinetic-energy` ranked #1 in the
expansion, `"KE"` resolves via its shabda key. `"speed"` alone is mithya; with `velocity`
ranked high from a mechanics context, `"speed"` resolves via `velocity`'s word: key.

**Effect on match-mantra**: at fixpoint, the mantra that best explains the satya nodes is
already surfaced by PPR — it has the highest activation from the question seeds. match-mantra
reads the top-ranked mantra from the PPR output. It is no longer a separate search.

**satya triple is reflexive** ✅: `[mass, satya, mass]` — subject = object = kosha node.
`walk "mass" "satya"` returns `mass` (the kosha node), from which you can continue walking
into all its kosha structure. `nth tri 2` gives a live kosha node name, directly usable as
a PPR seed. Done: emit-triples, avrti-refine, find-context updated; all tests updated.

**New tantra**: `kosha-expand.tantra`
```
inputs:
  question-graph  list    -- current question graph
  threshold       float   -- PPR cutoff (adaptive)
outputs:
  expanded-graph  list    -- question graph + pulled-in kosha context
```

**Files modified** (reflexive satya — done ✅):
- `brahman/yantra/emit-triples.tantra` — `[node, satya, node]` reflexive ✅
- `brahman/yantra/avrti-refine.tantra` — compound satya triples reflexive ✅
- `brahman/yantra/find-context.tantra` — check simplified to `(eq edge "satya")` ✅
- All ~57 test files updated (input triples + 2 formalization assertion checks) ✅

**Files to create** (kosha-expand — next):
- New: `brahman/yantra/kosha-expand.tantra`
- `brahman/yantra/avrti-refine.tantra` — call kosha-expand between passes (or as a new pass)

**Gate**: 124/11 maintained. kosha-expand is additive — it adds context, does not remove triples.

---

### Phase S1.6 — English grammar nodes → Sanskrit grammar roots

The English bhasha grammar nodes must explicitly point to the Sanskrit grammatical concepts
they EXPRESS. Currently most use flat English-layer roles (`role:possession`, `role:grammar`).
The artha-viveka principle requires: the English surface word dissolves; what remains is the
Sanskrit grammatical relation. That connection must be explicit in the node structure.

**Pattern**: each bhasha English grammar node should carry `"X-sthita"` where X is the Sanskrit
grammar node it expresses. The pipeline (avrti, sandhi-viveka) then works with the Sanskrit
concept directly, not the English word role.

---

#### Missing: shashthi-vibhakti connections (possession signals)

These four nodes signal the genitive/possessive relation in English. Each IS `shashthi-vibhakti`
expressed in English surface form. Add `"shashthi-vibhakti-sthita"` to each:

| File | Word | Currently | Add |
|---|---|---|---|
| `verb-has.om` | has | `role:possession` | `"shashthi-vibhakti-sthita"` |
| `verb-have.om` | have | `role:possession` | `"shashthi-vibhakti-sthita"` |
| `prep-with.om` | with | `role:possession` | `"shashthi-vibhakti-sthita"` |
| `prep-of.om` | of | `role:grammar` | `"shashthi-vibhakti-sthita"` + fix role to `possession` |

Note on `prep-of.om`: currently `role:grammar` so R8 (ownership detection) never fires on
"mass of the ball". Must be `role:possession` with the context-dependent guard already planned
in graph-formalization-plan.md Step 6: if followed by a known entity → possession; otherwise
structural (e.g. "square root of").

---

#### Missing: pronoun nodes (naama-pratibodha signals)

These do not exist yet. Create in `brahman/bhasha/english/grammar/`:

| File | Word | Sanskrit root | Role |
|---|---|---|---|
| `pronoun-its.om` | its | `naama-pratibodha` | `role:pronoun` singular |
| `pronoun-their.om` | their | `naama-pratibodha` | `role:pronoun` plural |
| `pronoun-it.om` | it | `naama-pratibodha` | `role:pronoun` singular neuter |

Each should carry:
- `"naama-pratibodha-sthita"` — connects to the Sanskrit grammar concept
- `"eka-vachana-sthita"` or `"bahu-vachana-sthita"` — number
- `role:pronoun` in shabda — so avrti can detect pronoun signals

---

#### Missing: vibhakti connections on prepositions

Prepositions are English expressions of Sanskrit vibhakti (case) relations. Each preposition
IS a vibhakti expressed as a separate word (Sanskrit expresses this through noun inflection).
Add the vibhakti connection to each:

| File | Word | Vibhakti | Sanskrit case | Add |
|---|---|---|---|---|
| `prep-at.om` | at | saptami | locative — at a point/location | `"saptami-vibhakti-sthita"` |
| `prep-by.om` | by | trtiya | instrumental — by means of | `"trtiya-vibhakti-sthita"` |
| `prep-from.om` | from | panchami | ablative — source/origin | `"panchami-vibhakti-sthita"` |

`prep-per.om` already has `"matra-sthita"` (unit/rate relation) — correct as-is.
`prep-over.om` already has `"division-sthita"` — correct as-is.

---

#### Borderline: article-the → naama-pratibodha

`article-the.om` signals a definite back-reference: "the ball" = the ball already established.
This is in the naama-pratibodha family (recognising something already named) but weaker than
a pronoun — it carries the noun explicitly. Lower priority. Add when S2 (sandhi-viveka) needs it.

---

#### Already correctly connected ✓

| Node | Connected to |
|---|---|
| `bhuta/vartamana/bhavishya/vidhi/sambhavana-kaala.om` | `dhatu X-sthita` ✓ |
| `kartari/karmani/bhave-prayoga.om` | `dhatu X-sthita` ✓ |
| `conj-and.om` | `dvandva-sthita` ✓ |
| `conj-or.om` | `vikalpa-sthita` ✓ |
| `copula-was/were.om` | `bhuta-kaala-sthita` ✓ |
| `copula-is/are.om` | `vartamana-kaala-sthita` ✓ |
| `verb-moves/moving/rotates/rotating.om` | `kartari-prayoga-sthita` ✓ |

---

**Implementation order within S1.6:**
1. Add `shashthi-vibhakti-sthita` to has/have/with + fix prep-of (unblocks R8 graph-based rewrite)
2. Create pronoun nodes its/their/it (unblocks R10 pronoun resolution)
3. Add vibhakti to prep-at/by/from (needed for S2 sandhi-viveka)
4. Gate: 83/11 maintained (all additive)

---

### Phase S2 — sandhi-viveka tantra (new pipeline stage)
A new tantra between BQG and avrti that assigns vibhakti/kala/prayoga to
the raw triple graph. Backwards compatible — adds Sanskrit grammar triples
alongside existing ones.

Key rules:
- Possession signal (`has`/`with`) → mark as `shashthi-vibhakti` context
- Intent signal (`find`/`calculate`) → mark as `vidhi-kaala`
- Concept following intent → `chaturthi-vibhakti` (dative, purpose = "for")
- Entity preceding possession → `prathama-vibhakti` (nominative)
- Tense signals: `was` → `bhuta-kaala`, `is`/`are` → `vartamana-kaala`

### Phase S3 — Tense → avastha synthesis
In avrti-refine: `bhuta-kaala` signal in context → auto-synthesize `initial-X`
compound for next active concept. `bhavishya-kaala`/`vartamana-kaala after was`
→ `final-X`. This removes dependence on explicit "initial"/"final" words.

Currently: "train was moving at 20 m/s and accelerates to 40 m/s" fails because
both bind to same `velocity` node. With kaala signals: bhuta-kaala → initial-velocity,
vartamana-kaala → final-velocity. No collision.

### Phase S4 — anuvada response generation
Use vibhakti structure to generate English output properly:
- `shashthi` → "of" (genitive)
- `prathama` + result → "The X is Y"
- `matra` → unit appended to result
- `vidhi` → answer addresses the question directly

Currently output is just the numeric result. With anuvada: full grammatical sentence.

---

## Relation to Existing Plans

| Plan | Relation |
|---|---|
| `graph-formalization-plan.md` | Phase S1 is the Sanskrit rename of what that plan called q-* dimensions |
| `scene-understanding.md` | Phase S2 (sandhi-viveka) extends the avrti rule table |
| `grammar.md` | The vibhakti/kala/prayoga assignments in S2 use those Sanskrit grammar nodes |
| `composition-pipeline.md` | Phase S4 (anuvada) is the compose-response stage |
| `session-notes.md` | Current baseline 83/11 is the gate for all phases here |

---

## Key Files

### To create
```
brahman/sangati/artha-viveka.om
brahman/sangati/sphoTa.om
brahman/yantra/sandhi-viveka.tantra           (Phase S2)
```

### To modify
```
brahman/kosha/physics/time.om                             fix kramanusara comment
brahman/kosha/physics/thermodynamics/quantities/entropy.om  add vrnda-sankhya, ushna-apeksha
brahman/kosha/physics/thermodynamics/thermodynamics-varga.om  fix kaala-yukta note
brahman/kosha/physics/kinematics/linear/quantities/velocity.om     add sthira-apeksha-sthita
brahman/kosha/physics/kinematics/linear/quantities/acceleration.om  add sthira-apeksha-sthita
brahman/kosha/physics/kinematics/linear/quantities/jerk.om          add sthira-apeksha-sthita
brahman/kosha/physics/kinematics/rotational/quantities/angular-velocity.om
brahman/kosha/physics/kinematics/rotational/quantities/angular-acceleration.om
brahman/yantra/emit-triples.tantra            Phase S1 rename
brahman/yantra/avrti-refine.tantra            Phase S1 rename + S3 tense synthesis
brahman/yantra/match-mantra.tantra            Phase S1 rename
brahman/yantra/materialize-question-graph.tantra  Phase S1 rename
brahman/kosha/yantra/visheshanam/visheshanam-ring.om  Phase S1 canonical names
brahman/yantra/tests/**/*.tantra              Phase S1 rename all edge string literals
```
