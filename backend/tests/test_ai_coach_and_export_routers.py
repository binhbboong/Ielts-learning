from pathlib import Path
import uuid

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.ai import get_ai_provider
from app.ai.schemas import (
    CriterionFeedback,
    SentenceCorrection,
    SpeakingEvaluationResult,
    WritingEvaluationResult,
)
from app.ai.testing import FakeAIProvider
from app.core.db import get_db
from app.core.security import SESSION_COOKIE_NAME, create_session_token
from app.data.speaking_questions_seed import seed_questions
from app.models.speaking_submission import SpeakingSubmission
from app.routers.data_portability import router as export_router
from app.routers.speaking_coach import router as speaking_router
from app.routers.writing_coach import router as writing_router
from app.services.speech_to_text import (
    FakeSpeechToText,
    TranscriptionResult,
    get_speech_to_text,
)


def _criterion() -> CriterionFeedback:
    return CriterionFeedback(
        band_score=7,
        feedback="Specific feedback tied to the submitted response.",
        strengths=["Clear central idea"],
        weaknesses=["Develop the example"],
    )


def _provider() -> FakeAIProvider:
    criterion = _criterion()
    return FakeAIProvider(
        writing_result=WritingEvaluationResult(
            status="ok",
            task_response=criterion,
            coherence_and_cohesion=criterion,
            lexical_resource=criterion,
            grammatical_range_and_accuracy=criterion,
            overall_band=7,
            corrections=[
                SentenceCorrection(
                    original="People is affected.",
                    corrected="People are affected.",
                    explanation="Plural agreement.",
                )
            ],
        ),
        speaking_result=SpeakingEvaluationResult(
            status="ok",
            fluency_and_coherence=criterion,
            lexical_resource=criterion,
            grammatical_range_and_accuracy=criterion,
        ),
    )


def _client(db_session_factory, *, authenticated=True):
    app = FastAPI()
    app.include_router(writing_router)
    app.include_router(speaking_router)
    app.include_router(export_router)

    def override_get_db():
        with db_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_ai_provider] = _provider
    app.dependency_overrides[get_speech_to_text] = lambda: FakeSpeechToText(
        TranscriptionResult(status="ok", transcript="A complete spoken answer.")
    )
    client = TestClient(app, base_url="https://testserver")
    if authenticated:
        client.cookies.set(SESSION_COOKIE_NAME, create_session_token())
    return client


def test_new_feature_routes_reject_unauthenticated_requests(db_session_factory):
    client = _client(db_session_factory, authenticated=False)
    assert client.get("/api/writing-coach/submissions").status_code == 401
    assert client.get("/api/speaking-coach/questions").status_code == 401
    assert client.post("/api/data-portability/export").status_code == 401


def test_writing_route_round_trips_complete_feedback(db_session_factory):
    client = _client(db_session_factory)
    response = client.post(
        "/api/writing-coach/submissions",
        json={
            "task_type": "task2",
            "question_text": "Discuss both views.",
            "response_text": "People is affected.",
        },
    )
    assert response.status_code == 200
    created = response.json()
    assert created["status"] == "complete"
    assert len(created["corrections"]) == 1
    assert client.get("/api/writing-coach/submissions").json()[0]["id"] == created["id"]
    detail = client.get(
        f"/api/writing-coach/submissions/{created['id']}"
    ).json()
    assert detail["grammatical_range_and_accuracy"]["band_score"] == 7


def test_writing_submissions_list_filters_by_day(db_session_factory):
    client = _client(db_session_factory)
    other_day = client.post(
        "/api/writing-coach/submissions",
        json={
            "task_type": "task2",
            "question_text": "Discuss both views.",
            "response_text": "People is affected.",
            "day": "2026-07-30",
        },
    ).json()
    same_day_first = client.post(
        "/api/writing-coach/submissions",
        json={
            "task_type": "task2",
            "question_text": "Discuss both views.",
            "response_text": "First attempt.",
            "day": "2026-07-31",
        },
    ).json()
    same_day_second = client.post(
        "/api/writing-coach/submissions",
        json={
            "task_type": "task2",
            "question_text": "Discuss both views.",
            "response_text": "Second attempt.",
            "day": "2026-07-31",
        },
    ).json()

    filtered = client.get(
        "/api/writing-coach/submissions", params={"day": "2026-07-31"}
    ).json()

    assert {item["id"] for item in filtered} == {
        same_day_first["id"],
        same_day_second["id"],
    }
    assert other_day["id"] not in {item["id"] for item in filtered}
    # Most recent attempt for the day comes first.
    assert filtered[0]["id"] == same_day_second["id"]


def test_speaking_route_runs_separate_steps_and_synthesizes_pronunciation(
    db_session_factory,
):
    with db_session_factory() as session:
        seed_questions(session)
    client = _client(db_session_factory)
    question = client.get("/api/speaking-coach/questions").json()[0]
    response = client.post(
        "/api/speaking-coach/submissions",
        data={"question_id": question["id"], "duration_seconds": "10"},
        files={"audio": ("response.webm", b"audio bytes", "audio/webm")},
    )
    assert response.status_code == 201
    created = response.json()
    assert created["status"] == "PROCESSING"
    transcribed = client.post(
        f"/api/speaking-coach/submissions/{created['id']}/transcribe"
    ).json()
    assert transcribed["status"] == "PROCESSING"
    assert transcribed["transcript"] == "A complete spoken answer."
    evaluated = client.post(
        f"/api/speaking-coach/submissions/{created['id']}/evaluate"
    ).json()
    assert evaluated["status"] == "COMPLETED"
    assert evaluated["pronunciation"] == "Not assessed"
    assert evaluated["fluency_and_coherence"]["band_score"] == 7

    with db_session_factory() as session:
        stored = session.get(SpeakingSubmission, uuid.UUID(created["id"]))
        audio_path = Path(stored.audio_storage_ref)
    if audio_path.is_file():
        audio_path.unlink()


def test_speaking_route_accepts_an_ai_generated_prompt_text_instead_of_a_question_id(
    db_session_factory,
):
    client = _client(db_session_factory)
    response = client.post(
        "/api/speaking-coach/submissions",
        data={
            "prompt_text": "Describe a memorable trip.",
            "day": "2026-07-30",
            "duration_seconds": "10",
        },
        files={"audio": ("response.webm", b"audio bytes", "audio/webm")},
    )
    assert response.status_code == 201
    created = response.json()
    assert created["question_id"] is None
    assert created["question"] == "Describe a memorable trip."

    with db_session_factory() as session:
        stored = session.get(SpeakingSubmission, uuid.UUID(created["id"]))
        audio_path = Path(stored.audio_storage_ref)
    if audio_path.is_file():
        audio_path.unlink()


def test_export_route_returns_complete_downloadable_document(db_session_factory):
    client = _client(db_session_factory)
    first = client.post("/api/data-portability/export")
    second = client.post("/api/data-portability/export")
    assert first.status_code == second.status_code == 200
    assert first.headers["content-type"].startswith("application/json")
    assert "attachment;" in first.headers["content-disposition"]
    body = first.json()
    assert body["complete"] is True
    assert body["category_count"] == 7
    assert set(body["categories"]) == set(body["data"])
