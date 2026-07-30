# ADR: AIProvider gains dedicated Reading/Listening exercise-generation methods

Date: 2026-07-30
Slug: reading-listening-generation-interface
Status: Accepted
Related spec: docs/specs/reading-practice/Specification.md, docs/specs/listening-practice/Specification.md

## Context

`backend/app/ai/provider.py` already defines `generate_quiz(request: QuizGenerationRequest) ->
QuizGenerationResult`, added when the `AIProvider` interface shape was first decided
(`docs/adr/2026-07-29-ai-provider-interface-shape.md`) but never wired to a router —
`QuizGenerationResult` only carries `questions: list[str]`, a flat list of question strings
with no passage/script text and no answer key. Reading Practice (Epic-9) and Listening
Practice (Epic-10) both need a passage/script *plus* multiple-choice questions *plus* a correct
answer per question, generated together as one coherent exercise (FR-1/FR-2 in each spec) —
`generate_quiz`'s existing shape cannot represent that without overloading a field name to mean
something it wasn't designed for. This is exactly the kind of interface-shape decision the
original ADR flagged as needing coordination once "other backend modules are written against a
specific method signature."

## Decision

Two new methods are added to `AIProvider`, following every rule established by
`2026-07-29-ai-provider-interface-shape.md` (typed request/result pair per method, synchronous,
status-discriminated result, no vendor exception crosses the boundary, request carries no
learner identity):

```
class AIProvider(ABC):
    ...
    @abstractmethod
    def generate_reading_exercise(
        self, request: ReadingExerciseGenerationRequest
    ) -> ReadingExerciseGenerationResult: ...

    @abstractmethod
    def generate_listening_script(
        self, request: ListeningScriptGenerationRequest
    ) -> ListeningScriptGenerationResult: ...
```

```
class ReadingExerciseGenerationRequest(BaseModel):
    focus_description: str   # e.g. "the word 'nevertheless'", "conditional clauses" —
                              # the daily_focus.focus_reference value verbatim; the provider
                              # does not need to know whether it came from a mistake or a
                              # vocabulary word

class GeneratedQuestion(BaseModel):
    question_text: str
    options: list[str]              # length 4, per the wireframe's 4-option layout
    correct_option_index: int       # 0-based

class ReadingExerciseGenerationResult(BaseModel):
    status: Literal["ok", "error"]
    error_message: str | None = None
    passage_text: str | None = None
    questions: list[GeneratedQuestion] = Field(default_factory=list)
    # validated the same way as every other *Result model in schemas.py: "ok" requires
    # passage_text and a non-empty questions list; "error" requires error_message.

class ListeningScriptGenerationRequest(BaseModel):
    focus_description: str

class ListeningScriptGenerationResult(BaseModel):
    status: Literal["ok", "error"]
    error_message: str | None = None
    script_text: str | None = None
    questions: list[GeneratedQuestion] = Field(default_factory=list)
```

`generate_quiz()` is left exactly as-is (still unused, still a flat question-string list) —
not repurposed, not deleted. It predates this decision and nothing currently calls it; removing
or changing it is out of scope for Epic-9/10 and can be revisited independently if a future
feature actually needs it.

Listening deliberately does *not* get an AI-provider method that also produces audio —
text-to-speech is a separate integration boundary, not an `AIProvider` concern (see
`docs/adr/2026-07-30-text-to-speech-integration-and-audio-storage.md`). `generate_listening_script()`
returns text only; the Listening Practice service layer calls the Text-to-Speech integration
afterward, as two independently retryable steps per `docs/specs/listening-practice/Specification.md`
FR-12.

`GeneratedQuestion` is a shared shape used by both new result types (defined once in
`backend/app/ai/schemas.py`), since Reading and Listening's question/answer-key structure is
identical — only the surrounding content (passage vs. script) differs.

## Consequences

- **Easier**: Reading Practice's and Listening Practice's plans/tasks can each implement
  against a fixed, already-decided method signature without needing to jointly design the
  shape while one or both features are being built — mirroring exactly how writing-coach and
  speaking-coach avoided coordinating on `evaluate_writing`/`evaluate_speaking`. `ClaudeProvider`,
  `LocalAIProvider`, and `FakeAIProvider` each implement two more methods in the same
  established pattern (local: deterministic canned content; fake: test-configurable).
- **Harder**: `AIProvider` now has six methods instead of four; any future provider
  implementation (a different vendor, or a specialized one) must implement all six, even if a
  particular deployment never uses Reading/Listening generation with that provider.
- **Forecloses**: extending `generate_quiz()`'s existing shape to also carry a passage and
  answer key — keeping it untouched avoids a breaking change to a method signature nothing
  currently depends on, and avoids conflating "a flat list of questions" (whatever that was
  originally intended for) with "a scored comprehension exercise."
