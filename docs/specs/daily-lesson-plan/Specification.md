# Specification: Daily Personalized Lesson Plan
Related UX: docs/ux/prototypes/daily-lesson-flow.md, docs/ux/wireframes/daily-overview.md

## Revision 6 — Tier-scaled structure and minutes

Decision: `docs/adr/2026-08-05-ielts-exam-structure-band-scaling.md`.

- FR-27: The per-skill minutes budget (FR-0C/FR-14's support/primary split) MUST scale by the
  learner's tier (beginner/standard/advanced — the same phase mapping as Writing/Speaking/
  Reading/Listening's respective revisions): beginner keeps the existing 20/10-minute primary/
  support split; standard raises primary to ~35-40 minutes and support to ~15-20; advanced raises
  primary toward real exam duration (~60 min Reading, ~30-40 min Listening, ~60 min Writing) with
  a reduced, not full-length, support-day version of the same tier's structure.
- FR-28: The daily overview's displayed total/skill minutes (FR-0D) MUST reflect FR-27's
  tier-scaled values, not the fixed beginner-tier numbers, once a learner is in standard or
  advanced tier.

## Revision 5 — Speaking removed from the daily rotation and checkpoint

Decision: `docs/adr/2026-08-05-remove-speaking-from-daily-checkpoint.md`. Supersedes revision 3's
FR-13 ("all four skills") and adjusts FR-15/FR-17's checkpoint count accordingly.

- FR-23: Every calendar day MUST generate content for Reading, Listening, and Writing only —
  Speaking is no longer part of the daily rotation, generation, or checkpoint — superseding
  revision 3's FR-13.
- FR-24: The checkpoint `required_count` is 4 (Reading, Listening, Writing, vocabulary quiz) —
  superseding revision 3's FR-15/FR-17's five/four-skills wording.
- FR-25: The primary-skill weekday rotation MUST distribute across Reading/Listening/Writing
  only, redistributing the weekday previously assigned to Speaking.
- FR-26: Speaking Coach (Epic-8) remains reachable as an independent, learner-initiated feature
  outside the daily plan; it MUST NOT be supplied a `daily-lesson-plan` `DailyFocus`/prompt for
  any new day going forward.

## Revision 4 — Scheduled pre-generation

Decision: `docs/adr/2026-08-03-daily-lesson-pregeneration-job.md`.

- FR-19: A scheduled job MUST run once daily at 08:00 `Asia/Ho_Chi_Minh` and, for every learner
  with an existing study profile, ensure content is generated for that learner's effective day
  (FR-16) and the day after — 2 days total, reusing FR-3's per-skill idempotent generation so an
  already-generated day/skill is left untouched and only missing ones are generated.
- FR-20: The scheduled job MUST NOT create a study profile for a learner who doesn't already have
  one (i.e., MUST NOT trigger generation for an account that has never opened the app).
- FR-21: The scheduled job's trigger endpoint MUST reject any request that doesn't present the
  configured shared secret — it is not a publicly callable endpoint, since it spends real AI
  generation cost.
- FR-22: A single learner's generation failure during the scheduled job MUST NOT prevent
  generation from completing for any other learner in the same run.

## Revision 3 — All 4 skills daily, checkpoint gating

Decision: `docs/adr/2026-08-03-daily-checkpoint-gating.md`.

- FR-13: Every calendar day MUST generate content for all four skills (Reading, Listening,
  Writing, Speaking), not a rotating subset — superseding FR-1's "select a primary and
  supporting skill" (now: select which skill is primary, all four still generate).
- FR-14: One skill per day MUST be designated primary (more allocated minutes) on a rotation;
  the other three are support skills for that day (fewer minutes each), summing to the 50-minute
  skill budget from FR-0C.
- FR-15: A skill's checkpoint for a day is passed when: Reading/Listening reach ≥80% correct on
  that day's submission; Writing's `overall_band` meets or exceeds the learner's
  `minimum_skill_band`; Speaking's average of its three criterion band scores meets or exceeds
  the learner's `minimum_skill_band`; Vocabulary's post-review quiz (Vocabulary Review revision
  4) reaches ≥80% correct. A skill with no submission yet is "not yet passed," not failed — it
  remains retryable within the day.
- FR-16: The day the learner is generating/working on ("effective day") MUST be the earliest
  calendar day since their plan start whose checkpoint (FR-15, all 4 skills + vocabulary quiz)
  is not yet fully passed, capped at the real current calendar date — never generated ahead of
  it. A learner who clears every day's checkpoint on time always has effective day = today,
  identical to pre-revision-3 behavior.
- FR-17: The overview MUST show the learner's checkpoint progress for the effective day (how
  many of the 5 required checkpoints — 4 skills + vocabulary quiz — are passed) and MUST make
  clear that tomorrow's content only becomes available once today's are all passed.
- FR-18: The system MUST NOT generate or expose any day's content beyond the effective day (FR-16)
  — no AI generation calls are spent on a locked-out future day.

## Status
Approved — revision 4 (scheduled pre-generation)

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
- FR-0: Every daily plan, generated exercise, submission, mistake, vocabulary item, result,
  and export MUST belong to exactly one authenticated learner and MUST be inaccessible to
  every other learner.
- FR-0A: A learner MUST be able to register and log in with a unique email and password; the
  authenticated session MUST identify the learner by an immutable account identifier.
- FR-0B: The system MUST maintain an IELTS Academic goal profile per learner with baseline
  band, target overall band, minimum skill band, plan start/end dates, daily minutes, and
  study days per week.
- FR-0C: For the default profile (3.5 to 6.5, minimum 6.0, 24 weeks, 60 minutes/day), each
  daily session MUST reserve 10 minutes for vocabulary/mistake review and allocate the
  remaining 50 minutes across all four skills (FR-13), with the day's primary skill (FR-14)
  receiving more of that budget than the other three.
- FR-0D: The daily overview MUST display exam type, current plan week/phase, target band,
  total minutes, review minutes, each allocated skill's minutes, priority, and selection
  rationale.
- FR-0E: Generated prompts and exercises MUST explicitly target IELTS Academic, the phase's
  target band, and the learner's selected weakness or review focus.
- FR-1: On each effective day (FR-16), the system MUST generate content for all four skills
  (FR-13) and select which one is primary for that day (FR-14), using the learner's plan phase,
  recent results, mistake patterns, and due vocabulary.
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
  focus for the day, before the learner starts either. The task type/complexity of each supplied
  prompt MUST match the learner's current phase (foundation through peak-performance), per
  `docs/adr/2026-08-03-writing-speaking-level-adaptation.md` — Writing-Coach's FR-18 and
  Speaking-Coach's FR-17 own the exact per-phase mapping.
- FR-8: The system MUST NOT impose a fixed end date or maximum number of days on this feature —
  a personalization focus MUST be computable for any future calendar day indefinitely, once that
  day becomes the effective day (FR-16).
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
  the boundary is the effective day (FR-16), not a learner-triggered advance.
- Notifications, reminders, or streak/gamification mechanics — not backed by a Vision goal.
- Per-skill independent gating (a strong learner in one skill advancing that skill's next day
  while behind in another) — the checkpoint gate (FR-15/FR-16) is whole-day, all 5 checkpoints
  together, per `docs/adr/2026-08-03-daily-checkpoint-gating.md`.

## Open Questions
None — resolved with the user: incomplete skills carry over and remain completable (FR-11,
FR-12) rather than being replaced.

## Acceptance Criteria
- [ ] Opening the app shows one 60-minute IELTS Academic session with 10 review minutes and
      all four skills allocated across the remaining 50 minutes, one marked primary, including
      phase and target-band context (FR-0C, FR-13, FR-14).
- [ ] Two registered learners cannot read, update, submit, or export each other's data.
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
- [ ] Reaching ≥80% on Reading/Listening, meeting `minimum_skill_band` on Writing (`overall_band`)
      and Speaking (avg of 3 criteria), and ≥80% on the vocabulary quiz all mark that day's
      checkpoint passed; falling short on any one leaves the day's checkpoint incomplete (FR-15).
- [ ] With today's checkpoint incomplete, tomorrow's content does not exist in the overview and
      no generation call is made for it; the moment today's checkpoint completes, the next
      calendar day (or the next not-yet-passed day if behind) generates on the next visit
      (FR-16, FR-18).
- [ ] The overview shows how many of today's 5 checkpoints (4 skills + vocabulary quiz) are
      passed (FR-17).
- [ ] Running the scheduled job for a learner with an effective day and no content yet generates
      that day and the next; running it again immediately after generates nothing further
      (FR-19).
- [ ] Running the scheduled job does not create a study profile for an account with none (FR-20).
- [ ] The job's trigger endpoint rejects a request without the correct shared secret (FR-21).
- [ ] One learner's simulated generation failure during the job does not prevent another
      learner's content from generating in the same run (FR-22).
