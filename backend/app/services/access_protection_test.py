from datetime import datetime, timedelta, timezone

import bcrypt

from app.models.access_protection import LoginAttempt
from app.services.access_protection import (
    authenticate,
    is_locked_out,
    record_attempt,
    verify_password,
)


def test_verify_password_true_for_correct_password(monkeypatch):
    hashed = bcrypt.hashpw(b"correct-horse", bcrypt.gensalt()).decode()
    monkeypatch.setattr(
        "app.services.access_protection.settings.LEARNER_PASSWORD_HASH", hashed
    )

    assert verify_password("correct-horse") is True


def test_verify_password_false_for_incorrect_password(monkeypatch):
    hashed = bcrypt.hashpw(b"correct-horse", bcrypt.gensalt()).decode()
    monkeypatch.setattr(
        "app.services.access_protection.settings.LEARNER_PASSWORD_HASH", hashed
    )

    assert verify_password("wrong-guess") is False


def test_five_failed_attempts_in_window_locks_out_that_ip(db_session_factory):
    session = db_session_factory()
    for _ in range(5):
        record_attempt(session, ip="203.0.113.9", succeeded=False)

    assert is_locked_out(session, ip="203.0.113.9") is True
    session.close()


def test_attempts_older_than_15_minutes_do_not_count_toward_lockout(db_session_factory):
    session = db_session_factory()
    old_time = datetime.now(timezone.utc) - timedelta(minutes=16)
    for _ in range(5):
        session.add(
            LoginAttempt(ip_address="203.0.113.10", occurred_at=old_time, succeeded=False)
        )
    session.commit()

    assert is_locked_out(session, ip="203.0.113.10") is False
    session.close()


def test_lockout_is_per_ip(db_session_factory):
    session = db_session_factory()
    for _ in range(5):
        record_attempt(session, ip="203.0.113.11", succeeded=False)

    assert is_locked_out(session, ip="203.0.113.11") is True
    assert is_locked_out(session, ip="203.0.113.12") is False
    session.close()


def test_authenticate_when_locked_out_never_calls_verify_password_even_if_correct(
    db_session_factory, monkeypatch
):
    session = db_session_factory()
    for _ in range(5):
        record_attempt(session, ip="203.0.113.20", succeeded=False)

    was_called = {"value": False}

    def spy_verify_password(_password: str) -> bool:
        was_called["value"] = True
        return True

    monkeypatch.setattr(
        "app.services.access_protection.verify_password", spy_verify_password
    )

    result = authenticate(session, password="the-real-correct-password", ip="203.0.113.20")

    assert result.success is False
    assert was_called["value"] is False
    session.close()


def test_authenticate_wrong_password_fails_and_is_recorded(db_session_factory, monkeypatch):
    session = db_session_factory()
    hashed = bcrypt.hashpw(b"correct-horse", bcrypt.gensalt()).decode()
    monkeypatch.setattr(
        "app.services.access_protection.settings.LEARNER_PASSWORD_HASH", hashed
    )

    result = authenticate(session, password="wrong-guess", ip="203.0.113.21")

    assert result.success is False
    recorded = (
        session.query(LoginAttempt).filter_by(ip_address="203.0.113.21").one()
    )
    assert recorded.succeeded is False
    session.close()


def test_authenticate_failure_shape_identical_for_wrong_password_and_lockout(
    db_session_factory, monkeypatch
):
    hashed = bcrypt.hashpw(b"correct-horse", bcrypt.gensalt()).decode()
    monkeypatch.setattr(
        "app.services.access_protection.settings.LEARNER_PASSWORD_HASH", hashed
    )

    session = db_session_factory()
    wrong_password_result = authenticate(session, password="nope", ip="203.0.113.22")

    for _ in range(5):
        record_attempt(session, ip="203.0.113.23", succeeded=False)
    locked_out_result = authenticate(session, password="nope", ip="203.0.113.23")

    # Both are failures; the only field distinguishing them is the operational
    # `locked_out` flag (used by the router to pick 401 vs 429) — neither result
    # carries any additional text/field that would reveal *why* beyond that.
    assert wrong_password_result.success is False
    assert locked_out_result.success is False
    assert vars(wrong_password_result).keys() == vars(locked_out_result).keys()
    assert wrong_password_result.locked_out is False
    assert locked_out_result.locked_out is True
    session.close()
