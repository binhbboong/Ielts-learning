# ADR: Remove Speaking from the daily plan and checkpoint

Date: 2026-08-05
Slug: remove-speaking-from-daily-checkpoint
Status: Accepted
Related spec: docs/specs/daily-lesson-plan/Specification.md, docs/specs/speaking-coach/Specification.md

## Context

`docs/adr/2026-08-03-daily-checkpoint-gating.md` made all four skills (Reading, Listening,
Writing, Speaking) mandatory every day, gating the next day behind all four checkpoints plus
the vocabulary quiz. In practice this forces the learner through record → transcribe →
evaluate for Speaking every single day just to unlock tomorrow. The product no longer wants
Speaking to be a hard daily gate — it remains a valuable feature, but as self-directed,
learner-initiated practice (Speaking Coach, PRD Epic-8), not a mandatory daily deliverable
alongside Reading/Listening/Writing.

## Decision

Remove `speaking` from the daily rotation and required checkpoint set:

- `daily-lesson-plan`'s daily generation, minutes budget, and primary-skill weekday rotation
  cover Reading, Listening, and Writing only.
- Checkpoint `required_count` drops from 5 to 4 (3 skills + vocabulary quiz).
- Speaking Coach (Epic-8) is otherwise unchanged: still reachable as a standalone feature,
  still supporting phase-based prompt complexity
  (`docs/adr/2026-08-03-writing-speaking-level-adaptation.md`) when a learner opts into it
  directly via its own question-bank picker. It simply no longer receives a
  `daily-lesson-plan`-supplied `DailyFocus`/prompt tied to a specific calendar day's checkpoint.

## Consequences

Existing `DailyFocus` rows with `skill="speaking"` become historical (harmless — simply no
longer created going forward; no migration needed). The daily-generated-prompt path in
speaking-coach's revision 2 (FR-16) loses its supplier for new days; previously recorded
submissions created via that path remain fully retrievable, unaffected. Minutes/day drop by
whatever Speaking previously consumed, redistributed across Reading/Listening/Writing's
rotation.
