import { getBackendOrigin } from "./baseUrl";
import type { DesktopDiagnostics } from "../types/desktop";

export class DesktopRequestError extends Error {
  status?: number;

  constructor(message: string, status?: number) {
    super(message);
    this.name = "DesktopRequestError";
    this.status = status;
  }
}

export async function getDesktopDiagnostics(): Promise<DesktopDiagnostics> {
  const response = await fetch(`${getBackendOrigin()}/api/desktop/diagnostics`);
  if (!response.ok) {
    throw new DesktopRequestError("Diagnostics request failed", response.status);
  }
  return response.json() as Promise<DesktopDiagnostics>;
}
