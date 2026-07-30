from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.ai import get_ai_provider
from app.ai.provider import AIProvider
from app.core.db import get_db
from app.core.security import require_learner
from app.models.listening_practice import ListeningExercise, ListeningSubmission
from app.schemas.listening_practice import (
    ListeningAnswerResult,
    ListeningExerciseAnswering,
    ListeningSubmissionResult,
    ListeningSubmitRequest,
)
from app.services import listening_practice as service
from app.services.text_to_speech import TextToSpeech, get_text_to_speech

router = APIRouter(
    prefix="/api/listening-practice",
    dependencies=[Depends(require_learner)],
)


@router.get("/{day}", response_model=ListeningExerciseAnswering)
def get_exercise(
    day: date,
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_ai_provider),
    tts: TextToSpeech = Depends(get_text_to_speech),
) -> ListeningExerciseAnswering:
    exercise = service.get_or_create_exercise(db, day, None, provider, tts)
    has_submission = (
        db.query(ListeningSubmission).filter_by(exercise_id=exercise.id).first()
        is not None
    )
    return ListeningExerciseAnswering(
        day=exercise.day,
        status=exercise.status,
        focus_reference=exercise.focus_reference,
        script_text=exercise.script_text if has_submission else None,
        questions=service.get_questions(db, exercise.id),
    )


@router.get("/{day}/audio")
def get_audio(day: date, db: Session = Depends(get_db)) -> Response:
    exercise = db.query(ListeningExercise).filter_by(day=day).one_or_none()
    if exercise is None or exercise.audio_bytes is None:
        raise HTTPException(status_code=404, detail="Audio not found")
    return Response(
        content=exercise.audio_bytes,
        media_type=exercise.audio_content_type or "application/octet-stream",
    )


@router.post("/{day}/submit", response_model=ListeningSubmissionResult)
def submit(
    day: date,
    payload: ListeningSubmitRequest,
    db: Session = Depends(get_db),
) -> ListeningSubmissionResult:
    exercise = db.query(ListeningExercise).filter_by(day=day).one_or_none()
    if exercise is None:
        raise HTTPException(status_code=404, detail="Listening exercise not found")

    submission = service.score_submission(db, exercise, payload.answers)
    questions = service.get_questions(db, exercise.id)
    answers = [
        ListeningAnswerResult(
            question_text=question.question_text,
            options=question.options,
            learner_answer_index=answer,
            correct_option_index=question.correct_option_index,
            correct=question.correct_option_index == answer,
        )
        for question, answer in zip(questions, payload.answers)
    ]
    return ListeningSubmissionResult(
        day=day,
        score=submission.score,
        total=len(questions),
        script_text=exercise.script_text,
        answers=answers,
    )


@router.post("/{day}/retry-script", response_model=ListeningExerciseAnswering)
def retry_script(
    day: date,
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_ai_provider),
) -> ListeningExerciseAnswering:
    exercise = service.retry_script(db, day, provider)
    return ListeningExerciseAnswering(
        day=exercise.day,
        status=exercise.status,
        focus_reference=exercise.focus_reference,
        script_text=None,
        questions=service.get_questions(db, exercise.id),
    )


@router.post("/{day}/retry-audio", response_model=ListeningExerciseAnswering)
def retry_audio(
    day: date,
    db: Session = Depends(get_db),
    tts: TextToSpeech = Depends(get_text_to_speech),
) -> ListeningExerciseAnswering:
    exercise = service.retry_audio(db, day, tts)
    return ListeningExerciseAnswering(
        day=exercise.day,
        status=exercise.status,
        focus_reference=exercise.focus_reference,
        script_text=None,
        questions=service.get_questions(db, exercise.id),
    )
