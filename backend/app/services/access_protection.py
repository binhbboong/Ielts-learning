from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

import bcrypt
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.access_protection import LoginAttempt
from app.models.user import User

LOCKOUT_WINDOW_MINUTES = 15
LOCKOUT_THRESHOLD = 5


@dataclass
class AuthResult:
    success: bool
    locked_out: bool = False
    user: User | None = None


def hash_password(plain_password: str) -> str:
    return bcrypt.hashpw(plain_password.encode(), bcrypt.gensalt()).decode()


def verify_password(plain_password: str, password_hash: str | None = None) -> bool:
    password_hash = password_hash or settings.LEARNER_PASSWORD_HASH
    return bcrypt.checkpw(plain_password.encode(), password_hash.encode())


def register(db: Session, email: str, password: str, display_name: str) -> User:
    user = User(
        email=email.strip().lower(),
        display_name=display_name.strip(),
        password_hash=hash_password(password),
    )
    db.add(user)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise ValueError("Email is already registered") from exc
    db.refresh(user)
    return user


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


def authenticate(
    db: Session,
    password: str,
    ip: str,
    email: str | None = None,
) -> AuthResult:
    if is_locked_out(db, ip):
        return AuthResult(success=False, locked_out=True)

    user = (
        db.query(User).filter(User.email == email.strip().lower()).one_or_none()
        if email
        else None
    )
    success = (
        verify_password(password, user.password_hash)
        if user is not None
        else (verify_password(password) if email is None else False)
    )
    record_attempt(db, ip=ip, succeeded=success)
    return AuthResult(success=success, locked_out=False, user=user if success else None)
