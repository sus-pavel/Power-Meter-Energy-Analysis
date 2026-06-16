import type { CandidateProbeResult } from "../types/candidate";
import { EmptyState } from "./EmptyState";

export function ProbeResultsTable({ results }: { results: CandidateProbeResult[] }) {
  if (results.length === 0) {
    return <EmptyState title="No probe results" description="Run a safe probe to collect configured register reads." />;
  }
  return (
    <div className="overflow-hidden rounded-md border border-border bg-card">
      <table className="w-full min-w-[720px] text-left text-sm">
        <thead className="bg-muted text-xs uppercase text-muted-foreground">
          <tr>
            <th className="px-3 py-2">Register</th>
            <th className="px-3 py-2">Function</th>
            <th className="px-3 py-2">Data Type</th>
            <th className="px-3 py-2">Decoded Value</th>
            <th className="px-3 py-2">Valid</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {results.map((result) => (
            <tr key={result.id}>
              <td className="px-3 py-2">{result.register_address}</td>
              <td className="px-3 py-2">{result.function_code}</td>
              <td className="px-3 py-2">{result.data_type}</td>
              <td className="px-3 py-2 tabular-nums">{result.decoded_value ?? "-"}</td>
              <td className="px-3 py-2">{result.valid ? "Yes" : "No"}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
