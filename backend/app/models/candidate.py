from __future__ import annotations

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class DiscoveredCandidate:
    id: int
    scan_result_id: int
    ip_address: str
    port: int
    unit_id: int
    status: str
    device_type_guess: Optional[str]
    confidence_score: Optional[float]
    vendor_guess: Optional[str]
    notes: Optional[str]
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class CandidateProbeResult:
    id: int
    candidate_id: int
    register_address: int
    function_code: str
    data_type: str
    raw_value: Optional[str]
    decoded_value: Optional[float]
    valid: bool
    created_at: str
