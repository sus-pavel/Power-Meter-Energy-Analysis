#!/usr/bin/env python3
"""Create a documentation-only PowerMeter demo SQLite database.

The generated database is intended for README screenshots and local UI demos.
It is written under docs/demo by default and is never used by the desktop app
unless explicitly passed through POWERMETER_DB_PATH.
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
import sqlite3
import sys
import time
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))
DEFAULT_OUTPUT = REPO_ROOT / "docs" / "demo" / "powermeter_demo.sqlite"
DEMO_APP_DATA = REPO_ROOT / "docs" / "demo" / "app-data"
DEMO_PASSWORD = "demo-admin"
DEMO_PASSWORD_SALT = b"powermeter-demo!!"
BASE_TS = 1_779_875_100.0  # 2026-05-24T10:25:00Z


def fixed_password_hash(password: str) -> str:
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), DEMO_PASSWORD_SALT, 120_000)
    return "pbkdf2_sha256$120000$%s$%s" % (
        base64.urlsafe_b64encode(DEMO_PASSWORD_SALT).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def configure_environment(output_path: Path) -> None:
    os.environ["POWERMETER_DB_PATH"] = str(output_path)
    os.environ["POWERMETER_APP_DATA_DIR"] = str(DEMO_APP_DATA)
    os.environ["POWERMETER_JWT_SECRET"] = "demo-documentation-only-secret"
    os.environ.setdefault("POWERMETER_PORT", "8765")


def reset_tables(conn: sqlite3.Connection) -> None:
    tables = [
        "app_drpi_results",
        "measurements_agg_5min",
        "measurements_agg_10min",
        "measurements_agg_15min",
        "measurements_agg_30min",
        "measurements_agg_1h",
        "measurements_raw",
        "polling_jobs",
        "device_status",
        "device_registers",
        "devices",
        "candidate_probe_results",
        "discovered_candidates",
        "scan_results",
        "scan_jobs",
        "audit_log",
        "users",
    ]
    for table_name in tables:
        conn.execute(f"DELETE FROM {table_name}")
    conn.execute("DELETE FROM sqlite_sequence")


def insert_user(conn: sqlite3.Connection) -> None:
    conn.execute(
        """
        INSERT INTO users (
            id, username, password_hash, full_name, role, is_active, must_change_password, created_at, updated_at
        )
        VALUES (1, 'admin', ?, 'Demo Administrator', 'admin', 1, 0, '2026-05-24T09:00:00Z', '2026-05-24T09:00:00Z')
        """,
        (fixed_password_hash(DEMO_PASSWORD),),
    )


def insert_discovery(conn: sqlite3.Connection) -> None:
    jobs = [
        (
            1,
            "2026-05-24T09:05:00Z",
            "2026-05-24T09:05:04Z",
            "2026-05-24T09:06:18Z",
            1,
            "completed",
            "192.0.2.10",
            "192.0.2.18",
            9,
            9,
            3,
            "custom",
            [1, 7, 11, 17],
            2.0,
            5,
            None,
        ),
        (
            2,
            "2026-05-24T09:20:00Z",
            "2026-05-24T09:20:03Z",
            "2026-05-24T09:20:41Z",
            1,
            "failed",
            "198.51.100.20",
            "198.51.100.24",
            5,
            4,
            0,
            "quick",
            [0, 1, 2, 3, 10, 100, 247],
            1.5,
            3,
            "Demo firewall blocked TCP/502 on one host.",
        ),
    ]
    conn.executemany(
        """
        INSERT INTO scan_jobs (
            id, created_at, started_at, finished_at, created_by_user_id, status, ip_start, ip_end,
            total_hosts, processed_hosts, found_hosts, unit_id_scan_mode, unit_ids_json,
            timeout_seconds, max_concurrent_hosts, error_message
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [(*job[:12], json.dumps(job[12]), *job[13:]) for job in jobs],
    )

    results = [
        (1, 1, "192.0.2.10", 502, 1, 1, 42.8, [1], "2026-05-24T09:05:21Z"),
        (2, 1, "192.0.2.11", 502, 1, 1, 57.4, [7, 11], "2026-05-24T09:05:29Z"),
        (3, 1, "192.0.2.12", 502, 1, 0, 118.0, [], "2026-05-24T09:05:34Z"),
        (4, 1, "192.0.2.13", 502, 0, 0, None, [], "2026-05-24T09:05:39Z"),
        (5, 1, "192.0.2.17", 502, 1, 1, 61.2, [17], "2026-05-24T09:06:04Z"),
        (6, 2, "198.51.100.20", 502, 0, 0, None, [], "2026-05-24T09:20:13Z"),
        (7, 2, "198.51.100.21", 502, 1, 0, 205.3, [], "2026-05-24T09:20:20Z"),
        (8, 2, "198.51.100.22", 502, 0, 0, None, [], "2026-05-24T09:20:28Z"),
    ]
    conn.executemany(
        """
        INSERT INTO scan_results (
            id, job_id, ip_address, port, tcp_open, modbus_responding, response_time_ms,
            candidate_unit_ids, last_checked_at, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [(*row[:7], json.dumps(row[7]), row[8], row[8]) for row in results],
    )

    candidates = [
        (
            1,
            1,
            "192.0.2.10",
            502,
            1,
            "promoted",
            "three_phase_power_meter",
            0.92,
            "Contoso Instruments",
            "Main switchboard meter promoted for dashboard screenshots.",
            "2026-05-24T09:05:22Z",
            "2026-05-24T09:08:10Z",
        ),
        (
            2,
            2,
            "192.0.2.11",
            502,
            7,
            "reviewed",
            "branch_circuit_meter",
            0.76,
            "Northwind Energy",
            "Voltage and current registers decoded; awaiting operator review.",
            "2026-05-24T09:05:30Z",
            "2026-05-24T09:07:42Z",
        ),
        (
            3,
            2,
            "192.0.2.11",
            502,
            11,
            "discovered",
            "unknown_modbus_device",
            0.35,
            "unknown",
            "Responds to Modbus but register profile is not confirmed.",
            "2026-05-24T09:05:31Z",
            "2026-05-24T09:05:31Z",
        ),
        (
            4,
            5,
            "192.0.2.17",
            502,
            17,
            "rejected",
            "gateway_or_bridge",
            0.44,
            "Fabrikam Controls",
            "Demo rejection: gateway answered but did not expose meter registers.",
            "2026-05-24T09:06:05Z",
            "2026-05-24T09:09:20Z",
        ),
    ]
    conn.executemany(
        """
        INSERT INTO discovered_candidates (
            id, scan_result_id, ip_address, port, unit_id, status, device_type_guess,
            confidence_score, vendor_guess, notes, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        candidates,
    )

    probe_rows = [
        (1, 1, 30001, "read_input_registers", "float32", "43 3a 80 00", 186.5, 1, "2026-05-24T09:07:10Z"),
        (2, 1, 30003, "read_input_registers", "float32", "42 c8 00 00", 100.0, 1, "2026-05-24T09:07:11Z"),
        (3, 2, 30001, "read_input_registers", "float32", "42 a6 66 66", 83.2, 1, "2026-05-24T09:07:33Z"),
        (4, 2, 40010, "read_holding_registers", "uint16", "00 00", None, 0, "2026-05-24T09:07:35Z"),
        (5, 3, 30001, "read_input_registers", "float32", None, None, 0, "2026-05-24T09:07:50Z"),
        (6, 4, 30001, "read_input_registers", "float32", "00 01", None, 0, "2026-05-24T09:08:02Z"),
    ]
    conn.executemany(
        """
        INSERT INTO candidate_probe_results (
            id, candidate_id, register_address, function_code, data_type, raw_value,
            decoded_value, valid, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        probe_rows,
    )


def insert_devices(conn: sqlite3.Connection) -> None:
    devices = [
        (
            1,
            "Main Switchboard Meter",
            "192.0.2.10",
            502,
            1,
            "Demo meter promoted from discovery candidate #1.",
            "Building A / Main Electrical Room",
            1,
            30,
            "2026-05-24T09:08:10Z",
            "2026-05-24T09:08:10Z",
        ),
        (
            2,
            "PV Inverter Feeder",
            "203.0.113.25",
            502,
            3,
            "Documentation-only sample endpoint for analytics screenshots.",
            "Building A / Roof Inverter Panel",
            1,
            60,
            "2026-05-24T09:12:00Z",
            "2026-05-24T09:12:00Z",
        ),
        (
            3,
            "Workshop Panel Meter",
            "203.0.113.41",
            502,
            16,
            "Disabled sample meter used to show readiness states.",
            "Workshop / Panel W1",
            0,
            300,
            "2026-05-24T09:13:00Z",
            "2026-05-24T09:13:00Z",
        ),
    ]
    conn.executemany(
        """
        INSERT INTO devices (
            id, name, host, port, unit_id, description, location, enabled,
            poll_interval_sec, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        devices,
    )

    registers = [
        (1, 1, "active_power_total", "read_input_registers", 30001, "float32", 0.001, "kW", "Total active power", 1),
        (2, 1, "voltage_l1_l2", "read_input_registers", 30009, "float32", 1.0, "V", "Line voltage L1-L2", 1),
        (3, 1, "current_l1", "read_input_registers", 30013, "float32", 1.0, "A", "Phase current L1", 1),
        (4, 2, "active_power_total", "read_input_registers", 30001, "float32", 0.001, "kW", "Inverter feeder active power", 1),
        (5, 2, "frequency", "read_input_registers", 30071, "float32", 1.0, "Hz", "Grid frequency", 1),
        (6, 3, "active_power_total", "read_input_registers", 30001, "float32", 0.001, "kW", "Workshop active power", 0),
    ]
    conn.executemany(
        """
        INSERT INTO device_registers (
            id, device_id, metric, function_code, address, data_type, scale, unit,
            description, enabled, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, '2026-05-24T09:14:00Z', '2026-05-24T09:14:00Z')
        """,
        registers,
    )

    conn.executemany(
        """
        INSERT INTO polling_jobs (
            id, device_id, status, poll_interval_sec, last_run_at, next_run_at, created_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (1, 1, "running", 30, "2026-05-24T10:24:30Z", BASE_TS + 30, "2026-05-24T09:15:00Z", "2026-05-24T10:24:30Z"),
            (2, 2, "paused", 60, "2026-05-24T10:23:45Z", BASE_TS + 60, "2026-05-24T09:15:10Z", "2026-05-24T10:23:45Z"),
            (3, 3, "disabled", 300, None, None, "2026-05-24T09:15:20Z", "2026-05-24T09:15:20Z"),
        ],
    )

    conn.executemany(
        """
        INSERT INTO device_status (
            device_id, status, last_success_at, last_error_at, last_error_message, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (1, "online", "2026-05-24T10:24:30Z", None, None, "2026-05-24T10:24:30Z"),
            (2, "timeout", "2026-05-24T10:18:45Z", "2026-05-24T10:23:45Z", "Demo timeout waiting for Unit ID 3.", "2026-05-24T10:23:45Z"),
            (3, "disabled", None, None, None, "2026-05-24T09:15:20Z"),
        ],
    )


def insert_measurements(conn: sqlite3.Connection) -> None:
    raw_rows = []
    row_id = 1
    for offset_minutes in range(0, 60, 5):
        ts = BASE_TS - (55 - offset_minutes) * 60
        main_power = 142.0 + offset_minutes * 0.9
        pv_power = 38.0 + offset_minutes * 0.25
        raw_rows.extend(
            [
                (row_id, 1, 1, ts, "active_power_total", round(main_power, 3), "kW"),
                (row_id + 1, 2, 4, ts, "active_power_total", round(pv_power, 3), "kW"),
                (row_id + 2, 1, 2, ts, "voltage_l1_l2", 399.5 + (offset_minutes % 10) * 0.2, "V"),
            ]
        )
        row_id += 3
    conn.executemany(
        """
        INSERT INTO measurements_raw (
            id, device_id, register_id, timestamp, metric, value, unit, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, '2026-05-24T10:25:00Z')
        """,
        raw_rows,
    )

    for index, table_name in enumerate(
        [
            "measurements_agg_5min",
            "measurements_agg_10min",
            "measurements_agg_15min",
            "measurements_agg_30min",
            "measurements_agg_1h",
        ],
        start=1,
    ):
        for device_id, mean_value in [(1, 166.5), (2, 45.1)]:
            conn.execute(
                f"""
                INSERT INTO {table_name} (
                    id, window_start, window_end, device_id, metric, unit,
                    mean_value, min_value, max_value, sample_count, created_at
                )
                VALUES (?, ?, ?, ?, 'active_power_total', 'kW', ?, ?, ?, ?, '2026-05-24T10:25:00Z')
                """,
                (
                    (index * 10) + device_id,
                    BASE_TS - 3600,
                    BASE_TS,
                    device_id,
                    mean_value,
                    mean_value - 8.0,
                    mean_value + 9.0,
                    12,
                ),
            )

    drpi_rows = [
        (1, BASE_TS - 900, "TOTAL", 0.62, 0.54, 0.48, 0.55, 0.57),
        (2, BASE_TS - 600, "TOTAL", 0.65, 0.56, 0.51, 0.58, 0.60),
        (3, BASE_TS - 300, "TOTAL", 0.68, 0.59, 0.53, 0.60, 0.63),
        (4, BASE_TS, "TOTAL", 0.70, 0.61, 0.55, 0.62, 0.65),
    ]
    conn.executemany(
        """
        INSERT INTO app_drpi_results (
            id, ts, source_id, F1, F2, F3, R_raw, DRPI, created_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, '2026-05-24T10:25:00Z')
        """,
        drpi_rows,
    )


def insert_audit_log(conn: sqlite3.Connection) -> None:
    conn.executemany(
        """
        INSERT INTO audit_log (id, timestamp, user_id, action, entity_type, entity_id, details_json)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (1, "2026-05-24T09:05:00Z", 1, "discovery.scan.created", "scan_job", 1, '{"mode":"custom"}'),
            (2, "2026-05-24T09:08:10Z", 1, "candidate.promoted", "candidate", 1, '{"device_id":1}'),
            (3, "2026-05-24T09:12:00Z", 1, "device.created", "device", 2, '{"source":"demo_fixture"}'),
            (4, "2026-05-24T09:20:41Z", 1, "discovery.scan.failed", "scan_job", 2, '{"reason":"demo firewall block"}'),
        ],
    )


def seed_database(output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    if output_path.exists():
        output_path.unlink()

    configure_environment(output_path)

    from backend.app.core.database import get_connection, init_db

    init_db()
    with get_connection() as conn:
        reset_tables(conn)
        insert_user(conn)
        insert_discovery(conn)
        insert_devices(conn)
        insert_measurements(conn)
        insert_audit_log(conn)
        conn.commit()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed a documentation-only PowerMeter demo database.")
    parser.add_argument(
        "--output",
        type=Path,
        default=DEFAULT_OUTPUT,
        help=f"SQLite output path. Defaults to {DEFAULT_OUTPUT}",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_path = args.output.expanduser().resolve()
    started = time.perf_counter()
    seed_database(output_path)
    elapsed_ms = (time.perf_counter() - started) * 1000
    print(f"Created demo database: {output_path}")
    print(f"Demo login: admin / {DEMO_PASSWORD}")
    print(f"Rows are fake and documentation-only. Completed in {elapsed_ms:.1f} ms.")


if __name__ == "__main__":
    main()
