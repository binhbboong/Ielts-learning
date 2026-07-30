from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException, Request, Response
from itsdangerous import BadData, SignatureExpired, URLSafeTimedSerializer

from app.core.config import settings

SESSION_COOKIE_NAME = "session"
SLIDING_REISSUE_THRESHOLD_DAYS = 7


@dataclass
class TokenVerificationResult:
    valid: bool
    reason: str | None = None
    issued_at: datetime | None = None


def _serializer() -> URLSafeTimedSerializer:
    return URLSafeTimedSerializer(settings.SESSION_SECRET)


def session_cookie_max_age_seconds() -> int:
    return settings.SESSION_COOKIE_MAX_AGE_DAYS * 24 * 60 * 60


def create_session_token() -> str:
    return _serializer().dumps({"learner": True})


def verify_session_token(token: str) -> TokenVerificationResult:
    try:
        _payload, issued_at = _serializer().loads(
            token, max_age=session_cookie_max_age_seconds(), return_timestamp=True
        )
    except SignatureExpired:
        return TokenVerificationResult(valid=False, reason="expired")
    except BadData:
        return TokenVerificationResult(valid=False, reason="invalid")
    return TokenVerificationResult(valid=True, issued_at=issued_at)


def require_learner(request: Request, response: Response) -> None:
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token is None:
        raise HTTPException(status_code=401, detail={"reason": "missing"})

    result = verify_session_token(token)
    if not result.valid:
        raise HTTPException(status_code=401, detail={"reason": result.reason})

    expires_at = result.issued_at + timedelta(days=settings.SESSION_COOKIE_MAX_AGE_DAYS)
    remaining = expires_at - datetime.now(timezone.utc)
    if remaining < timedelta(days=SLIDING_REISSUE_THRESHOLD_DAYS):
        response.set_cookie(
            SESSION_COOKIE_NAME,
            create_session_token(),
            max_age=session_cookie_max_age_seconds(),
            httponly=True,
            secure=settings.SESSION_COOKIE_SECURE,
            samesite="lax",
            path="/",
        )
