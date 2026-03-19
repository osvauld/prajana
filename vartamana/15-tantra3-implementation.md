# 15 — Tantra3 Implementation: Findings and Plan

**What the live graph actually contains, what the 77 xfails actually need,
and the concrete steps to make the om graph drive the pipeline.**

This is the implementation companion to [14-tantra3.md](14-tantra3.md).
That document is the philosophy. This document is the engineering.

---

## What the live graph told us (2026-03-19)

### The numbers

| What | Count |
|------|-------|
| Total nodes in graph | ~2000+ |
| Sangati layer nodes | 308 |
| Mantra nodes (total) | 108 |
| Mantra nodes with janya+phala contracts | 26 |
| Physics-mantra varga members (currently routed) | 23 |
| Mantras with contracts NOT in physics-mantra varga | 4 |
| Nodes with both janya AND phala edges | 109 |
| Phala→janya chain connections traced | 150+ |
| Varga groups | 17 |
| Pratipaksha (inverse) relationships on math ops | 12 |

### What the pipeline currently reads

The pipeline reads a small fraction of the om graph's structure:

| Edge type | Read by pipeline? | Where |
|-----------|------------------|-------|
| satya / mithya | Yes | build-question-graph, avrti-refine |
| sankhya | Yes | sankhya-sparsha, sankhya-bandha, match-mantra |
| matra | Yes | emit-triples, sandhi-bandhana |
| vishesa | Yes | vishesa-bandhana, rashi-viveka |
| shashthi-vibhakti | Yes | vibhakti-shashthi, shashthi-sparsha |
| prathama-vibhakti | Yes | prathama-sparsha, extract-solve-for |
| vidhi-kaala | Yes | extract-solve-for |
| janya | Partially | match-mantra (hardcoded per-mantra) |
| phala | Partially | match-mantra, derive-chain |
| kriya | Partially | execute-math (via shabda math-op) |
| pratipaksha | Yes | invert-math (via shabda) |
| varga | Yes | varga-inheritance boot pass, PPR |
| swarupa | Partially | kosha-expand PPR seeds, varga-inheritance |
| **abheda** | **No** | — |
| **sthita** | **No** | — |
| **siddha** | **No** | — |
| **yukta** (on sangati nodes) | **No** | — |

The bolded rows are entire edge types with rich content that nothing reads.

### Untapped structures

**abheda (equivalence) — 6+ physics concepts have actionable entries:**

```
velocity abheda: [decelerate-to-rest, free-fall, initial-rest,
                  relative-velocity, angular-velocity, laya, vega]
mass abheda:     [moment-of-inertia, link-mass, ghana, samskaara]
force abheda:    [centripetal-force, torque, karma]
energy abheda:   [path-energy, work, temperature, spanda, vibration]
frequency abheda: [thaalam, avrti, angular-velocity, swara]
momentum abheda: [angular-momentum, samskaara]
```

These declare equivalences. `initial-rest` is abheda of velocity — it IS
a velocity (specifically: zero). If the pipeline read abheda, then "from
rest" in a sentence could resolve to `initial-velocity = 0` by recognizing
`initial-rest` as a velocity-abheda with implied sankhya of zero.

**sthita (context) — declares domain membership:**

```
velocity sthita:     [krama, sthira-apeksha]
mass sthita:         [kshetrajna, niyama]
momentum sthita:     [krama, kshetrajna, niyama]
acceleration sthita: [niyama, sthira-apeksha]
work sthita:         [niyama]
frequency sthita:    [spanda, niyama]
```

These declare where concepts live. A concept with `sthita: niyama` is
law-bound — it participates in conservation laws. A concept with
`sthita: krama` is sequence-dependent — it has a time dimension. The
pipeline could use sthita for domain routing instead of the hardcoded
`walk-in "physics-mantra" "varga"`.

**The janya/phala DAG — 150+ traced connections:**

The phala of one node flows into the janya of another. Selected chains:

```
velocity-mantra --[velocity]--> kinetic-energy-mantra
velocity-mantra --[velocity]--> momentum-mantra
velocity-mantra --[velocity]--> angular-velocity-mantra
acceleration-mantra --[acceleration]--> velocity-mantra
frequency-mantra --[frequency]--> photon-energy-mantra
period-mantra --[period]--> frequency-mantra
newton-second-law-motion --[force]--> work-mantra
falling --[velocity]--> kinetic-energy-mantra
```

This IS derive-chain's logic as graph structure. Today derive-chain
searches by trying each mantra. With the DAG, it walks backward from
the solve-for concept to find the producer, checks what the producer
needs, recurses. Search becomes deduction.

**The logic layer — complete but unread:**

```
modus-ponens [mantra]:  janya=[implication], swarupa=[inference]
inference [kosha]:      swarupa=[inversion, modus-ponens, substitution]
proposition [kosha]:    yukta=[satya, viveka]
proof [kosha]:          phala=[theorem], yukta=[satya, niyama, krama]
theorem [kosha]:        yukta=[satya], siddha=[niyama]
```

And the five-step proof:
```
pratijnaa [sangati]:  abheda=[assertion], kriya=[lekhana], phala=[visarjana]
pramana [sangati]:    janya=[seva], phala=[samskaara], kriya=[lekhana]
pratyaksha [sangati]: abheda=[darshana, sparsha, direct-perception]
nigamana [sangati]:   janya=[om-parser], phala=[avrti]
```

The mechanism for syllogism — swarupa chain + yukta inheritance — is
structurally identical to what the pipeline does for physics. Walking
`swarupa` IS the IS-A relation. Inheriting `yukta` along that chain IS
modus-ponens. The tantra3 generic walker handles both domains with the
same code.

**Count mantras — orphaned from pipeline:**

```
count-add-mantra [mantra]: janya=[count1, count2] → phala=[count-total]
                           kriya=[count-add-expr]
count-sub-mantra [mantra]: janya=[count1, count2] → phala=[count-remaining]
                           kriya=[count-sub-expr]
```

These have full janya/phala/kriya contracts but are not in `physics-mantra`
varga. The pipeline never finds them. Om-driven matching would find them
automatically — they are mantra nodes with contracts, same as any physics
mantra.

**Everyday concepts — gaps in kosha:**

```
width:         NOT IN GRAPH
rectangle:     NOT IN GRAPH
proportional:  NOT IN GRAPH
twice:         NOT IN GRAPH
speed:         exists but no janya/phala (not a mantra)
distance:      exists but no formula relationship declared
area:          exists but no formula relationship declared
```

For `test_train_distance` and `test_rectangle_area` to work, we need:
- `distance-mantra.om`: janya=[speed, time] → phala=[distance]
- `area-mantra.om`: janya=[length, width] → phala=[area]

With tantra3, writing these om files IS writing the mantras. No tantra
code needed.

---

## The 77 xfails — classified by what unblocks them

### Category A — Om-driven match-mantra (11 tests)

All from `test_match_decomp.py`. These tests literally ask for the
decomposed match-mantra sub-tantras:

| Sub-tantra | Tests | What it does |
|-----------|-------|-------------|
| `scope-vps` | 3 | Given entity, return only that entity's owned val-pairs |
| `mantra-select` | 3 | Given solve-for, return candidate mantras from om graph |
| `forward-match` | 2 | Check if all janya are bound, return match |
| `inverse-match` | 2 | Check if phala+all-but-one-janya bound, return inverse match |
| `relative-vps` | 2 | For two-entity mantras, return paired val-pairs |

**Tantra3 approach:** `mantra-select` becomes `om-phala`/`om-janya` walk.
`forward-match` becomes: check all `om-janya m` are in bound-concepts.
`inverse-match` becomes: check `om-phala m` is in bound + all-but-one janya.
These are the same generic walker applied differently.

**Unblocked by:** Phase 2 (om-driven match-mantra rewrite).

### Category B — Count/everyday mantras not routed (8 tests)

| Test | What's missing |
|------|---------------|
| `test_birds_subtraction` | count-sub-mantra not found (not in physics-mantra) |
| `test_balls_addition` | count-add-mantra not found (not in physics-mantra) |
| `test_proportional_ke_mass_doubled` | proportional reasoning — no mechanism |
| `test_proportional_ke_velocity_doubled` | same |
| `test_train_distance` | distance-mantra doesn't exist |
| `test_rectangle_area` | area-mantra doesn't exist |
| `test_total_kinetic_energy_resolves` | "total" + compound → needs count+physics bridge |
| `test_total_momentum_resolves` | same |

**Unblocked by:** Phase 2 (om-driven matching finds count-mantras automatically)
+ new `.om` files for distance-mantra, area-mantra + abheda reading for
proportional reasoning.

### Category C — Collocation / verb-as-signal (15 tests)

| Gap | Tests | What's needed |
|-----|-------|-------------|
| Verb binding | 6 | "moves at", "moving at" → velocity binding signal |
| "from rest" | 2 | initial-rest abheda → initial-velocity = 0 |
| "total X" | 2 | total as summation signal over dvandva entities |
| Color as entity qualifier | 2 | "red ball", "blue ball" → entity distinction |
| Field strength collocation | 3 | "electric field strength", "magnetic field strength" → concept resolution |

**Verb binding** — "moves at 5 m/s" should bind velocity. The om graph has
`velocity abheda: [vega]` and the bhasha layer has verb entries. The pipeline
needs a sub-tantra in avrti-refine that reads verb-concept associations.
Not directly tantra3 (this is linguistic, not structural) but tantra3 makes
the concept resolution generic once the signal is detected.

**"from rest"** — The om graph already has `initial-rest` as velocity-abheda.
Reading abheda during avrti-refine would let `initial-rest` resolve to
`initial-velocity` with implied sankhya=0. This IS tantra3 — the om graph
declares the equivalence, the pipeline reads it.

**Color qualifier** — "red ball" and "blue ball" need color as an entity
distinguisher, not a concept. Needs a bhasha-layer understanding of adjective
position.

**Unblocked by:** Phase 3 (abheda reading) + new verb-binding sub-tantra +
kosha entries for collocations.

### Category D — Logic / syllogism (8 tests)

| Test | What it needs |
|------|-------------|
| `test_syllogism_cats_breathe` | IS-A chain: cat→mammal→breather |
| `test_syllogism_dogs_mammals` | IS-A chain: dog→mammal |
| `test_syllogism_from_kosha_electron_is_particle` | swarupa walk: electron→particle |
| `test_transitive_greater_than` | transitive ordering |
| `test_transitive_mass_ordering` | transitive mass comparison |
| `test_transitive_chain_three_steps` | 3-step transitive chain |
| `test_more_apples_or_oranges` | count + comparison |
| `test_syllogism_plus_count` | syllogism + arithmetic |

**The mechanism exists.** Syllogism = swarupa chain walk + yukta inheritance.
"All cats are mammals" = `[cat, swarupa, mammal]`. "All mammals breathe" =
`[mammal, yukta, breathing]`. Derive: `[cat, yukta, breathing]` by walking
swarupa then inheriting yukta. This is structurally identical to varga-
inheritance (which already works).

**What's missing:** Common-sense kosha nodes (`cat`, `mammal`, `breathing`,
`dog`, `apple`, `orange`). The mechanism fires automatically once the nodes
exist — the om graph's swarupa/yukta/abheda edges encode the relationships,
tantra3's generic walker reads them.

For `electron_is_particle`, the graph already has `electron` and `particle`.
It needs `[electron, swarupa, particle]` to be explicitly declared (or
derivable). Currently `particle swarupa: [vrnda]` but electron's swarupa
chain doesn't include particle.

**Unblocked by:** Phase 4 (swarupa-chain walking) + common-sense kosha files.

### Category E — Multi-entity / session (12 tests)

| Sub-group | Tests | What's needed |
|-----------|-------|-------------|
| Session entity carry | 3 | prathama/shashthi triples in se_graph |
| Two entities across turns | 3 | same |
| Electron + field | 1 | multi-entity session + field concept |
| Dvandva collection | 1 | two instances of same concept |
| Per-entity computation | 2 | scope-aware mantra firing |
| Position ownership | 1 | bindu as owned vector |
| Full simulation scene | 1 | all of the above |

**Not directly tantra3.** These need Gap 2 (session entity structure) which
is a socket.ml + session-anuvada change. But tantra3 makes the scope-aware
matching cleaner — `om-sthita` on interaction mantras declares slot structure.

**Unblocked by:** Gap 2 implementation (separate from tantra3).

### Category F — Viveka / computed comparison (6 tests)

| Test | What's needed |
|------|-------------|
| `test_which_has_more_ke_from_mass_velocity` | compute KE for both, then compare |
| `test_which_has_more_momentum` | compute momentum for both, then compare |
| `test_which_has_more_ke_shows_both_computations` | reasoning emission for viveka |
| `test_rank_three_balls_by_mass` | 3-way comparison |
| `test_which_has_more_ke_two_seeks` | viveka with two solve-fors |
| `test_viveka_computed_quantity_two_knows` | viveka result as known fact |

Viveka already partially works for direct values. These tests need
**compute-then-compare**: fire the mantra for each entity first, then
compare the phala values. The om graph declares: `viveka: phala → [eka]`,
`kriya → [eka-aneka]`. The viveka walker computes per-entity, then
selects one from many.

**Unblocked by:** Entity-scoped computation (working) + per-entity mantra
firing in viveka path + reasoning emission for the comparison.

### Category G — Composed expressions (1 test)

`test_gravitational_force` — needs gravitational constant G auto-supplied
+ r² composition in expression graph. P8f Phase B.

**Unblocked by:** Expression subgraph implementation.

### Category H — Reasoning emission (3 tests)

Natural language answer formatting for composed sentences. Pipeline-level.

**Unblocked by:** emit-reasoning improvements.

---

## OCaml changes

### New primitives to add (~40 lines)

Add to `yantra_eval_primitives.ml`:

```ocaml
(* om-contract: node-name → [[janya...], [phala...], [kriya...],
                              [yukta...], [sthita...], [swarupa...]] *)
| "om-contract" ->
    let node_name = eval_str 0 in
    let dedup rel =
      let targets = Proof_graph.edges_of k node_name in
      let vish = Proof_graph.visheshanam_of_string rel in
      match vish with
      | None -> VList []
      | Some v ->
        let seen = Hashtbl.create 8 in
        VList (List.filter_map (fun edge ->
          if edge.relation = v && edge.source = node_name
             && not (Hashtbl.mem seen edge.target) then begin
            Hashtbl.replace seen edge.target true;
            Some (VNode edge.target)
          end else None
        ) targets)
    in
    Some (VList [dedup "janya"; dedup "phala"; dedup "kriya";
                 dedup "yukta"; dedup "sthita"; dedup "swarupa"])
```

Also add individual shortcuts for readability in tantras:

```ocaml
| "om-janya"   -> Some (dedup_walk "janya")
| "om-phala"   -> Some (dedup_walk "phala")
| "om-kriya"   -> Some (dedup_walk "kriya")
| "om-yukta"   -> Some (dedup_walk "yukta")
| "om-sthita"  -> Some (dedup_walk "sthita")
| "om-swarupa" -> Some (dedup_walk "swarupa")
| "om-abheda"  -> Some (dedup_walk "abheda")
```

Register arities:

```ocaml
r "om-contract" 1;
r "om-janya"    1;
r "om-phala"    1;
r "om-kriya"    1;
r "om-yukta"    1;
r "om-sthita"   1;
r "om-swarupa"  1;
r "om-abheda"   1;
```

### What can move OUT of OCaml

**`find-context` → tantra2 scan.** Currently a hardcoded OCaml function in
`yantra_eval_primitives.ml`. It tracks `active-concept` and `pending-number`
through the triple stream — this is a scan with two state variables. Could
be a tantra2 scan block. ~50 lines of OCaml → ~20 lines of tantra2.

**Session binding logic.** `remember-bindings` and `session-bindings` in
`yantra_pipeline_ops.ml` touch `eval_ctx` directly. The ctx access must stay
in OCaml, but the binding merge logic (what to store, deduplication, concept
name resolution) could move to a tantra that calls thinner primitives:
- `session-get-bindings` → returns raw binding list
- `session-put-binding name value` → stores one binding
The policy (which concepts to remember, how to resolve shashthi-vibhakti
subjects) moves to `session-anuvada.tantra2`.

**Tantra dispatch fallback.** The `_ ->` case in `yantra_pipeline_ops.ml`
(env lookup + tantra-by-name dispatch + arg binding) is 25 lines that could
be simplified. The arg-binding loop manually matches `t.t_inputs` to `args`
— this is what `eval_tantra` already does. The fallback could call
`eval_tantra` directly instead of reimplementing arg binding.

### What MUST stay in OCaml

| Module | Why |
|--------|-----|
| `proof_graph.ml` (653 lines) | Core graph data structure, CSR materialization, PPR |
| `yantra_eval.ml` (296 lines) | Eval engine — expression evaluator, scan engine |
| `yantra_ops.ml` (509 lines) | String/list/math/boolean primitives |
| `yantra_eval_primitives.ml` (997 lines) | Graph traversal primitives (walk, emit, ppr) |
| `yantra_tantra_file2.ml` (932 lines) | Layer 2 parser |
| `om_parser.ml` (372 lines) | .om file parser, compound decomposition |
| `socket.ml` (699 lines) | Socket server, session management |

Total OCaml that must remain: ~4400 lines. The tantra3 changes add ~40
lines and potentially remove ~80 (find-context + binding policy migration).

---

## The implementation phases (revised after performance analysis)

The original plan had 6 phases. The performance data showed that 80% of
test time is inside `anuvada-ganana` — not in any single sub-stage but in
the orchestration overhead. Chain derivation is 1.7× slower than simple
calls (371ms vs 220ms) but only 16% of pipeline time. The base pipeline
cost of 220ms per call across 102 simple one-shot calls (18.0s / 45% of
total time) is where improvements matter most.

This led to three structural merges:

1. **Derive-chain rewrite merged into Phase 2.** If `mantra-select`
   already walks om-phala to find the producer, derive-chain becomes
   "call mantra-select for each missing janya, recurse." Same structural
   change, not a separate rewrite.

2. **Domain routing merged into Phase 2.** Removing the `physics-mantras`
   filter IS domain routing — once match-mantra discovers mantras by
   walking om-janya/om-phala from any mantra-layer node, count-mantras
   and future domains are found automatically. One line removal, not a
   separate phase.

3. **Phase 3 (abheda) moved before Phase 4 (syllogism).** Abheda reading
   adds ~1-2ms to the existing fixpoint loop in an already-fast domain
   (physics). Syllogism needs new kosha files AND a new mechanism AND a
   new domain. Lower risk, higher density of xfail payoff first.

### Step 1 — om-contract primitive (foundation)

**What:** Add `om-contract`, `om-janya`, `om-phala`, `om-kriya`, `om-yukta`,
`om-sthita`, `om-swarupa`, `om-abheda` to `yantra_eval_primitives.ml`.

**Lines changed:** ~40 added to primitives, ~8 added to arity registration.

**Tests:** Verify via socket eval:
```python
vy.eval('om-janya "kinetic-energy-mantra"')   # → [mass, velocity]
vy.eval('om-phala "kinetic-energy-mantra"')   # → [kinetic-energy]
vy.eval('om-contract "rashi"')                # → [[sankhya,matra,sambandha],[...],...]
```

**Prerequisite for:** All subsequent steps.

**xfails unblocked:** 0 directly (infrastructure only).

**Performance impact:** None. New primitives, nothing changes in existing
pipeline.

### Step 2 — Om-driven match + derive + domain (merged)

**What:** Rewrite `match-mantra.tantra2` and `derive-chain.tantra2` as a
single coherent change: the matching subsystem reads the om graph instead
of hardcoding edge names and candidate lists.

This merges the old Phases 2, 5, and 6 because they are one structural
change — "the matcher reads om nodes" — applied at three points in the
same subsystem.

**The three changes in one:**

**(a) Candidate discovery (replaces physics-mantras):**

```
-- today: hardcoded domain list
candidates = physics-mantras graph

-- step 2: walk all mantra-layer nodes
all-mantras  = filter (graph-all-nodes) (fn n ->
  eq (node-layer (to-string n)) "mantra")
candidates   = filter all-mantras (fn m ->
  let gives = om-phala (to-string m)
  let needs = om-janya (to-string m)
  (or (member solve-for (map gives to-string))
      (member solve-for (map needs to-string))))
```

This automatically finds `count-add-mantra`, `count-sub-mantra`, and any
future mantra. The `physics-mantras.tantra2` shared tantra becomes dead.
Cross-domain questions work because the filter is structural (om-phala
contains solve-for), not domain-gated.

**(b) Forward/inverse matching (replaces hardcoded janya checks):**

```
-- today: manually check if concepts are bound
-- step 2: read om-janya, check each

forward = filter candidates (fn m ->
  let needs = om-janya (to-string m)
  all needs (fn j -> member (to-string j) bound-concepts))

inverse = filter candidates (fn m ->
  let needs = om-janya (to-string m)
  let gives = om-phala (to-string m)
  (and (member solve-for (map needs to-string))
       (eq (length (filter needs (fn j -> not (member (to-string j) bound-concepts)))) 1)))
```

**(c) Derive-chain as DAG walk (replaces search loop):**

```
-- today: try each mantra, check if it helps, recurse
-- step 2: walk backward from solve-for through om-phala edges

goal = solve-for
producer = first-match candidates (fn m -> member goal (map (om-phala (to-string m)) to-string))
missing = filter (om-janya (to-string producer)) (fn j -> not (member (to-string j) bound-concepts))
-- for each missing: recursively find its producer via om-phala
-- fire chain from leaves to root
```

The 150+ phala→janya connections already traced form the complete
dependency DAG. Walking it is O(depth) where depth is typically 2-3.
Searching is O(23 mantras × multiple attempts).

**Sub-tantras to extract** (matching `test_match_decomp.py`):

| Tantra | Signature | Implementation |
|--------|-----------|---------------|
| `mantra-select` | solve-for → [mantra-nodes] | filter all mantra-layer nodes by om-phala/om-janya |
| `scope-vps` | graph, entity → [[concept, val], ...] | walk entity's shashthi-vibhakti + sankhya |
| `forward-match` | mantra, bound-concepts → match or [] | check all om-janya in bound-concepts |
| `inverse-match` | mantra, bound-concepts, solve-for → match or [] | check om-phala + all-but-one om-janya |
| `relative-vps` | graph, mantra, entities → paired val-pairs | for two-entity mantras |

**xfails unblocked:** 11 (test_match_decomp.py) + 2 (count-mantras auto-found) = **13+**.

**Performance impact:**
- Removes `physics-mantras` tantra call from hot path (~1 tantra dispatch saved)
- Derive-chain: 371ms median → estimated ~250ms (DAG walk instead of search).
  Chain derivation is 16% of pipeline time → saves ~1-2s across full suite.
- Domain routing overhead: zero (it's the absence of a filter, not a new step)
- match-mantra currently 17ms median — may increase slightly due to walking
  all mantra nodes (108) instead of filtered 23, but the walk is just
  `node-layer` + `om-phala` which are <1ms each. Net: ~similar.

### Step 3 — abheda reading in avrti-refine

**What:** New sub-tantra `abheda-viveka` in the avrti-refine sequence that
reads abheda edges to resolve equivalences.

**The mechanism:**

When a word resolves to a concept that has abheda edges pointing to another
concept, and that other concept is a recognized physics quantity with an
implied value:

```
"from rest" → lookup-word "rest" → initial-rest
→ walk "initial-rest" "abheda" → [...] — but initial-rest IS abheda OF velocity
→ walk-in "initial-rest" "abheda" → [velocity]  (initial-rest is abheda of velocity)
→ initial-rest implies: velocity with sankhya = 0, with avastha = initial (bhuta-kaala)
→ emit [initial-velocity, sankhya, 0]
```

More generally: when a satya concept C has `abheda` edges, and one of those
abheda targets is a recognized quantity in the current graph's context,
the abheda acts as a type-qualified alias.

**Specific resolutions this enables:**

| Phrase | Abheda path | Result |
|--------|------------|--------|
| "from rest" | initial-rest → abheda of velocity | initial-velocity = 0 |
| "decelerate to rest" | decelerate-to-rest → abheda of velocity | final-velocity = 0 |
| "free fall" | free-fall → abheda of velocity | initial-velocity = 0, only gravity |

**xfails unblocked:** ~4 (from-rest tests, decelerate tests).

**Performance impact:** Adds one sub-tantra to the avrti-refine fixpoint
loop. Each pass checks satya concepts for abheda edges — one `walk` call
per satya concept per pass. The fixpoint typically converges in 2-3 passes.
With ~5-8 satya concepts per sentence: ~15-24 extra `walk` calls per
pipeline run. Walk calls are <1ms each. **Estimated overhead: +1-2ms per
pipeline call** — well within noise on a 220ms base.

### Step 4 — swarupa-chain walking for syllogism / IS-A reasoning

**What:** A tantra that walks swarupa chains and inherits yukta/abheda edges
along them — structural modus-ponens.

**The mechanism:**

Given a question like "does an electron have mass?":
1. Find `electron` in graph
2. Walk `electron → swarupa → ?` chain: electron → ? (currently no swarupa to particle)
3. At each swarupa ancestor, check if `yukta` contains the queried property
4. If found: the property is inherited

This is the same structural pattern as varga-inheritance (boot pass) but
applied at query time rather than boot time, and for yukta/abheda inheritance
rather than varga membership.

**What's needed in kosha:**

For the syllogism tests to work, we need common-sense kosha entries:

```
-- brahman/kosha/common-sense/taxonomy.om (new file)
kosha cat
  "mammal-swarupa"
  "breathing-yukta living-yukta"
shabda cat / a-small-domesticated-feline
done

kosha mammal
  "animal-swarupa"
  "breathing-yukta warm-blooded-yukta"
shabda mammal / warm-blooded-vertebrate-that-breathes
done

kosha dog
  "mammal-swarupa"
  "breathing-yukta living-yukta"
shabda dog / a-domesticated-canine
done
```

The mechanism is domain-independent. Once the kosha nodes exist, the
swarupa walker handles both "electron is a particle" and "cat is a mammal"
with the same code.

**For the physics case**, `electron` needs:
```
kosha electron
  "particle-swarupa lepton-swarupa"     -- electron IS-A particle, IS-A lepton
  "charge-yukta mass-yukta velocity-yukta"
  ...
```

**xfails unblocked:** up to 8 (syllogism + transitive tests), depending on
how many common-sense kosha entries are authored.

**Performance impact:** New tantra only fires when a question involves IS-A
or categorical reasoning (detected by question-graph structure). Zero impact
on existing physics pipeline path.

---

## New kosha files needed

### For count/everyday tests (Step 2 unlocks routing, these unlock content)

```
-- brahman/kosha/common-sense/everyday-mantras.om (new)
mantra distance-mantra
  "speed-janya physics-time-janya"
  "distance-phala"
  "multiplication-kriya"
shabda distance-mantra / distance-equals-speed-times-time
done

mantra area-mantra
  "length-janya width-janya"
  "area-phala"
  "multiplication-kriya"
shabda area-mantra / area-equals-length-times-width
done
```

Also need `width` as a kosha concept node:
```
kosha width
  "subanta"
  "metre-yukta"
shabda width / the-horizontal-extent-of-a-rectangular-shape
done
```

### For syllogism tests (Step 4)

A small `brahman/kosha/common-sense/taxonomy.om` with `cat`, `dog`,
`mammal`, `animal`, `breathing`, `living` nodes with swarupa/yukta edges.

### For collocation tests (Step 3)

May need `initial-rest` to have an explicit `shabda` entry mapping it to
"rest" or "from rest" in English. Check if `lookup-word "rest"` already
resolves.

---

## The seven unnamed structures — what tantra3 names

`analyze_pipeline.py` found seven recurring structures in tantra2 code
that have no name. Each one is a translation of what the om graph already
declares. Tantra3 names them by eliminating the translation — the om
graph's own names become the code's names. This is the Manipravalam
principle (see 14-tantra3.md).

### Structure 1: `sankhya-sparsha` → om-yukta "rashi"

**16 occurrences** across tantra2. Three separate tantras doing the same
thing three ways:

```
bound-concepts:      graph | where [s, e, o] | and (eq e "sankhya") | collect [s, o]
bound-vals:          reduce graph [[], []] (fn acc kv -> cond (eq e "sankhya") ...)
bound-concept-names: ... | collect (to-string (nth _it 0))
```

Om graph declares: `rashi.om: "sankhya-yukta"` — rashi HAS sankhya.

Tantra3 form: `om-yukta "rashi" → [sankhya, matra, sambandha]`. One
word in the om graph replaces 16 scattered `eq e "sankhya"` checks.

**Tantra3 step:** Step 1 (om-contract primitive enables this reading).

### Structure 2: `shashthi-sparsha` → om-yukta on vibhakti

**43 occurrences** across 11 tantras — the single most repeated pattern:

```
graph | where [s, e, owner] | and (eq e "shashthi-vibhakti")
      | and (eq (to-string owner) (to-string scope-entity)) | collect s
```

Om graph declares: `vakya.om: "shashthi-vibhakti-yukta"`.

Tantra3 form: `shashthi-sparsha graph scope-entity → [owned-nodes]`.
Named after the grammatical operation — shashthi IS the genitive case.

**Tantra3 step:** Step 2 (extracted as a named sub-tantra).

### Structure 3: `iccha-viveka` → om-janya/phala on iccha

**9 occurrences.** `extract-solve-for` + 5 lines of `nth` destructuring
repeated in `anuvada-ganana`, `match-mantra`, `session-anuvada`:

```
sf-result    = extract-solve-for graph
has-intent   = nth sf-result 0
solve-for    = nth sf-result 1
scope-entity = nth sf-result 2
```

Om graph declares: `iccha.om: "karma-janya" "ahara-phala" "sva-dharana-kriya"`.
Iccha takes karma (what is to be done), produces ahara (direction).

Tantra3 form: `iccha-viveka graph → [has-intent, solve-for, scope]`.
The name IS the operation: discrimination of intention.

**Tantra3 step:** Step 2 (rename + collapse into the match rewrite).

### Structure 4: `pramana-bandha` → om on pramana

**4 occurrences.** 20 lines scattered across `anuvada-ganana`:

```
result-triples = cond ... (append [[sf, "sankhya", result], [sf, "derived-by", mantra]] ...)
proof-graph = cond is-viveka (append base viveka-triples) otherwise (append enriched result-triples)
```

Om graph declares: `pramana.om: "seva-janya" "samskaara-phala" "lekhana-kriya"`.
Pramana takes evidence, produces proof, acts by recording. That IS what
the 20 lines do.

Tantra3 form: `pramana-bandha base-graph result final-match → proof-graph`.

**Tantra3 step:** Step 2 (extracted as named sub-tantra in anuvada-ganana rewrite).

### Structure 5: `varga-viveka` → om-sthita on mantra nodes

**Hardcoded in two files:**

```
physics-mantras.tantra2:  result = walk-in "physics-mantra" "varga"
math-mantras.tantra2:     result = walk-in "math-mantra" "varga"
```

Then in match-mantra:
```
is-count-question = member (to-string solve-for) count-concepts
mantras = cond is-count-question math-ms otherwise (append physics-ms math-ms)
```

Om graph already declares domain via `sthita` edges on every mantra node.

Tantra3 form: the split disappears entirely. All mantra-layer nodes are
candidates. `om-phala` match replaces domain-gated filtering. Count-mantras
found automatically because they have `phala: [count-total]`.

**Tantra3 step:** Step 2 (merged — removal of hardcoded filter IS domain routing).

### Structure 6: `eval_arg` (OCaml level)

**72 occurrences** in `yantra_eval_primitives.ml`:

```ocaml
let name = as_string (e_eval k e (List.nth args 0)) in
let name2 = as_string (e_eval k e (List.nth args 1)) in
```

Stays in OCaml (execution engine sparsha). But tantra3 reduces what each
call dispatches — one `om-contract` call replaces N mantra-specific branches.

**Tantra3 step:** Step 1 (om-contract reduces dispatch fan-out).

### Structure 7: `with_node` (OCaml level)

**34 occurrences** in primitives and proof_graph:

```ocaml
match Proof_graph.find k name with
| Some n -> (* use n *)
| None   -> fallback
```

Stays in OCaml. But `om-contract` consolidates multiple existence checks
into one contract fetch per node.

**Tantra3 step:** Step 1 (foundation).

---

## The "no match" anatomy — what the tests revealed

### Current baseline

**500 passed / 77 xfailed / 0 hard failures** (2026-03-19, post-session 6).

### "No match" is the dominant failure mode — but not the only one

Of the 77 xfails, **42 (55%)** produce "no match" somewhere in their
output. **35 (45%)** fail for other reasons.

| Failure mode | xfails | What happens |
|---|---|---|
| **"no match" — mantra not found** | 42 | Pipeline has intent, has values, but matching/routing fails |
| **Sub-tantra doesn't exist** | 10 | `test_match_decomp` — tantras not yet written |
| **Wrong avrti/sandhi resolution** | 7 | Words stay mithya or don't compound correctly |
| **Computation gives wrong result** | 6 | Viveka fires but scoping is wrong |
| **Proportional / structural gap** | 2 | Mechanism not built |
| **Dvandva / collection** | 3 | Values don't group per-entity |
| **Other structural** | 7 | Position, relative velocity, etc. |

### "No match" in PASSING tests — this is correct behavior

**29 passing tests** also produce "no match" somewhere. These are:

| Category | Count | Why it's correct |
|---|---|---|
| Session first-turn (statement, no solve-for) | 8 | "mass is 5" has no intent — later turn completes |
| Tests that verify no-match behavior | 3 | `test_no_match_insufficient_janya` etc. — intentionally testing the no-match path |
| Entity setup turns | 3 | "ball has mass 5 velocity 10" — no intent, next turn does computation |
| Edge case verification | 6 | `test_find_force_needs_acceleration_not_velocity` — verifies correct non-firing |
| Intermediate no-match | 6 | Inverse/spring-force — "no match" in one call, test assertion checks something else |
| Session multi-turn | 3 | First call is "find force" with no prior binding — second turn provides values |

**Key insight:** "no match" in passing tests is either intentional (testing
the graceful-failure path) or intermediate (first turn of multi-turn session
where the second turn completes). No passing test produces "no match" as
its final, asserted answer.

### What tantra3 steps fix which "no match" failures

| "No match" cause | xfails | Tantra3 step |
|---|---|---|
| Mantra not in physics-mantra varga (count-mantras orphaned) | 4 | Step 2 — om-driven match auto-discovers |
| Inverse match path broken | 7 | Step 2 — om-janya/om-phala generic inverse |
| sthita-viveka / multi-entity slots | 4 | Step 2 + Gap 2 |
| Logic/syllogism (no kosha) | 4 | Step 4 — swarupa-chain + kosha files |
| Session/entity across turns | 5 | Gap 2 (not tantra3) |
| Collocation / verb binding | 4 | Step 3 (abheda) + bhasha layer |
| Missing kosha concept | 3 | New om files |
| Viveka/comparison | 5 | Viveka path improvement |
| Other | 6 | Mixed |

---

## Summary: impact vs effort matrix (revised)

| Step | Status | xfails promoted | Perf impact | Architecture |
|------|--------|----------------|-------------|-------------|
| 1. om-contract primitive | **DONE** | 0 (foundation) | None | `om-janya`, `om-phala`, `om-kriya`, `om-yukta`, `om-sthita`, `om-swarupa`, `om-abheda`, `om-contract` in OCaml |
| 2. Om-driven match + derive + domain | **DONE** | 4 (decomp sub-tantras) | mantra-select: 1393ms→1ms | `mantra-select` via varga walk. `physics-mantras`/`math-mantras` dead. |
| Dissolution (3 tiers) | **DONE** | 0 | median 44ms→28ms (-36%) | 9 dead tantras dissolved. 5 new named acts created. panchaavayava strands extracted. pramana-bandha named. |
| 3. abheda reading | **NEXT** | ~3 | +1-2ms negligible | "from rest" → initial-velocity=0. New `abheda-viveka` sub-tantra in avrti-refine. |
| 4. swarupa-chain / syllogism | Pending | up to 8 | Zero on existing path | IS-A chain walk + common-sense kosha files. |

**Baseline after Steps 1-2 + dissolution: 501 passed / 73 xfailed / 0 failing.**
**Baseline after session 8 (decomp + anumana): 512 passed / 62 xfailed / 0 failing.**
**Baseline after session 9 (scan body escape fix): 511 passed / 63 xfailed / 0 failing.**

**Next work: see [17-scan-ref-patterns.md](17-scan-ref-patterns.md) for the active implementation plan.**

**Immediate next fixes (not steps — test fixes):**
- 9 decomp xfails: `forward-match`, `inverse-match`, `scope-vps` tests use old single-arg API — update to multi-arg
- 7 inverse-math xfails: debug `inverse-match.tantra3` execution path

**Unnamed structures — session 7 resolution:**

| Structure | Status | How resolved |
|---|---|---|
| sankhya-sparsha (16×) | Named | `bound-state` wraps `sankhya-sparsha` — 3 tantras → 1 |
| shashthi-sparsha (43×) | Named | `scope-vps` calls `shashthi-sparsha` — inline pattern → named |
| iccha-viveka (9×) | Named | `extract-solve-for` is the named form — already extracted |
| pramana-bandha (4×) | Named | `pramana-bandha.tantra3` extracted from `anuvada-ganana` |
| varga-viveka | Dissolved | `mantra-select` with varga walk — filter IS the routing |
| eval_arg (72×) OCaml | Reduced | `execute-mantra` dispatches once — 3 paths → 1 tantra |
| with_node (34×) OCaml | Reduced | `om-contract` consolidates — N walks → 1 per node |

**Remaining ~73 xfails need:**
- Decomp test API fixes (9) — quick
- Inverse-match debugging (7) — medium
- Step 3 abheda (~3) — 1 new tantra
- Step 4 syllogism (~8) — kosha files + 1 tantra
- Gap 2 session entity carry (~6) — session-anuvada
- Verb-as-signal collocation (~4) — bhasha layer
- Dvandva per-entity (~4) — avrti-refine extension
- Viveka compute-then-compare (~4) — viveka-ganana
- Unit rate compound (~4) — sandhi + avrti
- Sthita-viveka multi-slot (~4) — new sub-tantra
- Various structural (~10)

---

## Baseline performance from test cache

Data collected by `tools/collect_graph_patterns.py` and analyzed by
`tools/analyze_test_results.py` and `tools/analyze_graph_patterns.py`.
Cache in `vyakarana/.pytest_cache/vyakarana/` (549 entries) and
`/tmp/graph_patterns.json` (197 traces: 87 passing, 39 failing).

### The old xfail baseline (cached, pre-session 5)

The test cache was collected at **496 passed / 52 xfailed** — before
sessions 5 and 6 which added 25 new xfail tests and fixed 4 existing
ones. The cache reflects the earlier state but its structural findings
are still valid.

The cached 52 xfails broke down as:

| Gate | Count | Status now |
|------|-------|-----------|
| arithmetic (plain count) | 4 | Still xfail — count-mantras not routed |
| dvandva (per-entity instance-map) | 4 | 3 still xfail, 1 fixed |
| inverse-math (bound-vals path) | 4 | All fixed in session 5 |
| kosha (missing concept node) | 2 | 1 fixed (frequency), 1 still xfail |
| logic_nyaya (P8d not built) | 8 | Still xfail |
| session_gap2 (prathama/shashthi) | 4 | Still xfail |
| sthita-viveka (multi-slot) | 4 | Still xfail |
| viveka (compute-then-compare) | 4 | Still xfail |
| viveka (proportional reasoning) | 2 | Still xfail |
| p8f_gravity (G + r²) | 1 | Still xfail |
| unit_rate (m/s compound) | 1 | Still xfail |
| parsing (article/natural) | 2 | Still xfail |
| other scattered | 12 | Mixed |

### Structural anatomy from graph traces

From 197 traced sentences (87 passing, 39 failing, rest no-intent):

**Success marker:** `rashi-bandha` edge present in 0.21× of passing
sentences, absent from failing. This edge means a numeric value was
successfully assigned to a concept — it is the proof that the pipeline
completed binding.

**Failure anatomy (28 sentences with intent but no match):**

| Failure mode | Count | What it means |
|-------------|-------|-------------|
| No entities (no ownership) | 15 | No `shashthi-vibhakti` detected |
| Mithya stuck (kosha gap) | 26 | Words never promoted to satya |
| Binding gap (unvalued satya) | 24 | Concept recognized but number never binds |
| No sankhya at all | 1 | No numeric values in sentence |

The dominant failure mode is **mithya stuck + binding gap together** — a
word is recognized as a concept (satya) but its numeric value never finds
its way to the concept node. This is the rashi pipeline gap: the number
is present, the concept is present, but the binding step fails because
either:
- The entity ownership chain is broken (no shashthi-vibhakti)
- The concept is a compound that wasn't resolved (kosha gap)
- The mantra isn't found (routing gap — what Phase 2 fixes)

**Top mithya-stuck words (kosha gaps):**

| Word | Frequency | Why it's stuck |
|------|-----------|---------------|
| kinetic | 56× | Only meaningful as compound "kinetic-energy" |
| ball | 38× | Entity name — correctly mithya, but needs prathama |
| m1, v1, a1 | 36×/27×/8× | Instance labels — correctly mithya |
| initial | 15× | Only meaningful as compound "initial-velocity" |
| ball-A, ball-B | 34×/31× | Entity names |
| m/s | 7× | Compound unit — no word-index entry |
| potential | 6× | Only meaningful as "potential-energy" |
| apples | 4× | Common-sense domain — no kosha entry |

**Key insight:** Most "kosha gaps" are not real gaps — `kinetic`,
`initial`, `ball`, `m1` are CORRECTLY mithya. They become satya through
compound resolution (`kinetic`+`energy` → `kinetic-energy`) or entity
recognition (`ball-A` → prathama-vibhakti). The real gaps are:
- `apples`, `oranges`, `birds`, `cats`, `dogs` — common-sense domain
  missing entirely
- `m/s` — compound unit not handled
- `spring constant` — two-word compound not in sandhi-kosha

**Top binding gaps (satya but unvalued):**

| Concept | Frequency | Why unvalued |
|---------|-----------|-------------|
| kinetic-energy | 52× | This is the solve-for — correctly unvalued (it's what we're computing) |
| momentum | 23× | Same — solve-for |
| force | 13× | Same |
| mass | 10× | Should have value but binding failed |
| electron | 9× | Entity concept — not a numeric value |
| velocity | 8× | Should have value but binding failed |

**Key insight:** Most "binding gaps" are the solve-for concept — it's
unvalued because that's what the question asks to compute. The analyzer
needs fixing to exclude solve-for from the binding gap count. The real
binding gaps are `mass` (10×) and `velocity` (8×) — these should have
values but the binding step failed, usually because of the ownership
chain being broken.

### Template clusters — what structural patterns work

The graph pattern analyzer groups sentences by edge-type signature.
Sentences with the same signature share structural form.

**Always-passing templates:**

| Template (edge types in refined graph) | Count | What it means |
|---------------------------------------|-------|-------------|
| `[prathama, sankhya, satya, shashthi, vidhi-kaala, vishesa]` | 19 | Entity + owned values + intent + type = full pipeline |
| `[mithya, prathama, rashi-bandha, sankhya, satya, shashthi, vidhi-kaala, viraam]` | 11 | Multi-clause with entity + rashi-bandha signal |
| `[sankhya, satya, vidhi-kaala]` | 8 | Simple: concept + value + intent |

**Always-failing templates:**

| Template | Count | What it means |
|---------|-------|-------------|
| `[mithya, prathama, sankhya, satya, shashthi, vishesa]` | 17 | Has entities + types but **no intent** (no vidhi-kaala) |

**Mixed templates (some pass, some fail):**

| Template | Count | Pass/Fail | What determines success |
|---------|-------|-----------|----------------------|
| `[sankhya, satya, vidhi-kaala, viraam]` | 33 | 1✓/4✗ | Multi-clause + intent but inverse-match needed (most fail) |
| `[mithya, prathama, sankhya, satya, shashthi, vidhi-kaala, viraam, vishesa]` | 14 | 4✓/1✗ | Full entity pipeline — spring-constant kosha gap causes 1 failure |

**Key insight:** The missing `vidhi-kaala` (intent signal) is the single
strongest predictor of failure. 17 sentences have full entity structure but
no "find X" / "what is X" intent signal — they all fail. This is correct
behavior (no intent = ambiguous), but it means the pipeline's intent
detection is critical. Tantra3's om-driven approach doesn't change this —
intent still comes from the English sentence, not the om graph.

### Performance profile

**Slowest individual pipeline calls:**

| Time | Sentence pattern |
|------|-----------------|
| 437ms | Chain: "find force given initial velocity 0 final velocity 20 time 4 mass 3" |
| 420ms | Chain: "initial velocity is 0. acceleration is 10. time is 3. find velocity" |
| 411ms | Chain: "find kinetic energy given initial velocity 0 acceleration 4 time 5 mass 2" |
| 406ms | Chain: similar SUVAT chain |
| 379ms | Chain: "find momentum ball has initial velocity 0..." |

**Pattern:** All slowest calls are **chain derivations** — sentences
requiring 2-3 mantra fires in sequence (velocity→KE, velocity→momentum).
The derive-chain search is the bottleneck. Phase 5 (DAG walk) would
directly improve these — O(depth=2-3) instead of O(search over 23 mantras
× multiple attempts).

**Slowest tests (total duration including multiple calls):**

| Time | Test | Calls |
|------|------|-------|
| 0.78s | test_three_entities_accumulate | 4 |
| 0.71s | test_electron_and_field_across_turns | 3 |
| 0.69s | test_electron_simulation_scene_full | 3 |
| 0.52s | (several multi-entity session tests) | 2-3 |

**Pattern:** Multi-entity session tests are slow because each turn is a
full pipeline call. With tantra3, per-entity computation would be scoped
by om-sthita slot structure rather than flat search, potentially faster.

### Full timing profile from test cache

623 individual calls cached. Total execution time: 40.1s.

**Per-call distribution:**

| Bucket | Calls | % | Note |
|--------|-------|---|------|
| <10ms | 373 | 59.9% | Graph queries, lookups, shabda, simple evals |
| 10-25ms | 34 | 5.5% | match-mantra, small BQG |
| 25-50ms | 53 | 8.5% | Larger BQG + avrti |
| 50-100ms | 8 | 1.3% | Transitional |
| 100-200ms | 37 | 5.9% | Simple anuvada-ganana |
| 200-300ms | 100 | 16.1% | Typical anuvada-ganana |
| 300-500ms | 18 | 2.9% | Chain derivation anuvada-ganana |
| >500ms | 0 | 0.0% | None |

```
median:  4ms    (most calls are fast graph queries)
p90:   254ms    (top 10% are full pipeline calls)
p95:   270ms
p99:   379ms
max:   437ms
mean:   64ms
```

**Time by pipeline stage:**

| Stage | Calls | Median | P90 | Max | Total | % time |
|-------|-------|--------|-----|-----|-------|--------|
| anuvada-ganana (full pipeline) | 165 | 227ms | 307ms | 437ms | 32.1s | **80.1%** |
| other eval (sub-stage calls) | 206 | 0ms | 150ms | 259ms | 6.8s | 17.1% |
| BQG + avrti-refine (fixpoint) | 79 | 5ms | 9ms | 250ms | 0.6s | 1.6% |
| match-mantra | 18 | 17ms | 21ms | 28ms | 0.3s | 0.8% |
| build-question-graph only | 60 | 2ms | 4ms | 5ms | 0.1s | 0.3% |
| kosha-expand | 7 | 6ms | 11ms | 11ms | <0.1s | 0.1% |
| avrti-refine only | 49 | 0ms | 0ms | 1ms | <0.1s | <0.1% |
| graph query (walk/edges) | 3 | 0ms | 0ms | 0ms | <0.1s | <0.1% |
| shabda/lookup | 36 | 0ms | 0ms | 0ms | <0.1s | <0.1% |

**Key finding:** 80% of all test time is inside `anuvada-ganana`. BQG
alone is fast (2ms median). avrti-refine alone is fast (<1ms). match-mantra
is fast (17ms median). The time is in the full orchestration — the
composition of all stages plus derive-chain plus execute.

**anuvada-ganana calls by test category:**

| Category | Calls | Median | P90 | Max | Total |
|----------|-------|--------|-----|-----|-------|
| Simple (one-shot) | 102 | 220ms | 268ms | 297ms | 18.0s |
| Entity-scoped | 35 | 256ms | 307ms | 338ms | 7.7s |
| Chain derivation | 15 | 371ms | 420ms | 437ms | 5.0s |
| Viveka (comparison) | 13 | 35ms | 259ms | 262ms | 1.4s |

Chain derivation calls are **1.7× slower** than simple calls (371ms vs
220ms median). Entity-scoped calls are **1.2× slower** than simple calls
(256ms vs 220ms). The chain overhead is the derive-step search loop.

**Sub-stage timing (calls outside anuvada-ganana):**

| Stage | Calls | Median | Max | Total |
|-------|-------|--------|-----|-------|
| find (intent detection) | 40 | 42ms | 222ms | 3.1s |
| entity-name evals | ~11 | 242ms | 259ms | 2.9s |
| fixpoint (avrti loop) | 77 | 5ms | 250ms | 0.6s |
| match-mantra | 18 | 17ms | 28ms | 0.3s |
| build-question-graph | 46 | 2ms | 5ms | 0.1s |
| kosha-expand | 7 | 6ms | 11ms | 0.1s |

The `find` calls at 42ms median are `extract-solve-for` evaluations —
they scan the full graph for `vidhi-kaala` edges. Entity-name evals
(ball-A, electron, etc.) at 242ms are full pipeline runs in session tests
where entity names trigger full re-evaluation.

### Sparsha/viveka/bandha distribution

From `tools/analyze_pipeline.py` cross-layer analysis:

**In tantra2 code:**
- Sparsha: 100 instances (walk-edge 26, scan-triple 25, shabda 19, bound-concepts 18, graph-where-collect 12)
- Viveka: 220 instances (eq-edge-type 58, gt-length 55, member-check 38, cond 37, is-viveka 32)
- Bandha: 80 instances (append-acc 29, reduce-to-list 21, sankhya-triple 16, emit 8, derived-by 6)

**In OCaml code:**
- Sparsha: 66 instances (hashtbl_find 30, json_field 13, eval_arg 9, proof_graph_find 9)
- Viveka: 58 instances (string_compare 18, match_option 15, node_match 12, eval_ctx 9)
- Bandha: 336 instances (ref_mutate 121, some_return 105, list_cons 51, hashtbl_replace 47)

**Key insight:** OCaml's bandha count (336) dwarfs tantra2's (80). This
makes sense — OCaml is the execution engine, it does the actual writing.
The tantra2 viveka count (220) is the largest tantra-level category — the
pipeline spends most of its tantra code discriminating and filtering. This
is where tantra3 has the biggest impact: replacing hardcoded `eq e "sankhya"`
(58 instances) with om-driven edge discovery eliminates the need for
per-edge-type discrimination in tantra code.

---

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-19 | Initial writing — live graph analysis, xfail classification, implementation phases, OCaml change plan. |
| 2026-03-19 | Baseline performance section added from test cache (549 entries, 197 traces). Structural anatomy, template clusters, performance profile, sparsha/viveka/bandha distribution. Key insights: mithya-stuck is mostly correct behavior; binding gaps are mostly solve-for; missing vidhi-kaala is strongest failure predictor; chain derivations are the performance bottleneck. |
| 2026-03-19 | Implementation plan revised from 6 phases to 4 steps after performance analysis. Derive-chain rewrite and domain routing merged into Step 2 (om-driven match-mantra) — they are one structural change not three. Abheda moved before syllogism (lower risk, higher density). Per-step performance impact estimates added. Full timing profile: 623 calls, 40.1s total, 80% in anuvada-ganana orchestration, chain 1.7× slower than simple, base cost 220ms is the real target. |
| 2026-03-19 | Seven unnamed structures section added — cross-reference between `analyze_pipeline.py` findings and tantra3 steps. sankhya-sparsha (16×), shashthi-sparsha (43×), iccha-viveka (9×), pramana-bandha (4×), varga-viveka, eval_arg (72×), with_node (34×). Each mapped to the tantra3 step that names it. Total: ~130 translation instances eliminated by Steps 1-2. The Manipravalam principle: the code speaks the same language as the knowledge. |
| 2026-03-19 | "No match" anatomy added. 42/77 xfails (55%) produce "no match". 35/77 fail for other reasons (sub-tantra doesn't exist, wrong resolution, wrong scoping, structural gaps). 29 passing tests also produce "no match" — all correctly (session first-turns, edge-case verification, intentional no-match tests). "No match" in passing tests is always intermediate or intentional, never the asserted final answer. Cross-reference table: which "no match" causes map to which tantra3 steps. Updated baseline: 500 passed / 77 xfailed / 0 failing. |
| 2026-03-19 | **Session 7: Full tantra3 migration complete + dissolution.** Steps 1 and 2 complete. All tantra2 files deleted. 63 active tantra3 files. `mantra-select` varga walk: 1393ms → 1ms. Seven dissolution actions across three tiers. Philosophical mapping: sparsha=pratyaksha, bound-state=sthiti, execute-mantra=kriya, shabda-anveshana=pratyabhijna, emit-reasoning strands=panchaavayava nyaya, pramana-bandha=proof binding. Baseline: 501 passed / 73 xfailed / 0 failing. Tantra3 file count: 68 (including 5 new sub-tantras). Total lines: 2655 (-17% from tantra2). Next: decomp test fixes (9 xfails — API mismatch), Step 3 abheda reading (~3 xfails), inverse-match fix (7 xfails). |
