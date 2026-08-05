import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.ai.provider import AIProvider
from app.ai.schemas import ReadingExerciseGenerationRequest
from app.models.reading_practice import (
    ReadingExercise,
    ReadingPassage,
    ReadingQuestion,
    ReadingSubmission,
)
from app.services import exam_question_types
from app.services.export_utils import serialize_all, serialize_row
from app.models.user import LEGACY_USER_ID

_DEFAULT_FOCUS = "general IELTS reading practice"


def get_passages(db: Session, exercise_id: uuid.UUID) -> list[ReadingPassage]:
    return (
        db.query(ReadingPassage)
        .filter_by(exercise_id=exercise_id)
        .order_by(ReadingPassage.order)
        .all()
    )


def get_questions(db: Session, exercise_id: uuid.UUID) -> list[ReadingQuestion]:
    return (
        db.query(ReadingQuestion)
        .join(ReadingPassage, ReadingQuestion.passage_id == ReadingPassage.id)
        .filter(ReadingPassage.exercise_id == exercise_id)
        .order_by(ReadingPassage.order, ReadingQuestion.order)
        .all()
    )


def _persist_passages(db: Session, exercise: ReadingExercise, passages) -> None:
    for p_order, passage in enumerate(passages, start=1):
        db_passage = ReadingPassage(
            exercise_id=exercise.id,
            title=passage.title,
            passage_text=passage.passage_text,
            order=p_order,
        )
        db.add(db_passage)
        db.flush()
        for q_order, question in enumerate(passage.questions, start=1):
            db.add(
                ReadingQuestion(
                    passage_id=db_passage.id,
                    question_text=question.question_text,
                    question_type=question.question_type,
                    options=question.options,
                    correct_option_index=question.correct_option_index,
                    accepted_answers=question.accepted_answers,
                    group_instructions=question.group_instructions,
                    order=q_order,
                )
            )


def get_or_create_exercise(
    db: Session, day: date, focus_reference: str | None, provider: AIProvider,
    user_id=LEGACY_USER_ID, tier: str = "beginner",
) -> ReadingExercise:
    existing = db.query(ReadingExercise).filter_by(user_id=user_id, day=day).one_or_none()
    if existing is not None:
        return existing

    result = provider.generate_reading_exercise(
        ReadingExerciseGenerationRequest(
            focus_description=focus_reference or _DEFAULT_FOCUS, tier=tier,
        )
    )

    if result.status != "ok":
        exercise = ReadingExercise(
            user_id=user_id,
            day=day,
            focus_reference=focus_reference,
            status="failed",
        )
        db.add(exercise)
        db.commit()
        db.refresh(exercise)
        return exercise

    exercise = ReadingExercise(
        user_id=user_id,
        day=day,
        focus_reference=focus_reference,
        status="ready",
    )
    db.add(exercise)
    db.flush()
    _persist_passages(db, exercise, result.passages)
    db.commit()
    db.refresh(exercise)
    return exercise


def retry_exercise(
    db: Session, day: date, provider: AIProvider, user_id=LEGACY_USER_ID,
    tier: str = "beginner",
) -> ReadingExercise:
    exercise = db.query(ReadingExercise).filter_by(user_id=user_id, day=day).one()

    result = provider.generate_reading_exercise(
        ReadingExerciseGenerationRequest(
            focus_description=exercise.focus_reference or _DEFAULT_FOCUS, tier=tier,
        )
    )

    if result.status != "ok":
        exercise.status = "failed"
        db.commit()
        db.refresh(exercise)
        return exercise

    old_passage_ids = [p.id for p in get_passages(db, exercise.id)]
    if old_passage_ids:
        db.query(ReadingQuestion).filter(
            ReadingQuestion.passage_id.in_(old_passage_ids)
        ).delete(synchronize_session=False)
        db.query(ReadingPassage).filter_by(exercise_id=exercise.id).delete()
    exercise.status = "ready"
    db.flush()
    _persist_passages(db, exercise, result.passages)
    db.commit()
    db.refresh(exercise)
    return exercise


def score_submission(
    db: Session, exercise: ReadingExercise, answers: list[int | str]
) -> ReadingSubmission:
    existing = (
        db.query(ReadingSubmission).filter_by(exercise_id=exercise.id).one_or_none()
    )
    if existing is not None:
        return existing

    questions = get_questions(db, exercise.id)
    score = sum(
        1
        for question, answer in zip(questions, answers)
        if exam_question_types.is_correct(question, answer)
    )
    submission = ReadingSubmission(
        exercise_id=exercise.id, answers=answers, score=score
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def export_learner_data(db: Session, user_id=LEGACY_USER_ID) -> dict:
    exercise_ids = [
        row.id for row in db.query(ReadingExercise).filter_by(user_id=user_id).all()
    ]
    passage_ids = [
        row.id
        for row in db.query(ReadingPassage)
        .filter(ReadingPassage.exercise_id.in_(exercise_ids))
        .all()
    ]
    return {
        "category": "reading_practice",
        "exercises": serialize_all(db, ReadingExercise, user_id),
        "passages": [
            serialize_row(row)
            for row in db.query(ReadingPassage)
            .filter(ReadingPassage.exercise_id.in_(exercise_ids))
            .all()
        ],
        "questions": [
            serialize_row(row)
            for row in db.query(ReadingQuestion)
            .filter(ReadingQuestion.passage_id.in_(passage_ids))
            .all()
        ],
        "submissions": [
            serialize_row(row)
            for row in db.query(ReadingSubmission)
            .filter(ReadingSubmission.exercise_id.in_(exercise_ids))
            .all()
        ],
    }
