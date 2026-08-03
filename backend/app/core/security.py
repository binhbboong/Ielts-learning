from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
import uuid

from fastapi import Depends, HTTPException, Request, Response
from itsdangerous import BadData, SignatureExpired, URLSafeTimedSerializer
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.models.user import LEGACY_USER_ID, User

SESSION_COOKIE_NAME = "session"
SLIDING_REISSUE_THRESHOLD_DAYS = 7


@dataclass
class TokenVerificationResult:
    valid: bool
    reason: str | None = None
    issued_at: datetime | None = None
    user_id: uuid.UUID | None = None


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.SESSION_SECRET)


def session_cookie_max_age_seconds() -> int:
    return settings.SESSION_COOKIE_MAX_AGE_DAYS * 24 * 60 * 60


def create_session_token(
    user_id: uuid.UUID | str = LEGACY_USER_ID,
) -> str:
    return _serializer().dumps({"user_id": str(user_id)})


def verify_session_token(token: str) -> TokenVerificationResult:
    try:
        payload, issued_at = _serializer().loads(
            token, max_age=session_cookie_max_age_seconds(), return_timestamp=True
        )
    except SignatureExpired:
        return TokenVerificationResult(valid=False, reason="expired")
    except BadData:
        return TokenVerificationResult(valid=False, reason="invalid")
    try:
        user_id = uuid.UUID(payload["user_id"])
    except (KeyError, TypeError, ValueError):
        return TokenVerificationResult(valid=False, reason="invalid")
    return TokenVerificationResult(valid=True, issued_at=issued_at, user_id=user_id)


def require_learner(
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
) -> User:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token is None:
        raise HTTPException(status_code=401, detail={"reason": "missing"})

    result = verify_session_token(token)
    if not result.valid:
        raise HTTPException(status_code=401, detail={"reason": result.reason})
    user = None if result.user_id == LEGACY_USER_ID else db.get(User, result.user_id)
    if user is None and result.user_id != LEGACY_USER_ID:
        raise HTTPException(status_code=401, detail={"reason": "unknown_user"})

    expires_at = result.issued_at + timedelta(days=settings.SESSION_COOKIE_MAX_AGE_DAYS)
    remaining = expires_at - datetime.now(timezone.utc)
    if remaining < timedelta(days=SLIDING_REISSUE_THRESHOLD_DAYS):
        response.set_cookie(
            SESSION_COOKIE_NAME,
            create_session_token(result.user_id),
            max_age=session_cookie_max_age_seconds(),
            httponly=True,
            secure=settings.SESSION_COOKIE_SECURE,
            samesite="lax",
            path="/",
        )
    if user is not None:
        return user
    return User(
        id=LEGACY_USER_ID,
        email="learner@legacy.local",
        display_name="Legacy learner",
        password_hash="",
    )
