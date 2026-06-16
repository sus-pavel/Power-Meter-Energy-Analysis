import { AttentionPanel } from "../components/AttentionPanel";
import { DeviceStatusTable } from "../components/DeviceStatusTable";
import { ErrorState } from "../components/ErrorState";
import { LoadingState } from "../components/LoadingState";
import { MeasurementAvailabilityCard } from "../components/MeasurementAvailabilityCard";
import { OperationalStatusCards } from "../components/OperationalStatusCards";
import { PageHeader } from "../components/PageHeader";
import { RecentActivityList } from "../components/RecentActivityList";
import { useOperationalDevices, useOperationsEvents, useOperationsStatus, useRecentMeasurements } from "../hooks/useOperations";
import { usePermissions } from "../hooks/usePermissions";
import { usePollingControls, usePollingStatus } from "../hooks/usePolling";

export function OperationsPage() {
  const status = useOperationsStatus(5000);
  const devices = useOperationalDevices(5000);
  const measurements = useRecentMeasurements(5000);
  const events = useOperationsEvents(5000);
  const polling = usePollingStatus(5000);
  const pollingControls = usePollingControls();
  const { canManageLifecycle } = usePermissions();
  const loading = status.isLoading || devices.isLoading || measurements.isLoading || events.isLoading || polling.isLoading;
  const failed = status.isError || devices.isError || measurements.isError || events.isError || polling.isError;

  return (
    <>
      <PageHeader title="Operations" description="Device operational status, recent measurements, readiness, and events." />
      <div className="space-y-4 p-6">
        {loading ? <LoadingState label="Loading operations" /> : null}
        {failed ? <ErrorState title="Operations endpoint unavailable" message="Unable to load operational monitoring data." /> : null}
        {status.data ? <OperationalStatusCards status={status.data} /> : null}
        {polling.data ? (
          <section className="rounded-md border border-border bg-card p-4">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <div>
                <h2 className="text-sm font-semibold">Polling Control</h2>
                <p className="mt-1 text-sm text-muted-foreground">
                  {polling.data.running ? "Scheduler is running." : "Scheduler is stopped."} Active workers: {polling.data.active_workers}. Measurements last hour: {polling.data.measurements_last_hour}.
                </p>
              </div>
              {canManageLifecycle ? (
                <div className="flex gap-2">
                  <button
                    className="h-9 rounded-md bg-primary px-3 text-sm font-medium text-primary-foreground disabled:opacity-60"
                    disabled={polling.data.running || pollingControls.start.isPending}
                    onClick={() => pollingControls.start.mutate()}
                  >
                    Start
                  </button>
                  <button
                    className="h-9 rounded-md border border-border px-3 text-sm font-medium disabled:opacity-60"
                    disabled={!polling.data.running || pollingControls.stop.isPending}
                    onClick={() => pollingControls.stop.mutate()}
                  >
                    Stop
                  </button>
                </div>
              ) : null}
            </div>
          </section>
        ) : null}
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
