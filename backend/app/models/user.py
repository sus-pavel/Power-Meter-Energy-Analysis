from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class User:
    id: int
    username: str
    password_hash: str
    full_name: str | None
    role: str
    is_active: bool
    must_change_password: bool
    created_at: str
    updated_at: str
