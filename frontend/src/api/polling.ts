import { apiClient } from "./client";
import type { PollingStatus } from "../types/polling";

export async function getPollingStatus(): Promise<PollingStatus> {
  const response = await apiClient.get<PollingStatus>("/polling/status");
  return response.data;
}

export async function startPolling(): Promise<{ running: boolean }> {
  const response = await apiClient.post<{ running: boolean }>("/polling/start");
  return response.data;
}

export async function stopPolling(): Promise<{ running: boolean }> {
  const response = await apiClient.post<{ running: boolean }>("/polling/stop");
  return response.data;
}
