import { useQuery } from "@tanstack/react-query";
import { getDevice, getDeviceMeasurements, getDeviceRegisters, getDeviceStatus } from "../api/devices";

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

export function useDeviceStatus(deviceId: number) {
  return useQuery({
    queryKey: ["devices", deviceId, "status"],
    queryFn: () => getDeviceStatus(deviceId),
    refetchInterval: 5000
  });
}

export function useDeviceMeasurements(deviceId: number) {
  return useQuery({
    queryKey: ["devices", deviceId, "measurements"],
    queryFn: () => getDeviceMeasurements(deviceId, 50),
    refetchInterval: 10000
  });
}
