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
  vendor_name: string | null;
  product_code: string | null;
  product_name: string | null;
  model_name: string | null;
  firmware_revision: string | null;
  vendor_identification_supported: boolean;
  vendor_identification_error: string | null;
  probe_profile_id: string | null;
  probe_profile_source: string | null;
  probe_quality: string | null;
  probe_status: string | null;
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
  metric: string | null;
  scale: number;
  unit: string | null;
  quality: string;
  status: string;
  source: string;
  tested_json: string;
  inferred_json: string;
  failure_reason: string | null;
  exception_code: number | null;
  response_time_ms: number | null;
  validated_from_config: boolean;
  probe_profile_id: string | null;
  probe_profile_source: string | null;
  created_at: string;
}

export interface CandidateDetails extends CandidateSummary {
  scan_result_id: number;
  notes: string | null;
  created_at: string;
  device_identification_raw: string | null;
  probe_summary_json: string | null;
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
