from __future__ import annotations

import asyncio
import ipaddress
import json
import logging
import sqlite3
import struct
import time
from dataclasses import dataclass
from typing import Iterable, Optional

from fastapi import HTTPException, status

from backend.app.core.config import settings
from backend.app.core.database import get_connection
from backend.app.models.discovery import ScanJob, ScanResult
from backend.app.schemas.discovery import ScanCreateRequest
from backend.app.services.audit_service import write_audit_log
from backend.app.services.candidate_service import create_candidates_from_scan_result


RUNNING_STATUSES = {"pending", "running"}
QUICK_UNIT_IDS = [0, 1, 2, 3, 4, 5, 10, 16, 17, 20, 100, 247, 255]
EXTENDED_UNIT_IDS = list(range(0, 33)) + [100, 101, 247, 255]
FULL_UNIT_IDS = list(range(1, 248))

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class HostScanOutcome:
    ip_address: str
    tcp_open: bool
    modbus_responding: bool
    response_time_ms: Optional[float]
    candidate_unit_ids: list[int]


def row_to_scan_job(row: sqlite3.Row) -> ScanJob:
    return ScanJob(
        id=row["id"],
        created_at=row["created_at"],
        started_at=row["started_at"],
        finished_at=row["finished_at"],
        created_by_user_id=row["created_by_user_id"],
        status=row["status"],
        ip_start=row["ip_start"],
        ip_end=row["ip_end"],
        total_hosts=row["total_hosts"],
        processed_hosts=row["processed_hosts"],
        found_hosts=row["found_hosts"],
        unit_id_scan_mode=row["unit_id_scan_mode"],
        unit_ids=json.loads(row["unit_ids_json"] or "[]"),
        timeout_seconds=row["timeout_seconds"],
        max_concurrent_hosts=row["max_concurrent_hosts"],
        error_message=row["error_message"],
    )


def row_to_scan_result(row: sqlite3.Row) -> ScanResult:
    return ScanResult(
        id=row["id"],
        job_id=row["job_id"],
        ip_address=row["ip_address"],
        port=row["port"],
        tcp_open=bool(row["tcp_open"]),
        modbus_responding=bool(row["modbus_responding"]),
        response_time_ms=row["response_time_ms"],
        candidate_unit_ids=json.loads(row["candidate_unit_ids"] or "[]"),
        last_checked_at=row["last_checked_at"],
        created_at=row["created_at"],
    )


def progress_percent(job: ScanJob) -> float:
    if job.total_hosts <= 0:
        return 0.0
    return round((job.processed_hosts / job.total_hosts) * 100, 1)


def validate_ip_range(payload: ScanCreateRequest) -> tuple[ipaddress.IPv4Address, ipaddress.IPv4Address, int]:
    try:
        ip_start = ipaddress.ip_address(payload.ip_start)
        ip_end = ipaddress.ip_address(payload.ip_end)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid IP address") from exc

    if ip_start.version != 4 or ip_end.version != 4:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Only IPv4 discovery is supported")
    if int(ip_start) > int(ip_end):
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="ip_start must be <= ip_end")

    total_hosts = int(ip_end) - int(ip_start) + 1
    if total_hosts > settings.discovery_max_hosts_per_scan:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Scan range is limited to {settings.discovery_max_hosts_per_scan} hosts",
        )
    return ip_start, ip_end, total_hosts


def iter_ip_range(ip_start: str, ip_end: str) -> Iterable[str]:
    start = ipaddress.ip_address(ip_start)
    end = ipaddress.ip_address(ip_end)
    for value in range(int(start), int(end) + 1):
        yield str(ipaddress.ip_address(value))


def normalize_unit_ids(unit_ids: Iterable[int]) -> list[int]:
    normalized: set[int] = set()
    for value in unit_ids:
        unit_id = int(value)
        if unit_id < 0 or unit_id > 255:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="Unit IDs must be between 0 and 255",
            )
        normalized.add(unit_id)
    return sorted(normalized)


def resolve_unit_ids_for_scan(payload: ScanCreateRequest, total_hosts: int) -> list[int]:
    if payload.unit_id_scan_mode == "quick":
        unit_ids = normalize_unit_ids(settings.discovery_quick_unit_ids or QUICK_UNIT_IDS)
    elif payload.unit_id_scan_mode == "extended":
        unit_ids = normalize_unit_ids(settings.discovery_extended_unit_ids or EXTENDED_UNIT_IDS)
    elif payload.unit_id_scan_mode == "full":
        if total_hosts > settings.discovery_full_scan_max_hosts:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=(
                    "Full Unit ID scan is limited to "
                    f"{settings.discovery_full_scan_max_hosts} hosts"
                ),
            )
        unit_ids = normalize_unit_ids(FULL_UNIT_IDS)
    elif payload.unit_id_scan_mode == "custom":
        if not payload.unit_ids:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="unit_ids is required for custom Unit ID scan mode",
            )
        unit_ids = normalize_unit_ids(payload.unit_ids)
    else:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Unsupported Unit ID scan mode",
        )

    if not unit_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="At least one Unit ID is required",
        )

    total_unit_id_probes = total_hosts * len(unit_ids)
    # Extended mode is an explicit operator-selected broader scan and is still bounded by host range limits.
    if total_unit_id_probes > settings.discovery_max_unit_ids_per_scan and payload.unit_id_scan_mode != "extended":
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=(
                "Discovery scan is limited to "
                f"{settings.discovery_max_unit_ids_per_scan} host/Unit ID combinations"
            ),
        )
    return unit_ids


def resolve_timeout_seconds(payload: ScanCreateRequest) -> float:
    return payload.timeout_seconds or settings.discovery_default_timeout_seconds


def resolve_max_concurrent_hosts(payload: ScanCreateRequest) -> int:
    max_concurrent_hosts = payload.max_concurrent_hosts or settings.discovery_real_network_max_concurrent_hosts
    if max_concurrent_hosts > settings.discovery_max_concurrent_hosts:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"max_concurrent_hosts is limited to {settings.discovery_max_concurrent_hosts}",
        )
    return max_concurrent_hosts


def create_scan_job(conn: sqlite3.Connection, payload: ScanCreateRequest, user_id: int) -> ScanJob:
    ip_start, ip_end, total_hosts = validate_ip_range(payload)
    unit_ids = resolve_unit_ids_for_scan(payload, total_hosts)
    timeout_seconds = resolve_timeout_seconds(payload)
    max_concurrent_hosts = resolve_max_concurrent_hosts(payload)
    cursor = conn.execute(
        """
        INSERT INTO scan_jobs (
            created_by_user_id,
            status,
            ip_start,
            ip_end,
            total_hosts,
            unit_id_scan_mode,
            unit_ids_json,
            timeout_seconds,
            max_concurrent_hosts
        )
        VALUES (?, 'pending', ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            user_id,
            str(ip_start),
            str(ip_end),
            total_hosts,
            payload.unit_id_scan_mode,
            json.dumps(unit_ids),
            timeout_seconds,
            max_concurrent_hosts,
        ),
    )
    job = get_scan_job(conn, cursor.lastrowid)
    if job is None:
        raise RuntimeError("Scan job was not created")
    return job


def get_scan_job(conn: sqlite3.Connection, job_id: int) -> Optional[ScanJob]:
    row = conn.execute("SELECT * FROM scan_jobs WHERE id = ?", (job_id,)).fetchone()
    return row_to_scan_job(row) if row else None


def list_scan_jobs(conn: sqlite3.Connection) -> list[ScanJob]:
    rows = conn.execute("SELECT * FROM scan_jobs ORDER BY id DESC").fetchall()
    return [row_to_scan_job(row) for row in rows]


def list_scan_results(conn: sqlite3.Connection, job_id: int) -> list[ScanResult]:
    rows = conn.execute(
        "SELECT * FROM scan_results WHERE job_id = ? ORDER BY ip_address",
        (job_id,),
    ).fetchall()
    return [row_to_scan_result(row) for row in rows]


def mark_job_cancelled(conn: sqlite3.Connection, job_id: int) -> Optional[ScanJob]:
    job = get_scan_job(conn, job_id)
    if job is None:
        return None
    if job.status in {"completed", "failed", "cancelled"}:
        return job
    conn.execute(
        """
        UPDATE scan_jobs
        SET status = 'cancelled', finished_at = CURRENT_TIMESTAMP
        WHERE id = ?
        """,
        (job_id,),
    )
    return get_scan_job(conn, job_id)


def _set_job_running(conn: sqlite3.Connection, job_id: int) -> None:
    conn.execute(
        """
        UPDATE scan_jobs
        SET status = 'running', started_at = COALESCE(started_at, CURRENT_TIMESTAMP)
        WHERE id = ? AND status = 'pending'
        """,
        (job_id,),
    )


def _finish_job(conn: sqlite3.Connection, job_id: int, status_value: str, error_message: Optional[str] = None) -> None:
    conn.execute(
        """
        UPDATE scan_jobs
        SET status = ?, finished_at = CURRENT_TIMESTAMP, error_message = ?
        WHERE id = ?
        """,
        (status_value, error_message, job_id),
    )


def _increment_progress(conn: sqlite3.Connection, job_id: int, found: bool) -> None:
    conn.execute(
        """
        UPDATE scan_jobs
        SET processed_hosts = processed_hosts + 1,
            found_hosts = found_hosts + ?
        WHERE id = ?
        """,
        (1 if found else 0, job_id),
    )


def _store_result(conn: sqlite3.Connection, job_id: int, outcome: HostScanOutcome) -> None:
    cursor = conn.execute(
        """
        INSERT INTO scan_results (
            job_id,
            ip_address,
            port,
            tcp_open,
            modbus_responding,
            response_time_ms,
            candidate_unit_ids,
            last_checked_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        """,
        (
            job_id,
            outcome.ip_address,
            settings.discovery_port,
            int(outcome.tcp_open),
            int(outcome.modbus_responding),
            outcome.response_time_ms,
            json.dumps(outcome.candidate_unit_ids),
        ),
    )
    if outcome.modbus_responding:
        create_candidates_from_scan_result(
            conn,
            scan_result_id=cursor.lastrowid,
            ip_address=outcome.ip_address,
            port=settings.discovery_port,
            unit_ids=outcome.candidate_unit_ids,
        )


async def _tcp_port_open(ip_address: str, timeout_seconds: float) -> bool:
    writer: Optional[asyncio.StreamWriter] = None
    try:
        _, writer = await asyncio.wait_for(
            asyncio.open_connection(ip_address, settings.discovery_port),
            timeout=timeout_seconds,
        )
        return True
    except (OSError, asyncio.TimeoutError):
        return False
    finally:
        if writer is not None:
            writer.close()
            await writer.wait_closed()


async def _send_modbus_request(
    ip_address: str,
    unit_id: int,
    function_code: int,
    payload: bytes,
    timeout_seconds: float,
) -> tuple[bool, str | None]:
    writer: Optional[asyncio.StreamWriter] = None
    transaction_id = (int(time.monotonic() * 1000) + unit_id + function_code) % 65535 or 1
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(ip_address, settings.discovery_port),
            timeout=timeout_seconds,
        )
        pdu = bytes([function_code]) + payload
        mbap = struct.pack(">HHHB", transaction_id, 0, len(pdu) + 1, unit_id)
        writer.write(mbap + pdu)
        await asyncio.wait_for(writer.drain(), timeout=timeout_seconds)

        header = await asyncio.wait_for(reader.readexactly(7), timeout=timeout_seconds)
        response_tid, protocol_id, length, response_unit = struct.unpack(">HHHB", header)
        if response_tid != transaction_id:
            return False, "transaction_id_mismatch"
        if protocol_id != 0:
            return False, "invalid_protocol_id"
        if response_unit != unit_id:
            return False, "unit_id_mismatch"
        if length < 2:
            return False, "invalid_mbap_length"

        pdu_response = await asyncio.wait_for(reader.readexactly(length - 1), timeout=timeout_seconds)
        if not pdu_response:
            return False, "empty_pdu_response"
        response_function_code = pdu_response[0]
        if response_function_code == function_code:
            return True, "normal_response"
        if response_function_code == (function_code | 0x80):
            return True, "exception_response"
        return False, f"unexpected_function_code_{response_function_code:#04x}"
    except (OSError, asyncio.IncompleteReadError, asyncio.TimeoutError, struct.error):
        return False, None
    finally:
        if writer is not None:
            writer.close()
            await writer.wait_closed()


async def _modbus_unit_responds(ip_address: str, unit_id: int, timeout_seconds: float) -> bool:
    probes = (
        (0x2B, bytes([0x0E, 0x01, 0x00]), "fc43_read_device_identification"),
        (0x03, struct.pack(">HH", 0, 1), "fc03_holding_register_0"),
        (0x04, struct.pack(">HH", 0, 1), "fc04_input_register_0"),
    )
    diagnostics: list[str] = []
    for function_code, payload, label in probes:
        responding, diagnostic = await _send_modbus_request(
            ip_address=ip_address,
            unit_id=unit_id,
            function_code=function_code,
            payload=payload,
            timeout_seconds=timeout_seconds,
        )
        if responding:
            if diagnostic:
                logger.debug(
                    "Modbus Unit ID responded: ip=%s unit_id=%s probe=%s diagnostic=%s",
                    ip_address,
                    unit_id,
                    label,
                    diagnostic,
                )
            return True
        if diagnostic:
            diagnostics.append(f"{label}:{diagnostic}")

    if diagnostics:
        logger.debug(
            "Modbus Unit ID probe failed: ip=%s unit_id=%s diagnostics=%s",
            ip_address,
            unit_id,
            diagnostics,
        )
    return False


async def scan_host(
    ip_address: str,
    unit_ids: list[int],
    timeout_seconds: float,
    cancel_event: asyncio.Event,
) -> HostScanOutcome:
    if cancel_event.is_set():
        return HostScanOutcome(ip_address, False, False, None, [])

    started = time.perf_counter()
    tcp_open = await _tcp_port_open(ip_address, timeout_seconds)
    if not tcp_open or cancel_event.is_set():
        return HostScanOutcome(ip_address, tcp_open, False, None, [])

    candidate_unit_ids: list[int] = []
    for unit_id in unit_ids:
        if cancel_event.is_set():
            break
        if await _modbus_unit_responds(ip_address, unit_id, timeout_seconds):
            candidate_unit_ids.append(unit_id)

    elapsed_ms = round((time.perf_counter() - started) * 1000, 2) if candidate_unit_ids else None
    return HostScanOutcome(
        ip_address=ip_address,
        tcp_open=True,
        modbus_responding=bool(candidate_unit_ids),
        response_time_ms=elapsed_ms,
        candidate_unit_ids=candidate_unit_ids,
    )


class DiscoveryRuntime:
    def __init__(self) -> None:
        self._cancel_events: dict[int, asyncio.Event] = {}
        self._tasks: dict[int, asyncio.Task] = {}

    def start(self, job_id: int, user_id: int) -> None:
        cancel_event = asyncio.Event()
        self._cancel_events[job_id] = cancel_event
        self._tasks[job_id] = asyncio.create_task(self._run_job(job_id, user_id, cancel_event))

    def cancel(self, job_id: int) -> None:
        event = self._cancel_events.get(job_id)
        if event is not None:
            event.set()

    async def _run_job(self, job_id: int, user_id: int, cancel_event: asyncio.Event) -> None:
        final_status = "completed"
        error_message: Optional[str] = None
        try:
            with get_connection() as conn:
                _set_job_running(conn, job_id)
                job = get_scan_job(conn, job_id)
                if job is None:
                    return
                unit_ids = job.unit_ids
                timeout_seconds = job.timeout_seconds or settings.discovery_default_timeout_seconds
                max_concurrent_hosts = (
                    job.max_concurrent_hosts
                    or settings.discovery_real_network_max_concurrent_hosts
                )

            queue: asyncio.Queue[str] = asyncio.Queue()
            for ip_address in iter_ip_range(job.ip_start, job.ip_end):
                queue.put_nowait(ip_address)

            async def worker() -> None:
                while not cancel_event.is_set():
                    try:
                        ip_address = queue.get_nowait()
                    except asyncio.QueueEmpty:
                        return
                    try:
                        outcome = await scan_host(ip_address, unit_ids, timeout_seconds, cancel_event)
                        if cancel_event.is_set():
                            return
                        with get_connection() as conn:
                            _store_result(conn, job_id, outcome)
                            _increment_progress(conn, job_id, outcome.modbus_responding)
                    finally:
                        queue.task_done()

            workers = [
                asyncio.create_task(worker())
                for _ in range(min(max_concurrent_hosts, job.total_hosts))
            ]
            await asyncio.gather(*workers)

            if cancel_event.is_set():
                final_status = "cancelled"
        except Exception as exc:
            final_status = "failed"
            error_message = str(exc)
        finally:
            with get_connection() as conn:
                current_job = get_scan_job(conn, job_id)
                if current_job and current_job.status == "cancelled":
                    final_status = "cancelled"
                _finish_job(conn, job_id, final_status, error_message)
                write_audit_log(
                    conn,
                    user_id=user_id,
                    action="scan_completed" if final_status == "completed" else f"scan_{final_status}",
                    entity_type="scan_job",
                    entity_id=job_id,
                    details={"status": final_status, "error_message": error_message},
                )
            self._cancel_events.pop(job_id, None)
            self._tasks.pop(job_id, None)


discovery_runtime = DiscoveryRuntime()
