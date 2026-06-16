import { AttentionPanel } from "../components/AttentionPanel";
import { DeviceStatusTable } from "../components/DeviceStatusTable";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { MeasurementAvailabilityCard } from "../components/MeasurementAvailabilityCard";
import { OperationalStatusCards } from "../components/OperationalStatusCards";
import { PageHeader } from "../components/PageHeader";
import { RecentActivityList } from "../components/RecentActivityList";
import { StatusCard } from "../components/StatusCard";
import { useDashboardSummary } from "../hooks/useDashboardSummary";
import { useOperationalDevices, useOperationsEvents, useOperationsStatus, useRecentMeasurements } from "../hooks/useOperations";

export function DashboardPage() {
  const status = useOperationsStatus(10000);
  const devices = useOperationalDevices(10000);
  const measurements = useRecentMeasurements(10000);
  const events = useOperationsEvents(10000);
  const dashboard = useDashboardSummary();
  const loading = status.isLoading || devices.isLoading || measurements.isLoading || events.isLoading || dashboard.isLoading;
  const failed = status.isError || devices.isError || measurements.isError || events.isError || dashboard.isError;

  return (
    <>
      <PageHeader title="Dashboard" description="Operational visibility and polling readiness." />
      <div className="space-y-4 p-6">
        {loading ? <LoadingState label="Loading operational dashboard" /> : null}
        {failed ? <ErrorState title="Operations endpoint unavailable" message="Backend unavailable, unauthorized, or operations endpoint failed." /> : null}
        {status.data ? <OperationalStatusCards status={status.data} /> : null}
        {dashboard.data ? (
          <div className="grid gap-3 sm:grid-cols-4">
            <StatusCard label="Latest Total Power" value={dashboard.data.latest_total_power?.toFixed(3) ?? "-"} detail="Configured analytics metric" />
            <StatusCard label="Latest DRPI TOTAL" value={dashboard.data.latest_drpi_total?.toFixed(3) ?? "-"} />
            <StatusCard label="Analytics Services" value={dashboard.data.analytics_service_status?.running ? "Running" : "Stopped"} />
            <StatusCard label="5 min Aggregates" value={dashboard.data.aggregation_status?.["5min"] ?? 0} />
          </div>
        ) : null}
        {status.data && devices.data && measurements.data ? <AttentionPanel status={status.data} devices={devices.data} measurements={measurements.data} /> : null}
        {devices.data ? (
          <section className="space-y-2">
            <h2 className="text-sm font-semibold">Device Status</h2>
            <DeviceStatusTable devices={devices.data} />
          </section>
        ) : null}
        {measurements.data ? <MeasurementAvailabilityCard measurements={measurements.data} /> : null}
        {events.data ? <RecentActivityList events={events.data} /> : null}
      </div>
    </>
  );
}
