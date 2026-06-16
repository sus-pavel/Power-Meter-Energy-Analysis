import { useQuery } from "@tanstack/react-query";
import { getDevices } from "../api/devices";

export function useDevices() {
  return useQuery({
    queryKey: ["devices"],
    queryFn: getDevices
  });
}
