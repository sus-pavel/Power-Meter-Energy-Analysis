from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends

from backend.app.api.deps import Database, require_permission
from backend.app.models.user import User
from backend.app.polling.scheduler import polling_scheduler


router = APIRouter(prefix="/api/polling", tags=["polling"])


def _measurements_last_hour(conn: Database) -> int:
    one_hour_ago = datetime.now(tz=timezone.utc).timestamp() - 3600
    return conn.execute(
        "SELECT COUNT(*) FROM measurements_raw WHERE timestamp >= ?",
        (one_hour_ago,),
    ).fetchone()[0]


@router.get("/status")
def polling_status(
    conn: Database,
    _: object = Depends(require_permission("view_dashboard")),
) -> dict[str, Any]:
    enabled_devices = conn.execute("SELECT COUNT(*) FROM devices WHERE enabled = 1").fetchone()[0]
    return {
        "running": polling_scheduler.running,
        "enabled_devices": enabled_devices,
        "active_workers": polling_scheduler.active_workers,
        "measurements_last_hour": _measurements_last_hour(conn),
    }


@router.post("/start")
async def start_polling(
    current_user: User = Depends(require_permission("manage_polling")),
) -> dict[str, bool]:
    polling_scheduler.start(user_id=current_user.id)
    return {"running": polling_scheduler.running}


@router.post("/stop")
async def stop_polling(
    current_user: User = Depends(require_permission("manage_polling")),
) -> dict[str, bool]:
    await polling_scheduler.stop(user_id=current_user.id)
    return {"running": polling_scheduler.running}
