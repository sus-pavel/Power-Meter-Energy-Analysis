from __future__ import annotations

import sqlite3

from fastapi import APIRouter, Depends, HTTPException, Response, status

from backend.app.api.deps import CurrentUser, Database, require_permission
from backend.app.models.user import User
from backend.app.schemas.user import UserCreate, UserRead, UserUpdate
from backend.app.services import user_service
from backend.app.services.audit_service import write_audit_log


router = APIRouter(prefix="/api/users", tags=["users"])


@router.get("", response_model=list[UserRead])
def list_users(
    conn: Database,
    _: User = Depends(require_permission("manage_users")),
) -> list[UserRead]:
    return [UserRead(**user.__dict__) for user in user_service.list_users(conn)]


@router.post("", response_model=UserRead, status_code=status.HTTP_201_CREATED)
def create_user(
    payload: UserCreate,
    conn: Database,
    current_user: User = Depends(require_permission("manage_users")),
) -> UserRead:
    try:
        user = user_service.create_user(conn, payload)
        write_audit_log(conn, user_id=current_user.id, action="create", entity_type="user", entity_id=user.id)
        return UserRead(**user.__dict__)
    except sqlite3.IntegrityError as exc:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Username already exists") from exc


@router.get("/{user_id}", response_model=UserRead)
def get_user(
    user_id: int,
    conn: Database,
    _: User = Depends(require_permission("manage_users")),
) -> UserRead:
    user = user_service.get_user_by_id(conn, user_id)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    return UserRead(**user.__dict__)


@router.put("/{user_id}", response_model=UserRead)
def update_user(
    user_id: int,
    payload: UserUpdate,
    conn: Database,
    current_user: User = Depends(require_permission("manage_users")),
) -> UserRead:
    user = user_service.update_user(conn, user_id, payload)
    if user is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    write_audit_log(conn, user_id=current_user.id, action="update", entity_type="user", entity_id=user.id)
    return UserRead(**user.__dict__)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_user(
    user_id: int,
    conn: Database,
    current_user: User = Depends(require_permission("manage_users")),
):
    if user_id == current_user.id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current user cannot delete itself")
    deleted = user_service.delete_user(conn, user_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="User not found")
    write_audit_log(conn, user_id=current_user.id, action="delete", entity_type="user", entity_id=user_id)
