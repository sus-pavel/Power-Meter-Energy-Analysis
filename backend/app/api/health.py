from __future__ import annotations

from fastapi import APIRouter

from backend.app.core.config import settings
from backend.app.core.database import database_status


router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "mode": settings.app_mode,
        "database": database_status(),
    }
