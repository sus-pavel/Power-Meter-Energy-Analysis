import { FormEvent, useState } from "react";
import { ErrorState } from "../components/ErrorState";
import { LineChart } from "../components/LineChart";
import { LoadingState } from "../components/LoadingState";
import { MultiLineChart } from "../components/MultiLineChart";
import { PageHeader } from "../components/PageHeader";
import { ScatterChart } from "../components/ScatterChart";
import { WcorrHeatmap } from "../components/WcorrHeatmap";
import { useSSAAnalysis, useTrendMetrics } from "../hooks/useAnalytics";

export function SsaPage() {
  const metrics = useTrendMetrics();
  const analysis = useSSAAnalysis();
  const [deviceIds, setDeviceIds] = useState<string>("");
  const [metric, setMetric] = useState("active_power_total");
  const [aggregation, setAggregation] = useState("30min");
  const [fromValue, setFromValue] = useState("");
  const [toValue, setToValue] = useState("");
  const [windowPoints, setWindowPoints] = useState(48);
  const [componentCount, setComponentCount] = useState(20);
  const [clusterCount, setClusterCount] = useState(4);

  function submit(event: FormEvent) {
    event.preventDefault();
    analysis.mutate({
      device_ids: deviceIds.split(",").map((value) => Number(value.trim())).filter(Boolean),
      metric,
      aggregation,
      from: fromValue || undefined,
      to: toValue || undefined,
      window_points: windowPoints,
      component_count: componentCount,
      cluster_count: clusterCount
    });
  }

  return (
    <>
      <PageHeader title="SSA" description="Singular Spectrum Analysis using the prototype SSA trajectory, SVD, reconstruction, W-correlation, and KMeans logic." />
      <div className="space-y-4 p-6">
        <form onSubmit={submit} className="rounded-md border border-border bg-card p-4">
          <div className="grid gap-3 md:grid-cols-4">
            <label className="text-sm font-medium">Device IDs<input className="mt-1 h-9 w-full rounded-md border border-border px-2" placeholder="1,2 or blank for all" value={deviceIds} onChange={(e) => setDeviceIds(e.target.value)} /></label>
            <label className="text-sm font-medium">Metric<select className="mt-1 h-9 w-full rounded-md border border-border px-2" value={metric} onChange={(e) => setMetric(e.target.value)}>{(metrics.data?.metrics.length ? metrics.data.metrics : ["active_power_total"]).map((item) => <option key={item}>{item}</option>)}</select></label>
            <label className="text-sm font-medium">Aggregation<select className="mt-1 h-9 w-full rounded-md border border-border px-2" value={aggregation} onChange={(e) => setAggregation(e.target.value)}>{["5min", "10min", "15min", "30min", "1h"].map((item) => <option key={item}>{item}</option>)}</select></label>
            <label className="text-sm font-medium">Window Points<input className="mt-1 h-9 w-full rounded-md border border-border px-2" type="number" min={2} value={windowPoints} onChange={(e) => setWindowPoints(Number(e.target.value))} /></label>
            <label className="text-sm font-medium">From<input className="mt-1 h-9 w-full rounded-md border border-border px-2" type="datetime-local" value={fromValue} onChange={(e) => setFromValue(e.target.value)} /></label>
            <label className="text-sm font-medium">To<input className="mt-1 h-9 w-full rounded-md border border-border px-2" type="datetime-local" value={toValue} onChange={(e) => setToValue(e.target.value)} /></label>
            <label className="text-sm font-medium">Components<input className="mt-1 h-9 w-full rounded-md border border-border px-2" type="number" min={1} value={componentCount} onChange={(e) => setComponentCount(Number(e.target.value))} /></label>
            <label className="text-sm font-medium">Clusters<input className="mt-1 h-9 w-full rounded-md border border-border px-2" type="number" min={1} value={clusterCount} onChange={(e) => setClusterCount(Number(e.target.value))} /></label>
          </div>
          <button className="mt-4 h-9 rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground disabled:opacity-60" disabled={analysis.isPending}>Run Analysis</button>
        </form>
        {analysis.isPending ? <LoadingState label="Running SSA analysis" /> : null}
        {analysis.isError ? <ErrorState title="SSA analysis failed" message="Check the selected range has enough aggregated points." /> : null}
        {analysis.data ? (
          <>
            <LineChart points={analysis.data.original_series} label="Original series" />
            <LineChart points={analysis.data.trend_series} label="Trend component" />
            <MultiLineChart series={analysis.data.cluster_series.map((item) => ({ name: `Cluster ${item.cluster}`, points: item.points }))} />
            <LineChart points={analysis.data.cumulative_contribution.map((point) => ({ ts: `C${point.component}`, value: point.value }))} label="Cumulative contribution" />
            <ScatterChart points={analysis.data.amplitude_frequency_points} />
            <WcorrHeatmap matrix={analysis.data.wcorr_matrix} />
          </>
        ) : null}
      </div>
    </>
  );
}
