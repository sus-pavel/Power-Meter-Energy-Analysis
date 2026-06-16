from __future__ import annotations

from typing import Union

from fastapi import APIRouter

from backend.app.core.config import settings
from backend.app.core.database import database_status
from backend.app.core.desktop_paths import ensure_desktop_paths, resolve_desktop_paths


router = APIRouter(prefix="/api", tags=["health"])


@router.get("/health")
def health() -> dict[str, str]:
    return {
        "status": "ok",
        "app": settings.app_name,
        "mode": settings.app_mode,
        "database": database_status(),
    }


@router.get("/desktop/diagnostics")
def desktop_diagnostics() -> dict[str, Union[bool, int, str]]:
    paths = ensure_desktop_paths(resolve_desktop_paths()) if settings.desktop_mode else resolve_desktop_paths()
    return {
        "desktop_mode": settings.desktop_mode,
        "app_data_dir": str(paths.app_data_dir if settings.desktop_mode else settings.database_path.parent),
        "db_path": str(settings.database_path),
        "log_dir": str(paths.log_dir if settings.desktop_mode else settings.database_path.parent),
        "backend_port": settings.backend_port,
        "database_ok": database_status() == "ok",
    }
