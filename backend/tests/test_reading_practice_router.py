from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.ai import get_ai_provider
from app.ai.schemas import (
    GeneratedQuestion,
    ReadingExerciseGenerationRequest,
    ReadingExerciseGenerationResult,
)
from app.ai.testing import FakeAIProvider
from app.core.db import get_db
from app.core.security import SESSION_COOKIE_NAME, create_session_token
from app.routers.reading_practice import router as reading_router


def _success_provider() -> FakeAIProvider:
    return FakeAIProvider(
        reading_exercise_result=ReadingExerciseGenerationResult(
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
    )


def _client(db_session_factory, *, authenticated=True, provider=None):
    app = FastAPI()
    app.include_router(reading_router)

    def override_get_db():
        with db_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_ai_provider] = provider or _success_provider
    client = TestClient(app, base_url="https://testserver")
    if authenticated:
        client.cookies.set(SESSION_COOKIE_NAME, create_session_token())
    return client


def test_reading_practice_route_rejects_unauthenticated_requests(db_session_factory):
    client = _client(db_session_factory, authenticated=False)

    assert client.get("/api/reading-practice/2026-07-30").status_code == 401


def test_get_exercise_generates_on_first_request_and_omits_correct_answers(
    db_session_factory,
):
    client = _client(db_session_factory)

    response = client.get("/api/reading-practice/2026-07-30")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["passage_text"] == "A passage about nevertheless."
    assert len(body["questions"]) == 1
    assert "correct_option_index" not in body["questions"][0]
    assert "accepted_answers" not in body["questions"][0]
    assert body["questions"][0]["question_type"] == "multiple_choice"
    assert "options" in body["questions"][0]


def test_get_exercise_second_request_returns_the_same_content(db_session_factory):
    client = _client(db_session_factory)

    first = client.get("/api/reading-practice/2026-07-30").json()
    second = client.get("/api/reading-practice/2026-07-30").json()

    assert first == second


def test_submit_scores_immediately_and_returns_quick_add_ready_data(db_session_factory):
    client = _client(db_session_factory)
    client.get("/api/reading-practice/2026-07-30")

    response = client.post(
        "/api/reading-practice/2026-07-30/submit", json={"answers": [0]}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["score"] == 0
    assert body["total"] == 1
    answer = body["answers"][0]
    assert answer["correct"] is False
    assert answer["learner_answer"] == 0
    assert answer["correct_answer"] == 1
    assert answer["question_type"] == "multiple_choice"
    assert answer["question_text"] == "What is discussed?"
    assert answer["options"] == ["A", "B", "C", "D"]


def test_submitting_twice_returns_the_original_result_instead_of_500(db_session_factory):
    client = _client(db_session_factory)
    client.get("/api/reading-practice/2026-07-30")

    first = client.post(
        "/api/reading-practice/2026-07-30/submit", json={"answers": [1]}
    )
    second = client.post(
        "/api/reading-practice/2026-07-30/submit", json={"answers": [0]}
    )

    assert second.status_code == 200
    assert second.json() == first.json()


def _failing_provider() -> FakeAIProvider:
    return FakeAIProvider(
        reading_exercise_result=ReadingExerciseGenerationResult(
            status="error", error_message="provider timeout"
        )
    )


def test_retry_endpoint_replaces_failed_content_after_generation_succeeds(
    db_session_factory,
):
    failing_client = _client(db_session_factory, provider=_failing_provider)
    first = failing_client.get("/api/reading-practice/2026-07-30").json()
    assert first["status"] == "failed"

    retry_client = _client(db_session_factory, provider=_success_provider)
    response = retry_client.post("/api/reading-practice/2026-07-30/retry")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ready"
    assert body["passage_text"] == "A passage about nevertheless."
