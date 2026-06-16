from __future__ import annotations

import asyncio
import logging

from backend.app.analytics.aggregation_service import aggregation_service
from backend.app.analytics.drpi_app_service import drpi_service
from backend.app.analytics.retention_service import retention_service


logger = logging.getLogger(__name__)


class AnalyticsManager:
    def __init__(self) -> None:
        self._tasks: list[asyncio.Task] = []

    @property
    def running(self) -> bool:
        return any(not task.done() for task in self._tasks)

    def start(self) -> None:
        if self.running:
            return
        self._tasks = [
            asyncio.create_task(aggregation_service.start()),
            asyncio.create_task(drpi_service.start()),
            asyncio.create_task(retention_service.start()),
        ]
        for task in self._tasks:
            task.add_done_callback(self._log_task_failure)

    async def stop(self) -> None:
        await aggregation_service.stop()
        await drpi_service.stop()
        await retention_service.stop()
        if self._tasks:
            for task in self._tasks:
                if not task.done():
                    task.cancel()
            await asyncio.gather(*self._tasks, return_exceptions=True)
        self._tasks = []

    @staticmethod
    def _log_task_failure(task: asyncio.Task) -> None:
        if task.cancelled():
            return
        exc = task.exception()
        if exc is not None:
            logger.exception("Analytics background service failed", exc_info=exc)


analytics_manager = AnalyticsManager()
