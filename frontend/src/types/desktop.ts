export interface DesktopDiagnostics {
  desktop_mode: boolean;
  app_data_dir: string;
  db_path: string;
  log_dir: string;
  backend_port: number;
  database_ok: boolean;
}

export interface DesktopBackendState {
  phase: "starting" | "checking" | "ready" | "error" | "port_in_use";
  message: string;
  app_data_dir?: string;
  db_path?: string;
  log_dir?: string;
  port: number;
}

export interface DesktopStartupIssue {
  stage: "health" | "diagnostics";
  url: string;
  status?: number;
  message: string;
}
