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
  latest_total_power?: number | null;
  latest_drpi_total?: number | null;
  analytics_service_status?: {
    running: boolean;
    aggregation: boolean;
    drpi: boolean;
    retention: boolean;
  };
  aggregation_status?: Record<string, number>;
}
