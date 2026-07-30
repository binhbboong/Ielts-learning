import uuid
from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, field_validator


class ReviewOutcome(str, Enum):
    forgot = "forgot"
    remembered = "remembered"


class VocabularyWordCreate(BaseModel):
    word: str
    meaning: str
    example: str | None = None
    topic: str | None = None

    @field_validator("word", "meaning")
    @classmethod
    def required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be empty")
        return stripped

    @field_validator("example", "topic")
    @classmethod
    def optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None


class VocabularyWordRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    word: str
    meaning: str
    example: str | None
    topic: str | None
    interval_index: int
    next_due_date: date
    created_at: datetime
    last_reviewed_at: datetime | None


class DueQueueSummary(BaseModel):
    total_due: int
    by_interval: dict[str, int]
    by_topic: dict[str, int]


class ReviewCurrentItem(BaseModel):
    session_id: uuid.UUID
    item_id: uuid.UUID
    word_id: uuid.UUID
    word: str
    meaning: str
    example: str | None
    position: int
    total: int


class ReviewAssessmentRequest(BaseModel):
    outcome: ReviewOutcome


class ReviewCompleteSummary(BaseModel):
    session_id: uuid.UUID
    total_reviewed: int
    forgot: int
    remembered: int
    review_dates_updated: bool = True
