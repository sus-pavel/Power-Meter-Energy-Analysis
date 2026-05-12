"""
services/drpi_service.py

Назначение:
- читать 5-минутные агрегаты активной мощности из SQLite;
- рассчитывать production DRPI:
  1) по каждому счётчику,
  2) по сумме мощностей всех счётчиков;
- писать результаты в таблицу drpi_results.

Окно:
- 24 часа
- 5-минутная дискретизация
- 288 точек

Архитектурно:
- service = orchestration layer
- engine = calculation layer
- service должен уметь как автоматический цикл, так и единичный запуск с параметрами
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Literal

import pandas as pd
import yaml

from core.drpi_engine import DRPIEngine


logger = logging.getLogger(__name__)


# =========================
# Конфигурация
# =========================

SourceMode = Literal["all", "total", "all_plus_total"]


@dataclass(slots=True)
class DRPIServiceConfig:
    db_path: str = "data/energy.db"
    agg_table_name: str = "agg_5min"
    metric_name: str = "active_power_avg"
    results_table_name: str = "drpi_results"

    poll_interval: float = 60.0
    source_mode: SourceMode = "all_plus_total"
    window_size: int = 288

    q_baseline: float = 0.2
    flexible_share_target: float = 0.5
    w1: float = 0.5
    w2: float = 0.3
    w3: float = 0.2

    auto_init_db: bool = True


@dataclass(slots=True)
class DRPIParams:
    source_mode: SourceMode = "all_plus_total"
    window_size: int = 288
    q_baseline: float = 0.2
    flexible_share_target: float = 0.5
    w1: float = 0.5
    w2: float = 0.3
    w3: float = 0.2


def load_drpi_config(config_path: str | Path) -> DRPIServiceConfig:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"DRPI config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    cfg = raw.get("drpi", {})

    return DRPIServiceConfig(
        db_path=str(cfg.get("db_path", "data/energy.db")),
        agg_table_name=str(cfg.get("agg_table_name", "agg_5min")),
        metric_name=str(cfg.get("metric_name", "active_power_avg")),
        results_table_name=str(cfg.get("results_table_name", "drpi_results")),
        poll_interval=float(cfg.get("poll_interval", 60.0)),
        source_mode=str(cfg.get("source_mode", "all_plus_total")),
        window_size=int(cfg.get("window_size", 288)),
        q_baseline=float(cfg.get("q_baseline", 0.2)),
        flexible_share_target=float(cfg.get("flexible_share_target", 0.5)),
        w1=float(cfg.get("w1", 0.5)),
        w2=float(cfg.get("w2", 0.3)),
        w3=float(cfg.get("w3", 0.2)),
        auto_init_db=bool(cfg.get("auto_init_db", True)),
    )


# =========================
# Инициализация БД
# =========================

def init_db(config: DRPIServiceConfig) -> None:
    conn = sqlite3.connect(config.db_path)
    try:
        conn.execute(
            f"""
            CREATE TABLE IF NOT EXISTS {config.results_table_name} (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ts INTEGER NOT NULL,
                source_id TEXT NOT NULL,
                F1 REAL NOT NULL,
                F2 REAL NOT NULL,
                F3 REAL NOT NULL,
                R_raw REAL NOT NULL,
                DRPI REAL NOT NULL,
                created_at REAL NOT NULL,
                UNIQUE(ts, source_id)
            );
            """
        )

        conn.execute(
            f"""
            CREATE INDEX IF NOT EXISTS idx_{config.results_table_name}_ts_source
            ON {config.results_table_name} (ts, source_id);
            """
        )

        conn.commit()
    finally:
        conn.close()


# =========================
# SQL helpers
# =========================

def read_active_power_5min(
    conn: sqlite3.Connection,
    table_name: str,
    metric_name: str,
) -> pd.DataFrame:
    query = f"""
    SELECT
        window_end,
        device_id,
        mean_value
    FROM {table_name}
    WHERE metric = ?
    ORDER BY window_end, device_id
    """
    return pd.read_sql_query(query, conn, params=[metric_name])


def existing_result_keys(
    conn: sqlite3.Connection,
    table_name: str,
) -> set[tuple[int, str]]:
    rows = conn.execute(f"SELECT ts, source_id FROM {table_name}").fetchall()
    return {(int(ts), str(source_id)) for ts, source_id in rows}


def insert_results(
    conn: sqlite3.Connection,
    table_name: str,
    rows: list[tuple[int, str, float, float, float, float, float, float]],
) -> int:
    if not rows:
        return 0

    query = f"""
    INSERT OR IGNORE INTO {table_name} (
        ts, source_id, F1, F2, F3, R_raw, DRPI, created_at
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """

    conn.executemany(query, rows)
    conn.commit()
    return len(rows)


# =========================
# Сервис
# =========================

class DRPIService:
    def __init__(self, config: DRPIServiceConfig):
        self.config = config
        self._running = False

    def _make_engine(self, params: DRPIParams) -> DRPIEngine:
        return DRPIEngine(
            q_baseline=params.q_baseline,
            flexible_share_target=params.flexible_share_target,
            w1=params.w1,
            w2=params.w2,
            w3=params.w3,
        )

    def _prepare_sources(
        self,
        df: pd.DataFrame,
        source_mode: SourceMode,
    ) -> dict[str, pd.Series]:
        df["window_end"] = pd.to_datetime(df["window_end"], unit="s")

        sources: dict[str, pd.Series] = {}

        if source_mode in {"all", "all_plus_total"}:
            for device_id, group in df.groupby("device_id"):
                s = pd.Series(
                    group["mean_value"].values,
                    index=group["window_end"].values,
                    name=str(device_id),
                ).sort_index()
                sources[str(device_id)] = s

        if source_mode in {"total", "all_plus_total"}:
            pivot = df.pivot_table(
                index="window_end",
                columns="device_id",
                values="mean_value",
                aggfunc="mean",
            ).sort_index()

            total_series = pivot.sum(axis=1, min_count=1)
            total_series.name = "TOTAL"
            sources["TOTAL"] = total_series

        return sources

    def _build_rows_to_insert(
        self,
        conn: sqlite3.Connection,
        params: DRPIParams,
    ) -> tuple[list[tuple[int, str, float, float, float, float, float, float]], int]:
        df = read_active_power_5min(
            conn=conn,
            table_name=self.config.agg_table_name,
            metric_name=self.config.metric_name,
        )

        if df.empty:
            return [], 0

        sources = self._prepare_sources(df, params.source_mode)
        existing_keys = existing_result_keys(conn, self.config.results_table_name)
        engine = self._make_engine(params)

        rows_to_insert: list[tuple[int, str, float, float, float, float, float, float]] = []
        source_count = 0

        for source_id, series in sources.items():
            drpi_df = engine.compute_drpi_rolling(
                ts=series,
                window_size=params.window_size,
            )

            if drpi_df.empty:
                continue

            source_count += 1

            for ts_idx, row in drpi_df.iterrows():
                ts_int = int(pd.Timestamp(ts_idx).timestamp())
                key = (ts_int, str(source_id))
                if key in existing_keys:
                    continue

                rows_to_insert.append(
                    (
                        ts_int,
                        str(source_id),
                        float(row["F1"]),
                        float(row["F2"]),
                        float(row["F3"]),
                        float(row["R_raw"]),
                        float(row["DRPI"]),
                        time.time(),
                    )
                )

        return rows_to_insert, source_count

    def run_once_with_params(
        self,
        params: DRPIParams,
    ) -> dict[str, int]:
        """
        Единичный расчёт DRPI с явными параметрами.

        Это подготовка к будущему вызову из дашборда или API.
        В production-цикле используются default-параметры из YAML.
        """
        conn = sqlite3.connect(self.config.db_path)
        try:
            rows_to_insert, source_count = self._build_rows_to_insert(conn=conn, params=params)
            inserted = insert_results(
                conn=conn,
                table_name=self.config.results_table_name,
                rows=rows_to_insert,
            )
            return {
                "inserted": inserted,
                "sources": source_count,
            }
        finally:
            conn.close()

    def run_once_default(self) -> dict[str, int]:
        params = DRPIParams(
            source_mode=self.config.source_mode,
            window_size=self.config.window_size,
            q_baseline=self.config.q_baseline,
            flexible_share_target=self.config.flexible_share_target,
            w1=self.config.w1,
            w2=self.config.w2,
            w3=self.config.w3,
        )
        return self.run_once_with_params(params)

    async def start(self) -> None:
        if self.config.auto_init_db:
            init_db(self.config)

        self._running = True
        logger.info(
            "DRPI service started | db=%s | source=%s | window=%d | poll_interval=%.1fs",
            self.config.db_path,
            self.config.source_mode,
            self.config.window_size,
            self.config.poll_interval,
        )

        while self._running:
            try:
                stats = await asyncio.to_thread(self.run_once_default)
                logger.info(
                    "DRPI cycle done | inserted=%d | sources=%d",
                    stats["inserted"],
                    stats["sources"],
                )
            except Exception:
                logger.exception("DRPI cycle failed")

            await asyncio.sleep(self.config.poll_interval)

        logger.info("DRPI service stopped")

    async def stop(self) -> None:
        self._running = False


# =========================
# Фабрика
# =========================

def build_drpi_service_from_config(
    config_path: str | Path = "config/drpi.yaml",
) -> DRPIService:
    config = load_drpi_config(config_path)
    return DRPIService(config=config)


# =========================
# Локальный запуск
# =========================

async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    service = build_drpi_service_from_config("config/drpi.yaml")

    try:
        await service.start()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received")
    finally:
        await service.stop()


if __name__ == "__main__":
    asyncio.run(main())