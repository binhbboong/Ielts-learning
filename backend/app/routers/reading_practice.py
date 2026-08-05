from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.ai import get_ai_provider
from app.ai.provider import AIProvider
from app.core.db import get_db
from app.core.security import require_learner
from app.models.reading_practice import ReadingExercise
from app.models.user import User
from app.schemas.reading_practice import (
    ReadingAnswerResult,
    ReadingExerciseAnswering,
    ReadingSubmissionResult,
    ReadingSubmitRequest,
)
from app.services import exam_question_types, reading_practice as service

router = APIRouter(
    prefix="/api/reading-practice",
    dependencies=[Depends(require_learner)],
)


@router.get("/{day}", response_model=ReadingExerciseAnswering)
def get_exercise(
    day: date,
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_ai_provider),
    user: User = Depends(require_learner),
) -> ReadingExerciseAnswering:
    exercise = service.get_or_create_exercise(db, day, None, provider, user.id)
    return ReadingExerciseAnswering(
        day=exercise.day,
        status=exercise.status,
        focus_reference=exercise.focus_reference,
        passage_text=exercise.passage_text if exercise.status == "ready" else None,
        questions=service.get_questions(db, exercise.id),
    )


@router.post("/{day}/submit", response_model=ReadingSubmissionResult)
def submit(
    day: date,
    payload: ReadingSubmitRequest,
    db: Session = Depends(get_db),
    user: User = Depends(require_learner),
) -> ReadingSubmissionResult:
    exercise = db.query(ReadingExercise).filter_by(user_id=user.id, day=day).one_or_none()
    if exercise is None:
        raise HTTPException(status_code=404, detail="Reading exercise not found")

    submission = service.score_submission(db, exercise, payload.answers)
    questions = service.get_questions(db, exercise.id)
    answers = [
        ReadingAnswerResult(
            question_text=question.question_text,
            question_type=question.question_type,
            options=question.options,
            learner_answer=answer,
            correct_answer=exam_question_types.canonical_correct_answer(question),
            correct=exam_question_types.is_correct(question, answer),
        )
        for question, answer in zip(questions, submission.answers)
    ]
    return ReadingSubmissionResult(
        day=day, score=submission.score, total=len(questions), answers=answers
    )


@router.post("/{day}/retry", response_model=ReadingExerciseAnswering)
def retry(
    day: date,
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_ai_provider),
    user: User = Depends(require_learner),
) -> ReadingExerciseAnswering:
    exercise = service.retry_exercise(db, day, provider, user.id)
    return ReadingExerciseAnswering(
        day=exercise.day,
        status=exercise.status,
        focus_reference=exercise.focus_reference,
        passage_text=exercise.passage_text if exercise.status == "ready" else None,
        questions=service.get_questions(db, exercise.id),
    )
