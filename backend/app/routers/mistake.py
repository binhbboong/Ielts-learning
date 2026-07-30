from datetime import datetime

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import require_learner
from app.schemas.mistake import (
    MistakeCategoryDetail,
    MistakeCreate,
    MistakeGroupedCategory,
    MistakeRead,
    ReasonCategory,
)
from app.services import mistake as service

router = APIRouter(
    prefix="/api/mistakes",
    dependencies=[Depends(require_learner)],
)


@router.post("", response_model=MistakeRead, status_code=status.HTTP_201_CREATED)
def create(payload: MistakeCreate, db: Session = Depends(get_db)):
    return service.mistake_to_read(service.create_mistake(db, payload))


@router.get("", response_model=list[MistakeRead])
def chronological(
    start: datetime,
    end: datetime,
    db: Session = Depends(get_db),
):
    return [
        service.mistake_to_read(row)
        for row in service.list_mistakes(db, start, end)
    ]


@router.get("/grouped", response_model=list[MistakeGroupedCategory])
def grouped(
    start: datetime,
    end: datetime,
    db: Session = Depends(get_db),
):
    return service.list_grouped_by_reason(db, start, end)


@router.get(
    "/grouped/{reason_category}",
    response_model=list[MistakeCategoryDetail],
)
def category_detail(
    reason_category: ReasonCategory,
    start: datetime,
    end: datetime,
    db: Session = Depends(get_db),
):
    return service.get_category_detail(
        db, reason_category, start, end
    )
