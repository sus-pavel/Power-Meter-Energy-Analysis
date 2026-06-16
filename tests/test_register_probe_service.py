from __future__ import annotations

import asyncio
import sqlite3
import unittest
from unittest.mock import patch

from backend.app.models.candidate import DiscoveredCandidate
from backend.app.services.register_probe_service import (
    DeviceIdentification,
    RegisterReadOutcome,
    _parse_device_identification_response,
    probe_candidate,
    resolve_probe_plan,
)


def make_candidate() -> DiscoveredCandidate:
    return DiscoveredCandidate(
        id=1,
        scan_result_id=10,
        ip_address="192.168.1.50",
        port=502,
        unit_id=7,
        status="discovered",
        device_type_guess="unknown_modbus_device",
        confidence_score=0.2,
        vendor_guess="unknown",
        vendor_name=None,
        product_code=None,
        product_name=None,
        model_name=None,
        firmware_revision=None,
        device_identification_raw=None,
        vendor_identification_supported=False,
        vendor_identification_error=None,
        probe_profile_id=None,
        probe_profile_source=None,
        probe_quality=None,
        probe_status=None,
        probe_summary_json=None,
        notes=None,
        created_at="2026-06-16 00:00:00",
        updated_at="2026-06-16 00:00:00",
    )


def make_config_db() -> sqlite3.Connection:
    conn = sqlite3.connect(":memory:")
    conn.row_factory = sqlite3.Row
    conn.executescript(
        """
        CREATE TABLE devices (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            host TEXT NOT NULL,
            port INTEGER NOT NULL,
            unit_id INTEGER NOT NULL
        );
        CREATE TABLE device_registers (
            id INTEGER PRIMARY KEY,
            device_id INTEGER NOT NULL,
            metric TEXT NOT NULL,
            function_code TEXT NOT NULL,
            address INTEGER NOT NULL,
            data_type TEXT NOT NULL,
            scale REAL NOT NULL DEFAULT 1.0,
            unit TEXT,
            enabled INTEGER NOT NULL DEFAULT 1
        );
        INSERT INTO devices (id, name, host, port, unit_id)
        VALUES (99, 'Configured meter', '192.168.1.50', 502, 7);
        INSERT INTO device_registers
            (id, device_id, metric, function_code, address, data_type, scale, unit, enabled)
        VALUES
            (1, 99, 'active_power_avg', 'holding', 403059, 'float32', 1.0, 'kW', 1);
        """
    )
    return conn


class RegisterProbeServiceTests(unittest.TestCase):
    def test_resolve_probe_plan_prefers_persisted_config(self) -> None:
        candidate = make_candidate()
        with make_config_db() as conn:
            plan = resolve_probe_plan(candidate, conn, DeviceIdentification(False, {}, None, "unsupported"))
        self.assertEqual(plan.profile_source, "persisted_config")
        self.assertEqual(plan.profile_id, "device:99")
        self.assertEqual(plan.registers[0].metric, "active_power_avg")
        self.assertEqual(plan.registers[0].address, 403059)

    def test_parse_device_identification_response(self) -> None:
        vendor = b"Schneider Electric"
        product = b"PM8000"
        revision = b"1.2.3"
        pdu = bytes([0x2B, 0x0E, 0x01, 0x01, 0x00, 0x00, 0x03])
        pdu += bytes([0x00, len(vendor)]) + vendor
        pdu += bytes([0x01, len(product)]) + product
        pdu += bytes([0x02, len(revision)]) + revision
        parsed = _parse_device_identification_response(pdu)
        self.assertEqual(parsed["objects"]["VendorName"], "Schneider Electric")
        self.assertEqual(parsed["objects"]["ProductCode"], "PM8000")
        self.assertEqual(parsed["objects"]["MajorMinorRevision"], "1.2.3")

    def test_unsupported_device_identification_continues_with_config(self) -> None:
        candidate = make_candidate()

        async def run_probe() -> dict:
            with make_config_db() as conn:
                with patch(
                    "backend.app.services.register_probe_service.read_device_identification",
                    return_value=DeviceIdentification(False, {}, None, "modbus_exception_1"),
                ), patch(
                    "backend.app.services.register_probe_service._read_register",
                    return_value=RegisterReadOutcome("validated_from_config", [0x3F80, 0x0000], None, 12.5, None, "[16256, 0]"),
                ):
                    return await probe_candidate(candidate, conn)

        outcome = asyncio.run(run_probe())
        self.assertFalse(outcome["metadata"]["vendor_identification_supported"])
        self.assertEqual(outcome["metadata"]["vendor_identification_error"], "modbus_exception_1")
        self.assertEqual(outcome["results"][0]["status"], "validated_from_config")
        self.assertTrue(outcome["results"][0]["valid"])

    def test_invalid_register_read_does_not_validate_mapping(self) -> None:
        candidate = make_candidate()

        async def run_probe() -> dict:
            with make_config_db() as conn:
                with patch(
                    "backend.app.services.register_probe_service.read_device_identification",
                    return_value=DeviceIdentification(True, {"VendorName": "ABB"}, "{}", None),
                ), patch(
                    "backend.app.services.register_probe_service._read_register",
                    return_value=RegisterReadOutcome("register_validation_failed", None, 2, 10.0, "modbus_exception_2", '{"exception_code": 2}'),
                ):
                    return await probe_candidate(candidate, conn)

        outcome = asyncio.run(run_probe())
        self.assertEqual(outcome["metadata"]["probe_status"], "register_validation_failed")
        self.assertFalse(outcome["results"][0]["valid"])
        self.assertFalse(outcome["results"][0]["validated_from_config"])
        self.assertEqual(outcome["results"][0]["exception_code"], 2)


if __name__ == "__main__":
    unittest.main()
