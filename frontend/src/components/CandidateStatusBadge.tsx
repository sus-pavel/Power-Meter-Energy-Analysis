import { StatusBadge } from "./badges";
import type { CandidateStatus } from "../types/candidate";

export function CandidateStatusBadge({ status }: { status: CandidateStatus }) {
  return <StatusBadge value={status} />;
}
