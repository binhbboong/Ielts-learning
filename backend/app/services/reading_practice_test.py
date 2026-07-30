from datetime import date

from app.ai.schemas import (
    GeneratedQuestion,
    ReadingExerciseGenerationRequest,
    ReadingExerciseGenerationResult,
)

from app.ai.testing import FakeAIProvider
from app.models.reading_practice import ReadingExercise, ReadingQuestion
from app.services.reading_practice import (
    get_or_create_exercise,
    retry_exercise,
    score_submission,
)


def _success_result() -> ReadingExerciseGenerationResult:
    return ReadingExerciseGenerationResult(
        status="ok",
        passage_text="A passage about nevertheless.",
        questions=[
            GeneratedQuestion(
                question_text="What is discussed?",
                options=["A", "B", "C", "D"],
                correct_option_index=1,
            )
        ],
    )


def test_first_call_generates_and_persists_exercise_with_questions(db_session_factory):
    session = db_session_factory()
    provider = FakeAIProvider(reading_exercise_result=_success_result())

    exercise = get_or_create_exercise(
        session, date(2026, 7, 30), "the word 'nevertheless'", provider
    )

    assert exercise.status == "ready"
    assert exercise.passage_text == "A passage about nevertheless."
    assert provider.reading_exercise_requests == [
        ReadingExerciseGenerationRequest(focus_description="the word 'nevertheless'")
    ]
    questions = (
        session.query(ReadingQuestion).filter_by(exercise_id=exercise.id).all()
    )
    assert len(questions) == 1
    assert questions[0].correct_option_index == 1
    session.close()


def test_second_call_same_day_returns_identical_row_without_regenerating(
    db_session_factory,
):
    session = db_session_factory()
    provider = FakeAIProvider(reading_exercise_result=_success_result())

    first = get_or_create_exercise(
        session, date(2026, 7, 30), "the word 'nevertheless'", provider
    )
    second = get_or_create_exercise(
        session, date(2026, 7, 30), "the word 'nevertheless'", provider
    )

    assert first.id == second.id
    assert len(provider.reading_exercise_requests) == 1
    session.close()


def test_generation_failure_persists_a_failed_status_exercise(db_session_factory):
    session = db_session_factory()
    provider = FakeAIProvider(
        reading_exercise_result=ReadingExerciseGenerationResult(
            status="error", error_message="provider timeout"
        )
    )

    exercise = get_or_create_exercise(
        session, date(2026, 7, 30), "the word 'nevertheless'", provider
    )

    assert exercise.status == "failed"
    reloaded = session.query(ReadingExercise).filter_by(day=date(2026, 7, 30)).one()
    assert reloaded.status == "failed"
    session.close()


def test_no_focus_reference_still_generates_using_a_general_default(db_session_factory):
    session = db_session_factory()
    provider = FakeAIProvider(reading_exercise_result=_success_result())

    get_or_create_exercise(session, date(2026, 7, 30), None, provider)

    assert provider.reading_exercise_requests[0].focus_description
    session.close()


def _three_question_result() -> ReadingExerciseGenerationResult:
    return ReadingExerciseGenerationResult(
        status="ok",
        passage_text="A passage with three questions.",
        questions=[
            GeneratedQuestion(
                question_text="Q1?", options=["A", "B", "C", "D"], correct_option_index=0
            ),
            GeneratedQuestion(
                question_text="Q2?", options=["A", "B", "C", "D"], correct_option_index=1
            ),
            GeneratedQuestion(
                question_text="Q3?", options=["A", "B", "C", "D"], correct_option_index=2
            ),
        ],
    )


def test_score_submission_computes_correct_count_without_any_ai_call(db_session_factory):
    session = db_session_factory()
    generation_provider = FakeAIProvider(reading_exercise_result=_three_question_result())
    exercise = get_or_create_exercise(
        session, date(2026, 7, 30), "focus", generation_provider
    )

    # Answers: correct, wrong, correct (2 out of 3)
    submission = score_submission(session, exercise, [0, 0, 2])

    assert submission.score == 2
    assert submission.answers == [0, 0, 2]
    # score_submission takes no AIProvider argument at all, so it structurally
    # cannot call the AI provider during scoring.
    assert len(generation_provider.reading_exercise_requests) == 1
    session.close()


def test_retry_after_failure_reuses_the_original_focus_and_succeeds(db_session_factory):
    session = db_session_factory()
    failing_provider = FakeAIProvider(
        reading_exercise_result=ReadingExerciseGenerationResult(
            status="error", error_message="provider timeout"
        )
    )
    exercise = get_or_create_exercise(
        session, date(2026, 7, 30), "the word 'nevertheless'", failing_provider
    )
    assert exercise.status == "failed"

    succeeding_provider = FakeAIProvider(reading_exercise_result=_success_result())
    retried = retry_exercise(session, date(2026, 7, 30), succeeding_provider)

    assert retried.status == "ready"
    assert retried.id == exercise.id
    assert succeeding_provider.reading_exercise_requests == [
        ReadingExerciseGenerationRequest(focus_description="the word 'nevertheless'")
    ]
    questions = (
        session.query(ReadingQuestion).filter_by(exercise_id=exercise.id).all()
    )
    assert len(questions) == 1
    session.close()
