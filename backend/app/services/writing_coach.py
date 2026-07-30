import uuid
from concurrent.futures import ThreadPoolExecutor, TimeoutError

from sqlalchemy.orm import Session

from app.ai.provider import AIProvider
from app.ai.schemas import WritingEvaluationRequest
from app.models.ai_call_log import AICallLog
from app.models.writing_submission import WritingSubmission
from app.schemas.writing_submission import WritingSubmissionCreate
from app.services.export_utils import serialize_all


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
) -> WritingSubmission:
    request = WritingEvaluationRequest(**payload.model_dump())
    result = _run_with_timeout(provider, request, timeout_seconds)
    valid = result is not None and result.status == "ok" and bool(result.corrections)
    submission = WritingSubmission(
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


def get_submission_list(db: Session) -> list[WritingSubmission]:
    return (
        db.query(WritingSubmission)
        .order_by(WritingSubmission.created_at.desc())
        .all()
    )


def get_submission_detail(
    db: Session, submission_id: uuid.UUID
) -> WritingSubmission | None:
    return db.get(WritingSubmission, submission_id)


def export_learner_data(db: Session) -> dict:
    return {
        "category": "writing_submissions",
        "submissions": serialize_all(db, WritingSubmission),
        "ai_call_log": serialize_all(db, AICallLog),
    }
