from __future__ import annotations

from typing import Literal, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


UnitIdScanMode = Literal["quick", "extended", "full", "custom"]


class ScanCreateRequest(BaseModel):
    ip_start: str = Field(min_length=1, max_length=45)
    ip_end: str = Field(min_length=1, max_length=45)
    unit_id_scan_mode: UnitIdScanMode = "quick"
    unit_ids: Optional[list[int]] = None
    timeout_seconds: Optional[float] = Field(default=None, ge=0.5, le=10.0)
    max_concurrent_hosts: Optional[int] = Field(default=None, ge=1)

    @field_validator("unit_ids")
    @classmethod
    def validate_unit_ids(cls, value: Optional[list[int]]) -> Optional[list[int]]:
        if value is None:
            return None
        for unit_id in value:
            if unit_id < 0 or unit_id > 255:
                raise ValueError("Unit IDs must be between 0 and 255")
        return value

    @model_validator(mode="after")
    def validate_custom_unit_ids(self) -> "ScanCreateRequest":
        if self.unit_id_scan_mode == "custom" and not self.unit_ids:
            raise ValueError("unit_ids is required for custom Unit ID scan mode")
        return self


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
    unit_id_scan_mode: str
    unit_ids: list[int]
    timeout_seconds: Optional[float]
    max_concurrent_hosts: Optional[int]
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
