import { apiClient } from "./client";
import type { ScanCreatePayload, ScanJob, ScanResult } from "../types/discovery";

export async function getDiscoveryJobs(): Promise<ScanJob[]> {
  const response = await apiClient.get<ScanJob[]>("/discovery/jobs");
  return response.data;
}

export async function createDiscoveryScan(payload: ScanCreatePayload): Promise<{ job_id: number; status: string }> {
  const response = await apiClient.post<{ job_id: number; status: string }>("/discovery/scan", payload);
  return response.data;
}

export async function getDiscoveryJob(jobId: number): Promise<ScanJob> {
  const response = await apiClient.get<ScanJob>(`/discovery/jobs/${jobId}`);
  return response.data;
}

export async function getDiscoveryJobResults(jobId: number): Promise<ScanResult[]> {
  const response = await apiClient.get<ScanResult[]>(`/discovery/jobs/${jobId}/results`);
  return response.data;
}

export async function cancelDiscoveryJob(jobId: number): Promise<void> {
  await apiClient.post(`/discovery/jobs/${jobId}/cancel`);
}
