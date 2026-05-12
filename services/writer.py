"""
services/writer.py

Назначение:
- принимать записи из asyncio.Queue, которые сформировал collector.py;
- буферизовать их в памяти;
- записывать в SQLite батчами;
- минимизировать количество операций записи на диск;
- обеспечить устойчивую работу при потоке данных от collector.

Writer НЕ:
- опрашивает устройства;
- не считает аналитику;
- не агрегирует данные;
- не читает Modbus.

Формат входной записи (ожидается из collector.py):
{
    "timestamp": 1713600000.123,
    "device_id": "PowerMeter_1",
    "metric": "active_power_avg",
    "value": 12.34
}
"""

from __future__ import annotations

import asyncio
import logging
import sqlite3
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


logger = logging.getLogger(__name__)


# =========================
# Конфигурационные модели
# =========================

@dataclass(slots=True)
class SQLiteConfig:
    journal_mode: str = "WAL"
    synchronous: str = "NORMAL"
    temp_store: str = "MEMORY"
    foreign_keys: bool = True


@dataclass(slots=True)
class WriterConfig:
    db_path: str = "data/energy.db"
    batch_size: int = 64
    flush_interval: float = 2.0
    max_retry_attempts: int = 3
    retry_delay: float = 0.5
    raw_table_name: str = "raw_data"
    auto_init_db: bool = True
    sqlite: SQLiteConfig = field(default_factory=SQLiteConfig)


# =========================
# Загрузка конфигурации
# =========================

def load_writer_config(config_path: str | Path) -> WriterConfig:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Writer config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    writer_raw = raw.get("writer", {})
    sqlite_raw = writer_raw.get("sqlite", {})

    sqlite_cfg = SQLiteConfig(
        journal_mode=str(sqlite_raw.get("journal_mode", "WAL")),
        synchronous=str(sqlite_raw.get("synchronous", "NORMAL")),
        temp_store=str(sqlite_raw.get("temp_store", "MEMORY")),
        foreign_keys=bool(sqlite_raw.get("foreign_keys", True)),
    )

    return WriterConfig(
        db_path=str(writer_raw.get("db_path", "data/energy.db")),
        batch_size=int(writer_raw.get("batch_size", 64)),
        flush_interval=float(writer_raw.get("flush_interval", 2.0)),
        max_retry_attempts=int(writer_raw.get("max_retry_attempts", 3)),
        retry_delay=float(writer_raw.get("retry_delay", 0.5)),
        raw_table_name=str(writer_raw.get("raw_table_name", "raw_data")),
        auto_init_db=bool(writer_raw.get("auto_init_db", True)),
        sqlite=sqlite_cfg,
    )


# =========================
# SQL-схема и инициализация
# =========================

def ensure_parent_dir(db_path: str | Path) -> None:
    Path(db_path).parent.mkdir(parents=True, exist_ok=True)


def make_create_table_sql(table_name: str) -> str:
    return f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp REAL NOT NULL,
        device_id TEXT NOT NULL,
        metric TEXT NOT NULL,
        value REAL NOT NULL,
        created_at REAL NOT NULL
    );
    """


def make_index_sql(table_name: str) -> str:
    return f"""
    CREATE INDEX IF NOT EXISTS idx_{table_name}_ts_device_metric
    ON {table_name} (timestamp, device_id, metric);
    """


def init_db(config: WriterConfig) -> None:
    ensure_parent_dir(config.db_path)

    conn = sqlite3.connect(config.db_path)
    try:
        conn.execute(f"PRAGMA journal_mode={config.sqlite.journal_mode};")
        conn.execute(f"PRAGMA synchronous={config.sqlite.synchronous};")
        conn.execute(f"PRAGMA temp_store={config.sqlite.temp_store};")
        conn.execute(f"PRAGMA foreign_keys={'ON' if config.sqlite.foreign_keys else 'OFF'};")

        conn.execute(make_create_table_sql(config.raw_table_name))
        conn.execute(make_index_sql(config.raw_table_name))
        conn.commit()
    finally:
        conn.close()


# =========================
# Преобразование записи
# =========================

def validate_record(record: dict[str, Any]) -> bool:
    required_keys = {"timestamp", "device_id", "metric", "value"}
    if not required_keys.issubset(record.keys()):
        return False

    try:
        float(record["timestamp"])
        str(record["device_id"])
        str(record["metric"])
        float(record["value"])
    except (TypeError, ValueError):
        return False

    return True


def normalize_record(record: dict[str, Any]) -> tuple[float, str, str, float, float]:
    return (
        float(record["timestamp"]),
        str(record["device_id"]),
        str(record["metric"]),
        float(record["value"]),
        time.time(),
    )


# =========================
# Writer
# =========================

class Writer:
    def __init__(
        self,
        queue: asyncio.Queue,
        config: WriterConfig,
    ):
        self.queue = queue
        self.config = config
        self._running = False
        self._buffer: list[tuple[float, str, str, float, float]] = []

    def _write_batch_sync(self, batch: list[tuple[float, str, str, float, float]]) -> None:
        if not batch:
            return

        insert_sql = f"""
        INSERT INTO {self.config.raw_table_name} (
            timestamp,
            device_id,
            metric,
            value,
            created_at
        )
        VALUES (?, ?, ?, ?, ?)
        """

        conn = sqlite3.connect(self.config.db_path)
        try:
            conn.execute(f"PRAGMA journal_mode={self.config.sqlite.journal_mode};")
            conn.execute(f"PRAGMA synchronous={self.config.sqlite.synchronous};")

            conn.executemany(insert_sql, batch)
            conn.commit()
        finally:
            conn.close()

    async def flush(self) -> int:
        if not self._buffer:
            return 0

        batch = self._buffer[:]
        self._buffer.clear()

        for attempt in range(1, self.config.max_retry_attempts + 1):
            try:
                await asyncio.to_thread(self._write_batch_sync, batch)
                logger.info("Writer flushed %d records to DB", len(batch))
                return len(batch)

            except Exception:
                logger.exception(
                    "Writer flush failed (attempt %d/%d)",
                    attempt,
                    self.config.max_retry_attempts,
                )

                if attempt < self.config.max_retry_attempts:
                    await asyncio.sleep(self.config.retry_delay)
                else:
                    self._buffer = batch + self._buffer
                    raise

        return 0

    async def start(self) -> None:
        if self.config.auto_init_db:
            init_db(self.config)

        self._running = True

        logger.info(
            "Writer started | db=%s | batch_size=%d | flush_interval=%.2fs",
            self.config.db_path,
            self.config.batch_size,
            self.config.flush_interval,
        )

        last_flush_time = time.monotonic()

        while self._running:
            timeout = max(
                0.0,
                self.config.flush_interval - (time.monotonic() - last_flush_time),
            )

            try:
                record = await asyncio.wait_for(self.queue.get(), timeout=timeout)

                if validate_record(record):
                    self._buffer.append(normalize_record(record))
                else:
                    logger.warning("Invalid record skipped: %s", record)

                self.queue.task_done()

                if len(self._buffer) >= self.config.batch_size:
                    written = await self.flush()
                    last_flush_time = time.monotonic()

                    logger.info(
                        "Writer batch flush complete | written=%d | queue_size=%d | buffer_size=%d",
                        written,
                        self.queue.qsize(),
                        len(self._buffer),
                    )

            except asyncio.TimeoutError:
                if self._buffer:
                    written = await self.flush()
                    logger.info(
                        "Writer timed flush complete | written=%d | queue_size=%d | buffer_size=%d",
                        written,
                        self.queue.qsize(),
                        len(self._buffer),
                    )
                last_flush_time = time.monotonic()

            except Exception:
                logger.exception("Writer main loop error")
                await asyncio.sleep(1.0)

        if self._buffer:
            try:
                written = await self.flush()
                logger.info("Final flush complete | written=%d", written)
            except Exception:
                logger.exception("Final flush failed during shutdown")

        logger.info("Writer stopped")

    async def stop(self) -> None:
        self._running = False


# =========================
# Фабрика
# =========================

def build_writer_from_config(
    queue: asyncio.Queue,
    config_path: str | Path = "config/writer.yaml",
) -> Writer:
    config = load_writer_config(config_path)
    return Writer(queue=queue, config=config)


# =========================
# Локальный тестовый запуск
# =========================

async def _demo_producer(queue: asyncio.Queue) -> None:
    for i in range(25):
        await queue.put(
            {
                "timestamp": time.time(),
                "device_id": "PowerMeter_1",
                "metric": "active_power_avg",
                "value": 10.0 + i,
            }
        )
        await asyncio.sleep(0.1)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    queue: asyncio.Queue = asyncio.Queue(maxsize=10000)
    writer = build_writer_from_config(
        queue=queue,
        config_path="config/writer.yaml",
    )

    writer_task = asyncio.create_task(writer.start())
    producer_task = asyncio.create_task(_demo_producer(queue))

    try:
        await producer_task
        await asyncio.sleep(3.0)
    finally:
        await writer.stop()
        await writer_task


if __name__ == "__main__":
    asyncio.run(main())