import { useQuery } from "@tanstack/react-query";
import { getDevice, getDeviceRegisters } from "../api/devices";

export function useDevice(deviceId: number) {
  return useQuery({
    queryKey: ["devices", deviceId],
    queryFn: () => getDevice(deviceId)
  });
}

export function useDeviceRegisters(deviceId: number) {
  return useQuery({
    queryKey: ["devices", deviceId, "registers"],
    queryFn: () => getDeviceRegisters(deviceId)
  });
}
