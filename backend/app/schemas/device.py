from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class DeviceBase(BaseModel):
    name: str = Field(min_length=1, max_length=160)
    host: str = Field(min_length=1, max_length=255)
    port: int = Field(default=502, ge=1, le=65535)
    unit_id: int = Field(default=1, ge=0, le=255)
    description: Optional[str] = None
    location: Optional[str] = None
    enabled: bool = True


class DeviceCreate(DeviceBase):
    pass


class DeviceUpdate(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=160)
    host: Optional[str] = Field(default=None, min_length=1, max_length=255)
    port: Optional[int] = Field(default=None, ge=1, le=65535)
    unit_id: Optional[int] = Field(default=None, ge=0, le=255)
    description: Optional[str] = None
    location: Optional[str] = None
    enabled: Optional[bool] = None


class DeviceRead(DeviceBase):
    id: int
    created_at: str
    updated_at: str


class DeviceGuestRead(BaseModel):
    id: int
    name: str
    description: Optional[str]
    location: Optional[str]
    enabled: bool
    created_at: str
    updated_at: str


class RegisterBase(BaseModel):
    metric: str = Field(min_length=1, max_length=120)
    function_code: str = Field(min_length=1, max_length=40)
    address: int = Field(ge=0)
    data_type: str = Field(min_length=1, max_length=40)
    scale: float = 1.0
    unit: Optional[str] = None
    description: Optional[str] = None
    enabled: bool = True


class RegisterCreate(RegisterBase):
    pass


class RegisterUpdate(BaseModel):
    metric: Optional[str] = Field(default=None, min_length=1, max_length=120)
    function_code: Optional[str] = Field(default=None, min_length=1, max_length=40)
    address: Optional[int] = Field(default=None, ge=0)
    data_type: Optional[str] = Field(default=None, min_length=1, max_length=40)
    scale: Optional[float] = None
    unit: Optional[str] = None
    description: Optional[str] = None
    enabled: Optional[bool] = None


class RegisterRead(RegisterBase):
    id: int
    device_id: int
    created_at: str
    updated_at: str


class ProbeResponse(BaseModel):
    device_id: int
    status: str
    message: str
