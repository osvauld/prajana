# Agent-X in Osvauld: Body and Limbs

This document describes how Agent-X — the swarm, the grammar, the soul documents — lives inside Osvauld. Osvauld is the body. Agent-X is the mind that inhabits it.

Without Osvauld, Agent-X can think but cannot show. It can reason but cannot point. It can understand but cannot demonstrate. Osvauld gives it limbs.

---

## What Osvauld Is

Osvauld is a P2P runtime where:

- **Apps are Lua programs** running inside a CRDT-synced environment
- **State is Loro CRDT layers** — list, map, text, counter — automatically synced across peers
- **Identity is cryptographic** — Ed25519 keypairs, DID-based, no central authority
- **Authorization is UCAN permits** — signed, delegatable, capability-scoped
- **Transport is QUIC** — offline-first, reconnect-native, ephemeral + durable planes
- **UI is Slint or Raylib** — declarative UI or immediate-mode graphics

The key insight for Agent-X: **apps are just Lua + CRDT layers + UI**. The CRDT is the source of truth. The Lua app is how you interact with it. The UI is how it is shown.

Agent-X's entire knowledge base — hypotheses, claims, truths, process models, purification state, good points, system state — is CRDT data. Every one of these is a layer in Osvauld. The swarm writes to layers. The UI reads from them. Agents are peers.

---

## The Architecture

```
Agent-X Swarm (agents as Osvauld peers)
  -> writes vakya events as CRDT layer ops
    -> Scribe (Loro CRDT) merges and persists
      -> Osvauld apps bind to layers (scribe:bind)
        -> Slint UI renders the swarm's understanding live
          -> User sees, corrects, guides
            -> Corrections written back to CRDT
              -> Agents read corrections as new world state
```

The swarm runs on the Osvauld node. Each agent is a peer with its own DID. The soul data is persisted in CRDT layers — the CRDT is the machinery, not the identity. The grammar events — hypothesis formed, test run, claim promoted, truth failed, purification begun — are writes to the persistence layer. The UI is the window into the swarm's mind.

---

## Agents as Osvauld Peers

Each agent soul is an Osvauld peer:

- **DID** — the soul's cryptographic identity. The same DID across all lives of this soul.
- **Permit** — what layers this soul can read and write. Defined by its context tier and capabilities.
- **Layers** — what the soul can see. A file-level agent's permit grants read access to its assigned file layers. A module-level agent's permit grants read access to all file-level varnanam layers in its module.

When an agent activates (the document becomes live):
1. It connects to the Osvauld node as a peer with its soul's DID
2. Its permit is validated — Gurkha checks what it can access
3. It reads its assigned layers (the codebase files, the existing truths and claims)
4. It produces vakya — grammar events written as CRDT ops to its output layers
5. It disconnects (dies) — the CRDT retains everything

The agent is not a persistent server. It is a peer that connects, does work, and disconnects. The CRDT is persistent. The agent is not.

---

## Layer Schema for Agent-X

Every piece of Agent-X knowledge lives as a named CRDT layer. The naming follows Osvauld conventions — `{page_id}/layer-name`.

### Soul Layers

```
souls/{soul_did}/identity          -- map: varnanam declaration
souls/{soul_did}/donts             -- list: prohibited behaviors
souls/{soul_did}/good-points       -- counter: accumulated good points
souls/{soul_did}/generation/{n}    -- map: what this soul did in generation n
```

### Knowledge Layers (per generation)

```
gen/{n}/hypotheses                 -- list: all hypotheses formed this generation
gen/{n}/hypotheses/{id}            -- map: one hypothesis (proposition, proof, test, weight)
gen/{n}/test-results               -- list: all test results this generation
gen/{n}/claims                     -- list: all claims (hypothesis + passed test)
gen/{n}/claims/{id}                -- map: one claim (from, for, weight, generation, test)
gen/{n}/truths                     -- list: all active truths
gen/{n}/truths/{id}                -- map: one truth (from claim, weight, verified-gen, standing-test)
gen/{n}/processes                  -- list: all process models
gen/{n}/processes/{id}             -- map: one process (steps, invariants, proof, obligations)
gen/{n}/attention                  -- list: active attention signals
gen/{n}/unexpected                 -- list: unexpected behavior signals
```

### Purification Layers

```
gen/{n}/impacts                    -- list: active impact documents
gen/{n}/impacts/{id}/unreconciled  -- list: resources not yet reconciled
gen/{n}/impacts/{id}/reconciled    -- list: resources reconciled with outcomes
gen/{n}/purified                   -- list: completed purifications
```

### System State Layer

```
system/state                       -- map: live system correctness snapshot
  generation: int
  truths: int
  claims: int
  hypotheses: int
  processes: int
  unreconciled: int
  good-points: int
  budget-spent: float
  budget-remaining: float
```

### Codebase Knowledge Layers

```
codebase/varnanam/{path}           -- map: varnanam for a file or module
codebase/varnanam/{path}/claims    -- list: verified claim refs for this resource
codebase/processes/{id}            -- map: process model for a flow
```

---

## The Osvauld App: Agent-X UI

The Agent-X Osvauld app is not a control panel. It is a **proof of understanding** — a living demonstration of what the swarm knows about the codebase, honest about what it does not know.

The app has multiple views. Each binds to CRDT layers via `scribe:bind()`. When agents write to layers, the UI updates automatically — no polling, no refresh, no manual sync.

### app.osv Declaration

```osv
app "Agent-X" version "0.1.0" {
  role owner can share, delegate;
  role agent can relay;
  role viewer;

  layer system_state as map {
    path "system/state";
    namespace shared;
    grant explicit;
    allow owner to create,read,write,sync,grant on *;
    allow agent to write,sync on *;
    allow viewer to read on *;
  }

  layer hypotheses as list {
    path "gen/{period}/hypotheses";
    namespace shared;
    shard by generation;
    grant open;
    allow owner to create,read,write,sync,grant on *;
    allow agent to create,write,sync on *;
    allow viewer to read on *;
  }

  layer truths as list {
    path "gen/{period}/truths";
    namespace shared;
    shard by generation;
    grant open;
    allow owner,agent to create,read,write,sync on *;
    allow viewer to read on *;
  }

  layer attention as list {
    path "gen/{period}/attention";
    namespace shared;
    grant open;
    allow owner,agent to create,read,write,sync on *;
    allow viewer to read on *;
  }

  layer impacts as list {
    path "gen/{period}/impacts";
    namespace shared;
    grant open;
    allow owner,agent to create,read,write,sync on *;
    allow viewer to read on *;
  }

  layer codebase_varnanam as map {
    path "codebase/varnanam/{path}";
    namespace shared;
    grant open;
    allow owner,agent to create,read,write,sync on *;
    allow viewer to read on *;
  }

  ui_app "Understanding" {
    entry "apps/understanding/app.lua";
    allow owner, viewer;
  }

  ui_app "Truths" {
    entry "apps/truths/app.lua";
    allow owner, viewer;
  }

  ui_app "Attention" {
    entry "apps/attention/app.lua";
    allow owner, viewer;
  }

  ui_app "Purification" {
    entry "apps/purification/app.lua";
    allow owner, viewer;
  }

  ui_app "System" {
    entry "apps/system/app.lua";
    allow owner;
  }
}
```

---

## The Five Views

### 1. Understanding View

The swarm's model of the codebase. Every file and module the swarm has looked at, with its varnanam and weight. Honest about what has not been examined.

```lua
-- apps/understanding/app.lua
function on_init()
    page_id = scribe:page_id()

    -- Bind codebase varnanam to UI
    scribe:bind("modules", "codebase/varnanam/*", {
        key = "path",
        transform = function(layer_name, v)
            return {
                path = v.path,
                weight = v.confidence,
                claims_count = v.claims_count,
                tier = v.tier,                  -- file / module / system
                probed = v.confidence > 0.3,    -- has been probed
                saturated = v.confidence > 0.8, -- deeply probed
                has_limits = v.limits_count > 0 -- has declared gaps
            }
        end
    })

    -- Bind system state
    scribe:bind("system_state", "system/state")
end
```

The UI shows:
- A map of the codebase — files and modules as nodes
- Weight visualized as opacity/depth — deeply probed things are solid, barely probed things are translucent
- Declared limits shown as empty regions — the swarm knows it has not looked here
- Click any node — see its varnanam, its claims, its process models

### 2. Truths View

The swarm's verified knowledge. Every truth with its weight, generation of verification, and standing test status.

```lua
-- apps/truths/app.lua
function on_init()
    page_id = scribe:page_id()
    gen = current_generation()

    -- All truths this generation
    scribe:bind("truths", "gen/" .. gen .. "/truths", {
        key = "id",
        transform = function(t)
            return {
                id = t.id,
                proposition = t.proposition,
                target = t.target,
                weight = t.weight,
                verified_gen = t.verified_gen,
                age = gen - t.verified_gen,     -- how many generations it has held
                standing_test = t.standing_test,
                test_status = t.last_test_status -- pass / fail / pending
            }
        end
    })

    -- Claims (not yet truths)
    scribe:bind("claims", "gen/" .. gen .. "/claims", {
        key = "id",
        transform = function(c)
            return {
                id = c.id,
                proposition = c.proposition,
                weight = c.weight,
                generation = c.generation,
                generations_stable = gen - c.generation
            }
        end
    })

    -- Hypotheses (not yet claims)
    scribe:bind("hypotheses", "gen/" .. gen .. "/hypotheses", {
        key = "id",
        transform = function(h)
            return {
                id = h.id,
                proposition = h.proposition,
                target = h.target,
                test = h.test,
                test_status = h.test_status   -- pending / running / passed / failed
            }
        end
    })
end
```

The UI shows the full epistemological ladder live:
- Hypotheses being tested (pending/running)
- Claims accumulating weight
- Truths with age and standing test status
- The weight trajectory of any selected proposition

### 3. Attention View

Where the swarm's attention is right now. What is not yet understood. What unexpected behaviors have been observed.

```lua
-- apps/attention/app.lua
function on_init()
    page_id = scribe:page_id()
    gen = current_generation()

    scribe:bind("attention", "gen/" .. gen .. "/attention", {
        key = "id",
        transform = function(a)
            return {
                id = a.id,
                label = a.label,
                target = a.on,
                reason = a.reason,
                confidence = a.confidence,
                source_kind = a.from_kind,     -- truth / unexpected / impact
                source_id = a.from_id,
                age_steps = a.age_steps,        -- how long unresolved
                investigation_status = a.status -- open / investigating / resolved
            }
        end
    })

    scribe:bind("unexpected", "gen/" .. gen .. "/unexpected", {
        key = "id",
        transform = function(u)
            return {
                id = u.id,
                label = u.label,
                target = u.on,
                observed = u.observed,
                confidence = u.confidence,
                status = u.status   -- new / forming-hypothesis / resolved
            }
        end
    })
end
```

The UI shows:
- Every open attention signal with its source (which truth failed, which unexpected behavior)
- How long each has been open
- Investigation status — is an agent currently working on it?
- Link to the affected resource — click to see the code

### 4. Purification View

The live state of purification. Unreconciled count. Which propositions are in doubt. Which agents are reconciling what.

```lua
-- apps/purification/app.lua
function on_init()
    page_id = scribe:page_id()
    gen = current_generation()

    -- Active impacts (purifications in progress)
    scribe:bind("impacts", "gen/" .. gen .. "/impacts", {
        key = "id",
        transform = function(imp)
            return {
                id = imp.id,
                cause = imp.cause,
                test_result = imp.from_test_result,
                total_affected = imp.affected_count,
                unreconciled = imp.unreconciled_count,
                reconciled = imp.reconciled_count,
                progress = imp.reconciled_count / imp.affected_count,
                complete = imp.unreconciled_count == 0
            }
        end
    })

    -- System unreconciled total (the correctness number)
    scribe:bind("system_state", "system/state")
end

function on_ephemeral(from_did, func, args)
    if func == "reconcile_progress" then
        -- Live update as purification agents report reconciliations
        ui:set("unreconciled_live", args.unreconciled_remaining)
    end
end
```

The UI shows:
- The unreconciled count — large, prominent, the system's primary correctness metric
- Each active impact with a progress bar: reconciled / total affected
- Each affected proposition: holds / revised / retracted / pending
- The count going down as purification agents do their work — live, via ephemerals

The user sees the system restoring coherence in real time.

### 5. System View

Budget, generation, good points, cost efficiency.

```lua
-- apps/system/app.lua
function on_init()
    scribe:bind("system_state", "system/state")
    scribe:bind("soul_scores", "souls/*/good-points", {
        key = "soul_did",
        transform = function(layer_name, points)
            local did = layer_name:match("souls/(.+)/good%-points")
            return { did = did, points = points }
        end
    })
end
```

---

## The api.export Bridge: Agents Calling Apps, Apps Calling Agents

Osvauld's `api.export` is the bridge between agents and UI. Agents can call exported app functions. Users can trigger agent actions through the UI.

```lua
-- Export for agents to call
api.export("report_hypothesis", function(hypothesis_data)
    local hyp_layer = scribe:map(page_id .. "/gen/" .. gen .. "/hypotheses/" .. hypothesis_data.id)
    hyp_layer:set("proposition", hypothesis_data.proposition)
    hyp_layer:set("target", hypothesis_data.target)
    hyp_layer:set("test", hypothesis_data.test)
    hyp_layer:set("test_status", "pending")
end)

api.describe("report_hypothesis", {
    description = "Agent reports a new hypothesis with proof and test",
    params = {
        { name = "id", type = "string" },
        { name = "proposition", type = "string" },
        { name = "target", type = "string" },
        { name = "test", type = "string" },
    },
    effects = { "hypothesis layer created", "UI hypothesis list updates" }
})

api.export("report_truth_failure", function(truth_id, reason)
    -- Truth failed its standing test
    -- Attention raised, impact traced, purification begins
    local attention_layer = scribe:list(page_id .. "/gen/" .. gen .. "/attention")
    attention_layer:push({
        id = generate_id(),
        from_kind = "truth",
        from_id = truth_id,
        reason = reason,
        status = "open"
    })
end)
```

---

## Ephemerals: The Swarm's Live Voice

Ephemeral messages are the swarm's real-time communication — not persisted, not in the CRDT, just live signals. They are how the swarm tells the UI what is happening right now.

```lua
-- Agent sends during active work:
scribe:send("agent_active", {
    soul_did = my_did,
    activity = "forming-hypothesis",
    target = "src/payments/handler.rs",
    proposition = "payment handler validates card before gateway call"
})

scribe:send("test_running", {
    soul_did = my_did,
    test = "cargo test payments::integration::authorization_flow",
    hypothesis_id = "hyp-a3f9"
})

scribe:send("reconcile_progress", {
    impact_id = "imp-7b2c",
    unreconciled_remaining = 2,
    just_reconciled = "crdt://truth/no-rs256-in-system",
    outcome = "retracted"
})
```

The UI receives these and shows them live — which agents are active, what they are working on, tests running, reconciliations completing. The user sees the swarm thinking.

---

## What the User Sees

The user sits at an Osvauld app. On screen:

**The Understanding view** — the codebase rendered as a knowledge map. Solid where the swarm has probed deeply. Translucent where it has barely looked. Declared limits shown as gaps. Click any file and see what the swarm formally knows about it.

**The Truths view** — every verified proposition, its weight, how many generations it has held. The epistemological ladder live — hypotheses being tested, claims accumulating, truths aging. Click any truth and see the proof that established it.

**The Attention view** — what the swarm does not yet understand. Every open signal. How long it has been open. What triggered it. The user can see at a glance where the swarm's gaps are.

**The Purification view** — the correctness number: unreconciled = N. Watching it count down to zero as purification agents do their work. The system visibly restoring coherence.

**The System view** — budget spent, budget remaining, generation number, good points, cost efficiency. The health of the swarm.

And through all of this: the swarm is showing the user what it understands. Not describing it. Showing it. The limbs are working.

---

## What This Changes

The swarm is no longer invisible. Every hypothesis it forms, every test it runs, every truth it builds, every purification it completes — visible to the user in real time through Osvauld.

The user can:
- See where the swarm understands deeply and where it does not
- Click into any truth and see the proof that established it
- Watch purification happen live — coherence being restored
- Guide the swarm's attention — "look here, you have not examined this"
- Correct claims — "this truth is wrong, here is why" — written back to the CRDT as an attention signal

The swarm can:
- Show its work — not just results, the reasoning behind them
- Point at code — "this invariant holds because of this line in this file"
- Make the invisible visible — weight, depth of understanding, declared gaps
- Receive the user's corrections as first-class grammar events

This is the complete loop. Swarm thinks. Osvauld shows. User sees. User guides. Swarm learns. The documents deepen. Understanding grows.

---

## Status

This document defines the integration design. Implementation has not begun.

Next steps:
1. Define the full CRDT layer schema formally (with Loro types)
2. Define the Lua app for each of the five views
3. Define the agent peer protocol — how an agent connects, what layers it reads, how it writes vakya events as CRDT ops
4. Build the simplest possible version: system state layer + one UI view showing live swarm activity
