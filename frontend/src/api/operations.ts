import { apiClient } from "./client";
import type { OperationalDevice, OperationsEvent, OperationsStatus, RecentMeasurements } from "../types/operations";

export async function getOperationsStatus(): Promise<OperationsStatus> {
  const response = await apiClient.get<OperationsStatus>("/operations/status");
  return response.data;
}

export async function getOperationalDevices(): Promise<OperationalDevice[]> {
  const response = await apiClient.get<OperationalDevice[]>("/operations/devices");
  return response.data;
}

export async function getRecentMeasurements(): Promise<RecentMeasurements> {
  const response = await apiClient.get<RecentMeasurements>("/operations/recent-measurements");
  return response.data;
}

export async function getOperationsEvents(): Promise<OperationsEvent[]> {
  const response = await apiClient.get<OperationsEvent[]>("/operations/events");
  return response.data;
}
