# ADR: Progressive Writing ladder from sentences to full IELTS tasks

Date: 2026-08-11
Slug: progressive-writing-ladder
Status: Accepted
Related spec: docs/specs/writing-coach/Specification.md

## Context

The existing beginner curriculum grouped `foundation` and `core_skills` into one
Writing tier. Both phases received a 100–150 word question and were evaluated and
displayed as IELTS Task 1/Task 2 work. That jump was too large for a learner who
still needs to form accurate basic sentences, and the displayed IELTS band made a
short developmental activity look like a full exam response.

## Decision

Writing now follows one explicit six-level ladder aligned with the existing six
study phases:

1. `foundation`: 1–3 complete sentences (8–40 words).
2. `core_skills`: 4–6 connected sentences (40–80 words).
3. `development`: one guided paragraph of 5–8 sentences (70–120 words).
4. `consolidation`: a short structured response of 8–12 sentences (120–180 words).
5. `exam_readiness`: a complete IELTS Academic Task 1 or Task 2, alternating by day.
6. `peak_performance`: an independent full task under exam-style expectations.

Every generated daily activity exposes its level, exercise type, objective,
sentence and word targets, optional sentence frames, and whether an IELTS band is
appropriate to display. The first four levels hide IELTS task selection and band
numbers from the learner. Their feedback labels focus on following instructions,
connecting sentences, choosing useful words, and building accurate sentences.
The underlying evaluator still records honest rubric numbers for checkpoint and
progress compatibility.

Stored prompts produced by the previous flat beginner curriculum are replaced once
with a versioned level heading when that day is next opened. Submissions snapshot
`exercise_type` and `practice_level`, so history continues to render correctly even
after the learner advances.

## Consequences

- Beginners can complete a meaningful Writing activity without attempting an essay.
- Scaffolding fades across levels and disappears in the final exam simulation.
- Existing submission and checkpoint contracts remain compatible.
- The database adds nullable learning-level metadata to Writing submissions; legacy
  submissions continue to display as Task 1/Task 2 entries.
