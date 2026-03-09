# ~~Robotics + Graduate Motion Plan~~ [SUPERSEDED — see scene-comprehension-plan.md]
## Status: COMPLETE (partially implemented) — remaining items carried forward to new plan

### What was completed from this plan:
- Extended `binding` type with 4 new fields (timestamp, source, confidence, ttl) ✓
- Updated all binding construction sites across OCaml codebase ✓
- 22 new motion tantras (rotational, rolling, circular, projectile, SHM, friction, collisions) ✓
- `seema-pariksha.tantra` (threshold check) ✓
- Phase 1 build + test (rolling sphere 6.48 m/s ✓, SHM ✓, incline friction ✓) ✓
- CSR-backed PPR (previous session) ✓

### What was NOT completed (carried forward):
- Problem ingestion (PROBLEM...END) → scene-comprehension-plan.md Part F
- Configurable chain depth → scene-comprehension-plan.md Part F
- Binary cache (--cache flag) → scene-comprehension-plan.md Part F
- Robotics sensor demo → scene-comprehension-plan.md Part F
- Multi-entity resolver → superseded by scene-aware resolver in new plan

### Why superseded:
The design for multi-body physics revealed a deeper architectural need:
N-entity scene comprehension with root-sangati as structural grammar,
dynamic graph dimensions (sandhi, matra, krama as new visheshanam axes),
and concept-type matching in the resolver. These replace the "second-mass"
naming approach. The new plan builds on the completed work here.

---

---

## What This Plan Covers

Four interconnected goals:

1. **Graduate-level motion tantras** — 22 new tantras covering rotational dynamics, SHM,
   complete projectile analysis, circular motion, friction, collisions, and constraints.
   These fill the gap between what exists and what an engineering degree problem requires.

2. **Complex multi-line problem solving** — problem ingestion mode, configurable chain depth,
   multi-target resolution, and PPR-based context-aware binding disambiguation (Approach B).

3. **Robotics sensor demo** — high-frequency sensor stream (50Hz IMU) driving a tantra chain:
   force → torque → threshold → action. Same decomposition mechanism as text queries.

4. **Graph persistence + explicit binary mode** — `Marshal`-based binary cache for sub-10ms
   restarts. `--cache <path>` flag explicit; default stays parse-from-source.

Regular text input (`madakkal` REPL and JSON socket) is **unchanged throughout**.

---

## Measured Baselines

| Metric | Value |
|---|---|
| Cold start (parse .om + CSR) | 0.577s |
| Per-query latency (socket, running) | 1ms |
| Chain resolve max depth (current) | 4 steps |
| Chain resolve beam width (current) | 8 states |
| Session chaining overhead | 0ms (bindings in memory) |
| Graph nodes / edges (post-axiom) | 1556 nodes / 16,771 edges |
| .om corpus on disk | 1.62MB, 1393 files |
| Estimated marshalled binary | ~1–2MB |

---

## Part A: What Already Works (Baseline)

The session binding mechanism already decomposes problems. These work today with no changes:

```
"mass is 2, height is 3, what is potential energy"
→ sthithi-urja.tantra: PE = 2 × 9.8 × 3 = 58.84 J  ✓

"potential-energy is 58.84, mass is 2, what is velocity"
→ INVERSE of chala-urja.tantra: v = √(2×58.84/2) = 7.67 m/s  ✓
  (engine inverts KE = ½mv² automatically)

"force is 50, radius is 0.3, angle is 1.5708, what is torque"
→ tirupu.tantra: τ = 50 × 0.3 × sin(π/2) = 15 N·m  ✓

"initial-velocity is 0, acceleration is 3, time is 10, what is displacement"
→ sthana-antara.tantra: s = 0 + ½×3×100 = 150 m  ✓
```

**The decomposition is already the architecture.** Session holds intermediate results.
Each tantra is one step. Inverse solve finds unknowns automatically. The path from
`F is 20, a is 4, what is mass` to a 6-step rolling sphere problem is not an
architectural change — it is the same resolver applied to a richer tantra library
with a deeper search budget.

---

## Part B: The Tantra Gap

### Existing motion tantras (12)

| Tantra | Formula | Status |
|---|---|---|
| `antya-vega` | v = u + at | ✓ |
| `sthana-antara` | s = ut + ½at² | ✓ |
| `vega-varga` | v² = u² + 2as | ✓ |
| `kshipra` | x,y,vx,vy at time t (needs t as input) | ✓ partial |
| `bala` | F = ma | ✓ |
| `samvega` | p = mv | ✓ |
| `tirupu` | τ = F·r·sin(θ) | ✓ |
| `kona-vega` | ω = θ/t | ✓ |
| `karya` | W = F·d·cos(θ) | ✓ |
| `chala-urja` | KE = ½mv² | ✓ |
| `sthithi-urja` | PE = mgh | ✓ |
| `kaksiya-vega` | v = √(GM/r) | ✓ |

### Knowledge nodes with no computation tantra

These nodes exist in the graph (engine knows WHAT they are) but cannot compute them:

| Concept | Formula | .om node |
|---|---|---|
| Moment of inertia (sphere) | I = 2/5 mr² | `moment-of-inertia.om` |
| Moment of inertia (cylinder) | I = ½mr² | `moment-of-inertia.om` |
| Moment of inertia (rod, center) | I = 1/12 mL² | `moment-of-inertia.om` |
| Angular momentum | L = Iω | `angular-momentum.om` |
| Rotational KE | KE_rot = ½Iω² | — |
| Angular acceleration | α = τ/I | `angular-acceleration.om` |
| Rolling velocity | v = √(2mgh/(m + I/r²)) | — |
| Centripetal force | F = mv²/r | `centripetal-force.om` |
| Flight time | t = 2v·sin(θ)/g | — |
| Max height (projectile) | h = v²sin²(θ)/(2g) | — |
| Range (projectile) | R = v²sin(2θ)/g | — |
| Spring period (SHM) | T = 2π√(m/k) | `harmonic.om` |
| Pendulum period | T = 2π√(L/g) | `harmonic.om` |
| SHM max velocity | v_max = A√(k/m) | — |
| Spring energy | E = ½kA² | — |
| Normal force | N = mg·cos(θ) | — |
| Friction force | f = μN | — |
| Inclined plane acceleration | a = g(sin θ − μcos θ) | — |
| Inelastic collision | v_f = m₁v₁/(m₁+m₂) | — |
| Elastic collision | v₁_f, v₂_f from conservation | — |
| Atwood machine | a = (m₂−m₁)g/(m₁+m₂) | — |

---

## Part C: New Tantras (22 files)

All go in `brahman/yantra/bhautika/`.

### Rotational dynamics (6)

**1. `ghana-jada-gola.tantra`** — moment of inertia, solid sphere
```
inputs:  mass (kg), radius (m)
formula: I = (2/5) × mass × radius²
returns: moment-of-inertia (kg·m²)
```

**2. `ghana-jada-chakra.tantra`** — moment of inertia, solid cylinder
```
inputs:  mass (kg), radius (m)
formula: I = (1/2) × mass × radius²
returns: moment-of-inertia (kg·m²)
```

**3. `ghana-jada-danda.tantra`** — moment of inertia, uniform rod (about center)
```
inputs:  mass (kg), length (m)
formula: I = (1/12) × mass × length²
returns: moment-of-inertia (kg·m²)
```

**4. `bhraman-urja.tantra`** — rotational kinetic energy
```
inputs:  moment-of-inertia (kg·m²), angular-velocity (rad/s)
formula: KE = (1/2) × I × ω²
returns: kinetic-energy (J)
```

**5. `bhraman-samvega.tantra`** — angular momentum
```
inputs:  moment-of-inertia (kg·m²), angular-velocity (rad/s)
formula: L = I × ω
returns: angular-momentum (kg·m²/s)
```

**6. `bhraman-kshipra.tantra`** — angular acceleration from torque
```
inputs:  torque (N·m), moment-of-inertia (kg·m²)
formula: α = τ / I
returns: angular-acceleration (rad/s²)
```

### Rolling motion (1)

**7. `ghurnan-vega.tantra`** — speed at bottom for rolling without slipping
```
inputs:  mass (kg), height (m), moment-of-inertia (kg·m²), radius (m)
formula: v = sqrt(2 × mass × g × height / (mass + moment-of-inertia / radius²))
returns: velocity (m/s)
note:    general — works for sphere, cylinder, any body with known I
```

### Circular / centripetal motion (2)

**8. `abhisarana-bala.tantra`** — centripetal force
```
inputs:  mass (kg), velocity (m/s), radius (m)
formula: F = mass × velocity² / radius
returns: force (N)
```

**9. `vartula-avdhi.tantra`** — period of circular motion
```
inputs:  radius (m), velocity (m/s)
formula: T = 2π × radius / velocity
returns: period (s)
```

### Complete projectile (3)

**10. `udaya-kaala.tantra`** — total time of flight
```
inputs:  initial-velocity (m/s), angle (rad)
formula: t = 2 × initial-velocity × sin(angle) / g
returns: time (s)
```

**11. `param-uchcha.tantra`** — maximum height
```
inputs:  initial-velocity (m/s), angle (rad)
formula: h = initial-velocity² × sin²(angle) / (2 × g)
returns: height (m)
```

**12. `dura-kshepa.tantra`** — horizontal range
```
inputs:  initial-velocity (m/s), angle (rad)
formula: R = initial-velocity² × sin(2 × angle) / g
returns: displacement (m)
```

### Simple harmonic motion (4)

**13. `spanda-avdhi.tantra`** — period of spring-mass system
```
inputs:  mass (kg), spring-constant (N/m)
formula: T = 2π × sqrt(mass / spring-constant)
returns: period (s)
```

**14. `lola-avdhi.tantra`** — period of simple pendulum
```
inputs:  length (m)
formula: T = 2π × sqrt(length / g)
returns: period (s)
```

**15. `spanda-param-vega.tantra`** — SHM maximum velocity
```
inputs:  amplitude (m), spring-constant (N/m), mass (kg)
formula: v_max = amplitude × sqrt(spring-constant / mass)
returns: velocity (m/s)
```

**16. `spanda-urja.tantra`** — total spring energy
```
inputs:  spring-constant (N/m), amplitude (m)
formula: E = (1/2) × spring-constant × amplitude²
returns: energy (J)
```

### Friction and constraints (3)

**17. `lambika-bala.tantra`** — normal force on inclined surface
```
inputs:  mass (kg), angle (rad)
formula: N = mass × g × cos(angle)
returns: force (N)
note:    angle=0 gives N=mg (flat surface)
```

**18. `ghasana-bala.tantra`** — friction force
```
inputs:  friction-coefficient (dimensionless), force (N)
formula: f = friction-coefficient × force
returns: force (N)
note:    pass normal-force as the force input
```

**19. `avanati-tvarana.tantra`** — acceleration on inclined plane with friction
```
inputs:  angle (rad), friction-coefficient (dimensionless)
formula: a = g × (sin(angle) − friction-coefficient × cos(angle))
returns: acceleration (m/s²)
note:    friction-coefficient=0 gives frictionless case a=g·sin(θ)
```

### Collisions (3)

**20. `asprishta-sanghat.tantra`** — perfectly inelastic collision
```
inputs:  mass (kg), velocity (m/s), mass-2 (kg)
formula: v_f = mass × velocity / (mass + mass-2)
         (mass-2 initially at rest)
returns: velocity (m/s)
```

**21. `sprishta-sanghat.tantra`** — elastic collision (two outputs)
```
inputs:  mass (kg), velocity (m/s), mass-2 (kg)
formula: v1_f = (mass − mass-2) × velocity / (mass + mass-2)
         v2_f = 2 × mass × velocity / (mass + mass-2)
         (mass-2 initially at rest)
returns: velocity (m/s), velocity-2 (m/s)
```

**22. `atwood-yantra.tantra`** — Atwood machine
```
inputs:  mass (kg), mass-2 (kg)
formula: a = (mass-2 − mass) × g / (mass + mass-2)
         T = 2 × mass × mass-2 × g / (mass + mass-2)
returns: acceleration (m/s²), tension (N)
```

---

## Part D: Complex Problem Solving

### D1 — The three limits of the current engine

**Limit 1: Chain depth is 4 steps (hardcoded)**
`chain_resolve ~max_depth:4` at `yantra_resolver.ml:189`.
Problems with 5–8 steps are silently not found.

**Limit 2: One sentence → one target**
`anuvada-ganana.tantra` processes one sentence, finds one target, runs one chain.
"Find (a) speed, (b) time, (c) range" requires three separate chain calls.

**Limit 3: Binding extraction is positional, not contextual**
"A 2 kg block on a 30° incline" → NLP extracts `2` and `30` but does not know
`block → mass`, `incline → angle-context`, `30° → angle`.
The current extractor works for explicit `X is N` syntax only.

### D2 — Fix 1: Configurable chain depth

One line change in `yantra_resolver.ml:189`:
```ocaml
(* current *)
match chain_resolve ~max_depth:4 k idx bindings target with

(* new — depth from resolution config, default 4 for normal queries *)
match chain_resolve ~max_depth:config.rc_max_depth k idx bindings target with
```

Expose via socket protocol `max_depth` field (already parsed as `max_passes`,
repurpose or add new field). Problem mode sets `max_depth = 10`.

**Why depth 10 is safe:** The tantra graph is sparse. At each beam step only
2–4 tantras are executable (inputs satisfied). Beam width=8 keeps the search
bounded. In practice, physics problems at depth 8 terminate in <5ms even at
depth 10 because the candidate set narrows after each step.

### D3 — Fix 2: Problem ingestion mode

A new input block that reads a full multi-line problem, extracts ALL bindings
from ALL sentences before resolving anything, then handles multi-target questions.

**Input syntax** (works in both REPL and socket):
```
PROBLEM
A 2 kg block slides down a frictionless 30° incline of length 4 m.
At the bottom it collides with a spring of spring constant 500 N/m.
Find: (a) speed at the bottom, (b) spring compression.
END
```

**Processing pipeline:**
```
1. Collect all lines between PROBLEM and END
2. Run binding extraction on EACH sentence individually
   → sentence 1: mass=2, angle=30°(→0.5236 rad), displacement=4
   → sentence 2: spring-constant=500
3. Parse the Find: line → targets = ["velocity", "spring-compression"]
4. For each target in order:
   a. Run chain_resolve with ALL bindings + max_depth=10
   b. Store result as a new binding for subsequent targets
   c. Format and accumulate answer
5. Present all answers together
```

**New OCaml function:** `solve_problem : proof_graph -> tantra_index -> session -> string list -> string`

Takes the lines of the problem body, returns formatted multi-part answer.
Lives in `vyakarana/lib/yantra_resolver.ml` or a new `problem_solver.ml`.

### D4 — Fix 3: Multi-target resolution

Parse `Find: (a) X, (b) Y, (c) Z` as a target list. Run chain_resolve once per
target. Each resolved value becomes an additional binding for the next target.

**Target extraction:** simple pattern match on `Find:` / `find:` / `Calculate:` / `Determine:`.
Strip `(a)`, `(b)`, `(c)` prefixes, lowercase, canonicalize via graph.

**Binding accumulation between targets:**
```
target (a): velocity → resolved → bind velocity=6.26
target (b): spring-compression → chain_resolve sees velocity=6.26 in bindings
            → can use KE = ½mv² = ½×2×6.26² = 39.2J → ½kx² = 39.2 → x = 0.396 m
```
Each answer feeds the next. This is already how the interactive session works —
problem mode just automates it.

### D5 — Fix 4: Context-aware binding disambiguation (Approach B)

**The problem:** A physics word problem uses "displacement" to mean two different
things — the incline length (4 m) and the spring compression (unknown). If both
get bound to `displacement`, the second overwrites the first.

**Approach B: Sequential disambiguation via PPR context shift**

The key insight: PPR seeds shift between sentences. When the solver is processing
sentence 1 (incline context), the active PPR seeds are `{mass, angle, incline, displacement}`.
When processing sentence 2 (spring context), seeds shift to `{spring-constant, spring-force, spring}`.

In this shifted context, `displacement` scores lower than `spring-compression` because:
- `spring-compression` has `sthita` edges to `spring-force` and `spring-constant`
- `displacement` has `sthita` edges to `acceleration` and `kinematics`
- With spring seeds active, PPR flows preferentially to `spring-compression`

**Implementation:** When extracting bindings from a sentence, use the PPR scores
from THAT sentence's context words to disambiguate which concept a bare noun
(like "distance", "displacement", "length") refers to.

```ocaml
(* for each sentence in the problem *)
let sentence_context_words = extract_nouns_and_adjectives sentence in
let ppr = run_ppr k ~seed_nodes:(List.map (fun w -> (w, 1.0)) sentence_context_words)
                    ~target:"" ~binding_names:[] in
(* when "displacement" appears, use PPR to pick between
   displacement, spring-compression, incline-length, path-length, etc. *)
let disambiguate word candidates =
  List.sort (fun a b ->
    Float.compare (ppr_score ppr b) (ppr_score ppr a)
  ) candidates |> List.hd
```

**Why Approach B over Approach A (namespacing):**
- No new syntax or schema — the graph's own PPR handles disambiguation
- Consistent with how the engine already resolves ambiguity in single queries
- The graph already has the right edges: `spring-compression` is connected to
  `spring-force`, `spring-constant`; `displacement` is connected to `kinematics`,
  `equations-of-motion`. The PPR naturally separates them when seeds differ.
- Progressive: gets better as the graph grows (more edges = better disambiguation)
- Degrades gracefully: if disambiguation fails, falls back to first-occurrence binding

**Binding naming:** When a sentence produces an ambiguous binding, store it under
the disambiguated concept name, not the raw word. So sentence 1 produces
`incline-displacement=4` (or just `displacement=4` if no ambiguity detected) and
sentence 2, with spring-context PPR, maps "spring compresses by x" → target `spring-compression`.

**The ordering rule (sequential story order):** Process sentences left-to-right.
When the same raw word appears in two sentences with different PPR contexts, the
second occurrence creates a NEW binding under the disambiguated name rather than
overwriting. The original binding is preserved. This is the "story order" property —
the problem builds context sequentially and the engine follows that structure.

### D6 — Graduate-level problem demonstration

**Problem: Rolling sphere (3-step decomposition)**
> "A solid sphere of mass 2 kg and radius 0.1 m rolls without slipping
> down an incline of height 3 m. Find its speed at the bottom."

```
Step 1: sthithi-urja.tantra     → PE = 2 × 9.8 × 3 = 58.84 J
Step 2: ghana-jada-gola.tantra  → I = 2/5 × 2 × 0.01 = 0.008 kg·m²
Step 3: ghurnan-vega.tantra     → v = √(2×2×9.8×3 / (2 + 0.008/0.01)) = 6.48 m/s ✓
```

Why 6.48 not 7.67: naive PE=KE gives 7.67 (ignores rotational KE).
With rolling constraint: KE_total = 7/10 mv², so v = √(10gh/7) = 6.48. ✓

**Problem: Inclined plane with friction (5-step)**
> "A 3 kg block slides down a 30° incline (length 5 m, μ=0.2).
> Find speed at bottom and distance it travels on the flat before stopping."

```
Step 1: avanati-tvarana.tantra  → a = 9.8(sin30° − 0.2cos30°) = 3.2 m/s²
Step 2: vega-varga.tantra       → v = √(2×3.2×5) = 5.66 m/s
Step 3: lambika-bala.tantra     → N = 3×9.8×cos0° = 29.4 N  (flat surface, θ=0)
Step 4: ghasana-bala.tantra     → f = 0.2×29.4 = 5.88 N
Step 5: bala.tantra (inverse)   → a_flat = −f/m = −1.96 m/s²
Step 6: vega-varga.tantra (inv) → s = v²/(2×1.96) = 8.17 m
```

6 steps — exceeds current max_depth=4. Works at max_depth=10. ✓

**Problem: SHM full analysis (4-step)**
> "A 0.5 kg mass on a spring (k=200 N/m) is displaced 10 cm.
> Find period, max velocity, and total energy."

```
Step 1: spanda-avdhi.tantra      → T = 2π√(0.5/200) = 0.314 s
Step 2: spanda-param-vega.tantra → v_max = 0.1×√(200/0.5) = 2.0 m/s
Step 3: spanda-urja.tantra       → E = ½×200×0.01 = 1.0 J
```

**Problem: Projectile complete analysis (3 tantras, multi-target)**
> "A ball is thrown at 25 m/s at 37°. Find max height, range, and speed at impact."

```
Target (a): param-uchcha.tantra  → h = 25²×sin²(37°)/(2×9.8) = 11.49 m
Target (b): dura-kshepa.tantra   → R = 25²×sin(74°)/9.8 = 61.5 m
Target (c): udaya-kaala.tantra   → t = 2×25×sin(37°)/9.8 = 3.07 s
            kshipra.tantra       → vx=19.97, vy=−19.97 → |v|=28.2 m/s
```

### D7 — Coverage estimate after all changes

| Category | Now | After 22 tantras + depth 10 + problem mode |
|---|---|---|
| Linear kinematics | ~95% | ~95% |
| Newton's laws (single body) | ~80% | ~90% |
| Energy / work | ~85% | ~97% |
| Projectile | ~40% | ~97% |
| Circular motion | ~10% | ~85% |
| Rotational dynamics | ~20% | ~90% |
| SHM / oscillations | ~0% | ~80% |
| Collisions | ~20% | ~80% |
| Multi-body / constraints (inclined, Atwood) | ~10% | ~75% |
| Multi-step word problems (5-8 steps) | ~0% | ~80% |
| **Overall UG mechanics** | **~45%** | **~88%** |

---

## Part E: Robotics Sensor Demo

### Architecture

```
┌────────────────────────────────────────────────────────────────────┐
│                  vyakarana (one process, OCaml 5.2)                │
│                                                                    │
│  proof_graph  ── FROZEN after startup (read-only across Domains) ──│
│  CSR arrays   ── immutable, shared ────────────────────────────────│
│  tantra_index ── read-only ─────────────────────────────────────── │
│                                                                    │
│  robot_session  (shared mutable, Mutex-protected)                  │
│  ┌──────────────────────────────────────────────────────────────┐ │
│  │  binding_store  (timestamped, sourced, TTL per sensor type)  │ │
│  └──────────────────────────────────────────────────────────────┘ │
│           ▲                              ▲                         │
│  ┌────────────────┐          ┌────────────────────────────┐        │
│  │ sensor Domain  │          │ text / problem Domain      │        │
│  │ command:sense  │          │ command:query (unchanged)  │        │
│  │ → direct bind  │          │ command:problem (new)      │        │
│  │ → TTL expiry   │          │ → NLP or problem ingestion │        │
│  │ → trigger chain│          │ → tantra chain (depth 10)  │        │
│  └────────────────┘          └────────────────────────────┘        │
│                                                                    │
│  Unix domain socket  (listen 64, Domain.spawn per connection)      │
└────────────────────────────────────────────────────────────────────┘
         ▲                                ▲
  sensor_sim.ml (demo)           madakkal REPL / existing clients
  50Hz IMU simulation            UNCHANGED — works exactly as before
```

### Demo: Robot arm force monitoring

Permanent bindings at startup: `mass=5 kg`, `max-force=20 N`, `radius=0.3 m`

Sensor stream at 50Hz:
```json
{"command":"sense","source":"imu","readings":[{"name":"acceleration","value":2.5}],"ttl":0.1}
```

Trigger chain on each sense event (~3ms total):
```
sense(acceleration=X)
  → bala.tantra:           force = mass × acceleration
  → seema-pariksha.tantra: status = "safe" | "breach", margin
  → emit:                  {force, status, action: "continue"|"brake"}
```

Expected output at 10Hz display:
```
[  0ms]  accel=2.0  force=10.0N  status=safe    action=continue
[100ms]  accel=3.5  force=17.5N  status=safe    action=continue
[200ms]  accel=4.2  force=21.0N  status=breach  action=brake    margin=+1.0N
[300ms]  accel=1.1  force=5.5N   status=safe    action=continue
```

---

## Part F: Binary Cache — Explicit Mode

- **Default (unchanged):** parse all `.om` files every time. Always fresh.
- **Explicit:** `--cache /path/to/graph.bin`
  - Binary exists + checksum matches → load ~10ms, skip .om parse
  - Binary missing or stale → parse normally → save binary for next run
  - Load fails → fallback to parse (try/with, never crash)

**Checksum:** `mtime + byte_size` of each `.om` file in sorted order. Fast (no content hashing), correct for any modification.

**What is serialised:** Full `proof_graph` including CSR arrays (`Marshal.to_channel`). `tantra_index` is NOT serialised — tantras are fast to parse and contain closures.

**Revised startup with `--cache`:**
```
First run:  parse .om (510ms) + build_index (50ms) + CSR in binary → 577ms → save
Next runs:  load binary (~10ms) + build_index (50ms)                → ~60ms
```

---

## Part G: Extended Binding Type

```ocaml
type binding = {
  b_name       : string;
  b_value      : float;
  b_unit       : string option;
  b_timestamp  : float;         (* Unix.gettimeofday() at write time *)
  b_source     : string;        (* "user" | "tantra:force" | "imu" | "inferred" *)
  b_confidence : float;         (* 0.0–1.0, default 1.0 *)
  b_ttl        : float option;  (* seconds until stale; None = permanent *)
}
```

`remember-bindings` fills: `b_timestamp=now`, `b_source="user"`, `b_confidence=1.0`, `b_ttl=None`.
Sensor `sense` fills all fields from the JSON packet.
Problem ingestion fills: `b_source="problem-sentence-N"`, `b_confidence` from PPR disambiguation score.

---

## Part H: New OCaml Code

### `vyakarana/lib/robot_session.ml` (new)
Mutex-protected binding store for concurrent sensor writes.

```ocaml
type robot_session = { rs_session: session; rs_mutex: Mutex.t }
val create         : unit -> robot_session
val sense          : robot_session -> name:string -> value:float
                  -> ?unit_:string -> source:string -> confidence:float -> ttl:float -> unit
val fresh_bindings : robot_session -> binding list
val prune_stale    : robot_session -> unit
```

### `vyakarana/lib/problem_solver.ml` (new)
Problem ingestion, multi-target resolution, PPR-based disambiguation.

```ocaml
(* parse a PROBLEM...END block into lines *)
val parse_problem_block : string list -> string list * string list
  (* returns (body_lines, target_strings) *)

(* extract bindings from one sentence using PPR context *)
val extract_with_context : proof_graph -> tantra_index -> string -> binding list

(* solve a full problem: extract all bindings, resolve all targets *)
val solve_problem : proof_graph -> tantra_index -> session
                 -> max_depth:int -> body:string list -> targets:string list
                 -> string   (* formatted multi-part answer *)
```

### `vyakarana/lib/yantra_resolver.ml` (modify)
- Add `rc_max_depth : int` to resolution config
- Pass `max_depth` as parameter to `chain_resolve`
- Default remains 4 for regular queries

### `vyakarana/demo/sensor_sim.ml` (new)
Standalone executable: sends 50Hz IMU packets, prints triggered responses.
```
sensor_sim <socket-path> [--mass N] [--limit N] [--freq N] [--duration N]
```

---

## Part I: dune Build Changes

### `vyakarana/lib/dune`
```
(library
 (name vyakarana_lib)
 (libraries unix str)
 (modules
   ... (all existing) ...
   robot_session
   problem_solver))
```

### `vyakarana/demo/dune` (new directory + file)
```
(executable
 (name sensor_sim)
 (libraries vyakarana_lib unix))
```

---

## Implementation Order

| Step | Files | What | Risk |
|---|---|---|---|
| 1 | `yantra_types.ml` | Add 4 fields to `binding` type | Low |
| 2 | `yantra_pipeline_ops.ml` | Fill new fields in `remember-bindings` | Low |
| 3 | 22 new `.tantra` files | All new motion tantras | Low |
| 4 | `seema-pariksha.tantra` | Threshold check (robotics + problems) | Low |
| 5 | Build + test Phase 1 | Verify rolling sphere, SHM, friction, collision queries | — |
| 6 | `yantra_resolver.ml` | Add `rc_max_depth` config, expose depth parameter | Low |
| 7 | `problem_solver.ml` | Problem ingestion + multi-target + PPR disambiguation | Medium |
| 8 | `vyakarana.ml` | PROBLEM...END parsing in madakkal REPL | Low |
| 9 | `socket.ml` | `command:problem` handler in socket server | Low |
| 10 | Build + test Phase 2 | 5-step incline+friction, multi-target projectile | — |
| 11 | `proof_graph.ml` | `save_binary` / `load_binary` + checksum | Low |
| 12 | `vyakarana.ml` | Wire `--cache` flag + binary load/save | Low |
| 13 | `robot_session.ml` | Mutex-protected session for sensors | Medium |
| 14 | `socket.ml` | Domain-per-connection + `command:sense` | Medium |
| 15 | `vyakarana/demo/` | `sensor_sim.ml` + `dune` | Low |
| 16 | `lib/dune` | Add `robot_session`, `problem_solver` | Low |
| 17 | Integration test | sensor_sim + socket + problem mode end-to-end | — |

Steps 1–5: tantras only, zero risk, no OCaml changes.
Steps 6–10: problem solving layer, no sensor code yet.
Steps 11–17: binary cache + robotics layer.

---

## What Is NOT Changing

| Thing | Status |
|---|---|
| `madakkal` REPL (stdin text queries) | Unchanged |
| JSON socket `command:query` interface | Unchanged |
| NLP pipeline (tokenise → classify → resolve) | Unchanged |
| All 102 existing tantras | Unchanged |
| Default startup (no `--cache`) | Unchanged — always parse from source |
| max_depth for regular queries | Unchanged at 4 (only problem mode uses 10) |
| gRPC | Not in this plan — Unix socket sufficient for same-machine |
| Vector database | Not used — destroys typed relational structure |

---

## Composability Summary

The single-line query `F is 20, a is 4, what is mass` and the multi-line problem

```
PROBLEM
A 2 kg block slides down a 30° frictionless incline of length 4 m.
At the bottom it collides with a spring (k = 500 N/m).
Find: (a) speed at bottom, (b) spring compression.
END
```

use **identical machinery**: session bindings, beam search over the tantra graph,
PPR for concept scoring, inverse solve for unknowns. The differences are:
- problem mode accumulates bindings across sentences before the first resolve call
- PPR context shifts between sentences for disambiguation (Approach B)
- max_depth=10 instead of 4
- two chain_resolve calls (one per target) with result binding fed forward

The robotics demo is the same mechanism receiving sensor data at 50Hz instead of
text. Sensor readings → bindings → chain → action output. Same resolver, same PPR,
same session. Different input transport and timing.
