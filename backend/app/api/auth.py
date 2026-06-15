from __future__ import annotations

from fastapi import APIRouter, HTTPException, status

from backend.app.api.deps import CurrentUser, Database
from backend.app.core.security import create_access_token
from backend.app.schemas.auth import LoginRequest, LogoutResponse, TokenResponse
from backend.app.schemas.user import UserRead
from backend.app.services.auth_service import authenticate_user


router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, conn: Database) -> TokenResponse:
    user = authenticate_user(conn, payload.username, payload.password)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return TokenResponse(access_token=create_access_token(str(user.id)))


@router.get("/me", response_model=UserRead)
def me(current_user: CurrentUser) -> UserRead:
    return UserRead(**current_user.__dict__)


@router.post("/logout", response_model=LogoutResponse)
def logout(_: CurrentUser) -> LogoutResponse:
    return LogoutResponse(status="ok", message="JWT logout is client-side for Stage 1.")
