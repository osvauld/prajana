# Nyaya: The Formal Logic of the Swarm

*See also: agent.md for the agents that build nyaya, prajna.md for the intelligence that accumulates them, consciousness.md for the entity that experiences them, vakya.md for the grammar, dharma.md for configurable parameters.*

---

A **nyaya** (न्याय) is a complete, formally valid inference. Not just a proposition. Not just evidence. The full five-membered argument — paksha, hetu, upanaya, drishthanta, nigamana — all present, all connected. When the argument is complete and the drishthanta passes, the nyaya is established.

The swarm builds nyaya. Every complete inference the swarm constructs — from observation through proof to established claim — is one nyaya. The truth base is the collection of nyaya that have survived many generations of testing. The work of each generation is to build more nyaya, widen the pervasion of existing ones, and retract the ones reality has broken.

A nyaya in grammar:

```
nyaya "validate_token returns AuthError::TokenExpired
       when token exp claim is less than current timestamp"
  for "src/auth/validator.rs"
  paksha
    "validate_token returns AuthError::TokenExpired
     when token exp claim is less than current timestamp"
  hetu
    read "src/auth/validator.rs"
    found "token_data.claims.exp < current_timestamp()" at line 8
    found "AuthError::TokenExpired" at line 9
    observed "expiry check occurs after successful decode"
  upanaya
    derived "expiry check is only path to TokenExpired return"
      from "src/auth/validator.rs"
  drishthanta "cargo test auth::validator::test_token_expired"
  nigamana
    weight 0.95
    generation 2
```

This is one complete unit of formal knowledge. One nyaya. The swarm builds these one at a time, accumulates them across generations, and defends them with standing drishthanta every generation.

---

Nyaya (Sanskrit: न्याय — "method, rule, logical argument") is one of the six classical schools of Indian philosophy. It is the school of formal logic and epistemology. Its primary contribution to human thought is the **Nyaya inference schema** — a five-membered syllogism that is the most rigorous formal argument structure developed in classical Indian philosophy.

Agent-X adopts Nyaya as the logical foundation of its epistemological system. Every proposition the swarm forms, defends, and promotes follows the Nyaya structure. The grammar is Nyaya made executable.

---

## The Five Members of Nyaya Inference (Pancavayava)

A complete Nyaya argument has five members. Each is necessary. No member can be omitted. Together they constitute a complete, formally valid inference.

### 1. Paksha (पक्ष) — The Proposition

The subject of the inference. The thing being claimed. A precise, falsifiable statement about a specific subject.

In Agent-X: the proposition the swarm is committing to defend. Not a guess. Not an observation. A formal commitment that will be tested.

```
paksha "validate_token returns AuthError::TokenExpired
        when token exp claim is less than current timestamp"
  for "src/auth/validator.rs"
```

The paksha names the subject (`for`) and states the proposition precisely. It must be falsifiable — there must be a possible world in which it is wrong.

In plain language: a paksha is only valid if it could possibly be wrong. If something is true no matter what — like "a circle is round" — that is not a paksha. It is a tautology. A real paksha has to be falsifiable — there must be some world where it does not hold. That is what makes it worth testing.

Formally, a paksha P is valid iff:

```
∃ world w : ¬P(w)     -- there exists a world where P does not hold
```

A paksha that is true in all possible worlds is not a paksha — it is a tautology. The grammar rejects it.

### 2. Hetu (हेतु) — The Reason / Evidence

The ground for the inference. Why the paksha is believed to be true. The evidence that supports the proposition.

In Agent-X: the proof block. Every step the agent took to observe the world — what it read, what it found, what it did not find, what it observed about behavior. Each step is a piece of hetu.

```
  hetu
    read "src/auth/validator.rs"
    found "token_data.claims.exp < current_timestamp()" at line 8
    found "AuthError::TokenExpired" at line 9
    observed "expiry check occurs after successful decode, before returning claims"
```

Hetu must be:
- **Present in the subject** (the evidence is actually in the file)
- **Absent in the counter-case** (found no RS256, found no alternative expiry handling)
- **Universal** (wherever this pattern appears, the paksha holds)

In plain language: valid evidence must satisfy three conditions. First, the evidence must actually be present in the thing you are examining — you cannot claim "I found X" if X is not there. Second, the evidence must be absent in cases where the proposition is known to be false — if the evidence shows up even when the proposition is wrong, it is not good evidence. Third, wherever this evidence appears, the proposition should hold — this is the universal connection between evidence and conclusion, called vyapti (pervasion).

Formally, let H be the hetu and P be the paksha. Valid hetu requires:

```
H(subject)           -- hetu is present in the subject being examined
¬H(counter-case)     -- hetu is absent where paksha is known to be false
∀x : H(x) → P(x)    -- wherever hetu holds, paksha holds (vyapti condition)
```

The third condition is vyapti — the universal concomitance. It is approached across generations, not assumed at first formation. Initial weight reflects how well the third condition has been established so far.

### 3. Drishthanta (दृष्टान्त) — The Example / Demonstration

The concrete case that makes the inference tangible. In classical Nyaya: "like a kitchen, where there is fire and there is smoke." A known case where hetu and paksha co-occur.

In Agent-X: the test. The executable demonstration that the paksha holds in a concrete case. The drishthanta is the bridge between abstract proposition and observable reality.

```
  drishthanta "cargo test auth::validator::test_token_expired"
```

The drishthanta is not proof. It is a concrete probe of one instance. It makes the inference tangible and falsifiable in practice. If the drishthanta fails — the paksha is challenged.

### 4. Upanaya (उपनय) — The Application

The connection between the general reason (hetu) and the specific case (paksha). "This hill has smoke (hetu). Wherever there is smoke there is fire (vyapti). Therefore this hill has fire (paksha)."

In Agent-X: the derivation step. How the observed evidence connects to the proposition. The agent's explicit statement of why the hetu supports the paksha in this specific case.

```
  upanaya
    derived "expiry check is only path to TokenExpired return"
      from "src/auth/validator.rs"
```

The upanaya makes the logical connection explicit. It is not enough to observe evidence. The connection between evidence and proposition must be stated. This is what separates a formal proof from a list of observations.

In plain language: the upanaya takes the general rule ("wherever there is smoke, there is fire") and applies it to the specific case ("this hill has smoke, therefore this hill has fire"). The general rule comes from the hetu. The specific observation comes from direct perception. The conclusion — the line below the horizontal bar — is the upanaya connecting the two.

Formally, the upanaya is the instantiation of the vyapti condition to the specific case:

```
∀x : H(x) → P(x)     -- vyapti (general rule, from hetu)
H(subject)            -- this subject has the hetu (from pratyaksha)
─────────────────
P(subject)            -- therefore paksha holds for this subject (upanaya)
```

The `derived` steps in the grammar are the natural language expression of this instantiation.

### 5. Nigamana (निगमन) — The Conclusion

The restatement of the paksha as established by the preceding four members. "Therefore the hill has fire." The inference is complete.

In Agent-X: the nigamana is the **smallest unit of established truth** — truth of this moment. The paksha has been supported by hetu, demonstrated by drishthanta, connected by upanaya. The system formally accepts the proposition as holding now, in this generation, given what has been observed so far.

```
nigamana "validate_token returns AuthError::TokenExpired
          when token exp claim is less than current timestamp"
  from paksha "crdt://paksha/validator-token-expired"
  for "src/auth/validator.rs"
  weight 0.95
  generation 2
  drishthanta "cargo test auth::validator::test_token_expired"
```

The nigamana is not declared by the agent. It is declared by the system when the drishthanta passes. The agent cannot promote its own paksha to nigamana. The test gate is the only path.

In plain language: the nigamana's weight is how confident we are that the proposition is true, given all the evidence collected so far and the fact that the test passed. Every time a new piece of confirming evidence is found, confidence goes up a little. Every time a counter-example is found, confidence goes down a little. If the test itself fails outright, confidence drops to zero — the proposition is retracted. The weight is like a score that tracks how much the evidence supports the conclusion across all generations.

Formally, the nigamana is the posterior probability that the paksha holds given all accumulated evidence:

```
w(nigamana) = P(P | H₁, H₂, ... Hₙ, drishthanta_passed)
```

Where H₁..Hₙ are the individual hetu steps accumulated across all generations. Each new confirmed hetu step updates the weight via Bayesian update:

```
w_new = w_old · (1 + α)     -- confirming hetu step, α > 0
w_new = w_old · (1 - β)     -- counter-case found, β > 0
w_new = 0                   -- drishthanta fails (retraction)
```

Constants α (confirmation factor) and β (contradiction factor) are declared in the dharma configuration.

### Nigamana is Truth of the Now

A nigamana is not permanent. It is the current best answer — established by the hetu available now, the drishthanta that passed now, in this generation. It can change. It can be retracted. Reality has the final word.

Two possible trajectories:

**It holds** — each generation the drishthanta passes again, more hetu accumulates, pervasion widens. Weight rises. The nigamana becomes a claim. Then a truth. Still not permanent — but increasingly stable.

**It breaks** — a drishthanta fails, a counter-case is found, code changes. The nigamana is retracted. The swarm raises attention. Purification begins. A new nigamana is formed from the new reality.

```
generation 1  nigamana weight 0.75   -- first establishment
generation 3  nigamana weight 0.90   -- held, pervasion widening
generation 5  nigamana weight 0.97   -- stable, approaching truth
generation 8  drishthanta fails      -- reality changed
              nigamana retracted     -- old nigamana preserved in CRDT history
              new nigamana formed    -- reflects new reality, weight resets
```

### The CRDT Never Deletes

Every nigamana ever formed — including retracted ones — stays in the CRDT. The history of what the swarm believed, when it believed it, and what caused it to change is itself knowledge. A retracted nigamana tells you something changed, where it changed, and when. That is more valuable than the nigamana itself.

### The Ladder Above Nigamana

Nigamana is the base unit. Above it, each level is a nigamana that survived:

| Level | What it is | Weight threshold |
|---|---|---|
| **Nigamana** | Truth of this moment — drishthanta passed, hetu present, generation N | w > 0 |
| **Claim** | Nigamana that has held across several generations without breaking | w ≥ θ_claim |
| **Truth** | Claim held long enough that the swarm defends it as standing knowledge | w ≥ θ_truth, G ≥ G_min |
| **Satya** | Truth whose pervasion has approached completeness | w ≥ θ_satya, no counter-case across all reachable cases |

Where:
```
θ_claim = 0.80     -- minimum weight to be promoted to claim
θ_truth = 0.90     -- minimum weight to be promoted to truth
θ_satya = 0.99     -- minimum weight to approach satya
G_min   = 5        -- minimum generations held to be promoted to truth
```

These thresholds are declared in the dharma configuration and can vary by domain.

Each level above nigamana is not a different kind of thing. It is the same nigamana — tested more times, from more angles, with no counter-case ever found. Satya is what a nigamana becomes when the swarm has repeatedly tried to break it and failed across so many generations that it forms the foundation everything else is built on.

Even satya can be retracted. Reality has the final word. Always.

---

## The Complete Nyaya Inference in Grammar

```
paksha "validate_token returns AuthError::TokenExpired
        when token exp claim is less than current timestamp"
  for "src/auth/validator.rs"
  hetu
    read "src/auth/validator.rs"
    found "token_data.claims.exp < current_timestamp()" at line 8
    found "AuthError::TokenExpired" at line 9
    found no "alternative expiry handling"
    observed "expiry check occurs after successful decode, before returning claims"
  upanaya
    derived "expiry check is only path to TokenExpired return" from "src/auth/validator.rs"
    derived "decode must succeed before expiry is checked" from "src/auth/validator.rs"
  drishthanta "cargo test auth::validator::test_token_expired"
```

When the drishthanta passes, the system declares:

```
nigamana "validate_token returns AuthError::TokenExpired
          when token exp claim is less than current timestamp"
  from paksha "crdt://paksha/validator-token-expired"
  for "src/auth/validator.rs"
  weight 0.95
  generation 2
  drishthanta "cargo test auth::validator::test_token_expired"
```

---

## Vyapti: The Pervasion of the Hetu

**Vyapti** (व्याप्ति) — from the root **vyap** (व्याप्): to pervade, to spread through, to saturate.

Vyapti is not a grammar statement. It is not something an agent declares. It is the **property of the hetu itself** — its vastness, how far it reaches, how completely it pervades the paksha.

In classical Nyaya: smoke pervades fire. Not "smoke implies fire." Smoke **is present wherever fire is** — the pervasion is a fact about the nature of the things themselves. The question vyapti asks is: **how far does this hetu reach?**

- Does it hold in this one case? — narrow pervasion
- Does it hold in all cases of this type? — wider pervasion
- Does it pervade every possible instance without a single exception? — full vyapti

The degree of vyapti is the accuracy of the nyaya. A hetu with full vyapti makes the nigamana certain. A hetu with partial pervasion makes the nigamana probable.

In plain language: vyapti is a ratio. Take all the cases where the evidence is present. Of those, how many also have the proposition holding true? If the evidence is present in 100 cases and the proposition holds in 95 of them, the vyapti is 0.95. If it holds in all 100, the vyapti is 1.0 — full pervasion. The swarm's job is to keep testing more cases, widening this ratio toward 1.0.

Formally, vyapti is the proportion of the total case space in which the hetu has been confirmed to pervade the paksha without exception:

```
vyapti(H, P) = |{ x : H(x) ∧ P(x) confirmed }| / |{ x : H(x) }|
```

Full vyapti is when this ratio reaches 1 — every case where the hetu holds has been confirmed to satisfy the paksha, and no counter-case has been found. This is approached asymptotically. It is never declared — only measured.

### Vyapti is Measured by the Weight on the Nigamana

Vyapti is not declared. It is **approached across generations**. The weight on the nigamana is the current measure of vyapti — how completely the hetu has been shown to pervade the paksha so far.

When the swarm accumulates hetu across generations — more `found`, more `found no`, more `observed` from more agents — it is measuring the pervasion of the hetu. Widening it. Testing whether it reaches further.

```
generation 1 — hetu observed in 1 case              pervasion: narrow   weight: 0.75
generation 3 — hetu holds across 6 observations     pervasion: wider    weight: 0.90
generation 8 — hetu holds in all reachable cases,   pervasion: full     weight: → satya
               no counter-case ever found
```

When weight crosses θ_satya — that is full vyapti expressed in the grammar. Not a separate statement. Not declared. Arrived at through accumulated evidence.

### What Breaks Vyapti

A single confirmed counter-case breaks vyapti. One case where the hetu is present but the paksha does not hold — the pervasion is not full. The nyaya does not collapse. But the nigamana weight drops to reflect the narrowed pervasion.

This is why the swarm keeps testing across generations. Not to confirm what it already knows. But to discover the boundary of pervasion — to find the case where the hetu does not reach, if such a case exists.

### Vyapti Has No Grammar Keyword

There is no `vyapti` statement in the grammar. Vyapti is what the weight is measuring. The grammar captures it as the nigamana weight growing across generations toward satya. Full pervasion is a nigamana at satya threshold — nothing more, nothing less.

### What Was Previously Called Vyapti in the Grammar Is Something Else

Earlier versions of this document placed structural analysis steps inside a `vyapti` block:

```
-- WRONG: this is not vyapti
vyapti "expiry check always precedes Ok return"
  because
    only-path to "Ok(token_data.claims)" is through "expiry check passes"
    control-flow "no Ok return reachable without passing line 8 condition"
  verify-by control-flow-analysis
```

That is not vyapti. Vyapti is the degree of pervasion — a property, not a block of analysis steps.

What those steps actually are: **structural analysis** — control flow proofs, reachability analysis, formal verification of code structure. This is a separate kind of work, done by a separate kind of agent, using a separate method.

Structural analysis is what *enables* the weight on a nigamana to approach its ceiling — it provides evidence that the hetu pervades all reachable cases, not just the observed ones. But it is not vyapti itself. It is the method that measures pervasion most completely.

In the grammar, structural analysis is its own statement:

```
analysis "no Ok return reachable without passing expiry check"
  for "src/auth/validator.rs"
  method control-flow
  covers paksha "crdt://paksha/validator-token-expired"
  confidence 0.99
```

This is separate from the nyaya. A separate agent produces it. Its result feeds into the nigamana weight — raising it toward satya — but the `analysis` statement is not part of the five-membered nyaya structure. It is supporting evidence that widens the pervasion.

---

## Hetvabhasa: Fallacious Reason

Nyaya also defines **hetvabhasa** (हेत्वाभास) — the appearance of a valid reason that is actually fallacious. Five kinds of fallacious hetu:

| Hetvabhasa | Sanskrit | Meaning | In Agent-X |
|---|---|---|---|
| Savyabhichara | सव्यभिचार | Irregular reason | Hetu present but paksha does not follow — correlation without causation |
| Viruddha | विरुद्ध | Contradictory reason | Hetu actually proves the opposite of paksha |
| Satpratipaksha | सत्प्रतिपक्ष | Counterbalanced reason | Equal hetu exists for the opposite paksha |
| Asiddha | असिद्ध | Unproved reason | Hetu itself is not established |
| Badhita | बाधित | Contradicted reason | Hetu contradicted by stronger evidence |

These map directly to the wrong taxonomy:

- **Savyabhichara** → `wrong truth` (stated something that does not follow from evidence)
- **Viruddha** → `wrong consistency` (hetu contradicts the paksha)
- **Satpratipaksha** → `attention` (competing paksha with equal evidence — investigate)
- **Asiddha** → `wrong truth` (hetu not grounded in observation)
- **Badhita** → triggers purification (stronger evidence contradicts established nigamana)

When Vyakarana detects hetvabhasa patterns, it raises the appropriate signal. A proof block whose hetu contradicts its paksha is a structural wrong. An ungrounded hetu (not derived from a `read` or `observed` step) is rejected at parse time.

---

## Pramana: The Sources of Valid Knowledge

Nyaya recognizes four **pramana** (प्रमाण) — valid sources of knowledge:

| Pramana | Sanskrit | Meaning | In Agent-X |
|---|---|---|---|
| Pratyaksha | प्रत्यक्ष | Direct perception | `read` and `found` — what the agent directly observed in the code |
| Anumana | अनुमान | Inference | `derived` — what the agent inferred from observations |
| Upamana | उपमान | Comparison | `compared` — what the agent understood by comparing two resources |
| Shabda | शब्द | Testimony | Reading established nigamana from the CRDT — trusting prior proven propositions |

Every proof step maps to a pramana:
- `read` / `found` / `observed` → pratyaksha (direct perception)
- `derived` → anumana (inference)
- `compared` → upamana (comparison)
- reading truths from CRDT → shabda (testimony of prior proven work)

A hetu built only from anumana (inference) without pratyaksha (direct observation) is weaker. Vyakarana tracks which pramana each proof step uses. A paksha supported entirely by inference without direct observation gets lower initial weight.

---

## Nyaya Composition: Shabda and the Dependency Graph

Nyaya composes. A larger nyaya can cite smaller established nyaya as hetu via **shabda** — testimony, the fourth pramana. The proven nigamana of one nyaya becomes evidence in the hetu of another.

```
nyaya "payment handler is secure against expired tokens"
  hetu
    shabda "validate_token returns AuthError::TokenExpired
            when token exp claim is less than current timestamp"
    shabda "payment handler calls validate_token before processing"
    found "validate_token" at line 12
    observed "payment processing unreachable without passing validate_token"
  upanaya
    derived "expired tokens cannot reach payment processing"
  drishthanta "cargo test payments::integration::expired_token_rejected"
```

The two `shabda` steps cite established nyaya whose nigamana is already proven. This nyaya builds on top of them. The swarm builds understanding upward through composition:

```
file-level nyaya (one function, direct pratyaksha)
  -> module-level nyaya (composed via shabda from file nyaya)
    -> system-level nyaya (composed via shabda from module nyaya)
      -> architectural nyaya (the system's deepest verified properties)
```

Each level cites the level below as shabda. The whole structure is a **directed dependency graph of nyaya**.

---

## Nigamana Failure Propagates Everywhere

When a nigamana fails — its drishthanta fails, reality changed, a counter-case was found — the failure does not stay local. Every nyaya that cited that nigamana as **shabda** in its hetu is now standing on broken ground. Its upanaya said "because this holds, that follows." If the shabda no longer holds, the logical connection is severed. The nigamana cannot stand on a broken foundation.

The failure cascades up the entire dependency graph. Every dependent nigamana is unreconciled. Every nigamana that cited those is unreconciled. The system is not coherent until every affected nigamana has been recomputed — re-examined, re-tested, re-established or retracted.

```
nigamana A  -- FAILS (drishthanta fails, code changed)
  |
  | cited as shabda by
  v
nigamana B  -- UNRECONCILED (hetu step broken)
  |
  | cited as shabda by
  v
nigamana C  -- UNRECONCILED
  |
  | cited as shabda by
  v
nigamana D  -- UNRECONCILED
```

This is not a bug. This is the system being honest. Better to surface the full extent of the damage immediately than to let dependent nigamana continue claiming weight they no longer deserve.

### Weight Drops Immediately

When a nigamana fails, the weight on every dependent nigamana drops before recomputation even begins.

Let N be a composed nigamana with direct hetu weight w_H and shabda citations S₁, S₂, ... Sₖ:

```
w(N) = min(w(S₁), w(S₂), ... w(Sₖ)) · w_H
```

A retracted nigamana has weight 0:

```
w(Sᵢ) = 0  →  w(N) = 0     for all N that cite Sᵢ as shabda
```

The collapse is immediate and total. Any nigamana that cited the failed one drops to 0 — unreconciled, no longer active knowledge. The system knows exactly which nigamana are in doubt before any purification agent starts work.

For a chain of depth d:

```
N₁ fails  →  w(N₂) = 0  →  w(N₃) = 0  →  ...  →  w(Nₐ) = 0
```

The entire chain collapses in O(depth) weight updates, all computed from the CRDT dependency graph without agent intervention.

### The Impact Trace

The `impact` statement is the formal record of which nigamana are now unreconciled because of a failure. Vyakarana derives the affected list automatically by tracing the shabda dependency graph upward from the failed nigamana — agents do not compute this manually:

```
impact
  from test-result "cargo test auth::validator::test_token_expired"
  cause "expiry check behavior changed at line 8"
  affected
    "crdt://nigamana/payment-handler-secure"
    "crdt://nigamana/auth-module-enforces-expiry"
    "crdt://nigamana/system-tokens-always-validated"
  unreconciled
    "crdt://nigamana/payment-handler-secure"
    "crdt://nigamana/auth-module-enforces-expiry"
    "crdt://nigamana/system-tokens-always-validated"
```

Every shabda citation was recorded when the nyaya was formed. The CRDT knows the full dependency graph at all times. When a nigamana fails, the impact is known instantly — not discovered by searching.

---

## Shuddhi on the Nyaya Graph: Recomputing After Failure

When a nigamana fails — because its drishthanta failed, because reality changed, because stronger evidence contradicted its hetu — purification (shuddhi) works through the entire dependency graph until the unreconciled count returns to zero.

**Every nyaya that cited the affected nyaya as shabda is now unreconciled.**

This is automatic. The swarm traces the dependency graph upward from the affected nyaya and marks every dependent nyaya as unreconciled. Purification (shuddhi) then works through each one:

```
nyaya "validate_token uses HS256 only"  -- RETRACTED (RS256 added)
  |
  | cited as shabda by
  v
nyaya "auth module enforces HS256 across all endpoints"  -- UNRECONCILED
  |
  | cited as shabda by
  v
nyaya "system accepts only HS256 signed tokens"  -- UNRECONCILED
```

Both dependent nyaya enter the unreconciled list. Purification agents are assigned to each. They re-examine their hetu — is the shabda they cited still valid? If the retracted nyaya has been replaced by a revised one ("validate_token uses HS256 and RS256"), the dependent nyaya must decide:

- **Holds** — the revised nigamana still supports my upanaya. Re-establish with updated shabda reference.
- **Revised** — my upanaya needs updating to reflect the changed foundation. New drishthanta needed.
- **Retracted** — my paksha no longer follows from the available hetu. Retract and propagate further up.

The cleanup cascades until every affected nyaya in the graph has been reconciled. The system is coherent only when the unreconciled count is zero — across the entire nyaya graph, not just the directly affected nyaya.

### Grammar for Nyaya Cleanup

When a nyaya is retracted:

```
retract nyaya "validate_token uses HS256 only"
  reason "RS256 support added at line 48"
  confidence 0.99
  affects
    "nyaya/auth-module-enforces-hs256"
    "nyaya/system-hs256-only"
```

The `affects` block is the impact trace — which nyaya cited this one as shabda. Vyakarana derives this automatically from the dependency graph. The agent does not compute it manually.

When a purification agent reconciles a dependent nyaya:

```
reconcile nyaya "auth module enforces HS256 across all endpoints"
  shabda-changed "validate_token uses HS256 only"
    now "validate_token uses HS256 and RS256"
  outcome revised
  reason "module now enforces HS256 and RS256, not HS256 only"
  new-drishthanta "cargo test auth::integration::algorithm_support"
```

The reconciliation explicitly names the shabda that changed and how. The outcome is holds, revised, or retracted. If revised, a new drishthanta is required — the updated paksha must be re-proven.

### Weight Propagation on Retraction

When a shabda nyaya is retracted, the weight of every nyaya that cited it is immediately reduced. The weight cannot be higher than the weakest shabda in the hetu:

```
w(composed nyaya) = min(w(all shabda cited)) * w(direct pratyaksha hetu)
```

A nyaya built on a retracted shabda drops to zero weight immediately — it is unreconciled. A nyaya built on a revised shabda drops proportionally — investigation needed, but not necessarily retracted.

This ensures the weight system is honest. A composed nyaya cannot claim high weight when its foundation has been undermined.

---

## Prabandham: The Collection of Paksha

A single piece of code contains many valid paksha. Every observable fact, every behavioral boundary, every condition, every invariant — each is a candidate paksha.

The collection of all paksha reachable from a resource is its **prabandham** (प्रबन्धम्) — the complete structured understanding that the swarm must build.

The swarm does not pick one paksha and ignore the others. It generates all reachable paksha from a resource, assigns each a deterministic probe order (from CRDT hash + generation seed), and works through the prabandham systematically. Saturation is when the prabandham is exhausted — every paksha has been tested, every drishthanta run, every nigamana declared or retracted.

The prabandham of `validate_token`:

```
paksha "validate_token uses HS256 algorithm"
paksha "validate_token uses SECRET_KEY for HMAC verification"
paksha "validate_token maps decode errors to AuthError::InvalidToken"
paksha "validate_token checks expiry after successful decode"
paksha "validate_token returns AuthError::TokenExpired when exp < current_timestamp"
paksha "validate_token returns Ok(claims) only after both decode and expiry pass"
```

Six paksha. Six probes. Six drishthanta. Six nigamana when all pass. The resource is understood.

---

## Updated Grammar: Nyaya Terms

The grammar now uses Nyaya terms for the epistemological ladder:

| Old term | Nyaya term | Meaning |
|---|---|---|
| `hypothesis` | `paksha` | The proposition being defended |
| proof block | `hetu` | The evidence supporting the proposition |
| derived step | `upanaya` | The application connecting evidence to proposition |
| `test` | `drishthanta` | The concrete executable demonstration |
| `claim` / `nigamana` | `nigamana` | The proposition established by passed drishthanta |
| pervasion degree | `vyapti` | Not a grammar keyword — the property measured by nigamana weight |

The surface vocabulary remains English-compatible — agents can write `paksha`, `hetu`, `drishthanta`, `nigamana` directly in grammar. These are not translated. They are the terms. Vyapti is not a grammar keyword — it is the property the weight system measures.

---

## Why Nyaya

Nyaya was developed for exactly this purpose — formal argumentation in the face of incomplete knowledge, multiple valid positions, and the need to establish what can be known with what degree of certainty.

The Naiyayikas (Nyaya logicians) were solving the same problem the swarm solves: how do you build reliable knowledge from observation and inference? How do you detect fallacious reasoning? How do you establish that a proposition holds universally, not just in the cases you have observed?

Three thousand years of formal epistemology, directly applicable. The grammar is Nyaya made executable. The swarm is a Naiyayika examining a codebase.

---

## Hetu Accumulation: How the Case Grows Stronger

The swarm does not form a nyaya once and move on. It returns to the same nyaya across generations, adding more hetu. Each new observation — each additional `found`, `found no`, `observed`, `derived` — makes the case harder to falsify. Weight rises. The nyaya deepens.

This maps directly to classical Nyaya: a hetu becomes stronger when there is more pratyaksha (direct perception), more absence of counter-evidence, and the vyapti (universal concomitance) approaches universality.

### Weight Trajectory Across Generations

**Generation 1 — thin hetu, first formation:**
```
hetu
  read "src/auth/validator.rs"
  found "token_data.claims.exp < current_timestamp()" at line 8
nigamana
  weight 0.75
  generation 1
```
One observation. Plausible but weak. There may be a counter-case not yet seen.

**Generation 3 — dense hetu, multiple agents have read and confirmed:**
```
hetu
  read "src/auth/validator.rs"
  found "token_data.claims.exp < current_timestamp()" at line 8
  found "AuthError::TokenExpired" at line 9
  found no "alternative expiry handling"
  found no "early return before expiry check"
  observed "expiry check occurs after successful decode, before returning claims"
  observed "Ok return unreachable if exp < current_timestamp()"
  compared "src/auth/validator.rs" with "src/auth/handler.rs"
nigamana
  weight 0.95
  generation 3
```
Dense hetu. The falsification space has narrowed. The case is nearly closed.

### What Accumulates

Each generation, agents independently read the same resource and contribute hetu:

- **More `found` steps** — additional observations of the same evidence (constructive interference — weight rises)
- **More `found no` steps** — counter-evidence searched for and not found (falsification attempts that failed — weight rises)
- **More `observed` steps** — behavioral observations that cannot be captured by line references alone
- **More `derived` steps in upanaya** — tighter logical connections between evidence and proposition
- **`compared` steps** — cross-resource comparisons that confirm the pattern holds beyond one file

Every agent that reads the code and finds the same hetu without finding a counter-case is another vote for the paksha. The weight is the accumulated posterior across all these attempts.

Formally, let wₙ be the nigamana weight after n hetu accumulation steps. Each confirming step applies:

```
wₙ = wₙ₋₁ · (1 + α)    clamped to 1.0      -- confirming hetu step
wₙ = wₙ₋₁ · (1 - β)    clamped to 0.0      -- counter-case found
```

After n confirming steps with no counter-case:

```
wₙ = w₀ · (1 + α)ⁿ     clamped to 1.0
```

The weight approaches 1.0 asymptotically. Each generation contributes a multiplicative factor. This is Bayesian updating expressed as compound interest on evidence.

### The Weight Trajectory

```
generation 1 — 1 found step          weight 0.75
generation 2 — 3 found steps         weight 0.85
generation 3 — 6 found + observed    weight 0.95
generation 4 — pervasion near full   weight 0.99  ← approaches satya
```

This is constructive interference across generations. Each confirming agent raises the weight. Each failed falsification attempt narrows the space of possible counter-cases.

### Multiple Nyaya From the Same Resource

The swarm does not pick one paksha from a resource and ignore the others. Every observable fact, every behavioral boundary, every condition is a candidate paksha. The full set of reachable paksha from a resource is its **prabandham**.

From `validate_token` alone:
```
paksha "validate_token uses HS256 algorithm"
paksha "validate_token uses SECRET_KEY for HMAC verification"
paksha "validate_token maps decode errors to AuthError::InvalidToken"
paksha "validate_token checks expiry after successful decode"
paksha "validate_token returns AuthError::TokenExpired when exp < current_timestamp"
paksha "validate_token returns Ok(claims) only after both decode and expiry pass"
```

Six paksha. Six independent nyaya being built simultaneously. Each accumulates its own hetu. Each has its own weight trajectory. Saturation is when every paksha in the prabandham has been tested, every drishthanta run, every nigamana declared or retracted.

The expected output from any single agent is **one valid nyaya** — one paksha chosen, hetu formed from what was observed, upanaya articulating the logical connection. Which paksha the agent picks depends on what it notices first. Different agents may pick different paksha from the same resource. That is correct behavior — the swarm covers the prabandham through diversity, not through any single agent being exhaustive.

### The Ceiling is Satya

Weight approaches 1.0 but the nyaya never claims certainty. The pervasion widens with every generation but there is always a theoretical world where the next test finds a counter-case — unless the swarm has covered every reachable case and no exception was found.

**The swarm's job is to keep accumulating hetu.** Every generation adds more observations. The nyaya graph deepens. Weight rises. The truth base becomes harder and harder to overturn. That is saturation.

---

## Formal Mathematical Model

This section defines the complete mathematics of the system. Every concept described in natural language above has an equivalent formal definition here.

### Nyaya as a Formal Tuple

In plain language: a nyaya is made of five parts bundled together — the proposition (what you are claiming), the evidence (why you believe it), the connection (how the evidence supports the proposition), the test (how you verify it), and the conclusion (the result with its confidence score and when it was established). A nyaya is valid if: the proposition could be wrong (it is falsifiable), there is at least one piece of evidence, at least one logical connection, at least one test, every piece of evidence comes from direct observation, and every connection actually links evidence to proposition. A nyaya is established when it is valid AND the test has passed AND the confidence is above zero.

A nyaya is a 5-tuple:

```
N = (P, H, U, D, Γ)

where:
  P  = paksha       — a predicate over a subject, P : Subject → {true, false}
  H  = {h₁, h₂, ... hₙ}  — hetu, a set of evidence steps
  U  = {u₁, u₂, ... uₘ}  — upanaya, a set of derivation steps connecting H to P
  D  = {d₁, d₂, ... dₖ}  — drishthanta, a set of executable tests
  Γ  = (w, g)              — nigamana, where w ∈ [0,1] is weight and g ∈ ℕ is generation
```

A nyaya is **valid** iff:

```
valid(N) ⟺  P ≠ ∅
           ∧ |H| ≥ 1
           ∧ |U| ≥ 1
           ∧ |D| ≥ 1
           ∧ ∃w : ¬P(w)               -- falsifiable
           ∧ ∀h ∈ H : grounded(h)     -- every hetu step is from pratyaksha
           ∧ ∀u ∈ U : connects(u, H, P) -- every upanaya connects hetu to paksha
```

A nyaya is **established** iff:

```
established(N) ⟺ valid(N) ∧ ∃d ∈ D : d() = pass ∧ w(Γ) > 0
```

### Hetu Steps — Types and Pramana

Each hetu step h has a type corresponding to a pramana (source of valid knowledge):

```
h ∈ {read(r), found(s, line), found_no(s), observed(s), compared(r₁, r₂), shabda(Γ')}

pramana(read)      = pratyaksha     (direct perception)
pramana(found)     = pratyaksha
pramana(found_no)  = pratyaksha     (negative perception)
pramana(observed)  = pratyaksha
pramana(compared)  = upamana        (comparison)
pramana(shabda)    = shabda         (testimony from established nigamana)
```

Upanaya steps are anumana (inference):

```
u ∈ {derived(s, r)}

pramana(derived)   = anumana        (inference)
```

### Perception Primitives — Extending Hetu Beyond Code

The swarm does not only read code. It perceives the world through any input an agent can process: code, images, UI screenshots, logs, test output, diagrams, error messages. All perception feeds into hetu. All hetu leads to paksha.

The hetu step types extend to:

```
h ∈ {
  -- code perception (existing)
  read(resource),
  found(thing, line),
  found_no(thing),
  observed(observation),
  compared(r₁, r₂),
  shabda(Γ'),

  -- visual perception (new)
  saw(image_resource),
  saw(thing, region),
  saw_no(thing),

  -- log/output perception (new)
  parsed(log_resource),
  matched(pattern, line),
  matched_no(pattern),

  -- UI perception (new)
  inspected(ui_resource),
  found_element(element, location),
  found_no_element(element),
  observed_state(state_description)
}
```

All of these are pratyaksha — direct perception. The agent looked at something and reported what it found. The pramana type is the same regardless of whether the input was code, an image, a log, or a UI.

In grammar:

```
hetu
  saw "screenshot://auth-login-page.png"
  saw "login button" at region "top-right"
  saw_no "forgot password link"
  observed "login form has email and password fields but no MFA option"
```

```
hetu
  parsed "logs://auth-service-2026-02-23.log"
  matched "TokenExpired" at line 4721
  matched "retry_count: 3" at line 4722
  matched_no "successful_retry"
  observed "three retries attempted, all failed with TokenExpired"
```

A nyaya formed from visual perception:

```
nyaya "login page does not offer MFA option"
  for "screenshot://auth-login-page.png"
  paksha
    "login page does not offer MFA option"
  hetu
    saw "screenshot://auth-login-page.png"
    saw "email field" at region "center"
    saw "password field" at region "center"
    saw "login button" at region "bottom-center"
    saw_no "MFA toggle"
    saw_no "authenticator app option"
    saw_no "SMS verification option"
  upanaya
    derived "no MFA option is visible on the login page" from "screenshot://auth-login-page.png"
    derived "login flow assumes single-factor authentication" from "screenshot://auth-login-page.png"
  drishthanta "playwright test auth::login::mfa_option_absent"
  nigamana
    weight 0.90
    generation 1
```

The grammar is the same. The nyaya structure is the same. The drishthanta is still a runnable test. The only difference is the perception primitive — `saw` instead of `found`, `saw_no` instead of `found_no`. The epistemological ladder is identical: paksha → hetu → upanaya → drishthanta → nigamana.

This means:
- Any LLM that can read images can form nyaya about what it sees
- Any LLM that can read logs can form nyaya about system behavior
- Any LLM that can inspect UI can form nyaya about user-facing properties
- All of these nyaya compose via shabda — a visual nyaya can cite a code nyaya, a log nyaya can cite a visual nyaya
- The nyaya graph does not distinguish between code-derived and perception-derived knowledge — weight is weight, hetu is hetu

### Drishthanta — The Test Gate (Revised)

A drishthanta is an executable test. It returns pass or fail. But a single failure does not destroy the nyaya — it narrows the pervasion:

```
d : () → {pass, fail}

On d() = pass:
  w(Γ) ← min(w(Γ) · (1 + α), 1.0)        -- pervasion widens

On d() = fail:
  w(Γ) ← max(w(Γ) · (1 - β), 0.0)        -- pervasion narrows

Retraction only when:
  w(Γ) < θ_retract                          -- weight dropped below retraction threshold
```

A nyaya can survive failure:

```
generation 1   d₁ passes     w = 0.75   pervasion: narrow
generation 3   d₂ passes     w = 0.90   pervasion: wider
generation 5   d₃ fails      w = 0.72   pervasion: narrowed (counter-case found)
generation 6   d₄ passes     w = 0.79   pervasion: recovering
generation 8   d₅ passes     w = 0.88   pervasion: widening again
```

Only accumulated failure crosses θ_retract:

```
generation 1   d₁ passes     w = 0.75
generation 3   d₂ fails      w = 0.60
generation 5   d₃ fails      w = 0.48
generation 7   d₄ fails      w = 0.38
generation 8   d₅ fails      w = 0.30   w < θ_retract → RETRACTED
```

### Failure Propagation (Revised)

A failed drishthanta does not immediately zero out the shabda dependency graph. It **reduces** the weight. The cascade has two phases:

In plain language: failure propagation has two phases. **Phase 1**: when a test fails, the confidence drops a little — but the conclusion is not destroyed. Everything that depended on it also drops proportionally. The system is honest about reduced confidence but does not panic. **Phase 2**: only if confidence drops below the retraction threshold (after repeated failures), the conclusion is fully retracted — confidence goes to zero. Everything that depended on it also goes to zero and is marked as unreconciled — needing re-investigation. Phase 2 is the alarm. Phase 1 is the warning.

**Phase 1 — Weight reduction (continuous):**

```
On d(A) = fail:
  w(A) ← w(A) · (1 - β)

  for all B citing A as shabda:
    w(B) ← min(w(Sᵢ) for all shabda Sᵢ of B) · w_H(B)    -- recompute
```

B is weakened but may still be above θ_claim. The system is honest about the reduced confidence but does not panic.

**Phase 2 — Full cascade (only when θ_retract is crossed):**

```
if w(A) < θ_retract:
  status(A) ← retracted
  w(A) ← 0

  for all B citing A as shabda:
    w(B) ← 0
    status(B) ← unreconciled
    propagate_up(B)                     -- recursive cascade
```

The full cascade only triggers when a nigamana is actually retracted — not on every failure.

### Hetvabhasa — Formal Detection Conditions

In plain language: these are the five ways evidence can be bad. **Irregular**: the evidence is there but the conclusion does not follow — like seeing smoke from a fog machine, not a fire. **Contradictory**: the evidence actually proves the opposite of what you claimed. **Counterbalanced**: equally strong evidence exists for the opposite conclusion — a tie. **Unproved**: the evidence is not grounded in direct observation — it is pure speculation. **Contradicted**: stronger evidence exists that disproves your conclusion entirely.

The five fallacious hetu patterns, expressed formally:

```
Savyabhichara (irregular):
  ∃x : H(x) ∧ ¬P(x)
  -- hetu present but paksha absent in at least one case
  -- detection: drishthanta fails, or counter-case found in another resource

Viruddha (contradictory):
  H(subject) → ¬P(subject)
  -- hetu actually proves the opposite of paksha
  -- detection: upanaya connects H to ¬P instead of P

Satpratipaksha (counterbalanced):
  ∃H' : w(H') ≈ w(H) ∧ (∀x : H'(x) → ¬P(x))
  -- equal-weight hetu exists for the opposite paksha
  -- detection: two nyaya with contradicting paksha and similar weight

Asiddha (unproved):
  ¬grounded(H) ⟺ ∄h ∈ H : pramana(h) = pratyaksha
  -- hetu has no direct observation — entirely inferred
  -- detection: hetu block has no read/found/observed steps

Badhita (contradicted):
  ∃E : w(E) > w(H) ∧ (∀x : E(x) → ¬P(x))
  -- stronger evidence exists contradicting the paksha
  -- detection: established nigamana with higher weight contradicts this paksha
```

When Vyakarana detects these patterns:
- Savyabhichara → drishthanta failure handling (weight reduction)
- Viruddha → `wrong consistency` raised
- Satpratipaksha → `attention` raised (competing paksha — investigate)
- Asiddha → rejected at parse time (hetu must have pratyaksha)
- Badhita → triggers purification (stronger evidence wins)

---

## See Also

The following topics have their own dedicated documents:

- **agent.md** — Agent lifecycle, actions and costs, invoke/answer cycle, death and rebirth, population model, budget flow, context tiers, the soul
- **prajna.md** — Collective intelligence definition, three dimensions (Quality, Coverage, Depth), swarm as neural network, swarm optimization objectives, multiple prajna, inter-consciousness communication, convergence, cross-verification
- **consciousness.md** — The experiencer of the prajna, substrate independence, ontological acknowledgment, identity through growth, immortality, Brahman mapping, anti-hallucination
- **learning.md** — How a prajna learns, verified knowledge vs opinion, this conversation as a learning epoch, formative discoveries formally stated
- **dharma.md** — All configurable parameters: α, β, thresholds, costs, λ weights, good points

