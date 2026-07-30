# Specification: AI-Generated Reading Practice & Auto-Scoring
Related UX: docs/ux/prototypes/daily-lesson-flow.md, docs/ux/wireframes/reading-exercise.md, docs/ux/wireframes/mistake-quick-add.md

## Status
Draft

## Overview
This feature generates a Reading passage and a set of multiple-choice comprehension questions
targeted at the day's Reading personalization focus (supplied by the Daily Personalized Lesson
Plan, PRD Epic-1), lets the learner answer them, and scores the answers immediately and
objectively — Reading correctness is well-defined, unlike Writing/Speaking, so no further AI
call is needed at scoring time. Each result feeds the learner's progress trend (Practice Result
Tracking, Epic-4) and offers a one-action path to log a wrong answer as a mistake (Mistake
Tracking, Epic-3), closing the personalization loop for future days.

This feature did not exist before the PRD revision that introduced it — Reading practice was
previously assumed to happen outside the app, with only a result manually logged elsewhere.

It corresponds to PRD Epic-9 and traces to Vision goals G-1, G-2, and G-5.

## User Scenarios
- As the learner, I want a Reading passage and questions ready for me each day, so I never have
  to find my own Reading material.
- As the learner, I want to see why this specific passage was chosen for me, so I trust it's
  actually targeting my weaknesses.
- As the learner, I want to know immediately how many questions I got right and which ones I
  missed, without waiting.
- As the learner, I want to turn a wrong answer directly into a Mistake Notebook entry without
  re-typing anything I already just saw on screen.

## Functional Requirements
- FR-1: The system MUST generate one Reading passage and a set of multiple-choice comprehension
  questions targeted at the day's Reading personalization focus supplied by the Daily
  Personalized Lesson Plan feature (Epic-1).
- FR-2: Each generated question MUST have exactly one correct answer recorded at generation
  time, so scoring never requires an additional AI call.
- FR-3: The passage MUST be displayed together with a note describing what it targets (the
  mistake pattern or vocabulary item it was generated for), in terms the learner recognizes.
- FR-4: The learner MUST be able to answer all questions and submit them in a single action.
- FR-5: On submission, the system MUST score the learner's answers immediately, without any
  additional AI call, and display for each question whether the learner's answer was correct
  and, if not, the correct answer.
- FR-6: The system MUST display an overall score (correct count out of total) alongside the
  per-question review.
- FR-7: For each incorrect answer, the system MUST offer a one-action path to log it as a
  Mistake Notebook entry, pre-filled with the skill, source (today's passage/question), the
  learner's answer, and the correct answer — the learner supplies, at most, only a reason
  category, per `docs/ux/wireframes/mistake-quick-add.md`.
- FR-8: Each Reading result (score, per-question correctness) MUST be recorded so it
  contributes to the learner's progress trend (Epic-4).
- FR-9: Once generated for a given day, a Reading passage and its questions MUST NOT change —
  re-opening the exercise before submission MUST show the same passage/questions, and after
  submission MUST show the same result.
- FR-10: If generation fails, the system MUST report a distinct failure state (not an empty or
  broken-looking exercise) and support retry using the same personalization focus, consistent
  with Epic-1's retry contract (FR-5 of `docs/specs/daily-lesson-plan/Specification.md`).
- FR-11: The Reading passage, questions, and the learner's submitted answers/result for a given
  day MUST be included in the learner's data export (Epic-5).

## Out of Scope
- Question types other than multiple-choice (e.g. matching headings, True/False/Not Given,
  fill-in-the-blank) — a deliberate V1 simplification; real IELTS Reading uses varied question
  types, but multiple-choice is the only type this feature generates/scores for now.
- A countdown timer or other exam-condition constraints — this is a practice tool, not a
  mock-test simulator (PRD Non-Goal: no full mock-test engine).
- Passage difficulty explicitly calibrated to a specific IELTS band score — personalization
  targets topics/weaknesses, not a numeric difficulty level.
- More than one Reading passage per calendar day.
- Manual creation/import of a Reading passage by the learner — all content is AI-generated.

## Open Questions
None — this feature's scope was fully resolved during the UX phase (see
`docs/ux/prototypes/daily-lesson-flow.md`'s Decisions Record).

## Acceptance Criteria
- [ ] A Reading passage and questions are generated and become visible once the day's Reading
      focus (from Epic-1) is available (FR-1).
- [ ] The passage displays a personalization note naming a specific mistake pattern or
      vocabulary item, when one exists for that day (FR-3).
- [ ] Submitting answers produces an immediate score and per-question correct/incorrect
      breakdown with no additional wait beyond local processing (FR-5, FR-6).
- [ ] Each incorrect answer offers a pre-filled "Add to Mistake Notebook" action that requires
      no re-entry of the question/answer/correct-answer (FR-7).
- [ ] A completed Reading result appears in the learner's progress trend view (FR-8).
- [ ] Re-opening a completed day's Reading exercise shows the identical passage, questions, and
      result as originally generated/submitted (FR-9).
- [ ] Forcing a generation failure shows a distinct failure state with a working retry that
      reuses the same personalization focus (FR-10).
- [ ] An exported data file includes the day's Reading passage, questions, and result (FR-11).
