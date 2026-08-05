from datetime import date

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.ai import get_ai_provider
from app.ai.schemas import (
    ChatResult,
    GeneratedQuestion,
    ListeningScriptGenerationResult,
    ReadingExerciseGenerationResult,
)
from app.ai.testing import FakeAIProvider
from app.core.db import get_db
from app.core.security import SESSION_COOKIE_NAME, create_session_token
from app.models import speaking_question  # noqa: F401 registers the FK target table
from app.routers.daily_lesson_plan import router as daily_lesson_router
from app.services.text_to_speech import (
    FakeTextToSpeech,
    SynthesisResult,
    get_text_to_speech,
)


def _success_provider() -> FakeAIProvider:
    return FakeAIProvider(
        reading_exercise_result=ReadingExerciseGenerationResult(
            status="ok", passage_text="A passage.",
            questions=[GeneratedQuestion(
                question_text="Q?", options=["A", "B", "C", "D"], correct_option_index=0
            )],
        ),
        listening_script_result=ListeningScriptGenerationResult(
            status="ok", script_text="A script.",
            questions=[GeneratedQuestion(
                question_text="Q?", options=["A", "B", "C", "D"], correct_option_index=0
            )],
        ),
        chat_result=ChatResult(status="ok", message="A generated prompt."),
    )


def _success_tts() -> FakeTextToSpeech:
    return FakeTextToSpeech(
        SynthesisResult(status="ok", audio_bytes=b"audio", content_type="audio/mpeg")
    )


def _client(db_session_factory, *, authenticated=True):
    app = FastAPI()
    app.include_router(daily_lesson_router)

    def override_get_db():
        with db_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_ai_provider] = _success_provider
    app.dependency_overrides[get_text_to_speech] = _success_tts
    client = TestClient(app, base_url="https://testserver")
    if authenticated:
        client.cookies.set(SESSION_COOKIE_NAME, create_session_token())
    return client


def test_daily_lesson_route_rejects_unauthenticated_requests(db_session_factory):
    client = _client(db_session_factory, authenticated=False)

    assert client.get("/api/daily-lesson/overview").status_code == 401


def test_overview_returns_all_three_daily_skills_and_session_context(db_session_factory):
    client = _client(db_session_factory)

    response = client.get("/api/daily-lesson/overview")

    assert response.status_code == 200
    body = response.json()
    today = date.today().isoformat()
    todays_entries = [entry for entry in body["skills"] if entry["day"] == today]
    assert {entry["skill"] for entry in todays_entries} == {
        "reading", "listening", "writing",
    }
    assert body["exam_type"] == "ielts_academic"
    assert body["total_minutes"] == 60
    assert body["review_minutes"] == 10
    assert sum(entry["estimated_minutes"] for entry in todays_entries) == 40
    assert sum(1 for e in todays_entries if e["priority"] == "primary") == 1
    assert all(entry["status"] == "ready" for entry in todays_entries)
    assert body["effective_day"] == today
    assert body["checkpoint"]["all_passed"] is False
    assert body["checkpoint"]["passed_count"] == 0
    assert body["checkpoint"]["required_count"] == 4


def test_overview_is_idempotent_across_requests(db_session_factory):
    client = _client(db_session_factory)

    first = client.get("/api/daily-lesson/overview").json()
    second = client.get("/api/daily-lesson/overview").json()

    assert first == second


def _failing_provider() -> FakeAIProvider:
    return FakeAIProvider(
        reading_exercise_result=ReadingExerciseGenerationResult(
            status="error", error_message="x"
        ),
        listening_script_result=ListeningScriptGenerationResult(
            status="error", error_message="x"
        ),
        chat_result=ChatResult(status="error", error_message="x"),
    )


def test_retry_endpoint_recovers_a_failed_skill(db_session_factory):
    today = date.today().isoformat()
    # All 3 daily skills are always allocated now, so any of them is a valid retry target.
    skill_to_retry = "reading"

    failing_app = FastAPI()
    failing_app.include_router(daily_lesson_router)

    def override_get_db():
        with db_session_factory() as session:
            yield session

    failing_app.dependency_overrides[get_db] = override_get_db
    failing_app.dependency_overrides[get_ai_provider] = _failing_provider
    failing_app.dependency_overrides[get_text_to_speech] = _success_tts
    failing_client = TestClient(failing_app, base_url="https://testserver")
    failing_client.cookies.set(SESSION_COOKIE_NAME, create_session_token())

    first = failing_client.get("/api/daily-lesson/overview").json()
    failed_entry = next(
        e for e in first["skills"] if e["skill"] == skill_to_retry and e["day"] == today
    )
    assert failed_entry["status"] == "failed"

    retry_client = _client(db_session_factory)
    response = retry_client.post(f"/api/daily-lesson/{skill_to_retry}/retry?day={today}")

    assert response.status_code == 200
    assert response.json()["status"] == "ready"
