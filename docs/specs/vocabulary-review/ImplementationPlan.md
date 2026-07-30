# Implementation Plan: Vocabulary & Spaced Repetition Review
Spec: docs/specs/vocabulary-review/Specification.md

**Supersedes** the prior version of this plan, which was written against the client-only
IndexedDB architecture (`docs/adr/2026-07-29-v1-no-backend-architecture.md`, now Superseded).
No code exists against either version — nothing was implemented under the old plan, so this is
a clean rewrite, not a migration. FR-1 through FR-24 are unchanged and reused as-is (the spec
was already written tech-agnostic); only the storage/module shape below is new.

## Approach

This feature now lives inside the full-stack architecture recorded in
`docs/adr/2026-07-29-fullstack-vercel-claude-architecture.md` and
`docs/architecture/Architecture.md`: Angular calls a FastAPI REST API; FastAPI is the sole
owner of Neon PostgreSQL via SQLAlchemy models and Alembic migrations. Access control
(`require_learner`), the shared DB session (`get_db`), and the frontend's shared HTTP client
(`ApiClient`) are owned by the access-protection epic's plan (parallel work) and are only
imported here, not redefined. Per the single-learner simplification, no table in this plan
carries a `learner_id`/owner column — `require_learner` gates the whole router instead.

Within that architecture, the open design question specific to this feature is unchanged in
kind from the old plan, just relocated to SQL: how is the spaced-repetition schedule state
modeled, and how is FR-22's "exact resume, no re-presentation of already-assessed words"
guarantee represented alongside it, now as relational tables instead of IndexedDB stores.

**Approach A — Two tables, JSON snapshot.** `vocabulary_words` (id, word, meaning, example,
topic, interval_index, next_due_date, created_at, last_reviewed_at) holds current schedule
state per word, directly analogous to the old plan's word record. `review_sessions` (id,
`queue` as a JSONB-ordered array of word IDs, `position` integer pointer, `outcomes` as a
parallel JSONB map of word ID → outcome, `started_at`, `completed_at`) holds the single active
session, closest analog to the old plan's IndexedDB `ReviewSession` record.
- Cost: low schema surface (two tables), but every read/write of session progress requires
  (de)serializing and mutating a JSON blob in Python — the same "rewrite the whole snapshot"
  pattern IndexedDB required, now inside Postgres instead of gaining relational tooling from it.
- Risk: no database-enforced guarantee that a word ID inside the JSON queue still refers to a
  real `vocabulary_words` row; that integrity check would have to be re-implemented in
  application code.
- Makes easy later: fewer tables to migrate.

**Approach B — Three tables, fully normalized (recommended).** `vocabulary_words` unchanged
from Approach A. `review_sessions` becomes a thin header (id, started_at, completed_at nullable
— null means active). A new `review_session_items` table holds one row per word in that
session's snapshot: id, `session_id` FK → `review_sessions.id`, `word_id` FK →
`vocabulary_words.id`, `position` (0-based order), `outcome` nullable ('forgot' |
'remembered'), `assessed_at` nullable. Unique constraints on (session_id, position) and
(session_id, word_id).
- Cost: one extra small table, and starting a session means bulk-inserting one row per due word
  instead of writing one JSON array — negligible at single-learner data volumes (tens to low
  hundreds of due words).
- Risk: none material; foreign keys give referential integrity the JSON approach would have to
  hand-roll.
- Makes easy later: FR-22 resume is one indexed query (`ORDER BY position`, first row with
  `outcome IS NULL`); FR-20's summary is a `GROUP BY outcome` aggregate; FR-16's per-assessment
  save is a single-row `UPDATE` by primary key; backend tests assert directly against rows in
  a test database instead of parsing JSON structure, which keeps this epic's tests symmetric
  with every other epic's SQLAlchemy-based tests.

**Approach C — Fold the session into the words table; no separate session record, infer
resumability from timestamps** (e.g., a `last_session_started_at` column plus comparing each
due word's `last_reviewed_at` against it). Checked directly against FR-22: if the due set
changes between session start and resume (e.g., the calendar date rolls over mid-session on a
long pause, making a previously-not-yet-due word newly due), the recomputed "due" set would
differ from the original queue, and queue order/membership from session start would not be
preserved — a direct violation of FR-22's "not restart the queue" guarantee. This is the same
failure mode the old IndexedDB-era plan's Approach C was rejected for; the underlying reason
does not change with the storage engine.
- Rejected for that reason, not on cost grounds.

**Recommendation: Approach B**, and recorded as its own ADR —
`docs/adr/2026-07-29-vocab-relational-schema.md` — since it is a data-model decision other code
(every service/router test, the resume and summary logic) depends on directly, per the
implementation-planning skill's ADR trigger conditions. It is the only approach that pairs
FR-22's exact-resume guarantee with idiomatic, directly-testable relational access, and it
matches the Vocabulary module's data-owning responsibility already assigned in
`docs/architecture/Architecture.md`. The "forgot" interval rule this approach's spaced-
repetition logic implements is fixed by `docs/adr/2026-07-29-vocab-forgot-resets-interval.md`
(reset to the 1-day step; that ADR is not reopened here — only its old IndexedDB storage
framing was ever stale).

**Constitution check (tests-first).** Per Constitution principle 2 and the
`test-driven-development` skill, every module in the File/Module Structure below is built by
writing its corresponding test first (see Testing Strategy), watching it fail, then
implementing — for every layer (model, schema, service, router, repository, facade, component),
not just the service layer. No exceptions are anticipated for this feature; if one arises it
requires explicit user sign-off per the constitution, not a silent skip.

## File/Module Structure

### Backend (owned by this plan)

| Path | Responsibility | Implements (wireframe, if UI-facing) |
|------|-----------------|-----------------|
| `backend/app/models/vocabulary.py` | SQLAlchemy ORM models: `VocabularyWord`, `ReviewSession`, `ReviewSessionItem`, per `docs/adr/2026-07-29-vocab-relational-schema.md`. Table definitions and relationships only — no query or business logic. | — |
| `backend/app/schemas/vocabulary.py` | Pydantic request/response schemas: `VocabularyWordCreate`, `VocabularyWordRead`, `DueQueueSummary` (count + interval/topic breakdown), `ReviewCurrentItem` (word shown now, hidden-until-revealed meaning/example, progress), `ReviewAssessmentRequest` (outcome), `ReviewCompleteSummary`. Validation rules (e.g., word/meaning non-empty) live here, not in the router. | — |
| `backend/app/services/vocabulary.py` | All Vocabulary business logic: adding a word (validate + persist at the 1-day interval), computing the due-queue summary and breakdown, starting/resuming the single active session (creating `review_session_items` snapshot rows), reading the current unassessed item, recording an assessment (reschedule the word via the spaced-repetition rule + mark the item + detect session completion), and the review-complete summary. Internally composed of small, separately unit-testable functions (a pure reschedule function has no I/O and is tested in isolation from the rest) even though colocated in one module per this project's shared backend convention. | — |
| `backend/app/routers/vocabulary.py` | FastAPI routes under `/vocabulary`, all behind `require_learner`: `POST /words` (add word), `GET /due` (due summary), `POST /review/start` (start-or-resume the active session), `GET /review/current` (current item or nothing-due/complete/error state), `POST /review/current/assess` (record outcome). Thin: parses/validates via schemas, delegates to `services/vocabulary.py`, maps service results to HTTP status/response. | — |
| `backend/alembic/versions/<timestamp>_create_vocabulary_tables.py` | One migration creating `vocabulary_words`, `review_sessions`, `review_session_items`, their foreign keys, the (session_id, position)/(session_id, word_id) unique constraints, the `next_due_date` index, and the partial unique index enforcing at most one active (`completed_at IS NULL`) session. | — |

### Frontend (owned by this plan), following `src/app/study-plan/`'s internal shape

| Path | Responsibility | Implements (wireframe) |
|------|-----------------|-----------------|
| `src/app/vocabulary/models/vocabulary-word.model.ts` | TypeScript shape of a `VocabularyWord` as returned by the API, and the fixed 1/3/7/14/30-day ladder constant used for display (e.g., interval-step labels in the breakdown). | — |
| `src/app/vocabulary/models/review-session.model.ts` | TypeScript shapes for `DueQueueSummary`, `ReviewCurrentItem`, `ReviewCompleteSummary`, and the review-session status union (nothing-due / in-progress / complete / error) the facade exposes to pages. | — |
| `src/app/vocabulary/data/vocabulary.repository.ts` | Sole point of contact with `core/api/api-client.ts` for this module: `addWord()`, `getDueSummary()`, `startOrResumeReview()`, `getCurrentItem()`, `assessCurrentItem(outcome)`. No state, no orchestration — one HTTP call in, one typed result out, per call. | — |
| `src/app/vocabulary/state/vocabulary.facade.ts` | Holds signals for due summary, current review item/progress, and session-complete summary; orchestrates repository calls and is the only thing the pages below call into, mirroring `study-plan.facade.ts`'s role. | — |
| `src/app/vocabulary/pages/vocabulary-due-list/vocabulary-due-list.component.ts` | Renders the due-count summary, interval/topic breakdown, Start/Resume Review action, and Add-a-word entry point, across Empty/Loading/Error/Populated states. | `docs/ux/wireframes/vocabulary-due-list.md` |
| `src/app/vocabulary/pages/vocabulary-review-session/vocabulary-review-session.component.ts` | Renders the Recall → Reveal → Assess loop with auto-advance, plus the Nothing-due/Loading/Error states and the Session-complete sub-view; delegates all scheduling/session logic to `vocabulary.facade.ts`. | `docs/ux/wireframes/vocabulary-review-session.md` |
| `src/app/vocabulary/components/add-vocabulary-word-panel/add-vocabulary-word-panel.component.ts` | Renders the add-word overlay form (word/meaning/example/topic), inline validation, Loading/Error/Populated states, and emits save/cancel outcomes. Has no knowledge of which parent screen opened it or where it should return to — each of the three host contexts (Due List, Review Session, Session-complete sub-view) owns its own return-destination handling after save/cancel, keeping the panel itself return-destination-agnostic. | `docs/ux/wireframes/add-vocabulary-word.md` |

## Testing Strategy

Per Constitution principle 2, every row below is written and fails (red) before the
corresponding module exists, then made to pass (green), per the `test-driven-development`
skill. Backend tests run against a real test-database instance (not mocks) so FK/unique
constraints and query behavior are exercised, not assumed.

| Requirement | Verified by |
|---|---|
| FR-1 (save with word+meaning only) | `backend/tests/services/test_vocabulary_service.py::test_add_word_minimal_fields` (test DB) + `test_vocabulary_router.py::test_post_word_minimal_returns_201`. |
| FR-2 (example/topic optional, never required) | `test_vocabulary_service.py::test_add_word_without_example_or_topic`. |
| FR-3 (block save until word+meaning non-empty) | `backend/tests/schemas/test_vocabulary_schemas.py`: empty word/meaning rejected by `VocabularyWordCreate`; router test asserts 422. Frontend: `add-vocabulary-word-panel.component.spec.ts` — Save Word disabled while either field is empty. |
| FR-4 (new word enters at 1-day interval) | `test_vocabulary_service.py::test_add_word_sets_interval_index_zero_and_next_due_tomorrow`. |
| FR-5 (visible save confirmation) | `add-vocabulary-word-panel.component.spec.ts`: confirmation shown after `facade.addWord()` resolves; `test_vocabulary_router.py`: response body contains the saved word's schedule fields the UI confirms against. |
| FR-6 (preserve fields + allow retry on failure) | `add-vocabulary-word-panel.component.spec.ts`: repository call rejected → all four fields retain values, Save Word re-enables. Backend: `test_vocabulary_router.py::test_add_word_db_error_returns_5xx_not_partial_write`. |
| FR-7 (mid-session add-word returns to exact position) | `test_vocabulary_service.py::test_add_word_during_active_session_does_not_alter_session_items_or_position`. Frontend: `vocabulary-review-session.component.spec.ts` — opening/closing the panel resumes the same word/progress. |
| FR-8 (show due count before session) | `test_vocabulary_service.py::test_due_summary_count`; `vocabulary-due-list.component.spec.ts` — due count rendered in Populated state. |
| FR-9 (breakdown alongside raw count) | `test_vocabulary_service.py::test_due_summary_breakdown_by_interval_and_topic`. |
| FR-10 (empty state neutral, no Start Review) | `test_vocabulary_service.py::test_due_summary_zero_due`; `vocabulary-due-list.component.spec.ts` — Empty state: no Start Review button, positive copy. |
| FR-11 (due count load failure, no fabricated/zero count) | `test_vocabulary_router.py::test_get_due_db_error_returns_explicit_error_not_zero`; `vocabulary-due-list.component.spec.ts` — Error state rendering, distinct from Empty. |
| FR-12 (add word reachable regardless of due state) | `vocabulary-due-list.component.spec.ts`: Add-a-word control present in both Empty and Populated states. |
| FR-13 / FR-14 (meaning hidden until explicit reveal) | `vocabulary-review-session.component.spec.ts`: recall card hides meaning/example pre-reveal, shown only after the Reveal Answer action, never on a timer. |
| FR-15 (must assess before advancing) | `vocabulary-review-session.component.spec.ts`: no auto-advance without a Forgot/Remembered selection. |
| FR-16 (assessment saved before advance) | `test_vocabulary_service.py::test_assess_item_persists_before_returning_next_item` — asserts the `review_session_items` row and word reschedule are committed in the same transaction before the response is built. |
| FR-17 (auto-advance without manual action) | `vocabulary-review-session.component.spec.ts`: next word renders automatically immediately after `facade.assessCurrentItem()` resolves. |
| FR-18 (remembered → next interval step) | `test_vocabulary_service.py::test_reschedule_remembered` — table-driven across the full 1/3/7/14/30 ladder, including floor at the last step. |
| FR-18-adjacent (forgot → resets to 1-day step, per `docs/adr/2026-07-29-vocab-forgot-resets-interval.md`) | `test_vocabulary_service.py::test_reschedule_forgot_resets_to_step_zero_from_any_step`. |
| FR-19 (last word → immediate review-complete transition) | `test_vocabulary_service.py::test_assessing_final_item_sets_session_completed_at`; `test_vocabulary_router.py::test_get_current_after_last_item_returns_complete_state`; `vocabulary-review-session.component.spec.ts` renders the Session-complete sub-view. |
| FR-20 (summary: total + forgot/remembered breakdown) | `test_vocabulary_service.py::test_review_complete_summary_tallies_match_items`; component test renders both counts. |
| FR-21 (confirms review dates were updated) | `vocabulary-review-session.component.spec.ts`: Session-complete copy asserts the update-confirmation text is present. |
| FR-22 (resume interrupted session at exact next word) | `test_vocabulary_service.py::test_resume_active_session_returns_first_unassessed_item_in_position_order` — creates a session, assesses some items, calls the resume path fresh (simulating reopen), asserts the exact next item and that already-assessed items are never re-returned. Frontend: `vocabulary.facade.spec.ts` — on load, calls `startOrResumeReview()` and renders the resumed item/position. |
| FR-23 (nothing-due state distinct from review-complete) | `test_vocabulary_router.py::test_get_current_with_zero_due_and_no_active_session_returns_nothing_due_not_complete`; `vocabulary-review-session.component.spec.ts` asserts the nothing-due and session-complete states render distinctly. |
| FR-24 (read failure during review → explicit error, never a word) | `test_vocabulary_router.py::test_get_current_db_error_returns_explicit_error_no_word_body`; `vocabulary-review-session.component.spec.ts` — Error state shown, no recall card. |

## Risks / Open Questions

- **Add-word return destination (resolved 2026-07-29).** Due List and Review Complete retain
  their exact host state. Save closes the panel and shows inline host confirmation; cancel
  closes it without navigation. Mid-session behavior continues to preserve the exact queue item.
- **Due-queue backlog cap (resolved 2026-07-29).** There is no hard cap for V1; the full
  overdue backlog is computed and shown in one queue, however large. This
  is a UX/product question, not a technical constraint: the due-summary query (`next_due_date <=
  today`) does not need to change shape to add a cap, batch, or pagination later. Risk
  accepted risk remains: a multi-day miss could produce a due count and session
  length large enough to undermine the "bounded, doable" framing the Due List wireframe is built
  around, even with the interval/topic breakdown softening the raw number.
- **"Today" / timezone determination (resolved 2026-07-29).** All Vocabulary due-date
  calculations use the learner-local calendar date in the configured IANA timezone,
  `LEARNER_TIMEZONE`, defaulting to `Asia/Ho_Chi_Minh`. A shared backend clock performs this
  conversion; deployment-server local time and raw UTC date do not define "today." Tests cover
  the UTC boundary where Ho Chi Minh City has already advanced to the next day.
- **Single active-session enforcement is a new integrity concern that didn't exist under
  IndexedDB's implicit single-tab model.** Two browser tabs (or a slow double-click on "Start
  Review") could both call `POST /review/start` concurrently. This plan relies on a partial
  unique index on `review_sessions` (`WHERE completed_at IS NULL`) plus an application-level
  check in `services/vocabulary.py` as a race-condition backstop — the second concurrent request
  should receive the same resumed session, not a duplicate. Worth an explicit concurrency test
  once the service exists; flagged rather than assumed correct by construction.
- **Vercel serverless execution model.** `docs/architecture/Architecture.md` already flags
  Vercel's per-invocation execution limits as an open risk for Epic-8 (chained external calls);
  this feature makes no external AI/Speech-to-Text calls and every request here is a single
  short-lived DB round trip, so it is not expected to be at risk — noted only so this isn't
  silently assumed safe without saying why.

## Related ADRs

- `docs/adr/2026-07-29-fullstack-vercel-claude-architecture.md`
- `docs/adr/2026-07-29-vocab-forgot-resets-interval.md` (rule unchanged; storage framing it was
  originally written against is superseded by this plan)
- `docs/adr/2026-07-29-vocab-relational-schema.md` (new — the relational table shape decided by
  this plan)
