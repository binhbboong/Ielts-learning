from datetime import date

from app.models.listening_practice import (
    ListeningExercise,
    ListeningQuestion,
    ListeningSubmission,
)


def test_listening_exercise_with_questions_round_trips_through_a_fresh_session(
    db_session_factory,
):
    session = db_session_factory()
    exercise = ListeningExercise(
        day=date(2026, 7, 30),
        script_text="A short script about consequently and nevertheless.",
        audio_bytes=b"fake-audio-bytes",
        audio_content_type="audio/mpeg",
        focus_reference="the word 'nevertheless'",
        status="ready",
    )
    session.add(exercise)
    session.flush()

    question = ListeningQuestion(
        exercise_id=exercise.id,
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
    assert reloaded.script_text == "A short script about consequently and nevertheless."
    assert reloaded.audio_bytes == b"fake-audio-bytes"
    assert reloaded.audio_content_type == "audio/mpeg"
    assert reloaded.status == "ready"

    reloaded_question = (
        fresh.query(ListeningQuestion).filter_by(exercise_id=exercise_id).one()
    )
    assert reloaded_question.options == ["A", "B", "C", "D"]
    assert reloaded_question.correct_option_index == 2
    fresh.close()


def test_listening_submission_round_trips_through_a_fresh_session(db_session_factory):
    session = db_session_factory()
    exercise = ListeningExercise(
        day=date(2026, 7, 31),
        script_text="Script text.",
        audio_bytes=None,
        audio_content_type=None,
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
    session.add(
        ListeningExercise(
            day=date(2026, 8, 1),
            script_text="First.",
            audio_bytes=None,
            audio_content_type=None,
            focus_reference=None,
            status="ready",
        )
    )
    session.commit()
    session.close()

    session2 = db_session_factory()
    session2.add(
        ListeningExercise(
            day=date(2026, 8, 1),
            script_text="Second.",
            audio_bytes=None,
            audio_content_type=None,
            focus_reference=None,
            status="ready",
        )
    )
    try:
        session2.commit()
        raised = False
    except Exception:
        session2.rollback()
        raised = True
    finally:
        session2.close()

    assert raised is True
