import type { OperationalDevice, OperationsStatus, RecentMeasurements } from "../types/operations";

interface AttentionPanelProps {
  status: OperationsStatus;
  devices: OperationalDevice[];
  measurements: RecentMeasurements;
}

export function AttentionPanel({ status, devices, measurements }: AttentionPanelProps) {
  const issues = [
    ...devices.filter((device) => device.status === "offline").map((device) => `Device offline: ${device.name}`),
    ...devices.filter((device) => device.status === "error").map((device) => `Device error: ${device.name}`),
    ...devices.filter((device) => device.enabled && device.registers_enabled === 0).map((device) => `No enabled registers: ${device.name}`),
    ...(status.pending_candidates > 0 ? [`${status.pending_candidates} candidates pending review`] : []),
    ...(measurements.available ? [] : ["No measurement data available yet"])
  ];
  return (
    <section className="rounded-md border border-border bg-card p-4">
      <h2 className="text-sm font-semibold">Attention</h2>
      {issues.length === 0 ? (
        <p className="mt-2 text-sm text-muted-foreground">No urgent operational issues.</p>
      ) : (
        <ul className="mt-2 space-y-1 text-sm">
          {issues.map((issue) => <li key={issue} className="text-amber-800">- {issue}</li>)}
        </ul>
      )}
    </section>
  );
}
