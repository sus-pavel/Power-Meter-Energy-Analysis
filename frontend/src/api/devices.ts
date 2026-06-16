import { apiClient } from "./client";
import type { Device } from "../types/device";

export async function getDevices(): Promise<Device[]> {
  const response = await apiClient.get<Device[]>("/devices");
  return response.data;
}
