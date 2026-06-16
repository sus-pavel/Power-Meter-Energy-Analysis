from __future__ import annotations

from enum import Enum


class Role(str, Enum):
    ADMIN = "admin"
    CHIEF_ENGINEER = "chief_engineer"
    ANALYST = "analyst"
    GUEST = "guest"


PERMISSIONS_BY_ROLE: dict[str, set[str]] = {
    Role.ADMIN: {
        "manage_users",
        "manage_devices",
        "scan_network",
        "view_discovery",
        "view_candidates",
        "manage_candidates",
        "probe_registers",
        "view_dashboard",
        "view_analytics",
        "export_data",
        "manage_settings",
        "manage_polling",
        "manage_analytics",
    },
    Role.CHIEF_ENGINEER: {
        "manage_devices",
        "scan_network",
        "view_discovery",
        "view_candidates",
        "manage_candidates",
        "probe_registers",
        "view_dashboard",
        "view_discovery",
        "view_candidates",
        "view_analytics",
        "export_data",
        "manage_polling",
        "manage_analytics",
    },
    Role.ANALYST: {
        "view_dashboard",
        "view_analytics",
        "export_data",
    },
    Role.GUEST: {
        "view_dashboard",
    },
}


def has_permission(role: str, permission: str) -> bool:
    return permission in PERMISSIONS_BY_ROLE.get(role, set())


def allowed_roles() -> list[str]:
    return [role.value for role in Role]
