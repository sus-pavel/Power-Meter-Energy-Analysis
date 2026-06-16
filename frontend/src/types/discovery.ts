export type ScanJobStatus = "pending" | "running" | "completed" | "failed" | "cancelled";

export interface ScanJob {
  id: number;
  created_at: string;
  started_at: string | null;
  finished_at: string | null;
  created_by_user_id: number | null;
  status: ScanJobStatus;
  ip_start: string;
  ip_end: string;
  total_hosts: number;
  processed_hosts: number;
  found_hosts: number;
  error_message: string | null;
  progress_percent: number;
}

export interface ScanResult {
  id: number;
  job_id: number;
  ip_address: string;
  port: number;
  tcp_open: boolean;
  modbus_responding: boolean;
  response_time_ms: number | null;
  candidate_unit_ids: number[];
  last_checked_at: string;
  created_at: string;
}

export interface ScanCreatePayload {
  ip_start: string;
  ip_end: string;
}
