# ADR: Per-skill 80% checkpoint, effective-day gating, all-4-skills-daily, and a vocabulary quiz mode

Date: 2026-08-03
Slug: daily-checkpoint-gating
Status: Accepted
Related spec: docs/specs/daily-lesson-plan/Specification.md, docs/specs/vocabulary-review/Specification.md

## Context

The user asked for the daily lesson flow to gate progression: each of the 4 skills plus
vocabulary must clear an 80%+ checkpoint before the next calendar day's lesson unlocks. Today,
`daily-lesson-plan`'s `get_skill_status` considers a skill "done" purely from the *existence* of
a submission — no score is checked (per `docs/adr/2026-07-30-daily-lesson-plan-data-model.md`,
FR-1/FR-11), and there is no concept of "locked" at all.

Scoring shapes differ across skills and needed reconciling before a single 80% rule could apply:
- Reading/Listening already persist a raw `score` (count correct) against a known `total`
  (question count) — percentage is trivial.
- Writing/Speaking are AI-graded on an IELTS band scale (0-9), not a percentage. Writing persists
  `overall_band`; Speaking persists only three per-criterion band scores, no aggregate.
- Vocabulary has no auto-graded, scoreable exercise at all today — review is self-assessed
  (learner marks "forgot"/"remembered"), which cannot produce a checkpoint score without
  fabricating one.

Two decisions were resolved directly with the user:
1. **Writing/Speaking checkpoint** uses the learner's own `StudyProfile.minimum_skill_band`
   (already tracked per learner, default 6.0) rather than a literal `band/9 >= 80%` conversion —
   band 7.2/9 was judged too strict relative to this app's default 3.5→6.5 target range.
2. **Gate scope is whole-day**: all 4 skills *and* the vocabulary quiz must pass today's
   checkpoint before tomorrow unlocks — not each skill gating independently.

**Revised while drafting**: an initial version of this ADR proposed a "soft gate" (generation stays
purely calendar-based/unconditional; only access is blocked). That was rejected before
implementation started — it would unconditionally spend AI-generation calls (real cost, per the
PRD's cost-consciousness constraint) on every future day's content even while the learner is
locked out of it, and it does not match the user's own framing ("nếu hoàn thành checkpoint có thể
làm bài của ngày tiếp theo" — next day's lesson only *becomes available* once the checkpoint is
cleared). The design below gates generation itself, via a computed "effective day," not just
display.

**All 4 skills, every calendar day**: also resolved with the user mid-implementation. The prior
design (`docs/adr/2026-07-30-daily-lesson-plan-data-model.md`'s `_DAILY_ROTATION`) allocated only
2 of 4 skills per day, rotating weekly. The user wants all 4 skills scheduled the same day, every
day. `_DAILY_ROTATION` (weekday → 2 skills) is replaced by a weekday → single *primary* skill
mapping; all 4 skills always generate, the day's primary gets more minutes than the other three.

## Decision

0. **Effective day, not literal calendar day, drives generation.** New function
   `get_effective_day(db, user_id, today)`: starting from the learner's `StudyProfile.start_date`,
   scan forward day by day; the effective day is the first day whose checkpoint (point 1 below)
   has not yet been fully cleared, capped at `today` (never generate ahead of the real calendar —
   a learner who is fully on pace simply has `effective_day == today`, unchanged from today's
   behavior). `ensure_today_generated`/`get_overview` operate on `effective_day`, not `today`
   directly. This avoids spending AI-generation calls on locked-out future days, and needs no
   persisted "current day" column — it is recomputed from existing submission/quiz data each call.
1. **Per-skill/vocab checkpoint pass criteria** (`backend/app/services/daily_lesson_plan.py`,
   new `evaluate_checkpoint(day, user_id)`):
   - Reading / Listening: `submission.score / total_questions >= 0.8`.
   - Writing: `submission.overall_band >= profile.minimum_skill_band`.
   - Speaking: `avg(criterion.band_score for the 3 criteria) >= profile.minimum_skill_band`
     (computed at read time; no new column — `SpeakingSubmission` gains no `overall_band` field,
     keeping this change additive-only on that model).
   - Vocabulary: a new **quiz mode** (see point 2) scored `correct / total >= 0.8`.
   - A skill with no submission yet for that day is simply "not yet passed" (not a hard failure) —
     the learner can still retry within the day.
2. **New Vocabulary quiz mode** (`docs/specs/vocabulary-review/Specification.md` revision 4):
   after a day's recall/reveal/self-assess review session completes (the existing flow, unchanged),
   a quiz step presents each word reviewed that day as a multiple-choice question — the word
   shown, 4 shuffled meaning options (1 correct + 3 distractors drawn from other owned words at
   the same CEFR level, falling back to other reviewed words if fewer than 3 same-level
   distractors exist), learner selects one. Auto-graded, `correct/total` computed on submission.
   This is additive: the existing self-assessed spaced-repetition scheduling (FR-13 through
   FR-24) is unchanged and still drives `next_due_date`/`interval_index` — the quiz only adds a
   graded checkpoint on top, it does not replace rescheduling logic.
3. **Effective-day gating (see point 0) is the whole gating mechanism** — there is no separate
   `locked` flag to invent, and no new endpoint-level 403s: a day beyond `effective_day` simply
   has no `DailyFocus`/quiz rows yet, so it doesn't exist in the overview at all until unlocked.
   This is deliberately *not* a revival of `study-plan-execution`'s persisted day-pointer — nothing
   is stored; `effective_day` is a pure function of existing checkpoint data, recomputed every
   call, so it stays consistent with `docs/adr/2026-07-30-daily-lesson-plan-data-model.md`'s
   "status derived from each skill's own table, never owned" principle. FR-8 ("no fixed end date")
   still holds — a learner who clears every checkpoint never notices any gating at all.
4. **Tab bar cleanup**: the top-level nav (`src/app/app.html`) drops a dead `/history` link (no
   such route exists — a leftover from the superseded `study-plan-execution` module) and the
   direct `Writing Coach`/`Speaking Coach` entries (those flows are meant to be entered from
   today's skill cards, not browsed independently — having them in the primary nav undercuts the
   gated daily-flow model this decision introduces). Primary tabs become: Today, Vocabulary,
   Mistakes, Progress, with Export moved to a secondary/utility position and active-route
   highlighting added (previously absent).

## Consequences

- Easier: a learner gets a clear, enforceable daily rhythm (must clear today before tomorrow),
  and the nav no longer offers ways to wander around today's gate.
- Harder: four different "pass" computations must be kept in sync with any future scoring change
  per skill; Speaking's derived aggregate band exists only in this evaluation function, not as a
  queryable column — if another feature later needs "speaking's overall band," it will need the
  same derivation or a proper persisted column (deferred, not decided here).
- Forecloses (for now): true per-skill independent gating (a strong learner in one skill being
  able to race ahead while behind in another) — whole-day gating was the explicit choice; revisit
  as its own decision if it proves too strict in practice.
- The vocabulary quiz's distractor-selection logic (same-CEFR-level fallback to other reviewed
  words) is a heuristic, not exhaustively specified — flagged as a risk in the implementation
  plan for small vocabularies where fewer than 4 total words exist.
