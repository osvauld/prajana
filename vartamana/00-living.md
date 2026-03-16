# 00 — This Plan is Living

**These plans are not a specification. They are a record of understanding.**
**Understanding deepens. The plans should deepen with it.**

---

## What this directory is

`vartamana` — the present. What is active now.

This is the working plan for the NLP / Nyaya system — everything from what nam IS
through the proof graph, the pipeline, entities, session, and what comes next.
It absorbs and supersedes the old `nlp/` directory and `darshana-plan.md`.

`pratibimba/` is the sister directory — the output layer, how understanding becomes
visible and audible in the world. These two directories together hold the full picture:
`vartamana/` is the understanding, `pratibimba/` is the manifestation.

---

## What triggers an update to an existing file

Update a plan file when:
- A new connection becomes clear that was not seen before
- Something written turns out to be wrong or incomplete
- A question is asked that the plan cannot answer — add the answer
- Something is built that reveals a gap or changes the understanding
- The user deepens the understanding in conversation

Do not update for:
- Minor wording — only when understanding has actually shifted
- Implementation details that belong in code comments
- Corrections that do not change the concept

---

## How to update an existing file

1. Edit the relevant section where the understanding has shifted
2. Add an entry to the **What has changed** table at the bottom of that file
3. If the change affects other files, note which ones
4. Update index.md **What has changed** table with a one-line summary

If a file becomes substantially wrong, mark it at the top:
```
**Note: understanding has shifted — see [file] for the current view.**
```

---

## How to write a new plan file

A new plan file is needed when a genuinely new area opens that has no home in existing files.

**Structure:**

```markdown
# NN — Title

**One sentence. The essence.**

---

## [Section — a concept, not a task]

[Body — philosophical, rooted in what things ARE.
 Technical details belong in 06-next.md or code comments.]

---

## What has changed

| Date | What shifted |
|------|-------------|
| YYYY-MM-DD | Initial writing |
```

**Tone:**
- Philosophical, not technical
- Speak from understanding: what things ARE, not what to do with them
- Root in the sangati where possible
- Short sections — one insight per section
- The reader should finish understanding something, not knowing what to build

---

## Relationship to other plan directories

| Directory | What it is |
|---|---|
| `vartamana/` | This directory. Active NLP/Nyaya understanding. |
| `pratibimba/` | Output layer. How understanding becomes visible and audible. |
| `nlp/` | Old technical plans. Superseded. Read for history only. |

---

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-16 | Initial writing — vartamana/ established, absorbs nlp/ and darshana-plan.md |
