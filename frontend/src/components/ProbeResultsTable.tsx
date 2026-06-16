import type { CandidateProbeResult } from "../types/candidate";
import { EmptyState } from "./EmptyState";

export function ProbeResultsTable({ results }: { results: CandidateProbeResult[] }) {
  if (results.length === 0) {
    return <EmptyState title="No register validation results" description="Run a probe after a configured register profile is available." />;
  }
  return (
    <div className="overflow-hidden rounded-md border border-border bg-card">
      <table className="w-full min-w-[980px] text-left text-sm">
        <thead className="bg-muted text-xs uppercase text-muted-foreground">
          <tr>
            <th className="px-3 py-2">Metric</th>
            <th className="px-3 py-2">Register</th>
            <th className="px-3 py-2">Function</th>
            <th className="px-3 py-2">Data Type</th>
            <th className="px-3 py-2">Decoded Value</th>
            <th className="px-3 py-2">Source</th>
            <th className="px-3 py-2">Status</th>
            <th className="px-3 py-2">Response</th>
            <th className="px-3 py-2">Failure</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {results.map((result) => (
            <tr key={result.id}>
              <td className="px-3 py-2 font-medium">{result.metric ?? "-"}</td>
              <td className="px-3 py-2">{result.register_address}</td>
              <td className="px-3 py-2">{result.function_code}</td>
              <td className="px-3 py-2">{result.data_type}</td>
              <td className="px-3 py-2 tabular-nums">{result.decoded_value ?? "-"}{result.unit ? ` ${result.unit}` : ""}</td>
              <td className="px-3 py-2">{result.source.replace(/_/g, " ")}</td>
              <td className="px-3 py-2">
                {result.validated_from_config ? "Validated from config" : result.status.replace(/_/g, " ")}
              </td>
              <td className="px-3 py-2 tabular-nums">{result.response_time_ms === null ? "-" : `${result.response_time_ms} ms`}</td>
              <td className="px-3 py-2">{result.failure_reason ?? (result.exception_code === null ? "-" : `Modbus exception ${result.exception_code}`)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
