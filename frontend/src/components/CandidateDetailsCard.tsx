import type { CandidateDetails } from "../types/candidate";
import { ConfidenceBadge, StatusBadge } from "./badges";

export function CandidateDetailsCard({ candidate }: { candidate: CandidateDetails }) {
  return (
    <div className="rounded-md border border-border bg-card p-4">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <p className="text-sm font-semibold">{candidate.ip_address}:{candidate.port}</p>
          <p className="text-sm text-muted-foreground">Unit ID {candidate.unit_id}</p>
        </div>
        <StatusBadge value={candidate.status} />
      </div>
      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2 xl:grid-cols-4">
        <div><dt className="text-muted-foreground">Type Guess</dt><dd className="font-medium">{candidate.device_type_guess ?? "unknown"}</dd></div>
        <div><dt className="text-muted-foreground">Confidence</dt><dd><ConfidenceBadge value={candidate.confidence_score} /></dd></div>
        <div><dt className="text-muted-foreground">Vendor Guess</dt><dd className="font-medium">{candidate.vendor_guess ?? "unknown"}</dd></div>
        <div><dt className="text-muted-foreground">Scan Result</dt><dd className="font-medium">#{candidate.scan_result_id}</dd></div>
      </dl>
    </div>
  );
}
