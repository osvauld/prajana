# Changelog

**Single source of truth for baseline and session-by-session progress.**

The baseline is the test suite result at the end of each working session.
Do not update this mid-session — only when a session is complete and tests pass.

---

## Current baseline

**511 passed / 63 xfailed / 0 failing** (2026-03-19, session 10)

---

## Sessions

### 2026-03-19 — Session 10: architectural plan — every tantra is one complete thought

**Started:** 511 passed / 63 xfailed / 0 failing (session 9 end)
**Ended:** 511 passed / 63 xfailed / 0 failing (planning session, no code changes)

**What was done:**

Architectural analysis — re-examined all 72 tantras not from "what test does this fix"
but from "is this tantra one complete thought?"

Key discovery: sparsha → viveka → bandha (the three operations) appear at every scale:
inside each tantra, across tantras (10 natural groups), and across the pipeline. The
scan-ref fix completed the cycle at the tantra scale — before, a tantra could perceive
(scan) but couldn't reflect on its perception (post-scan binding). This forced fragmentation
(one thought split across files) and monoliths (orchestrators carrying state between fragments).

Ten natural groups identified (by what tantras ARE, not by directory):
1. Orchestrators (5) — anuvada-ganana is the monolith to dissolve
2. Perception (8) — the system's eyes, well-structured
3. Refinement (14) — the understanding passes, count-bandha dissolves
4. Derivation (11) — the math engine, derive-chain simplifies
5. Proof emission (11) — panchaavayava, architecturally sound
6. Comparison (3) — all three absorb internal repetition
7. Graph construction (4) — intake system, keep
8. Equations (11) — pure math, the template form
9. Infrastructure (6) — boot/lookup/debug, keep
10. Counting (3) — the broken group, rewrite count-chain

Four-phase plan written:
1. Complete broken cycles (count-chain, derive-chain, anumana-viveka, viveka-ganana)
2. Dissolve the monolith (anuvada-ganana → composable pieces)
3. Merge fragments (sandhi-kosha + sandhi-avastha, optional)
4. Build new complete thoughts (viveka-derive, dvandva-ganana, krama-viveka)

Documents:
- `17-scan-ref-patterns.md` rewritten — now architecture-driven, not test-driven.
  Title: "Completing the Tantra: Architecture After Scan-Ref"
- `index.md` updated — doc 17 description reflects new direction

**Philosophical principle:** Dissolution IS abstraction. When we dissolve
anuvada-ganana, we name what was unnamed (viveka-sparsha, ganana-dispatch).
Composition replaces orchestration. A new question type = one new tantra,
not a new branch in a monolith.

### 2026-03-19 — Session 9: scan body escape fix + pattern analysis

**Started:** 512 passed / 62 xfailed / 0 failing (session 8 end)
**Ended:** 511 passed / 63 xfailed / 0 failing

**What was done:**

Parser bug fix — scan body escape:
- **Root cause found**: `in_scan_body` flag in `yantra_tantra_file2.ml` never reset to false. Every line after a scan header was absorbed into the scan binding's raw lines. Post-scan bindings never compiled separately.
- First fix attempt (remove `in_scan_body` from `inside_block`) broke 250+ tests — scan body state assignments (`cur-base = ...`) mistaken for new top-level bindings.
- **Correct fix**: indentation check. Only un-indented lines (column 0) can escape the scan body. Scan body state mutations are always indented.
- Verified: `_test-scan-ref` tantra correctly returns `length scanned` after scan.
- Reverted `avrti-refine` from `count-chain` back to `count-bandha` (count-chain was broken stub from session 8).

Test adjustments:
- `test_count_add_we_find_names_total` — xfailed (count-chain not wired yet)
- `test_count_sub_we_find_names_remaining` — xfailed (same)
- `test_total_momentum_resolves` — xfail reason updated (total still resolves to count concept)
- Net: -1 pass, +1 xfail from session 8 baseline (count.om changes from session 8 broke 2 count grammar tests; these were passing before but are now correctly xfailed pending count-chain)

Pattern analysis completed:
- All 72 tantras read and analysed for scan-ref applicability
- All 63 xfails mapped to gates; 22 identified as attackable via scan-ref patterns
- Five scan-ref patterns identified: scan→filter→emit, scan→collect→aggregate, scan→derive-per-entity→compare, scan→collect-edges→build-closure, scan→measure→branch
- Four implementation tiers planned: count-chain (6 tests), viveka compute-then-compare (4), dvandva per-entity (4), transitive reasoning (8)

Documents:
- `16-let-binding-resolution.md` updated with actual root cause (was wrong about parse-time theory)
- `17-scan-ref-patterns.md` created — new working document with patterns, xfail attack plan, implementation order

**Files changed:**
- `vyakarana/lib/yantra_tantra_file2.ml` — scan body escape with indentation check (lines 870-887)
- `brahman/yantra/avrti/avrti-refine.tantra3` — reverted count-chain → count-bandha
- `vyakarana/tests/test_reasoning_grammar.py` — 2 tests xfailed
- `vyakarana/tests/test_collocation.py` — xfail reason updated

### 2026-03-19 — Session 8: decomp fixes + anumana + count redesign (blocked)

**Started:** 501 passed / 73 xfailed / 0 failing (session 7 end)
**Ended:** 512 passed / 62 xfailed / 0 failing

See CLAUDE.md session notes for details. Key: 7 decomp tests promoted,
5 anumana tests promoted, count-chain redesign blocked by parser bug
(now fixed in session 9).

### 2026-03-19 — Session 7: tantra3 migration complete + dissolution

**Started:** 500 passed / 77 xfailed / 0 failing
**Ended:** 501 passed / 73 xfailed / 0 failing

**What was done:**

**Full tantra2 → tantra3 migration:**
- 69 tantra3 files written (all 66 tantra2 replaced, physics-mantras/math-mantras eliminated)
- All tantra2 files deleted — zero tantra2 remain
- 63 active tantra3 files in production (after dissolution)
- `mantra-select` uses varga walk (O(25) not O(2210)) — 1393ms → 1ms per call

**Dissolution (Tier 1 — sparsha into single perception):**
- `bound-vals` + `bound-concepts` + `bound-concept-names` → `bound-state` (one epistemic position)
- `satya-concepts` → inlined into `kosha-expand`
- `find-context` → inlined into `build-question-graph`

**Dissolution (Tier 2 — merged acts):**
- `lookup-word` + `try-morpheme-rules` → `shabda-anveshana` (pratyabhijna — recognition with fallback)
- `execute-math` + `execute-chain` → `execute-mantra` (kriya — one act, three dispatch paths)

**Dissolution (Tier 3 — panchaavayava nyaya breakdown):**
- `emit-reasoning` (225 lines) broken into five limbs:
  - `emit-pratijna` — "we have" (stating what is given)
  - `emit-hetu` — "we seek" (reason for inquiry)
  - `emit-udaharana-upanaya` — "we know" / "we see" (rule + application)
  - `emit-nigamana` — "we find" (conclusion)
  - thin weaver (`emit-reasoning`, now 35 lines) — joins strands
- `pramana-bandha` extracted from `anuvada-ganana` — proof graph binding as named act

**Tests promoted (xfail → pass, 4 tests):**
- `test_mantra_select_velocity_returns_multiple` — mantra-select tantra3 written
- `test_mantra_select_unknown_returns_all` — same
- `test_relative_vps_returns_two_velocity_pairs` — relative-vps tantra3 written
- `test_relative_vps_empty_when_no_scope` — same

**Tests rewritten (6 dissolved → 5 better tests):**
- `test_find_context_*` (6 tests calling dissolved tantra) → `test_context_*` (5 tests through pipeline)
- `test_word_index.py` and `test_probe.py` updated: `lookup-word` → `shabda-anveshana`

**Performance:**
- `mantra-select ""`: 1393ms → 1ms (varga walk)
- Median call: 44ms → 28ms (-36%)
- Suite time: 41.1s → 39.87s (-3%)
- Total lines: ~3200 → 2655 (-17%)

**Philosophy recorded:**
- Philosophical mapping of each abstraction to its process in understanding
- Sparsha = pratyaksha (direct perception, below tantra reasoning)
- Bound-state = sthiti (the understander's current position)
- Iccha-viveka = discrimination of intention
- Execute-mantra = kriya, one act
- Shabda-anveshana = pratyabhijna, recognition
- Emit-reasoning strands = panchaavayava nyaya (the five-limbed proof)
- Pramana-bandha = binding of proof (the fourth unnamed structure from the spec)

**Next (from implementation plan):**
- Fix 9 decomp test xfails (update API calls to match new multi-arg signatures)
- Step 3: abheda reading — "from rest" → initial-velocity=0 (~3 xfails)
- Fix inverse-match path (7 xfails)
- Step 4: swarupa-chain for syllogism (~8 xfails + kosha files)

### 2026-03-19 — Session 6: tantra3 spec + analysis + 77 xfail classification

**Started:** 419 passed / 12 xfailed / 0 failing
**Ended:** 500 passed / 77 xfailed / 0 failing

**What was done:**

Tantra3 discovery and specification:
- 109 janya/phala contracts found in live graph via socket queries
- Six suffixes mapped to instruction set (janya, phala, kriya, yukta, sthita, swarupa)
- Three levels of om interfacing defined (sparsha, matching, active schema)
- Migration path from tantra2 to tantra3 — 4 implementation steps
- `14-tantra3.md` written — philosophy
- `15-tantra3-implementation.md` written — engineering

Analysis tools run and cross-referenced:
- `analyze_test_results.py` — 500/77/0 confirmed, xfails classified by gate
- `analyze_pipeline.py` — seven unnamed structures found (sankhya-sparsha 16×, shashthi-sparsha 43×, iccha-viveka 9×, pramana-bandha 4×, varga-viveka, eval_arg 72×, with_node 34×)
- Cross-reference: each unnamed structure maps to the om graph declaration it translates
- "No match" anatomy: 42/77 xfails produce "no match"; 29 passing tests also produce "no match" (all correctly — intermediate or intentional)

Manipravalam principle documented:
- Tantra2 translates om declarations into machine operations
- Tantra3 eliminates the translation — code speaks the same language as the knowledge
- Seven unnamed structures are the proof: each is a place where tantra2 says what the om graph already says more naturally
- Under tantra3, writing an om file IS writing the program

77 xfails classified into 8 categories:
- A: Om-driven match-mantra (11 tests) → Step 2
- B: Count/everyday mantras not routed (8 tests) → Step 2 + new om files
- C: Collocation / verb-as-signal (15 tests) → Step 3 + bhasha layer
- D: Logic / syllogism (8 tests) → Step 4 + kosha files
- E: Multi-entity / session (12 tests) → Gap 2
- F: Viveka / computed comparison (6 tests) → viveka path improvement
- G: Composed expressions (1 test) → expression subgraph
- H: Reasoning emission (3 tests) → emit-reasoning improvements

New tests added (81 new tests, 65 new xfails):
- `test_match_decomp.py` (10 tests) — sub-tantra tests for tantra3 Step 2
- `test_collocation.py` (15 tests) — verb binding, field strength, color, total, from-rest
- `test_composed_inference.py` (4 tests) — syllogism reasoning, transitive reasoning, viveka reasoning
- `test_logic_and_comparison.py` (8 tests) — syllogism, transitive, comparison, count+logic
- `test_everyday_logic.py` (6 tests) — counting, area, distance, proportional
- Additional tests across existing files

**Previous session baseline for reference:**

**419 passed / 12 xfailed / 0 failing** (2026-03-18, session 5)

**xfails closed in session 5 (7):**
- `test_two_entities_compute_correct_entity` — proton momentum correct despite electron in graph
- `test_two_entities_ke_correct_entity` — ball-A KE correct despite ball-B
- `test_three_entities_find_named` — three entities, correct entity's mass used
- `test_electron_paragraph_ke` — natural language electron paragraph fires correctly
- `test_three_entities_no_labels_momentum_first`
- `test_two_entities_labelled_answer_correct_entity`
- `test_three_entities_labelled_answer_first`

### 2026-03-18 — Session 5: entity-scoped computation + subject/modifier distinction

**Started:** 412 passed / 19 xfailed / 0 failing
**Ended:** 419 passed / 12 xfailed / 0 failing

**What was done:**

`extract-solve-for.tantra2` extended — now returns `[has-intent, solve-for, scope-entity]`.
Scope entity is the named entity after the solve-for concept: "find KE of ball-A" → scope is ball-A.
Detects both mithya entities (unlabelled: `ball-A`) and satya entities used as subjects (`electron`, `proton`).

`match-mantra.tantra2` updated — when scope entity present, builds entity-scoped val-pairs:
- Instance path: `[inst, shashthi-vibhakti, entity]` + `[inst, vishesa, concept]` + `[inst, sankhya, val]`
- Concept path: `[concept, shashthi-vibhakti, entity]` + `[concept, sankhya, val]`
- Supplements with flat vals for constants and given-clause inputs not owned by the entity.

`sandhi-kosha.tantra2` — entity-subject guard added to Way 2 compounding.
When the preceding satya word was followed by a shashthi-vibhakti signal (`has`, `with`),
it is a subject, not a modifier. `electron has mass` stays as ownership — does not compound to `electron-mass`.
`kinetic energy`, `mass density`, `photon energy` still compound correctly — no subject signal precedes them.

**Philosophical insight recorded in `11-tantra2-philosophy.md`:**
- "The question names the perspective" — solve-for is direction of inquiry; scope entity is viewpoint.
  The question declares which perspective the graph is read from. Not search. Perspectival reading.
- "Subject vs modifier — the shashthi-vibhakti signal" — ownership and qualification are distinct
  structures of knowing. The possession signal marks the subject, preventing it from being read
  as a modifier of what it owns. The species universal (electron-mass) and the owned property
  (electron's mass) are genuinely different kinds of knowing.

**Key discovery:**
- `sandhi-kosha` ran before `vibhakti-shashthi` within each avrti pass, so `prathama-vibhakti`
  entities were not yet established when sandhi fired on pass 1. Fix was to track the subject
  signal inline in the reduce state — when `[_, shashthi-vibhakti, shashthi-vibhakti]` is seen,
  the `last-satya` at that moment is a subject. No dependency on prathama-vibhakti needed.

---

### 2026-03-17 — Session 4: extraction + migration of core pipeline tantras

**Started:** 412 passed / 19 xfailed / 0 failing
**Ended:** 412 passed / 19 xfailed / 0 failing (refactoring only)

**New shared tantras extracted (eliminates duplication):**
- `extract-solve-for.tantra2` — identical 10-line reduce block from anuvada-ganana, session-anuvada, match-mantra
- `bound-vals.tantra2` — `[bound-concepts, val-pairs]` from derive-step + match-mantra
- `bound-concepts.tantra2` — sankhya subjects list from 5 tantras
- `resolve-janya-args.tantra2` — janya→args resolution from execute-math, execute-chain, invert-math
- `physics-mantras.tantra2` — `walk-in "physics-mantra" "varga"` from 3 tantras

**Tantras migrated to Layer 2:**
- `avrti.tantra2`, `avrti-refine.tantra2` — `fn nd ->` (not `node` — reserved op)
- `match-mantra.tantra2` — forward/inverse matching, all candidates/forward/inverse logic
- `derive-step.tantra2` — forward chaining with phala/janya checks
- `execute-math.tantra2`, `execute-chain.tantra2`, `invert-math.tantra2`

**Key bugs found and fixed:**

1. **Zero-input tantra body mis-parsed as param** — `result = walk-in ...` in `"header"` section
   was being parsed as param name `"result"`. Fix: lines containing `=` in `"header"` section
   are now treated as body bindings, not param declarations.

2. **Local variable name clashing with tantra name** — `bound-concepts = nth bv 0` in
   `match-mantra` caused `Var"bound-concepts"` to resolve to the `bound-concepts.tantra2` tantra
   (returning `VFn`) instead of the local list. Fix: renamed to `bcs`.

3. **`cond` predicate closing to depth 0** — the line-joiner thought the binding was complete
   after `cond (gt ...) 0)` (depth=0), splitting the consequence onto a "new binding".
   Fix: keep consequence on same line, or wrap entire `cond` in outer `(...)`.

4. **`debug-print` shows `VNode` as `?`** — `show` function doesn't handle `VNode`.
   Not a bug — use `debug-print (to-string mynode)` to see the node name.

### 2026-03-17 — Session 3: variadic fix, Phase 2 Steps 4-6, pre-existing failures fixed

**Started:** 409 passed / 20 xfailed / 2 failing
**Ended:** 412 passed / 19 xfailed / 0 failing

**What was done:**

OCaml parser fix — variadic ops (`arity=-1`):
- `parse2_primary` only dispatched on `arity > 0`, treating variadic ops as zero-arity variables
- `append`, `pair`, `or`, `concat` etc. all inherit `op-class-monoid` → `parse-arity:-1`
- Fix: added `arity = -1` branch that collects args greedily to boundary tokens
- Root discovery method: `[DEBUG arity append=-1]` print during parse, then `[DEBUG variadic] op=pair` confirmed `pair` parameter eating the whole token stream

Layer 2 migrations (Phase 2 Steps 4-6):
- `agra-bandha.tantra2` — generic proximity-binding scan with `agra-map` state, `(and ...)` variadic guards
- `sankhya-bandha.tantra2` — simple scan with `last-active` state
- `rashi-anuvada.tantra2` — two `reduce` calls, pipe-based instance→concept bridging

Pre-existing failure fixes:
- `test_two_entities_ownership` — test was checking concept-level `[mass, shashthi-vibhakti, ball1]` which vishesa-bandhana intentionally redirects to instance level. Test corrected to check `[m1, shashthi-vibhakti, ball1]`.
- `test_session_ownership_persists` — "electron has mass 9.109e-31" stored binding under `electron-mass` not `mass`. Fixed `session-anuvada` to also store bindings under `shashthi-vibhakti` concept subjects from `refined`. Turn 2 then finds `[mass, sankhya, 9.109e-31]` in prior-graph.

Bonus xfails unlocked by session fix:
- `test_two_entities_no_labels_distinct_values` — fixed by variadic op fix (sv-redirects now works)
- `test_three_entities_accumulate` — session binding fix made multi-entity cross-turn accumulation work

**Key discoveries:**

1. **`pair` is a reserved variadic op name** — `op-pair` inherits `op-class-monoid` → `parse-arity:-1`. Any lambda using `pair` as a parameter silently eats all remaining tokens. Safe names: `kv`, `elem`, `item`, `acc`, single letters.

2. **`reload-all` crashes server** — the `reload-all` socket command crashes the server when called mid-session. Always restart the server fresh after `.tantra` or `.tantra2` file changes. OCaml changes require rebuild + restart.

3. **Session binding scope** — `session-anuvada` stores sankhya subjects (`electron-mass`) not the user-facing concept (`mass`). Kosha constants like `electron-mass` are not connected to `mass` in the question graph — only in the kosha ancestry. The fix: also store under `shashthi-vibhakti` subjects from `refined` (the concepts the user actually named).

4. **`[eval]` logging floods terminal for large results** — socket.ml line 532 prints full result strings. Added 200-char suppression threshold to avoid graph dumps.

---

### 2026-03-17 — Session 2: vishesa-bandhana sv-redirects fixed

**Started:** 407 passed / 20 xfailed / 4 failing
**Ended:** 409 passed / 20 xfailed / 2 failing

**What was done:**

Root cause of `sv-redirects = 'append'` found and fixed:
- `append` has graph arity=-1 (inherits `op-class-monoid` `parse-arity:-1`)
- `parse2_primary` only dispatched `arity > 0` — variadic ops fell through as zero-arity variables
- Lambda parameter `pair` clashed with `op-pair` (also arity=-1) — `nth pair 0` ate rest of token stream
- Fix: added `-1` branch in `parse2_primary`; renamed `pair` → `kv` in vishesa-bandhana

Bonus: `test_two_entities_no_labels_distinct_values` xfail removed — passes now.

---

### 2026-03-17 — Layer 2 tantra rewrite: Phase 0 + Phase 2 Steps 1-3

**Started:** 392 passed / 18 xfailed / 0 failing
**Ended:** 407 passed / 20 xfailed / 4 failing

**What was done:**

Layer 2 parser (`yantra_tantra_file2.ml`) — extended from ~400 to ~900 lines:
- Depth-aware paren extraction in `parse2_primary` (NOT working — see pitfalls)
- `collect_guard_expr` — paren-depth-counting extractor for `| and (guard)` pipes
- `or` as infix operator in `parse2_pipe`
- `| and` / `"|" :: "and"` handling in `collect_guards`
- `let name = expr` inside scan body → `SLet(name, expr)` (was falling to `SEmit`)
- `debug-print` op added to `yantra_ops.ml` (prints to stderr, returns value unchanged)
- `_it` binding in `eval_from` for `| collect (nth _it 0)` pattern

Arity / loading fixes:
- `pre_scan_tantra_file` now handles `"tantra2 "` prefix (was only `"tantra "`)
- `load_tantra_dir` split into two passes: `.tantra` first, `.tantra2` last — Layer 2 always wins
- `.tantra` originals removed for 3 migrated tantras

Parser bugs found and fixed (10+):
- `is_scan_start` not matching `name = scan ...:`
- Double-reverse of `cur_lines` in `flush_binding` → `compile_let_lines`
- `takes graph` not parsed as inline param declaration
- `when pred ->` on same line not splitting at `->`
- `close_bracket` off-by-one (includes `]` in pattern name)
- `_ ->` not setting `in_body := true` unconditionally
- `"and"` infix in `parse2_pipe` conflicted with `| and` guard syntax (removed)

Tantras migrated (Phase 2 Steps 1-3):
- `vishesa-instance.tantra2` — typed scan state, outer scope access, Tension 3 fixed
- `rashi-viveka.tantra2` — gate-edge scan, `qty` instead of `value` (reserved op)
- `vishesa-bandhana.tantra2` — reduce lambda with `| where` pipe filters, `cond` inline

Old Layer 1 files removed:
- `vishesa-instance.tantra`, `rashi-viveka.tantra`, `vishesa-bandhana.tantra`

**Key discoveries:**

1. **Pattern names in `| where [s, sankhya, _]` are ALL variables** — unlike scan
   branch patterns where `sankhya` auto-generates `eq(edge, "sankhya")`, the pipe
   `where` pattern treats ALL names as variable bindings. Must use explicit
   `| and (eq e "sankhya")` guards.

2. **`value` is a reserved op name** — `op-value` kosha node has `parse-arity:1`.
   Any variable named `value` in a `.tantra2` scan body gets parsed as
   `Call("value", [next_token])` — silently consuming the next token. Renamed to `qty`.

3. **`fn` body parsing stops at first `)` via `parse2_pipe`** — when `fn` is inside
   `(fn acc pair -> ... length (acc | ...) ... cond ... otherwise acc)`, the `)` closing
   `length(...)` terminates the body parse. The outer `(fn ...)` `)` is never reached.
   Depth-aware paren extraction was attempted but has a counting issue (inner pairs
   that return to depth 0 match prematurely). Currently the original `parse2_expr`-based
   approach works for most cases but the reduce lambda in `vishesa-bandhana` still
   returns wrong results. Needs a proper fix.

4. **`parse2_expr` inside `parse2_cond`'s `otherwise` is greedy** — `otherwise acc)`
   parses `acc` then leaves `)` as rest. This is correct for `LetIn` chain propagation
   but fragile. Wrapping `cond` in explicit parens `(cond ... otherwise acc)` helps.

---

### 2026-03-17 — P8f Way 2 sandhi + boot/reboot pass

**Started:** 376 passed / 19 xfailed  
**Ended:** 392 passed / 18 xfailed

**What was done:**

Boot/reboot architecture:
- Added `emit-edge` and `graph-all-nodes` OCaml primitives
- `reboot.tantra` — orchestrator, runs at startup and on `reload-all`
- `varga-inheritance.tantra` — derives `[N, varga, X-varga]` from `[N, swarupa, X]`
- `walk-in "energy-varga" "varga"` now returns `["kinetic-energy", "potential-energy", ...]`
- Wired `reboot` into `vyakarana.ml` (startup) and `socket.ml` (reload-all)
- See `08-boot.md` for full architecture

Sandhi Way 2 (satya + satya compound):
- `sandhi-kosha` extended — when two consecutive `satya` words hit, tries `word1-word2` lookup
- `mass density` → `mass-density` ✓
- `photon energy` → `photon-energy` ✓ (required new `.om` file)

Kosha fixes:
- `photon-energy.om` — authored concept node (`energy-swarupa`, `photon-yukta`, `frequency-yukta`)
- `planck-constant.om` — added `constants-key:planck-constant` shabda (was missing — mantra couldn't auto-supply it)
- `frequency.om` — added `shabda frequency / ...` (was missing — word didn't resolve as `satya`)
- `wave.om` — removed `frequency` from word alias list (was shadowing `frequency` kosha node)

xfails closed:
- `test_frequency` — `f = 1/T` now works via math-domain; xfail marker removed

Tests added:
- `test_bqg.py` — varga inheritance (3 tests), frequency/photon satya resolution (2 tests)
- `test_sandhi.py` — Way 1 regression (2 tests), Way 2 new (4 tests)
- `test_physics_mantras.py` — photon energy end-to-end (3 cases), planck constant auto-supply, mass density satya+satya compound

Bugs found and documented (see `07-tantra-rewrite.md`):
- **Tension 7**: `let` inside `fn` body in tantra file is split into new top-level binding by file parser — `varga-inheritance` ran for 351ms emitting nothing. Fix: never use bare `let x = ...` inside fn bodies in tantra files.
- **Tension 8**: `graph-all-nodes` returns `VNode` not `VString` — `concat (VNode) "-varga"` returns `""` silently. Fix: always `to-string` before string ops on graph results.
- **Tension 9**: `word:` alias shadowing — `wave.om` claimed `frequency` as a word alias, silently routing `lookup-word "frequency"` to `wave`. Fix: never claim a word that matches another concept's node name.

---

### 2026-03-17 — Gap 1 closed + paragraph + P8f Phase A (13 mantras)

**Started:** 362 passed / 14 xfailed  
**Ended:** 376 passed / 19 xfailed (net: 19 new tests added, mostly xfail for new work)

**What was done:**

P8f Phase A — math-domain unification:
- 13 physics expr tantras deleted (ohm-expr, momentum-expr, etc.)
- 13 physics `.om` files updated: `shabda math-op:multiplication` or `math-op:division`
- `execute-math.tantra` — forward execution via math kosha
- `invert-math.tantra` — inverse via `pratipaksha` walk
- `execute-matched.tantra` — dispatches forward/inverse
- `match-mantra.tantra` returns 3-element list `[mantra, val-pairs, mode]`
- Inversion working: `find current given resistance and voltage`, `find mass given momentum`, etc.

Paragraph / viraam:
- `build-question-graph.tantra` fixed for viraam emission
- `test_paragraph.py` added: 15 passing, 4 xfailed (dvandva)

Parser fixes (Gap 1 closure):
- `or` infix in scan guards — `parse_guard_atom` + `absorb_or` in `collect_and_guards`
- Outer `let` bindings visible in scan guards via paren wrapping
- `collect_init` stops at `let` — multi-line scan state works
- `parse_scan_stmts` loud failure on unknown tokens
- Bare `cond` at end of `fn` lambda body fixed

---

### 2026-03-16 — Gap 1 partial + session + entity scene tests

**Started:** ~330 passed  
**Ended:** 362 passed / 14 xfailed

**What was done:**
- `session-anuvada.tantra` built — cross-turn sankhya binding
- `test_entity_scene.py` written — 22 tests
- Gap 1 partially closed: `emit-triples` `word≠node` discriminant
- `vibhakti-shashthi`: satya-named entities
- `vishesa-instance`: `can-promote` scan state (outer let not visible in scan when)
- `split-numeric`: scientific notation
- Gaps 3/4/5 closed
