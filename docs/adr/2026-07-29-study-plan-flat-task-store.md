# ADR: Study Plan Data Modeled as a Flat Task Store with an Explicit Current-Day Pointer

Date: 2026-07-29
Slug: study-plan-flat-task-store
Status: Superseded by 2026-07-30-daily-lesson-plan-data-model
Related spec: docs/specs/study-plan-execution/Specification.md (superseded — see docs/specs/daily-lesson-plan/Specification.md)

## Context

The Study Plan module (`docs/architecture/Architecture.md`) owns the 180-day plan structure,
daily task assignment, and completion state, persisted via the shared Local Data Layer
(IndexedDB for structured records, per the accepted no-backend architecture in
`docs/adr/2026-07-29-v1-no-backend-architecture.md`). The Specification
(`docs/specs/study-plan-execution/Specification.md`) requires per-task editing (status, note,
description, estimated time — FR-3 through FR-5), a completed/total count that updates
immediately (FR-9), read-only browsing of past days (FR-10), and — critically — that the current
day never advances except through an explicit learner action (FR-6, FR-7, FR-8). This last
requirement rules out deriving "current day" from task completion state, since that would make
the current day flip as a side effect of finishing the last task of a day.

This data shape will be depended on by other components once built: the App Shell/Dashboard
aggregates "today's plan" for its overview, and the Backup/Restore module (Epic-5) will need to
serialize and restore it. Getting the shape right now avoids a rewrite later.

## Decision

Model the plan as a single flat, day-indexed IndexedDB object store of task records —
`{ id, dayNumber, skill, title, description, estimatedMinutes, status, note, updatedAt }`, indexed
by `dayNumber` — with no separate "day" document. A day's task list is a query (index range scan)
against this store, not a stored aggregate. A second, small `planState` record — `{
currentDayNumber, totalDays }` — lives in the same IndexedDB database (not LocalStorage) as the
single, explicit source of truth for which day is current. It changes only when
`moveToNextDay()` is invoked and that operation's gate (all current-day tasks Completed or
Skipped) passes; it never changes as a derived side effect of any task-level edit.

## Consequences

- Easier: every task-level operation (the dominant interaction — status toggles, notes,
  description/time edits) is an independent single-record read/write, with no need to
  read-modify-write a larger "day" aggregate. Querying "all tasks for day N," for both the
  current-day view and Day History, is a cheap indexed range lookup at this data volume (~6
  tasks/day x 180 days). Keeping `planState` in IndexedDB rather than splitting it into
  LocalStorage means "move to next day" and any future consistency check happen inside one
  storage engine, not two.
- Harder: there is no single "get the whole day in one read" convenience the way a day-aggregate
  document would offer; any day-level rendering does a query over the tasks index instead of one
  document `get`. This is an accepted, cheap cost at 180 days x ~6 tasks.
- Forecloses: nothing regarding FR-12 (past-day editability). Because tasks are addressed by
  their own `id`, not nested inside an immutable per-day document, enabling edits to a past day's
  task later — if that open question resolves in favor of allowing it — is a UI-layer change
  (adding controls to Day History), not a data-model change.
- Confirms: an explicit stored `currentDayNumber` (rather than any state derived from task
  statuses) is required to satisfy FR-6's "no automatic advance" rule; this was evaluated and
  rejected as an alternative in the Implementation Plan.
