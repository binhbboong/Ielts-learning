import json

from app.ai.openai_provider import OpenAIProvider
from app.ai.schemas import (
    ChatRequest,
    ListeningScriptGenerationRequest,
    ReadingExerciseGenerationRequest,
)


class _FakeResponse:
    def __init__(self, output_text: str):
        self.output_text = output_text


class _FakeResponses:
    def __init__(self, response_text: str = "", error: Exception | None = None):
        self._response_text = response_text
        self._error = error

    def create(self, **kwargs):
        if self._error:
            raise self._error
        return _FakeResponse(self._response_text)


class _FakeOpenAIClient:
    def __init__(self, response_text: str = "", error: Exception | None = None):
        self.responses = _FakeResponses(response_text, error)


def test_openai_provider_generates_reading_exercise_from_model_response():
    payload = {
        "passage_text": "A passage about nevertheless.",
        "questions": [
            {
                "question_text": "What does the passage discuss?",
                "options": ["A", "B", "C", "D"],
                "correct_option_index": 1,
            }
        ],
    }
    provider = OpenAIProvider(client=_FakeOpenAIClient(json.dumps(payload)))

    result = provider.generate_reading_exercise(
        ReadingExerciseGenerationRequest(focus_description="the word 'nevertheless'")
    )

    assert result.status == "ok"
    assert result.passage_text == "A passage about nevertheless."


def test_openai_provider_returns_error_result_on_client_failure():
    provider = OpenAIProvider(client=_FakeOpenAIClient(error=RuntimeError("network down")))

    result = provider.generate_reading_exercise(
        ReadingExerciseGenerationRequest(focus_description="the word 'nevertheless'")
    )

    assert result.status == "error"
    assert result.error_message is not None


def test_openai_provider_generates_listening_script_from_model_response():
    payload = {
        "script_text": "A script about nevertheless.",
        "questions": [
            {
                "question_text": "What does the script discuss?",
                "options": ["A", "B", "C", "D"],
                "correct_option_index": 2,
            }
        ],
    }
    provider = OpenAIProvider(client=_FakeOpenAIClient(json.dumps(payload)))

    result = provider.generate_listening_script(
        ListeningScriptGenerationRequest(focus_description="the word 'nevertheless'")
    )

    assert result.status == "ok"
    assert result.script_text == "A script about nevertheless."


def test_openai_provider_generates_chat_response():
    provider = OpenAIProvider(client=_FakeOpenAIClient("An IELTS practice prompt"))

    result = provider.chat(ChatRequest(message="Generate a prompt"))

    assert result.status == "ok"
    assert result.message == "An IELTS practice prompt"
