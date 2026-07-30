# Tasks: Practice Result Tracking & Progress Visibility

## Implemented recommendation record

- Scores are normalized to percentages. Trend direction compares chronological halves, assigns
  an odd session to the recent half, and uses inclusive +/-2.5 percentage-point boundaries.
- Recent periods are 4, 8, or 12 weeks. Boundaries start at learner-local midnight in
  `Asia/Ho_Chi_Minh` and are converted to UTC for querying.
- Practice Log History is a core capability. Below-threshold progress links to that history.
- The app shell exposes one Progress navigation item; Progress and History provide prominent
  Log Result actions without adding another primary navigation item.
Plan: docs/specs/progress-tracking/ImplementationPlan.md

Every task follows Constitution principle 2 (tests-first/TDD): the test for a task's behavior is
written and failing before the behavior is implemented, and "Definition of done" is checked by
running that test suite — never by manual inspection.

This backlog is written against the full-stack architecture (FastAPI + Neon PostgreSQL + Angular)
per the rewritten Implementation Plan; it replaces the prior IndexedDB-era version of this file in
place, per Constitution principle 6 (docs are durable, updated in place rather than left to drift).

**Cross-epic dependency assumption**: every backend task below imports `backend/app/core/db.py`
(`get_db`) and `backend/app/core/security.py` (`require_learner`), which are owned by the
access-protection epic's backlog and assumed to already exist (parallel, not sequenced here). If
this epic is implemented first, a minimal local stub for `get_db`/`require_learner` will be needed
to keep these tasks' tests running in isolation — not itself a task in this backlog. Likewise, the
frontend repository task assumes `src/app/core/api/api-client.ts` already exists.

## Task-1 — PracticeResult SQLAlchemy model and Alembic migration
- [x] Status: Done
- Depends on: none
- Goal: Define the `PracticeResult` ORM model (`id`, `skill` VARCHAR, `source` VARCHAR, `score`
  INTEGER, `total` INTEGER, `time_taken_seconds` INTEGER, `missed_question_types`
  `ARRAY(VARCHAR)`, `note` TEXT nullable, `logged_at` TIMESTAMP server-set at insert) per
  `docs/adr/2026-07-29-practice-results-schema-and-derivation.md`, and write the Alembic migration
  creating the `practice_results` table plus its `(skill, logged_at)` index. No `learner_id`
  column (single-learner simplification, per the ADR).
- Files touched: `backend/app/models/practice_result.py`,
  `backend/alembic/versions/<rev>_create_practice_results.py`
- Definition of done: a migration test (upgrade then downgrade against a test database, or a
  schema-inspection test) confirms the table and its `(skill, logged_at)` index exist with the
  documented columns/types; a model-level test confirms a row round-trips (insert then read back)
  with all fields intact, including an empty `missed_question_types` array and a null `note`. No
  FR of its own — prerequisite for FR-1 through FR-16, all of which depend on durable storage
  existing.
- Implementation note: Added Alembic revision `0005`, registered the model for migration
  metadata, and verified schema/index inspection, row round-trip, and the full upgrade/downgrade
  chain against PostgreSQL.

## Task-2 — Missed-question-type taxonomy constant and read-only taxonomy endpoint
- [x] Status: Done
- Depends on: none
- Goal: Define the fixed, per-skill missed-question-type taxonomy constant (one list for Reading,
  one for Listening) per `docs/adr/2026-07-29-missed-question-type-taxonomy.md`, and expose it
  read-only via `GET /practice-results/taxonomy` per the schema ADR, so logging (FR-2) and the
  trend breakdown (FR-7) share one backend-canonical source instead of each guessing independently.
- Taxonomy decision: use the official IELTS Academic lists (11 Reading and 6 Listening types),
  storing stable machine keys and returning those keys with human-readable labels.
- Files touched: `backend/app/models/practice_result_taxonomy.py`,
  `backend/app/schemas/practice_result.py` (taxonomy response shape),
  `backend/app/routers/practice_result.py` (adds `GET /practice-results/taxonomy` only)
- Definition of done: a route test confirms `GET /practice-results/taxonomy` returns a per-skill
  breakdown (distinct, non-empty lists for Reading and Listening) behind `require_learner` (401
  without a valid session), and a unit test confirms the constant itself is fixed (not derived
  from any request input). No FR of its own — prerequisite for FR-2's checklist and FR-7's
  breakdown ranking, both of which must read the same values this endpoint serves.
- Implementation note: Added an immutable backend-canonical taxonomy, protected read endpoint,
  and tests for authentication, exact keys, distinct per-skill lists, and stable key/label
  serialization.

## Task-3 — POST /practice-results: log a result with FR-1/FR-2 field rules
- [x] Status: Done
- Depends on: Task-1, Task-2
- Goal: Implement the service function and route that create a practice result: reject (422) a
  payload missing skill, source, score, or time taken; accept `missed_question_types` and `note`
  both absent or empty; validate `skill` against the code-level allow-list and any provided
  `missed_question_types` against Task-2's taxonomy for the given skill before persisting.
  `score <= total` is enforced only at the Pydantic layer, per the plan's flagged, deliberate
  lightweight choice (not a DB constraint).
- Files touched: `backend/app/schemas/practice_result.py` (create payload + read model),
  `backend/app/services/practice_result.py`,
  `backend/app/routers/practice_result.py` (adds `POST /practice-results`)
- Definition of done: route tests confirm a payload missing any of skill/source/score/time-taken
  is rejected with 422 and nothing is persisted; a payload with `missed_question_types: []` and no
  `note` saves successfully and is readable back; a payload with a `missed_question_types` value
  outside the selected skill's taxonomy is rejected. Covers FR-1 and FR-2 (backend half — the
  save-confirmation/failure-retry UX itself is frontend behavior, covered by Task-15/Task-16).
- Implementation note: Added Pydantic validation for required text/numeric fields,
  `score <= total`, positive total/time, skill membership, and per-skill taxonomy keys; the
  authenticated POST route persists and returns the complete created row.

## Task-4 — practice_trend.py: average score and trend-direction pure functions
- [x] Status: Done
- Depends on: Task-1
- Goal: Pure functions (no DB session, no HTTP) computing average score and a trend-direction
  label (Up/Steady/Down) from an already-fetched list of practice-result rows, using a
  recent-half-vs-earlier-half average comparison with a small epsilon for "Steady" — the
  Implementation Plan's named algorithm choice, an implementation judgment call rather than
  something FR-7 itself fixes, confirmed here as the definition under test.
- Files touched: `backend/app/services/practice_trend.py`
- Definition of done: unit tests (fixture row lists, no live database) confirm average-score
  arithmetic, and confirm trend-direction correctly labels dedicated Up/Steady/Down fixtures per
  the recent-half/earlier-half rule and epsilon. Supporting function for FR-7 (the trend half of
  the combined view); FR-7 itself is verified once the combined entry point (Task-7) and its
  route/UI consumers exist.

## Task-5 — practice_trend.py: 4-session threshold status with exact boundary tests
- [x] Status: Done
- Depends on: Task-1
- Goal: A pure function that, given a session count, returns whether the count meets the
  4-session threshold and, if not, the current count and how many more are needed to reach
  exactly 4. This is FR-8's defining constraint and gets its own dedicated, boundary-tested task,
  per the plan's requirement that FR-8 not be folded silently into a general trend task.
- Files touched: `backend/app/services/practice_trend.py`
- Definition of done: unit tests parametrized over 0, 1, and 2 sessions confirm "insufficient"
  with the correct count and correct remaining-to-4; a **dedicated test at exactly 3 sessions**
  confirms "insufficient" with remaining = 1; a **dedicated test at exactly 4 sessions** confirms
  "sufficient" with a real trend eligible — the boundary itself is asserted at both sides, not
  just "fewer is insufficient." Covers FR-8's threshold logic in isolation (rendering is Task-20).
- Implementation note: Added an immutable threshold result and explicit tests for 0, 1, 2, 3,
  and exactly 4 sessions.

## Task-6 — practice_trend.py: missed-question-type breakdown ranking
- [x] Status: Done
- Depends on: Task-1
- Goal: A pure function that groups and ranks missed-question-type occurrences across a list of
  practice-result rows, most-frequent first, regardless of how many sessions are in the list
  (including fewer than 4), so it produces useful output even below the FR-8 threshold.
- Files touched: `backend/app/services/practice_trend.py`
- Definition of done: unit tests confirm correct grouping/ranking/counting over fixture row sets,
  including a fixture with fewer than 4 rows (breakdown still computes from whatever exists) and a
  fixture with zero rows (returns an empty ranking, not an error). Supports the breakdown half of
  FR-7 and the "still surface available breakdown data" clause of FR-8; combined-response
  verification is Task-7.
- Implementation note: Added deterministic count-descending/key-ascending ranking with tests for
  ties, below-threshold input, and zero rows.

## Task-7 — practice_trend.py: combined computation always returns trend + breakdown together
- [x] Status: Done
- Depends on: Task-4, Task-5, Task-6
- Goal: A single entry-point function that, given a row list, always returns both the
  trend/threshold result (Task-4/Task-5) and the breakdown result (Task-6) in one return value —
  there is no code path that returns one without the other. This is the pure-logic half of FR-7's
  defining "never independently fetchable in a way that could desync" constraint, and gets its own
  dedicated task per the plan.
- Files touched: `backend/app/services/practice_trend.py`
- Definition of done: a unit test confirms that for fixtures at 0, 3, 4, and 8+ sessions (crossing
  the FR-8 threshold) and for Up/Steady/Down trend fixtures, **every single call returns a
  structurally complete result containing both a trend/threshold field and a breakdown field —
  never one with the other omitted or undefined**. Covers the pure-function contract underlying
  FR-7 and FR-8 together, verified per fixture, not once.

## Task-8 — GET /practice-results/trend: route wiring, skill/period filters, error distinction
- [x] Status: Done
- Depends on: Task-1, Task-7
- Goal: Wire Task-7's combined computation to one indexed SQL query filtered by `skill` (or no
  filter for "Both") and a `logged_at` cutoff derived from the requested period, expose it as
  `GET /practice-results/trend`, and ensure a genuine DB/read failure returns a distinct 5xx
  rather than an empty-but-successful 200.
- Files touched: `backend/app/services/practice_result.py` (query),
  `backend/app/routers/practice_result.py` (adds `GET /practice-results/trend`)
- Definition of done: a route test confirms `skill` and `period` query params narrow the fetched
  row set before it reaches Task-7's computation (FR-10's backend half); a route test with a
  simulated DB error returns a 5xx distinct from a genuine empty-but-successful 200 for a
  skill/period with zero rows (FR-12's backend half). Covers FR-7 (trend and breakdown served from
  one response, never as two separate calls), FR-8 (threshold status surfaced via the same
  response), FR-10 (backend filter half), and FR-12 (backend error-distinction half).

## Task-9 — GET /practice-results: chronological history route with filter/sort
- [x] Status: Done
- Depends on: Task-1
- Goal: Implement the route listing every practice result with date, skill, source, score, time
  taken, missed question types, and note, supporting a `skill` filter and a `sort` (newest-first /
  oldest-first) query param.
- Files touched: `backend/app/services/practice_result.py` (list query),
  `backend/app/schemas/practice_result.py` (list response),
  `backend/app/routers/practice_result.py` (adds `GET /practice-results`)
- Definition of done: a route test confirms the response includes date, skill, source, score, and
  time taken per entry with missed types and note included (FR-13, backend half); a route test
  confirms a `skill` query param narrows results and a `sort` param reverses order (FR-14, backend
  half).
- Implementation note: Added the authenticated history endpoint with validated Reading/Listening
  filters, newest/oldest ordering, complete row serialization, and route-level persistence tests.

## Task-10 — Frontend models mirroring backend schemas
- [x] Status: Done
- Depends on: Task-2, Task-3, Task-8, Task-9
- Goal: Define TypeScript types (`PracticeResult`, `TrendResult`, `BreakdownEntry`,
  `TaxonomyResponse`) mirroring the now-finalized backend Pydantic schemas from Tasks 2/3/8/9, per
  the existing `src/app/study-plan/models/` pattern, so the frontend and backend shapes cannot
  silently drift apart.
- Files touched: `src/app/progress/models/practice-result.model.ts`
- Definition of done: a type-level/unit test suite confirms sample payloads matching each backend
  response shape (taxonomy, created result, trend+breakdown, history entry) satisfy the
  corresponding TypeScript type, including `missedQuestionTypes` and `note` both absent. No FR of
  its own — prerequisite for FR-1 through FR-16's frontend-facing tasks.

## Task-11 — practice-result.repository.ts: sole API-client caller for this module
- [x] Status: Done
- Depends on: Task-10
- Goal: Implement the repository as the only module component calling
  `src/app/core/api/api-client.ts` for this feature — create a result, list/filter/sort history,
  fetch trend, fetch taxonomy — following the existing `src/app/study-plan/data/` pattern.
- Files touched: `src/app/progress/data/practice-result.repository.ts`
- Definition of done: a test suite (mocked api-client) confirms each method calls the correct
  endpoint/params and returns the typed response, and that a simulated HTTP failure on any method
  surfaces as a rejected/errored call rather than a silent no-op — the failure path Task-15,
  Task-24, and Task-28 build on. No FR of its own — prerequisite storage seam for FR-1 through
  FR-16's frontend behavior.

## Task-12 — practice-log.facade.ts: log-form submission state
- [x] Status: Done
- Depends on: Task-11
- Goal: Hold the log-form's submission state machine (filled/saving/error/confirmed) and call the
  repository's create method, without owning any rendering, following the existing
  `src/app/study-plan/state/` pattern.
- Files touched: `src/app/progress/state/practice-log.facade.ts`
- Definition of done: a unit test confirms the facade transitions filled -> saving -> confirmed on
  a successful repository call (retaining the just-saved skill/score for the confirmation state),
  and filled -> saving -> error (retaining every submitted field value) on a rejected call, with a
  retry from error re-invoking create with the same retained values. Supporting state layer for
  FR-3 and FR-4; rendering verification is Task-15/Task-16.

## Task-13 — progress-trend.facade.ts: filter and fetch state
- [x] Status: Done
- Depends on: Task-11
- Goal: Hold the trend view's skill/period filter state and the last-fetched trend+breakdown
  result; call the repository on load, on filter change, and on manual refresh only (no polling).
- Files touched: `src/app/progress/state/progress-trend.facade.ts`
- Definition of done: a unit test confirms changing the skill or period filter triggers a new
  repository call and replaces the held result; a separate test confirms the held result does NOT
  change on its own (no polling) and only updates when a refresh action is explicitly invoked.
  Supporting state layer for FR-10 and FR-11; rendering verification is Task-22/Task-23.

## Task-14 — Log Practice Result form: save gating on required fields
- [x] Status: Done
- Depends on: Task-12
- Goal: Render the entry form (skill, source, score/total, time taken, missed-type checklist
  sourced from the taxonomy endpoint, optional note) per `docs/ux/wireframes/log-practice-result.md`,
  and enforce that save is blocked unless skill, source, score, and time taken are all provided,
  while missed question types and note may remain unset.
- Files touched:
  `src/app/progress/pages/log-practice-result/log-practice-result.component.ts`,
  `log-practice-result.component.html`
- Definition of done: component tests confirm save is blocked/disabled while any one of
  skill/source/score/timeTaken is missing (checked by filling fields one at a time so save never
  enables early), and that save succeeds with missedQuestionTypes and note both left empty. Covers
  FR-1 and FR-2 (frontend half).

## Task-15 — Log Practice Result form: failed save preserves input and allows retry
- [x] Status: Done
- Depends on: Task-14
- Goal: When the facade reports an error state, keep every entered/selected field value on screen,
  show an explicit failure indication, and allow retrying the same save without re-entering data.
- Files touched:
  `src/app/progress/pages/log-practice-result/log-practice-result.component.ts`,
  `log-practice-result.component.html`
- Definition of done: a component test with a mocked repository rejection confirms every field
  value is still present after the failed attempt, an explicit error state is rendered, and a
  retry (same in-memory data, no re-entry) succeeds once the mock is switched to allow the save.
  Covers FR-3.

## Task-16 — Log Practice Result form: success confirmation state
- [x] Status: Done
- Depends on: Task-14
- Goal: On a successful save, replace the entry form with an explicit confirmation state (not a
  silent return to a prior screen, not the form left as-is) naming the just-saved skill and score.
- Files touched:
  `src/app/progress/pages/log-practice-result/log-practice-result.component.ts`,
  `log-practice-result.component.html`
- Definition of done: a component test confirms that after a successful save the rendered state is
  a distinct confirmation view containing the saved skill and score, and that the form is no
  longer shown. Covers FR-4.

## Task-17 — Log Practice Result form: post-confirmation actions (log another / return)
- [x] Status: Done
- Depends on: Task-16
- Goal: From the confirmation state, let the learner either start logging another result (a fresh,
  empty form) or return to their prior context, without the save itself ever being undone by
  either action.
- Files touched:
  `src/app/progress/pages/log-practice-result/log-practice-result.component.ts`,
  `log-practice-result.component.html`
- Definition of done: two separate component-test assertions confirm (a) choosing "Log Another"
  resets to a fresh empty form, and (b) choosing the return action navigates back, exercised as
  distinct test cases. Covers FR-5.

## Task-18 — Log Practice Result form: abandon in-progress entry
- [x] Status: Done
- Depends on: Task-14
- Goal: Let the learner cancel/abandon a filled-but-unsaved entry at any point without creating a
  saved record.
- Files touched:
  `src/app/progress/pages/log-practice-result/log-practice-result.component.ts`,
  `log-practice-result.component.html`
- Definition of done: a component test confirms that cancelling a filled form exits the screen
  without the repository's create method ever being invoked (asserted via a spy/mock call count of
  zero). Covers FR-6.

## Task-19 — Progress Trend view: render trend + breakdown together (>=4 sessions)
- [x] Status: Done
- Depends on: Task-13
- Goal: Render Region 1 (average score, trend direction, framing note) and Region 2
  (missed-question-type breakdown) together, per `docs/ux/wireframes/progress-trend.md`, for a
  selected skill/period with >=4 logged sessions, from a single facade-held response.
- Files touched:
  `src/app/progress/pages/progress-trend/progress-trend.component.ts`,
  `progress-trend.component.html`
- Definition of done: a component test matrix over Up/Steady/Down fixtures (each with >=4
  sessions) confirms that in every case **both Region 1 and Region 2 are present in the rendered
  output** — asserted for all three directions, not just one, since this is the feature's defining
  constraint. Covers FR-7.

## Task-20 — Progress Trend view: below-threshold state (<4 sessions)
- [x] Status: Done
- Depends on: Task-19
- Goal: When fewer than 4 sessions are logged for the selected skill/period, render the current
  count and how many more are needed to reach 4 instead of a score trend, while still rendering
  any missed-question-type breakdown available from the sessions that do exist.
- **Open question — explicitly not resolved by this task:** whether this partial-breakdown state
  should cross-link to the Practice Log/History list is unresolved per the spec's Open Questions
  and the Implementation Plan's Risks. This task exposes an optional action slot/output per the
  plan's stated assumption, but does not wire it to an actual navigation target.
- Files touched:
  `src/app/progress/pages/progress-trend/progress-trend.component.ts`,
  `progress-trend.component.html`
- Definition of done: component tests parametrized over 1 and 2 logged sessions confirm the
  count/remaining message renders instead of a trend chart, and that any available breakdown data
  is still shown alongside it; a **dedicated test at exactly 3 sessions** confirms the
  below-threshold state still renders, and a **dedicated test at exactly 4 sessions** confirms the
  real trend from Task-19 renders instead — the boundary itself is asserted, mirroring Task-5's
  backend boundary tests. Covers FR-8 (frontend half).

## Task-21 — Progress Trend view: zero-sessions-ever onboarding message
- [x] Status: Done
- Depends on: Task-20
- Goal: When zero practice sessions have ever been logged for the selected skill/period, render a
  message directing the learner to log a practice result, rather than an empty/blank trend
  display.
- Files touched:
  `src/app/progress/pages/progress-trend/progress-trend.component.ts`,
  `progress-trend.component.html`
- Definition of done: a component test with zero sessions confirms the rendered output is an
  onboarding message pointing to Log Practice Result (not a blank chart, and not merely the
  generic Task-20 "0 of 4" count with no call-to-action). Covers FR-9.

## Task-22 — Progress Trend view: filter change recomputes both regions together
- [x] Status: Done
- Depends on: Task-21
- Goal: Changing the skill filter (Reading/Listening/Both) or the period filter re-triggers the
  facade's fetch and re-renders both Region 1 and Region 2 together for the new filter values.
- **Open note:** exact period-filter options and date-boundary/timezone handling for "recent" are
  not fixed by the spec or wireframe (Plan Risks); this task implements them behind the facade's
  period parameter without silently deciding the boundary semantics beyond what its tests need to
  assert change-triggers-refetch.
- Files touched:
  `src/app/progress/pages/progress-trend/progress-trend.component.ts`,
  `progress-trend.component.html`
- Definition of done: a component test changing the skill filter, and a separate test changing the
  period filter, each confirm both regions' rendered content changed together (not just one region
  updating) after the filter change. Covers FR-10 (frontend half).

## Task-23 — Progress Trend view: manual refresh reflects newly logged results
- [x] Status: Done
- Depends on: Task-19
- Goal: Let the learner manually refresh the Progress Trend view so a result logged since the view
  was opened is reflected.
- Files touched:
  `src/app/progress/pages/progress-trend/progress-trend.component.ts`,
  `progress-trend.component.html`
- Definition of done: a component test adds a record to the repository's mock after initial load,
  confirms the view does NOT reflect it before Refresh is tapped, then confirms it does after
  Refresh is tapped. Covers FR-11.

## Task-24 — Progress Trend view: distinguish "not enough sessions" from "failed to load"
- [x] Status: Done
- Depends on: Task-20
- Goal: Ensure the FR-8 "insufficient sessions" message and a genuine repository/API read failure
  use visibly distinct wording/test-ids, so the learner can tell which situation applies.
- Files touched:
  `src/app/progress/pages/progress-trend/progress-trend.component.ts`,
  `progress-trend.component.html`
- Definition of done: a component test simulates a repository read failure and asserts the
  rendered error message/test-id is distinct from (not equal to, not a substring/superset of) the
  Task-20 insufficient-sessions message — a direct equality-of-difference assertion, not merely
  "some message shown." Covers FR-12 (frontend half).

## Task-25 — Practice Log History view: render chronological list
- [x] Status: Done
- Depends on: Task-10, Task-11
- Goal: Render the complete chronological list of every logged practice result, per
  `docs/ux/wireframes/practice-log-history.md`, showing date, skill, source, score, and time taken
  per entry, with missed question types and note shown as secondary detail per entry.
- **Open question — explicitly not resolved by this task:** whether Practice Log/History is a
  core/required capability of this epic or an optional, lower-priority one is unresolved per the
  spec's Open Questions (FR-13). This task builds the module fully independent of the Progress
  Trend module (own facade path via the shared repository, no shared component state), consistent
  with the plan's stated assumption that it can be deprioritized or dropped from the backlog
  without touching FR-1 through FR-12.
- Files touched:
  `src/app/progress/pages/practice-log-history/practice-log-history.component.ts`,
  `practice-log-history.component.html`
- Definition of done: a component test confirms each rendered entry shows date, skill, source,
  score, and time taken, and that missed question types and note (when present) render as
  secondary detail. Covers FR-13 (frontend half).

## Task-26 — Practice Log History view: filter by skill and toggle sort order
- [x] Status: Done
- Depends on: Task-25
- Goal: Let the learner filter the chronological list by skill and change its sort order between
  newest-first and oldest-first.
- Files touched:
  `src/app/progress/pages/practice-log-history/practice-log-history.component.ts`,
  `practice-log-history.component.html`
- Definition of done: a component test confirms applying a skill filter narrows the displayed list
  correctly, and a separate assertion confirms toggling sort order reverses the displayed entry
  order. Covers FR-14 (frontend half).

## Task-27 — Practice Log History view: nothing-logged-yet message
- [x] Status: Done
- Depends on: Task-25
- Goal: When no practice results have ever been logged, present a message indicating nothing has
  been logged yet, together with a direct path to log a result.
- Files touched:
  `src/app/progress/pages/practice-log-history/practice-log-history.component.ts`,
  `practice-log-history.component.html`
- Definition of done: a component test with zero logged results confirms a "nothing logged yet"
  message renders with a call-to-action linking to Log Practice Result. Covers FR-15.

## Task-28 — Practice Log History view: distinguish "nothing logged" from "failed to load"
- [x] Status: Done
- Depends on: Task-27
- Goal: Ensure the FR-15 "nothing logged yet" message and a genuine repository/API read failure use
  visibly distinct wording/test-ids.
- Files touched:
  `src/app/progress/pages/practice-log-history/practice-log-history.component.ts`,
  `practice-log-history.component.html`
- Definition of done: a component test simulates a repository read failure and asserts the
  rendered error message/test-id is distinct from the Task-27 "nothing logged yet" message — a
  direct equality-of-difference assertion. Covers FR-16.

## Task-29 — Wire progress module routes
- [x] Status: Done
- Depends on: Task-14, Task-19, Task-25
- Goal: Declare routes for the three screens (Log Practice Result, Progress Trend, Practice Log
  History) so each is reachable at a distinct path, following the existing
  `src/app/study-plan/study-plan.routes.ts` pattern.
- **Open question — explicitly not resolved by this task:** the exact mechanism by which the
  learner starts a new log entry (a persistent "Log Result" action, a nav item, or a dedicated
  landing screen) is unresolved per the spec's Open Questions and the plan's Risks. This task only
  declares the routes/paths themselves, consistent with the plan's assumption that the App Shell's
  persistent nav will link to them; it does not build or decide the App Shell's nav entry-point
  chrome.
- Files touched: `src/app/progress/progress.routes.ts`
- Definition of done: a routing test confirms navigating to each of the three declared paths
  renders the corresponding component. No single FR names routing directly; this task is a
  prerequisite for the entry points FR-1 through FR-16's UI-facing requirements are exercised
  through in a real running app.
