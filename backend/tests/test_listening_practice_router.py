from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.ai import get_ai_provider
from app.ai.schemas import GeneratedQuestion, ListeningScriptGenerationResult
from app.ai.testing import FakeAIProvider
from app.core.db import get_db
from app.core.security import SESSION_COOKIE_NAME, create_session_token
from app.routers.listening_practice import router as listening_router
from app.services.text_to_speech import (
    FakeTextToSpeech,
    SynthesisResult,
    get_text_to_speech,
)


def _success_provider() -> FakeAIProvider:
    return FakeAIProvider(
        listening_script_result=ListeningScriptGenerationResult(
            status="ok",
            script_text="A script about nevertheless.",
            questions=[
                GeneratedQuestion(
                    question_text="What is discussed?",
                    options=["A", "B", "C", "D"],
                    correct_option_index=1,
                )
            ],
        )
    )


def _success_tts() -> FakeTextToSpeech:
    return FakeTextToSpeech(
        SynthesisResult(status="ok", audio_bytes=b"fake-audio", content_type="audio/mpeg")
    )


def _client(db_session_factory, *, authenticated=True, provider=None, tts=None):
    app = FastAPI()
    app.include_router(listening_router)

    def override_get_db():
        with db_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_ai_provider] = provider or _success_provider
    app.dependency_overrides[get_text_to_speech] = tts or _success_tts
    client = TestClient(app, base_url="https://testserver")
    if authenticated:
        client.cookies.set(SESSION_COOKIE_NAME, create_session_token())
    return client


def test_listening_practice_route_rejects_unauthenticated_requests(db_session_factory):
    client = _client(db_session_factory, authenticated=False)

    assert client.get("/api/listening-practice/2026-07-30").status_code == 401


def test_get_exercise_generates_on_first_request_and_withholds_transcript(
    db_session_factory,
):
    client = _client(db_session_factory)

    response = client.get("/api/listening-practice/2026-07-30")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["script_text"] is None
    assert len(body["questions"]) == 1
    assert "correct_option_index" not in body["questions"][0]


def test_get_audio_serves_the_stored_bytes_with_content_type(db_session_factory):
    client = _client(db_session_factory)
    client.get("/api/listening-practice/2026-07-30")

    response = client.get("/api/listening-practice/2026-07-30/audio")

    assert response.status_code == 200
    assert response.content == b"fake-audio"
    assert response.headers["content-type"] == "audio/mpeg"


def test_submit_scores_immediately_and_reveals_transcript(db_session_factory):
    client = _client(db_session_factory)
    client.get("/api/listening-practice/2026-07-30")

    response = client.post(
        "/api/listening-practice/2026-07-30/submit", json={"answers": [0]}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["score"] == 0
    assert body["total"] == 1
    assert body["script_text"] == "A script about nevertheless."
    answer = body["answers"][0]
    assert answer["correct"] is False
    assert answer["learner_answer"] == 0
    assert answer["correct_answer"] == 1


def test_submitting_twice_returns_the_original_result_instead_of_500(db_session_factory):
    client = _client(db_session_factory)
    client.get("/api/listening-practice/2026-07-30")

    first = client.post(
        "/api/listening-practice/2026-07-30/submit", json={"answers": [1]}
    )
    second = client.post(
        "/api/listening-practice/2026-07-30/submit", json={"answers": [0]}
    )

    assert second.status_code == 200
    assert second.json() == first.json()


def test_get_after_submission_reveals_the_transcript(db_session_factory):
    client = _client(db_session_factory)
    client.get("/api/listening-practice/2026-07-30")
    client.post("/api/listening-practice/2026-07-30/submit", json={"answers": [1]})

    response = client.get("/api/listening-practice/2026-07-30")

    assert response.json()["script_text"] == "A script about nevertheless."


def _failing_provider() -> FakeAIProvider:
    return FakeAIProvider(
        listening_script_result=ListeningScriptGenerationResult(
            status="error", error_message="provider timeout"
        )
    )


def _failing_tts() -> FakeTextToSpeech:
    return FakeTextToSpeech(SynthesisResult(status="error", error_message="tts down"))


def test_retry_script_endpoint_recovers_from_script_failure(db_session_factory):
    failing_client = _client(db_session_factory, provider=_failing_provider)
    first = failing_client.get("/api/listening-practice/2026-07-30").json()
    assert first["status"] == "script_failed"

    retry_client = _client(db_session_factory, provider=_success_provider)
    response = retry_client.post("/api/listening-practice/2026-07-30/retry-script")

    assert response.status_code == 200
    assert response.json()["status"] == "script_generated"


def test_retry_audio_endpoint_recovers_from_audio_failure(db_session_factory):
    failing_client = _client(db_session_factory, tts=_failing_tts)
    first = failing_client.get("/api/listening-practice/2026-07-30").json()
    assert first["status"] == "audio_failed"

    retry_client = _client(db_session_factory, tts=_success_tts)
    response = retry_client.post("/api/listening-practice/2026-07-30/retry-audio")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
