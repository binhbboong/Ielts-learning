# ADR: Study Plan Data Modeled as Two Postgres Tables — Flat `tasks` + Singleton `plan_state`

Date: 2026-07-29
Slug: study-plan-relational-task-store
Status: Superseded by 2026-07-30-daily-lesson-plan-data-model
Related spec: docs/specs/study-plan-execution/Specification.md (superseded — see docs/specs/daily-lesson-plan/Specification.md)

## Context

The project has moved from a client-only, IndexedDB-backed architecture to a full-stack one
(`docs/adr/2026-07-29-fullstack-vercel-claude-architecture.md`): Angular frontend, FastAPI
backend, Neon PostgreSQL via SQLAlchemy/Alembic. The Study Plan module
(`docs/architecture/Architecture.md`) owns the 180-day plan structure, daily task assignment, and
completion state. The Specification (`docs/specs/study-plan-execution/Specification.md`) is
unchanged and still requires per-task editing (status, note, description, estimated time — FR-3
through FR-5), a completed/total count that updates immediately (FR-9), read-only browsing of
past days (FR-10), and — critically — that the current day never advances except through an
explicit learner action (FR-6, FR-7, FR-8), which rules out deriving "current day" from task
completion state.

A prior ADR (`docs/adr/2026-07-29-study-plan-flat-task-store.md`) made an equivalent decision for
IndexedDB: a flat, day-indexed task store plus a separate `planState` record as the explicit
current-day pointer, explicitly rejecting a day-as-aggregate shape because embedding tasks as an
array inside one day *document* turned every single-task edit into a read-modify-write of the
whole array. That decision's storage mechanism (IndexedDB) is obsolete under the new
architecture; this ADR is a new decision for Postgres, not a revision of the old one — filed
separately rather than editing or superseding the old record, since it addresses a different
storage technology, and the old ADR's reasoning is reference context, not binding precedent.

This shape will be depended on by other code once built: a future dashboard aggregation and
Epic-5's data export will both query these tables directly, so getting the shape right now avoids
a later migration.

## Decision

Two tables, matching Approach A from `docs/specs/study-plan-execution/ImplementationPlan.md`:

- **`tasks`**: `id (identity PK), day_number (int, indexed, not null), skill (Postgres enum, 7
  fixed values), title (text), description (text), estimated_minutes (int), status (Postgres
  enum: not_started / completed / skipped), note (text, nullable), updated_at (timestamptz)`.
  "Day N's tasks" is a `WHERE day_number = :n` query against this one table — there is no
  separate "day" entity and no stored per-day aggregate.
- **`plan_state`**: a singleton table — `id (PK, CHECK (id = 1)), current_day_number (int),
  total_days (int)`. Enforced at the schema level to hold exactly one row, not just by
  convention. It is the single source of truth for which day is current and changes only inside
  `move_to_next_day()`, after that operation's gate (every current-day task is `completed` or
  `skipped`) passes — never as a derived side effect of any task-level edit.

`day_number` on `tasks` and `current_day_number` on `plan_state` are plain integers, not foreign
keys into a separate `study_days` table. This was a real choice, not an oversight — see
Alternatives Considered.

## Alternatives Considered

**`study_days` parent table + `tasks.day_id` foreign key (day-as-aggregate via a relational
FK).** The prior IndexedDB ADR's objection to day-as-aggregate — that it turns single-task edits
into whole-array read-modify-writes — **does not apply in a relational database**: a foreign key
from `tasks.day_id` to `study_days.id` does not change the cost of updating one task row; Postgres
never requires touching sibling rows to update a single row regardless of whether `day_number` is
a bare int or a FK. So this alternative is not rejected on the old grounds. It is rejected here on
different, relational-specific grounds: its actual benefits — FK-enforced referential integrity
(a task's day is guaranteed to exist; the current-day pointer could be FK-enforced too) and a
natural home for future day-level attributes (e.g. a day theme) — serve no current requirement.
The spec's Out of Scope explicitly excludes learner-authored days and task-to-day reassignment, so
the integrity risk this ADR accepts instead (a `day_number`/`current_day_number` int that isn't
FK-validated) is low: both are set once, by the seed script, and never touched by any user-facing
mutation. The cost of the FK approach — an extra table, an extra join on every day-level read, two
identity concepts to track (`day_number` vs internal `day_id`), 180 extra seed rows to manage — is
real and buys nothing today.

**Current-day pointer stored in a shared generic config/key-value table** instead of a dedicated
`plan_state` table. Rejected: no such shared table exists in `docs/architecture/Architecture.md`,
and creating one here would couple this epic's migration to a cross-epic concern it does not own.
A singleton table this epic fully owns keeps migration ownership boundaries clean, consistent with
each epic owning its own tables and its own Alembic migration.

## Consequences

- **Easier**: every task-level operation (status toggles, notes, description/time edits — the
  dominant interaction) is an independent single-row UPDATE. Querying "all tasks for day N," for
  both the current-day view and Day History, is a cheap indexed lookup on `tasks.day_number` at
  this data volume (~6 tasks/day × 180 days). The `plan_state` singleton constraint means "which
  day is current" can never accidentally fork into two rows.
- **Harder**: there is no day-level table to hang future day-specific attributes on (e.g. a day
  theme or day-level note) without either adding a column to `tasks` redundantly per row or
  migrating to the `study_days`+FK shape later.
- **Forecloses nothing regarding FR-12** (past-day editability). Because tasks are addressed by
  their own `id`, enabling edits to a past day's task later — if that open question resolves in
  favor of allowing it — is a router/service change (the existing `PATCH /tasks/{id}` endpoints
  take a task id, not a day, so they don't structurally forbid this today) plus a UI change, not a
  schema rewrite.
- **Migration path if day-level attributes are needed later**: introducing `study_days` and a
  `tasks.day_id` FK is additive — backfill `study_days` rows from the distinct `day_number` values
  already in `tasks`, add the FK column, migrate reads incrementally. It does not touch task
  identity (`tasks.id`) or any task-level field, so it is a low-risk migration to defer until an
  actual day-level attribute requirement exists.
- **Confirms**: an explicit, schema-enforced-singleton `plan_state.current_day_number` (rather
  than anything derived from task statuses) is required to satisfy FR-6's "no automatic advance"
  rule — same conclusion the prior IndexedDB ADR reached, now re-derived for Postgres rather than
  assumed to carry over.
