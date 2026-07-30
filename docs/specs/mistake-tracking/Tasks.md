# Tasks: Mistake Tracking & Pattern Insight
Plan: docs/specs/mistake-tracking/ImplementationPlan.md

## Task-1 — `Mistake` SQLAlchemy model + Alembic migration
- [x] Status: Done
- Depends on: none (assumes `backend/app/core/db.py`'s declarative `Base` exists, owned by the
  access-protection epic's parallel backlog)
- Goal: Define the `Mistake` ORM model (`backend/app/models/mistake.py`) mapping the single flat
  `mistakes` table per the plan's Approach A: UUID primary key (`gen_random_uuid()` default), all
  FR-3 fields (`skill`, `question_type`, `source`, `own_answer`, `correct_answer` nullable text,
  `explanation`, `reason_category` NOT NULL defaulting to `'not_sure_other'`), and `logged_at`
  (server default now). No `learner_id`/owner column (single-learner simplification, per plan). Write
  the paired Alembic migration creating the table with an index on `logged_at` and on
  `reason_category` (supports FR-10's ordering and FR-11/FR-12's grouping). No query or business
  logic in the model itself.
- Files touched: `backend/app/models/mistake.py`, `backend/alembic/versions/<rev>_create_mistakes_table.py`,
  `backend/tests/test_mistake_model.py` (or migration test, per repo's existing migration-test convention)
- Implementation note: Added the flat UUID-backed `mistakes` model and migration `0003`, with
  database defaults and indexes for chronological and grouped reads. Real-Postgres tests verify
  schema shape and minimal-entry round-trip.
- Definition of done: a test applies the migration against a test database, asserts the `mistakes`
  table and its columns/defaults/indexes exist as specified, and that a row can be inserted with only
  `skill` and `source` set (all other columns accept NULL/default) and read back with
  `reason_category == 'not_sure_other'`. Tests pass. Supports FR-3, FR-16 (schema-level groundwork;
  not itself an FR-complete task).

## Task-2 — Full mistake-entry creation: service + schema + happy-path save (FR-1 through FR-4)
- [x] Status: Done
- Depends on: Task-1
- Goal: `schemas/mistake.py`'s `MistakeCreate`/`MistakeRead` Pydantic models (with
  `reason_category` validated against the ADR's fixed 9 string keys via `Literal`/enum) and
  `services/mistake.py`'s `create_mistake()` function, covering the full-entry save path: all FR-3
  fields accepted and persisted, and the FR-4 fixed 9-option reason-category set enforced at the
  schema layer (any other value rejected). This task covers the complete-entry case only — the
  incomplete/partial-save case is deliberately deferred to Task-3.
- Files touched: `backend/app/schemas/mistake.py`, `backend/app/services/mistake.py`,
  `backend/tests/test_mistake_service.py`
- Definition of done: unit tests (test-first) cover: creating a mistake with every FR-3 field
  populated persists all values correctly; `MistakeCreate` rejects a `reason_category` value outside
  the ADR's 9 keys. Tests pass. Definition of done references FR-1 (context-agnostic backend support;
  frontend context-trigger is Task-9), FR-3, FR-4.

## Task-3 — Incomplete-entry save (FR-5, FR-6, FR-7)
- [x] Status: Done
- Depends on: Task-2
- Goal: Extend `services/mistake.py` with `is_incomplete(mistake) -> bool`, the single function used
  everywhere completeness is reported, computed live from a row's current field values
  (`correct_answer IS NULL` or `reason_category == 'not_sure_other'`) — never stored, per the plan's
  explicit "computed, never stored" decision. Extend `MistakeRead` to include the computed
  `is_incomplete` field. Verify (via tests, not new code) that `create_mistake()` from Task-2 already
  accepts a save with only `skill` and `source` set and every other field blank/default, since no
  field in the schema is required beyond those two.
- Files touched: `backend/app/services/mistake.py`, `backend/app/schemas/mistake.py`,
  `backend/tests/test_mistake_service.py`
- Definition of done: unit tests cover: saving an entry with `correct_answer` omitted and
  `reason_category` left at its default succeeds and `is_incomplete` is `true` (FR-5); saving an
  entry with only `skill` and `source` set succeeds and `is_incomplete` is `true` (FR-6);
  `is_incomplete()` exercised against a fixture matrix — missing correct answer only, default reason
  only, both, neither — asserting the correct boolean in each case, retrievable via `MistakeRead`
  (FR-7). Tests pass.

## Task-4 — Period-scoped chronological list (FR-10, FR-14, FR-15)
- [x] Status: Done
- Depends on: Task-3
- Goal: Add `list_mistakes(start, end) -> list[Mistake]` to `services/mistake.py`, returning entries
  within `[start, end]` ordered by `logged_at` descending. This task establishes the `start`/`end`
  date-range parameter shape that grouped counts (Task-5) and category detail (Task-6) reuse; it does
  not itself decide period-boundary semantics (rolling vs. calendar week) — the service only ever
  receives concrete `start`/`end` values, per the plan's Open-Question-3 handling.
- Files touched: `backend/app/services/mistake.py`, `backend/tests/test_mistake_service.py`
- Definition of done: unit tests cover: entries outside `[start, end]` are excluded; entries inside
  the range are returned most-recent-first; a range with zero matching entries returns an empty list
  (never an error) — the empty-range case gives the eventual `GET .../mistakes` endpoint a
  well-defined re-scope response, supporting FR-15's "re-scope without a separate reload." Tests pass.
  References FR-10, FR-14 (range-acceptance groundwork; the default-period decision and reload-free
  re-render are frontend concerns finished in Task-11), FR-15.

## Task-5 — Grouped-by-reason counts via SQL GROUP BY (FR-11, FR-12)
- [x] Status: Done
- Depends on: Task-4
- Goal: Add `list_grouped_by_reason(start, end) -> list[MistakeGroupedCategory]` to
  `services/mistake.py`, using a `GROUP BY reason_category` SQL query (`SELECT reason_category,
  COUNT(*) FROM mistakes WHERE logged_at BETWEEN :start AND :end GROUP BY reason_category ORDER BY
  COUNT(*) DESC`) per the plan's Approach A — no denormalized rollup, no client-side aggregation.
  Add the `MistakeGroupedCategory` schema (`reason_category`, `count`).
- Files touched: `backend/app/schemas/mistake.py`, `backend/app/services/mistake.py`,
  `backend/tests/test_mistake_service.py`
- Definition of done: unit tests cover: a fixture set of mistakes across multiple categories within
  a date range produces correct per-category counts (FR-11); results are ordered by count descending,
  and a fixture category with a count of exactly 1 is present in the results, not truncated to a
  top-N (FR-12). Tests pass.

## Task-6 — Category drill-down with concrete examples (FR-13)
- [x] Status: Done
- Depends on: Task-5
- Goal: Add `get_category_detail(reason_category, start, end) -> list[Mistake]` to
  `services/mistake.py`, returning the individual mistakes behind one reason category for the given
  period, and the `MistakeCategoryDetail` schema (own answer, correct answer or its absence,
  explanation).
- Files touched: `backend/app/schemas/mistake.py`, `backend/app/services/mistake.py`,
  `backend/tests/test_mistake_service.py`
- Definition of done: unit test covers: for a fixture set spanning several categories, querying one
  category returns exactly the mistakes belonging to it (and none from other categories) within the
  date range, each with own answer, correct answer (or `None`), and explanation present in the
  result. Tests pass. References FR-13.

## Task-7 — API router: mistake endpoints
- [x] Status: Done
- Depends on: Task-6 (assumes `backend/app/core/security.py`'s `require_learner` exists, owned by the
  access-protection epic's parallel backlog)
- Goal: `routers/mistake.py` wiring `require_learner` + `get_db` to the service layer built in
  Tasks 2–6, with no business logic beyond request/response mapping: `POST /api/mistakes`,
  `GET /api/mistakes?start&end`, `GET /api/mistakes/grouped?start&end`,
  `GET /api/mistakes/grouped/{reason_category}?start&end`. Register the router on the app.
- Files touched: `backend/app/routers/mistake.py`, `backend/app/main.py` (router registration),
  `backend/tests/test_mistake_router.py`
- Implementation note: Added authenticated create/list/group/detail endpoints and registered auth,
  study-plan, and mistake routers on the real FastAPI app. HTTP tests verify all access boundaries,
  full and minimal creation, grouping, chronological retrieval, and category detail.
- Definition of done: integration tests (test-first, against a test DB session) cover: each of the
  four endpoints round-trips correctly end-to-end; requests without a valid learner session are
  rejected by `require_learner` on all four routes; a full create-then-list-then-group-then-detail
  sequence persists and is retrievable within one test. Tests pass. References FR-3, FR-4, FR-5,
  FR-6, FR-10, FR-11, FR-12, FR-13, FR-16 (persistence across requests against the real DB, per the
  plan's FR-16 testing strategy).

## Task-8 — Frontend: models, repository, facade (mirrors `src/app/study-plan/` pattern)
- [x] Status: Done
- Depends on: Task-7 (assumes `src/app/core/api/api-client.ts` exists, owned by the access-protection
  epic's parallel backlog)
- Goal: `models/mistake.model.ts` (`MistakeEntry` interface matching `MistakeRead`, including
  `isIncomplete` as an API-returned field, never computed client-side, per the plan; the fixed 9-key
  `ReasonCategory` union per the ADR); `models/review-period.model.ts` (`ReviewPeriod` option list,
  not a hardcoded single literal, per Open-Question-4 handling); `data/mistake.repository.ts`
  (`create()`, `listChronological(range)`, `listGrouped(range)`, `getCategoryDetail(category,
  range)` — sole point of contact with `ApiClient`); `state/mistake-period.resolver.ts` (pure
  function resolving a `ReviewPeriod` selection into concrete `{start, end}`, isolated per the plan
  so the rolling-vs-calendar-week open question stays a single-file change); `state/mistake.facade.ts`
  (view-mode, selected period, loaded entries/grouped-results as signals; orchestrates repository
  calls and re-fetches on period/view-mode change).
- Files touched: `src/app/mistakes/models/mistake.model.ts`,
  `src/app/mistakes/models/review-period.model.ts`, `src/app/mistakes/data/mistake.repository.ts`,
  `src/app/mistakes/data/mistake.repository.spec.ts`, `src/app/mistakes/state/mistake-period.resolver.ts`,
  `src/app/mistakes/state/mistake-period.resolver.spec.ts`, `src/app/mistakes/state/mistake.facade.ts`,
  `src/app/mistakes/state/mistake.facade.spec.ts`
- Implementation note: Added typed models and fixed reason labels, API mapping repository, the
  Monday-Sunday/three-preset period resolver, and a signal-based facade that refetches the active
  view when period or mode changes. Frontend suite: 55 passed.
- Definition of done: unit tests (against a fake `ApiClient`/HTTP layer, no real backend) cover:
  repository methods call the correct endpoints with correct params and map responses to
  `MistakeEntry`/grouped shapes; `mistake-period.resolver.ts` resolves a default period when no
  explicit selection has been made (FR-14); the facade re-fetches and updates its signals when the
  period or view-mode changes (FR-15). Tests pass.

## Task-9 — Frontend: logging form + in-context entry action (FR-1, FR-2, FR-3, FR-4, FR-5, FR-6, FR-8, FR-9)
- [x] Status: Done
- Depends on: Task-8
- Goal: `pages/log-entry-action/` — the contextual "Log Mistake" trigger, reading current
  study-context state to pass inferable skill/source into the form (tested against fixture contexts
  for each of the four skills, since the real host screens don't exist yet per the plan's noted
  risk). `pages/logging-form/` — the logging form per
  `docs/ux/wireframes/mistake-logging-form.md`: Sections A/B/C, the "don't have correct answer yet"
  checkbox, the reason single-select rendering exactly the 9 fixed options, and Save / Close (X) /
  Cancel actions, where Close preserves entered data as an incomplete save via
  `mistake.facade.ts`/`repository.create()`, and Cancel makes no repository call at all.
- Files touched: `src/app/mistakes/pages/log-entry-action/log-entry-action.component.ts`,
  `.html`, `.spec.ts`; `src/app/mistakes/pages/logging-form/logging-form.component.ts`, `.html`,
  `.spec.ts`
- Definition of done: component tests cover: the trigger opens the form pre-tagged with
  skill/source for each of the four skill-context fixtures, with those fields left editable, not
  disabled (FR-1, FR-2); filling every documented field and saving calls `repository.create()` with
  the full payload (FR-3); the reason-select renders exactly the 9 fixed options (FR-4); checking
  "don't have correct answer yet" and leaving reason unset allows Save with no validation error
  (FR-5); saving with only skill and source filled succeeds (FR-6); triggering Close preserves
  everything typed so far via a save call (FR-8); triggering Cancel makes no repository call (FR-9).
  Tests pass.

## Task-10 — Frontend: review screen list/grouped/category-detail view-modes (FR-7, FR-10, FR-11, FR-12, FR-13, FR-14, FR-15)
- [x] Status: Done
- Depends on: Task-9
- Goal: `pages/review-shell/` — shared chrome per `docs/ux/wireframes/mistake-review.md`: header,
  period selector (rendering from the `ReviewPeriod` option list, not a hardcoded literal), List/
  Grouped view toggle, and drill-down state, re-scoping the active view via the facade whenever the
  period changes, without a separate reload action. `pages/review-list/` — chronological list
  (Variant B), most recent first, showing date/skill/reason per row, and visually distinguishing
  complete vs. incomplete entries using the API-returned `isIncomplete` field. `pages/review-grouped/`
  — ranked reason-category list with counts (Variant A), all categories with count ≥ 1 visible.
  `pages/review-category-detail/` — example list for one selected category (Variant C): own answer,
  correct answer or its absence, explanation. `mistakes.routes.ts` wiring the logging form and
  review shell routes.
- Files touched: `src/app/mistakes/pages/review-shell/review-shell.component.ts`, `.html`, `.spec.ts`;
  `src/app/mistakes/pages/review-list/review-list.component.ts`, `.html`, `.spec.ts`;
  `src/app/mistakes/pages/review-grouped/review-grouped.component.ts`, `.html`, `.spec.ts`;
  `src/app/mistakes/pages/review-category-detail/review-category-detail.component.ts`, `.html`,
  `.spec.ts`; `src/app/mistakes/mistakes.routes.ts`, `src/app/mistakes/mistakes.routes.spec.ts`
- Definition of done: component tests cover: `review-list` renders date/skill/reason per row,
  most-recent-first, distinguishing complete vs. incomplete entries via `isIncomplete` (FR-7, FR-10);
  `review-grouped` renders counts per category from the facade's signal, ranked descending, with a
  count-of-1 category still visible (FR-11, FR-12); selecting a category from `review-grouped`
  navigates to/renders `review-category-detail` showing own answer, correct answer (or its absence),
  and explanation per example (FR-13); `review-shell` opens with the resolver's default period
  selected and its data loaded (FR-14); changing the period selector while either view is active
  triggers the facade to re-fetch and re-render that same view with no separate reload action
  (FR-15). Tests pass.
