import { useState } from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate, useParams } from "react-router-dom";
import { AxiosError } from "axios";
import { probeCandidate, promoteCandidate, rejectCandidate } from "../api/candidates";
import { CandidateDetailsCard } from "../components/CandidateDetailsCard";
import { ConfirmDialog } from "../components/ConfirmDialog";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { PageHeader } from "../components/PageHeader";
import { ProbeResultsTable } from "../components/ProbeResultsTable";
import { PromotionDialog } from "../components/PromotionDialog";
import { StatusCard } from "../components/StatusCard";
import { useCandidate } from "../hooks/useCandidates";
import { usePermissions } from "../hooks/usePermissions";
import type { PromoteCandidatePayload } from "../types/candidate";

export function CandidateDetailsPage() {
  const candidateId = Number(useParams().candidateId);
  const query = useCandidate(candidateId);
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const { canManageLifecycle } = usePermissions();
  const [error, setError] = useState<string | null>(null);
  const [promoteOpen, setPromoteOpen] = useState(false);
  const [rejectOpen, setRejectOpen] = useState(false);

  const probeMutation = useMutation({
    mutationFn: () => probeCandidate(candidateId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["candidates", candidateId] }),
    onError: (err: AxiosError<{ detail?: string }>) => setError(err.response?.data?.detail ?? "Probe failed.")
  });
  const promoteMutation = useMutation({
    mutationFn: (payload: PromoteCandidatePayload) => promoteCandidate(candidateId, payload),
    onSuccess: (result) => navigate(`/devices/${result.device_id}`),
    onError: (err: AxiosError<{ detail?: string }>) => setError(err.response?.data?.detail ?? "Promotion failed.")
  });
  const rejectMutation = useMutation({
    mutationFn: () => rejectCandidate(candidateId),
    onSuccess: () => {
      setRejectOpen(false);
      queryClient.invalidateQueries({ queryKey: ["candidates", candidateId] });
      queryClient.invalidateQueries({ queryKey: ["candidates"] });
    },
    onError: (err: AxiosError<{ detail?: string }>) => setError(err.response?.data?.detail ?? "Reject failed.")
  });

  const candidate = query.data;

  return (
    <>
      <PageHeader title={`Candidate #${candidateId}`} description="Probe, fingerprint, and promote discovered endpoints." />
      <div className="space-y-4 p-6">
        {query.isLoading ? <LoadingState label="Loading candidate" /> : null}
        {query.isError ? <ErrorState message="Candidate could not be loaded." /> : null}
        {error ? <ErrorState title="Action failed" message={error} /> : null}
        {candidate ? (
          <>
            <CandidateDetailsCard candidate={candidate} />
            <div className="grid gap-4 sm:grid-cols-3">
              <StatusCard label="Device Type Guess" value={candidate.device_type_guess ?? "Unknown"} detail="Fingerprint result" />
              <StatusCard label="Confidence Score" value={candidate.confidence_score === null ? "-" : `${Math.round(candidate.confidence_score * 100)}%`} detail="Heuristic confidence" />
              <StatusCard label="Vendor Guess" value={candidate.vendor_guess ?? "unknown"} detail="Vendor-specific ID not enabled" />
            </div>
            {canManageLifecycle ? (
              <div className="flex flex-wrap gap-2">
                <button disabled={probeMutation.isPending || candidate.status === "promoted" || candidate.status === "rejected"} className="h-9 rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground disabled:opacity-60" onClick={() => probeMutation.mutate()}>
                  {probeMutation.isPending ? "Running Probe" : "Run Probe"}
                </button>
                <button disabled={candidate.status === "promoted" || candidate.status === "rejected"} className="h-9 rounded-md border border-border px-3 text-sm hover:bg-muted disabled:opacity-60" onClick={() => setPromoteOpen(true)}>Promote Device</button>
                <button disabled={candidate.status === "promoted" || candidate.status === "rejected"} className="h-9 rounded-md border border-red-200 px-3 text-sm text-red-700 hover:bg-red-50 disabled:opacity-60" onClick={() => setRejectOpen(true)}>Reject</button>
              </div>
            ) : null}
            <ProbeResultsTable results={candidate.probe_results} />
            <PromotionDialog
              open={promoteOpen}
              defaultName={`${candidate.device_type_guess ?? "Modbus Device"} ${candidate.ip_address}`}
              submitting={promoteMutation.isPending}
              onCancel={() => setPromoteOpen(false)}
              onSubmit={(payload) => promoteMutation.mutate(payload)}
            />
            <ConfirmDialog
              open={rejectOpen}
              title="Reject candidate"
              message="Reject this candidate? It will remain in history but will be closed for promotion."
              confirmLabel="Reject"
              danger
              onCancel={() => setRejectOpen(false)}
              onConfirm={() => rejectMutation.mutate()}
            />
          </>
        ) : null}
      </div>
    </>
  );
}
