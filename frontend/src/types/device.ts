export interface Device {
  id: number;
  name: string;
  host: string;
  port: number;
  unit_id: number;
  description: string | null;
  location: string | null;
  enabled: boolean;
  poll_interval_sec: number;
  created_at: string;
  updated_at: string;
}

export interface DeviceUpdatePayload {
  name?: string;
  description?: string | null;
  location?: string | null;
  enabled?: boolean;
  poll_interval_sec?: number;
}

export interface RegisterMapEntry {
  id: number;
  device_id: number;
  metric: string;
  function_code: string;
  address: number;
  data_type: string;
  scale: number;
  unit: string | null;
  description: string | null;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface RegisterPayload {
  metric: string;
  function_code: string;
  address: number;
  data_type: string;
  scale: number;
  unit?: string | null;
  description?: string | null;
  enabled: boolean;
}

export interface DeviceStatus {
  status: "online" | "offline" | "timeout" | "error" | "disabled" | "unknown";
  last_success_at: string | null;
  last_error_at: string | null;
  last_error_message: string | null;
}

export interface DeviceMeasurement {
  id: number;
  device_id: number;
  register_id: number;
  timestamp: number;
  metric: string;
  value: number;
  unit: string | null;
  created_at: string;
}
