"""
services/aggregator.py

Назначение:
- читать сырые данные из raw_data;
- строить агрегаты по нескольким временным окнам:
    5, 10, 15, 30, 60 минут;
- сохранять агрегаты в отдельные таблицы;
- поддерживать политику хранения raw_data = 1 сутки.

Логика:
- для DRPI далее используется agg_5min + active_power_avg;
- для SSA далее в дашборде можно использовать любой уровень агрегации
  (5/10/15/30/60 минут) + active_power_avg;
- прочие метрики тоже агрегируются обычным средним.

Таблицы:
- raw_data
- agg_5min
- agg_10min
- agg_15min
- agg_30min
- agg_60min
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path

import yaml


logger = logging.getLogger(__name__)


# =========================
# Конфигурационные модели
# =========================

@dataclass(slots=True)
class AggregatorConfig:
    db_path: str = "data/energy.db"
    poll_interval: float = 30.0

    raw_table_name: str = "raw_data"
    # УДАЛЕНИЕ СЫРЫХ ДАННЫХ ЧЕРЕЗ СУТКИ
    raw_retention_sec: int = 86400

    aggregation_windows_sec: list[int] = field(default_factory=lambda: [300, 600, 900, 1800, 3600])

    power_metric_name: str = "active_power_avg"
    auxiliary_metrics: list[str] = field(default_factory=lambda: [
        "voltage_phase_avg",
        "current_avg",
        "frequency",
    ])

    auto_init_db: bool = True


# =========================
# Загрузка конфигурации
# =========================

def load_aggregator_config(config_path: str | Path) -> AggregatorConfig:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Aggregator config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    agg_raw = raw.get("aggregator", {})

    return AggregatorConfig(
        db_path=str(agg_raw.get("db_path", "data/energy.db")),
        poll_interval=float(agg_raw.get("poll_interval", 30.0)),
        raw_table_name=str(agg_raw.get("raw_table_name", "raw_data")),
        raw_retention_sec=int(agg_raw.get("raw_retention_sec", 86400)),
        aggregation_windows_sec=list(agg_raw.get("aggregation_windows_sec", [300, 600, 900, 1800, 3600])),
        power_metric_name=str(agg_raw.get("power_metric_name", "active_power_avg")),
        auxiliary_metrics=list(agg_raw.get("auxiliary_metrics", [
            "voltage_phase_avg",
            "current_avg",
            "frequency",
        ])),
        auto_init_db=bool(agg_raw.get("auto_init_db", True)),
    )


# =========================
# SQL и инициализация
# =========================

def ensure_parent_dir(db_path: str | Path) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)


def table_name_for_window(window_sec: int) -> str:
    if window_sec % 3600 == 0:
        hours = window_sec // 3600
        return f"agg_{hours}h"

    if window_sec % 60 == 0:
        minutes = window_sec // 60
        return f"agg_{minutes}min"

    return f"agg_{window_sec}s"


def make_agg_table_sql(table_name: str) -> str:
    return f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        window_start INTEGER NOT NULL,
        window_end INTEGER NOT NULL,
        device_id TEXT NOT NULL,
        metric TEXT NOT NULL,
        mean_value REAL NOT NULL,
        sample_count INTEGER NOT NULL,
        created_at REAL NOT NULL,
        UNIQUE(window_start, window_end, device_id, metric)
    );
    """


def make_agg_index_sql(table_name: str) -> str:
    return f"""
    CREATE INDEX IF NOT EXISTS idx_{table_name}_window_device_metric
    ON {table_name} (window_start, window_end, device_id, metric);
    """


def init_db(config: AggregatorConfig) -> None:
    ensure_parent_dir(config.db_path)

    conn = sqlite3.connect(config.db_path)
    try:
        for window_sec in config.aggregation_windows_sec:
            table_name = table_name_for_window(window_sec)
            conn.execute(make_agg_table_sql(table_name))
            conn.execute(make_agg_index_sql(table_name))

        conn.commit()
    finally:
        conn.close()


# =========================
# Вспомогательная логика
# =========================

def floor_to_window(ts: int, window_size: int) -> int:
    return ts - (ts % window_size)


def get_last_aggregated_window_start(
    conn: sqlite3.Connection,
    table_name: str,
) -> int | None:
    row = conn.execute(f"SELECT MAX(window_start) FROM {table_name}").fetchone()
    if row is None or row[0] is None:
        return None
    return int(row[0])


def build_windows_to_process(
    conn: sqlite3.Connection,
    raw_table_name: str,
    agg_table_name: str,
    window_size: int,
) -> list[tuple[int, int]]:
    """
    Находит завершённые окна, которых ещё нет в таблице агрегатов.
    """
    raw_bounds = conn.execute(
        f"SELECT MIN(CAST(timestamp AS INTEGER)), MAX(CAST(timestamp AS INTEGER)) FROM {raw_table_name}"
    ).fetchone()

    if raw_bounds is None or raw_bounds[0] is None or raw_bounds[1] is None:
        return []

    raw_min_ts, raw_max_ts = int(raw_bounds[0]), int(raw_bounds[1])

    # Берём только полностью завершённые окна
    last_complete_window_start = floor_to_window(raw_max_ts, window_size) - window_size
    if last_complete_window_start < 0:
        return []

    last_done = get_last_aggregated_window_start(conn, agg_table_name)

    if last_done is None:
        start_window = floor_to_window(raw_min_ts, window_size)
    else:
        start_window = last_done + window_size

    windows: list[tuple[int, int]] = []
    current = start_window

    while current <= last_complete_window_start:
        windows.append((current, current + window_size))
        current += window_size

    return windows


def aggregate_one_window_sync(
    conn: sqlite3.Connection,
    raw_table_name: str,
    agg_table_name: str,
    window_start: int,
    window_end: int,
    metrics: list[str],
) -> int:
    placeholders = ",".join("?" for _ in metrics)

    query = f"""
    SELECT
        device_id,
        metric,
        AVG(value) AS mean_value,
        COUNT(*) AS sample_count
    FROM {raw_table_name}
    WHERE timestamp >= ?
      AND timestamp < ?
      AND metric IN ({placeholders})
    GROUP BY device_id, metric
    ORDER BY device_id, metric
    """

    rows = conn.execute(query, [window_start, window_end, *metrics]).fetchall()

    if not rows:
        return 0

    insert_query = f"""
    INSERT OR IGNORE INTO {agg_table_name} (
        window_start,
        window_end,
        device_id,
        metric,
        mean_value,
        sample_count,
        created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?)
    """

    now_ts = time.time()
    payload = [
        (
            int(window_start),
            int(window_end),
            str(device_id),
            str(metric),
            float(mean_value),
            int(sample_count),
            now_ts,
        )
        for device_id, metric, mean_value, sample_count in rows
    ]

    conn.executemany(insert_query, payload)
    conn.commit()
    return len(payload)


def cleanup_raw_sync(
    conn: sqlite3.Connection,
    raw_table_name: str,
    raw_retention_sec: int,
) -> int:
    """
    Храним raw_data только 1 сутки.
    """
    threshold_ts = time.time() - raw_retention_sec

    before_count = conn.execute(f"SELECT COUNT(*) FROM {raw_table_name}").fetchone()[0]

    conn.execute(
        f"DELETE FROM {raw_table_name} WHERE timestamp < ?",
        (threshold_ts,),
    )
    conn.commit()

    after_count = conn.execute(f"SELECT COUNT(*) FROM {raw_table_name}").fetchone()[0]
    return int(before_count - after_count)


# =========================
# Основной сервис
# =========================

class Aggregator:
    def __init__(self, config: AggregatorConfig):
        self.config = config
        self._running = False

    def _run_aggregation_cycle_sync(self) -> dict[str, int]:
        conn = sqlite3.connect(self.config.db_path)
        try:
            metrics = [self.config.power_metric_name, *self.config.auxiliary_metrics]

            total_inserted_rows = 0
            total_windows = 0

            for window_sec in self.config.aggregation_windows_sec:
                agg_table_name = table_name_for_window(window_sec)

                windows = build_windows_to_process(
                    conn=conn,
                    raw_table_name=self.config.raw_table_name,
                    agg_table_name=agg_table_name,
                    window_size=window_sec,
                )

                inserted_for_this_table = 0

                for window_start, window_end in windows:
                    inserted_for_this_table += aggregate_one_window_sync(
                        conn=conn,
                        raw_table_name=self.config.raw_table_name,
                        agg_table_name=agg_table_name,
                        window_start=window_start,
                        window_end=window_end,
                        metrics=metrics,
                    )

                total_inserted_rows += inserted_for_this_table
                total_windows += len(windows)

            deleted_raw_rows = cleanup_raw_sync(
                conn=conn,
                raw_table_name=self.config.raw_table_name,
                raw_retention_sec=self.config.raw_retention_sec,
            )

            return {
                "inserted_rows": total_inserted_rows,
                "processed_windows": total_windows,
                "deleted_raw_rows": deleted_raw_rows,
            }

        finally:
            conn.close()

    async def start(self) -> None:
        if self.config.auto_init_db:
            init_db(self.config)

        self._running = True
        logger.info(
            "Aggregator started | db=%s | poll_interval=%.1fs | windows=%s | raw_retention_sec=%d",
            self.config.db_path,
            self.config.poll_interval,
            self.config.aggregation_windows_sec,
            self.config.raw_retention_sec,
        )

        while self._running:
            try:
                stats = await asyncio.to_thread(self._run_aggregation_cycle_sync)

                logger.info(
                    "Aggregation cycle done | inserted_rows=%d | processed_windows=%d | deleted_raw_rows=%d",
                    stats["inserted_rows"],
                    stats["processed_windows"],
                    stats["deleted_raw_rows"],
                )

            except Exception:
                logger.exception("Aggregator cycle failed")

            await asyncio.sleep(self.config.poll_interval)

        logger.info("Aggregator stopped")

    async def stop(self) -> None:
        self._running = False


# =========================
# Фабрика
# =========================

def build_aggregator_from_config(
    config_path: str | Path = "config/aggregator.yaml",
) -> Aggregator:
    config = load_aggregator_config(config_path)
    return Aggregator(config=config)


# =========================
# Локальный запуск
# =========================

async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    aggregator = build_aggregator_from_config(
        config_path="config/aggregator.yaml",
    )

    try:
        await aggregator.start()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received")
    finally:
        await aggregator.stop()


if __name__ == "__main__":
    asyncio.run(main())