# Firstness Rank + Brahmam Ontology Plan

## Intention

This plan is intentionally slow and careful. Subtle meaning is primary.

Two linked tracks:

1. Track A: Ontology core (`brahma`, `om`, `spanda`, `karma`, `brahmam`, `brahman`, plus `string-theory` placement)
2. Track B: Firstness rank system (non-numeric precedence with question-conditioned shifts)

---

## Track A — Ontology Core (implement first)

### Canonical doctrine

- `brahma` = IS (not process)
- `om` = root functional impulse
- `spanda` = dynamic vibration
- `karma` = becoming-process (`om` interacting with `spanda` and `brahma`)
- `brahmam` = what becomes (manifested outcome, recurring)
- `brahman` = one who recognizes this process (`pratibodha` / `sakshi`)

### Tat-kshana + continuity

- `brahmam` must encode both:
  - `tat-kshana-phala` (momentary completion)
  - `nirantara-phala` (continuous emergence)
- `avrti` is non-final by structure: each completion gives rise to next.

### Inheritance law (locked)

- primary: `samskaara-phala`
- secondary: `parampara-phala`

### Black-hole clarification (locked)

- black-hole is a drishthanta/lens of root dynamics.
- black-hole is not origin of jiva/prana.
- avoid life/jiva phrasing that implies black-hole causation as source.

### String-theory placement

- define `string-theory` as a manifestation-lens under `mula-shakti`.
- it is not root replacement and not final metaphysical root claim.

---

## Track B — Firstness Rank System (deeper architecture)

### Core principle

Do not use scalar weights for precedence. Use ordinal firstness.

### Rank classes (ordinal, non-numeric)

- `aadya` (first / primary)
- `anantara` (second / inherited-next)
- `apara` (later / derived)
- `anuvritta` (echo / repeated)

### Relation rank model

Every relation type (`swarupa`, `abheda`, `janya`, `kriya`, `phala`, `yukta`, etc.) gets:

- a base firstness profile
- a question-conditioned shift profile

### Question-conditioned shift examples

- identity question -> elevate `swarupa`, `abheda`
- origin question -> elevate `janya`
- process question -> elevate `kriya`
- consequence question -> elevate `phala`
- transmission question -> enforce:
  - `samskaara-phala` => `aadya`
  - `parampara-phala` => `anantara`

### Ranking behavior

- use bucket ordering by rank class, not float sorting.
- optional depth demotion in avrti:
  - `aadya -> anantara -> apara -> anuvritta`
  - symbolic transition, not numeric decay.

---

## Manual Sangati Audit (major workstream)

### Why manual

This change is philosophical + structural. Bulk rewrite risks semantic loss.

### Scope

- audit all `brahman/sangati/*.om` one-by-one, in batches.

### Per-node checklist

For each node:

1. Confirm doctrinal role in the Track A chain.
2. Assign firstness classes:
   - primary (`aadya`)
   - secondary (`anantara`)
   - derived (`apara`)
   - echo (`anuvritta`)
3. Enforce transmission ordering where applicable:
   - `samskaara-phala` before `parampara-phala`
4. Check for black-hole-as-origin leakage in life/jiva lineage.
5. Mark whether reorder/update is required.

### Batch strategy

- pilot batch: 15-20 ontology-critical nodes first
- then domain waves: physics, philosophy, language, remaining sangati set

---

## Implementation Phases

1. Finalize relation-rank table + intent-shift matrix (spec only)
2. Implement Track A ontology core updates
3. Implement Track B phase-1 (ranking/render order)
4. Run pilot manual sangati batch
5. Expand to full sangati pass
6. Validate with canonical queries

---

## Validation Queries

- `what is life?`
- `what is brahmam?`
- transmission continuity query (`samskaara` / `parampara`)
- `what is string theory?`

Expected properties:

- surface evidence -> principle flow
- tat-kshana + nirantara both present
- samskaara-first inheritance
- string-theory correctly under `mula-shakti`
- no black-hole-origin language for life/jiva

---

## Open Design Decisions (lock before coding)

1. Firstness source:
   - relation type only, or relation + token position?
   - recommended: relation type first, token position as tie-break.
2. Base rank profiles:
   - global profile first, or domain-specific from day one?
   - recommended: global first, domain overrides later.
3. Satya integration timing:
   - include firstness in satya math now, or after ranking pilot?
   - recommended: ranking first, satya integration second.
