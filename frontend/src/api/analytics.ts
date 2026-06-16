import { apiClient } from "./client";
import type { DrpiComponents, DrpiHistory, DrpiSummary, SSAAnalyzeRequest, SSAResult, TrendMetrics, TrendSeries, TrendSummary } from "../types/analytics";

export async function getTrendMetrics(): Promise<TrendMetrics> {
  const response = await apiClient.get<TrendMetrics>("/trends/metrics");
  return response.data;
}

export async function getTrendSeries(params: Record<string, string | number | null | undefined>): Promise<TrendSeries> {
  const response = await apiClient.get<TrendSeries>("/trends/series", { params });
  return response.data;
}

export async function getTrendSummary(params: Record<string, string | number | null | undefined>): Promise<TrendSummary> {
  const response = await apiClient.get<TrendSummary>("/trends/summary", { params });
  return response.data;
}

export async function getDrpiSummary(): Promise<DrpiSummary> {
  const response = await apiClient.get<DrpiSummary>("/drpi/summary");
  return response.data;
}

export async function getDrpiHistory(sourceId: string): Promise<DrpiHistory> {
  const response = await apiClient.get<DrpiHistory>("/drpi/history", { params: { source_id: sourceId } });
  return response.data;
}

export async function getDrpiComponents(sourceId: string): Promise<DrpiComponents> {
  const response = await apiClient.get<DrpiComponents>("/drpi/components", { params: { source_id: sourceId } });
  return response.data;
}

export async function recalculateDrpi(): Promise<{ inserted: number; sources: number; recalculated_at: string }> {
  const response = await apiClient.post("/drpi/recalculate");
  return response.data;
}

export async function analyzeSSA(payload: SSAAnalyzeRequest): Promise<SSAResult> {
  const response = await apiClient.post<SSAResult>("/ssa/analyze", payload);
  return response.data;
}
