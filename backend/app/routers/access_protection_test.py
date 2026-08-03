from datetime import datetime, timedelta, timezone
from http.cookies import SimpleCookie

import bcrypt
from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import Column, Integer, String

from app.core.db import Base, get_db
from app.core.security import SESSION_COOKIE_NAME, create_session_token, require_learner
from app.models.access_protection import LoginAttempt
from app.routers.access_protection import router
from app.services.access_protection import record_attempt


class _FixtureLearnerData(Base):
    """Stand-in for another epic's data table, to prove lockout never touches it."""

    __tablename__ = "test_fixture_learner_data"

    id = Column(Integer, primary_key=True)
    payload = Column(String, nullable=False)


def _client(
    db_session_factory,
    with_protected_route: bool = False,
    base_url: str = "https://testserver",
) -> TestClient:
    app = FastAPI()
    app.include_router(router)

    if with_protected_route:

        @app.get("/protected", dependencies=[Depends(require_learner)])
        def protected():
            return {"ok": True}

    def override_get_db():
        session = db_session_factory()
        try:
            yield session
        finally:
            session.close()

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app, base_url=base_url)


def _set_password(monkeypatch, password: str) -> None:
    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
    monkeypatch.setattr(
        "app.services.access_protection.settings.LEARNER_PASSWORD_HASH", hashed
    )


def test_login_with_correct_password_returns_200_and_sets_cookie(
    db_session_factory, monkeypatch
):
    _set_password(monkeypatch, "correct-horse")
    monkeypatch.setattr(
        "app.routers.access_protection.settings.SESSION_COOKIE_SECURE", True
    )
    client = _client(db_session_factory)

    response = client.post("/api/auth/login", json={"password": "correct-horse"})

    assert response.status_code == 200
    assert "set-cookie" in response.headers
    cookie = SimpleCookie()
    cookie.load(response.headers["set-cookie"])
    session_cookie = cookie[SESSION_COOKIE_NAME]
    assert session_cookie["httponly"] is True
    assert session_cookie["secure"] is True
    assert session_cookie["samesite"].lower() == "lax"
    assert session_cookie["path"] == "/"


def test_local_http_login_can_use_cookie_when_secure_flag_is_disabled(
    db_session_factory, monkeypatch
):
    _set_password(monkeypatch, "correct-horse")
    monkeypatch.setattr(
        "app.routers.access_protection.settings.SESSION_COOKIE_SECURE", False
    )
    client = _client(
        db_session_factory,
        with_protected_route=True,
        base_url="http://testserver",
    )

    login_response = client.post(
        "/api/auth/login", json={"password": "correct-horse"}
    )
    protected_response = client.get("/protected")

    assert login_response.status_code == 200
    assert protected_response.status_code == 200


def test_login_with_wrong_password_returns_401_with_no_cookie_and_generic_body(
    db_session_factory, monkeypatch
):
    _set_password(monkeypatch, "correct-horse")
    client = _client(db_session_factory)

    response = client.post("/api/auth/login", json={"password": "wrong-guess"})

    assert response.status_code == 401
    assert "set-cookie" not in response.headers
    assert "wrong" not in response.text.lower()
    assert "password" not in response.text.lower()


def test_login_locked_out_returns_429_even_with_correct_password_and_never_evaluates_it(
    db_session_factory, monkeypatch
):
    _set_password(monkeypatch, "correct-horse")
    client = _client(db_session_factory)
    session = db_session_factory()
    for _ in range(5):
        record_attempt(session, ip="testclient", succeeded=False)
    session.close()

    was_called = {"value": False}

    def spy_verify_password(_password: str) -> bool:
        was_called["value"] = True
        return True

    monkeypatch.setattr(
        "app.services.access_protection.verify_password", spy_verify_password
    )

    response = client.post("/api/auth/login", json={"password": "correct-horse"})

    assert response.status_code == 429
    assert was_called["value"] is False


def test_register_route_exists_in_openapi_schema(db_session_factory):
    client = _client(db_session_factory)

    schema = client.get("/openapi.json").json()

    assert "/api/auth/register" in schema["paths"]


def test_register_creates_account_sets_cookie_and_rejects_duplicate(
    db_session_factory, monkeypatch
):
    monkeypatch.setattr(
        "app.routers.access_protection.settings.SESSION_COOKIE_SECURE", False
    )
    client = _client(db_session_factory, base_url="http://testserver")
    payload = {
        "email": "developer@example.com",
        "password": "correct-horse",
        "display_name": "Developer",
    }

    created = client.post("/api/auth/register", json=payload)
    duplicate = client.post("/api/auth/register", json=payload)

    assert created.status_code == 201
    assert created.json()["email"] == "developer@example.com"
    assert created.json()["authenticated"] is True
    assert SESSION_COOKIE_NAME in created.cookies
    assert duplicate.status_code == 409


def test_logout_with_valid_session_clears_cookie_via_max_age_zero(db_session_factory):
    token = create_session_token()
    client = _client(db_session_factory)
    client.cookies.set(SESSION_COOKIE_NAME, token)

    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    cookie = SimpleCookie()
    cookie.load(response.headers["set-cookie"])
    assert cookie[SESSION_COOKIE_NAME]["max-age"] == "0"


def test_logout_with_no_cookie_still_succeeds_idempotently(db_session_factory):
    client = _client(db_session_factory)

    response = client.post("/api/auth/logout")

    assert response.status_code == 200
    cookie = SimpleCookie()
    cookie.load(response.headers["set-cookie"])
    assert cookie[SESSION_COOKIE_NAME]["max-age"] == "0"


def test_status_with_no_cookie_returns_200_authenticated_false(db_session_factory):
    client = _client(db_session_factory)

    response = client.get("/api/auth/status")

    assert response.status_code == 200
    assert response.json() == {"authenticated": False}


def test_status_with_valid_cookie_returns_200_authenticated_true(db_session_factory):
    token = create_session_token()
    client = _client(db_session_factory)
    client.cookies.set(SESSION_COOKIE_NAME, token)

    response = client.get("/api/auth/status")

    assert response.status_code == 200
    assert response.json() == {"authenticated": True}


def test_status_with_malformed_cookie_returns_200_authenticated_false(db_session_factory):
    client = _client(db_session_factory)
    client.cookies.set(SESSION_COOKIE_NAME, "not-a-real-token")

    response = client.get("/api/auth/status")

    assert response.status_code == 200
    assert response.json() == {"authenticated": False}


def test_lockout_does_not_touch_unrelated_data_or_delete_login_attempt_rows(
    db_session_factory, monkeypatch
):
    _set_password(monkeypatch, "correct-horse")
    session = db_session_factory()
    session.add(_FixtureLearnerData(payload="untouched"))
    session.commit()
    session.close()

    client = _client(db_session_factory)
    for _ in range(5):
        client.post("/api/auth/login", json={"password": "wrong-guess"})

    session = db_session_factory()
    fixture_rows = session.query(_FixtureLearnerData).all()
    assert len(fixture_rows) == 1
    assert fixture_rows[0].payload == "untouched"

    attempt_rows = (
        session.query(LoginAttempt).filter_by(ip_address="testclient").all()
    )
    assert len(attempt_rows) == 5
    assert all(row.succeeded is False for row in attempt_rows)
    session.close()


def test_lockout_is_temporary_and_lifts_once_rolling_window_elapses(
    db_session_factory, monkeypatch
):
    _set_password(monkeypatch, "correct-horse")
    session = db_session_factory()
    stale_time = datetime.now(timezone.utc) - timedelta(minutes=16)
    for _ in range(5):
        session.add(
            LoginAttempt(ip_address="testclient", occurred_at=stale_time, succeeded=False)
        )
    session.commit()
    session.close()

    client = _client(db_session_factory)

    response = client.post("/api/auth/login", json={"password": "correct-horse"})

    assert response.status_code == 200
    assert "set-cookie" in response.headers


def test_one_login_authenticates_multiple_subsequent_requests_without_re_proof(
    db_session_factory, monkeypatch
):
    _set_password(monkeypatch, "correct-horse")
    client = _client(db_session_factory, with_protected_route=True)

    login_response = client.post("/api/auth/login", json={"password": "correct-horse"})
    assert login_response.status_code == 200

    for _ in range(3):
        response = client.get("/protected")
        assert response.status_code == 200
        assert response.json() == {"ok": True}
