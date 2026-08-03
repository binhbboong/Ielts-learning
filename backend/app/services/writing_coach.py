import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from sqlalchemy.orm import Session

from app.ai.provider import AIProvider
from app.ai.schemas import WritingEvaluationRequest
from app.models.ai_call_log import AICallLog
from app.models.writing_submission import WritingSubmission
from app.schemas.writing_submission import WritingSubmissionCreate
from app.services.export_utils import serialize_all
from app.models.user import LEGACY_USER_ID


def _run_with_timeout(provider, request, timeout_seconds):
    executor = ThreadPoolExecutor(max_workers=1)
    future = executor.submit(provider.evaluate_writing, request)
    try:
        return future.result(timeout=timeout_seconds)
    except TimeoutError:
        return None
    finally:
        executor.shutdown(wait=False, cancel_futures=True)


def create_and_evaluate(
    db: Session,
    payload: WritingSubmissionCreate,
    provider: AIProvider,
    timeout_seconds: float = 25,
    user_id=LEGACY_USER_ID,
) -> WritingSubmission:
    request = WritingEvaluationRequest(**payload.model_dump())
    result = _run_with_timeout(provider, request, timeout_seconds)
    valid = result is not None and result.status == "ok" and bool(result.corrections)
    submission = WritingSubmission(
        user_id=user_id,
        **payload.model_dump(),
        status="complete" if valid else "failed",
        error_message=(
            None if valid
            else ("Evaluation timed out" if result is None else result.error_message or
                  "Evaluation returned incomplete feedback")
        ),
    )
    if valid:
        submission.task_response = result.task_response.model_dump()
        submission.coherence_and_cohesion = result.coherence_and_cohesion.model_dump()
        submission.lexical_resource = result.lexical_resource.model_dump()
        submission.grammatical_range_and_accuracy = (
            result.grammatical_range_and_accuracy.model_dump()
        )
        submission.overall_band = result.overall_band
        submission.corrections = [item.model_dump() for item in result.corrections]
    db.add(submission)
    db.flush()
    db.add(
        AICallLog(
            submission_id=submission.id,
            provider=provider.__class__.__name__,
            status="ok" if valid else "error",
        )
    )
    db.commit()
    db.refresh(submission)
    return submission


def get_submission_list(db: Session, user_id=LEGACY_USER_ID) -> list[WritingSubmission]:
    return (
        db.query(WritingSubmission)
        .filter(WritingSubmission.user_id == user_id)
        .order_by(WritingSubmission.created_at.desc())
        .all()
    )


def get_submission_detail(
    db: Session, submission_id: uuid.UUID, user_id=LEGACY_USER_ID
) -> WritingSubmission | None:
    return db.query(WritingSubmission).filter_by(id=submission_id, user_id=user_id).one_or_none()


def export_learner_data(db: Session, user_id=LEGACY_USER_ID) -> dict:
    return {
        "category": "writing_submissions",
        "submissions": serialize_all(db, WritingSubmission, user_id),
        "ai_call_log": [
            item
            for item in serialize_all(db, AICallLog)
            if any(
                str(row.id) == item["submission_id"]
                for row in db.query(WritingSubmission).filter_by(user_id=user_id)
            )
        ],
    }
