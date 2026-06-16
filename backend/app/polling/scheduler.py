from __future__ import annotations

import asyncio
import time
from typing import Optional

from backend.app.core.config import settings
from backend.app.core.database import get_connection
from backend.app.models.device import Device
from backend.app.polling.status_manager import update_device_status
from backend.app.polling.worker import poll_device
from backend.app.services.audit_service import write_audit_log
from backend.app.services.device_service import list_devices


class PollingScheduler:
    def __init__(self) -> None:
        self._running = False
        self._task: Optional[asyncio.Task] = None
        self._semaphore = asyncio.Semaphore(settings.polling_max_parallel_devices)
        self._active_workers = 0
        self._worker_tasks: set[asyncio.Task] = set()

    @property
    def running(self) -> bool:
        return self._running

    @property
    def active_workers(self) -> int:
        return self._active_workers

    def start(self, user_id: int | None = None) -> None:
        if self._running:
            return
        self._running = True
        with get_connection() as conn:
            write_audit_log(conn, user_id=user_id, action="polling_started", entity_type="polling", entity_id=None)
        self._task = asyncio.create_task(self._run())

    async def stop(self, user_id: int | None = None) -> None:
        if not self._running:
            return
        self._running = False
        if self._task is not None:
            await self._task
        with get_connection() as conn:
            write_audit_log(conn, user_id=user_id, action="polling_stopped", entity_type="polling", entity_id=None)

    async def _run(self) -> None:
        while self._running:
            self._cleanup_workers()
            with get_connection() as conn:
                devices = list_devices(conn)
                self._sync_jobs(conn, devices)
                due_devices = self._due_devices(conn, devices)
            for device in due_devices:
                if not self._running:
                    break
                if any(not task.done() and getattr(task, "device_id", None) == device.id for task in self._worker_tasks):
                    continue
                task = asyncio.create_task(self._run_worker(device))
                setattr(task, "device_id", device.id)
                self._worker_tasks.add(task)
            await asyncio.sleep(settings.polling_loop_interval_sec)
        if self._worker_tasks:
            await asyncio.gather(*self._worker_tasks, return_exceptions=True)
            self._cleanup_workers()

    def _cleanup_workers(self) -> None:
        self._worker_tasks = {task for task in self._worker_tasks if not task.done()}

    def _sync_jobs(self, conn, devices: list[Device]) -> None:
        now = time.time()
        for device in devices:
            status = "pending" if device.enabled else "disabled"
            conn.execute(
                """
                INSERT INTO polling_jobs (device_id, status, poll_interval_sec, next_run_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(device_id) DO UPDATE SET
                    status = CASE
                        WHEN excluded.status = 'disabled' THEN 'disabled'
                        WHEN polling_jobs.status = 'disabled' THEN 'pending'
                        ELSE polling_jobs.status
                    END,
                    poll_interval_sec = excluded.poll_interval_sec,
                    next_run_at = COALESCE(polling_jobs.next_run_at, excluded.next_run_at),
                    updated_at = CURRENT_TIMESTAMP
                """,
                (device.id, status, device.poll_interval_sec, now),
            )
            if not device.enabled:
                update_device_status(conn, device_id=device.id, status="disabled")

    def _due_devices(self, conn, devices: list[Device]) -> list[Device]:
        now = time.time()
        by_id = {device.id: device for device in devices if device.enabled}
        rows = conn.execute(
            """
            SELECT device_id
            FROM polling_jobs
            WHERE status IN ('pending', 'failed')
              AND next_run_at <= ?
            ORDER BY next_run_at
            LIMIT ?
            """,
            (now, settings.polling_max_parallel_devices),
        ).fetchall()
        return [by_id[row["device_id"]] for row in rows if row["device_id"] in by_id]

    async def _run_worker(self, device: Device) -> None:
        async with self._semaphore:
            self._active_workers += 1
            try:
                with get_connection() as conn:
                    conn.execute(
                        "UPDATE polling_jobs SET status = 'running', last_run_at = CURRENT_TIMESTAMP, updated_at = CURRENT_TIMESTAMP WHERE device_id = ?",
                        (device.id,),
                    )
                await poll_device(device)
                with get_connection() as conn:
                    conn.execute(
                        """
                        UPDATE polling_jobs
                        SET status = 'pending',
                            next_run_at = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE device_id = ?
                        """,
                        (time.time() + device.poll_interval_sec, device.id),
                    )
            except Exception as exc:
                with get_connection() as conn:
                    conn.execute(
                        """
                        UPDATE polling_jobs
                        SET status = 'failed',
                            next_run_at = ?,
                            updated_at = CURRENT_TIMESTAMP
                        WHERE device_id = ?
                        """,
                        (time.time() + device.poll_interval_sec, device.id),
                    )
                    update_device_status(conn, device_id=device.id, status="error", error_message=str(exc))
            finally:
                self._active_workers -= 1


polling_scheduler = PollingScheduler()
