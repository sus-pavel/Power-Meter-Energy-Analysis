import type { DeviceMeasurement } from "../types/device";
import { EmptyState } from "./EmptyState";

export function RecentMeasurementsTable({ measurements }: { measurements: DeviceMeasurement[] }) {
  if (measurements.length === 0) {
    return <EmptyState title="No measurements yet" description="Start polling after the device register map is configured." />;
  }
  return (
    <div className="overflow-hidden rounded-md border border-border bg-card">
      <table className="w-full min-w-[760px] text-left text-sm">
        <thead className="bg-muted text-xs uppercase text-muted-foreground">
          <tr>
            <th className="px-3 py-2">Timestamp</th>
            <th className="px-3 py-2">Metric</th>
            <th className="px-3 py-2">Value</th>
            <th className="px-3 py-2">Unit</th>
            <th className="px-3 py-2">Register ID</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-border">
          {measurements.map((measurement) => (
            <tr key={measurement.id} className="hover:bg-muted/40">
              <td className="px-3 py-2 tabular-nums">{new Date(measurement.timestamp * 1000).toLocaleString()}</td>
              <td className="px-3 py-2 font-medium">{measurement.metric}</td>
              <td className="px-3 py-2 tabular-nums">{Number(measurement.value).toFixed(3)}</td>
              <td className="px-3 py-2">{measurement.unit ?? "-"}</td>
              <td className="px-3 py-2">{measurement.register_id}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
