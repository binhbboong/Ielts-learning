from datetime import date
from pathlib import Path

from alembic import command
from alembic.config import Config
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.ai import get_ai_provider
from app.ai.schemas import ChatResult
from app.ai.testing import FakeAIProvider
from app.core.config import settings
from app.core.db import get_db
from app.models import speaking_question  # noqa: F401 registers the FK target table
from app.models.writing_submission import WritingSubmission
from app.routers.cron import router as cron_router
from app.services.text_to_speech import (
    FakeTextToSpeech,
    SynthesisResult,
    get_text_to_speech,
)

_ALEMBIC_INI = Path(__file__).resolve().parents[1] / "alembic.ini"


def _migrations_config_for_test_db() -> Config:
    cfg = Config(str(_ALEMBIC_INI))
    cfg.set_main_option("sqlalchemy.url", settings.TEST_DATABASE_URL)
    cfg.set_main_option("script_location", str(_ALEMBIC_INI.parent / "alembic"))
    return cfg


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


def test_run_migrations_rejects_missing_or_wrong_secret(db_session_factory, monkeypatch):
    monkeypatch.setattr(settings, "CRON_SECRET", "the-real-secret")
    client = _client(db_session_factory)

    no_header = client.post("/api/cron/run-migrations")
    assert no_header.status_code == 401

    wrong_secret = client.post(
        "/api/cron/run-migrations",
        headers={"Authorization": "Bearer wrong-value"},
    )
    assert wrong_secret.status_code == 401


def test_run_migrations_upgrades_the_configured_database_to_head(monkeypatch):
    monkeypatch.setattr(settings, "CRON_SECRET", "the-real-secret")
    monkeypatch.setattr(settings, "DATABASE_URL", settings.TEST_DATABASE_URL)
    cfg = _migrations_config_for_test_db()
    command.downgrade(cfg, "base")
    try:
        app = FastAPI()
        app.include_router(cron_router)
        client = TestClient(app, base_url="https://testserver")

        response = client.post(
            "/api/cron/run-migrations",
            headers={"Authorization": "Bearer the-real-secret"},
        )

        assert response.status_code == 200
        assert response.json() == {"revision": "0023"}
    finally:
        command.downgrade(cfg, "base")


def test_debug_checkpoint_rejects_missing_or_wrong_secret(db_session_factory, monkeypatch):
    monkeypatch.setattr(settings, "CRON_SECRET", "the-real-secret")
    client = _client(db_session_factory)

    no_header = client.get("/api/cron/debug-checkpoint")
    assert no_header.status_code == 401


def test_debug_checkpoint_reports_the_days_required_band_and_actual_writing_band(
    db_session_factory, monkeypatch
):
    monkeypatch.setattr(settings, "CRON_SECRET", "the-real-secret")
    client = _client(db_session_factory)
    day = date(2026, 8, 6)

    with db_session_factory() as session:
        session.add(
            WritingSubmission(
                question_text="Describe a place you like.",
                task_type="task2",
                response_text="Essay text.",
                status="complete",
                day=day,
                overall_band=3.5,
            )
        )
        session.commit()

    response = client.get(
        f"/api/cron/debug-checkpoint?day={day.isoformat()}",
        headers={"Authorization": "Bearer the-real-secret"},
    )

    assert response.status_code == 200
    body = response.json()
    # A brand-new profile's first day is the foundation phase (target_band 4.5).
    assert body["phase"] == "foundation"
    assert body["required_band"] == 4.5
    assert body["writing"] == {
        "passed": False, "overall_band": 3.5, "status": "complete",
    }
    assert body["all_passed"] is False
