# ADR: Vocabulary Review Data Modeled as Three Normalized Postgres Tables (Words, Sessions, Session Items)

Date: 2026-07-29
Slug: vocab-relational-schema
Status: Accepted
Related spec: docs/specs/vocabulary-review/Specification.md

## Context

`docs/adr/2026-07-29-fullstack-vercel-claude-architecture.md` moved this project from a
client-only Angular app with IndexedDB to Angular + FastAPI + Neon PostgreSQL, and explicitly
flagged that the prior vocabulary data-model ADR's storage framing (`docs/adr/2026-07-29-vocab-
forgot-resets-interval.md` was written against an IndexedDB `VocabularyWord` store plus a
single-row `ReviewSession` record) is now stale, while the "forgot resets to 1-day" rule itself
is not — that rule is not reopened here.

The old (IndexedDB-era) plan chose a denormalized shape: each word carries its own current
schedule state, and a single "active session" record holds a queue snapshot (word-ID array) and
a position pointer, updated in place after every assessment. That shape mapped directly onto
IndexedDB's single-object-per-key model. Moving to a relational database reopens the question:
should the review-session snapshot stay a single blob-ish row (an array/JSON column of word IDs
plus a position and a parallel outcomes map), or become its own normalized table with one row
per queued word?

This is a data-model decision other code depends on directly: `backend/app/services/
vocabulary.py`'s session-resume logic (FR-22), its review-complete summary (FR-20), and every
router/service test written against it all key off however this is shaped — the same class of
"other code depends on directly" trigger the interval-reset ADR named for the reschedule rule.
It is worth deciding once, explicitly, rather than left to whoever writes `models/vocabulary.py`
first to decide implicitly.

Two shapes were considered:

1. **Two tables, JSON snapshot.** `vocabulary_words` (current schedule state per word) +
   `review_sessions` (id, `queue` as a JSONB-ordered array of word IDs, `position` integer,
   `outcomes` as a parallel JSONB map of word ID → outcome, `started_at`, `completed_at`).
   Closest analog to the old IndexedDB shape.
2. **Three tables, fully normalized.** `vocabulary_words` (unchanged) + `review_sessions`
   (session header only: id, `started_at`, `completed_at`) + `review_session_items` (one row
   per queued word: id, `session_id` FK, `word_id` FK, `position`, `outcome` nullable,
   `assessed_at` nullable), with real foreign keys and a unique row per (session, position) and
   per (session, word).

## Decision

Adopt the fully normalized three-table shape (option 2): `vocabulary_words`,
`review_sessions`, and `review_session_items`, with `review_session_items.session_id` and
`review_session_items.word_id` as enforced foreign keys.

Reasoning:
- **Relational database, relational shape.** Postgres via SQLAlchemy makes per-row queries,
  foreign-key integrity, and aggregate SQL (`COUNT ... WHERE outcome = 'forgot'`) direct and
  idiomatic. A JSONB queue/outcomes blob would work but re-introduces the same
  read-modify-write-whole-blob pattern IndexedDB required, without gaining anything from now
  being on Postgres — it trades relational tooling for hand-rolled JSON bookkeeping in Python.
- **Testability.** Per this plan's constitution-mandated TDD, service/router tests assert
  session-resume and summary behavior directly against test-database rows (`SELECT ... WHERE
  session_id = ... AND outcome IS NULL ORDER BY position LIMIT 1`) rather than deserializing and
  asserting on JSON structure. This keeps test setup and assertions symmetric with the rest of
  the FastAPI/SQLAlchemy stack every other epic's plan is also using.
- **Referential integrity for near-zero extra cost.** At single-learner data volumes (tens to
  low hundreds of due words per session), one extra small table and one bulk insert at session
  start is negligible cost, in exchange for the database itself guaranteeing a session item can
  never reference a nonexistent word — the JSONB approach could silently drift if it referenced
  a word ID that was ever removed (words are not deletable per spec Out of Scope, but the
  guarantee is free either way).
- **FR-22 is satisfied identically by both shapes** (both snapshot the queue at session start,
  independent of later due-date changes), so this was decided on maintainability/testability
  grounds, not correctness grounds — either would have passed the acceptance criteria.

## Consequences

- **Easier:** session-resume logic is one indexed query (`review_session_items` ordered by
  `position`, first row with `outcome IS NULL`); the review-complete summary (FR-20) is a
  `GROUP BY outcome` aggregate; per-assessment writes (FR-16) are a single-row `UPDATE` by
  primary key, easy to reason about as atomic; no JSON (de)serialization code exists anywhere
  in the vocabulary module.
- **Harder / accepted trade-off:** starting a session requires bulk-inserting one
  `review_session_items` row per due word (an `INSERT ... SELECT`-shaped operation) instead of
  writing a single JSON array; three tables and two foreign keys to migrate via Alembic instead
  of two tables, a small, fixed one-time cost.
- **At most one active session** is still an assumption carried over from the old plan's
  "`ReviewSession` singleton" risk — enforced here via a partial unique index on
  `review_sessions` (`WHERE completed_at IS NULL`) plus an application-level check in
  `services/vocabulary.py`, not by the schema shape decided in this ADR. If a future requirement
  allows concurrent/parallel queues, that assumption — not this table shape — is what would need
  to change.
- **Forecloses:** nothing behavioral; this is purely a storage-shape decision. The interval-reset
  rule (`docs/adr/2026-07-29-vocab-forgot-resets-interval.md`) is unaffected and unreopened.
