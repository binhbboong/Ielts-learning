# ADR: Scheduled daily pre-generation of the next 2 days' lessons

Date: 2026-08-03
Slug: daily-lesson-pregeneration-job
Status: Accepted
Related spec: docs/specs/daily-lesson-plan/Specification.md

## Context

Today, lesson content generates lazily: the first time a learner opens the overview on a given
day, `ensure_today_generated` calls the AI provider synchronously for whatever skills aren't
generated yet for that day. The learner waits on that generation the moment they open the app.
The user asked for a scheduled job, once daily at 8:00am, that pre-generates content ahead of
time so it's already sitting ready before the learner opens the app that morning — covering the
next 2 days, skipping anything already generated, generating only what's missing.

This directly touches the effective-day checkpoint gating just shipped
(`docs/adr/2026-08-03-daily-checkpoint-gating.md`, FR-16/FR-18): that decision explicitly stops
`ensure_today_generated` from running for any day beyond the learner's effective day, specifically
to avoid spending AI-generation calls on a day the learner is locked out of. A naive job that
pre-generates "today+1, today+2" by the real calendar date, ignoring each learner's own progress,
would undo that — a learner stuck 5 days behind would still get their next 5+ days of content
silently generated (and paid for) every morning regardless of whether they'll ever reach them.

## Decision

1. **"Next 2 days" means 2 days relative to each learner's own effective day, not the raw
   calendar date.** New `pregenerate_upcoming_days(db, provider, tts, user_id, today)`: computes
   `effective_day = get_effective_day(...)`, then calls the existing `ensure_today_generated` for
   `effective_day` and `effective_day + 1` (2 target days, reusing FR-16's existing definition of
   "reachable"). A learner exactly on pace gets tomorrow pre-warmed before they open the app; a
   learner behind schedule gets their actual next unlocked day (and the one after) pre-warmed —
   never content beyond what they can reach. `ensure_today_generated` is already idempotent per
   skill (skips anything already generated) — that already satisfies the "if already generated,
   skip; if missing, generate the difference" requirement with no new logic needed there.
2. **Runs once per learner with an existing `StudyProfile`**, not every registered user. A user
   who registered but never opened the app has no profile yet; pre-generating for them would
   silently spend AI-generation cost on an account that may never be used. Profile creation stays
   triggered only by the learner's own first visit (unchanged), and the job iterates
   `StudyProfile` rows, not the full `users` table.
3. **Delivery mechanism: Vercel Cron** (`backend/vercel.json`'s `crons` array) calling a new
   `GET /api/cron/pregenerate-lessons` endpoint. GET, not POST, because Vercel Cron always issues
   GET requests to the configured path — this is a platform constraint, not a REST-purity choice;
   the endpoint has side effects (AI generation, DB writes) despite the verb.
   - Schedule `0 1 * * *` (01:00 UTC = 08:00 `Asia/Ho_Chi_Minh`, this app's fixed
     `LEARNER_TIMEZONE`, no DST to account for).
   - **Auth**: a new `CRON_SECRET` setting/env var. Vercel automatically attaches
     `Authorization: Bearer $CRON_SECRET` to its own cron-triggered requests when that env var is
     set on the project; the endpoint verifies the incoming header matches. Without this, the
     endpoint would be a public, unauthenticated trigger for real AI spend — unacceptable.
4. **Per-learner failures don't abort the batch.** Each profile's pre-generation runs in its own
   try/except; one learner's AI-provider error is recorded in the response body, not raised,
   so it can't block pre-generation for every other learner in the same run.

## Consequences

- Easier: learners who visit daily no longer wait on synchronous AI generation most mornings;
  the checkpoint-gating cost discipline from the prior decision is preserved, not undone.
- Harder: the job's correctness is now coupled to `get_effective_day`'s cost — for a learner very
  far behind (many unpassed days since `start_date`), that function scans forward day-by-day from
  `start_date` on every run, including inside this nightly job. Acceptable at this app's expected
  scale (single-digit learners, ≤168-day plans) — flagged, not solved, if this ever needs to
  serve materially more learners or much longer plans.
- Forecloses (for now): a "catch-up mode" that pre-generates further ahead for a learner who is
  behind — deliberately not built, since the effective-day model already re-derives what's next
  each time the job runs; a future decision could revisit whether 2 days is enough buffer.
