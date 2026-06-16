import { useQuery } from "@tanstack/react-query";
import { getDiscoveryJob, getDiscoveryJobResults, getDiscoveryJobs } from "../api/discovery";

export function useDiscoveryJobs() {
  return useQuery({
    queryKey: ["discovery", "jobs"],
    queryFn: getDiscoveryJobs,
    refetchInterval: (query) => query.state.data?.some((job) => job.status === "running" || job.status === "pending") ? 5000 : false
  });
}

export function useDiscoveryJob(jobId: number) {
  return useQuery({
    queryKey: ["discovery", "jobs", jobId],
    queryFn: () => getDiscoveryJob(jobId),
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      return status === "running" || status === "pending" ? 5000 : false;
    }
  });
}

export function useDiscoveryJobResults(jobId: number) {
  return useQuery({
    queryKey: ["discovery", "jobs", jobId, "results"],
    queryFn: () => getDiscoveryJobResults(jobId)
  });
}
