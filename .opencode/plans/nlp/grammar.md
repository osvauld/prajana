# Sanskrit Grammar as the Sangati Foundation

Sanskrit is the root language of the sangati layer. The graph already uses Sanskrit naming
conventions throughout. Every sloka tag (`yukta`, `sthita`, `phala`, `kriya`, `abheda`,
`swarupa`, `dhatu`, `janya`) is Sanskrit. The grammar extends this naturally.

Malayalam grammar derives from Sanskrit grammar — the terms (`kaalam`, `vachanam`,
`prayogam`) are Malayalam-ized Sanskrit. Both map to the same sangati nodes.

---

## Grammatical dimension nodes (parent categories)

These are the categories that govern inflection. Each is in `brahman/sangati/grammar/`.

```
sangati kaala       grammatical tense   (time of action)
sangati vachana     number              (singular/dual/plural)
sangati purusa      person              (1st/2nd/3rd)
sangati prayoga     voice               (kartari/karmani/bhave)
sangati linga       grammatical gender  (pullinga/striling/napumsaka)
sangati vibhakti    case                (the relation of a word to its clause)
sangati pada        word class          (subanta/tinanta/avyaya)
sangati pratyaya    suffix/affix        (morphological unit encoding grammar)
sangati samasa      compound formation  (how words join)
sangati pratishedha negation            (grammatical negation — ≠ pratipaksha which is semantic)
sangati vakya       sentence            (unit of meaning containing a verb)
```

---

## Tense (kaala) — amshas of kaala

`kaala.om` IS the tense parent — no separate `kala.om`. Values use `-kaala` suffix.
Each is a `kaala-amsha`. Together they constitute the full tense system.

```
sangati vartamana-kaala    kaala-amsha    present
                                          Extraction: current state or ongoing constraint
                                          English: "drops", "reaches", "vibrates"

sangati bhuta-kaala        kaala-amsha    past
                                          Extraction: initial condition, historical fact
                                          English: "dropped", "reached", "was travelling"

sangati bhavishya-kaala    kaala-amsha    future
                                          Extraction: goal / target state
                                          English: "will reach", "will drop"

sangati vidhi-kaala        kaala-amsha    imperative
                                          Extraction: command / goal (highest priority)
                                          English: "reach [0.4, 0.3]", "drop the load"

sangati sambhavana-kaala   kaala-amsha    potential/modal
                                          Extraction: constraint / capability
                                          English: "must", "should", "can", "cannot"
```

Extraction roles:
- `vidhi-kaala` and `bhavishya-kaala` → goals/targets
- `bhuta-kaala` → initial conditions
- `vartamana-kaala` → current state or constraint
- `sambhavana-kaala` → hard/soft constraint depending on modal strength

---

## Voice (prayoga) — amshas of prayoga

```
sangati kartari-prayoga    prayoga-amsha    active voice   — agent acts
sangati karmani-prayoga    prayoga-amsha    passive voice  — patient receives
sangati bhave-prayoga      prayoga-amsha    impersonal     — pure process
```

`bhave-prayoga` is the most important amsha. Every kosha process node declares
`bhave-prayoga-swarupa` — meaning this process IS the impersonal voice (identity, not membership).

---

## Number (vachana) — amshas of vachana

```
sangati eka-vachana     vachana-amsha    singular    — connects to sangati eka
sangati dvi-vachana     vachana-amsha    dual        — connects to sangati dvaya
sangati bahu-vachana    vachana-amsha    plural      — connects to sangati aneka
```

Note: English has no dual. `dvi-vachana` applies to Sanskrit/Malayalam but not English.
Bhasha/english/ nodes only use `eka-vachana` and `bahu-vachana`.

---

## Person (purusa) — amshas of purusa

Sanskrit counts person from the one spoken about (prathama = 3rd in English):

```
sangati prathama-purusa    purusa-amsha    3rd person   — "the ball drops", "it reaches"
sangati madhyama-purusa    purusa-amsha    2nd person   — "you drop", "you reach"
sangati uttama-purusa      purusa-amsha    1st person   — "I drop", "we reach"
```

---

## Case (vibhakti) — amshas of vibhakti

The eight Sanskrit cases are universal. For NLP extraction, six matter directly.

```
sangati prathama-vibhakti    vibhakti-amsha    nominative   — the subject
sangati dvitiya-vibhakti     vibhakti-amsha    accusative   — the direct object
sangati trtiya-vibhakti      vibhakti-amsha    instrumental — by/with: means or agent
sangati chaturthi-vibhakti   vibhakti-amsha    dative       — for/to: recipient or purpose
sangati panchami-vibhakti    vibhakti-amsha    ablative     — from: source or cause
sangati shashthi-vibhakti    vibhakti-amsha    genitive     — of: possession or domain
sangati saptami-vibhakti     vibhakti-amsha    locative     — in/at/on: location or condition
sangati sambodhana           vibhakti-amsha    vocative     — O!: direct address
```

Physics quantities always appear in a specific vibhakti relation:
- "velocity **of** the ball" → shashthi (genitive)
- "force **on** the surface" → saptami (locative)
- "drop it **from** 5m" → panchami (ablative)
- "it travels **to** position X" → chaturthi/dvitiya

Query words are `prashna + vibhakti`:
- `how-far` = prashna + dvitiya-vibhakti
- `how-fast` = prashna + trtiya-vibhakti
- `how-much` = prashna + prathama-vibhakti

---

## Word class (pada) — amshas of pada

```
sangati subanta     pada-amsha    nominal forms      — nouns, pronouns, adjectives (declined)
sangati tinanta     pada-amsha    verbal forms       — conjugated verbs (inflected)
sangati avyaya      pada-amsha    indeclinables      — particles, adverbs (no inflection)
sangati nipata      pada-amsha    pure particles     — untranslatable connectives: "and", "or"
sangati upasarga    pada-amsha    verbal prefixes    — pre-, un-, re-, dis-
```

---

## Verbal derivative types (krit pratyaya) — amshas of pratyaya

```
sangati shatr-pratyaya    pratyaya-amsha    present active participle  → "-ing": reaching
sangati kta-pratyaya      pratyaya-amsha    past passive participle    → "-ed": reached
sangati tvaa-pratyaya     pratyaya-amsha    gerund (having done)       → "having reached"
sangati tumun-pratyaya    pratyaya-amsha    infinitive                 → "to reach"
```

---

## Compound types (samasa) — amshas of samasa

```
sangati tatpurusha     samasa-amsha    determinative  — "free-fall" (fall that is free)
sangati karmadharaya   samasa-amsha    descriptive    — "kinetic-energy" (energy that is kinetic)
sangati dvandva        samasa-amsha    copulative     — connects to sangati dvandva-shakti
sangati bahuvrihi      samasa-amsha    possessive     — "zero-friction" (having zero friction)
```

---

## Grammar value nodes use amsha, not janaka

**Before:**
```
sangati vartamana-kaala
  "kaala-yukta"
```

**After:**
```
sangati vartamana-kaala
  "kaala-amsha"
  "vartamana-yukta"   -- present-time specific
```

Parent dimension nodes (kaala, vibhakti, etc.) do NOT list children via `-janaka`.
Direction is always: member → parent (upward via amsha edge).

---

## New visheshanam-ring dims added (Phase 1)

Seven new dims added to `brahman/kosha/yantra/visheshanam/visheshanam-ring.om`:

**Morphological / argument** (3):
```
ahara-yukta    intake/input
dhatu-yukta    morphological root
vrnda-yukta    paradigm family
```

**Grammatical** (4):
```
kala-yukta     tense
prayoga-yukta  voice
vachana-yukta  number
purusa-yukta   person
```
