import { apiClient } from "./client";
import type { CandidateDetails, CandidateSummary, PromoteCandidatePayload, PromoteCandidateResponse } from "../types/candidate";

export async function getCandidates(): Promise<CandidateSummary[]> {
  const response = await apiClient.get<CandidateSummary[]>("/candidates");
  return response.data;
}

export async function getCandidate(candidateId: number): Promise<CandidateDetails> {
  const response = await apiClient.get<CandidateDetails>(`/candidates/${candidateId}`);
  return response.data;
}

export async function probeCandidate(candidateId: number) {
  const response = await apiClient.post(`/candidates/${candidateId}/probe`);
  return response.data;
}

export async function promoteCandidate(candidateId: number, payload: PromoteCandidatePayload): Promise<PromoteCandidateResponse> {
  const response = await apiClient.post<PromoteCandidateResponse>(`/candidates/${candidateId}/promote`, payload);
  return response.data;
}

export async function rejectCandidate(candidateId: number): Promise<void> {
  await apiClient.post(`/candidates/${candidateId}/reject`);
}
