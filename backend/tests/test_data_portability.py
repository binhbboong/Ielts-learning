from datetime import date

from app.ai.schemas import (
    GeneratedPassage,
    GeneratedQuestion,
    GeneratedSection,
    ListeningScriptGenerationResult,
    ReadingExerciseGenerationResult,
)
from app.ai.testing import FakeAIProvider
from app.services.data_portability import (
    REQUIRED_CATEGORIES,
    assemble_export,
)
from app.services.reading_practice import get_or_create_exercise, score_submission
from app.services import listening_practice
from app.services.text_to_speech import FakeTextToSpeech, SynthesisResult


def test_full_export_contains_every_registered_category(db_session):
    document = assemble_export(db_session)
    assert set(document.categories) == set(REQUIRED_CATEGORIES)
    assert document.category_count == len(REQUIRED_CATEGORIES)
    assert set(document.data) == set(REQUIRED_CATEGORIES)
    assert document.export_format_version == 1


def test_export_includes_a_completed_reading_exercise_and_result(db_session):
    provider = FakeAIProvider(
        reading_exercise_result=ReadingExerciseGenerationResult(
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
    )
    exercise = get_or_create_exercise(
        db_session, date(2026, 7, 30), "the word 'nevertheless'", provider
    )
    score_submission(db_session, exercise, [1])

    document = assemble_export(db_session)

    reading_data = document.data["reading_practice"]
    assert (
        reading_data["passages"][0]["passage_text"] == "A passage about nevertheless."
    )
    assert reading_data["submissions"][0]["score"] == 1


def test_export_includes_the_actual_audio_bytes_for_a_completed_listening_exercise(
    db_session,
):
    provider = FakeAIProvider(
        listening_script_result=ListeningScriptGenerationResult(
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
    )
    tts = FakeTextToSpeech(
        SynthesisResult(status="ok", audio_bytes=b"raw-audio-bytes", content_type="audio/mpeg")
    )
    exercise = listening_practice.get_or_create_exercise(
        db_session, date(2026, 7, 30), "the word 'nevertheless'", provider, tts
    )
    listening_practice.score_submission(db_session, exercise, [1])

    document = assemble_export(db_session)

    listening_data = document.data["listening_practice"]
    import base64

    assert (
        base64.b64decode(listening_data["sections"][0]["audio_bytes"])
        == b"raw-audio-bytes"
    )
    assert listening_data["submissions"][0]["score"] == 1


def test_export_is_repeatable_and_current(db_session):
    first = assemble_export(db_session)
    second = assemble_export(db_session)
    assert first.export_id != second.export_id
    assert second.produced_at >= first.produced_at
