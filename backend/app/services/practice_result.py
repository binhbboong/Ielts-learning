from datetime import date, timedelta
from dataclasses import asdict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.clock import learner_day_start_utc, learner_today
from app.models.practice_result import PracticeResult
from app.schemas.practice_result import (
    PracticeHistorySkill,
    PracticeHistorySort,
    PracticeResultCreate,
    PracticeTrendPeriod,
    PracticeTrendResponse,
    PracticeTrendSkill,
)
from app.services.practice_trend import compute_trend
from app.services.export_utils import serialize_all
from app.models.user import LEGACY_USER_ID


def create_result(
    session: Session, payload: PracticeResultCreate, user_id=LEGACY_USER_ID
) -> PracticeResult:
    result = PracticeResult(user_id=user_id, **payload.model_dump())
    session.add(result)
    session.commit()
    session.refresh(result)
    return result


def list_results(
    session: Session,
    *,
    skill: PracticeHistorySkill | None = None,
    sort: PracticeHistorySort = PracticeHistorySort.newest,
    user_id=LEGACY_USER_ID,
) -> list[PracticeResult]:
    query = select(PracticeResult).where(PracticeResult.user_id == user_id)
    if skill is not None:
        query = query.where(PracticeResult.skill == skill.value)
    ordering = (
        PracticeResult.logged_at.desc()
        if sort == PracticeHistorySort.newest
        else PracticeResult.logged_at.asc()
    )
    return list(
        session.scalars(query.order_by(ordering, PracticeResult.id))
    )


_PERIOD_DAYS = {
    PracticeTrendPeriod.four_weeks: 28,
    PracticeTrendPeriod.eight_weeks: 56,
    PracticeTrendPeriod.twelve_weeks: 84,
}


def get_trend(
    session: Session,
    *,
    skill: PracticeTrendSkill,
    period: PracticeTrendPeriod,
    today: date | None = None,
    user_id=LEGACY_USER_ID,
) -> PracticeTrendResponse:
    current_date = today or learner_today()
    period_start = current_date - timedelta(
        days=_PERIOD_DAYS[period] - 1
    )
    query = select(PracticeResult).where(
        PracticeResult.user_id == user_id,
        PracticeResult.logged_at >= learner_day_start_utc(period_start)
    )
    if skill != PracticeTrendSkill.both:
        query = query.where(PracticeResult.skill == skill.value)
    rows = list(
        session.scalars(
            query.order_by(PracticeResult.logged_at, PracticeResult.id)
        )
    )
    result = compute_trend(rows)
    return PracticeTrendResponse.model_validate(asdict(result))


def export_learner_data(session: Session, user_id=LEGACY_USER_ID) -> dict:
    return {
        "category": "practice_results",
        "entries": serialize_all(session, PracticeResult, user_id),
    }
