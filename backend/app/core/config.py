from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from backend.app.core.desktop_paths import is_desktop_mode, resolve_desktop_paths


BASE_DIR = Path(__file__).resolve().parents[3]
DESKTOP_PATHS = resolve_desktop_paths()


@dataclass(frozen=True)
class Settings:
    app_name: str = "PowerMeter"
    app_mode: str = "desktop" if is_desktop_mode() else "app"
    desktop_mode: bool = is_desktop_mode()
    app_data_dir: Path = DESKTOP_PATHS.app_data_dir
    log_dir: Path = DESKTOP_PATHS.log_dir
    backend_log_path: Path = DESKTOP_PATHS.backend_log_path
    backend_port: int = DESKTOP_PATHS.port
    database_path: Path = Path(
        os.getenv(
            "POWERMETER_DB_PATH",
            os.getenv(
                "POWERMETER_APP_DB",
                DESKTOP_PATHS.db_path if is_desktop_mode() else BASE_DIR / "data" / "powermeter_app.db",
            ),
        )
    )
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
    discovery_quick_unit_ids: tuple[int, ...] = (0, 1, 2, 3, 4, 5, 10, 16, 17, 20, 100, 247, 255)
    discovery_extended_unit_ids: tuple[int, ...] = tuple(list(range(0, 33)) + [100, 101, 247, 255])
    discovery_full_scan_max_hosts: int = 8
    discovery_max_unit_ids_per_scan: int = 4096
    discovery_default_timeout_seconds: float = 2.0
    discovery_real_network_max_concurrent_hosts: int = 5
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
