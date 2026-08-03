import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.ai.provider import AIProvider
from app.ai.schemas import ListeningScriptGenerationRequest
from app.models.listening_practice import (
    ListeningExercise,
    ListeningQuestion,
    ListeningSubmission,
)
from app.services.export_utils import serialize_all, serialize_row
from app.services.text_to_speech import TextToSpeech
from app.models.user import LEGACY_USER_ID

_DEFAULT_FOCUS = "general IELTS listening practice"


def get_questions(db: Session, exercise_id: uuid.UUID) -> list[ListeningQuestion]:
    return (
        db.query(ListeningQuestion)
        .filter_by(exercise_id=exercise_id)
        .order_by(ListeningQuestion.order)
        .all()
    )


def _persist_questions(db: Session, exercise: ListeningExercise, questions) -> None:
    for order, question in enumerate(questions, start=1):
        db.add(
            ListeningQuestion(
                exercise_id=exercise.id,
                question_text=question.question_text,
                options=question.options,
                correct_option_index=question.correct_option_index,
                order=order,
            )
        )


def _generate_script(
    db: Session, exercise: ListeningExercise, provider: AIProvider
) -> bool:
    result = provider.generate_listening_script(
        ListeningScriptGenerationRequest(
            focus_description=exercise.focus_reference or _DEFAULT_FOCUS
        )
    )
    if result.status != "ok":
        exercise.status = "script_failed"
        db.commit()
        db.refresh(exercise)
        return False

    db.query(ListeningQuestion).filter_by(exercise_id=exercise.id).delete()
    exercise.script_text = result.script_text
    exercise.status = "script_generated"
    db.flush()
    _persist_questions(db, exercise, result.questions)
    db.commit()
    db.refresh(exercise)
    return True


def _generate_audio(db: Session, exercise: ListeningExercise, tts: TextToSpeech) -> bool:
    exercise.status = "audio_generating"
    db.commit()

    synthesis = tts.synthesize(exercise.script_text)
    if synthesis.status != "ok":
        exercise.status = "audio_failed"
        db.commit()
        db.refresh(exercise)
        return False

    exercise.audio_bytes = synthesis.audio_bytes
    exercise.audio_content_type = synthesis.content_type
    exercise.status = "ready"
    db.commit()
    db.refresh(exercise)
    return True


def get_or_create_exercise(
    db: Session,
    day: date,
    focus_reference: str | None,
    provider: AIProvider,
    tts: TextToSpeech,
    user_id=LEGACY_USER_ID,
) -> ListeningExercise:
    existing = db.query(ListeningExercise).filter_by(user_id=user_id, day=day).one_or_none()
    if existing is not None:
        return existing

    exercise = ListeningExercise(
        user_id=user_id,
        day=day,
        script_text="",
        audio_bytes=None,
        audio_content_type=None,
        focus_reference=focus_reference,
        status="script_generating",
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)

    if not _generate_script(db, exercise, provider):
        return exercise

    _generate_audio(db, exercise, tts)
    return exercise


def retry_script(
    db: Session, day: date, provider: AIProvider, user_id=LEGACY_USER_ID
) -> ListeningExercise:
    exercise = db.query(ListeningExercise).filter_by(user_id=user_id, day=day).one()
    _generate_script(db, exercise, provider)
    return exercise


def retry_audio(
    db: Session, day: date, tts: TextToSpeech, user_id=LEGACY_USER_ID
) -> ListeningExercise:
    exercise = db.query(ListeningExercise).filter_by(user_id=user_id, day=day).one()
    _generate_audio(db, exercise, tts)
    return exercise


def score_submission(
    db: Session, exercise: ListeningExercise, answers: list[int]
) -> ListeningSubmission:
    questions = get_questions(db, exercise.id)
    score = sum(
        1
        for question, answer in zip(questions, answers)
        if question.correct_option_index == answer
    )
    submission = ListeningSubmission(
        exercise_id=exercise.id, answers=answers, score=score
    )
    db.add(submission)
    db.commit()
    db.refresh(submission)
    return submission


def export_learner_data(db: Session, user_id=LEGACY_USER_ID) -> dict:
    exercise_ids = [
        row.id for row in db.query(ListeningExercise).filter_by(user_id=user_id).all()
    ]
    return {
        "category": "listening_practice",
        "exercises": serialize_all(db, ListeningExercise, user_id),
        "questions": [
            serialize_row(row)
            for row in db.query(ListeningQuestion)
            .filter(ListeningQuestion.exercise_id.in_(exercise_ids))
            .all()
        ],
        "submissions": [
            serialize_row(row)
            for row in db.query(ListeningSubmission)
            .filter(ListeningSubmission.exercise_id.in_(exercise_ids))
            .all()
        ],
    }
