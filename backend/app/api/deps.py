from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from typing import Annotated, Callable, Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from backend.app.core.database import get_connection
from backend.app.core.permissions import has_permission
from backend.app.core.security import decode_access_token
from backend.app.models.user import User
from backend.app.services.user_service import get_user_by_id


bearer_scheme = HTTPBearer(auto_error=False)


def get_db() -> Iterator[sqlite3.Connection]:
    with get_connection() as conn:
        yield conn


Database = Annotated[sqlite3.Connection, Depends(get_db)]


def get_current_user(
    credentials: Annotated[Optional[HTTPAuthorizationCredentials], Depends(bearer_scheme)],
    conn: Database,
) -> User:
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    payload = decode_access_token(credentials.credentials)
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    user = get_user_by_id(conn, int(user_id))
    if user is None or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Inactive or missing user")
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_permission(permission: str) -> Callable[[CurrentUser], User]:
    def dependency(current_user: CurrentUser) -> User:
        if not has_permission(current_user.role, permission):
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user

    return dependency
