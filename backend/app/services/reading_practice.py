import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.ai.provider import AIProvider
from app.ai.schemas import ReadingExerciseGenerationRequest
from app.models.reading_practice import ReadingExercise, ReadingQuestion, ReadingSubmission
from app.services.export_utils import serialize_all

_DEFAULT_FOCUS = "general IELTS reading practice"


def get_questions(db: Session, exercise_id: uuid.UUID) -> list[ReadingQuestion]:
    return (
        db.query(ReadingQuestion)
        .filter_by(exercise_id=exercise_id)
        .order_by(ReadingQuestion.order)
        .all()
    )


def get_or_create_exercise(
    db: Session, day: date, focus_reference: str | None, provider: AIProvider
) -> ReadingExercise:
    existing = db.query(ReadingExercise).filter_by(day=day).one_or_none()
    if existing is not None:
        return existing

    result = provider.generate_reading_exercise(
        ReadingExerciseGenerationRequest(
            focus_description=focus_reference or _DEFAULT_FOCUS
        )
    )

    if result.status != "ok":
        exercise = ReadingExercise(
            day=day,
            passage_text="",
            focus_reference=focus_reference,
            status="failed",
        )
        db.add(exercise)
        db.commit()
        db.refresh(exercise)
        return exercise

    exercise = ReadingExercise(
        day=day,
        passage_text=result.passage_text,
        focus_reference=focus_reference,
        status="ready",
    )
    db.add(exercise)
    db.flush()
    for order, question in enumerate(result.questions, start=1):
        db.add(
            ReadingQuestion(
                exercise_id=exercise.id,
                question_text=question.question_text,
                options=question.options,
                correct_option_index=question.correct_option_index,
                order=order,
            )
        )
    db.commit()
    db.refresh(exercise)
    return exercise


def retry_exercise(db: Session, day: date, provider: AIProvider) -> ReadingExercise:
    exercise = db.query(ReadingExercise).filter_by(day=day).one()

    result = provider.generate_reading_exercise(
        ReadingExerciseGenerationRequest(
            focus_description=exercise.focus_reference or _DEFAULT_FOCUS
        )
    )

    if result.status != "ok":
        exercise.status = "failed"
        db.commit()
        db.refresh(exercise)
        return exercise

    db.query(ReadingQuestion).filter_by(exercise_id=exercise.id).delete()
    exercise.passage_text = result.passage_text
    exercise.status = "ready"
    db.flush()
    for order, question in enumerate(result.questions, start=1):
        db.add(
            ReadingQuestion(
                exercise_id=exercise.id,
                question_text=question.question_text,
                options=question.options,
                correct_option_index=question.correct_option_index,
                order=order,
            )
        )
    db.commit()
    db.refresh(exercise)
    return exercise


def score_submission(
    db: Session, exercise: ReadingExercise, answers: list[int]
) -> ReadingSubmission:
    questions = get_questions(db, exercise.id)
    score = sum(
        1
        for question, answer in zip(questions, answers)
        if question.correct_option_index == answer
    )
    submission = ReadingSubmission(
        exercise_id=exercise.id, answers=answers, score=score
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def export_learner_data(db: Session) -> dict:
    return {
        "category": "reading_practice",
        "exercises": serialize_all(db, ReadingExercise),
        "questions": serialize_all(db, ReadingQuestion),
        "submissions": serialize_all(db, ReadingSubmission),
    }
