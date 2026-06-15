from __future__ import annotations

import json
import sqlite3
from typing import Any


def write_audit_log(
    conn: sqlite3.Connection,
    *,
    user_id: int | None,
    action: str,
    entity_type: str,
    entity_id: int | None,
    details: dict[str, Any] | None = None,
) -> None:
    conn.execute(
        """
        INSERT INTO audit_log (user_id, action, entity_type, entity_id, details_json)
        VALUES (?, ?, ?, ?, ?)
        """,
        (
            user_id,
            action,
            entity_type,
            entity_id,
            json.dumps(details or {}, ensure_ascii=False),
        ),
    )
