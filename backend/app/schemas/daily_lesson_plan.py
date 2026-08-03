from datetime import date

from pydantic import BaseModel


class SkillOverviewEntry(BaseModel):
    day: date
    skill: str
    status: str
    focus_reference: str | None
    target_band: float
    estimated_minutes: int
    priority: str
    phase: str
    rationale: str
    generated_prompt_text: str | None = None


class CheckpointStatus(BaseModel):
    day: date
    skills: dict[str, bool]
    vocabulary_quiz: bool
    passed_count: int
    required_count: int
    all_passed: bool


class PregenerationResponse(BaseModel):
    processed: dict[str, list[date]]
    errors: dict[str, str]


class DailyOverviewResponse(BaseModel):
    exam_type: str
    week: int
    phase: str
    target_band: float
    total_minutes: int
    review_minutes: int
    effective_day: date
    checkpoint: CheckpointStatus
    skills: list[SkillOverviewEntry]
