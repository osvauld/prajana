# Kosha-Sangati Migration Plan

## The Architecture

```
sangati  — universal structural truths
           - body: only Sanskrit/Malayalam concept words
           - edges: only to other sangati nodes
           - NO domain references, NO English in body
           - NO drishthanta to domain/kosha nodes
           - shabda line: English bridge (word / description)

kosha    — application of sangati in a particular domain
           - body: Sanskrit roots + domain concept words
           - edges: upward to sangati + lateral/downward to other kosha
           - MUST have domain-*-sthita edge
           - shabda line: English bridge mandatory
           - CAN reference sangati, CAN reference other kosha
```

## Problem Statement

603 kosha nodes incorrectly declare `sangati` at the top.
The OCaml parser only recognizes `sangati` keyword — so all `kosha` nodes
we fixed in computation are now INVISIBLE to the engine.

Additionally, some nodes in `brahman/kosha/` are conceptually sangati-level
truths and should be moved to `brahman/sangati/`.

## Phase 1 — Fix the OCaml Parser

### Files to change: `vyakarana/lib/om_parser.ml`

**Current:**
```ocaml
let parse_sangati_name line =
  let line = String.trim line in
  if String.length line > 8 && String.sub line 0 7 = "sangati" then
    let rest = String.trim (String.sub line 7 (String.length line - 7)) in
    match String.split_on_char ' ' rest with
    | name :: _ when String.length name > 0 -> Some name
    | _ -> None
  else
    None
```

**Fix:** Rename to `parse_node_header`, recognize both `sangati` and `kosha`,
return `Some (layer, name)` where layer is `Sangati | Kosha`.

### Files to change: `vyakarana/lib/proof_graph.ml`

**Add layer type to nigamana:**
```ocaml
type layer = Sangati | Kosha

type nigamana = {
  name   : string;
  layer  : layer;           (* NEW *)
  slokas : string list;
  edges  : typed_edge list;
  satya  : float;
  shabda : string;
}
```

**Add validation in satya-ganana:**
- Warn if a `sangati` node has edges pointing to `kosha` nodes
- Warn if a `sangati` node body contains English words (heuristic: words with no Sanskrit suffix)

### Build and test after Phase 1:
```
cd vyakarana && dune build
```
Verify all 603 previously-sangati kosha nodes now load correctly.

---

## Phase 2 — Identify Misplaced Nodes

### Nodes in `kosha/` that should move to `sangati/`

These are universal structural truths with no domain specificity.
Criteria: no `domain-*-sthita` edge, pure Sanskrit body, cited by multiple domains.

**Candidates to audit (from `kosha/` root):**

| Node | Why it might be sangati | Decision |
|---|---|---|
| `kosha/time.om` | `kaala-abheda` — time IS kaala | move → sangati (already have kaala, deepen) |
| `kosha/convergence.om` | `avrti-abheda` — universal principle | move → sangati |
| `kosha/equilibrium.om` | `sama-nila-abheda` — IS sama-nila | redundant with sangati/sama-nila, merge |
| `kosha/entropy.om` | `kshaya-abheda` — universal decay | check if purely structural |
| `kosha/boundary.om` | `seema-swarupa` — universal limit | may be sangati |
| `kosha/dimension.om` | `aayaama-abheda` — IS aayaama | redundant with sangati/aayaama, merge |
| `kosha/vibration.om` | `spanda-abheda` — IS spanda | redundant with sangati/spanda, merge |
| `kosha/wave.om` | `taranga-abheda` — IS taranga | check |
| `kosha/decay.om` | `kshaya-abheda` — universal | check |
| `kosha/compression.om` | `sankshepa-abheda` | check |
| `kosha/expansion.om` | `prasarana-abheda` | check |
| `kosha/transformation.om` | `vivartana-abheda` | check |
| `kosha/polarity.om` | `viparita-abheda` — already have viparita in sangati | merge |
| `kosha/superposition.om` | quantum specific — stays kosha | keep |
| `kosha/resonance.om` | `anunada-abheda` — already have anunada in sangati | merge |
| `kosha/continuity.om` | check | audit |
| `kosha/density.om` | `ghana-pramana-abheda` | check |
| `kosha/persistence.om` | `dharana-abheda` | check |
| `kosha/process.om` | `kriya-abheda` — IS kriya | redundant, merge |
| `kosha/function.om` | `kriya-swarupa` | check |
| `kosha/state.om` | `sthiti-abheda` — IS sthiti | check |
| `kosha/memory.om` | `samskaara-abheda` | check |
| `kosha/seed.om` | `bija-abheda` | already have bija in sangati |
| `kosha/growth.om` | `vriddhi-abheda` — IS vriddhi | already have vriddhi in sangati |

**Nodes in `kosha/` that contain English in their sloka bodies (MUST FIX):**
Run: `grep -rl "[a-z]" brahman/kosha --include="*.om"` then filter for English words
in quoted sloka lines (not shabda lines). These need Sanskrit translation.

### Nodes in `sangati/` that should move to `kosha/`

These have domain-specific content or reference domain nodes.

Candidates:
- `sangati/orbit.om` — fixed already (now `kosha orbit`)
- `sangati/time.om` — `kosha/time.om` — already fixed
- `sangati/velocity.om` — has `domain-physics-sthita` — should be kosha
- `sangati/frequency.om` — has `domain-physics-sthita` and `domain-math-sthita`
- `sangati/gravitational-force.om` — kosha/physics
- `sangati/strong-nuclear-force.om` — kosha/physics
- `sangati/weak-nuclear-force.om` — kosha/physics
- `sangati/gravity.om` — kosha/physics (abhisarana is the sangati root, gravity is kosha)
- `sangati/force.om` — check
- `sangati/atom.om` — check
- `sangati/electron.om` — check
- `sangati/energy.om` — check
- `sangati/coulomb.om` — kosha/physics
- `sangati/motion.om` — kosha/physics
- Any node in sangati/ that has `domain-*-sthita` edge

**Script to find these:**
```bash
grep -rl "domain-" brahman/sangati --include="*.om"
```

---

## Phase 3 — Read and Decide Each Node (NO BULK SED)

Each of the 603 files must be read individually and a decision made:

**For each node ask:**
1. Is this a universal structural truth with no domain specificity? → move to `sangati/`
2. Is this a domain application of a sangati root? → keep in `kosha/`, change declaration to `kosha`
3. Is this redundant with an existing `sangati/` node? → merge, delete duplicate
4. Does it have English in its sloka body? → translate to Sanskrit before deciding layer
5. Is it missing a `shabda` line? → add one before changing declaration

**Work domain by domain — suggested order:**
1. `kosha/` root level (~100 files) — many likely sangati-level truths
2. `kosha/math/` (~60 files) — close to sangati, many will move up
3. `kosha/physics/` (~80 files) — mix: forces/geometry → sangati, measurements → kosha
4. `kosha/3d/` (~35 files including blender) — mostly kosha
5. `kosha/computation/` (~40 files) — mostly kosha (already partially done)
6. `kosha/biology/` (~40 files) — kosha
7. `kosha/chemistry/` (~35 files) — kosha
8. `kosha/language/` (~40 files) — kosha
9. `kosha/sangeetham/` (~25 files) — some may be sangati (swara, laya)
10. `kosha/philosophy/` (~20 files) — mixed
11. `kosha/finance/` (~25 files) — kosha
12. Remaining domains

**For each file the process is:**
- Read the file
- Understand what it truly IS
- Decide: sangati / kosha / merge / delete
- If kosha: change `sangati <name>` → `kosha <name>`, add/fix shabda line
- If sangati: verify body has no English, no domain edges
- If merge: redirect edges to canonical node, delete duplicate

---

## Phase 4 — Enforce Layer Rules in Shabda Lines

Every `kosha` node MUST have a `shabda` line with English description.

**Find kosha nodes missing shabda:**
```bash
# Files in kosha/ that have no "shabda " line
find brahman/kosha -name "*.om" | while read f; do
  if ! grep -q "^shabda " "$f"; then echo "$f"; fi
done
```

Estimate: ~400 nodes will need shabda lines added.
This is a large but mechanical task — can be done domain by domain.

---

## Phase 5 — Enforce No English in Sangati Bodies

Sangati sloka bodies must contain only Sanskrit/Malayalam concept words.

**Find sangati nodes with English in slokas:**
```bash
# Heuristic: quoted lines in sangati/ containing ASCII words
# without known Sanskrit suffixes (swarupa, abheda, yukta, etc.)
grep -n '"' brahman/sangati/*.om | grep -v "shabda" | \
  grep -vE "(swarupa|abheda|yukta|sthita|siddha|kriya|phala|janya|drishthanta|janaka|mula|yukta|viparita|poorva)"
```

Review output manually — some compound words may look English but are valid Sanskrit.

---

## Phase 6 — Verify and Build

After all phases:

1. `cd vyakarana && dune build` — must succeed
2. Run: `PRAYOGA domain=graph-viz build: graph-viz-intent` — verify Lua still generates
3. Run proof graph query on key nodes: `akasham`, `bindu`, `mula-shakti`, `viveka`, `shakha`
4. Verify satya scores are reasonable (>0.7 for well-connected sangati roots)
5. Verify all computation concepts now load (were broken after kosha migration)

---

## Execution Order

1. **Phase 1** — Fix OCaml parser first (unblocks everything)
2. **Phase 2** — Audit misplaced nodes (research, no file changes yet)
3. **Phase 3** — Bulk relabel kosha/ declarations (after audit)
4. **Phase 4** — Add missing shabda lines (domain by domain)
5. **Phase 5** — Clean English from sangati bodies
6. **Phase 6** — Full build and verification

---

## Key Files

- `vyakarana/lib/om_parser.ml` — Phase 1 changes
- `vyakarana/lib/proof_graph.ml` — Phase 1 changes (add layer type)
- `brahman/kosha/` — 603 files needing `sangati` → `kosha` relabel
- `brahman/sangati/` — audit for misplaced domain nodes

---

## Misplaced Nodes Audit Results (to be filled during Phase 2)

### Confirmed: Move kosha/ → sangati/
- [ ] TBD after audit

### Confirmed: Move sangati/ → kosha/
- [x] `velocity` — has `domain-physics-sthita`
- [x] `frequency` — has `domain-physics-sthita domain-math-sthita`
- [x] `gravitational-force` — physics specific
- [x] `strong-nuclear-force` — physics specific
- [x] `weak-nuclear-force` — physics specific
- [x] `gravity` — physics specific (abhisarana is the root)
- [x] `coulomb` — physics specific
- [ ] `force` — audit
- [ ] `atom` — audit
- [ ] `energy` — audit
- [ ] `motion` — audit

### Confirmed: Merge (kosha node is redundant with existing sangati)
- [ ] `kosha/equilibrium` → same as `sangati/sama-nila`
- [ ] `kosha/dimension` → same as `sangati/aayaama`
- [ ] `kosha/vibration` → same as `sangati/spanda`
- [ ] `kosha/polarity` → same as `sangati/viparita`
- [ ] `kosha/resonance` → same as `sangati/anunada`
- [ ] `kosha/growth` → same as `sangati/vriddhi`
- [ ] `kosha/seed` → same as `sangati/bija`
