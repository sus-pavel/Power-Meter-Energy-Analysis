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

function parseProbeSummary(value: string | null) {
  if (!value) {
    return null;
  }
  try {
    return JSON.parse(value) as {
      recommended_next_action?: string;
      failed_checks?: Array<{ metric?: string | null; address?: number; status?: string | null; failure_reason?: string | null }>;
      from_config?: { profile_id?: string; profile_source?: string; registers_configured?: number };
      from_device_identification?: Record<string, string>;
    };
  } catch {
    return null;
  }
}

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
  const probeSummary = parseProbeSummary(candidate?.probe_summary_json ?? null);

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
              <StatusCard label="Probe Status" value={(candidate.probe_status ?? "not probed").replace(/_/g, " ")} detail="Validation state" />
              <StatusCard label="Profile Source" value={(candidate.probe_profile_source ?? "unknown").replace(/_/g, " ")} detail={candidate.probe_profile_id ?? "No profile selected"} />
              <StatusCard
                label="Vendor Identification"
                value={candidate.vendor_identification_supported ? "Available" : "Unavailable"}
                detail={candidate.vendor_identification_error ?? candidate.vendor_name ?? "FC43/14 not confirmed"}
              />
            </div>
            {candidate.probe_status ? (
              <section className="rounded-md border border-border bg-card p-4 text-sm">
                <div className="grid gap-3 md:grid-cols-3">
                  <div>
                    <p className="text-muted-foreground">Validation Status</p>
                    <p className="font-medium">{candidate.probe_status.replace(/_/g, " ")}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Quality</p>
                    <p className="font-medium">{candidate.probe_quality?.replace(/_/g, " ") ?? "unknown"}</p>
                  </div>
                  <div>
                    <p className="text-muted-foreground">Recommended Next Action</p>
                    <p className="font-medium">{probeSummary?.recommended_next_action ?? "Run probe or configure a register map."}</p>
                  </div>
                </div>
                {probeSummary?.failed_checks?.length ? (
                  <div className="mt-4">
                    <p className="font-medium">Failed Checks</p>
                    <ul className="mt-2 space-y-1 text-muted-foreground">
                      {probeSummary.failed_checks.slice(0, 4).map((check, index) => (
                        <li key={`${check.metric ?? "check"}-${index}`}>
                          {(check.metric ?? `Register ${check.address ?? "-"}`)}: {(check.status ?? "failed").replace(/_/g, " ")}{check.failure_reason ? ` (${check.failure_reason})` : ""}
                        </li>
                      ))}
                    </ul>
                  </div>
                ) : null}
              </section>
            ) : null}
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
