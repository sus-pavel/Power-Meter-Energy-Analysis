from __future__ import annotations

import asyncio
import math
import struct
from dataclasses import dataclass
from typing import Optional

from backend.app.core.config import settings
from backend.app.models.device import Device, DeviceRegister


class ModbusConnectionError(Exception):
    pass


class ModbusTimeoutError(Exception):
    pass


class ModbusReadError(Exception):
    pass


FUNCTION_CODES = {
    "holding": 0x03,
    "input": 0x04,
}


@dataclass(frozen=True)
class RegisterMeasurement:
    register_id: int
    metric: str
    value: float
    unit: Optional[str]


def _zero_based_address(register: DeviceRegister) -> int:
    if register.function_code == "holding" and register.address >= 40001:
        return register.address - 40001
    if register.function_code == "input" and register.address >= 30001:
        return register.address - 30001
    return register.address


def _register_count(data_type: str) -> int:
    return 1 if data_type in {"uint16", "int16"} else 2


def decode_registers(registers: list[int], data_type: str) -> float:
    if data_type == "uint16":
        return float(registers[0])
    if data_type == "int16":
        return float(struct.unpack(">h", struct.pack(">H", registers[0]))[0])
    if len(registers) < 2:
        raise ModbusReadError("Not enough registers returned")
    first, second = registers[0], registers[1]
    if data_type == "float32_swapped":
        first, second = second, first
    raw = struct.pack(">HH", first, second)
    if data_type in {"float32", "float32_swapped"}:
        value = struct.unpack(">f", raw)[0]
    elif data_type == "uint32":
        value = float(struct.unpack(">I", raw)[0])
    elif data_type == "int32":
        value = float(struct.unpack(">i", raw)[0])
    else:
        raise ModbusReadError(f"Unsupported data type: {data_type}")
    if not math.isfinite(value):
        raise ModbusReadError("Decoded value is not finite")
    return float(value)


async def read_register(device: Device, register: DeviceRegister) -> RegisterMeasurement:
    if register.function_code not in FUNCTION_CODES:
        raise ModbusReadError(f"Unsupported function code: {register.function_code}")
    timeout = settings.polling_modbus_timeout_sec
    writer: Optional[asyncio.StreamWriter] = None
    transaction_id = (device.id + register.id) % 65535
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(device.host, device.port),
            timeout=timeout,
        )
        count = _register_count(register.data_type)
        pdu = struct.pack(">BHH", FUNCTION_CODES[register.function_code], _zero_based_address(register), count)
        mbap = struct.pack(">HHHB", transaction_id, 0, len(pdu) + 1, device.unit_id)
        writer.write(mbap + pdu)
        await asyncio.wait_for(writer.drain(), timeout=timeout)
        header = await asyncio.wait_for(reader.readexactly(7), timeout=timeout)
        response_tid, protocol_id, length, unit_id = struct.unpack(">HHHB", header)
        if response_tid != transaction_id or protocol_id != 0 or unit_id != device.unit_id or length < 2:
            raise ModbusReadError("Invalid Modbus response header")
        pdu_response = await asyncio.wait_for(reader.readexactly(length - 1), timeout=timeout)
        if not pdu_response or pdu_response[0] & 0x80:
            raise ModbusReadError("Modbus exception response")
        if pdu_response[0] != FUNCTION_CODES[register.function_code] or len(pdu_response) < 2:
            raise ModbusReadError("Invalid Modbus response body")
        byte_count = pdu_response[1]
        data = pdu_response[2: 2 + byte_count]
        if len(data) != byte_count or byte_count % 2 != 0:
            raise ModbusReadError("Invalid register byte count")
        registers = [struct.unpack(">H", data[index:index + 2])[0] for index in range(0, byte_count, 2)]
        value = decode_registers(registers, register.data_type) * register.scale
        return RegisterMeasurement(register.id, register.metric, value, register.unit)
    except asyncio.TimeoutError as exc:
        raise ModbusTimeoutError("Modbus read timed out") from exc
    except OSError as exc:
        raise ModbusConnectionError(str(exc)) from exc
    finally:
        if writer is not None:
            writer.close()
            await writer.wait_closed()
