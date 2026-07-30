from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.db import get_db
from app.core.security import SESSION_COOKIE_NAME, create_session_token
from app.routers.mistake import router


def _client(db_session_factory, authenticated=True):
    app = FastAPI()
    app.include_router(router)

    def override_get_db():
        with db_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    client = TestClient(app, base_url="https://testserver")
    if authenticated:
        client.cookies.set(SESSION_COOKIE_NAME, create_session_token())
    return client


def _range():
    now = datetime.now(timezone.utc)
    return {
        "start": (now - timedelta(days=1)).isoformat(),
        "end": (now + timedelta(days=1)).isoformat(),
    }


def test_every_mistake_route_requires_authentication(db_session_factory):
    client = _client(db_session_factory, authenticated=False)
    params = _range()

    assert client.post(
        "/api/mistakes", json={"skill": "reading", "source": "Book"}
    ).status_code == 401
    assert client.get("/api/mistakes", params=params).status_code == 401
    assert client.get("/api/mistakes/grouped", params=params).status_code == 401
    assert client.get(
        "/api/mistakes/grouped/carelessness", params=params
    ).status_code == 401


def test_create_list_group_and_detail_round_trip(db_session_factory):
    client = _client(db_session_factory)
    payload = {
        "skill": "reading",
        "question_type": "true_false_not_given",
        "source": "Cambridge 18",
        "own_answer": "True",
        "correct_answer": "False",
        "explanation": "I read too quickly.",
        "reason_category": "carelessness",
    }

    created = client.post("/api/mistakes", json=payload)
    assert created.status_code == 201
    assert created.json()["is_incomplete"] is False

    params = _range()
    chronological = client.get("/api/mistakes", params=params)
    assert chronological.status_code == 200
    assert chronological.json()[0]["source"] == "Cambridge 18"

    grouped = client.get("/api/mistakes/grouped", params=params)
    assert grouped.json() == [
        {"reason_category": "carelessness", "count": 1}
    ]

    detail = client.get(
        "/api/mistakes/grouped/carelessness", params=params
    )
    assert detail.status_code == 200
    assert detail.json()[0]["own_answer"] == "True"
    assert detail.json()[0]["correct_answer"] == "False"
    assert detail.json()[0]["explanation"] == "I read too quickly."


def test_minimal_create_is_persisted_as_incomplete(db_session_factory):
    client = _client(db_session_factory)
    response = client.post(
        "/api/mistakes",
        json={"skill": "listening", "source": "Mock test"},
    )

    assert response.status_code == 201
    assert response.json()["reason_category"] == "not_sure_other"
    assert response.json()["is_incomplete"] is True
