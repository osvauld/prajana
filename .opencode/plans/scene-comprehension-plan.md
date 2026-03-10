# Vyakarana / Prajana — Master Plan
## Scene Comprehension · Dynamic Tantra Composition · Universal Physics Scene Graph

---

## The Core Insight: Every Problem IS a Scene Graph

Any physics or math problem can be represented as a scene graph of entities,
connections, and constraints. The scene graph is the universal representation.
The tantras are the laws. The `compose-plan` finds which laws apply.

| Problem type | Entities | Connections | Governing law |
|---|---|---|---|
| Kinematic chain | links + joints | krama sequence (chala-apeksha chain) | FK/IK + Newton-Euler |
| Pulley system | masses + rope + pulley | sandhi (junction), sambandha (rope) | Atwood / tension continuity |
| Circuit | components + junctions | sandhi (KCL node), krama (KVL loop) | Kirchhoff + Ohm |
| SHM | mass + spring | spanda (oscillation) | F = -kx → period/energy |
| Collision | two bodies | sandhi (impact event) | momentum + energy conservation |
| Inclined plane | block + surface | gati + friction sambandha | Newton's 2nd + friction |
| Electrostatics | charges at positions | sambandha (force field) | Coulomb's law |
| Thermal network | sources + conductors | sambandha (heat flow) | Fourier's law |
| Optics | lenses + mirrors | krama (ray sequence) | Snell + lens equation |

The sangati roots already model all of these:
- `sandhi` — junction where things meet (pulley, circuit node, collision point)
- `krama` — ordered sequence where each step grounds the next (kinematic chain, KVL loop, ray path)
- `sambandha` — typed connection carrying meaning (rope tension, electric field, heat flow)
- `spanda` — oscillation / self-pulsing (SHM, LC circuit, pendulum)
- `gati` — directed motion (projectile, rolling body, current flow)
- `kramanusara` — rate of change propagating through the structure (velocity, current, heat flux)
- `sthira-apeksha` / `chala-apeksha` — fixed vs moving reference frame

`scene-extract` identifies which sangati roots apply → emits the right graph topology.
`compose-plan` finds tantras from `by_output` → the laws emerge from the graph.

The robot arm with 3D kinematic chain + motor feasibility is the **first concrete demo**.
Circuits and pulley systems are the **next demos** — same machinery, different tantras.

---

## Demo 1 — Robot Arm (primary): 3D Kinematic Chain

Given this natural language input:

```
PROBLEM
A 3-joint robot arm in 3D space.
Joint 1 is revolute about Z axis, link length 0.5m, mass 1kg, max speed 2 rad/s, motor rated 5 N·m and 20 W.
Joint 2 is revolute about Y axis, link length 0.4m, mass 0.8kg, max speed 2 rad/s, motor rated 4 N·m and 15 W.
Joint 3 is revolute about Z axis, link length 0.3m, mass 0.5kg, max speed 3 rad/s, motor rated 3 N·m and 12 W.
All joints currently at 0 radians.
Move end effector to position (0.6, 0.3, 0.4).
Find joint angles, velocities, move time, torque per joint, power per joint, motor feasibility.
END
```

The engine must produce:

```
Scene understood:
  Kinematic chain: 3-DOF serial arm in aayaama-traya (3D workspace)
  Frame model: sthira-apeksha (world) → chala-apeksha[0] → chala-apeksha[1] → chala-apeksha[2]

  Joint 0  revolute  axis=[0,0,1] (Z)  θ=0 rad  ω_max=2 rad/s  motor: 5 N·m, 20 W
    └── Link 0  length=0.5m  mass=1kg
  Joint 1  revolute  axis=[0,1,0] (Y)  θ=0 rad  ω_max=2 rad/s  motor: 4 N·m, 15 W
    └── Link 1  length=0.4m  mass=0.8kg
  Joint 2  revolute  axis=[0,0,1] (Z)  θ=0 rad  ω_max=3 rad/s  motor: 3 N·m, 12 W
    └── Link 2  length=0.3m  mass=0.5kg

  Target: end-effector to [0.6, 0.3, 0.4] in world-space (sthira-apeksha)
  Goals:  joint-angles, joint-velocities, move-time, torque, power, motor-check

Decomposition (graph-derived):
  Step 1  fk-3d                  →  joint-positions, end-effector-pos, end-effector-rot
  Step 2  ik-3d-jacobian         →  joint-angles [θ0, θ1, θ2]
  Step 3  joint-velocity-ndof    →  joint-velocities [ω0, ω1, ω2], move-time
  Step 4  moment-of-inertia-rod  ×3 →  inertia [I0, I1, I2]
  Step 5  angular-accel-joint    ×3 →  alpha [α0, α1, α2]
  Step 6  torque-joint           ×3 →  torque [τ0, τ1, τ2]
  Step 7  power-joint            ×3 →  power [P0, P1, P2]
  Step 8  motor-check            ×3 →  motor-ok, margin-torque, margin-power per joint

Results:
  joint-angles   = [θ0, θ1, θ2] rad
  joint-velocities = [ω0, ω1, ω2] rad/s
  move-time      = T s
  torque         = [τ0, τ1, τ2] N·m
  power          = [P0, P1, P2] W
  motor joint 0: ok / FAIL
  motor joint 1: ok / FAIL
  motor joint 2: ok / FAIL
```

Output composed entirely by `format-scene-trace.tantra`. No formatting in OCaml.

---

## Demo 2 — Circuit (Kirchhoff's laws)

```
PROBLEM
A 9V battery connected to a 10Ω resistor and 20Ω resistor in series.
Find the current, voltage across each resistor, and power dissipated.
END
```

Scene graph emitted:
```
circuit-<hash>
  ├── battery-0        (voltage=9V, sthira-apeksha — fixed potential source)
  ├── resistor-0       (resistance=10Ω, sandhi-sthita)
  ├── resistor-1       (resistance=20Ω, sandhi-sthita)
  ├── junction-0       (sandhi-swarupa — KCL: currents sum to 0)
  ├── junction-1       (sandhi-swarupa)
  └── loop-0           (krama-swarupa — KVL: voltages sum to 0 around loop)
```

Decomposition:
```
  Step 1  series-resistance  →  total-resistance   (R = R1 + R2 = 30Ω)
  Step 2  ohm-tantra         →  current            (I = V/R = 0.3A)
  Step 3  ohm-tantra ×2      →  voltage-0, voltage-1  (V = IR)
  Step 4  power-dissipated ×2 →  power-0, power-1  (P = I²R)
```

---

## Demo 3 — Pulley (Atwood machine)

```
PROBLEM
Two masses of 3kg and 5kg connected by a rope over a frictionless pulley.
Find acceleration, tension in the rope, and velocity after 2 seconds.
END
```

Scene graph emitted:
```
pulley-system-<hash>
  ├── mass-0           (mass=3kg, gati-sthita — accelerates upward)
  ├── mass-1           (mass=5kg, gati-sthita — accelerates downward)
  ├── pulley-0         (sandhi-swarupa — redirects tension, frictionless)
  └── rope-0           (sambandha — tension same throughout,
                        kramanusara constraint: a0 = -a1)
```

Decomposition:
```
  Step 1  atwood-yantra       →  acceleration, tension   (existing tantra)
  Step 2  antya-vega          →  velocity after t=2s     (v = u + at)
```

---

## The Key Architectural Insight: Scene IS the Graph

`scene-extract` does NOT return a flat parameter list. It **emits live nodes** into the
proof graph using the existing `Proof_graph.join` / `emit-node` infrastructure.

The scene becomes a subgraph:

```
arm-instance-<hash>           (kinematic-chain-swarupa, aayaama-traya-sthita)
  ├── joint-0-<hash>          (revolute, axis=[0,0,1], joint-angle=0, sthira-apeksha-sthita)
  │     └── link-0-<hash>     (length=0.5, mass=1.0, chala-apeksha-sthita)
  ├── joint-1-<hash>          (revolute, axis=[0,1,0], joint-angle=0, chala-apeksha-sthita)
  │     └── link-1-<hash>     (length=0.4, mass=0.8, chala-apeksha-sthita)
  ├── joint-2-<hash>          (revolute, axis=[0,0,1], joint-angle=0, chala-apeksha-sthita)
  │     └── link-2-<hash>     (length=0.3, mass=0.5, chala-apeksha-sthita)
  └── target-<hash>           (bindu-swarupa, world-space=[0.6,0.3,0.4], sthira-apeksha-sthita)
```

All subsequent ops — `compose-plan`, `execute-plan-traced`, `format-scene-trace` —
walk THIS graph using `edges`, `outgoing-edges`, `shabda` to find values.
PPR, `by_output`, `by_input` all work on these live nodes automatically.

---

## What's Already Done ✓

| Item | Status |
|---|---|
| `binding` type (timestamp, source, confidence, ttl) | ✓ |
| 22 motion tantras (rotational, rolling, SHM, friction, collision) | ✓ |
| `visheshanam` int registry, ring-based, CSR dynamic | ✓ |
| `matra-aayaama.shabda` — SI dim vectors for 60+ units | ✓ |
| `dim-vector`, `dim-op`, `dim-to-unit` primitives | ✓ |
| `matra-ganana.tantra`, `matra-viveka.tantra` | ✓ |
| Scene types in `yantra_types.ml`: `krama_state`, `entity`, `sandhi`, `process`, `scene` | ✓ |
| `asin`, `acos`, `atan2` in `yantra_ops.ml` + `op-asin/acos/atan2.om` | ✓ |
| n-D vector ops: `vec-add`, `vec-sub`, `vec-scale`, `vec-dot`, `vec-norm`, `rot2d`, `mat-mul` | ✓ |
| `ik-2dof.tantra`, `joint-velocity-2dof.tantra`, `fk-2dof.tantra`, `arm-plan-2dof.tantra` | ✓ |
| EVAL: `arm-plan-2dof 5 3 0 0 3 4 2 3` → θ1,θ2,ω1,ω2,T,ex,ey all correct | ✓ |
| `moment-of-inertia-rod.tantra`, `angular-accel-joint.tantra` | ✓ |
| `torque-joint.tantra`, `power-joint.tantra`, `motor-check.tantra` | ✓ |
| `sthira-apeksha.om`, `chala-apeksha.om` — fixed/moving frame sangati roots | ✓ |
| `apeksha.om` — updated: `sthira-apeksha-abheda chala-apeksha-abheda` | ✓ |
| `kinematic-chain.om` — bridges 3D + physics, FK=scene-graph, motion=keyframe | ✓ |
| `joint.om` — DOF connector: `chala-apeksha-sthita chala-apeksha-phala krama-janya-yukta` | ✓ |
| `link.om`, `link-mass.om`, `link-length.om` — physical link properties | ✓ |
| `joint-angle.om`, `joint-speed-max.om` — joint DOF state and limits | ✓ |
| `rated-torque.om`, `rated-power.om` — motor actuator limits | ✓ |
| `target-position.om` — n-dim bindu in sthira-apeksha (not split x/y/z files) | ✓ |
| `target-orientation.om` — SO(3) rotation target | ✓ |
| `bone.om` updated — `mass-yukta moment-of-inertia-yukta kona-yukta rekha-abheda fk-siddha` | ✓ |
| `domain-robotics.om` updated — `kinematic-chain-yukta world-space-yukta` | ✓ |

---

## Existing Infrastructure (concrete, confirmed)

### `emit-node` — live graph node emitter (already exists)
```ocaml
(* in yantra_eval_primitives.ml line 527 *)
(* name × layer × slokas-list × shabda → VNode *)
| "emit-node" ->
  let name   = as_string ... in   (* node name *)
  let layer  = as_string ... in   (* "kosha" | "sangati" *)
  let slokas = List.map as_string (as_list ...) in
  let shabda = as_string ... in   (* key:value data *)
  (* decomposes slokas into typed_edges, calls Proof_graph.join k n *)
  Some (VNode name)
```

### `edges` and `outgoing-edges` — graph traversal (already exists)
```ocaml
(* edges: both directions — returns [[src, rel, tgt], ...] *)
| "edges" -> ... (* calls Proof_graph.edges_of k node_name *)

(* outgoing-edges: src only — returns [[src, rel, tgt], ...] *)
| "outgoing-edges" -> ... (* filters k.all_edges for source = node_name *)
```

### `eval_ctx` — access to tantra index and session
```ocaml
(* in yantra_eval_primitives.ml line 26 *)
type eval_context = { ctx_index : tantra_index; ctx_session : session; }
let eval_ctx : eval_context option ref = ref None
(* accessed in pipeline ops as: (Option.get !eval_ctx).ctx_index *)
```

### `eval_pipeline_op` signature
```ocaml
(* in yantra_pipeline_ops.ml line 23 *)
let eval_pipeline_op (e_eval : proof_graph -> env -> expr -> value)
    (k : proof_graph) (e : env) (op : string) (args : expr list) : value option =
```

### `Proof_graph.join` — merge node into live graph
```ocaml
(* proof_graph.ml line 185 *)
let join (k : proof_graph) (n : nigamana) : proof_graph =
(* mutates k.nodes and k.all_edges, deduplicates edges, returns k *)
```

### `shabda` field — key:value data on each node
Each node has a `shabda` string with `key:value` pairs.
`scene-extract` stores per-joint values here:
`"joint-type:revolute axis-x:0 axis-y:0 axis-z:1 joint-angle:0 joint-speed-max:2 rated-torque:5 rated-power:20"`
Then `compose-plan` reads them via `Setu.read_shabda k node_name`.

---

## Phase 5: Scene Extraction — Emits Live Graph Nodes

### 5A. `scene-extract` op

**File:** `vyakarana/lib/yantra_pipeline_ops.ml`
**Arity:** 1 (takes sentence string)
**Returns:** `VNode scene_root_name` — the root scene node in the live graph

The root node type depends on what was detected:
- `arm-<hash>` — kinematic chain (joints + links)
- `circuit-<hash>` — electrical circuit (components + junctions + loops)
- `pulley-<hash>` — pulley/Atwood system (masses + rope + pulleys)
- `collision-<hash>` — collision event (bodies + sandhi)
- `oscillator-<hash>` — SHM system (mass + spring/pendulum)
- `scene-<hash>` — generic fallback for unrecognized topology

**Scene type detection** (from process words + entity types):

| Detected words | Scene type | Root sangati |
|---|---|---|
| "joint", "revolute", "prismatic", "arm", "link" | kinematic-chain | `kinematic-chain-swarupa` |
| "resistor", "capacitor", "battery", "circuit", "voltage", "current" | circuit | `sandhi-swarupa krama-swarupa` |
| "pulley", "rope", "Atwood", "connected by" | pulley-system | `sandhi-swarupa sambandha-swarupa` |
| "collides", "collision", "impact", "hits" | collision | `sandhi-swarupa` |
| "spring", "oscillates", "SHM", "pendulum" | oscillator | `spanda-swarupa` |
| "rolls", "incline", "slope", "friction" | constrained-gati | `gati-swarupa sambandha-swarupa` |

**Algorithm:**

```ocaml
| "scene-extract" ->
  let sentence = as_string (e_eval k e (List.nth args 0)) in
  let tokens = Yantra_eval.yantra_tokenise sentence in
  let hash = Printf.sprintf "%d" (abs (Hashtbl.hash sentence)) in

  (* --- pass 1: detect scene type from tokens --- *)
  (* check for scene-type keywords in order of specificity *)
  let scene_type = detect_scene_type tokens in
  (* returns one of:
     "kinematic-chain" | "circuit" | "pulley-system" |
     "collision" | "oscillator" | "constrained-gati" | "generic" *)

  (* --- pass 2: detect goals --- *)
  (* words after "find:", "compute:", "determine:" with kriya-yantra role *)
  (* also map natural goal words to concept names via graph:
     "current" → "current", "velocity" → "velocity",
     "joint angles" → "joint-angles", "power" → "power" *)
  let goals = detect_goals k tokens in   (* string list of concept names *)

  (* --- pass 3: dispatch to scene-type-specific extractor --- *)
  (* each extractor emits the appropriate graph nodes and returns root VNode name *)
  let root_name = match scene_type with
    | "kinematic-chain" -> extract_kinematic_chain k tokens hash goals
    | "circuit"         -> extract_circuit k tokens hash goals
    | "pulley-system"   -> extract_pulley k tokens hash goals
    | "collision"       -> extract_collision k tokens hash goals
    | "oscillator"      -> extract_oscillator k tokens hash goals
    | _                 -> extract_generic k tokens hash goals
  in
  Some (VNode root_name)
```

**Each scene-type extractor** follows the same pattern:
1. Segment tokens into entity blocks (by entity keyword: "joint", "resistor", "mass" etc.)
2. For each entity block: extract properties (values + units) into shabda key:value pairs
3. Detect connections between entities (series/parallel, rope, collision, etc.)
4. Emit entity nodes + connection nodes + root scene node via `Proof_graph.join`
5. Store goals in root node shabda
6. Return root node name

**`extract_kinematic_chain`** — for robot arms:
```
emits: arm-<hash>, joint-N-<hash>, link-N-<hash>, target-<hash>
key shabda fields: joint-type, axis-x/y/z, joint-angle, joint-speed-max,
                   rated-torque, rated-power, link-length, link-mass
root slokas: kinematic-chain-swarupa aayaama-traya-sthita
```

**`extract_circuit`** — for electrical circuits:
```
emits: circuit-<hash>, component-N-<hash>, junction-N-<hash>, loop-N-<hash>
key shabda fields: component-type (resistor/capacitor/battery/inductor),
                   resistance/capacitance/voltage/inductance, topology (series/parallel)
root slokas: circuit-swarupa sandhi-swarupa krama-swarupa domain-physics-sthita
```

**`extract_pulley`** — for pulley/Atwood systems:
```
emits: pulley-system-<hash>, mass-N-<hash>, pulley-N-<hash>, rope-N-<hash>
key shabda fields: mass, initial-velocity, height, friction-coefficient (pulley)
root slokas: sandhi-swarupa sambandha-swarupa domain-physics-sthita
```

**`extract_collision`** — for collision events:
```
emits: collision-<hash>, body-N-<hash>
key shabda fields: mass, velocity, collision-type (elastic/inelastic)
root slokas: sandhi-swarupa domain-physics-sthita
```

**`extract_oscillator`** — for SHM systems:
```
emits: oscillator-<hash>, mass-<hash>, spring-<hash> or pendulum-<hash>
key shabda fields: mass, spring-constant, amplitude, length (pendulum)
root slokas: spanda-swarupa domain-physics-sthita
```

**`extract_generic`** — fallback for unrecognized topology:
```
emits: scene-<hash>, entity-N-<hash>
key shabda fields: all detected float+unit pairs
root slokas: domain-physics-sthita
goals → passed to compose-plan which uses existing chain_resolve as fallback
```

**Detection helpers** (all in `yantra_pipeline_ops.ml`):

| Helper | Detects | Examples |
|---|---|---|
| `detect_joint_count` | Number before "joint"/"DOF" | "3-joint", "3 DOF", "two joints" |
| `segment_by_joint` | Split tokens at "joint N" markers | Sequential blocks per joint |
| `detect_joint_type` | Joint type word | "revolute", "prismatic", "spherical" |
| `detect_joint_axis` | Axis from "about Z", "along Y", "[0,0,1]" | Returns [ax;ay;az] |
| `detect_float_before_unit` | Float followed by unit token | "0.5m", "1kg", "2 rad/s" |
| `detect_rated_torque` | "rated N N·m" or "motor rated N N·m" | Returns float |
| `detect_rated_power` | "N W" near "motor"/"rated" | Returns float |
| `detect_target_position` | "(x,y,z)", "[x y z]", "position x=N y=N z=N" | Returns float list |
| `detect_goals` | Words after "find:"/"compute:" with kriya-yantra role | Returns string list |

**Unit recognition** uses `matra-aayaama.shabda` — look up token against known unit names
(metre, kilogram, radian, radian-per-second, newton-metre, watt etc.).

**Axis recognition:**
- "Z axis" / "about Z" → [0.0; 0.0; 1.0]
- "Y axis" / "about Y" → [0.0; 1.0; 0.0]
- "X axis" / "about X" → [1.0; 0.0; 0.0]
- "[0,0,1]" or "(0,0,1)" → parse directly

**Register arity:**
```ocaml
(* yantra_eval.ml *)
Yantra_parser.register_graph_op_arity "scene-extract" 1;
```

---

### 5B. `scene-narrate` op

**File:** `vyakarana/lib/yantra_pipeline_ops.ml`
**Arity:** 1 (takes VNode arm root name)
**Returns:** `VString` narration

```ocaml
| "scene-narrate" ->
  let arm_name = as_string (e_eval k e (List.nth args 0)) in
  let arm_pairs = Setu.read_shabda k arm_name in
  let n_joints = int_of_string (List.assoc "n-joints" arm_pairs) in
  let workspace = List.assoc "workspace" arm_pairs in
  let hash = String.sub arm_name 4 (String.length arm_name - 4) in

  (* frame model line *)
  let frames = "sthira-apeksha (world)" ::
    List.init n_joints (fun i -> Printf.sprintf "chala-apeksha[%d]" i) in
  let frame_line = "  Frame model: " ^ String.concat " → " frames in

  (* per-joint lines: walk joint-N-hash nodes *)
  let joint_lines = List.init n_joints (fun i ->
    let jname = Printf.sprintf "joint-%d-%s" i hash in
    let lname = Printf.sprintf "link-%d-%s" i hash in
    let jp = Setu.read_shabda k jname in
    let lp = Setu.read_shabda k lname in
    let jtype = List.assoc_opt "joint-type" jp |> Option.value ~default:"revolute" in
    let ax = List.assoc_opt "axis-x" jp |> Option.value ~default:"0" in
    let ay = List.assoc_opt "axis-y" jp |> Option.value ~default:"0" in
    let az = List.assoc_opt "axis-z" jp |> Option.value ~default:"1" in
    let angle = List.assoc_opt "joint-angle" jp |> Option.value ~default:"0" in
    let spmax = List.assoc_opt "joint-speed-max" jp |> Option.value ~default:"?" in
    let rtorq = List.assoc_opt "rated-torque" jp |> Option.value ~default:"?" in
    let rpower= List.assoc_opt "rated-power" jp |> Option.value ~default:"?" in
    let llen  = List.assoc_opt "link-length" lp |> Option.value ~default:"?" in
    let lmass = List.assoc_opt "link-mass" lp |> Option.value ~default:"?" in
    Printf.sprintf
      "  Joint %d  %s  axis=[%s,%s,%s]  θ=%s rad  ω_max=%s rad/s  motor: %s N·m, %s W\n\
       \    └── Link %d  length=%sm  mass=%skg"
      i jtype ax ay az angle spmax rtorq rpower i llen lmass
  ) in

  (* target line *)
  let tname = "target-" ^ hash in
  let tp = Setu.read_shabda k tname in
  let tx = List.assoc_opt "x" tp |> Option.value ~default:"?" in
  let ty = List.assoc_opt "y" tp |> Option.value ~default:"?" in
  let tz = List.assoc_opt "z" tp |> Option.value ~default:"?" in
  let target_line = Printf.sprintf
    "  Target: end-effector to [%s, %s, %s] in world-space (sthira-apeksha)" tx ty tz in

  let goals_str = List.assoc_opt "goals" (Setu.read_shabda k arm_name)
    |> Option.value ~default:"" in
  let goals_line = "  Goals:  " ^ goals_str in

  let narration = String.concat "\n" (
    ["Scene understood:";
     Printf.sprintf "  Kinematic chain: %d-DOF serial arm in %s" n_joints workspace;
     frame_line; ""] @
    joint_lines @
    [""; target_line; goals_line]
  ) in
  Some (VString narration)
```

---

## Phase 6: Dynamic Tantra Composer

### 6A. `compose-plan` op

**File:** `vyakarana/lib/yantra_pipeline_ops.ml`
**Arity:** 1 (takes VNode arm root name)
**Returns:** `VList` of steps — `[[step-n, tantra-name, [inputs], [outputs]], ...]`

The composer walks the arm graph to extract bindings, then backward-chains
from goals over `tantra_index.by_output`:

```ocaml
| "compose-plan" ->
  let arm_name = as_string (e_eval k e (List.nth args 0)) in
  let idx = (Option.get !eval_ctx).ctx_index in
  let hash = String.sub arm_name 4 (String.length arm_name - 4) in
  let arm_pairs = Setu.read_shabda k arm_name in
  let n_joints = int_of_string (List.assoc "n-joints" arm_pairs) in

  (* collect all bindings from scene graph nodes *)
  let satisfied : (string, float) Hashtbl.t = Hashtbl.create 32 in

  (* from joint + link nodes: read shabda key:value pairs *)
  List.iter (fun i ->
    let jname = Printf.sprintf "joint-%d-%s" i hash in
    let lname = Printf.sprintf "link-%d-%s" i hash in
    let jp = Setu.read_shabda k jname in
    let lp = Setu.read_shabda k lname in
    (* store with indexed names so tantras can distinguish per-joint values *)
    List.iter (fun (k_str, v_str) ->
      match float_of_string_opt v_str with
      | Some f -> Hashtbl.replace satisfied (k_str ^ "-" ^ string_of_int i) f
      | None -> ()
    ) (jp @ lp)
  ) (List.init n_joints Fun.id);

  (* from target node *)
  let tname = "target-" ^ hash in
  let tp = Setu.read_shabda k tname in
  List.iter (fun (k_str, v_str) ->
    match float_of_string_opt v_str with
    | Some f -> Hashtbl.replace satisfied ("target-" ^ k_str) f
    | None -> ()
  ) tp;

  (* goals to satisfy *)
  let goals_str = List.assoc_opt "goals" arm_pairs |> Option.value ~default:"" in
  let goals = String.split_on_char ',' goals_str
    |> List.map String.trim |> List.filter (fun s -> s <> "") in

  (* backward-chain from goals over by_output *)
  let steps : tantra list ref = ref [] in
  let seen_tantras : (string, bool) Hashtbl.t = Hashtbl.create 16 in
  let queue = Queue.create () in
  List.iter (fun g -> Queue.push g queue) goals;

  while not (Queue.is_empty queue) do
    let target = Queue.pop queue in
    if not (Hashtbl.mem satisfied target) then begin
      match Hashtbl.find_opt idx.by_output target with
      | None -> ()
      | Some candidate_tantras ->
        (* pick tantra with most inputs already satisfied *)
        let scored = List.map (fun t ->
          let n_sat = List.length (List.filter (fun inp ->
            Hashtbl.mem satisfied inp.tp_name ||
            Hashtbl.mem satisfied inp.tp_canonical
          ) t.t_inputs) in
          (n_sat, t)
        ) candidate_tantras in
        let (_, best) = List.fold_left
          (fun (bs, bt) (s, t) -> if s > bs then (s, t) else (bs, bt))
          (List.hd scored) (List.tl scored) in
        if not (Hashtbl.mem seen_tantras best.t_name) then begin
          Hashtbl.replace seen_tantras best.t_name true;
          (* push unsatisfied inputs as new goals *)
          List.iter (fun inp ->
            if not (Hashtbl.mem satisfied inp.tp_name) then
              Queue.push inp.tp_name queue
          ) best.t_inputs;
          (* mark outputs satisfied *)
          List.iter (fun ret ->
            Hashtbl.replace satisfied ret.tp_name true
          ) best.t_returns;
          steps := best :: !steps
        end
    end
  done;

  (* topological sort — deps before consumers *)
  let ordered = topological_sort (List.rev !steps) idx in

  (* encode as VList of [step-n, name, [input-names], [output-names]] *)
  let encoded = List.mapi (fun i t ->
    VList [
      VFloat (float_of_int (i+1));
      VString t.t_name;
      VList (List.map (fun inp -> VString inp.tp_name) t.t_inputs);
      VList (List.map (fun ret -> VString ret.tp_name) t.t_returns);
    ]
  ) ordered in
  Some (VList encoded)
```

**`topological_sort`** — sorts tantra list so if tantra A produces output X
and tantra B consumes X, A comes before B:

```ocaml
let topological_sort (tantras : tantra list) (idx : tantra_index) : tantra list =
  (* Kahn's algorithm on the tantra DAG *)
  (* build adjacency: if t1 produces something t2 needs, t1 → t2 *)
  ...
```

---

### 6B. `execute-plan-traced` op

**File:** `vyakarana/lib/yantra_pipeline_ops.ml`
**Arity:** 2 (plan VList, arm root VNode)
**Returns:** `VList` of trace records `[[step-n, tantra-name, output-name, value, unit], ...]`

Seeds env from scene graph (reads joint/link shabda values), executes each tantra
in plan order, feeds outputs forward, collects trace records.

The key difference from the old approach: inputs for per-joint tantras are
assembled from indexed bindings (`joint-angle-0`, `link-length-0` etc.)
and the tantra is called once per joint in a loop.

---

### 6C. `format-scene-trace.tantra`

**File:** `brahman/yantra/robotics/format-scene-trace.tantra`

Receives:
- `narration string` — from `scene-narrate`
- `plan-steps list` — from `compose-plan`: `[[n, name, [inputs], [outputs]], ...]`
- `results list` — from `execute-plan-traced`: `[[n, name, output-name, value, unit], ...]`

Composes the full human-readable output. No OCaml formatting code.

```
tantra format-scene-trace

  inputs
    narration   string
    plan-steps  list
    results     list

  let
    decomp-header  = "Decomposition (graph-derived):"
    results-header = "Results:"

    step-lines = map plan-steps (fn s ->
      let n    = nth s 0
      let name = nth s 1
      let ins  = nth s 2
      let outs = nth s 3
      in concat "  Step " (to-string n) "  " name
                "  →  " (join outs ", ")
                "  (from: " (join ins ", ") ")")

    result-lines = map results (fn r ->
      let name  = nth r 2
      let value = nth r 3
      let unit  = nth r 4
      let unit-part = cond (eq unit "") "" otherwise (concat " " unit)
      in concat "  " name " = " (to-string value) unit-part)

    output = concat
      narration "\n\n"
      decomp-header "\n" (join step-lines "\n") "\n\n"
      results-header "\n" (join result-lines "\n")

  return
    output string

done
```

---

### 6D. `scene-understand.tantra`

**File:** `brahman/yantra/robotics/scene-understand.tantra`

```
tantra scene-understand

  inputs
    sentence  string

  let
    arm        = scene-extract sentence
    narration  = scene-narrate arm
    plan       = compose-plan arm
    trace      = execute-plan-traced plan arm
    output     = format-scene-trace narration plan trace

  return
    output  string

done
```

---

## Phase 7: n-DOF Tantras

The existing 2-DOF tantras (`ik-2dof`, `joint-velocity-2dof`) work on scalar inputs.
For n-DOF the tantras need list inputs. These are NEW tantras, not replacements.
The `compose-plan` selects the right one based on `n-joints` from the arm node.

| Tantra | Inputs | Returns | Notes |
|---|---|---|---|
| `fk-3d.tantra` | link-lengths list, joint-axes list, joint-angles list | joint-positions list, end-effector-pos list | Sequential homogeneous transform composition using `mat-mul`, `rot2d` extended to 3D |
| `ik-3d-jacobian.tantra` | link-lengths list, joint-axes list, joint-angles-init list, target-pos list | joint-angles list | Iterative Jacobian pseudo-inverse — calls `fk-3d` internally |
| `joint-velocity-ndof.tantra` | joint-angles list, joint-angles-target list, joint-speed-max list | joint-velocities list, move-time | Generalization of `joint-velocity-2dof` to n joints |

---

## Phase 8: Problem Mode

`PROBLEM...END` block in `vyakarana/bin/vyakarana.ml`.

```ocaml
| "PROBLEM" ->
  let lines = collect_until_end () in        (* read until "END" *)
  let sentence = String.concat " " lines in  (* join for scene-extract *)
  (* route through scene-understand.tantra *)
  match Yantra.run k yantra_idx yantra_session
    ("scene-understand when sentence is \"" ^ sentence ^ "\"") with
  | Some r -> Yantra.print_result r
  | None   -> Printf.printf "could not understand scene\n%!"
```

---

## Implementation Order (updated)

| Step | Files | What | Status |
|---|---|---|---|
| 1 | `brahman/yantra/robotics/` | 5 robotics tantras | ✓ done |
| 2 | `brahman/kosha/robotics/`, `brahman/sangati/` | 13 kosha + sangati nodes | ✓ done |
| 3 | `vyakarana/lib/yantra_pipeline_ops.ml` | `scene-extract` op — emits live graph nodes | next |
| 4 | `vyakarana/lib/yantra_pipeline_ops.ml` | `scene-narrate` op — walks arm graph, builds narration | next |
| 5 | `vyakarana/lib/yantra_eval.ml` | Register arities: `scene-extract:1`, `scene-narrate:1` | next |
| 6 | Build + EVAL test | `EVAL scene-extract "3-joint arm..."` → `VNode arm-<hash>` | next |
| 7 | `vyakarana/lib/yantra_pipeline_ops.ml` | `compose-plan` op — backward-chain + topo sort | — |
| 8 | Build + EVAL test | `EVAL compose-plan arm-<hash>` → step list | — |
| 9 | `vyakarana/lib/yantra_pipeline_ops.ml` | `execute-plan-traced` op | — |
| 10 | `brahman/yantra/robotics/format-scene-trace.tantra` | Output formatter | — |
| 11 | `brahman/yantra/robotics/scene-understand.tantra` | Top-level orchestrator | — |
| 12 | Build + integration test | Full `scene-understand` on arm sentence | — |
| 13 | `brahman/yantra/robotics/fk-3d.tantra` | 3D forward kinematics | — |
| 14 | `brahman/yantra/robotics/joint-velocity-ndof.tantra` | n-DOF velocity planning | — |
| 15 | `brahman/yantra/robotics/ik-3d-jacobian.tantra` | Jacobian IK | — |
| 16 | `vyakarana/bin/vyakarana.ml` | `PROBLEM...END` REPL handler | — |
| 17 | Binary cache (`--cache` flag) | Cold start <60ms | — |

---

## Measured Targets

| Metric | Now | Target | Step |
|---|---|---|---|
| `arm-plan-2dof` via EVAL | ✓ | ✓ | done |
| `scene-extract` emits correct graph nodes | ✗ | ✓ | 3 |
| `scene-narrate` produces correct narration | ✗ | ✓ | 4 |
| `compose-plan` builds correct DAG | ✗ | ✓ | 7 |
| `execute-plan-traced` runs DAG with feed-forward | ✗ | ✓ | 9 |
| `format-scene-trace` formats full output | ✗ | ✓ | 10 |
| Full `scene-understand` on 3-joint arm sentence | ✗ | ✓ | 12 |
| 3D FK + n-DOF velocity planning | ✗ | ✓ | 13-14 |
| Jacobian IK for n-DOF | ✗ | ✓ | 15 |
| `PROBLEM...END` REPL handler | ✗ | ✓ | 16 |
| Cold start with `--cache` | 577ms | <60ms | 17 |

---

## Hardcoded Things That Remain (Intentional)

| Thing | Where | Reason |
|---|---|---|
| Core 10 dim constants (swarupa=0...) | `proof_graph.ml` | Bootstrap foundation |
| `"visheshanam-ring"` node name | `om_parser.ml` | Well-named constant |
| `"matra-beeja"` node name | `vyakarana.ml` startup | Well-named constant |
| `arm-plan-2dof.tantra` flat inlined | `brahman/yantra/robotics/` | Keep for regression |
| `ik-2dof.tantra` analytic closed-form | `brahman/yantra/robotics/` | Faster than Jacobian for 2-DOF |
