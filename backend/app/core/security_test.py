import time
from datetime import datetime, timezone
from http.cookies import SimpleCookie

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from app.core.security import (
    SESSION_COOKIE_NAME,
    create_session_token,
    require_learner,
    verify_session_token,
)


def test_session_cookie_name_is_defined():
    assert SESSION_COOKIE_NAME == "session"


def test_freshly_created_token_verifies_successfully():
    token = create_session_token()

    result = verify_session_token(token)

    assert result.valid is True


def test_tampered_token_fails_verification_as_invalid():
    token = create_session_token()
    # Flip a character in the middle of the signature segment. Flipping the
    # very last character can land on an unused padding bit in the base64
    # encoding and silently decode to the same bytes, so tamper further in.
    index = len(token) - 5
    tampered = token[:index] + ("a" if token[index] != "a" else "b") + token[index + 1 :]

    result = verify_session_token(tampered)

    assert result.valid is False
    assert result.reason == "invalid"


def test_malformed_token_fails_verification_as_invalid():
    result = verify_session_token("not-a-real-token")

    assert result.valid is False
    assert result.reason == "invalid"


def test_expired_token_fails_verification_as_expired(monkeypatch):
    thirty_one_days_ago = time.time() - (31 * 24 * 60 * 60)
    monkeypatch.setattr("itsdangerous.timed.time.time", lambda: thirty_one_days_ago)
    token = create_session_token()
    monkeypatch.undo()

    result = verify_session_token(token)

    assert result.valid is False
    assert result.reason == "expired"


def _protected_test_app() -> FastAPI:
    app = FastAPI()

    @app.get("/protected", dependencies=[Depends(require_learner)])
    def protected():
        return {"ok": True}

    return app


def test_require_learner_rejects_missing_cookie_with_401_missing():
    client = TestClient(_protected_test_app())

    response = client.get("/protected")

    assert response.status_code == 401
    assert response.json()["detail"]["reason"] == "missing"


def test_require_learner_rejects_malformed_cookie_with_401_invalid():
    client = TestClient(_protected_test_app())
    client.cookies.set(SESSION_COOKIE_NAME, "not-a-real-token")

    response = client.get("/protected")

    assert response.status_code == 401
    assert response.json()["detail"]["reason"] == "invalid"


def test_require_learner_rejects_expired_cookie_with_401_expired(monkeypatch):
    thirty_one_days_ago = time.time() - (31 * 24 * 60 * 60)
    monkeypatch.setattr("itsdangerous.timed.time.time", lambda: thirty_one_days_ago)
    token = create_session_token()
    monkeypatch.undo()

    client = TestClient(_protected_test_app())
    client.cookies.set(SESSION_COOKIE_NAME, token)

    response = client.get("/protected")

    assert response.status_code == 401
    assert response.json()["detail"]["reason"] == "expired"


def test_require_learner_allows_valid_token_through():
    token = create_session_token()
    client = TestClient(_protected_test_app())
    client.cookies.set(SESSION_COOKIE_NAME, token)

    response = client.get("/protected")

    assert response.status_code == 200
    assert response.json() == {"ok": True}


def _extract_cookie_value(response, name: str) -> str:
    cookie = SimpleCookie()
    cookie.load(response.headers["set-cookie"])
    return cookie[name].value


def test_require_learner_does_not_reissue_cookie_when_far_from_expiry():
    token = create_session_token()
    client = TestClient(_protected_test_app())
    client.cookies.set(SESSION_COOKIE_NAME, token)

    response = client.get("/protected")

    assert response.status_code == 200
    assert "set-cookie" not in response.headers


def test_require_learner_reissues_cookie_with_fresh_expiry_when_under_7_days_remaining(
    monkeypatch,
):
    # 30-day max age, issued 24 days ago -> 6 days remaining, under the 7-day threshold.
    twenty_four_days_ago = time.time() - (24 * 24 * 60 * 60)
    monkeypatch.setattr("itsdangerous.timed.time.time", lambda: twenty_four_days_ago)
    token = create_session_token()
    monkeypatch.undo()

    client = TestClient(_protected_test_app())
    client.cookies.set(SESSION_COOKIE_NAME, token)

    response = client.get("/protected")

    assert response.status_code == 200
    assert "set-cookie" in response.headers

    reissued_token = _extract_cookie_value(response, SESSION_COOKIE_NAME)
    reissued_result = verify_session_token(reissued_token)
    assert reissued_result.valid is True
    assert (
        abs((reissued_result.issued_at - datetime.now(timezone.utc)).total_seconds())
        < 5
    )
