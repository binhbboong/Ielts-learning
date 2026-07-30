# Implementation Plan: AI-Assisted Speaking Coaching
Spec: docs/specs/speaking-coach/Specification.md

## Approach

This epic is new under the full-stack architecture (`docs/adr/2026-07-29-fullstack-vercel-claude-architecture.md`,
`docs/architecture/Architecture.md`) — nothing has been implemented against it before. The
open question this plan must resolve is the end-to-end evaluation flow's execution model,
because `Architecture.md`'s Known Constraints section names Speaking specifically as the
scenario most at risk of exceeding Vercel's (still-unresolved) serverless execution-time
limit: a submission requires two chained external calls — the Speech-to-Text integration,
then `AIProvider.evaluate_speaking()` — inside what would naturally be a single request.

**Approach A — Synchronous end-to-end.** One `POST /speaking-submissions` request does
everything: upload the audio, call Speech-to-Text, call `AIProvider.evaluate_speaking()`, and
return the completed result in the response body.
- Cost: simplest possible frontend (one call, one await, no polling/orchestration code) and
  the simplest possible backend (one handler, no status machine).
- Risk: exactly the scenario `Architecture.md` flags — two sequential external calls (network
  round-trip to a Speech-to-Text vendor, then to Claude) sharing one serverless invocation's
  time budget. A ~2-minute IELTS Part 2 recording is the slowest case and the most likely to
  tip this over whatever Vercel's actual limit is. This is a real, not theoretical, risk given
  the constraint is already documented as unresolved specifically for this epic.
- Also risky independent of infrastructure: FR-6 and FR-10 require transcription failure and
  evaluation failure to be presented as *distinct, separately retryable* states. A single
  synchronous call has no natural place to persist "transcription already succeeded, only
  evaluation needs retrying" — that state has to be invented anyway, which erodes most of this
  approach's simplicity advantage.
- **Rejected.**

**Approach B — Asynchronous, step-tracked processing with client-driven orchestration
(recommended).** Creating a submission is a single fast write (no external call), returning
immediately with a `PROCESSING` status. Transcription and evaluation are each triggered by
their own separate backend endpoint, so each external call gets its own execution budget
instead of sharing one. Status and the transcript are persisted after every step, so the
current state of any submission is always durable and re-readable, not held in memory across a
long-running request. The Angular frontend chains the steps automatically right after
submission, and resumes an unfinished chain automatically whenever the learner reopens a
`PROCESSING` submission later.
- Cost: more endpoints and a small status model to build and test versus Approach A. The
  frontend needs resume-on-view orchestration logic, not just a single await.
- Risk: processing only advances when some client actively drives it — if the learner submits
  a recording and never reopens the app, that submission never finishes. No server-side worker
  exists to force it forward. Documented and accepted below rather than solved with new
  infrastructure (see Risks).
- Makes easy later: this is a direct, low-friction fit for FR-6/FR-10 (each step has its own
  persisted state and its own retry endpoint, so "retry just the failed step" is exactly what
  the model already does) and FR-11/FR-12 (a real, durable `PROCESSING` state that survives the
  learner leaving and coming back). It also sidesteps the execution-time risk by construction,
  without needing to know Vercel's actual limit.
- Full design in `docs/adr/2026-07-29-speaking-async-step-tracked-processing.md`.

**Approach C — Asynchronous processing with a true server-side background worker/queue** (a
cron sweep of pending submissions, or an external queue/job service that runs independently of
any client being open).
- Cost: real added infrastructure — either a queue/worker service (new vendor, new cost,
  against the PRD's cost-consciousness constraint) or Vercel Cron, whose Hobby-tier invocation
  frequency (as infrequent as once/day) is too coarse to give timely results for an
  interactive learner-facing feature.
- Risk: meaningfully more moving parts for a solo project with one user, most of the time idle.
- **Deferred, not rejected.** Approach B's schema and endpoints do not need to change to add
  this later — a cron sweep or queue consumer would call the exact same `transcribe`/`evaluate`
  endpoints Approach B already defines; only the trigger mechanism would be added on top if
  "the learner never returns" ever proves to be a real problem in practice.

**Recommendation: Approach B.** It takes the flagged Vercel execution-time risk seriously by
removing it structurally (each external call gets its own request/response cycle) rather than
hoping the actual limit turns out to be generous enough, it fits FR-6/FR-10's
separately-retryable-failure-states requirement naturally instead of needing extra state
bolted on, and it avoids Approach C's added infrastructure and cost that a solo, cost-conscious
project doesn't yet need. The accepted trade-off — a submission left completely unattended
never finishes on its own — is reasonable for a single learner who is also the only person who
will ever open the app to check on it, and is written down as a risk rather than assumed
silently.

### Status model

Four learner-facing statuses, matching FR-13's wording exactly: `PROCESSING`,
`TRANSCRIPTION_FAILED`, `EVALUATION_FAILED`, `COMPLETED`. There is no separate "which step is
next" column — it is derived from whether `transcript` is populated:

| status | transcript | feedback | meaning / next action |
|---|---|---|---|
| `PROCESSING` | null | null | not yet transcribed — next: call transcribe |
| `PROCESSING` | present | null | transcribed, not yet evaluated — next: call evaluate |
| `TRANSCRIPTION_FAILED` | null | null | transcription failed — learner-initiated retry calls transcribe again |
| `EVALUATION_FAILED` | present | null | evaluation failed — learner-initiated retry calls evaluate again (no re-transcription) |
| `COMPLETED` | present | present | done — transcript and all feedback viewable (FR-14) |

The frontend auto-resumes both `PROCESSING` rows (no learner action needed — this is what
makes "leave and come back" in FR-12 work without a manual button); the two `*_FAILED` rows
only ever advance via an explicit Retry action, per FR-6/FR-10's "let the learner retry"
language, never silently auto-retried.

### Resolving the spec's open questions

The spec left five questions for planning to resolve. Four are resolved here with stated
reasoning; one is left open because it is a product decision, not a technical one.

1. **Max recording length — resolved: 120 seconds (2 minutes) per submission, one global cap.**
   IELTS Speaking's longest single turn is Part 2's cue-card response, which the exam format
   itself caps at 1–2 minutes; Part 1 and Part 3 answers are individually shorter. A single
   120-second hard cap comfortably covers the longest legitimate answer without inviting
   open-ended, cost-driving recordings. Enforced client-side (recorder stops/warns at the
   limit) and re-validated server-side on upload (reject audio exceeding the corresponding
   max duration/file size) as defense in depth. One global cap (rather than a per-part cap) is
   a deliberate simplification — nothing in the spec requires per-part limits, and a single
   number is far simpler to implement, test, and explain to the learner.
   **Frequency/usage limit is NOT resolved here** — left open (see Risks) because it is a
   product/cost-policy decision (how many submissions per day/week is "cost-conscious enough")
   that this plan should not invent unilaterally; the schema does not preclude adding a simple
   per-day count check to the create endpoint later if a limit is set.
2. **Part 1/2/3 structure — resolved: a `part` field on the question, not separate tables.**
   `speaking_questions.part` is an enum (`PART_1`, `PART_2`, `PART_3`); there is one
   `speaking_submissions` table regardless of which part the answered question belongs to.
   This is the minimal model that still lets the UI group/filter questions by part (useful for
   question selection) without duplicating the submission/evaluation pipeline three times. The
   three IELTS Speaking criteria in scope (Fluency & Coherence, Lexical Resource, Grammar) are
   evaluated identically regardless of part for this MVP — no part-specific feedback framing is
   built now, since nothing in the spec requires it.
3. **Question source — resolved: a curated, seeded question bank**, consistent with how
   `study-plan-execution` seeds its 180-day content (`src/app/study-plan/data/study-plan-seed.ts`).
   A `speaking_questions` table is populated via an Alembic data migration / seed script
   (`backend/app/data/speaking_questions_seed.py`) with a starter set of IELTS-style prompts
   tagged by `part`. Free-text learner-authored prompts are rejected: FR-1 requires every
   submission to reference a real question/prompt, and an uncontrolled free-text prompt would
   make evaluation harder to keep consistent and is not something the spec's user scenarios ask
   for. As with study-plan's seed, authoring the actual prompt *content* (real, well-formed
   IELTS-style questions per part) is a content task, not a code task — flagged under Risks,
   same as study-plan's "Content authoring risk."
4. **Re-recording policy — resolved: allowed, as a wholly new, independent submission.**
   Re-recording a response to a question already submitted (and even already completed) is
   allowed and simply creates a new `speaking_submissions` row referencing the same
   `question_id` — no versioning, no linking to the prior submission, no replacement. FR-2
   already frames "a submission" as one audio response tied to one question, and FR-13's list
   is naturally able to show multiple entries for the same question distinguished by date and
   status, so nothing in the data model needs to change to allow this. (Writing-coach's
   sibling spec raises an analogous question but as a genuine revision-linking/before-after
   comparison feature for essays; recordings don't carry the same "improve the same artifact"
   framing, so this plan does not assume the two epics must resolve it identically — they are
   independent submissions either way at the schema level.)
5. **Transcript editability — resolved: NOT editable.** The transcript is stored and displayed
   read-only, exactly as produced by the Speech-to-Text step. FR-5 frames the learner's need as
   being able to *verify* what was captured, not correct it, and evaluating an edited transcript
   would risk scoring the learner's editing/writing skill rather than what they actually said —
   the same risk the spec's own Open Questions text names. If transcription genuinely
   mis-hears something, the existing FR-6 retry-transcription path (or, ultimately,
   re-recording) is the correct remedy, not manual editing.

## File/Module Structure

No wireframe/prototype exists yet for this epic (per the spec's header) — UI-facing rows below
describe structure and responsibility only; none can cite a wireframe file.

### Backend — depended upon, owned by other epics' plans (imported, not modified here)
| Path | Responsibility |
|---|---|
| `backend/app/core/db.py` | SQLAlchemy engine/session + `get_db` dependency (access-protection epic). |
| `backend/app/core/security.py` | `require_learner` dependency gating this router (access-protection epic). |
| `backend/app/ai/provider.py`, `backend/app/ai/claude_provider.py` | `AIProvider` interface incl. `evaluate_speaking()`, and its Claude implementation (writing-coach epic). |

### Backend — owned by this plan
| Path | Responsibility |
|---|---|
| `backend/app/models/speaking_question.py` | SQLAlchemy model for `speaking_questions` (id, `part`, prompt text) — the curated question bank. No `learner_id` (single-learner simplification). |
| `backend/app/models/speaking_submission.py` | SQLAlchemy model for `speaking_submissions` (id, `question_id` FK, `audio_storage_ref`, `transcript`, `status`, per-criterion feedback + band columns, timestamps). No `learner_id`. |
| `backend/app/schemas/speaking_submission.py` | Pydantic request/response schemas: submission create, list-item (question, date, status), detail (transcript + full feedback incl. the always-constant "Not assessed" Pronunciation marker synthesized at serialization time, never stored). |
| `backend/app/services/speech_to_text.py` | Sole caller of the external Speech-to-Text vendor; one function, e.g. `transcribe(audio) -> TranscriptionResult`, isolated so it is the single thing tests mock for FR-4/FR-6. |
| `backend/app/services/speaking_coach.py` | Business logic: create submission (no external call), `run_transcription(submission_id)` (calls `speech_to_text.transcribe`, updates transcript/status per FR-4/FR-6), `run_evaluation(submission_id)` (guards that transcript exists per FR-4, calls `AIProvider.evaluate_speaking()`, updates feedback/status per FR-7–FR-10), and read/list queries for FR-13/FR-14/FR-15. Owns the status-transition rules from the table above. |
| `backend/app/routers/speaking_coach.py` | REST endpoints, all behind `require_learner`: `POST /speaking-questions` (n/a — read-only), `GET /speaking-questions`, `POST /speaking-submissions`, `POST /speaking-submissions/{id}/transcribe`, `POST /speaking-submissions/{id}/evaluate`, `GET /speaking-submissions`, `GET /speaking-submissions/{id}`. Thin — delegates all logic to `speaking_coach.py`. |
| `backend/app/data/speaking_questions_seed.py` | Curated starter question-bank content (per-part prompts), loaded by the Alembic data migration — mirrors `study-plan-seed.ts`'s role for Epic-1. |
| `backend/alembic/versions/<rev>_create_speaking_tables.py` | Migration creating `speaking_questions` and `speaking_submissions`, plus a data-seed step running `speaking_questions_seed.py`. |

### Frontend — owned by this plan (mirrors `src/app/study-plan/`'s shape)
| Path | Responsibility |
|---|---|
| `src/app/speaking-coach/models/speaking-question.model.ts` | `SpeakingQuestion` type (id, part, prompt) — types only. |
| `src/app/speaking-coach/models/speaking-submission.model.ts` | `SpeakingSubmission` type incl. the four-value `status` union and optional transcript/feedback fields — types only. |
| `src/app/speaking-coach/data/speaking-coach.repository.ts` | Sole point of contact with `src/app/core/api/api-client.ts` for this module: question list, create submission, transcribe/evaluate/retry calls, list/detail reads. |
| `src/app/speaking-coach/state/speaking-coach.facade.ts` | Holds submission state; exposes `submit()`, `retryTranscription()`, `retryEvaluation()`; owns the auto-chain-after-submit and auto-resume-on-view orchestration logic described above — the only service pages call into. |
| `src/app/speaking-coach/pages/record-response/record-response.component.ts` (+`.html`) | Question selection + recording capture (client-side 120s cap) + submit; renders the FR-3 "received, processing" confirmation. |
| `src/app/speaking-coach/pages/submission-list/submission-list.component.ts` (+`.html`) | Renders past submissions: question, date, status, distinguishing all four statuses (FR-13, FR-15). |
| `src/app/speaking-coach/pages/submission-detail/submission-detail.component.ts` (+`.html`) | Renders one submission's transcript (independent of evaluation state, FR-5) and, once present, all feedback incl. Pronunciation "not assessed" (FR-7–FR-9, FR-14); renders in-progress and both failure states with a labeled Retry action (FR-6, FR-10, FR-11, FR-15); triggers auto-resume on load for `PROCESSING` rows. |
| `src/app/speaking-coach/speaking-coach.routes.ts` | Declares this module's routes for mounting into the App Shell. |

## Testing Strategy

Per constitution principle 2 (tests before code) and the `test-driven-development` skill,
every row below is written test-first: the failing test is written from the FR before the
corresponding service/router/component code exists. All backend tests mock
`speech_to_text.transcribe()` and `AIProvider.evaluate_speaking()` — no real network call to
either external service ever runs in the test suite, both for speed and because real calls
cost money against the PRD's cost-consciousness constraint.

| Requirement | Verified by |
|---|---|
| FR-1 | Router/service test: `POST /speaking-submissions` without a `question_id` is rejected (422/400) and no row is created. Component test: submit is disabled/blocked in `record-response.component` until a question is selected. |
| FR-2 | Service test: creating a submission persists exactly one row linking one `audio_storage_ref` to one `question_id` — not a list, not multiple rows. |
| FR-3 | Router test: `POST /speaking-submissions` returns 201 with `status=PROCESSING` and `transcript`/feedback fields absent/null, with the `speech_to_text` mock asserted never called during create. Component test: the confirmation state renders immediately from the create response, visibly distinct from later transcript/feedback rendering. |
| FR-4 | Service test: calling `run_evaluation()` when `transcript` is null is rejected by a guard, with the `AIProvider.evaluate_speaking` mock asserted never called. |
| FR-5 | Service/schema test: `GET` detail returns a populated `transcript` field whenever non-null across all of `PROCESSING` (post-transcribe), `EVALUATION_FAILED`, and `COMPLETED` fixtures. Component test: `submission-detail.component` renders the transcript section independent of the feedback section's state. |
| FR-6 | Service test: `speech_to_text.transcribe` mock raising/returning failure sets `status=TRANSCRIPTION_FAILED`, with `AIProvider.evaluate_speaking` mock asserted never called. Router test: `POST /{id}/transcribe` retried against the same stored `audio_storage_ref` (no new upload) succeeds once the mock is switched to succeed, advancing status without requiring re-submission. |
| FR-7 | Schema/service test: a successful `evaluate_speaking` mock response is mapped into three distinct, separately-keyed fields (fluency-coherence, lexical resource, grammar) — asserted as separate objects/fields, not one concatenated string. |
| FR-8 | Schema/service test: each of the three criterion objects includes a populated band field sourced from the mocked `AIProvider` response. |
| FR-9 | Schema test: every serialized `COMPLETED` submission includes a Pronunciation field fixed to "Not assessed" even when the `AIProvider` mock response omits it entirely — proving it is synthesized by the serializer, not passed through from the provider. |
| FR-10 | Service test: `AIProvider.evaluate_speaking` mock raising/returning failure (with `transcript` already present) sets `status=EVALUATION_FAILED` while leaving the `transcript` column unchanged. Router test: `POST /{id}/evaluate` retried succeeds once the mock allows it, with the `speech_to_text.transcribe` mock's call count asserted unchanged (proving no re-transcription happened). |
| FR-11 | Router/service test: immediately after create (before any step is attempted), `GET` detail shows `status=PROCESSING` with `transcript` and feedback both null — a shape asserted distinct from each of the other three statuses. |
| FR-12 | Facade test (frontend): loading a `PROCESSING` fixture with `transcript=null` auto-triggers the transcribe call with no explicit user action; a second facade test for `PROCESSING` with `transcript` present auto-triggers evaluate instead — both simulating "reopening later," not a continuously-open session. |
| FR-13 | Router test: `GET /speaking-submissions` against fixtures covering all four statuses returns question, submission date, and status for every entry. Component test: `submission-list.component` renders all four status labels distinctly. |
| FR-14 | Router/component test: `GET` detail for a `COMPLETED` fixture returns/renders the transcript plus all three assessed criteria and the Pronunciation "not assessed" marker on a fresh fetch (simulating a later session). |
| FR-15 | Router test: list and detail responses for `TRANSCRIPTION_FAILED` vs. `EVALUATION_FAILED` fixtures expose visibly distinct status values. Component test: the list badge and detail-page heading text differ between the two failure kinds, not one generic "failed" label. |

## Constitution Check

- **Tests before code (principle 2)**: required, no exceptions requested. Every row above is
  written and failing before its corresponding backend service/router or frontend
  component/facade code is written, per the `test-driven-development` skill.
- **External services never called in tests**: `speech_to_text.transcribe()` and
  `AIProvider.evaluate_speaking()` are mocked/stubbed in every test in the table above; this
  also directly supports the PRD's cost-consciousness constraint (no accidental paid API usage
  from the test suite).
- **Single-learner simplification**: no `learner_id`/owner column on `speaking_questions` or
  `speaking_submissions`; `require_learner` gates the entire router, consistent with the shared
  convention given for this epic and with `access-protection`'s FR-2.
- **Docs are durable (principle 6)**: this plan does not silently diverge from
  `docs/specs/speaking-coach/Specification.md` or `docs/architecture/Architecture.md`; where it
  resolves an open question, the resolution is written here with reasoning rather than assumed
  silently in code.

## Risks / Open Questions

- **Submission frequency/rate limit is unresolved** (spec Open Question, not resolved by this
  plan). The PRD requires cost-conscious AI usage but no specific per-day/week cap is defined
  anywhere upstream; setting one is a product decision, not a technical one, so it is left open
  here — same as writing-coach's sibling spec leaves an analogous limit open. The schema/API
  does not preclude adding a simple per-day count check to `POST /speaking-submissions` later
  if a limit is set.
- **A submission left completely unattended never finishes on its own** (direct consequence of
  Approach B / the async ADR): if the learner submits a recording and never reopens the app,
  nothing advances it past whatever step it last reached. Accepted for a single-learner tool;
  flagged as the trade-off to revisit (Approach C: a cron sweep or queue) if this ever proves
  to be a real problem in practice.
- **Raw audio object storage is not yet decided.** This plan assumes `audio_storage_ref` on
  `speaking_submissions` points at wherever the raw recording bytes are persisted (e.g., Vercel
  Blob or equivalent object storage), but the actual storage mechanism/vendor is not chosen
  here — it is an infrastructure detail that does not change this plan's module boundaries
  (everything downstream just reads by reference), flagged for task breakdown.
- **Speech-to-Text vendor is not chosen.** `Architecture.md` establishes it as "a separate
  external service," not which one. `backend/app/services/speech_to_text.py` isolates that
  choice behind one function so tests never depend on it and the vendor can be picked (and
  swapped) during task breakdown/implementation without touching this plan's structure.
- **Question-bank content authoring is a content task, not a code task** — same caveat as
  `study-plan-execution`'s seed data: `speaking_questions_seed.py` cannot be meaningfully
  populated with real, well-formed IELTS-style prompts until that content is authored
  separately from this plan.
- **Any retention/deletion policy for raw audio after transcription is explicitly out of
  scope** per the spec's Out of Scope section; this plan does not invent one. Audio rows are
  assumed to persist indefinitely alongside their submission until a future epic/decision
  addresses retention.
- **Alignment dependency on the writing-coach plan**: this plan depends on
  `backend/app/ai/provider.py`'s `AIProvider` interface already exposing
  `evaluate_speaking(transcript, question) -> SpeakingEvaluationResult` (or an equivalent
  shape) as defined by the writing-coach epic's plan, which did not yet exist at the time this
  plan was written (only `docs/specs/writing-coach/Specification.md` existed). If
  writing-coach's plan lands with a materially different method shape, `speaking_coach.py`'s
  call site — and only that call site — needs to be reconciled; no other part of this plan
  depends on the interface's internals.

## Related ADRs
- docs/adr/2026-07-29-speaking-async-step-tracked-processing.md
