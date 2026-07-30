import uuid
from datetime import date, datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict


class ListeningQuestionAnswering(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_text: str
    options: list[str]
    order: int


class ListeningExerciseAnswering(BaseModel):
    day: date
    status: str
    focus_reference: str | None
    script_text: str | None
    questions: list[ListeningQuestionAnswering]


class ListeningSubmitRequest(BaseModel):
    answers: list[int]


class ListeningAnswerResult(BaseModel):
    question_text: str
    options: list[str]
    learner_answer_index: int
    correct_option_index: int
    correct: bool


class ListeningSubmissionResult(BaseModel):
    day: date
    score: int
    total: int
    script_text: str
    answers: list[ListeningAnswerResult]
