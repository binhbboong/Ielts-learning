import uuid
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.orm import Session

from app.ai import get_ai_provider
from app.ai.provider import AIProvider
from app.core.db import get_db
from app.core.security import require_learner
from app.models.speaking_question import SpeakingQuestion
from app.models.speaking_submission import SpeakingSubmission
from app.schemas.speaking_submission import (
    SpeakingQuestionRead,
    SpeakingSubmissionRead,
)
from app.services import speaking_coach
from app.services.speech_to_text import SpeechToText, get_speech_to_text

router = APIRouter(
    prefix="/api/speaking-coach",
    dependencies=[Depends(require_learner)],
)


def _serialize(db: Session, value: SpeakingSubmission) -> SpeakingSubmissionRead:
    question = db.get(SpeakingQuestion, value.question_id)
    return SpeakingSubmissionRead(
        id=value.id,
        question_id=value.question_id,
        question=question.prompt,
        part=question.part,
        audio_duration_seconds=value.audio_duration_seconds,
        transcript=value.transcript,
        status=value.status,
        fluency_and_coherence=value.fluency_and_coherence,
        lexical_resource=value.lexical_resource,
        grammatical_range_and_accuracy=value.grammatical_range_and_accuracy,
        error_message=value.error_message,
        created_at=value.created_at,
    )


@router.get("/questions", response_model=list[SpeakingQuestionRead])
def questions(db: Session = Depends(get_db)):
    return [
        SpeakingQuestionRead(id=value.id, part=value.part, prompt=value.prompt)
        for value in speaking_coach.list_questions(db)
    ]


@router.post(
    "/submissions",
    response_model=SpeakingSubmissionRead,
    status_code=status.HTTP_201_CREATED,
)
async def create(
    question_id: uuid.UUID = Form(...),
    duration_seconds: int = Form(...),
    audio: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    if duration_seconds <= 0 or duration_seconds > 120:
        raise HTTPException(status_code=422, detail="Recording must be 1 to 120 seconds")
    content = await audio.read()
    if not content or len(content) > 20 * 1024 * 1024:
        raise HTTPException(status_code=422, detail="Audio file is empty or too large")
    audio_dir = Path("data/audio")
    audio_dir.mkdir(parents=True, exist_ok=True)
    suffix = Path(audio.filename or "recording.webm").suffix or ".webm"
    path = audio_dir / f"{uuid.uuid4()}{suffix}"
    path.write_bytes(content)
    try:
        value = speaking_coach.create_submission(
            db, question_id, str(path), duration_seconds
        )
    except LookupError as exc:
        path.unlink(missing_ok=True)
        raise HTTPException(status_code=404, detail=str(exc))
    return _serialize(db, value)


@router.post("/submissions/{submission_id}/transcribe", response_model=SpeakingSubmissionRead)
def transcribe(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db),
    stt: SpeechToText = Depends(get_speech_to_text),
):
    try:
        return _serialize(
            db, speaking_coach.run_transcription(db, submission_id, stt)
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))


@router.post("/submissions/{submission_id}/evaluate", response_model=SpeakingSubmissionRead)
def evaluate(
    submission_id: uuid.UUID,
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_ai_provider),
):
    try:
        return _serialize(
            db, speaking_coach.run_evaluation(db, submission_id, provider)
        )
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc))


@router.get("/submissions", response_model=list[SpeakingSubmissionRead])
def submissions(db: Session = Depends(get_db)):
    return [_serialize(db, value) for value in speaking_coach.list_submissions(db)]


@router.get("/submissions/{submission_id}", response_model=SpeakingSubmissionRead)
def detail(submission_id: uuid.UUID, db: Session = Depends(get_db)):
    value = speaking_coach.get_submission(db, submission_id)
    if value is None:
        raise HTTPException(status_code=404, detail="Speaking submission not found")
    return _serialize(db, value)
