# Migration Status

## Done

### Phase 0 — Shabda Inheritance
`walk_inheritance`, `raw_shabda_for_node`, `merge_shabda_priority`

### Phase 0.5 — Bhasha Layer Recognition
`om_parser.ml` recognizes `bhasha` header

### Phase 0.6 — Bhasha Satya Weighting
`raw_satya` applies `*. 0.5` for `"bhasha"` layer

### Phase 1 — Ring Extension
7 new dims added to `visheshanam-ring.om`:
`ahara-yukta dhatu-yukta vrnda-yukta kala-yukta prayoga-yukta vachana-yukta purusa-yukta`

### Phase 1.5 — Sangati Grammar Nodes
48 files written in `brahman/sangati/`:
- `kaala.om` updated (owns tense values; IS the tense parent — no separate kala.om)
- tense: `vartamana-kaala`, `bhuta-kaala`, `bhavishya-kaala`, `vidhi-kaala`, `sambhavana-kaala`
- voice: `kartari-prayoga`, `karmani-prayoga`, `bhave-prayoga`
- number: `eka-vachana`, `dvi-vachana`, `bahu-vachana`
- person: `prathama-purusa`, `madhyama-purusa`, `uttama-purusa`
- vibhakti: `prathama` through `saptami` + `sambodhana`
- pada: `subanta`, `tinanta`, `avyaya`, `nipata`, `upasarga`
- pratyaya: `shatr`, `kta`, `tvaa`, `tumun`
- samasa: `tatpurusha`, `karmadharaya`, `dvandva`, `bahuvrihi`
- domains: `domain-vak`, `domain-yantra-bhasha` (split from domain-language)
- `grammatical-gender.om` moved from `brahman/kosha/` → `brahman/sangati/`

### Phase 2 — Kosha Process Nodes
- Annotated existing physics process nodes with `bhave-prayoga-swarupa tinanta-swarupa` and `subanta-swarupa`
- 21 new process nodes created
- 525 kosha headers corrected sangati→kosha
- `aarambham`/`abhava`/`niyama` moved to `brahman/sangati/`

### Phase 2.5 — Kosha Samanya Nodes + Inheritance Restructure
- Step 1: `vishesa` and `amsha` added as ring dims to `visheshanam-ring.om`; `walk_inheritance` updated
- Step 2: Varga nodes created for all domains:
  - Root: `physics-varga`, `math-varga`, `cs-varga`, `chemistry-varga`, `biology-varga`, `sangeetham-varga`, `finance-varga`, `robotics-varga`
  - Physics subdomain vargas: `kinematics-varga`, `dynamics-varga`, `energy-varga`, `oscillation-varga`, `thermodynamics-varga`, `electromagnetism-varga`, `optics-varga`, `fluid-varga`, `quantum-varga`
  - Physics sub-subdomain vargas: `linear-motion-varga`, `rotational-motion-varga`, `linear-force-varga`, `rotational-force-varga`, `mechanical-energy-varga`, `circuit-varga`, `field-varga`
  - Math subdomain vargas: `algebra-varga`, `geometry-varga`, `calculus-varga`, `number-varga`, `set-varga`
  - CS subdomain vargas: `type-varga`, `computation-varga`, `memory-varga`
  - Chemistry/Biology/Sangeetham/Finance subdomain vargas: all created
- Step 3+4: Full physics kosha subdir restructure complete:
  - All physics leaf nodes migrated to subdir topology
  - All `domain-physics-sthita` removed from leaves
  - Sangati fixes: `matra.om`, `sambandha.om`, `prasarana.om` — removed downward domain references

### Phase 2.6 — Sangati Subdir Restructure
Full restructure of `brahman/sangati/` from 263 flat files into hierarchy:

```
brahman/sangati/
  mula/          22 root philosophical claims
  spanda/        19 vibration/spiral/pulse nodes
  parampara/     19 structure-in-nature nodes
  jiva/          22 living-things nodes
  bhava/         16 experiential-state nodes
  chetan/        14 consciousness/knowing nodes
  vak/           13 language/sound nodes
  grammar/
    kaala/       kaala.om + 5 tense amshas
    vibhakti/    vibhakti.om + 8 case amshas
    pada/        pada.om + 5 word class nodes
    vachana/     vachana.om + 3 number nodes
    prayoga/     prayoga.om + 3 voice nodes
    purusa/      purusa.om + 3 person nodes
    samasa/      samasa.om + 4 compound nodes
    pratyaya/    pratyaya.om + 4 suffix nodes
    linga/       linga.om + grammatical-gender
  geometry/      15 spatial/geometric nodes
```

Sthalam nodes: all 6 rewritten as thin anchors (direction flipped to upward). 5 new sthalam nodes.
Engine duplicates and collatz removed from sangati.

**Regression: 49/52 — same 3 pre-existing failures. Zero new failures.**

### Bhasha migration
- `brahman/bhasha/ocaml/` — 30 files moved from `kosha/language/ocaml/`, headers → bhasha
- `brahman/bhasha/lua/` — 12 files moved, headers → bhasha
- `brahman/bhasha/strudel/` — 6 files moved, headers → bhasha
- `brahman/bhasha/render/` — 5 files moved, headers → bhasha
- `_migration/kosha-language/` — 138 English language files removed from brahman, kept as reference

---

## Not yet done

### Phase 2.7 — Engine to kosha/engine/ (folds into 2.9)
Move `brahman/engine/` → `brahman/kosha/engine/`
Update any loader paths that reference `brahman/engine/` directly

### Phase 2.8 — Collatz to kosha/math/ (folds into 2.9)
Write `collatz-math-seema`, `collatz-returningness`, `collatz-space` into
`brahman/kosha/math/number/structures/`

### Phase 2.9 — Math kosha full restructure (NEXT — see phase-2.9-math.md)
Full details in `phase-2.9-math.md`

### Phase 3 — Bhasha/English
Write all nodes in `brahman/bhasha/english/` from `bhasha-english.md` directory structure.
Fix loader to pick up `brahman/bhasha/` (see loader fix below).
Delete `_migration/kosha-language/` after verifying coverage.

### Phase 4 — Extraction Pipeline Upgrade
- New tantra `compute-extraction-seeds` — pre-pass goal detection → seed list
- Modify `extract-vector-coords` — seeds param, context-score, kala-aware role assignment
- Modify `scene-extract-kinematic-chain` — call pre-pass, remove `target-triggers`, pass seeds

### Phase 5 — Sense Nodes (Polysemy)
`position-spatial.om`, `position-verb.om` sense nodes

### Phase 6 — Signal Weight Cache
Startup pass: compute context-score for kosha process nodes, write to shabda

### Phase 7 — Deduplication Cleanup
Robotics, physics chain, visheshanam consolidation

### Phase 8 — Broader English Vocabulary
Comparatives, ordinals, temporal, approximation, circuit/oscillator gaps

### Phase 9+ — Machine Language Bhasha Rewrite
OCaml/Lua/Strudel nodes: apply Sanskrit grammatical annotations to programming constructs

---

## Loader fix needed (Phase 3 prerequisite)

`om_parser.ml` `expand_dir` currently only expands `brahman/kosha/`. Must also expand
`brahman/bhasha/`:

```ocaml
let expand_dir d =
  let sub_kosha = Filename.concat d "kosha" in
  let sub_bhasha = Filename.concat d "bhasha" in
  let dirs = [d] in
  let dirs = if Sys.file_exists sub_kosha && Sys.is_directory sub_kosha
             then dirs @ [sub_kosha] else dirs in
  let dirs = if Sys.file_exists sub_bhasha && Sys.is_directory sub_bhasha
             then dirs @ [sub_bhasha] else dirs in
  dirs
```

Also: `kosha_root` tracking and `search_dirs` for `shabda-tmpl` resolution must include
the bhasha path.

---

## Pre-existing test failures (3 — do not fix, do not worsen)

Same 3 failures throughout all phases. Regression target is always 49/52.
