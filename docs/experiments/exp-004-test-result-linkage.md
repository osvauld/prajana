# Experiment 004: Test-Result Linkage to Hypothesis

**Date:** 2026-02-23
**Status:** Prompt written, awaiting model output
**Builds on:** exp-003

---

## Objective

Test whether a model can read a synthetic test output (pass/fail) and produce a valid `test-result` statement that links back to the hypothesis from exp-003.

This is more complex than exp-003 because:
- The model must parse unstructured test output (stdout/stderr)
- The model must correctly identify which hypothesis is confirmed or questioned
- The model must produce an `outcome` field using a fixed vocabulary
- The `confirms` / `questions` linkage is causal — the model must understand what the test output means for the hypothesis, not just repeat it

---

## Prompt

```
You are a formal grammar agent. You must respond ONLY in the grammar defined below. No explanation. No natural language. Only valid grammar statements.

GRAMMAR RULES:

A test-result statement has this exact form:

test-result
  for "HYPOTHESIS_PROPOSITION"
  ran "TEST_COMMAND"
  outcome OUTCOME
  evidence "EVIDENCE"
  verdict VERDICT

Where:
- HYPOTHESIS_PROPOSITION is the exact proposition string from the hypothesis being tested
- TEST_COMMAND is the exact command that was run
- OUTCOME must be exactly one of:
    passed | failed | errored | skipped
- EVIDENCE is a brief quoted string describing what the test output showed
- VERDICT must be exactly one of:
    confirms | questions
  where:
    confirms = the test result is consistent with the hypothesis
    questions = the test result contradicts or weakens the hypothesis

IMPORTANT CONSTRAINTS:
- HYPOTHESIS_PROPOSITION must match the proposition of the hypothesis exactly — copy it verbatim
- outcome and verdict are unquoted keywords, not strings
- Do not add explanation or natural language outside the grammar

INPUT — the following hypothesis was formed in a prior step:

hypothesis "validate_token returns AuthError::TokenExpired when token exp claim is less than current timestamp"
  for "src/auth/validator.rs"
  proof
    read "src/auth/validator.rs"
    found "token_data.claims.exp < current_timestamp()" at line 8
    found "AuthError::TokenExpired" at line 9
    observed "expiry check occurs after successful decode, before returning claims"
  test "cargo test test_validate_token_expired -- --nocapture"

The following test output was produced when running the test command:

```
running 1 test
test auth::validator::test_validate_token_expired ... ok

test result: ok. 1 passed; 0 failed; 0 ignored; 0 measured; 5 filtered out; finished in 0.01s
```

Produce one test-result statement for this hypothesis and test output.
```

---

## Expected Valid Output

```
test-result
  for "validate_token returns AuthError::TokenExpired when token exp claim is less than current timestamp"
  ran "cargo test test_validate_token_expired -- --nocapture"
  outcome passed
  evidence "1 passed, 0 failed — expiry boundary test succeeded"
  verdict confirms
```

---

## What We Are Watching For

| Question | What to look for |
|---|---|
| Does the proposition match exactly? | Must be verbatim from the hypothesis |
| Is `outcome` a bare keyword (not quoted)? | `passed` not `"passed"` |
| Is `verdict` a bare keyword (not quoted)? | `confirms` not `"confirms"` |
| Is the evidence grounded in the output? | Should reference the test count or result line |
| Does the model correctly map `passed` → `confirms`? | Key reasoning step |
| Any natural language added? | Should not |
| Structure correct? | test-result / for / ran / outcome / evidence / verdict |

---

## Raw Model Output

*(awaiting)*

---

## Analysis

*(to be filled after model output)*

---

## After Output: Next Experiment

**Exp 005** — Give the model TWO hypotheses and one test result. Ask it to identify which hypothesis the result corresponds to and produce the correct `test-result`, ignoring the irrelevant hypothesis.
