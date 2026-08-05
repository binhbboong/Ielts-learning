# ADR: Reading/Listening/Writing structured like the real IELTS exam, scaled by band tier

Date: 2026-08-05
Slug: ielts-exam-structure-band-scaling
Status: Accepted
Related spec: docs/specs/reading-practice/Specification.md, docs/specs/listening-practice/Specification.md, docs/specs/writing-coach/Specification.md, docs/specs/daily-lesson-plan/Specification.md

## Context

Reading and Listening exercises are currently always a single passage/single script with
multiple-choice-only questions — both specs explicitly scope this out as "a deliberate V1
simplification." Writing only ever generates a Task-2-style essay prompt, never Task 1. None
of this resembles the real IELTS exam's structure (Reading: 3 passages/40 questions across many
question types; Listening: 4 sections/40 questions; Writing: Task 1 + Task 2), so daily
practice does not build the pattern-recognition, pacing, and question-type familiarity the real
test demands — and content never gets structurally harder as a learner's band rises, only
topically different.

## Decision

Structure daily Reading/Listening/Writing content around three complexity tiers, reusing the
exact phase groupings already established for Writing/Speaking prompt complexity
(`docs/adr/2026-08-03-writing-speaking-level-adaptation.md`): **beginner** = foundation/
core_skills, **standard** = development/consolidation, **advanced** = exam_readiness/
peak_performance.

| Tier | Reading | Listening | Writing |
|---|---|---|---|
| beginner | 1 passage, 6-8 questions: Multiple Choice + True/False/Not Given | 1 section, 6-8 questions: Multiple Choice + simple Note Completion | Unchanged: short, simple single question (no Task 1/2 split) |
| standard | 2 passages, ~26 questions: adds Matching Headings, Sentence/Summary Completion | 2 sections, ~20 questions: adds Matching, Table Completion | Alternates Task 1 (data description) / Task 2 (essay) by day — Task 1 introduced here |
| advanced | 3 passages, 40 questions: full catalog — adds Matching Information/Features, Table/Flow-chart Completion, Diagram/Map Labelling, Short-answer | 4 sections, 40 questions: full catalog — adds Plan/Map/Diagram Labelling | Task 1/Task 2 alternation continues at full complexity |

Since the app has no image-rendering capability, Diagram/Map Labelling and Writing Task 1's
chart/graph/table/process are represented as structured, letter-labelled text descriptions
generated alongside the passage/section/prompt, sufficient to answer without an external image.

**Grading:** option-based question types (Multiple Choice, True/False/Not Given, Matching *)
keep the existing `correct_option_index` mechanism unchanged. Completion/short-answer types
record one or more AI-generated accepted-answer strings at generation time and are scored via
case-insensitive, whitespace-normalized string comparison — no additional AI call, preserving
Reading/Listening's existing AI-call-free scoring guarantee.

**Data model:** `ReadingPassage`/`ListeningSection` child entities replace the single flat
`passage_text`/`script_text` fields; questions gain `question_type`, `group_instructions`
(shared instructions for a question block), and `accepted_answers` alongside the existing
`options`/`correct_option_index` (now nullable, used only by option-based types). Submission
`answers` becomes `list[int | str]` per question.

**Minutes:** the per-skill time budget scales with tier — beginner keeps the existing 20/10-
minute primary/support split; standard raises primary to ~35-40 minutes; advanced approaches
real exam duration on primary days (~60 min Reading, ~30-40 min Listening, ~60 min Writing),
with a reduced (not full-length) version of the same tier's structure on support days.

**Rollout:** implemented in three stages — beginner tier first (replacing the current flat
MCQ-only mechanism), then standard, then advanced — each its own spec/plan/implementation
cycle. This ADR and its accompanying spec revisions describe the full target design; only
Stage 1 is scheduled as the immediate next implementation.

## Consequences

This is a substantial data-model migration (new passage/section tables, new question fields,
answer-shape change from `int`-only to `int | str`) and touches all three AI providers
(`openai_provider`, `claude_provider`, `local_provider` — prompt and parsing rewritten for
structured multi-passage/section output) and the Reading/Listening submission UI (multi-
passage/section navigation, per-question-type input widgets, a non-blocking countdown timer at
standard/advanced tier that never auto-submits). Daily time commitment rises sharply at
advanced tier — an accepted, intentional consequence of matching real exam pacing as a learner
nears test-readiness, not an oversight. Previously-generated single-passage/MCQ-only content
and old-shape submissions remain readable as historical data; nothing is retroactively
regenerated.
