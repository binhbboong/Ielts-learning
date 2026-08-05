import uuid
from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ReadingQuestionAnswering(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_text: str
    question_type: str
    options: list[str] | None
    group_instructions: str | None
    order: int


class ReadingPassageAnswering(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    title: str | None
    passage_text: str
    order: int
    questions: list[ReadingQuestionAnswering]


class ReadingExerciseAnswering(BaseModel):
    day: date
    status: Literal["ready", "failed"]
    focus_reference: str | None
    passages: list[ReadingPassageAnswering]
    # phase/target_minutes come from the day's DailyFocus (Epic-1) when one
    # exists, so the frontend can show a non-blocking countdown timer at
    # standard/advanced tier and none at beginner tier — see
    # docs/adr/2026-08-05-ielts-exam-structure-band-scaling.md.
    phase: str | None = None
    target_minutes: int | None = None


class ReadingSubmitRequest(BaseModel):
    answers: list[int | str]


class ReadingAnswerResult(BaseModel):
    question_text: str
    question_type: str
    options: list[str] | None
    learner_answer: int | str
    correct_answer: int | str | None
    correct: bool


class ReadingSubmissionResult(BaseModel):
    day: date
    score: int
    total: int
    answers: list[ReadingAnswerResult]
