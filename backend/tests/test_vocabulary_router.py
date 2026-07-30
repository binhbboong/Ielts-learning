from datetime import date

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.db import get_db
from app.core.security import SESSION_COOKIE_NAME, create_session_token
from app.models.vocabulary import VocabularyWord
from app.routers.vocabulary import router


def _client(db_session_factory):
    app = FastAPI()
    app.include_router(router)

    def override_get_db():
        with db_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app, base_url="https://testserver")
    client.cookies.set(SESSION_COOKIE_NAME, create_session_token())
    return client


def test_post_word_minimal_returns_201_confirmation(db_session_factory):
    response = _client(db_session_factory).post(
        "/api/vocabulary/words",
        json={"word": "ubiquitous", "meaning": "found everywhere"},
    )
    assert response.status_code == 201
    assert response.json()["saved"] is True
    assert response.json()["word"]["interval_index"] == 0


def test_due_and_current_distinguish_zero_due_from_failure(
    db_session_factory, monkeypatch
):
    client = _client(db_session_factory)
    due = client.get("/api/vocabulary/due")
    assert due.status_code == 200
    assert due.json()["total_due"] == 0
    current = client.get("/api/vocabulary/review/current")
    assert current.json() == {"status": "nothing_due"}

    def fail(*_args, **_kwargs):
        raise RuntimeError("database unavailable")

    monkeypatch.setattr(
        "app.routers.vocabulary.service.get_due_summary", fail
    )
    failed = client.get("/api/vocabulary/due")
    assert failed.status_code == 503
    assert "total_due" not in failed.json()


def test_review_start_assess_and_complete_round_trip(db_session_factory):
    with db_session_factory() as session:
        session.add(
            VocabularyWord(
                word="mitigate",
                meaning="make less severe",
                interval_index=0,
                next_due_date=date.today(),
            )
        )
        session.commit()
    client = _client(db_session_factory)

    started = client.post("/api/vocabulary/review/start")
    assert started.status_code == 200
    assert started.json()["status"] == "item"
    assert started.json()["item"]["word"] == "mitigate"

    assessed = client.post(
        "/api/vocabulary/review/current/assess",
        json={"outcome": "remembered"},
    )
    assert assessed.status_code == 200
    assert assessed.json()["status"] == "complete"
    assert assessed.json()["summary"]["total_reviewed"] == 1
    assert assessed.json()["summary"]["remembered"] == 1
