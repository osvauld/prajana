# Linguistic Graph & NLP Plan — Index

**Status**: Phase 0 through 2.6 done. Next: **Phase 2.9** (math kosha full restructure).

## Key decisions (quick reference)

- `kaala.om` IS the tense parent — no separate `kala.om`. Tense values use `-kaala` suffix.
- Three IS-A edges: `swarupa` (identity), `vishesa` (particular of universal), `amsha` (member of set). Old `abheda` conflated all three.
- Sangati cluster anchors use `-sthalam` suffix. Members point UP via `X-sthalam-sthita`. Thin anchors only.
- Engine nodes (`proof-graph`, `om-parser`, `nigamana`, etc.) belong in `brahman/kosha/engine/` — NOT sangati.
- Collatz nodes belong in `brahman/kosha/math/number/structures/` — NOT sangati, NOT kosha root.
- Kosha cluster nodes use `-varga` suffix. Varga nodes are pure organisational anchors.
- Directory structure IS the inheritance topology.
- `domain-X-sthita` on leaves is replaced by `X-varga-vishesa` edges. Varga carries domain identity once.
- Math uses `structures/` + `properties/` + `operations/` subdirs (not physics `quantities/` + `processes/`).
- `lakshana` is the math property edge suffix — properties are neither subanta nor tinanta.

## Files in this directory

| File | Contents |
|---|---|
| [architecture.md](architecture.md) | Three-layer model (sangati/kosha/bhasha), bhave-prayoga principle, domain splits |
| [inheritance.md](inheritance.md) | Varga/vishesa/amsha system, full varga hierarchy tree, subdir pattern, walk costs |
| [grammar.md](grammar.md) | Sanskrit grammar nodes: kaala, vibhakti, prayoga, vachana, purusa, pada, etc. |
| [kosha-nodes.md](kosha-nodes.md) | Bhave process nodes + subanta quantity nodes catalog with sloka patterns |
| [bhasha-english.md](bhasha-english.md) | English bhasha layer: directory structure, node formats (tinanta/subanta/avyaya) |
| [shabda-extraction.md](shabda-extraction.md) | Shabda inheritance, lookup priority chain, extraction pipeline, signal weights |
| [phase-2.9-math.md](phase-2.9-math.md) | **NEXT** — Math kosha full restructure: edge vocab, dir skeleton, missing nodes, build sequence |
| [phase-cs-restructure.md](phase-cs-restructure.md) | CS kosha full restructure: types/control/state/concurrency/modules/hardware sub-vargas |
| [migration-status.md](migration-status.md) | What is done, what is not done, full phase sequence |
| [engine-tantra-migration.md](engine-tantra-migration.md) | OCaml → tantra migration plan: dead code, new primitives, higher-order tantras, graph system deepening |

## Other plan files (sibling directory)

```
tantra-domain-authoring.md     READ BEFORE writing any tantra — pitfalls list
visheshanam-algebra-plan.md    Ring algebra background
sphota-scene-extraction-plan.md  sphoTa extraction pattern
```

## Regression baseline

49/52 passing. 3 pre-existing failures. Do not break further.

```
vyakarana/scripts/run-regression.sh
```

## Key source files

```
vyakarana/lib/proof_graph.ml        walk_inheritance, raw_satya, dimension registry
vyakarana/lib/setu.ml               read_shabda, raw_shabda_for_node, merge_shabda_priority
vyakarana/lib/om_parser.ml          parse_node_header, expand_dir (needs bhasha fix — see migration-status)
brahman/kosha/yantra/visheshanam/visheshanam-ring.om   dimension registry
brahman/sangati/                    eternal structural truths (subdir hierarchy)
brahman/kosha/math/                 NEXT TARGET — full restructure (Phase 2.9)
brahman/kosha/engine/               engine domain (one source of truth)
brahman/bhasha/                     surface language forms
```
