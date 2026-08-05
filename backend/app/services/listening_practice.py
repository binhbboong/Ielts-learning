import uuid
from datetime import date

from sqlalchemy.orm import Session

from app.ai.provider import AIProvider
from app.ai.schemas import ListeningScriptGenerationRequest
from app.models.listening_practice import (
    ListeningExercise,
    ListeningQuestion,
    ListeningSection,
    ListeningSubmission,
)
from app.services import exam_question_types
from app.services.export_utils import serialize_all, serialize_row
from app.services.text_to_speech import TextToSpeech
from app.models.user import LEGACY_USER_ID

_DEFAULT_FOCUS = "general IELTS listening practice"


def get_sections(db: Session, exercise_id: uuid.UUID) -> list[ListeningSection]:
    return (
        db.query(ListeningSection)
        .filter_by(exercise_id=exercise_id)
        .order_by(ListeningSection.order)
        .all()
    )


def get_questions(db: Session, exercise_id: uuid.UUID) -> list[ListeningQuestion]:
    return (
        db.query(ListeningQuestion)
        .join(ListeningSection, ListeningQuestion.section_id == ListeningSection.id)
        .filter(ListeningSection.exercise_id == exercise_id)
        .order_by(ListeningSection.order, ListeningQuestion.order)
        .all()
    )


def _persist_questions(db: Session, section: ListeningSection, questions) -> None:
    for order, question in enumerate(questions, start=1):
        db.add(
            ListeningQuestion(
                section_id=section.id,
                question_text=question.question_text,
                question_type=question.question_type,
                options=question.options,
                correct_option_index=question.correct_option_index,
                accepted_answers=question.accepted_answers,
                group_instructions=question.group_instructions,
                order=order,
            )
        )


def _generate_sections(
    db: Session, exercise: ListeningExercise, provider: AIProvider, tier: str
) -> bool:
    result = provider.generate_listening_script(
        ListeningScriptGenerationRequest(
            focus_description=exercise.focus_reference or _DEFAULT_FOCUS, tier=tier,
        )
    )
    if result.status != "ok":
        exercise.status = "script_failed"
        db.commit()
        db.refresh(exercise)
        return False

    old_section_ids = [s.id for s in get_sections(db, exercise.id)]
    if old_section_ids:
        db.query(ListeningQuestion).filter(
            ListeningQuestion.section_id.in_(old_section_ids)
        ).delete(synchronize_session=False)
        db.query(ListeningSection).filter_by(exercise_id=exercise.id).delete()

    exercise.status = "script_generated"
    db.flush()
    for order, section in enumerate(result.sections, start=1):
        db_section = ListeningSection(
            exercise_id=exercise.id,
            context_type=section.context_type,
            script_text=section.script_text,
            order=order,
        )
        db.add(db_section)
        db.flush()
        _persist_questions(db, db_section, section.questions)
    db.commit()
    db.refresh(exercise)
    return True


def _generate_audio(db: Session, exercise: ListeningExercise, tts: TextToSpeech) -> bool:
    exercise.status = "audio_generating"
    db.commit()

    sections = get_sections(db, exercise.id)
    for section in sections:
        synthesis = tts.synthesize(section.script_text)
        if synthesis.status != "ok":
            exercise.status = "audio_failed"
            db.commit()
            db.refresh(exercise)
            return False
        section.audio_bytes = synthesis.audio_bytes
        section.audio_content_type = synthesis.content_type

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
    tier: str = "beginner",
) -> ListeningExercise:
    existing = db.query(ListeningExercise).filter_by(user_id=user_id, day=day).one_or_none()
    if existing is not None:
        return existing

    exercise = ListeningExercise(
        user_id=user_id,
        day=day,
        focus_reference=focus_reference,
        status="script_generating",
    )
    db.add(exercise)
    db.commit()
    db.refresh(exercise)

    if not _generate_sections(db, exercise, provider, tier):
        return exercise

    _generate_audio(db, exercise, tts)
    return exercise


def retry_script(
    db: Session, day: date, provider: AIProvider, user_id=LEGACY_USER_ID,
    tier: str = "beginner",
) -> ListeningExercise:
    exercise = db.query(ListeningExercise).filter_by(user_id=user_id, day=day).one()
    _generate_sections(db, exercise, provider, tier)
    return exercise


def retry_audio(
    db: Session, day: date, tts: TextToSpeech, user_id=LEGACY_USER_ID
) -> ListeningExercise:
    exercise = db.query(ListeningExercise).filter_by(user_id=user_id, day=day).one()
    _generate_audio(db, exercise, tts)
    return exercise


def score_submission(
    db: Session, exercise: ListeningExercise, answers: list[int | str]
) -> ListeningSubmission:
    existing = (
        db.query(ListeningSubmission).filter_by(exercise_id=exercise.id).one_or_none()
    )
    if existing is not None:
        return existing

    questions = get_questions(db, exercise.id)
    score = sum(
        1
        for question, answer in zip(questions, answers)
        if exam_question_types.is_correct(question, answer)
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
    section_ids = [
        row.id
        for row in db.query(ListeningSection)
        .filter(ListeningSection.exercise_id.in_(exercise_ids))
        .all()
    ]
    return {
        "category": "listening_practice",
        "exercises": serialize_all(db, ListeningExercise, user_id),
        "sections": [
            serialize_row(row)
            for row in db.query(ListeningSection)
            .filter(ListeningSection.exercise_id.in_(exercise_ids))
            .all()
        ],
        "questions": [
            serialize_row(row)
            for row in db.query(ListeningQuestion)
            .filter(ListeningQuestion.section_id.in_(section_ids))
            .all()
        ],
        "submissions": [
            serialize_row(row)
            for row in db.query(ListeningSubmission)
            .filter(ListeningSubmission.exercise_id.in_(exercise_ids))
            .all()
        ],
    }
