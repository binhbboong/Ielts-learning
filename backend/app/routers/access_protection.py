from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.db import get_db
from app.core.security import (
    SESSION_COOKIE_NAME,
    create_session_token,
    session_cookie_max_age_seconds,
    verify_session_token,
)
from app.schemas.access_protection import AuthStatusResponse, LoginRequest
from app.services.access_protection import authenticate

router = APIRouter(prefix="/api/auth")


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"
    result = authenticate(db, password=payload.password, ip=ip)

    if result.locked_out:
        raise HTTPException(status_code=429, detail="Too many attempts")

    if not result.success:
        raise HTTPException(status_code=401, detail="Authentication failed")

    response.set_cookie(
        SESSION_COOKIE_NAME,
        create_session_token(),
        max_age=session_cookie_max_age_seconds(),
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )
    return {"authenticated": True}


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(
        SESSION_COOKIE_NAME,
        path="/",
        secure=settings.SESSION_COOKIE_SECURE,
        httponly=True,
        samesite="lax",
    )
    return {"authenticated": False}


@router.get("/status", response_model=AuthStatusResponse)
def status(request: Request):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token is None:
        return AuthStatusResponse(authenticated=False)

    result = verify_session_token(token)
    return AuthStatusResponse(authenticated=result.valid)
