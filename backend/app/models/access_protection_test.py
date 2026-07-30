from datetime import datetime, timezone

from app.models.access_protection import LoginAttempt


def test_login_attempt_round_trips_through_a_fresh_session(db_session_factory):
    occurred_at = datetime.now(timezone.utc)

    write_session = db_session_factory()
    write_session.add(
        LoginAttempt(ip_address="203.0.113.5", occurred_at=occurred_at, succeeded=False)
    )
    write_session.commit()
    write_session.close()

    read_session = db_session_factory()
    row = read_session.query(LoginAttempt).filter_by(ip_address="203.0.113.5").one()
    read_session.close()

    assert row.ip_address == "203.0.113.5"
    assert row.succeeded is False
    assert row.occurred_at == occurred_at
