from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass

from backend.app.core.config import settings
from backend.app.core.database import get_connection


logger = logging.getLogger(__name__)

AGGREGATION_WINDOWS: dict[str, int] = {
    "5min": 300,
    "10min": 600,
    "15min": 900,
    "30min": 1800,
    "1h": 3600,
}

AGGREGATION_TABLES = {
    "5min": "measurements_agg_5min",
    "10min": "measurements_agg_10min",
    "15min": "measurements_agg_15min",
    "30min": "measurements_agg_30min",
    "1h": "measurements_agg_1h",
}


def floor_to_window(ts: float, window_size: int) -> int:
    value = int(ts)
    return value - (value % window_size)


def build_windows_to_process(conn, table_name: str, window_size: int) -> list[tuple[int, int]]:
    bounds = conn.execute("SELECT MIN(timestamp), MAX(timestamp) FROM measurements_raw").fetchone()
    if bounds is None or bounds[0] is None or bounds[1] is None:
        return []
    raw_min_ts = float(bounds[0])
    raw_max_ts = float(bounds[1])
    last_complete_start = floor_to_window(raw_max_ts, window_size) - window_size
    if last_complete_start < 0:
        return []
    last_done = conn.execute(f"SELECT MAX(window_start) FROM {table_name}").fetchone()[0]
    start_window = floor_to_window(raw_min_ts, window_size) if last_done is None else int(last_done) + window_size
    windows: list[tuple[int, int]] = []
    current = start_window
    while current <= last_complete_start:
        windows.append((current, current + window_size))
        current += window_size
    return windows


def aggregate_one_window(conn, table_name: str, window_start: int, window_end: int) -> int:
    rows = conn.execute(
        """
        SELECT
            device_id,
            metric,
            unit,
            AVG(value) AS mean_value,
            MIN(value) AS min_value,
            MAX(value) AS max_value,
            COUNT(*) AS sample_count
        FROM measurements_raw
        WHERE timestamp >= ?
          AND timestamp < ?
        GROUP BY device_id, metric, unit
        ORDER BY device_id, metric
        """,
        (window_start, window_end),
    ).fetchall()
    if not rows:
        return 0
    before = conn.total_changes
    conn.executemany(
        f"""
        INSERT OR IGNORE INTO {table_name} (
            window_start, window_end, device_id, metric, unit,
            mean_value, min_value, max_value, sample_count
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                window_start,
                window_end,
                row["device_id"],
                row["metric"],
                row["unit"],
                float(row["mean_value"]),
                float(row["min_value"]),
                float(row["max_value"]),
                int(row["sample_count"]),
            )
            for row in rows
        ],
    )
    return conn.total_changes - before


@dataclass
class AggregationStats:
    inserted_rows: int
    processed_windows: int


class AggregationService:
    def __init__(self) -> None:
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    def run_once(self) -> AggregationStats:
        inserted = 0
        processed = 0
        with get_connection() as conn:
            for key, window_size in AGGREGATION_WINDOWS.items():
                table_name = AGGREGATION_TABLES[key]
                windows = build_windows_to_process(conn, table_name, window_size)
                for window_start, window_end in windows:
                    inserted += aggregate_one_window(conn, table_name, window_start, window_end)
                processed += len(windows)
        return AggregationStats(inserted_rows=inserted, processed_windows=processed)

    async def start(self) -> None:
        self._running = True
        while self._running:
            try:
                await asyncio.to_thread(self.run_once)
            except Exception:
                logger.exception("Aggregation cycle failed")
            await asyncio.sleep(settings.aggregation_poll_interval_sec)

    async def stop(self) -> None:
        self._running = False


aggregation_service = AggregationService()
