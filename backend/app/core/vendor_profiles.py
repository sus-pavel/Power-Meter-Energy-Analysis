from __future__ import annotations

from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class VendorProfile:
    vendor_key: str
    vendor_name: str
    known_model_patterns: tuple[str, ...]
    default_port: int = 502
    default_unit_ids: tuple[int, ...] = (1,)
    default_register_profiles: tuple[dict[str, Any], ...] = ()
    supported_function_codes: tuple[str, ...] = ("holding", "input")
    byte_order: str = "big"
    word_order: str = "normal"
    scaling_conventions: tuple[str, ...] = ()
    required_registers: tuple[dict[str, Any], ...] = ()
    optional_registers: tuple[dict[str, Any], ...] = ()
    validation_registers: tuple[dict[str, Any], ...] = ()
    needs_verification: bool = True
    notes: str = "Placeholder profile. Add verified registers only after hardware validation."


VENDOR_PROFILES: tuple[VendorProfile, ...] = (
    VendorProfile("schneider_electric", "Schneider Electric", ("schneider", "powerlogic", "pm")),
    VendorProfile("siemens", "Siemens", ("siemens", "sentron", "pac")),
    VendorProfile("abb", "ABB", ("abb",)),
    VendorProfile("janitza", "Janitza", ("janitza", "umg")),
    VendorProfile("socomec", "Socomec", ("socomec", "diris")),
    VendorProfile("lovato", "Lovato", ("lovato", "dmG".lower())),
    VendorProfile("carlo_gavazzi", "Carlo Gavazzi", ("carlo gavazzi", "gavazzi")),
    VendorProfile("iskra", "Iskra", ("iskra",)),
    VendorProfile("phoenix_contact", "Phoenix Contact", ("phoenix contact",)),
    VendorProfile("wago", "WAGO", ("wago",)),
    VendorProfile("generic_modbus_meter", "Generic Modbus meter", ("modbus", "meter")),
)


def _normalize(value: str | None) -> str:
    return (value or "").strip().lower()


def match_vendor_profile(identity_fields: dict[str, str]) -> VendorProfile | None:
    haystack = " ".join(
        _normalize(identity_fields.get(key))
        for key in ("VendorName", "ProductCode", "ProductName", "ModelName")
    )
    if not haystack.strip():
        return None
    for profile in VENDOR_PROFILES:
        if any(pattern in haystack for pattern in profile.known_model_patterns):
            return profile
    return None


def get_generic_profile() -> VendorProfile:
    return VENDOR_PROFILES[-1]
