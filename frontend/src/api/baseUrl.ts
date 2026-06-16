const DEFAULT_DEV_API_BASE_URL = "http://127.0.0.1:8000/api";
const DEFAULT_DESKTOP_API_BASE_URL = "http://127.0.0.1:8765/api";

declare global {
  interface Window {
    __TAURI_INTERNALS__?: unknown;
  }
}

export function isDesktopRuntime(): boolean {
  return Boolean(window.__TAURI_INTERNALS__) || import.meta.env.VITE_POWERMETER_DESKTOP === "1";
}

export function getApiBaseUrl(): string {
  if (import.meta.env.VITE_API_BASE_URL) {
    return import.meta.env.VITE_API_BASE_URL;
  }
  return isDesktopRuntime() ? DEFAULT_DESKTOP_API_BASE_URL : DEFAULT_DEV_API_BASE_URL;
}

export function getBackendOrigin(): string {
  return getApiBaseUrl().replace(/\/api\/?$/, "");
}
