from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.ai import get_ai_provider
from app.ai.schemas import ChatResult
from app.ai.testing import FakeAIProvider
from app.core.config import settings
from app.core.db import get_db
from app.models import speaking_question  # noqa: F401 registers the FK target table
from app.routers.cron import router as cron_router
from app.services.text_to_speech import (
    FakeTextToSpeech,
    SynthesisResult,
    get_text_to_speech,
)


def _client(db_session_factory):
    app = FastAPI()
    app.include_router(cron_router)

    def override_get_db():
        with db_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_ai_provider] = lambda: FakeAIProvider(
        chat_result=ChatResult(status="ok", message="A generated prompt.")
    )
    app.dependency_overrides[get_text_to_speech] = lambda: FakeTextToSpeech(
        SynthesisResult(status="ok", audio_bytes=b"audio", content_type="audio/mpeg")
    )
    return TestClient(app, base_url="https://testserver")


def test_pregenerate_lessons_rejects_missing_or_wrong_secret(db_session_factory, monkeypatch):
    monkeypatch.setattr(settings, "CRON_SECRET", "the-real-secret")
    client = _client(db_session_factory)

    no_header = client.get("/api/cron/pregenerate-lessons")
    assert no_header.status_code == 401

    wrong_secret = client.get(
        "/api/cron/pregenerate-lessons",
        headers={"Authorization": "Bearer wrong-value"},
    )
    assert wrong_secret.status_code == 401


def test_pregenerate_lessons_rejects_when_secret_not_configured(db_session_factory, monkeypatch):
    monkeypatch.setattr(settings, "CRON_SECRET", "")
    client = _client(db_session_factory)

    response = client.get(
        "/api/cron/pregenerate-lessons",
        headers={"Authorization": "Bearer anything"},
    )
    assert response.status_code == 401


def test_pregenerate_lessons_succeeds_with_correct_secret(db_session_factory, monkeypatch):
    monkeypatch.setattr(settings, "CRON_SECRET", "the-real-secret")
    client = _client(db_session_factory)

    response = client.get(
        "/api/cron/pregenerate-lessons",
        headers={"Authorization": "Bearer the-real-secret"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["processed"] == {}
    assert body["errors"] == {}
