from __future__ import annotations

import asyncio
import logging
from dataclasses import dataclass
from typing import Literal

import pandas as pd

from backend.app.core.config import settings
from backend.app.core.database import get_connection
from backend.app.analytics.prototype_compat import prototype_drpi_engine


logger = logging.getLogger(__name__)
SourceMode = Literal["all", "total", "all_plus_total"]


@dataclass
class DRPIRunStats:
    inserted: int
    sources: int


class AppDRPIService:
    def __init__(self) -> None:
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    def _read_agg(self, conn) -> pd.DataFrame:
        return pd.read_sql_query(
            """
            SELECT window_end, device_id, mean_value
            FROM measurements_agg_5min
            WHERE metric = ?
            ORDER BY window_end, device_id
            """,
            conn,
            params=[settings.analytics_metric_name],
        )

    def _prepare_sources(self, df: pd.DataFrame, source_mode: SourceMode) -> dict[str, pd.Series]:
        df["window_end"] = pd.to_datetime(df["window_end"], unit="s")
        sources: dict[str, pd.Series] = {}
        if source_mode in {"all", "all_plus_total"}:
            for device_id, group in df.groupby("device_id"):
                sources[str(device_id)] = pd.Series(
                    group["mean_value"].values,
                    index=group["window_end"].values,
                    name=str(device_id),
                ).sort_index()
        if source_mode in {"total", "all_plus_total"}:
            pivot = df.pivot_table(index="window_end", columns="device_id", values="mean_value", aggfunc="mean").sort_index()
            sources["TOTAL"] = pivot.sum(axis=1, min_count=1)
        return sources

    def run_once(self) -> DRPIRunStats:
        with get_connection() as conn:
            df = self._read_agg(conn)
            if df.empty:
                return DRPIRunStats(inserted=0, sources=0)
            engine = prototype_drpi_engine().DRPIEngine()
            sources = self._prepare_sources(df, settings.drpi_source_mode)  # type: ignore[arg-type]
            existing = {
                (float(row["ts"]), str(row["source_id"]))
                for row in conn.execute("SELECT ts, source_id FROM app_drpi_results").fetchall()
            }
            rows = []
            for source_id, series in sources.items():
                result = engine.compute_drpi_rolling(series, window_size=settings.drpi_window_size)
                if result.empty:
                    continue
                for ts_idx, row in result.iterrows():
                    ts = float(pd.Timestamp(ts_idx).timestamp())
                    if (ts, source_id) in existing:
                        continue
                    rows.append((ts, source_id, float(row["F1"]), float(row["F2"]), float(row["F3"]), float(row["R_raw"]), float(row["DRPI"])))
            before = conn.total_changes
            conn.executemany(
                """
                INSERT OR IGNORE INTO app_drpi_results (ts, source_id, F1, F2, F3, R_raw, DRPI)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                rows,
            )
            return DRPIRunStats(inserted=conn.total_changes - before, sources=len(sources))

    async def start(self) -> None:
        self._running = True
        while self._running:
            try:
                await asyncio.to_thread(self.run_once)
            except Exception:
                logger.exception("DRPI cycle failed")
            await asyncio.sleep(settings.drpi_poll_interval_sec)

    async def stop(self) -> None:
        self._running = False


drpi_service = AppDRPIService()
