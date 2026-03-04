# Vyakarana Socket + Dual-App CRDT Plan

## Goal
- Keep `vyakarana` clean and algorithmic.
- Move orchestration, session handling, transport, scheduling, and rendering integration to Rust.
- Run dual apps (chat + graph/audio) with shared CRDT session layers.
- Emit execution dynamics so Raylib can render proof-graph resonance (animation) and optionally drive audio.

## Core Decisions
- Transport between Rust and engine: Unix domain socket (UDS), framed JSON.
- Session authority: CRDT layers (not engine memory).
- Query context sent to engine: question + bounded question chain + optional structured `context`.
- `context` is modeled as an active resonance frame (a running `prayoga`), not free-form prose.
- `question_chain` window size: **8 turns**.
- Ambiguity disambiguation threshold: ask clarification when top confidence is **< 0.75**.
- Add `resonance_ir` emission as the canonical visual-dynamics stream for Raylib.
- Rhythm/resonance authority is the proof graph execution itself; UI layers render, not reinterpret.

## Runtime Architecture
- OCaml (`vyakarana`): inference, graph reasoning, symbolic output generation.
- Rust orchestrator: socket client/server lifecycle, queueing, retries, timeouts, normalization, CRDT writes.
- Slint app (`Vyakarana Chat`): prompt/response UX, clarification chips, turn timeline.
- Raylib app (`Vyakarana Graph`): graph simulation playback and native audio from `music_ir`.

## CRDT Session Model
- `vyakarana/<session_id>/turns`
- `vyakarana/<session_id>/queries`
- `vyakarana/<session_id>/results`
- `vyakarana/<session_id>/graph_deltas`
- `vyakarana/<session_id>/music_ir`
- `vyakarana/<session_id>/resonance_ir`
- `vyakarana/<session_id>/playback`
- `vyakarana/<session_id>/understanding`

Notes:
- Turns/results are immutable per `turn_id`; corrections are new turns.
- Playback uses last-writer-wins semantics.
- Understanding state uses merge-friendly CRDT map/set semantics.

## Socket Protocol v1

### Request
- `request_id`
- `session_id`
- `turn_id`
- `question`
- `question_chain` (max 8 turns)
- optional `context`
  - optional `running_prayoga`
    - `id`
    - `domain`
    - `seeds[]`
    - optional `focus_nodes[]`
    - optional `thaalam`
    - optional `intensity` (0.0-1.0)
  - optional `resolved_ref`

### Context Semantics (`running_prayoga`)
- `running_prayoga` represents a currently active process that should influence interpretation of new queries.
- It acts as a resonance lens: boost ranking toward nodes connected to its `domain`, `seeds`, and `focus_nodes`.
- It is a soft prior, not a hard constraint; normal graph reasoning remains primary.
- If top referent confidence remains `< 0.75`, return `needs_clarification` as usual.

### Response
- `status`: `ok | needs_clarification | error`
- `answer_text`
- `steps`
- `next_questions`
- `graph_delta`
- `music_ir`
- `resonance_ir`
- `assets`
- `diagnostics`

### Clarification Response (Ambiguity)
Returned when referent resolution is uncertain and top confidence `< 0.75`.

- `status: needs_clarification`
- `pronoun`
- `candidates[]`
  - `node_id`
  - `label`
  - `confidence`
  - `reason`
- `clarification_prompt`

### Concrete JSON Examples (v1 Snapshot)

Request:

```json
{
  "schema_version": "1.0",
  "request_id": "req_20260302_001",
  "session_id": "session_alpha",
  "turn_id": "turn_0007",
  "question": "how is he related to gamaka now?",
  "question_chain": [
    {
      "turn_id": "turn_0005",
      "role": "user",
      "text": "explain andolan in sangeetham"
    },
    {
      "turn_id": "turn_0006",
      "role": "assistant",
      "text": "andolan is linked to gamaka through spanda and swara"
    }
  ],
  "context": {
    "running_prayoga": {
      "id": "prayoga_01",
      "domain": "sangeetham",
      "seeds": ["gamaka", "andolan", "thaalam"],
      "focus_nodes": ["gamaka"],
      "thaalam": "adi",
      "intensity": 0.82
    }
  }
}
```

`ok` response:

```json
{
  "schema_version": "1.0",
  "request_id": "req_20260302_001",
  "session_id": "session_alpha",
  "turn_id": "turn_0007",
  "status": "ok",
  "answer_text": "andolan is currently resolved as a gamaka-linked oscillation inside sangeetham.",
  "steps": [
    {
      "pass": 1,
      "kind": "pure_domain",
      "text": "andolan is same-as gamaka; rests-on shruti; connects-to swara"
    },
    {
      "pass": 2,
      "kind": "nature_equiv",
      "text": "thaalam/spanda links reinforce resonance path"
    }
  ],
  "next_questions": [
    "what action of resonance as logos should we test next?"
  ],
  "graph_delta": {
    "nodes_activated": ["andolan", "gamaka", "swara", "thaalam", "spanda"],
    "edges_activated": [
      { "source": "andolan", "relation": "abheda", "target": "gamaka" },
      { "source": "andolan", "relation": "yukta", "target": "swara" },
      { "source": "bhava", "relation": "janya", "target": "thaalam" }
    ]
  },
  "music_ir": {
    "meta": {
      "request_id": "req_20260302_001",
      "session_id": "session_alpha",
      "turn_id": "turn_0007",
      "source_nodes": ["andolan", "gamaka", "thaalam"]
    },
    "timing": {
      "bpm": 96,
      "cycle_beats": 8,
      "ticks_per_beat": 24
    },
    "voices": [
      {
        "voice_id": "v_melody",
        "label": "gamaka-line",
        "timbre": "piano",
        "gain": 0.6,
        "pan": 0.0,
        "octave": 4,
        "speed": 1.0
      }
    ],
    "events": [
      {
        "t_start_tick": 0,
        "t_dur_tick": 24,
        "voice_id": "v_melody",
        "pitch": "g4",
        "velocity": 0.82,
        "articulation": "legato",
        "tags": ["gamaka"]
      }
    ],
    "automation": [],
    "provenance": [
      {
        "source": "andolan",
        "relation": "abheda",
        "target": "gamaka"
      }
    ]
  },
  "resonance_ir": {
    "meta": {
      "request_id": "req_20260302_001",
      "session_id": "session_alpha",
      "turn_id": "turn_0007",
      "source_nodes": ["andolan", "gamaka", "thaalam"]
    },
    "timing": {
      "bpm": 96,
      "cycle_beats": 8,
      "ticks_per_beat": 24,
      "accent_pattern": [1.0, 0.4, 0.6, 0.8, 0.4, 0.6, 0.8, 0.4]
    },
    "nodes": [
      { "node_id": "andolan", "energy": 0.91, "relevance": 0.95, "focus": true },
      { "node_id": "gamaka", "energy": 0.88, "relevance": 0.92 }
    ],
    "edges": [
      {
        "source": "andolan",
        "target": "gamaka",
        "flow": 0.84,
        "direction_bias": 0.7
      }
    ],
    "events": [
      {
        "t_tick": 0,
        "kind": "focus_shift",
        "target": "andolan",
        "strength": 0.8,
        "reason": "running_prayoga_focus"
      }
    ],
    "camera": {
      "center_node": "andolan",
      "zoom_bias": 0.12,
      "breath": 0.25
    }
  },
  "assets": {
    "strudel": "stack(note(\"g4\").sound(\"piano\"))"
  },
  "diagnostics": {
    "passes": 2,
    "connections": 98,
    "confidence_top": 0.86
  }
}
```

`needs_clarification` response:

```json
{
  "schema_version": "1.0",
  "request_id": "req_20260302_002",
  "session_id": "session_alpha",
  "turn_id": "turn_0008",
  "status": "needs_clarification",
  "pronoun": "he",
  "candidates": [
    {
      "node_id": "gamaka",
      "label": "gamaka",
      "confidence": 0.62,
      "reason": "closest in question_chain and running_prayoga"
    },
    {
      "node_id": "andolan",
      "label": "andolan",
      "confidence": 0.58,
      "reason": "recent node with high resonance"
    }
  ],
  "clarification_prompt": "when you say 'he', do you mean gamaka or andolan?",
  "diagnostics": {
    "confidence_top": 0.62,
    "threshold": 0.75
  }
}
```

`error` response:

```json
{
  "schema_version": "1.0",
  "request_id": "req_20260302_003",
  "session_id": "session_alpha",
  "turn_id": "turn_0009",
  "status": "error",
  "error": {
    "code": "ENGINE_TIMEOUT",
    "message": "vyakarana request timed out before completion",
    "retryable": true
  },
  "diagnostics": {
    "timeout_ms": 5000
  }
}
```

## Music Output Strategy
- Keep existing Strudel generation path.
- Add canonical backend-neutral `music_ir` for native playback and visualization sync.
- Rust derives renderer/audio-specific execution from `music_ir`.

## Resonance Output Strategy
- Add canonical backend-neutral `resonance_ir` for graph motion dynamics tied to proof execution.
- `resonance_ir` is separate from `music_ir` but can share the same `thaalam` timing grid.
- Raylib consumes `resonance_ir` for animation even when audio is disabled.
- `thaalam`, beat accents, and resonance energy are graph-derived outputs from engine reasoning paths.
- `running_prayoga` in request is only a soft lens; emitted rhythm remains graph-authoritative.

### `resonance_ir` v1
- `meta`: `request_id`, `session_id`, `turn_id`, `source_nodes`
- `timing`: `bpm`, `cycle_beats`, `ticks_per_beat`, `accent_pattern[]`
- `nodes[]`: `node_id`, `energy`, `relevance`, optional `focus`
- `edges[]`: `source`, `target`, `flow`, optional `direction_bias`
- `events[]`: `t_tick`, `kind`, `target`, `strength`, optional `reason`
- `camera`: optional `center_node`, `zoom_bias`, `breath`

### `music_ir` v1
- `meta`: `request_id`, `session_id`, `turn_id`, `source_nodes`
- `timing`: `bpm`, `cycle_beats`, `ticks_per_beat`
- `voices[]`: `voice_id`, `label`, `timbre`, `gain`, `pan`, `octave`, `speed`
- `events[]`: `t_start_tick`, `t_dur_tick`, `voice_id`, `pitch`, `velocity`, `articulation`, `tags[]`
- `automation[]`: `voice_id`, `param`, `curve`, `from`, `to`, `t_start_tick`, `t_end_tick`
- `provenance[]`: node/relation chain for traceability

## Mapping Rules (Initial)
- `thaalam` -> cycle grid and accents.
- `swara` -> pitch mapping.
- `arohana/avarohana` -> directional note ordering.
- `nyasa` -> held/final duration multiplier.
- `gamaka` -> faster small modulation.
- `andolan` -> slower modulation.
- `meend` -> glide automation.

## Rust Orchestrator Responsibilities
- Ordered processing per `session_id`.
- Parallel sessions.
- Timeout/retry policy and socket health checks.
- Deterministic write pipeline: query -> response -> graph/audio layers.
- Optional response cache keyed by `session_id + turn_hash` (non-authoritative).

## Dual-App Behavior
- Chat app submits turns and renders results/clarifications.
- Graph app consumes `graph_deltas` + `resonance_ir` + `playback` cursor (and `music_ir` when audio enabled).
- Both windows stay synchronized via the same CRDT session namespace.

## Implementation Milestones
1. Freeze wire schema (`request`, `response`, `music_ir`, clarification contract).
2. Implement Rust socket orchestrator and per-session queue.
3. Add `vyakarana` socket mode emitting structured response payloads (`graph_delta`, `music_ir`, `resonance_ir`).
4. Wire CRDT turn pipeline end-to-end.
5. Implement chat clarification UX (candidate chips -> `resolved_ref`).
6. Implement raylib graph resonance animation from `resonance_ir` + native audio playback from `music_ir`.
7. Add E2E tests with two windows sharing one session.

## Acceptance Criteria
- Two independent windows can follow the same `session_id` and stay in sync.
- Ambiguous references produce `needs_clarification` with ranked candidates.
- Clarified follow-up continues reasoning correctly.
- `resonance_ir` is emitted and drives graph motion in raylib.
- `music_ir` is emitted and consumed by raylib app playback.
- Engine remains focused on reasoning; Rust owns orchestration and app integration.
