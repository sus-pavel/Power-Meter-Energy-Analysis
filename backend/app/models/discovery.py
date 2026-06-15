from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class ScanJob:
    id: int
    created_at: str
    started_at: Optional[str]
    finished_at: Optional[str]
    created_by_user_id: Optional[int]
    status: str
    ip_start: str
    ip_end: str
    total_hosts: int
    processed_hosts: int
    found_hosts: int
    error_message: Optional[str]


@dataclass(frozen=True)
class ScanResult:
    id: int
    job_id: int
    ip_address: str
    port: int
    tcp_open: bool
    modbus_responding: bool
    response_time_ms: Optional[float]
    candidate_unit_ids: list[int]
    last_checked_at: str
    created_at: str
