from datetime import date

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.core.security import require_learner
from app.models.user import User
from app.schemas.vocabulary import (
    QuizAnswerRequest,
    ReviewAssessmentRequest,
    VocabularyHistoryDay,
    VocabularyHistoryResponse,
    VocabularyHistoryReview,
    VocabularyHistoryWord,
    VocabularyRecommendationFeed,
    VocabularyWordCreate,
    VocabularyWordRead,
)
from app.core.clock import learner_today
from app.services import vocabulary as service

router = APIRouter(
    prefix="/api/vocabulary",
    dependencies=[Depends(require_learner)],
)


def _target_day(day: date | None) -> date:
    target = day or learner_today()
    if target > learner_today():
        raise HTTPException(status_code=400, detail="Future vocabulary is not available yet")
    return target


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


def _quiz_body(result):
    if result.kind == "item":
        return {"status": "item", "item": result.item.model_dump(mode="json")}
    if result.kind == "complete":
        return {"status": "complete", "summary": result.summary.model_dump(mode="json")}
    return {"status": result.kind}


@router.post("/words", status_code=status.HTTP_201_CREATED)
def add_word(payload: VocabularyWordCreate, db: Session = Depends(get_db), user: User = Depends(require_learner)):
    try:
        word = service.add_word(db, payload, user_id=user.id)
    except Exception:
        _unavailable(db)
    return {
        "saved": True,
        "word": VocabularyWordRead.model_validate(word).model_dump(mode="json"),
    }


@router.get("/due")
def due(db: Session = Depends(get_db), user: User = Depends(require_learner)):
    try:
        return service.get_due_summary(db, user_id=user.id)
    except Exception:
        _unavailable(db)


@router.get("/history", response_model=VocabularyHistoryResponse)
def history(db: Session = Depends(get_db), user: User = Depends(require_learner)):
    try:
        days = service.get_history(db, user_id=user.id)
    except Exception:
        _unavailable(db)
    return VocabularyHistoryResponse(
        days=[
            VocabularyHistoryDay(
                day=day.day,
                words_added=[
                    VocabularyHistoryWord(word=w.word, meaning=w.meaning)
                    for w in day.words_added
                ],
                words_reviewed=[
                    VocabularyHistoryReview(
                        word=r.word, outcome=r.outcome, assessed_at=r.assessed_at
                    )
                    for r in day.words_reviewed
                ],
            )
            for day in days
        ]
    )


@router.get("/recommendations", response_model=VocabularyRecommendationFeed)
def recommendations(
    db: Session = Depends(get_db), user: User = Depends(require_learner)
):
    try:
        return service.get_level_recommendations(db, user.id)
    except Exception:
        _unavailable(db)


@router.post("/recommendations/{key}/add", status_code=status.HTTP_201_CREATED)
def add_recommendation(
    key: str, db: Session = Depends(get_db), user: User = Depends(require_learner)
):
    try:
        word = service.add_level_recommendation(db, key, user.id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except Exception:
        _unavailable(db)
    return {
        "saved": True,
        "word": VocabularyWordRead.model_validate(word).model_dump(mode="json"),
    }


@router.post("/review/start")
def start_review(
    day: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_learner),
):
    try:
        target = _target_day(day)
        service.start_or_resume_review(db, today=target, user_id=user.id)
        return _current_body(
            service.get_current_item(db, today=target, user_id=user.id)
        )
    except HTTPException:
        raise
    except Exception:
        _unavailable(db)


@router.get("/review/current")
def current_item(
    day: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_learner),
):
    try:
        return _current_body(
            service.get_current_item(db, today=_target_day(day), user_id=user.id)
        )
    except HTTPException:
        raise
    except Exception:
        _unavailable(db)


@router.post("/review/current/assess")
def assess(
    payload: ReviewAssessmentRequest,
    day: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_learner),
):
    try:
        target = _target_day(day)
        current = service.get_current_item(db, today=target, user_id=user.id)
        if current.kind != "item":
            raise HTTPException(status_code=409, detail="No current review item")
        session_id = current.item.session_id
        result = service.assess_current_item(
            db, payload.outcome, today=target, user_id=user.id
        )
        if result.kind == "complete":
            return {
                "status": "complete",
                "summary": service.get_review_complete_summary(
                    db, session_id, user.id
                ).model_dump(mode="json"),
            }
        return _current_body(result)
    except HTTPException:
        raise
    except Exception:
        _unavailable(db)


@router.post("/quiz/start")
def start_quiz(
    day: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_learner),
):
    try:
        return _quiz_body(
            service.get_or_start_quiz_item(
                db, day=_target_day(day), user_id=user.id
            )
        )
    except HTTPException:
        raise
    except Exception:
        _unavailable(db)


@router.get("/quiz/current")
def quiz_current(
    day: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_learner),
):
    try:
        return _quiz_body(
            service.get_or_start_quiz_item(
                db, day=_target_day(day), user_id=user.id
            )
        )
    except HTTPException:
        raise
    except Exception:
        _unavailable(db)


@router.post("/quiz/current/answer")
def quiz_answer(
    payload: QuizAnswerRequest,
    day: date | None = None,
    db: Session = Depends(get_db),
    user: User = Depends(require_learner),
):
    try:
        target = _target_day(day)
        result = service.answer_current_quiz_item(
            db, payload.selected_option_index, day=target, user_id=user.id
        )
        return _quiz_body(result)
    except HTTPException:
        raise
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    except Exception:
        _unavailable(db)
