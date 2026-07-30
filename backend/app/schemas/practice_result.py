import uuid
from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

from app.models.practice_result_taxonomy import (
    ALLOWED_SKILLS,
    QUESTION_TYPE_TAXONOMY,
)


class QuestionTypeOption(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    key: str
    label: str


class TaxonomyResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    reading: tuple[QuestionTypeOption, ...] = Field(alias="Reading")
    listening: tuple[QuestionTypeOption, ...] = Field(alias="Listening")


class PracticeResultCreate(BaseModel):
    skill: str
    source: str
    score: int = Field(ge=0)
    total: int = Field(gt=0)
    time_taken_seconds: int = Field(gt=0)
    missed_question_types: list[str] = Field(default_factory=list)
    note: str | None = None

    @field_validator("skill", "source")
    @classmethod
    def required_text(cls, value: str) -> str:
        stripped = value.strip()
        if not stripped:
            raise ValueError("must not be empty")
        return stripped

    @field_validator("note")
    @classmethod
    def optional_text(cls, value: str | None) -> str | None:
        if value is None:
            return None
        return value.strip() or None

    @model_validator(mode="after")
    def validate_result(self):
        if self.skill not in ALLOWED_SKILLS:
            raise ValueError("skill must be Reading or Listening")
        if self.score > self.total:
            raise ValueError("score must not exceed total")
        allowed_types = {
            option.key for option in QUESTION_TYPE_TAXONOMY[self.skill]
        }
        invalid_types = set(self.missed_question_types) - allowed_types
        if invalid_types:
            raise ValueError(
                "missed question types must belong to the selected skill"
            )
        return self


class PracticeResultRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    skill: str
    source: str
    score: int
    total: int
    time_taken_seconds: int
    missed_question_types: list[str]
    note: str | None
    logged_at: datetime


class PracticeHistorySkill(str, Enum):
    reading = "Reading"
    listening = "Listening"


class PracticeHistorySort(str, Enum):
    newest = "newest"
    oldest = "oldest"


class PracticeTrendSkill(str, Enum):
    reading = "Reading"
    listening = "Listening"
    both = "Both"


class PracticeTrendPeriod(str, Enum):
    four_weeks = "4_weeks"
    eight_weeks = "8_weeks"
    twelve_weeks = "12_weeks"


class TrendThreshold(BaseModel):
    sufficient: bool
    count: int
    remaining: int


class TrendBreakdownEntry(BaseModel):
    key: str
    count: int


class PracticeTrendResponse(BaseModel):
    session_count: int
    average_score_percentage: float | None
    direction: Literal["up", "steady", "down"] | None
    threshold: TrendThreshold
    breakdown: list[TrendBreakdownEntry]
