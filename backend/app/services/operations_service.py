from __future__ import annotations

import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from backend.app.core.config import settings
from backend.app.core.database import table_exists
from backend.app.polling.scheduler import polling_scheduler


ONLINE_WINDOW_SECONDS = 300


def _iso_from_unix(value: float | int | None) -> str | None:
    if value is None:
        return None
    return datetime.fromtimestamp(float(value), tz=timezone.utc).isoformat()


def _connect_if_exists(path: Path) -> sqlite3.Connection | None:
    if not path.exists():
        return None
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    return conn


def _measurement_db() -> sqlite3.Connection | None:
    for path in (settings.database_path, settings.prototype_database_path):
        conn = _connect_if_exists(path)
        if conn is None:
            continue
        if table_exists(conn, "measurements_raw") or table_exists(conn, "raw_data"):
            return conn
        conn.close()
    return None


def recent_measurements_summary() -> dict[str, Any]:
    conn = _measurement_db()
    if conn is None:
        return {
            "available": False,
            "message": "Measurement tables are not available in the application database yet.",
        }
    try:
        table_name = "measurements_raw" if table_exists(conn, "measurements_raw") else "raw_data"
        latest_ts = conn.execute(f"SELECT MAX(timestamp) FROM {table_name}").fetchone()[0]
        if latest_ts is None:
            return {
                "available": False,
                "message": "Measurement tables exist but contain no measurements yet.",
            }
        one_hour_ago = float(latest_ts) - 3600
        total_points = conn.execute(
            f"SELECT COUNT(*) FROM {table_name} WHERE timestamp >= ?",
            (one_hour_ago,),
        ).fetchone()[0]
        power_metric = "active_power_total" if table_name == "measurements_raw" else "active_power_avg"
        rows = conn.execute(
            f"""
            SELECT r.device_id, r.value
            FROM {table_name} r
            JOIN (
                SELECT device_id, MAX(timestamp) AS latest_ts
                FROM {table_name}
                WHERE metric = ?
                GROUP BY device_id
            ) latest
              ON latest.device_id = r.device_id
             AND latest.latest_ts = r.timestamp
            WHERE r.metric = ?
            """,
            (power_metric, power_metric),
        ).fetchall()
        total_power = round(sum(float(row["value"]) for row in rows), 3) if rows else None
        return {
            "available": True,
            "total_points_last_hour": total_points,
            "last_measurement_at": _iso_from_unix(latest_ts),
            "total_power_kw": total_power,
        }
    finally:
        conn.close()


def _last_seen_by_device() -> dict[str, dict[str, Any]]:
    conn = _measurement_db()
    if conn is None:
        return {}
    try:
        table_name = "measurements_raw" if table_exists(conn, "measurements_raw") else "raw_data"
        rows = conn.execute(
            f"""
            SELECT device_id, MAX(timestamp) AS last_seen_at
            FROM {table_name}
            GROUP BY device_id
            """,
        ).fetchall()
        return {
            str(row["device_id"]): {
                "timestamp": float(row["last_seen_at"]),
                "iso": _iso_from_unix(row["last_seen_at"]),
            }
            for row in rows
        }
    finally:
        conn.close()


def operational_devices(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    last_seen_map = _last_seen_by_device()
    now_ts = datetime.now(tz=timezone.utc).timestamp()
    rows = conn.execute(
        """
        SELECT d.*,
               ds.status AS status_row,
               ds.last_success_at,
               ds.last_error_at,
               ds.last_error_message,
               COALESCE(SUM(CASE WHEN r.enabled = 1 THEN 1 ELSE 0 END), 0) AS registers_enabled
        FROM devices d
        LEFT JOIN device_registers r ON r.device_id = d.id
        LEFT JOIN device_status ds ON ds.device_id = d.id
        GROUP BY d.id
        ORDER BY d.name
        """
    ).fetchall()
    devices: list[dict[str, Any]] = []
    for row in rows:
        keys = [str(row["id"]), row["name"], row["host"]]
        seen = next((last_seen_map[key] for key in keys if key in last_seen_map), None)
        enabled = bool(row["enabled"])
        registers_enabled = int(row["registers_enabled"] or 0)
        if not enabled:
            status = "disabled"
        elif row["status_row"]:
            status = row["status_row"]
        elif seen is None:
            status = "unknown"
        elif now_ts - seen["timestamp"] <= ONLINE_WINDOW_SECONDS:
            status = "online"
        else:
            status = "offline"
        if not enabled:
            readiness = "disabled"
        elif registers_enabled > 0:
            readiness = "ready"
        else:
            readiness = "no_registers"
        devices.append(
            {
                "id": row["id"],
                "name": row["name"],
                "host": row["host"],
                "port": row["port"],
                "unit_id": row["unit_id"],
                "enabled": enabled,
                "status": status,
                "last_seen_at": row["last_success_at"] or (seen["iso"] if seen else None),
                "last_error": row["last_error_message"],
                "registers_enabled": registers_enabled,
                "polling_readiness": readiness,
            }
        )
    return devices


def operations_status(conn: sqlite3.Connection) -> dict[str, Any]:
    devices = operational_devices(conn)
    measurement = recent_measurements_summary()
    pending_candidates = conn.execute(
        "SELECT COUNT(*) FROM discovered_candidates WHERE status IN ('discovered', 'reviewed')"
    ).fetchone()[0]
    active_scan_jobs = conn.execute(
        "SELECT COUNT(*) FROM scan_jobs WHERE status IN ('pending', 'running')"
    ).fetchone()[0]
    return {
        "configured_devices": len(devices),
        "enabled_devices": sum(1 for device in devices if device["enabled"]),
        "online_devices": sum(1 for device in devices if device["status"] == "online"),
        "offline_devices": sum(1 for device in devices if device["status"] == "offline"),
        "unknown_devices": sum(1 for device in devices if device["status"] == "unknown"),
        "active_scan_jobs": active_scan_jobs,
        "pending_candidates": pending_candidates,
        "recent_measurements_available": bool(measurement.get("available")),
        "last_measurement_at": measurement.get("last_measurement_at"),
        "polling_running": polling_scheduler.running,
        "measurements_last_hour": measurement.get("total_points_last_hour", 0) if measurement.get("available") else 0,
    }


def recent_events(conn: sqlite3.Connection) -> list[dict[str, Any]]:
    rows = conn.execute(
        """
        SELECT timestamp, action, entity_type, entity_id
        FROM audit_log
        ORDER BY id DESC
        LIMIT 25
        """
    ).fetchall()
    return [dict(row) for row in rows]
