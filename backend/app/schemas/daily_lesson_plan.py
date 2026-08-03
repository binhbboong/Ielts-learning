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


class DailyOverviewResponse(BaseModel):
    exam_type: str
    week: int
    phase: str
    target_band: float
    total_minutes: int
    review_minutes: int
    skills: list[SkillOverviewEntry]
