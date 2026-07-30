# Tasks: 180-Day Study Plan & Daily Execution
Plan: docs/specs/study-plan-execution/ImplementationPlan.md

## Status of this revision

This backlog **replaces** the prior `Tasks.md` for this epic (19/19 tasks previously completed
against the now-superseded IndexedDB architecture — see
`docs/adr/2026-07-29-study-plan-flat-task-store.md`). It is re-derived from the new
`ImplementationPlan.md` (Postgres/FastAPI backend, Approach A two-table shape) and the new ADR
`docs/adr/2026-07-29-study-plan-relational-task-store.md`. The Specification (FR-1–FR-12) is
unchanged; FR-12 remains `[NEEDS CLARIFICATION]` and is deliberately not implemented by any task
below, exactly as in the prior backlog.

**Frontend reuse, confirmed against the actual files in `src/app/study-plan/`:**
- **Reusable unmodified (verify existing tests still pass, no source changes expected):**
  `pages/daily-checklist/daily-checklist.component.ts/.html` +
  `daily-checklist.component.spec.ts`; `pages/task-detail/task-detail.component.ts/.html` +
  `task-detail.component.spec.ts`; `pages/day-history/day-history.component.ts/.html` +
  `day-history.component.spec.ts`; `study-plan.routes.ts` + `study-plan.routes.spec.ts`. Confirmed
  by reading these files: all three components and the routing spec depend only on
  `StudyPlanFacade`'s public signals/methods (`tasks`, `currentDayNumber`, `loadCurrentDay`,
  `setStatus`, `updateNote`, `updateTaskDetails`, `moveToNextDay`, `getHistoryForDay`,
  `getTaskById`) via a facade stub — none reference `StudyPlanRepository` or IndexedDB directly.
- **Small internal rewrite, same public API (`state/study-plan.facade.ts` +
  `study-plan.facade.spec.ts`):** confirmed the current facade funnels every mutation through a
  generic `repository.saveTask()` (read-modify-write) and `repository.savePlanState()`. This
  becomes targeted calls to the new repository's per-field methods. Method signatures on the
  facade itself do not change, so callers (the 3 components) are unaffected — but
  `facade.spec.ts`'s repository spies (currently `saveTask`/`getTask`/`savePlanState`) must be
  updated to the new method names, per the Implementation Plan's explicit flag that this is "a
  genuine, small internal change, not a pure swap."
- **Not reusable — replaced or deleted:** `data/study-plan.repository.ts` (rewritten: IndexedDB →
  HTTP via `ApiClient`) and its test file `data/study-plan.repository.spec.ts` (**replaced**, not
  extended — the new tests mock HTTP responses, not `indexedDB.deleteDatabase`); `data/
  study-plan-seed.ts` + `data/study-plan-seed.spec.ts` (**deleted** — seed content moves to
  `backend/app/db/seed_study_plan.py`); `models/task.model.ts` (small edit: `id: string` →
  `id: number`).

## Task-1 — Backend: `Task`/`PlanState` SQLAlchemy models + Alembic migration
- [x] Status: Done
- Depends on: none (assumes `backend/app/core/db.py`'s SQLAlchemy `Base`/engine exists, owned by
  the access-protection epic's backlog, built in parallel)
- Goal: Define the `Task` and `PlanState` ORM models per Approach A (`docs/adr/
  2026-07-29-study-plan-relational-task-store.md`) — `tasks(id, day_number, skill enum, title,
  description, estimated_minutes, status enum, note, updated_at)` and `plan_state(id CHECK (id=1),
  current_day_number, total_days)` — and the Alembic migration that creates both tables, the
  `skill`/`status` Postgres enum types, the `day_number` index, and the singleton `CHECK`
  constraint. No business logic in this task.
- Files touched: `backend/app/models/study_plan.py`, `backend/alembic/versions/
  xxxx_create_study_plan_tables.py`, `backend/tests/test_study_plan_models.py`
- Implementation note: Added native Postgres skill/status enums, relational `tasks` and singleton `plan_state` models, migration `0002`, Alembic metadata registration, and three real-Postgres tests. Full backend suite: 43 passed.
- Definition of done: `test_study_plan_models.py` passes against a real test Postgres database —
  asserts the migration creates both tables with the expected columns/enum types, that inserting a
  second `plan_state` row (any `id`, including `id != 1`) violates the `CHECK`/PK constraint, and
  that a `Task`/`PlanState` row written via the ORM round-trips unchanged on read. This is the
  persistence foundation FR-1 (pre-loaded plan storage) and FR-11 (cross-session persistence)
  depend on; no other FR is directly verifiable at this layer.

## Task-2 — Backend: seed mechanism for the 180-day plan content
- [x] Status: Done
- Depends on: Task-1
- Goal: Author the pre-loaded 180-day/task content and an idempotent `seed_if_empty(session)`
  function that inserts all 180 days of tasks plus the initial `plan_state` row
  (`current_day_number=1, total_days=180`) only when the `tasks` table is empty; a no-op on every
  later call. This replaces `src/app/study-plan/data/study-plan-seed.ts`, which is deleted in
  Task-6.
- Files touched: `backend/app/db/seed_study_plan.py`, `backend/tests/test_seed_study_plan.py`
- Implementation note: Ported the existing seven-skills-per-day seed to Postgres for all 180 days, added an idempotent `seed_if_empty`, and verified state preservation on repeat calls. Full backend suite: 45 passed.
- Definition of done: `test_seed_study_plan.py` passes against a real test Postgres database —
  asserts that after `seed_if_empty()`, exactly 180 distinct `day_number` values exist and every
  task's `skill` is one of the 7 allowed enum values, and that calling `seed_if_empty()` a second
  time does not duplicate rows or change `plan_state` — covers FR-1.

## Task-3 — Backend: Pydantic schemas + service read/mutate CRUD
- [x] Status: Done
- Depends on: Task-1
- Goal: Define response/request schemas (`TaskOut`, `PlanStateOut`, `TaskStatusUpdate`,
  `TaskNoteUpdate`, `TaskDetailsUpdate`) and the service functions `get_plan_state()`,
  `get_tasks_for_day(day_number)`, `get_task(task_id)`, `set_task_status(task_id, status)`,
  `update_task_note(task_id, note)`, `update_task_details(task_id, description,
  estimated_minutes)`. No FastAPI/HTTP concerns here (router comes in Task-5); no
  move-to-next-day gate logic here (that's Task-4).
- Files touched: `backend/app/schemas/study_plan.py`, `backend/app/services/study_plan.py`,
  `backend/tests/test_study_plan_service.py`
- Implementation note: Added typed Pydantic request/response contracts and real-Postgres service
  CRUD for plan state, day/task reads, status transitions, notes, and task details. Mutations
  update `updated_at` while leaving `plan_state.current_day_number` unchanged.
- Definition of done: `test_study_plan_service.py` passes against a real test Postgres database —
  asserts `get_plan_state()`/`get_tasks_for_day(n)` return correct data (FR-2, FR-10 for `n <
  current_day_number`); `set_task_status()` transitions a task through Not Started → Completed →
  Skipped → Not Started and persists each transition (FR-3); `update_task_note()` persists a
  free-text note (FR-4); `update_task_details()` persists edited description/estimated minutes
  (FR-5); and that none of these three mutation functions change `plan_state.current_day_number`
  (FR-6).

## Task-4 — Backend: `move_to_next_day()` gate and advance logic
- [x] Status: Done
- Depends on: Task-3
- Goal: Implement `move_to_next_day()` in `backend/app/services/study_plan.py`: return a blocked
  result naming the unresolved task ids when any current-day task is `not_started`; otherwise
  increment and persist `plan_state.current_day_number`.
- Files touched: `backend/app/services/study_plan.py`, `backend/tests/test_study_plan_service.py`
- Implementation note: Added a typed move result, deterministic unresolved-task reporting, and
  persisted day advancement only when every current-day task is completed or skipped. A fresh
  database session verifies the advance and continued readability of the previous day's tasks.
- Definition of done: `test_study_plan_service.py` passes — asserts (a) `move_to_next_day()`
  returns a blocked result naming the unresolved task id(s) when ≥1 current-day task is
  `not_started`, and `current_day_number` is unchanged (FR-7); (b) `move_to_next_day()` succeeds
  and increments/persists `current_day_number` once every current-day task is `completed` or
  `skipped`, verified by re-reading `plan_state` in a fresh DB session (FR-8, FR-11); (c) the
  underlying day's tasks (now on a past day) remain readable but no code path here mutates them
  (supports FR-6).

## Task-5 — Backend: FastAPI router and endpoint wiring
- [x] Status: Done
- Depends on: Task-3, Task-4 (assumes `backend/app/core/security.py`'s `require_learner` and
  `backend/app/core/db.py`'s `get_db` exist, owned by the access-protection epic's backlog, built
  in parallel)
- Goal: Wire `GET /study-plan/state`, `GET /study-plan/days/{day_number}/tasks`, `GET
  /study-plan/tasks/{task_id}`, `PATCH /study-plan/tasks/{task_id}/status`, `PATCH
  /study-plan/tasks/{task_id}/note`, `PATCH /study-plan/tasks/{task_id}`, `POST
  /study-plan/move-to-next-day` to the Task-3/Task-4 service functions, gated by `require_learner`.
  No business logic of its own — translates HTTP ⇄ service calls/results only.
- Files touched: `backend/app/routers/study_plan.py`, `backend/tests/test_study_plan_router.py`
- Implementation note: Added authenticated `/api/study-plan` read and mutation endpoints,
  Pydantic response serialization, not-found handling, and a 409 response carrying unresolved
  task ids. Real-Postgres HTTP tests cover authentication, past/current reads, every mutation,
  blocked movement, and successful advancement.
- Definition of done: `test_study_plan_router.py` passes against a real test Postgres database and
  a test HTTP client — round-trips each endpoint (FR-2 via `GET .../tasks`; FR-3 via `PATCH
  .../status`; FR-4 via `PATCH .../note`; FR-5 via `PATCH .../tasks/{id}`; FR-7 via `POST
  .../move-to-next-day` returning a 409-or-equivalent with unresolved task ids when blocked; FR-8
  via the same endpoint succeeding and returning the advanced day; FR-10 via `GET
  .../days/{n}/tasks` for `n < current_day_number`); asserts an unauthenticated request is
  rejected by `require_learner`.

## Task-6 — Frontend: rewrite `study-plan.repository.ts` internals to call the new API
- [x] Status: Done
- Depends on: Task-5 (assumes `src/app/core/api/api-client.ts` exists, owned by the
  access-protection epic's backlog, built in parallel)
- Goal: Replace `StudyPlanRepository`'s IndexedDB calls with HTTP calls through `ApiClient` against
  the Task-5 endpoints — `getPlanState()`, `getTasksForDay(dayNumber)`, `getTask(id)`,
  `updateTaskStatus(id, status)`, `updateTaskNote(id, note)`, `updateTaskDetails(id, details)`,
  `moveToNextDay()` — owning the camelCase ⇄ snake_case field mapping at the HTTP boundary. Update
  `Task.id` in `models/task.model.ts` from `string` to `number`. Delete `data/study-plan-seed.ts`
  (content now lives server-side per Task-2) and its spec file. **This task replaces
  `data/study-plan.repository.spec.ts` wholesale** — the new spec mocks `HttpClient`/`ApiClient`
  responses; it does not extend or reuse the old IndexedDB-based spec (which tested
  `indexedDB.deleteDatabase`, `LocalDataLayerService`, and `ensureSeeded()`, none of which exist in
  the new repository — `ensureSeeded()` is removed since seeding is server-side now).
- Files touched: `src/app/study-plan/data/study-plan.repository.ts`, `src/app/study-plan/data/
  study-plan.repository.spec.ts` (replaced), `src/app/study-plan/models/task.model.ts`; deleted:
  `src/app/study-plan/data/study-plan-seed.ts`, `src/app/study-plan/data/study-plan-seed.spec.ts`
- Definition of done: the new `study-plan.repository.spec.ts` passes — with `HttpClient` mocked,
  asserts each repository method issues the expected request and maps the response back into the
  frontend's camelCase shape, for `getPlanState`/`getTasksForDay`/`getTask` (FR-2, FR-10),
  `updateTaskStatus` (FR-3), `updateTaskNote` (FR-4), `updateTaskDetails` (FR-5), and
  `moveToNextDay` (FR-7, FR-8) — covers the frontend half of FR-11 (no client-owned persistence
  remains; the repository is a thin, verifiably-correct HTTP mapping layer).

## Task-7 — Frontend: rewire `study-plan.facade.ts` internals to the new repository methods
- [x] Status: Done
- Depends on: Task-6
- Goal: Replace the facade's generic get-then-`saveTask()`/`savePlanState()` calls with direct
  calls to the new repository's targeted methods (`updateTaskStatus`, `updateTaskNote`,
  `updateTaskDetails`, `moveToNextDay`) — a pass-through instead of a read-modify-write. Public
  method signatures (`setStatus`, `updateNote`, `updateTaskDetails`, `moveToNextDay`,
  `getHistoryForDay`, `getTaskById`) and the `tasks`/`currentDayNumber` signals are unchanged, so
  no caller outside this file is touched by this task.
- Files touched: `src/app/study-plan/state/study-plan.facade.ts`, `src/app/study-plan/state/
  study-plan.facade.spec.ts`
- Definition of done: `study-plan.facade.spec.ts` passes with its repository spy updated to mock
  the new method names (`updateTaskStatus`/`updateTaskNote`/`updateTaskDetails`/`moveToNextDay`
  instead of `saveTask`/`savePlanState`; `ensureSeeded` spy removed) while preserving the same
  behavioral assertions as the prior file: reading the current day (FR-2), `setStatus` transitions
  and persistence without changing `currentDayNumber` (FR-3, FR-6), `updateNote` persistence
  (FR-4, FR-6), `updateTaskDetails` persistence (FR-5, FR-6), `moveToNextDay`'s blocked result and
  successful advance (FR-7, FR-8), and `getHistoryForDay`/`getTaskById` (FR-10).

## Task-8 — Frontend: verify the 3 existing page components pass unmodified
- [x] Status: Done
- Depends on: Task-7
- Goal: Run the existing component test suites with no source changes to the components
  themselves, confirming the Implementation Plan's reuse assessment holds now that the facade's
  internals (not its public API) have changed underneath them. If a test fails, fix only what's
  necessary to restore the pre-existing behavior — do not add new features.
- Files touched (verification only, no source changes expected): `src/app/study-plan/pages/
  daily-checklist/daily-checklist.component.spec.ts`, `src/app/study-plan/pages/task-detail/
  task-detail.component.spec.ts`, `src/app/study-plan/pages/day-history/
  day-history.component.spec.ts`
- Definition of done: all three prior spec files pass unmodified (or, if the plan's anticipated
  facade-internal change leaks through, with only the minimal changes needed to keep their
  existing assertions true — no new test cases). Coverage carried forward unchanged: Daily
  Checklist renders tasks/skill tags/status and the completed/total count (FR-2, FR-9), status
  controls call `facade.setStatus` and the count updates synchronously (FR-3, FR-9), and the
  move-to-next-day action renders the blocked reason or the advanced day (FR-6, FR-7, FR-8); Task
  Detail renders and edits note (FR-4), description/estimated time (FR-5), and status (FR-3); Day
  History renders a past day's tasks read-only with no mutation controls (FR-10).

## Task-9 — Frontend: verify/adjust routing and nav wiring
- [x] Status: Done
- Depends on: Task-8
- Goal: Confirm `study-plan.routes.ts` (default route → Daily Checklist, `task/:taskId` → Task
  Detail with `taskResolver`, `history` → Day History) and its mount into `app.routes.ts` /
  shared nav ("Today"/"History" entries) still resolve correctly now that the facade/repository
  underneath have changed. Adjust only if the access-protection epic's route guard (parallel work)
  requires wrapping these routes — no other change expected.
- Files touched (verification, adjust only if needed): `src/app/study-plan/study-plan.routes.ts`,
  `src/app/study-plan/study-plan.routes.spec.ts`, `src/app/app.routes.ts`
- Definition of done: `study-plan.routes.spec.ts` passes unmodified (or with only an auth-guard
  provider added if required by the parallel access-protection epic) — asserts `/` resolves to
  `DailyChecklistComponent`, `/task/:taskId` resolves to `TaskDetailComponent`, and `/history`
  resolves to `DayHistoryComponent` — supports the FR-2/FR-10 acceptance criteria that the learner
  reaches the current day's task list on load and can reach previous-day history.

## Task-10 — Full-cycle persistence integration test against the real backend + DB
- [x] Status: Done
- Depends on: Task-2, Task-4, Task-5 (equivalent in intent to the prior architecture's Task-19,
  which verified full-cycle persistence against fake-IndexedDB; this is the full-stack
  replacement, verifying the same guarantee against the real backend/DB stack this epic now owns)
- Goal: Verify that a realistic sequence of state changes — a status edit, a note edit, a
  description/estimated-time edit, and one successful `move_to_next_day()` advance — all persist
  through the service layer against a real test Postgres database, and are read back identically
  by a fresh DB session (simulating a new request after a server restart).
- Files touched: `backend/tests/test_study_plan_integration.py`
- Implementation note: Added a real-Postgres full-cycle test that performs all edit types and a
  successful day advance in one session, then verifies the exact task and plan state from a fresh
  session. Full backend suite: 54 passed.
- Definition of done: `test_study_plan_integration.py` passes — after performing the sequence
  above through `backend/app/services/study_plan.py` in one session, a fresh session against the
  same test database reads back the edited task's status/note/description/estimated_minutes and
  `plan_state.current_day_number` identical to what was written — covers FR-11 end-to-end (this
  epic's full persistence guarantee, now inherent to Postgres rather than client-implemented).

## Notes
- FR-12 (past-day editability) is intentionally not implemented by any task above — it remains
  `[NEEDS CLARIFICATION]` per the Specification. No mutation endpoint or UI control admits a
  day-number scope beyond what FR-3/FR-4/FR-5 already allow via task id, and Day History
  (Task-8/Task-9) stays strictly read-only, matching the prior implementation's decision. No task
  should be picked up to add editing to Day History until FR-12 is resolved and the
  Specification/Plan are updated accordingly (Constitution principle 1).
- Test-database provisioning (a real Postgres test DB for Tasks 1–5 and 10, matching `backend/
  app/core/db.py`'s engine) is a shared-infrastructure dependency owned outside this epic's
  backlog, per the Implementation Plan's Risks section — assumed available, not built here.
