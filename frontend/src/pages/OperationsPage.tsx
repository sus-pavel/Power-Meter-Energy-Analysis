import { AttentionPanel } from "../components/AttentionPanel";
import { DeviceStatusTable } from "../components/DeviceStatusTable";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { MeasurementAvailabilityCard } from "../components/MeasurementAvailabilityCard";
import { OperationalStatusCards } from "../components/OperationalStatusCards";
import { PageHeader } from "../components/PageHeader";
import { RecentActivityList } from "../components/RecentActivityList";
import { useOperationalDevices, useOperationsEvents, useOperationsStatus, useRecentMeasurements } from "../hooks/useOperations";

export function OperationsPage() {
  const status = useOperationsStatus(5000);
  const devices = useOperationalDevices(5000);
  const measurements = useRecentMeasurements(5000);
  const events = useOperationsEvents(5000);
  const loading = status.isLoading || devices.isLoading || measurements.isLoading || events.isLoading;
  const failed = status.isError || devices.isError || measurements.isError || events.isError;

  return (
    <>
      <PageHeader title="Operations" description="Device operational status, recent measurements, readiness, and events." />
      <div className="space-y-4 p-6">
        {loading ? <LoadingState label="Loading operations" /> : null}
        {failed ? <ErrorState title="Operations endpoint unavailable" message="Unable to load operational monitoring data." /> : null}
        {status.data ? <OperationalStatusCards status={status.data} /> : null}
        {status.data && devices.data && measurements.data ? <AttentionPanel status={status.data} devices={devices.data} measurements={measurements.data} /> : null}
        {devices.data ? (
          <section className="space-y-2">
            <h2 className="text-sm font-semibold">Polling Readiness</h2>
            <DeviceStatusTable devices={devices.data} showReadiness />
          </section>
        ) : null}
        {measurements.data ? <MeasurementAvailabilityCard measurements={measurements.data} /> : null}
        {events.data ? <RecentActivityList events={events.data} /> : null}
      </div>
    </>
  );
}
