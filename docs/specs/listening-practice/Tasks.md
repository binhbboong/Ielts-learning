# Tasks: AI-Generated Listening Practice & Auto-Scoring
Plan: docs/specs/listening-practice/ImplementationPlan.md

## Task-1 — ListeningExercise/ListeningQuestion/ListeningSubmission models + migration
- [x] Status: Done
- Depends on: none
- Goal: Define `ListeningExercise` (id, day unique, script_text, audio_bytes, audio_content_type, focus_reference, status: script_generating/script_generated/audio_generating/ready/script_failed/audio_failed), `ListeningQuestion`, and `ListeningSubmission` (mirroring Reading Practice's shapes) in `backend/app/models/listening_practice.py`, and the Alembic migration creating all three tables.
- Files touched: `backend/app/models/listening_practice.py`, `backend/alembic/versions/<ts>_listening_practice_tables.py`
- Definition of done: migration test creates all three tables with expected columns; a model round-trip test writes one exercise (with audio bytes) and two questions and reads them back identically.

## Task-2 — TextToSpeech protocol + LocalDemoTextToSpeech adapter
- [x] Status: Done
- Depends on: none
- Goal: Implement `TextToSpeech` (Protocol), `SynthesisResult`, and `LocalDemoTextToSpeech` in `backend/app/services/text_to_speech.py`, mirroring `speech_to_text.py` exactly — per `docs/adr/2026-07-30-text-to-speech-integration-and-audio-storage.md`.
- Files touched: `backend/app/services/text_to_speech.py`, `backend/app/services/text_to_speech_test.py`
- Definition of done: unit test passes, asserting `LocalDemoTextToSpeech.synthesize()` returns a `SynthesisResult` with `status="ok"`, non-empty `audio_bytes`, and a valid `content_type`.

## Task-3 — AIProvider Listening generation methods
- [x] Status: Done
- Depends on: reading-practice Task-2 (shares the `GeneratedQuestion` schema)
- Goal: Add `ListeningScriptGenerationRequest`, `ListeningScriptGenerationResult` to `backend/app/ai/schemas.py`, add `generate_listening_script()` to `AIProvider`, and implement it on `ClaudeProvider`, `LocalAIProvider`, and `FakeAIProvider`.
- Files touched: `backend/app/ai/schemas.py`, `backend/app/ai/provider.py`, `backend/app/ai/claude_provider.py`, `backend/app/ai/local_provider.py`, `backend/app/ai/testing.py`
- Definition of done: unit tests pass for each implementation, asserting a successful call returns a script plus questions each with exactly one correct answer, and a forced-error path returns `status="error"`. Covers the script-generation half of FR-1.

## Task-4 — get_or_create_exercise() two-step generation service
- [x] Status: Done
- Depends on: Task-1, Task-2, Task-3
- Goal: Implement `get_or_create_exercise(day: date, focus_reference: str) -> ListeningExercise` in `backend/app/services/listening_practice.py`: if an exercise already exists for `day`, return it unchanged; otherwise call `AIProvider.generate_listening_script()`, persist the script/questions and advance status to `script_generated`, then call `TextToSpeech.synthesize()` on the script and advance to `ready` (or `audio_failed`) on completion.
- Files touched: `backend/app/services/listening_practice.py`, `backend/app/services/listening_practice_test.py`
- Definition of done: unit tests pass, asserting (1) a first call persists script, questions, and audio matching the fakes' responses, ending in `ready` — covers FR-1, FR-2; (2) a second call for the same day returns the identical row without re-invoking either fake — covers FR-14.

## Task-5 — retry_script() / retry_audio() service methods
- [x] Status: Done
- Depends on: Task-4
- Goal: Implement `retry_script()` (re-invokes `generate_listening_script()` with the exercise's stored focus, only valid from `script_failed`) and `retry_audio()` (re-invokes `TextToSpeech.synthesize()` on the already-stored script, only valid from `audio_failed`, without touching script generation) in `backend/app/services/listening_practice.py`.
- Files touched: `backend/app/services/listening_practice.py`, `backend/app/services/listening_practice_test.py`
- Definition of done: unit tests pass, asserting (1) `retry_audio()` after a forced audio failure does not call `generate_listening_script()` again (spy/mock call-count assertion) — covers FR-12; (2) `retry_script()` after a forced script failure reuses the same focus — covers FR-13.

## Task-6 — GET /api/listening-practice/{day} endpoint
- [x] Status: Done
- Depends on: Task-4
- Goal: Implement the endpoint returning the day's questions and personalization focus note, withholding `script_text` until the exercise has a submission.
- Files touched: `backend/app/routers/listening_practice.py`, `backend/app/routers/listening_practice_test.py`, `backend/app/schemas/listening_practice.py`
- Definition of done: integration test passes, asserting the pre-submission response omits `script_text` — covers FR-5.

## Task-7 — GET /api/listening-practice/{day}/audio endpoint
- [x] Status: Done
- Depends on: Task-4
- Goal: Implement the endpoint serving `audio_bytes` with the stored `audio_content_type`.
- Files touched: `backend/app/routers/listening_practice.py`, `backend/app/routers/listening_practice_test.py`
- Definition of done: integration test passes, asserting the response body matches the stored bytes and the `Content-Type` header matches the stored content type.

## Task-8 — score_submission() local scoring service
- [x] Status: Done
- Depends on: Task-1
- Goal: Implement `score_submission(exercise: ListeningExercise, answers: list[int]) -> ListeningSubmission` in `backend/app/services/listening_practice.py`, mirroring Reading Practice's local, no-AI-call scoring.
- Files touched: `backend/app/services/listening_practice.py`, `backend/app/services/listening_practice_test.py`
- Definition of done: unit test passes, asserting correct scoring for a mixed answer set and zero `AIProvider`/`TextToSpeech` calls during scoring — covers FR-7.

## Task-9 — POST /api/listening-practice/{day}/submit endpoint
- [x] Status: Done
- Depends on: Task-6, Task-8
- Goal: Implement the submit endpoint: accepts all answers in one request, calls `score_submission`, and returns the overall score, per-question breakdown, and the now-revealed transcript — plus the same wrong-answer quick-add data shape as Reading Practice.
- Files touched: `backend/app/routers/listening_practice.py`, `backend/app/routers/listening_practice_test.py`, `backend/app/schemas/listening_practice.py`
- Definition of done: integration test passes, asserting the response includes the overall score (FR-6, FR-8), the transcript is present post-submission (FR-9), and each wrong answer carries question/learner-answer/correct-answer data (FR-10).

## Task-10 — POST retry-script / retry-audio endpoints
- [x] Status: Done
- Depends on: Task-5
- Goal: Expose `retry_script()` and `retry_audio()` as two distinct endpoints so the frontend can retry the specific failed step shown in the player.
- Files touched: `backend/app/routers/listening_practice.py`, `backend/app/routers/listening_practice_test.py`
- Definition of done: router-level integration tests pass, asserting each endpoint drives the correct state transition and that `retry-audio` never triggers script regeneration (FR-12, FR-13).

## Task-11 — Export integration
- [x] Status: Done
- Depends on: Task-1, Task-9, data-portability's existing export-source registry mechanism
- Goal: Register Listening Practice as an export source, including a day's script, questions, submission/result, and the actual audio bytes in the assembled export document.
- Files touched: `backend/app/services/export_utils.py`, corresponding test file
- Definition of done: export integration test passes, asserting the exported document includes the actual audio bytes for a completed day, not only the transcript text — covers FR-15.

## Task-12 — Frontend Listening Exercise page
- [x] Status: Done
- Depends on: Task-6, Task-7, Task-9
- Goal: Implement `src/app/listening-practice/{models,data,state,pages/listening-exercise}` rendering layout A (answering, with audio player) and layout B (result, transcript revealed) from `docs/ux/wireframes/listening-exercise.md`, including the player's own distinct loading/error state separate from the screen-level state.
- Files touched: `src/app/listening-practice/models/listening-exercise.model.ts`, `src/app/listening-practice/data/listening-practice.repository.ts`, `src/app/listening-practice/state/listening-practice.state.ts`, `src/app/listening-practice/pages/listening-exercise/*`
- Definition of done: component tests pass covering both layouts, unlimited replay (FR-4), and the player's own error/failed state distinct from a full-screen error (FR-12 UX consequence).

## Task-13 — Frontend Mistake Quick-Add reuse
- [x] Status: Done
- Depends on: reading-practice Task-10, Task-9 (this spec)
- Goal: Reuse (or generalize, if needed) the Mistake Quick-Add component built for Reading Practice so it also works from a Listening Practice wrong answer.
- Files touched: shared component location decided during reading-practice Task-10; `src/app/listening-practice/pages/listening-exercise/*` wiring
- Definition of done: component test passes, asserting the same quick-add component correctly pre-fills and saves from Listening-sourced wrong-answer data — covers FR-10.
