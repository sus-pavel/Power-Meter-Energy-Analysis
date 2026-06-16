from __future__ import annotations

import sqlite3
from pathlib import Path

from backend.app.core.config import settings
from backend.app.core.security import hash_password


def get_connection() -> sqlite3.Connection:
    settings.database_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(settings.database_path, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def table_exists(conn: sqlite3.Connection, table_name: str) -> bool:
    row = conn.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
        (table_name,),
    ).fetchone()
    return row is not None


def database_status(path: Path | None = None) -> str:
    try:
        db_path = path or settings.database_path
        db_path.parent.mkdir(parents=True, exist_ok=True)
        with sqlite3.connect(db_path) as conn:
            conn.execute("SELECT 1")
        return "ok"
    except sqlite3.Error:
        return "error"


def init_db() -> None:
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT NOT NULL UNIQUE,
                password_hash TEXT NOT NULL,
                full_name TEXT,
                role TEXT NOT NULL CHECK (role IN ('admin', 'chief_engineer', 'analyst', 'guest')),
                is_active INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS devices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT NOT NULL,
                host TEXT NOT NULL,
                port INTEGER NOT NULL DEFAULT 502,
                unit_id INTEGER NOT NULL DEFAULT 1,
                description TEXT,
                location TEXT,
                enabled INTEGER NOT NULL DEFAULT 1,
                poll_interval_sec INTEGER NOT NULL DEFAULT 30,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS device_registers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER NOT NULL,
                metric TEXT NOT NULL,
                function_code TEXT NOT NULL,
                address INTEGER NOT NULL,
                data_type TEXT NOT NULL,
                scale REAL NOT NULL DEFAULT 1.0,
                unit TEXT,
                description TEXT,
                enabled INTEGER NOT NULL DEFAULT 1,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS audit_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                user_id INTEGER,
                action TEXT NOT NULL,
                entity_type TEXT NOT NULL,
                entity_id INTEGER,
                details_json TEXT,
                FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS scan_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                started_at TEXT,
                finished_at TEXT,
                created_by_user_id INTEGER,
                status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
                ip_start TEXT NOT NULL,
                ip_end TEXT NOT NULL,
                total_hosts INTEGER NOT NULL DEFAULT 0,
                processed_hosts INTEGER NOT NULL DEFAULT 0,
                found_hosts INTEGER NOT NULL DEFAULT 0,
                error_message TEXT,
                FOREIGN KEY (created_by_user_id) REFERENCES users(id) ON DELETE SET NULL
            );

            CREATE TABLE IF NOT EXISTS scan_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                job_id INTEGER NOT NULL,
                ip_address TEXT NOT NULL,
                port INTEGER NOT NULL DEFAULT 502,
                tcp_open INTEGER NOT NULL DEFAULT 0,
                modbus_responding INTEGER NOT NULL DEFAULT 0,
                response_time_ms REAL,
                candidate_unit_ids TEXT NOT NULL DEFAULT '[]',
                last_checked_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (job_id) REFERENCES scan_jobs(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS discovered_candidates (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                scan_result_id INTEGER NOT NULL,
                ip_address TEXT NOT NULL,
                port INTEGER NOT NULL DEFAULT 502,
                unit_id INTEGER NOT NULL,
                status TEXT NOT NULL CHECK (status IN ('discovered', 'reviewed', 'promoted', 'rejected')),
                device_type_guess TEXT,
                confidence_score REAL,
                vendor_guess TEXT,
                notes TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (scan_result_id) REFERENCES scan_results(id) ON DELETE CASCADE,
                UNIQUE (scan_result_id, unit_id)
            );

            CREATE TABLE IF NOT EXISTS candidate_probe_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                candidate_id INTEGER NOT NULL,
                register_address INTEGER NOT NULL,
                function_code TEXT NOT NULL,
                data_type TEXT NOT NULL,
                raw_value TEXT,
                decoded_value REAL,
                valid INTEGER NOT NULL DEFAULT 0,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (candidate_id) REFERENCES discovered_candidates(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS polling_jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER NOT NULL UNIQUE,
                status TEXT NOT NULL CHECK (status IN ('pending', 'running', 'paused', 'failed', 'disabled')),
                poll_interval_sec INTEGER NOT NULL DEFAULT 30,
                last_run_at TEXT,
                next_run_at REAL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS measurements_raw (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                device_id INTEGER NOT NULL,
                register_id INTEGER NOT NULL,
                timestamp REAL NOT NULL,
                metric TEXT NOT NULL,
                value REAL NOT NULL,
                unit TEXT,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE,
                FOREIGN KEY (register_id) REFERENCES device_registers(id) ON DELETE CASCADE
            );

            CREATE INDEX IF NOT EXISTS idx_measurements_raw_device_ts
            ON measurements_raw (device_id, timestamp);

            CREATE TABLE IF NOT EXISTS device_status (
                device_id INTEGER PRIMARY KEY,
                status TEXT NOT NULL CHECK (status IN ('online', 'offline', 'timeout', 'error', 'disabled')),
                last_success_at TEXT,
                last_error_at TEXT,
                last_error_message TEXT,
                updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (device_id) REFERENCES devices(id) ON DELETE CASCADE
            );

            CREATE TABLE IF NOT EXISTS app_drpi_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts REAL NOT NULL,
                source_id TEXT NOT NULL,
                F1 REAL NOT NULL,
                F2 REAL NOT NULL,
                F3 REAL NOT NULL,
                R_raw REAL NOT NULL,
                DRPI REAL NOT NULL,
                created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (ts, source_id)
            );

            CREATE INDEX IF NOT EXISTS idx_app_drpi_results_ts_source
            ON app_drpi_results (ts, source_id);
            """
        )

        for table_name in (
            "measurements_agg_5min",
            "measurements_agg_10min",
            "measurements_agg_15min",
            "measurements_agg_30min",
            "measurements_agg_1h",
        ):
            conn.execute(
                f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    window_start REAL NOT NULL,
                    window_end REAL NOT NULL,
                    device_id INTEGER NOT NULL,
                    metric TEXT NOT NULL,
                    unit TEXT,
                    mean_value REAL NOT NULL,
                    min_value REAL NOT NULL,
                    max_value REAL NOT NULL,
                    sample_count INTEGER NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE (window_start, window_end, device_id, metric)
                );
                """
            )
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_window_end ON {table_name} (window_end);")
            conn.execute(f"CREATE INDEX IF NOT EXISTS idx_{table_name}_device_metric ON {table_name} (device_id, metric);")

        columns = {
            row["name"]
            for row in conn.execute("PRAGMA table_info(devices)").fetchall()
        }
        if "poll_interval_sec" not in columns:
            conn.execute("ALTER TABLE devices ADD COLUMN poll_interval_sec INTEGER NOT NULL DEFAULT 30")

        conn.execute(
            """
            UPDATE scan_jobs
            SET status = 'failed',
                finished_at = CURRENT_TIMESTAMP,
                error_message = 'Application stopped before scan completed.'
            WHERE status IN ('pending', 'running')
            """
        )

        user_count = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        if user_count == 0:
            conn.execute(
                """
                INSERT INTO users (username, password_hash, full_name, role, is_active)
                VALUES (?, ?, ?, ?, 1)
                """,
                (
                    settings.default_admin_username,
                    hash_password(settings.default_admin_password),
                    "Default Administrator",
                    "admin",
                ),
            )
