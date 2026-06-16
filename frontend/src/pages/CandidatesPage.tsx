import { useMemo, useState } from "react";
import { CandidateTable } from "../components/CandidateTable";
import { EmptyState } from "../components/EmptyState";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { PageHeader } from "../components/PageHeader";
import { useCandidates } from "../hooks/useCandidates";
import type { CandidateStatus } from "../types/candidate";

const FILTERS: Array<"all" | CandidateStatus> = ["all", "discovered", "reviewed", "promoted", "rejected"];

export function CandidatesPage() {
  const { data, isLoading, isError } = useCandidates();
  const [filter, setFilter] = useState<(typeof FILTERS)[number]>("all");
  const [search, setSearch] = useState("");

  const filtered = useMemo(() => (data ?? []).filter((candidate) => {
    const matchesFilter = filter === "all" || candidate.status === filter;
    const value = `${candidate.ip_address} ${candidate.unit_id}`;
    return matchesFilter && value.includes(search.trim());
  }), [data, filter, search]);

  return (
    <>
      <PageHeader title="Candidates" description="Review discovered Modbus-compatible endpoints." />
      <div className="space-y-4 p-6">
        <div className="flex flex-wrap gap-2">
          {FILTERS.map((item) => <button key={item} className={`h-9 rounded-md border border-border px-3 text-sm capitalize ${filter === item ? "bg-muted text-foreground" : "bg-card text-muted-foreground"}`} onClick={() => setFilter(item)}>{item}</button>)}
          <input className="h-9 min-w-64 rounded-md border border-border px-3 text-sm" placeholder="Search IP or Unit ID" value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        {isLoading ? <LoadingState label="Loading candidates" /> : null}
        {isError ? <ErrorState message="Candidates could not be loaded." /> : null}
        {data && filtered.length === 0 ? <EmptyState title="No candidates match" description="Adjust filters or run discovery." /> : null}
        {filtered.length > 0 ? <CandidateTable candidates={filtered} /> : null}
      </div>
    </>
  );
}
