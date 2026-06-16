import type { RecentMeasurements } from "../types/operations";

export function MeasurementAvailabilityCard({ measurements }: { measurements: RecentMeasurements }) {
  return (
    <section className="rounded-md border border-border bg-card p-4">
      <h2 className="text-sm font-semibold">Measurement Availability</h2>
      {measurements.available ? (
        <dl className="mt-3 grid gap-3 text-sm sm:grid-cols-3">
          <div><dt className="text-muted-foreground">Last measurement</dt><dd className="font-medium">{measurements.last_measurement_at ? new Date(measurements.last_measurement_at).toLocaleString() : "-"}</dd></div>
          <div><dt className="text-muted-foreground">Points last hour</dt><dd className="font-medium">{measurements.total_points_last_hour ?? 0}</dd></div>
          <div><dt className="text-muted-foreground">Total power, kW</dt><dd className="font-medium">{measurements.total_power_kw ?? "-"}</dd></div>
        </dl>
      ) : (
        <p className="mt-2 text-sm text-muted-foreground">{measurements.message ?? "No measurement data available yet. Start polling after devices and registers are configured."}</p>
      )}
    </section>
  );
}
