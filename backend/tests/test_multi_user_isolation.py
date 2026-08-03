from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.core.db import get_db
from app.core.security import SESSION_COOKIE_NAME, create_session_token
from app.models.user import User
from app.routers.mistake import router as mistake_router


def _app(db_session_factory):
    app = FastAPI()
    app.include_router(mistake_router)

    def override_get_db():
        with db_session_factory() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    return app


def _user(db_session_factory, email: str) -> User:
    with db_session_factory() as session:
        user = User(email=email, display_name=email.split("@")[0], password_hash="unused")
        session.add(user)
        session.commit()
        session.refresh(user)
        session.expunge(user)
        return user


def test_mistake_history_is_isolated_between_registered_learners(db_session_factory):
    app = _app(db_session_factory)
    alice = _user(db_session_factory, "alice@example.com")
    bob = _user(db_session_factory, "bob@example.com")
    alice_client = TestClient(app, base_url="https://testserver")
    bob_client = TestClient(app, base_url="https://testserver")
    alice_client.cookies.set(SESSION_COOKIE_NAME, create_session_token(alice.id))
    bob_client.cookies.set(SESSION_COOKIE_NAME, create_session_token(bob.id))

    created = alice_client.post(
        "/api/mistakes",
        json={
            "skill": "reading",
            "source": "Alice private exercise",
            "reason_category": "missed_paraphrase",
        },
    )
    now = datetime.now(timezone.utc)
    params = {
        "start": (now - timedelta(days=1)).isoformat(),
        "end": (now + timedelta(days=1)).isoformat(),
    }

    assert created.status_code == 201
    assert len(alice_client.get("/api/mistakes", params=params).json()) == 1
    assert bob_client.get("/api/mistakes", params=params).json() == []
