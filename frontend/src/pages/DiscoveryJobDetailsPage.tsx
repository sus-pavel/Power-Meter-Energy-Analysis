import { Link, useParams } from "react-router-dom";
import { DiscoveryProgressCard } from "../components/DiscoveryProgressCard";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { PageHeader } from "../components/PageHeader";
import { StatusBadge } from "../components/badges";
import { useDiscoveryJob, useDiscoveryJobResults } from "../hooks/useDiscovery";

export function DiscoveryJobDetailsPage() {
  const jobId = Number(useParams().jobId);
  const jobQuery = useDiscoveryJob(jobId);
  const resultsQuery = useDiscoveryJobResults(jobId);

  return (
    <>
      <PageHeader title={`Discovery Job #${jobId}`} description="Progress, status, and scan result candidates." />
      <div className="space-y-4 p-6">
        {jobQuery.isLoading ? <LoadingState label="Loading scan job" /> : null}
        {jobQuery.isError ? <ErrorState message="Discovery job could not be loaded." /> : null}
        {jobQuery.data ? <DiscoveryProgressCard job={jobQuery.data} /> : null}
        {resultsQuery.data ? (
          <div className="overflow-hidden rounded-md border border-border bg-card">
            <table className="w-full min-w-[760px] text-left text-sm">
              <thead className="bg-muted text-xs uppercase text-muted-foreground">
                <tr><th className="px-3 py-2">IP</th><th className="px-3 py-2">Port</th><th className="px-3 py-2">TCP</th><th className="px-3 py-2">Modbus</th><th className="px-3 py-2">Unit Hints</th><th className="px-3 py-2">Checked</th></tr>
              </thead>
              <tbody className="divide-y divide-border">
                {resultsQuery.data.map((result) => (
                  <tr key={result.id}>
                    <td className="px-3 py-2 font-medium">{result.ip_address}</td>
                    <td className="px-3 py-2">{result.port}</td>
                    <td className="px-3 py-2"><StatusBadge value={result.tcp_open ? "completed" : "failed"} /></td>
                    <td className="px-3 py-2"><StatusBadge value={result.modbus_responding ? "completed" : "failed"} /></td>
                    <td className="px-3 py-2">{result.candidate_unit_ids.join(", ") || "-"}</td>
                    <td className="px-3 py-2">{new Date(result.last_checked_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : null}
        <Link className="inline-flex h-9 items-center rounded-md border border-border px-3 text-sm hover:bg-muted" to="/candidates">Open candidate inbox</Link>
      </div>
    </>
  );
}
