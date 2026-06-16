import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { analyzeSSA, getDrpiComponents, getDrpiHistory, getDrpiSummary, getTrendMetrics, getTrendSeries, getTrendSummary, recalculateDrpi } from "../api/analytics";
import type { SSAAnalyzeRequest } from "../types/analytics";

export function useTrendMetrics() {
  return useQuery({ queryKey: ["trends", "metrics"], queryFn: getTrendMetrics });
}

export function useTrendSeries(params: Record<string, string | number | null | undefined>) {
  return useQuery({ queryKey: ["trends", "series", params], queryFn: () => getTrendSeries(params) });
}

export function useTrendSummary(params: Record<string, string | number | null | undefined>) {
  return useQuery({ queryKey: ["trends", "summary", params], queryFn: () => getTrendSummary(params) });
}

export function useDrpiSummary() {
  return useQuery({ queryKey: ["drpi", "summary"], queryFn: getDrpiSummary, refetchInterval: 30000 });
}

export function useDrpiHistory(sourceId: string) {
  return useQuery({ queryKey: ["drpi", "history", sourceId], queryFn: () => getDrpiHistory(sourceId) });
}

export function useDrpiComponents(sourceId: string) {
  return useQuery({ queryKey: ["drpi", "components", sourceId], queryFn: () => getDrpiComponents(sourceId) });
}

export function useDrpiRecalculate() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: recalculateDrpi,
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["drpi"] })
  });
}

export function useSSAAnalysis() {
  return useMutation({ mutationFn: (payload: SSAAnalyzeRequest) => analyzeSSA(payload) });
}
