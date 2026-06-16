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
    vendor_name: Optional[str]
    product_code: Optional[str]
    product_name: Optional[str]
    model_name: Optional[str]
    firmware_revision: Optional[str]
    device_identification_raw: Optional[str]
    vendor_identification_supported: bool
    vendor_identification_error: Optional[str]
    probe_profile_id: Optional[str]
    probe_profile_source: Optional[str]
    probe_quality: Optional[str]
    probe_status: Optional[str]
    probe_summary_json: Optional[str]
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
    metric: Optional[str]
    scale: float
    unit: Optional[str]
    quality: str
    status: str
    source: str
    tested_json: str
    inferred_json: str
    failure_reason: Optional[str]
    exception_code: Optional[int]
    response_time_ms: Optional[float]
    validated_from_config: bool
    probe_profile_id: Optional[str]
    probe_profile_source: Optional[str]
    created_at: str
