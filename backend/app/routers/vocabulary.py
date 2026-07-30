from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import require_learner
from app.schemas.vocabulary import (
    ReviewAssessmentRequest,
    VocabularyWordCreate,
    VocabularyWordRead,
)
from app.services import vocabulary as service

router = APIRouter(
    prefix="/api/vocabulary",
    dependencies=[Depends(require_learner)],
)


def _unavailable(db: Session) -> None:
    db.rollback()
    raise HTTPException(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        detail="Vocabulary data could not be loaded",
    )


def _current_body(result):
    if result.kind == "item":
        return {"status": "item", "item": result.item.model_dump(mode="json")}
    return {"status": result.kind}


@router.post("/words", status_code=status.HTTP_201_CREATED)
def add_word(payload: VocabularyWordCreate, db: Session = Depends(get_db)):
    try:
        word = service.add_word(db, payload)
    except Exception:
        _unavailable(db)
    return {
        "saved": True,
        "word": VocabularyWordRead.model_validate(word).model_dump(mode="json"),
    }


@router.get("/due")
def due(db: Session = Depends(get_db)):
    try:
        return service.get_due_summary(db)
    except Exception:
        _unavailable(db)


@router.post("/review/start")
def start_review(db: Session = Depends(get_db)):
    try:
        service.start_or_resume_review(db)
        return _current_body(service.get_current_item(db))
    except Exception:
        _unavailable(db)


@router.get("/review/current")
def current_item(db: Session = Depends(get_db)):
    try:
        return _current_body(service.get_current_item(db))
    except Exception:
        _unavailable(db)


@router.post("/review/current/assess")
def assess(
    payload: ReviewAssessmentRequest,
    db: Session = Depends(get_db),
):
    try:
        current = service.get_current_item(db)
        if current.kind != "item":
            raise HTTPException(status_code=409, detail="No current review item")
        session_id = current.item.session_id
        result = service.assess_current_item(db, payload.outcome)
        if result.kind == "complete":
            return {
                "status": "complete",
                "summary": service.get_review_complete_summary(
                    db, session_id
                ).model_dump(mode="json"),
            }
        return _current_body(result)
    except HTTPException:
        raise
    except Exception:
        _unavailable(db)
