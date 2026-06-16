from __future__ import annotations

import sqlite3

from backend.app.polling.modbus_client import RegisterMeasurement


def write_measurements(
    conn: sqlite3.Connection,
    *,
    device_id: int,
    timestamp: float,
    measurements: list[RegisterMeasurement],
) -> int:
    if not measurements:
        return 0
    conn.executemany(
        """
        INSERT INTO measurements_raw (device_id, register_id, timestamp, metric, value, unit)
        VALUES (?, ?, ?, ?, ?, ?)
        """,
        [
            (device_id, measurement.register_id, timestamp, measurement.metric, measurement.value, measurement.unit)
            for measurement in measurements
        ],
    )
    return len(measurements)
