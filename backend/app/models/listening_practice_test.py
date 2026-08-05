from datetime import date

from app.models.listening_practice import (
    ListeningExercise,
    ListeningQuestion,
    ListeningSection,
    ListeningSubmission,
)


def test_listening_exercise_with_section_and_questions_round_trips_through_a_fresh_session(
    db_session_factory,
):
    session = db_session_factory()
    exercise = ListeningExercise(
        day=date(2026, 7, 30),
        focus_reference="the word 'nevertheless'",
        status="ready",
    )
    session.add(exercise)
    session.flush()

    section = ListeningSection(
        exercise_id=exercise.id,
        context_type="monologue",
        script_text="A short script about consequently and nevertheless.",
        audio_bytes=b"fake-audio-bytes",
        audio_content_type="audio/mpeg",
        order=1,
    )
    session.add(section)
    session.flush()

    question = ListeningQuestion(
        section_id=section.id,
        question_text="What does the script say about X?",
        options=["A", "B", "C", "D"],
        correct_option_index=2,
        order=1,
    )
    session.add(question)
    session.commit()
    exercise_id = exercise.id
    session.close()

    fresh = db_session_factory()
    reloaded = fresh.query(ListeningExercise).filter_by(id=exercise_id).one()
    assert reloaded.status == "ready"

    reloaded_section = (
        fresh.query(ListeningSection).filter_by(exercise_id=exercise_id).one()
    )
    assert reloaded_section.script_text == (
        "A short script about consequently and nevertheless."
    )
    assert reloaded_section.audio_bytes == b"fake-audio-bytes"
    assert reloaded_section.audio_content_type == "audio/mpeg"

    reloaded_question = (
        fresh.query(ListeningQuestion).filter_by(section_id=reloaded_section.id).one()
    )
    assert reloaded_question.options == ["A", "B", "C", "D"]
    assert reloaded_question.correct_option_index == 2
    fresh.close()


def test_listening_submission_round_trips_through_a_fresh_session(db_session_factory):
    session = db_session_factory()
    exercise = ListeningExercise(
        day=date(2026, 7, 31),
        focus_reference=None,
        status="script_generating",
    )
    session.add(exercise)
    session.flush()

    submission = ListeningSubmission(
        exercise_id=exercise.id,
        answers=[0, 2, 1],
        score=2,
    )
    session.add(submission)
    session.commit()
    exercise_id = exercise.id
    session.close()

    fresh = db_session_factory()
    reloaded = fresh.query(ListeningSubmission).filter_by(exercise_id=exercise_id).one()
    assert reloaded.answers == [0, 2, 1]
    assert reloaded.score == 2
    fresh.close()


def test_listening_exercise_day_is_unique(db_session_factory):
    session = db_session_factory()
    session.add(ListeningExercise(day=date(2026, 8, 1), focus_reference=None, status="ready"))
    session.commit()
    session.close()

    session2 = db_session_factory()
    session2.add(ListeningExercise(day=date(2026, 8, 1), focus_reference=None, status="ready"))
    try:
        session2.commit()
        raised = False
    except Exception:
        session2.rollback()
        raised = True
    finally:
        session2.close()

    assert raised is True
