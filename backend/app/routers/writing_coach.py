import uuid

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai import get_ai_provider
from app.ai.provider import AIProvider
from app.core.db import get_db
from app.core.security import require_learner
from app.models.user import User
from app.schemas.writing_submission import (
    WritingSubmissionCreate,
    WritingSubmissionDetail,
    WritingSubmissionSummary,
)
from app.services import writing_coach

router = APIRouter(
    prefix="/api/writing-coach",
    dependencies=[Depends(require_learner)],
)


def _detail(value) -> WritingSubmissionDetail:
    return WritingSubmissionDetail.model_validate(value)


@router.post("/submissions", response_model=WritingSubmissionDetail)
def create_submission(
    payload: WritingSubmissionCreate,
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_ai_provider),
    user: User = Depends(require_learner),
) -> WritingSubmissionDetail:
    return _detail(writing_coach.create_and_evaluate(db, payload, provider, user_id=user.id))


@router.get("/submissions", response_model=list[WritingSubmissionSummary])
def list_submissions(db: Session = Depends(get_db), user: User = Depends(require_learner)):
    return [
        WritingSubmissionSummary(
            id=value.id,
            created_at=value.created_at,
            task_type=value.task_type,
            status=value.status,
            overall_band=value.overall_band,
            task_response_score=(
                value.task_response.get("band_score") if value.task_response else None
            ),
            question_excerpt=value.question_text[:120],
        )
        for value in writing_coach.get_submission_list(db, user.id)
    ]


@router.get("/submissions/{submission_id}", response_model=WritingSubmissionDetail)
def submission_detail(
    submission_id: uuid.UUID, db: Session = Depends(get_db),
    user: User = Depends(require_learner),
) -> WritingSubmissionDetail:
    value = writing_coach.get_submission_detail(db, submission_id, user.id)
    if value is None:
        raise HTTPException(status_code=404, detail="Writing submission not found")
    return _detail(value)
