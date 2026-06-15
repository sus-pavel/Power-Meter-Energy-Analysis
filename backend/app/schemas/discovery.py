from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class ScanCreateRequest(BaseModel):
    ip_start: str = Field(min_length=1, max_length=45)
    ip_end: str = Field(min_length=1, max_length=45)


class ScanCreateResponse(BaseModel):
    job_id: int
    status: str


class ScanJobRead(BaseModel):
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
    progress_percent: float


class ScanResultRead(BaseModel):
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


class ScanCancelResponse(BaseModel):
    job_id: int
    status: str
    message: str
