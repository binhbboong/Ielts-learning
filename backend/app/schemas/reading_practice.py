import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ReadingQuestionAnswering(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_text: str
    question_type: str
    options: list[str] | None
    order: int


class ReadingExerciseAnswering(BaseModel):
    day: date
    status: Literal["ready", "failed"]
    focus_reference: str | None
    passage_text: str | None
    questions: list[ReadingQuestionAnswering]


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
