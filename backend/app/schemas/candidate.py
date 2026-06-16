from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class CandidateSummary(BaseModel):
    id: int
    ip_address: str
    port: int
    unit_id: int
    status: str
    device_type_guess: Optional[str]
    confidence_score: Optional[float]
    vendor_guess: Optional[str]
    updated_at: str


class CandidateProbeResultRead(BaseModel):
    id: int
    candidate_id: int
    register_address: int
    function_code: str
    data_type: str
    raw_value: Optional[str]
    decoded_value: Optional[float]
    valid: bool
    created_at: str


class CandidateDetails(CandidateSummary):
    scan_result_id: int
    notes: Optional[str]
    created_at: str
    probe_results: list[CandidateProbeResultRead]


class CandidateProbeResponse(BaseModel):
    candidate_id: int
    probe_status: str
    valid_registers_found: int
    device_type_guess: str
    confidence_score: float


class CandidatePromoteRequest(BaseModel):
    device_name: str = Field(min_length=1, max_length=160)
    location: Optional[str] = None
    description: Optional[str] = None


class CandidatePromoteResponse(BaseModel):
    candidate_id: int
    device_id: int
    status: str
    registers_created: int


class CandidateRejectResponse(BaseModel):
    candidate_id: int
    status: str
    message: str
