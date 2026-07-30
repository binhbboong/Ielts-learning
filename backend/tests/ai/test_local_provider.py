from app.ai.local_provider import LocalAIProvider
from app.ai.schemas import (
    ListeningScriptGenerationRequest,
    ReadingExerciseGenerationRequest,
)


def test_local_provider_generates_a_reading_exercise_referencing_the_focus():
    provider = LocalAIProvider()
    request = ReadingExerciseGenerationRequest(focus_description="the word 'nevertheless'")

    result = provider.generate_reading_exercise(request)

    assert result.status == "ok"
    assert "nevertheless" in result.passage_text
    assert len(result.questions) >= 1
    for question in result.questions:
        assert 0 <= question.correct_option_index < len(question.options)


def test_local_provider_generates_a_listening_script_referencing_the_focus():
    provider = LocalAIProvider()
    request = ListeningScriptGenerationRequest(focus_description="the word 'nevertheless'")

    result = provider.generate_listening_script(request)

    assert result.status == "ok"
    assert "nevertheless" in result.script_text
    assert len(result.questions) >= 1
    for question in result.questions:
        assert 0 <= question.correct_option_index < len(question.options)
