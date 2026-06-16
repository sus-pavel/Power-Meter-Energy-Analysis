import { useQuery } from "@tanstack/react-query";
import { getCandidate, getCandidates } from "../api/candidates";

export function useCandidates() {
  return useQuery({
    queryKey: ["candidates"],
    queryFn: getCandidates
  });
}

export function useCandidate(candidateId: number) {
  return useQuery({
    queryKey: ["candidates", candidateId],
    queryFn: () => getCandidate(candidateId)
  });
}
