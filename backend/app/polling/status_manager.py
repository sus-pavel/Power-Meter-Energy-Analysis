from __future__ import annotations

import sqlite3

from backend.app.services.audit_service import write_audit_log


def update_device_status(
    conn: sqlite3.Connection,
    *,
    device_id: int,
    status: str,
    error_message: str | None = None,
) -> None:
    previous = conn.execute(
        "SELECT status FROM device_status WHERE device_id = ?",
        (device_id,),
    ).fetchone()
    conn.execute(
        """
        INSERT INTO device_status (
            device_id, status, last_success_at, last_error_at, last_error_message, updated_at
        )
        VALUES (
            ?, ?,
            CASE WHEN ? = 'online' THEN CURRENT_TIMESTAMP ELSE NULL END,
            CASE WHEN ? != 'online' THEN CURRENT_TIMESTAMP ELSE NULL END,
            ?, CURRENT_TIMESTAMP
        )
        ON CONFLICT(device_id) DO UPDATE SET
            status = excluded.status,
            last_success_at = CASE
                WHEN excluded.status = 'online' THEN CURRENT_TIMESTAMP
                ELSE device_status.last_success_at
            END,
            last_error_at = CASE
                WHEN excluded.status != 'online' THEN CURRENT_TIMESTAMP
                ELSE device_status.last_error_at
            END,
            last_error_message = ?,
            updated_at = CURRENT_TIMESTAMP
        """,
        (device_id, status, status, status, error_message, error_message),
    )
    if previous is None or previous["status"] != status:
        action = {
            "online": "device_online",
            "offline": "device_offline",
            "timeout": "device_timeout",
            "error": "polling_failed",
            "disabled": "device_disabled",
        }.get(status, "polling_status_changed")
        write_audit_log(
            conn,
            user_id=None,
            action=action,
            entity_type="device",
            entity_id=device_id,
            details={"status": status, "error_message": error_message},
        )
