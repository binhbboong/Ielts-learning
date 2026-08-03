import uuid

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
from app.models.user import User
from app.schemas.access_protection import AuthStatusResponse, LoginRequest, RegisterRequest
from app.services.access_protection import authenticate, register

router = APIRouter(prefix="/api/auth")


@router.post("/login")
def login(
    payload: LoginRequest,
    request: Request,
    response: Response,
    db: Session = Depends(get_db),
):
    ip = request.client.host if request.client else "unknown"
    result = authenticate(
        db,
        email=str(payload.email) if payload.email else None,
        password=payload.password,
        ip=ip,
    )

    if result.locked_out:
        raise HTTPException(status_code=429, detail="Too many attempts")

    if not result.success:
        raise HTTPException(status_code=401, detail="Authentication failed")

    response.set_cookie(
        SESSION_COOKIE_NAME,
        create_session_token(result.user.id) if result.user else create_session_token(),
        max_age=session_cookie_max_age_seconds(),
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )
    return AuthStatusResponse(
        authenticated=True,
        user_id=result.user.id if result.user else None,
        email=result.user.email if result.user else None,
        display_name=result.user.display_name if result.user else "Legacy learner",
    )


@router.post("/register", response_model=AuthStatusResponse, status_code=201)
def create_account(
    payload: RegisterRequest,
    response: Response,
    db: Session = Depends(get_db),
):
    try:
        user = register(
            db,
            email=str(payload.email),
            password=payload.password,
            display_name=payload.display_name,
        )
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    response.set_cookie(
        SESSION_COOKIE_NAME,
        create_session_token(user.id),
        max_age=session_cookie_max_age_seconds(),
        httponly=True,
        secure=settings.SESSION_COOKIE_SECURE,
        samesite="lax",
        path="/",
    )
    return AuthStatusResponse(
        authenticated=True,
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
    )


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


@router.get(
    "/status",
    response_model=AuthStatusResponse,
    response_model_exclude_none=True,
)
def status(request: Request, db: Session = Depends(get_db)):
    token = request.cookies.get(SESSION_COOKIE_NAME)
    if token is None:
        return AuthStatusResponse(authenticated=False)

    result = verify_session_token(token)
    if not result.valid:
        return AuthStatusResponse(authenticated=False)
    if result.user_id == uuid.UUID("00000000-0000-0000-0000-000000000001"):
        return AuthStatusResponse(authenticated=True)
    user = db.get(User, result.user_id)
    if user is None:
        return AuthStatusResponse(authenticated=False)
    return AuthStatusResponse(
        authenticated=True,
        user_id=user.id,
        email=user.email,
        display_name=user.display_name,
    )
