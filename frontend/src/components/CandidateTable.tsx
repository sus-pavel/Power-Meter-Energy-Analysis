import { Link } from "react-router-dom";
import { Eye } from "lucide-react";
import type { CandidateSummary } from "../types/candidate";
import { ConfidenceBadge } from "./badges";
import { CandidateStatusBadge } from "./CandidateStatusBadge";

export function CandidateTable({ candidates }: { candidates: CandidateSummary[] }) {
  return (
    <div className="overflow-hidden rounded-md border border-border bg-card">
      <table className="w-full min-w-[820px] text-left text-sm">
        <thead className="bg-muted text-xs uppercase text-muted-foreground">
          <tr>
            <th className="px-3 py-2">IP</th>
            <th className="px-3 py-2">Port</th>
            <th className="px-3 py-2">Unit ID</th>
            <th className="px-3 py-2">Status</th>
            <th className="px-3 py-2">Type Guess</th>
            <th className="px-3 py-2">Confidence</th>
            <th className="px-3 py-2">Created</th>
            <th className="px-3 py-2">Actions</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {candidates.map((candidate) => (
            <tr key={candidate.id} className="hover:bg-muted/40">
              <td className="px-3 py-2 font-medium">{candidate.ip_address}</td>
              <td className="px-3 py-2">{candidate.port}</td>
              <td className="px-3 py-2">{candidate.unit_id}</td>
              <td className="px-3 py-2"><CandidateStatusBadge status={candidate.status} /></td>
              <td className="px-3 py-2">{candidate.device_type_guess ?? "-"}</td>
              <td className="px-3 py-2"><ConfidenceBadge value={candidate.confidence_score} /></td>
              <td className="px-3 py-2">{new Date(candidate.updated_at).toLocaleString()}</td>
              <td className="px-3 py-2">
                <Link title="View" className="inline-flex rounded-md border border-border p-2 hover:bg-muted" to={`/candidates/${candidate.id}`}>
                  <Eye className="h-4 w-4" />
                </Link>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
