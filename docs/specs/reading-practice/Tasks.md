# Tasks: AI-Generated Reading Practice & Auto-Scoring
Plan: docs/specs/reading-practice/ImplementationPlan.md

## Task-1 — ReadingExercise/ReadingQuestion/ReadingSubmission models + migration
- [x] Status: Done
- Depends on: none
- Goal: Define `ReadingExercise` (id, day unique, passage_text, focus_reference, status), `ReadingQuestion` (exercise_id FK, question_text, options JSON, correct_option_index, order), and `ReadingSubmission` (exercise_id FK unique, answers JSON, score, submitted_at) in `backend/app/models/reading_practice.py`, and the Alembic migration creating all three tables.
- Files touched: `backend/app/models/reading_practice.py`, `backend/alembic/versions/<ts>_reading_practice_tables.py`
- Definition of done: migration test creates all three tables with expected columns against the test database; a model round-trip test writes one exercise with two questions and reads them back identically. No FR of its own — this is the persisted shape every later task builds on.

## Task-2 — AIProvider Reading generation methods
- [x] Status: Done
- Depends on: none
- Goal: Add `GeneratedQuestion`, `ReadingExerciseGenerationRequest`, `ReadingExerciseGenerationResult` to `backend/app/ai/schemas.py`, add `generate_reading_exercise()` to the `AIProvider` abstract class, and implement it on `ClaudeProvider`, `LocalAIProvider`, and `FakeAIProvider` — per `docs/adr/2026-07-30-reading-listening-generation-interface.md`.
- Files touched: `backend/app/ai/schemas.py`, `backend/app/ai/provider.py`, `backend/app/ai/claude_provider.py`, `backend/app/ai/local_provider.py`, `backend/app/ai/testing.py`
- Definition of done: unit tests pass for each implementation, asserting a successful call returns a passage plus questions each with exactly one correct answer, and a forced-error path returns `status="error"` with no passage/questions. Covers the AI-generation half of FR-1/FR-2.

## Task-3 — get_or_create_exercise() generation service
- [x] Status: Done
- Depends on: Task-1, Task-2
- Goal: Implement `get_or_create_exercise(day: date, focus_reference: str) -> ReadingExercise` in `backend/app/services/reading_practice.py`: if an exercise already exists for `day`, return it unchanged; otherwise call `AIProvider.generate_reading_exercise()` with the given focus, persist the passage and questions, and return the new row.
- Files touched: `backend/app/services/reading_practice.py`, `backend/app/services/reading_practice_test.py`
- Definition of done: unit tests pass, asserting (1) a first call with a `FakeAIProvider` persists a passage and questions matching the fake's response — covers FR-1; (2) a second call for the same day returns the identical row without a second `AIProvider` call — covers FR-9.

## Task-4 — GET /api/reading-practice/{day} endpoint (answering view)
- [x] Status: Done
- Depends on: Task-3
- Goal: Implement the endpoint returning the day's passage, its personalization focus note, and its questions (options only — never `correct_option_index`) in `backend/app/routers/reading_practice.py`.
- Files touched: `backend/app/routers/reading_practice.py`, `backend/app/routers/reading_practice_test.py`, `backend/app/schemas/reading_practice.py`
- Definition of done: integration test pass, asserting the response includes `focus_reference` (FR-3) and that no question's correct answer is present in the response body (protects FR-9's "same passage/questions" guarantee from being trivially defeated by peeking at the network response).

## Task-5 — score_submission() local scoring service
- [x] Status: Done
- Depends on: Task-1
- Goal: Implement `score_submission(exercise: ReadingExercise, answers: list[int]) -> ReadingSubmission` in `backend/app/services/reading_practice.py`, comparing each answer to its question's `correct_option_index` locally and persisting the result.
- Files touched: `backend/app/services/reading_practice.py`, `backend/app/services/reading_practice_test.py`
- Definition of done: unit test passes, asserting the computed score and per-question correctness are right for a mixed correct/incorrect answer set, and that no `AIProvider` method is called during scoring (spy/mock assertion) — covers FR-5.

## Task-6 — POST /api/reading-practice/{day}/submit endpoint
- [x] Status: Done
- Depends on: Task-4, Task-5
- Goal: Implement the submit endpoint: accepts all answers in one request, calls `score_submission`, and returns the overall score plus a per-question breakdown (correct/incorrect, correct answer if wrong) with enough data per wrong answer (question text, learner's answer, correct answer) to pre-fill a Mistake Notebook entry without further lookups.
- Files touched: `backend/app/routers/reading_practice.py`, `backend/app/routers/reading_practice_test.py`, `backend/app/schemas/reading_practice.py`
- Definition of done: integration test passes, asserting a single request with all answers returns the overall score (FR-4, FR-6) and that each wrong-answer entry in the response carries question text, learner answer, and correct answer (FR-7's data-shape requirement).

## Task-7 — POST /api/reading-practice/{day}/retry endpoint
- [x] Status: Done
- Depends on: Task-3
- Goal: Implement a retry endpoint that re-invokes `AIProvider.generate_reading_exercise()` using the exercise's already-stored `focus_reference`, replacing a failed exercise's content.
- Files touched: `backend/app/routers/reading_practice.py`, `backend/app/routers/reading_practice_test.py`
- Definition of done: integration test passes, asserting that after a forced generation failure, calling retry succeeds and the retried call's focus argument matches the original — covers FR-10.

## Task-8 — Export integration
- [x] Status: Done
- Depends on: Task-1, Task-6, data-portability's existing export-source registry mechanism
- Goal: Register Reading Practice as an export source in `backend/app/services/export_utils.py`, including a day's passage, questions, and submission/result in the assembled export document.
- Files touched: `backend/app/services/export_utils.py`, corresponding test file
- Definition of done: export integration test passes, asserting a completed day's Reading exercise and result appear in the exported document — covers FR-11.

## Task-9 — Frontend Reading Exercise page
- [x] Status: Done
- Depends on: Task-4, Task-6
- Goal: Implement `src/app/reading-practice/{models,data,state,pages/reading-exercise}` rendering layout A (answering) and layout B (result) from `docs/ux/wireframes/reading-exercise.md`, including the empty/loading/error/populated states.
- Files touched: `src/app/reading-practice/models/reading-exercise.model.ts`, `src/app/reading-practice/data/reading-practice.repository.ts`, `src/app/reading-practice/state/reading-practice.state.ts`, `src/app/reading-practice/pages/reading-exercise/*`
- Definition of done: component tests pass covering both layouts and all four states from the wireframe (FR-3, FR-4, FR-5, FR-6).

## Task-10 — Frontend Mistake Quick-Add component
- [x] Status: Done
- Depends on: Task-6 (result data shape), existing mistake-tracking creation endpoint
- Goal: Implement the quick-add component from `docs/ux/wireframes/mistake-quick-add.md`, pre-filled from a wrong-answer's result data, calling the existing Mistake Notebook creation endpoint with the reason category selected (or skipped).
- Files touched: `src/app/reading-practice/pages/reading-exercise/mistake-quick-add/*` (or a shared location if reused by listening-practice — decide during implementation)
- Definition of done: component test passes, asserting the pre-filled fields require no re-entry and the save action calls the existing mistake-creation endpoint with the correct payload, with and without a reason selected — covers FR-7.
