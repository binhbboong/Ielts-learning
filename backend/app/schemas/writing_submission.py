import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.ai.schemas import CriterionFeedback, SentenceCorrection


class WritingSubmissionCreate(BaseModel):
    response_text: str
    task_type: Literal["task1", "task2"]
    question_text: str
    day: date | None = None

    @field_validator("response_text", "question_text")
    @classmethod
    def required_text(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("must not be empty")
        return value


class WritingSubmissionSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    task_type: Literal["task1", "task2"]
    exercise_type: str | None = None
    practice_level: int | None = None
    status: Literal["complete", "failed"]
    overall_band: float | None
    task_response_score: float | None = None
    question_excerpt: str = ""


class WritingSubmissionDetail(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    created_at: datetime
    task_type: Literal["task1", "task2"]
    exercise_type: str | None = None
    practice_level: int | None = None
    question_text: str
    response_text: str
    status: Literal["complete", "failed"]
    task_response: CriterionFeedback | None
    coherence_and_cohesion: CriterionFeedback | None
    lexical_resource: CriterionFeedback | None
    grammatical_range_and_accuracy: CriterionFeedback | None
    overall_band: float | None
    corrections: list[SentenceCorrection] | None
    error_message: str | None

    @model_validator(mode="after")
    def complete_requires_feedback(self):
        if self.status == "complete":
            values = (
                self.task_response,
                self.coherence_and_cohesion,
                self.lexical_resource,
                self.grammatical_range_and_accuracy,
            )
            if any(value is None for value in values):
                raise ValueError("complete submission requires four criteria")
            if not self.corrections:
                raise ValueError("complete submission requires corrections")
        return self
