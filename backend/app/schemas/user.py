from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from backend.app.core.permissions import Role


class UserBase(BaseModel):
    username: str = Field(min_length=1, max_length=80)
    full_name: Optional[str] = None
    role: Role
    is_active: bool = True


class UserCreate(UserBase):
    password: str = Field(min_length=1)


class UserUpdate(BaseModel):
    password: Optional[str] = Field(default=None, min_length=1)
    full_name: Optional[str] = None
    role: Optional[Role] = None
    is_active: Optional[bool] = None


class UserRead(UserBase):
    id: int
    created_at: str
    updated_at: str
