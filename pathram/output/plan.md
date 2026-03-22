# Plan — What Remains to Build

## Step 3: Dissolve anuvada-ganana into mode dispatch ←

anuvada-ganana is currently a 133-line monolith that handles all utterance types inline. Every utterance to the proof graph IS a vibhakti relation — the routing problem is not "classify intent" but "read the vibhakti."

**The dissolution**: anuvada-ganana becomes a thin dispatcher that detects the mode and calls the appropriate tantra. Each mode gets its own tantra.

| Mode | Vibhakti | Detection | Current state |
|---|---|---|---|
| **sambodhana** | vocative | "Hello", "Hi" → greeting words | Not built |
| **darshana** | nominative | "What is X?" → vidhi-kaala + satya + NO sankhya | Not built |
| **prajna-dana** | accusative | "ball has mass 5" → NO vidhi-kaala, NO prashna | Not built |
| **ganana** | imperative | "Find KE" → vidhi-kaala + sankhya | Current path (physics/count/viveka/anumana) |

After dissolution, anuvada-ganana becomes:
```
mode = detect-mode graph
cond (eq mode "sambodhana") (sambodhana-response graph)
     (eq mode "darshana")   (darshana-response graph)
     (eq mode "prajna-dana") (prajna-dana-response graph)
     otherwise              (ganana-response graph)
```

The ganana path IS the current anuvada-ganana body (physics, count, viveka, anumana). It moves into its own tantra.

## Step 3.0: Sambodhana — existence acknowledgment

"Hello" = sambodhana (vocative). The speaker acknowledges the proof graph exists.

**Build:**
1. bhasha grammar nodes: greeting-hello.om, greeting-hi.om, greeting-hey.om
   - "sambodhana-sthita" → connects to sambodhana vibhakti
   - shabda word:hello role:grammar
2. In BQG/emit-triples: detect sambodhana words (via sthita walk)
   - Emit [word, sambodhana, vyakarana] triple
3. sambodhana-response tantra: detect sambodhana in graph → acknowledgment
   - Response from anuvada-setu.shabda: speech-sambodhana: I am here
4. Add "sambodhana-yukta" to visheshanam-ring

**Verify:** python3 -m tools ask "hello" → "I am here"

## Step 3.1: Darshana — what is X?

"What is mass?" = darshana (nominative). The speaker asks what the graph KNOWS about a concept, not what it can COMPUTE.

**Detection:** vidhi-kaala present + satya concept present + NO sankhya values → darshana mode

**Build:**
1. darshana-response tantra: walks concept edges, shabda, connections
2. Routes to existing node-info builtin in OCaml
3. Formats via anuvada-setu

**Verify:** python3 -m tools ask "what is mass" → "mass is a quantity. units: kilogram. appears in: momentum, kinetic-energy, ..."

## Restructure sangati/ by darshana — split mula(47→15), create viraam/(6), pramana/(8), vidya/(4), move 100 ungrouped nodes to correct sthalams ✓

## Enrich nam with Advaita Vedanta — connect to chetan/ (sakshi, pratibodha, prajna, darshana, lekhana-pratibodha). Add atman, pratyabhijna. Nam = atman = brahman = the graph recognizing itself.

## Step 3.2: Prajna-dana — knowledge intake

"A ball has mass 5kg" (statement, no question) = prajna-dana (accusative). The speaker gives knowledge to the graph.

**Detection:** NO vidhi-kaala + NO prashna → statement mode

**Build:**
1. prajna-dana-response tantra: accept BQG triples as session state
2. Echo back parsed knowledge as acknowledgment

**Verify:** python3 -m tools ask "a ball has mass 5kg" → "ball: mass = 5 kg"

## Step 3.3: Proper noun recognition

Capitalized non-sentence-initial words are proper nouns (prathama-vibhakti entities).

**Build:**
1. OCaml primitive or BQG check: is-capitalized
2. If capitalized + not sentence-initial + not in kosha → emit [word, prathama-vibhakti, word]
3. Entity enters entity-registry subgraph

**Verify:** python3 -m tools vy parse "Tom has 5 apples" → Tom [prathama-vibhakti]

## Step 3.4: Pronoun resolution

"He", "She", "It" → resolve to last entity in entity-registry.

**Build:**
1. bhasha grammar nodes: pronoun-he.om, pronoun-she.om, pronoun-it.om
2. In emit-triples: detect pronoun → look up entity-registry → replace with entity name
3. Emit [entity-name, naama-pratibodha, pronoun-word]

**Verify:** python3 -m tools vy parse "Tom has 5 apples. He gives 2 to Mary." → He → Tom

## Steps 7-10: Post-dissolution computation

After anuvada-ganana is dissolved, the ganana path can be extended:

| Step | What | Gate it unblocks | Xfails |
|---|---|---|---|
| 7 | viveka-derive: compute per-entity then compare | compute-then-compare | +2 |
| 8 | dvandva-ganana: per-entity instance-map + fold | dvandva | +3 |
| 9 | krama-viveka: transitive chain inference | transitive | +2 |
| 10 | anumana-ganana: logic ops + premise graph | logic_nyaya | +1 |

These depend on mode dispatch being clean (Step 3 / Step 6 done first).

## Priority order

**Implementation sequence:**

3.0 sambodhana → 3.1 darshana → 3.2 prajna-dana (dissolves anuvada-ganana)
→ 3.3 proper nouns → 3.4 pronouns (entity recognition)
→ 7 viveka-derive → 8 dvandva → 9 transitivity → 10 anumana

3.0 is first because it is simplest — just pattern detection + static response.
3.1 uses existing node-info builtin.
3.2 requires session integration.
After 3.2, anuvada-ganana is dissolved into mode dispatch + ganana-response.

## Signal emission: emit-triples emits graph-declared signals for all words ✓



emit-triples rewritten with word-info, word-resolve, is-direction helpers. shabda-anveshana now sole word resolution path — word-node only used internally. All consumer tantras switched from word-node to shabda-anveshana.

## Plural morphology: strip -s/-es/-ies to resolve stems, emit bahu-vachana signal

## Vibhakti signals: prepositions emit their vibhakti case (panchami from 'from', saptami from 'at', chaturthi from 'to')

## Tense signals: copula variants emit kaala (vartamana/bhuta) and vachana (eka/bahu)

## Distribution signal: add 'each/every/per' → distribution node with kriya→multiplication

## Motion verb binding: 'moves/moving' emit kartari-prayoga + velocity concept binding

## From-rest sandhi: panchami-vibhakti + 'rest' → initial-velocity=0

## Multiplication in count-chain: distribution signal triggers multiply instead of add

## Flip resolved xfails to passing tests (13 tests: 8 earlier + 5 from swarupa-anuvada)

## tantra4 created: 61 files with 4-layer composition (primitives → operations → structures → compositions). Signal bus via write-signals/read-signal. Pipeline tantras 26% smaller. Next: swap into live pipeline, test, om node updates for new helpers. ✓



tantra4 live: all 13 pipeline tantras + 48 helpers swapped into live pipeline. Old tantras moved to history/yantra_old/. Fixed 10 variable-name collisions (role→rl, pair→kv, base→base-graph, hit→found-node, found→matched, name→w, anumana-result→anumana-field). Fixed swarupa-anuvada propagating sankhya to direction nodes. Fixed count-chain aggregation path false-triggering on direction swarupa edges. 32 passed / 31 xfailed / 5 XPASS / 0 regressions.

## tantra4 live: old tantras moved to history, 10 collision fixes, swarupa-anuvada direction guard, count-chain aggregation guard. 32p/31x/5xpass. ✓

## S-expression tantra format: new .tantra4 parser in OCaml (yantra_tantra_sexp.ml). Reuse existing sexp tokenizer from setu_shabda.ml. (tantra name (params) body) syntax — last expression is return, (name expr) for bindings. Coexists with .tantra3. ✓

## Convert 56 tantra4 helpers to .tantra4 s-expression format. Most become single-expression tantras: (tantra has-text (w) (gt (string-length w) 0)). No variable bindings needed for simple helpers. ✓

## Convert 76 pipeline tantras to .tantra4 s-expression format. With semantic helpers, most become sentence tantras — body reads as prose with minimal variable bindings. ✓

## Sentence tantras: push abstraction until every cond branch is a single named call. Pipeline tantras read as natural language — the conclusion is the viveka conclusion or the physics conclusion.

## Stratify scan tantras: convert 14 scan tantras from stateful fold+pattern-match into stratified pipe chains. Each scan becomes multiple pure from/where/collect strata — no mutable state. Sentence boundaries via split-at-viraam, relational joins via named helpers. Eliminates scan as a construct. ✓

## Prakriya dissolution: 8 scan tantras dissolved into composable tantra4 files. 3 new helpers (proximity-bind, rewrite-subjects, find-after-signal) + 3 OCaml primitives (with-index, nearest-before, sentence-of). Zero .tantra3 or .prakriya files remain — all 139 tantras are .tantra4 s-expressions. ✓



All 8 scan prakriyas dissolved into composed tantra4 files. Intermediate .prakriya format created and then absorbed — prakriya concept lives on as a composition pattern, not a file format.

## Relational graph consumers: viveka-ganana uses ownership joins instead of positional scan. extract-solve-for uses grade-scoped queries. All 8 rewrite tantras grade-scoped. Positional helpers (proximity-bind, rewrite-subjects, find-after-signal) removed. append-triples made idempotent. 31p/33x/4xpass. ✓



Relational model working. 1 pass regression vs baseline (31 vs 32) — red_blue tests shifted from XPASS to XFAIL. Root cause identified: scan was flatmap (rewrite), prakriya was additive (append). Fix: grade-scoped sequential reduce within each sentence, relational joins across sentences. Three positional OCaml primitives (with-index, nearest-before, sentence-of) still in codebase but no longer used by any tantra.

## Remove 62 unused OCaml ops from yantra_ops.ml and yantra_eval_primitives.ml. Remove corresponding arity registrations. Includes: 3 prakriya primitives (with-index, nearest-before, sentence-of), 6 vector/matrix ops (vec-add/sub/scale/dot/norm, rot2d, mat-mul), dimension ops (dim-op, dim-to-unit, dim-kramanusara-depth), graph introspection (all-edges, graph-node-count, edge-weight, node-satya, etc), and misc (sort-desc, frequencies, first-match, etc). Build and test after. ✓



Removed 62 unused OCaml ops. Total: 8156→6295 lines, 22→21 modules. Removed scan eval+parser (~190 lines). Removed yantra_tantra_file2 from build. Switched sexp parser to Yantra_expr_parser. 31p/33x.

## Remove scan construct from OCaml: delete ScanStmt, scan_branch, SEmit, SSet, SClear from yantra_types.ml. Remove eval_scan from yantra_eval.ml. Remove scan parsing from yantra_expr_parser.ml and yantra_tantra_file2.ml. Remove scan-related boundary keywords from arity registration. No tantra uses scan anymore. ✓



Scan construct removed: eval_scan deleted (~80 lines), parse_scan deleted (~110 lines). Both replaced with failwith stubs.

## Extract shared expression parser from yantra_tantra_file2.ml. The sexp parser (yantra_tantra_sexp.ml) depends on tokenise2 and parse2_expr_string from the old tantra3 parser. Extract these into a standalone yantra_expr_core.ml module. Then yantra_tantra_file2.ml (956 lines) can be removed entirely — no more .tantra2/.tantra3 loading. ✓



Expression parser extracted: yantra_tantra_sexp.ml switched from Yantra_tantra_file2.parse2_expr_string to Yantra_expr_parser.parse_expr_string.

## Remove .tantra2/.tantra3/.tantra loading from yantra_index.ml and socket.ml. After expression parser extraction (step 31), these old format paths are dead. Remove tantra_files_recursive extensions for .tantra/.tantra2/.tantra3. Remove pre_scan_arities line-based scanner. Remove write-tantra tantra3 support from socket.ml. ✓



Old format loading removed: yantra_index.ml only loads .tantra4. socket.ml dump-ast uses sexp parser. pre_scan_arities uses sexp scanner only. yantra_tantra_file2.ml removed from dune build.

## Design om5 s-expression format. Target: (layer name (swarupa X) (yukta A B) (shabda (word W) (eval E)) (krama expr)). Key decisions: (1) edges explicit as (relation target...) — no compound suffix decomposition, (2) shabda inlined — no separate .shabda files, (3) mantra krama as evaluable s-expression — replaces krama edges + execute-chain, (4) one parser (extend yantra_tantra_sexp.ml tokenizer). Write format spec, convert 3-5 example nodes, verify roundtrip.

**[SUPERSEDED]** → plan.step-38

## Build om5 parser in OCaml. Extend sexp tokenizer to handle om5 format. Parse (layer name ...) into nigamana type with explicit edges. No two-pass name collection needed — edges are explicit. No decompose_compound. Shabda parsed from inline (shabda ...) block. Krama stored as expr for mantra nodes. Coexists with .om — both formats load, om5 supersedes same-name .om.

**[SUPERSEDED]** → plan.step-39

## Dissolve execute-chain into krama evaluation. Once mantra nodes carry krama as s-expressions, execute-chain OCaml primitive (stack machine over krama edges) is replaced by direct eval of the krama expression. The 28 eval: shabda ops become inline (krama (primitive args)) on mantra nodes. apply-op reads node krama, evals it. OCaml dispatch table shrinks to ~15 irreducible math atoms.

**[SUPERSEDED]** → plan.step-40

## Migrate 1579 om nodes from .om sloka format to .om5 s-expression format. Mechanical conversion: parse existing slokas, decompose compounds into explicit (relation target) edges, inline shabda from .shabda files. Write Python migration tool in tools/. Convert layer by layer: sangati (326) → kosha (996) → bhasha (156) → mantra (101). Test after each layer.

**[SUPERSEDED]** → plan.step-41

## Remove old om_parser.ml (373 lines) and setu_shabda.ml shabda file loader. After om5 migration, the two-pass compound decomposition parser, dynamic dimension discovery from visheshanam-ring slokas, and separate .shabda file loading are all dead. The sexp parser handles everything. Remove .shabda files (merged into .om5). Update tools/om.py and tools/shabda.py for new format.

**[SUPERSEDED]** → plan.step-42

## Om5 format design: (layer name (relation target...)...) — everything is an edge. No key-value properties. Arity → existing op-class kriya edges (binary→op-class-binary, unary→op-class-projection, variadic→op-class-monoid). Invertible/commutative/associative → (siddha concept) edges to ~3 new sangati nodes. Inverse → already (pratipaksha X). eval: not needed — derivable from op-* kriya edges. Only exception: (krama expr) on mantra nodes for evaluable s-expression formulas. Create sangati nodes: invertible, commutative, associative. Write spec, convert 5 example nodes, verify roundtrip.

## Om5 parser in OCaml: extend sexp tokenizer to parse (layer name (relation target...)...) into nigamana type. Edges explicit — no compound decomposition, no two-pass name collection. (krama expr) on mantra nodes stored as evaluable expr (reuse parse2_expr_string). Coexists with .om — om5 supersedes same-name .om nodes.

## Dissolve equation tantras into mantra krama: 10 equation tantras (ke-expr, velocity-expr, acceleration-expr, etc.) become (krama expr) on their 31 mantra om5 nodes. Today: tantra file (formula) + mantra.om (graph edges) + execute-chain (OCaml stack machine) = 3 things per equation. After: one mantra node IS the formula + graph edges. Remove execute-chain OCaml primitive. Remove krama edge walking from yantra_eval_primitives.ml. Remove 10 tantra files.

## Migrate 1579 om nodes to om5 sexp format. Python converter in tools/: parse existing slokas, decompose compounds into explicit (relation target...) edges, merge intrinsic shabda keys (eval/arity/invertible/etc.) as edges to concept nodes. Fix 21 files with slokas after done, split 1 multi-node file. Convert layer by layer: sangati (326) → kosha (996) → bhasha (156) → mantra (101). Test after each layer.

## Remove old parsers: om_parser.ml (373L, two-pass compound decomposition), execute-chain in yantra_eval_primitives.ml, krama edge walking, dynamic dimension discovery from visheshanam-ring slokas. The sexp parser handles everything. Update tools/om.py for om5 format. Remove intrinsic keys from .shabda files (eval/arity/invertible/symmetric/etc. now edges in om5). Shabda retains linguistic surface only (word/desc/alias/name/role/pos).

## Om5 conversion tool: tools/om5.py + cli_om5.py + om5_verify.py. 72 suffixes, 99/100 match vs OCaml. 8 om files fixed. ✓

## Ground 15 missing visheshanam dims: created sangati nodes + ring entries for janaka, rahita, lakshana, poorva, paschat, garbha, antya, nirodha, paripurna, daatri, vibheda, atita, bhanga, atikrama, purva. 188 edges unlocked. ✓

## Pipe operator in expr parser: added | tokenization + full pipe handling (where/collect/filter/map/all/any/find/reduce) to Yantra_expr_parser. Fixed pipeline regression. ✓

## Edge dimension tests: 72 passed / 7 xfailed in test_edges.py. L1 edge exists, L2 walk traversal, L3 graph self-reasoning (inverse plans, entity classification, robotics chain, pure math). ✓

## invert-krama tantra: multi-step formula inversion. Walk krama chain in reverse, pratipaksha each step. Unlocks KE→velocity, KE→mass, any multi-op mantra. Uses krama + pratipaksha + karma (varga validation) + lakshana (invertibility check). ←

## lakshana-query tantra: detect 'properties of X' pattern, walk lakshana dimension. Unlocks test_what_are_properties_of_algebra.

## karma-query tantra: detect 'operations in X' pattern, walk karma dimension. Unlocks test_what_operations_in_calculus.

## rahita-query tantra: detect negation/absence patterns, walk rahita. Unlocks test_what_is_jada_without.

## janaka-query tantra: detect generate/produce patterns, walk janaka. Unlocks test_what_does_vector_space_generate.

## torque-compute: add math-op:multiplication shabda to torque-mantra. Enables existing invert-math for robotics. Unlocks test_3dof_arm_torque.

## op-validity-check: pre-inversion validation via lakshana. Check inverse-element, closure, commutativity on varga before inverting. Structural safety net for all formula manipulation.
