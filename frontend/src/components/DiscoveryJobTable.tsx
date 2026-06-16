import { Link } from "react-router-dom";
import { Eye, ListChecks, XCircle } from "lucide-react";
import type { ScanJob } from "../types/discovery";
import { StatusBadge } from "./badges";
import { formatDate } from "./DiscoveryProgressCard";

interface DiscoveryJobTableProps {
  jobs: ScanJob[];
  canManage: boolean;
  onCancel: (job: ScanJob) => void;
}

export function DiscoveryJobTable({ jobs, canManage, onCancel }: DiscoveryJobTableProps) {
  return (
    <div className="overflow-hidden rounded-md border border-border bg-card">
      <table className="w-full min-w-[980px] text-left text-sm">
        <thead className="bg-muted text-xs uppercase text-muted-foreground">
          <tr>
            <th className="px-3 py-2">ID</th>
            <th className="px-3 py-2">Status</th>
            <th className="px-3 py-2">IP Range</th>
            <th className="px-3 py-2">Progress</th>
            <th className="px-3 py-2">Found Hosts</th>
            <th className="px-3 py-2">Created By</th>
            <th className="px-3 py-2">Started</th>
            <th className="px-3 py-2">Finished</th>
            <th className="px-3 py-2">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {jobs.map((job) => (
            <tr key={job.id} className="hover:bg-muted/40">
              <td className="px-3 py-2 font-medium">#{job.id}</td>
              <td className="px-3 py-2"><StatusBadge value={job.status} /></td>
              <td className="px-3 py-2">{job.ip_start} - {job.ip_end}</td>
              <td className="px-3 py-2 tabular-nums">{job.progress_percent}%</td>
              <td className="px-3 py-2 tabular-nums">{job.found_hosts}</td>
              <td className="px-3 py-2">{job.created_by_user_id ?? "-"}</td>
              <td className="px-3 py-2">{formatDate(job.started_at)}</td>
              <td className="px-3 py-2">{formatDate(job.finished_at)}</td>
              <td className="px-3 py-2">
                <div className="flex gap-1">
                  <Link title="View" className="rounded-md border border-border p-2 hover:bg-muted" to={`/discovery/jobs/${job.id}`}><Eye className="h-4 w-4" /></Link>
                  <Link title="Results" className="rounded-md border border-border p-2 hover:bg-muted" to={`/discovery/jobs/${job.id}`}><ListChecks className="h-4 w-4" /></Link>
                  {canManage && (job.status === "pending" || job.status === "running") ? (
                    <button title="Cancel" className="rounded-md border border-border p-2 text-red-700 hover:bg-red-50" onClick={() => onCancel(job)}>
                      <XCircle className="h-4 w-4" />
                    </button>
                  ) : null}
                </div>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
