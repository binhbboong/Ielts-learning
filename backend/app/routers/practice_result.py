from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import require_learner
from app.models.user import User
from app.models.practice_result import PracticeResult
from app.models.practice_result_taxonomy import QUESTION_TYPE_TAXONOMY
from app.schemas.practice_result import (
    PracticeHistorySkill,
    PracticeHistorySort,
    PracticeResultCreate,
    PracticeResultRead,
    PracticeTrendPeriod,
    PracticeTrendResponse,
    PracticeTrendSkill,
    TaxonomyResponse,
)
from app.services import practice_result as service

router = APIRouter(
    prefix="/api/practice-results",
    dependencies=[Depends(require_learner)],
)


@router.get("/taxonomy", response_model=TaxonomyResponse)
def taxonomy() -> TaxonomyResponse:
    return TaxonomyResponse(
        reading=QUESTION_TYPE_TAXONOMY["Reading"],
        listening=QUESTION_TYPE_TAXONOMY["Listening"],
    )


@router.post(
    "",
    response_model=PracticeResultRead,
    status_code=status.HTTP_201_CREATED,
)
def create(
    payload: PracticeResultCreate,
    db: Session = Depends(get_db),
    user: User = Depends(require_learner),
) -> PracticeResult:
    return service.create_result(db, payload, user.id)


@router.get("", response_model=list[PracticeResultRead])
def history(
    skill: PracticeHistorySkill | None = None,
    sort: PracticeHistorySort = PracticeHistorySort.newest,
    db: Session = Depends(get_db),
    user: User = Depends(require_learner),
) -> list[PracticeResult]:
    return service.list_results(db, skill=skill, sort=sort, user_id=user.id)


@router.get("/trend", response_model=PracticeTrendResponse)
def trend(
    skill: PracticeTrendSkill = PracticeTrendSkill.both,
    period: PracticeTrendPeriod = PracticeTrendPeriod.eight_weeks,
    db: Session = Depends(get_db),
    user: User = Depends(require_learner),
) -> PracticeTrendResponse:
    try:
        return service.get_trend(db, skill=skill, period=period, user_id=user.id)
    except Exception:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Progress data could not be loaded",
        )
