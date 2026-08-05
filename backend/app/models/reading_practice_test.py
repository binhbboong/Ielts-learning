from datetime import date

from app.models.reading_practice import (
    ReadingExercise,
    ReadingPassage,
    ReadingQuestion,
    ReadingSubmission,
)


def test_reading_exercise_with_passage_and_questions_round_trips_through_a_fresh_session(
    db_session_factory,
):
    session = db_session_factory()
    exercise = ReadingExercise(
        day=date(2026, 7, 30),
        focus_reference="the word 'nevertheless'",
        status="ready",
    )
    session.add(exercise)
    session.flush()

    passage = ReadingPassage(
        exercise_id=exercise.id,
        title=None,
        passage_text="A short passage about consequently and nevertheless.",
        order=1,
    )
    session.add(passage)
    session.flush()

    question = ReadingQuestion(
        passage_id=passage.id,
        question_text="What does the passage say about X?",
        options=["A", "B", "C", "D"],
        correct_option_index=2,
        order=1,
    )
    session.add(question)
    session.commit()
    exercise_id = exercise.id
    session.close()

    fresh = db_session_factory()
    reloaded = fresh.query(ReadingExercise).filter_by(id=exercise_id).one()
    assert reloaded.focus_reference == "the word 'nevertheless'"
    assert reloaded.status == "ready"

    reloaded_passage = fresh.query(ReadingPassage).filter_by(exercise_id=exercise_id).one()
    assert reloaded_passage.passage_text == (
        "A short passage about consequently and nevertheless."
    )

    reloaded_question = (
        fresh.query(ReadingQuestion).filter_by(passage_id=reloaded_passage.id).one()
    )
    assert reloaded_question.options == ["A", "B", "C", "D"]
    assert reloaded_question.correct_option_index == 2
    fresh.close()


def test_reading_submission_round_trips_through_a_fresh_session(db_session_factory):
    session = db_session_factory()
    exercise = ReadingExercise(
        day=date(2026, 7, 31),
        focus_reference=None,
        status="ready",
    )
    session.add(exercise)
    session.flush()

    submission = ReadingSubmission(
        exercise_id=exercise.id,
        answers=[0, 2, 1],
        score=2,
    )
    session.add(submission)
    session.commit()
    exercise_id = exercise.id
    session.close()

    fresh = db_session_factory()
    reloaded = fresh.query(ReadingSubmission).filter_by(exercise_id=exercise_id).one()
    assert reloaded.answers == [0, 2, 1]
    assert reloaded.score == 2
    fresh.close()


def test_reading_exercise_day_is_unique(db_session_factory):
    session = db_session_factory()
    session.add(ReadingExercise(day=date(2026, 8, 1), focus_reference=None, status="ready"))
    session.commit()
    session.close()

    session2 = db_session_factory()
    session2.add(ReadingExercise(day=date(2026, 8, 1), focus_reference=None, status="ready"))
    try:
        session2.commit()
        raised = False
    except Exception:
        session2.rollback()
        raised = True
    finally:
        session2.close()

    assert raised is True
