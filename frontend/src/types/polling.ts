export interface PollingStatus {
  running: boolean;
  enabled_devices: number;
  active_workers: number;
  measurements_last_hour: number;
}
