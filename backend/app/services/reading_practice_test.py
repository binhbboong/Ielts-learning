from datetime import date

from app.ai.local_provider import LocalAIProvider
from app.ai.schemas import (
    GeneratedPassage,
    GeneratedQuestion,
    ReadingExerciseGenerationRequest,
    ReadingExerciseGenerationResult,
)

from app.ai.testing import FakeAIProvider
from app.models.reading_practice import ReadingExercise, ReadingPassage, ReadingQuestion
from app.services.reading_practice import (
    get_or_create_exercise,
    get_passages,
    get_questions,
    retry_exercise,
    score_submission,
)


def _success_result() -> ReadingExerciseGenerationResult:
    return ReadingExerciseGenerationResult(
        status="ok",
        passages=[
            GeneratedPassage(
                passage_text="A passage about nevertheless.",
                questions=[
                    GeneratedQuestion(
                        question_text="What is discussed?",
                        options=["A", "B", "C", "D"],
                        correct_option_index=1,
                    )
                ],
            )
        ],
    )


def test_first_call_generates_and_persists_exercise_with_passage_and_questions(
    db_session_factory,
):
    session = db_session_factory()
    provider = FakeAIProvider(reading_exercise_result=_success_result())

    exercise = get_or_create_exercise(
        session, date(2026, 7, 30), "the word 'nevertheless'", provider
    )

    assert exercise.status == "ready"
    passages = get_passages(session, exercise.id)
    assert len(passages) == 1
    assert passages[0].passage_text == "A passage about nevertheless."
    assert provider.reading_exercise_requests == [
        ReadingExerciseGenerationRequest(
            focus_description="the word 'nevertheless'", tier="beginner",
        )
    ]
    questions = get_questions(session, exercise.id)
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


def test_standard_tier_requests_and_persists_two_passages(db_session_factory):
    session = db_session_factory()
    provider = FakeAIProvider(
        reading_exercise_result=ReadingExerciseGenerationResult(
            status="ok",
            passages=[
                GeneratedPassage(
                    passage_text="Passage 1.",
                    questions=[
                        GeneratedQuestion(
                            question_text="Q1?", options=["A", "B"], correct_option_index=0,
                        )
                    ],
                ),
                GeneratedPassage(
                    title="Passage 2 title",
                    passage_text="Passage 2.",
                    questions=[
                        GeneratedQuestion(
                            question_text="Paragraph A",
                            question_type="matching_headings",
                            options=["Heading 1", "Heading 2"],
                            correct_option_index=0,
                            group_instructions="Match each paragraph to a heading.",
                        )
                    ],
                ),
            ],
        )
    )

    exercise = get_or_create_exercise(
        session, date(2026, 7, 30), "focus", provider, tier="standard",
    )

    assert provider.reading_exercise_requests == [
        ReadingExerciseGenerationRequest(focus_description="focus", tier="standard")
    ]
    passages = get_passages(session, exercise.id)
    assert [p.passage_text for p in passages] == ["Passage 1.", "Passage 2."]
    assert passages[1].title == "Passage 2 title"
    questions = get_questions(session, exercise.id)
    assert [q.question_type for q in questions] == ["multiple_choice", "matching_headings"]
    assert questions[1].group_instructions == "Match each paragraph to a heading."
    session.close()


def test_advanced_tier_requests_and_persists_three_passages(db_session_factory):
    session = db_session_factory()
    provider = LocalAIProvider()

    exercise = get_or_create_exercise(
        session, date(2026, 7, 30), "focus", provider, tier="advanced",
    )

    passages = get_passages(session, exercise.id)
    assert len(passages) == 3
    questions = get_questions(session, exercise.id)
    assert len(questions) == 2 + 2 + 5
    session.close()


def _three_question_result() -> ReadingExerciseGenerationResult:
    return ReadingExerciseGenerationResult(
        status="ok",
        passages=[
            GeneratedPassage(
                passage_text="A passage with three questions.",
                questions=[
                    GeneratedQuestion(
                        question_text="Q1?", options=["A", "B", "C", "D"],
                        correct_option_index=0,
                    ),
                    GeneratedQuestion(
                        question_text="Q2?", options=["A", "B", "C", "D"],
                        correct_option_index=1,
                    ),
                    GeneratedQuestion(
                        question_text="Q3?", options=["A", "B", "C", "D"],
                        correct_option_index=2,
                    ),
                ],
            )
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


def test_score_submission_is_idempotent_when_already_submitted(db_session_factory):
    session = db_session_factory()
    generation_provider = FakeAIProvider(reading_exercise_result=_three_question_result())
    exercise = get_or_create_exercise(
        session, date(2026, 7, 30), "focus", generation_provider
    )

    first = score_submission(session, exercise, [0, 0, 2])
    second = score_submission(session, exercise, [1, 1, 1])

    assert second.id == first.id
    assert second.score == 2
    assert second.answers == [0, 0, 2]
    session.close()


def _mixed_type_result() -> ReadingExerciseGenerationResult:
    return ReadingExerciseGenerationResult(
        status="ok",
        passages=[
            GeneratedPassage(
                passage_text="A passage with mixed question types.",
                questions=[
                    GeneratedQuestion(
                        question_text="What is discussed?",
                        question_type="multiple_choice",
                        options=["A", "B", "C", "D"],
                        correct_option_index=1,
                    ),
                    GeneratedQuestion(
                        question_text="The delay was caused by funding shortfalls.",
                        question_type="true_false_not_given",
                        options=["True", "False", "Not Given"],
                        correct_option_index=0,
                    ),
                ],
            )
        ],
    )


def test_score_submission_grades_true_false_not_given_as_option_based(
    db_session_factory,
):
    session = db_session_factory()
    provider = FakeAIProvider(reading_exercise_result=_mixed_type_result())
    exercise = get_or_create_exercise(session, date(2026, 7, 30), "focus", provider)

    submission = score_submission(session, exercise, [1, 0])

    assert submission.score == 2
    questions = get_questions(session, exercise.id)
    assert questions[1].question_type == "true_false_not_given"
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
        ReadingExerciseGenerationRequest(
            focus_description="the word 'nevertheless'", tier="beginner",
        )
    ]
    questions = get_questions(session, exercise.id)
    assert len(questions) == 1
    session.close()


def test_retry_replaces_passages_not_just_appends(db_session_factory):
    session = db_session_factory()
    provider = FakeAIProvider(reading_exercise_result=_success_result())
    exercise = get_or_create_exercise(session, date(2026, 7, 30), "focus", provider)
    assert len(get_passages(session, exercise.id)) == 1

    retried_provider = FakeAIProvider(
        reading_exercise_result=ReadingExerciseGenerationResult(
            status="ok",
            passages=[
                GeneratedPassage(
                    passage_text="A brand new passage.",
                    questions=[
                        GeneratedQuestion(
                            question_text="New Q?", options=["A", "B"],
                            correct_option_index=0,
                        )
                    ],
                )
            ],
        )
    )
    retry_exercise(session, date(2026, 7, 30), retried_provider)

    passages = get_passages(session, exercise.id)
    assert len(passages) == 1
    assert passages[0].passage_text == "A brand new passage."
    assert (
        session.query(ReadingPassage).filter_by(exercise_id=exercise.id).count() == 1
    )
    session.close()
