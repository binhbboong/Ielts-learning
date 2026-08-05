import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ListeningQuestionAnswering(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_text: str
    question_type: str
    options: list[str] | None
    order: int


class ListeningExerciseAnswering(BaseModel):
    day: date
    status: str
    focus_reference: str | None
    script_text: str | None
    questions: list[ListeningQuestionAnswering]


class ListeningSubmitRequest(BaseModel):
    answers: list[int | str]


class ListeningAnswerResult(BaseModel):
    question_text: str
    question_type: str
    options: list[str] | None
    learner_answer: int | str
    correct_answer: int | str | None
    correct: bool


class ListeningSubmissionResult(BaseModel):
    day: date
    score: int
    total: int
    script_text: str
    answers: list[ListeningAnswerResult]
