import { useMemo, useState } from "react";
import { ErrorState } from "../components/ErrorState";
import { LineChart } from "../components/LineChart";
import { LoadingState } from "../components/LoadingState";
import { PageHeader } from "../components/PageHeader";
import { StatusCard } from "../components/StatusCard";
import { useTrendMetrics, useTrendSeries, useTrendSummary } from "../hooks/useAnalytics";

const AGGREGATIONS = ["raw", "5min", "10min", "15min", "30min", "1h"];

export function HistoryPage() {
  const metrics = useTrendMetrics();
  const [deviceId, setDeviceId] = useState<string>("");
  const [metric, setMetric] = useState("active_power_total");
  const [aggregation, setAggregation] = useState("5min");
  const [fromValue, setFromValue] = useState("");
  const [toValue, setToValue] = useState("");
  const params = useMemo(() => ({
    device_id: deviceId ? Number(deviceId) : undefined,
    metric,
    aggregation,
    from: fromValue || undefined,
    to: toValue || undefined,
    limit: 1000
  }), [aggregation, deviceId, fromValue, metric, toValue]);
  const series = useTrendSeries(params);
  const summary = useTrendSummary(params);

  return (
    <>
      <PageHeader title="History" description="Historical trends from raw and aggregated app measurements." />
      <div className="space-y-4 p-6">
        <section className="rounded-md border border-border bg-card p-4">
          <div className="grid gap-3 md:grid-cols-5">
            <label className="text-sm font-medium">Device<select className="mt-1 h-9 w-full rounded-md border border-border px-2" value={deviceId} onChange={(e) => setDeviceId(e.target.value)}><option value="">All devices</option>{metrics.data?.devices.map((device) => <option key={device.id} value={device.id}>{device.name}</option>)}</select></label>
            <label className="text-sm font-medium">Metric<select className="mt-1 h-9 w-full rounded-md border border-border px-2" value={metric} onChange={(e) => setMetric(e.target.value)}>{(metrics.data?.metrics.length ? metrics.data.metrics : ["active_power_total"]).map((item) => <option key={item}>{item}</option>)}</select></label>
            <label className="text-sm font-medium">Aggregation<select className="mt-1 h-9 w-full rounded-md border border-border px-2" value={aggregation} onChange={(e) => setAggregation(e.target.value)}>{AGGREGATIONS.map((item) => <option key={item}>{item}</option>)}</select></label>
            <label className="text-sm font-medium">From<input className="mt-1 h-9 w-full rounded-md border border-border px-2" type="datetime-local" value={fromValue} onChange={(e) => setFromValue(e.target.value)} /></label>
            <label className="text-sm font-medium">To<input className="mt-1 h-9 w-full rounded-md border border-border px-2" type="datetime-local" value={toValue} onChange={(e) => setToValue(e.target.value)} /></label>
          </div>
        </section>
        {series.isLoading || summary.isLoading ? <LoadingState label="Loading historical trends" /> : null}
        {series.isError || summary.isError ? <ErrorState title="Trend query failed" message="The selected trend could not be loaded." /> : null}
        {summary.data ? (
          <div className="grid gap-3 sm:grid-cols-4">
            <StatusCard label="Mean" value={summary.data.mean?.toFixed(3) ?? "-"} />
            <StatusCard label="Min" value={summary.data.min?.toFixed(3) ?? "-"} />
            <StatusCard label="Max" value={summary.data.max?.toFixed(3) ?? "-"} />
            <StatusCard label="Samples" value={summary.data.sample_count} />
          </div>
        ) : null}
        {series.data ? <LineChart points={series.data.points} label={`${series.data.metric} (${series.data.aggregation})`} /> : null}
      </div>
    </>
  );
}
