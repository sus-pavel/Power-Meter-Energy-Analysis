"""
services/collector.py

Назначение:
- опрос Modbus TCP устройств с заданной периодичностью;
- чтение списка устройств и регистров из config/devices.yaml;
- декодирование значений в унифицированный формат;
- передача записей в asyncio.Queue для writer.py.

Формат записи:
{
    "timestamp": 1713600000.123,
    "device_id": "PowerMeter_1",
    "metric": "active_power_avg",
    "value": 0.025
}

Подтверждённая для текущих счётчиков схема:
- function code: holding
- address_mode: minus_400000
- data_type: float32

Текущий рабочий режим:
- interval = 2.0 c
- timeout = 1.5 c (задаётся в devices.yaml)
- последовательное чтение регистров внутри устройства
"""

from __future__ import annotations

import asyncio
import logging
import struct
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from pymodbus.client import AsyncModbusTcpClient
from pymodbus.exceptions import ConnectionException


logger = logging.getLogger(__name__)


# =========================
# Конфигурационные модели
# =========================

@dataclass(slots=True)
class RegisterConfig:
    name: str
    address: int
    data_type: str = "float32"
    scale: float = 1.0
    function: str = "holding"
    count: int | None = None
    enabled: bool = True

    @property
    def register_count(self) -> int:
        if self.count is not None:
            return self.count

        if self.data_type in {"float32", "float32_swapped", "uint32", "int32"}:
            return 2

        return 1


@dataclass(slots=True)
class DeviceConfig:
    name: str
    host: str
    port: int
    unit_id: int
    enabled: bool
    timeout: float
    address_mode: str
    registers: list[RegisterConfig]


# =========================
# Загрузка конфигурации
# =========================

def load_devices_config(config_path: str | Path) -> list[DeviceConfig]:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    devices_raw = raw.get("devices", [])
    devices: list[DeviceConfig] = []

    for device in devices_raw:
        registers: list[RegisterConfig] = []
        for reg in device.get("registers", []):
            registers.append(
                RegisterConfig(
                    name=reg["name"],
                    address=int(reg["address"]),
                    data_type=reg.get("data_type", reg.get("type", "float32")),
                    scale=float(reg.get("scale", 1.0)),
                    function=reg.get("function", "holding"),
                    count=reg.get("count"),
                    enabled=bool(reg.get("enabled", True)),
                )
            )

        devices.append(
            DeviceConfig(
                name=device["name"],
                host=device["host"],
                port=int(device.get("port", 502)),
                unit_id=int(device["unit_id"]),
                enabled=bool(device.get("enabled", True)),
                timeout=float(device.get("timeout", 1.5)),
                address_mode=device.get("address_mode", "minus_400000"),
                registers=registers,
            )
        )

    return [d for d in devices if d.enabled]


# =========================
# Адресация Modbus
# =========================

def modbus_reference_to_offset(address: int, address_mode: str) -> int:
    """
    Преобразование референсного адреса вида 4xxxx в offset для pymodbus.

    Поддерживаемые режимы:
    - minus_400000: 403059 -> 3059
    - minus_400001: 403059 -> 3058
    - raw:          403059 -> 403059

    Для текущих счётчиков подтверждено:
    - address_mode = minus_400000
    """
    if address_mode == "minus_400000":
        if address >= 400000:
            return address - 400000
        return address

    if address_mode == "minus_400001":
        if address >= 400001:
            return address - 400001
        return address

    if address_mode == "raw":
        return address

    raise ValueError(f"Unsupported address_mode: {address_mode}")


# =========================
# Декодирование
# =========================

def decode_registers(registers: list[int], data_type: str) -> float | int:
    if data_type == "float32":
        if len(registers) != 2:
            raise ValueError(f"float32 requires 2 registers, got {len(registers)}")
        raw = struct.pack(">HH", registers[0], registers[1])
        return struct.unpack(">f", raw)[0]

    if data_type == "float32_swapped":
        if len(registers) != 2:
            raise ValueError(f"float32_swapped requires 2 registers, got {len(registers)}")
        raw = struct.pack(">HH", registers[1], registers[0])
        return struct.unpack(">f", raw)[0]

    if data_type == "uint16":
        if len(registers) != 1:
            raise ValueError(f"uint16 requires 1 register, got {len(registers)}")
        return int(registers[0])

    if data_type == "int16":
        if len(registers) != 1:
            raise ValueError(f"int16 requires 1 register, got {len(registers)}")
        value = registers[0]
        if value >= 0x8000:
            value -= 0x10000
        return value

    if data_type == "uint32":
        if len(registers) != 2:
            raise ValueError(f"uint32 requires 2 registers, got {len(registers)}")
        return (registers[0] << 16) | registers[1]

    if data_type == "int32":
        if len(registers) != 2:
            raise ValueError(f"int32 requires 2 registers, got {len(registers)}")
        value = (registers[0] << 16) | registers[1]
        if value >= 0x80000000:
            value -= 0x100000000
        return value

    raise ValueError(f"Unsupported data_type: {data_type}")


# =========================
# Устройство Modbus
# =========================

class ModbusDevice:
    def __init__(self, config: DeviceConfig):
        self.config = config
        self.client: AsyncModbusTcpClient | None = None
        self._connect_lock = asyncio.Lock()
        self._io_lock = asyncio.Lock()

    async def connect(self) -> None:
        """
        Подключение к устройству.
        Используем отдельный lock, чтобы не было гонок reconnect.
        """
        async with self._connect_lock:
            if self.client is not None and getattr(self.client, "connected", False):
                return

            if self.client is not None:
                try:
                    self.client.close()
                except Exception:
                    logger.exception("Error while closing stale client for %s", self.config.name)

            self.client = AsyncModbusTcpClient(
                host=self.config.host,
                port=self.config.port,
            )

            connected = await self.client.connect()
            if not connected:
                raise ConnectionError(
                    f"Failed to connect to {self.config.name} "
                    f"({self.config.host}:{self.config.port}, unit_id={self.config.unit_id})"
                )

            logger.info(
                "Connected to %s (%s:%s, unit_id=%s)",
                self.config.name,
                self.config.host,
                self.config.port,
                self.config.unit_id,
            )

    async def ensure_connection(self) -> None:
        if self.client is None or not getattr(self.client, "connected", False):
            await self.connect()

    async def close(self) -> None:
        async with self._connect_lock:
            if self.client is not None:
                try:
                    self.client.close()
                except Exception:
                    logger.exception("Error while closing client for %s", self.config.name)

    async def _mark_connection_broken(self) -> None:
        """
        Закрывает клиент после timeout/connection error.
        На следующем запросе ensure_connection() выполнит reconnect.
        """
        await self.close()
        self.client = None

    async def read_register(self, reg: RegisterConfig, timestamp: float) -> dict[str, Any] | None:
        if not reg.enabled:
            return None

        try:
            await self.ensure_connection()

            if self.client is None:
                return None

            address = modbus_reference_to_offset(reg.address, self.config.address_mode)
            count = reg.register_count

            async with self._io_lock:
                # Повторно проверяем соединение прямо перед I/O
                if self.client is None or not getattr(self.client, "connected", False):
                    await self.ensure_connection()

                if self.client is None:
                    return None

                if reg.function == "holding":
                    response = await asyncio.wait_for(
                        self.client.read_holding_registers(
                            address=address,
                            count=count,
                            slave=self.config.unit_id,
                        ),
                        timeout=self.config.timeout,
                    )

                elif reg.function == "input":
                    response = await asyncio.wait_for(
                        self.client.read_input_registers(
                            address=address,
                            count=count,
                            slave=self.config.unit_id,
                        ),
                        timeout=self.config.timeout,
                    )

                else:
                    raise ValueError(f"Unsupported function: {reg.function}")

            if response.isError():
                logger.warning(
                    "Modbus error: device=%s metric=%s address=%s offset=%s function=%s response=%s",
                    self.config.name,
                    reg.name,
                    reg.address,
                    address,
                    reg.function,
                    response,
                )
                return None

            value = decode_registers(list(response.registers), reg.data_type)
            value = float(value) * reg.scale

            return {
                "timestamp": timestamp,
                "device_id": self.config.name,
                "metric": reg.name,
                "value": value,
            }

        except asyncio.TimeoutError:
            logger.warning(
                "Timeout: device=%s metric=%s address=%s function=%s",
                self.config.name,
                reg.name,
                reg.address,
                reg.function,
            )
            await self._mark_connection_broken()
            return None

        except ConnectionException:
            logger.error(
                "Read failed: device=%s metric=%s address=%s function=%s",
                self.config.name,
                reg.name,
                reg.address,
                reg.function,
                exc_info=True,
            )
            await self._mark_connection_broken()
            return None

        except Exception:
            logger.exception(
                "Read failed: device=%s metric=%s address=%s function=%s",
                self.config.name,
                reg.name,
                reg.address,
                reg.function,
            )
            await self._mark_connection_broken()
            return None

    async def poll(self) -> list[dict[str, Any]]:
        """
        Последовательное чтение регистров внутри одного устройства.

        Это принципиально важно для устойчивости:
        - исключает конкурентный доступ к одному Modbus client/socket;
        - уменьшает риск лавины reconnect;
        - лучше подходит для gateway/сервера с несколькими unit_id.
        """
        timestamp = time.time()
        results: list[dict[str, Any]] = []

        for reg in self.config.registers:
            if not reg.enabled:
                continue

            record = await self.read_register(reg, timestamp)
            if record is not None:
                results.append(record)

        return results


# =========================
# Collector
# =========================

class Collector:
    def __init__(
        self,
        devices: list[ModbusDevice],
        queue: asyncio.Queue,
        interval: float = 2.0,
        drop_if_queue_full: bool = True,
    ):
        self.devices = devices
        self.queue = queue
        self.interval = interval
        self.drop_if_queue_full = drop_if_queue_full
        self._running = False

    async def start(self) -> None:
        self._running = True

        for device in self.devices:
            try:
                await device.connect()
            except Exception:
                logger.exception("Initial connect failed for %s", device.config.name)

        logger.info("Collector started with %d devices", len(self.devices))

        while self._running:
            cycle_started_at = time.monotonic()

            # Устройства можно опрашивать параллельно,
            # но внутри каждого устройства чтение уже последовательное.
            poll_tasks = [device.poll() for device in self.devices]
            all_results = await asyncio.gather(*poll_tasks, return_exceptions=True)

            records_enqueued = 0

            for result in all_results:
                if isinstance(result, Exception):
                    logger.exception("Polling cycle failed", exc_info=result)
                    continue

                for record in result:
                    if self.drop_if_queue_full and self.queue.full():
                        logger.warning(
                            "Queue full, record dropped: device=%s metric=%s",
                            record["device_id"],
                            record["metric"],
                        )
                        continue

                    await self.queue.put(record)
                    records_enqueued += 1

            elapsed = time.monotonic() - cycle_started_at
            sleep_time = max(0.0, self.interval - elapsed)

            logger.info(
                "Collector cycle done: records=%d elapsed=%.3fs sleep=%.3fs queue_size=%d",
                records_enqueued,
                elapsed,
                sleep_time,
                self.queue.qsize(),
            )

            await asyncio.sleep(sleep_time)

    async def stop(self) -> None:
        self._running = False
        for device in self.devices:
            await device.close()
        logger.info("Collector stopped")


# =========================
# Фабрика
# =========================

def build_collector_from_config(
    queue: asyncio.Queue,
    config_path: str | Path = "config/devices.yaml",
    interval: float = 2.0,
) -> Collector:
    device_configs = load_devices_config(config_path)
    devices = [ModbusDevice(cfg) for cfg in device_configs]
    return Collector(devices=devices, queue=queue, interval=interval)


# =========================
# Локальный запуск
# =========================

async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    queue: asyncio.Queue = asyncio.Queue(maxsize=10000)
    collector = build_collector_from_config(
        queue=queue,
        config_path="config/devices.yaml",
        interval=2.0,
    )

    try:
        await collector.start()
        logger.info("Collector cycle elapsed=%.3f sec", elapsed)
    except KeyboardInterrupt:
        logger.info("KeyboardInterrupt received")
    finally:
        await collector.stop()


if __name__ == "__main__":
    asyncio.run(main())