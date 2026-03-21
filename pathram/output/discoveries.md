# Discoveries

## I and you are apeksha markers, not entity names. I=vacaka=chala-apeksha (speaker, moving frame). you=addressee=sthira-apeksha (graph/nam, fixed frame). When utterance crosses the boundary, pronouns invert. Every question is implicitly apeksha-nam; sambodhana makes it explicit.

## Greeting words (hello, hi, hey) are not nodes — they are shabda signals on sangati roots, like common-sense-events maps verbs to kshaya/vriddhi. english-grammar-signals.shabda maps: hello→sambodhana, hey→abhisambodhana, greetings→aamantrana. Detection: shabda lookup, not node walk.

## Sambodhana is not a special mode — the graph already acknowledges every utterance through panchaavayava (five limbs). Sambodhana is the case where only pratijna exists — the speaker is present, nothing is sought. The triple [hello, sambodhana, hello] enters the graph like any other signal.

## Vaisheshika padarthas formalized as sangati/padartha/: padartha (category), dravya (substance), guna (quality), karma (action), samanya (universal), vishesa (particular), samavaya (inherence), abhava (absence), amsha (part). thing=padartha, some=amsha, something=amsha+padartha. karma and abhava moved from parampara/ and mula/ respectively.

## Sambodhana has three degrees (amshas): sambodhana (neutral — hello, hi), abhisambodhana (emphatic — hey, yo), aamantrana (formal — greetings). Created as sangati nodes under grammar/vibhakti/. The degree is carried by the shabda signal, not by separate bhasha nodes.

## Engine nodes (14 in brahman/engine/) were mislabeled as sangati — they are kosha (domain knowledge about the system, not structural truths). Fixed: all changed to kosha except visheshanam which IS sangati (the structural truth that edges are typed relations). visheshanam moved from engine/ to sangati/.

## sangati restructuring analysis: 100 ungrouped top-level nodes. Mula pulls 47 — too broad, needs splitting into: viraam/ (6 boundary nodes), pramana/ (8 proof/epistemology nodes), vidya/ (4 knowledge nodes), true mula (~15 ultimate reality). New tools built: om classify, om ungrouped, om sthalam — static edge-affinity analysis for batch classification.

## Distinction: sangati vs kosha for self-describing nodes. sangati = structural truth (vibhakti, visheshanam, samavaya — WHAT relations ARE). kosha = domain knowledge (proof-graph, vyakarana, socket — what the system IS MADE OF). The structure is sangati; the implementation is kosha.

## Sangati restructured: 101 ungrouped top-level nodes moved into 14 sub-buckets via script. New directories: sambandha/ (12), viraam/ (6), pramana/ (8), vidya/ (6), svabhava/ (8), shuddhi/ (5). Existing dirs absorbed nodes: spanda/ (+16), parampara/ (+5), chetan/ (+2), jiva/ (+5), geometry/ (+4), vak/ (+6), mula/ (+9), padartha/ (+2). Only 13 sthalam meta-nodes + visheshanam remain at top level. 4 ungrouped nodes remain (from 101). Tests: 78 passed / 39 xfailed / 0 failed — identical before and after.

## aneka family (aneka, eka-aneka, aneka-aneka, aneka-eka, eka-eka) are all sambandha-swarupa — types of relation by cardinality. Placed together in sangati/sambandha/ along with dvaya, sama-kalana, sangati, sambandha itself. The sub-bucket principle: nodes that share swarupa (IS-A) or abheda (equivalence) with the same root belong together.

## Phase A complete: 12 graph-only edits to sangati. Created bhasha node (21 swarupa chains unblocked), gave swarupa to subanta/avyaya/bhave-prayoga/karma/krama/viveka, added pratipaksha pairs (kshaya↔vriddhi, avrti↔sthiti, guna↔karma, prayoga triad), created 6 ghost nodes (artha, setu, tantra, upakarana, shakti, eka), created yantra-varga. Result: sangati 20→1 components, 0 islands.

## Parser upgraded: added amsha (part-of), drishthanta (example), rahita (devoid-of) to RELATION_SUFFIXES. Fixed greedy regex bug — non-greedy *? was matching shortest prefix (math-varga-vishesa → math+varga), greedy * correctly matches longest (math-varga+vishesa). Made RELATION_SUFFIXES and LAYERS dynamic constants — regex, analysis, health all derive from single source. Impact: 14/14 relations active, kosha 69→27 components, 368 fewer orphans.

## Moved sangati-old/ (158 old-format nodes with wave equations, proofs, epochs) from brahman/ to history/sangati-old/. These were polluting the parse — old format nodes were being loaded alongside current sangati. Now only current-format nodes are parsed.

## Shabda separation design: shabda (surface words) should live separately from .om node definitions. .om files are pure structure — layer, name, slokas, done. Shabda files use the same key-value format the codebase already parses. Directory: brahman/shabda/ with composable files by domain (sangati.shabda, physics.shabda, math.shabda, english.shabda, yantra.shabda). Each entry: header line (shabda node-name), indented properties (word:, desc:, eval:, arity:, matra: etc.). OCaml reads natively via existing parse_shabda_file. Can emit JSON for Python tools. No new parser needed.

## Bridge node resolution design (Option C): instead of rewriting 90+ kosha .om files to use Sanskrit names, the shabda file injects synthetic abheda edges into the graph at load time. sangati-english.shabda maps English words to sangati concepts (interference→samsarga, polarity→shiva-shakti, etc.). om_parser reads the shabda file after .om loading and creates abheda edges — same as what the 80 bridge .om files did, but from one file. resolve_to_canonical, to_english, word_index all work unchanged.

## Surgical edit API: built om_writer.ml + om_edit.ml in OCaml. 14 socket commands for creating/editing/deleting .om files, shabda entries, tantra files, and comments. Pattern: disk first → graph update → CSR rebuild. Python vy.py client has matching methods. CLI: vy add-sloka, vy set-comment, vy add-edge etc. Six typed comment prefixes: desc, not, example, usage, see, math.

## Shabda separation complete: extracted 1250 inline shabda lines from .om files into 41 domain-grouped .shabda files in brahman/shabda/. OCaml loads shabda store at startup (setu_shabda.load_shabda_dir). Fixed 7 call sites that read n.shabda directly to use raw_shabda_for_node or _shabda_store. .om files are now pure structure: layer, name, slokas, comments, done. All tests pass 29/39/0.

## Tantra4 spec: the system knowing itself as the knower. Five philosophical angles — krama-viveka (self-ordering from janya/phala DAG), pramana-sreni (full provenance chains), aprameya-bodha (diagnosing why 'no match'), chhanana-krama (pipeline as algebraic filtration), spanda-delta (semi-naive: only the new vibrates). Connected to Datalog stratified evaluation and Gödel incompleteness. Core mechanism: create yantra .om nodes for all 74 tantras, making the pipeline visible to itself via the same graph-walk used for physics.

## Pipeline architecture encoded in graph: 20 .om nodes (7 layers + 9 refine steps + 4 dispatch paths) with krama/janya/phala/kriya edges. walk pipeline-construct krama 7 gives the full sequence. 86 flat tantra nodes reduced to 20 meaningful architectural nodes. Key insight: krama edges encode ordering, janya/phala encode data flow, kriya connects to implementing tantras. Three composition types: sequential (krama chain), fixpoint (avrti-refine), conditional (dispatch paths).

## The 7 abstract patterns (filter-collect, scan-accumulate, shabda-read, walk, fixpoint, apply-op, om-read) already exist as kosha nodes: transducer, endomorphism, morphism, fold, op-fixpoint, op-filter, op-map. No new nodes needed — just abheda edges connecting each pipeline layer to its mathematical identity. pipeline-construct IS transducer, pipeline-refine IS endomorphism under op-fixpoint, dispatch-viveka IS fold, etc. The graph now knows not just WHAT runs in WHAT ORDER (krama) but WHAT EACH LAYER IS mathematically (abheda).

## Tantra4 rewrite is not just the orchestrator — 42 tantras (2762/3532 lines) contain hardcoded logic the graph already declares. 81 string literal edge names, 5 hardcoded word lists, 3 unrolled loops, ~20 inline op dispatches. Each replacement converts a hardcoded string into a graph walk, increasing connection density. Template: derive-step already uses om-contract to read janya/phala/kriya in one call — zero hardcoded concept names. Estimated: 3532 lines → ~2800 lines with dramatically more graph connectivity.

## tantra3 parser does not support 'return [a, b, c]' — must bind list to variable first: 'result = [a, b, c]' then 'return result'. All other tantras follow this pattern.

## Phase 2 partial: derive-chain rewritten to use fixpoint (80→60 lines, no arbitrary 3-step cap). count-bandha hardcoded word lists (23 words) replaced with shabda reads from common-sense-events and count-signals. viveka-ganana and invert-math already clean — no changes needed. Remaining Phase 3: assertion-bandha copula/quantifier word lists need shabda entries first, sandhi-avastha avastha-modifier words need shabda entries.

## S-expression shabda migration exposed two latent bugs: (1) emit-triples used word-node to detect units but word-node just means 'resolves via shabda word key' — fixed to check concepts-for-unit instead. (2) concepts-for-unit was in inheritable_keys, leaking from radian to ALL physics concepts — removed from inheritance. Both bugs were masked by the old flat format's ambiguous parsing where word: values included trailing text.
