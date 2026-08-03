from datetime import datetime

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.mistake import Mistake
from app.schemas.mistake import (
    MistakeCreate,
    MistakeGroupedCategory,
    MistakeRead,
    ReasonCategory,
)
from app.services.export_utils import serialize_all
from app.models.user import LEGACY_USER_ID


def create_mistake(session: Session, payload: MistakeCreate, user_id=LEGACY_USER_ID) -> Mistake:
    mistake = Mistake(user_id=user_id, **payload.model_dump())
    session.add(mistake)
    session.commit()
    session.refresh(mistake)
    return mistake


def is_incomplete(mistake: Mistake) -> bool:
    return (
        mistake.correct_answer is None
        or mistake.reason_category == ReasonCategory.not_sure_other
    )


def mistake_to_read(mistake: Mistake) -> MistakeRead:
    return MistakeRead.model_validate(
        {
            "id": mistake.id,
            "skill": mistake.skill,
            "question_type": mistake.question_type,
            "source": mistake.source,
            "own_answer": mistake.own_answer,
            "correct_answer": mistake.correct_answer,
            "explanation": mistake.explanation,
            "reason_category": mistake.reason_category,
            "logged_at": mistake.logged_at,
            "is_incomplete": is_incomplete(mistake),
        }
    )


def list_mistakes(
    session: Session, start: datetime, end: datetime, user_id=LEGACY_USER_ID
) -> list[Mistake]:
    statement = (
        select(Mistake)
        .where(Mistake.user_id == user_id, Mistake.logged_at.between(start, end))
        .order_by(Mistake.logged_at.desc())
    )
    return list(session.scalars(statement))


def export_learner_data(session: Session, user_id=LEGACY_USER_ID) -> dict:
    return {
        "category": "mistakes",
        "entries": serialize_all(session, Mistake, user_id),
    }


def list_grouped_by_reason(
    session: Session, start: datetime, end: datetime, user_id=LEGACY_USER_ID
) -> list[MistakeGroupedCategory]:
    count = func.count(Mistake.id)
    statement = (
        select(Mistake.reason_category, count)
        .where(Mistake.user_id == user_id, Mistake.logged_at.between(start, end))
        .group_by(Mistake.reason_category)
        .order_by(count.desc(), Mistake.reason_category)
    )
    return [
        MistakeGroupedCategory(reason_category=reason, count=row_count)
        for reason, row_count in session.execute(statement)
    ]


def get_category_detail(
    session: Session,
    reason_category: ReasonCategory,
    start: datetime,
    end: datetime,
    user_id=LEGACY_USER_ID,
) -> list[Mistake]:
    statement = (
        select(Mistake)
        .where(
            Mistake.reason_category == reason_category,
            Mistake.user_id == user_id,
            Mistake.logged_at.between(start, end),
        )
        .order_by(Mistake.logged_at.desc())
    )
    return list(session.scalars(statement))
