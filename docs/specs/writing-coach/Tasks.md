# Tasks: AI-Assisted Writing Coaching
Plan: docs/specs/writing-coach/ImplementationPlan.md

Sequencing note: Task-1 (the `AIProvider` interface + typed schemas + `FakeAIProvider`) is the
foundation for every AI-calling task in this backlog. It is also the file
`speaking-coach`'s backlog depends on per `docs/adr/2026-07-29-ai-provider-interface-shape.md` —
nothing about its shape should change once later tasks in this backlog start testing against it.
Every task below that touches AI evaluation states explicitly which test double it uses; none
call a real Claude API or the real Anthropic SDK.

Open-questions resolution reflected below (not re-opened): no hard submission cap — every
`evaluate_writing()` call is logged to `ai_call_log` for cost visibility instead (Task-3, Task-5);
resubmission of a revised essay is modeled as a new, independent `writing_submissions` row
referencing the same question — never an overwrite or a linked "revision" (Task-5).

## Task-1 — AIProvider interface, typed schemas, and FakeAIProvider test double
- [x] Status: Done
- Depends on: none
- Goal: Define the abstract `AIProvider` interface and the Pydantic request/result models for
  all four of its methods, per `docs/adr/2026-07-29-ai-provider-interface-shape.md` (typed
  request/result pair per method, synchronous, status-discriminated results, no vendor
  exceptions crossing the boundary). Also provide a `FakeAIProvider` test double implementing
  the full interface with canned/configurable `WritingEvaluationResult` objects (including an
  error/timeout-shaped result), placed somewhere importable by both this backlog's tests and
  `speaking-coach`'s backlog's tests. `evaluate_writing()` has no real implementation yet —
  only the interface, schemas, and fake exist after this task. No Anthropic SDK import anywhere
  in these files.
- Files touched: `backend/app/ai/provider.py`, `backend/app/ai/schemas.py`,
  `backend/app/ai/testing.py` (FakeAIProvider), `backend/tests/ai/test_provider_interface.py`,
  `backend/tests/ai/test_schemas.py`
- Definition of done: tests pass. `WritingEvaluationRequest`/`WritingEvaluationResult` (and the
  stub Speaking/Quiz/Chat request/result pairs) match the ADR's field rules; `FakeAIProvider`
  satisfies the `AIProvider` ABC and can be configured to return both `status: "ok"` and
  `status: "error"` results. This task alone doesn't satisfy any FR end-to-end — it is the
  prerequisite typed contract every later FR-5–FR-8/FR-10-covering task builds on, and the
  contract other epics (speaking-coach) build against without reading this backlog further.
- Implementation note: Added the synchronous four-method ABC, vendor-neutral typed request/result
  schemas with `ok`/`error` invariants, and a configurable request-recording fake supporting
  success, provider error, and delayed writing responses.

## Task-2 — ClaudeProvider.evaluate_writing() implementation
- [x] Status: Done
- Depends on: Task-1
- Goal: Implement `ClaudeProvider(AIProvider).evaluate_writing()` — build the four-criterion
  prompt from `WritingEvaluationRequest`, call the Anthropic SDK, parse/validate the response
  into `WritingEvaluationResult`, and catch all Anthropic SDK exceptions internally, translating
  them to `status: "error"` results (no vendor exception ever crosses the `AIProvider`
  boundary). Also add `get_ai_provider()` — a small factory that reads `AI_PROVIDER` and
  constructs `ClaudeProvider` (only value supported today). `evaluate_speaking`/`generate_quiz`/
  `chat` are left as `NotImplementedError` stubs — out of scope for this epic.
- Files touched: `backend/app/ai/claude_provider.py`, `backend/app/ai/__init__.py`,
  `backend/tests/ai/test_claude_provider.py`
- Definition of done: tests pass mocking **only the Anthropic SDK client** (never a real network
  call, never the whole `ClaudeProvider`) — verifies prompt construction includes
  `response_text`/`task_type`/`question_text`, successful responses parse into a
  `WritingEvaluationResult` with all four criteria and at least one correction, and a raised
  Anthropic SDK exception is caught and translated to `status: "error"` with no exception
  propagating out. Prerequisite for FR-5–FR-8's real (non-fake) output shape and FR-10's error
  translation; per the plan, FR-6/FR-7's actual output *quality* still requires a manual smoke
  test against the real API before the epic is considered done — noted here, not closed by this
  task's automated suite.

## Task-3 — writing_submissions + ai_call_log models and migration
- [x] Status: Done
- Depends on: none (assumes `backend/app/core/db.py` exists, owned by the access-protection
  epic's backlog)
- Goal: Add the SQLAlchemy models for `writing_submissions` (id, question_text, task_type,
  response_text, status [`pending`/`complete`/`failed`], created_at, four criterion scores +
  strengths/weaknesses/corrections as JSON columns) and `ai_call_log` (id, submission_id FK,
  called_at, provider name, status, token/cost usage if available), plus the Alembic migration
  creating both tables.
- Files touched: `backend/app/models/writing_submission.py`,
  `backend/app/models/ai_call_log.py`, `backend/alembic/versions/<rev>_writing_submissions.py`,
  `backend/tests/models/test_writing_submission.py`
- Definition of done: migration applies cleanly (upgrade/downgrade both tested); model tests
  confirm required columns, the status enum values, and the `ai_call_log.submission_id` FK.
  Prerequisite for FR-11 (full persistence) and for the resolved "log usage, no hard cap" open
  question, which `ai_call_log` exists specifically to satisfy.

## Task-4 — WritingSubmissionCreate schema and creation-time validation
- [x] Status: Done
- Depends on: Task-3
- Goal: Add the `WritingSubmissionCreate` Pydantic schema (`response_text: str`,
  `task_type: Literal["task1", "task2"]`, `question_text: str`) with validation that rejects a
  missing/blank `response_text` or `question_text`, and rejects a `task_type` that isn't
  `task1`/`task2`.
- Files touched: `backend/app/schemas/writing_submission.py` (adds `WritingSubmissionCreate`
  only — `WritingSubmissionSummary`/`WritingSubmissionDetail` are added in Task-6),
  `backend/tests/schemas/test_writing_submission_schema.py`
- Definition of done: tests pass. FR-1 (schema rejects a payload missing either `response_text`
  or `question_text`); FR-2 (schema rejects any `task_type` other than `task1`/`task2`); FR-3
  (schema rejects a whitespace-only `response_text`).

## Task-5 — Evaluation service: orchestration, timeout wrapper, FR-10 failure path
- [x] Status: Done
- Depends on: Task-1, Task-2, Task-3, Task-4
- Goal: Implement `services/writing_coach.py`'s submission-creation path: validate the incoming
  `WritingSubmissionCreate` (re-asserting FR-1/FR-2/FR-3 at the service boundary before any AI
  call is made), call `get_ai_provider().evaluate_writing()` wrapped in a ~25s timeout, write the
  `writing_submissions` row (status `complete` or `failed`) and a corresponding `ai_call_log` row
  for every attempted call (success, provider error, or timeout alike), and map any
  timeout/provider failure into the same `status: "error"`-derived FR-10 failure path (preserve
  `response_text`/`question_text`, no exception raised out of the service).
- Files touched: `backend/app/services/writing_coach.py`,
  `backend/tests/services/test_writing_coach_service.py`
- Definition of done: tests pass, exclusively against **`FakeAIProvider` from Task-1** — no real
  Claude/Anthropic call anywhere in this suite. FR-1/FR-3: a request missing/blank
  `response_text` or `question_text` is rejected before `AIProvider` is ever called (fake
  asserted not-called). FR-2: the request object passed to `evaluate_writing()` carries the
  submitted `task_type` unchanged. FR-10: a `FakeAIProvider` configured to return `status:
  "error"` or to exceed the timeout both result in a `failed`-status row with the original
  `response_text`/`question_text` intact, and no exception propagates. Every call attempt
  (success or failure) writes exactly one `ai_call_log` row — reflecting the resolved "log usage,
  no hard cap" decision. A second call with the same `question_text`/`task_type` and a revised
  `response_text` creates an independent second `writing_submissions` row — reflecting the
  resolved "resubmission is a new row, never an overwrite or linked revision" decision.

## Task-6 — Four-criteria and specificity enforcement (FR-5–FR-8)
- [x] Status: Done
- Depends on: Task-1, Task-5
- Goal: Add `WritingSubmissionSummary`/`WritingSubmissionDetail` schemas that make all four
  criterion scores required fields (never optional, never replaceable by a single combined
  score alone) and require the corrections list to have at least one entry with non-empty
  `original`/`corrected` fields. Extend the service to treat a `FakeAIProvider` result with zero
  corrections as an invalid provider response (mapped to the same FR-10 failure path, not
  silently accepted).
- Files touched: `backend/app/schemas/writing_submission.py` (adds `WritingSubmissionSummary`,
  `WritingSubmissionDetail`), `backend/app/services/writing_coach.py`,
  `backend/tests/schemas/test_writing_submission_schema.py`,
  `backend/tests/services/test_writing_coach_service.py`
- Definition of done: tests pass, using **`FakeAIProvider` fixtures only** (varied canned
  results, including a zero-corrections result) — no real Claude call. FR-5: schema test asserts
  `WritingSubmissionDetail` requires four distinct, independently-set criterion score fields.
  FR-6: schema/service test asserts each criterion's feedback field is a non-empty string
  sourced from the provider result (shape-level check only — FR-6's actual specificity is the
  manual-verification gap noted in Task-2, not provable by a mocked unit test). FR-7: schema
  test asserts at least one correction with non-empty `original`/`corrected`; service test
  asserts a zero-corrections `FakeAIProvider` result is rejected into the failure path. FR-8:
  schema test asserts there is no `WritingSubmissionDetail` variant exposing an overall score
  without the four criterion scores and FR-6/FR-7 feedback alongside it (one schema, not an
  optional-fields shape).

## Task-7 — Backend in-progress-state contract (FR-9)
- [x] Status: Done
- Depends on: Task-5
- Goal: Verify and lock in the guarantee that makes FR-9 satisfiable purely as a frontend
  loading state (per the plan's Approach A/C): a `writing_submissions` row is only ever
  persisted once `evaluate_writing()` has resolved (to `complete` or `failed`); no row is ever
  written or observable with status `pending`. This closes the backend side of "no blank,
  frozen, or ambiguous state" — there is no intermediate persisted state a client could
  poll into and misread as a silent failure.
- Files touched: `backend/tests/services/test_writing_coach_service.py` (extends; may require
  no production code change if Task-5 already satisfies this — this task is the explicit test
  proving it)
- Definition of done: tests pass, using `FakeAIProvider` (including a fake with an artificially
  delayed response) — no real Claude call. FR-9: asserts no query against `writing_submissions`
  during an in-flight `evaluate_writing()` call returns a `pending`-status row for that
  submission; the row appears only after the call resolves, with status `complete` or `failed`.

## Task-8 — Retrieval service: past submissions (FR-11–FR-15)
- [x] Status: Done
- Depends on: Task-3, Task-5
- Goal: Add `get_submission_list()` and `get_submission_detail(id)` to
  `services/writing_coach.py` — list returns summaries ordered by recency; detail returns the
  full stored feedback for one submission. Both distinguish "no submissions exist" from a
  genuine query/database failure (raise/return distinguishably) so the router/frontend layers
  have enough signal to satisfy FR-14/FR-15's distinct wording later.
- Files touched: `backend/app/services/writing_coach.py`,
  `backend/tests/services/test_writing_coach_service.py`
- Definition of done: tests pass (DB-level integration tests, no AI call involved in retrieval).
  FR-11: create a submission via Task-5's path, then fetch it via `get_submission_detail()`
  through a separate DB session (simulating a later session) — `response_text`, `question_text`,
  `task_type`, and full feedback round-trip unchanged. FR-12:
  `get_submission_list()` items include `created_at`, `task_type`, and per-criterion/overall
  scores. FR-13: `get_submission_detail()` returns all four criterion scores,
  strengths/weaknesses, and corrections identical (byte-for-byte) to what was stored at creation.
  FR-14: `get_submission_list()` on an empty table returns an empty list distinctly (not an
  exception) so callers can render the FR-14 empty-state message. FR-15: a genuine query failure
  (e.g., simulated DB error) raises/returns a distinguishable outcome from the empty-list case.

## Task-9 — POST /api/writing-coach/submissions (create + evaluate endpoint)
- [x] Status: Done
- Depends on: Task-5, Task-7
- Goal: Add the router and wire `POST /api/writing-coach/submissions` to
  `services/writing_coach.py`'s creation path, behind `require_learner`. Invalid payloads
  (FR-1/FR-2/FR-3) return a 4xx before any AI call; valid payloads return the full result
  synchronously in the same response, including the FR-10 failure shape when evaluation fails.
- Files touched: `backend/app/routers/writing_coach.py` (POST route only),
  `backend/tests/routers/test_writing_coach_router.py`
- Definition of done: tests pass with the service's `AIProvider` dependency overridden to
  `FakeAIProvider` — no real Claude call reaches this router's tests. FR-1/FR-2/FR-3: invalid
  payloads rejected with a 4xx, fake asserted not-called. FR-9: the endpoint does not return
  until `evaluate_writing()` resolves, so the frontend has exactly one outstanding request to
  show a loading state against (no polling contract to build). FR-10: a `FakeAIProvider` failure
  produces a response the frontend can distinguish from success and retry against, without the
  original text being lost server-side. FR-16: a request without a valid learner session returns
  401/403 and creates no submission row (fake asserted not-called).

## Task-10 — GET submissions list + detail endpoints
- [x] Status: Done
- Depends on: Task-8, Task-9
- Goal: Add `GET /api/writing-coach/submissions` (list) and
  `GET /api/writing-coach/submissions/{id}` (detail) to the same router, both behind
  `require_learner`, wired to Task-8's service functions.
- Files touched: `backend/app/routers/writing_coach.py` (GET routes, after Task-9's POST route),
  `backend/tests/routers/test_writing_coach_router.py`
- Definition of done: tests pass (no AI call involved — pure DB retrieval through the router).
  FR-12: list response items include date, task type, and score detail. FR-13: detail response
  matches the stored feedback exactly. FR-14: an empty list returns a response shape the
  frontend can render as the FR-14 empty-state message rather than a blank list. FR-15: a
  simulated retrieval failure returns a response distinguishable from the empty-list case. FR-16
  (fully covered here): all three routes in `writing_coach.py` — POST, GET list, GET detail — are
  asserted to depend on `require_learner`; an unauthenticated request to any of the three returns
  401/403 and touches no submission data.

## Task-11 — Frontend models, repository, and facade
- [x] Status: Done
- Depends on: Task-9, Task-10
- Goal: Add the frontend data layer for this module, mirroring `src/app/study-plan/`'s shape:
  types-only models, a repository that is the sole point of contact with `api-client` (submit,
  list, get-by-id), and a facade holding submission-list state and current-submission-in-progress
  state as signals, exposing `submit()`, `loadSubmissions()`, `loadSubmission(id)`.
- Files touched: `src/app/writing-coach/models/writing-submission.model.ts`,
  `src/app/writing-coach/data/writing-coach.repository.ts`,
  `src/app/writing-coach/data/writing-coach.repository.spec.ts`,
  `src/app/writing-coach/state/writing-coach.facade.ts`,
  `src/app/writing-coach/state/writing-coach.facade.spec.ts`,
  `src/app/writing-coach/writing-coach.routes.ts`
- Definition of done: tests pass, mocking `api-client` only (no real backend call, no AI call —
  this layer never talks to `AIProvider` directly). Repository methods call the correct
  endpoints/payload shapes matching Task-9/Task-10's contract; facade exposes loading/error/data
  signals correctly reflecting repository outcomes. Prerequisite for FR-4/FR-9/FR-10 (Task-12)
  and FR-12–FR-15 (Task-13, Task-14) UI behavior — no FR independently satisfied end-to-end by
  this task alone.

## Task-12 — Frontend: submission form (FR-4, FR-9, FR-10)
- [x] Status: Done
- Depends on: Task-11
- Goal: Build the submission form page (task type, question text, response text) with
  abandon-without-saving, in-progress, and failure-with-retry states. No wireframe exists yet
  for this epic (`Specification.md`'s header: "Related UX: none yet") — this layout is
  provisional, inferred directly from the User Scenarios/FRs, and should be revisited once a
  wireframe is produced.
- Files touched: `src/app/writing-coach/pages/submit/submit.component.ts`,
  `src/app/writing-coach/pages/submit/submit.component.html`,
  `src/app/writing-coach/pages/submit/submit.component.spec.ts`
- Definition of done: tests pass against the Task-11 facade with its repository call
  mocked/stubbed — no real backend or AI call. FR-4: navigating away before submit calls no
  facade/repository method and creates no submission. FR-9: while the facade's submit call is
  pending (unresolved), the component renders a loading indicator, never a blank state. FR-10:
  on a failure result, the entered `response_text`/`question_text` remain populated in the form
  and a retry action resubmits the same payload without requiring re-entry.

## Task-13 — Frontend: past-submissions list (FR-12, FR-14, FR-15)
- [x] Status: Done
- Depends on: Task-11
- Goal: Build the past-submissions list page showing date, task type, and enough score detail
  to distinguish entries, with the FR-14 empty state and FR-15 empty-vs-error wording. Provisional
  layout — no wireframe exists yet, same caveat as Task-12.
- Files touched: `src/app/writing-coach/pages/submission-list/submission-list.component.ts`,
  `src/app/writing-coach/pages/submission-list/submission-list.component.html`,
  `src/app/writing-coach/pages/submission-list/submission-list.component.spec.ts`
- Definition of done: tests pass against the Task-11 facade with its repository call
  mocked/stubbed — no real backend call. FR-12: rendered list items show date, task type, and
  score detail. FR-14: given zero submissions, renders the FR-14 empty-state message directing
  the learner to submit one, not a blank list. FR-15: an empty-but-successful response renders
  the FR-14 message; a failed fetch (mocked repository rejection) renders a distinct
  failure message, asserted via separate test assertions on the rendered text.

## Task-14 — Frontend: submission detail / feedback view (FR-13, FR-15)
- [x] Status: Done
- Depends on: Task-11
- Goal: Build the full-feedback view for one past submission — all four criterion scores,
  strengths/weaknesses, and sentence-level corrections — plus a load-failure state distinct from
  a "not found"/empty case. Provisional layout — no wireframe exists yet, same caveat as Task-12.
- Files touched:
  `src/app/writing-coach/pages/submission-detail/submission-detail.component.ts`,
  `src/app/writing-coach/pages/submission-detail/submission-detail.component.html`,
  `src/app/writing-coach/pages/submission-detail/submission-detail.component.spec.ts`
- Definition of done: tests pass against the Task-11 facade with its repository call
  mocked/stubbed — no real backend call. FR-13: given a mocked detail response, all four
  criterion scores, strengths/weaknesses, and corrections render unchanged from the fetched
  data. FR-15: a failed fetch (mocked repository rejection) renders wording visibly distinct
  from any "nothing here" state, so a learner can tell a genuine load failure from there simply
  being no such submission.
