"""
main.py

Назначение:
- единая точка запуска пайплайна сбора, записи, агрегации и расчёта DRPI;
- создаёт общую asyncio.Queue;
- запускает services.collector, services.writer, services.aggregator и services.drpi_service;
- обрабатывает корректное завершение по Ctrl+C / сигналам ОС.

Состав пайплайна:
    Modbus devices --> collector.py --> asyncio.Queue --> writer.py --> SQLite(raw_data)
                                                           |
                                                           v
                                                     aggregator.py
                                                           |
                                                           +--> agg_5min
                                                           +--> agg_30min
                                                           |
                                                           v
                                                     drpi_service.py
                                                           |
                                                           v
                                                     drpi_results
"""

from __future__ import annotations

import asyncio
import logging
import signal
from pathlib import Path

from services.collector import build_collector_from_config
from services.writer import build_writer_from_config
from services.aggregator import build_aggregator_from_config
from services.drpi_service import build_drpi_service_from_config


# =========================
# Базовая конфигурация
# =========================

QUEUE_MAXSIZE = 10000

DEVICES_CONFIG_PATH = Path("config/devices.yaml")
WRITER_CONFIG_PATH = Path("config/writer.yaml")
AGGREGATOR_CONFIG_PATH = Path("config/aggregator.yaml")
DRPI_CONFIG_PATH = Path("config/drpi.yaml")

COLLECT_INTERVAL = 2.0


# =========================
# Настройка логирования
# =========================

def setup_logging() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


logger = logging.getLogger(__name__)


# =========================
# Управление остановкой
# =========================

class PipelineApp:
    def __init__(self) -> None:
        self.queue: asyncio.Queue = asyncio.Queue(maxsize=QUEUE_MAXSIZE)
        self.stop_event = asyncio.Event()

        self.collector = build_collector_from_config(
            queue=self.queue,
            config_path=DEVICES_CONFIG_PATH,
            interval=COLLECT_INTERVAL,
        )

        self.writer = build_writer_from_config(
            queue=self.queue,
            config_path=WRITER_CONFIG_PATH,
        )

        self.aggregator = build_aggregator_from_config(
            config_path=AGGREGATOR_CONFIG_PATH,
        )

        self.drpi_service = build_drpi_service_from_config(
            config_path=DRPI_CONFIG_PATH,
        )

        self.collector_task: asyncio.Task | None = None
        self.writer_task: asyncio.Task | None = None
        self.aggregator_task: asyncio.Task | None = None
        self.drpi_task: asyncio.Task | None = None

    def request_stop(self) -> None:
        if not self.stop_event.is_set():
            logger.info("Shutdown requested")
            self.stop_event.set()

    async def start(self) -> None:
        logger.info("Starting pipeline")
        logger.info("Devices config: %s", DEVICES_CONFIG_PATH)
        logger.info("Writer config: %s", WRITER_CONFIG_PATH)
        logger.info("Aggregator config: %s", AGGREGATOR_CONFIG_PATH)
        logger.info("DRPI config: %s", DRPI_CONFIG_PATH)

        self.collector_task = asyncio.create_task(
            self.collector.start(),
            name="collector_task",
        )
        self.writer_task = asyncio.create_task(
            self.writer.start(),
            name="writer_task",
        )
        self.aggregator_task = asyncio.create_task(
            self.aggregator.start(),
            name="aggregator_task",
        )
        self.drpi_task = asyncio.create_task(
            self.drpi_service.start(),
            name="drpi_task",
        )

        await self.stop_event.wait()
        await self.shutdown()

    async def shutdown(self) -> None:
        # 1. Останавливаем collector, чтобы новые данные больше не поступали в очередь
        logger.info("Stopping collector")
        await self.collector.stop()

        # 2. Даём writer возможность дописать всё, что уже в очереди
        logger.info("Waiting until queue is drained")
        await self.queue.join()

        # 3. Останавливаем writer
        logger.info("Stopping writer")
        await self.writer.stop()

        # 4. Останавливаем агрегатор и DRPI
        logger.info("Stopping aggregator")
        await self.aggregator.stop()

        logger.info("Stopping DRPI service")
        await self.drpi_service.stop()

        tasks = [
            task
            for task in [
                self.collector_task,
                self.writer_task,
                self.aggregator_task,
                self.drpi_task,
            ]
            if task is not None
        ]

        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for task, result in zip(tasks, results, strict=False):
                if isinstance(result, Exception):
                    logger.exception("Task %s finished with error: %s", task.get_name(), result)
                else:
                    logger.info("Task %s finished successfully", task.get_name())

        logger.info("Pipeline stopped")


# =========================
# Регистрация сигналов ОС
# =========================

def register_signal_handlers(app: PipelineApp) -> None:
    loop = asyncio.get_running_loop()

    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, app.request_stop)
        except NotImplementedError:
            logger.warning("Signal handlers are not supported on this platform")


# =========================
# Точка входа
# =========================

async def main() -> None:
    setup_logging()

    app = PipelineApp()
    register_signal_handlers(app)

    try:
        await app.start()
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received")
        app.request_stop()
        await app.shutdown()
    except Exception:
        logger.exception("Fatal pipeline error")
        app.request_stop()
        await app.shutdown()
        raise


if __name__ == "__main__":
    asyncio.run(main())