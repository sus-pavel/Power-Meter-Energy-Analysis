import { apiClient } from "./client";
import type {
  Device,
  DeviceMeasurement,
  DeviceStatus,
  DeviceUpdatePayload,
  RegisterMapEntry,
  RegisterPayload
} from "../types/device";

export async function getDevices(): Promise<Device[]> {
  const response = await apiClient.get<Device[]>("/devices");
  return response.data;
}

export async function getDevice(deviceId: number): Promise<Device> {
  const response = await apiClient.get<Device>(`/devices/${deviceId}`);
  return response.data;
}

export async function updateDevice(deviceId: number, payload: DeviceUpdatePayload): Promise<Device> {
  const response = await apiClient.put<Device>(`/devices/${deviceId}`, payload);
  return response.data;
}

export async function deleteDevice(deviceId: number): Promise<void> {
  await apiClient.delete(`/devices/${deviceId}`);
}

export async function getDeviceRegisters(deviceId: number): Promise<RegisterMapEntry[]> {
  const response = await apiClient.get<RegisterMapEntry[]>(`/devices/${deviceId}/registers`);
  return response.data;
}

export async function getDeviceStatus(deviceId: number): Promise<DeviceStatus> {
  const response = await apiClient.get<DeviceStatus>(`/devices/${deviceId}/status`);
  return response.data;
}

export async function getDeviceMeasurements(deviceId: number, limit = 50): Promise<DeviceMeasurement[]> {
  const response = await apiClient.get<DeviceMeasurement[]>(`/devices/${deviceId}/measurements`, {
    params: { limit }
  });
  return response.data;
}

export async function createDeviceRegister(deviceId: number, payload: RegisterPayload): Promise<RegisterMapEntry> {
  const response = await apiClient.post<RegisterMapEntry>(`/devices/${deviceId}/registers`, payload);
  return response.data;
}

export async function updateDeviceRegister(deviceId: number, registerId: number, payload: Partial<RegisterPayload>): Promise<RegisterMapEntry> {
  const response = await apiClient.put<RegisterMapEntry>(`/devices/${deviceId}/registers/${registerId}`, payload);
  return response.data;
}

export async function deleteDeviceRegister(deviceId: number, registerId: number): Promise<void> {
  await apiClient.delete(`/devices/${deviceId}/registers/${registerId}`);
}
