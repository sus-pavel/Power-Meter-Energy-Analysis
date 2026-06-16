export type CandidateStatus = "discovered" | "reviewed" | "promoted" | "rejected";

export interface CandidateSummary {
  id: number;
  ip_address: string;
  port: number;
  unit_id: number;
  status: CandidateStatus;
  device_type_guess: string | null;
  confidence_score: number | null;
  vendor_guess: string | null;
  updated_at: string;
}

export interface CandidateProbeResult {
  id: number;
  candidate_id: number;
  register_address: number;
  function_code: string;
  data_type: string;
  raw_value: string | null;
  decoded_value: number | null;
  valid: boolean;
  created_at: string;
}

export interface CandidateDetails extends CandidateSummary {
  scan_result_id: number;
  notes: string | null;
  created_at: string;
  probe_results: CandidateProbeResult[];
}

export interface PromoteCandidatePayload {
  device_name: string;
  location?: string | null;
  description?: string | null;
}

export interface PromoteCandidateResponse {
  candidate_id: number;
  device_id: number;
  status: string;
  registers_created: number;
}
