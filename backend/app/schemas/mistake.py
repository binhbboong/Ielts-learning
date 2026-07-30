import uuid
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict


class ReasonCategory(str, Enum):
    missing_vocab = "missing_vocab"
    missed_paraphrase = "missed_paraphrase"
    misread_question = "misread_question"
    missing_information = "missing_information"
    outside_knowledge = "outside_knowledge"
    ran_out_of_time = "ran_out_of_time"
    carelessness = "carelessness"
    wrong_grammar = "wrong_grammar"
    not_sure_other = "not_sure_other"


class MistakeCreate(BaseModel):
    skill: str
    source: str
    question_type: str | None = None
    own_answer: str | None = None
    correct_answer: str | None = None
    explanation: str | None = None
    reason_category: ReasonCategory = ReasonCategory.not_sure_other


class MistakeRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    skill: str
    question_type: str | None
    source: str
    own_answer: str | None
    correct_answer: str | None
    explanation: str | None
    reason_category: ReasonCategory
    logged_at: datetime
    is_incomplete: bool


class MistakeGroupedCategory(BaseModel):
    reason_category: ReasonCategory
    count: int


class MistakeCategoryDetail(BaseModel):
    own_answer: str | None
    correct_answer: str | None
    explanation: str | None
