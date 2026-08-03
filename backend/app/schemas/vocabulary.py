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
    target_band: float | None
    cefr_level: str | None
    source: str
    interval_index: int
    next_due_date: date
    created_at: datetime
    last_reviewed_at: datetime | None


class DueQueueSummary(BaseModel):
    total_due: int
    by_interval: dict[str, int]
    by_topic: dict[str, int]
    daily_target: int
    backfill_count: int
    shortfall: bool


class VocabularyRecommendation(BaseModel):
    key: str
    word: str
    meaning: str
    example: str
    topic: str
    target_band: float
    cefr_level: str


class VocabularyRecommendationFeed(BaseModel):
    current_band: float
    cefr_level: str
    phase: str
    week: int
    recommendations: list[VocabularyRecommendation]


class ReviewCurrentItem(BaseModel):
    session_id: uuid.UUID
    item_id: uuid.UUID
    word_id: uuid.UUID
    word: str
    meaning: str
    example: str | None
    position: int
    total: int
    is_new: bool


class ReviewAssessmentRequest(BaseModel):
    outcome: ReviewOutcome


class ReviewCompleteSummary(BaseModel):
    session_id: uuid.UUID
    total_reviewed: int
    forgot: int
    remembered: int
    new_words_included: int
    review_dates_updated: bool = True


class VocabularyHistoryWord(BaseModel):
    word: str
    meaning: str


class VocabularyHistoryReview(BaseModel):
    word: str
    outcome: str
    assessed_at: datetime


class VocabularyHistoryDay(BaseModel):
    day: date
    words_added: list[VocabularyHistoryWord]
    words_reviewed: list[VocabularyHistoryReview]


class VocabularyHistoryResponse(BaseModel):
    days: list[VocabularyHistoryDay]
