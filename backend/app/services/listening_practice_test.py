from datetime import date

from app.ai.schemas import (
    GeneratedQuestion,
    GeneratedSection,
    ListeningScriptGenerationRequest,
    ListeningScriptGenerationResult,
)
from app.ai.testing import FakeAIProvider
from app.models.listening_practice import ListeningExercise, ListeningSection
from app.services.listening_practice import (
    get_or_create_exercise,
    get_questions,
    get_sections,
    retry_audio,
    retry_script,
    score_submission,
)
from app.services.text_to_speech import FakeTextToSpeech, SynthesisResult


def _success_script_result() -> ListeningScriptGenerationResult:
    return ListeningScriptGenerationResult(
        status="ok",
        sections=[
            GeneratedSection(
                script_text="A script about nevertheless.",
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


def _success_audio_result() -> SynthesisResult:
    return SynthesisResult(
        status="ok", audio_bytes=b"fake-audio", content_type="audio/mpeg"
    )


def test_first_call_generates_script_audio_and_persists_questions_reaching_ready(
    db_session_factory,
):
    session = db_session_factory()
    provider = FakeAIProvider(listening_script_result=_success_script_result())
    tts = FakeTextToSpeech(_success_audio_result())

    exercise = get_or_create_exercise(
        session, date(2026, 7, 30), "the word 'nevertheless'", provider, tts
    )

    assert exercise.status == "ready"
    sections = get_sections(session, exercise.id)
    assert len(sections) == 1
    assert sections[0].script_text == "A script about nevertheless."
    assert sections[0].audio_bytes == b"fake-audio"
    assert sections[0].audio_content_type == "audio/mpeg"
    assert provider.listening_script_requests == [
        ListeningScriptGenerationRequest(
            focus_description="the word 'nevertheless'", tier="beginner",
        )
    ]
    assert tts.calls == ["A script about nevertheless."]
    questions = get_questions(session, exercise.id)
    assert len(questions) == 1
    session.close()


def test_second_call_same_day_returns_identical_row_without_regenerating(
    db_session_factory,
):
    session = db_session_factory()
    provider = FakeAIProvider(listening_script_result=_success_script_result())
    tts = FakeTextToSpeech(_success_audio_result())

    first = get_or_create_exercise(
        session, date(2026, 7, 30), "the word 'nevertheless'", provider, tts
    )
    second = get_or_create_exercise(
        session, date(2026, 7, 30), "the word 'nevertheless'", provider, tts
    )

    assert first.id == second.id
    assert len(provider.listening_script_requests) == 1
    assert len(tts.calls) == 1
    session.close()


def test_script_generation_failure_persists_script_failed_status(db_session_factory):
    session = db_session_factory()
    provider = FakeAIProvider(
        listening_script_result=ListeningScriptGenerationResult(
            status="error", error_message="provider timeout"
        )
    )
    tts = FakeTextToSpeech(_success_audio_result())

    exercise = get_or_create_exercise(
        session, date(2026, 7, 30), "the word 'nevertheless'", provider, tts
    )

    assert exercise.status == "script_failed"
    assert len(tts.calls) == 0
    reloaded = session.query(ListeningExercise).filter_by(day=date(2026, 7, 30)).one()
    assert reloaded.status == "script_failed"
    session.close()


def test_audio_generation_failure_persists_audio_failed_status_but_keeps_script(
    db_session_factory,
):
    session = db_session_factory()
    provider = FakeAIProvider(listening_script_result=_success_script_result())
    tts = FakeTextToSpeech(
        SynthesisResult(status="error", error_message="tts down")
    )

    exercise = get_or_create_exercise(
        session, date(2026, 7, 30), "the word 'nevertheless'", provider, tts
    )

    assert exercise.status == "audio_failed"
    sections = get_sections(session, exercise.id)
    assert sections[0].script_text == "A script about nevertheless."
    assert sections[0].audio_bytes is None
    session.close()


def test_retry_audio_after_audio_failure_does_not_regenerate_the_script(
    db_session_factory,
):
    session = db_session_factory()
    provider = FakeAIProvider(listening_script_result=_success_script_result())
    failing_tts = FakeTextToSpeech(
        SynthesisResult(status="error", error_message="tts down")
    )
    exercise = get_or_create_exercise(
        session, date(2026, 7, 30), "the word 'nevertheless'", provider, failing_tts
    )
    assert exercise.status == "audio_failed"

    succeeding_tts = FakeTextToSpeech(_success_audio_result())
    retried = retry_audio(session, date(2026, 7, 30), succeeding_tts)

    assert retried.status == "ready"
    sections = get_sections(session, retried.id)
    assert sections[0].audio_bytes == b"fake-audio"
    # Script generation must not be re-invoked on an audio-only retry.
    assert len(provider.listening_script_requests) == 1
    session.close()


def test_retry_script_after_script_failure_reuses_the_original_focus(
    db_session_factory,
):
    session = db_session_factory()
    failing_provider = FakeAIProvider(
        listening_script_result=ListeningScriptGenerationResult(
            status="error", error_message="provider timeout"
        )
    )
    tts = FakeTextToSpeech(_success_audio_result())
    exercise = get_or_create_exercise(
        session, date(2026, 7, 30), "the word 'nevertheless'", failing_provider, tts
    )
    assert exercise.status == "script_failed"

    succeeding_provider = FakeAIProvider(listening_script_result=_success_script_result())
    retried = retry_script(session, date(2026, 7, 30), succeeding_provider)

    assert retried.status == "script_generated"
    assert succeeding_provider.listening_script_requests == [
        ListeningScriptGenerationRequest(
            focus_description="the word 'nevertheless'", tier="beginner",
        )
    ]
    session.close()


def test_standard_tier_requests_and_persists_two_sections(db_session_factory):
    session = db_session_factory()
    provider = FakeAIProvider(
        listening_script_result=ListeningScriptGenerationResult(
            status="ok",
            sections=[
                GeneratedSection(
                    context_type="monologue",
                    script_text="Section 1 script.",
                    questions=[
                        GeneratedQuestion(
                            question_text="Q1?", options=["A", "B"], correct_option_index=0,
                        )
                    ],
                ),
                GeneratedSection(
                    context_type="social_conversation",
                    script_text="Section 2 script.",
                    questions=[
                        GeneratedQuestion(
                            question_text="Speaker",
                            question_type="matching",
                            options=["Option 1", "Option 2"],
                            correct_option_index=1,
                            group_instructions="Match each speaker to an option.",
                        )
                    ],
                ),
            ],
        )
    )
    tts = FakeTextToSpeech(_success_audio_result())

    exercise = get_or_create_exercise(
        session, date(2026, 7, 30), "focus", provider, tts, tier="standard",
    )

    assert provider.listening_script_requests == [
        ListeningScriptGenerationRequest(focus_description="focus", tier="standard")
    ]
    sections = get_sections(session, exercise.id)
    assert [s.script_text for s in sections] == ["Section 1 script.", "Section 2 script."]
    assert [s.context_type for s in sections] == ["monologue", "social_conversation"]
    # Audio is synthesized once per section.
    assert tts.calls == ["Section 1 script.", "Section 2 script."]
    questions = get_questions(session, exercise.id)
    assert [q.question_type for q in questions] == ["multiple_choice", "matching"]
    session.close()


def _three_question_result() -> ListeningScriptGenerationResult:
    return ListeningScriptGenerationResult(
        status="ok",
        sections=[
            GeneratedSection(
                script_text="A script with three questions.",
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
    provider = FakeAIProvider(listening_script_result=_three_question_result())
    tts = FakeTextToSpeech(_success_audio_result())
    exercise = get_or_create_exercise(
        session, date(2026, 7, 30), "focus", provider, tts
    )

    submission = score_submission(session, exercise, [0, 0, 2])

    assert submission.score == 2
    assert submission.answers == [0, 0, 2]
    assert len(provider.listening_script_requests) == 1
    session.close()


def test_score_submission_is_idempotent_when_already_submitted(db_session_factory):
    session = db_session_factory()
    provider = FakeAIProvider(listening_script_result=_three_question_result())
    tts = FakeTextToSpeech(_success_audio_result())
    exercise = get_or_create_exercise(
        session, date(2026, 7, 30), "focus", provider, tts
    )

    first = score_submission(session, exercise, [0, 0, 2])
    second = score_submission(session, exercise, [1, 1, 1])

    assert second.id == first.id
    assert second.score == 2
    assert second.answers == [0, 0, 2]
    session.close()


def _mixed_type_result() -> ListeningScriptGenerationResult:
    return ListeningScriptGenerationResult(
        status="ok",
        sections=[
            GeneratedSection(
                script_text="A script with mixed question types.",
                questions=[
                    GeneratedQuestion(
                        question_text="What is discussed?",
                        question_type="multiple_choice",
                        options=["A", "B", "C", "D"],
                        correct_option_index=1,
                    ),
                    GeneratedQuestion(
                        question_text="Complete the note: the team missed the ___ deadline.",
                        question_type="note_completion",
                        accepted_answers=["funding", "budget"],
                    ),
                ],
            )
        ],
    )


def test_score_submission_grades_note_completion_as_text_based(db_session_factory):
    session = db_session_factory()
    provider = FakeAIProvider(listening_script_result=_mixed_type_result())
    tts = FakeTextToSpeech(_success_audio_result())
    exercise = get_or_create_exercise(session, date(2026, 7, 30), "focus", provider, tts)

    submission = score_submission(session, exercise, [1, "  Funding  "])

    assert submission.score == 2
    questions = get_questions(session, exercise.id)
    assert questions[1].question_type == "note_completion"
    assert questions[1].accepted_answers == ["funding", "budget"]
    session.close()


def test_retry_script_replaces_sections_not_just_appends(db_session_factory):
    session = db_session_factory()
    provider = FakeAIProvider(listening_script_result=_success_script_result())
    tts = FakeTextToSpeech(_success_audio_result())
    exercise = get_or_create_exercise(session, date(2026, 7, 30), "focus", provider, tts)
    assert len(get_sections(session, exercise.id)) == 1

    retried_provider = FakeAIProvider(
        listening_script_result=ListeningScriptGenerationResult(
            status="ok",
            sections=[
                GeneratedSection(
                    script_text="A brand new script.",
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
    retry_script(session, date(2026, 7, 30), retried_provider)

    sections = get_sections(session, exercise.id)
    assert len(sections) == 1
    assert sections[0].script_text == "A brand new script."
    assert (
        session.query(ListeningSection).filter_by(exercise_id=exercise.id).count() == 1
    )
    session.close()
