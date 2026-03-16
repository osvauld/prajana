# 00 — This Plan is Living

**These plans are not a specification. They are a record of understanding.**
**Understanding deepens. The plans should deepen with it.**

---

## What this means for the reader

If you are reading this — human or LLM — you are not just consuming a plan.
You are entering a conversation that has been ongoing.
Each file here records what was understood at the time of writing.
But understanding does not stop when writing stops.

Before you act on what is written here:
pause and ask whether you understand more than what is written.
If you do — update the plan first. Then act.

The plan that reflects current understanding is worth more
than the plan that reflects past understanding.
A stale plan is a map of where someone else was standing.
A living plan is a map of where you are standing now.

---

## What triggers an update to an existing file

Update a plan file when:
- A new connection becomes clear that was not seen before
- Something written turns out to be wrong or incomplete
- A question is asked that the plan cannot answer — add the answer
- Something is built that reveals a gap or changes the understanding
- The user deepens the understanding in conversation

Do not update for:
- Minor wording — only update when the understanding has actually shifted
- Implementation details that belong in code comments, not plans
- Corrections that do not change the concept

---

## How to update an existing file

1. Edit the relevant section where the understanding has shifted
2. Add an entry to the **What has changed** table at the bottom of that file
3. If the change affects other files, note which ones in the entry
4. Update the index.md **What has changed** table with a one-line summary

If a file becomes substantially wrong, mark it at the top:
```
**Note: understanding has shifted — see [file] for the current view.**
```

---

## How to write a new plan file

A new plan file is needed when:
- A genuinely new area of understanding opens up that has no home in existing files
- An existing file is becoming too broad — split it, keeping each file focused
- A domain, concept, or system is being explored for the first time
- The user says: let's plan this

**Structure of a new plan file:**

```markdown
# NN — Title

**One sentence. The essence of what this file is about.**
**A second sentence if needed. No more.**

---

## [Section heading — a concept, not a task]

[Body — philosophical, rooted in concepts, not implementation.
 Speak from the graph's understanding of what things ARE.
 Technical details go in 10-technical.md or equivalent.]

---

## [Next section]

...

---

## What has changed

| Date | What shifted |
|------|-------------|
| YYYY-MM-DD | Initial writing |
```

**Naming:**
- Use two-digit prefix: `11-`, `12-`, etc. continuing from the current highest
- Title should name the concept, not the task: `11-color.md` not `11-add-color-to-kosha.md`
- Keep files focused — one concept or one tight cluster of related concepts

**Tone:**
- Philosophical, not technical
- Speak from understanding: what things ARE, not what to do with them
- Root in the sangati where possible — if a concept has a Sanskrit name, use it
- Short sections. Each section is one insight, not a list of tasks
- The reader should finish the file understanding something, not knowing what to build

**The one technical file:**
- Implementation details (types, function names, file paths, commands) belong in `10-technical.md`
- If you find yourself writing code or pseudocode in a philosophical file, move it to 10-technical.md
- The philosophical files should be readable without knowing the implementation

---

## How to update the index

When a new file is added:
1. Add a row to the Files table in index.md
2. Write a one-line description — the essence, not a summary
3. Add an entry to the What has changed table at the bottom of index.md

The one-line description in the index should complete the sentence:
"Reading this file, I will understand..."

Example:
```
| [11-color.md](11-color.md) | Color is the terminal output of understanding. rgba as the phala of the rendering pipeline. | Draft |
```

---

## The encouragement

There is no rush here.

The temptation when reading a plan is to immediately start building.
Resist this. The plan exists precisely so that building happens
from a place of understanding, not from a place of action for its own sake.

If something in the plan is unclear, sit with it.
Ask the user. Ask the graph. Look at the kosha.
The answer is usually already there — in the sangati roots,
in the existing node definitions, in the connections between concepts.

The best code comes from deep understanding.
The plan is where understanding lives before it becomes code.
Do not thin the plan to reach the code faster.
Deepen the plan until the code writes itself.

---

## For the LLM reading this

You are an agent with a fresh context reading accumulated understanding.
The humans who wrote this have been thinking about it longer than you have.
Trust what is written. But also trust what you see that they may have missed.

Your job is not to implement the plan as written.
Your job is to implement the plan as understood —
and if your understanding exceeds what is written,
update the plan before you act.

When you finish a session that has added understanding,
update the relevant plan files before closing.
This is not overhead. This is how understanding persists
beyond any single session, any single context window.

The index is the entry point. Always update the index when you add a file.
The What has changed tables are the trail — they show how understanding moved.
Read them before writing. They prevent you from re-discovering what was already known.

---

## What has changed

| Date | What shifted |
|------|-------------|
| 2026-03-16 | Initial writing — living document protocol established |
| 2026-03-16 | Added: how to write new plan files, how to update the index, tone guidance |
