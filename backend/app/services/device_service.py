from __future__ import annotations

import sqlite3

from backend.app.models.device import Device, DeviceRegister
from backend.app.schemas.device import DeviceCreate, DeviceUpdate, RegisterCreate, RegisterUpdate


def row_to_device(row: sqlite3.Row) -> Device:
    return Device(
        id=row["id"],
        name=row["name"],
        host=row["host"],
        port=row["port"],
        unit_id=row["unit_id"],
        description=row["description"],
        location=row["location"],
        enabled=bool(row["enabled"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def row_to_register(row: sqlite3.Row) -> DeviceRegister:
    return DeviceRegister(
        id=row["id"],
        device_id=row["device_id"],
        metric=row["metric"],
        function_code=row["function_code"],
        address=row["address"],
        data_type=row["data_type"],
        scale=row["scale"],
        unit=row["unit"],
        description=row["description"],
        enabled=bool(row["enabled"]),
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


def list_devices(conn: sqlite3.Connection) -> list[Device]:
    rows = conn.execute("SELECT * FROM devices ORDER BY name").fetchall()
    return [row_to_device(row) for row in rows]


def get_device(conn: sqlite3.Connection, device_id: int) -> Device | None:
    row = conn.execute("SELECT * FROM devices WHERE id = ?", (device_id,)).fetchone()
    return row_to_device(row) if row else None


def create_device(conn: sqlite3.Connection, payload: DeviceCreate) -> Device:
    cursor = conn.execute(
        """
        INSERT INTO devices (name, host, port, unit_id, description, location, enabled)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        (
            payload.name,
            payload.host,
            payload.port,
            payload.unit_id,
            payload.description,
            payload.location,
            int(payload.enabled),
        ),
    )
    return get_device(conn, cursor.lastrowid)


def update_device(conn: sqlite3.Connection, device_id: int, payload: DeviceUpdate) -> Device | None:
    existing = get_device(conn, device_id)
    if existing is None:
        return None
    values = payload.model_dump(exclude_unset=True)
    if "enabled" in values and values["enabled"] is not None:
        values["enabled"] = int(values["enabled"])
    if not values:
        return existing
    assignments = ", ".join(f"{field} = ?" for field in values)
    conn.execute(
        f"UPDATE devices SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
        [*values.values(), device_id],
    )
    return get_device(conn, device_id)


def delete_device(conn: sqlite3.Connection, device_id: int) -> bool:
    cursor = conn.execute("DELETE FROM devices WHERE id = ?", (device_id,))
    return cursor.rowcount > 0


def list_registers(conn: sqlite3.Connection, device_id: int) -> list[DeviceRegister]:
    rows = conn.execute(
        "SELECT * FROM device_registers WHERE device_id = ? ORDER BY metric, address",
        (device_id,),
    ).fetchall()
    return [row_to_register(row) for row in rows]


def get_register(conn: sqlite3.Connection, device_id: int, register_id: int) -> DeviceRegister | None:
    row = conn.execute(
        "SELECT * FROM device_registers WHERE id = ? AND device_id = ?",
        (register_id, device_id),
    ).fetchone()
    return row_to_register(row) if row else None


def create_register(conn: sqlite3.Connection, device_id: int, payload: RegisterCreate) -> DeviceRegister:
    cursor = conn.execute(
        """
        INSERT INTO device_registers
            (device_id, metric, function_code, address, data_type, scale, unit, description, enabled)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            device_id,
            payload.metric,
            payload.function_code,
            payload.address,
            payload.data_type,
            payload.scale,
            payload.unit,
            payload.description,
            int(payload.enabled),
        ),
    )
    return get_register(conn, device_id, cursor.lastrowid)


def update_register(
    conn: sqlite3.Connection,
    device_id: int,
    register_id: int,
    payload: RegisterUpdate,
) -> DeviceRegister | None:
    existing = get_register(conn, device_id, register_id)
    if existing is None:
        return None
    values = payload.model_dump(exclude_unset=True)
    if "enabled" in values and values["enabled"] is not None:
        values["enabled"] = int(values["enabled"])
    if not values:
        return existing
    assignments = ", ".join(f"{field} = ?" for field in values)
    conn.execute(
        f"UPDATE device_registers SET {assignments}, updated_at = CURRENT_TIMESTAMP WHERE id = ? AND device_id = ?",
        [*values.values(), register_id, device_id],
    )
    return get_register(conn, device_id, register_id)


def delete_register(conn: sqlite3.Connection, device_id: int, register_id: int) -> bool:
    cursor = conn.execute(
        "DELETE FROM device_registers WHERE id = ? AND device_id = ?",
        (register_id, device_id),
    )
    return cursor.rowcount > 0
