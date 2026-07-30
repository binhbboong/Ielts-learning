from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import bcrypt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.access_protection import LoginAttempt

LOCKOUT_WINDOW_MINUTES = 15
LOCKOUT_THRESHOLD = 5


@dataclass
class AuthResult:
    success: bool
    locked_out: bool = False


def verify_password(plain_password: str) -> bool:
    return bcrypt.checkpw(
        plain_password.encode(), settings.LEARNER_PASSWORD_HASH.encode()
    )


def record_attempt(db: Session, ip: str, succeeded: bool) -> None:
    db.add(
        LoginAttempt(
            ip_address=ip, occurred_at=datetime.now(timezone.utc), succeeded=succeeded
        )
    )
    db.commit()


def is_locked_out(db: Session, ip: str) -> bool:
    window_start = datetime.now(timezone.utc) - timedelta(minutes=LOCKOUT_WINDOW_MINUTES)
    failed_count = (
        db.query(LoginAttempt)
        .filter(
            LoginAttempt.ip_address == ip,
            LoginAttempt.succeeded.is_(False),
            LoginAttempt.occurred_at >= window_start,
        )
        .count()
    )
    return failed_count >= LOCKOUT_THRESHOLD


def authenticate(db: Session, password: str, ip: str) -> AuthResult:
    if is_locked_out(db, ip):
        return AuthResult(success=False, locked_out=True)

    success = verify_password(password)
    record_attempt(db, ip=ip, succeeded=success)
    return AuthResult(success=success, locked_out=False)
