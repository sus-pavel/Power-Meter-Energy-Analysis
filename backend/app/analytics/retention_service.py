from __future__ import annotations

import asyncio
import logging
import time

from backend.app.analytics.aggregation_service import AGGREGATION_TABLES
from backend.app.core.config import settings
from backend.app.core.database import get_connection
from backend.app.services.audit_service import write_audit_log


logger = logging.getLogger(__name__)


class RetentionService:
    def __init__(self) -> None:
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    def run_once(self) -> dict[str, int]:
        now = time.time()
        raw_threshold = now - settings.raw_retention_days * 86400
        agg_threshold = now - settings.agg_retention_days * 86400
        deleted: dict[str, int] = {}
        with get_connection() as conn:
            before = conn.total_changes
            conn.execute("DELETE FROM measurements_raw WHERE timestamp < ?", (raw_threshold,))
            deleted["measurements_raw"] = conn.total_changes - before
            for table_name in AGGREGATION_TABLES.values():
                before = conn.total_changes
                conn.execute(f"DELETE FROM {table_name} WHERE window_end < ?", (agg_threshold,))
                deleted[table_name] = conn.total_changes - before
            if any(deleted.values()):
                write_audit_log(
                    conn,
                    user_id=None,
                    action="retention_cleanup_completed",
                    entity_type="analytics",
                    entity_id=None,
                    details=deleted,
                )
        return deleted

    async def start(self) -> None:
        self._running = True
        while self._running:
            try:
                await asyncio.to_thread(self.run_once)
            except Exception:
                logger.exception("Retention cycle failed")
            await asyncio.sleep(settings.retention_poll_interval_sec)

    async def stop(self) -> None:
        self._running = False


retention_service = RetentionService()
