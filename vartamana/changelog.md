# Changelog

**Single source of truth for baseline and session-by-session progress.**

The baseline is the test suite result at the end of each working session.
Do not update this mid-session — only when a session is complete and tests pass.

---

## Current baseline

**392 passed / 18 xfailed / 0 failing** (2026-03-17)

Pre-existing failures (not regressions):
- `test_session_ownership_persists` — Gap 2, session entity structure not yet carried
- `test_electron_paragraph_ke` — dvandva / multi-entity KE computation not yet built

---

## Sessions

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
