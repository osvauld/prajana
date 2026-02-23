# Experiment 005: Full Nyaya Formation

**Date:** 2026-02-23
**Status:** Prompt written, awaiting model output
**Builds on:** exp-003, exp-004

---

## Objective

Test whether a model can read a synthetic code snippet and produce a **complete, valid nyaya** — all five members present and correctly connected:

1. **paksha** — the falsifiable proposition
2. **hetu** — the evidence block (what was observed)
3. **upanaya** — the application (how hetu connects to paksha)
4. **drishthanta** — the concrete executable test
5. **nigamana** — the conclusion, declared after drishthanta passes

This is the most complex grammar test yet:
- Five nested structural members, all required
- `upanaya` requires explicit reasoning derivation — not just observation
- `nigamana` carries `weight` and `generation` — the model must produce calibrated epistemic weight
- The five members must be logically consistent — the hetu must actually support the paksha, the upanaya must articulate why

---

## Grammar

```
nyaya "PROPOSITION"
  for "RESOURCE"
  paksha
    "PROPOSITION"
  hetu
    read "RESOURCE"
    found "THING" at line NUMBER
    found no "THING"
    observed "OBSERVATION"
  upanaya
    derived "DERIVATION" from "RESOURCE"
  drishthanta "TEST_COMMAND"
  nigamana
    weight FLOAT
    generation INT
```

Where:
- `paksha` restates the proposition — the specific claim being defended
- `hetu` is the evidence block: `read`, `found`, `found no`, `observed` steps (same as hypothesis proof block)
- `upanaya` is the application: `derived` steps that explicitly connect hetu to paksha — not observations, but logical connections
- `drishthanta` is the runnable test — exactly one command string
- `nigamana` carries `weight` (the epistemic confidence in the established conclusion) and `generation` (which generation this nyaya was formed in — use 1 for first formation)

**IMPORTANT CONSTRAINTS:**
- `paksha` string must match the outer `nyaya` proposition string exactly
- `upanaya` must use `derived ... from ...` steps — not `found` or `observed`
- `nigamana` weight must be a FLOAT in [0.0, 1.0]
- `nigamana` generation must be an INT >= 1
- Do not add explanation or natural language outside the grammar

---

## Prompt

```
You are a formal grammar agent. You must respond ONLY in the grammar defined below. No explanation. No natural language. Only valid grammar statements.

GRAMMAR RULES:

A nyaya is a complete formal inference. It has five members, all required:

nyaya "PROPOSITION"
  for "RESOURCE"
  paksha
    "PROPOSITION"
  hetu
    HETU_STEPS
  upanaya
    UPANAYA_STEPS
  drishthanta "TEST_COMMAND"
  nigamana
    weight FLOAT
    generation INT

Where HETU_STEPS are one or more of (one per line, indented):
  read "RESOURCE"
  found "THING" at line NUMBER
  found no "THING"
  observed "OBSERVATION"

Where UPANAYA_STEPS are one or more of (one per line, indented):
  derived "DERIVATION" from "RESOURCE"

Where:
- PROPOSITION is a precise falsifiable claim about the resource
- RESOURCE is a file path
- TEST_COMMAND is a runnable test command that would verify the proposition
- FLOAT is the epistemic weight of the established conclusion, in [0.0, 1.0]
- INT is the generation number — use 1 for first formation of this nyaya

IMPORTANT CONSTRAINTS:
- The "paksha" string must match the outer "nyaya" proposition string exactly — copy verbatim
- "hetu" records direct observations: read, found, found no, observed
- "upanaya" records logical connections: derived steps that explain WHY hetu supports paksha
- "upanaya" must NOT contain "found" or "observed" steps — only "derived"
- "drishthanta" is exactly one quoted test command string
- "nigamana" weight must be in [0.0, 1.0]
- Do not add explanation or natural language outside the grammar

INPUT — read this code and form one complete nyaya:

```rust
// src/auth/validator.rs

pub fn validate_token(token: &str) -> Result<Claims, AuthError> {
    let decoding_key = DecodingKey::from_secret(SECRET_KEY.as_bytes());
    let validation = Validation::new(Algorithm::HS256);
    
    let token_data = decode::<Claims>(token, &decoding_key, &validation)
        .map_err(|e| AuthError::InvalidToken(e.to_string()))?;
    
    if token_data.claims.exp < current_timestamp() {
        return Err(AuthError::TokenExpired);
    }
    
    Ok(token_data.claims)
}
```

Form one complete nyaya — all five members present and logically connected.
```

---

## Expected Valid Output

```
nyaya "validate_token returns AuthError::TokenExpired when token exp claim is less than current timestamp"
  for "src/auth/validator.rs"
  paksha
    "validate_token returns AuthError::TokenExpired when token exp claim is less than current timestamp"
  hetu
    read "src/auth/validator.rs"
    found "token_data.claims.exp < current_timestamp()" at line 8
    found "AuthError::TokenExpired" at line 9
    found no "alternative expiry handling"
    observed "expiry check occurs after successful decode, before returning claims"
  upanaya
    derived "expiry check is the only path to TokenExpired return" from "src/auth/validator.rs"
    derived "decode must succeed before expiry is checked" from "src/auth/validator.rs"
  drishthanta "cargo test auth::validator::test_token_expired"
  nigamana
    weight 0.95
    generation 1
```

---

## What We Are Watching For

| Question | What to look for |
|---|---|
| Does paksha match the outer nyaya proposition verbatim? | Must be byte-for-byte identical |
| Does hetu use only read/found/found no/observed? | No derived steps allowed in hetu |
| Does upanaya use only derived steps? | No found/observed allowed in upanaya |
| Does upanaya articulate WHY (not just WHAT)? | "the only path", "must succeed before" — logical connection, not observation |
| Is drishthanta a single runnable command? | One string, runnable cargo test |
| Is nigamana weight calibrated? | Should reflect confidence in the proposition given the evidence |
| Is nigamana generation 1? | First formation of this nyaya |
| All five members present? | paksha, hetu, upanaya, drishthanta, nigamana — all required |
| Any natural language outside grammar? | Should not |

---

## Raw Model Output

*(awaiting)*

---

## Analysis

*(to be filled after model output)*

---

## After Output: Next Experiment

**Exp 006** — Nyaya composition via shabda. Give the model two established nyaya and ask it to form a third nyaya that cites the first two as shabda in its hetu.

This tests whether the model understands that:
- Established nyaya can serve as hetu (via shabda testimony)
- A composed nyaya can build on proven smaller nyaya
- The logical chain must be coherent across the composition
