export interface Device {
  id: number;
  name: string;
  host?: string;
  port?: number;
  unit_id?: number;
  description: string | null;
  location: string | null;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}
