# ADR: AI Provider Interface Shape (`AIProvider` abstract methods)

Date: 2026-07-29
Slug: ai-provider-interface-shape
Status: Accepted
Related spec: docs/specs/writing-coach/Specification.md

## Context

`docs/architecture/Architecture.md` and the fullstack-vercel-claude-architecture ADR both name
an `AIProvider` abstraction (`evaluate_writing()`, `evaluate_speaking()`, `generate_quiz()`,
`chat()`) with `ClaudeProvider` as the default implementation, selected by an `AI_PROVIDER`
env var — but neither document fixes the actual method signatures or return shapes. This
plan (`writing-coach`) is the first to implement any part of that interface
(`backend/app/ai/provider.py`, `backend/app/ai/claude_provider.py`), and only exercises the
`evaluate_writing()` path. The `speaking-coach` epic's own plan is being written in parallel by
a different agent and depends on `evaluate_speaking()` existing on the same interface with a
shape it can code against without having seen this file. Once other backend modules
(`services/writing_coach.py`, and later `services/speaking_coach.py`) are written against a
specific method signature and return type, changing that shape becomes a cross-epic, multi-file
change — this is exactly the "API/data shape other code will depend on" trigger the
implementation-planning skill flags for an ADR, made sharper by the fact that a second epic
must independently align with it without a shared review step.

## Decision

`backend/app/ai/provider.py` defines an abstract base class:

```
class AIProvider(ABC):
    @abstractmethod
    def evaluate_writing(self, request: WritingEvaluationRequest) -> WritingEvaluationResult: ...

    @abstractmethod
    def evaluate_speaking(self, request: SpeakingEvaluationRequest) -> SpeakingEvaluationResult: ...

    @abstractmethod
    def generate_quiz(self, request: QuizGenerationRequest) -> QuizGenerationResult: ...

    @abstractmethod
    def chat(self, request: ChatRequest) -> ChatResult: ...
```

Rules that make this shape stable across epics implemented by different, non-communicating
agents:

1. **One typed request object in, one typed result object out, per method.** No positional
   strings-and-dicts. Each method's request/result is its own Pydantic model defined in
   `backend/app/ai/schemas.py` (not in `provider.py` itself, so provider.py stays a pure
   interface file). This means a new field never breaks the call site — callers pass a
   constructed object, not positional args, so adding an optional field to
   `SpeakingEvaluationRequest` later never touches `evaluate_writing()`'s signature or any of
   its callers.
2. **Every method is synchronous (`def`, not `async def`) and provider-implementation-specific
   timeout/retry handling stays inside the concrete provider class, not the interface.** This
   plan's own Approach section (see `docs/specs/writing-coach/ImplementationPlan.md`) concludes
   Writing can call this synchronously inline from a FastAPI request handler; if Speaking's plan
   independently concludes it needs an async/background execution model, that is a concern for
   how *the router* calls `evaluate_speaking()` (e.g. from a background task), not a reason to
   change the method's own signature — the interface itself stays call-and-return either way.
3. **Result objects always carry a success/failure discriminant, never raise a
   provider-specific exception across the interface boundary.** Concretely:
   `WritingEvaluationResult` (and by the same pattern, `SpeakingEvaluationResult`) is a Pydantic
   model with `status: Literal["ok", "error"]`, an `error_message: str | None`, and the
   feedback fields populated only when `status == "ok"`. This lets `services/writing_coach.py`
   (and later `services/speaking_coach.py`) implement FR-10-style "explicit failure, preserve
   input, allow retry" behavior uniformly without needing to know which concrete provider raised
   what SDK-specific exception. `ClaudeProvider` is responsible for catching Anthropic
   SDK-level exceptions internally and translating them into this result shape — no
   `anthropic`-specific exception type ever crosses the `AIProvider` boundary.
4. **`WritingEvaluationRequest` carries exactly what `evaluate_writing()` needs to build a
   prompt, and nothing about HTTP, the database, or the learner.** Concretely: `response_text:
   str`, `task_type: Literal["task1", "task2"]`, `question_text: str`. No `learner_id` (per the
   single-learner simplification, identity is a router-level concern via `require_learner`, not
   an AI-provider concern). `evaluate_speaking()`'s request object follows the same rule —
   speaking-coach's plan decides its own fields (e.g. `transcript: str` instead of
   `response_text`), but should not thread learner identity or persistence concerns through the
   request either.
5. **`ClaudeProvider` is the only class that imports the Anthropic SDK.** `provider.py`
   (the ABC) and `backend/app/ai/schemas.py` (the request/result models) have zero dependency on
   any specific AI vendor's SDK — this is what keeps `AI_PROVIDER` swappable in fact, not just
   in name.

## Consequences

- **Easier**: `speaking-coach`'s plan can implement `evaluate_speaking()` against this same
  file without waiting on or reading `writing-coach`'s implementation — the contract (typed
  request/result pair, sync call, status-discriminated result, no vendor exception leakage) is
  fully specified here. A future third or fourth `AIProvider` implementation (e.g. a different
  vendor, or a local/offline stub for tests) only has to implement four methods against fixed
  signatures. Testing every caller (`services/writing_coach.py`, later
  `services/speaking_coach.py`) is mock-friendly: tests construct a fake `AIProvider` returning
  canned `WritingEvaluationResult`/`SpeakingEvaluationResult` objects, no real API calls.
- **Harder**: any future change to a request/result model's required fields is a shared-contract
  change that must be coordinated across whichever epics already call that method (currently
  just writing-coach; speaking-coach once its plan lands) — this is the accepted cost of a
  shared interface, mitigated by keeping the fields minimal and provider-orchestration concerns
  (retries, timeouts, sync-vs-async execution) explicitly out of the interface itself.
- **Forecloses**: passing raw dicts or provider-native SDK types across the `AIProvider`
  boundary; letting a concrete provider's exception types propagate to callers; giving
  `evaluate_writing()`/`evaluate_speaking()` knowledge of the database, HTTP, or learner
  identity.
