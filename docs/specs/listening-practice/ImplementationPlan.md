# Implementation Plan: AI-Generated Listening Practice & Auto-Scoring
Spec: docs/specs/listening-practice/Specification.md

## Approach

**Chosen approach**: mirrors Reading Practice's table shape (exercise / questions / submission)
with two additions: an `audio_bytes` column (per
`docs/adr/2026-07-30-text-to-speech-integration-and-audio-storage.md`) and a more granular
status than Reading's single ready/failed, because generation here is genuinely two independent
steps — script generation (`AIProvider.generate_listening_script()`) and audio synthesis
(`TextToSpeech.synthesize()`) — and FR-12 requires a failure in the second step to be retryable
without discarding a successful first step.

**Status model** (`ListeningExercise.status`): `script_generating` → `script_generated` →
`audio_generating` → `ready`, with `script_failed` and `audio_failed` as terminal failure states
reachable from `script_generating` and `audio_generating` respectively. This is Listening
Practice's own internal detail — the Daily Lesson Plan module (Epic-1) only ever sees this
collapsed to the shared Ready/Generating/Failed vocabulary (per
`docs/adr/2026-07-30-daily-lesson-plan-data-model.md`, decision point 3), so adding or renaming
an internal state here later does not touch Epic-1.

**Two alternatives considered**:
- *A single combined "generate" call that produces script and audio together, all-or-nothing on
  retry* — rejected: this is exactly what FR-12 explicitly rules out (a successful script must
  not be discarded because audio failed); the two-step status model is the direct, faithful
  implementation of that requirement rather than a workaround.
- *Store audio via an object-storage URL instead of `bytea`* — rejected in the linked ADR at the
  architecture level; not re-litigated here.

## File/Module Structure
| Path | Responsibility | Implements (wireframe/prototype) |
|------|-----------------|-----------------|
| `backend/app/models/listening_practice.py` | `ListeningExercise` (id, day unique, script_text, audio_bytes, audio_content_type, focus_reference, status per the 6-state model above), `ListeningQuestion` (mirrors ReadingQuestion), `ListeningSubmission` (mirrors ReadingSubmission) | — |
| `backend/alembic/versions/000X_listening_practice_tables.py` | Creates the three tables above | — |
| `backend/app/schemas/listening_practice.py` | Request/response shapes: exercise-with-questions (answering view, transcript withheld pre-submission per FR-5), submission request, result response (per-question correctness + score + transcript revealed) | docs/ux/wireframes/listening-exercise.md |
| `backend/app/services/text_to_speech.py` | `TextToSpeech` Protocol, `SynthesisResult`, `LocalDemoTextToSpeech` — per the ADR, mirrors `speech_to_text.py` exactly | — |
| `backend/app/services/listening_practice.py` | `get_or_create_exercise(day, focus_reference)` (two-step: script then audio), `retry_script()`, `retry_audio()` (reuses existing script per FR-12), `score_submission()` (local, no AI call) | — |
| `backend/app/routers/listening_practice.py` | `GET /api/listening-practice/{day}` (metadata + questions, transcript withheld pre-submission), `GET /api/listening-practice/{day}/audio` (serves `audio_bytes` with the stored content type), `POST /api/listening-practice/{day}/submit`, `POST /api/listening-practice/{day}/retry-script`, `POST /api/listening-practice/{day}/retry-audio` | docs/ux/wireframes/listening-exercise.md |
| `backend/app/ai/schemas.py` (extended) | `ListeningScriptGenerationRequest`, `ListeningScriptGenerationResult` (reuses `GeneratedQuestion`) — per the ADR | — |
| `backend/app/ai/claude_provider.py`, `local_provider.py`, `testing.py` (extended) | Implement `generate_listening_script()` on each provider | — |
| `backend/app/services/export_utils.py` (extended) | Listening exercises/questions/submissions/audio bytes included in the export contract (FR-15) | — |
| `src/app/listening-practice/models/listening-exercise.model.ts` | TypeScript types | — |
| `src/app/listening-practice/data/listening-practice.repository.ts` | Calls the endpoints above via the shared `ApiClient`, including fetching the audio endpoint as a blob for the player | — |
| `src/app/listening-practice/state/listening-practice.state.ts` | Holds the current exercise/answering state, audio player state, and the result after submission | — |
| `src/app/listening-practice/pages/listening-exercise/` | Layout A (answering, with audio player) and layout B (result, transcript revealed), including the player's own distinct loading/error state | docs/ux/wireframes/listening-exercise.md |

## Testing Strategy
| Requirement | Verified by |
|---|---|
| FR-1 (generate script + questions targeted at focus) | Service unit test with a `FakeAIProvider` asserting the focus argument received |
| FR-2 (audio required before Ready) | Service test asserting status only reaches `ready` after both script and audio succeed |
| FR-3 (one correct answer per question) | Model/service test, same shape as Reading Practice FR-2 |
| FR-4 (unlimited play/pause/replay) | Frontend component test asserting no play-count limit is enforced by the player |
| FR-5 (transcript hidden pre-submission) | Router integration test asserting the pre-submission response omits `script_text` |
| FR-6 (single-action submit) | Router integration test posting all answers in one request |
| FR-7 (immediate local scoring, matches Reading's shape) | Service test asserting `score_submission` makes zero AI-provider calls |
| FR-8 (overall score displayed) | Router integration test asserting the result includes a correct-count/total |
| FR-9 (transcript revealed after submission) | Router integration test asserting the post-submission response includes `script_text` |
| FR-10 (same Mistake Notebook quick-add path as Reading) | Router integration test, same shape as Reading Practice FR-7 |
| FR-11 (result feeds progress trend) | Integration test, same shape as Reading Practice FR-8 |
| FR-12 (audio failure is player-scoped, retry doesn't re-request script) | Service test: force `TextToSpeech.synthesize()` to fail after a successful script generation, call `retry_audio()`, assert `generate_listening_script()` is not called again (spy/mock count) |
| FR-13 (script failure distinct + retryable with same focus) | Service test forcing `generate_listening_script()` to fail, asserting a distinct failure status and that `retry_script()` reuses the same focus |
| FR-14 (immutable once generated) | Service test: fetch exercise twice before submission (identical script/audio/questions), submit, fetch again (identical result) |
| FR-15 (audio included in export) | Export integration test asserting the exported document includes the actual audio bytes for a completed day, not only the transcript |

## Risks / Open Questions
- `LocalDemoTextToSpeech`'s fixed local clip means local/dev testing cannot exercise real
  vendor-specific failure modes (e.g. rate limits, unsupported characters) — acceptable for this
  plan's test strategy (which tests the retry/status contract via a fake, not real audio
  quality), but flagged so real-vendor integration testing is understood as a separate,
  later concern when a vendor is actually selected.
- Serving audio via `GET /api/listening-practice/{day}/audio` reading a `bytea` column on every
  playback (including replays) is simple but re-reads the same bytes from Postgres repeatedly;
  acceptable at single-learner scale per the storage ADR, not optimized further here.

## Related ADRs
- docs/adr/2026-07-30-reading-listening-generation-interface.md
- docs/adr/2026-07-30-text-to-speech-integration-and-audio-storage.md
