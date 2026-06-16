from __future__ import annotations

from typing import Any, Optional, Union

from fastapi import APIRouter, Depends, HTTPException, Query, Response, status

from backend.app.api.deps import CurrentUser, Database, require_permission
from backend.app.core.permissions import Role
from backend.app.models.user import User
from backend.app.schemas.device import (
    DeviceCreate,
    DeviceGuestRead,
    DeviceRead,
    DeviceStatusRead,
    DeviceUpdate,
    MeasurementRead,
    ProbeResponse,
    RegisterCreate,
    RegisterRead,
    RegisterUpdate,
)
from backend.app.services import device_service
from backend.app.services.audit_service import write_audit_log
from backend.app.services.modbus_probe_service import probe_device_placeholder


router = APIRouter(prefix="/api/devices", tags=["devices"])


def _device_response(device: Any, current_user: CurrentUser) -> Union[DeviceRead, DeviceGuestRead]:
    if current_user.role == Role.GUEST:
        return DeviceGuestRead(
            id=device.id,
            name=device.name,
            description=device.description,
            location=device.location,
            enabled=device.enabled,
            created_at=device.created_at,
            updated_at=device.updated_at,
        )
    return DeviceRead(**device.__dict__)


@router.get("")
def list_devices(conn: Database, current_user: CurrentUser) -> list[Union[DeviceRead, DeviceGuestRead]]:
    return [_device_response(device, current_user) for device in device_service.list_devices(conn)]


@router.post("", response_model=DeviceRead, status_code=status.HTTP_201_CREATED)
def create_device(
    payload: DeviceCreate,
    conn: Database,
    current_user: User = Depends(require_permission("manage_devices")),
) -> DeviceRead:
    device = device_service.create_device(conn, payload)
    write_audit_log(conn, user_id=current_user.id, action="create", entity_type="device", entity_id=device.id)
    return DeviceRead(**device.__dict__)


@router.get("/{device_id}")
def get_device(device_id: int, conn: Database, current_user: CurrentUser) -> Union[DeviceRead, DeviceGuestRead]:
    device = device_service.get_device(conn, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return _device_response(device, current_user)


@router.put("/{device_id}", response_model=DeviceRead)
def update_device(
    device_id: int,
    payload: DeviceUpdate,
    conn: Database,
    current_user: User = Depends(require_permission("manage_devices")),
) -> DeviceRead:
    device = device_service.update_device(conn, device_id, payload)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    write_audit_log(conn, user_id=current_user.id, action="update", entity_type="device", entity_id=device.id)
    return DeviceRead(**device.__dict__)


@router.delete("/{device_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_device(
    device_id: int,
    conn: Database,
    current_user: User = Depends(require_permission("manage_devices")),
):
    deleted = device_service.delete_device(conn, device_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    write_audit_log(conn, user_id=current_user.id, action="delete", entity_type="device", entity_id=device_id)


@router.get("/{device_id}/registers", response_model=list[RegisterRead])
def list_registers(device_id: int, conn: Database, _: CurrentUser) -> list[RegisterRead]:
    if device_service.get_device(conn, device_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return [RegisterRead(**register.__dict__) for register in device_service.list_registers(conn, device_id)]


@router.get("/{device_id}/status", response_model=DeviceStatusRead)
def get_device_status(device_id: int, conn: Database, _: CurrentUser) -> DeviceStatusRead:
    device = device_service.get_device(conn, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    row = conn.execute(
        """
        SELECT status, last_success_at, last_error_at, last_error_message
        FROM device_status
        WHERE device_id = ?
        """,
        (device_id,),
    ).fetchone()
    if row is None:
        return DeviceStatusRead(
            status="disabled" if not device.enabled else "unknown",
            last_success_at=None,
            last_error_at=None,
            last_error_message=None,
        )
    return DeviceStatusRead(**dict(row))


@router.get("/{device_id}/measurements", response_model=list[MeasurementRead])
def get_device_measurements(
    device_id: int,
    conn: Database,
    _: CurrentUser,
    from_ts: Optional[float] = Query(default=None, alias="from"),
    to_ts: Optional[float] = Query(default=None, alias="to"),
    limit: int = Query(default=200, ge=1, le=2000),
) -> list[MeasurementRead]:
    if device_service.get_device(conn, device_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    clauses = ["device_id = ?"]
    params: list[Any] = [device_id]
    if from_ts is not None:
        clauses.append("timestamp >= ?")
        params.append(from_ts)
    if to_ts is not None:
        clauses.append("timestamp <= ?")
        params.append(to_ts)
    params.append(limit)
    rows = conn.execute(
        f"""
        SELECT id, device_id, register_id, timestamp, metric, value, unit, created_at
        FROM measurements_raw
        WHERE {' AND '.join(clauses)}
        ORDER BY timestamp DESC, id DESC
        LIMIT ?
        """,
        params,
    ).fetchall()
    return [MeasurementRead(**dict(row)) for row in rows]


@router.post("/{device_id}/registers", response_model=RegisterRead, status_code=status.HTTP_201_CREATED)
def create_register(
    device_id: int,
    payload: RegisterCreate,
    conn: Database,
    current_user: User = Depends(require_permission("manage_devices")),
) -> RegisterRead:
    if device_service.get_device(conn, device_id) is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    register = device_service.create_register(conn, device_id, payload)
    write_audit_log(
        conn,
        user_id=current_user.id,
        action="create",
        entity_type="device_register",
        entity_id=register.id,
        details={"device_id": device_id},
    )
    return RegisterRead(**register.__dict__)


@router.put("/{device_id}/registers/{register_id}", response_model=RegisterRead)
def update_register(
    device_id: int,
    register_id: int,
    payload: RegisterUpdate,
    conn: Database,
    current_user: User = Depends(require_permission("manage_devices")),
) -> RegisterRead:
    register = device_service.update_register(conn, device_id, register_id, payload)
    if register is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Register not found")
    write_audit_log(
        conn,
        user_id=current_user.id,
        action="update",
        entity_type="device_register",
        entity_id=register.id,
        details={"device_id": device_id},
    )
    return RegisterRead(**register.__dict__)


@router.delete("/{device_id}/registers/{register_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
def delete_register(
    device_id: int,
    register_id: int,
    conn: Database,
    current_user: User = Depends(require_permission("manage_devices")),
):
    deleted = device_service.delete_register(conn, device_id, register_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Register not found")
    write_audit_log(
        conn,
        user_id=current_user.id,
        action="delete",
        entity_type="device_register",
        entity_id=register_id,
        details={"device_id": device_id},
    )


@router.post("/{device_id}/probe", response_model=ProbeResponse)
def probe_device(
    device_id: int,
    conn: Database,
    _: User = Depends(require_permission("probe_registers")),
) -> ProbeResponse:
    device = device_service.get_device(conn, device_id)
    if device is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Device not found")
    return probe_device_placeholder(device)
