# Shabda Inheritance + Extraction Pipeline

## Shabda inheritance (Phase 0 — done)

`read_shabda` walks IS-A edges (dhatu, vishesa, amsha, swarupa) and merges parent shabda.
Own pairs win on key conflict. `shabda-tmpl` is never inherited.

```
bhasha reaches  →  dhatu  →  kosha reach-target  →  (signal:ik=1.0 pos:verb)
```

`read_shabda "reaches" "signal"` returns `"ik=1.0"` without `reaches.om` declaring it.
`read_shabda "reaches" "pos"` returns `"verb"` without `reaches.om` declaring it.

---

## What stays in shabda

| Key | On | Purpose |
|-----|----|---------|
| `pos:verb\|noun\|adj\|modal` | kosha process/quantity nodes | O(1) POS lookup; inherited by bhasha via dhatu |
| `signal:ik=1.0,...` | kosha process nodes | PPR cache; inherited by bhasha via dhatu |
| description after `/` | all nodes | Human-readable documentation |
| Parser op metadata | yantra op nodes | Operational |
| Domain defaults | scene-defaults nodes | Configuration |
| `shabda-tmpl:path` | setu bridge nodes | Large lookup tables |

## What is eliminated

- `governs:` key — `ik-ahara` edge IS the governs relationship
- `domain-language-sthita` in sloka — bhasha layer declares it
- `pos:verb` on bhasha nodes — inherited from kosha via dhatu
- `signal:...` on bhasha nodes — inherited from kosha via dhatu

---

## Signal weight computation (Phase 6)

At startup, after `compute_visheshanam_entropy_weights`, run over all kosha process nodes:

- Compute context-score against four seed sets:
  - IK: `[ik, target-position, aayaama, bindu]`
  - Motion: `[gati, kaala, velocity]`
  - Structure: `[link, joint, kinematic-chain]`
  - Constraint: `[seema, niyama]`
- Write `signal:ik=X,motion=Y,structure=Z,constraint=W` to each process node's shabda
- Bhasha forms inherit via dhatu — computed once, available everywhere

---

## Lookup priority chain

```
1. bhasha node exists with this name → always wins (direct name lookup, O(1))
2. kosha node exists with this name → use it
3. classify_token: token-roles → grammar → direct node → shabda scan → partial match
4. flat .shabda tables (unit-aliases, joint-type-words, etc.) — fallback
```

When a bhasha node is added, it supersedes any flat-table entry automatically.
No manual conflict resolution per token.

### Critical conflicts resolved by bhasha nodes

| Conflict | Resolution |
|----------|-----------|
| `find/solve/calculate` in token-roles + compute.om | `bhasha find`, `bhasha solve` etc. → remove from token-roles kriya-yantra |
| `to` as yukta (grammar) vs phala (prepositions) | `bhasha to-preposition` → dhatu → `kosha toward` wins |
| `it/its/that` as article vs pronoun-reference | `bhasha it`, `bhasha that` with reference dhatu win |
| `when/where/with` in grammar vs binding | binding wins (more specific); grammar.om removes entries |

---

## Question-relative extraction pipeline (Phase 4)

### The key principle

Relevance = context-score(resolved, seeds-from-question). Same word scores differently
depending on what the sentence is asking.

### Pre-pass: goal seed computation

Before classify-fold, scan raw words for goal type → build seed list:

```
goal "reach target"      → [[ik,1.0],[target-position,1.0],[aayaama,0.8],[bindu,0.8]]
goal "find joint angles" → [[joint-angle,1.0],[ik,1.0],[joint,0.8]]
goal "minimize power"    → [[rated-power,1.0],[torque,0.8],[joint,0.5]]
no goal detected         → [[aayaama,0.5],[bindu,0.5]]
```

New tantra: `compute-extraction-seeds` — takes raw-words + scene-type, returns seed list.

---

## Open questions

1. **`dvi-vachana` in English** — English has no dual. Bhasha/english/ nodes only use
   `eka-vachana` and `bahu-vachana`. Correct — sangati categories are universal, bhasha
   nodes only use the categories applicable to their language.

2. **Polysemy and prayoga** — "position" as noun (subanta) vs "position" as verb (tinanta/kartari).
   Two bhasha nodes: `bhasha position-noun` and `bhasha position-verb`. PPR picks by context.

3. **Modal scope across conjunctions** — "must reach [0.4, 0.3] and can rotate by 45°".
   `must` scopes over `reach`, `can` scopes over `rotate`. Tracking scope not yet designed.

4. **`respectively` extraction** — `krama-kriya` signals ordered 1:1 assignment but the
   extraction tantra needs a second-pass grouping step. Architecture not yet designed.

5. **Bhave-prayoga for tantra nodes** — should tantra nodes explicitly declare
   `bhave-prayoga-swarupa`? Probably yes — lets PPR distinguish "this node IS a process".

6. **vibhakti on query words** — `how-far` as `prashna + dvitiya-vibhakti` — does the
   extraction pipeline read the vibhakti annotation to constrain what type of quantity
   it searches for? This could eliminate false positives. Needs design.
