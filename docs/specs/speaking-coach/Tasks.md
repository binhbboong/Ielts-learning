# Tasks: AI-Assisted Speaking Coaching
Plan: docs/specs/speaking-coach/ImplementationPlan.md

## Revision-2 Task-16 — Phase-based part selection, level-aware grading, wire AI prompt into recording UI
- [x] Status: Done
- Depends on: daily-lesson-plan's `generate_prompt_text`/`SkillOverviewEntry.generated_prompt_text`
- Goal: `daily_lesson_plan.py`'s `_PROMPT_INSTRUCTION`/`_prompt_complexity_tier` select Part
  1/2/3-style Speaking prompts by phase (foundation/core_skills -> beginner/Part 1,
  development/consolidation -> standard/Part 2, exam_readiness/peak_performance ->
  advanced/Part 3). `SpeakingEvaluationRequest` gains optional `target_band`/`phase`;
  `run_evaluation` looks up that day's `DailyFocus` (skill="speaking") and populates them via
  `level_context_line()`. `SpeakingCoachRepository.create()`/`SpeakingCoachFacade.submit()`
  restructured to an options object supporting `promptText`+`day` (the backend contract already
  supported this; the frontend never used it). `RecordResponseComponent` defaults to today's
  daily-generated prompt when one exists, with the existing Part/question-bank picker as a
  manual fallback. Also fixed an unrelated pre-existing bug found while touching this code: the
  repository read `fluency_and_cohesion` but the backend field is `fluency_and_coherence`,
  silently nulling that criterion in the UI.
- Files touched: `backend/app/services/daily_lesson_plan.py`, `backend/app/ai/schemas.py`,
  `backend/app/ai/claude_provider.py`, `backend/app/ai/openai_provider.py`,
  `backend/app/services/speaking_coach.py`, `backend/app/services/speaking_coach_test.py`,
  `backend/app/services/daily_lesson_plan_test.py`,
  `src/app/speaking-coach/data/speaking-coach.repository.ts`,
  `src/app/speaking-coach/state/speaking-coach.facade.ts`,
  `src/app/speaking-coach/pages/record-response/*`.
- Definition of done: `test_run_evaluation_passes_the_days_focus_level_to_the_provider`,
  `test_run_evaluation_has_no_level_context_without_a_matching_focus`, the
  `daily_lesson_plan_test.py` phase-tier tests, and the record-response pre-fill/submit test all
  pass. Covers FR-16 through FR-18 and resolves the Part 1/2/3 Open Question below.

## Task-1 — Speaking question bank: model, migration, seed data
- [x] Status: Done
- Depends on: none (assumes `backend/app/core/db.py` already exists — owned by the
  access-protection epic's backlog, parallel; imported here, not built here)
- Goal: Create the curated, seeded question bank the rest of this epic references. Add the
  `SpeakingQuestion` SQLAlchemy model (id, `part` enum `PART_1`/`PART_2`/`PART_3`, prompt text,
  no `learner_id` — single-learner simplification), the Alembic migration creating
  `speaking_questions`, and a seed script/data file (`speaking_questions_seed.py`) loaded by a
  data migration step, mirroring `src/app/study-plan/data/study-plan-seed.ts`'s
  seed-then-migrate pattern. No free-text learner-authored prompts — the bank is the only
  source of questions.
- Files touched: `backend/app/models/speaking_question.py`, `backend/app/data/speaking_questions_seed.py`,
  `backend/alembic/versions/<rev>_create_speaking_questions.py`
- Definition of done: tests pass (model/migration test asserting the table exists with the
  `part` enum constrained to the three values, and a seed test asserting rows exist for all
  three parts after migration); supports FR-1 (a real question/prompt always exists to
  reference). Question *content* authoring is a separate content task, not verified by tests
  here (per the plan's Risks section) — a handful of placeholder/starter prompts per part is
  sufficient for tests to pass.

## Task-2 — Speaking submission model, status enum, migration
- [x] Status: Done
- Depends on: Task-1 (FK to `speaking_questions`)
- Goal: Add the `SpeakingSubmission` SQLAlchemy model backing the whole pipeline: id,
  `question_id` FK, `audio_storage_ref`, `transcript` (nullable), `status` enum
  (`PROCESSING`, `TRANSCRIPTION_FAILED`, `EVALUATION_FAILED`, `COMPLETED`), per-criterion
  feedback + band columns (Fluency & Coherence, Lexical Resource, Grammar), timestamps. No
  `learner_id`. Plus its Alembic migration. This is schema only — no service/router logic yet.
- Files touched: `backend/app/models/speaking_submission.py`,
  `backend/alembic/versions/<rev>_create_speaking_submissions.py`
- Definition of done: tests pass (migration test asserting the table and status enum exist
  with exactly the four values from the ImplementationPlan's status table; model test asserting
  the FK to `speaking_questions` and nullable `transcript`/feedback columns). Lays the schema
  foundation for FR-3, FR-5, FR-11, FR-13 — no behavior yet, so no FR is fully satisfied by this
  task alone.

## Task-3 — FakeSpeechToText test double + Speech-to-Text service integration
- [x] Status: Done
- Depends on: none (independent of the submission schema; this isolates the external
  integration itself)
- Goal: Build `backend/app/services/speech_to_text.py` — the sole caller of the external
  Speech-to-Text vendor, exposing one function (e.g. `transcribe(audio) -> TranscriptionResult`
  with a status/error discriminant, mirroring the `AIProvider` result-shape convention). Write
  its own isolated unit tests that mock only the external HTTP/SDK call — never a real network
  call. Also build `FakeSpeechToText`, a test double implementing the same call shape with
  canned success/failure results, for use by every later task that needs a transcription step
  without hitting the real vendor.
- Files touched: `backend/app/services/speech_to_text.py`, test double (e.g.
  `backend/app/services/testing/fake_speech_to_text.py` or equivalent fixture module)
- Definition of done: tests pass; `speech_to_text.py`'s own unit tests mock the vendor call and
  assert both success and failure translate to the expected result shape; `FakeSpeechToText` is
  available for import by Task-5's tests. Provides the isolated, mockable boundary FR-4 and
  FR-6 depend on (no FR is behaviorally satisfied yet — this is test infrastructure).

## Task-4 — Submission creation endpoint
- [x] Status: Done
- Depends on: Task-1 (question bank to validate against/list), Task-2 (submission model)
- Goal: `POST /speaking-submissions` — a fast DB write with no external call: validates a
  `question_id` is present and references a real seeded question, validates the uploaded
  audio's duration/length does not exceed the 120-second cap (server-side re-validation, defense
  in depth alongside the client-side cap built in Task-11), creates one `speaking_submissions`
  row per request with `status=PROCESSING` and null transcript/feedback, and returns
  immediately. Also add the read-only `GET /speaking-questions` endpoint needed for question
  selection.
- Files touched: `backend/app/schemas/speaking_submission.py` (create schema),
  `backend/app/services/speaking_coach.py` (submission-creation logic only, at this stage),
  `backend/app/routers/speaking_coach.py` (create + questions-list routes only, at this stage)
- Definition of done: tests pass covering FR-1 (missing `question_id` rejected with 422/400,
  no row created), FR-2 (creating a submission persists exactly one row linking one
  `audio_storage_ref` to one `question_id`), FR-3 (201 response with `status=PROCESSING` and
  null transcript/feedback, with the Task-3 speech-to-text mock asserted never called), and the
  120-second cap (audio exceeding it is rejected server-side even if the client-side cap in
  Task-11 is bypassed).

## Task-5 — Transcription step endpoint/service
- [x] Status: Done
- Depends on: Task-3 (`FakeSpeechToText`), Task-4 (submission creation)
- Goal: `POST /speaking-submissions/{id}/transcribe` and its service function
  `run_transcription(submission_id)`: calls `speech_to_text.transcribe()` (via `FakeSpeechToText`
  in tests) against the stored `audio_storage_ref`, and on success writes the `transcript`
  column and advances status per the plan's status table (still `PROCESSING`, now with a
  transcript). On failure, sets `status=TRANSCRIPTION_FAILED` — a state distinct from
  evaluation failure — and does not touch evaluation. The same endpoint, called again, is how a
  learner retries transcription without a new recording.
- Files touched: `backend/app/services/speaking_coach.py` (add `run_transcription`),
  `backend/app/routers/speaking_coach.py` (add `/transcribe` route)
- Definition of done: tests pass covering FR-4 (transcript is produced as the prerequisite step
  — evaluation is not invoked from this path at all), FR-5 (a populated `transcript` is
  readable via the service/schema layer independent of what happens to evaluation afterward),
  and FR-6 (a `FakeSpeechToText` failure sets `status=TRANSCRIPTION_FAILED` with the evaluation
  call-site asserted never invoked; retrying the same endpoint after switching the fake to
  succeed advances status using the same stored `audio_storage_ref`, no new upload required).

## Task-6 — Evaluation step endpoint/service
- [x] Status: Done
- Depends on: Task-5 (a transcript must exist before evaluation can run). **Cross-epic
  dependency: this task requires `backend/app/ai/provider.py`'s `AIProvider` interface
  (specifically `evaluate_speaking()`) and its `FakeAIProvider` test double, both owned and
  built by writing-coach's backlog (parallel epic) — not rebuilt here. Do not start this task
  until that interface and fake exist; reference them, don't reimplement them.**
- Goal: `POST /speaking-submissions/{id}/evaluate` and its service function
  `run_evaluation(submission_id)`: guards that `transcript` is non-null before doing anything
  else (rejects with the `AIProvider` mock asserted never called if not), calls
  `AIProvider.evaluate_speaking()` (via writing-coach's `FakeAIProvider` in tests) with the
  stored transcript and question, maps a successful result into three distinct, separately-keyed
  criterion fields (Fluency & Coherence, Lexical Resource, Grammar) each carrying its own
  band-level indicator, and sets `status=COMPLETED`. On failure, sets
  `status=EVALUATION_FAILED` — distinct from `TRANSCRIPTION_FAILED` — while leaving the
  existing `transcript` column unchanged. The same endpoint, called again, is how a learner
  retries evaluation without re-transcribing or re-recording.
- Files touched: `backend/app/services/speaking_coach.py` (add `run_evaluation`),
  `backend/app/routers/speaking_coach.py` (add `/evaluate` route)
- Definition of done: tests pass covering FR-4 (the guard: calling `run_evaluation` with a null
  `transcript` is rejected, `AIProvider.evaluate_speaking` mock asserted never called), FR-7 (a
  successful `FakeAIProvider` response is mapped into three distinct, separately-keyed
  criterion objects, not one combined string), FR-8 (each of the three criterion objects
  includes a populated band field sourced from the fake's response), and FR-10 (a
  `FakeAIProvider` failure sets `status=EVALUATION_FAILED` with `transcript` unchanged; retrying
  after the fake is switched to succeed advances status while the `FakeSpeechToText` call count
  from Task-5 is asserted unchanged, proving no re-transcription happened).

## Task-7 — Pronunciation "not assessed" synthesis
- [x] Status: Done
- Depends on: Task-6 (evaluation must produce the other three criteria first)
- Goal: Ensure every serialized `COMPLETED` submission includes a Pronunciation field fixed to
  "Not assessed," synthesized at the schema/serialization layer — never stored as a database
  column and never passed through from whatever `FakeAIProvider`/`AIProvider` returns. This is
  broken out as its own task specifically because it is easy to accidentally satisfy only when
  the provider happens to omit Pronunciation, rather than unconditionally.
- Files touched: `backend/app/schemas/speaking_submission.py` (detail/response schema)
- Definition of done: tests pass covering FR-9 — a schema test asserts the Pronunciation field
  is always "Not assessed" in a `COMPLETED` response even when the `FakeAIProvider` mock
  response is constructed to include an estimated Pronunciation score or to omit the field
  entirely, proving the value is synthesized, not passed through.

## Task-8 — Retrieval of past submissions: list and detail endpoints
- [x] Status: Done
- Depends on: Task-4 (creation), Task-5 (transcription/failure states), Task-6 and Task-7
  (evaluation/failure states and Pronunciation marker) — needs all four statuses to exist as
  producible fixtures
- Goal: `GET /speaking-submissions` (list) and `GET /speaking-submissions/{id}` (detail).
  List returns, at minimum, each submission's question, submission date, and current status
  across all four status values. Detail returns the transcript (independent of evaluation
  state) and, once completed, full feedback including the Pronunciation marker from Task-7.
  Both list and detail responses distinguish `TRANSCRIPTION_FAILED` from `EVALUATION_FAILED`
  with visibly different values, not one generic "failed."
- Files touched: `backend/app/services/speaking_coach.py` (add list/detail read queries),
  `backend/app/routers/speaking_coach.py` (add list/detail routes)
- Definition of done: tests pass covering FR-11 (immediately after create, detail shows
  `status=PROCESSING` with transcript and feedback both null, a shape distinct from the other
  three statuses), FR-13 (list against fixtures covering all four statuses returns question,
  date, and status for every entry), FR-14 (detail for a `COMPLETED` fixture returns the
  transcript plus all three assessed criteria and the Pronunciation marker on a fresh fetch,
  simulating a later session), and FR-15 (list and detail responses for `TRANSCRIPTION_FAILED`
  vs. `EVALUATION_FAILED` fixtures expose visibly distinct status values).

## Task-9 — API router wiring
- [x] Status: Done
- Depends on: Task-1, Task-4, Task-5, Task-6, Task-7, Task-8 (assembles every route built so
  far into one router). Assumes `backend/app/core/security.py`'s `require_learner` dependency
  already exists — owned by the access-protection epic's backlog, parallel; imported here, not
  built here.
- Goal: Finalize `backend/app/routers/speaking_coach.py` as the single router exposing
  `GET /speaking-questions`, `POST /speaking-submissions`, `POST /speaking-submissions/{id}/transcribe`,
  `POST /speaking-submissions/{id}/evaluate`, `GET /speaking-submissions`,
  `GET /speaking-submissions/{id}`, every route gated behind `require_learner`, and mount it
  into the FastAPI app. Add one end-to-end integration smoke test driving the full happy path
  (create → transcribe → evaluate → detail) through the real router using the Task-3/Task-6
  fakes.
- Files touched: `backend/app/routers/speaking_coach.py`, backend app-assembly module wiring
  the router in
- Definition of done: tests pass covering the full happy-path chain end to end (touching FR-3,
  FR-6, FR-10, FR-13 collectively as one integration path) and an auth test asserting every
  route in the router 401/403s without a valid learner session (consistent with
  access-protection's convention; no dedicated FR in this spec, enforced as a router-wide
  guard).

## Task-10 — Frontend models, repository, and facade
- [x] Status: Done
- Depends on: Task-9 (backend endpoints must exist to wrap)
- Goal: Following `src/app/study-plan/`'s pattern (models → repository → facade), add
  `SpeakingQuestion` and `SpeakingSubmission` types (including the four-value status union),
  a `speaking-coach.repository.ts` as the sole point of contact with `api-client.ts` (question
  list, create, transcribe, evaluate, list/detail reads), and a `speaking-coach.facade.ts`
  exposing `submit()`, `retryTranscription()`, `retryEvaluation()`, and owning the auto-chain-
  after-submit and auto-resume-on-view orchestration logic from the ADR (transcribe fires
  automatically after submit; opening a `PROCESSING` submission with a null transcript
  auto-fires transcribe, one with a transcript auto-fires evaluate; the two `*_FAILED` states
  only ever advance via an explicit retry call, never auto-retried).
- Files touched: `src/app/speaking-coach/models/speaking-question.model.ts`,
  `src/app/speaking-coach/models/speaking-submission.model.ts`,
  `src/app/speaking-coach/data/speaking-coach.repository.ts`,
  `src/app/speaking-coach/state/speaking-coach.facade.ts`
- Definition of done: tests pass covering FR-3 (repository/facade surfaces the create
  response's `PROCESSING` confirmation distinctly from later states), FR-5 (facade exposes
  transcript state independent of feedback state), FR-6 and FR-10 (facade's
  `retryTranscription()`/`retryEvaluation()` call the correct endpoint without requiring a new
  recording or re-transcription respectively), FR-11 (facade state model distinguishes
  processing from both failure states and completion), and FR-12 (facade test: loading a
  `PROCESSING` fixture with `transcript=null` auto-triggers transcribe with no explicit user
  action; a second test for `PROCESSING` with `transcript` present auto-triggers evaluate
  instead — both simulating reopening the app later, not a continuously open session).

## Task-11 — Frontend recording/submission UI and feedback display
- [x] Status: Done
- Depends on: Task-10 (facade)
- Goal: Build the three learner-facing pages: `record-response` (question selection with
  part filtering, audio recording capped client-side at 120 seconds, submit, and the FR-3
  "received, processing" confirmation), `submission-list` (renders question, date, and all four
  statuses distinctly per FR-13/FR-15), and `submission-detail` (renders the transcript
  independent of feedback state per FR-5; once complete, renders all three criteria with band
  indicators per FR-7/FR-8 plus the Pronunciation "not assessed" marker per FR-9; renders
  distinct, labeled in-progress and failure states with a Retry action per FR-6/FR-10/FR-11;
  indicates which step failed per FR-15; triggers the facade's auto-resume on load for
  `PROCESSING` rows per FR-12). **No wireframe exists yet for this epic** (per the spec's
  header and the plan's File/Module Structure note) — this task's exact layout is provisional
  and should be treated as inferred from the FRs, not a UX decision already made.
- Files touched: `src/app/speaking-coach/pages/record-response/record-response.component.ts`
  (+`.html`), `src/app/speaking-coach/pages/submission-list/submission-list.component.ts`
  (+`.html`), `src/app/speaking-coach/pages/submission-detail/submission-detail.component.ts`
  (+`.html`), `src/app/speaking-coach/speaking-coach.routes.ts`
- Definition of done: tests pass covering FR-1 (submit is disabled/blocked until a question is
  selected), FR-3 (confirmation state renders immediately and is visibly distinct from later
  transcript/feedback rendering), FR-5 (transcript section renders independent of feedback
  section's state), FR-6/FR-10 (labeled failure states each render their own Retry action), FR-7
  (three criteria render as separate items), FR-8 (each criterion shows a band indicator), FR-9
  (Pronunciation "not assessed" always rendered on a completed result), FR-11 (processing state
  is visually distinct from completed/failed states), FR-13 (list renders all four status labels
  distinctly), FR-14 (a completed submission's detail view renders transcript plus full feedback
  on a fresh load), and FR-15 (list badge and detail heading text differ between
  `TRANSCRIPTION_FAILED` and `EVALUATION_FAILED`, not one generic "failed" label). The 120-second
  client-side recording cap is verified by a component test asserting the recorder stops/warns
  at the limit, as defense-in-depth alongside Task-4's server-side re-validation.
