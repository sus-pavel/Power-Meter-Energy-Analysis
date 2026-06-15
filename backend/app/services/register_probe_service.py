from __future__ import annotations

import asyncio
import json
import math
import struct
from typing import Any, Optional

import yaml

from backend.app.core.config import settings
from backend.app.models.candidate import DiscoveredCandidate


REGISTER_FUNCTIONS = {
    "holding": 0x03,
    "input": 0x04,
}


def load_probe_profiles() -> dict[str, Any]:
    with settings.probe_profiles_path.open("r", encoding="utf-8") as handle:
        profiles = yaml.safe_load(handle) or {}
    if not isinstance(profiles, dict):
        return {}
    return profiles


def _to_zero_based_address(register_address: int, function_code: str) -> int:
    if function_code == "holding" and register_address >= 40001:
        return register_address - 40001
    if function_code == "input" and register_address >= 30001:
        return register_address - 30001
    return register_address


def _decode_registers(registers: list[int], data_type: str) -> Optional[float]:
    if len(registers) < 2:
        return None
    high, low = registers[0], registers[1]
    if data_type == "float32_swapped":
        high, low = low, high
    if data_type not in {"float32", "float32_swapped"}:
        return None
    raw = struct.pack(">HH", high, low)
    value = struct.unpack(">f", raw)[0]
    if not math.isfinite(value):
        return None
    return float(value)


def _is_valid_value(value: Optional[float]) -> bool:
    if value is None:
        return False
    return -1_000_000_000.0 <= value <= 1_000_000_000.0


async def _read_registers(
    candidate: DiscoveredCandidate,
    *,
    function_code: str,
    register_address: int,
    count: int,
) -> Optional[list[int]]:
    writer: Optional[asyncio.StreamWriter] = None
    transaction_id = (candidate.id + register_address) % 65535
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(candidate.ip_address, candidate.port),
            timeout=settings.register_probe_timeout_seconds,
        )
        start_address = _to_zero_based_address(register_address, function_code)
        pdu = struct.pack(">BHH", REGISTER_FUNCTIONS[function_code], start_address, count)
        mbap = struct.pack(">HHHB", transaction_id, 0, len(pdu) + 1, candidate.unit_id)
        writer.write(mbap + pdu)
        await asyncio.wait_for(writer.drain(), timeout=settings.register_probe_timeout_seconds)
        header = await asyncio.wait_for(reader.readexactly(7), timeout=settings.register_probe_timeout_seconds)
        response_tid, protocol_id, length, response_unit = struct.unpack(">HHHB", header)
        if response_tid != transaction_id or protocol_id != 0 or response_unit != candidate.unit_id or length < 2:
            return None
        pdu_response = await asyncio.wait_for(reader.readexactly(length - 1), timeout=settings.register_probe_timeout_seconds)
        if not pdu_response or pdu_response[0] & 0x80:
            return None
        if pdu_response[0] != REGISTER_FUNCTIONS[function_code] or len(pdu_response) < 2:
            return None
        byte_count = pdu_response[1]
        register_bytes = pdu_response[2: 2 + byte_count]
        if len(register_bytes) != byte_count or byte_count % 2 != 0:
            return None
        return [
            struct.unpack(">H", register_bytes[index:index + 2])[0]
            for index in range(0, byte_count, 2)
        ]
    except (OSError, asyncio.IncompleteReadError, asyncio.TimeoutError, KeyError, struct.error):
        return None
    finally:
        if writer is not None:
            writer.close()
            await writer.wait_closed()


async def probe_candidate(candidate: DiscoveredCandidate) -> list[dict]:
    profiles = load_probe_profiles()
    stored_results: list[dict] = []
    for profile in profiles.values():
        if not isinstance(profile, dict):
            continue
        data_types = profile.get("data_types", [])
        if not isinstance(data_types, list):
            continue
        for function_code, key in (("holding", "holding_registers"), ("input", "input_registers")):
            addresses = profile.get(key, [])
            if not isinstance(addresses, list):
                continue
            for register_address in addresses:
                await asyncio.sleep(settings.register_probe_delay_seconds)
                registers = await _read_registers(
                    candidate,
                    function_code=function_code,
                    register_address=int(register_address),
                    count=2,
                )
                raw_value = json.dumps(registers) if registers is not None else None
                for data_type in data_types:
                    decoded_value = _decode_registers(registers or [], str(data_type))
                    stored_results.append(
                        {
                            "register_address": int(register_address),
                            "function_code": function_code,
                            "data_type": str(data_type),
                            "raw_value": raw_value,
                            "decoded_value": decoded_value,
                            "valid": _is_valid_value(decoded_value),
                        }
                    )
    return stored_results
