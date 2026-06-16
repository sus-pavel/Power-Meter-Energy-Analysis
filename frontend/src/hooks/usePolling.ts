import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { getPollingStatus, startPolling, stopPolling } from "../api/polling";

export function usePollingStatus(intervalMs = 5000) {
  return useQuery({
    queryKey: ["polling", "status"],
    queryFn: getPollingStatus,
    refetchInterval: intervalMs
  });
}

export function usePollingControls() {
  const queryClient = useQueryClient();
  const invalidate = () => {
    queryClient.invalidateQueries({ queryKey: ["polling"] });
    queryClient.invalidateQueries({ queryKey: ["operations"] });
    queryClient.invalidateQueries({ queryKey: ["devices"] });
  };
  return {
    start: useMutation({ mutationFn: startPolling, onSuccess: invalidate }),
    stop: useMutation({ mutationFn: stopPolling, onSuccess: invalidate })
  };
}
