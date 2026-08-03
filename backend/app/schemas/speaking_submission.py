import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel

from app.ai.schemas import CriterionFeedback


class SpeakingQuestionRead(BaseModel):
    id: uuid.UUID
    part: Literal["PART_1", "PART_2", "PART_3"]
    prompt: str


class SpeakingSubmissionRead(BaseModel):
    id: uuid.UUID
    question_id: uuid.UUID | None
    question: str
    part: str | None
    day: date | None = None
    audio_duration_seconds: int
    transcript: str | None
    status: Literal[
        "PROCESSING",
        "TRANSCRIPTION_FAILED",
        "EVALUATION_FAILED",
        "COMPLETED",
    ]
    fluency_and_coherence: CriterionFeedback | None
    lexical_resource: CriterionFeedback | None
    grammatical_range_and_accuracy: CriterionFeedback | None
    pronunciation: Literal["Not assessed"] = "Not assessed"
    error_message: str | None
    created_at: datetime
