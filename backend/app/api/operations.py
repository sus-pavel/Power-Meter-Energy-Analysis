from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Depends

from backend.app.api.deps import Database, require_permission
from backend.app.services.operations_service import (
    operational_devices,
    operations_status,
    recent_events,
    recent_measurements_summary,
)


router = APIRouter(prefix="/api/operations", tags=["operations"])


@router.get("/status")
def status(
    conn: Database,
    _: object = Depends(require_permission("view_dashboard")),
) -> dict[str, Any]:
    return operations_status(conn)


@router.get("/devices")
def devices(
    conn: Database,
    _: object = Depends(require_permission("view_dashboard")),
) -> list[dict[str, Any]]:
    return operational_devices(conn)


@router.get("/recent-measurements")
def recent_measurements(
    _: object = Depends(require_permission("view_dashboard")),
) -> dict[str, Any]:
    return recent_measurements_summary()


@router.get("/events")
def events(
    conn: Database,
    _: object = Depends(require_permission("view_dashboard")),
) -> list[dict[str, Any]]:
    return recent_events(conn)
