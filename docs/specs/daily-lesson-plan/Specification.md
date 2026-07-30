# Specification: Daily Personalized Lesson Plan
Related UX: docs/ux/prototypes/daily-lesson-flow.md, docs/ux/wireframes/daily-overview.md

## Status
Draft

## Overview
This feature decides, each calendar day, what the learner's practice should focus on across
all four skills (Reading, Listening, Writing, Speaking) — drawing on the learner's recent
mistake patterns (Mistake Tracking, PRD Epic-3) and vocabulary due for review (Vocabulary
Review, PRD Epic-2) — and presents one always-current overview showing what's ready, still
generating, or already completed for each skill. It is the orchestration and personalization
layer: it does not itself generate a Reading passage, a Listening script, or evaluate a
Writing/Speaking response — it decides *what those should target* and hands that focus to
Reading Practice (Epic-9), Listening Practice (Epic-10), Writing Coaching (Epic-7), and
Speaking Coaching (Epic-8), then aggregates their state for display.

The feature is continuous — there is no fixed number of days or an end date. A new day's
focus becomes available on each new calendar day, replacing the fixed 180-day plan model of
the superseded `study-plan-execution` spec.

It corresponds to PRD Epic-1 (`docs/business/PRD.md`) and traces to Vision goals G-1 and G-2.

## User Scenarios
- As the learner, I want to open the app and immediately see today's practice status for all
  four skills, so I don't have to guess what to do or go find material myself.
- As the learner, I want today's practice to reflect my own recent mistakes and vocabulary
  gaps, so I'm not repeating things I've already mastered or missing what I actually need.
- As the learner, I want to see *why* a piece of practice was chosen (which mistake or
  vocabulary word it targets), so personalization feels real rather than claimed.
- As the learner, I want a failed generation for one skill to be retryable without losing my
  progress on the other three, so a single failure doesn't ruin my whole session.
- As the learner, I want to reach Vocabulary Review, Mistake Notebook, Progress, and Data
  Export from this screen regardless of today's generation state, so a stuck skill never
  blocks me from the rest of the app.

## Functional Requirements
- FR-1: On each calendar day, the system MUST determine one personalization focus per skill
  (Reading, Listening, Writing, Speaking), derived from the learner's recent mistake patterns
  and vocabulary due for review, for that skill's content generator to target.
- FR-2: When the learner has no recorded mistakes or due vocabulary yet (cold start), the
  system MUST still produce a personalization focus for each skill using a general-topic
  default, rather than blocking generation on personalization data that doesn't exist yet.
- FR-3: The system MUST compute and generate today's content exactly once per skill per day
  and reuse it across every view that day — it MUST NOT recompute the personalization focus or
  trigger new content generation for a skill already generated today, even across repeated
  visits to the overview.
- FR-4: The overview MUST show, for each of the four skills, exactly one of these states at
  all times: Ready (content available, not yet completed), Generating (content not yet
  available), Done (learner has completed and received a result/feedback), or Failed
  (generation did not succeed).
- FR-5: When a skill's content generation fails, the system MUST let the learner retry, and a
  retry MUST reuse the same personalization focus already computed for that skill that day
  rather than recomputing it.
- FR-6: The overview MUST display the specific mistake pattern or vocabulary item that informed
  each skill's personalization focus, described in terms the learner recognizes (e.g. "targets
  the word 'nevertheless'"), not an internal identifier.
- FR-7: The system MUST supply today's Writing prompt to Writing Coaching (Epic-7) and today's
  Speaking prompt to Speaking Coaching (Epic-8), each derived from that skill's personalization
  focus for the day, before the learner starts either.
- FR-8: The system MUST NOT impose a fixed end date or maximum number of days on this feature —
  a personalization focus MUST be computable for any future calendar day indefinitely.
- FR-9: Navigation from the overview to Vocabulary Review, Mistake Notebook, Progress, and Data
  Export MUST remain available regardless of any skill's generation state — a stuck or failed
  skill MUST NOT block access to these other features.
- FR-10: If personalization-source data (a mistake pattern or vocabulary item) used for a given
  day's focus is later deleted or changed, the system MUST NOT require that day's already
  generated/completed content to be regenerated or invalidated retroactively.
- FR-11: A skill not yet Done when a new calendar day begins MUST remain accessible and
  completable at any later time — its content MUST NOT be discarded or silently replaced by a
  new day's content. The learner can accumulate more than one day's worth of not-yet-Done
  skills across multiple days.
- FR-12: The overview MUST visibly distinguish a not-yet-Done skill carried over from a prior
  day from the current day's own skills (e.g. which day each belongs to), so the learner always
  knows whether they're looking at today's practice or unfinished earlier practice.

## Out of Scope
- The actual generation of Reading passages, Listening scripts/audio, or Writing/Speaking
  evaluation — owned by Epic-9, Epic-10, Epic-7, and Epic-8 respectively; this feature only
  decides and supplies the personalization focus and aggregates status.
- Learner-editable/manual override of the computed personalization focus (e.g. "let me pick my
  own topic today") — not requested by the Vision/PRD; the system always chooses.
- More than one lesson set per calendar day, or an explicit "start a new day early" action —
  the boundary is the calendar day (see FR-1), not a learner-triggered advance.
- Notifications, reminders, or streak/gamification mechanics — not backed by a Vision goal.

## Open Questions
None — resolved with the user: incomplete skills carry over and remain completable (FR-11,
FR-12) rather than being replaced.

## Acceptance Criteria
- [ ] Opening the app on a given day shows a status (Ready/Generating/Done/Failed) for all four
      skills, without the learner needing to trigger anything manually (FR-1, FR-4).
- [ ] With existing mistake/vocabulary data, at least one skill's displayed personalization
      note names a specific mistake pattern or vocabulary item (FR-6).
- [ ] With no mistake/vocabulary data at all (fresh account), all four skills still reach a
      Ready or Generating state rather than an error or blocked state (FR-2).
- [ ] Revisiting the overview multiple times in one day does not trigger additional generation
      for a skill already Ready/Done (FR-3) — verified by confirming no duplicate generation
      calls/content occur.
- [ ] Forcing one skill's generation to fail and retrying reuses the same personalization focus
      (verified by identical inputs to the retried generation call) and does not affect the
      other three skills' states (FR-5).
- [ ] Vocabulary Review, Mistake Notebook, Progress, and Data Export are reachable from the
      overview even while one skill is in a Failed state (FR-9).
- [ ] Today's Writing/Speaking prompts, once supplied, match the day's computed personalization
      focus for those skills (FR-7).
- [ ] Leaving a skill not-yet-Done and advancing to the next calendar day still allows that
      skill to be opened and completed, clearly labeled as belonging to its original day rather
      than the current one (FR-11, FR-12).
