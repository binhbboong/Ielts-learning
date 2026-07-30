import json

from app.ai.claude_provider import ClaudeProvider
from app.ai.schemas import (
    ListeningScriptGenerationRequest,
    ReadingExerciseGenerationRequest,
)


class _FakeTextBlock:
    def __init__(self, text: str):
        self.text = text


class _FakeMessage:
    def __init__(self, text: str):
        self.content = [_FakeTextBlock(text)]


class _FakeMessages:
    def __init__(self, response_text: str, error: Exception | None = None):
        self._response_text = response_text
        self._error = error

    def create(self, **kwargs):
        if self._error:
            raise self._error
        return _FakeMessage(self._response_text)


class _FakeAnthropicClient:
    def __init__(self, response_text: str = "", error: Exception | None = None):
        self.messages = _FakeMessages(response_text, error)


def test_claude_provider_generates_reading_exercise_from_model_response():
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
    client = _FakeAnthropicClient(response_text=json.dumps(payload))
    provider = ClaudeProvider(client=client)

    result = provider.generate_reading_exercise(
        ReadingExerciseGenerationRequest(focus_description="the word 'nevertheless'")
    )

    assert result.status == "ok"
    assert result.passage_text == "A passage about nevertheless."
    assert result.questions[0].correct_option_index == 1


def test_claude_provider_returns_error_result_on_client_failure():
    client = _FakeAnthropicClient(error=RuntimeError("network down"))
    provider = ClaudeProvider(client=client)

    result = provider.generate_reading_exercise(
        ReadingExerciseGenerationRequest(focus_description="the word 'nevertheless'")
    )

    assert result.status == "error"
    assert result.error_message is not None


def test_claude_provider_generates_listening_script_from_model_response():
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
    client = _FakeAnthropicClient(response_text=json.dumps(payload))
    provider = ClaudeProvider(client=client)

    result = provider.generate_listening_script(
        ListeningScriptGenerationRequest(focus_description="the word 'nevertheless'")
    )

    assert result.status == "ok"
    assert result.script_text == "A script about nevertheless."
    assert result.questions[0].correct_option_index == 2


def test_claude_provider_returns_error_result_on_listening_script_client_failure():
    client = _FakeAnthropicClient(error=RuntimeError("network down"))
    provider = ClaudeProvider(client=client)

    result = provider.generate_listening_script(
        ListeningScriptGenerationRequest(focus_description="the word 'nevertheless'")
    )

    assert result.status == "error"
    assert result.error_message is not None
