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
import type { ScanJob } from "../types/discovery";

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
    createMutation.mutate({ ip_start: ipStart, ip_end: ipEnd });
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
          <form onSubmit={submit} className="w-full max-w-md rounded-md border border-border bg-card p-5 shadow-lg">
            <h2 className="text-base font-semibold">Start Discovery Scan</h2>
            <div className="mt-4 grid gap-3">
              <label className="text-sm font-medium">Start IP<input className="mt-1 h-9 w-full rounded-md border border-border px-3" value={ipStart} onChange={(e) => setIpStart(e.target.value)} /></label>
              <label className="text-sm font-medium">End IP<input className="mt-1 h-9 w-full rounded-md border border-border px-3" value={ipEnd} onChange={(e) => setIpEnd(e.target.value)} /></label>
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
