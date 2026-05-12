"""
services/debug_collector.py

Назначение:
- диагностический опрос Modbus-устройств без записи в БД;
- проверка корректности address offset;
- проверка function code: holding/input;
- сравнение декодирования float32 и float32_swapped;
- вывод сырых регистров и декодированных значений в консоль.

Этот модуль нужен для первичной верификации:
1. правильности конфигурации devices.yaml;
2. корректности адресации Modbus;
3. корректного порядка слов при float32;
4. корректного типа регистра (holding vs input).

Важно:
- не использовать как production collector;
- не пишет в БД;
- запускается отдельно от writer.py.
"""

from __future__ import annotations

import asyncio
import logging
import math
import struct
from pathlib import Path
from typing import Any

import yaml
from pymodbus.client import AsyncModbusTcpClient

logger = logging.getLogger(__name__)


# =========================
# Загрузка конфига
# =========================

def load_devices_config(config_path: str | Path) -> list[dict[str, Any]]:
    path = Path(config_path)
    if not path.exists():
        raise FileNotFoundError(f"Config file not found: {path}")

    with path.open("r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}

    return raw.get("devices", [])


# =========================
# Декодирование
# =========================

def decode_float32(registers: list[int]) -> float:
    raw = struct.pack(">HH", registers[0], registers[1])
    return struct.unpack(">f", raw)[0]


def decode_float32_swapped(registers: list[int]) -> float:
    raw = struct.pack(">HH", registers[1], registers[0])
    return struct.unpack(">f", raw)[0]


def decode_uint16(registers: list[int]) -> int:
    return int(registers[0])


def decode_int16(registers: list[int]) -> int:
    value = registers[0]
    if value >= 0x8000:
        value -= 0x10000
    return value


def decode_uint32(registers: list[int]) -> int:
    return (registers[0] << 16) | registers[1]


def decode_int32(registers: list[int]) -> int:
    value = (registers[0] << 16) | registers[1]
    if value >= 0x80000000:
        value -= 0x100000000
    return value


def is_reasonable_number(value: Any) -> bool:
    """
    Грубая инженерная эвристика:
    отсеиваем nan/inf и совсем безумные величины.
    """
    if not isinstance(value, (int, float)):
        return False
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return False
    if abs(value) > 1e9:
        return False
    return True


# =========================
# Варианты адресации
# =========================

def candidate_offsets(address: int) -> list[tuple[str, int]]:
    """
    Проверяем несколько типичных вариантов адресации.

    Примеры:
    - 403059 -> 3058   (адресация от 400001)
    - 403059 -> 3059   (адресация от 400000)
    - 403059          (если прибор ожидает "как есть")
    """
    variants: list[tuple[str, int]] = []

    if address >= 400001:
        variants.append(("address_minus_400001", address - 400001))
    if address >= 400000:
        variants.append(("address_minus_400000", address - 400000))

    variants.append(("raw_address", address))

    # убрать дубликаты, сохранив порядок
    seen: set[int] = set()
    unique_variants: list[tuple[str, int]] = []
    for mode, value in variants:
        if value not in seen and value >= 0:
            seen.add(value)
            unique_variants.append((mode, value))

    return unique_variants


# =========================
# Диагностический клиент
# =========================

class DebugModbusClient:
    def __init__(self, host: str, port: int, unit_id: int, timeout: float = 1.0):
        self.host = host
        self.port = port
        self.unit_id = unit_id
        self.timeout = timeout
        self.client: AsyncModbusTcpClient | None = None

    async def connect(self) -> None:
        self.client = AsyncModbusTcpClient(host=self.host, port=self.port)
        connected = await self.client.connect()
        if not connected:
            raise ConnectionError(
                f"Cannot connect to {self.host}:{self.port}, unit_id={self.unit_id}"
            )

    async def close(self) -> None:
        if self.client is not None:
            self.client.close()

    async def try_read_holding(self, address: int, count: int) -> tuple[list[int] | None, str]:
        if self.client is None:
            raise RuntimeError("Client is not connected")

        try:
            response = await asyncio.wait_for(
                self.client.read_holding_registers(
                    address=address,
                    count=count,
                    slave=self.unit_id,
                ),
                timeout=self.timeout,
            )

            if response.isError():
                return None, f"modbus_error={response}"

            return list(response.registers), "ok"

        except Exception as exc:
            return None, f"exception={type(exc).__name__}: {exc}"

    async def try_read_input(self, address: int, count: int) -> tuple[list[int] | None, str]:
        if self.client is None:
            raise RuntimeError("Client is not connected")

        try:
            response = await asyncio.wait_for(
                self.client.read_input_registers(
                    address=address,
                    count=count,
                    slave=self.unit_id,
                ),
                timeout=self.timeout,
            )

            if response.isError():
                return None, f"modbus_error={response}"

            return list(response.registers), "ok"

        except Exception as exc:
            return None, f"exception={type(exc).__name__}: {exc}"


# =========================
# Вывод диагностики
# =========================

def print_register_analysis(
    *,
    device_name: str,
    metric_name: str,
    function_name: str,
    source_address: int,
    offset_mode: str,
    request_address: int,
    registers: list[int],
) -> None:
    print("=" * 100)
    print(f"DEVICE         : {device_name}")
    print(f"METRIC         : {metric_name}")
    print(f"FUNCTION       : {function_name}")
    print(f"SOURCE ADDRESS : {source_address}")
    print(f"OFFSET MODE    : {offset_mode}")
    print(f"REQUEST ADDR   : {request_address}")
    print(f"RAW REGISTERS  : {registers}")

    if len(registers) == 2:
        candidates: list[tuple[str, Any]] = []

        try:
            candidates.append(("float32", decode_float32(registers)))
        except Exception as exc:
            candidates.append(("float32", f"decode_error: {exc}"))

        try:
            candidates.append(("float32_swapped", decode_float32_swapped(registers)))
        except Exception as exc:
            candidates.append(("float32_swapped", f"decode_error: {exc}"))

        try:
            candidates.append(("uint32", decode_uint32(registers)))
        except Exception as exc:
            candidates.append(("uint32", f"decode_error: {exc}"))

        try:
            candidates.append(("int32", decode_int32(registers)))
        except Exception as exc:
            candidates.append(("int32", f"decode_error: {exc}"))

        hints: list[str] = []
        for label, value in candidates:
            print(f"{label:16}: {value}")
            if is_reasonable_number(value):
                hints.append(f"{label} plausible")

        if hints:
            print("HINT           :", "; ".join(hints))
        else:
            print("HINT           : no plausible decode detected")

    elif len(registers) == 1:
        candidates: list[tuple[str, Any]] = []

        try:
            candidates.append(("uint16", decode_uint16(registers)))
        except Exception as exc:
            candidates.append(("uint16", f"decode_error: {exc}"))

        try:
            candidates.append(("int16", decode_int16(registers)))
        except Exception as exc:
            candidates.append(("int16", f"decode_error: {exc}"))

        hints: list[str] = []
        for label, value in candidates:
            print(f"{label:16}: {value}")
            if is_reasonable_number(value):
                hints.append(f"{label} plausible")

        if hints:
            print("HINT           :", "; ".join(hints))
        else:
            print("HINT           : no plausible int decode detected")

    else:
        print("HINT           : unsupported register count for quick analysis")


async def debug_register(
    client: DebugModbusClient,
    device_name: str,
    register_cfg: dict[str, Any],
) -> None:
    metric_name = register_cfg["name"]
    source_address = int(register_cfg["address"])
    declared_type = register_cfg.get("data_type", "float32")
    declared_function = register_cfg.get("function", "holding")

    count = int(
        register_cfg.get(
            "count",
            2 if declared_type in {"float32", "float32_swapped", "uint32", "int32"} else 1,
        )
    )

    print("\n" + "#" * 100)
    print(f"Checking {device_name} :: {metric_name}")
    print(f"Declared address  : {source_address}")
    print(f"Declared data_type: {declared_type}")
    print(f"Declared function : {declared_function}")
    print(f"Read count        : {count}")

    found_any = False

    for offset_mode, request_address in candidate_offsets(source_address):
        if declared_function == "holding":
            registers, status = await client.try_read_holding(request_address, count)
        elif declared_function == "input":
            registers, status = await client.try_read_input(request_address, count)
        else:
            print(f"[ERROR] Unsupported function: {declared_function}")
            return

        if registers is None:
            print(
                f"[FAIL] mode={offset_mode:22s} request_addr={request_address:<8d} "
                f"function={declared_function:<7s} status={status}"
            )
            continue

        found_any = True
        print_register_analysis(
            device_name=device_name,
            metric_name=metric_name,
            function_name=declared_function,
            source_address=source_address,
            offset_mode=offset_mode,
            request_address=request_address,
            registers=registers,
        )

    if not found_any:
        print(f"[ERROR] No successful reads for {device_name} :: {metric_name}")


async def debug_device(device_cfg: dict[str, Any], metrics_filter: set[str] | None = None) -> None:
    device_name = device_cfg["name"]
    host = device_cfg["host"]
    port = int(device_cfg.get("port", 502))
    unit_id = int(device_cfg["unit_id"])
    timeout = float(device_cfg.get("timeout", 1.0))

    print("\n" + "=" * 100)
    print(f"DEVICE: {device_name} | HOST: {host}:{port} | UNIT_ID: {unit_id}")
    print("=" * 100)

    client = DebugModbusClient(host=host, port=port, unit_id=unit_id, timeout=timeout)

    try:
        await client.connect()

        registers = device_cfg.get("registers", [])
        for reg in registers:
            if not reg.get("enabled", True):
                continue

            if metrics_filter and reg["name"] not in metrics_filter:
                continue

            await debug_register(client, device_name, reg)

    finally:
        await client.close()


# =========================
# Точка входа
# =========================

async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )

    config_path = "config/devices.yaml"
    devices = load_devices_config(config_path)

    # Для первого пуска лучше проверять 1 устройство и 2-4 тега.
    device_name_filter = {
        "PowerMeter_1",
        # "PowerMeter_2",
        # "PowerMeter_3",
        # "PowerMeter_4",
        # "PowerMeter_Main",
    }

    metrics_filter = {
        "voltage_phase_avg",
        "current_avg",
        "frequency",
        "active_power_avg",
    }

    selected_devices = [d for d in devices if d["name"] in device_name_filter]

    if not selected_devices:
        raise RuntimeError("No devices selected for debugging")

    for device_cfg in selected_devices:
        await debug_device(device_cfg, metrics_filter=metrics_filter)


if __name__ == "__main__":
    asyncio.run(main())