# Robotics + Graduate Motion Plan
## High-Frequency Sensor Input, Graduate-Level Motion Decomposition, Graph Persistence

---

## What This Plan Covers

Three interconnected goals discussed in one session:

1. **Graduate-level motion problem** — 15 new tantras for rotational dynamics, SHM,
   complete projectile, and circular motion. These fill the gap between what exists
   and what a physics degree problem requires.

2. **Robotics sensor demo** — high-frequency sensor stream (50Hz IMU) driving a
   tantra chain: force → torque → threshold → action. Uses the same decomposition
   mechanism that already works for text queries.

3. **Graph persistence + explicit binary mode** — `Marshal`-based binary cache for
   sub-10ms restarts. `--cache <path>` flag for explicit use; default stays parse-from-source.

Regular text input (`madakkal` REPL and JSON socket) is **unchanged**. All additions
are additive — no existing interface breaks.

---

## Measured Baselines

| Metric | Value |
|---|---|
| Cold start (parse .om + CSR) | 0.577s |
| Per-query latency (socket, running) | 1ms |
| Session chaining overhead | 0ms (bindings already in memory) |
| Graph nodes / edges (post-axiom) | 1556 nodes / 16,771 edges |
| .om corpus on disk | 1.62MB, 1393 files |
| Estimated marshalled binary | ~1–2MB |

---

## Part A: What the Engine Already Does (Baseline)

The session binding mechanism already solves multi-step problems through decomposition.
These work today with no changes:

```
"mass is 2, height is 3, what is potential energy"
→ sthithi-urja.tantra: PE = 2 × 9.8 × 3 = 58.84 J  ✓

"potential-energy is 58.84, mass is 2, what is velocity"
→ INVERSE of chala-urja.tantra: v = √(2×58.84/2) = 7.67 m/s  ✓
  (engine inverts KE = ½mv² automatically)

"force is 20, displacement is 5, angle is 0, what is work"
→ karya.tantra: W = 20 × 5 × cos(0) = 100 J  ✓

"force is 50, radius is 0.3, angle is 1.5708, what is torque"
→ tirupu.tantra: τ = 50 × 0.3 × sin(π/2) = 15 N·m  ✓

"mass is 2, velocity is 6.48, what is kinetic energy"
→ chala-urja.tantra: KE = ½ × 2 × 6.48² = 41.99 J  ✓
```

**The decomposition is already the architecture.** Session holds intermediate results.
Each tantra is one computational step. Inverse solve finds unknowns automatically.
Adding new tantras directly extends what problems the engine can solve — no new
pipeline machinery needed.

---

## Part B: What's Missing — The Tantra Gap

### Existing tantras (motion-relevant)

| Tantra | Formula | Status |
|---|---|---|
| `antya-vega` | v = u + at | ✓ |
| `sthana-antara` | s = ut + ½at² | ✓ |
| `vega-varga` | v² = u² + 2as | ✓ |
| `kshipra` (projectile) | x,y,vx,vy at time t | ✓ but partial (needs t as input) |
| `bala` | F = ma | ✓ |
| `samvega` | p = mv | ✓ |
| `tirupu` | τ = F·r·sin(θ) | ✓ |
| `kona-vega` | ω = θ/t | ✓ |
| `karya` | W = F·d·cos(θ) | ✓ |
| `chala-urja` | KE = ½mv² | ✓ |
| `sthithi-urja` | PE = mgh | ✓ |
| `kaksiya-vega` | v = √(GM/r) | ✓ |

### Knowledge nodes with NO computation tantra

These nodes exist in the graph (the engine knows WHAT they are conceptually) but
there is no `.tantra` file that computes them:

| Concept | Formula | Node file |
|---|---|---|
| Moment of inertia (sphere) | I = 2/5 mr² | `moment-of-inertia.om` |
| Moment of inertia (cylinder) | I = ½mr² | `moment-of-inertia.om` |
| Moment of inertia (rod, center) | I = 1/12 mL² | `moment-of-inertia.om` |
| Angular momentum | L = Iω | `angular-momentum.om` |
| Rotational KE | KE = ½Iω² | — |
| Angular acceleration | α = τ/I | `angular-acceleration.om` |
| Rolling velocity | v = √(2mgh/(m + I/r²)) | — |
| Centripetal force | F = mv²/r | `centripetal-force.om` |
| Flight time | t = 2v·sin(θ)/g | — |
| Max height (projectile) | h = v²sin²(θ)/(2g) | — |
| Range (projectile) | R = v²sin(2θ)/g | — |
| Spring period (SHM) | T = 2π√(m/k) | `harmonic.om`, `spring-force.om` |
| Pendulum period | T = 2π√(L/g) | `harmonic.om` |
| SHM max velocity | v_max = A√(k/m) | — |
| Spring energy | E = ½kA² | — |

---

## Part C: The Graduate-Level Demo Problem

### Problem: Rolling Sphere (requires 3-step decomposition)

> "A solid sphere of mass 2 kg and radius 0.1 m rolls without slipping
> down an incline of height 3 m. Find its speed at the bottom."

**Why this is graduate-level:** combines translational + rotational kinetic energy.
Naive energy conservation (PE = ½mv²) gives the wrong answer (7.67 m/s).
Correct answer with rolling constraint is 6.48 m/s.

**How the engine decomposes it:**

```
Step 1: "mass is 2, height is 3, what is potential energy"
        → sthithi-urja.tantra → PE = 58.84 J
        → session now holds: mass=2, height=3, potential-energy=58.84

Step 2: "radius is 0.1, what is moment of inertia of a sphere"
        → [NEW] ghana-jada-gola.tantra → I = 2/5 × 2 × 0.1² = 0.008 kg·m²
        → session now holds: ..., radius=0.1, moment-of-inertia=0.008

Step 3: "what is rolling velocity"
        → [NEW] ghurnan-vega.tantra → v = √(2×58.84 / (2 + 0.008/0.01))
        = √(117.68 / 2.8) = √(42.03) = 6.48 m/s  ✓
```

The session carries all intermediate values. Each step is one tantra call. The resolver
finds which tantra to call based on what bindings are present. This is identical to
how `F is 20, a is 4, what is mass` works today — just more steps.

### Problem: Complete Projectile (4-step)

> "A ball is thrown at 25 m/s at 37° above horizontal. Find max height,
> time of flight, range, and speed at impact."

```
Step 1: "initial-velocity is 25, angle is 0.6458, what is flight time"
        → [NEW] udaya-kaala.tantra → t = 2×25×sin(0.6458)/9.8 = 3.06 s

Step 2: "what is max height"
        → [NEW] param-uchcha.tantra → h = 25²×sin²(0.6458)/(2×9.8) = 11.5 m

Step 3: "what is range"
        → [NEW] dura-kshepa.tantra → R = 25²×sin(2×0.6458)/9.8 = 58.3 m

Step 4: "time is 3.06, what is projectile"
        → kshipra.tantra (existing) → vx=19.97, vy=-19.97 m/s → |v| = 28.2 m/s
```

### Problem: Simple Harmonic Motion (4-step)

> "A 0.5 kg mass on a spring (k = 200 N/m) is displaced 10 cm. Find:
> period, frequency, max velocity, total energy."

```
Step 1: "mass is 0.5, spring-constant is 200, what is period"
        → [NEW] spanda-avdhi.tantra → T = 2π√(0.5/200) = 0.314 s

Step 2: "period is 0.314, what is frequency"
        → (1/T, simple inversion) → f = 3.18 Hz

Step 3: "amplitude is 0.1, what is max velocity"
        → [NEW] spanda-param-vega.tantra → v = 0.1×√(200/0.5) = 2.0 m/s

Step 4: "what is spring energy"
        → [NEW] spanda-urja.tantra → E = ½×200×0.1² = 1.0 J
```

---

## Part D: New Tantras to Write (15 files)

All go in `brahman/yantra/bhautika/` (motion physics).

### Rotational dynamics (5 tantras)

**1. `ghana-jada-gola.tantra`** — moment of inertia, solid sphere
```
inputs: mass (kg), radius (m)
formula: I = 2/5 × mass × radius²
returns: moment-of-inertia (kg·m²)
```

**2. `ghana-jada-chakra.tantra`** — moment of inertia, solid cylinder
```
inputs: mass (kg), radius (m)
formula: I = 1/2 × mass × radius²
returns: moment-of-inertia (kg·m²)
```

**3. `ghana-jada-danda.tantra`** — moment of inertia, uniform rod (about center)
```
inputs: mass (kg), length (m)
formula: I = 1/12 × mass × length²
returns: moment-of-inertia (kg·m²)
```

**4. `bhraman-urja.tantra`** — rotational kinetic energy
```
inputs: moment-of-inertia (kg·m²), angular-velocity (rad/s)
formula: KE = 1/2 × I × ω²
returns: kinetic-energy (J)
```

**5. `bhraman-samvega.tantra`** — angular momentum
```
inputs: moment-of-inertia (kg·m²), angular-velocity (rad/s)
formula: L = I × ω
returns: angular-momentum (kg·m²/s)
```

**6. `bhraman-kshipra.tantra`** — angular acceleration from torque
```
inputs: torque (N·m), moment-of-inertia (kg·m²)
formula: α = τ / I
returns: angular-acceleration (rad/s²)
```

### Rolling motion (1 tantra)

**7. `ghurnan-vega.tantra`** — velocity for rolling without slipping
```
inputs: mass (kg), height (m), moment-of-inertia (kg·m²), radius (m)
formula: v = sqrt(2 × mass × g × height / (mass + moment-of-inertia / radius²))
returns: velocity (m/s)
note: general form works for sphere (I=2/5mr²), cylinder (I=½mr²), any shape
```

### Circular / centripetal motion (2 tantras)

**8. `abhisarana-bala.tantra`** — centripetal force
```
inputs: mass (kg), velocity (m/s), radius (m)
formula: F = mass × velocity² / radius
returns: force (N)
```

**9. `vartula-avdhi.tantra`** — period of circular motion
```
inputs: radius (m), velocity (m/s)
formula: T = 2π × radius / velocity
returns: period (s)
```

### Complete projectile (3 tantras)

**10. `udaya-kaala.tantra`** — total flight time
```
inputs: initial-velocity (m/s), angle (rad)
formula: t = 2 × initial-velocity × sin(angle) / g
returns: time (s)
```

**11. `param-uchcha.tantra`** — max height of projectile
```
inputs: initial-velocity (m/s), angle (rad)
formula: h = initial-velocity² × sin²(angle) / (2 × g)
returns: height (m)
```

**12. `dura-kshepa.tantra`** — horizontal range
```
inputs: initial-velocity (m/s), angle (rad)
formula: R = initial-velocity² × sin(2 × angle) / g
returns: displacement (m)
```

### Simple harmonic motion (3 tantras)

**13. `spanda-avdhi.tantra`** — period of spring-mass system
```
inputs: mass (kg), spring-constant (N/m)
formula: T = 2π × sqrt(mass / spring-constant)
returns: period (s)
```

**14. `lola-avdhi.tantra`** — period of simple pendulum
```
inputs: length (m)
formula: T = 2π × sqrt(length / g)
returns: period (s)
```

**15. `spanda-param-vega.tantra`** — SHM max velocity
```
inputs: amplitude (m), spring-constant (N/m), mass (kg)
formula: v = amplitude × sqrt(spring-constant / mass)
returns: velocity (m/s)
```

**16. `spanda-urja.tantra`** — total spring energy
```
inputs: spring-constant (N/m), amplitude (m)
formula: E = 1/2 × spring-constant × amplitude²
returns: energy (J)
```

*(16 tantras total — added one SHM energy tantra that the demo needs)*

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
│  │ sensor Domain  │          │ text query Domain          │        │
│  │ command:sense  │          │ command:query (unchanged)  │        │
│  │ → direct bind  │          │ → NLP pipeline (unchanged) │        │
│  │ → TTL expiry   │          │ → tantra resolve           │        │
│  │ → trigger chain│          │ → session bindings         │        │
│  └────────────────┘          └────────────────────────────┘        │
│                                                                    │
│  Unix domain socket  (listen 64, Domain.spawn per connection)      │
└────────────────────────────────────────────────────────────────────┘
         ▲                                ▲
  sensor_sim.ml (demo)           madakkal REPL / existing clients
  50Hz IMU simulation            UNCHANGED — works exactly as before
```

### Demo scenario: Robot arm force monitoring

Permanent bindings at startup: `mass = 5 kg`, `max-force = 20 N`, `radius = 0.3 m`

Sensor stream at 50Hz: `{command: sense, source: imu, readings: [{name: acceleration, value: X}], ttl: 0.1}`

Trigger chain on each sense event (runs at sensor rate, ~3ms total):
```
sense(acceleration=X)
  → bala.tantra:           force = mass × acceleration
  → seema-pariksha.tantra: status = "safe" | "breach", margin
  → emit JSON action:      {force, status, action: "continue"|"brake"}
```

Expected output at 10Hz display rate:
```
[  0ms]  accel=2.0  force=10.0N  status=safe    action=continue
[100ms]  accel=3.5  force=17.5N  status=safe    action=continue
[200ms]  accel=4.2  force=21.0N  status=breach  action=brake    margin=+1.0N
[300ms]  accel=1.1  force=5.5N   status=safe    action=continue
```

The demo connects the same engine that solves "A solid sphere rolls down a ramp at 6.48 m/s"
to a real-time sensor stream — same decomposition, different input modality.

---

## Part F: Binary Cache — Explicit Mode

### Design

- **Default behaviour (unchanged):** parse all `.om` files every time. Safe, always fresh.
- **Explicit cache mode:** `--cache /path/to/graph.bin`
  - If binary exists AND checksum matches → load in ~10ms (skip .om parse)
  - If binary missing or stale → parse normally → save binary for next run
  - If load fails for any reason → fallback to parse (try/with, never crash)

### Checksum strategy

Compute: `SHA256(sorted concat of: each .om filepath + its mtime + its byte size)`

This is fast (no file content hashing), correct for any modification, and doesn't
require reading all .om bytes twice.

### What gets serialized

The entire `proof_graph` record including the `csr` field (already populated by
`materialize_csr`). `Marshal.to_channel` handles `Hashtbl`, `array`, and `option ref`
correctly. Re-running `materialize_csr` after load is not needed — it's in the binary.

The `tantra_index` is **not** serialized — tantras are small, fast to parse (~50ms of
the 577ms total), and contain closures that don't marshal cleanly. Only the graph binary
is cached; tantras always reload from source.

Revised startup timing with `--cache`:
```
First run:  parse .om (510ms) + build_index (50ms) + CSR (17ms) + save binary → 577ms
Next runs:  load binary (~10ms) + build_index (50ms) + CSR already in binary → ~60ms
```

### New CLI flag

```
vyakarana [--cache /path/to/graph.bin] [--socket path] [dir1 dir2 ...]
```

No `--cache` → current behaviour exactly. With `--cache` → fast restart path.

---

## Part G: Extended Binding Type

Minimal extension — adds sensor metadata without breaking any existing code:

```ocaml
type binding = {
  b_name       : string;
  b_value      : float;
  b_unit       : string option;
  (* new fields — filled with defaults by existing remember-bindings *)
  b_timestamp  : float;         (* Unix.gettimeofday() at write time *)
  b_source     : string;        (* "user" | "tantra:force" | "imu-left" | "inferred" *)
  b_confidence : float;         (* 0.0–1.0, default 1.0 *)
  b_ttl        : float option;  (* seconds until stale; None = permanent *)
}
```

`remember-bindings` in `yantra_pipeline_ops.ml` fills:
`b_timestamp = now`, `b_source = "user"`, `b_confidence = 1.0`, `b_ttl = None`.

Sensor `sense` command fills:
`b_timestamp = now`, `b_source = sender source field`, `b_confidence = from JSON`,
`b_ttl = from JSON ttl field`.

---

## Part H: New OCaml Files / Modules

### `vyakarana/lib/robot_session.ml` (new)

Mutex-protected wrapper around `session` for concurrent sensor writes:

```ocaml
type robot_session = {
  rs_session : session;
  rs_mutex   : Mutex.t;
}

val create : unit -> robot_session
val sense  : robot_session -> name:string -> value:float
          -> ?unit_:string -> source:string -> confidence:float -> ttl:float -> unit
val fresh_bindings : robot_session -> binding list   (* drops stale, under mutex *)
val prune_stale    : robot_session -> unit
```

### `vyakarana/demo/sensor_sim.ml` (new)

Standalone executable: connects to Unix socket, sends 50Hz IMU sense packets,
prints triggered action responses.

```
Usage: sensor_sim <socket-path> [--mass N] [--limit N] [--freq N] [--duration N]
```

### `brahman/yantra/bhautika/seema-pariksha.tantra` (new)

Threshold check used by both robotics demo and graduate problems:
```
inputs: value (float), limit (float)
let exceeded = gt value limit
let margin = sub value limit
return: status (string), margin (float)
```

---

## Part I: dune Build Changes

### `vyakarana/lib/dune`
```
(library
 (name vyakarana_lib)
 (libraries unix str)
 (modules ... robot_session))   ← add robot_session
```

### `vyakarana/demo/dune` (new)
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
| 3 | `proof_graph.ml` | Add `save_binary` / `load_binary` + checksum | Low |
| 4 | `vyakarana.ml` | Wire `--cache` flag + binary load/save in startup | Low |
| 5 | 16 new `.tantra` files | All new motion tantras in `brahman/yantra/bhautika/` | Low |
| 6 | `seema-pariksha.tantra` | Threshold check tantra | Low |
| 7 | Build + test graduate problems | Verify rolling sphere, projectile, SHM queries | — |
| 8 | `robot_session.ml` | New Mutex-protected session module | Medium |
| 9 | `socket.ml` | Domain-per-connection + `sense` command | Medium |
| 10 | `vyakarana.ml` | Pass `robot_session` to `Socket.serve` | Low |
| 11 | `vyakarana/demo/sensor_sim.ml` + `dune` | Demo sensor simulator | Low |
| 12 | `lib/dune` | Add `robot_session` to modules list | Low |
| 13 | Integration test | Run demo: sensor_sim + socket + verify 1ms actions | — |

Steps 1–7 are pure additions (tantras + binary cache) with no risk of breaking existing
behaviour. Steps 8–13 are the sensor/concurrency layer.

---

## What Is NOT Changing

| Thing | Status |
|---|---|
| `madakkal` REPL (stdin text) | Unchanged — regular input works exactly as before |
| JSON socket query interface | Unchanged — existing clients unaffected |
| NLP pipeline (tokenise→classify→resolve) | Unchanged |
| Graph structure (.om files) | Additive only (new physics .om nodes for new tantras) |
| Existing 102 tantras | Unchanged |
| Default startup (no `--cache`) | Unchanged — always parse from source |
| Vector database | Not used — wrong tool for typed relational knowledge |
| gRPC | Not in this plan — Unix socket sufficient for same-machine |

---

## Composability Summary

The user's observation is correct: **the engine already decomposes problems through
session memory, and adding new tantras directly extends the problem space with zero
new pipeline machinery.**

The path from `F is 20, a is 4, what is mass` (one-step inverse) to
`A solid sphere rolls down a 3m ramp, find speed` (three-step chain) is not an
architectural change — it's the same resolver, the same session, the same PPR,
applied to a richer tantra library.

The robotics demo is the same mechanism applied to continuous sensor data:
sensor readings become bindings, bindings trigger tantras, tantras produce outputs.
The only new things are the transport (sensor socket command) and the timing (TTL, 50Hz).
