from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Depends

from backend.app.api.deps import Database, require_permission
from backend.app.core.config import settings
from backend.app.core.database import database_status, table_exists


router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


def _measurement_summary() -> dict[str, Any]:
    try:
        summaries: dict[str, Any] = {"available": False, "tables": {}}
        for path in (settings.database_path, settings.prototype_database_path):
            if not path.exists():
                continue
            with sqlite3.connect(path) as conn:
                for table_name in ("measurements_raw", "raw_data", "agg_5min", "agg_30min", "drpi_results"):
                    if table_exists(conn, table_name):
                        count = conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
                        summaries["available"] = True
                        summaries["tables"][table_name] = {"rows": count}
        if not summaries["available"]:
            summaries["message"] = "No measurement tables found."
        return summaries
    except sqlite3.Error:
        return {"available": False, "message": "Measurement database could not be read."}


@router.get("/summary")
def dashboard_summary(
    conn: Database,
    _: object = Depends(require_permission("view_dashboard")),
) -> dict[str, Any]:
    device_count = conn.execute("SELECT COUNT(*) FROM devices").fetchone()[0]
    enabled_device_count = conn.execute("SELECT COUNT(*) FROM devices WHERE enabled = 1").fetchone()[0]
    user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
    active_scan_jobs = conn.execute(
        "SELECT COUNT(*) FROM scan_jobs WHERE status IN ('pending', 'running')"
    ).fetchone()[0]
    discovered_candidates = conn.execute("SELECT COUNT(*) FROM discovered_candidates").fetchone()[0]
    promoted_devices = conn.execute(
        "SELECT COUNT(*) FROM discovered_candidates WHERE status = 'promoted'"
    ).fetchone()[0]
    pending_review = conn.execute(
        "SELECT COUNT(*) FROM discovered_candidates WHERE status IN ('discovered', 'reviewed')"
    ).fetchone()[0]
    return {
        "devices": device_count,
        "enabled_devices": enabled_device_count,
        "users": user_count,
        "active_scan_jobs": active_scan_jobs,
        "discovered_candidates": discovered_candidates,
        "promoted_devices": promoted_devices,
        "pending_review": pending_review,
        "mode": settings.app_mode,
        "database": database_status(),
        "measurement_summary": _measurement_summary(),
    }
