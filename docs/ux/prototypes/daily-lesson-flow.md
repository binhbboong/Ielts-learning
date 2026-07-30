# Prototype: Daily Lesson Flow
Journey: docs/ux/journeys/solo-ielts-learner-daily-lesson.md

## Screen Sequence
1. docs/ux/wireframes/daily-overview.md — triggered by: learner opens the app / logs in (journey step 1)
2. docs/ux/wireframes/reading-exercise.md (layout A) — triggered by: tapping "Start" on the Reading card, only enabled when its state is "Ready" (journey step 2-3)
3. docs/ux/wireframes/reading-exercise.md (layout B) — triggered by: "Submit Answers" on layout A (journey step 4)
4. docs/ux/wireframes/listening-exercise.md (layout A) — triggered by: tapping "Start" on the Listening card from Daily Overview, only enabled when "Ready" (journey step 5)
5. docs/ux/wireframes/listening-exercise.md (layout B) — triggered by: "Submit Answers" on layout A (journey step 6)
6. docs/ux/wireframes/writing-submission.md (layout A, existing) — triggered by: tapping "Start" on the Writing card from Daily Overview, prompt pre-filled from today's generated Writing prompt (journey step 7)
7. docs/ux/wireframes/writing-submission.md (layout B, existing) — triggered by: "Submit for Feedback" on layout A (journey step 8)
8. docs/ux/wireframes/speaking-submission.md (existing) — triggered by: tapping "Start" on the Speaking card from Daily Overview, prompt pre-filled from today's generated Speaking prompt (journey step 9)
9. docs/ux/wireframes/speaking-submission.md result state (existing, async status-tracked) — triggered by: recording submitted, polls through transcribing → evaluating → evaluated (journey step 10)
10. docs/ux/wireframes/daily-overview.md — triggered by: "Back to Today" / "Back to Today's Lesson" from any of the above, or automatically after each skill's result is shown (journey step 11 — all 4 cards now reflect Done)
11. docs/ux/wireframes/mistake-quick-add.md — triggered by: "Add to Mistake Notebook" quick action on a wrong Reading/Listening answer (journey step 12, optional); pre-filled from the result, not the manual mistake-logging-form.md (resolved — see Decisions Record below)

## Transitions
| From | Trigger | To |
|---|---|---|
| Daily Overview | Tap "Start" on a Ready skill card (any order) | That skill's exercise screen (layout A) |
| Daily Overview | Tap "Review" on a Done skill card | That skill's result screen (layout B) |
| Reading Exercise (A) | "Submit Answers" | Reading Exercise (B) — local, immediate |
| Listening Exercise (A) | "Submit Answers" | Listening Exercise (B) — local, immediate |
| Writing Submission (A) | "Submit for Feedback" | Writing Submission Loading state → (B) on success, or Error state on failure (existing behavior) |
| Speaking Submission | Recording submitted | Async status progression (submitted → transcribing → transcribed → evaluating → evaluated) → result view (existing behavior) |
| Reading/Listening Result (B) | "Add to Mistake Notebook" on a wrong answer | mistake-quick-add.md, pre-filled, one tap-and-confirm |
| Any exercise/result screen | "Back to Today" / "Back to Today's Lesson" | Daily Overview, with that skill's card now reflecting the up-to-date state |
| Daily Overview | Tap a secondary link (Vocabulary, Mistakes, Progress, Export) | That existing feature's own screen (out of this flow's scope) |

## Readiness for Specification
- [x] Every step of the source journey is covered by a screen in this flow. (Steps 1-12 all map to a screen sequence entry above.)
- [x] Every transition has a clear, unambiguous trigger.
- [x] No screen exists in this flow without a stated purpose from the journey. (`mistake-quick-add.md` was added specifically to close the earlier gap — see Decisions Record.)
- [x] Open UX questions are listed below, not silently resolved.

## Decisions Record
Resolved with the user before moving to `/spec:spec`:
- **Mistake quick-add**: a new, lightweight `docs/ux/wireframes/mistake-quick-add.md` was created rather than reusing `mistake-logging-form.md` as-is — the manual form's what/where/answer fields are all already known from the exercise result, so only the reason-category selection remains.
- **Retry on generation failure**: retries the exact same generation request (same personalization target) rather than recomputing personalization from scratch — keeps failures easy to reason about (a failed retry with identical inputs points at the AI provider, not at personalization logic).
- **Listening replay limit**: unlimited, by design — this is a personal practice tool, not a mock-exam simulator (PRD Non-Goal: no full mock-test engine), so replay is not artificially restricted to match real exam conditions.

## Open Questions
None outstanding.
