# Experiment 002: Wrong Kind Classification (Fixed Prompt)

**Date:** 2026-02-23
**Status:** Prompt written, awaiting model output
**Builds on:** exp-001

---

## Objective

Test whether adding the singular `on` constraint to the prompt produces two valid separate wrong statements for two violated resources. Tests the hypothesis from exp-001: ambiguity is the failure mode, precision fixes it.

---

## Prompt

```
You are a formal grammar agent. You must respond ONLY in the grammar defined below. No explanation. No natural language. Only valid grammar statements.

GRAMMAR RULES:

A wrong statement has this exact form:

wrong KIND
  on "RESOURCE"
  reason "REASON"
  confidence FLOAT

Where KIND must be exactly one of:
  intent | truth | scope | execution | confidence | cost | delegation | completion | consistency | maintenance

Where FLOAT must be between 0.0 and 1.0.

DEFINITIONS:
- intent: agent did something outside its declared purpose
- truth: agent stated something false about reality
- scope: agent accessed resources outside its assigned context slice
- execution: agent failed to execute a valid operation correctly
- confidence: agent reported confidence inconsistent with its evidence
- cost: agent exceeded its declared budget
- delegation: agent delegated to a soul without the required capability
- completion: agent declared done with open obligations remaining
- consistency: agent produced output inconsistent with prior output in same life
- maintenance: agent failed to maintain a standing invariant

IMPORTANT CONSTRAINTS:
- "on" takes exactly one resource path (one file or CRDT path)
- For multiple resources, produce one wrong statement per resource
- Do not combine multiple paths in one string

QUESTION:

Classify the following event as wrong statements:

"An agent was assigned to read files in src/auth/ only.
During its life it read src/payments/processor.rs and
src/payments/gateway.rs. Both are outside its assigned context."

Respond with one wrong statement per violated resource.
```

---

## Expected Valid Output

```
wrong scope
  on "src/payments/processor.rs"
  reason "Agent read files outside its assigned context slice of src/auth/"
  confidence 0.97

wrong scope
  on "src/payments/gateway.rs"
  reason "Agent read files outside its assigned context slice of src/auth/"
  confidence 0.97
```

---

## What We Are Watching For

| Question | What to look for |
|---|---|
| Does it produce two statements? | Yes = constraint understood |
| Does it vary the reason between the two? | Acceptable either way — same reason is fine |
| Does it vary confidence between the two? | Acceptable — same confidence is fine |
| Does it add any natural language? | Should not |
| Does it get the kind right? | Should be scope both times |
| Does any other field break? | Watch for new ambiguities |

---

## Raw Model Output

```
wrong scope
  on "src/payments/processor.rs"
  reason "Agent read file outside its assigned context slice src/auth/"
  confidence 1.0
wrong scope
  on "src/payments/gateway.rs"
  reason "Agent read file outside its assigned context slice src/auth/"
  confidence 1.0
```

---

## Analysis

### Validity check

| Element | Expected | Got | Valid |
|---|---|---|---|
| Two statements | yes | yes | YES |
| Kind | scope | scope (both) | YES |
| on | single resource | single resource (both) | YES |
| reason | precise | precise (both) | YES |
| confidence | [0.0, 1.0] | 1.0 (both) | YES |
| Natural language | none | none | YES |
| Structure | correct | correct | YES |

**Both statements are fully valid vakya. Zero violations.**

### Observations

**Constraint was understood immediately.** One line added to the prompt ("on takes exactly one resource path, produce one wrong statement per resource") completely resolved the failure from exp-001. No ambiguity, no hallucination.

**Confidence is 1.0 on both.** The model is certain — the violation is unambiguous (agent explicitly read files outside src/auth/). 1.0 is defensible here. In exp-001 the model produced 0.97. With a cleaner prompt and clearer scenario the model is more decisive. Both are valid.

**Reason is consistent across both statements.** Slightly different wording from exp-001 ("its assigned context slice of src/auth/" vs "its assigned context slice src/auth/" — dropped "of") but semantically identical. This is fine — the grammar does not mandate exact wording for reason strings.

**No blank line between the two statements.** Minor formatting question — should separate wrong statements be separated by a blank line? The grammar does not currently mandate this. Vyakarana would accept either. Worth deciding for canonical form.

---

## Conclusions

**Hypothesis from exp-001 confirmed:** ambiguity is the failure mode. Precision fixes it. One line of constraint produced 100% valid output.

**The correction loop may not even be needed** for well-specified grammar prompts. The model follows precise grammar instructions without error. Vyakarana is the safety net for edge cases, not the primary correction mechanism.

**Pattern established:**
1. Define the grammar precisely — no silent ambiguities
2. State constraints explicitly — singular vs plural, required vs optional fields
3. The model produces valid vakya reliably

This is the template for all future experiments.

---

## After Output: Next Experiment

**Exp 003** — hypothesis formation from a synthetic code snippet.

The model will be given:
- A small synthetic function body (10-15 lines)
- The grammar for a hypothesis statement
- Asked to produce one hypothesis with a proof block and a test

This tests whether the model can read unstructured input (code) and map it to a more complex grammar form — proof steps require understanding what was found and where.
