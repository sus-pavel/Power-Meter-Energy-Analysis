from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuditLogEntry:
    id: int
    timestamp: str
    user_id: int | None
    action: str
    entity_type: str
    entity_id: int | None
    details_json: str | None
