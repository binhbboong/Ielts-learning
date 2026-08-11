from datetime import date

from pydantic import BaseModel, Field


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
    task_type: str | None = None
    writing_level: int | None = None
    exercise_type: str | None = None
    exercise_label: str | None = None
    objective: str | None = None
    min_sentences: int | None = None
    max_sentences: int | None = None
    min_words: int | None = None
    max_words: int | None = None
    sentence_frames: list[str] = Field(default_factory=list)
    show_ielts_band: bool = False


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
