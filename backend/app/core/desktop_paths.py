from __future__ import annotations

import os
import secrets
from dataclasses import dataclass
from pathlib import Path


APP_NAME = "PowerMeter"
DESKTOP_MODE_ENV = "POWERMETER_DESKTOP_MODE"
DESKTOP_ENV = "POWERMETER_DESKTOP"
APP_DATA_DIR_ENV = "POWERMETER_APP_DATA_DIR"
DB_PATH_ENV = "POWERMETER_DB_PATH"
PORT_ENV = "POWERMETER_PORT"
HOST_ENV = "POWERMETER_HOST"
JWT_SECRET_ENV = "POWERMETER_JWT_SECRET"


@dataclass(frozen=True)
class DesktopPaths:
    desktop_mode: bool
    app_data_dir: Path
    db_path: Path
    config_dir: Path
    log_dir: Path
    exports_dir: Path
    reports_dir: Path
    cache_dir: Path
    tmp_dir: Path
    backend_log_path: Path
    jwt_secret_path: Path
    port: int


def is_desktop_mode() -> bool:
    return os.getenv(DESKTOP_MODE_ENV, "").lower() in {"1", "true", "yes", "on"} or os.getenv(DESKTOP_ENV, "").lower() in {"1", "true", "yes", "on"}


def default_app_data_dir() -> Path:
    return Path.home() / "Library" / "Application Support" / APP_NAME


def resolve_app_data_dir() -> Path:
    override = os.getenv(APP_DATA_DIR_ENV)
    if override:
        return Path(override).expanduser()
    return default_app_data_dir()


def resolve_desktop_paths(create: bool = False) -> DesktopPaths:
    app_data_dir = resolve_app_data_dir()
    db_path = Path(os.getenv(DB_PATH_ENV, app_data_dir / "app.sqlite")).expanduser()
    log_dir = app_data_dir / "logs"
    paths = DesktopPaths(
        desktop_mode=is_desktop_mode(),
        app_data_dir=app_data_dir,
        db_path=db_path,
        config_dir=app_data_dir / "config",
        log_dir=log_dir,
        exports_dir=app_data_dir / "exports",
        reports_dir=app_data_dir / "reports",
        cache_dir=app_data_dir / "cache",
        tmp_dir=app_data_dir / "tmp",
        backend_log_path=log_dir / "backend.log",
        jwt_secret_path=app_data_dir / "config" / "jwt_secret",
        port=int(os.getenv(PORT_ENV, "8765")),
    )
    if create:
        ensure_desktop_paths(paths)
    return paths


def ensure_desktop_paths(paths: DesktopPaths | None = None) -> DesktopPaths:
    resolved = paths or resolve_desktop_paths()
    for directory in (
        resolved.app_data_dir,
        resolved.config_dir,
        resolved.log_dir,
        resolved.exports_dir,
        resolved.reports_dir,
        resolved.cache_dir,
        resolved.tmp_dir,
        resolved.db_path.parent,
    ):
        directory.mkdir(parents=True, exist_ok=True)
    return resolved


def ensure_desktop_jwt_secret(paths: DesktopPaths | None = None) -> str:
    resolved = ensure_desktop_paths(paths)
    if resolved.jwt_secret_path.exists():
        return resolved.jwt_secret_path.read_text(encoding="utf-8").strip()
    secret = secrets.token_urlsafe(48)
    resolved.jwt_secret_path.write_text(secret + "\n", encoding="utf-8")
    try:
        resolved.jwt_secret_path.chmod(0o600)
    except OSError:
        pass
    return secret


def configure_desktop_environment() -> DesktopPaths:
    os.environ.setdefault(DESKTOP_MODE_ENV, "1")
    os.environ.setdefault(DESKTOP_ENV, "1")
    paths = ensure_desktop_paths(resolve_desktop_paths(create=True))
    os.environ[APP_DATA_DIR_ENV] = str(paths.app_data_dir)
    os.environ[DB_PATH_ENV] = str(paths.db_path)
    os.environ.setdefault(HOST_ENV, "127.0.0.1")
    os.environ.setdefault(PORT_ENV, str(paths.port))
    os.environ.setdefault(JWT_SECRET_ENV, ensure_desktop_jwt_secret(paths))
    return paths
