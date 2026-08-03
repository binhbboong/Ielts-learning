# Changelog

All notable changes to this project are documented here, newest first. Entries are drafted by
`/release:release` and appended manually after review.

## [Unreleased]

### Added
- Vocabulary daily minimum: each day's vocabulary review now targets at least 20 words —
  due words first, backfilled with curated level-matched words when the due count falls short
  (docs/specs/vocabulary-review/, docs/adr/2026-08-03-vocabulary-daily-minimum.md). Curated word
  bank expanded from 5 to 20 words per IELTS band. Due List and Review Session (standalone pages
  and the Daily Overview warm-up widget) now show the backfill preview, shortfall messaging, a
  New word/Review tag per card, and a new-words-included count on the review-complete summary.

### Fixed
- Two pre-existing test suites had hardcoded dates from when they were authored
  (`test_vocabulary_service.py`, `test_daily_lesson_plan_router.py`,
  `daily-overview.component.spec.ts`) and had gone stale/flaky as real time passed them by;
  anchored to the real clock / derived from the same rotation table the code under test uses.

### Notes
- This is the project's first drafted release entry. The broader app (daily-lesson-plan,
  mistake-tracking, progress-tracking, reading/listening practice, writing/speaking coaching,
  access-protection, data-portability) is implemented and its own Tasks.md backlogs are fully
  checked off, but several of those *other* epics carry pre-existing, deliberately-deferred
  `[NEEDS CLARIFICATION]` markers in their specs (e.g. access-protection's session-duration
  question, writing/speaking-coach's submission-limit questions) — out of scope for this entry,
  not introduced by it, and not blockers for the vocabulary-daily-minimum work above. Flagged
  here for visibility, not silently passed over.
