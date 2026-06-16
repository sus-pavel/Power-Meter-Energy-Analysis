import { useQuery } from "@tanstack/react-query";
import { getOperationalDevices, getOperationsEvents, getOperationsStatus, getRecentMeasurements } from "../api/operations";

export function useOperationsStatus(intervalMs = 10000) {
  return useQuery({
    queryKey: ["operations", "status"],
    queryFn: getOperationsStatus,
    refetchInterval: intervalMs
  });
}

export function useOperationalDevices(intervalMs = 10000) {
  return useQuery({
    queryKey: ["operations", "devices"],
    queryFn: getOperationalDevices,
    refetchInterval: intervalMs
  });
}

export function useRecentMeasurements(intervalMs = 10000) {
  return useQuery({
    queryKey: ["operations", "measurements"],
    queryFn: getRecentMeasurements,
    refetchInterval: intervalMs
  });
}

export function useOperationsEvents(intervalMs = 10000) {
  return useQuery({
    queryKey: ["operations", "events"],
    queryFn: getOperationsEvents,
    refetchInterval: intervalMs
  });
}
