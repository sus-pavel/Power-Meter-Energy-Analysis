import type { ScanJob } from "../types/discovery";
import { StatusBadge } from "./badges";

export function DiscoveryProgressCard({ job }: { job: ScanJob }) {
  return (
    <div className="rounded-md border border-border bg-card p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">Scan job #{job.id}</p>
          <p className="text-sm text-muted-foreground">{job.ip_start} - {job.ip_end}</p>
        </div>
        <StatusBadge value={job.status} />
      </div>
      <div className="mt-4">
        <div className="mb-1 flex justify-between text-xs text-muted-foreground">
          <span>{job.processed_hosts} / {job.total_hosts} hosts</span>
          <span>{job.progress_percent}%</span>
        </div>
        <div className="h-2 overflow-hidden rounded-sm bg-muted">
          <div className="h-full bg-primary" style={{ width: `${Math.min(100, Math.max(0, job.progress_percent))}%` }} />
        </div>
      </div>
      <div className="mt-3 grid gap-2 text-sm sm:grid-cols-3">
        <span>Found hosts: <strong>{job.found_hosts}</strong></span>
        <span>Started: <strong>{formatDate(job.started_at)}</strong></span>
        <span>Finished: <strong>{formatDate(job.finished_at)}</strong></span>
      </div>
      {job.error_message ? <p className="mt-3 text-sm text-red-700">{job.error_message}</p> : null}
    </div>
  );
}

export function formatDate(value: string | null | undefined) {
  if (!value) {
    return "-";
  }
  return new Date(value).toLocaleString();
}
