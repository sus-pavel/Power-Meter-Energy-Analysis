from __future__ import annotations

import sqlite3
from typing import Any

from fastapi import APIRouter, Depends

from backend.app.analytics.aggregation_service import AGGREGATION_TABLES, aggregation_service
from backend.app.analytics.drpi_app_service import drpi_service
from backend.app.analytics.manager import analytics_manager
from backend.app.analytics.retention_service import retention_service
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
    latest_power = conn.execute(
        """
        SELECT SUM(value) AS total_power
        FROM measurements_raw r
        JOIN (
            SELECT device_id, MAX(timestamp) AS latest_ts
            FROM measurements_raw
            WHERE metric = ?
            GROUP BY device_id
        ) latest
          ON latest.device_id = r.device_id
         AND latest.latest_ts = r.timestamp
        WHERE r.metric = ?
        """,
        (settings.analytics_metric_name, settings.analytics_metric_name),
    ).fetchone()["total_power"]
    latest_drpi = conn.execute(
        "SELECT DRPI FROM app_drpi_results WHERE source_id = 'TOTAL' ORDER BY ts DESC LIMIT 1"
    ).fetchone()
    aggregation_counts = {
        key: conn.execute(f"SELECT COUNT(*) FROM {table_name}").fetchone()[0]
        for key, table_name in AGGREGATION_TABLES.items()
    }
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
        "latest_total_power": float(latest_power) if latest_power is not None else None,
        "latest_drpi_total": float(latest_drpi["DRPI"]) if latest_drpi else None,
        "analytics_service_status": {
            "running": analytics_manager.running,
            "aggregation": aggregation_service.running,
            "drpi": drpi_service.running,
            "retention": retention_service.running,
        },
        "aggregation_status": aggregation_counts,
    }
