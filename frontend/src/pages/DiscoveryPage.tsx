import { FormEvent, useMemo, useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { AxiosError } from "axios";
import { cancelDiscoveryJob, createDiscoveryScan } from "../api/discovery";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { DiscoveryJobTable } from "../components/DiscoveryJobTable";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { PageHeader } from "../components/PageHeader";
import { useDiscoveryJobs } from "../hooks/useDiscovery";
import { usePermissions } from "../hooks/usePermissions";
import type { ScanJob, UnitIdScanMode } from "../types/discovery";

function ipToNumber(ip: string) {
  const parts = ip.split(".").map(Number);
  if (parts.length !== 4 || parts.some((part) => !Number.isInteger(part) || part < 0 || part > 255)) {
    return null;
  }
  return parts.reduce((acc, part) => acc * 256 + part, 0);
}

export function DiscoveryPage() {
  const { data, isLoading, isError } = useDiscoveryJobs();
  const { canManageLifecycle } = usePermissions();
  const queryClient = useQueryClient();
  const [modalOpen, setModalOpen] = useState(false);
  const [ipStart, setIpStart] = useState("192.168.1.1");
  const [ipEnd, setIpEnd] = useState("192.168.1.254");
  const [unitIdScanMode, setUnitIdScanMode] = useState<UnitIdScanMode>("quick");
  const [customUnitIds, setCustomUnitIds] = useState("");
  const [timeoutSeconds, setTimeoutSeconds] = useState("2.0");
  const [maxConcurrentHosts, setMaxConcurrentHosts] = useState("5");
  const [formError, setFormError] = useState<string | null>(null);
  const [cancelJob, setCancelJob] = useState<ScanJob | null>(null);

  const createMutation = useMutation({
    mutationFn: createDiscoveryScan,
    onSuccess: () => {
      setModalOpen(false);
      queryClient.invalidateQueries({ queryKey: ["discovery", "jobs"] });
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      setFormError(error.response?.data?.detail ?? "Discovery scan could not be started.");
    }
  });

  const cancelMutation = useMutation({
    mutationFn: cancelDiscoveryJob,
    onSuccess: () => {
      setCancelJob(null);
      queryClient.invalidateQueries({ queryKey: ["discovery", "jobs"] });
    }
  });

  const grouped = useMemo(() => ({
    active: data?.filter((job) => job.status === "pending" || job.status === "running") ?? [],
    completed: data?.filter((job) => job.status === "completed") ?? [],
    cancelled: data?.filter((job) => job.status === "cancelled" || job.status === "failed") ?? []
  }), [data]);

  function submit(event: FormEvent) {
    event.preventDefault();
    setFormError(null);
    const start = ipToNumber(ipStart);
    const end = ipToNumber(ipEnd);
    if (start === null || end === null) {
      setFormError("Enter valid IPv4 addresses.");
      return;
    }
    if (end < start) {
      setFormError("End IP must be greater than or equal to start IP.");
      return;
    }
    if (end - start + 1 > 1024) {
      setFormError("Range is limited to 1024 hosts from the UI.");
      return;
    }
    const timeout = Number(timeoutSeconds);
    if (!Number.isFinite(timeout) || timeout < 0.5 || timeout > 10) {
      setFormError("Timeout must be between 0.5 and 10.0 seconds.");
      return;
    }
    const concurrency = Number(maxConcurrentHosts);
    if (!Number.isInteger(concurrency) || concurrency < 1) {
      setFormError("Max concurrent hosts must be at least 1.");
      return;
    }
    const payload = {
      ip_start: ipStart,
      ip_end: ipEnd,
      unit_id_scan_mode: unitIdScanMode,
      timeout_seconds: timeout,
      max_concurrent_hosts: concurrency
    };
    if (unitIdScanMode === "custom") {
      const unitIds = customUnitIds.split(",").map((value) => value.trim()).filter(Boolean).map(Number);
      if (unitIds.length === 0) {
        setFormError("Enter at least one custom Unit ID.");
        return;
      }
      if (unitIds.some((unitId) => !Number.isInteger(unitId) || unitId < 0 || unitId > 255)) {
        setFormError("Custom Unit IDs must be whole numbers from 0 to 255.");
        return;
      }
      createMutation.mutate({ ...payload, unit_ids: unitIds });
      return;
    }
    createMutation.mutate(payload);
  }

  return (
    <>
      <PageHeader title="Discovery" description="Launch and monitor safe Modbus TCP discovery jobs." />
      <div className="space-y-6 p-6">
        {canManageLifecycle ? (
          <button className="inline-flex h-9 items-center rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground" onClick={() => setModalOpen(true)}>
            <Plus className="mr-2 h-4 w-4" />Start Discovery Scan
          </button>
        ) : null}
        {isLoading ? <LoadingState label="Loading discovery jobs" /> : null}
        {isError ? <ErrorState message="Discovery jobs could not be loaded." /> : null}
        {data && data.length === 0 ? <EmptyState title="No discovery jobs" description="Start a scan to discover Modbus-compatible endpoints." /> : null}
        {data && data.length > 0 ? (
          <>
            <section className="space-y-2"><h2 className="text-sm font-semibold">Active Jobs</h2><DiscoveryJobTable jobs={grouped.active} canManage={canManageLifecycle} onCancel={setCancelJob} /></section>
            <section className="space-y-2"><h2 className="text-sm font-semibold">Completed Jobs</h2><DiscoveryJobTable jobs={grouped.completed} canManage={canManageLifecycle} onCancel={setCancelJob} /></section>
            <section className="space-y-2"><h2 className="text-sm font-semibold">Cancelled / Failed Jobs</h2><DiscoveryJobTable jobs={grouped.cancelled} canManage={canManageLifecycle} onCancel={setCancelJob} /></section>
          </>
        ) : null}
      </div>
      {modalOpen ? (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/30 px-4">
          <form onSubmit={submit} className="max-h-[90vh] w-full max-w-lg overflow-y-auto rounded-md border border-border bg-card p-5 shadow-lg">
            <h2 className="text-base font-semibold">Start Discovery Scan</h2>
            <div className="mt-4 grid gap-3">
              <label className="text-sm font-medium">Start IP<input className="mt-1 h-9 w-full rounded-md border border-border px-3" value={ipStart} onChange={(e) => setIpStart(e.target.value)} /></label>
              <label className="text-sm font-medium">End IP<input className="mt-1 h-9 w-full rounded-md border border-border px-3" value={ipEnd} onChange={(e) => setIpEnd(e.target.value)} /></label>
              <label className="text-sm font-medium">
                Unit ID scan mode
                <select className="mt-1 h-9 w-full rounded-md border border-border px-3" value={unitIdScanMode} onChange={(e) => setUnitIdScanMode(e.target.value as UnitIdScanMode)}>
                  <option value="quick">Quick</option>
                  <option value="extended">Extended</option>
                  <option value="full">Full</option>
                  <option value="custom">Custom</option>
                </select>
              </label>
              {unitIdScanMode === "full" ? <p className="rounded-md border border-amber-300 bg-amber-50 px-3 py-2 text-sm text-amber-900">Use only for one host or a small IP range.</p> : null}
              {unitIdScanMode === "custom" ? (
                <label className="text-sm font-medium">
                  Custom Unit IDs
                  <input className="mt-1 h-9 w-full rounded-md border border-border px-3" placeholder="7, 11, 17, 31" value={customUnitIds} onChange={(e) => setCustomUnitIds(e.target.value)} />
                </label>
              ) : null}
              <div className="grid gap-3 sm:grid-cols-2">
                <label className="text-sm font-medium">Timeout<input className="mt-1 h-9 w-full rounded-md border border-border px-3" inputMode="decimal" value={timeoutSeconds} onChange={(e) => setTimeoutSeconds(e.target.value)} /></label>
                <label className="text-sm font-medium">Max concurrent hosts<input className="mt-1 h-9 w-full rounded-md border border-border px-3" inputMode="numeric" value={maxConcurrentHosts} onChange={(e) => setMaxConcurrentHosts(e.target.value)} /></label>
              </div>
            </div>
            {formError ? <p className="mt-3 text-sm text-red-700">{formError}</p> : null}
            <div className="mt-5 flex justify-end gap-2">
              <button type="button" className="h-9 rounded-md border border-border px-3 text-sm hover:bg-muted" onClick={() => setModalOpen(false)}>Cancel</button>
              <button type="submit" disabled={createMutation.isPending} className="h-9 rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground disabled:opacity-60">Start Scan</button>
            </div>
          </form>
        </div>
      ) : null}
      <ConfirmDialog
        open={Boolean(cancelJob)}
        title="Cancel discovery job"
        message={`Cancel scan job #${cancelJob?.id}? Partial results will remain available.`}
        confirmLabel="Cancel Job"
        danger
        onCancel={() => setCancelJob(null)}
        onConfirm={() => cancelJob && cancelMutation.mutate(cancelJob.id)}
      />
    </>
  );
}
