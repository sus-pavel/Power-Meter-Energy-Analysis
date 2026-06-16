export type OperationalDeviceStatus = "online" | "offline" | "unknown" | "disabled" | "error" | "timeout";
export type PollingReadiness = "ready" | "no_registers" | "disabled" | "unknown";

export interface OperationsStatus {
  configured_devices: number;
  enabled_devices: number;
  online_devices: number;
  offline_devices: number;
  unknown_devices: number;
  active_scan_jobs: number;
  pending_candidates: number;
  recent_measurements_available: boolean;
  last_measurement_at: string | null;
  polling_running: boolean;
  measurements_last_hour: number;
}

export interface OperationalDevice {
  id: number;
  name: string;
  host: string;
  port: number;
  unit_id: number;
  enabled: boolean;
  status: OperationalDeviceStatus;
  last_seen_at: string | null;
  last_error: string | null;
  registers_enabled: number;
  polling_readiness: PollingReadiness;
}

export interface RecentMeasurements {
  available: boolean;
  total_points_last_hour?: number;
  last_measurement_at?: string | null;
  total_power_kw?: number | null;
  message?: string;
}

export interface OperationsEvent {
  timestamp: string;
  action: string;
  entity_type: string;
  entity_id: number | null;
}
