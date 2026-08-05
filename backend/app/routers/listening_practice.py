from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.ai import get_ai_provider
from app.ai.provider import AIProvider
from app.core.db import get_db
from app.core.security import require_learner
from app.models.listening_practice import (
    ListeningExercise,
    ListeningSection,
    ListeningSubmission,
)
from app.models.user import User
from app.schemas.listening_practice import (
    ListeningAnswerResult,
    ListeningExerciseAnswering,
    ListeningSectionAnswering,
    ListeningSubmissionResult,
    ListeningSubmitRequest,
)
from app.services import exam_question_types, listening_practice as service
from app.services.text_to_speech import TextToSpeech, get_text_to_speech

router = APIRouter(
    prefix="/api/listening-practice",
    dependencies=[Depends(require_learner)],
)


def _build_exercise_answering(
    db: Session, exercise: ListeningExercise, *, reveal_scripts: bool
) -> ListeningExerciseAnswering:
    sections = service.get_sections(db, exercise.id)
    questions = service.get_questions(db, exercise.id)
    questions_by_section: dict = {}
    for question in questions:
        questions_by_section.setdefault(question.section_id, []).append(question)
    return ListeningExerciseAnswering(
        day=exercise.day,
        status=exercise.status,
        focus_reference=exercise.focus_reference,
        sections=[
            ListeningSectionAnswering(
                id=section.id,
                context_type=section.context_type,
                script_text=section.script_text if reveal_scripts else None,
                order=section.order,
                questions=questions_by_section.get(section.id, []),
            )
            for section in sections
        ],
    )


@router.get("/{day}", response_model=ListeningExerciseAnswering)
def get_exercise(
    day: date,
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_ai_provider),
    tts: TextToSpeech = Depends(get_text_to_speech),
    user: User = Depends(require_learner),
) -> ListeningExerciseAnswering:
    exercise = service.get_or_create_exercise(db, day, None, provider, tts, user.id)
    has_submission = (
        db.query(ListeningSubmission).filter_by(exercise_id=exercise.id).first()
        is not None
    )
    return _build_exercise_answering(db, exercise, reveal_scripts=has_submission)


@router.get("/{day}/audio/{order}")
def get_audio(
    day: date, order: int, db: Session = Depends(get_db),
    user: User = Depends(require_learner),
) -> Response:
    exercise = db.query(ListeningExercise).filter_by(user_id=user.id, day=day).one_or_none()
    section = (
        db.query(ListeningSection).filter_by(exercise_id=exercise.id, order=order).one_or_none()
        if exercise is not None
        else None
    )
    if section is None or section.audio_bytes is None:
        raise HTTPException(status_code=404, detail="Audio not found")
    return Response(
        content=section.audio_bytes,
        media_type=section.audio_content_type or "application/octet-stream",
    )


@router.post("/{day}/submit", response_model=ListeningSubmissionResult)
def submit(
    day: date,
    payload: ListeningSubmitRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_learner),
) -> ListeningSubmissionResult:
    exercise = db.query(ListeningExercise).filter_by(user_id=user.id, day=day).one_or_none()
    if exercise is None:
        raise HTTPException(status_code=404, detail="Listening exercise not found")

    submission = service.score_submission(db, exercise, payload.answers)
    questions = service.get_questions(db, exercise.id)
    answers = [
        ListeningAnswerResult(
            question_text=question.question_text,
            question_type=question.question_type,
            options=question.options,
            learner_answer=answer,
            correct_answer=exam_question_types.canonical_correct_answer(question),
            correct=exam_question_types.is_correct(question, answer),
        )
        for question, answer in zip(questions, submission.answers)
    ]
    revealed = _build_exercise_answering(db, exercise, reveal_scripts=True)
    return ListeningSubmissionResult(
        day=day,
        score=submission.score,
        total=len(questions),
        sections=revealed.sections,
        answers=answers,
    )


@router.post("/{day}/retry-script", response_model=ListeningExerciseAnswering)
def retry_script(
    day: date,
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_ai_provider),
    user: User = Depends(require_learner),
) -> ListeningExerciseAnswering:
    exercise = service.retry_script(db, day, provider, user.id)
    return _build_exercise_answering(db, exercise, reveal_scripts=False)


@router.post("/{day}/retry-audio", response_model=ListeningExerciseAnswering)
def retry_audio(
    day: date,
    db: Session = Depends(get_db),
    tts: TextToSpeech = Depends(get_text_to_speech),
    user: User = Depends(require_learner),
) -> ListeningExerciseAnswering:
    exercise = service.retry_audio(db, day, tts, user.id)
    return _build_exercise_answering(db, exercise, reveal_scripts=False)
