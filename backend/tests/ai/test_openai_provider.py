import json

from app.ai.openai_provider import OpenAIProvider
from app.ai.schemas import (
    ChatRequest,
    ListeningScriptGenerationRequest,
    ReadingExerciseGenerationRequest,
    WritingEvaluationRequest,
)


class _FakeResponse:
    def __init__(self, output_text: str):
        self.output_text = output_text


class _FakeResponses:
    def __init__(self, response_text: str = "", error: Exception | None = None):
        self._response_text = response_text
        self._error = error
        self.last_kwargs = None

    def create(self, **kwargs):
        self.last_kwargs = kwargs
        if self._error:
            raise self._error
        return _FakeResponse(self._response_text)


class _FakeOpenAIClient:
    def __init__(self, response_text: str = "", error: Exception | None = None):
        self.responses = _FakeResponses(response_text, error)


def test_openai_provider_generates_reading_exercise_from_model_response():
    payload = {
        "passages": [
            {
                "title": None,
                "passage_text": "A passage about nevertheless.",
                "questions": [
                    {
                        "question_text": "What does the passage discuss?",
                        "options": ["A", "B", "C", "D"],
                        "correct_option_index": 1,
                    }
                ],
            }
        ],
    }
    provider = OpenAIProvider(client=_FakeOpenAIClient(json.dumps(payload)))

    result = provider.generate_reading_exercise(
        ReadingExerciseGenerationRequest(focus_description="the word 'nevertheless'")
    )

    assert result.status == "ok"
    assert result.passages[0].passage_text == "A passage about nevertheless."


def test_openai_provider_returns_error_result_on_client_failure():
    provider = OpenAIProvider(client=_FakeOpenAIClient(error=RuntimeError("network down")))

    result = provider.generate_reading_exercise(
        ReadingExerciseGenerationRequest(focus_description="the word 'nevertheless'")
    )

    assert result.status == "error"
    assert result.error_message is not None


def test_openai_provider_generates_listening_script_from_model_response():
    payload = {
        "sections": [
            {
                "context_type": "monologue",
                "script_text": "A script about nevertheless.",
                "questions": [
                    {
                        "question_text": "What does the script discuss?",
                        "options": ["A", "B", "C", "D"],
                        "correct_option_index": 2,
                    }
                ],
            }
        ],
    }
    provider = OpenAIProvider(client=_FakeOpenAIClient(json.dumps(payload)))

    result = provider.generate_listening_script(
        ListeningScriptGenerationRequest(focus_description="the word 'nevertheless'")
    )

    assert result.status == "ok"
    assert result.sections[0].script_text == "A script about nevertheless."


def test_openai_provider_generates_chat_response():
    provider = OpenAIProvider(client=_FakeOpenAIClient("An IELTS practice prompt"))

    result = provider.chat(ChatRequest(message="Generate a prompt"))

    assert result.status == "ok"
    assert result.message == "An IELTS practice prompt"


def test_openai_writing_evaluation_recovers_wrapped_overall_band():
    criterion = {
        "band_score": 4.5,
        "feedback": "Specific feedback about 'I go school'.",
        "strengths": "The meaning is clear.",
        "weaknesses": "A preposition is missing.",
    }
    payload = {
        "task_response": criterion,
        "coherence_and_cohesion": criterion,
        "lexical_resource": criterion,
        "grammatical_range_and_accuracy": criterion,
        "overall_band": {"band_score": 4.5, "feedback": "Accidentally wrapped."},
        "corrections": [{
            "original": "I go school.",
            "corrected": "I go to school.",
            "explanation": "Use the preposition 'to'.",
        }],
    }
    client = _FakeOpenAIClient(json.dumps(payload))
    provider = OpenAIProvider(client=client)

    result = provider.evaluate_writing(WritingEvaluationRequest(
        response_text="I go school.",
        task_type="task2",
        question_text="Write one sentence about your routine.",
        target_band=4.5,
        phase="foundation",
        exercise_type="sentence_building",
        practice_level=1,
    ))

    assert result.status == "ok"
    assert result.overall_band == 4.5
    assert result.task_response.strengths == ["The meaning is clear."]
    assert result.task_response.weaknesses == ["A preposition is missing."]
    prompt = client.responses.last_kwargs["input"]
    assert "overall_band MUST be one JSON number" in prompt
    assert "strengths and weaknesses MUST each be a JSON array" in prompt
