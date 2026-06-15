from __future__ import annotations

from backend.app.models.device import Device
from backend.app.schemas.device import ProbeResponse


def probe_device_placeholder(device: Device) -> ProbeResponse:
    """Stage 1 intentionally avoids network access and only exposes the future contract."""
    return ProbeResponse(
        device_id=device.id,
        status="not_implemented",
        message="Modbus register probing will be implemented in Stage 2.",
    )
