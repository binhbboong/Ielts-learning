# Implementation Plan: AI-Generated Reading Practice & Auto-Scoring
Spec: docs/specs/reading-practice/Specification.md

## Approach

**Chosen approach**: a new backend module owning three tables — one Reading exercise per
calendar day (passage + generation status), its questions (with the correct answer recorded at
generation time), and the learner's single submission per exercise (answers + computed
correctness, stored so the result never needs recomputation). Generation calls the new
`AIProvider.generate_reading_exercise()` method
(`docs/adr/2026-07-30-reading-listening-generation-interface.md`); scoring is a pure local
comparison against the stored answer key — no AI call at submission time, satisfying FR-5's
"no additional AI call" requirement directly from the data model rather than by convention.

**Two alternatives considered**:
- *Store the answer key only in the AI provider's response, re-deriving it at scoring time by
  calling the AI again* — rejected: makes scoring dependent on the AI provider being available
  and consistent every time, and violates FR-9 (immutability) since a second AI call could, in
  principle, return something different.
- *One combined table (exercise + questions + submission as JSON blobs)* — rejected: makes the
  per-question review (FR-5) and the Mistake Notebook quick-add (FR-7, which needs one specific
  question's text/answers) harder to query than normalized rows; the exercise/day scale here
  (one row per day) doesn't need the write-simplicity a blob would buy.

## File/Module Structure
| Path | Responsibility | Implements (wireframe/prototype) |
|------|-----------------|-----------------|
| `backend/app/models/reading_practice.py` | `ReadingExercise` (id, day unique, passage_text, focus_reference, status), `ReadingQuestion` (exercise_id FK, question_text, options JSON, correct_option_index, order), `ReadingSubmission` (exercise_id FK unique, answers JSON, score, submitted_at) | — |
| `backend/alembic/versions/000X_reading_practice_tables.py` | Creates the three tables above | — |
| `backend/app/schemas/reading_practice.py` | Request/response shapes: exercise-with-questions (answering view, no correct answers exposed), submission request, result response (per-question correctness + score) | docs/ux/wireframes/reading-exercise.md |
| `backend/app/services/reading_practice.py` | `get_or_create_exercise(day, focus_reference)` (calls `AIProvider.generate_reading_exercise()`), `score_submission(exercise, answers)` (local comparison, no AI call), retry (reuses the day's `daily_focus` reference per `docs/specs/daily-lesson-plan/Specification.md` FR-5) | — |
| `backend/app/routers/reading_practice.py` | `GET /api/reading-practice/{day}` (answering view, correct answers withheld pre-submission per FR-9's "same passage/questions" guarantee), `POST /api/reading-practice/{day}/submit`, `POST /api/reading-practice/{day}/retry` | docs/ux/wireframes/reading-exercise.md |
| `backend/app/ai/schemas.py` (extended) | `ReadingExerciseGenerationRequest`, `GeneratedQuestion`, `ReadingExerciseGenerationResult` — per the ADR | — |
| `backend/app/ai/claude_provider.py`, `local_provider.py`, `testing.py` (extended) | Implement `generate_reading_exercise()` on each of `ClaudeProvider`, `LocalAIProvider`, `FakeAIProvider` | — |
| `backend/app/services/export_utils.py` (extended) | Reading exercises/questions/submissions included in the data-portability export contract (Epic-5) | — |
| `src/app/reading-practice/models/reading-exercise.model.ts` | TypeScript types | — |
| `src/app/reading-practice/data/reading-practice.repository.ts` | Calls the endpoints above via the shared `ApiClient` | — |
| `src/app/reading-practice/state/reading-practice.state.ts` | Holds the current exercise/answering state and the result after submission | — |
| `src/app/reading-practice/pages/reading-exercise/` | Layout A (answering) and layout B (result) from the wireframe, including the "Add to Mistake Notebook" quick action | docs/ux/wireframes/reading-exercise.md |

## Testing Strategy
| Requirement | Verified by |
|---|---|
| FR-1 (generate passage + questions targeted at focus) | Service unit test with a `FakeAIProvider` configured to assert the focus argument it receives |
| FR-2 (one correct answer per question, recorded at generation) | Model/service test asserting `correct_option_index` is persisted and never null after generation |
| FR-3 (personalization note displayed) | Router integration test asserting the answering-view response includes `focus_reference` |
| FR-4 (single-action submit) | Router integration test posting all answers in one request |
| FR-5 (immediate local scoring, no additional AI call) | Service test asserting `score_submission` makes zero calls to the injected `AIProvider` |
| FR-6 (overall score displayed) | Router integration test asserting the result response includes a correct-count/total |
| FR-7 (pre-filled Mistake Notebook quick-add) | Router integration test asserting a wrong-answer's result payload includes everything `mistake-quick-add.md` needs (skill, source, learner answer, correct answer) with no additional lookup required |
| FR-8 (result feeds progress trend) | Integration test asserting a completed submission produces a row consumable by `practice_trend.py` (Epic-4) |
| FR-9 (immutable once generated) | Service test: fetch the exercise twice before submission (identical), submit, fetch again (identical result) |
| FR-10 (distinct failure state + retry) | Router integration test forcing `AIProvider.generate_reading_exercise()` to return `status="error"`, asserting a distinct failure response and that retry re-invokes generation with the same focus |
| FR-11 (included in export) | Export integration test asserting a day's Reading exercise/questions/result appear in the exported document |

## Risks / Open Questions
None outstanding — this feature's scope was fully resolved during the UX and prior spec-review
phases.

## Related ADRs
- docs/adr/2026-07-30-reading-listening-generation-interface.md
