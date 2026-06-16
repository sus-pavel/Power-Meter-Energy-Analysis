import { useEffect, useState } from "react";
import { Activity, AlertTriangle, CheckCircle2, Database, Folder, Loader2, Terminal } from "lucide-react";
import { getApiBaseUrl, getBackendOrigin } from "../api/baseUrl";
import { DesktopRequestError, getDesktopDiagnostics } from "../api/desktop";
import type { DesktopBackendState, DesktopDiagnostics, DesktopStartupIssue } from "../types/desktop";

interface DesktopStartupPageProps {
  onReady: (diagnostics: DesktopDiagnostics | null) => void;
}

async function invokeBackendState(): Promise<DesktopBackendState | null> {
  if (!window.__TAURI_INTERNALS__) {
    return null;
  }
  const tauri = await import("@tauri-apps/api/core");
  return tauri.invoke<DesktopBackendState>("backend_state");
}

function delay(ms: number): Promise<void> {
  return new Promise((resolve) => window.setTimeout(resolve, ms));
}

export function DesktopStartupPage({ onReady }: DesktopStartupPageProps) {
  const [status, setStatus] = useState("Starting backend...");
  const [diagnostics, setDiagnostics] = useState<DesktopDiagnostics | null>(null);
  const [issue, setIssue] = useState<DesktopStartupIssue | null>(null);
  const [diagnosticsWarning, setDiagnosticsWarning] = useState<DesktopStartupIssue | null>(null);

  useEffect(() => {
    let cancelled = false;
    const backendOrigin = getBackendOrigin();
    const healthUrl = `${backendOrigin}/api/health`;
    const diagnosticsUrl = `${backendOrigin}/api/desktop/diagnostics`;

    async function checkBackend() {
      console.info("[PowerMeter desktop startup] API base URL", getApiBaseUrl());
      setIssue(null);
      setDiagnosticsWarning(null);
      setStatus("Starting backend...");
      try {
        const state = await invokeBackendState();
        if (!cancelled && state) {
          setStatus(state.phase === "ready" ? "Backend ready" : state.message);
        }
      } catch (err) {
        if (!cancelled) {
          setStatus("Checking backend health...");
          console.warn("[PowerMeter desktop startup] Tauri backend_state unavailable", err);
        }
      }

      let healthOk = false;
      for (let attempt = 0; attempt < 60 && !cancelled; attempt += 1) {
        try {
          setStatus("Checking backend health...");
          console.info("[PowerMeter desktop startup] health check started", healthUrl);
          const health = await fetch(healthUrl);
          if (!health.ok) {
            throw new DesktopRequestError("Health request failed", health.status);
          }
          console.info("[PowerMeter desktop startup] health check succeeded", healthUrl);
          healthOk = true;
          break;
        } catch (err) {
          if (!cancelled) {
            setIssue({
              stage: "health",
              url: healthUrl,
              status: err instanceof DesktopRequestError ? err.status : undefined,
              message: err instanceof Error ? err.message : String(err)
            });
          }
          await delay(500);
          continue;
        }
      }

      if (cancelled) {
        return;
      }

      if (!healthOk) {
        setStatus("Backend health check failed");
        return;
      }

      setIssue(null);
      setStatus("Backend ready");

      try {
        console.info("[PowerMeter desktop startup] diagnostics fetch started", diagnosticsUrl);
        const data = await getDesktopDiagnostics();
        if (cancelled) {
          return;
        }
        console.info("[PowerMeter desktop startup] diagnostics fetch succeeded", data);
        setDiagnostics(data);
        await delay(500);
        if (cancelled) {
          return;
        }
        console.info("[PowerMeter desktop startup] entering app");
        onReady(data);
      } catch (err) {
        if (cancelled) {
          return;
        }
        const warning = {
          stage: "diagnostics" as const,
          url: diagnosticsUrl,
          status: err instanceof DesktopRequestError ? err.status : undefined,
          message: err instanceof Error ? err.message : String(err)
        };
        console.warn("[PowerMeter desktop startup] diagnostics fetch failed; entering app anyway", warning);
        setDiagnosticsWarning(warning);
        await delay(1000);
        if (cancelled) {
          return;
        }
        console.info("[PowerMeter desktop startup] entering app");
        onReady(null);
      }
    }

    checkBackend();
    return () => {
      cancelled = true;
    };
  }, [onReady]);

  const ready = status === "Backend ready";
  const visibleIssue = issue ?? diagnosticsWarning;

  return (
    <main className="flex min-h-screen items-center justify-center bg-background p-6">
      <section className="w-full max-w-2xl rounded-md border border-border bg-card p-6 shadow-sm">
        <div className="flex items-center gap-3">
          <div className="flex h-10 w-10 items-center justify-center rounded-md bg-primary text-primary-foreground">
            <Activity className="h-5 w-5" />
          </div>
          <div>
            <h1 className="text-lg font-semibold text-foreground">PowerMeter Desktop</h1>
            <p className="text-sm text-muted-foreground">Local backend startup diagnostics</p>
          </div>
        </div>

        <div className="mt-6 space-y-3">
          <div className="flex items-center gap-3 rounded-md border border-border bg-background px-4 py-3">
            {ready ? <CheckCircle2 className="h-5 w-5 text-primary" /> : <Loader2 className="h-5 w-5 animate-spin text-primary" />}
            <span className="text-sm font-medium text-foreground">{status}</span>
          </div>
          <div className="grid gap-3 sm:grid-cols-3">
            <div className="rounded-md border border-border bg-background p-3">
              <Folder className="mb-2 h-4 w-4 text-primary" />
              <p className="text-xs font-medium uppercase text-muted-foreground">App data directory</p>
              <p className="mt-1 break-words text-xs text-foreground">{diagnostics?.app_data_dir ?? "Pending"}</p>
            </div>
            <div className="rounded-md border border-border bg-background p-3">
              <Database className="mb-2 h-4 w-4 text-primary" />
              <p className="text-xs font-medium uppercase text-muted-foreground">Database path</p>
              <p className="mt-1 break-words text-xs text-foreground">{diagnostics?.db_path ?? "Pending"}</p>
            </div>
            <div className="rounded-md border border-border bg-background p-3">
              <Terminal className="mb-2 h-4 w-4 text-primary" />
              <p className="text-xs font-medium uppercase text-muted-foreground">Backend logs path</p>
              <p className="mt-1 break-words text-xs text-foreground">{diagnostics?.log_dir ?? "Pending"}</p>
            </div>
          </div>
          {visibleIssue && (!ready || visibleIssue.stage === "diagnostics") ? (
            <div className={`flex gap-3 rounded-md border px-4 py-3 text-sm text-foreground ${visibleIssue.stage === "diagnostics" ? "border-accent/40 bg-accent/10" : "border-destructive/30 bg-destructive/5"}`}>
              <AlertTriangle className={`mt-0.5 h-4 w-4 shrink-0 ${visibleIssue.stage === "diagnostics" ? "text-accent-foreground" : "text-destructive"}`} />
              <div>
                <p className="font-medium">{visibleIssue.stage === "diagnostics" ? "Diagnostics unavailable" : "Startup check failed"}</p>
                <p className="mt-1 break-words text-muted-foreground">
                  Stage: {visibleIssue.stage}. URL: {visibleIssue.url}. {visibleIssue.status ? `HTTP ${visibleIssue.status}. ` : ""}
                  {visibleIssue.message}
                </p>
              </div>
            </div>
          ) : null}
        </div>
      </section>
    </main>
  );
}
