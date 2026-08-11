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


def writing_evaluation_context_line(
    target_band: float | None,
    phase: str | None,
    exercise_type: str | None,
    practice_level: int | None,
) -> str:
    context = level_context_line(target_band, phase)
    if exercise_type not in {
        "sentence_building",
        "sentence_expansion",
        "guided_paragraph",
        "structured_response",
    }:
        return context
    return context + (
        f"\nThis is a developmental Level {practice_level or 1} '{exercise_type}' activity, "
        "not a full IELTS essay. Keep the numeric band fields honest for internal progress "
        "tracking, but make the written feedback encouraging and appropriate to the requested "
        "number of sentences. Interpret task_response as instruction fulfilment, "
        "coherence_and_cohesion as sentence order and connections, lexical_resource as useful "
        "word choice, and grammatical_range_and_accuracy as sentence construction. Prioritize "
        "one achievable next step and correct the learner's exact sentences."
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

    @field_validator("strengths", "weaknesses", mode="before")
    @classmethod
    def normalize_feedback_lists(cls, value):
        # Models occasionally return one feedback sentence instead of a JSON
        # array. It still represents one valid item, so preserve it as a list.
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return value


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
    exercise_type: str | None = None
    practice_level: int | None = Field(default=None, ge=1, le=6)


class WritingEvaluationResult(BaseModel):
    status: Literal["ok", "error"]
    error_message: str | None = None
    task_response: CriterionFeedback | None = None
    coherence_and_cohesion: CriterionFeedback | None = None
    lexical_resource: CriterionFeedback | None = None
    grammatical_range_and_accuracy: CriterionFeedback | None = None
    overall_band: float | None = Field(default=None, ge=0, le=9)
    corrections: list[SentenceCorrection] = Field(default_factory=list)

    @model_validator(mode="before")
    @classmethod
    def normalize_provider_payload(cls, value):
        """Normalize common provider shape drift before nested validation."""
        if not isinstance(value, dict):
            return value
        normalized = dict(value)
        overall_band = normalized.get("overall_band")
        if isinstance(overall_band, dict):
            for key in ("band_score", "overall_band", "score", "value"):
                if key in overall_band:
                    normalized["overall_band"] = overall_band[key]
                    break
        return normalized

    @field_validator("overall_band", mode="before")
    @classmethod
    def normalize_overall_band(cls, value):
        """Recover a numeric score when an AI wraps it in a criterion-like object.

        Providers are instructed to return a scalar, but generative models can still
        produce ``{"band_score": 4.5, ...}``. The score is unambiguous in that shape,
        so accepting it avoids discarding an otherwise complete evaluation.
        """
        if isinstance(value, dict):
            for key in ("band_score", "overall_band", "score", "value"):
                if key in value:
                    return value[key]
            raise ValueError("overall_band object does not contain a numeric score")
        return value

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


# Full IELTS Reading/Listening question-type catalog, per
# docs/adr/2026-08-05-ielts-exam-structure-band-scaling.md. Only a subset is
# actually generated at the beginner tier (multiple_choice/true_false_not_given
# for Reading, multiple_choice/note_completion for Listening) — the remaining
# types are reserved for the standard/advanced-tier rollout stages so this
# shape does not need to change again between stages.
OPTION_BASED_QUESTION_TYPES = frozenset({
    "multiple_choice",
    "true_false_not_given",
    "yes_no_not_given",
    "matching_headings",
    "matching_information",
    "matching_features",
    "diagram_labelling",
    "plan_map_diagram_labelling",
    "matching",
})
TEXT_BASED_QUESTION_TYPES = frozenset({
    "sentence_completion",
    "summary_completion",
    "table_completion",
    "flow_chart_completion",
    "short_answer",
    "form_completion",
    "note_completion",
})
QuestionType = Literal[
    "multiple_choice",
    "true_false_not_given",
    "yes_no_not_given",
    "matching_headings",
    "matching_information",
    "matching_features",
    "sentence_completion",
    "summary_completion",
    "table_completion",
    "flow_chart_completion",
    "diagram_labelling",
    "short_answer",
    "form_completion",
    "note_completion",
    "matching",
    "plan_map_diagram_labelling",
]


class GeneratedQuestion(_RequiredTextModel):
    question_text: str
    question_type: QuestionType = "multiple_choice"
    options: list[str] | None = None
    correct_option_index: int | None = Field(default=None, ge=0)
    accepted_answers: list[str] | None = None
    # Shared instructions for a block of questions (e.g. "Questions 6-9: choose
    # the correct heading..."), introduced at the standard tier for grouped
    # types like matching/summary completion — None for standalone questions.
    group_instructions: str | None = None

    @model_validator(mode="after")
    def validate_shape_for_question_type(self):
        if self.question_type in TEXT_BASED_QUESTION_TYPES:
            if not self.accepted_answers:
                raise ValueError(
                    f"{self.question_type} questions require at least one accepted answer"
                )
        else:
            if not self.options:
                raise ValueError(f"{self.question_type} questions require options")
            if self.correct_option_index is None or self.correct_option_index >= len(
                self.options
            ):
                raise ValueError("correct_option_index must index into options")
        return self


# beginner = 1 passage/section, standard = 2, advanced = 3 passages/4 sections
# with the full question-type catalog — see
# docs/adr/2026-08-05-ielts-exam-structure-band-scaling.md.
GenerationTier = Literal["beginner", "standard", "advanced"]


class GeneratedPassage(_RequiredTextModel):
    title: str | None = None
    passage_text: str
    questions: list[GeneratedQuestion] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_has_questions(self):
        if not self.questions:
            raise ValueError("a passage requires at least one question")
        return self


class ReadingExerciseGenerationRequest(_RequiredTextModel):
    focus_description: str
    tier: GenerationTier = "beginner"


class ReadingExerciseGenerationResult(BaseModel):
    status: Literal["ok", "error"]
    error_message: str | None = None
    passages: list[GeneratedPassage] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_status_shape(self):
        if self.status == "ok" and not self.passages:
            raise ValueError(
                "successful reading exercise result requires at least one passage"
            )
        if self.status == "error" and not (
            self.error_message and self.error_message.strip()
        ):
            raise ValueError("error result requires an error message")
        return self


class GeneratedSection(_RequiredTextModel):
    # social_conversation, monologue, educational_discussion, academic_lecture —
    # only social_conversation/monologue are used at standard tier for now.
    context_type: str = "monologue"
    script_text: str
    questions: list[GeneratedQuestion] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_has_questions(self):
        if not self.questions:
            raise ValueError("a section requires at least one question")
        return self


class ListeningScriptGenerationRequest(_RequiredTextModel):
    focus_description: str
    tier: GenerationTier = "beginner"


class ListeningScriptGenerationResult(BaseModel):
    status: Literal["ok", "error"]
    error_message: str | None = None
    sections: list[GeneratedSection] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_status_shape(self):
        if self.status == "ok" and not self.sections:
            raise ValueError(
                "successful listening script result requires at least one section"
            )
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
