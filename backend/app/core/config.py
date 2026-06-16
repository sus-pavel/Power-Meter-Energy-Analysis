from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[3]


@dataclass(frozen=True)
class Settings:
    app_name: str = "PowerMeter"
    app_mode: str = "app"
    database_path: Path = Path(os.getenv("POWERMETER_APP_DB", BASE_DIR / "data" / "powermeter_app.db"))
    prototype_database_path: Path = Path(os.getenv("POWERMETER_PROTOTYPE_DB", BASE_DIR / "data" / "energy.db"))
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
    default_poll_interval_sec: int = 30
    allowed_poll_intervals_sec: tuple[int, ...] = (10, 30, 60, 300, 600)
    polling_max_parallel_devices: int = 20
    polling_loop_interval_sec: float = 1.0
    polling_modbus_timeout_sec: float = 2.0
    frontend_api_base_url: str = os.getenv("VITE_API_BASE_URL", "/api")
    aggregation_poll_interval_sec: float = float(os.getenv("POWERMETER_AGGREGATION_POLL_SECONDS", "30"))
    drpi_poll_interval_sec: float = float(os.getenv("POWERMETER_DRPI_POLL_SECONDS", "60"))
    retention_poll_interval_sec: float = float(os.getenv("POWERMETER_RETENTION_POLL_SECONDS", "300"))
    raw_retention_days: int = int(os.getenv("POWERMETER_RAW_RETENTION_DAYS", "7"))
    agg_retention_days: int = int(os.getenv("POWERMETER_AGG_RETENTION_DAYS", "365"))
    drpi_window_size: int = int(os.getenv("POWERMETER_DRPI_WINDOW_SIZE", "288"))
    drpi_source_mode: str = os.getenv("POWERMETER_DRPI_SOURCE_MODE", "all_plus_total")
    analytics_metric_name: str = os.getenv("POWERMETER_ANALYTICS_METRIC", "active_power_total")


settings = Settings()
