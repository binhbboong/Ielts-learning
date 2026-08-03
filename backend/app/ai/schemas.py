from typing import Literal

from pydantic import BaseModel, Field, field_validator, model_validator


def level_context_line(target_band: float | None, phase: str | None) -> str:
    """Grading-prompt addendum so evaluation is calibrated to the learner's current
    level rather than an implicit flat band-9 standard. Empty when no level is known
    (e.g. free/ad hoc practice not tied to a daily-lesson-plan day) — grading then
    falls back to the prior, level-agnostic behavior unchanged."""
    if target_band is None or phase is None:
        return ""
    return (
        f"\nThe learner's current target band is {target_band} "
        f"({phase.replace('_', ' ')} phase). Grade fairly against realistic "
        "expectations for this level, not a flat band-9 standard — still give an "
        "honest overall_band and cite exact submitted wording."
    )


class _RequiredTextModel(BaseModel):
    @field_validator("*")
    @classmethod
    def strip_string_fields(cls, value):
        if isinstance(value, str):
            stripped = value.strip()
            if not stripped:
                raise ValueError("must not be empty")
            return stripped
        return value


class CriterionFeedback(_RequiredTextModel):
    band_score: float = Field(ge=0, le=9)
    feedback: str
    strengths: list[str] = Field(default_factory=list)
    weaknesses: list[str] = Field(default_factory=list)


class SentenceCorrection(_RequiredTextModel):
    original: str
    corrected: str
    explanation: str


class WritingEvaluationRequest(_RequiredTextModel):
    response_text: str
    task_type: Literal["task1", "task2"]
    question_text: str
    target_band: float | None = None
    phase: str | None = None


class WritingEvaluationResult(BaseModel):
    status: Literal["ok", "error"]
    error_message: str | None = None
    task_response: CriterionFeedback | None = None
    coherence_and_cohesion: CriterionFeedback | None = None
    lexical_resource: CriterionFeedback | None = None
    grammatical_range_and_accuracy: CriterionFeedback | None = None
    overall_band: float | None = Field(default=None, ge=0, le=9)
    corrections: list[SentenceCorrection] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_status_shape(self):
        feedback = (
            self.task_response,
            self.coherence_and_cohesion,
            self.lexical_resource,
            self.grammatical_range_and_accuracy,
        )
        if self.status == "ok" and (
            any(item is None for item in feedback)
            or self.overall_band is None
        ):
            raise ValueError("successful writing result requires full feedback")
        if self.status == "error" and not (
            self.error_message and self.error_message.strip()
        ):
            raise ValueError("error result requires an error message")
        return self


class SpeakingEvaluationRequest(_RequiredTextModel):
    transcript: str
    question_text: str
    target_band: float | None = None
    phase: str | None = None


class SpeakingEvaluationResult(BaseModel):
    status: Literal["ok", "error"]
    error_message: str | None = None
    fluency_and_coherence: CriterionFeedback | None = None
    lexical_resource: CriterionFeedback | None = None
    grammatical_range_and_accuracy: CriterionFeedback | None = None

    @model_validator(mode="after")
    def validate_status_shape(self):
        feedback = (
            self.fluency_and_coherence,
            self.lexical_resource,
            self.grammatical_range_and_accuracy,
        )
        if self.status == "ok" and any(item is None for item in feedback):
            raise ValueError("successful speaking result requires full feedback")
        if self.status == "error" and not (
            self.error_message and self.error_message.strip()
        ):
            raise ValueError("error result requires an error message")
        return self


class QuizGenerationRequest(_RequiredTextModel):
    topic: str
    question_count: int = Field(ge=1, le=50)


class QuizGenerationResult(BaseModel):
    status: Literal["ok", "error"]
    error_message: str | None = None
    questions: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_status_shape(self):
        if self.status == "ok" and not self.questions:
            raise ValueError("successful quiz result requires questions")
        if self.status == "error" and not self.error_message:
            raise ValueError("error result requires an error message")
        return self


class GeneratedQuestion(_RequiredTextModel):
    question_text: str
    options: list[str]
    correct_option_index: int = Field(ge=0)

    @model_validator(mode="after")
    def validate_correct_index_in_range(self):
        if self.correct_option_index >= len(self.options):
            raise ValueError("correct_option_index must index into options")
        return self


class ReadingExerciseGenerationRequest(_RequiredTextModel):
    focus_description: str


class ReadingExerciseGenerationResult(BaseModel):
    status: Literal["ok", "error"]
    error_message: str | None = None
    passage_text: str | None = None
    questions: list[GeneratedQuestion] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_status_shape(self):
        if self.status == "ok" and not (
            self.passage_text and self.passage_text.strip() and self.questions
        ):
            raise ValueError("successful reading exercise result requires a passage and questions")
        if self.status == "error" and not (
            self.error_message and self.error_message.strip()
        ):
            raise ValueError("error result requires an error message")
        return self


class ListeningScriptGenerationRequest(_RequiredTextModel):
    focus_description: str


class ListeningScriptGenerationResult(BaseModel):
    status: Literal["ok", "error"]
    error_message: str | None = None
    script_text: str | None = None
    questions: list[GeneratedQuestion] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_status_shape(self):
        if self.status == "ok" and not (
            self.script_text and self.script_text.strip() and self.questions
        ):
            raise ValueError("successful listening script result requires a script and questions")
        if self.status == "error" and not (
            self.error_message and self.error_message.strip()
        ):
            raise ValueError("error result requires an error message")
        return self


class ChatRequest(_RequiredTextModel):
    message: str


class ChatResult(BaseModel):
    status: Literal["ok", "error"]
    error_message: str | None = None
    message: str | None = None

    @model_validator(mode="after")
    def validate_status_shape(self):
        if self.status == "ok" and not (self.message and self.message.strip()):
            raise ValueError("successful chat result requires a message")
        if self.status == "error" and not self.error_message:
            raise ValueError("error result requires an error message")
        return self
