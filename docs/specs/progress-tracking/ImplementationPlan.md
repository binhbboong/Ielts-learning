# Implementation Plan: Practice Result Tracking & Progress Visibility
Spec: docs/specs/progress-tracking/Specification.md

## Status
Rewritten 2026-07-29 against the full-stack architecture
(`docs/adr/2026-07-29-fullstack-vercel-claude-architecture.md`). The previous version of this
plan was written against the now-superseded client-only/IndexedDB architecture and no code was
ever built from it — this replaces it in place rather than appending an alternative.

## Approach

This plan decides two things: how a practice result is shaped as a Postgres table, and how the
average score, trend direction, 4-session threshold (FR-8), and missed-question-type breakdown
(FR-7) are computed. Both are recorded in
`docs/adr/2026-07-29-practice-results-schema-and-derivation.md` (new ADR, see Related ADRs); this
section carries the reasoning.

Per the shared conventions, this epic owns `backend/app/models/practice_result.py`,
`backend/app/schemas/practice_result.py`, `backend/app/services/practice_result.py`,
`backend/app/routers/practice_result.py`, and its own Alembic migration. It imports
`backend/app/core/db.py` (`get_db`) and `backend/app/core/security.py` (`require_learner`) from
the access-protection epic's plan rather than defining them. No `learner_id`/owner column is
added to any table (single-learner simplification) — `require_learner` gates the whole router.

### Derivation approaches considered

**Approach A — On-demand derivation via one SQL SELECT per request, computed in Python
(recommended).** The trend endpoint runs one indexed query — `WHERE skill = :skill AND
logged_at >= :period_start` (or no skill filter for "Both") — fetching the matching rows, then
pure Python functions in `services/practice_trend.py` compute average, trend direction, threshold
status, and the missed-type breakdown from that in-memory list. Nothing beyond the raw
`practice_results` rows is persisted.
- Costs: every trend view open/filter-change/refresh re-fetches and re-computes over the full
  matching row set. At this project's real scale (one learner, realistically hundreds of rows
  accumulated over years) this is sub-millisecond in Postgres and not a meaningful cost.
- Risks: none structural. The derivation functions take a plain list of rows as input, so they are
  unit-testable with fixture data and no live database connection.
- Makes easy later: FR-10 (filter change) and FR-11 (refresh) are both just "run the query and the
  same pure functions again" — there is no cache to invalidate and no way for the displayed trend
  to disagree with the raw log, which is the persona's core trust concern named in the spec.

**Approach B — Persisted running aggregates, updated on every write.** A summary row (or one per
skill) tracks running sum/count/missed-type tallies, updated inside the same transaction as every
`POST /practice-results`; the trend endpoint reads the aggregate instead of scanning raw rows.
- Costs: a second table and a second write path — every save must keep both the raw row and the
  aggregate consistent, or they drift, which is a direct threat to FR-4/FR-11's reliability intent.
- Risks: the "period" filter (FR-10, e.g. "last 8 weeks") is a sliding window relative to *today*,
  not a fixed bucket. A sum updated at write time doesn't stay valid as the window advances daily
  unless aggregates are bucketed per day/week and re-summed at read time — which reintroduces
  Approach A's read-time computation anyway while keeping all of Approach B's extra write-time
  complexity and drift risk.
- Rejected: no scale justifies the added surface area, and it is the more costly-to-reverse choice
  once other code (or Epic-7/8's future Writing/Speaking rows) starts depending on the aggregate's
  shape.

**Approach C — Push the derivation into SQL (window functions / a materialized view) instead of
Python.** One query does the average, a `LAG`/window-function half-vs-half trend comparison, and a
`GROUP BY unnest(missed_question_types)` breakdown, all inside Postgres.
- Costs: harder to unit-test in isolation — asserting FR-7/FR-8's exact behavior (the feature's two
  defining constraints) against SQL window-function output requires a real database in every test
  run, versus plain Python functions over fixture lists.
- Risks: SQL window-function trend logic is harder to read and change than an equivalent ~20-line
  Python function, for no performance benefit at this scale.
- Rejected: optimizes for a read-latency problem this project doesn't have, at the cost of the
  testability the constitution's TDD requirement depends on.

**Recommendation: Approach A.** It has no data-drift failure mode, keeps FR-7 and FR-8 trivially
testable as pure functions of one input (the fetched row list), and matches the reasoning already
accepted for this feature before the architecture pivot (the superseded plan's Approach 1) — the
sliding-window and single-learner-scale arguments transfer unchanged from IndexedDB to Postgres.
The exact trend-direction algorithm (recent-half vs. earlier-half average comparison, small
epsilon for "Steady") is an implementation-level judgment call not fixed by the spec or wireframe;
flagged under Risks, not silently decided as load-bearing here.

### Schema shape

`practice_results` (see ADR for full reasoning): `id`, `skill` (VARCHAR, validated against a
code-level allow-list — not a DB enum/CHECK — so `Writing`/`Speaking` can be added later without a
destructive migration, per PRD Epic-4's scope note), `source` (VARCHAR), `score` (INTEGER),
`total` (INTEGER), `time_taken_seconds` (INTEGER — the wireframe leaves mm:ss-vs-minutes as an
implementation choice; storing seconds lets the frontend render either), `missed_question_types`
(Postgres `ARRAY(VARCHAR)`, values validated against the fixed per-skill taxonomy at write time),
`note` (TEXT, nullable), `logged_at` (TIMESTAMP, server-set at insert). Index on `(skill,
logged_at)` to support the trend query's filter pattern. No `learner_id` column.

## File/Module Structure

| Path | Responsibility | Implements (wireframe, if UI-facing) |
|------|-----------------|-----------------|
| `backend/app/models/practice_result.py` | SQLAlchemy ORM model for the `practice_results` table. | — |
| `backend/app/models/practice_result_taxonomy.py` | Canonical fixed per-skill missed-question-type taxonomy constant (per the taxonomy ADR) and the code-level allowed-`skill` set. | — |
| `backend/app/schemas/practice_result.py` | Pydantic schemas: create payload, read model, trend response, history-list response, taxonomy response. | — |
| `backend/app/services/practice_result.py` | Creates and lists practice results; enforces the FR-1 minimum-field rule and FR-2's optional fields, validates `skill`/`missed_question_types` membership before persisting. | — |
| `backend/app/services/practice_trend.py` | Pure functions computing average, trend direction, 4-session threshold status, and missed-type breakdown from an already-fetched row list; no DB session, no HTTP — unit-tested without a database. | — |
| `backend/app/routers/practice_result.py` | `POST /practice-results` (log), `GET /practice-results` (history, skill filter + sort order), `GET /practice-results/trend` (skill + period params), `GET /practice-results/taxonomy`; every route behind `require_learner`. | — |
| `backend/alembic/versions/<rev>_create_practice_results.py` | Migration creating `practice_results` and its `(skill, logged_at)` index. | — |
| `src/app/progress/models/practice-result.model.ts` | TypeScript types mirroring the backend schemas (`PracticeResult`, `TrendResult`, `BreakdownEntry`). | — |
| `src/app/progress/data/practice-result.repository.ts` | Sole caller of `core/api/api-client.ts` for this module: create, list/filter/sort, fetch trend, fetch taxonomy. | — |
| `src/app/progress/state/practice-log.facade.ts` | Holds the log-form's submission state (filled/saving/error/confirmed) and the history list's data/filter/sort state; calls the repository. | — |
| `src/app/progress/state/progress-trend.facade.ts` | Holds the trend view's skill/period filter state and the last-fetched trend+breakdown result; calls the repository on load, filter change, and refresh. | — |
| `src/app/progress/pages/log-practice-result/log-practice-result.component.ts` (+ `.html`) | Entry form: skill/source/score/time fields, missed-type checklist (from the taxonomy endpoint), optional note, save gate, error and confirmation sub-states. | docs/ux/wireframes/log-practice-result.md |
| `src/app/progress/pages/progress-trend/progress-trend.component.ts` (+ `.html`) | Skill/period filters plus Region 1 (score trend) and Region 2 (missed-type breakdown) always rendered together, including empty/loading/error/threshold states. | docs/ux/wireframes/progress-trend.md |
| `src/app/progress/pages/practice-log-history/practice-log-history.component.ts` (+ `.html`) | Filterable, sortable chronological list of every logged result, including empty/error states. | docs/ux/wireframes/practice-log-history.md |
| `src/app/progress/progress.routes.ts` | Route declarations for the three pages above; exposes the path the app shell's nav links to (exact entry-point mechanism is an open question — see Risks). | — |

## Testing Strategy

Per Constitution principle 2 and the `test-driven-development` skill, every row below is written
test-first — the test is written and fails before the corresponding behavior is implemented, for
both backend pure functions/routes and frontend components.

| Requirement | Verified by |
|---|---|
| FR-1 | Backend: service/route test — `POST /practice-results` rejects (422) a payload missing skill, source, score, or time taken; succeeds once all four are present. Frontend: component test — Save is disabled until all four fields are filled. |
| FR-2 | Backend: service test — a payload with `missed_question_types: []` and no `note` saves successfully. Frontend: component test — save succeeds with the checklist and note both left empty. |
| FR-3 | Frontend component test with a mocked repository rejection: after a failed save, every entered field value is still present, an explicit error is shown, and retrying with the same data (no re-entry) succeeds once the mock allows it. |
| FR-4 | Frontend component test: a successful save replaces the form with a confirmation state naming the just-saved skill and score. |
| FR-5 | Frontend component test: from the confirmation state, "Log Another" resets to a fresh empty form, and the return action navigates back — asserted as two separate cases. |
| FR-6 | Frontend component test: Cancel on a filled-but-unsaved form exits without the repository's create method ever being called. |
| FR-7 | **Backend `practice_trend.py` unit test**: for a >=4-session fixture, one function call returns both a trend result and a breakdown result together, for each of an Up, a Steady, and a Down fixture — not just one direction. **Frontend component test matrix over the same three fixtures**: in every case, both Region 1 and Region 2 are present in the rendered output — this is the feature's defining constraint, asserted per direction, not once. |
| FR-8 | **Backend `practice_trend.py` unit tests parametrized over 0, 1, 2, 3, and 4 sessions**: 0-3 return an "insufficient" status with the current count and sessions-still-needed to reach exactly 4, never a trend value; 4 returns a real trend — the boundary itself is asserted, not just "fewer is insufficient." **Frontend component test**: below-threshold response renders the count/remaining message (not a chart) alongside any available breakdown data. |
| FR-9 | Frontend component test: zero sessions ever logged (skill/period with no rows at all) renders an onboarding message pointing to Log Practice Result, not a blank/empty chart. |
| FR-10 | Frontend component test: changing the skill filter or period triggers a new fetch and asserts both regions' content changed together, for at least one filter case and one period case. Backend route test: `GET /practice-results/trend` respects `skill` and `period` query params. |
| FR-11 | Frontend component test: a result added to the repository's mock after initial load is reflected only after Refresh is invoked, not before — no polling. |
| FR-12 | Frontend component test asserting the FR-8 "insufficient sessions" message and a simulated repository-read-failure message render with visibly distinct text/test-ids — an explicit inequality assertion, not "some message shown." Backend route test: a simulated DB error returns a 5xx distinct from an empty-but-successful 200. |
| FR-13 | Backend route test: `GET /practice-results` returns date, skill, source, score, and time taken per entry, with missed types and note included. Frontend component test: the list renders those fields, with missed types/note as secondary detail. |
| FR-14 | Backend route test: `skill` query param narrows results; a `sort` param reverses order. Frontend component test: applying the skill filter narrows the rendered list; toggling sort reverses displayed entry order. |
| FR-15 | Frontend component test: zero logged results renders "nothing logged yet" plus a call-to-action linking to Log Practice Result. |
| FR-16 | Frontend component test asserting the FR-15 message and a simulated repository-read-failure message use visibly distinct text/test-ids. |

## Constitution Check

- **Tests-first (principle 2, no exceptions without explicit user sign-off)**: every backend
  service/route and every frontend component/facade in the File/Module Structure above is built
  by writing its failing test first, per the `test-driven-development` skill. `practice_trend.py`
  in particular must exist as fixture-driven unit tests (no DB) before any route wires it up,
  since FR-7/FR-8 are this feature's defining constraints.
- **Root cause over patches (principle 3)**: applies to `systematic-debugging` during
  implementation; nothing in this plan sets up a debugging shortcut.
- **Small, reviewable units (principle 4)**: the file structure above is already decomposed to one
  responsibility per file; task breakdown (`/spec:tasks`) should keep each task scoped to one row.
- **Docs are durable (principle 6)**: this plan replaces the prior client-only version of
  `ImplementationPlan.md` in place rather than leaving both to coexist; the new ADR does not
  duplicate the taxonomy ADR's still-valid fixed-list decision.
- **No irreversible actions (principle 7)**: not applicable — this plan performs no deploy/release
  action.

## Risks / Open Questions

Carried forward from the spec, unresolved by design (not to be silently decided here):

- **Missed-question-type taxonomy content (resolved 2026-07-29).** Use the official IELTS
  Academic lists: 11 Reading types and 6 Listening types. Persist stable machine keys and expose
  each key with its official display label from the backend-canonical taxonomy endpoint.
- **Practice Log/History core-vs-optional priority is genuinely unresolved** (spec FR-13 open
  question). Planning assumption: build `practice-log-history/` as fully independent of
  `progress-trend/` (separate facade, separate route), so it can be deprioritized or dropped from
  the task backlog without touching FR-1 through FR-12, or kept with no rework — reversible either
  way.
- **Exact entry-point mechanism for starting a new log is unresolved** (spec open question).
  Planning assumption: `progress.routes.ts` exposes a route the app shell's persistent nav links
  to, consistent with the shell owning cross-module navigation; this module does not build its own
  landing chrome.
- **Below-threshold cross-linking between the trend view and history list is unresolved** (spec
  open question). Planning assumption: no cross-link is built initially; `progress-trend.component`
  should expose an optional action slot for a future "view history" link so adding it later is
  additive.
- **Trend-direction algorithm is an implementation judgment call**, not fixed by FR-7's "up,
  stable, down" wording. Assumed: recent-half vs. earlier-half average comparison with a small
  epsilon for "Steady" — confirm or revise during task breakdown since it determines what the
  FR-7 test fixtures assert.
- **Period-filter options and date-boundary handling** (exact choices like "last 4/8/12 weeks",
  timezone/local-midnight edges for "recent") are not fixed by the spec or wireframe; flagged so
  they are not silently decided inside a component during implementation.
- **Sequencing dependency on the access-protection epic.** `require_learner`, `get_db`, and the
  Alembic bootstrap (`alembic.ini`, `env.py`) are owned by that epic's plan and are assumed to
  exist before this epic's router/migration can run; if this epic is implemented first, a minimal
  stub for `require_learner`/`get_db` will be needed to keep this module's tests running in
  isolation.
- **score/total consistency** (e.g. `score <= total`) is enforced only at the Pydantic layer in
  this plan, not as a DB constraint — flagged as a deliberate lightweight choice, not an oversight;
  revisit if data integrity issues ever surface.
- **Writing/Speaking integration remains explicitly out of scope for this epic's build**, per PRD
  Epic-4's scope note — the schema (`skill` as an open, code-validated string) is designed not to
  block that later work, but no Writing/Speaking field, route, or UI is built now.

## Related ADRs
- docs/adr/2026-07-29-missed-question-type-taxonomy.md (taxonomy-is-a-fixed-list decision; still
  valid, not duplicated here)
- docs/adr/2026-07-29-practice-results-schema-and-derivation.md (new; table shape + on-demand
  derivation, written as part of this plan)
