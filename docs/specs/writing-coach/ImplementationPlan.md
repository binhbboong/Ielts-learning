# Implementation Plan: AI-Assisted Writing Coaching
Spec: docs/specs/writing-coach/Specification.md

## Sequencing Dependency (read first)

This plan owns `backend/app/ai/provider.py` (the `AIProvider` abstract interface) and
`backend/app/ai/claude_provider.py` (its Claude implementation) — the first two files that give
`docs/architecture/Architecture.md`'s "AI Provider Layer" concrete shape. The `speaking-coach`
epic's plan (written in parallel, order relative to this one unknown) depends on
`evaluate_speaking()` existing on that same interface. This plan implements and tests only
`evaluate_writing()`; `evaluate_speaking()`, `generate_quiz()`, and `chat()` are declared as
abstract methods with a fixed signature shape (see ADR below) but have no implementation body
here — that is out of scope for this epic and belongs to whichever plan owns them.
`backend/app/core/db.py`, `backend/app/core/security.py` (`require_learner`), and
`src/app/core/api/api-client.ts` are owned by the `access-protection` epic's plan; this plan
assumes they exist and only imports them.

## Approach — how a Writing submission is evaluated end-to-end

**Approach A — Synchronous: the endpoint calls `AIProvider.evaluate_writing()` inline and
returns the full result in the same HTTP response.** `POST /api/writing-coach/submissions`
validates the request (FR-1/FR-2/FR-3), calls `evaluate_writing()` directly, persists the
result on success, and returns it — one request, one response, no polling. Simplest possible
flow: FR-9 ("explicit in-progress indication") is satisfied entirely on the frontend by showing
a loading state for the duration of one outstanding HTTP call, and FR-10 ("failure preserves
input, explicit failure state, retry without re-entering text") is satisfied by the frontend
holding the submitted text in local component state until a 2xx response is received, and
resubmitting the same payload on retry. Risk: this ties up a Vercel serverless function for the
full duration of the AI call, which `Architecture.md`'s Known Constraints flags as an open risk
for Speaking specifically.

**Approach B — Asynchronous: the endpoint stores the submission as "pending," evaluation runs
out-of-band, and the frontend polls a status endpoint until the result is ready.** Requires a
`status` column (`pending`/`complete`/`failed`) on the submission table, a mechanism to trigger
the background evaluation (Vercel background function, queue, or a fire-and-forget task), a
second `GET /api/writing-coach/submissions/{id}` polling endpoint, and frontend polling logic
(interval + stop condition). More resilient to a slow AI call exceeding the serverless execution
limit, but every FR-9/FR-10 behavior now has to be built twice as many states to cover
(pending-but-not-yet-polled, polling-in-progress, poll-detected-failure) and needs a background
execution mechanism that does not yet exist anywhere in this codebase.

**Approach C — Hybrid: synchronous by default, with a server-side timeout that converts to a
"failed, retry" response if the AI call runs unexpectedly long**, rather than truly moving to a
background job. Keeps Approach A's simplicity for the common case while capping worst-case
request duration below the Vercel limit. Adds one piece of complexity (a timeout wrapper around
the `evaluate_writing()` call) but none of Approach B's new moving parts.

**Recommendation: Approach A (synchronous), with Approach C's timeout wrapper folded in as a
cheap safety margin — not a full Approach B.** Reasoning:

- Writing evaluation is **one** AI call (`evaluate_writing()` alone), unlike Speaking's chained
  Speech-to-Text-then-AI-call, which is the specific case `Architecture.md` flags as "could be
  at real risk." A single Claude call producing four criterion scores plus sentence-level
  corrections is a normal, bounded-latency text-generation request — well inside typical
  serverless execution limits (commonly 10s–60s on free/hobby tiers, up to 300s on paid Vercel
  plans) even accounting for occasional slow responses. Speaking's two-step chain is the
  documented risk case, not Writing's single call.
- FR-9 and FR-10 are both fully satisfiable by a single request/response cycle plus ordinary
  frontend loading/error UI — nothing in the spec (re-read FR-1 through FR-16) requires a
  "check back later" experience; FR-9's "explicit in-progress indication" reads naturally as "a
  spinner while the request is outstanding," not a multi-visit wait.
- Approach A costs zero new backend infrastructure (no status column, no background trigger, no
  polling endpoint) versus Approach B's several new pieces, all for a risk that is not actually
  likely to materialize for this specific epic.
- The one gap Approach A alone leaves — an unexpectedly slow provider call blowing through
  Vercel's limit with no controlled failure — is exactly what a request-level timeout closes at
  near-zero cost: wrap the `evaluate_writing()` call with a timeout comfortably under the
  platform limit (e.g. 25s against a 30s+ budget); a timeout maps to the same FR-10 failure path
  as any other provider error (`status: "error"` result), so no new state is introduced, only a
  bound on how long the existing "in-progress" state can last before it becomes "failed."
- If real-world latency later proves this wrong, Approach B remains available as a follow-up
  without reworking the data model — `WritingSubmission` already has a natural `status` field
  (see File/Module Structure) that Approach B would only need to start actually using instead of
  always writing rows as already-complete-or-failed.

## Open Questions — Resolved

**Submission limit: no hard cap at launch; log every AI call for the learner's own cost
visibility instead.** The PRD/spec constrain AI usage to be cost-conscious and
explicit-submission-only (never automatic/background), but this is a solo learner spending their
own money via their own `AI_PROVIDER` credentials — there is no second party to protect from
overuse, so a system-enforced cap (daily/weekly/total) would only ever inconvenience the one
legitimate user with no corresponding benefit. Instead, every call to `evaluate_writing()` is
logged (timestamp, submission id, estimated/actual token usage or cost if the provider response
exposes it) to a simple `ai_call_log` table, giving the learner the information they'd need to
notice and self-limit their own usage if they ever wanted to — which directly serves the same
underlying cost-consciousness goal without adding a hard-block failure mode that FR-1/FR-9 would
otherwise need a "limit reached" state for. If real cost data after launch shows this was wrong,
a cap can be added later as a small, additive change (reject at the router level once a computed
threshold is hit) — nothing in this plan forecloses it.

**Revise-and-resubmit: yes, in scope, modeled as a new, independent submission row referencing
the same question — never an overwrite of the original.** A resubmission is simply another
`POST /api/writing-coach/submissions` call with the same `question_text`/`task_type` and revised
`response_text`; nothing distinguishes it from an unrelated new submission at the data-model
level except that both rows happen to share the same question text. This satisfies the informal
source workflow's revise-and-see-if-it-improved goal (the learner can find both submissions in
their FR-12 list and compare) without inventing a new "revision" concept, a linking foreign key,
or a before/after comparison UI — none of which FR-1 through FR-16 actually require, and the
spec's own Out of Scope section explicitly excludes in-place editing of an already-evaluated
submission's stored feedback. This reading keeps FR-11 through FR-15 ("retrieve past
submissions") doing double duty as the resubmission-history mechanism for free: every attempt at
a question is just another row the learner can browse and reopen. A dedicated "linked revision +
before/after diff" feature remains a clean, additive future epic if ever prioritized, built on
top of this without a data migration (the rows already exist; only a new query/grouping-by-
question-text view would be added).

## File/Module Structure

No wireframe exists yet for this epic (`Specification.md`'s header states "Related UX: none
yet") — the two Angular pages below are inferred directly from the User Scenarios/FRs and should
be treated as provisional until a wireframe is produced, not as a UX decision made by this plan.

| Path | Responsibility |
|------|-----------------|
| `backend/app/ai/provider.py` | Defines the abstract `AIProvider` interface (`evaluate_writing`, `evaluate_speaking`, `generate_quiz`, `chat`) — see ADR for exact signatures. Zero vendor SDK imports. |
| `backend/app/ai/schemas.py` | Pydantic request/result models for all four `AIProvider` methods (`WritingEvaluationRequest`/`Result`, `SpeakingEvaluationRequest`/`Result`, etc.) — the typed contract every provider implementation and every caller shares. |
| `backend/app/ai/claude_provider.py` | `ClaudeProvider(AIProvider)`: implements `evaluate_writing()` by building the four-criterion prompt, calling the Anthropic SDK, and parsing/validating the response into `WritingEvaluationResult`; catches all Anthropic SDK exceptions internally and translates them to `status: "error"` results. `evaluate_speaking`/`generate_quiz`/`chat` are implemented as stubs (`NotImplementedError` or minimal pass-through) left for their owning epics to fill in. |
| `backend/app/ai/__init__.py` | Selects and constructs the active provider from the `AI_PROVIDER` env var (currently only `"claude"` → `ClaudeProvider`); exposes a single `get_ai_provider()` factory function for dependency injection into routers. |
| `backend/app/models/writing_submission.py` | SQLAlchemy model for `writing_submissions`: id, question_text, task_type, response_text, status (`pending`/`complete`/`failed`), created_at, and the four criterion scores + strengths/weaknesses/corrections as JSON columns once evaluation completes. No learner_id column (single-learner simplification). |
| `backend/app/models/ai_call_log.py` | SQLAlchemy model for `ai_call_log`: id, submission_id (FK), called_at, provider name, status, cost/token usage if available — the log resolving the submission-limit open question. |
| `backend/app/schemas/writing_submission.py` | Pydantic request/response schemas for the router: `WritingSubmissionCreate` (response_text, task_type, question_text), `WritingSubmissionSummary` (list view: id, created_at, task_type, scores), `WritingSubmissionDetail` (full feedback). |
| `backend/app/services/writing_coach.py` | Orchestrates one submission: validates non-blank input (FR-3), calls `get_ai_provider().evaluate_writing()` with a timeout wrapper, writes the `writing_submissions` row and the `ai_call_log` row, and maps provider failure/timeout to the FR-10 failure path. Owns all business logic; no HTTP or SQL-session concerns beyond what's passed in. |
| `backend/app/routers/writing_coach.py` | Exposes `POST /api/writing-coach/submissions` (create + evaluate, FR-1–FR-10), `GET /api/writing-coach/submissions` (list, FR-12/FR-14), `GET /api/writing-coach/submissions/{id}` (detail, FR-13/FR-15). Depends on `require_learner` on every route (FR-16). |
| `backend/alembic/versions/<rev>_writing_submissions.py` | Migration creating `writing_submissions` and `ai_call_log` tables. |
| `src/app/writing-coach/models/writing-submission.model.ts` | Frontend types mirroring the backend schemas (submission create payload, summary, detail) — types only. |
| `src/app/writing-coach/data/writing-coach.repository.ts` | Sole point of contact with `api-client` for this module: submit, list, get-by-id — mirrors `study-plan.repository.ts`'s shape (thin wrapper methods, no business logic). |
| `src/app/writing-coach/state/writing-coach.facade.ts` | Holds submission-list state and current-submission-in-progress state as signals; exposes `submit()`, `loadSubmissions()`, `loadSubmission(id)` — mirrors `study-plan.facade.ts`'s shape (facade is the only service pages call into). |
| `src/app/writing-coach/pages/submit/submit.component.ts` | The submission form (task type, question text, response text) plus in-progress/failure states (FR-4, FR-9, FR-10). No wireframe exists yet — provisional, see note above. |
| `src/app/writing-coach/pages/submission-list/submission-list.component.ts` | Past-submissions list with FR-14 empty state and FR-15 error-vs-empty distinction. Provisional, no wireframe. |
| `src/app/writing-coach/pages/submission-detail/submission-detail.component.ts` | Full feedback view for one past submission (FR-13). Provisional, no wireframe. |
| `src/app/writing-coach/writing-coach.routes.ts` | Declares this module's routes for mounting into the App Shell nav. |

## Testing Strategy

Every AI-calling path is tested against a mock/stub `AIProvider` (a fake implementing the same
interface returning canned `WritingEvaluationResult` objects) — **no test in this suite calls
the real Claude API**, so the suite stays fast and incurs no real AI cost. `ClaudeProvider`
itself gets a narrow, separate test that mocks only the Anthropic SDK client (not the whole
provider) to verify prompt construction and response-parsing/error-translation logic. All rows
are written test-first per constitution principle 2.

| Requirement | Verified by |
|---|---|
| FR-1 (require both response text and task/question) | `writing_coach.py` service test: submitting with response_text or question_text missing is rejected before `AIProvider` is ever called (mock asserted not-called). |
| FR-2 (require Task 1 vs Task 2) | Schema test: `WritingSubmissionCreate` without a valid `task_type` fails validation. Service test: `evaluate_writing()`'s request object receives the submitted task_type unchanged. |
| FR-3 (reject empty/blank response) | Service test: whitespace-only `response_text` is rejected pre-AI-call (mock asserted not-called), mirroring FR-1's pattern. |
| FR-4 (abandon in-progress response, nothing saved) | Frontend `submit.component` test: navigating away before submit calls no repository method and creates no submission. |
| FR-5 (four distinct criterion scores, never one combined only) | `writing_coach.py` service test with a mock `AIProvider` returning a full `WritingEvaluationResult`: asserts the persisted/returned submission has four distinct, independently-set criterion scores. Schema test: `WritingSubmissionDetail` makes all four criterion fields required (not optional). |
| FR-6 (criterion feedback references specific submission text) | Service/schema test: asserts each criterion's feedback field is a non-empty string sourced from the mock result (shape-level check); the actual quality of Claude's references is a prompt-engineering concern verified manually against `ClaudeProvider`, not something a mocked unit test can prove — noted as a manual-verification gap below. |
| FR-7 (at least one sentence-level correction, original + corrected) | Schema test: `WritingSubmissionDetail`'s corrections list requires at least one entry with both `original` and `corrected` non-empty fields; service test asserts a mock result with zero corrections is treated as an invalid/error provider response, not silently accepted. |
| FR-8 (overall score never shown alone) | Schema test: `WritingSubmissionDetail` has no schema variant that includes an overall score field without also requiring the four criterion scores and feedback fields alongside it (single schema, not an optional-fields-only shape). |
| FR-9 (explicit in-progress indication, never blank/frozen) | Frontend `submit.component` test: while the repository call is pending (unresolved promise/mock), the component renders a loading indicator, not a blank state. |
| FR-10 (preserve text on failure, explicit failure state, retry without re-entering) | Service test: mock `AIProvider` returns `status: "error"` → service writes a `failed`-status submission row and does not raise; the original response_text/question_text are still present on that row. Frontend test: on a failure response, the form's entered text remains populated and a retry action resubmits the same payload. Timeout wrapper test: a mock provider call that exceeds the configured timeout resolves to the same `status: "error"` failure path. |
| FR-11 (persist every successful submission fully, retrievable in a later session) | Repository/service integration test: create a submission, then fetch it via a separate `GET` call (simulating a new session) and assert response_text, question_text, task_type, and full feedback all round-trip unchanged. |
| FR-12 (list shows date, task type, enough score detail) | Router test: `GET /api/writing-coach/submissions` response items include created_at, task_type, and at least the overall/per-criterion scores. |
| FR-13 (reopen full original feedback unchanged) | Router test: `GET /api/writing-coach/submissions/{id}` returns all four criterion scores, strengths/weaknesses, and corrections identical to what was stored at creation time (byte-for-byte comparison against the create-time result). |
| FR-14 (empty state directs learner to submit) | Frontend `submission-list.component` test: given zero submissions, renders the FR-14 empty-state message, not a blank list. |
| FR-15 (distinguish "nothing yet" vs "failed to load") | Frontend `submission-list.component` and `submission-detail.component` tests: an empty-but-successful response renders the FR-14 message; a failed fetch (mock repository rejecting) renders a distinct failure message using different wording, asserted via distinct test assertions on the rendered text. |
| FR-16 (never another learner's submissions) | Router test: every route in `writing_coach.py` is asserted to depend on `require_learner`; a request without a valid session returns 401/403 and touches no submission data. Given the single-learner simplification, there is structurally only one learner's data to protect against unauthenticated access, not cross-learner leakage between two learners. |

**Manual-verification gap, stated explicitly:** FR-6's "specific enough to reference the
learner's own text, not generic" is a prompt-quality property of `ClaudeProvider`'s actual
output, which a mocked-`AIProvider` unit test cannot verify (the mock's output is whatever the
test author wrote). This plan's automated suite verifies the *shape* is enforced (non-empty,
sourced-from-result fields); verifying Claude's actual output quality against FR-6/FR-7 requires
a manual smoke test against the real API during implementation (not part of the automated,
cost-free suite) before this epic is considered done.

## Constitution Check

- **Tests-first (principle 2):** every row above is written as a failing test before the
  corresponding code exists; the AI-calling path is tested exclusively against a mock
  `AIProvider`, never the real Claude API, so the test suite stays fast and free to run — no
  exception requested.
- **Small, reviewable units (principle 4):** `provider.py`/`schemas.py` (interface),
  `claude_provider.py` (implementation), `writing_coach.py` (orchestration), and the
  router/frontend layers are separable, independently reviewable changes.
- **Upstream docs are the contract (principle 1):** this plan does not diverge from
  `Architecture.md`'s AI Provider Layer description or the fullstack-vercel-claude-architecture
  ADR; the two Open Questions resolved above fill gaps the spec explicitly left open rather than
  overriding anything already decided.
- **Docs are durable (principle 6):** the ADR below is the source of truth for the `AIProvider`
  interface shape that `speaking-coach`'s plan must align with; this plan does not implement
  `evaluate_speaking()`, only declares its slot on the interface.

## ADR

The `AIProvider` interface's exact method signatures and request/result shapes are a
costly-to-reverse, cross-epic API-shape decision — the implementation-planning skill's ADR
trigger ("defining an API shape other code will depend on") applies directly, sharpened by the
fact that `speaking-coach`'s plan depends on this same interface without a shared review step.
See `docs/adr/2026-07-29-ai-provider-interface-shape.md`.

**Requested `docs/adr/DECISIONS.md` row (not added by this plan — seven other agents are
writing plans in parallel; append separately):**

```
| 2026-07-29 | [AIProvider interface: typed request/result pairs per method, synchronous, status-discriminated results, no vendor exceptions crossing the boundary](2026-07-29-ai-provider-interface-shape.md) | Accepted | — | writing-coach, speaking-coach |
```
