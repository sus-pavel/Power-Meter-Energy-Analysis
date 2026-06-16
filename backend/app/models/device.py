from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Device:
    id: int
    name: str
    host: str
    port: int
    unit_id: int
    description: str | None
    location: str | None
    enabled: bool
    poll_interval_sec: int
    vendor_name: str | None
    product_code: str | None
    product_name: str | None
    model_name: str | None
    firmware_revision: str | None
    device_identification_raw: str | None
    probe_profile_id: str | None
    probe_profile_source: str | None
    created_at: str
    updated_at: str


@dataclass(frozen=True)
class DeviceRegister:
    id: int
    device_id: int
    metric: str
    function_code: str
    address: int
    data_type: str
    scale: float
    unit: str | None
    description: str | None
    enabled: bool
    created_at: str
    updated_at: str
