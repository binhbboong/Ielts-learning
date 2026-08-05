import uuid
from datetime import date

from pydantic import BaseModel, ConfigDict


class ListeningQuestionAnswering(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    question_text: str
    question_type: str
    options: list[str] | None
    group_instructions: str | None
    order: int


class ListeningSectionAnswering(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    context_type: str
    script_text: str | None
    order: int
    questions: list[ListeningQuestionAnswering]


class ListeningExerciseAnswering(BaseModel):
    day: date
    status: str
    focus_reference: str | None
    sections: list[ListeningSectionAnswering]


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
    sections: list[ListeningSectionAnswering]
    answers: list[ListeningAnswerResult]
