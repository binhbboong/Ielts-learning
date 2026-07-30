# Implementation Plan: 180-Day Study Plan & Daily Execution
Spec: docs/specs/study-plan-execution/Specification.md

## Status of this revision

This plan **replaces** the prior IndexedDB-based Implementation Plan for this same epic. That
prior plan (19/19 tasks previously completed) was built against the now-superseded client-only
architecture (`docs/adr/2026-07-29-v1-no-backend-architecture.md`) and does not run against the
new full-stack architecture (`docs/adr/2026-07-29-fullstack-vercel-claude-architecture.md`,
`docs/architecture/Architecture.md`). The Specification itself (FR-1 through FR-12) is unchanged
and was verified reusable as-is. The prior data-model ADR
(`docs/adr/2026-07-29-study-plan-flat-task-store.md`) is used below only as conceptual reference
(flat task records + an explicit current-day pointer, not day-as-aggregate, not derived-current-
day) — its storage mechanism (IndexedDB) is not carried forward; the relational shape is
re-derived from first principles for Postgres in the ADR this plan produces.

## Approach

The shared architecture (Angular frontend, FastAPI backend, Neon PostgreSQL via SQLAlchemy/
Alembic, Vercel deployment) is already decided at the project level and is not reconsidered
here. What this plan owns is this epic's own table shape and its own backend/frontend layers,
built on top of the shared `backend/app/core/db.py` (`get_db`), `backend/app/core/security.py`
(`require_learner`), and `src/app/core/api/api-client.ts`, all owned by the access-protection
epic's plan.

Per the **single-learner simplification**: exactly one legitimate identity exists system-wide.
`require_learner` gates the whole router; no `learner_id`/owner column is added to any table in
this epic purely for access control.

### Table design — three approaches considered

**Approach A — Two tables, directly mirroring the prior flat-task-store model relationally
(recommended).**
- `tasks`: `id (PK, identity), day_number (int, indexed), skill (enum, 7 fixed values), title,
  description, estimated_minutes (int), status (enum: not_started/completed/skipped), note
  (text, nullable), updated_at (timestamptz)`.
- `plan_state`: a singleton table — `id (PK, fixed value 1 via CHECK (id = 1)),
  current_day_number (int), total_days (int)`. Exactly one row ever exists; enforced at the
  schema level (`CHECK (id = 1)` plus the primary key), not just by convention.
- "Day N's tasks" is `SELECT * FROM tasks WHERE day_number = :n`, a cheap indexed-column scan —
  no stored per-day aggregate.

**Approach B — `study_days` parent table + `tasks` FK to it (day-as-aggregate via a foreign
key).** The prior ADR rejected day-as-aggregate for IndexedDB because embedding tasks as an
array inside one day *document* turned every single-task edit into a read-modify-write of the
whole array. **That specific cost does not carry over to a relational database**: with a
`study_days(id, day_number)` parent and `tasks.day_id` as a foreign key, a single task UPDATE is
still a single-row UPDATE regardless of whether `day_number` is a plain int or a foreign key —
Postgres never requires touching sibling rows to update one row. So Approach B is not rejected on
the old grounds; it is rejected here on different, relational-specific grounds: it buys FK
referential integrity (a task's day_id is guaranteed to reference a real day; `plan_state`'s
current-day pointer could be a FK too) and a natural home for future day-level attributes (e.g. a
day theme), at the cost of an extra table, an extra join on every day-level read, two identity
concepts to keep straight (`day_number` vs internal `day_id`), and 180 extra seed rows to
manage — for zero present benefit, since no FR needs a day-level attribute beyond `day_number`
(which Approach A already carries on `tasks`) and the spec's Out of Scope explicitly excludes
learner-authored days or task-to-day reassignment (so the integrity risk Approach A accepts —
`tasks.day_number` and `plan_state.current_day_number` are plain ints, not FK-enforced — is
low: both are set once by the seed script and never touched by any user-facing mutation).
**Not recommended now**, but not dismissed by restating the old IndexedDB argument uncritically —
see the ADR for the full reasoning and the migration path if a future epic needs day-level
attributes.

**Approach C — Track `current_day_number` in a shared generic key-value/config table instead of
a dedicated `plan_state` table.** Rejected: no such shared config table exists in
`docs/architecture/Architecture.md`, and inventing one here would couple this epic's migration to
a cross-epic concern outside its ownership. Each epic owns its own tables and its own migration
(per the shared conventions); a small singleton table this epic fully owns is simpler and keeps
that boundary clean.

**Recommendation: Approach A.** It satisfies every FR with the fewest moving parts, keeps this
epic's migration self-contained (two tables, one migration file), and does not build relational
integrity machinery (Approach B) that no current requirement exercises. This is a data-model
decision other code will plausibly depend on later (a future dashboard aggregation, Epic-5's data
export reading across this epic's tables), so it is recorded as its own ADR — see
`docs/adr/2026-07-29-study-plan-relational-task-store.md` (Related ADRs below). That ADR
explicitly does not "supersede" the old IndexedDB ADR (different storage technology, not a
revision of the same decision) — it references it as superseded-in-spirit context only.

`skill` and `status` are modeled as native Postgres enums (via SQLAlchemy `Enum`), not free-text
CHECK-constrained strings, because their value sets are fixed by the spec (Out of Scope excludes
adding new skills) and DB-level enforcement is worth the (rare, spec-excluded) cost of an
`ALTER TYPE` migration if that ever changes.

### Frontend reuse assessment

`src/app/study-plan/` already exists in this exact folder shape (`models/`, `data/`, `state/`,
`pages/daily-checklist/`, `pages/task-detail/`, `pages/day-history/`, `study-plan.routes.ts`)
from the prior IndexedDB implementation. Assessed reuse, file by file:

- **Reusable almost as-is (components + routing, ~6 files):** `pages/daily-checklist/*`,
  `pages/task-detail/*`, `pages/day-history/*`, `study-plan.routes.ts`. None of these ever called
  IndexedDB directly — they call `StudyPlanFacade` only, and the facade's public method names
  (`setStatus`, `updateNote`, `updateTaskDetails`, `moveToNextDay`, `getHistoryForDay`,
  `getTaskById`) are preserved unchanged below. Expect near-zero logic changes; re-verify their
  existing `.spec.ts` files still pass once the facade is rewired, rather than rewriting them.
- **Facade — same public API, small internal rewrite (`state/study-plan.facade.ts`):** method
  signatures stay the same, but the *internals* change in one real way: the prior facade did
  read-the-whole-task/merge-one-field/re-save-the-whole-task for every mutation (`setStatus`,
  `updateNote`, `updateTaskDetails` all funneled through a generic `repository.saveTask()`). That
  pattern existed to fit IndexedDB's single-record-put model; against a REST API it is replaced
  with targeted calls to three separate repository methods (matching three separate PATCH
  endpoints — see below), each a direct pass-through instead of a get-then-merge. This is a
  genuine, small internal change, not a pure swap — flagged here rather than assumed silent.
- **Not reusable — deleted or replaced:**
  - `data/study-plan-seed.ts` (removed entirely). The 180-day/task seed content moves server-side
    (`backend/app/db/seed_study_plan.py`) since the backend now owns persistence; shipping seed
    content in the Angular bundle no longer makes sense.
  - `data/study-plan.repository.ts` (rewritten). Same file path and role (sole point of contact
    for this module's data access), but internals become HTTP calls through
    `src/app/core/api/api-client.ts` instead of IndexedDB calls, against the endpoints listed
    below.
  - `models/task.model.ts`, `models/plan-state.model.ts` (small edits, not rewrites): `Task.id`
    changes from a client-generated `string` to a backend-assigned `number` (Postgres identity
    column), and `estimatedMinutes`/`updatedAt`-style camelCase fields are mapped from the
    backend's snake_case JSON by the repository, not the models themselves.

Net assessment: **the majority of the UI layer (3 page components + routing + most facade logic)
carries forward with minimal or no change; the swap is concentrated in the repository and the
seed content, exactly as the epic's file-structure ownership already separates them.**

## File/Module Structure

### Backend

| Path | Responsibility | Implements (wireframe, if UI-facing) |
|------|-----------------|-----------------|
| `backend/app/models/study_plan.py` | SQLAlchemy ORM models: `Task` and `PlanState` (the singleton row), matching Approach A's shape. No business logic. | — |
| `backend/app/schemas/study_plan.py` | Pydantic request/response schemas: `TaskOut`, `PlanStateOut`, `TaskStatusUpdate`, `TaskNoteUpdate`, `TaskDetailsUpdate`, `MoveToNextDayResult`. Contracts only, no logic. | — |
| `backend/app/services/study_plan.py` | All business logic: `get_plan_state()`, `get_tasks_for_day(day_number)`, `get_task(task_id)`, `set_task_status(task_id, status)`, `update_task_note(task_id, note)`, `update_task_details(task_id, description, estimated_minutes)`, `move_to_next_day()` (enforces the FR-7/FR-8 gate: blocks with the unresolved task ids while any current-day task is `not_started`, else advances `plan_state.current_day_number`). No FastAPI/HTTP concerns, no direct SQL outside the ORM. | — |
| `backend/app/routers/study_plan.py` | FastAPI router, depends on `require_learner` + `get_db`; translates HTTP requests to service calls and service results to HTTP responses/status codes. No business logic of its own. Routes: `GET /study-plan/state`, `GET /study-plan/days/{day_number}/tasks`, `GET /study-plan/tasks/{task_id}`, `PATCH /study-plan/tasks/{task_id}/status`, `PATCH /study-plan/tasks/{task_id}/note`, `PATCH /study-plan/tasks/{task_id}`, `POST /study-plan/move-to-next-day`. | — |
| `backend/app/db/seed_study_plan.py` | Holds the pre-loaded 180-day/task content (FR-1) and an idempotent `seed_if_empty(session)` function — inserts the 180-day plan plus the initial `plan_state` row only if the `tasks` table is empty; a no-op on every later call. | — |
| `backend/alembic/versions/xxxx_create_study_plan_tables.py` | Migration creating `tasks` and `plan_state` (with the `CHECK (id = 1)` singleton constraint), the `day_number` index, and the `skill`/`status` Postgres enum types. | — |

### Frontend

| Path | Responsibility | Implements (wireframe) |
|------|-----------------|-----------------|
| `src/app/study-plan/models/task.model.ts` | `Task`/`TaskStatus`/`Skill` TypeScript types (id now `number`). Types only. | — |
| `src/app/study-plan/models/plan-state.model.ts` | `PlanState` type (`currentDayNumber`, `totalDays`). Types only. | — |
| `src/app/study-plan/data/study-plan.repository.ts` | Sole point of contact with the backend REST API for this module (via `ApiClient`): `getPlanState()`, `getTasksForDay(dayNumber)`, `getTask(id)`, `updateTaskStatus(id, status)`, `updateTaskNote(id, note)`, `updateTaskDetails(id, details)`, `moveToNextDay()`. Owns the camelCase ⇄ snake_case field mapping at the HTTP boundary. No seeding responsibility (seeding is server-side now). | — |
| `src/app/study-plan/state/study-plan.facade.ts` | Holds current-day task state and `currentDayNumber` as signals; exposes `setStatus`, `updateNote`, `updateTaskDetails`, `moveToNextDay()`, `getHistoryForDay(dayNumber)`, `getTaskById(id)` — unchanged public API from the prior implementation, internals call the targeted repository methods above instead of a generic save. | — |
| `src/app/study-plan/pages/daily-checklist/daily-checklist.component.ts` | Renders the current day's task list, progress count, per-task status controls, and the Move-to-Next-Day action/blocked-reason. Reused near-as-is. | `docs/ux/wireframes/daily-checklist.md` |
| `src/app/study-plan/pages/task-detail/task-detail.component.ts` | Renders and edits one task's status, description, estimated time, and note, with Save/Cancel. Reused near-as-is. | `docs/ux/wireframes/task-detail.md` |
| `src/app/study-plan/pages/day-history/day-history.component.ts` | Renders the day selector and the selected past day's read-only task list. Reused near-as-is. | `docs/ux/wireframes/day-history.md` |
| `src/app/study-plan/study-plan.routes.ts` | Declares the module's routes (Daily Checklist, Task Detail, Day History) for mounting into the App Shell. Reused unchanged. | — |

## Testing Strategy

Per Constitution principle 2 (tests before code): every row below is written and fails before
the corresponding backend/frontend code exists, per the `test-driven-development` skill. Backend
tests run against a real test Postgres database (not SQLite), since the design relies on
Postgres-native enum types and a `CHECK` constraint that a lighter-weight substitute would not
faithfully exercise — the concrete test-DB provisioning mechanism (e.g. a Neon test branch or
`testcontainers-python`) is shared infrastructure and not decided by this plan (see Risks).

| Requirement | Backend verification | Frontend verification |
|---|---|---|
| FR-1 (pre-loaded 180-day plan, every task tagged with exactly one of the 7 skills) | `test_seed_study_plan.py`: after `seed_if_empty()`, asserts 180 distinct `day_number` values exist and every task's `skill` is one of the 7 allowed enum values; asserts calling it twice does not duplicate rows. | — (content is server-side; no frontend seed test remains) |
| FR-2 (display current day's tasks + status) | `test_study_plan_router.py`: `GET /study-plan/state` then `GET /study-plan/days/{n}/tasks` for the current day returns the right tasks with status. | `daily-checklist.component.spec.ts`: given a facade stub returning N tasks for the current day, all N render with correct skill tag and status. |
| FR-3 (set Completed/Skipped, revert to Not Started) | `test_study_plan_service.py`: `set_task_status()` transitions through all three states and persists; `test_study_plan_router.py`: `PATCH /tasks/{id}/status` round-trips. | `study-plan.facade.spec.ts`: `setStatus()` calls `repository.updateTaskStatus` and refreshes state; component test that each status control invokes `setStatus` with the expected task id/value. |
| FR-4 (add/edit a free-text note) | `test_study_plan_service.py` + router test for `PATCH /tasks/{id}/note`. | `task-detail.component.spec.ts`: editing the note field then Save calls `facade.updateNote(taskId, text)`. |
| FR-5 (edit description and estimated time) | `test_study_plan_service.py` + router test for `PATCH /tasks/{id}`. | `task-detail.component.spec.ts`: editing description/time then Save calls `facade.updateTaskDetails(...)`; values round-trip on reload. |
| FR-6 (no automatic day advance) | `test_study_plan_service.py`: asserts `plan_state.current_day_number` is unchanged after `set_task_status`/`update_task_note`/`update_task_details` — only `move_to_next_day()` may change it. | `study-plan.facade.spec.ts`: same assertion at the facade level (mirrors backend intent, guards against a future facade regression). |
| FR-7 (block move-to-next-day while any task Not Started, with feedback) | `test_study_plan_service.py`: `move_to_next_day()` returns a blocked result naming unresolved task ids when ≥1 task is `not_started`; router test asserts the corresponding HTTP response (e.g. 409 + body). | `daily-checklist.component.spec.ts`: the blocked-reason message renders from the facade's result. |
| FR-8 (move-to-next-day succeeds once all resolved) | `test_study_plan_service.py`: succeeds once every current-day task is Completed/Skipped; `current_day_number` increments and is persisted (re-read via a fresh DB query). | `study-plan.facade.spec.ts`: `currentDayNumber` signal updates after a successful `moveToNextDay()`. |
| FR-9 (completed/total count updates immediately) | — (server has no "immediacy" concept; covered by FR-3's persistence test) | `daily-checklist.component.spec.ts`: after a simulated status change resolves through the facade, the rendered count reflects the new total without a manual reload. |
| FR-10 (view a previous day's tasks, read-only) | `test_study_plan_router.py`: `GET /study-plan/days/{n}/tasks` for `n < current_day_number` returns that day's tasks; no mutation route accepts a day number, only a task id, so past-day tasks are reachable for reading only through this router shape. | `day-history.component.spec.ts`: requesting day N < current returns that day's tasks; the screen exposes no mutation controls for them. |
| FR-11 (all plan/task state persists across sessions) | `test_study_plan_integration.py`: write task and `plan_state` rows through the service in one test-DB session, open a fresh session (simulating a new request/"session"), confirm identical state reads back — persistence is now inherent to Postgres rather than a thing this epic implements, but the round-trip is still verified end-to-end. | Repository test with `HttpClient` mocked: confirms the repository issues the expected requests and maps responses back into the facade's state shape; no frontend-owned persistence exists anymore (that responsibility moved server-side). |
| FR-12 (past-day history editability — NEEDS CLARIFICATION) | Not verifiable — requirement unresolved. No test written. Day History stays read-only, matching the prior implementation's decision (see Risks). | Same — no write controls are built into `day-history.component.ts`. |

## Constitution check

- **Tests-first (principle 2):** every row above is written and confirmed failing before its
  implementation exists — backend model/service/router tests against a real test Postgres
  database, frontend facade/component tests in the same shape as the prior (superseded)
  implementation's tests. No exception requested.
- **Principle 1 (upstream docs are the contract):** this plan does not silently diverge from the
  Specification (FR-1–FR-12 reused verbatim) or from `docs/architecture/Architecture.md`
  (FastAPI/SQLAlchemy/Postgres, `require_learner`-gated router, no per-table `learner_id`). FR-12
  remains open and is not silently resolved here, per the task's explicit instruction.
- **Principle 6 (docs are durable):** this plan overwrites the prior (stale, IndexedDB-based)
  `ImplementationPlan.md` for this same epic as an intentional, explicit rewrite following the
  architecture pivot — not a silent drift; the ADR below is additive, not a rewrite of the old
  IndexedDB ADR.

## Risks / Open Questions

- **FR-12 is still unresolved** (whether a past day's task status/note is ever editable after the
  day advances). Not resolved here, per instruction. The relational model does not foreclose
  either answer: because tasks are addressed by their own `id` (not nested inside an immutable
  per-day document or locked by a day-level status), enabling `PATCH` on a past day's task later
  is a router/service change (drop the "current day only" assumption those endpoints don't
  actually enforce today, since `PATCH /tasks/{id}` takes a task id, not a day) plus a UI change
  (adding controls to Day History) — not a schema rewrite.
- **Test-database provisioning is a shared-infra dependency, not owned by this plan.** This plan
  assumes a pytest fixture provides a real Postgres test database (matching `backend/app/core/
  db.py`'s engine, owned by the access-protection epic's plan) so that native enum/`CHECK`
  behavior is exercised faithfully. The concrete mechanism (Neon branch, Docker/testcontainers,
  etc.) is not decided here.
- **Seed timing is not fully pinned down.** `seed_if_empty()` needs to run once against a fresh
  database (e.g., on backend startup, or as a one-off ops script/Alembic data migration invoked
  after the schema migration). This plan assumes it is safe to call idempotently and leaves the
  exact invocation point (startup hook vs. manual script) to task breakdown, since either
  satisfies FR-1 without changing the function's contract.
- **Content authoring risk carries over unchanged from the prior plan**: FR-1 requires actual
  180-day/task plan content, which is a content task, not just code — `seed_study_plan.py` cannot
  be meaningfully verified end-to-end until that content exists.
- **`day_number`/`current_day_number` are plain integers, not FK-enforced** (Approach A, accepted
  cost — see the ADR). This is safe under the spec's current Out-of-Scope guarantees (no
  learner-authored days, no day reassignment); if a future epic needs those guarantees enforced
  at the schema level, migrating to Approach B (`study_days` + FK) is additive, not a rewrite of
  task identity.
- **Vercel serverless execution limits** (flagged generally in `docs/architecture/Architecture.md`
  Known Constraints) are a low risk for this epic specifically — all endpoints here are simple
  CRUD/read operations with no chained external calls, unlike Writing/Speaking evaluation.

## Related ADRs

- `docs/adr/2026-07-29-study-plan-relational-task-store.md` (new — this plan's table-design
  decision)
- `docs/adr/2026-07-29-study-plan-flat-task-store.md` (prior, IndexedDB-specific decision — kept
  for conceptual history, referenced but not superseded by the new ADR, since it addresses a
  different storage technology, not a revision of the same one)
- `docs/adr/2026-07-29-fullstack-vercel-claude-architecture.md` (governing architecture)
