from __future__ import annotations

import sqlite3

from backend.app.core.security import hash_password
from backend.app.models.user import User
from backend.app.schemas.user import UserCreate, UserUpdate


def row_to_user(row: sqlite3.Row) -> User:
    return User(
        id=row["id"],
        username=row["username"],
        password_hash=row["password_hash"],
        full_name=row["full_name"],
        role=row["role"],
        is_active=bool(row["is_active"]),
        must_change_password=bool(row["must_change_password"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def get_user_by_username(conn: sqlite3.Connection, username: str) -> User | None:
    row = conn.execute("SELECT * FROM users WHERE username = ?", (username,)).fetchone()
    return row_to_user(row) if row else None


def get_user_by_id(conn: sqlite3.Connection, user_id: int) -> User | None:
    row = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    return row_to_user(row) if row else None


def list_users(conn: sqlite3.Connection) -> list[User]:
    rows = conn.execute("SELECT * FROM users ORDER BY username").fetchall()
    return [row_to_user(row) for row in rows]


def create_user(conn: sqlite3.Connection, payload: UserCreate) -> User:
    cursor = conn.execute(
        """
        INSERT INTO users (username, password_hash, full_name, role, is_active)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            payload.username,
            hash_password(payload.password),
            payload.full_name,
            payload.role.value,
            int(payload.is_active),
        ),
    )
    return get_user_by_id(conn, cursor.lastrowid)


def update_user(conn: sqlite3.Connection, user_id: int, payload: UserUpdate) -> User | None:
    existing = get_user_by_id(conn, user_id)
    if existing is None:
        return None
    values = payload.model_dump(exclude_unset=True)
    if "password" in values:
        values["password_hash"] = hash_password(values.pop("password"))
        values["must_change_password"] = 0
    if "role" in values and values["role"] is not None:
        values["role"] = values["role"].value
    if "is_active" in values and values["is_active"] is not None:
        values["is_active"] = int(values["is_active"])
    if not values:
        return existing
    assignments = ", ".join(f"{field} = ?" for field in values)
    params = [*values.values(), user_id]
    conn.execute(
        f"UPDATE users SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        params,
    )
    return get_user_by_id(conn, user_id)


def delete_user(conn: sqlite3.Connection, user_id: int) -> bool:
    cursor = conn.execute("DELETE FROM users WHERE id = ?", (user_id,))
    return cursor.rowcount > 0
