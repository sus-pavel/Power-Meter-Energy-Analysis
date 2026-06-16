from __future__ import annotations

import asyncio
import json
import math
import sqlite3
import struct
import time
from dataclasses import dataclass
from typing import Any, Optional

import yaml

from backend.app.core.config import settings
from backend.app.core.vendor_profiles import get_generic_profile, match_vendor_profile
from backend.app.models.candidate import DiscoveredCandidate


REGISTER_FUNCTIONS = {
    "holding": 0x03,
    "input": 0x04,
}

DEVICE_ID_OBJECTS = {
    0x00: "VendorName",
    0x01: "ProductCode",
    0x02: "MajorMinorRevision",
    0x03: "VendorUrl",
    0x04: "ProductName",
    0x05: "ModelName",
    0x06: "UserApplicationName",
}


@dataclass(frozen=True)
class ProbeRegister:
    metric: str
    address: int
    function_code: str
    data_type: str
    scale: float = 1.0
    unit: Optional[str] = None
    required: bool = True
    address_mode: str = "reference"


@dataclass(frozen=True)
class ProbePlan:
    profile_id: str
    profile_source: str
    quality: str
    registers: list[ProbeRegister]
    inferred: dict[str, Any]


@dataclass(frozen=True)
class DeviceIdentification:
    supported: bool
    fields: dict[str, str]
    raw: Optional[str]
    error: Optional[str]


@dataclass(frozen=True)
class RegisterReadOutcome:
    status: str
    registers: Optional[list[int]]
    exception_code: Optional[int]
    response_time_ms: Optional[float]
    failure_reason: Optional[str]
    raw_value: Optional[str]


def _register_count(data_type: str) -> int:
    if data_type in {"float32", "float32_swapped", "uint32", "int32"}:
        return 2
    return 1


def _decode_registers(registers: list[int], data_type: str, scale: float) -> Optional[float]:
    try:
        if data_type == "uint16":
            value = float(registers[0])
        elif data_type == "int16":
            raw = registers[0]
            value = float(raw - 0x10000 if raw >= 0x8000 else raw)
        elif data_type in {"float32", "float32_swapped"}:
            if len(registers) < 2:
                return None
            high, low = registers[0], registers[1]
            if data_type == "float32_swapped":
                high, low = low, high
            value = float(struct.unpack(">f", struct.pack(">HH", high, low))[0])
        elif data_type == "uint32":
            if len(registers) < 2:
                return None
            value = float((registers[0] << 16) | registers[1])
        elif data_type == "int32":
            if len(registers) < 2:
                return None
            raw_value = (registers[0] << 16) | registers[1]
            value = float(raw_value - 0x100000000 if raw_value >= 0x80000000 else raw_value)
        else:
            return None
        decoded = value * scale
        return decoded if math.isfinite(decoded) else None
    except (IndexError, struct.error):
        return None


def _to_zero_based_address(register: ProbeRegister) -> int:
    address = register.address
    if register.address_mode == "minus_400000" and address >= 400000:
        return address - 400000
    if register.address_mode == "minus_400001" and address >= 400001:
        return address - 400001
    if register.address_mode == "minus_300000" and address >= 300000:
        return address - 300000
    if register.address_mode == "minus_300001" and address >= 300001:
        return address - 300001
    if register.function_code == "holding" and address >= 40001 and address < 400000:
        return address - 40001
    if register.function_code == "input" and address >= 30001 and address < 300000:
        return address - 30001
    return address


def _coerce_function_code(value: str) -> str:
    lowered = str(value).strip().lower()
    if lowered in {"holding", "fc03", "03", "3"}:
        return "holding"
    if lowered in {"input", "fc04", "04", "4"}:
        return "input"
    return lowered


def _load_config_file_registers(candidate: DiscoveredCandidate) -> Optional[ProbePlan]:
    path = settings.devices_config_path
    if not path.exists():
        return None
    with path.open("r", encoding="utf-8") as handle:
        raw = yaml.safe_load(handle) or {}
    for device in raw.get("devices", []):
        if str(device.get("host")) != candidate.ip_address:
            continue
        if int(device.get("port", 502)) != candidate.port:
            continue
        if int(device.get("unit_id", 1)) != candidate.unit_id:
            continue
        address_mode = str(device.get("address_mode", "reference"))
        registers: list[ProbeRegister] = []
        for register in device.get("registers", []):
            if not bool(register.get("enabled", True)):
                continue
            registers.append(
                ProbeRegister(
                    metric=str(register.get("name") or register.get("metric") or "configured_register"),
                    address=int(register["address"]),
                    function_code=_coerce_function_code(register.get("function", "holding")),
                    data_type=str(register.get("data_type", register.get("type", "float32"))),
                    scale=float(register.get("scale", 1.0)),
                    unit=register.get("unit"),
                    required=bool(register.get("required", True)),
                    address_mode=address_mode,
                )
            )
        return ProbePlan(
            profile_id=f"config_file:{device.get('name', candidate.ip_address)}",
            profile_source="config",
            quality="validated_from_config",
            registers=registers,
            inferred={"source_file": str(path), "device_name": device.get("name")},
        )
    return None


def _load_persisted_registers(conn: sqlite3.Connection, candidate: DiscoveredCandidate) -> Optional[ProbePlan]:
    rows = conn.execute(
        """
        SELECT d.id AS device_id, d.name AS device_name, r.*
        FROM devices d
        JOIN device_registers r ON r.device_id = d.id
        WHERE d.host = ? AND d.port = ? AND d.unit_id = ? AND r.enabled = 1
        ORDER BY r.metric, r.address
        """,
        (candidate.ip_address, candidate.port, candidate.unit_id),
    ).fetchall()
    if not rows:
        return None
    registers = [
        ProbeRegister(
            metric=row["metric"],
            address=row["address"],
            function_code=_coerce_function_code(row["function_code"]),
            data_type=row["data_type"],
            scale=float(row["scale"]),
            unit=row["unit"],
            required=True,
        )
        for row in rows
    ]
    first = rows[0]
    return ProbePlan(
        profile_id=f"device:{first['device_id']}",
        profile_source="persisted_config",
        quality="validated_from_config",
        registers=registers,
        inferred={"device_id": first["device_id"], "device_name": first["device_name"]},
    )


def resolve_probe_plan(
    candidate: DiscoveredCandidate,
    conn: Optional[sqlite3.Connection],
    identification: DeviceIdentification,
) -> ProbePlan:
    if conn is not None:
        persisted = _load_persisted_registers(conn, candidate)
        if persisted is not None:
            return persisted
    config_file = _load_config_file_registers(candidate)
    if config_file is not None:
        return config_file

    matched_profile = match_vendor_profile(identification.fields)
    if matched_profile is not None:
        return ProbePlan(
            profile_id=matched_profile.vendor_key,
            profile_source="vendor_default",
            quality="vendor_profile_matched",
            registers=[],
            inferred={
                "vendor_name": matched_profile.vendor_name,
                "needs_verification": matched_profile.needs_verification,
                "notes": matched_profile.notes,
            },
        )

    generic = get_generic_profile()
    return ProbePlan(
        profile_id=generic.vendor_key,
        profile_source="generic",
        quality="generic_modbus_detected",
        registers=[],
        inferred={
            "needs_manual_mapping": True,
            "notes": "No configured register profile matched this endpoint.",
        },
    )


def _parse_device_identification_response(pdu_response: bytes) -> dict[str, Any]:
    if len(pdu_response) < 7 or pdu_response[0] != 0x2B or pdu_response[1] != 0x0E:
        raise ValueError("Invalid FC43/14 response")
    object_count = pdu_response[6]
    offset = 7
    objects: dict[str, str] = {}
    raw_objects: dict[str, str] = {}
    for _ in range(object_count):
        if offset + 2 > len(pdu_response):
            break
        object_id = pdu_response[offset]
        length = pdu_response[offset + 1]
        offset += 2
        value_bytes = pdu_response[offset: offset + length]
        offset += length
        value = value_bytes.decode("utf-8", errors="replace").strip()
        key = DEVICE_ID_OBJECTS.get(object_id, f"Object{object_id}")
        objects[key] = value
        raw_objects[str(object_id)] = value
    return {"objects": objects, "raw_objects": raw_objects}


async def read_device_identification(candidate: DiscoveredCandidate) -> DeviceIdentification:
    writer: Optional[asyncio.StreamWriter] = None
    transaction_id = (int(time.monotonic() * 1000) + candidate.id + candidate.unit_id + 0x2B) % 65535 or 1
    started = time.perf_counter()
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(candidate.ip_address, candidate.port),
            timeout=settings.register_probe_timeout_seconds,
        )
        pdu = bytes([0x2B, 0x0E, 0x01, 0x00])
        mbap = struct.pack(">HHHB", transaction_id, 0, len(pdu) + 1, candidate.unit_id)
        writer.write(mbap + pdu)
        await asyncio.wait_for(writer.drain(), timeout=settings.register_probe_timeout_seconds)
        header = await asyncio.wait_for(reader.readexactly(7), timeout=settings.register_probe_timeout_seconds)
        response_tid, protocol_id, length, response_unit = struct.unpack(">HHHB", header)
        if response_tid != transaction_id or protocol_id != 0 or response_unit != candidate.unit_id or length < 2:
            return DeviceIdentification(False, {}, None, "invalid_response_header")
        pdu_response = await asyncio.wait_for(reader.readexactly(length - 1), timeout=settings.register_probe_timeout_seconds)
        if not pdu_response:
            return DeviceIdentification(False, {}, None, "empty_response")
        if pdu_response[0] == 0xAB:
            exception_code = pdu_response[1] if len(pdu_response) > 1 else None
            return DeviceIdentification(False, {}, json.dumps({"exception_code": exception_code}), f"modbus_exception_{exception_code}")
        parsed = _parse_device_identification_response(pdu_response)
        parsed["response_time_ms"] = round((time.perf_counter() - started) * 1000, 2)
        return DeviceIdentification(True, parsed["objects"], json.dumps(parsed), None)
    except (OSError, asyncio.IncompleteReadError, asyncio.TimeoutError, struct.error, ValueError) as exc:
        return DeviceIdentification(False, {}, None, type(exc).__name__)
    finally:
        if writer is not None:
            writer.close()
            await writer.wait_closed()


async def _read_register(candidate: DiscoveredCandidate, register: ProbeRegister) -> RegisterReadOutcome:
    writer: Optional[asyncio.StreamWriter] = None
    transaction_id = (int(time.monotonic() * 1000) + candidate.id + register.address) % 65535 or 1
    started = time.perf_counter()
    try:
        reader, writer = await asyncio.wait_for(
            asyncio.open_connection(candidate.ip_address, candidate.port),
            timeout=settings.register_probe_timeout_seconds,
        )
        start_address = _to_zero_based_address(register)
        count = _register_count(register.data_type)
        function_code = REGISTER_FUNCTIONS[register.function_code]
        pdu = struct.pack(">BHH", function_code, start_address, count)
        mbap = struct.pack(">HHHB", transaction_id, 0, len(pdu) + 1, candidate.unit_id)
        writer.write(mbap + pdu)
        await asyncio.wait_for(writer.drain(), timeout=settings.register_probe_timeout_seconds)
        header = await asyncio.wait_for(reader.readexactly(7), timeout=settings.register_probe_timeout_seconds)
        response_tid, protocol_id, length, response_unit = struct.unpack(">HHHB", header)
        response_time_ms = round((time.perf_counter() - started) * 1000, 2)
        if response_tid != transaction_id or protocol_id != 0 or response_unit != candidate.unit_id or length < 2:
            return RegisterReadOutcome("invalid_response", None, None, response_time_ms, "invalid_response_header", None)
        pdu_response = await asyncio.wait_for(reader.readexactly(length - 1), timeout=settings.register_probe_timeout_seconds)
        if not pdu_response:
            return RegisterReadOutcome("invalid_response", None, None, response_time_ms, "empty_response", None)
        if pdu_response[0] == (function_code | 0x80):
            exception_code = pdu_response[1] if len(pdu_response) > 1 else None
            return RegisterReadOutcome(
                "register_validation_failed",
                None,
                exception_code,
                response_time_ms,
                f"modbus_exception_{exception_code}",
                json.dumps({"exception_code": exception_code}),
            )
        if pdu_response[0] != function_code or len(pdu_response) < 2:
            return RegisterReadOutcome("invalid_response", None, None, response_time_ms, "unexpected_function_code", None)
        byte_count = pdu_response[1]
        register_bytes = pdu_response[2: 2 + byte_count]
        if len(register_bytes) != byte_count or byte_count % 2 != 0:
            return RegisterReadOutcome("invalid_response", None, None, response_time_ms, "invalid_byte_count", None)
        registers = [
            struct.unpack(">H", register_bytes[index:index + 2])[0]
            for index in range(0, byte_count, 2)
        ]
        return RegisterReadOutcome("validated_from_config", registers, None, response_time_ms, None, json.dumps(registers))
    except asyncio.TimeoutError:
        return RegisterReadOutcome("timeout", None, None, None, "timeout", None)
    except (OSError, asyncio.IncompleteReadError):
        return RegisterReadOutcome("connection_failed", None, None, None, "connection_failed", None)
    except (KeyError, struct.error):
        return RegisterReadOutcome("invalid_response", None, None, None, "invalid_probe_request", None)
    finally:
        if writer is not None:
            writer.close()
            await writer.wait_closed()


def _candidate_metadata(identification: DeviceIdentification, plan: ProbePlan, results: list[dict]) -> dict:
    fields = identification.fields
    validated_count = sum(1 for result in results if result.get("valid"))
    failed_count = sum(1 for result in results if not result.get("valid"))
    if plan.registers and validated_count == len(results):
        probe_status = "validated_from_config"
    elif plan.registers and validated_count > 0:
        probe_status = "partial_probe"
    elif plan.registers:
        probe_status = "register_validation_failed"
    elif not identification.supported and identification.error:
        probe_status = "unsupported_device_identification"
    else:
        probe_status = plan.quality

    summary = {
        "tested": {
            "host": True,
            "port": True,
            "unit_id": True,
            "device_identification": True,
            "register_count": len(results),
        },
        "from_config": {
            "profile_id": plan.profile_id,
            "profile_source": plan.profile_source,
            "registers_configured": len(plan.registers),
        },
        "from_device_identification": fields,
        "inferred": plan.inferred,
        "failed_checks": [
            {
                "metric": result.get("metric"),
                "address": result.get("register_address"),
                "status": result.get("status"),
                "failure_reason": result.get("failure_reason"),
            }
            for result in results
            if not result.get("valid")
        ],
        "recommended_next_action": _recommended_next_action(probe_status, plan),
        "validated_registers": validated_count,
        "failed_registers": failed_count,
    }
    return {
        "vendor_name": fields.get("VendorName"),
        "product_code": fields.get("ProductCode"),
        "product_name": fields.get("ProductName"),
        "model_name": fields.get("ModelName"),
        "firmware_revision": fields.get("MajorMinorRevision"),
        "device_identification_raw": identification.raw,
        "vendor_identification_supported": identification.supported,
        "vendor_identification_error": identification.error,
        "probe_profile_id": plan.profile_id,
        "probe_profile_source": plan.profile_source,
        "probe_quality": plan.quality if probe_status != "validated_from_config" else "validated_from_config",
        "probe_status": probe_status,
        "probe_summary_json": json.dumps(summary),
    }


def _recommended_next_action(probe_status: str, plan: ProbePlan) -> str:
    if probe_status == "validated_from_config":
        return "Review validated configured registers before promotion."
    if probe_status == "partial_probe":
        return "Review failed configured registers before promotion."
    if probe_status == "register_validation_failed":
        return "Check Unit ID, function code, address mode, and register map."
    if plan.profile_source == "vendor_default":
        return "Add and verify a vendor-specific register map before polling."
    return "Create a manual register map or add a verified config profile."


async def probe_candidate(candidate: DiscoveredCandidate, conn: Optional[sqlite3.Connection] = None) -> dict[str, Any]:
    identification = await read_device_identification(candidate)
    plan = resolve_probe_plan(candidate, conn, identification)
    selected_registers = plan.registers[: settings.register_probe_max_validation_registers]

    stored_results: list[dict] = []
    for register in selected_registers:
        await asyncio.sleep(settings.register_probe_delay_seconds)
        outcome = await _read_register(candidate, register)
        decoded_value = (
            _decode_registers(outcome.registers, register.data_type, register.scale)
            if outcome.registers is not None
            else None
        )
        valid = outcome.status == "validated_from_config" and decoded_value is not None
        status = "validated_from_config" if valid else outcome.status
        failure_reason = outcome.failure_reason
        if outcome.status == "validated_from_config" and decoded_value is None:
            status = "invalid_response"
            failure_reason = "decode_failed"
        stored_results.append(
            {
                "register_address": register.address,
                "function_code": register.function_code,
                "data_type": register.data_type,
                "raw_value": outcome.raw_value,
                "decoded_value": decoded_value,
                "valid": valid,
                "metric": register.metric,
                "scale": register.scale,
                "unit": register.unit,
                "quality": "validated_from_config" if valid else status,
                "status": status,
                "source": plan.profile_source,
                "tested_json": json.dumps(
                    {
                        "host": candidate.ip_address,
                        "port": candidate.port,
                        "unit_id": candidate.unit_id,
                        "address": register.address,
                        "zero_based_address": _to_zero_based_address(register),
                        "function_code": register.function_code,
                        "data_type": register.data_type,
                        "required": register.required,
                    }
                ),
                "inferred_json": json.dumps(plan.inferred),
                "failure_reason": failure_reason,
                "exception_code": outcome.exception_code,
                "response_time_ms": outcome.response_time_ms,
                "validated_from_config": valid,
                "probe_profile_id": plan.profile_id,
                "probe_profile_source": plan.profile_source,
            }
        )

    return {
        "results": stored_results,
        "metadata": _candidate_metadata(identification, plan, stored_results),
    }
