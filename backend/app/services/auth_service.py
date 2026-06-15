from __future__ import annotations

import sqlite3

from backend.app.core.security import verify_password
from backend.app.models.user import User
from backend.app.services.user_service import get_user_by_username


def authenticate_user(conn: sqlite3.Connection, username: str, password: str) -> User | None:
    user = get_user_by_username(conn, username)
    if user is None or not user.is_active:
        return None
    if not verify_password(password, user.password_hash):
        return None
    return user
