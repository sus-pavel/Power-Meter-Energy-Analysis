from __future__ import annotations

from dataclasses import dataclass

from backend.app.models.candidate import CandidateProbeResult, DiscoveredCandidate


SUPPORTED_DEVICE_GUESSES = {
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
    """Estimate a broad device class from safe probe evidence only."""
    valid_results = [result for result in probe_results if result.valid]
    if not valid_results:
        return FingerprintResult("unknown_modbus_device", 0.2)

    holding_count = sum(1 for result in valid_results if result.function_code == "holding")
    input_count = sum(1 for result in valid_results if result.function_code == "input")
    decoded_values = [result.decoded_value for result in valid_results if result.decoded_value is not None]
    plausible_energy_values = [
        value for value in decoded_values if -1_000_000.0 <= value <= 1_000_000.0
    ]

    if holding_count >= 2 and input_count >= 2 and len(plausible_energy_values) >= 4:
        return FingerprintResult("energy_analyzer", 0.78)
    if len(plausible_energy_values) >= 4:
        return FingerprintResult("power_meter", 0.72)
    if holding_count + input_count >= 2:
        return FingerprintResult("industrial_controller", 0.52)
    return FingerprintResult("unknown_modbus_device", 0.4)
