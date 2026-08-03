# Tasks: Vocabulary & Spaced Repetition Review
Plan: docs/specs/vocabulary-review/ImplementationPlan.md

## Revision-3 Task-18 — Expand curated word bank to 20/band + shared recommendation-candidate helper
- [x] Status: Done
- Depends on: none
- Goal: Expand `_LEVEL_VOCABULARY` from 5 to 20 words per band (100 total); extract
  `_band_recommendation_candidates(session, user_id, band, cefr)` shared by
  `get_level_recommendations` and the new backfill path so both always agree on what's available.
- Files touched: `backend/app/services/vocabulary.py`, `backend/tests/test_vocabulary_service.py`.
- Definition of done: `test_level_recommendations_follow_profile_and_exclude_existing` updated to
  assert 20 recommendations for a fresh band; existing exclude-already-owned behavior unchanged.

## Revision-3 Task-19 — Daily-target backfill in start_or_resume_review
- [x] Status: Done
- Depends on: Task-18
- Goal: `DAILY_REVIEW_TARGET = 20`; `_backfill_daily_words` persists up to
  `DAILY_REVIEW_TARGET - len(due_words)` new `VocabularyWord` rows (`source="daily_backfill"`,
  `interval_index=0`, `next_due_date=today`) from the band's candidates; session snapshot is
  `due_words + backfilled`. Covers FR-31, FR-32.
- Files touched: `backend/app/services/vocabulary.py`, `backend/tests/test_vocabulary_service.py`.
- Definition of done: `test_start_or_resume_backfills_to_daily_target_when_due_below_target` and
  `test_backfilled_word_is_persisted_source_daily_backfill_due_today` pass; pre-existing
  resume/session tests updated to `monkeypatch` `DAILY_REVIEW_TARGET` down to their original due
  count so their resume-mechanics assertions stay meaningful and unchanged.

## Revision-3 Task-20 — Due-summary backfill preview, shortfall, and FR-10 redefinition
- [x] Status: Done
- Depends on: Task-18
- Goal: `get_due_summary` gains `daily_target`, `backfill_count`, `shortfall`;
  `get_current_item`'s nothing-to-review branch checks `backfill_count == 0` too, not just
  `total_due == 0`. Covers FR-33, FR-34, and the FR-10 redefinition.
- Files touched: `backend/app/schemas/vocabulary.py`, `backend/app/services/vocabulary.py`,
  `backend/tests/test_vocabulary_service.py`, `backend/tests/test_vocabulary_router.py`.
- Definition of done: `test_due_summary_reports_daily_target_and_backfill_preview`,
  `test_backfill_reports_shortfall_when_band_recommendations_exhausted`,
  `test_zero_due_with_backfill_available_is_not_started_not_nothing_due`, and
  `test_zero_due_and_zero_backfill_is_nothing_due` pass.

## Revision-3 Task-21 — is_new on current item + new_words_included on complete summary
- [x] Status: Done
- Depends on: Task-19
- Goal: `ReviewCurrentItem.is_new` (word's `source == 'daily_backfill'`);
  `ReviewCompleteSummary.new_words_included` (count of that session's backfilled items). Covers
  FR-35.
- Files touched: `backend/app/schemas/vocabulary.py`, `backend/app/services/vocabulary.py`,
  `backend/tests/test_vocabulary_service.py`.
- Definition of done: `test_review_complete_summary_reports_new_words_included` passes;
  `get_current_item`'s item-kind result includes `is_new` matching the underlying word's source.

## Revision-3 Task-22 — Frontend: due-list backfill/shortfall preview
- [x] Status: Done
- Depends on: Task-20
- Goal: `DueQueueSummary` model + repository mapping gain `dailyTarget`/`backfillCount`/
  `shortfall`; Due List page shows "N due + M new words today" (or shortfall messaging) next to
  the existing due-count summary; zero-due-but-backfill-available no longer suppresses "Start
  review" (FR-10 frontend half).
- Files touched: `src/app/vocabulary/models/vocabulary-word.model.ts`,
  `src/app/vocabulary/data/vocabulary.repository.ts`,
  `src/app/vocabulary/pages/vocabulary-due-list/*`.
- Definition of done: `vocabulary-due-list.component.spec.ts` covers the backfill-preview and
  shortfall-messaging render paths and the zero-due-with-backfill "Start review" visibility case.

## Revision-3 Task-23 — Frontend: new-word tagging in session + review-complete new-words count
- [x] Status: Done
- Depends on: Task-21
- Goal: `ReviewItem` model gains `isNew`; `ReviewCompleteSummary` model gains
  `newWordsIncluded`; recall card shows a "New word" vs "Review" tag; Review-complete sub-view
  shows the new-words-included count alongside remembered/forgot.
- Files touched: `src/app/vocabulary/models/review-session.model.ts`,
  `src/app/vocabulary/data/vocabulary.repository.ts`,
  `src/app/vocabulary/pages/vocabulary-review-session/*`.
- Definition of done: `vocabulary-review-session.component.spec.ts` covers the New-word tag and
  the review-complete new-words-included count rendering.

## Revision-2 Task-13 — Level metadata and recommendation service
- [x] Status: Done
- Goal: Derive band/CEFR from StudyProfile, recommend curated IELTS Academic words, exclude
  existing words, and persist recommendation metadata per user.

## Revision-2 Task-14 — Level-aware vocabulary UI
- [x] Status: Done
- Goal: Show week, phase, IELTS band, CEFR, meanings, examples, topics, and one-click
  add-to-review actions.

## Notes

- **Supersedes the prior version of this file**, which was written against the client-only
  IndexedDB architecture (`docs/adr/2026-07-29-v1-no-backend-architecture.md`, now Superseded).
  No code exists against either version — this is a full build, not a migration of prior work.
- **External dependencies (not tasks in this backlog):** `backend/app/core/db.py` (`get_db`) and
  `backend/app/core/security.py` (`require_learner`), owned by the access-protection epic's
  backlog, running in parallel. This backlog assumes both exist by the time Task-11 (router)
  starts; if they don't yet, Task-11 blocks until they land. Same for the frontend's shared
  `core/api/api-client.ts`, assumed available by Task-12.
- **Product decisions resolved 2026-07-29:** Add Word returns to the exact Due List or Review
  Complete host state, closing with inline confirmation after save; cancel closes without
  navigation. The MVP due queue has no cap. Vocabulary "today" uses the configured learner
  timezone, defaulting to `Asia/Ho_Chi_Minh`.
- Per Constitution principle 2, every task below is implemented test-first: write the failing
  test named (or matching the shape) in Definition of Done, watch it fail, then implement.

## Task-1 — Vocabulary SQLAlchemy models and Alembic migration
- [x] Status: Done
- Depends on: none
- Goal: Define the three normalized tables from `docs/adr/2026-07-29-vocab-relational-schema.md`
  — `VocabularyWord`, `ReviewSession`, `ReviewSessionItem` — as SQLAlchemy ORM models (table
  definitions and relationships only, no query/business logic), and the Alembic migration that
  creates them: foreign keys (`review_session_items.session_id` -> `review_sessions.id`,
  `review_session_items.word_id` -> `vocabulary_words.id`), unique constraints on
  (session_id, position) and (session_id, word_id), an index on `next_due_date`, and a partial
  unique index on `review_sessions` enforcing at most one row with `completed_at IS NULL`.
- Files touched: `backend/app/models/vocabulary.py`,
  `backend/alembic/versions/<timestamp>_create_vocabulary_tables.py`.
- Definition of done: `alembic upgrade head` runs cleanly against a test database and creates
  all three tables with the constraints above; a migration test (or model-level test) asserts
  each FK, both unique constraints, and the partial unique index exist and reject violating
  inserts. Underpins FR-4 (interval-index-0 column), FR-18 (interval progression storage),
  FR-22 (session/session-items shape resume depends on) — no user-facing behavior yet, no FR
  closed by this task alone.

## Task-2 — Vocabulary Pydantic schemas and input validation
- [x] Status: Done
- Depends on: Task-1
- Goal: `VocabularyWordCreate` (word/meaning required non-empty, example/topic optional),
  `VocabularyWordRead`, `DueQueueSummary`, `ReviewCurrentItem`, `ReviewAssessmentRequest`,
  `ReviewCompleteSummary` schemas. Validation rules live here, not in router or service.
- Files touched: `backend/app/schemas/vocabulary.py`, `backend/tests/schemas/test_vocabulary_schemas.py`.
- Definition of done: `test_vocabulary_schemas.py` shows `VocabularyWordCreate` rejects an
  empty/whitespace-only `word` or `meaning` and accepts a payload with only `word`+`meaning`
  set (example/topic omitted). Covers FR-3 (schema half); enables FR-1/FR-2 for Task-3.

## Task-3 — Add-word service logic
- [x] Status: Done
- Depends on: Task-1, Task-2
- Goal: `services/vocabulary.py::add_word` — validates via the Task-2 schema, persists a new
  `VocabularyWord` row with `interval_index = 0` and `next_due_date = today + 1 day`.
- Files touched: `backend/app/services/vocabulary.py`, `backend/tests/services/test_vocabulary_service.py`.
- Definition of done: `test_add_word_minimal_fields` (word+meaning only, saves) and
  `test_add_word_without_example_or_topic` pass against a test database;
  `test_add_word_sets_interval_index_zero_and_next_due_tomorrow` asserts the persisted row's
  interval/due-date. Covers FR-1, FR-2, FR-4.

## Task-4 — Due-queue summary service
- [x] Status: Done
- Depends on: Task-1
- Goal: `services/vocabulary.py::get_due_summary` — counts `vocabulary_words` where
  `next_due_date <= today` using the configured learner-local date, plus a breakdown by
  interval step and by topic; returns a zero-safe result when
  nothing is due (no exception, no fabricated non-zero count). No cap/pagination on backlog
  size is implemented — per the spec's open question on this, out of scope here.
- Files touched: `backend/app/services/vocabulary.py`, `backend/tests/services/test_vocabulary_service.py`.
- Definition of done: `test_due_summary_count`, `test_due_summary_breakdown_by_interval_and_topic`,
  and `test_due_summary_zero_due` pass against a test database. Covers FR-8, FR-9, FR-10.

## Task-5 — Review session start-or-resume service
- [x] Status: Done
- Depends on: Task-1, Task-4
- Goal: `services/vocabulary.py::start_or_resume_review` — if a `review_sessions` row with
  `completed_at IS NULL` already exists, return it unchanged (resume, no new snapshot, no
  mutation of existing `review_session_items`); otherwise, if due words exist, create a new
  `review_sessions` header row plus one `review_session_items` row per due word (bulk insert,
  `position` assigned by a fixed order at creation time) and return it. Relies on the partial
  unique index from Task-1 as a concurrency backstop; add an application-level check ahead of
  the insert per the plan's concurrency risk note.
- Files touched: `backend/app/services/vocabulary.py`, `backend/tests/services/test_vocabulary_service.py`.
- Definition of done: a test creates a session, asserts snapshot rows match the due set at
  creation time 1:1 by position; a second call to `start_or_resume_review` with no new due
  words returns the same session id and leaves `review_session_items` untouched (row count and
  `position`/`outcome` values unchanged) — this is the resume half of FR-22. A concurrency test
  simulating two near-simultaneous calls asserts both resolve to the same session id, not two
  sessions.

## Task-6 — Spaced-repetition reschedule function (forgot-resets-interval rule)
- [x] Status: Done
- Depends on: none
- Goal: A pure, no-I/O function `reschedule(interval_index: int, outcome: Literal['forgot',
  'remembered']) -> tuple[int, date]` implementing the fixed 1/3/7/14/30-day ladder:
  "remembered" advances one step, floored at the last step (30 days); "forgot" resets to step 0
  (1 day) regardless of the prior step, per `docs/adr/2026-07-29-vocab-forgot-resets-interval.md`.
  Kept as its own task per that ADR's status as a highest-risk, independently-decided rule.
- Files touched: `backend/app/services/vocabulary.py` (or a colocated pure helper),
  `backend/tests/services/test_vocabulary_service.py`.
- Definition of done: `test_reschedule_remembered` is table-driven across all five ladder steps
  including the floor-at-30-days case; `test_reschedule_forgot_resets_to_step_zero_from_any_step`
  is table-driven asserting reset-to-1-day from every starting step (0 through 4). Covers FR-18
  and the forgot-reset rule (ADR `vocab-forgot-resets-interval`).

## Task-7 — Current-item resolution service (resume / nothing-due / error)
- [x] Status: Done
- Depends on: Task-4, Task-5
- Goal: `services/vocabulary.py::get_current_item` — if an active session exists, returns the
  first `review_session_items` row in `position` order with `outcome IS NULL` (or a
  "session-complete, ready to summarize" signal if none remain unassessed); if no active
  session exists and nothing is due, returns an explicit nothing-due signal; on a DB read
  failure, propagates an explicit error rather than any of the above.
- Files touched: `backend/app/services/vocabulary.py`, `backend/tests/services/test_vocabulary_service.py`.
- Definition of done: `test_resume_active_session_returns_first_unassessed_item_in_position_order`
  — creates a session, marks some items assessed, calls this function fresh (simulating reopen),
  asserts the exact next unassessed item is returned and already-assessed items are never
  re-returned (FR-22). A zero-due/no-active-session case returns the nothing-due signal (FR-23,
  service half). A simulated DB failure returns the error signal, never a word (FR-24, service
  half).

## Task-8 — Assess-item service
- [x] Status: Done
- Depends on: Task-6, Task-7
- Goal: `services/vocabulary.py::assess_current_item` — given a session's current unassessed
  item and an outcome ('forgot'/'remembered'), in one transaction: updates that
  `review_session_items` row (`outcome`, `assessed_at`), reschedules the corresponding
  `vocabulary_words` row via Task-6's `reschedule`, and — if this was the last unassessed item
  in the session — sets `review_sessions.completed_at`. Commits before returning.
- Files touched: `backend/app/services/vocabulary.py`, `backend/tests/services/test_vocabulary_service.py`.
- Definition of done: `test_assess_item_persists_before_returning_next_item` asserts the item
  row and word reschedule are committed in the same transaction before the function returns
  (FR-16); `test_assessing_final_item_sets_session_completed_at` asserts completion is set
  immediately on the last item (FR-19, service half). This function returning promptly (no
  extra step required) is what Task-16's auto-advance relies on for FR-17.

## Task-9 — Review-complete summary service
- [x] Status: Done
- Depends on: Task-8
- Goal: `services/vocabulary.py::get_review_complete_summary` — for a completed session,
  returns total items reviewed and a forgot/remembered tally via a `GROUP BY outcome` aggregate
  over `review_session_items`.
- Files touched: `backend/app/services/vocabulary.py`, `backend/tests/services/test_vocabulary_service.py`.
- Definition of done: `test_review_complete_summary_tallies_match_items` asserts the returned
  total and forgot/remembered counts match a fixture session's assessed items exactly. Covers
  FR-20; supports FR-21 (the "dates were updated" confirmation is true by construction since
  Task-8 already committed each reschedule before session completion — this task only supplies
  the numbers the confirmation copy is rendered alongside).

## Task-10 — Mid-session add-word non-interference guarantee
- [x] Status: Done
- Depends on: Task-3, Task-5, Task-7
- Goal: Verify and, if needed, harden `add_word` (Task-3) so that calling it while a session is
  active never inserts into, reorders, or otherwise mutates that session's
  `review_session_items` rows or `position` values — a newly added word is not eligible for the
  in-progress session's queue.
- Files touched: `backend/app/services/vocabulary.py` (if a guard is needed),
  `backend/tests/services/test_vocabulary_service.py`.
- Definition of done: `test_add_word_during_active_session_does_not_alter_session_items_or_position`
  — starts a session, records its `review_session_items` row count/positions/outcomes, calls
  `add_word`, re-reads the session's items and asserts byte-for-byte equality with the
  pre-add snapshot, and asserts `get_current_item` (Task-7) still returns the same item it
  would have before the add. Covers FR-7 (backend half).

## Task-11 — Vocabulary router
- [x] Status: Done
- Depends on: Task-2, Task-3, Task-4, Task-5, Task-7, Task-8, Task-9
- Goal: `POST /vocabulary/words`, `GET /vocabulary/due`, `POST /vocabulary/review/start`,
  `GET /vocabulary/review/current`, `POST /vocabulary/review/current/assess` — all behind
  `require_learner` (external dependency, access-protection epic). Thin: parse/validate via
  Task-2 schemas, delegate to the Task-3/4/5/7/8/9 service functions, map results to HTTP
  status/response bodies, including explicit error responses (never a fabricated/zero value or
  a silently-empty body) when the underlying service reports a read/write failure.
- Files touched: `backend/app/routers/vocabulary.py`, `backend/tests/routers/test_vocabulary_router.py`.
- Definition of done: `test_post_word_minimal_returns_201` (FR-1, response confirms save — FR-5);
  `test_add_word_db_error_returns_5xx_not_partial_write` (FR-6, backend half);
  `test_get_due_db_error_returns_explicit_error_not_zero` (FR-11);
  `test_get_current_after_last_item_returns_complete_state` (FR-19, router half);
  `test_get_current_with_zero_due_and_no_active_session_returns_nothing_due_not_complete`
  (FR-23, router half); `test_get_current_db_error_returns_explicit_error_no_word_body`
  (FR-24, router half). All routes reachable only with a valid learner session (delegated to
  `require_learner`, not re-tested here).

## Task-12 — Frontend vocabulary models and repository
- [x] Status: Done
- Depends on: Task-11 (API contract must exist)
- Goal: Following `src/app/study-plan/`'s repository pattern (sole point of contact with the
  shared HTTP client, one call in / one typed result out, no orchestration): TypeScript models
  for `VocabularyWord` and the fixed interval ladder; `DueQueueSummary`, `ReviewCurrentItem`,
  `ReviewCompleteSummary`, and a review-session status union; and
  `VocabularyRepository` wrapping `core/api/api-client.ts` (external dependency,
  access-protection epic) with `addWord()`, `getDueSummary()`, `startOrResumeReview()`,
  `getCurrentItem()`, `assessCurrentItem(outcome)`.
- Files touched: `src/app/vocabulary/models/vocabulary-word.model.ts`,
  `src/app/vocabulary/models/review-session.model.ts`,
  `src/app/vocabulary/data/vocabulary.repository.ts`,
  `src/app/vocabulary/data/vocabulary.repository.spec.ts`.
- Definition of done: `vocabulary.repository.spec.ts` asserts each method calls the correct API
  endpoint with the correct payload/shape and propagates a rejected call as a rejection rather
  than swallowing or translating it to a default value — the frontend contract FR-6 and FR-11's
  "never fabricate a value on failure" guarantees depend on at this layer.

## Task-13 — Vocabulary facade
- [x] Status: Done
- Depends on: Task-12
- Goal: Following `study-plan.facade.ts`'s pattern (signals + orchestration, the only thing
  pages call into): `VocabularyFacade` holding signals for due summary, current review
  item/progress, and session-complete summary; `loadDueSummary()`, `startOrResumeReview()`
  (called on review-flow entry), `assessCurrentItem(outcome)` (advances to the next item on
  resolve), and `addWord(...)` that calls the repository without touching session/current-item
  state.
- Files touched: `src/app/vocabulary/state/vocabulary.facade.ts`,
  `src/app/vocabulary/state/vocabulary.facade.spec.ts`.
- Definition of done: `vocabulary.facade.spec.ts` asserts (1) on load, `startOrResumeReview()`
  is called and the resumed item/position signal reflects the repository's response (FR-22,
  facade half); (2) `assessCurrentItem()` resolving updates the current-item signal to the next
  item without a further caller action (FR-17, facade half); (3) `addWord()` does not mutate the
  current-item/progress signals (FR-7, facade half).

## Task-14 — Add-vocabulary-word-panel component
- [x] Status: Done
- Depends on: Task-13
- Goal: Per `docs/ux/wireframes/add-vocabulary-word.md`: word/meaning/example/topic form,
  inline validation, Loading/Error/Populated states, save/cancel outcomes emitted to the host.
  Return-destination-agnostic by design (per `ImplementationPlan.md`'s File/Module Structure) —
  each host screen (Task-15, Task-16, Task-17) decides what happens after save/cancel; this
  component only emits the outcome.
- Files touched: `src/app/vocabulary/components/add-vocabulary-word-panel/add-vocabulary-word-panel.component.ts`,
  `.../add-vocabulary-word-panel.component.spec.ts`.
- Definition of done: Save Word stays disabled while word or meaning is empty (FR-3, frontend
  half); a successful `facade.addWord()` shows a visible confirmation (FR-5); a rejected
  `facade.addWord()` leaves all four field values intact and re-enables Save Word without
  requiring re-entry (FR-6, frontend half).

## Task-15 — Vocabulary Due List page
- [x] Status: Done
- Depends on: Task-13, Task-14
- Goal: Per `docs/ux/wireframes/vocabulary-due-list.md`: due-count summary, interval/topic
  breakdown, Start/Resume Review action, Add-a-word entry point (using Task-14's panel), across
  Empty/Loading/Error/Populated states.
- Files touched: `src/app/vocabulary/pages/vocabulary-due-list/vocabulary-due-list.component.ts`,
  `.../vocabulary-due-list.component.spec.ts`.
- Definition of done: Populated state renders the due count and breakdown (FR-8, FR-9); Empty
  state shows no "Start Review" action and reads as a positive milestone (FR-10); Error state
  is visually distinct from Empty and states the load failed, never shows 0 (FR-11); the
  Add-a-word control is present and reachable in both Empty and Populated states (FR-12).
  Stops short of the open question: what happens after save/cancel from this entry point is
  not specified or implemented here beyond closing the panel — no return-destination copy is
  invented.

## Task-16 — Vocabulary Review Session page: recall/reveal/assess loop
- [x] Status: Done
- Depends on: Task-13, Task-14
- Goal: Per `docs/ux/wireframes/vocabulary-review-session.md`: the Nothing-due / Loading /
  Error / Populated states, and within Populated, the Recall -> Reveal -> Assess loop with
  auto-advance, plus the footer "+ Add a word I just noticed" control (opens Task-14's panel
  without leaving the session).
- Files touched: `src/app/vocabulary/pages/vocabulary-review-session/vocabulary-review-session.component.ts`,
  `.../vocabulary-review-session.component.spec.ts`.
- Definition of done: recall card hides meaning/example until "Reveal Answer" is explicitly
  clicked, never on a timer or automatically (FR-13, FR-14); no advance to the next word occurs
  without a Forgot/Remembered selection (FR-15); the next word renders automatically immediately
  after `facade.assessCurrentItem()` resolves, no further action needed (FR-17); on load, the
  component renders whatever item/position `facade`'s resume call surfaced, including
  mid-queue (FR-22, frontend half); zero-due-and-no-session renders the Nothing-due state,
  visibly distinct from Loading/Error/Populated (FR-23); a facade/repository error renders the
  Error state and never a recall card (FR-24); opening and closing/saving the footer add-word
  panel leaves the learner on the exact same word and progress position they were on before
  opening it (FR-7, frontend half).

## Task-17 — Vocabulary Review Session page: session-complete sub-view
- [x] Status: Done
- Depends on: Task-16, Task-14
- Goal: Per `docs/ux/wireframes/vocabulary-review-session.md`'s "Session complete" state:
  swap the recall card for the Review Complete Summary (total reviewed, remembered/forgot
  breakdown, review-dates-updated confirmation copy, "+ Add a word" control using Task-14's
  panel).
- Files touched: `src/app/vocabulary/pages/vocabulary-review-session/vocabulary-review-session.component.ts`
  (same file as Task-16, complete-state branch and its spec cases),
  `.../vocabulary-review-session.component.spec.ts`.
- Definition of done: the instant the last due word is assessed, the component transitions to
  this sub-view (not a silently empty queue) (FR-19); it renders total reviewed and the
  forgot/remembered breakdown sourced from Task-9's summary (FR-20); it displays copy
  confirming review dates were updated (FR-21). Stops short of the open question: the
  "+ Add a word" control here is rendered and reachable, but what happens after save/cancel
  from this entry point (distinct from Task-16's mid-session case, which *is* fully specified)
  is not decided or implemented beyond closing the panel — no return-destination copy is
  invented, consistent with Task-15.
