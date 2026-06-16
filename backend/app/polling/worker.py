from __future__ import annotations

import time

from backend.app.core.database import get_connection
from backend.app.models.device import Device
from backend.app.polling.measurement_writer import write_measurements
from backend.app.polling.modbus_client import (
    ModbusConnectionError,
    ModbusTimeoutError,
    read_register,
)
from backend.app.polling.status_manager import update_device_status
from backend.app.services.device_service import list_registers


async def poll_device(device: Device) -> int:
    with get_connection() as conn:
        registers = [register for register in list_registers(conn, device.id) if register.enabled]
    if not device.enabled:
        with get_connection() as conn:
            update_device_status(conn, device_id=device.id, status="disabled")
        return 0
    if not registers:
        with get_connection() as conn:
            update_device_status(conn, device_id=device.id, status="error", error_message="No enabled registers")
        return 0

    measurements = []
    timestamp = time.time()
    try:
        for register in registers:
            measurements.append(await read_register(device, register))
    except ModbusTimeoutError as exc:
        with get_connection() as conn:
            update_device_status(conn, device_id=device.id, status="timeout", error_message=str(exc))
        return 0
    except ModbusConnectionError as exc:
        with get_connection() as conn:
            update_device_status(conn, device_id=device.id, status="offline", error_message=str(exc))
        return 0
    except Exception as exc:
        with get_connection() as conn:
            update_device_status(conn, device_id=device.id, status="error", error_message=str(exc))
        return 0

    with get_connection() as conn:
        count = write_measurements(conn, device_id=device.id, timestamp=timestamp, measurements=measurements)
        update_device_status(conn, device_id=device.id, status="online")
        return count
