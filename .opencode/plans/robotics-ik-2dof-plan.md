# Robotics IK 2-DOF Plan
## Inverse Kinematics · Joint Velocities · Time-Optimized Motion · 2-DOF Planar Arm

---

## Core Insight: No New Ontology Needed

The full spatial and structural ontology is already in the graph. Robotics composes
FROM physics and 3D — it does not reinvent either.

| Existing concept | Robot arm meaning |
|---|---|
| `akasham` | space itself — the unbounded field prior to dimension |
| `aayaama-dvaya` | 2D workspace — the tala (flat field) in which the arm operates |
| `bindu` | a point in that space — the end-effector target (x, y) |
| `rekha` | a directed line segment — each link IS a rekha |
| `armature` (3d kosha) | the whole arm — the kinematic chain |
| `bone` (3d kosha) | each rigid link segment |
| `bone.parent-yukta child-yukta` | krama ordering: base → link1 → link2 → effector |
| `scene-graph` | transform composition — each bone's world pos = parent × local |
| `kona` | joint angle — the revolute DOF state |
| `angular-velocity` | dθ/dt — rate of joint angle change (kramanusara wrt time) |
| `radian`, `radian-per-second` | units — already in `matra-aayaama.shabda` |

`domain-3d` already references `domain-physics`. Robotics inherits both by pointing
to `domain-3d`. The workspace IS `aayaama-dvaya` — two-dimensional, bounded by
the reach of the arm (L1 + L2), with the target as a `bindu` in the `tala`.

---

## The Problem

> "A 2-joint robot arm. Link 1 is 5 metres, link 2 is 3 metres.
> Currently at angles 0, 0. Max joint speeds are 2 rad/s and 3 rad/s.
> Point the end effector at position (3, 4).
> Find the joint angles, joint velocities, and time required."

### The Three Computation Layers

**Layer 1 — Inverse Kinematics (position level)**
Given target (x, y), find θ1, θ2 — where do the joints need to END UP.

```
cos(θ2) = (x² + y² - L1² - L2²) / (2·L1·L2)
θ1 = atan2(y, x) - atan2(L2·sin(θ2), L1 + L2·cos(θ2))
```

**Layer 2 — Joint Velocities (kramanusara level)**
dθ/dt for each joint — the rate of change of angle wrt time.
The apeksha here is time (as in physics), but the quantity differentiating
is joint-angle (not displacement). Same kramanusara structure, different apeksha.

```
ω = dθ/dt    ← kramanusara of kona wrt time
```

**Layer 3 — Time Optimization**
Synchronized motion: both joints finish simultaneously.
The bottleneck joint runs at max speed; the other is scaled down.

```
T = max(|Δθ1|/ω1_max, |Δθ2|/ω2_max)
ω1_actual = Δθ1 / T
ω2_actual = Δθ2 / T
```

### Verified Answer for the Concrete Problem

```
L1=5, L2=3, target=(3,4), θ_current=(0,0), ω_max=(2,3)

cos(θ2) = (9 + 16 - 25 - 9) / 30 = -9/30 = -0.3
θ2 = acos(-0.3) ≈ 1.8755 rad (107.46°)

θ1 = atan2(4,3) - atan2(3·sin(1.8755), 5 + 3·cos(1.8755))
   ≈ 0.9273 - 0.6098 ≈ 0.3175 rad (18.19°)

Verify: 5·cos(0.3175) + 3·cos(1.8755+0.3175) ≈ 3.0 ✓
        5·sin(0.3175) + 3·sin(1.8755+0.3175) ≈ 4.0 ✓

Δθ1 = 0.3175, Δθ2 = 1.8755
t1 = 0.3175/2 = 0.1588s, t2 = 1.8755/3 = 0.6252s
T = max(0.1588, 0.6252) = 0.6252s

ω1 = 0.3175 / 0.6252 ≈ 0.508 rad/s  (joint 2 is bottleneck)
ω2 = 1.8755 / 0.6252 ≈ 3.000 rad/s  (joint 2 at max speed)
```

---

## What Needs to Be Built

### Status: Nothing Pre-exists in Robotics

| What | File | Status |
|---|---|---|
| `asin`, `acos`, `atan2` math primitives | `vyakarana/lib/yantra_ops.ml` | ✗ missing |
| `domain-robotics.om` | `brahman/kosha/robotics/` | ✗ missing |
| `ik-2dof.tantra` | `brahman/yantra/robotics/` | ✗ missing |
| `joint-velocity-2dof.tantra` | `brahman/yantra/robotics/` | ✗ missing |
| `arm-plan-2dof.tantra` | `brahman/yantra/robotics/` | ✗ missing |
| Robotics token roles | `brahman/kosha/language/english/token-roles.om` | ✗ missing |

### Already Available (no changes needed)

| What | Where |
|---|---|
| `sin`, `cos`, `sqrt`, `power`, `abs`, `max`, `div`, `mul`, `sub`, `add` | `yantra_ops.ml` |
| `radian`, `radian-per-second`, `metre` dim vectors | `matra-aayaama.shabda` |
| `akasham`, `aayaama-dvaya`, `bindu`, `rekha`, `tala` | `brahman/sangati/` |
| `armature`, `bone`, `scene-graph` | `brahman/kosha/3d/blender/` |
| `kona`, `angular-velocity` | `brahman/kosha/physics/` |
| `domain-3d` (already refs `domain-physics`) | `brahman/kosha/3d/domain-3d.om` |

---

## Implementation

### Step 1: `yantra_ops.ml` — Add `asin`, `acos`, `atan2`

Add alongside the existing `sin`/`cos`/`tan` block:

```ocaml
| "asin"  -> Some (VFloat (asin  (as_float (e_eval k e (List.nth args 0)))))
| "acos"  -> Some (VFloat (acos  (as_float (e_eval k e (List.nth args 0)))))
| "atan2" -> Some (VFloat (atan2 (as_float (e_eval k e (List.nth args 0)))
                                 (as_float (e_eval k e (List.nth args 1)))))
```

Note: `asin` is already CALLED in `snell-niyama.tantra` but was never added to
the dispatch table — so snell has been silently failing. This fixes that too.

### Step 2: `brahman/kosha/robotics/domain-robotics.om`

```
sangati domain-robotics
  "domain-3d-yukta domain-physics-yukta"
  "aayaama-dvaya-sthita tala-sthita akasham-yukta"
  "armature-yukta bone-yukta scene-graph-yukta"
  "kona-yukta angular-velocity-yukta time-yukta"
  "kramanusara-yukta apeksha-yukta"
shabda robotics, robot-arm, manipulator
done
```

### Step 3: `brahman/yantra/robotics/ik-2dof.tantra`

Inverse kinematics — independently callable, returns θ1 and θ2:

```
tantra ik-2dof

  -- 2-DOF planar IK in aayaama-dvaya (the 2D tala)
  -- bone 1 = rekha of length L1 rotating at the base (sandhi/joint 1)
  -- bone 2 = rekha of length L2 rotating at the elbow (sandhi/joint 2)
  -- target = bindu at (x, y) in world-space
  --
  -- cos(θ2) = (x² + y² - L1² - L2²) / (2·L1·L2)
  -- θ1 = atan2(y,x) - atan2(L2·sin(θ2), L1 + L2·cos(θ2))
  --
  -- this solution is the elbow-down configuration.
  -- for elbow-up: theta2 = -acos(cos-theta2)

  inputs
    link-length-1   float  metre
    link-length-2   float  metre
    target-x        float  metre
    target-y        float  metre

  let
    x-sq        = mul target-x target-x
    y-sq        = mul target-y target-y
    r-sq        = add x-sq y-sq
    l1-sq       = mul link-length-1 link-length-1
    l2-sq       = mul link-length-2 link-length-2
    cos-theta2  = div (sub r-sq (add l1-sq l2-sq))
                      (mul 2 (mul link-length-1 link-length-2))
    theta2      = acos cos-theta2
    sin-theta2  = sin theta2
    alpha       = atan2 target-y target-x
    beta        = atan2 (mul link-length-2 sin-theta2)
                        (add link-length-1 (mul link-length-2 cos-theta2))
    theta1      = sub alpha beta

  return
    theta1  float  radian
    theta2  float  radian

done
```

### Step 4: `brahman/yantra/robotics/joint-velocity-2dof.tantra`

Joint velocity planning — independently callable:

```
tantra joint-velocity-2dof

  -- synchronized joint motion: both joints start and finish together
  -- the bottleneck joint (larger |Δθ|/ω_max) runs at its max speed
  -- the other joint is scaled to finish at the same time T
  --
  -- this minimizes total motion time while respecting both speed limits
  -- it is the kramanusara of kona wrt time for each joint: ω = dθ/dt

  inputs
    theta1-current  float  radian
    theta2-current  float  radian
    theta1-target   float  radian
    theta2-target   float  radian
    omega1-max      float  radian-per-second
    omega2-max      float  radian-per-second

  let
    delta-theta1  = sub theta1-target theta1-current
    delta-theta2  = sub theta2-target theta2-current
    t1            = div (abs delta-theta1) omega1-max
    t2            = div (abs delta-theta2) omega2-max
    move-time     = max t1 t2
    omega1        = div delta-theta1 move-time
    omega2        = div delta-theta2 move-time

  return
    omega1      float  radian-per-second
    omega2      float  radian-per-second
    move-time   float  second

done
```

### Step 5: `brahman/yantra/robotics/arm-plan-2dof.tantra`

Full plan — IK + velocity inlined flat. No tantra-to-tantra call needed.
All math in one let-block:

```
tantra arm-plan-2dof

  -- complete 2-DOF arm motion plan
  -- workspace: aayaama-dvaya — the 2D tala
  -- structure: armature with two bones (rekha) joined at sandhi points (kona state)
  -- given: current config (purva-avastha), target bindu, joint speed limits
  -- computes: target config (uttara-avastha), joint velocities, motion time

  inputs
    link-length-1   float  metre
    link-length-2   float  metre
    theta1-current  float  radian
    theta2-current  float  radian
    target-x        float  metre
    target-y        float  metre
    omega1-max      float  radian-per-second
    omega2-max      float  radian-per-second

  let
    -- IK block: find target joint angles from target bindu position
    x-sq          = mul target-x target-x
    y-sq          = mul target-y target-y
    r-sq          = add x-sq y-sq
    l1-sq         = mul link-length-1 link-length-1
    l2-sq         = mul link-length-2 link-length-2
    cos-theta2    = div (sub r-sq (add l1-sq l2-sq))
                        (mul 2 (mul link-length-1 link-length-2))
    theta2        = acos cos-theta2
    sin-theta2    = sin theta2
    alpha         = atan2 target-y target-x
    beta          = atan2 (mul link-length-2 sin-theta2)
                          (add link-length-1 (mul link-length-2 cos-theta2))
    theta1        = sub alpha beta
    -- velocity block: synchronized motion, minimize time
    delta-theta1  = sub theta1 theta1-current
    delta-theta2  = sub theta2 theta2-current
    t1            = div (abs delta-theta1) omega1-max
    t2            = div (abs delta-theta2) omega2-max
    move-time     = max t1 t2
    omega1        = div delta-theta1 move-time
    omega2        = div delta-theta2 move-time

  return
    theta1      float  radian
    theta2      float  radian
    omega1      float  radian-per-second
    omega2      float  radian-per-second
    move-time   float  second

done
```

### Step 6: Token roles

Add to `brahman/kosha/language/english/token-roles.om`:

```
arm:concept joint:concept link:concept bone:concept armature:concept
reach:kriya-yantra point:kriya-yantra plan:kriya-yantra
```

---

## Implementation Order

| Step | File | What | Risk |
|---|---|---|---|
| 1 | `vyakarana/lib/yantra_ops.ml` | Add `asin`, `acos`, `atan2` | Low — 3 lines |
| 2 | `brahman/kosha/robotics/domain-robotics.om` | New domain kosha | Low |
| 3 | `brahman/yantra/robotics/ik-2dof.tantra` | Inverse kinematics | Low |
| 4 | `brahman/yantra/robotics/joint-velocity-2dof.tantra` | Joint velocity + time | Low |
| 5 | `brahman/yantra/robotics/arm-plan-2dof.tantra` | Full inlined plan | Low |
| 6 | `brahman/kosha/language/english/token-roles.om` | Robotics token roles | Low |
| 7 | Build + test | Verify concrete query | — |

### Test Query

```
link-length-1 is 5 | link-length-2 is 3 | target-x is 3 | target-y is 4 |
theta1-current is 0 | theta2-current is 0 |
omega1-max is 2 | omega2-max is 3 | find arm-plan-2dof
```

Expected output:
```
theta1    ≈ 0.3175 rad
theta2    ≈ 1.8755 rad
omega1    ≈ 0.508  rad/s
omega2    ≈ 3.000  rad/s
move-time ≈ 0.625  s
```

---

## Future Extensions (Not in This Plan)

| Extension | What it requires |
|---|---|
| Elbow-up configuration | `theta2 = neg (acos cos-theta2)` — second solution |
| Reachability check | `sqrt(r-sq) le (add link-length-1 link-length-2)` before IK |
| 3-DOF planar arm | Third bone, third joint — extends IK to redundant case (iterative) |
| 3D arm (6-DOF) | Jacobian + iterative Newton-Raphson — `aayaama-traya` workspace |
| Trajectory planning | Polynomial interpolation of θ(t) — smooth motion, not step |
| Obstacle avoidance | Constraint on workspace bindu — joint-space planning |
| Jacobian computation | `d(end-effector)/d(theta_i)` — each column is kramanusara wrt joint-angle |

The Jacobian is the natural next step: each column is a kramanusara with a joint-angle
as apeksha — exactly the generalized framework already in the graph.
