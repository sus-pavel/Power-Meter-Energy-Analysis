from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Settings:
    app_name: str = "PowerMeter"
    app_mode: str = "app"
    database_path: Path = BASE_DIR / "data" / "powermeter_app.db"
    prototype_database_path: Path = BASE_DIR / "data" / "energy.db"
    jwt_secret: str = os.getenv("POWERMETER_JWT_SECRET", "change-this-local-secret")
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = int(os.getenv("POWERMETER_TOKEN_MINUTES", "1440"))
    default_admin_username: str = "admin"
    default_admin_password: str = "admin"
    discovery_port: int = 502
    discovery_timeout_seconds: float = 1.0
    discovery_max_concurrent_hosts: int = 20
    discovery_candidate_unit_ids: tuple[int, ...] = (1, 2, 3, 10, 100, 247)
    discovery_max_hosts_per_scan: int = int(os.getenv("POWERMETER_DISCOVERY_MAX_HOSTS", "4096"))
    probe_profiles_path: Path = BASE_DIR / "backend" / "app" / "config" / "probe_profiles.yaml"
    register_probe_timeout_seconds: float = 1.0
    register_probe_delay_seconds: float = 0.05


settings = Settings()
