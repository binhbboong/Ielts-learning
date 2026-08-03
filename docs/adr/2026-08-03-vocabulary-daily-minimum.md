# ADR: Vocabulary daily minimum of 20 words via due-queue + recommendation backfill

Date: 2026-08-03
Slug: vocabulary-daily-minimum
Status: Accepted
Related spec: docs/specs/vocabulary-review/Specification.md

## Context

The Vocabulary & Spaced Repetition Review feature (revision 2) presents exactly the words that
are due for review on a given day (`next_due_date <= today`), with an explicit MVP decision that
there is no cap on that count (see "Resolved Decisions" in the spec). There is no floor either:
a learner with a light due-queue (or none at all) gets a short session or no session, even though
the product goal — daily practice across all 4 skills plus vocabulary — calls for a minimum,
predictable daily vocabulary workload.

The user has asked for a day-by-day study roadmap covering all 4 skills with a minimum of 20
vocabulary words per day and full tracking. `daily-lesson-plan` (revision 2, IELTS Academic
adaptive allocation) already reserves 10 minutes/day for vocabulary+mistake review and drives the
4-skill daily orchestration, but a time budget is not a word-count guarantee — a learner could
have zero due words and see nothing to review that day. Vocabulary Review (revision 2) already
has the building block needed to close this gap: `get_level_recommendations` recommends curated,
level-appropriate words the learner doesn't yet own (FR-25 through FR-30). That mechanism was
built for a learner-initiated "add a recommended word" action, not for guaranteeing a daily floor
automatically.

Two supporting facts shape the decision:
1. The curated word bank (`_LEVEL_VOCABULARY`) has only 5 words per IELTS band today — nowhere
   near enough to backfill up to 20 new words on a due-less day without immediately exhausting
   the bank.
2. Every other AI-generation surface in this codebase (reading passages, listening scripts,
   writing/speaking prompts) goes through the `AIProvider` interface
   (`docs/adr/2026-07-29-ai-provider-interface-shape.md`). Routing vocabulary backfill through
   `AIProvider` as well was considered and rejected for this iteration — see Decision.

## Decision

1. **A learner's daily vocabulary session targets a minimum of 20 words** (`DAILY_REVIEW_TARGET
   = 20` in `backend/app/services/vocabulary.py`), computed each time a review session is
   started (`start_or_resume_review`) or previewed (`get_due_summary`):
   - Due words (`next_due_date <= today`) are always included first, in existing order.
   - If the due count is below 20, the session is **backfilled** with additional curated,
     level-appropriate recommended words (the same source as FR-25–FR-30's recommendation feed)
     up to a total of 20, or as many as remain unowned for the learner's current band —
     whichever is smaller.
   - Backfilled words are persisted as real `vocabulary_words` rows (`source =
     "daily_backfill"`, `interval_index = 0`, `next_due_date = today` — due *today*, not
     tomorrow, since they are being presented for review immediately) and enter the same
     recall → reveal → assess loop as due words. Assessing one reschedules it via the existing
     1/3/7/14/30-day ladder like any other word.
   - If fewer than 20 unowned recommended words remain for the learner's band, the system uses
     what's available and reports the shortfall rather than blocking or erroring (mirrors the
     existing FR-11/FR-24 "never fabricate, always communicate" pattern already in this spec).
2. **The curated word bank is expanded from 5 to 20 words per IELTS band** (100 words total,
   still hardcoded in `_LEVEL_VOCABULARY`, not `AIProvider`-generated). This is the smallest
   change that makes a full 20-word backfill possible on day one for a learner with zero due
   words and zero owned words, without introducing a new AI-generation surface. Rejected
   alternative: generating backfill words via `AIProvider` (consistent with reading/listening/
   writing/speaking) — deferred because it would require a new `AIProvider` method + prompt
   design + non-determinism handling + real-provider implementation, which is a bigger unit of
   work than this decision's scope and not requested. Flagged as a natural follow-up once the
   100-word bank is exhausted by an active learner (roughly 5 weeks of pure backfill at one band
   before the bank must expand again, phase-dependent).
3. **FR-10's "nothing to review" empty state is redefined** from "zero words due" to "zero words
   due AND zero backfill words available" — because with the floor in place, zero due no longer
   means zero to do; it may just mean today's words are all new ones.

## Consequences

- Easier: the daily vocabulary workload becomes predictable (always ~20 words, modulo bank
  exhaustion) instead of variable/possibly-zero, closing the gap with the day-by-day, all-4-
  skills, tracked roadmap the product goal calls for. `daily-lesson-plan`'s existing due-vocabulary
  personalization signal and 10-minute review budget are unaffected — this decision only changes
  what Vocabulary Review itself considers "today's queue."
- Harder: `_LEVEL_VOCABULARY` is now 100 hand-curated words instead of 25; maintaining/expanding
  it is manual work, and a very active learner can exhaust a band's bank before advancing to the
  next band/phase (shortfall is surfaced, not hidden, per point 1 above — accepted as an MVP
  limitation, not silently patched over).
- Forecloses (for now): true AI-generated, unlimited vocabulary recommendations. This decision
  explicitly chooses the curated-bank expansion over an `AIProvider` extension; revisiting that
  tradeoff is its own future decision, not bundled into this one.
- `Specification.md`'s "Out of Scope" bullet "AI-generated or AI-suggested vocabulary (words the
  learner did not enter themselves)" was already stale before this decision (revision 2's FR-25–
  FR-30 recommendations contradict it) — this decision's propagation pass corrects it, since
  backfill sharpens the same contradiction (backfilled words are suggested and auto-entered
  without the learner clicking "add").
