import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ReadingQuestionAnswering(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_text: str
    options: list[str]
    order: int


class ReadingExerciseAnswering(BaseModel):
    day: date
    status: Literal["ready", "failed"]
    focus_reference: str | None
    passage_text: str | None
    questions: list[ReadingQuestionAnswering]


class ReadingSubmitRequest(BaseModel):
    answers: list[int]


class ReadingAnswerResult(BaseModel):
    question_text: str
    options: list[str]
    learner_answer_index: int
    correct_option_index: int
    correct: bool


class ReadingSubmissionResult(BaseModel):
    day: date
    score: int
    total: int
    answers: list[ReadingAnswerResult]
