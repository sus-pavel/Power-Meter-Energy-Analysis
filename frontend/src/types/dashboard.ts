export interface DashboardSummary {
  devices: number;
  enabled_devices: number;
  users: number;
  active_scan_jobs: number;
  discovered_candidates: number;
  promoted_devices: number;
  pending_review: number;
  mode: string;
  database: string;
  measurement_summary?: unknown;
}
