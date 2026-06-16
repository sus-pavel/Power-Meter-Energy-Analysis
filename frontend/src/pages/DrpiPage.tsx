import { useEffect, useState } from "react";
import { ErrorState } from "../components/ErrorState";
import { LineChart } from "../components/LineChart";
import { LoadingState } from "../components/LoadingState";
import { MultiLineChart } from "../components/MultiLineChart";
import { PageHeader } from "../components/PageHeader";
import { StatusCard } from "../components/StatusCard";
import { useDrpiComponents, useDrpiHistory, useDrpiRecalculate, useDrpiSummary } from "../hooks/useAnalytics";
import { usePermissions } from "../hooks/usePermissions";

export function DrpiPage() {
  const summary = useDrpiSummary();
  const [sourceId, setSourceId] = useState("TOTAL");
  const { canManageLifecycle } = usePermissions();
  const recalculate = useDrpiRecalculate();
  useEffect(() => {
    if (summary.data?.sources.length && !summary.data.sources.some((source) => source.source_id === sourceId)) {
      setSourceId(summary.data.sources[0].source_id);
    }
  }, [sourceId, summary.data]);
  const history = useDrpiHistory(sourceId);
  const components = useDrpiComponents(sourceId);

  return (
    <>
      <PageHeader title="DRPI" description="Demand response potential index calculated with the prototype DRPI engine." />
      <div className="space-y-4 p-6">
        {summary.isLoading ? <LoadingState label="Loading DRPI summary" /> : null}
        {summary.isError ? <ErrorState title="DRPI unavailable" message="DRPI results could not be loaded." /> : null}
        <div className="flex flex-wrap items-end gap-3 rounded-md border border-border bg-card p-4">
          <label className="text-sm font-medium">Source<select className="mt-1 h-9 min-w-44 rounded-md border border-border px-2" value={sourceId} onChange={(e) => setSourceId(e.target.value)}>{(summary.data?.sources.length ? summary.data.sources : [{ source_id: "TOTAL" }]).map((source) => <option key={source.source_id}>{source.source_id}</option>)}</select></label>
          {canManageLifecycle ? <button className="h-9 rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground disabled:opacity-60" disabled={recalculate.isPending} onClick={() => recalculate.mutate()}>Recalculate</button> : null}
        </div>
        <div className="grid gap-3 sm:grid-cols-4">
          {(summary.data?.sources ?? []).filter((source) => source.source_id === sourceId).map((source) => (
            <>
              <StatusCard key="drpi" label="DRPI" value={source.DRPI.toFixed(3)} />
              <StatusCard key="f1" label="F1" value={source.F1.toFixed(3)} />
              <StatusCard key="f2" label="F2" value={source.F2.toFixed(3)} />
              <StatusCard key="f3" label="F3" value={source.F3.toFixed(3)} />
            </>
          ))}
        </div>
        {history.data ? <LineChart points={history.data.points} label={`DRPI trend: ${sourceId}`} /> : null}
        {components.data ? (
          <MultiLineChart series={[
            { name: "F1", points: components.data.points.map((point) => ({ ts: point.ts, value: point.F1 })) },
            { name: "F2", points: components.data.points.map((point) => ({ ts: point.ts, value: point.F2 })) },
            { name: "F3", points: components.data.points.map((point) => ({ ts: point.ts, value: point.F3 })) },
            { name: "DRPI", points: components.data.points.map((point) => ({ ts: point.ts, value: point.DRPI })) }
          ]} />
        ) : null}
      </div>
    </>
  );
}
