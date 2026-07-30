import base64
import uuid
from pathlib import Path

from sqlalchemy.orm import Session

from app.ai.provider import AIProvider
from app.ai.schemas import SpeakingEvaluationRequest
from app.models.speaking_question import SpeakingQuestion
from app.models.speaking_submission import SpeakingSubmission
from app.services.speech_to_text import SpeechToText
from app.services.export_utils import serialize_all


def create_submission(
    db: Session,
    question_id: uuid.UUID,
    audio_storage_ref: str,
    duration_seconds: int,
) -> SpeakingSubmission:
    if duration_seconds <= 0 or duration_seconds > 120:
        raise ValueError("audio duration must be between 1 and 120 seconds")
    if db.get(SpeakingQuestion, question_id) is None:
        raise LookupError("speaking question not found")
    value = SpeakingSubmission(
        question_id=question_id,
        audio_storage_ref=audio_storage_ref,
        audio_duration_seconds=duration_seconds,
        status="PROCESSING",
    )
    db.add(value)
    db.commit()
    db.refresh(value)
    return value


def run_transcription(
    db: Session,
    submission_id: uuid.UUID,
    speech_to_text: SpeechToText,
) -> SpeakingSubmission:
    value = db.get(SpeakingSubmission, submission_id)
    if value is None:
        raise LookupError("speaking submission not found")
    result = speech_to_text.transcribe(value.audio_storage_ref)
    if result.status == "ok":
        value.transcript = result.transcript
        value.status = "PROCESSING"
        value.error_message = None
    else:
        value.status = "TRANSCRIPTION_FAILED"
        value.error_message = result.error_message
    db.commit()
    db.refresh(value)
    return value


def run_evaluation(
    db: Session,
    submission_id: uuid.UUID,
    provider: AIProvider,
) -> SpeakingSubmission:
    value = db.get(SpeakingSubmission, submission_id)
    if value is None:
        raise LookupError("speaking submission not found")
    if not value.transcript:
        raise ValueError("transcript is required before evaluation")
    question = db.get(SpeakingQuestion, value.question_id)
    result = provider.evaluate_speaking(
        SpeakingEvaluationRequest(
            transcript=value.transcript, question_text=question.prompt
        )
    )
    if result.status == "ok":
        value.fluency_and_coherence = result.fluency_and_coherence.model_dump()
        value.lexical_resource = result.lexical_resource.model_dump()
        value.grammatical_range_and_accuracy = (
            result.grammatical_range_and_accuracy.model_dump()
        )
        value.status = "COMPLETED"
        value.error_message = None
    else:
        value.status = "EVALUATION_FAILED"
        value.error_message = result.error_message
    db.commit()
    db.refresh(value)
    return value


def list_questions(db: Session) -> list[SpeakingQuestion]:
    return db.query(SpeakingQuestion).order_by(SpeakingQuestion.part, SpeakingQuestion.prompt).all()


def list_submissions(db: Session) -> list[SpeakingSubmission]:
    return db.query(SpeakingSubmission).order_by(SpeakingSubmission.created_at.desc()).all()


def get_submission(db: Session, submission_id: uuid.UUID) -> SpeakingSubmission | None:
    return db.get(SpeakingSubmission, submission_id)


def export_learner_data(db: Session) -> dict:
    submissions = serialize_all(db, SpeakingSubmission)
    for item in submissions:
        path = Path(item["audio_storage_ref"])
        item["audio_base64"] = (
            base64.b64encode(path.read_bytes()).decode("ascii")
            if path.is_file()
            else None
        )
    return {
        "category": "speaking_submissions",
        "questions": serialize_all(db, SpeakingQuestion),
        "submissions": submissions,
    }
