from __future__ import annotations

from dataclasses import dataclass

from backend.app.models.candidate import CandidateProbeResult, DiscoveredCandidate


SUPPORTED_DEVICE_GUESSES = {
    "configured_modbus_device",
    "identified_modbus_device",
    "power_meter",
    "power_quality_meter",
    "energy_analyzer",
    "plc",
    "industrial_controller",
    "unknown_modbus_device",
}


@dataclass(frozen=True)
class FingerprintResult:
    device_type_guess: str
    confidence_score: float
    vendor_guess: str = "unknown"


def fingerprint_candidate(
    candidate: DiscoveredCandidate,
    probe_results: list[CandidateProbeResult],
) -> FingerprintResult:
    """Summarize probe evidence without promoting guessed registers to confirmed configuration."""
    vendor_guess = candidate.vendor_name or candidate.vendor_guess or "unknown"
    config_validated = [result for result in probe_results if result.valid and result.validated_from_config]
    if config_validated:
        return FingerprintResult("configured_modbus_device", 0.9, vendor_guess)

    if candidate.vendor_identification_supported:
        return FingerprintResult("identified_modbus_device", 0.55, vendor_guess)

    if candidate.probe_profile_source == "vendor_default":
        return FingerprintResult("unknown_modbus_device", 0.45, vendor_guess)

    return FingerprintResult("unknown_modbus_device", 0.25, vendor_guess)
